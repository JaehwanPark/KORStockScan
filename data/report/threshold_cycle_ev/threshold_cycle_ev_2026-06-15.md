# Threshold Cycle Daily EV Report - 2026-06-15

## Runtime Apply
- status: `auto_bounded_live_ready`
- runtime_change: `True`
- selected_families: `soft_stop_whipsaw_confirmation, score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, entry_price_gap_profile_runtime, profit_stagnation_exit_runtime, latency_spread_relief_real_operator_override, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, ai_watching_score_smoothing_report_only, lifecycle_decision_matrix_runtime, weak_pullback_entry_block_runtime, swing_gatekeeper_reject_cooldown`

## Daily EV
- completed: `2` / open: `0`
- win/loss: `0` / `2` (`0.0`%)
- avg_profit_rate: `-0.58`%
- realized_pnl_krw: `-20110`
- full_fill_completed_avg_profit_rate: `0.0`%

## Entry Funnel
- budget_pass_to_submitted: `2` / `6131` (`0.03`%)
- latency pass/block: `81` / `6050`
- latency submit routing: `latency_classifier_runtime_semantics_gap`
- latency recommended action: `reject` (`recovery_count=0 below floor=1640`)
- latency profile generation: `{'mode': 'grid_quantile_search', 'profile_count': 900, 'age_cap_ms': 1500, 'jitter_cap_ms': 1500, 'spread_cap_ratio': 0.012, 'counterfactual_sample_floor': 3, 'recovery_event_floor_ratio': 0.1}`
- safe/caution_normal/recovery: `0` / `0` / `0`
- recovery attempts/cf sample/cf ev: `0` / `0` / `None`%
- recovered/lost labels: `0` / `0`
- stale/broker override excluded: `0` / `0`
- full/partial fill: `6` / `6`

## Holding Exit
- holding_reviews: `1317`
- exit_signals: `85`
- holding_review_ms_p95: `2462.0`

## Scalp Simulator
- authority: `equal_weight` / fill_policy: `signal_inclusive_best_ask_v1`
- armed/filled/sold: `273` / `273` / `122`
- expired/unpriced/duplicate: `0` / `0` / `510`
- entry_ai_price applied/skip: `73` / `0`
- submit_revalidation warning/block: `239` / `0`
- scale_in filled/unfilled: `0` / `1`
- overnight decision/sell/hold/carry_restored: `15` / `15` / `0` / `0`
- completed_profit_summary: `{'sample': 122, 'win_count': 23, 'loss_count': 99, 'avg_profit_rate': -1.1257, 'median_profit_rate': -1.86, 'downside_p10_profit_rate': -2.63, 'upside_p90_profit_rate': 1.5, 'win_rate': 0.1885, 'loss_rate': 0.8115, 'stddev_profit_rate': 1.7796}`
- post_sell_join: joined=`115` / pending=`7`
- post_sell_mfe_mae_10m: mfe=`1.1385`% / mae=`-3.0443`% / close=`0.3112`%

## Missed Probe Counterfactual
- book: `scalp_score65_74_probe_counterfactual` / role: `missed_buy_probe_counterfactual`
- total/score65_74: `47` / `5`
- avg_expected_ev: `2.1299`% / score65_74_avg_expected_ev: `1.3557`%
- actual_order_submitted: `False` / broker_order_forbidden: `True`
- authority: `missed_probe_ev_only_not_broker_execution`

## Scalp Entry ADM
- artifact: `/home/ubuntu/KORStockScan/data/report/scalp_entry_action_decision_matrix/scalp_entry_action_decision_matrix_2026-06-15.json`
- status: `warning` / authority: `entry_advisory_prompt_context_only`
- total/joined/floor: `1144` / `103` / `20`
- prompt_applied_count: `894`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 1144}`
- forced_action_counts: `{'-': 1144}`
- missing_actions: `[]`
- zero_sample_actions: `['SKIP_STALE']`
- top_actions: `[{'action': 'BUY_NOW', 'sample_count': 10, 'joined_sample': 3, 'source_quality_adjusted_ev_pct': -0.699}, {'action': 'WAIT_REQUOTE', 'sample_count': 18, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'BUY_DEFENSIVE', 'sample_count': 9, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'NO_BUY_AI', 'sample_count': 1004, 'joined_sample': 61, 'source_quality_adjusted_ev_pct': -0.0646}, {'action': 'SKIP_SOURCE_QUALITY', 'sample_count': 14, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}]`

## Lifecycle Decision Matrix
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-06-15.json`
- status: `pass` / version: `lifecycle_decision_matrix_v1_2026-06-15`
- total/joined: `19534` / `17684`
- policy_pass/promote_ready: `5` / `1`
- lifecycle_flow buckets/complete/runtime/workorders: `120` / `79` / `0` / `20`
- holding/exit buckets: `36` / `54`
- holding/exit workorders: `10` / `10`
- lifecycle identity missing/join_rate: `0` / `1.0`
- lifecycle complete_flow_rate: `0.0044`
- incomplete_flow_reason_counts: `{'missing_entry': 17351, 'missing_holding': 17663, 'missing_exit': 17206, 'missing_submit': 17660, 'postclose_exit_without_entry': 511, 'candidate_id_only': 17362, 'sim_record_id_only': 234, 'scale_in_noise_only': 16819}`
- fixed_threshold_roles: `{'hard_safety': ['broker_submit_guard', 'stale_quote_submit_block', 'price_freshness_guard', 'hard_stop', 'protect_stop', 'emergency_stop', 'account_order_cooldown_qty_guard'], 'baseline_prior': ['BUY_SCORE_THRESHOLD', 'VPW_MIN_SCORE', 'strength_momentum_cutoff', 'entry_score_cutoff'], 'bounded_tunable': ['SCALP_ENTRY_LATENCY_MAX_WS_AGE_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_WS_JITTER_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_SPREAD_RATIO_FOR_CAUTION', 'score65_74_recovery_probe', 'soft_stop_whipsaw_confirmation', 'holding_flow_override', 'scale_in_price_guard'], 'legacy_archive': ['fallback_scout_main', 'fallback_single', 'latency_fallback_split_entry', 'legacy_latency_composite', 'closed_shadow_axes']}`
- policy_entries: `[{'stage': 'entry', 'sample': 1280, 'joined_sample': 111, 'stage_ev_composite_pct': 0.6496, 'confidence': 0.9626, 'selected_action': 'BUY_DEFENSIVE', 'source_quality_gate': 'pass', 'promote_ready': True}, {'stage': 'submit', 'sample': 314, 'joined_sample': 141, 'stage_ev_composite_pct': -0.2235, 'confidence': 1.0, 'selected_action': 'NO_CHANGE', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'holding', 'sample': 288, 'joined_sample': 141, 'stage_ev_composite_pct': -0.6796, 'confidence': 1.0, 'selected_action': 'EXIT', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'scale_in', 'sample': 17025, 'joined_sample': 16964, 'stage_ev_composite_pct': -0.6036, 'confidence': 1.0, 'selected_action': 'NO_CHANGE', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'exit', 'sample': 627, 'joined_sample': 327, 'stage_ev_composite_pct': -0.7974, 'confidence': 1.0, 'selected_action': 'EXIT', 'source_quality_gate': 'pass', 'promote_ready': False}]`

## Lifecycle Bucket Discovery
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-06-15.json`
- status: `pass` / human_intervention_required: `False`
- candidates/surfaced: `500` / `133`
- sim_auto/live_auto/new_bucket: `5` / `0` / `0`
- role/window: `new_pattern_detection` / `same_day_source_bundle_plus_rolling_threshold_cycle_consumer`
- parent_count/granularity/conflict: `53` / `target_pass` / `5`
- state_counts: `{'source_only_keep_collecting': 481, 'lifecycle_flow_sim_probe_candidate': 6, 'sim_auto_approved': 5, 'entry_only_sim_auto_approved': 7, 'entry_only_source_candidate': 1}`
- top_surfaced: `[{'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': 1.2181}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_blocked_ai_score_stale_fresh_liquidity_liq', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': 2.8034}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': 1.6373}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': 2.0685}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 14832, 'source_quality_adjusted_ev_pct': -0.7546}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_pyramid_', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 1926, 'source_quality_adjusted_ev_pct': 0.5766}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 186, 'source_quality_adjusted_ev_pct': -0.9546}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wait6579_ev_cohort_stale_fresh_or_unflagge', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 23, 'source_quality_adjusted_ev_pct': 0.9301}]`

## Lifecycle Bucket Windows
- promotion_window: `mtd`
- confirmation_windows: `['rolling5d', 'rolling10d']`
- windows: `{'rolling5d': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-06-15_rolling5d.json', 'window_role': 'rolling_confirmation', 'window_policy': 'rolling5d', 'status': 'pass', 'parent_bucket_count': 34, 'selected_parent_level': 'L1_broad', 'parent_granularity_status': 'target_pass', 'absorbed_child_count': 328, 'absorbed_sample_count': 49160, 'child_conflict_warning_count': 14, 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'parsed'}, 'rolling10d': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-06-15_rolling10d.json', 'window_role': 'rolling_confirmation', 'window_policy': 'rolling10d', 'status': 'pass', 'parent_bucket_count': 36, 'selected_parent_level': 'L1_broad', 'parent_granularity_status': 'target_pass', 'absorbed_child_count': 500, 'absorbed_sample_count': 111473, 'child_conflict_warning_count': 18, 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'parsed'}, 'mtd': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-06-15_mtd.json', 'window_role': 'promotion_confirmation', 'window_policy': 'mtd', 'status': 'pass', 'parent_bucket_count': 41, 'selected_parent_level': 'L1_broad', 'parent_granularity_status': 'target_pass', 'absorbed_child_count': 500, 'absorbed_sample_count': 124527, 'child_conflict_warning_count': 21, 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'parsed'}}`

## Lifecycle AI Context
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_ai_context/lifecycle_ai_context_2026-06-15.json`
- context_version: `lifecycle_ai_context_v1_2026-06-15` / authority: `ai_advisory_prompt_context_only`
- prompt_stage_count: `3` / runtime_effect: `False`
- stage_contexts: `[{'stage': 'entry', 'prompt_injection_allowed': True, 'policy_key': 'entry:weighted_adm_v1', 'alignment_hint': 'BUY_DEFENSIVE', 'context_contribution_score': -0.3263, 'attribution_quality_status': 'observational_only_pending_outcome'}, {'stage': 'submit', 'prompt_injection_allowed': False, 'policy_key': 'submit:weighted_adm_v1', 'alignment_hint': 'NO_CHANGE', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'holding', 'prompt_injection_allowed': True, 'policy_key': 'holding:weighted_adm_v1', 'alignment_hint': 'EXIT', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'scale_in', 'prompt_injection_allowed': False, 'policy_key': 'scale_in:weighted_adm_v1', 'alignment_hint': 'NO_CHANGE', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'exit', 'prompt_injection_allowed': True, 'policy_key': 'exit:weighted_adm_v1', 'alignment_hint': 'EXIT', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}]`

## Lifecycle AI Context Attribution
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_ai_context_attribution/lifecycle_ai_context_attribution_2026-06-15.json`
- eligible/applied/skipped: `3101` / `3101` / `0`
- replay_budget: `30`
- implementation_status: `implemented`
- stage_attribution: `{'entry': {'context_contribution_score': -0.3263, 'bounded_auxiliary_weight': -0.0489, 'attribution_quality_status': 'observational_only_pending_outcome', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': 0.0339, 'no_context_replay_observed': 0}, 'submit': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'holding': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'scale_in': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'exit': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}}`

## Institutional Flow Context
- artifact: `/home/ubuntu/KORStockScan/data/report/institutional_flow_context/institutional_flow_context_2026-06-15.json`
- status: `pass` / authority: `source_only_lifecycle_feature`
- rows ok/partial/missing/token_error: `120` / `0` / `0` / `0`
- join_rate_pct: `100.0`
- source_mix: `{'ka10059+ka10061': 120}`
- top_net_buy: `[{'stock_code': '018880', 'smart_money_net': 15213106, 'foreign_net_roll5': 10848960, 'inst_net_roll5': 4786482, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '003490', 'smart_money_net': 4824547, 'foreign_net_roll5': 5098252, 'inst_net_roll5': 3041908, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '403870', 'smart_money_net': 2733170, 'foreign_net_roll5': 0, 'inst_net_roll5': 6219514, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '093370', 'smart_money_net': 2142669, 'foreign_net_roll5': 9485780, 'inst_net_roll5': 2718087, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '088350', 'smart_money_net': 1600062, 'foreign_net_roll5': 4714152, 'inst_net_roll5': 885942, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '020560', 'smart_money_net': 923657, 'foreign_net_roll5': 173850, 'inst_net_roll5': 843008, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '204320', 'smart_money_net': 746343, 'foreign_net_roll5': 1253655, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}, {'stock_code': '316140', 'smart_money_net': 619884, 'foreign_net_roll5': 0, 'inst_net_roll5': 1432890, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '015760', 'smart_money_net': 547570, 'foreign_net_roll5': 627212, 'inst_net_roll5': 1530953, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '034220', 'smart_money_net': 535387, 'foreign_net_roll5': 0, 'inst_net_roll5': 504851, 'regime': 'INSTITUTION_ACCUMULATION'}]`

## Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-06-15.json`
- fresh: gemini=`False` claude=`True`
- consensus/orders/family_candidates: `0` / `10` / `0`

## Swing Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_2026-06-15.json`
- deepseek_lab_available: `True`
- findings/orders: `5` / `3`
- data_quality_warnings: `0`
- top_level_data_quality_warnings: `0`
- resolved_data_quality_warnings: `0`
- ofi_qi_stale_missing_unique_records: `13`
- ofi_qi_stale_missing_reasons: `{'micro_missing': 6411, 'micro_stale': 0, 'observer_unhealthy': 18, 'micro_not_ready': 6413, 'state_insufficient': 6413}`
- ofi_qi_stale_missing_reason_combinations: `{'micro_not_ready+state_insufficient': 2, 'micro_missing+micro_not_ready+state_insufficient': 6393, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 18}`
- ofi_qi_stale_missing_reason_combination_unique_records: `{'micro_missing+micro_not_ready+state_insufficient': 12, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 6}`
- ofi_qi_observer_unhealthy_overlap: `{'observer_unhealthy_total': 18, 'observer_unhealthy_with_other_reason': 18, 'observer_unhealthy_only': 0}`
- source_quality_blocked_families: `[{'family': 'swing_entry_ofi_qi_execution_quality', 'stage': 'entry', 'metric_role': 'source_quality_gate', 'decision_authority': 'swing_pattern_lab_analysis_workorder_source_only', 'window_policy': 'same_day_pattern_lab_source_quality', 'sample_floor': 1, 'primary_decision_metric': 'source_quality_gate', 'source_quality_gate': 'swing_orderbook_micro_context_ready_or_blocker_provenance_recorded', 'source_contract_version': 'swing_micro_context_source_quality_v1', 'source_contract_status': 'implemented', 'source_quality_blockers': ['entry_ofi_qi_invalid_micro_context'], 'invalid_micro_context_unique_record_count': 13, 'invalid_reason_combination_unique_record_counts': {'micro_missing+micro_not_ready+state_insufficient': 12, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 6}, 'reason_counts': {'micro_missing': 6411, 'micro_stale': 0, 'observer_unhealthy': 18, 'micro_not_ready': 6413, 'state_insufficient': 6413}, 'reason_combination_counts': {'micro_not_ready+state_insufficient': 2, 'micro_missing+micro_not_ready+state_insufficient': 6393, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 18}, 'observer_unhealthy_overlap': {'observer_unhealthy_total': 18, 'observer_unhealthy_with_other_reason': 18, 'observer_unhealthy_only': 0}, 'automation_input': True, 'runtime_effect': False, 'allowed_runtime_apply': False, 'forbidden_uses': ['swing_real_order_enable', 'one_share_real_canary', 'scale_in_real_canary', 'runtime_threshold_mutation', 'provider_route_change', 'bot_restart', 'recommendation_history_replace'], 'provenance_gap_count': 0, 'readiness_counts': {'micro_ready_count': 0, 'micro_insufficient_samples_count': 6413, 'micro_not_ready_count': 6413, 'state_insufficient_count': 6413}, 'spread_quality': {'wide_spread_threshold_ticks': 10, 'wide_spread_count': 0, 'wide_spread_rate': 0.0, 'max_spread_ticks': None, 'hard_block': False, 'decision_use': 'source_quality_adjusted_ev_penalty_or_filter_candidate'}, 'source_quality_reason_stage_split': {'micro_missing': 6411, 'micro_not_ready': 6413, 'state_insufficient': 6413, 'observer_unhealthy': 18, 'provenance_gap': 0}}, {'family': 'swing_scale_in_ofi_qi_confirmation', 'stage': 'scale_in', 'metric_role': 'source_quality_gate', 'decision_authority': 'swing_pattern_lab_analysis_workorder_source_only', 'window_policy': 'same_day_pattern_lab_source_quality', 'sample_floor': 1, 'primary_decision_metric': 'source_quality_gate', 'source_quality_gate': 'swing_orderbook_micro_context_ready_or_blocker_provenance_recorded', 'source_contract_version': 'swing_micro_context_source_quality_v1', 'source_contract_status': 'implemented', 'source_quality_blockers': ['scale_in_ofi_qi_invalid_micro_context'], 'invalid_micro_context_unique_record_count': 2, 'invalid_reason_combination_unique_record_counts': {'micro_missing+micro_not_ready+state_insufficient': 12, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 6}, 'reason_counts': {'micro_missing': 6411, 'micro_stale': 0, 'observer_unhealthy': 18, 'micro_not_ready': 6413, 'state_insufficient': 6413}, 'reason_combination_counts': {'micro_not_ready+state_insufficient': 2, 'micro_missing+micro_not_ready+state_insufficient': 6393, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 18}, 'observer_unhealthy_overlap': {'observer_unhealthy_total': 18, 'observer_unhealthy_with_other_reason': 18, 'observer_unhealthy_only': 0}, 'automation_input': True, 'runtime_effect': False, 'allowed_runtime_apply': False, 'forbidden_uses': ['swing_real_order_enable', 'one_share_real_canary', 'scale_in_real_canary', 'runtime_threshold_mutation', 'provider_route_change', 'bot_restart', 'recommendation_history_replace'], 'provenance_gap_count': 0, 'readiness_counts': {'micro_ready_count': 0, 'micro_insufficient_samples_count': 6413, 'micro_not_ready_count': 6413, 'state_insufficient_count': 6413}, 'spread_quality': {'wide_spread_threshold_ticks': 10, 'wide_spread_count': 0, 'wide_spread_rate': 0.0, 'max_spread_ticks': None, 'hard_block': False, 'decision_use': 'source_quality_adjusted_ev_penalty_or_filter_candidate'}, 'source_quality_reason_stage_split': {'micro_missing': 6411, 'micro_not_ready': 6413, 'state_insufficient': 6413, 'observer_unhealthy': 18, 'provenance_gap': 0}}]`
- carryover_warnings: `0`
- population_split_available: `True`

## Swing Strategy Discovery Sim
- artifact: `/home/ubuntu/KORStockScan/data/report/swing_strategy_discovery_ev/swing_strategy_discovery_ev_2026-06-15.json`
- authority: `swing_sim_exploration_only` / source_only: `True`
- candidate/arm/policy_exit_rows: `677` / `4310` / `4310`
- labeled/pending_future_quotes: `377` / `3425`
- implementation_status: `implemented`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- surviving/avoid_bucket_count: `1` / `15`
- runtime_effect: `False`

## Pipeline Event Verbosity
- artifact: `/home/ubuntu/KORStockScan/data/report/pipeline_event_verbosity/pipeline_event_verbosity_2026-06-15.json`
- state: `v2_shadow_pending_flush`
- recommended_workorder_state: `observe_pending_next_flush`
- high_volume_line_count: `34562`
- high_volume_byte_share_pct: `5.25`
- parity_ok: `False`
- suppress_eligibility: `False`

## Codebase Performance Workorder Source
- artifact: `/home/ubuntu/KORStockScan/data/report/codebase_performance_workorder/codebase_performance_workorder_2026-06-15.json`
- authority: `ops_performance_workorder_source`
- accepted/deferred/rejected: `7` / `3` / `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`

## Pattern Lab Audits
- currentness: status=`pass` fail=`0` orders=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-06-15.json`
- ai_review: status=`warning` orders=`4` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_ai_review/pattern_lab_ai_review_2026-06-15.json`
- time_window_regime_counterfactual: status=`pass` artifact=`/home/ubuntu/KORStockScan/data/report/time_window_regime_counterfactual/time_window_regime_counterfactual_2026-06-15.json`
- producer_gap_discovery: status=`pass` orders=`0` artifact=`/home/ubuntu/KORStockScan/data/report/producer_gap_discovery/producer_gap_discovery_2026-06-15.json`
- stage_hook_workorder_discovery: status=`warning` orders=`2` artifact=`/home/ubuntu/KORStockScan/data/report/stage_hook_workorder_discovery/stage_hook_workorder_discovery_2026-06-15.json`
- propagation: status=`warning` fail=`0` warnings=`2` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_2026-06-15.json`

## Swing Runtime Approval
- request_report: `/home/ubuntu/KORStockScan/data/report/swing_runtime_approval/swing_runtime_approval_2026-06-12.json`
- approval_artifact: `-`
- requested/approved/live_dry_run: `1` / `1` / `1`
- dry_run_forced: `True`
- legacy_phase0_real_canary_ignored: `False`
- blocked: `[]`

## Code Improvement Workorder
- artifact: `/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-06-15.json`
- markdown: `/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-06-15.md`
- selected_order_count: `160`
- decision_counts: `{'attach_existing_family': 144, 'design_family_candidate': 5, 'defer_evidence': 8, 'reject': 3}`

## Approval Requests
- none

## Swing Approval Requests
- `swing_gatekeeper_reject_cooldown` approval_id=`swing_runtime_approval:2026-06-12:swing_gatekeeper_reject_cooldown` score=`0.955` target_env_keys=`['ML_GATEKEEPER_REJECT_COOLDOWN']`

## Calibration Decisions
## Code Improvement Top Orders
- `order_entry_submit_drought_auto_resolution` decision=`attach_existing_family` subsystem=`runtime_instrumentation`
- `order_entry_broker_receipt_contract_gap_review` decision=`attach_existing_family` subsystem=`runtime_instrumentation`
- `order_entry_fill_quality_contract_gap_review` decision=`attach_existing_family` subsystem=`runtime_instrumentation`

- `soft_stop_whipsaw_confirmation`: `adjust_up` sample=`5237/10`
- `holding_flow_ofi_smoothing`: `hold` sample=`745/20`
- `protect_trailing_smoothing`: `adjust_down` sample=`95/20`
- `trailing_continuation`: `freeze` sample=`395/20`
- `market_regime_continuous_thresholds`: `hold_sample` sample=`8/10`
- `pre_submit_price_guard`: `hold` sample=`3/1`
- `dynamic_entry_price_resolver`: `hold_sample` sample=`862/20`
- `entry_price_execution_quality`: `hold` sample=`115/5`
- `score65_74_recovery_probe`: `adjust_up` sample=`224/20`
- `strength_momentum_soft_gate_p1`: `hold` sample=`22366/20`
- `overbought_pullback_guard_p1`: `hold` sample=`4917/20`
- `liquidity_pre_submit_guard_p1`: `hold` sample=`4229/20`
- `bad_entry_refined_canary`: `adjust_up` sample=`89390/10`
- `holding_exit_decision_matrix_advisory`: `hold_no_edge` sample=`0/1`
- `lifecycle_decision_matrix_runtime`: `adjust_up` sample=`19534/20`
- `scale_in_price_guard`: `hold` sample=`971/20`
- `position_sizing_dynamic_formula`: `hold_sample` sample=`0/30`

## Warnings
- `scalp_entry_adm:unknown_bucket_source_quality_gap`
- `lifecycle_bucket_discovery:source_contract_drift_warning`
- `lifecycle_bucket_discovery:source_contract_drift_warning`
- `swing_strategy_discovery:pending_future_quotes`
- `swing_strategy_discovery:clean_tuning_baseline_swing_discovery_lookback_filtered`
- `swing_lifecycle_decision_matrix:pending_future_quotes`
- `swing_lifecycle_decision_matrix:clean_tuning_baseline_swing_discovery_lookback_filtered`
- `pattern_lab_ai_review_warning`
- `pattern_lab_propagation_audit_warning`
