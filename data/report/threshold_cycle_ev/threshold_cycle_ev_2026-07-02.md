# Threshold Cycle Daily EV Report - 2026-07-02

## Summary
- status: `warning`
- warning_count: `11`
- source_quality: status=`pass` allowed=`True`
- samples real/sim: `19` / `159`
- live_auto_ready_count: `0`
- primary_verdict: `sim_evidence_present_no_live_bucket`

## Runtime Apply
- status: `auto_bounded_live_ready`
- runtime_change: `True`
- selected_families: `score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, profit_stagnation_exit_runtime, latency_spread_relief_real_operator_override, quote_consistency_normalization, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, ai_watching_score_smoothing_report_only, lifecycle_decision_matrix_runtime, weak_pullback_entry_block_runtime, early_accel_recheck_runtime, real_pyramid_scale_in_quality_guard_runtime, sell_side_open_time_block_runtime, pre_submit_liquidity_relief_runtime, weak_context_late_entry_guard_runtime, persistent_operator_overrides_2026_06_26`

## Daily EV
- completed: `19` / open: `1`
- win/loss: `11` / `6` (`57.89`%)
- avg_profit_rate: `0.43`%
- realized_pnl_krw: `-106273`
- full_fill_completed_avg_profit_rate: `0.633`%

## Entry Funnel
- budget_pass_to_submitted: `39` / `298` (`13.09`%)
- latency pass/block: `48` / `250`
- latency submit routing: `latency_classifier_runtime_semantics_gap`
- latency recommended action: `reject` (`recovery_count=0 below floor=37`)
- latency profile generation: `{'mode': 'grid_quantile_search', 'profile_count': 720, 'age_cap_ms': 1500, 'jitter_cap_ms': 1500, 'spread_cap_ratio': 0.012, 'counterfactual_sample_floor': 3, 'recovery_event_floor_ratio': 0.1}`
- safe/caution_normal/recovery: `1` / `0` / `0`
- recovery attempts/cf sample/cf ev: `0` / `0` / `None`%
- recovered/lost labels: `0` / `0`
- stale/broker override excluded: `0` / `0`
- full/partial fill: `18` / `0`

## Holding Exit
- holding_reviews: `1305`
- exit_signals: `759`
- holding_review_ms_p95: `1890.0`

## Scalp Simulator
- authority: `equal_weight` / fill_policy: `signal_inclusive_best_ask_v1`
- armed/filled/sold: `100` / `100` / `21`
- expired/unpriced/duplicate: `0` / `0` / `23`
- entry_ai_price applied/skip: `90` / `0`
- submit_revalidation warning/block: `3` / `0`
- scale_in filled/unfilled: `1` / `8`
- overnight decision/sell/hold/carry_restored: `1` / `1` / `0` / `0`
- completed_profit_summary: `{'sample': 21, 'win_count': 5, 'loss_count': 16, 'avg_profit_rate': -2.5795, 'median_profit_rate': -3.34, 'downside_p10_profit_rate': -5.13, 'upside_p90_profit_rate': 1.3, 'win_rate': 0.2381, 'loss_rate': 0.7619, 'stddev_profit_rate': 2.7504}`
- post_sell_join: joined=`20` / pending=`1`
- post_sell_mfe_mae_10m: mfe=`2.718`% / mae=`-7.1113`% / close=`0.4314`%

## Missed Probe Counterfactual
- book: `scalp_score65_74_probe_counterfactual` / role: `missed_buy_probe_counterfactual`
- total/score65_74: `13` / `0`
- avg_expected_ev: `2.2003`% / score65_74_avg_expected_ev: `0.0`%
- actual_order_submitted: `False` / broker_order_forbidden: `True`
- authority: `missed_probe_ev_only_not_broker_execution`

## Scalp Entry ADM
- artifact: `/home/ubuntu/KORStockScan/data/report/scalp_entry_action_decision_matrix/scalp_entry_action_decision_matrix_2026-07-02.json`
- status: `warning` / authority: `entry_advisory_prompt_context_only`
- total/joined/floor: `277` / `18` / `20`
- prompt_applied_count: `171`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 277}`
- forced_action_counts: `{'-': 277}`
- missing_actions: `[]`
- zero_sample_actions: `['SKIP_SOURCE_QUALITY']`
- top_actions: `[{'action': 'BUY_NOW', 'sample_count': 19, 'joined_sample': 2, 'source_quality_adjusted_ev_pct': -0.1516}, {'action': 'WAIT_REQUOTE', 'sample_count': 3, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'SKIP_STALE', 'sample_count': 5, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'BUY_DEFENSIVE', 'sample_count': 39, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'NO_BUY_AI', 'sample_count': 180, 'joined_sample': 7, 'source_quality_adjusted_ev_pct': -0.1423}]`

## Lifecycle Decision Matrix
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-07-02.json`
- status: `pass` / version: `lifecycle_decision_matrix_v1_2026-07-02`
- total/joined: `6662` / `3366`
- policy_pass/promote_ready: `5` / `0`
- lifecycle_flow buckets/complete/runtime/workorders: `77` / `9` / `0` / `20`
- holding/exit buckets: `18` / `38`
- holding/exit workorders: `7` / `10`
- lifecycle identity missing/join_rate: `0` / `1.0`
- lifecycle complete_flow_rate: `0.0014`
- incomplete_flow_reason_counts: `{'missing_exit': 3383, 'missing_entry': 6087, 'missing_holding': 6210, 'missing_submit': 6184, 'postclose_exit_without_entry': 2863, 'candidate_id_only': 6083, 'sim_record_id_only': 66, 'scale_in_noise_only': 3208}`
- fixed_threshold_roles: `{'hard_safety': ['broker_submit_guard', 'stale_quote_submit_block', 'price_freshness_guard', 'hard_stop', 'protect_stop', 'emergency_stop', 'account_order_cooldown_qty_guard'], 'baseline_prior': ['BUY_SCORE_THRESHOLD', 'VPW_MIN_SCORE', 'strength_momentum_cutoff', 'entry_score_cutoff'], 'bounded_tunable': ['SCALP_ENTRY_LATENCY_MAX_WS_AGE_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_WS_JITTER_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_SPREAD_RATIO_FOR_CAUTION', 'score65_74_recovery_probe', 'soft_stop_whipsaw_confirmation', 'holding_flow_override', 'scale_in_price_guard'], 'legacy_archive': ['fallback_scout_main', 'fallback_single', 'latency_fallback_split_entry', 'legacy_latency_composite', 'closed_shadow_axes']}`
- policy_entries: `[{'stage': 'entry', 'sample': 286, 'joined_sample': 17, 'stage_ev_composite_pct': 1.2343, 'confidence': 0.101, 'selected_action': 'BUY_DEFENSIVE', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'submit', 'sample': 142, 'joined_sample': 19, 'stage_ev_composite_pct': -0.9002, 'confidence': 0.2542, 'selected_action': 'NO_CHANGE', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'holding', 'sample': 101, 'joined_sample': 19, 'stage_ev_composite_pct': -1.7701, 'confidence': 0.3574, 'selected_action': 'EXIT', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'scale_in', 'sample': 3257, 'joined_sample': 3238, 'stage_ev_composite_pct': -0.7308, 'confidence': 1.0, 'selected_action': 'NO_CHANGE', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'exit', 'sample': 2876, 'joined_sample': 73, 'stage_ev_composite_pct': -1.1566, 'confidence': 0.1853, 'selected_action': 'EXIT', 'source_quality_gate': 'pass', 'promote_ready': False}]`

## Lifecycle Bucket Discovery
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-07-02.json`
- status: `pass` / human_intervention_required: `False`
- candidates/surfaced: `500` / `82`
- sim_auto/live_auto/new_bucket: `1` / `0` / `0`
- role/window: `new_pattern_detection` / `same_day_source_bundle_plus_rolling_threshold_cycle_consumer`
- parent_count/granularity/conflict: `43` / `target_pass` / `2`
- positive_parent/sample_ready/conflict: `4` / `1` / `1`
- active_positive_seed/nonpositive_seed: `5` / `0`
- positive_sim_auto/nonpositive_sim_auto: `6` / `0`
- state_counts: `{'source_only_keep_collecting': 494, 'lifecycle_flow_sim_probe_candidate': 1, 'sim_auto_approved': 1, 'entry_only_sim_auto_approved': 4}`
- top_surfaced: `[{'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 2720, 'source_quality_adjusted_ev_pct': -0.9518}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_pyramid_', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 469, 'source_quality_adjusted_ev_pct': 0.5635}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 46, 'source_quality_adjusted_ev_pct': -1.0143}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait6579_ev_cohort_stale_fresh_or_unflagged_', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 11, 'source_quality_adjusted_ev_pct': 0.7047}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_none_exit_ex', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 3, 'source_quality_adjusted_ev_pct': -1.4367}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_source_order_bundle_submitted_revalidatio', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 2, 'source_quality_adjusted_ev_pct': -2.1328}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_source_order_bundle_submitted_revalidatio', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 2, 'source_quality_adjusted_ev_pct': 0.8157}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_pyramid_', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 2, 'source_quality_adjusted_ev_pct': 0.655}]`
- top_sample_ready_positive_parent_buckets: `[{'parent_bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_mid_recovery|entry_source_parent=entry_source_wait6579|submit_quality_parent=submit_missing|exit_outcome_parent=exit_missing|major_holding_parent=holding_missing|scale_in_parent=scale_in_none', 'parent_ev_pct': 1.437567, 'parent_joined_sample': 12, 'complete_flow_count': 0, 'parent_granularity_floor_passed': True, 'child_conflict_warning': True, 'entry_score_parent': 'score_mid_recovery', 'entry_source_parent': 'entry_source_wait6579', 'submit_quality_parent': 'submit_missing', 'exit_outcome_parent': 'exit_missing', 'major_holding_parent': 'holding_missing', 'scale_in_parent': 'scale_in_none'}]`
- top_active_positive_seeds: `[{'active_seed_id': 'active_seed_7cf1c198fc1e5246', 'parent_ev_pct': 1.437567, 'parent_joined_sample': 12, 'complete_flow_count': 0, 'observable_prefix': {'entry_score_parent': 'score_mid_recovery', 'entry_source_parent': 'entry_source_wait6579'}, 'active_collection_reason': 'previous_active_first_fail_grace', 'live_conversion_blocked_reason': 'incomplete_lifecycle_flow', 'positive_ev_stage_sampling_plan': {'schema_version': 'positive_ev_stage_sampling_plan_v1', 'sampling_scope': 'positive_ev_parent_stage_completion', 'sample_goal_per_bucket': 10, 'complete_flow_goal_per_bucket': 5, 'current_parent_joined_sample': 12, 'current_complete_flow_count': 0, 'additional_parent_sample_needed': 0, 'additional_complete_flow_needed': 5, 'runtime_match_fields': {'entry_score_parent': 'score_mid_recovery', 'entry_source_parent': 'entry_source_wait6579'}, 'runtime_match_forbidden_fields': ['exit_outcome_parent', 'major_holding_parent', 'scale_in_parent'], 'stage_targets': [{'stage': 'entry', 'goal': 'revisit_positive_prefix_candidates', 'match_role': 'runtime_observable_prefix'}, {'stage': 'submit', 'goal': 'preserve_pre_submit_guard_verdict_and_revalidation', 'match_role': 'runtime_observable_prefix_when_available'}, {'stage': 'holding', 'goal': 'attach_holding_outcome_to_candidate_identity', 'match_role': 'post_observation_validation_only'}, {'stage': 'exit', 'goal': 'attach_exit_outcome_to_candidate_identity', 'match_role': 'post_observation_validation_only'}, {'stage': 'scale_in', 'goal': 'separate_none_avg_down_pyramid_observation', 'match_role': 'post_observation_validation_only'}], 'priority_reason': 'eligible_positive_parent_needs_complete_flow', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}, 'child_conflict_stratified_targets': {'schema_version': 'child_conflict_stratified_sampling_v1', 'enabled': False, 'sample_goal_per_conflict_child': 5, 'strata': [], 'resolution_policy': 'collect_until_child_floor_before_exclusion_or_live_authority', 'runtime_match_fields': {'entry_score_parent': 'score_mid_recovery', 'entry_source_parent': 'entry_source_wait6579'}, 'post_observation_dimensions_only': ['holding', 'exit', 'scale_in', 'profit'], 'runtime_consumption_allowed': False, 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}, 'stage_counterfactual_variant_count': 5}, {'active_seed_id': 'active_seed_f8f167383fabb79f', 'parent_ev_pct': 0.984067, 'parent_joined_sample': 3, 'complete_flow_count': 3, 'observable_prefix': {'entry_score_parent': 'score_watch_recovery', 'entry_source_parent': 'entry_source_action_decision', 'submit_quality_parent': 'submit_stale_context_or_quote'}, 'active_collection_reason': 'positive_ev_parent_active_sim_collection', 'live_conversion_blocked_reason': '', 'positive_ev_stage_sampling_plan': {'schema_version': 'positive_ev_stage_sampling_plan_v1', 'sampling_scope': 'positive_ev_parent_stage_completion', 'sample_goal_per_bucket': 10, 'complete_flow_goal_per_bucket': 5, 'current_parent_joined_sample': 3, 'current_complete_flow_count': 3, 'additional_parent_sample_needed': 7, 'additional_complete_flow_needed': 2, 'runtime_match_fields': {'entry_score_parent': 'score_watch_recovery', 'entry_source_parent': 'entry_source_action_decision', 'submit_quality_parent': 'submit_stale_context_or_quote'}, 'runtime_match_forbidden_fields': ['exit_outcome_parent', 'major_holding_parent', 'scale_in_parent'], 'stage_targets': [{'stage': 'entry', 'goal': 'revisit_positive_prefix_candidates', 'match_role': 'runtime_observable_prefix'}, {'stage': 'submit', 'goal': 'preserve_pre_submit_guard_verdict_and_revalidation', 'match_role': 'runtime_observable_prefix_when_available'}, {'stage': 'holding', 'goal': 'attach_holding_outcome_to_candidate_identity', 'match_role': 'post_observation_validation_only'}, {'stage': 'exit', 'goal': 'attach_exit_outcome_to_candidate_identity', 'match_role': 'post_observation_validation_only'}, {'stage': 'scale_in', 'goal': 'separate_none_avg_down_pyramid_observation', 'match_role': 'post_observation_validation_only'}], 'priority_reason': 'eligible_positive_parent_needs_complete_flow', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}, 'child_conflict_stratified_targets': {'schema_version': 'child_conflict_stratified_sampling_v1', 'enabled': False, 'sample_goal_per_conflict_child': 5, 'strata': [], 'resolution_policy': 'collect_until_child_floor_before_exclusion_or_live_authority', 'runtime_match_fields': {'entry_score_parent': 'score_watch_recovery', 'entry_source_parent': 'entry_source_action_decision', 'submit_quality_parent': 'submit_stale_context_or_quote'}, 'post_observation_dimensions_only': ['holding', 'exit', 'scale_in', 'profit'], 'runtime_consumption_allowed': False, 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}, 'stage_counterfactual_variant_count': 5}, {'active_seed_id': 'active_seed_78255c0d6b91747b', 'parent_ev_pct': 0.0712, 'parent_joined_sample': 3, 'complete_flow_count': 3, 'observable_prefix': {'entry_score_parent': 'score_mid_recovery', 'entry_source_parent': 'entry_source_action_decision', 'submit_quality_parent': 'submit_revalidation_ok'}, 'active_collection_reason': 'previous_active_first_fail_grace', 'live_conversion_blocked_reason': '', 'positive_ev_stage_sampling_plan': {'schema_version': 'positive_ev_stage_sampling_plan_v1', 'sampling_scope': 'positive_ev_parent_stage_completion', 'sample_goal_per_bucket': 10, 'complete_flow_goal_per_bucket': 5, 'current_parent_joined_sample': 3, 'current_complete_flow_count': 3, 'additional_parent_sample_needed': 7, 'additional_complete_flow_needed': 2, 'runtime_match_fields': {'entry_score_parent': 'score_mid_recovery', 'entry_source_parent': 'entry_source_action_decision', 'submit_quality_parent': 'submit_revalidation_ok'}, 'runtime_match_forbidden_fields': ['exit_outcome_parent', 'major_holding_parent', 'scale_in_parent'], 'stage_targets': [{'stage': 'entry', 'goal': 'revisit_positive_prefix_candidates', 'match_role': 'runtime_observable_prefix'}, {'stage': 'submit', 'goal': 'preserve_pre_submit_guard_verdict_and_revalidation', 'match_role': 'runtime_observable_prefix_when_available'}, {'stage': 'holding', 'goal': 'attach_holding_outcome_to_candidate_identity', 'match_role': 'post_observation_validation_only'}, {'stage': 'exit', 'goal': 'attach_exit_outcome_to_candidate_identity', 'match_role': 'post_observation_validation_only'}, {'stage': 'scale_in', 'goal': 'separate_none_avg_down_pyramid_observation', 'match_role': 'post_observation_validation_only'}], 'priority_reason': 'eligible_positive_parent_needs_complete_flow', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}, 'child_conflict_stratified_targets': {'schema_version': 'child_conflict_stratified_sampling_v1', 'enabled': True, 'sample_goal_per_conflict_child': 5, 'strata': [{'child_bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_s', 'child_bucket_key': 'entry=entry:combo_entry_spot:score_score_70p_source_scalp_entry_action_decision_snapshot_stale_stale_not_available_liquidity_|submit=submit:combo_submit_quality:source_order_bundle_submitted_revalidation_ok_or_unflagged_quote_age_quote_age_1_3s_liquidity_li|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_lt_neg070_held_held_not_applicable_at|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_missed_upside_profit_profit_lt_', 'current_joined_sample': 1, 'sample_goal': 5, 'additional_sample_needed': 4, 'source_quality_adjusted_ev_pct': -1.265, 'collection_role': 'conflict_child_stratum', 'runtime_consumption_allowed': False, 'post_observation_validation_only': True}], 'resolution_policy': 'collect_until_child_floor_before_exclusion_or_live_authority', 'runtime_match_fields': {'entry_score_parent': 'score_mid_recovery', 'entry_source_parent': 'entry_source_action_decision', 'submit_quality_parent': 'submit_revalidation_ok'}, 'post_observation_dimensions_only': ['holding', 'exit', 'scale_in', 'profit'], 'runtime_consumption_allowed': False, 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}, 'stage_counterfactual_variant_count': 5}, {'active_seed_id': 'active_seed_f59dd84c7dcc89c1', 'parent_ev_pct': 0.79005, 'parent_joined_sample': 2, 'complete_flow_count': 2, 'observable_prefix': {'entry_score_parent': 'score_mid_recovery', 'entry_source_parent': 'entry_source_action_decision', 'submit_quality_parent': 'submit_stale_context_or_quote'}, 'active_collection_reason': 'previous_active_first_fail_grace', 'live_conversion_blocked_reason': '', 'positive_ev_stage_sampling_plan': {'schema_version': 'positive_ev_stage_sampling_plan_v1', 'sampling_scope': 'positive_ev_parent_stage_completion', 'sample_goal_per_bucket': 10, 'complete_flow_goal_per_bucket': 5, 'current_parent_joined_sample': 2, 'current_complete_flow_count': 2, 'additional_parent_sample_needed': 8, 'additional_complete_flow_needed': 3, 'runtime_match_fields': {'entry_score_parent': 'score_mid_recovery', 'entry_source_parent': 'entry_source_action_decision', 'submit_quality_parent': 'submit_stale_context_or_quote'}, 'runtime_match_forbidden_fields': ['exit_outcome_parent', 'major_holding_parent', 'scale_in_parent'], 'stage_targets': [{'stage': 'entry', 'goal': 'revisit_positive_prefix_candidates', 'match_role': 'runtime_observable_prefix'}, {'stage': 'submit', 'goal': 'preserve_pre_submit_guard_verdict_and_revalidation', 'match_role': 'runtime_observable_prefix_when_available'}, {'stage': 'holding', 'goal': 'attach_holding_outcome_to_candidate_identity', 'match_role': 'post_observation_validation_only'}, {'stage': 'exit', 'goal': 'attach_exit_outcome_to_candidate_identity', 'match_role': 'post_observation_validation_only'}, {'stage': 'scale_in', 'goal': 'separate_none_avg_down_pyramid_observation', 'match_role': 'post_observation_validation_only'}], 'priority_reason': 'eligible_positive_parent_needs_complete_flow', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}, 'child_conflict_stratified_targets': {'schema_version': 'child_conflict_stratified_sampling_v1', 'enabled': False, 'sample_goal_per_conflict_child': 5, 'strata': [], 'resolution_policy': 'collect_until_child_floor_before_exclusion_or_live_authority', 'runtime_match_fields': {'entry_score_parent': 'score_mid_recovery', 'entry_source_parent': 'entry_source_action_decision', 'submit_quality_parent': 'submit_stale_context_or_quote'}, 'post_observation_dimensions_only': ['holding', 'exit', 'scale_in', 'profit'], 'runtime_consumption_allowed': False, 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}, 'stage_counterfactual_variant_count': 5}, {'active_seed_id': 'active_seed_b99a2dea7aac2a83', 'parent_ev_pct': 0.0041, 'parent_joined_sample': 1, 'complete_flow_count': 0, 'observable_prefix': {'entry_score_parent': 'score_watch_recovery', 'entry_source_parent': 'entry_source_wait6579'}, 'active_collection_reason': 'previous_active_first_fail_grace', 'live_conversion_blocked_reason': 'incomplete_lifecycle_flow', 'positive_ev_stage_sampling_plan': {'schema_version': 'positive_ev_stage_sampling_plan_v1', 'sampling_scope': 'positive_ev_parent_stage_completion', 'sample_goal_per_bucket': 10, 'complete_flow_goal_per_bucket': 5, 'current_parent_joined_sample': 1, 'current_complete_flow_count': 0, 'additional_parent_sample_needed': 9, 'additional_complete_flow_needed': 5, 'runtime_match_fields': {'entry_score_parent': 'score_watch_recovery', 'entry_source_parent': 'entry_source_wait6579'}, 'runtime_match_forbidden_fields': ['exit_outcome_parent', 'major_holding_parent', 'scale_in_parent'], 'stage_targets': [{'stage': 'entry', 'goal': 'revisit_positive_prefix_candidates', 'match_role': 'runtime_observable_prefix'}, {'stage': 'submit', 'goal': 'preserve_pre_submit_guard_verdict_and_revalidation', 'match_role': 'runtime_observable_prefix_when_available'}, {'stage': 'holding', 'goal': 'attach_holding_outcome_to_candidate_identity', 'match_role': 'post_observation_validation_only'}, {'stage': 'exit', 'goal': 'attach_exit_outcome_to_candidate_identity', 'match_role': 'post_observation_validation_only'}, {'stage': 'scale_in', 'goal': 'separate_none_avg_down_pyramid_observation', 'match_role': 'post_observation_validation_only'}], 'priority_reason': 'eligible_positive_parent_needs_complete_flow', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}, 'child_conflict_stratified_targets': {'schema_version': 'child_conflict_stratified_sampling_v1', 'enabled': False, 'sample_goal_per_conflict_child': 5, 'strata': [], 'resolution_policy': 'collect_until_child_floor_before_exclusion_or_live_authority', 'runtime_match_fields': {'entry_score_parent': 'score_watch_recovery', 'entry_source_parent': 'entry_source_wait6579'}, 'post_observation_dimensions_only': ['holding', 'exit', 'scale_in', 'profit'], 'runtime_consumption_allowed': False, 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}, 'stage_counterfactual_variant_count': 5}]`
- top_positive_sim_auto_approved: `[{'bucket_id': 'entry:strength_bucket:strong_strength_momentum', 'classification_state': 'entry_only_sim_auto_approved', 'stage': 'entry', 'bucket_type': 'strength_bucket', 'source_quality_adjusted_ev_pct': 1.7483, 'joined_sample': 11, 'sample': 40}, {'bucket_id': 'entry:chosen_action:wait_requote', 'classification_state': 'entry_only_sim_auto_approved', 'stage': 'entry', 'bucket_type': 'chosen_action', 'source_quality_adjusted_ev_pct': 1.3273, 'joined_sample': 13, 'sample': 14}, {'bucket_id': 'entry:source_stage:wait6579_ev_cohort', 'classification_state': 'sim_auto_approved', 'stage': 'entry', 'bucket_type': 'source_stage', 'source_quality_adjusted_ev_pct': 1.3273, 'joined_sample': 13, 'sample': 13}, {'bucket_id': 'entry:liquidity_bucket:liquidity_high', 'classification_state': 'entry_only_sim_auto_approved', 'stage': 'entry', 'bucket_type': 'liquidity_bucket', 'source_quality_adjusted_ev_pct': 1.2343, 'joined_sample': 17, 'sample': 184}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'classification_state': 'lifecycle_flow_sim_probe_candidate', 'stage': 'lifecycle_flow', 'bucket_type': 'combo_lifecycle_flow', 'source_quality_adjusted_ev_pct': 0.8991, 'joined_sample': 1, 'sample': 1}, {'bucket_id': 'entry:overbought_bucket:overbought_normal', 'classification_state': 'entry_only_sim_auto_approved', 'stage': 'entry', 'bucket_type': 'overbought_bucket', 'source_quality_adjusted_ev_pct': 0.7224, 'joined_sample': 15, 'sample': 168}]`
- top_nonpositive_sim_auto_approved: `[]`

## Lifecycle Bucket Windows
- promotion_window: `mtd`
- confirmation_windows: `['rolling5d', 'rolling10d']`
- windows: `{'rolling5d': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-07-02_rolling5d.json', 'window_role': 'rolling_confirmation', 'window_policy': 'rolling5d', 'status': 'pass', 'parent_bucket_count': 35, 'selected_parent_level': 'L1_broad', 'parent_granularity_status': 'target_pass', 'absorbed_child_count': 188, 'absorbed_sample_count': 25816, 'child_conflict_warning_count': 9, 'positive_parent_count': 10, 'positive_parent_sample_ready_count': 2, 'positive_parent_conflict_count': 1, 'top_sample_ready_positive_parent_buckets': [{'parent_bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_watch_recovery|submit_quality_parent=submit_missing|exit_outcome_parent=exit_missing', 'parent_ev_pct': 2.1866, 'parent_joined_sample': 13, 'complete_flow_count': 0, 'parent_granularity_floor_passed': True, 'child_conflict_warning': False, 'entry_score_parent': 'score_watch_recovery', 'entry_source_parent': 'entry_source_wait6579', 'submit_quality_parent': 'submit_missing', 'exit_outcome_parent': 'exit_missing', 'major_holding_parent': 'holding_missing', 'scale_in_parent': 'scale_in_none'}, {'parent_bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_mid_recovery|submit_quality_parent=submit_missing|exit_outcome_parent=exit_missing', 'parent_ev_pct': 1.337986, 'parent_joined_sample': 111, 'complete_flow_count': 0, 'parent_granularity_floor_passed': True, 'child_conflict_warning': False, 'entry_score_parent': 'score_mid_recovery', 'entry_source_parent': 'entry_source_wait6579', 'submit_quality_parent': 'submit_missing', 'exit_outcome_parent': 'exit_missing', 'major_holding_parent': 'holding_missing', 'scale_in_parent': 'scale_in_none'}], 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'parsed'}, 'rolling10d': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-07-02_rolling10d.json', 'window_role': 'rolling_confirmation', 'window_policy': 'rolling10d', 'status': 'pass', 'parent_bucket_count': 44, 'selected_parent_level': 'L1_broad', 'parent_granularity_status': 'target_pass', 'absorbed_child_count': 336, 'absorbed_sample_count': 49585, 'child_conflict_warning_count': 17, 'positive_parent_count': 8, 'positive_parent_sample_ready_count': 3, 'positive_parent_conflict_count': 3, 'top_sample_ready_positive_parent_buckets': [{'parent_bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_watch_recovery|submit_quality_parent=submit_missing|exit_outcome_parent=exit_missing', 'parent_ev_pct': 2.9796, 'parent_joined_sample': 33, 'complete_flow_count': 0, 'parent_granularity_floor_passed': True, 'child_conflict_warning': False, 'entry_score_parent': 'score_watch_recovery', 'entry_source_parent': 'entry_source_wait6579', 'submit_quality_parent': 'submit_missing', 'exit_outcome_parent': 'exit_missing', 'major_holding_parent': 'holding_missing', 'scale_in_parent': 'scale_in_none'}, {'parent_bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_mid_recovery|submit_quality_parent=submit_missing|exit_outcome_parent=exit_missing', 'parent_ev_pct': 1.422417, 'parent_joined_sample': 250, 'complete_flow_count': 0, 'parent_granularity_floor_passed': True, 'child_conflict_warning': False, 'entry_score_parent': 'score_mid_recovery', 'entry_source_parent': 'entry_source_wait6579', 'submit_quality_parent': 'submit_missing', 'exit_outcome_parent': 'exit_missing', 'major_holding_parent': 'holding_missing', 'scale_in_parent': 'scale_in_none'}, {'parent_bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_unobserved|submit_quality_parent=submit_missing|exit_outcome_parent=exit_missed_upside', 'parent_ev_pct': 0.742179, 'parent_joined_sample': 14, 'complete_flow_count': 0, 'parent_granularity_floor_passed': True, 'child_conflict_warning': True, 'entry_score_parent': 'score_unobserved', 'entry_source_parent': 'entry_source_observed_other', 'submit_quality_parent': 'submit_missing', 'exit_outcome_parent': 'exit_missed_upside', 'major_holding_parent': 'holding_missing', 'scale_in_parent': 'scale_in_none'}], 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'parsed'}, 'mtd': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-07-02_mtd.json', 'window_role': 'promotion_confirmation', 'window_policy': 'mtd', 'status': 'pass', 'parent_bucket_count': 52, 'selected_parent_level': 'L2_default', 'parent_granularity_status': 'target_pass', 'absorbed_child_count': 117, 'absorbed_sample_count': 13206, 'child_conflict_warning_count': 5, 'positive_parent_count': 4, 'positive_parent_sample_ready_count': 1, 'positive_parent_conflict_count': 1, 'top_sample_ready_positive_parent_buckets': [{'parent_bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_mid_recovery|entry_source_parent=entry_source_wait6579|submit_quality_parent=submit_missing|exit_outcome_parent=exit_missing|major_holding_parent=holding_missing|scale_in_parent=scale_in_none', 'parent_ev_pct': 2.50098, 'parent_joined_sample': 25, 'complete_flow_count': 0, 'parent_granularity_floor_passed': True, 'child_conflict_warning': True, 'entry_score_parent': 'score_mid_recovery', 'entry_source_parent': 'entry_source_wait6579', 'submit_quality_parent': 'submit_missing', 'exit_outcome_parent': 'exit_missing', 'major_holding_parent': 'holding_missing', 'scale_in_parent': 'scale_in_none'}], 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'parsed'}}`

## Lifecycle AI Context
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_ai_context/lifecycle_ai_context_2026-07-02.json`
- context_version: `lifecycle_ai_context_v1_2026-07-02` / authority: `ai_advisory_prompt_context_only`
- prompt_stage_count: `3` / runtime_effect: `False`
- stage_contexts: `[{'stage': 'entry', 'prompt_injection_allowed': True, 'policy_key': 'entry:weighted_adm_v1', 'alignment_hint': 'BUY_DEFENSIVE', 'context_contribution_score': -0.2698, 'attribution_quality_status': 'observational_only_pending_outcome'}, {'stage': 'submit', 'prompt_injection_allowed': False, 'policy_key': 'submit:weighted_adm_v1', 'alignment_hint': 'NO_CHANGE', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'holding', 'prompt_injection_allowed': True, 'policy_key': 'holding:weighted_adm_v1', 'alignment_hint': 'EXIT', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'scale_in', 'prompt_injection_allowed': False, 'policy_key': 'scale_in:weighted_adm_v1', 'alignment_hint': 'NO_CHANGE', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'exit', 'prompt_injection_allowed': True, 'policy_key': 'exit:weighted_adm_v1', 'alignment_hint': 'EXIT', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}]`

## Lifecycle AI Context Attribution
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_ai_context_attribution/lifecycle_ai_context_attribution_2026-07-02.json`
- eligible/applied/skipped: `428` / `428` / `0`
- replay_budget: `30`
- implementation_status: `implemented`
- stage_attribution: `{'entry': {'context_contribution_score': -0.2698, 'bounded_auxiliary_weight': -0.0405, 'attribution_quality_status': 'observational_only_pending_outcome', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': 0.1145, 'no_context_replay_observed': 0}, 'submit': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'holding': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'scale_in': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'exit': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}}`

## Institutional Flow Context
- artifact: `/home/ubuntu/KORStockScan/data/report/institutional_flow_context/institutional_flow_context_2026-07-02.json`
- status: `pass` / authority: `source_only_lifecycle_feature`
- rows ok/partial/missing/token_error: `120` / `0` / `0` / `0`
- join_rate_pct: `100.0`
- source_mix: `{'ka10059+ka10061': 120}`
- top_net_buy: `[{'stock_code': '252420', 'smart_money_net': 2200833, 'foreign_net_roll5': 0, 'inst_net_roll5': 2544843, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '015760', 'smart_money_net': 703149, 'foreign_net_roll5': 0, 'inst_net_roll5': 2298863, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '066570', 'smart_money_net': 495234, 'foreign_net_roll5': 399039, 'inst_net_roll5': 37599, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '073240', 'smart_money_net': 461957, 'foreign_net_roll5': 0, 'inst_net_roll5': 0, 'regime': 'UNKNOWN'}, {'stock_code': '035420', 'smart_money_net': 379059, 'foreign_net_roll5': 190320, 'inst_net_roll5': 120074, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '017670', 'smart_money_net': 369737, 'foreign_net_roll5': 262526, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}, {'stock_code': '034020', 'smart_money_net': 336674, 'foreign_net_roll5': 233514, 'inst_net_roll5': 158793, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '001210', 'smart_money_net': 324634, 'foreign_net_roll5': 0, 'inst_net_roll5': 5163, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '005380', 'smart_money_net': 296118, 'foreign_net_roll5': 0, 'inst_net_roll5': 76763, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '008770', 'smart_money_net': 165604, 'foreign_net_roll5': 71463, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}]`

## Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-07-02.json`
- fresh: gemini=`False` claude=`True`
- consensus/orders/family_candidates: `0` / `10` / `0`

## Swing Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_2026-07-02.json`
- deepseek_lab_available: `True`
- findings/orders: `5` / `3`
- data_quality_warnings: `0`
- top_level_data_quality_warnings: `0`
- resolved_data_quality_warnings: `0`
- ofi_qi_stale_missing_unique_records: `1`
- ofi_qi_stale_missing_reasons: `{'micro_missing': 0, 'micro_stale': 0, 'observer_unhealthy': 0, 'micro_not_ready': 5, 'state_insufficient': 5}`
- ofi_qi_stale_missing_reason_combinations: `{'micro_not_ready+state_insufficient': 5}`
- ofi_qi_stale_missing_reason_combination_unique_records: `{'micro_not_ready+state_insufficient': 1}`
- ofi_qi_observer_unhealthy_overlap: `{'observer_unhealthy_total': 0, 'observer_unhealthy_with_other_reason': 0, 'observer_unhealthy_only': 0}`
- source_quality_blocked_families: `[]`
- carryover_warnings: `0`
- population_split_available: `True`

## Swing Strategy Discovery Sim
- artifact: `/home/ubuntu/KORStockScan/data/report/swing_strategy_discovery_ev/swing_strategy_discovery_ev_2026-07-02.json`
- authority: `swing_sim_exploration_only` / source_only: `True`
- candidate/arm/policy_exit_rows: `1484` / `9843` / `9843`
- labeled/pending_future_quotes: `1361` / `3957`
- implementation_status: `implemented`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- surviving/avoid_bucket_count: `1` / `20`
- runtime_effect: `False`

## Pipeline Event Verbosity
- artifact: `/home/ubuntu/KORStockScan/data/report/pipeline_event_verbosity/pipeline_event_verbosity_2026-07-02.json`
- state: `v2_shadow_pending_flush`
- recommended_workorder_state: `observe_pending_next_flush`
- high_volume_line_count: `3476`
- high_volume_byte_share_pct: `2.63`
- parity_ok: `False`
- suppress_eligibility: `False`

## Codebase Performance Workorder Source
- artifact: `/home/ubuntu/KORStockScan/data/report/codebase_performance_workorder/codebase_performance_workorder_2026-07-02.json`
- authority: `ops_performance_workorder_source`
- accepted/deferred/rejected: `7` / `2` / `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`

## Pattern Lab Audits
- currentness: status=`pass` fail=`0` orders=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-07-02.json`
- ai_review: status=`pass` orders=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_ai_review/pattern_lab_ai_review_2026-07-02.json`
- time_window_regime_counterfactual: status=`pass` artifact=`/home/ubuntu/KORStockScan/data/report/time_window_regime_counterfactual/time_window_regime_counterfactual_2026-07-02.json`
- producer_gap_discovery: status=`pass` orders=`0` artifact=`/home/ubuntu/KORStockScan/data/report/producer_gap_discovery/producer_gap_discovery_2026-07-02.json`
- stage_hook_workorder_discovery: status=`warning` orders=`2` artifact=`/home/ubuntu/KORStockScan/data/report/stage_hook_workorder_discovery/stage_hook_workorder_discovery_2026-07-02.json`
- propagation: status=`warning` fail=`0` warnings=`2` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_2026-07-02.json`

## Swing Runtime Approval
- request_report: `/home/ubuntu/KORStockScan/data/report/swing_runtime_approval/swing_runtime_approval_2026-07-01.json`
- approval_artifact: `-`
- requested/approved/live_dry_run: `0` / `0` / `0`
- dry_run_forced: `False`
- legacy_phase0_real_canary_ignored: `False`
- blocked: `[]`

## Code Improvement Workorder
- artifact: `/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-02.json`
- markdown: `/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-07-02.md`
- selected_order_count: `164`
- decision_counts: `{'attach_existing_family': 152, 'design_family_candidate': 4, 'defer_evidence': 5, 'reject': 3}`

## Approval Requests
- none

## Swing Approval Requests
- none

## Calibration Decisions
## Code Improvement Top Orders
- `order_latency_canary_tag_완화_1축_canary_승인` decision=`attach_existing_family` subsystem=`runtime_instrumentation`
- `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_10_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_7508c15e` decision=`attach_existing_family` subsystem=`lifecycle_decision_matrix`
- `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_11_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_b5237a42` decision=`attach_existing_family` subsystem=`lifecycle_decision_matrix`

- `soft_stop_whipsaw_confirmation`: `hold_sample` sample=`1829/10`
- `holding_flow_ofi_smoothing`: `hold_sample` sample=`25/20`
- `protect_trailing_smoothing`: `adjust_down` sample=`30/20`
- `trailing_continuation`: `freeze` sample=`286/20`
- `market_regime_continuous_thresholds`: `hold_sample` sample=`8/10`
- `pre_submit_price_guard`: `hold` sample=`0/1`
- `dynamic_entry_price_resolver`: `hold_sample` sample=`293/20`
- `entry_price_execution_quality`: `hold` sample=`154/5`
- `score65_74_recovery_probe`: `adjust_up` sample=`124/20`
- `strength_momentum_soft_gate_p1`: `hold` sample=`4684/20`
- `overbought_pullback_guard_p1`: `hold` sample=`1132/20`
- `liquidity_pre_submit_guard_p1`: `hold` sample=`690/20`
- `bad_entry_refined_canary`: `adjust_up` sample=`44498/10`
- `holding_exit_decision_matrix_advisory`: `hold_no_edge` sample=`0/1`
- `lifecycle_decision_matrix_runtime`: `adjust_up` sample=`6662/20`
- `scale_in_price_guard`: `hold` sample=`842/20`
- `position_sizing_dynamic_formula`: `hold_sample` sample=`120/30`

## Warnings
- `scalp_entry_adm:joined_sample_below_sample_floor`
- `scalp_entry_adm:unknown_bucket_source_quality_gap`
- `scalp_entry_adm:ai_numeric_consistency_rows_excluded_from_aggregates`
- `lifecycle_bucket_discovery:source_contract_drift_warning`
- `lifecycle_bucket_discovery:source_contract_drift_warning`
- `swing_strategy_discovery:pending_future_quotes`
- `swing_strategy_discovery:clean_tuning_baseline_swing_discovery_lookback_filtered`
- `swing_lifecycle_decision_matrix:swing_intraday_live_equiv_probe_missing`
- `swing_lifecycle_decision_matrix:pending_future_quotes`
- `swing_lifecycle_decision_matrix:clean_tuning_baseline_swing_discovery_lookback_filtered`
- `pattern_lab_propagation_audit_warning`
