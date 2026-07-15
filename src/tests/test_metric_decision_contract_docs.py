from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read_doc(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_report_traceability_declares_metric_decision_contract():
    text = _read_doc("docs/report-based-automation-traceability.md")

    required_terms = (
        "## 2.6 Metric Decision Contract",
        "metric_role",
        "metric_definition",
        "decision_authority",
        "window_policy",
        "sample_floor",
        "primary_decision_metric",
        "secondary_diagnostics",
        "source_quality_gate",
        "runtime_effect=false",
        "forbidden_uses",
        "primary_ev",
        "diagnostic_win_rate",
        "funnel_count",
        "safety_veto",
        "source_quality_gate",
        "active_unrealized",
        "execution_quality_real_only",
        "sim_probe_ev",
        "real_only",
        "main_only_completed",
        "sim_equal_weight",
        "probe_observe_only",
        "combined_diagnostic",
        "source_quality_only",
        "counterfactual_only",
        "daily_only",
        "rolling_3d",
        "rolling_5d",
        "rolling_10d",
        "cumulative_since_owner_start",
        "post_apply_version_window",
        "same_day_intraday_light",
        "simple_sum_profit_pct",
        "equal_weight_avg_profit_pct",
        "notional_weighted_ev_pct",
        "source_quality_adjusted_ev_pct",
        "instrumentation_gap",
    )

    missing = [term for term in required_terms if term not in text]
    assert missing == []


def test_plan_rebase_points_new_observation_metrics_to_contract():
    text = _read_doc("docs/plan-korStockScanPerformanceOptimization.rebase.md")

    required_terms = (
        "diagnostic_win_rate",
        "primary_ev",
        "simple_sum_profit_pct",
        "equal_weight_avg_profit_pct",
        "decision_authority",
        "window_policy",
        "source_quality_blocker",
        "daily-only",
    )

    missing = [term for term in required_terms if term not in text]
    assert missing == []
