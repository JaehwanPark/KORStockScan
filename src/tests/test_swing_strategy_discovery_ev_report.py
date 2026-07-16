import json
import os
from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.models import (
    SwingStrategyDiscoveryArm,
    SwingStrategyDiscoveryCandidate,
    SwingStrategyDiscoveryLabel,
)
from src.engine import swing_strategy_discovery_ev_report as mod
from src.engine.swing_strategy_discovery_schema import (
    ensure_swing_strategy_discovery_schema,
)


def _external_test_db_url() -> str:
    db_url = os.getenv("KORSTOCKSCAN_TEST_DATABASE_URL", "").strip()
    if not db_url:
        pytest.skip(
            "set KORSTOCKSCAN_TEST_DATABASE_URL to run DB-backed discovery EV tests"
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
    with engine.begin() as conn:
        conn.execute(SwingStrategyDiscoveryLabel.__table__.delete())
        conn.execute(SwingStrategyDiscoveryArm.__table__.delete())
        conn.execute(SwingStrategyDiscoveryCandidate.__table__.delete())
    return db_url, sessionmaker(bind=engine)


def _seed_labeled_arm(
    session,
    idx: int,
    *,
    ret: float,
    source_date=date(2026, 5, 1),
    selection_arm="lifecycle_rank",
    stop_touch_outcome_bucket="no_touch",
    entry_position_opportunity_bucket="neutral_location_observation",
):
    candidate = SwingStrategyDiscoveryCandidate(
        source_date=source_date,
        stock_code=f"{idx:06d}",
        stock_name=f"종목{idx}",
        policy_version="swing_strategy_discovery_sim_v1",
        selection_arm=selection_arm,
        diversity_bucket="BREAKOUT|none|mid",
        position_tag="BREAKOUT",
        block_reason="no_block_observed",
        volatility_bucket="mid",
        sector="IT",
        theme_tags=json.dumps(["AI"]),
        legacy_pick_type="MAIN" if selection_arm == "legacy_ml" else "DIAGNOSTIC",
        lifecycle_exploration_score=0.8,
        decision_authority="swing_sim_exploration_only",
        actual_order_submitted=False,
        broker_order_forbidden=True,
        runtime_effect=False,
    )
    session.add(candidate)
    session.flush()
    arm = SwingStrategyDiscoveryArm(
        candidate_id=candidate.id,
        source_date=source_date,
        stock_code=f"{idx:06d}",
        policy_version="swing_strategy_discovery_sim_v1",
        arm_id="arm01_next_open_equal_fixed5d",
        entry_policy="next_open_entry",
        sizing_policy="equal_notional",
        exit_policy="fixed_5d",
        status="EXITED",
        virtual_notional_krw=100_000,
        actual_order_submitted=False,
        broker_order_forbidden=True,
        runtime_effect=False,
    )
    session.add(arm)
    session.flush()
    session.add(
        SwingStrategyDiscoveryLabel(
            arm_row_id=arm.id,
            source_date=source_date,
            stock_code=f"{idx:06d}",
            policy_version="swing_strategy_discovery_sim_v1",
            label_horizon="policy_exit",
            label_version="swing_strategy_discovery_label_v1",
            label_status="labeled",
            mfe_pct=max(0, ret) + 1,
            mae_pct=min(0, ret) - 1,
            close_return_pct=ret,
            final_return_pct=ret,
            realized_exit_return_pct=ret,
            label_features=json.dumps(
                {
                    "fill_status": "entered",
                    "entry_reason": "next_open",
                    "exit_reason": "fixed_5d_close",
                    "final_return_basis": "arm_policy_exit",
                    "entry_price_delta_bucket": "near_reference",
                    "entry_day_gap_bucket": "flat_gap",
                    "entry_day_low_from_entry_bucket": "drawdown_1_3pct",
                    "entry_day_close_from_entry_bucket": "close_near_entry",
                    "stop_touch_outcome_bucket": stop_touch_outcome_bucket,
                    "entry_position_opportunity_bucket": entry_position_opportunity_bucket,
                }
            ),
        )
    )
    arm.arm_features = json.dumps(
        {
            "label_maturity_status": "matured_labeled",
            "source_quality_status": "ok",
            "future_quote_count": 12,
            "quotes_from_entry_count": 12,
            "entry_price_delta_bucket": "near_reference",
            "entry_day_gap_bucket": "flat_gap",
            "entry_day_low_from_entry_bucket": "drawdown_1_3pct",
            "entry_day_close_from_entry_bucket": "close_near_entry",
            "stop_touch_outcome_bucket": stop_touch_outcome_bucket,
            "entry_position_opportunity_bucket": entry_position_opportunity_bucket,
        }
    )


def test_ev_report_aggregates_surviving_arms_and_contract(tmp_path):
    db_url, Session = _setup_test_db()
    with Session.begin() as session:
        for idx, ret in enumerate([1.0, 2.0, 1.5, 0.5, 3.0, -0.2], start=1):
            _seed_labeled_arm(session, idx, ret=ret)
        _seed_labeled_arm(session, 20, ret=-2.0, selection_arm="legacy_ml")

    report = mod.build_swing_strategy_discovery_ev_report(
        "2026-05-20", db_url=db_url, lookback_days=30
    )

    assert report["runtime_effect"] is False
    assert report["source_only"] is True
    assert report["decision_authority"] == "swing_sim_exploration_only"
    assert report["allowed_runtime_apply"] is False
    assert report["broker_order_forbidden"] is True
    assert report["summary"]["labeled_sample_count"] == 7
    assert report["summary"]["surviving_arm_count"] >= 1
    assert report["surviving_arms"][0]["arm_id"] == "arm01_next_open_equal_fixed5d"
    assert report["legacy_vs_discovery"]["discovery_combined"]["sample_count"] == 6
    assert report["source_quality_summary"]["implementation_status"] == "implemented"
    assert (
        report["source_quality_summary"]["maturity_status_counts"]["matured_labeled"]
        == 7
    )
    assert report["source_quality_summary"]["runtime_effect"] is False


def test_ev_report_adds_source_only_morning_turbulence_analysis(tmp_path):
    db_url, Session = _setup_test_db()
    with Session.begin() as session:
        for idx, ret in enumerate([1.0, 0.5, -0.2, 1.2, 0.8], start=1):
            _seed_labeled_arm(
                session,
                idx,
                ret=ret,
                stop_touch_outcome_bucket="wick_stop_recovered_close_above_stop",
                entry_position_opportunity_bucket="pullback_retest_observation",
            )
        _seed_labeled_arm(
            session,
            10,
            ret=-3.2,
            stop_touch_outcome_bucket="close_below_stop",
            entry_position_opportunity_bucket="invalidation_observation",
        )

    report = mod.build_swing_strategy_discovery_ev_report(
        "2026-05-20", db_url=db_url, lookback_days=30
    )
    analysis = report["morning_turbulence_analysis"]
    contract = analysis["metric_contract"]
    stop_rows = {
        item["stop_touch_outcome_bucket"]: item
        for item in analysis["axes"]["stop_touch_outcome_bucket"]
    }
    opportunity_rows = {
        item["entry_position_opportunity_bucket"]: item
        for item in analysis["axes"]["entry_position_opportunity_bucket"]
    }

    assert report["runtime_effect"] is False
    assert report["allowed_runtime_apply"] is False
    assert report["broker_order_forbidden"] is True
    assert (
        report["morning_turbulence_metric_contract"]["allowed_runtime_apply"] is False
    )
    assert contract["metric_role"] == "sim_probe_ev"
    assert contract["sample_floor_behavior"] == "hold_sample"
    assert "time_hard_gate" in contract["forbidden_uses"]
    assert "real_canary_approval_standalone" in contract["forbidden_uses"]
    assert "volatile_symbol_exclusion" in contract["forbidden_uses"]
    assert analysis["runtime_effect"] is False
    assert analysis["allowed_runtime_apply"] is False
    assert stop_rows["wick_stop_recovered_close_above_stop"]["sample_count"] == 5
    assert stop_rows["close_below_stop"]["sample_count"] == 1
    assert opportunity_rows["pullback_retest_observation"]["sample_count"] == 5
    assert opportunity_rows["invalidation_observation"]["sample_count"] == 1


def test_ev_report_clean_baseline_filters_pre_baseline_discovery_rows(tmp_path):
    db_url, Session = _setup_test_db()
    with Session.begin() as session:
        _seed_labeled_arm(session, 1, ret=-10.0, source_date=date(2026, 5, 20))
        _seed_labeled_arm(session, 2, ret=2.0, source_date=date(2026, 6, 4))

    report = mod.build_swing_strategy_discovery_ev_report(
        "2026-06-04", db_url=db_url, lookback_days=90
    )

    assert report["summary"]["labeled_sample_count"] == 1
    assert report["summary"]["candidate_count"] == 1
    assert report["clean_tuning_baseline"]["filter_active"] is True
    assert report["clean_tuning_baseline"]["requested_start_date"] == "2026-03-06"
    assert report["clean_tuning_baseline"]["effective_start_date"] == "2026-06-04"
    assert (
        "clean_tuning_baseline_swing_discovery_lookback_filtered" in report["warnings"]
    )
