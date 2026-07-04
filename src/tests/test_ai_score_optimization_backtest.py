import json

import pytest

from src.engine.scalping import ai_score_optimization_backtest as mod


@pytest.fixture(autouse=True)
def _source_quality_preflight_pass(monkeypatch, tmp_path):
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "threshold_cycle_ev")
    monkeypatch.setattr(
        mod,
        "load_source_quality_preflight",
        lambda target_date: {
            "status": "pass",
            "tuning_input_allowed": True,
            "allowed_runtime_apply": True,
            "source_quality_gate": "pass",
            "clean_baseline_enforced": True,
        },
    )


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_ai_score_optimization_keeps_score_only_entry_diagnostic_only(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "ENTRY_AI_GATE_BACKTEST_DIR", tmp_path / "entry_ai_gate_backtest")
    monkeypatch.setattr(
        mod,
        "RISING_MISSED_FIRST_TOUCH_CALIBRATION_DIR",
        tmp_path / "rising_missed_first_touch_calibration",
    )
    monkeypatch.setattr(
        mod,
        "SCALPING_PYRAMID_QUALITY_CALIBRATION_DIR",
        tmp_path / "scalping_pyramid_quality_calibration",
    )
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", tmp_path / "pipeline_events")

    _write_json(
        mod.ENTRY_AI_GATE_BACKTEST_DIR / "entry_ai_gate_backtest_2026-07-03.json",
        {
            "target_date": "2026-07-03",
            "summary": {"realized_joined_rows": 140, "counterfactual_rows": 278},
            "best_apply_candidate": {},
            "best_positive_realized_diagnostic_candidate": {
                "policy": "diagnostic_score_only",
                "threshold": 69,
                "realized": {"source_quality_adjusted_ev_pct": 0.45, "sample": 46},
                "counterfactual": {"missed_upside_close_10m_pct": 1.2, "sample": 24},
                "sample_floor_passed": False,
            },
        },
    )

    report = mod.build_report("2026-07-03", start_date="2026-07-03", end_date="2026-07-03")

    assert report["allowed_runtime_apply"] is False
    assert report["calibration_candidates"] == []
    assert report["diagnostic_only_candidates"][0]["apply_block_reason"] == "diagnostic_score_only"
    coverage = report["summary"]["backtest_coverage_status"]
    assert coverage["analyze_target_entry"]["status"] == "backtested"
    assert coverage["entry_price"]["status"] == "source_only_instrumentation_gap"
    assert coverage["holding_score_v2"]["status"] == "source_only_instrumentation_gap"
    assert coverage["holding_flow"]["status"] == "source_only_instrumentation_gap"


def test_ai_score_optimization_reads_entry_price_threshold_ev_source_only(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "ENTRY_AI_GATE_BACKTEST_DIR", tmp_path / "entry_ai_gate_backtest")
    monkeypatch.setattr(
        mod,
        "RISING_MISSED_FIRST_TOUCH_CALIBRATION_DIR",
        tmp_path / "rising_missed_first_touch_calibration",
    )
    monkeypatch.setattr(
        mod,
        "SCALPING_PYRAMID_QUALITY_CALIBRATION_DIR",
        tmp_path / "scalping_pyramid_quality_calibration",
    )
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", tmp_path / "pipeline_events")

    _write_json(
        mod.THRESHOLD_CYCLE_EV_DIR / "threshold_cycle_ev_2026-07-03.json",
        {
            "calibration_outcome": {
                "decisions": [
                    {
                        "family": "dynamic_entry_price_resolver",
                        "calibration_state": "hold_sample",
                        "source_metrics": {
                            "candidate_metrics_ready": True,
                            "candidate_metrics_missing": {},
                            "candidate_quality": {
                                "AI_candidate": {
                                    "candidate_event_count": 10,
                                    "candidate_failure_count": 2,
                                    "candidate_failure_rate": 20.0,
                                    "failure_reasons": {"above_best_ask": 2},
                                }
                            },
                            "unpriced_or_stale_warning_count": 1,
                            "excluded_from_fill_ev_count": 1,
                        },
                    },
                    {
                        "family": "entry_price_execution_quality",
                        "calibration_state": "hold",
                        "source_metrics": {},
                    },
                ]
            }
        },
    )

    report = mod.build_report("2026-07-03", start_date="2026-07-03", end_date="2026-07-03")

    coverage = report["summary"]["backtest_coverage_status"]["entry_price"]
    assert coverage["status"] == "source_only_backtested"
    assert coverage["producer"] == "threshold_cycle_ev.dynamic_entry_price_resolver"
    assert coverage["allowed_runtime_apply"] is False
    assert coverage["ai_candidate_event_count"] == 10
    assert coverage["ai_candidate_failure_count"] == 2
    assert coverage["unpriced_or_stale_warning_count"] == 1
    source_surface = report["surface_summaries"]["source_only_surfaces"][0]
    assert source_surface["surface"] == "entry_price"
    assert source_surface["status"] == "source_only_backtested"
    assert "entry_price_env_apply_from_ai_score_optimization" in source_surface["forbidden_uses"]


def test_ai_score_optimization_reads_holding_exit_threshold_ev_source_only(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "ENTRY_AI_GATE_BACKTEST_DIR", tmp_path / "entry_ai_gate_backtest")
    monkeypatch.setattr(
        mod,
        "RISING_MISSED_FIRST_TOUCH_CALIBRATION_DIR",
        tmp_path / "rising_missed_first_touch_calibration",
    )
    monkeypatch.setattr(
        mod,
        "SCALPING_PYRAMID_QUALITY_CALIBRATION_DIR",
        tmp_path / "scalping_pyramid_quality_calibration",
    )
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", tmp_path / "pipeline_events")

    _write_json(
        mod.THRESHOLD_CYCLE_EV_DIR / "threshold_cycle_ev_2026-07-03.json",
        {
            "calibration_outcome": {
                "decisions": [
                    {
                        "family": "soft_stop_whipsaw_confirmation",
                        "calibration_state": "hold_sample",
                        "source_metrics": {
                            "holding_exit_observation_total": 12,
                            "post_sell_joined_count": 8,
                        },
                    },
                    {
                        "family": "holding_flow_ofi_smoothing",
                        "calibration_state": "hold_sample",
                        "source_metrics": {
                            "holding_flow_override_defer_exit": 3,
                            "holding_flow_override_force_exit": 1,
                            "holding_flow_override_exit_confirmed": 2,
                        },
                    },
                    {
                        "family": "holding_exit_decision_matrix_advisory",
                        "calibration_state": "hold_no_edge",
                        "source_metrics": {
                            "counterfactual_ready_count": 5,
                            "counterfactual_gap_count": 2,
                        },
                    },
                ]
            }
        },
    )

    report = mod.build_report("2026-07-03", start_date="2026-07-03", end_date="2026-07-03")

    coverage = report["summary"]["backtest_coverage_status"]
    assert coverage["holding_score_v2"]["status"] == "source_only_backtested"
    assert coverage["holding_flow"]["producer"] == "threshold_cycle_ev.holding_exit_families"
    assert coverage["holding_flow"]["allowed_runtime_apply"] is False
    assert coverage["holding_flow"]["auto_apply_family_scope"] == []
    assert "soft_stop_whipsaw_confirmation" in coverage["holding_flow"]["threshold_ev_mapped_family_scope"]
    assert coverage["holding_flow"]["holding_flow_defer_exit_count"] == 3
    assert "negative_exit_from_unusable_ai_score" in coverage["holding_score_v2"]["forbidden_uses"]
    holding_surface = next(
        item
        for item in report["surface_summaries"]["source_only_surfaces"]
        if item["surface"] == "holding_exit"
    )
    assert holding_surface["status"] == "source_only_backtested"
    assert "holding_flow_ofi_smoothing" in holding_surface["threshold_ev_families_present"]


def test_ai_score_optimization_reads_general_scale_in_threshold_ev_source_only(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "ENTRY_AI_GATE_BACKTEST_DIR", tmp_path / "entry_ai_gate_backtest")
    monkeypatch.setattr(
        mod,
        "RISING_MISSED_FIRST_TOUCH_CALIBRATION_DIR",
        tmp_path / "rising_missed_first_touch_calibration",
    )
    monkeypatch.setattr(
        mod,
        "SCALPING_PYRAMID_QUALITY_CALIBRATION_DIR",
        tmp_path / "scalping_pyramid_quality_calibration",
    )
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", tmp_path / "pipeline_events")

    _write_json(
        mod.THRESHOLD_CYCLE_EV_DIR / "threshold_cycle_ev_2026-07-03.json",
        {
            "calibration_outcome": {
                "decisions": [
                    {
                        "family": "scale_in_price_guard",
                        "calibration_state": "hold",
                        "source_metrics": {
                            "avg_down_wait": 4,
                            "pyramid_wait": 6,
                            "scale_in_price_guard_block": 2,
                            "scale_in_price_resolved": 7,
                        },
                    }
                ]
            }
        },
    )

    report = mod.build_report("2026-07-03", start_date="2026-07-03", end_date="2026-07-03")

    coverage = report["summary"]["backtest_coverage_status"]["general_avg_down_reversal_add"]
    assert coverage["status"] == "source_only_backtested"
    assert coverage["producer"] == "threshold_cycle_ev.scale_in_price_guard"
    assert coverage["allowed_runtime_apply"] is False
    assert coverage["avg_down_wait_count"] == 4
    assert "avg_down_env_apply_without_dedicated_calibration" in coverage["forbidden_uses"]
    scale_surface = next(
        item
        for item in report["surface_summaries"]["source_only_surfaces"]
        if item["surface"] == "general_avg_down_reversal_add"
    )
    assert scale_surface["status"] == "source_only_backtested"


def test_ai_score_optimization_preserves_existing_scale_in_candidates(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "ENTRY_AI_GATE_BACKTEST_DIR", tmp_path / "entry_ai_gate_backtest")
    monkeypatch.setattr(
        mod,
        "RISING_MISSED_FIRST_TOUCH_CALIBRATION_DIR",
        tmp_path / "rising_missed_first_touch_calibration",
    )
    monkeypatch.setattr(
        mod,
        "SCALPING_PYRAMID_QUALITY_CALIBRATION_DIR",
        tmp_path / "scalping_pyramid_quality_calibration",
    )
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", tmp_path / "pipeline_events")

    _write_json(
        mod.RISING_MISSED_FIRST_TOUCH_CALIBRATION_DIR
        / "rising_missed_first_touch_calibration_2026-07-03.json",
        {
            "calibration_candidates": [
                {
                    "family": "rising_missed_first_touch_avgdown_decision_gate",
                    "stage": "scale_in",
                    "priority": 38,
                    "calibration_state": "adjust_up",
                    "allowed_runtime_apply": True,
                    "sample_floor_passed": True,
                    "source_quality_gate": "pass",
                    "target_env_keys": ["SCALP_FIRST_TOUCH_AVGDOWN_MIN_AI_SUPPORT"],
                    "current_values": {"min_ai_support": 70},
                    "recommended_values": {"min_ai_support": 75},
                }
            ]
        },
    )
    _write_json(
        mod.SCALPING_PYRAMID_QUALITY_CALIBRATION_DIR
        / "scalping_pyramid_quality_calibration_2026-07-03.json",
        {
            "calibration_candidates": [
                {
                    "family": "scalping_pyramid_quality_gate",
                    "stage": "scale_in",
                    "priority": 39,
                    "calibration_state": "adjust_down",
                    "allowed_runtime_apply": True,
                    "sample_floor_passed": True,
                    "source_quality_gate": "pass",
                    "target_env_keys": ["SCALPING_PYRAMID_MIN_PROFIT_PCT"],
                    "current_values": {"min_profit_pct": 1.5},
                    "recommended_values": {"min_profit_pct": 1.1},
                }
            ]
        },
    )

    report = mod.build_report("2026-07-03", start_date="2026-07-03", end_date="2026-07-03")

    families = {item["family"] for item in report["calibration_candidates"]}
    assert families == {
        "rising_missed_first_touch_avgdown_decision_gate",
        "scalping_pyramid_quality_gate",
    }
    assert report["allowed_runtime_apply"] is True
    assert report["summary"]["allowed_runtime_apply_candidate_count"] == 2


def test_ai_score_optimization_blocks_pyramid_candidate_when_nested_source_quality_blocked(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "ENTRY_AI_GATE_BACKTEST_DIR", tmp_path / "entry_ai_gate_backtest")
    monkeypatch.setattr(
        mod,
        "RISING_MISSED_FIRST_TOUCH_CALIBRATION_DIR",
        tmp_path / "rising_missed_first_touch_calibration",
    )
    monkeypatch.setattr(
        mod,
        "SCALPING_PYRAMID_QUALITY_CALIBRATION_DIR",
        tmp_path / "scalping_pyramid_quality_calibration",
    )
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", tmp_path / "pipeline_events")

    _write_json(
        mod.SCALPING_PYRAMID_QUALITY_CALIBRATION_DIR
        / "scalping_pyramid_quality_calibration_2026-07-03.json",
        {
            "source_quality": {"status": "micro_vwap_provenance_unusable"},
            "calibration_candidates": [
                {
                    "family": "scalping_pyramid_quality_gate",
                    "stage": "scale_in",
                    "priority": 39,
                    "calibration_state": "adjust_down",
                    "allowed_runtime_apply": True,
                    "sample_floor_passed": True,
                    "source_quality_gate": "pass",
                    "target_env_keys": ["SCALPING_PYRAMID_MIN_PROFIT_PCT"],
                    "current_values": {"min_profit_pct": 1.5},
                    "recommended_values": {"min_profit_pct": 1.1},
                }
            ],
        },
    )

    report = mod.build_report("2026-07-03", start_date="2026-07-03", end_date="2026-07-03")
    candidate = report["calibration_candidates"][0]

    assert report["allowed_runtime_apply"] is False
    assert candidate["allowed_runtime_apply"] is False
    assert candidate["source_quality_gate"] == "source_quality_blocked"
    assert candidate["apply_block_reason"] == "source_quality_blocked"


def test_ai_score_optimization_can_emit_entry_recheck_candidate(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "ENTRY_AI_GATE_BACKTEST_DIR", tmp_path / "entry_ai_gate_backtest")
    monkeypatch.setattr(
        mod,
        "RISING_MISSED_FIRST_TOUCH_CALIBRATION_DIR",
        tmp_path / "rising_missed_first_touch_calibration",
    )
    monkeypatch.setattr(
        mod,
        "SCALPING_PYRAMID_QUALITY_CALIBRATION_DIR",
        tmp_path / "scalping_pyramid_quality_calibration",
    )
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", tmp_path / "pipeline_events")

    _write_json(
        mod.ENTRY_AI_GATE_BACKTEST_DIR / "entry_ai_gate_backtest_2026-07-03.json",
        {
            "target_date": "2026-07-03",
            "best_apply_candidate": {
                "policy": "supported_wait_recovery",
                "threshold": 68,
                "sample_floor_passed": True,
                "allowed_runtime_apply": True,
                "realized": {"source_quality_adjusted_ev_pct": 0.22, "sample": 35},
                "counterfactual": {"missed_upside_close_10m_pct": 0.9, "sample": 120},
            },
        },
    )

    report = mod.build_report("2026-07-03", start_date="2026-07-03", end_date="2026-07-03")
    candidate = report["calibration_candidates"][0]

    assert candidate["family"] == "entry_opportunity_recheck_runtime"
    assert candidate["allowed_runtime_apply"] is True
    assert candidate["recommended_values"]["min_ai_score"] == 68
    assert "broad_buy_score_threshold_relaxation" in candidate["forbidden_uses"]


def test_ai_score_optimization_blocks_entry_candidate_when_source_report_blocked(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "ENTRY_AI_GATE_BACKTEST_DIR", tmp_path / "entry_ai_gate_backtest")
    monkeypatch.setattr(
        mod,
        "RISING_MISSED_FIRST_TOUCH_CALIBRATION_DIR",
        tmp_path / "rising_missed_first_touch_calibration",
    )
    monkeypatch.setattr(
        mod,
        "SCALPING_PYRAMID_QUALITY_CALIBRATION_DIR",
        tmp_path / "scalping_pyramid_quality_calibration",
    )
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", tmp_path / "pipeline_events")

    _write_json(
        mod.ENTRY_AI_GATE_BACKTEST_DIR / "entry_ai_gate_backtest_2026-07-03.json",
        {
            "target_date": "2026-07-03",
            "source_quality_gate": "source_quality_blocked",
            "best_apply_candidate": {
                "policy": "supported_wait_recovery",
                "threshold": 68,
                "sample_floor_passed": True,
                "allowed_runtime_apply": True,
                "realized": {"source_quality_adjusted_ev_pct": 0.22, "sample": 35},
                "counterfactual": {"missed_upside_close_10m_pct": 0.9, "sample": 120},
            },
        },
    )

    report = mod.build_report("2026-07-03", start_date="2026-07-03", end_date="2026-07-03")
    candidate = report["calibration_candidates"][0]

    assert report["allowed_runtime_apply"] is False
    assert report["summary"]["allowed_runtime_apply_candidate_count"] == 0
    assert candidate["allowed_runtime_apply"] is False
    assert candidate["source_quality_gate"] == "source_quality_blocked"
    assert candidate["apply_block_reason"] == "source_quality_blocked"


def test_ai_score_optimization_blocks_entry_candidate_when_primary_ev_non_positive(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "ENTRY_AI_GATE_BACKTEST_DIR", tmp_path / "entry_ai_gate_backtest")
    monkeypatch.setattr(
        mod,
        "RISING_MISSED_FIRST_TOUCH_CALIBRATION_DIR",
        tmp_path / "rising_missed_first_touch_calibration",
    )
    monkeypatch.setattr(
        mod,
        "SCALPING_PYRAMID_QUALITY_CALIBRATION_DIR",
        tmp_path / "scalping_pyramid_quality_calibration",
    )
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", tmp_path / "pipeline_events")

    _write_json(
        mod.ENTRY_AI_GATE_BACKTEST_DIR / "entry_ai_gate_backtest_2026-07-03.json",
        {
            "target_date": "2026-07-03",
            "best_apply_candidate": {
                "policy": "supported_wait_recovery",
                "threshold": 68,
                "sample_floor_passed": True,
                "allowed_runtime_apply": True,
                "realized": {"source_quality_adjusted_ev_pct": 0.0, "sample": 35},
                "counterfactual": {"missed_upside_close_10m_pct": 0.9, "sample": 120},
            },
        },
    )

    report = mod.build_report("2026-07-03", start_date="2026-07-03", end_date="2026-07-03")
    candidate = report["calibration_candidates"][0]

    assert report["allowed_runtime_apply"] is False
    assert report["summary"]["allowed_runtime_apply_candidate_count"] == 0
    assert candidate["allowed_runtime_apply"] is False
    assert candidate["primary_ev_positive"] is False
    assert candidate["apply_block_reason"] == "non_positive_primary_ev"


def test_ai_score_optimization_source_quality_preflight_blocks_candidates(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "ENTRY_AI_GATE_BACKTEST_DIR", tmp_path / "entry_ai_gate_backtest")
    monkeypatch.setattr(
        mod,
        "RISING_MISSED_FIRST_TOUCH_CALIBRATION_DIR",
        tmp_path / "rising_missed_first_touch_calibration",
    )
    monkeypatch.setattr(
        mod,
        "SCALPING_PYRAMID_QUALITY_CALIBRATION_DIR",
        tmp_path / "scalping_pyramid_quality_calibration",
    )
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", tmp_path / "pipeline_events")
    monkeypatch.setattr(
        mod,
        "load_source_quality_preflight",
        lambda target_date: {
            "status": "fail",
            "tuning_input_allowed": False,
            "allowed_runtime_apply": False,
            "source_quality_gate": "blocked_contract_gap",
            "blocked_reason": "raw_row_exclusion_missing",
            "hard_blocking_contract_gap_count": 3,
            "clean_baseline_enforced": True,
        },
    )
    _write_json(
        mod.ENTRY_AI_GATE_BACKTEST_DIR / "entry_ai_gate_backtest_2026-07-03.json",
        {
            "target_date": "2026-07-03",
            "best_apply_candidate": {
                "policy": "supported_wait_recovery",
                "threshold": 68,
                "sample_floor_passed": True,
                "allowed_runtime_apply": True,
                "realized": {"source_quality_adjusted_ev_pct": 0.22, "sample": 35},
                "counterfactual": {"missed_upside_close_10m_pct": 0.9, "sample": 120},
            },
        },
    )

    report = mod.build_report("2026-07-03", start_date="2026-07-03", end_date="2026-07-03")

    assert report["status"] == "source_quality_blocked"
    assert report["allowed_runtime_apply"] is False
    assert report["calibration_state"] == "source_quality_blocked"
    assert report["source_quality_gate"] == "blocked_contract_gap"
    assert report["summary"]["calibration_state"] == "source_quality_blocked"
    assert report["summary"]["allowed_runtime_apply_candidate_count"] == 0
    assert report["calibration_candidates"][0]["allowed_runtime_apply"] is False
