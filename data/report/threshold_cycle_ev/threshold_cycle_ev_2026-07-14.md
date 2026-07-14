# Threshold Cycle Daily EV Report - 2026-07-14

## Summary
- status: `warning`
- warning_count: `12`
- source_quality: status=`pass` allowed=`True`
- samples real/sim: `43` / `62`
- live_auto_ready_count: `0`
- primary_verdict: `real_primary_evidence_present`

## Runtime Apply
- status: `auto_bounded_live_ready`
- runtime_change: `True`
- selected_families: `soft_stop_whipsaw_confirmation, scale_in_split_order_plan, score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, profit_stagnation_exit_runtime, latency_spread_relief_real_operator_override, quote_consistency_normalization, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, ai_watching_score_smoothing_report_only, weak_pullback_entry_block_runtime, early_accel_recheck_runtime, real_pyramid_scale_in_quality_guard_runtime, sell_side_open_time_block_runtime, pre_submit_liquidity_relief_runtime, entry_opportunity_recheck_runtime, weak_context_late_entry_guard_runtime, rising_missed_normal_buy_bridge, persistent_operator_overrides_2026_06_26`

## Daily EV
- completed: `0` / open: `0`
- win/loss: `0` / `0` (`0.0`%)
- avg_profit_rate: `0.0`%
- realized_pnl_krw: `0`
- full_fill_completed_avg_profit_rate: `0.0`%

## Entry Funnel
- budget_pass_to_submitted: `0` / `0` (`0.0`%)
- latency pass/block: `0` / `0`
- latency submit routing: `latency_classifier_runtime_semantics_gap`
- latency recommended action: `reject` (`recovery_count=0 below floor=10`)
- latency profile generation: `{'mode': 'grid_quantile_search', 'profile_count': 405, 'age_cap_ms': 1500, 'jitter_cap_ms': 1500, 'spread_cap_ratio': 0.012, 'counterfactual_sample_floor': 3, 'recovery_event_floor_ratio': 0.1}`
- safe/caution_normal/recovery: `0` / `0` / `0`
- recovery attempts/cf sample/cf ev: `0` / `0` / `None`%
- recovered/lost labels: `0` / `0`
- stale/broker override excluded: `0` / `0`
- full/partial fill: `0` / `0`
- entry_split_order_plan: status=`pass` candidates=`0` policy=`entry_split_order_plan:2026-07-14:97d170e155`
- scale_in_split_order_plan: status=`pass` candidates=`1` policy=`scale_in_split_order_plan:2026-07-14:c91179494131`

## Holding Exit
- holding_reviews: `0`
- exit_signals: `0`
- holding_review_ms_p95: `0.0`

## Scalp Simulator
- authority: `equal_weight` / fill_policy: `signal_inclusive_best_ask_v1`
- armed/filled/sold: `22` / `22` / `1`
- expired/unpriced/duplicate: `0` / `0` / `17`
- entry_ai_price applied/skip: `22` / `0`
- submit_revalidation warning/block: `1` / `0`
- scale_in filled/unfilled: `0` / `0`
- overnight decision/sell/hold/carry_restored: `1` / `1` / `0` / `0`
- completed_profit_summary: `{'sample': 1, 'win_count': 0, 'loss_count': 1, 'avg_profit_rate': -1.27, 'median_profit_rate': -1.27, 'downside_p10_profit_rate': -1.27, 'upside_p90_profit_rate': -1.27, 'win_rate': 0.0, 'loss_rate': 1.0, 'stddev_profit_rate': None}`
- post_sell_join: joined=`0` / pending=`1`
- post_sell_mfe_mae_10m: mfe=`None`% / mae=`None`% / close=`None`%

## Missed Probe Counterfactual
- book: `-` / role: `-`
- total/score65_74: `None` / `None`
- avg_expected_ev: `None`% / score65_74_avg_expected_ev: `None`%
- actual_order_submitted: `None` / broker_order_forbidden: `None`
- authority: `-`

## Scalp Entry ADM
- artifact: `/home/ubuntu/KORStockScan/data/report/scalp_entry_action_decision_matrix/scalp_entry_action_decision_matrix_2026-07-14.json`
- status: `warning` / authority: `entry_advisory_prompt_context_only`
- total/joined/floor: `122` / `0` / `20`
- prompt_applied_count: `28`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 122}`
- forced_action_counts: `{'-': 122}`
- missing_actions: `[]`
- zero_sample_actions: `['BUY_NOW', 'SKIP_SOURCE_QUALITY']`
- outcome_join_diagnostic: `{'status': 'post_sell_evaluation_missing_or_empty', 'zero_join_reason': 'no_post_sell_evaluation_rows_for_target_date', 'candidate_key_count': 139, 'candidate_key_field_counts': {'candidate_id': 122, 'entry_adm_candidate_id': 0, 'sim_record_id': 9, 'record_id': 50}, 'post_sell_evaluation_rows': 0, 'post_sell_evaluation_join_keys': 0, 'candidate_post_sell_key_overlap_count': 0, 'joined_sample': 0, 'joined_sample_all_rows': 0, 'sample_floor': 20, 'sample_floor_met': False, 'decision_authority': 'source_quality_gap_discovery', 'runtime_effect': False, 'allowed_runtime_apply': False}`
- top_actions: `[{'action': 'WAIT_REQUOTE', 'sample_count': 53, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'SKIP_STALE', 'sample_count': 1, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'BUY_DEFENSIVE', 'sample_count': 8, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'NO_BUY_AI', 'sample_count': 52, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'SKIP_PRE_SUBMIT_SAFETY', 'sample_count': 8, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}]`

## Lifecycle Decision Matrix
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-07-14.json`
- status: `pass` / version: `lifecycle_decision_matrix_v1_2026-07-14`
- total/joined: `548` / `341`
- policy_pass/promote_ready: `2` / `0`
- lifecycle_flow buckets/complete/runtime/workorders: `32` / `16` / `0` / `20`
- holding/exit buckets: `11` / `19`
- holding/exit workorders: `0` / `9`
- lifecycle identity missing/join_rate: `0` / `1.0`
- lifecycle complete_flow_rate: `0.038`
- incomplete_flow_reason_counts: `{'missing_holding': 403, 'missing_exit': 372, 'missing_submit': 385, 'missing_entry': 352, 'candidate_id_only': 353, 'scale_in_noise_only': 319, 'sim_record_id_only': 18, 'postclose_exit_without_entry': 33}`
- fixed_threshold_roles: `{'hard_safety': ['broker_submit_guard', 'stale_quote_submit_block', 'price_freshness_guard', 'hard_stop', 'protect_stop', 'emergency_stop', 'account_order_cooldown_qty_guard'], 'baseline_prior': ['BUY_SCORE_THRESHOLD', 'VPW_MIN_SCORE', 'strength_momentum_cutoff', 'entry_score_cutoff'], 'bounded_tunable': ['SCALP_ENTRY_LATENCY_MAX_WS_AGE_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_WS_JITTER_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_SPREAD_RATIO_FOR_CAUTION', 'score65_74_recovery_probe', 'soft_stop_whipsaw_confirmation', 'holding_flow_override', 'scale_in_price_guard'], 'legacy_archive': ['fallback_scout_main', 'fallback_single', 'latency_fallback_split_entry', 'legacy_latency_composite', 'closed_shadow_axes']}`
- policy_entries: `[{'stage': 'entry', 'sample': 113, 'joined_sample': 0, 'stage_ev_composite_pct': None, 'confidence': 0.0, 'selected_action': 'NO_CHANGE', 'source_quality_gate': 'hold_sample', 'promote_ready': False}, {'stage': 'submit', 'sample': 41, 'joined_sample': 1, 'stage_ev_composite_pct': -1.27, 'confidence': 0.0024, 'selected_action': 'NO_CHANGE', 'source_quality_gate': 'hold_sample', 'promote_ready': False}, {'stage': 'holding', 'sample': 23, 'joined_sample': 1, 'stage_ev_composite_pct': -1.27, 'confidence': 0.0043, 'selected_action': 'EXIT', 'source_quality_gate': 'hold_sample', 'promote_ready': False}, {'stage': 'scale_in', 'sample': 320, 'joined_sample': 320, 'stage_ev_composite_pct': -1.2185, 'confidence': 1.0, 'selected_action': 'NO_CHANGE', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'exit', 'sample': 51, 'joined_sample': 19, 'stage_ev_composite_pct': -1.0549, 'confidence': 0.7078, 'selected_action': 'EXIT', 'source_quality_gate': 'pass', 'promote_ready': False}]`

## Lifecycle Bucket Discovery
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-07-14.json`
- status: `pass` / human_intervention_required: `False`
- candidates/surfaced: `307` / `47`
- sim_auto/live_auto/new_bucket: `2` / `0` / `10`
- role/window: `new_pattern_detection` / `same_day_source_bundle_plus_rolling_threshold_cycle_consumer`
- parent_count/granularity/conflict: `21` / `too_broad` / `0`
- positive_parent/sample_ready/conflict: `0` / `0` / `0`
- active_positive_seed/nonpositive_seed: `2` / `0`
- positive_sim_auto/nonpositive_sim_auto: `0` / `2`
- state_counts: `{'source_only_keep_collecting': 294, 'sim_auto_approved': 2, 'runtime_blocked_contract_gap': 1, 'new_bucket_candidate': 10}`
- top_surfaced: `[{'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 301, 'source_quality_adjusted_ev_pct': -1.2398}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 16, 'source_quality_adjusted_ev_pct': -1.0675}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_pyramid_', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 2, 'source_quality_adjusted_ev_pct': 0.115}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': -1.27}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_combo_holding_flow_source_scalp_sim_ov', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': -0.65}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_none_exit_ex', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': -1.36}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai_confirmed_stale_stale_high_liquidity_li', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 0, 'source_quality_adjusted_ev_pct': None}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai_confirmed_stale_stale_high_liquidity_li', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 0, 'source_quality_adjusted_ev_pct': None}]`
- top_sample_ready_positive_parent_buckets: `[]`
- top_active_positive_seeds: `[{'active_seed_id': 'active_seed_7cf1c198fc1e5246', 'parent_ev_pct': 0.4867, 'parent_joined_sample': 3, 'complete_flow_count': 0, 'observable_prefix': {'entry_score_parent': 'score_mid_recovery', 'entry_source_parent': 'entry_source_wait6579'}, 'active_collection_reason': 'positive_ev_parent_needs_sim_collection', 'live_conversion_blocked_reason': 'incomplete_lifecycle_flow', 'positive_ev_stage_sampling_plan': {'schema_version': 'positive_ev_stage_sampling_plan_v1', 'sampling_scope': 'positive_ev_parent_stage_completion', 'sample_goal_per_bucket': 10, 'complete_flow_goal_per_bucket': 5, 'current_parent_joined_sample': 3, 'current_complete_flow_count': 0, 'additional_parent_sample_needed': 7, 'additional_complete_flow_needed': 5, 'runtime_match_fields': {'entry_score_parent': 'score_mid_recovery', 'entry_source_parent': 'entry_source_wait6579'}, 'runtime_match_forbidden_fields': ['exit_outcome_parent', 'major_holding_parent', 'scale_in_parent'], 'stage_targets': [{'stage': 'entry', 'goal': 'revisit_positive_prefix_candidates', 'match_role': 'runtime_observable_prefix'}, {'stage': 'submit', 'goal': 'preserve_pre_submit_guard_verdict_and_revalidation', 'match_role': 'runtime_observable_prefix_when_available'}, {'stage': 'holding', 'goal': 'attach_holding_outcome_to_candidate_identity', 'match_role': 'post_observation_validation_only'}, {'stage': 'exit', 'goal': 'attach_exit_outcome_to_candidate_identity', 'match_role': 'post_observation_validation_only'}, {'stage': 'scale_in', 'goal': 'separate_none_avg_down_pyramid_observation', 'match_role': 'post_observation_validation_only'}], 'priority_reason': 'eligible_positive_parent_needs_complete_flow', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}, 'child_conflict_stratified_targets': {'schema_version': 'child_conflict_stratified_sampling_v1', 'enabled': False, 'sample_goal_per_conflict_child': 5, 'strata': [], 'resolution_policy': 'collect_until_child_floor_before_exclusion_or_live_authority', 'runtime_match_fields': {'entry_score_parent': 'score_mid_recovery', 'entry_source_parent': 'entry_source_wait6579'}, 'post_observation_dimensions_only': ['holding', 'exit', 'scale_in', 'profit'], 'runtime_consumption_allowed': False, 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}, 'stage_counterfactual_variant_count': 5}, {'active_seed_id': 'active_seed_dcd8fdaa26695704', 'parent_ev_pct': 1.1977, 'parent_joined_sample': 2, 'complete_flow_count': 2, 'observable_prefix': {'entry_score_parent': 'score_watch_recovery', 'entry_source_parent': 'entry_source_observed_other', 'submit_quality_parent': 'submit_revalidation_ok'}, 'active_collection_reason': 'positive_ev_parent_active_sim_collection', 'live_conversion_blocked_reason': '', 'positive_ev_stage_sampling_plan': {'schema_version': 'positive_ev_stage_sampling_plan_v1', 'sampling_scope': 'positive_ev_parent_stage_completion', 'sample_goal_per_bucket': 10, 'complete_flow_goal_per_bucket': 5, 'current_parent_joined_sample': 2, 'current_complete_flow_count': 2, 'additional_parent_sample_needed': 8, 'additional_complete_flow_needed': 3, 'runtime_match_fields': {'entry_score_parent': 'score_watch_recovery', 'entry_source_parent': 'entry_source_observed_other', 'submit_quality_parent': 'submit_revalidation_ok'}, 'runtime_match_forbidden_fields': ['exit_outcome_parent', 'major_holding_parent', 'scale_in_parent'], 'stage_targets': [{'stage': 'entry', 'goal': 'revisit_positive_prefix_candidates', 'match_role': 'runtime_observable_prefix'}, {'stage': 'submit', 'goal': 'preserve_pre_submit_guard_verdict_and_revalidation', 'match_role': 'runtime_observable_prefix_when_available'}, {'stage': 'holding', 'goal': 'attach_holding_outcome_to_candidate_identity', 'match_role': 'post_observation_validation_only'}, {'stage': 'exit', 'goal': 'attach_exit_outcome_to_candidate_identity', 'match_role': 'post_observation_validation_only'}, {'stage': 'scale_in', 'goal': 'separate_none_avg_down_pyramid_observation', 'match_role': 'post_observation_validation_only'}], 'priority_reason': 'eligible_positive_parent_needs_complete_flow', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}, 'child_conflict_stratified_targets': {'schema_version': 'child_conflict_stratified_sampling_v1', 'enabled': False, 'sample_goal_per_conflict_child': 5, 'strata': [], 'resolution_policy': 'collect_until_child_floor_before_exclusion_or_live_authority', 'runtime_match_fields': {'entry_score_parent': 'score_watch_recovery', 'entry_source_parent': 'entry_source_observed_other', 'submit_quality_parent': 'submit_revalidation_ok'}, 'post_observation_dimensions_only': ['holding', 'exit', 'scale_in', 'profit'], 'runtime_consumption_allowed': False, 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}, 'stage_counterfactual_variant_count': 5}]`
- top_positive_sim_auto_approved: `[]`
- top_nonpositive_sim_auto_approved: `[{'bucket_id': 'scale_in:stage_policy:scale_in_weighted_adm_v1', 'classification_state': 'sim_auto_approved', 'stage': 'scale_in', 'bucket_type': 'stage_policy', 'source_quality_adjusted_ev_pct': -1.2185, 'joined_sample': 320, 'sample': 320}, {'bucket_id': 'exit:stage_policy:exit_weighted_adm_v1', 'classification_state': 'sim_auto_approved', 'stage': 'exit', 'bucket_type': 'stage_policy', 'source_quality_adjusted_ev_pct': -1.0549, 'joined_sample': 19, 'sample': 51}]`

## Lifecycle Bucket Windows
- promotion_window: `mtd`
- confirmation_windows: `['rolling5d', 'rolling10d']`
- windows: `{'rolling5d': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-07-14_rolling5d.json', 'window_role': 'rolling_confirmation', 'window_policy': 'rolling5d', 'status': 'pass', 'parent_bucket_count': 47, 'selected_parent_level': 'L2_default', 'parent_granularity_status': 'target_pass', 'absorbed_child_count': 92, 'absorbed_sample_count': 2023, 'child_conflict_warning_count': 0, 'positive_parent_count': 3, 'positive_parent_sample_ready_count': 0, 'positive_parent_conflict_count': 0, 'top_sample_ready_positive_parent_buckets': [], 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'parsed'}, 'rolling10d': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-07-14_rolling10d.json', 'window_role': 'rolling_confirmation', 'window_policy': 'rolling10d', 'status': 'pass', 'parent_bucket_count': 31, 'selected_parent_level': 'L1_broad', 'parent_granularity_status': 'target_pass', 'absorbed_child_count': 202, 'absorbed_sample_count': 12761, 'child_conflict_warning_count': 10, 'positive_parent_count': 4, 'positive_parent_sample_ready_count': 1, 'positive_parent_conflict_count': 0, 'top_sample_ready_positive_parent_buckets': [{'parent_bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_mid_recovery|submit_quality_parent=submit_missing|exit_outcome_parent=exit_missing', 'parent_ev_pct': 0.05504, 'parent_joined_sample': 20, 'complete_flow_count': 0, 'parent_granularity_floor_passed': True, 'child_conflict_warning': False, 'entry_score_parent': 'score_mid_recovery', 'entry_source_parent': 'entry_source_wait6579', 'submit_quality_parent': 'submit_missing', 'exit_outcome_parent': 'exit_missing', 'major_holding_parent': 'holding_missing', 'scale_in_parent': 'scale_in_none'}], 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'partial'}, 'mtd': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-07-14_mtd.json', 'window_role': 'promotion_confirmation', 'window_policy': 'mtd', 'status': 'pass', 'parent_bucket_count': 36, 'selected_parent_level': 'L1_broad', 'parent_granularity_status': 'target_pass', 'absorbed_child_count': 273, 'absorbed_sample_count': 30795, 'child_conflict_warning_count': 13, 'positive_parent_count': 6, 'positive_parent_sample_ready_count': 1, 'positive_parent_conflict_count': 2, 'top_sample_ready_positive_parent_buckets': [{'parent_bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_mid_recovery|submit_quality_parent=submit_missing|exit_outcome_parent=exit_missing', 'parent_ev_pct': 1.719561, 'parent_joined_sample': 56, 'complete_flow_count': 0, 'parent_granularity_floor_passed': True, 'child_conflict_warning': True, 'entry_score_parent': 'score_mid_recovery', 'entry_source_parent': 'entry_source_wait6579', 'submit_quality_parent': 'submit_missing', 'exit_outcome_parent': 'exit_missing', 'major_holding_parent': 'holding_missing', 'scale_in_parent': 'scale_in_none'}], 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'partial'}}`

## Lifecycle AI Context
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_ai_context/lifecycle_ai_context_2026-07-14.json`
- context_version: `lifecycle_ai_context_v1_2026-07-14` / authority: `ai_advisory_prompt_context_only`
- prompt_stage_count: `3` / runtime_effect: `False`
- stage_contexts: `[{'stage': 'entry', 'prompt_injection_allowed': True, 'policy_key': 'entry:weighted_adm_v1', 'alignment_hint': 'NO_CHANGE', 'context_contribution_score': 0.1833, 'attribution_quality_status': 'observational_only_pending_outcome'}, {'stage': 'submit', 'prompt_injection_allowed': False, 'policy_key': 'submit:weighted_adm_v1', 'alignment_hint': 'NO_CHANGE', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'holding', 'prompt_injection_allowed': True, 'policy_key': 'holding:weighted_adm_v1', 'alignment_hint': 'EXIT', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'scale_in', 'prompt_injection_allowed': False, 'policy_key': 'scale_in:weighted_adm_v1', 'alignment_hint': 'NO_CHANGE', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'exit', 'prompt_injection_allowed': True, 'policy_key': 'exit:weighted_adm_v1', 'alignment_hint': 'EXIT', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}]`

## Lifecycle AI Context Attribution
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_ai_context_attribution/lifecycle_ai_context_attribution_2026-07-14.json`
- eligible/applied/skipped: `63` / `63` / `0`
- replay_budget: `30`
- implementation_status: `implemented`
- stage_attribution: `{'entry': {'context_contribution_score': 0.1833, 'bounded_auxiliary_weight': 0.0275, 'attribution_quality_status': 'observational_only_pending_outcome', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': 0.7619, 'no_context_replay_observed': 0}, 'submit': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'holding': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'scale_in': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'exit': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}}`

## Institutional Flow Context
- artifact: `/home/ubuntu/KORStockScan/data/report/institutional_flow_context/institutional_flow_context_2026-07-14.json`
- status: `pass` / authority: `source_only_lifecycle_feature`
- rows ok/partial/missing/token_error: `120` / `0` / `0` / `0`
- join_rate_pct: `100.0`
- source_mix: `{'ka10059+ka10061': 120}`
- top_net_buy: `[{'stock_code': '252670', 'smart_money_net': 589587949, 'foreign_net_roll5': 545244274, 'inst_net_roll5': -2147483648, 'regime': 'FOREIGN_ACCUMULATION'}, {'stock_code': '005930', 'smart_money_net': 7434782, 'foreign_net_roll5': 0, 'inst_net_roll5': 6763374, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '000660', 'smart_money_net': 1794838, 'foreign_net_roll5': 0, 'inst_net_roll5': 173549, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '530107', 'smart_money_net': 1138538, 'foreign_net_roll5': 0, 'inst_net_roll5': 1091152, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '252420', 'smart_money_net': 1035811, 'foreign_net_roll5': 0, 'inst_net_roll5': 6390474, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '006800', 'smart_money_net': 351439, 'foreign_net_roll5': 2201344, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}, {'stock_code': '054940', 'smart_money_net': 316003, 'foreign_net_roll5': 213313, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}, {'stock_code': '042660', 'smart_money_net': 257203, 'foreign_net_roll5': 0, 'inst_net_roll5': 378231, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '089970', 'smart_money_net': 230143, 'foreign_net_roll5': 0, 'inst_net_roll5': 1090897, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '520057', 'smart_money_net': 184219, 'foreign_net_roll5': 0, 'inst_net_roll5': 311405, 'regime': 'INSTITUTION_ACCUMULATION'}]`

## Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-07-14.json`
- fresh: gemini=`False` claude=`True`
- consensus/orders/family_candidates: `0` / `10` / `0`

## Swing Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_2026-07-14.json`
- deepseek_lab_available: `True`
- findings/orders: `3` / `2`
- data_quality_warnings: `1`
- top_level_data_quality_warnings: `1`
- resolved_data_quality_warnings: `0`
- ofi_qi_stale_missing_unique_records: `0`
- ofi_qi_stale_missing_reasons: `{}`
- ofi_qi_stale_missing_reason_combinations: `{}`
- ofi_qi_stale_missing_reason_combination_unique_records: `{}`
- ofi_qi_observer_unhealthy_overlap: `{'observer_unhealthy_total': 0, 'observer_unhealthy_with_other_reason': 0, 'observer_unhealthy_only': 0}`
- source_quality_blocked_families: `[]`
- carryover_warnings: `0`
- population_split_available: `True`

## Swing Strategy Discovery Sim
- artifact: `/home/ubuntu/KORStockScan/data/report/swing_strategy_discovery_ev/swing_strategy_discovery_ev_2026-07-14.json`
- authority: `swing_sim_exploration_only` / source_only: `True`
- candidate/arm/policy_exit_rows: `2135` / `13842` / `13842`
- labeled/pending_future_quotes: `2550` / `4645`
- implementation_status: `implemented`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- surviving/avoid_bucket_count: `1` / `20`
- runtime_effect: `False`

## Pipeline Event Verbosity
- artifact: `/home/ubuntu/KORStockScan/data/report/pipeline_event_verbosity/pipeline_event_verbosity_2026-07-14.json`
- state: `v2_shadow_pending_flush`
- recommended_workorder_state: `observe_pending_next_flush`
- high_volume_line_count: `303`
- high_volume_byte_share_pct: `0.2`
- parity_ok: `False`
- suppress_eligibility: `False`

## Codebase Performance Workorder Source
- artifact: `/home/ubuntu/KORStockScan/data/report/codebase_performance_workorder/codebase_performance_workorder_2026-07-14.json`
- authority: `ops_performance_workorder_source`
- accepted/deferred/rejected: `7` / `3` / `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`

## Pattern Lab Audits
- currentness: status=`pass` fail=`0` orders=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-07-14.json`
- ai_review: status=`pass` orders=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_ai_review/pattern_lab_ai_review_2026-07-14.json`
- time_window_regime_counterfactual: status=`pass` artifact=`/home/ubuntu/KORStockScan/data/report/time_window_regime_counterfactual/time_window_regime_counterfactual_2026-07-14.json`
- producer_gap_discovery: status=`pass` orders=`0` artifact=`/home/ubuntu/KORStockScan/data/report/producer_gap_discovery/producer_gap_discovery_2026-07-14.json`
- stage_hook_workorder_discovery: status=`warning` orders=`2` artifact=`/home/ubuntu/KORStockScan/data/report/stage_hook_workorder_discovery/stage_hook_workorder_discovery_2026-07-14.json`
- propagation: status=`pass` fail=`0` warnings=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_2026-07-14.json`

## Swing Runtime Approval
- request_report: `/home/ubuntu/KORStockScan/data/report/swing_runtime_approval/swing_runtime_approval_2026-07-13.json`
- approval_artifact: `-`
- requested/approved/live_dry_run: `0` / `0` / `0`
- dry_run_forced: `False`
- legacy_phase0_real_canary_ignored: `False`
- blocked: `[]`

## Code Improvement Workorder
- artifact: `/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-14.json`
- markdown: `/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-07-14.md`
- selected_order_count: `109`
- decision_counts: `{'attach_existing_family': 135, 'design_family_candidate': 3, 'defer_evidence': 5, 'reject': 3}`

## Approval Requests
- none

## Swing Approval Requests
- none

## Calibration Decisions
## Code Improvement Top Orders
- `order_entry_submit_drought_auto_resolution` decision=`attach_existing_family` subsystem=`runtime_instrumentation`
- `order_entry_broker_receipt_contract_gap_review` decision=`attach_existing_family` subsystem=`runtime_instrumentation`
- `order_entry_fill_quality_contract_gap_review` decision=`attach_existing_family` subsystem=`runtime_instrumentation`

- `soft_stop_whipsaw_confirmation`: `adjust_up` sample=`348/10`
- `holding_flow_ofi_smoothing`: `hold_sample` sample=`0/20`
- `protect_trailing_smoothing`: `adjust_down` sample=`64/20`
- `trailing_continuation`: `freeze` sample=`715/20`
- `market_regime_continuous_thresholds`: `hold_sample` sample=`9/10`
- `pre_submit_price_guard`: `hold` sample=`0/1`
- `dynamic_entry_price_resolver`: `hold_sample` sample=`67/20`
- `entry_split_order_plan`: `hold_sample` sample=`1217/20`
- `scale_in_split_order_plan`: `adjust_up` sample=`1/0`
- `entry_price_execution_quality`: `hold` sample=`24/5`
- `score65_74_recovery_probe`: `hold_sample` sample=`8/20`
- `strength_momentum_soft_gate_p1`: `hold` sample=`903/20`
- `overbought_pullback_guard_p1`: `hold` sample=`32/20`
- `liquidity_pre_submit_guard_p1`: `hold` sample=`120/20`
- `bad_entry_refined_canary`: `adjust_up` sample=`14666/10`
- `holding_exit_decision_matrix_advisory`: `hold_no_edge` sample=`14/1`
- `lifecycle_decision_matrix_runtime`: `adjust_up` sample=`548/20`
- `scale_in_price_guard`: `hold` sample=`105/20`
- `position_sizing_dynamic_formula`: `hold_sample` sample=`91/30`

## Warnings
- `trade_review_missing`
- `performance_tuning_missing`
- `swing_lab_dq:no OFI/QI micro context data found`
- `scalp_entry_adm:joined_sample_below_sample_floor`
- `scalp_entry_adm:unknown_bucket_source_quality_gap`
- `lifecycle_bucket_discovery:source_contract_drift_warning`
- `lifecycle_bucket_discovery:source_contract_drift_warning`
- `swing_strategy_discovery:pending_future_quotes`
- `swing_strategy_discovery:clean_tuning_baseline_swing_discovery_lookback_filtered`
- `swing_lifecycle_decision_matrix:swing_intraday_live_equiv_probe_missing`
- `swing_lifecycle_decision_matrix:pending_future_quotes`
- `swing_lifecycle_decision_matrix:clean_tuning_baseline_swing_discovery_lookback_filtered`
