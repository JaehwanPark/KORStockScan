from __future__ import annotations

from src.engine.swing.bottom_rebound_candidate_source import (
    DECISION_AUTHORITY,
    CandidateSourceConfig,
    build_candidate_source_report,
    config_from_policy_auto_loop,
)


def _bottom_report() -> dict:
    return {
        "schema_version": "bottom_rebound_pattern_research_v1",
        "report_type": "bottom_rebound_pattern_research",
        "date": "2026-05-22",
        "decision_authority": "research_only",
        "runtime_effect": False,
        "broker_order_forbidden": True,
        "allowed_runtime_apply": False,
        "metric_contract": {"sample_floor": 30},
        "summary": {
            "top_primary_entry_policy": "atr_pullback_entry",
            "top_primary_source_quality_adjusted_ev_pct": 1.25,
        },
        "latest_as_of_research_only_candidates": [
            {
                "stock_code": "000001",
                "stock_name": "Alpha",
                "backtest_rank_score": 5.0,
                "vwap_distance_pct": -1.2,
                "dist_low60_pct": 2.0,
                "drawdown_high60_pct": -30.0,
                "kiwoom_sector": "Semiconductor",
                "kiwoom_theme_tags": ["AI"],
            },
            {
                "stock_code": "000002",
                "stock_name": "Beta",
                "backtest_rank_score": 2.0,
                "vwap_distance_pct": -0.4,
                "dist_low60_pct": 4.0,
            },
        ],
    }


def test_candidate_source_builds_source_only_swing_packet() -> None:
    report = build_candidate_source_report(
        bottom_report=_bottom_report(),
        config=CandidateSourceConfig(max_candidates=10, min_backtest_rank_score=3.0),
    )

    assert report["decision_authority"] == DECISION_AUTHORITY
    assert report["runtime_effect"] is False
    assert report["actual_order_submitted"] is False
    assert report["broker_order_forbidden"] is True
    assert report["allowed_runtime_apply"] is False
    assert "broker_order_submit" in report["forbidden_uses"]
    assert report["source_quality"]["contract_pass"] is True
    assert report["source_quality"]["source_candidate_count"] == 2
    assert report["source_quality"]["selected_candidate_count"] == 1
    assert len(report["candidate_rows"]) == 1
    row = report["candidate_rows"][0]
    assert row["stock_code"] == "000001"
    assert row["recommended_sim_entry_policy"] == "atr_pullback_entry"
    assert row["diagnostic_features"]["kiwoom_sector"] == "Semiconductor"
    assert row["decision_authority"] == DECISION_AUTHORITY
    assert row["runtime_effect"] is False
    assert "broker_order_submit" in row["forbidden_uses"]
    assert "recommendation_history_replacement" in row["forbidden_uses"]


def test_candidate_source_blocks_bad_research_contract() -> None:
    source = _bottom_report()
    source["runtime_effect"] = True

    report = build_candidate_source_report(bottom_report=source, config=CandidateSourceConfig())

    assert report["source_quality"]["contract_pass"] is False
    assert "source_runtime_effect_not_false" in report["source_quality"]["contract_block_reasons"]
    assert report["candidate_rows"] == []
    assert "no_bottom_rebound_candidates_selected" in report["warnings"]


def test_candidate_source_documents_feedback_loop_without_runtime_authority() -> None:
    report = build_candidate_source_report(bottom_report=_bottom_report(), config=CandidateSourceConfig())
    loop = report["scannerization_feedback_loop"]

    assert loop["state"] == "source_only_design_ready"
    assert loop["allowed_next_mutation"] == "versioned_candidate_source_config_proposal_only"
    assert "swing_strategy_discovery_labels" in loop["feedback_sources"]
    assert "broker order enablement" in loop["forbidden_automatic_mutations"]


def test_candidate_source_consumes_only_sim_auto_approved_policy() -> None:
    approved = {
        "report_type": "swing_bottom_rebound_policy_auto_loop",
        "date": "2026-05-22",
        "final_conclusion": {"classification_state": "sim_auto_approved", "promote_policy": True},
        "sim_auto_approved_policy": {
            "policy_version": "bottom_rebound_swing_source_v2",
            "max_candidates": 40,
            "min_backtest_rank_score": 2.5,
            "min_primary_adjusted_ev_pct": 0.1,
        },
    }
    control_tower = {
        "report_type": "swing_sim_auto_approval",
        "approved": True,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "approved_source_ids": ["bottom_rebound_policy_auto_loop"],
    }

    config, diagnostics = config_from_policy_auto_loop(
        approved,
        require_sim_auto_approved=True,
        control_tower_approval=control_tower,
    )

    assert diagnostics["approved"] is True
    assert diagnostics["control_tower_approved"] is True
    assert config.policy_version == "bottom_rebound_swing_source_v2"
    assert config.max_candidates == 40
    assert config.min_backtest_rank_score == 2.5


def test_candidate_source_blocks_policy_without_control_tower_approval() -> None:
    approved = {
        "report_type": "swing_bottom_rebound_policy_auto_loop",
        "date": "2026-05-22",
        "final_conclusion": {"classification_state": "sim_auto_approved", "promote_policy": True},
        "sim_auto_approved_policy": {
            "policy_version": "bottom_rebound_swing_source_v2",
            "max_candidates": 40,
            "min_backtest_rank_score": 2.5,
            "min_primary_adjusted_ev_pct": 0.1,
        },
    }

    config, diagnostics = config_from_policy_auto_loop(approved, require_sim_auto_approved=True)

    assert diagnostics["block_reason"] == "control_tower_sim_auto_approval_missing"
    assert diagnostics["policy_approved"] is True
    assert diagnostics["control_tower_approved"] is False
    assert config.max_candidates == 0


def test_candidate_source_blocks_policy_without_sim_auto_approval() -> None:
    blocked = {
        "report_type": "swing_bottom_rebound_policy_auto_loop",
        "date": "2026-05-22",
        "final_conclusion": {"classification_state": "source_only_keep_collecting", "promote_policy": False},
        "sim_auto_approved_policy": None,
    }

    config, diagnostics = config_from_policy_auto_loop(blocked, require_sim_auto_approved=True)
    report = build_candidate_source_report(
        bottom_report=_bottom_report(),
        config=config,
        policy_auto_loop=blocked,
        policy_auto_loop_diagnostics=diagnostics,
    )

    assert diagnostics["block_reason"] == "policy_not_sim_auto_approved"
    assert config.min_backtest_rank_score == 1_000_000_000.0
    assert report["candidate_rows"] == []
    assert "policy_not_sim_auto_approved" in report["warnings"]
