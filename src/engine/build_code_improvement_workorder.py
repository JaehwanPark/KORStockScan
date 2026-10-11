"""Retired compatibility CLI for documented historical invocations.

Active callers have moved to their role owners. Remove this surface when the
remaining historical command references are retired by the document owner.
"""

import json
from src.engine.lifecycle.retirement import retired_status
from src.engine.lifecycle.archive.build_code_improvement_workorder_compat_paths import (
    buy_funnel_sentinel_report_path,
    code_improvement_workorder_paths,
    conversion_lane_report_path,
    entry_hurdle_backtest_report_path,
    intraday_entry_blocker_diagnostics_report_path,
    intraday_ws_freshness_monitor_report_path,
    lifecycle_decision_matrix_report_path,
    microstructure_reaction_context_report_path,
    pattern_lab_ai_review_report_path,
    pattern_lab_currentness_audit_report_path,
    producer_gap_discovery_report_path,
    rising_missed_classifier_prior_report_path,
    stage_hook_runtime_scaffold_report_path,
    stage_hook_workorder_discovery_report_path,
    swing_automation_report_path,
    swing_lifecycle_bucket_discovery_report_path,
    swing_lifecycle_decision_matrix_report_path,
    swing_pattern_lab_automation_report_path,
    swing_strategy_discovery_ev_report_path,
    threshold_ev_report_path,
)
from src.engine.lifecycle.archive.build_code_improvement_workorder_readers import (
    ClassifiedOrder,
    WorkorderSourceChanged,
    _SOURCE_READS,
    _buy_funnel_sentinel_followup_orders,
    _classify_order,
    _closed_instrumentation_order_families,
    _conversion_lane_followup_orders,
    _direct_family_order,
    _entry_split_order_plan_followup_orders,
    _entry_submit_drought_implementation_marker,
    _escalate_repeated_unresolved_orders,
    _file_fingerprint,
    _generation_fingerprint,
    _intraday_ws_freshness_followup_orders,
    _is_swing_scoped_order,
    _lifecycle_bucket_discovery_followup_orders,
    _lifecycle_entry_bucket_order_id,
    _load_json,
    _load_market_census_source,
    _load_prompt_research_source,
    _load_source_json,
    _market_census_followup_orders,
    _observation_source_quality_followup_orders,
    _panic_lifecycle_followup_orders,
    _pipeline_event_verbosity_followup_orders,
    _previous_workorder_lineage,
    _sanitize_producer_gap_order,
    _scale_in_split_order_plan_followup_orders,
    _scanner_lookup_attention_economic_evidence,
    _serialize_classified_order,
    _sim_fill_and_match_report_contract_orders,
    _sort_classified,
    _source_fingerprint,
    _swing_ldm_order_id,
    _swing_lifecycle_bucket_discovery_followup_orders,
    _swing_lifecycle_matrix_followup_orders,
    code_improvement_workorder_paths,
    threshold_ev_report_path,
)


def build_code_improvement_workorder(*args, **kwargs):
    return retired_status("build_code_improvement_workorder")


def render_code_improvement_workorder_markdown(*args, **kwargs):
    return retired_status("build_code_improvement_workorder")


def main(argv=None):
    print(json.dumps(retired_status("build_code_improvement_workorder")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
