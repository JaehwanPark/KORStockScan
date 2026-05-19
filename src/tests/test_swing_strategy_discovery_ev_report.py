import json
from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.models import (
    SwingStrategyDiscoveryArm,
    SwingStrategyDiscoveryCandidate,
    SwingStrategyDiscoveryLabel,
)
from src.engine import swing_strategy_discovery_ev_report as mod
from src.engine.swing_strategy_discovery_schema import ensure_swing_strategy_discovery_schema


def _seed_labeled_arm(session, idx: int, *, ret: float, selection_arm="lifecycle_rank"):
    candidate = SwingStrategyDiscoveryCandidate(
        source_date=date(2026, 5, 1),
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
        source_date=date(2026, 5, 1),
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
            source_date=date(2026, 5, 1),
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
            label_features=json.dumps({"fill_status": "entered"}),
        )
    )


def test_ev_report_aggregates_surviving_arms_and_contract(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'ev.db'}"
    ensure_swing_strategy_discovery_schema(db_url)
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    with Session.begin() as session:
        for idx, ret in enumerate([1.0, 2.0, 1.5, 0.5, 3.0, -0.2], start=1):
            _seed_labeled_arm(session, idx, ret=ret)
        _seed_labeled_arm(session, 20, ret=-2.0, selection_arm="legacy_ml")

    report = mod.build_swing_strategy_discovery_ev_report("2026-05-20", db_url=db_url, lookback_days=30)

    assert report["runtime_effect"] is False
    assert report["source_only"] is True
    assert report["decision_authority"] == "swing_sim_exploration_only"
    assert report["summary"]["labeled_sample_count"] == 7
    assert report["summary"]["surviving_arm_count"] >= 1
    assert report["surviving_arms"][0]["arm_id"] == "arm01_next_open_equal_fixed5d"
    assert report["legacy_vs_discovery"]["discovery_combined"]["sample_count"] == 6
