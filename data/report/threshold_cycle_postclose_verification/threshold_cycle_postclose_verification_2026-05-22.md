# Threshold Cycle Postclose Verification - 2026-05-22

- status: `not_yet_due`
- latest_start_marker: `-`
- latest_done_marker: `-`
- predecessor_status: `not_yet_due`
- predecessor_wait_count: `0`
- predecessor_timeout_count: `0`
- log_issues: `['ldm_scale_in_bucket_handoff_missing']`

## Execution Profile
- profile_status: `full_profile`
- disabled_stage_flags: `[]`
- missing_required_flags: `[]`
- interpretation: `latest START marker has no matching DONE marker`
- missing_required_artifacts: `['scalp_entry_action_decision_matrix', 'pattern_lab_currentness_audit', 'pattern_lab_propagation_audit', 'swing_daily_simulation', 'swing_lifecycle_audit', 'next_stage2_checklist']`
- missing_downstream_links: `['threshold_cycle_ev_sources_workorder', 'threshold_cycle_ev_sources_pattern_lab_currentness_audit', 'threshold_cycle_ev_sources_pattern_lab_propagation_audit', 'threshold_cycle_ev_sources_scalp_entry_action_decision_matrix', 'runtime_approval_summary_sources_scalp_entry_action_decision_matrix', 'runtime_approval_summary_sources_pattern_lab_propagation_audit']`

## AI Correction
- status: `missing`
- ai_status: `missing`
- provider_status: `-`
- blocking_runtime_candidate_families: `[]`
- parse_warnings: `[]`
- interpretation: `AI correction artifact missing or unreadable`

## Scalp Sim Overnight
- status: `missing`
- decision_target: `0`
- active_undecided_count: `0`
- decision_coverage_rate: `None`
- source_quality_status: `missing`
- source_quality_warnings: `[]`
- interpretation: `scalp sim overnight report was not present in this verification fixture/run`

## Entry Bucket Handoff
- status: `pass`
- expected_candidate_ids: `[]`
- missing_ev_candidate_ids: `[]`
- missing_runtime_summary_candidate_ids: `[]`
- missing_workorder_order_ids: `[]`
- interpretation: `LDM entry bucket candidates and workorders propagated to threshold EV, runtime summary, and code workorder.`

## Scale-In Bucket Handoff
- attribution_present: `True`
- source_present: `True`
- status: `fail`
- expected_candidate_ids: `['scale_in_bucket_1', 'scale_in_bucket_10', 'scale_in_bucket_2', 'scale_in_bucket_3', 'scale_in_bucket_4', 'scale_in_bucket_5', 'scale_in_bucket_6', 'scale_in_bucket_7', 'scale_in_bucket_8', 'scale_in_bucket_9']`
- missing_ev_candidate_ids: `['scale_in_bucket_1', 'scale_in_bucket_10', 'scale_in_bucket_2', 'scale_in_bucket_3', 'scale_in_bucket_4', 'scale_in_bucket_5', 'scale_in_bucket_6', 'scale_in_bucket_7', 'scale_in_bucket_8', 'scale_in_bucket_9']`
- missing_runtime_summary_candidate_ids: `[]`
- missing_workorder_order_ids: `[]`
- interpretation: `LDM scale-in bucket output was generated but one or more downstream consumers dropped it.`

## Overnight Bucket Handoff
- attribution_present: `True`
- source_present: `False`
- status: `pass`
- expected_candidate_ids: `[]`
- missing_ev_candidate_ids: `[]`
- missing_runtime_summary_candidate_ids: `[]`
- missing_workorder_order_ids: `[]`
- interpretation: `LDM overnight bucket candidates and workorders propagated to threshold EV, runtime summary, and code workorder.`

## Lifecycle Bucket Discovery Handoff
- status: `pass`
- source_contract_status: `pass`
- ai_two_pass_review_status: `disabled`
- expected_candidate_ids: `['entry:chosen_action:action_unknown', 'entry:exit_rule:exit_unknown', 'entry:liquidity_bucket:liquidity_unknown', 'entry:overbought_bucket:overbought_unknown', 'entry:source_stage:wait6579_ev_cohort', 'entry:stage_policy:entry_weighted_adm_v1', 'entry:stale_bucket:fresh_or_unflagged', 'entry:strength_bucket:strength_unknown', 'entry:time_bucket:time_unknown', 'exit:stage_policy:exit_weighted_adm_v1', 'holding:stage_policy:holding_weighted_adm_v1', 'scale_in:ai_score_source:ai_source_unknown', 'scale_in:arm:arm_unknown', 'scale_in:arm:avg_down', 'scale_in:arm:pyramid', 'scale_in:blocker_namespace:avg_down', 'scale_in:blocker_namespace:blocker_namespace_unknown', 'scale_in:blocker_namespace:pyramid', 'scale_in:blocker_reason:blocker_reason_unknown', 'scale_in:blocker_reason:hold_sec_out_of_range_1186s', 'scale_in:blocker_reason:hold_sec_out_of_range_11s', 'scale_in:blocker_reason:hold_sec_out_of_range_264s', 'scale_in:blocker_reason:hold_sec_out_of_range_7s', 'scale_in:blocker_reason:low_broken', 'scale_in:blocker_reason:ok', 'scale_in:blocker_reason:pnl_out_of_range_0_71', 'scale_in:blocker_reason:pnl_out_of_range_0_73', 'scale_in:blocker_reason:pnl_out_of_range_0_74', 'scale_in:blocker_reason:pnl_out_of_range_0_75', 'scale_in:blocker_reason:pnl_out_of_range_0_76', 'scale_in:blocker_reason:pnl_out_of_range_0_78', 'scale_in:blocker_reason:pnl_out_of_range_0_79', 'scale_in:blocker_reason:pnl_out_of_range_0_80', 'scale_in:blocker_reason:pnl_out_of_range_0_81', 'scale_in:blocker_reason:pnl_out_of_range_0_82', 'scale_in:blocker_reason:pnl_out_of_range_0_83', 'scale_in:blocker_reason:pnl_out_of_range_0_85', 'scale_in:blocker_reason:pnl_out_of_range_0_86', 'scale_in:blocker_reason:pnl_out_of_range_0_87', 'scale_in:blocker_reason:pnl_out_of_range_0_88', 'scale_in:blocker_reason:pnl_out_of_range_0_89', 'scale_in:blocker_reason:pnl_out_of_range_0_90', 'scale_in:blocker_reason:pnl_out_of_range_0_92', 'scale_in:blocker_reason:pnl_out_of_range_0_93', 'scale_in:blocker_reason:pnl_out_of_range_0_94', 'scale_in:blocker_reason:pnl_out_of_range_0_95', 'scale_in:blocker_reason:pnl_out_of_range_0_96', 'scale_in:blocker_reason:pnl_out_of_range_0_99', 'scale_in:blocker_reason:pnl_out_of_range_1_00', 'scale_in:blocker_reason:pnl_out_of_range_1_02', 'scale_in:blocker_reason:pnl_out_of_range_1_03', 'scale_in:blocker_reason:pnl_out_of_range_1_05', 'scale_in:blocker_reason:pnl_out_of_range_1_07', 'scale_in:blocker_reason:pnl_out_of_range_1_09', 'scale_in:blocker_reason:pnl_out_of_range_1_10', 'scale_in:blocker_reason:pnl_out_of_range_1_11', 'scale_in:blocker_reason:pnl_out_of_range_1_12', 'scale_in:blocker_reason:pnl_out_of_range_1_13', 'scale_in:blocker_reason:pnl_out_of_range_1_15', 'scale_in:blocker_reason:pnl_out_of_range_1_16', 'scale_in:blocker_reason:pnl_out_of_range_1_18', 'scale_in:blocker_reason:pnl_out_of_range_1_20', 'scale_in:blocker_reason:pnl_out_of_range_1_23', 'scale_in:blocker_reason:pnl_out_of_range_1_24', 'scale_in:blocker_reason:pnl_out_of_range_1_25', 'scale_in:blocker_reason:pnl_out_of_range_1_26', 'scale_in:blocker_reason:pnl_out_of_range_1_28', 'scale_in:blocker_reason:pnl_out_of_range_1_30', 'scale_in:blocker_reason:pnl_out_of_range_1_32', 'scale_in:blocker_reason:pnl_out_of_range_1_33', 'scale_in:blocker_reason:pnl_out_of_range_1_35', 'scale_in:blocker_reason:pnl_out_of_range_1_36', 'scale_in:blocker_reason:pnl_out_of_range_1_38', 'scale_in:blocker_reason:pnl_out_of_range_1_40', 'scale_in:blocker_reason:pnl_out_of_range_1_41', 'scale_in:blocker_reason:pnl_out_of_range_1_42', 'scale_in:blocker_reason:pnl_out_of_range_1_43', 'scale_in:blocker_reason:pnl_out_of_range_1_44', 'scale_in:blocker_reason:pnl_out_of_range_1_45', 'scale_in:blocker_reason:pnl_out_of_range_1_47', 'scale_in:blocker_reason:pnl_out_of_range_1_48', 'scale_in:blocker_reason:pnl_out_of_range_1_49', 'scale_in:blocker_reason:pnl_out_of_range_1_50', 'scale_in:blocker_reason:pnl_out_of_range_1_51', 'scale_in:blocker_reason:pnl_out_of_range_1_61', 'scale_in:blocker_reason:pnl_out_of_range_1_62', 'scale_in:blocker_reason:pnl_out_of_range_1_63', 'scale_in:blocker_reason:pnl_out_of_range_1_66', 'scale_in:blocker_reason:pnl_out_of_range_1_68', 'scale_in:blocker_reason:pnl_out_of_range_1_78', 'scale_in:blocker_reason:profit_not_enough', 'scale_in:blocker_reason:trend_not_strong', 'scale_in:stage_policy:scale_in_weighted_adm_v1', 'submit:stage_policy:submit_weighted_adm_v1']`
- live_auto_apply_families: `[]`
- missing_bridge_families: `[]`
- missing_runtime_summary_candidate_ids: `[]`
- workorder_needed_bucket_ids: `['entry:chosen_action:action_unknown', 'entry:exit_rule:exit_unknown', 'entry:liquidity_bucket:liquidity_unknown', 'entry:overbought_bucket:overbought_unknown', 'entry:strength_bucket:strength_unknown', 'entry:time_bucket:time_unknown', 'scale_in:ai_score_source:ai_source_unknown', 'scale_in:arm:arm_unknown', 'scale_in:blocker_namespace:blocker_namespace_unknown', 'scale_in:blocker_reason:blocker_reason_unknown']`
- ai_post_apply_followup_bucket_ids: `[]`
- warnings: `['ai_review_provider_disabled']`
- interpretation: `lifecycle bucket discovery candidates propagated to bridge/runtime summary/workorder`

## Workorder Snapshot
- generation_id: `2026-05-22-a233add9704b`
- source_hash: `a233add9704bfd96f810631e601209d7a877b36add58e6e0f3a75cb354d5172f`
- snapshot_status: `first_generation`
- previous_generation_id: `-`
- previous_source_hash: `-`
- new_order_ids: `['order_lifecycle_ai_context_attribution_feedback', 'order_lifecycle_bucket_discovery_entry_entry_chosen_action_action_unknown', 'order_lifecycle_bucket_discovery_entry_entry_exit_rule_exit_unknown', 'order_lifecycle_bucket_discovery_entry_entry_liquidity_bucket_liquidity_unknown', 'order_lifecycle_bucket_discovery_entry_entry_overbought_bucket_overbought_unknown', 'order_lifecycle_bucket_discovery_entry_entry_strength_bucket_strength_unknown', 'order_lifecycle_bucket_discovery_entry_entry_time_bucket_time_unknown', 'order_lifecycle_bucket_discovery_scale_in_scale_in_ai_score_source_ai_source_unknown', 'order_lifecycle_bucket_discovery_scale_in_scale_in_arm_arm_unknown', 'order_lifecycle_bucket_discovery_scale_in_scale_in_blocker_namespace_blocker_namespace_unknown', 'order_lifecycle_bucket_discovery_scale_in_scale_in_blocker_reason_blocker_reason_unknown', 'order_lifecycle_entry_bucket_chosen_action_action_unknown', 'order_lifecycle_entry_bucket_exit_rule_exit_unknown', 'order_lifecycle_entry_bucket_liquidity_bucket_liquidity_unknown', 'order_lifecycle_entry_bucket_overbought_bucket_overbought_unknown', 'order_lifecycle_entry_bucket_source_stage_wait6579_ev_cohort', 'order_lifecycle_entry_bucket_stale_bucket_fresh_or_unflagged', 'order_lifecycle_entry_bucket_strength_bucket_strength_unknown', 'order_lifecycle_entry_bucket_time_bucket_time_unknown', 'order_lifecycle_scale_in_bucket_arm_avg_down', 'order_lifecycle_scale_in_bucket_arm_pyramid', 'order_lifecycle_scale_in_bucket_blocker_namespace_avg_down', 'order_lifecycle_scale_in_bucket_blocker_namespace_pyramid', 'order_lifecycle_scale_in_bucket_blocker_reason_low_broken', 'order_lifecycle_scale_in_bucket_blocker_reason_pnl_out_of_range_0_76', 'order_lifecycle_scale_in_bucket_blocker_reason_pnl_out_of_range_0_82', 'order_lifecycle_scale_in_bucket_blocker_reason_pnl_out_of_range_0_90', 'order_lifecycle_scale_in_bucket_blocker_reason_pnl_out_of_range_0_96', 'order_lifecycle_scale_in_bucket_blocker_reason_profit_not_enough', 'order_scalp_entry_adm_daily_tuning_coverage']`
- removed_order_ids: `[]`
- decision_changed_order_ids: `[]`
