# Threshold Cycle Postclose Verification - 2026-05-26

- status: `not_yet_due`
- latest_start_marker: `-`
- latest_done_marker: `-`
- predecessor_status: `not_yet_due`
- predecessor_wait_count: `0`
- predecessor_timeout_count: `0`
- log_issues: `['buy_funnel_submit_drought_handoff_missing']`

## Execution Profile
- profile_status: `full_profile`
- disabled_stage_flags: `[]`
- missing_required_flags: `[]`
- interpretation: `latest START marker has no matching DONE marker`
- missing_required_artifacts: `['threshold_cycle_ev', 'scalp_entry_action_decision_matrix', 'lifecycle_decision_matrix', 'runtime_approval_summary', 'pattern_lab_currentness_audit', 'pattern_lab_propagation_audit', 'swing_daily_simulation', 'swing_lifecycle_audit', 'next_stage2_checklist']`
- missing_downstream_links: `['threshold_cycle_ev_sources_workorder', 'runtime_approval_summary_sources_ev', 'threshold_cycle_ev_sources_pattern_lab_currentness_audit', 'threshold_cycle_ev_sources_pattern_lab_propagation_audit', 'threshold_cycle_ev_sources_scalp_entry_action_decision_matrix', 'threshold_cycle_ev_sources_lifecycle_decision_matrix', 'runtime_approval_summary_sources_scalp_entry_action_decision_matrix', 'runtime_approval_summary_sources_lifecycle_decision_matrix', 'runtime_approval_summary_sources_pattern_lab_propagation_audit']`
- stale_downstream_links: `[]`
- runtime_apply_gap_issues: `[]`

## Runtime Apply Gap Audit
- status: `missing`
- retry_queue_count: `0`
- codex_directive_count: `0`
- summary: `{}`

## BUY Funnel Submit Drought Handoff
- status: `fail`
- critical: `True`
- missing: `['ldm_submit_bucket_attribution_missing', 'threshold_cycle_ev_buy_funnel_sentinel_missing', 'threshold_cycle_ev_entry_submit_drought_handoff_missing', 'runtime_approval_summary_buy_funnel_sentinel_missing', 'runtime_approval_summary_entry_submit_drought_handoff_missing']`

## Submit Bucket Handoff
- status: `missing`
- attribution_present: `False`
- missing: `[]`

## AI Correction
- status: `missing`
- ai_status: `missing`
- provider_status: `-`
- blocking_runtime_candidate_families: `[]`
- parse_warnings: `[]`
- interpretation: `AI correction artifact missing or unreadable`

## Scalp Sim Overnight
- status: `pass`
- decision_target: `23`
- active_undecided_count: `0`
- decision_coverage_rate: `None`
- source_quality_status: `pass`
- source_quality_warnings: `[]`
- interpretation: `scalp sim overnight preclose decisions covered active sim positions`

## Entry Bucket Handoff
- status: `pass`
- expected_candidate_ids: `[]`
- missing_ev_candidate_ids: `[]`
- missing_runtime_summary_candidate_ids: `[]`
- missing_workorder_order_ids: `[]`
- interpretation: `LDM entry bucket candidates and workorders propagated to threshold EV, runtime summary, and code workorder.`

## Scale-In Bucket Handoff
- attribution_present: `False`
- source_present: `False`
- status: `pass`
- expected_candidate_ids: `[]`
- missing_ev_candidate_ids: `[]`
- missing_runtime_summary_candidate_ids: `[]`
- missing_workorder_order_ids: `[]`
- interpretation: `LDM scale-in bucket candidates and workorders propagated to threshold EV, runtime summary, and code workorder.`

## Overnight Bucket Handoff
- attribution_present: `False`
- source_present: `False`
- status: `pass`
- expected_candidate_ids: `[]`
- missing_ev_candidate_ids: `[]`
- missing_runtime_summary_candidate_ids: `[]`
- missing_workorder_order_ids: `[]`
- interpretation: `LDM overnight bucket candidates and workorders propagated to threshold EV, runtime summary, and code workorder.`

## Lifecycle Bucket Discovery Handoff
- status: `missing`
- source_contract_status: `-`
- ai_two_pass_review_status: `-`
- expected_candidate_ids: `[]`
- live_auto_apply_families: `[]`
- missing_bridge_families: `[]`
- missing_runtime_summary_candidate_ids: `[]`
- workorder_needed_bucket_ids: `[]`
- ai_post_apply_followup_bucket_ids: `[]`
- warnings: `[]`
- interpretation: `lifecycle bucket discovery report missing`

## Swing Lifecycle Handoff
- status: `missing`
- expected_candidate_ids: `[]`
- missing_ev_candidate_ids: `[]`
- missing_runtime_summary_candidate_ids: `[]`
- missing_workorder_order_ids: `[]`
- daily_simulation_consumed: `False`
- interpretation: `Swing LDM report missing`

## Producer Gap Discovery Handoff
- status: `pass`
- ai_two_pass_review_status: `parsed`
- audit_status: `pass`
- expected_workorder_order_ids: `['order_producer_gap_discovery_producer_gap_limit_up_plateau_breakdown_exit_missing', 'order_producer_gap_discovery_producer_gap_sim_entry_selection_gap_missing', 'order_producer_gap_discovery_producer_gap_sim_exit_plateau_breakdown_gap_missing', 'order_producer_gap_discovery_producer_gap_sim_holding_runner_gap_missing', 'order_producer_gap_discovery_producer_gap_sim_stop_recovery_gap_missing', 'order_producer_gap_discovery_producer_gap_volatile_runner_exit_counterfactual_missing']`
- missing_workorder_order_ids: `[]`
- missing: `[]`
- interpretation: `producer gap high-priority orders propagated to code improvement workorder with parsed AI review`

## Bottom Rebound Sim Handoff
- status: `missing`
- included: `False`
- source_rows: `0`
- selected_candidate_count: `0`
- arm_count: `0`
- persisted_candidate_count: `0`
- persisted_arm_count: `0`
- missing: `['swing_strategy_discovery_sim_missing']`
- interpretation: `swing_strategy_discovery_sim artifact missing`

## Workorder Snapshot
- generation_id: `2026-05-26-50884f69a2c9`
- source_hash: `50884f69a2c9a224ac94236ed524d60c159ff2b9517d393eb1124faf35948c5d`
- snapshot_status: `same_snapshot_replay`
- previous_generation_id: `2026-05-26-50884f69a2c9`
- previous_source_hash: `50884f69a2c9a224ac94236ed524d60c159ff2b9517d393eb1124faf35948c5d`
- new_order_ids: `[]`
- removed_order_ids: `[]`
- decision_changed_order_ids: `[]`
