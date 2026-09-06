import pytest

from src.engine.scalping import entry_recheck_drought_controller as mod
from src.engine.scalping.entry_ai_gate_backtest import _exclusive_report_lock


def _policy():
    return {
        "activation_triggered": True,
        "stop_triggered": False,
        "stop_reasons": [],
        "desired_enabled": True,
        "allowed_scopes": ["KRX|KRX_REGULAR", "NXT|NXT_AFTERMARKET"],
        "intraday_escalation_allowed": True,
        "intraday_escalation_scopes": ["KRX|KRX_REGULAR"],
        "history": [
            {"source_date": day} for day in ("2026-09-02", "2026-09-03", "2026-09-04")
        ],
        "exact_post_apply_attribution": {
            "runtime_acceptance_state": "economics_evaluable",
            "top_evaluation_reason": (
                "edge_wait_recovery_probe_intent_fresh_strong_micro"
            ),
            "exact_evaluated_count": 30,
            "exact_armed_count": 20,
            "exact_direct_submitted_count": 12,
            "exact_filled_count": 11,
            "exact_completed_count": 10,
            "exact_paired_economic_sample": 10,
            "equal_weight_avg_profit_pct": 0.04,
            "realized_net_pnl_krw": 120,
        },
    }


def _candidate():
    return {
        "family": "entry_opportunity_recheck_runtime",
        "calibration_state": "adjust_up",
        "allowed_runtime_apply": True,
        "quality_update_id": "entry-recheck-1",
        "runtime_update_mode": "drought_triggered_bounded_live",
        "cumulative_quality_window": {
            "window_policy": "rolling_3_trading_days",
            "start_date": "2026-09-02",
            "end_date": "2026-09-04",
            "clean_tuning_baseline_date": "2026-06-05",
            "source_date_count": 3,
            "source_dates": ["2026-09-02", "2026-09-03", "2026-09-04"],
        },
    }


def test_daily_controller_owns_runtime_candidate_without_cumulative_score_sweep(
    monkeypatch,
):
    monkeypatch.setattr(
        mod,
        "clean_baseline_policy",
        lambda: {"clean_tuning_baseline_date": "2026-06-05"},
    )
    monkeypatch.setattr(mod, "_drought_conditional_policy", lambda **kwargs: _policy())
    monkeypatch.setattr(
        mod, "_entry_recheck_drought_candidate", lambda **kwargs: [_candidate()]
    )
    monkeypatch.setattr(
        mod,
        "load_source_quality_preflight",
        lambda day: {"status": "pass", "tuning_input_allowed": True},
    )

    report = mod.build_report("2026-09-04")

    assert report["report_type"] == "entry_recheck_drought_controller"
    assert report["diagnostic_apply_ready"] is False
    assert report["source_quality_gate"] == "pass"
    assert report["runtime_candidate_ready"] is True
    assert report["allowed_runtime_apply"] is True
    assert report["runtime_update_contract"]["allowed_runtime_apply_count"] == 1
    assert report["summary"]["intraday_escalation_scopes"] == ["KRX|KRX_REGULAR"]
    assert "policy_results" not in report


def test_daily_controller_recomputes_top_level_ready_after_source_quality_block(
    monkeypatch,
):
    monkeypatch.setattr(
        mod,
        "clean_baseline_policy",
        lambda: {"clean_tuning_baseline_date": "2026-06-05"},
    )
    monkeypatch.setattr(mod, "_drought_conditional_policy", lambda **kwargs: _policy())
    monkeypatch.setattr(
        mod, "_entry_recheck_drought_candidate", lambda **kwargs: [_candidate()]
    )
    monkeypatch.setattr(
        mod,
        "load_source_quality_preflight",
        lambda day: {
            "status": "fail",
            "tuning_input_allowed": False,
            "source_quality_gate": "blocked_contract_gap",
        },
    )

    report = mod.build_report("2026-09-04")

    assert report["status"] == "source_quality_blocked"
    assert report["runtime_candidate_ready"] is False
    assert report["allowed_runtime_apply"] is False
    assert report["runtime_update_contract"]["allowed_runtime_apply_count"] == 0


def test_same_target_report_lock_rejects_a_second_producer(tmp_path):
    with _exclusive_report_lock(tmp_path, "entry_recheck", "2026-09-04"):
        with pytest.raises(RuntimeError, match="already running"):
            with _exclusive_report_lock(tmp_path, "entry_recheck", "2026-09-04"):
                pass


def test_markdown_exposes_scope_stop_and_separate_fill_quality():
    policy = _policy()
    policy["scope_decisions"] = {
        "NXT|NXT_AFTERMARKET": {
            "desired_enabled": False,
            "intraday_escalation_allowed": False,
            "stop_reasons": ["exact_economics_nonpositive"],
            "controller_state": {"evidence_start_date": "2026-09-07"},
        }
    }
    policy["exact_post_apply_attribution"]["paired_economics_by_scope_and_cohort"] = {
        "NXT|NXT_AFTERMARKET": {
            "scale_in_mixed": {
                "paired_sample": 10,
                "equal_weight_avg_profit_pct": 1.0,
                "realized_net_pnl_krw": 1000,
                "decision_eligible": False,
            }
        }
    }
    rendered = mod.render_markdown({"drought_conditional_policy": policy})
    assert (
        "NXT/NXT_AFTERMARKET | False | False | exact_economics_nonpositive" in rendered
    )
    assert "scale_in_mixed | 10 | 1.0 | 1000 | False" in rendered
