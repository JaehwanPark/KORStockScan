# Threshold Cycle Daily EV Report - 2026-09-02

## Summary
- status: `pass`
- warning_count: `0`
- warning_contract active/disabled/raw: `0` / `9` / `9`
- source_quality: status=`pass` allowed=`True`
- samples real/sim: `1` / `12`
- live_auto_ready_count: `0`
- primary_verdict: `real_primary_evidence_present`

## Runtime Apply
- status: `auto_bounded_live_ready`
- runtime_change: `True`
- selected_families: `entry_split_order_plan, score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, profit_stagnation_exit_runtime, latency_spread_relief_real_operator_override, quote_consistency_normalization, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, lifecycle_decision_matrix_runtime, post_probe_winner_recovery, scalping_pyramid_quality_gate, holding_decision_context_v1, weak_pullback_entry_block_runtime, early_accel_recheck_runtime, real_pyramid_scale_in_quality_guard_runtime, sell_side_open_time_block_runtime, pre_submit_liquidity_relief_runtime, entry_opportunity_recheck_runtime, weak_context_late_entry_guard_runtime, rising_missed_normal_buy_bridge, persistent_operator_overrides_2026_06_26`

## Daily EV
- completed: `1` / open: `0`
- win/loss: `0` / `1` (`0.0`%)
- avg_profit_rate: `-2.55`%
- realized_pnl_krw: `-4717`
- full_fill_completed_avg_profit_rate: `-2.55`%

## Entry Funnel
- budget_pass_to_submitted: `3` / `757` (`0.4`%)
- latency pass/block: `165` / `371`
- latency submit routing: `latency_classifier_runtime_semantics_gap`
- latency recommended action: `reject` (`recovery_count=0 below floor=41`)
- latency profile generation: `{'mode': 'grid_quantile_search', 'profile_count': 360, 'age_cap_ms': 1500, 'jitter_cap_ms': 1500, 'spread_cap_ratio': 0.012, 'counterfactual_sample_floor': 3, 'recovery_event_floor_ratio': 0.1}`
- safe/caution_normal/recovery: `0` / `0` / `0`
- recovery attempts/cf sample/cf ev: `0` / `0` / `None`%
- recovered/lost labels: `0` / `0`
- stale/broker override excluded: `0` / `0`
- full/partial fill: `1` / `0`
- entry_split_order_plan: status=`pass` candidates=`1` policy=`entry_split_order_plan:2026-09-02:61717c33ea`
- scale_in_split_order_plan: status=`pass` candidates=`1` policy=`scale_in_split_order_plan:2026-09-02:ece34764cf9d`

## Holding Exit
- holding_reviews: `396`
- exit_signals: `10`
- holding_review_ms_p95: `7885.0`

## Scalp Simulator
- authority: `equal_weight` / fill_policy: `signal_inclusive_best_ask_v1`
- armed/filled/sold: `12` / `12` / `12`
- expired/unpriced/duplicate: `0` / `0` / `2`
- entry_ai_price applied/skip: `12` / `1`
- submit_revalidation warning/block: `0` / `0`
- scale_in filled/unfilled: `0` / `0`
- overnight decision/sell/hold/carry_restored: `2` / `2` / `0` / `0`
- completed_profit_summary: `{'sample': 12, 'win_count': 5, 'loss_count': 7, 'avg_profit_rate': -1.135, 'median_profit_rate': -1.52, 'downside_p10_profit_rate': -4.05, 'upside_p90_profit_rate': 1.81, 'win_rate': 0.4167, 'loss_rate': 0.5833, 'stddev_profit_rate': 2.6671}`
- post_sell_join: joined=`12` / pending=`0`
- post_sell_mfe_mae_10m: mfe=`1.9732`% / mae=`-8.9724`% / close=`1.1187`%

## Missed Probe Counterfactual
- book: `scalp_score65_74_probe_counterfactual` / role: `missed_buy_probe_counterfactual`
- total/score65_74: `22` / `0`
- avg_expected_ev: `12.6807`% / score65_74_avg_expected_ev: `0.0`%
- actual_order_submitted: `False` / broker_order_forbidden: `True`
- authority: `missed_probe_ev_only_not_broker_execution`

## Scalp Entry ADM
- artifact: `/home/ubuntu/KORStockScan/data/report/scalp_entry_action_decision_matrix/scalp_entry_action_decision_matrix_2026-09-02.json`
- status: `pass` / authority: `entry_advisory_prompt_context_only`
- total/joined/floor: `769` / `2638` / `20`
- prompt_applied_count: `221`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 769}`
- forced_action_counts: `{'-': 769}`
- missing_actions: `[]`
- zero_sample_actions: `['BUY_NOW']`
- outcome_join_diagnostic: `{'status': 'joined', 'zero_join_reason': '', 'candidate_key_count': 796, 'candidate_key_field_counts': {'candidate_id': 769, 'entry_adm_candidate_id': 627, 'sim_record_id': 14, 'record_id': 155}, 'post_sell_evaluation_rows': 12, 'post_sell_evaluation_join_keys': 24, 'entry_adm_relevant_post_sell_evaluation_rows': 11, 'non_entry_or_unmatched_post_sell_evaluation_rows': 1, 'unmatched_entry_adm_relevant_post_sell_evaluation_rows': 0, 'sim_outcome_eligible_rows': 13, 'sim_outcome_eligible_key_count': 26, 'sim_eligible_joined_sample': 11, 'sim_eligible_outcome_coverage_rate': 0.8462, 'matched_post_sell_evaluation_rows': 11, 'post_sell_evaluation_match_rate': 1.0, 'entry_adm_relevant_rate_of_all_post_sell_evaluations': 0.9167, 'coverage_state': 'source_outcome_underproduction', 'coverage_reason': 'entry_adm_relevant_sim_post_sell_evaluation_underproduction', 'candidate_post_sell_key_overlap_count': 24, 'joined_sample': 11, 'joined_sample_all_rows': 12, 'sample_floor': 20, 'sample_floor_met': False, 'decision_authority': 'source_quality_gap_discovery', 'runtime_effect': False, 'allowed_runtime_apply': False}`
- top_actions: `[{'action': 'WAIT_REQUOTE', 'sample_count': 388, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'SKIP_STALE', 'sample_count': 3, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'BUY_DEFENSIVE', 'sample_count': 74, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'NO_BUY_AI', 'sample_count': 248, 'joined_sample': 3, 'source_quality_adjusted_ev_pct': -0.0123}, {'action': 'SKIP_SOURCE_QUALITY', 'sample_count': 2, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}]`

## Lifecycle Decision Matrix
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-09-02.json`
- status: `pass` / version: `lifecycle_decision_matrix_v1_2026-09-02`
- total/joined: `2316` / `1229`
- policy_pass/promote_ready: `3` / `0`
- lifecycle_flow buckets/complete/runtime/workorders: `37` / `11` / `0` / `20`
- holding/exit buckets: `18` / `37`
- holding/exit workorders: `5` / `10`
- lifecycle identity missing/join_rate: `0` / `1.0`
- lifecycle complete_flow_rate: `0.0066`
- incomplete_flow_reason_counts: `{'missing_holding': 1650, 'missing_exit': 1336, 'missing_submit': 1595, 'missing_entry': 1494, 'postclose_exit_without_entry': 314, 'candidate_id_only': 1495, 'scale_in_noise_only': 1180, 'sim_record_id_only': 10}`
- fixed_threshold_roles: `{'hard_safety': ['broker_submit_guard', 'stale_quote_submit_block', 'price_freshness_guard', 'hard_stop', 'protect_stop', 'emergency_stop', 'account_order_cooldown_qty_guard'], 'baseline_prior': ['BUY_SCORE_THRESHOLD', 'VPW_MIN_SCORE', 'strength_momentum_cutoff', 'entry_score_cutoff'], 'bounded_tunable': ['SCALP_ENTRY_LATENCY_MAX_WS_AGE_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_WS_JITTER_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_SPREAD_RATIO_FOR_CAUTION', 'score65_74_recovery_probe', 'soft_stop_whipsaw_confirmation', 'holding_flow_override', 'scale_in_price_guard'], 'legacy_archive': ['fallback_scout_main', 'fallback_single', 'latency_fallback_split_entry', 'legacy_latency_composite', 'closed_shadow_axes']}`
- policy_entries: `[{'stage': 'entry', 'sample': 717, 'joined_sample': 3, 'stage_ev_composite_pct': 0.2038, 'confidence': 0.0013, 'selected_action': 'NO_CHANGE', 'source_quality_gate': 'hold_sample', 'promote_ready': False}, {'stage': 'submit', 'sample': 67, 'joined_sample': 11, 'stage_ev_composite_pct': -1.0131, 'confidence': 0.1806, 'selected_action': 'NO_CHANGE', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'holding', 'sample': 14, 'joined_sample': 11, 'stage_ev_composite_pct': -1.1528, 'confidence': 0.8643, 'selected_action': 'EXIT', 'source_quality_gate': 'hold_sample', 'promote_ready': False}, {'stage': 'scale_in', 'sample': 1180, 'joined_sample': 1179, 'stage_ev_composite_pct': -1.2016, 'confidence': 1.0, 'selected_action': 'NO_CHANGE', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'exit', 'sample': 338, 'joined_sample': 25, 'stage_ev_composite_pct': -0.982, 'confidence': 0.1849, 'selected_action': 'EXIT', 'source_quality_gate': 'pass', 'promote_ready': False}]`

## Lifecycle Bucket Discovery
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-09-02.json`
- status: `pass` / human_intervention_required: `False`
- candidates/surfaced: `424` / `37`
- sim_auto/live_auto/new_bucket: `0` / `0` / `0`
- role/window: `new_pattern_detection` / `same_day_source_bundle_plus_rolling_threshold_cycle_consumer`
- parent_count/granularity/conflict: `18` / `too_broad` / `0`
- positive_parent/sample_ready/conflict: `1` / `0` / `0`
- active_positive_seed/nonpositive_seed: `1` / `0`
- positive_sim_auto/nonpositive_sim_auto: `0` / `0`
- state_counts: `{'source_only_keep_collecting': 424}`
- top_surfaced: `[{'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 1148, 'source_quality_adjusted_ev_pct': -1.2524}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_pyramid_', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 31, 'source_quality_adjusted_ev_pct': 0.6793}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'tighten_or_exclude', 'joined_sample': 2, 'source_quality_adjusted_ev_pct': -1.13}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'tighten_or_exclude', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': -0.88}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_f', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'tighten_or_exclude', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': -0.46}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'tighten_or_exclude', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': -1.45}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'tighten_or_exclude', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': -1.11}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'tighten_or_exclude', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': -3.5005}]`
- top_sample_ready_positive_parent_buckets: `[]`
- top_active_positive_seeds: `[{'active_seed_id': 'active_seed_37c2c640b72a1f8e', 'parent_ev_pct': 0.1763, 'parent_joined_sample': 1, 'complete_flow_count': 1, 'observable_prefix': {'entry_score_parent': 'score_watch_recovery', 'entry_source_parent': 'entry_source_action_decision', 'submit_quality_parent': 'submit_revalidation_ok'}, 'active_collection_reason': 'positive_ev_parent_active_sim_collection', 'live_conversion_blocked_reason': '', 'positive_ev_stage_sampling_plan': {'schema_version': 'positive_ev_stage_sampling_plan_v1', 'sampling_scope': 'positive_ev_parent_stage_completion', 'sample_goal_per_bucket': 10, 'complete_flow_goal_per_bucket': 5, 'current_parent_joined_sample': 1, 'current_complete_flow_count': 1, 'additional_parent_sample_needed': 9, 'additional_complete_flow_needed': 4, 'runtime_match_fields': {'entry_score_parent': 'score_watch_recovery', 'entry_source_parent': 'entry_source_action_decision', 'submit_quality_parent': 'submit_revalidation_ok'}, 'runtime_match_forbidden_fields': ['exit_outcome_parent', 'major_holding_parent', 'scale_in_parent'], 'stage_targets': [{'stage': 'entry', 'goal': 'revisit_positive_prefix_candidates', 'match_role': 'runtime_observable_prefix'}, {'stage': 'submit', 'goal': 'preserve_pre_submit_guard_verdict_and_revalidation', 'match_role': 'runtime_observable_prefix_when_available'}, {'stage': 'holding', 'goal': 'attach_holding_outcome_to_candidate_identity', 'match_role': 'post_observation_validation_only'}, {'stage': 'exit', 'goal': 'attach_exit_outcome_to_candidate_identity', 'match_role': 'post_observation_validation_only'}, {'stage': 'scale_in', 'goal': 'separate_none_avg_down_pyramid_observation', 'match_role': 'post_observation_validation_only'}], 'priority_reason': 'eligible_positive_parent_needs_complete_flow', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}, 'child_conflict_stratified_targets': {'schema_version': 'child_conflict_stratified_sampling_v1', 'enabled': False, 'sample_goal_per_conflict_child': 5, 'strata': [], 'resolution_policy': 'collect_until_child_floor_before_exclusion_or_live_authority', 'runtime_match_fields': {'entry_score_parent': 'score_watch_recovery', 'entry_source_parent': 'entry_source_action_decision', 'submit_quality_parent': 'submit_revalidation_ok'}, 'post_observation_dimensions_only': ['holding', 'exit', 'scale_in', 'profit'], 'runtime_consumption_allowed': False, 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}, 'stage_counterfactual_variant_count': 5}]`
- top_positive_sim_auto_approved: `[]`
- top_nonpositive_sim_auto_approved: `[]`

## Lifecycle Bucket Windows
- promotion_window: `mtd`
- confirmation_windows: `['rolling5d', 'rolling10d']`
- windows: `{'rolling5d': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-09-02_rolling5d.json', 'window_role': 'rolling_confirmation', 'window_policy': 'rolling5d', 'status': 'pass', 'parent_bucket_count': 28, 'selected_parent_level': 'L3_detailed', 'parent_granularity_status': 'too_broad', 'absorbed_child_count': 66, 'absorbed_sample_count': 4793, 'child_conflict_warning_count': 0, 'positive_parent_count': 1, 'positive_parent_sample_ready_count': 0, 'positive_parent_conflict_count': 0, 'top_sample_ready_positive_parent_buckets': [], 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'parsed'}, 'rolling10d': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-09-02_rolling10d.json', 'window_role': 'rolling_confirmation', 'window_policy': 'rolling10d', 'status': 'pass', 'parent_bucket_count': 45, 'selected_parent_level': 'L2_default', 'parent_granularity_status': 'target_pass', 'absorbed_child_count': 143, 'absorbed_sample_count': 13774, 'child_conflict_warning_count': 2, 'positive_parent_count': 4, 'positive_parent_sample_ready_count': 0, 'positive_parent_conflict_count': 0, 'top_sample_ready_positive_parent_buckets': [], 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'parsed'}, 'mtd': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-09-02_mtd.json', 'window_role': 'promotion_confirmation', 'window_policy': 'mtd', 'status': 'pass', 'parent_bucket_count': 22, 'selected_parent_level': 'L3_detailed', 'parent_granularity_status': 'too_broad', 'absorbed_child_count': 53, 'absorbed_sample_count': 3498, 'child_conflict_warning_count': 0, 'positive_parent_count': 1, 'positive_parent_sample_ready_count': 0, 'positive_parent_conflict_count': 0, 'top_sample_ready_positive_parent_buckets': [], 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'parsed'}}`

## Lifecycle AI Context
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_ai_context/lifecycle_ai_context_2026-09-02.json`
- context_version: `lifecycle_ai_context_v1_2026-09-02` / authority: `ai_advisory_prompt_context_only`
- prompt_stage_count: `3` / runtime_effect: `False`
- stage_contexts: `[{'stage': 'entry', 'prompt_injection_allowed': True, 'policy_key': 'entry:weighted_adm_v1', 'alignment_hint': 'NO_CHANGE', 'context_contribution_score': 0.0, 'attribution_quality_status': 'observational_only_pending_outcome'}, {'stage': 'submit', 'prompt_injection_allowed': False, 'policy_key': 'submit:weighted_adm_v1', 'alignment_hint': 'NO_CHANGE', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'holding', 'prompt_injection_allowed': True, 'policy_key': 'holding:weighted_adm_v1', 'alignment_hint': 'EXIT', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'scale_in', 'prompt_injection_allowed': False, 'policy_key': 'scale_in:weighted_adm_v1', 'alignment_hint': 'NO_CHANGE', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'exit', 'prompt_injection_allowed': True, 'policy_key': 'exit:weighted_adm_v1', 'alignment_hint': 'EXIT', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}]`

## Lifecycle AI Context Attribution
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_ai_context_attribution/lifecycle_ai_context_attribution_2026-09-02.json`
- eligible/applied/skipped: `465` / `465` / `0`
- replay_budget: `30`
- implementation_status: `implemented`
- stage_attribution: `{'entry': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'observational_only_pending_outcome', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'submit': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'holding': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'scale_in': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'exit': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}}`

## Institutional Flow Context
- artifact: `/home/ubuntu/KORStockScan/data/report/institutional_flow_context/institutional_flow_context_2026-09-02.json`
- status: `pass` / authority: `source_only_lifecycle_feature`
- rows ok/partial/missing/token_error: `120` / `0` / `0` / `0`
- join_rate_pct: `100.0`
- source_mix: `{'ka10059+ka10061': 120}`
- top_net_buy: `[{'stock_code': '003160', 'smart_money_net': 435565, 'foreign_net_roll5': 50302, 'inst_net_roll5': 501219, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '044490', 'smart_money_net': 268159, 'foreign_net_roll5': 239716, 'inst_net_roll5': 122759, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '124500', 'smart_money_net': 167064, 'foreign_net_roll5': 0, 'inst_net_roll5': 0, 'regime': 'UNKNOWN'}, {'stock_code': '183300', 'smart_money_net': 154642, 'foreign_net_roll5': 0, 'inst_net_roll5': 0, 'regime': 'UNKNOWN'}, {'stock_code': '257720', 'smart_money_net': 154512, 'foreign_net_roll5': 3434060, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}, {'stock_code': '032350', 'smart_money_net': 94544, 'foreign_net_roll5': 0, 'inst_net_roll5': 322648, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '007810', 'smart_money_net': 79704, 'foreign_net_roll5': 39906, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}, {'stock_code': '323410', 'smart_money_net': 74519, 'foreign_net_roll5': 159070, 'inst_net_roll5': 176995, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '042700', 'smart_money_net': 68615, 'foreign_net_roll5': 0, 'inst_net_roll5': 125680, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '105630', 'smart_money_net': 54787, 'foreign_net_roll5': 35005, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}]`

## Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-09-02.json`
- fresh: gemini=`False` claude=`True`
- consensus/orders/family_candidates: `0` / `10` / `0`

## Swing Pattern Lab Automation
- artifact: `-`
- deepseek_lab_available: `None`
- findings/orders: `0` / `0`
- data_quality_warnings: `0`
- top_level_data_quality_warnings: `None`
- resolved_data_quality_warnings: `None`
- ofi_qi_stale_missing_unique_records: `0`
- ofi_qi_stale_missing_reasons: `{}`
- ofi_qi_stale_missing_reason_combinations: `{}`
- ofi_qi_stale_missing_reason_combination_unique_records: `{}`
- ofi_qi_observer_unhealthy_overlap: `{}`
- source_quality_blocked_families: `[]`
- carryover_warnings: `0`
- population_split_available: `False`

## Swing Strategy Discovery Sim
- artifact: `-`
- authority: `swing_sim_exploration_only` / source_only: `None`
- candidate/arm/policy_exit_rows: `0` / `0` / `None`
- labeled/pending_future_quotes: `0` / `0`
- implementation_status: `-`
- top_surviving_arm: `-`
- surviving/avoid_bucket_count: `None` / `0`
- runtime_effect: `False`

## Pipeline Event Verbosity
- artifact: `/home/ubuntu/KORStockScan/data/report/pipeline_event_verbosity/pipeline_event_verbosity_2026-09-02.json`
- state: `v2_shadow_pending_flush`
- recommended_workorder_state: `observe_pending_next_flush`
- high_volume_line_count: `180866`
- high_volume_byte_share_pct: `28.4`
- parity_ok: `False`
- suppress_eligibility: `False`

## Codebase Performance Workorder Source
- artifact: `-`
- authority: `-`
- accepted/deferred/rejected: `0` / `0` / `0`
- runtime_effect: `False`
- strategy_effect: `None`
- data_quality_effect: `None`
- tuning_axis_effect: `None`

## Pattern Lab Audits
- currentness: status=`pass` fail=`0` orders=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-09-02.json`
- ai_review: status=`pass` orders=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_ai_review/pattern_lab_ai_review_2026-09-02.json`
- time_window_regime_counterfactual: status=`missing` artifact=`-`
- producer_gap_discovery: status=`missing` orders=`0` artifact=`-`
- stage_hook_workorder_discovery: status=`missing` orders=`0` artifact=`-`
- propagation: status=`pass` fail=`0` warnings=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_2026-09-02.json`

## Swing Runtime Approval
- request_report: `-`
- approval_artifact: `-`
- requested/approved/live_dry_run: `0` / `0` / `0`
- dry_run_forced: `False`
- legacy_phase0_real_canary_ignored: `False`
- blocked: `[]`

## Code Improvement Workorder
- artifact: `/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-09-02.json`
- markdown: `/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-09-02.md`
- selected_order_count: `50`
- decision_counts: `{'implement_now': 1, 'attach_existing_family': 64, 'design_family_candidate': 3, 'reject': 1}`

## Approval Requests
- none

## Swing Approval Requests
- none

## Calibration Decisions
## Code Improvement Top Orders
- `order_scanner_funnel_executable_bbo_join` decision=`implement_now` subsystem=`scanner_runtime_freshness_funnel`
- `order_entry_submit_drought_auto_resolution` decision=`attach_existing_family` subsystem=`runtime_instrumentation`
- `order_conversion_lane_submit_drought_submit_drought_upstream_gate` decision=`attach_existing_family` subsystem=`sim_to_real_conversion_lineage`

- `soft_stop_whipsaw_confirmation`: `adjust_up` sample=`1076/10`
- `holding_flow_ofi_smoothing`: `hold_sample` sample=`4/20`
- `protect_trailing_smoothing`: `hold_sample` sample=`2/20`
- `trailing_continuation`: `freeze` sample=`105/20`
- `market_regime_continuous_thresholds`: `hold_sample` sample=`8/10`
- `pre_submit_price_guard`: `hold` sample=`0/1`
- `dynamic_entry_price_resolver`: `hold_sample` sample=`37/20`
- `entry_split_order_plan`: `adjust_up` sample=`3474/20`
- `scale_in_split_order_plan`: `hold_sample` sample=`0/3`
- `entry_price_execution_quality`: `hold` sample=`46/5`
- `score65_74_recovery_probe`: `adjust_up` sample=`93/20`
- `strength_momentum_soft_gate_p1`: `hold` sample=`3598/20`
- `overbought_pullback_guard_p1`: `hold` sample=`1166/20`
- `liquidity_pre_submit_guard_p1`: `hold` sample=`663/20`
- `bad_entry_refined_canary`: `hold_sample` sample=`0/10`
- `holding_exit_decision_matrix_advisory`: `hold_no_edge` sample=`0/1`
- `lifecycle_decision_matrix_runtime`: `adjust_up` sample=`2316/20`
- `scale_in_price_guard`: `hold_sample` sample=`39/20`
- `position_sizing_dynamic_formula`: `hold_sample` sample=`31/30`
- `scalping_avg_down_recovery_quality_gate`: `hold_no_edge` sample=`45/rolling_shallow_primary>=10 and rolling_deep_primary>=5`
