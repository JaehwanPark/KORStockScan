import json
import os
from datetime import date, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.models import (
    Base,
    DailyStockQuote,
    SwingStrategyDiscoveryArm,
    SwingStrategyDiscoveryCandidate,
    SwingStrategyDiscoveryLabel,
)
from src.engine import swing_strategy_discovery_label_builder as mod
from src.engine.swing_strategy_discovery_schema import (
    ensure_swing_strategy_discovery_schema,
)


def _external_test_db_url() -> str:
    db_url = os.getenv("KORSTOCKSCAN_TEST_DATABASE_URL", "").strip()
    if not db_url:
        pytest.skip(
            "set KORSTOCKSCAN_TEST_DATABASE_URL to run DB-backed discovery label tests"
        )
    if "test" not in db_url.lower():
        pytest.skip(
            "KORSTOCKSCAN_TEST_DATABASE_URL must point to an isolated test database"
        )
    return db_url


def _setup_test_db():
    db_url = _external_test_db_url()
    ensure_swing_strategy_discovery_schema(db_url)
    engine = create_engine(db_url)
    Base.metadata.create_all(bind=engine, tables=[DailyStockQuote.__table__])
    with engine.begin() as conn:
        conn.execute(SwingStrategyDiscoveryLabel.__table__.delete())
        conn.execute(SwingStrategyDiscoveryArm.__table__.delete())
        conn.execute(SwingStrategyDiscoveryCandidate.__table__.delete())
        conn.execute(DailyStockQuote.__table__.delete())
    return db_url, engine, sessionmaker(bind=engine)


def _seed_arm(session, *, entry_policy="next_open_entry", exit_policy="fixed_5d"):
    candidate = SwingStrategyDiscoveryCandidate(
        source_date=date(2026, 5, 1),
        stock_code="000001",
        stock_name="테스트",
        policy_version="swing_strategy_discovery_sim_v1",
        selection_arm="lifecycle_rank",
        diversity_bucket="BREAKOUT|none|mid",
        position_tag="BREAKOUT",
        block_reason="no_block_observed",
        volatility_bucket="mid",
        theme_tags=json.dumps(["AI"]),
        lifecycle_exploration_score=0.8,
        source_features=json.dumps({"quote_features": {"reference_price": 1000}}),
        decision_authority="swing_sim_exploration_only",
        actual_order_submitted=False,
        broker_order_forbidden=True,
        runtime_effect=False,
    )
    session.add(candidate)
    session.flush()
    arm = SwingStrategyDiscoveryArm(
        candidate_id=candidate.id,
        source_date=date(2026, 5, 1),
        stock_code="000001",
        policy_version="swing_strategy_discovery_sim_v1",
        arm_id=f"test_{entry_policy}_{exit_policy}",
        entry_policy=entry_policy,
        sizing_policy="equal_notional",
        exit_policy=exit_policy,
        status="PENDING_ENTRY",
        virtual_entry_price=1000,
        virtual_qty=10,
        virtual_notional_krw=10_000,
        arm_features=json.dumps({}),
        actual_order_submitted=False,
        broker_order_forbidden=True,
        runtime_effect=False,
    )
    session.add(arm)
    return arm


def _seed_quotes(session, *, days=12):
    start = date(2026, 5, 2)
    for idx in range(days):
        close = 1000 + idx * 10
        session.add(
            DailyStockQuote(
                quote_date=start + timedelta(days=idx),
                stock_code="000001",
                stock_name="테스트",
                open_price=1000 + idx * 5,
                high_price=close + 40,
                low_price=close - 30,
                close_price=close,
                volume=1000,
            )
        )


def test_label_builder_generates_horizon_and_policy_exit_labels(tmp_path):
    db_url, _engine, Session = _setup_test_db()
    with Session.begin() as session:
        _seed_arm(session)
        _seed_quotes(session)

    report = mod.build_swing_strategy_discovery_labels(
        "2026-05-20", db_url=db_url, refresh_matured=True
    )

    assert report["runtime_effect"] is False
    assert report["allowed_runtime_apply"] is False
    assert report["summary"]["processed_arm_count"] == 1
    with Session() as session:
        labels = session.query(SwingStrategyDiscoveryLabel).all()
        arm = session.query(SwingStrategyDiscoveryArm).first()
    assert {label.label_horizon for label in labels} == {
        "1d",
        "5d",
        "10d",
        "policy_exit",
    }
    assert all(label.label_status == "labeled" for label in labels)
    assert arm.status == "EXITED"
    assert arm.actual_order_submitted is False
    assert arm.broker_order_forbidden is True
    assert arm.runtime_effect is False
    features = json.loads(arm.arm_features)
    assert features["label_maturity_status"] == "matured_labeled"
    assert features["future_quote_count"] == 12
    assert features["quotes_from_entry_count"] == 12
    assert features["runtime_effect"] is False
    assert features["allowed_runtime_apply"] is False
    assert report["implementation_status"] == "implemented"
    assert report["summary"]["maturity_status_counts"]["matured_labeled"] == 1


def test_pullback_entry_expires_when_limit_not_touched(tmp_path):
    db_url, _engine, Session = _setup_test_db()
    with Session.begin() as session:
        _seed_arm(session, entry_policy="pullback_limit_entry", exit_policy="fixed_5d")
        for idx in range(5):
            session.add(
                DailyStockQuote(
                    quote_date=date(2026, 5, 2) + timedelta(days=idx),
                    stock_code="000001",
                    stock_name="테스트",
                    open_price=1000,
                    high_price=1030,
                    low_price=995,
                    close_price=1010,
                    volume=1000,
                )
            )

    mod.build_swing_strategy_discovery_labels(
        "2026-05-20", db_url=db_url, refresh_matured=True
    )

    with Session() as session:
        arm = session.query(SwingStrategyDiscoveryArm).first()
        statuses = {
            label.label_status
            for label in session.query(SwingStrategyDiscoveryLabel).all()
        }
        features = json.loads(
            session.query(SwingStrategyDiscoveryLabel).first().label_features
        )
    assert arm.status == "EXPIRED"
    assert statuses == {"expired_entry_no_trigger"}
    assert features["stop_touch_outcome_bucket"] == "not_entered_or_pending"


def test_entry_day_stop_touch_recovered_bucket_is_recorded(tmp_path):
    db_url, _engine, Session = _setup_test_db()
    with Session.begin() as session:
        _seed_arm(session, entry_policy="next_open_entry", exit_policy="fixed_5d")
        quotes = [
            (1000, 1040, 960, 990),
            (990, 1020, 980, 1010),
            (1010, 1030, 1000, 1020),
            (1020, 1040, 1010, 1030),
            (1030, 1050, 1020, 1040),
        ]
        for idx, (open_price, high_price, low_price, close_price) in enumerate(quotes):
            session.add(
                DailyStockQuote(
                    quote_date=date(2026, 5, 2) + timedelta(days=idx),
                    stock_code="000001",
                    stock_name="테스트",
                    open_price=open_price,
                    high_price=high_price,
                    low_price=low_price,
                    close_price=close_price,
                    volume=1000,
                )
            )

    mod.build_swing_strategy_discovery_labels(
        "2026-05-20", db_url=db_url, refresh_matured=True
    )

    with Session() as session:
        arm = session.query(SwingStrategyDiscoveryArm).first()
        policy_label = (
            session.query(SwingStrategyDiscoveryLabel)
            .filter_by(label_horizon="policy_exit")
            .first()
        )
    arm_features = json.loads(arm.arm_features)
    label_features = json.loads(policy_label.label_features)
    assert (
        arm_features["stop_touch_outcome_bucket"]
        == "wick_stop_recovered_close_above_stop"
    )
    assert (
        label_features["stop_touch_outcome_bucket"]
        == "wick_stop_recovered_close_above_stop"
    )
    assert label_features["entry_day_low_from_entry_bucket"] == "stop_zone_3_5pct"
    assert label_features["entry_day_observation_role"] == "source_only_no_hard_gate"
    assert label_features["entry_day_observation_runtime_effect"] is False
    assert label_features["entry_day_observation_allowed_runtime_apply"] is False
    assert (
        label_features["entry_position_objective"]
        == "observe_entry_location_for_better_price_or_momentum_entry"
    )
    assert (
        label_features["entry_position_opportunity_bucket"]
        == "pullback_retest_observation"
    )
    assert arm_features["allowed_runtime_apply"] is False
    assert arm_features["runtime_effect"] is False


def test_entry_day_stop_touch_close_below_stop_bucket_is_recorded(tmp_path):
    db_url, _engine, Session = _setup_test_db()
    with Session.begin() as session:
        _seed_arm(session, entry_policy="next_open_entry", exit_policy="fixed_5d")
        quotes = [
            (1000, 1010, 960, 965),
            (965, 980, 950, 970),
            (970, 990, 960, 980),
            (980, 1000, 970, 990),
            (990, 1010, 980, 1000),
        ]
        for idx, (open_price, high_price, low_price, close_price) in enumerate(quotes):
            session.add(
                DailyStockQuote(
                    quote_date=date(2026, 5, 2) + timedelta(days=idx),
                    stock_code="000001",
                    stock_name="테스트",
                    open_price=open_price,
                    high_price=high_price,
                    low_price=low_price,
                    close_price=close_price,
                    volume=1000,
                )
            )

    mod.build_swing_strategy_discovery_labels(
        "2026-05-20", db_url=db_url, refresh_matured=True
    )

    with Session() as session:
        policy_label = (
            session.query(SwingStrategyDiscoveryLabel)
            .filter_by(label_horizon="policy_exit")
            .first()
        )
    features = json.loads(policy_label.label_features)
    assert features["stop_touch_outcome_bucket"] == "close_below_stop"
    assert features["entry_day_close_from_entry_bucket"] == "close_below_stop"
    assert features["entry_position_opportunity_bucket"] == "invalidation_observation"


def test_entry_day_momentum_chase_opportunity_bucket_is_source_only(tmp_path):
    db_url, _engine, Session = _setup_test_db()
    with Session.begin() as session:
        _seed_arm(session, entry_policy="next_open_entry", exit_policy="fixed_5d")
        quotes = [
            (1020, 1050, 1010, 1040),
            (1040, 1060, 1030, 1050),
            (1050, 1070, 1040, 1060),
            (1060, 1080, 1050, 1070),
            (1070, 1090, 1060, 1080),
        ]
        for idx, (open_price, high_price, low_price, close_price) in enumerate(quotes):
            session.add(
                DailyStockQuote(
                    quote_date=date(2026, 5, 2) + timedelta(days=idx),
                    stock_code="000001",
                    stock_name="테스트",
                    open_price=open_price,
                    high_price=high_price,
                    low_price=low_price,
                    close_price=close_price,
                    volume=1000,
                )
            )

    mod.build_swing_strategy_discovery_labels(
        "2026-05-20", db_url=db_url, refresh_matured=True
    )

    with Session() as session:
        policy_label = (
            session.query(SwingStrategyDiscoveryLabel)
            .filter_by(label_horizon="policy_exit")
            .first()
        )
    features = json.loads(policy_label.label_features)
    assert features["stop_touch_outcome_bucket"] == "no_touch"
    assert features["entry_position_opportunity_bucket"] == "momentum_chase_observation"
    assert features["entry_day_observation_allowed_runtime_apply"] is False


def test_bottom_rebound_entry_policies_are_anticipatory_without_breakout_confirmation():
    quotes = [
        mod.Quote(
            quote_date=date(2026, 5, 2),
            open_price=1005,
            high_price=1008,
            low_price=998,
            close_price=1002,
        ),
        mod.Quote(
            quote_date=date(2026, 5, 3),
            open_price=1000,
            high_price=1004,
            low_price=989,
            close_price=995,
        ),
    ]

    next_open = mod.simulate_entry("bottom_rebound_next_open_entry", 1000, quotes)
    retest = mod.simulate_entry(
        "bottom_rebound_signal_close_retest_limit_entry", 1000, quotes
    )
    atr_pullback = mod.simulate_entry(
        "bottom_rebound_atr_pullback_limit_entry", 1000, quotes
    )

    assert next_open.status == "entered"
    assert next_open.reason == "bottom_rebound_next_open"
    assert retest.status == "entered"
    assert retest.reason == "bottom_rebound_signal_close_retest_touched"
    assert atr_pullback.status == "entered"
    assert atr_pullback.reason == "bottom_rebound_atr_pullback_touched"
