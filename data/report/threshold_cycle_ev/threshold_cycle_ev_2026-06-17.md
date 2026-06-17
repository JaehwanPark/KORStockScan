# Threshold Cycle Daily EV Report - 2026-06-17

## Summary
- status: `warning`
- warning_count: `16`
- source_quality: status=`pass` allowed=`True`
- samples real/sim: `8` / `1045`
- live_auto_ready_count: `0`
- primary_verdict: `sim_evidence_present_no_live_bucket`

## Runtime Apply
- status: `auto_bounded_live_ready`
- runtime_change: `True`
- selected_families: `soft_stop_whipsaw_confirmation, score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, profit_stagnation_exit_runtime, latency_spread_relief_real_operator_override, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, ai_watching_score_smoothing_report_only, lifecycle_decision_matrix_runtime, weak_pullback_entry_block_runtime, buy_side_time_block_disable_runtime`

## Daily EV
- completed: `0` / open: `0`
- win/loss: `0` / `0` (`0.0`%)
- avg_profit_rate: `0.0`%
- realized_pnl_krw: `0`
- full_fill_completed_avg_profit_rate: `0.0`%

## Entry Funnel
- budget_pass_to_submitted: `4` / `13627` (`0.03`%)
- latency pass/block: `65` / `13560`
- latency submit routing: `latency_classifier_runtime_semantics_gap`
- latency recommended action: `reject` (`recovery_count=0 below floor=4531`)
- latency profile generation: `{'mode': 'grid_quantile_search', 'profile_count': 900, 'age_cap_ms': 1500, 'jitter_cap_ms': 1500, 'spread_cap_ratio': 0.012, 'counterfactual_sample_floor': 3, 'recovery_event_floor_ratio': 0.1}`
- safe/caution_normal/recovery: `0` / `0` / `0`
- recovery attempts/cf sample/cf ev: `0` / `0` / `None`%
- recovered/lost labels: `0` / `0`
- stale/broker override excluded: `0` / `0`
- full/partial fill: `0` / `0`

## Holding Exit
- holding_reviews: `1590`
- exit_signals: `111`
- holding_review_ms_p95: `1989.0`

## Scalp Simulator
- authority: `equal_weight` / fill_policy: `signal_inclusive_best_ask_v1`
- armed/filled/sold: `181` / `181` / `183`
- expired/unpriced/duplicate: `0` / `0` / `641`
- entry_ai_price applied/skip: `58` / `0`
- submit_revalidation warning/block: `141` / `0`
- scale_in filled/unfilled: `1` / `24`
- overnight decision/sell/hold/carry_restored: `16` / `16` / `0` / `0`
- completed_profit_summary: `{'sample': 183, 'win_count': 43, 'loss_count': 140, 'avg_profit_rate': -1.1221, 'median_profit_rate': -1.93, 'downside_p10_profit_rate': -2.79, 'upside_p90_profit_rate': 1.86, 'win_rate': 0.235, 'loss_rate': 0.765, 'stddev_profit_rate': 2.222}`
- post_sell_join: joined=`171` / pending=`12`
- post_sell_mfe_mae_10m: mfe=`1.432`% / mae=`-3.6402`% / close=`-0.0184`%

## Missed Probe Counterfactual
- book: `scalp_score65_74_probe_counterfactual` / role: `missed_buy_probe_counterfactual`
- total/score65_74: `75` / `10`
- avg_expected_ev: `2.8002`% / score65_74_avg_expected_ev: `0.4854`%
- actual_order_submitted: `False` / broker_order_forbidden: `True`
- authority: `missed_probe_ev_only_not_broker_execution`

## Scalp Entry ADM
- artifact: `/home/ubuntu/KORStockScan/data/report/scalp_entry_action_decision_matrix/scalp_entry_action_decision_matrix_2026-06-17.json`
- status: `pass` / authority: `entry_advisory_prompt_context_only`
- total/joined/floor: `1666` / `165` / `20`
- prompt_applied_count: `1204`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 1666}`
- forced_action_counts: `{'-': 1666}`
- missing_actions: `[]`
- zero_sample_actions: `['SKIP_STALE']`
- top_actions: `[{'action': 'BUY_NOW', 'sample_count': 11, 'joined_sample': 9, 'source_quality_adjusted_ev_pct': 0.6191}, {'action': 'WAIT_REQUOTE', 'sample_count': 15, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'BUY_DEFENSIVE', 'sample_count': 5, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'NO_BUY_AI', 'sample_count': 1489, 'joined_sample': 59, 'source_quality_adjusted_ev_pct': -0.0468}, {'action': 'SKIP_SOURCE_QUALITY', 'sample_count': 31, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}]`

## Lifecycle Decision Matrix
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-06-17.json`
- status: `pass` / version: `lifecycle_decision_matrix_v1_2026-06-17`
- total/joined: `23836` / `21601`
- policy_pass/promote_ready: `5` / `1`
- lifecycle_flow buckets/complete/runtime/workorders: `155` / `129` / `0` / `20`
- holding/exit buckets: `34` / `46`
- holding/exit workorders: `10` / `10`
- lifecycle identity missing/join_rate: `0` / `1.0`
- lifecycle complete_flow_rate: `0.0058`
- incomplete_flow_reason_counts: `{'missing_entry': 21657, 'missing_holding': 21947, 'missing_exit': 21764, 'missing_submit': 21947, 'candidate_id_only': 21678, 'sim_record_id_only': 45, 'scale_in_noise_only': 21430, 'postclose_exit_without_entry': 210}`
- fixed_threshold_roles: `{'hard_safety': ['broker_submit_guard', 'stale_quote_submit_block', 'price_freshness_guard', 'hard_stop', 'protect_stop', 'emergency_stop', 'account_order_cooldown_qty_guard'], 'baseline_prior': ['BUY_SCORE_THRESHOLD', 'VPW_MIN_SCORE', 'strength_momentum_cutoff', 'entry_score_cutoff'], 'bounded_tunable': ['SCALP_ENTRY_LATENCY_MAX_WS_AGE_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_WS_JITTER_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_SPREAD_RATIO_FOR_CAUTION', 'score65_74_recovery_probe', 'soft_stop_whipsaw_confirmation', 'holding_flow_override', 'scale_in_price_guard'], 'legacy_archive': ['fallback_scout_main', 'fallback_single', 'latency_fallback_split_entry', 'legacy_latency_composite', 'closed_shadow_axes']}`
- policy_entries: `[{'stage': 'entry', 'sample': 1594, 'joined_sample': 140, 'stage_ev_composite_pct': 0.922, 'confidence': 1.0, 'selected_action': 'BUY_DEFENSIVE', 'source_quality_gate': 'pass', 'promote_ready': True}, {'stage': 'submit', 'sample': 213, 'joined_sample': 181, 'stage_ev_composite_pct': -0.3372, 'confidence': 1.0, 'selected_action': 'NO_CHANGE', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'holding', 'sample': 197, 'joined_sample': 181, 'stage_ev_composite_pct': -0.7509, 'confidence': 1.0, 'selected_action': 'EXIT', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'scale_in', 'sample': 21452, 'joined_sample': 20894, 'stage_ev_composite_pct': -0.3612, 'confidence': 1.0, 'selected_action': 'NO_CHANGE', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'exit', 'sample': 380, 'joined_sample': 205, 'stage_ev_composite_pct': -0.7896, 'confidence': 1.0, 'selected_action': 'EXIT', 'source_quality_gate': 'pass', 'promote_ready': False}]`

## Lifecycle Bucket Discovery
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-06-17.json`
- status: `pass` / human_intervention_required: `False`
- candidates/surfaced: `500` / `168`
- sim_auto/live_auto/new_bucket: `7` / `0` / `0`
- role/window: `new_pattern_detection` / `same_day_source_bundle_plus_rolling_threshold_cycle_consumer`
- parent_count/granularity/conflict: `32` / `target_pass` / `8`
- state_counts: `{'source_only_keep_collecting': 472, 'lifecycle_flow_sim_probe_candidate': 15, 'sim_auto_approved': 7, 'entry_only_sim_auto_approved': 5, 'entry_only_source_candidate': 1}`
- top_surfaced: `[{'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': 1.9619}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_stale_block_liquidi', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': 2.2855}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': 1.8375}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': 2.2247}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_blocked_ai_score_stale_fresh_liquidity_liq', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': 1.1079}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': 1.0604}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': 2.3708}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': 1.7779}]`

## Lifecycle Bucket Windows
- promotion_window: `mtd`
- confirmation_windows: `['rolling5d', 'rolling10d']`
- windows: `{'rolling5d': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-06-17_rolling5d.json', 'window_role': 'rolling_confirmation', 'window_policy': 'rolling5d', 'status': 'pass', 'parent_bucket_count': 39, 'selected_parent_level': 'L1_broad', 'parent_granularity_status': 'target_pass', 'absorbed_child_count': 315, 'absorbed_sample_count': 60472, 'child_conflict_warning_count': 14, 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'parsed'}, 'rolling10d': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-06-17_rolling10d.json', 'window_role': 'rolling_confirmation', 'window_policy': 'rolling10d', 'status': 'pass', 'parent_bucket_count': 38, 'selected_parent_level': 'L1_broad', 'parent_granularity_status': 'target_pass', 'absorbed_child_count': 500, 'absorbed_sample_count': 152017, 'child_conflict_warning_count': 20, 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'parsed'}, 'mtd': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-06-17_mtd.json', 'window_role': 'promotion_confirmation', 'window_policy': 'mtd', 'status': 'pass', 'parent_bucket_count': 42, 'selected_parent_level': 'L1_broad', 'parent_granularity_status': 'target_pass', 'absorbed_child_count': 500, 'absorbed_sample_count': 166167, 'child_conflict_warning_count': 19, 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'parsed'}}`

## Lifecycle AI Context
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_ai_context/lifecycle_ai_context_2026-06-17.json`
- context_version: `lifecycle_ai_context_v1_2026-06-17` / authority: `ai_advisory_prompt_context_only`
- prompt_stage_count: `3` / runtime_effect: `False`
- stage_contexts: `[{'stage': 'entry', 'prompt_injection_allowed': True, 'policy_key': 'entry:weighted_adm_v1', 'alignment_hint': 'BUY_DEFENSIVE', 'context_contribution_score': -0.3233, 'attribution_quality_status': 'observational_only_pending_outcome'}, {'stage': 'submit', 'prompt_injection_allowed': False, 'policy_key': 'submit:weighted_adm_v1', 'alignment_hint': 'NO_CHANGE', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'holding', 'prompt_injection_allowed': True, 'policy_key': 'holding:weighted_adm_v1', 'alignment_hint': 'EXIT', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'scale_in', 'prompt_injection_allowed': False, 'policy_key': 'scale_in:weighted_adm_v1', 'alignment_hint': 'NO_CHANGE', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'exit', 'prompt_injection_allowed': True, 'policy_key': 'exit:weighted_adm_v1', 'alignment_hint': 'EXIT', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}]`

## Lifecycle AI Context Attribution
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_ai_context_attribution/lifecycle_ai_context_attribution_2026-06-17.json`
- eligible/applied/skipped: `3332` / `3332` / `0`
- replay_budget: `30`
- implementation_status: `implemented`
- stage_attribution: `{'entry': {'context_contribution_score': -0.3233, 'bounded_auxiliary_weight': -0.0485, 'attribution_quality_status': 'observational_only_pending_outcome', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': 0.0381, 'no_context_replay_observed': 0}, 'submit': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'holding': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'scale_in': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'exit': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}}`

## Institutional Flow Context
- artifact: `/home/ubuntu/KORStockScan/data/report/institutional_flow_context/institutional_flow_context_2026-06-17.json`
- status: `pass` / authority: `source_only_lifecycle_feature`
- rows ok/partial/missing/token_error: `120` / `0` / `0` / `0`
- join_rate_pct: `100.0`
- source_mix: `{'ka10059+ka10061': 120}`
- top_net_buy: `[{'stock_code': '530036', 'smart_money_net': 53405562, 'foreign_net_roll5': 0, 'inst_net_roll5': 79544860, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '233740', 'smart_money_net': 4272195, 'foreign_net_roll5': 526566, 'inst_net_roll5': 14760105, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '279570', 'smart_money_net': 2062758, 'foreign_net_roll5': 2690446, 'inst_net_roll5': 9760139, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '042660', 'smart_money_net': 1810325, 'foreign_net_roll5': 1527609, 'inst_net_roll5': 532176, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '088350', 'smart_money_net': 946016, 'foreign_net_roll5': 4818997, 'inst_net_roll5': 842124, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '018000', 'smart_money_net': 706315, 'foreign_net_roll5': 0, 'inst_net_roll5': 20984, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '067290', 'smart_money_net': 529336, 'foreign_net_roll5': 0, 'inst_net_roll5': 20837, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '000660', 'smart_money_net': 420350, 'foreign_net_roll5': 1375649, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}, {'stock_code': '010140', 'smart_money_net': 252807, 'foreign_net_roll5': 0, 'inst_net_roll5': 3260213, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '000370', 'smart_money_net': 250675, 'foreign_net_roll5': 640514, 'inst_net_roll5': 155335, 'regime': 'DUAL_ACCUMULATION'}]`

## Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-06-17.json`
- fresh: gemini=`False` claude=`True`
- consensus/orders/family_candidates: `0` / `10` / `0`

## Swing Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_2026-06-17.json`
- deepseek_lab_available: `True`
- findings/orders: `5` / `3`
- data_quality_warnings: `0`
- top_level_data_quality_warnings: `0`
- resolved_data_quality_warnings: `0`
- ofi_qi_stale_missing_unique_records: `13`
- ofi_qi_stale_missing_reasons: `{'micro_missing': 12301, 'micro_stale': 0, 'observer_unhealthy': 4, 'micro_not_ready': 12312, 'state_insufficient': 12312}`
- ofi_qi_stale_missing_reason_combinations: `{'micro_not_ready+state_insufficient': 11, 'micro_missing+micro_not_ready+state_insufficient': 12297, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 4}`
- ofi_qi_stale_missing_reason_combination_unique_records: `{'micro_missing+micro_not_ready+state_insufficient': 13, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 1}`
- ofi_qi_observer_unhealthy_overlap: `{'observer_unhealthy_total': 4, 'observer_unhealthy_with_other_reason': 4, 'observer_unhealthy_only': 0}`
- source_quality_blocked_families: `[{'family': 'swing_entry_ofi_qi_execution_quality', 'stage': 'entry', 'metric_role': 'source_quality_gate', 'decision_authority': 'swing_pattern_lab_analysis_workorder_source_only', 'window_policy': 'same_day_pattern_lab_source_quality', 'sample_floor': 1, 'primary_decision_metric': 'source_quality_gate', 'source_quality_gate': 'swing_orderbook_micro_context_ready_or_blocker_provenance_recorded', 'source_contract_version': 'swing_micro_context_source_quality_v1', 'source_contract_status': 'implemented', 'source_quality_blockers': ['entry_ofi_qi_invalid_micro_context'], 'invalid_micro_context_unique_record_count': 13, 'invalid_reason_combination_unique_record_counts': {'micro_missing+micro_not_ready+state_insufficient': 13, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 1}, 'reason_counts': {'micro_missing': 12301, 'micro_stale': 0, 'observer_unhealthy': 4, 'micro_not_ready': 12312, 'state_insufficient': 12312}, 'reason_combination_counts': {'micro_not_ready+state_insufficient': 11, 'micro_missing+micro_not_ready+state_insufficient': 12297, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 4}, 'observer_unhealthy_overlap': {'observer_unhealthy_total': 4, 'observer_unhealthy_with_other_reason': 4, 'observer_unhealthy_only': 0}, 'automation_input': True, 'runtime_effect': False, 'allowed_runtime_apply': False, 'forbidden_uses': ['swing_real_order_enable', 'one_share_real_canary', 'scale_in_real_canary', 'runtime_threshold_mutation', 'provider_route_change', 'bot_restart', 'recommendation_history_replace'], 'provenance_gap_count': 0, 'readiness_counts': {'micro_ready_count': 0, 'micro_insufficient_samples_count': 12312, 'micro_not_ready_count': 12312, 'state_insufficient_count': 12312}, 'spread_quality': {'wide_spread_threshold_ticks': 10, 'wide_spread_count': 0, 'wide_spread_rate': 0.0, 'max_spread_ticks': None, 'hard_block': False, 'decision_use': 'source_quality_adjusted_ev_penalty_or_filter_candidate'}, 'source_quality_reason_stage_split': {'micro_missing': 12301, 'micro_not_ready': 12312, 'state_insufficient': 12312, 'observer_unhealthy': 4, 'provenance_gap': 0}}, {'family': 'swing_scale_in_ofi_qi_confirmation', 'stage': 'scale_in', 'metric_role': 'source_quality_gate', 'decision_authority': 'swing_pattern_lab_analysis_workorder_source_only', 'window_policy': 'same_day_pattern_lab_source_quality', 'sample_floor': 1, 'primary_decision_metric': 'source_quality_gate', 'source_quality_gate': 'swing_orderbook_micro_context_ready_or_blocker_provenance_recorded', 'source_contract_version': 'swing_micro_context_source_quality_v1', 'source_contract_status': 'implemented', 'source_quality_blockers': ['scale_in_ofi_qi_invalid_micro_context'], 'invalid_micro_context_unique_record_count': 1, 'invalid_reason_combination_unique_record_counts': {'micro_missing+micro_not_ready+state_insufficient': 13, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 1}, 'reason_counts': {'micro_missing': 12301, 'micro_stale': 0, 'observer_unhealthy': 4, 'micro_not_ready': 12312, 'state_insufficient': 12312}, 'reason_combination_counts': {'micro_not_ready+state_insufficient': 11, 'micro_missing+micro_not_ready+state_insufficient': 12297, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 4}, 'observer_unhealthy_overlap': {'observer_unhealthy_total': 4, 'observer_unhealthy_with_other_reason': 4, 'observer_unhealthy_only': 0}, 'automation_input': True, 'runtime_effect': False, 'allowed_runtime_apply': False, 'forbidden_uses': ['swing_real_order_enable', 'one_share_real_canary', 'scale_in_real_canary', 'runtime_threshold_mutation', 'provider_route_change', 'bot_restart', 'recommendation_history_replace'], 'provenance_gap_count': 0, 'readiness_counts': {'micro_ready_count': 0, 'micro_insufficient_samples_count': 12312, 'micro_not_ready_count': 12312, 'state_insufficient_count': 12312}, 'spread_quality': {'wide_spread_threshold_ticks': 10, 'wide_spread_count': 0, 'wide_spread_rate': 0.0, 'max_spread_ticks': None, 'hard_block': False, 'decision_use': 'source_quality_adjusted_ev_penalty_or_filter_candidate'}, 'source_quality_reason_stage_split': {'micro_missing': 12301, 'micro_not_ready': 12312, 'state_insufficient': 12312, 'observer_unhealthy': 4, 'provenance_gap': 0}}]`
- carryover_warnings: `0`
- population_split_available: `True`

## Swing Strategy Discovery Sim
- artifact: `/home/ubuntu/KORStockScan/data/report/swing_strategy_discovery_ev/swing_strategy_discovery_ev_2026-06-17.json`
- authority: `swing_sim_exploration_only` / source_only: `True`
- candidate/arm/policy_exit_rows: `860` / `5513` / `5513`
- labeled/pending_future_quotes: `457` / `3980`
- implementation_status: `implemented`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- surviving/avoid_bucket_count: `1` / `8`
- runtime_effect: `False`

## Pipeline Event Verbosity
- artifact: `/home/ubuntu/KORStockScan/data/report/pipeline_event_verbosity/pipeline_event_verbosity_2026-06-17.json`
- state: `v2_shadow_pending_flush`
- recommended_workorder_state: `observe_pending_next_flush`
- high_volume_line_count: `65981`
- high_volume_byte_share_pct: `4.86`
- parity_ok: `False`
- suppress_eligibility: `False`

## Codebase Performance Workorder Source
- artifact: `/home/ubuntu/KORStockScan/data/report/codebase_performance_workorder/codebase_performance_workorder_2026-06-17.json`
- authority: `ops_performance_workorder_source`
- accepted/deferred/rejected: `7` / `3` / `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`

## Pattern Lab Audits
- currentness: status=`pass` fail=`0` orders=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-06-17.json`
- ai_review: status=`warning` orders=`5` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_ai_review/pattern_lab_ai_review_2026-06-17.json`
- time_window_regime_counterfactual: status=`pass` artifact=`/home/ubuntu/KORStockScan/data/report/time_window_regime_counterfactual/time_window_regime_counterfactual_2026-06-17.json`
- producer_gap_discovery: status=`pass` orders=`0` artifact=`/home/ubuntu/KORStockScan/data/report/producer_gap_discovery/producer_gap_discovery_2026-06-17.json`
- stage_hook_workorder_discovery: status=`warning` orders=`2` artifact=`/home/ubuntu/KORStockScan/data/report/stage_hook_workorder_discovery/stage_hook_workorder_discovery_2026-06-17.json`
- propagation: status=`warning` fail=`0` warnings=`2` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_2026-06-17.json`

## Swing Runtime Approval
- request_report: `/home/ubuntu/KORStockScan/data/report/swing_runtime_approval/swing_runtime_approval_2026-06-16.json`
- approval_artifact: `-`
- requested/approved/live_dry_run: `0` / `0` / `0`
- dry_run_forced: `False`
- legacy_phase0_real_canary_ignored: `False`
- blocked: `[]`

## Code Improvement Workorder
- artifact: `/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-06-17.json`
- markdown: `/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-06-17.md`
- selected_order_count: `122`
- decision_counts: `{'implement_now': 1, 'attach_existing_family': 140, 'design_family_candidate': 5, 'defer_evidence': 8, 'reject': 3}`

## Approval Requests
- none

## Swing Approval Requests
- none

## Calibration Decisions
## Code Improvement Top Orders
- `order_swing_ofi_qi_stale_or_missing_context` decision=`implement_now` subsystem=`swing_orderbook_micro_context`
- `order_entry_submit_drought_auto_resolution` decision=`attach_existing_family` subsystem=`runtime_instrumentation`
- `order_entry_broker_receipt_contract_gap_review` decision=`attach_existing_family` subsystem=`runtime_instrumentation`

- `soft_stop_whipsaw_confirmation`: `adjust_up` sample=`8608/10`
- `holding_flow_ofi_smoothing`: `hold` sample=`1810/20`
- `protect_trailing_smoothing`: `adjust_down` sample=`95/20`
- `trailing_continuation`: `freeze` sample=`463/20`
- `market_regime_continuous_thresholds`: `hold_sample` sample=`8/10`
- `pre_submit_price_guard`: `hold` sample=`0/1`
- `dynamic_entry_price_resolver`: `hold_sample` sample=`561/20`
- `entry_price_execution_quality`: `hold` sample=`57/5`
- `score65_74_recovery_probe`: `adjust_up` sample=`255/20`
- `strength_momentum_soft_gate_p1`: `hold` sample=`30206/20`
- `overbought_pullback_guard_p1`: `hold` sample=`2916/20`
- `liquidity_pre_submit_guard_p1`: `hold` sample=`4304/20`
- `bad_entry_refined_canary`: `adjust_up` sample=`120616/10`
- `holding_exit_decision_matrix_advisory`: `hold_no_edge` sample=`9/1`
- `lifecycle_decision_matrix_runtime`: `adjust_up` sample=`23836/20`
- `scale_in_price_guard`: `hold` sample=`1423/20`
- `position_sizing_dynamic_formula`: `hold_sample` sample=`46/30`

## Warnings
- `lifecycle_bucket_discovery:source_contract_drift_warning`
- `lifecycle_bucket_discovery:ai_review_metric_contract_missing:source_contract:source_added:institutional_flow_context:source_key_institutional_flow_context`
- `lifecycle_bucket_discovery:ai_review_evidence_authority_violation:source_contract:source_added:institutional_flow_context:source_key_institutional_flow_context`
- `lifecycle_bucket_discovery:taxonomy_discovery_review:ai_review_metric_contract_missing:source_contract:source_added:institutional_flow_context:source_key_institutional_flow_context`
- `lifecycle_bucket_discovery:taxonomy_discovery_review:ai_review_evidence_authority_violation:source_contract:source_added:institutional_flow_context:source_key_institutional_flow_context`
- `lifecycle_bucket_discovery:source_contract_drift_warning`
- `lifecycle_bucket_discovery:ai_review_metric_contract_missing:source_contract:source_added:institutional_flow_context:source_key_institutional_flow_context`
- `lifecycle_bucket_discovery:ai_review_evidence_authority_violation:source_contract:source_added:institutional_flow_context:source_key_institutional_flow_context`
- `lifecycle_bucket_discovery:taxonomy_discovery_review:ai_review_metric_contract_missing:source_contract:source_added:institutional_flow_context:source_key_institutional_flow_context`
- `lifecycle_bucket_discovery:taxonomy_discovery_review:ai_review_evidence_authority_violation:source_contract:source_added:institutional_flow_context:source_key_institutional_flow_context`
- `swing_strategy_discovery:pending_future_quotes`
- `swing_strategy_discovery:clean_tuning_baseline_swing_discovery_lookback_filtered`
- `swing_lifecycle_decision_matrix:pending_future_quotes`
- `swing_lifecycle_decision_matrix:clean_tuning_baseline_swing_discovery_lookback_filtered`
- `pattern_lab_ai_review_warning`
- `pattern_lab_propagation_audit_warning`
