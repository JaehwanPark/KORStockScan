# Threshold Cycle Daily EV Report - 2026-07-29

## Summary
- status: `warning`
- warning_count: `12`
- source_quality: status=`pass` allowed=`True`
- samples real/sim: `34` / `8`
- live_auto_ready_count: `0`
- primary_verdict: `real_primary_evidence_present`

## Runtime Apply
- status: `auto_bounded_live_ready`
- runtime_change: `True`
- selected_families: `soft_stop_whipsaw_confirmation, entry_split_order_plan, scale_in_split_order_plan, score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, profit_stagnation_exit_runtime, latency_spread_relief_real_operator_override, quote_consistency_normalization, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, ai_watching_score_smoothing_report_only, holding_decision_context_v1, weak_pullback_entry_block_runtime, early_accel_recheck_runtime, real_pyramid_scale_in_quality_guard_runtime, sell_side_open_time_block_runtime, pre_submit_liquidity_relief_runtime, entry_opportunity_recheck_runtime, weak_context_late_entry_guard_runtime, rising_missed_normal_buy_bridge, persistent_operator_overrides_2026_06_26`

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
- latency profile generation: `{'mode': 'grid_quantile_search', 'profile_count': 360, 'age_cap_ms': 1500, 'jitter_cap_ms': 1500, 'spread_cap_ratio': 0.012, 'counterfactual_sample_floor': 3, 'recovery_event_floor_ratio': 0.1}`
- safe/caution_normal/recovery: `0` / `0` / `0`
- recovery attempts/cf sample/cf ev: `0` / `0` / `None`%
- recovered/lost labels: `0` / `0`
- stale/broker override excluded: `0` / `0`
- full/partial fill: `0` / `0`
- entry_split_order_plan: status=`pass` candidates=`1` policy=`entry_split_order_plan:2026-07-29:91f21e5a13`
- scale_in_split_order_plan: status=`pass` candidates=`1` policy=`scale_in_split_order_plan:2026-07-29:c91179494131`

## Holding Exit
- holding_reviews: `0`
- exit_signals: `0`
- holding_review_ms_p95: `0.0`

## Scalp Simulator
- authority: `equal_weight` / fill_policy: `signal_inclusive_best_ask_v1`
- armed/filled/sold: `3` / `3` / `4`
- expired/unpriced/duplicate: `0` / `0` / `1`
- entry_ai_price applied/skip: `3` / `11`
- submit_revalidation warning/block: `0` / `0`
- scale_in filled/unfilled: `0` / `0`
- overnight decision/sell/hold/carry_restored: `1` / `1` / `0` / `0`
- completed_profit_summary: `{'sample': 4, 'win_count': 1, 'loss_count': 3, 'avg_profit_rate': -0.725, 'median_profit_rate': -1.4, 'downside_p10_profit_rate': -1.44, 'upside_p90_profit_rate': 0.17, 'win_rate': 0.25, 'loss_rate': 0.75, 'stddev_profit_rate': 0.8191}`
- post_sell_join: joined=`3` / pending=`1`
- post_sell_mfe_mae_10m: mfe=`0.0837`% / mae=`-2.5603`% / close=`-0.749`%

## Missed Probe Counterfactual
- book: `-` / role: `-`
- total/score65_74: `None` / `None`
- avg_expected_ev: `None`% / score65_74_avg_expected_ev: `None`%
- actual_order_submitted: `None` / broker_order_forbidden: `None`
- authority: `-`

## Scalp Entry ADM
- artifact: `/home/ubuntu/KORStockScan/data/report/scalp_entry_action_decision_matrix/scalp_entry_action_decision_matrix_2026-07-29.json`
- status: `warning` / authority: `entry_advisory_prompt_context_only`
- total/joined/floor: `85` / `3` / `20`
- prompt_applied_count: `15`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 85}`
- forced_action_counts: `{'-': 85}`
- missing_actions: `[]`
- zero_sample_actions: `['SKIP_SOURCE_QUALITY']`
- outcome_join_diagnostic: `{'status': 'joined', 'zero_join_reason': '', 'candidate_key_count': 104, 'candidate_key_field_counts': {'candidate_id': 85, 'entry_adm_candidate_id': 0, 'sim_record_id': 11, 'record_id': 35}, 'post_sell_evaluation_rows': 3, 'post_sell_evaluation_join_keys': 6, 'candidate_post_sell_key_overlap_count': 3, 'joined_sample': 3, 'joined_sample_all_rows': 3, 'sample_floor': 20, 'sample_floor_met': False, 'decision_authority': 'source_quality_gap_discovery', 'runtime_effect': False, 'allowed_runtime_apply': False}`
- top_actions: `[{'action': 'BUY_NOW', 'sample_count': 6, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'WAIT_REQUOTE', 'sample_count': 28, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'SKIP_STALE', 'sample_count': 2, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'BUY_DEFENSIVE', 'sample_count': 13, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'NO_BUY_AI', 'sample_count': 25, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}]`

## Lifecycle Decision Matrix
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-07-29.json`
- status: `pass` / version: `lifecycle_decision_matrix_v1_2026-07-29`
- total/joined: `196` / `94`
- policy_pass/promote_ready: `1` / `0`
- lifecycle_flow buckets/complete/runtime/workorders: `21` / `3` / `0` / `20`
- holding/exit buckets: `12` / `25`
- holding/exit workorders: `3` / `5`
- lifecycle identity missing/join_rate: `0` / `1.0`
- lifecycle complete_flow_rate: `0.0224`
- incomplete_flow_reason_counts: `{'missing_holding': 130, 'missing_exit': 120, 'missing_submit': 114, 'missing_entry': 90, 'candidate_id_only': 95, 'scale_in_noise_only': 79, 'sim_record_id_only': 4, 'postclose_exit_without_entry': 11}`
- fixed_threshold_roles: `{'hard_safety': ['broker_submit_guard', 'stale_quote_submit_block', 'price_freshness_guard', 'hard_stop', 'protect_stop', 'emergency_stop', 'account_order_cooldown_qty_guard'], 'baseline_prior': ['BUY_SCORE_THRESHOLD', 'VPW_MIN_SCORE', 'strength_momentum_cutoff', 'entry_score_cutoff'], 'bounded_tunable': ['SCALP_ENTRY_LATENCY_MAX_WS_AGE_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_WS_JITTER_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_SPREAD_RATIO_FOR_CAUTION', 'score65_74_recovery_probe', 'soft_stop_whipsaw_confirmation', 'holding_flow_override', 'scale_in_price_guard'], 'legacy_archive': ['fallback_scout_main', 'fallback_single', 'latency_fallback_split_entry', 'legacy_latency_composite', 'closed_shadow_axes']}`
- policy_entries: `[{'stage': 'entry', 'sample': 76, 'joined_sample': 3, 'stage_ev_composite_pct': -0.8198, 'confidence': 0.0118, 'selected_action': 'WAIT_REQUOTE', 'source_quality_gate': 'hold_sample', 'promote_ready': False}, {'stage': 'submit', 'sample': 20, 'joined_sample': 3, 'stage_ev_composite_pct': -0.8198, 'confidence': 0.045, 'selected_action': 'NO_CHANGE', 'source_quality_gate': 'hold_sample', 'promote_ready': False}, {'stage': 'holding', 'sample': 4, 'joined_sample': 3, 'stage_ev_composite_pct': -0.8757, 'confidence': 0.225, 'selected_action': 'EXIT', 'source_quality_gate': 'hold_sample', 'promote_ready': False}, {'stage': 'scale_in', 'sample': 79, 'joined_sample': 78, 'stage_ev_composite_pct': -0.0975, 'confidence': 1.0, 'selected_action': 'NO_CHANGE', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'exit', 'sample': 17, 'joined_sample': 7, 'stage_ev_composite_pct': -0.7185, 'confidence': 0.2882, 'selected_action': 'EXIT', 'source_quality_gate': 'hold_sample', 'promote_ready': False}]`

## Lifecycle Bucket Discovery
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-07-29.json`
- status: `pass` / human_intervention_required: `False`
- candidates/surfaced: `206` / `32`
- sim_auto/live_auto/new_bucket: `1` / `0` / `10`
- role/window: `new_pattern_detection` / `same_day_source_bundle_plus_rolling_threshold_cycle_consumer`
- parent_count/granularity/conflict: `13` / `too_broad` / `0`
- positive_parent/sample_ready/conflict: `1` / `0` / `0`
- active_positive_seed/nonpositive_seed: `0` / `0`
- positive_sim_auto/nonpositive_sim_auto: `1` / `1`
- state_counts: `{'source_only_keep_collecting': 194, 'lifecycle_flow_sim_probe_candidate': 1, 'sim_auto_approved': 1, 'new_bucket_candidate': 10}`
- top_surfaced: `[{'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_pyramid_', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 41, 'source_quality_adjusted_ev_pct': 0.413}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 37, 'source_quality_adjusted_ev_pct': -0.6631}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_sim_entry_ai_price_skip_order_stale_s', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'tighten_or_exclude', 'joined_sample': 2, 'source_quality_adjusted_ev_pct': -1.28}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'stage': 'lifecycle_flow', 'classification_state': 'lifecycle_flow_sim_probe_candidate', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': 0.33}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_combo_holding_flow_source_scalp_sim_ov', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': -0.1725}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 0, 'source_quality_adjusted_ev_pct': None}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 0, 'source_quality_adjusted_ev_pct': None}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_sim_panic_level1_entry_observed_stal', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 0, 'source_quality_adjusted_ev_pct': None}]`
- top_sample_ready_positive_parent_buckets: `[]`
- top_active_positive_seeds: `[]`
- top_positive_sim_auto_approved: `[{'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'classification_state': 'lifecycle_flow_sim_probe_candidate', 'stage': 'lifecycle_flow', 'bucket_type': 'combo_lifecycle_flow', 'source_quality_adjusted_ev_pct': 0.33, 'joined_sample': 1, 'sample': 1}]`
- top_nonpositive_sim_auto_approved: `[{'bucket_id': 'scale_in:stage_policy:scale_in_weighted_adm_v1', 'classification_state': 'sim_auto_approved', 'stage': 'scale_in', 'bucket_type': 'stage_policy', 'source_quality_adjusted_ev_pct': -0.0975, 'joined_sample': 78, 'sample': 79}]`

## Lifecycle Bucket Windows
- promotion_window: `mtd`
- confirmation_windows: `['rolling5d', 'rolling10d']`
- windows: `{'rolling5d': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-07-29_rolling5d.json', 'window_role': 'rolling_confirmation', 'window_policy': 'rolling5d', 'status': 'pass', 'parent_bucket_count': 17, 'selected_parent_level': 'L2_default', 'parent_granularity_status': 'too_broad', 'absorbed_child_count': 37, 'absorbed_sample_count': 237, 'child_conflict_warning_count': 0, 'positive_parent_count': 1, 'positive_parent_sample_ready_count': 0, 'positive_parent_conflict_count': 0, 'top_sample_ready_positive_parent_buckets': [], 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'parsed'}, 'rolling10d': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-07-29_rolling10d.json', 'window_role': 'rolling_confirmation', 'window_policy': 'rolling10d', 'status': 'pass', 'parent_bucket_count': 30, 'selected_parent_level': 'L2_default', 'parent_granularity_status': 'target_pass', 'absorbed_child_count': 91, 'absorbed_sample_count': 1321, 'child_conflict_warning_count': 0, 'positive_parent_count': 1, 'positive_parent_sample_ready_count': 0, 'positive_parent_conflict_count': 0, 'top_sample_ready_positive_parent_buckets': [], 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'parsed'}, 'mtd': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-07-29_mtd.json', 'window_role': 'promotion_confirmation', 'window_policy': 'mtd', 'status': 'pass', 'parent_bucket_count': 38, 'selected_parent_level': 'L1_broad', 'parent_granularity_status': 'target_pass', 'absorbed_child_count': 246, 'absorbed_sample_count': 12809, 'child_conflict_warning_count': 8, 'positive_parent_count': 5, 'positive_parent_sample_ready_count': 0, 'positive_parent_conflict_count': 0, 'top_sample_ready_positive_parent_buckets': [], 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'parsed'}}`

## Lifecycle AI Context
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_ai_context/lifecycle_ai_context_2026-07-29.json`
- context_version: `lifecycle_ai_context_v1_2026-07-29` / authority: `ai_advisory_prompt_context_only`
- prompt_stage_count: `3` / runtime_effect: `False`
- stage_contexts: `[{'stage': 'entry', 'prompt_injection_allowed': True, 'policy_key': 'entry:weighted_adm_v1', 'alignment_hint': 'WAIT_REQUOTE', 'context_contribution_score': 0.0, 'attribution_quality_status': 'observational_only_pending_outcome'}, {'stage': 'submit', 'prompt_injection_allowed': False, 'policy_key': 'submit:weighted_adm_v1', 'alignment_hint': 'NO_CHANGE', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'holding', 'prompt_injection_allowed': True, 'policy_key': 'holding:weighted_adm_v1', 'alignment_hint': 'EXIT', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'scale_in', 'prompt_injection_allowed': False, 'policy_key': 'scale_in:weighted_adm_v1', 'alignment_hint': 'NO_CHANGE', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'exit', 'prompt_injection_allowed': True, 'policy_key': 'exit:weighted_adm_v1', 'alignment_hint': 'EXIT', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}]`

## Lifecycle AI Context Attribution
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_ai_context_attribution/lifecycle_ai_context_attribution_2026-07-29.json`
- eligible/applied/skipped: `23` / `23` / `0`
- replay_budget: `30`
- implementation_status: `implemented`
- stage_attribution: `{'entry': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'observational_only_pending_outcome', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'submit': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'holding': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'scale_in': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'exit': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}}`

## Institutional Flow Context
- artifact: `/home/ubuntu/KORStockScan/data/report/institutional_flow_context/institutional_flow_context_2026-07-29.json`
- status: `pass` / authority: `source_only_lifecycle_feature`
- rows ok/partial/missing/token_error: `120` / `0` / `0` / `0`
- join_rate_pct: `100.0`
- source_mix: `{'ka10059+ka10061': 120}`
- top_net_buy: `[{'stock_code': '005930', 'smart_money_net': 6265748, 'foreign_net_roll5': 0, 'inst_net_roll5': 1392144, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '251340', 'smart_money_net': 3168705, 'foreign_net_roll5': 0, 'inst_net_roll5': 5155214, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '530107', 'smart_money_net': 1028385, 'foreign_net_roll5': 0, 'inst_net_roll5': 1935624, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '253160', 'smart_money_net': 744828, 'foreign_net_roll5': 15000, 'inst_net_roll5': 1593504, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '011200', 'smart_money_net': 717800, 'foreign_net_roll5': 2633066, 'inst_net_roll5': 1502533, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '042660', 'smart_money_net': 636690, 'foreign_net_roll5': 1089064, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}, {'stock_code': '034020', 'smart_money_net': 583814, 'foreign_net_roll5': 0, 'inst_net_roll5': 536771, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '066570', 'smart_money_net': 389499, 'foreign_net_roll5': 342581, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}, {'stock_code': '316140', 'smart_money_net': 380095, 'foreign_net_roll5': 1238876, 'inst_net_roll5': 1028737, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '042700', 'smart_money_net': 374173, 'foreign_net_roll5': 0, 'inst_net_roll5': 0, 'regime': 'UNKNOWN'}]`

## Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-07-29.json`
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
- artifact: `/home/ubuntu/KORStockScan/data/report/pipeline_event_verbosity/pipeline_event_verbosity_2026-07-29.json`
- state: `v2_shadow_pending_flush`
- recommended_workorder_state: `observe_pending_next_flush`
- high_volume_line_count: `542`
- high_volume_byte_share_pct: `0.39`
- parity_ok: `False`
- suppress_eligibility: `False`

## Codebase Performance Workorder Source
- artifact: `/home/ubuntu/KORStockScan/data/report/codebase_performance_workorder/codebase_performance_workorder_2026-07-29.json`
- authority: `ops_performance_workorder_source`
- accepted/deferred/rejected: `8` / `2` / `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`

## Pattern Lab Audits
- currentness: status=`pass` fail=`0` orders=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-07-29.json`
- ai_review: status=`warning` orders=`1` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_ai_review/pattern_lab_ai_review_2026-07-29.json`
- time_window_regime_counterfactual: status=`pass` artifact=`/home/ubuntu/KORStockScan/data/report/time_window_regime_counterfactual/time_window_regime_counterfactual_2026-07-29.json`
- producer_gap_discovery: status=`pass` orders=`0` artifact=`/home/ubuntu/KORStockScan/data/report/producer_gap_discovery/producer_gap_discovery_2026-07-29.json`
- stage_hook_workorder_discovery: status=`warning` orders=`2` artifact=`/home/ubuntu/KORStockScan/data/report/stage_hook_workorder_discovery/stage_hook_workorder_discovery_2026-07-29.json`
- propagation: status=`warning` fail=`0` warnings=`2` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_2026-07-29.json`

## Swing Runtime Approval
- request_report: `-`
- approval_artifact: `-`
- requested/approved/live_dry_run: `0` / `0` / `0`
- dry_run_forced: `False`
- legacy_phase0_real_canary_ignored: `False`
- blocked: `[]`

## Code Improvement Workorder
- artifact: `/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-29.json`
- markdown: `/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-07-29.md`
- selected_order_count: `83`
- decision_counts: `{'attach_existing_family': 83, 'design_family_candidate': 3, 'defer_evidence': 3, 'reject': 3}`

## Approval Requests
- none

## Swing Approval Requests
- none

## Calibration Decisions
## Code Improvement Top Orders
- `order_conversion_lane_key_lineage_active_arm_07b7bc397f7a9d64` decision=`attach_existing_family` subsystem=`sim_to_real_conversion_lineage`
- `order_latency_canary_tag_완화_1축_canary_승인` decision=`attach_existing_family` subsystem=`runtime_instrumentation`
- `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_10_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_2ad7fdfe` decision=`attach_existing_family` subsystem=`lifecycle_decision_matrix`

- `soft_stop_whipsaw_confirmation`: `adjust_up` sample=`354/10`
- `holding_flow_ofi_smoothing`: `hold_sample` sample=`1/20`
- `protect_trailing_smoothing`: `hold` sample=`113/20`
- `trailing_continuation`: `freeze` sample=`535/20`
- `market_regime_continuous_thresholds`: `hold_sample` sample=`8/10`
- `pre_submit_price_guard`: `hold` sample=`0/1`
- `dynamic_entry_price_resolver`: `hold_sample` sample=`20/20`
- `entry_split_order_plan`: `adjust_up` sample=`207/20`
- `scale_in_split_order_plan`: `adjust_up` sample=`1/0`
- `entry_price_execution_quality`: `hold` sample=`28/5`
- `score65_74_recovery_probe`: `hold_sample` sample=`17/20`
- `strength_momentum_soft_gate_p1`: `hold` sample=`286/20`
- `overbought_pullback_guard_p1`: `hold_sample` sample=`0/20`
- `liquidity_pre_submit_guard_p1`: `hold_sample` sample=`9/20`
- `bad_entry_refined_canary`: `adjust_up` sample=`7285/10`
- `holding_exit_decision_matrix_advisory`: `hold_no_edge` sample=`14/1`
- `lifecycle_decision_matrix_runtime`: `adjust_up` sample=`196/20`
- `scale_in_price_guard`: `hold` sample=`26/20`
- `position_sizing_dynamic_formula`: `hold_sample` sample=`77/30`

## Warnings
- `trade_review_missing`
- `performance_tuning_missing`
- `swing_pattern_lab_automation_missing`
- `scalp_entry_adm:joined_sample_below_sample_floor`
- `scalp_entry_adm:unknown_bucket_source_quality_gap`
- `lifecycle_bucket_discovery:source_contract_drift_warning`
- `lifecycle_bucket_discovery:source_contract_drift_warning`
- `swing_strategy_discovery_ev_missing`
- `swing_lifecycle_decision_matrix_missing`
- `swing_lifecycle_bucket_discovery_missing`
- `pattern_lab_ai_review_warning`
- `pattern_lab_propagation_audit_warning`
