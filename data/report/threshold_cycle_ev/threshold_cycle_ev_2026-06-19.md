# Threshold Cycle Daily EV Report - 2026-06-19

## Summary
- status: `warning`
- warning_count: `10`
- source_quality: status=`pass` allowed=`True`
- samples real/sim: `13` / `771`
- live_auto_ready_count: `0`
- primary_verdict: `sim_evidence_present_no_live_bucket`

## Runtime Apply
- status: `auto_bounded_live_ready`
- runtime_change: `True`
- selected_families: `soft_stop_whipsaw_confirmation, score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, profit_stagnation_exit_runtime, latency_spread_relief_real_operator_override, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, ai_watching_score_smoothing_report_only, lifecycle_decision_matrix_runtime, weak_pullback_entry_block_runtime, early_accel_recheck_runtime, real_pyramid_scale_in_quality_guard_runtime, sell_side_open_time_block_runtime, pre_submit_liquidity_relief_runtime, weak_context_late_entry_guard_runtime`

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
- latency recommended action: `reject` (`recovery_count=0 below floor=86`)
- latency profile generation: `{'mode': 'grid_quantile_search', 'profile_count': 360, 'age_cap_ms': 1500, 'jitter_cap_ms': 1500, 'spread_cap_ratio': 0.012, 'counterfactual_sample_floor': 3, 'recovery_event_floor_ratio': 0.1}`
- safe/caution_normal/recovery: `0` / `0` / `0`
- recovery attempts/cf sample/cf ev: `0` / `0` / `None`%
- recovered/lost labels: `0` / `0`
- stale/broker override excluded: `0` / `0`
- full/partial fill: `0` / `0`

## Holding Exit
- holding_reviews: `0`
- exit_signals: `0`
- holding_review_ms_p95: `0.0`

## Scalp Simulator
- authority: `equal_weight` / fill_policy: `signal_inclusive_best_ask_v1`
- armed/filled/sold: `110` / `110` / `87`
- expired/unpriced/duplicate: `0` / `0` / `45`
- entry_ai_price applied/skip: `5` / `0`
- submit_revalidation warning/block: `110` / `0`
- scale_in filled/unfilled: `0` / `0`
- overnight decision/sell/hold/carry_restored: `20` / `20` / `0` / `0`
- completed_profit_summary: `{'sample': 86, 'win_count': 14, 'loss_count': 72, 'avg_profit_rate': -1.622, 'median_profit_rate': -2.2, 'downside_p10_profit_rate': -3.8, 'upside_p90_profit_rate': 1.71, 'win_rate': 0.1628, 'loss_rate': 0.8372, 'stddev_profit_rate': 3.0174}`
- post_sell_join: joined=`70` / pending=`16`
- post_sell_mfe_mae_10m: mfe=`2.039`% / mae=`-2.3839`% / close=`0.4006`%

## Missed Probe Counterfactual
- book: `-` / role: `-`
- total/score65_74: `None` / `None`
- avg_expected_ev: `None`% / score65_74_avg_expected_ev: `None`%
- actual_order_submitted: `None` / broker_order_forbidden: `None`
- authority: `-`

## Scalp Entry ADM
- artifact: `/home/ubuntu/KORStockScan/data/report/scalp_entry_action_decision_matrix/scalp_entry_action_decision_matrix_2026-06-19.json`
- status: `warning` / authority: `entry_advisory_prompt_context_only`
- total/joined/floor: `728` / `68` / `20`
- prompt_applied_count: `583`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 728}`
- forced_action_counts: `{'-': 728}`
- missing_actions: `[]`
- zero_sample_actions: `['SKIP_STALE', 'BUY_DEFENSIVE']`
- top_actions: `[{'action': 'BUY_NOW', 'sample_count': 27, 'joined_sample': 3, 'source_quality_adjusted_ev_pct': -0.2733}, {'action': 'WAIT_REQUOTE', 'sample_count': 17, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'NO_BUY_AI', 'sample_count': 614, 'joined_sample': 30, 'source_quality_adjusted_ev_pct': -0.108}, {'action': 'SKIP_SOURCE_QUALITY', 'sample_count': 2, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'SKIP_PRE_SUBMIT_SAFETY', 'sample_count': 51, 'joined_sample': 35, 'source_quality_adjusted_ev_pct': -1.9582}]`

## Lifecycle Decision Matrix
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-06-19.json`
- status: `pass` / version: `lifecycle_decision_matrix_v1_2026-06-19`
- total/joined: `3115` / `2116`
- policy_pass/promote_ready: `5` / `1`
- lifecycle_flow buckets/complete/runtime/workorders: `113` / `57` / `0` / `20`
- holding/exit buckets: `32` / `46`
- holding/exit workorders: `10` / `10`
- lifecycle identity missing/join_rate: `0` / `1.0`
- lifecycle complete_flow_rate: `0.0251`
- incomplete_flow_reason_counts: `{'missing_entry': 1974, 'missing_holding': 2166, 'missing_exit': 1939, 'missing_submit': 2166, 'postclose_exit_without_entry': 273, 'candidate_id_only': 1978, 'scale_in_noise_only': 1681, 'sim_record_id_only': 101}`
- fixed_threshold_roles: `{'hard_safety': ['broker_submit_guard', 'stale_quote_submit_block', 'price_freshness_guard', 'hard_stop', 'protect_stop', 'emergency_stop', 'account_order_cooldown_qty_guard'], 'baseline_prior': ['BUY_SCORE_THRESHOLD', 'VPW_MIN_SCORE', 'strength_momentum_cutoff', 'entry_score_cutoff'], 'bounded_tunable': ['SCALP_ENTRY_LATENCY_MAX_WS_AGE_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_WS_JITTER_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_SPREAD_RATIO_FOR_CAUTION', 'score65_74_recovery_probe', 'soft_stop_whipsaw_confirmation', 'holding_flow_override', 'scale_in_price_guard'], 'legacy_archive': ['fallback_scout_main', 'fallback_single', 'latency_fallback_split_entry', 'legacy_latency_composite', 'closed_shadow_axes']}`
- policy_entries: `[{'stage': 'entry', 'sample': 763, 'joined_sample': 82, 'stage_ev_composite_pct': 1.062, 'confidence': 0.8813, 'selected_action': 'BUY_DEFENSIVE', 'source_quality_gate': 'pass', 'promote_ready': True}, {'stage': 'submit', 'sample': 131, 'joined_sample': 86, 'stage_ev_composite_pct': 0.2986, 'confidence': 1.0, 'selected_action': 'NO_CHANGE', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'holding', 'sample': 130, 'joined_sample': 86, 'stage_ev_composite_pct': -0.7244, 'confidence': 1.0, 'selected_action': 'EXIT', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'scale_in', 'sample': 1739, 'joined_sample': 1720, 'stage_ev_composite_pct': -0.4709, 'confidence': 1.0, 'selected_action': 'NO_CHANGE', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'exit', 'sample': 352, 'joined_sample': 142, 'stage_ev_composite_pct': -0.7578, 'confidence': 1.0, 'selected_action': 'EXIT', 'source_quality_gate': 'pass', 'promote_ready': False}]`

## Lifecycle Bucket Discovery
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-06-19.json`
- status: `pass` / human_intervention_required: `False`
- candidates/surfaced: `500` / `127`
- sim_auto/live_auto/new_bucket: `4` / `0` / `0`
- role/window: `new_pattern_detection` / `same_day_source_bundle_plus_rolling_threshold_cycle_consumer`
- parent_count/granularity/conflict: `45` / `target_pass` / `6`
- state_counts: `{'source_only_keep_collecting': 479, 'lifecycle_flow_sim_probe_candidate': 7, 'sim_auto_approved': 4, 'entry_only_sim_auto_approved': 9, 'entry_only_source_candidate': 1}`
- top_surfaced: `[{'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': 1.5347}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': 1.4834}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 1116, 'source_quality_adjusted_ev_pct': -1.0113}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_pyramid_', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 546, 'source_quality_adjusted_ev_pct': 0.624}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 36, 'source_quality_adjusted_ev_pct': -1.1389}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait6579_ev_cohort_stale_fresh_or_unflagged_', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 34, 'source_quality_adjusted_ev_pct': 1.7385}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wait6579_ev_cohort_stale_fresh_or_unflagge', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 13, 'source_quality_adjusted_ev_pct': 0.3448}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_combo_holding_flow_source_scalp_sim_ov', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 6, 'source_quality_adjusted_ev_pct': -0.9217}]`

## Lifecycle Bucket Windows
- promotion_window: `mtd`
- confirmation_windows: `['rolling5d', 'rolling10d']`
- windows: `{'rolling5d': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-06-19_rolling5d.json', 'window_role': 'rolling_confirmation', 'window_policy': 'rolling5d', 'status': 'pass', 'parent_bucket_count': 40, 'selected_parent_level': 'L1_broad', 'parent_granularity_status': 'target_pass', 'absorbed_child_count': 465, 'absorbed_sample_count': 82308, 'child_conflict_warning_count': 16, 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'parsed'}, 'rolling10d': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-06-19_rolling10d.json', 'window_role': 'rolling_confirmation', 'window_policy': 'rolling10d', 'status': 'pass', 'parent_bucket_count': 40, 'selected_parent_level': 'L1_broad', 'parent_granularity_status': 'target_pass', 'absorbed_child_count': 500, 'absorbed_sample_count': 131700, 'child_conflict_warning_count': 20, 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'parsed'}, 'mtd': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-06-19_mtd.json', 'window_role': 'promotion_confirmation', 'window_policy': 'mtd', 'status': 'pass', 'parent_bucket_count': 38, 'selected_parent_level': 'L1_broad', 'parent_granularity_status': 'target_pass', 'absorbed_child_count': 500, 'absorbed_sample_count': 186773, 'child_conflict_warning_count': 17, 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'parsed'}}`

## Lifecycle AI Context
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_ai_context/lifecycle_ai_context_2026-06-19.json`
- context_version: `lifecycle_ai_context_v1_2026-06-19` / authority: `ai_advisory_prompt_context_only`
- prompt_stage_count: `3` / runtime_effect: `False`
- stage_contexts: `[{'stage': 'entry', 'prompt_injection_allowed': True, 'policy_key': 'entry:weighted_adm_v1', 'alignment_hint': 'BUY_DEFENSIVE', 'context_contribution_score': -0.3144, 'attribution_quality_status': 'observational_only_pending_outcome'}, {'stage': 'submit', 'prompt_injection_allowed': False, 'policy_key': 'submit:weighted_adm_v1', 'alignment_hint': 'NO_CHANGE', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'holding', 'prompt_injection_allowed': True, 'policy_key': 'holding:weighted_adm_v1', 'alignment_hint': 'EXIT', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'scale_in', 'prompt_injection_allowed': False, 'policy_key': 'scale_in:weighted_adm_v1', 'alignment_hint': 'NO_CHANGE', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'exit', 'prompt_injection_allowed': True, 'policy_key': 'exit:weighted_adm_v1', 'alignment_hint': 'EXIT', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}]`

## Lifecycle AI Context Attribution
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_ai_context_attribution/lifecycle_ai_context_attribution_2026-06-19.json`
- eligible/applied/skipped: `864` / `864` / `0`
- replay_budget: `30`
- implementation_status: `implemented`
- stage_attribution: `{'entry': {'context_contribution_score': -0.3144, 'bounded_auxiliary_weight': -0.0472, 'attribution_quality_status': 'observational_only_pending_outcome', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': 0.0509, 'no_context_replay_observed': 0}, 'submit': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'holding': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'scale_in': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'exit': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}}`

## Institutional Flow Context
- artifact: `/home/ubuntu/KORStockScan/data/report/institutional_flow_context/institutional_flow_context_2026-06-19.json`
- status: `pass` / authority: `source_only_lifecycle_feature`
- rows ok/partial/missing/token_error: `120` / `0` / `0` / `0`
- join_rate_pct: `100.0`
- source_mix: `{'ka10059+ka10061': 120}`
- top_net_buy: `[{'stock_code': '047040', 'smart_money_net': 1358474, 'foreign_net_roll5': 0, 'inst_net_roll5': 0, 'regime': 'UNKNOWN'}, {'stock_code': '088350', 'smart_money_net': 1348449, 'foreign_net_roll5': 6949685, 'inst_net_roll5': 1340936, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '003490', 'smart_money_net': 1090763, 'foreign_net_roll5': 6660773, 'inst_net_roll5': 4149536, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '279570', 'smart_money_net': 994339, 'foreign_net_roll5': 2343080, 'inst_net_roll5': 10380178, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '006800', 'smart_money_net': 961235, 'foreign_net_roll5': 2464356, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}, {'stock_code': '028050', 'smart_money_net': 574484, 'foreign_net_roll5': 0, 'inst_net_roll5': 686797, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '087260', 'smart_money_net': 439264, 'foreign_net_roll5': 0, 'inst_net_roll5': 8791, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '085620', 'smart_money_net': 367431, 'foreign_net_roll5': 276515, 'inst_net_roll5': 982530, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '035420', 'smart_money_net': 352348, 'foreign_net_roll5': 1516537, 'inst_net_roll5': 628976, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '066980', 'smart_money_net': 315729, 'foreign_net_roll5': 0, 'inst_net_roll5': 190653, 'regime': 'INSTITUTION_ACCUMULATION'}]`

## Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-06-19.json`
- fresh: gemini=`False` claude=`True`
- consensus/orders/family_candidates: `0` / `10` / `0`

## Swing Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_2026-06-19.json`
- deepseek_lab_available: `True`
- findings/orders: `5` / `3`
- data_quality_warnings: `0`
- top_level_data_quality_warnings: `0`
- resolved_data_quality_warnings: `0`
- ofi_qi_stale_missing_unique_records: `20`
- ofi_qi_stale_missing_reasons: `{'micro_missing': 100, 'micro_stale': 0, 'observer_unhealthy': 0, 'micro_not_ready': 100, 'state_insufficient': 100}`
- ofi_qi_stale_missing_reason_combinations: `{'micro_missing+micro_not_ready+state_insufficient': 100}`
- ofi_qi_stale_missing_reason_combination_unique_records: `{'micro_missing+micro_not_ready+state_insufficient': 20}`
- ofi_qi_observer_unhealthy_overlap: `{'observer_unhealthy_total': 0, 'observer_unhealthy_with_other_reason': 0, 'observer_unhealthy_only': 0}`
- source_quality_blocked_families: `[{'family': 'swing_entry_ofi_qi_execution_quality', 'stage': 'entry', 'metric_role': 'source_quality_gate', 'decision_authority': 'swing_pattern_lab_analysis_workorder_source_only', 'window_policy': 'same_day_pattern_lab_source_quality', 'sample_floor': 1, 'primary_decision_metric': 'source_quality_gate', 'source_quality_gate': 'swing_orderbook_micro_context_ready_or_blocker_provenance_recorded', 'source_contract_version': 'swing_micro_context_source_quality_v1', 'source_contract_status': 'implemented', 'source_quality_blockers': ['entry_ofi_qi_invalid_micro_context'], 'invalid_micro_context_unique_record_count': 20, 'invalid_reason_combination_unique_record_counts': {'micro_missing+micro_not_ready+state_insufficient': 20}, 'reason_counts': {'micro_missing': 100, 'micro_stale': 0, 'observer_unhealthy': 0, 'micro_not_ready': 100, 'state_insufficient': 100}, 'reason_combination_counts': {'micro_missing+micro_not_ready+state_insufficient': 100}, 'observer_unhealthy_overlap': {'observer_unhealthy_total': 0, 'observer_unhealthy_with_other_reason': 0, 'observer_unhealthy_only': 0}, 'automation_input': True, 'runtime_effect': False, 'allowed_runtime_apply': False, 'forbidden_uses': ['swing_real_order_enable', 'one_share_real_canary', 'scale_in_real_canary', 'runtime_threshold_mutation', 'provider_route_change', 'bot_restart', 'recommendation_history_replace'], 'provenance_gap_count': 0, 'readiness_counts': {'micro_ready_count': 0, 'micro_insufficient_samples_count': 100, 'micro_not_ready_count': 100, 'state_insufficient_count': 100}, 'spread_quality': {'wide_spread_threshold_ticks': 10, 'wide_spread_count': 0, 'wide_spread_rate': 0.0, 'max_spread_ticks': None, 'hard_block': False, 'decision_use': 'source_quality_adjusted_ev_penalty_or_filter_candidate'}, 'source_quality_reason_stage_split': {'micro_missing': 100, 'micro_not_ready': 100, 'state_insufficient': 100, 'observer_unhealthy': 0, 'provenance_gap': 0}}]`
- carryover_warnings: `0`
- population_split_available: `True`

## Swing Strategy Discovery Sim
- artifact: `/home/ubuntu/KORStockScan/data/report/swing_strategy_discovery_ev/swing_strategy_discovery_ev_2026-06-19.json`
- authority: `swing_sim_exploration_only` / source_only: `True`
- candidate/arm/policy_exit_rows: `1047` / `6660` / `6660`
- labeled/pending_future_quotes: `535` / `4128`
- implementation_status: `implemented`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- surviving/avoid_bucket_count: `1` / `16`
- runtime_effect: `False`

## Pipeline Event Verbosity
- artifact: `/home/ubuntu/KORStockScan/data/report/pipeline_event_verbosity/pipeline_event_verbosity_2026-06-19.json`
- state: `v2_shadow_pending_flush`
- recommended_workorder_state: `observe_pending_next_flush`
- high_volume_line_count: `5022`
- high_volume_byte_share_pct: `3.29`
- parity_ok: `False`
- suppress_eligibility: `False`

## Codebase Performance Workorder Source
- artifact: `/home/ubuntu/KORStockScan/data/report/codebase_performance_workorder/codebase_performance_workorder_2026-06-19.json`
- authority: `ops_performance_workorder_source`
- accepted/deferred/rejected: `7` / `2` / `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`

## Pattern Lab Audits
- currentness: status=`pass` fail=`0` orders=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-06-19.json`
- ai_review: status=`warning` orders=`1` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_ai_review/pattern_lab_ai_review_2026-06-19.json`
- time_window_regime_counterfactual: status=`pass` artifact=`/home/ubuntu/KORStockScan/data/report/time_window_regime_counterfactual/time_window_regime_counterfactual_2026-06-19.json`
- producer_gap_discovery: status=`pass` orders=`0` artifact=`/home/ubuntu/KORStockScan/data/report/producer_gap_discovery/producer_gap_discovery_2026-06-19.json`
- stage_hook_workorder_discovery: status=`pass` orders=`0` artifact=`/home/ubuntu/KORStockScan/data/report/stage_hook_workorder_discovery/stage_hook_workorder_discovery_2026-06-19.json`
- propagation: status=`pass` fail=`0` warnings=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_2026-06-19.json`

## Swing Runtime Approval
- request_report: `/home/ubuntu/KORStockScan/data/report/swing_runtime_approval/swing_runtime_approval_2026-06-18.json`
- approval_artifact: `-`
- requested/approved/live_dry_run: `0` / `0` / `0`
- dry_run_forced: `False`
- legacy_phase0_real_canary_ignored: `False`
- blocked: `[]`

## Code Improvement Workorder
- artifact: `/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-06-19.json`
- markdown: `/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-06-19.md`
- selected_order_count: `125`
- decision_counts: `{'attach_existing_family': 145, 'design_family_candidate': 5, 'defer_evidence': 7, 'reject': 3}`

## Approval Requests
- none

## Swing Approval Requests
- none

## Calibration Decisions
## Code Improvement Top Orders
- `order_entry_submit_drought_auto_resolution` decision=`attach_existing_family` subsystem=`runtime_instrumentation`
- `order_entry_broker_receipt_contract_gap_review` decision=`attach_existing_family` subsystem=`runtime_instrumentation`
- `order_entry_fill_quality_contract_gap_review` decision=`attach_existing_family` subsystem=`runtime_instrumentation`

- `soft_stop_whipsaw_confirmation`: `adjust_up` sample=`8709/10`
- `holding_flow_ofi_smoothing`: `hold` sample=`124/20`
- `protect_trailing_smoothing`: `adjust_down` sample=`118/20`
- `trailing_continuation`: `freeze` sample=`434/20`
- `market_regime_continuous_thresholds`: `hold_sample` sample=`8/10`
- `pre_submit_price_guard`: `hold` sample=`0/1`
- `dynamic_entry_price_resolver`: `hold_sample` sample=`335/20`
- `entry_price_execution_quality`: `hold` sample=`133/5`
- `score65_74_recovery_probe`: `adjust_up` sample=`474/20`
- `strength_momentum_soft_gate_p1`: `hold` sample=`50224/20`
- `overbought_pullback_guard_p1`: `hold` sample=`4472/20`
- `liquidity_pre_submit_guard_p1`: `hold` sample=`6188/20`
- `bad_entry_refined_canary`: `adjust_up` sample=`101555/10`
- `holding_exit_decision_matrix_advisory`: `hold_no_edge` sample=`12/1`
- `lifecycle_decision_matrix_runtime`: `adjust_up` sample=`3115/20`
- `scale_in_price_guard`: `hold` sample=`1354/20`
- `position_sizing_dynamic_formula`: `hold_sample` sample=`30/30`

## Warnings
- `trade_review_missing`
- `performance_tuning_missing`
- `scalp_entry_adm:ai_numeric_consistency_rows_excluded_from_aggregates`
- `lifecycle_bucket_discovery:source_contract_drift_warning`
- `lifecycle_bucket_discovery:source_contract_drift_warning`
- `swing_strategy_discovery:pending_future_quotes`
- `swing_strategy_discovery:clean_tuning_baseline_swing_discovery_lookback_filtered`
- `swing_lifecycle_decision_matrix:pending_future_quotes`
- `swing_lifecycle_decision_matrix:clean_tuning_baseline_swing_discovery_lookback_filtered`
- `pattern_lab_ai_review_warning`
