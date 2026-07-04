import json

from src.engine.scalping import ai_score_optimization_backtest as mod


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
