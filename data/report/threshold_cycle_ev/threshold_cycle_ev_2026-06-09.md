# Threshold Cycle Daily EV Report - 2026-06-09

## Runtime Apply
- status: `auto_bounded_live_ready`
- runtime_change: `True`
- selected_families: `soft_stop_whipsaw_confirmation, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, lifecycle_decision_matrix_runtime`

## Daily EV
- completed: `1` / open: `0`
- win/loss: `1` / `0` (`100.0`%)
- avg_profit_rate: `1.52`%
- realized_pnl_krw: `1734`
- full_fill_completed_avg_profit_rate: `1.52`%

## Entry Funnel
- budget_pass_to_submitted: `2` / `5169` (`0.04`%)
- latency pass/block: `29` / `5140`
- latency submit routing: `latency_classifier_runtime_semantics_gap`
- latency recommended action: `reject` (`recovery_count=0 below floor=1404`)
- latency profile generation: `{'mode': 'grid_quantile_search', 'profile_count': 810, 'age_cap_ms': 1500, 'jitter_cap_ms': 1500, 'spread_cap_ratio': 0.012, 'counterfactual_sample_floor': 3, 'recovery_event_floor_ratio': 0.1}`
- safe/caution_normal/recovery: `0` / `0` / `0`
- recovery attempts/cf sample/cf ev: `0` / `0` / `None`%
- recovered/lost labels: `0` / `0`
- stale/broker override excluded: `0` / `0`
- full/partial fill: `1` / `0`

## Holding Exit
- holding_reviews: `1881`
- exit_signals: `205`
- holding_review_ms_p95: `2079.0`

## Scalp Simulator
- authority: `equal_weight` / fill_policy: `signal_inclusive_best_ask_v1`
- armed/filled/sold: `281` / `281` / `281`
- expired/unpriced/duplicate: `0` / `0` / `999`
- entry_ai_price applied/skip: `99` / `0`
- submit_revalidation warning/block: `252` / `0`
- scale_in filled/unfilled: `0` / `0`
- overnight decision/sell/hold/carry_restored: `16` / `16` / `0` / `0`
- completed_profit_summary: `{'sample': 281, 'win_count': 72, 'loss_count': 209, 'avg_profit_rate': -1.1282, 'median_profit_rate': -1.76, 'downside_p10_profit_rate': -2.83, 'upside_p90_profit_rate': 1.35, 'win_rate': 0.2562, 'loss_rate': 0.7438, 'stddev_profit_rate': 2.0251}`
- post_sell_join: joined=`277` / pending=`4`
- post_sell_mfe_mae_10m: mfe=`1.5889`% / mae=`-5.3016`% / close=`0.2773`%

## Missed Probe Counterfactual
- book: `scalp_score65_74_probe_counterfactual` / role: `missed_buy_probe_counterfactual`
- total/score65_74: `114` / `0`
- avg_expected_ev: `4.2172`% / score65_74_avg_expected_ev: `0.0`%
- actual_order_submitted: `False` / broker_order_forbidden: `True`
- authority: `missed_probe_ev_only_not_broker_execution`

## Scalp Entry ADM
- artifact: `/home/ubuntu/KORStockScan/data/report/scalp_entry_action_decision_matrix/scalp_entry_action_decision_matrix_2026-06-09.json`
- status: `warning` / authority: `entry_advisory_prompt_context_only`
- total/joined/floor: `1238` / `230` / `20`
- prompt_applied_count: `870`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 1238}`
- forced_action_counts: `{'-': 1238}`
- missing_actions: `[]`
- zero_sample_actions: `['SKIP_STALE']`
- top_actions: `[{'action': 'BUY_NOW', 'sample_count': 21, 'joined_sample': 16, 'source_quality_adjusted_ev_pct': -0.0638}, {'action': 'WAIT_REQUOTE', 'sample_count': 7, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'BUY_DEFENSIVE', 'sample_count': 5, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'NO_BUY_AI', 'sample_count': 1021, 'joined_sample': 71, 'source_quality_adjusted_ev_pct': -0.074}, {'action': 'SKIP_SOURCE_QUALITY', 'sample_count': 25, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}]`

## Lifecycle Decision Matrix
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-06-09.json`
- status: `pass` / version: `lifecycle_decision_matrix_v1_2026-06-09`
- total/joined: `20862` / `19325`
- policy_pass/promote_ready: `5` / `1`
- lifecycle_flow buckets/complete/runtime/workorders: `159` / `137` / `0` / `20`
- holding/exit buckets: `35` / `62`
- holding/exit workorders: `10` / `10`
- lifecycle identity missing/join_rate: `0` / `1.0`
- lifecycle complete_flow_rate: `0.0072`
- incomplete_flow_reason_counts: `{'missing_submit': 18795, 'missing_holding': 18786, 'missing_exit': 18307, 'missing_entry': 18334, 'postclose_exit_without_entry': 500, 'candidate_id_only': 18459, 'sim_record_id_only': 246}`
- fixed_threshold_roles: `{'hard_safety': ['broker_submit_guard', 'stale_quote_submit_block', 'price_freshness_guard', 'hard_stop', 'protect_stop', 'emergency_stop', 'account_order_cooldown_qty_guard'], 'baseline_prior': ['BUY_SCORE_THRESHOLD', 'VPW_MIN_SCORE', 'strength_momentum_cutoff', 'entry_score_cutoff'], 'bounded_tunable': ['SCALP_ENTRY_LATENCY_MAX_WS_AGE_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_WS_JITTER_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_SPREAD_RATIO_FOR_CAUTION', 'score65_74_recovery_probe', 'soft_stop_whipsaw_confirmation', 'holding_flow_override', 'scale_in_price_guard'], 'legacy_archive': ['fallback_scout_main', 'fallback_single', 'latency_fallback_split_entry', 'legacy_latency_composite', 'closed_shadow_axes']}`
- policy_entries: `[{'stage': 'entry', 'sample': 1429, 'joined_sample': 201, 'stage_ev_composite_pct': 1.3021, 'confidence': 1.0, 'selected_action': 'BUY_DEFENSIVE', 'source_quality_gate': 'pass', 'promote_ready': True}, {'stage': 'submit', 'sample': 302, 'joined_sample': 281, 'stage_ev_composite_pct': -0.4741, 'confidence': 1.0, 'selected_action': 'NO_CHANGE', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'holding', 'sample': 297, 'joined_sample': 281, 'stage_ev_composite_pct': -0.8262, 'confidence': 1.0, 'selected_action': 'EXIT', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'scale_in', 'sample': 18054, 'joined_sample': 18053, 'stage_ev_composite_pct': -0.3088, 'confidence': 1.0, 'selected_action': 'NO_CHANGE', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'exit', 'sample': 780, 'joined_sample': 509, 'stage_ev_composite_pct': -0.9208, 'confidence': 1.0, 'selected_action': 'EXIT', 'source_quality_gate': 'pass', 'promote_ready': False}]`

## Lifecycle Bucket Discovery
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-06-09.json`
- status: `pass` / human_intervention_required: `False`
- candidates/surfaced: `500` / `208`
- sim_auto/live_auto/new_bucket: `48` / `0` / `0`
- role/window: `new_pattern_detection` / `same_day_source_bundle_plus_rolling_threshold_cycle_consumer`
- parent_count/granularity/conflict: `51` / `target_pass` / `8`
- state_counts: `{'source_only_keep_collecting': 433, 'lifecycle_flow_sim_probe_candidate': 18, 'sim_auto_approved': 48, 'entry_only_sim_auto_approved': 1}`
- top_surfaced: `[{'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 2, 'source_quality_adjusted_ev_pct': 2.6813}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': 1.4271}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': 1.94}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_scalp_entry_action_decision_snapshot_stale', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': 1.4887}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': 1.9121}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 12575, 'source_quality_adjusted_ev_pct': -0.6946}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_pyramid_', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 5251, 'source_quality_adjusted_ev_pct': 0.6423}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 202, 'source_quality_adjusted_ev_pct': -1.0963}]`

## Lifecycle Bucket Windows
- promotion_window: `mtd`
- confirmation_windows: `['rolling5d', 'rolling10d']`
- windows: `{'rolling5d': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-06-09_rolling5d.json', 'window_role': 'rolling_confirmation', 'window_policy': 'rolling5d', 'status': 'pass', 'parent_bucket_count': 30, 'selected_parent_level': 'L1_broad', 'parent_granularity_status': 'target_pass', 'absorbed_child_count': 281, 'absorbed_sample_count': 54728, 'child_conflict_warning_count': 10, 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'parsed'}, 'rolling10d': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-06-09_rolling10d.json', 'window_role': 'rolling_confirmation', 'window_policy': 'rolling10d', 'status': 'pass', 'parent_bucket_count': 38, 'selected_parent_level': 'L1_broad', 'parent_granularity_status': 'target_pass', 'absorbed_child_count': 326, 'absorbed_sample_count': 57031, 'child_conflict_warning_count': 13, 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'parsed'}, 'mtd': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-06-09_mtd.json', 'window_role': 'promotion_confirmation', 'window_policy': 'mtd', 'status': 'pass', 'parent_bucket_count': 38, 'selected_parent_level': 'L1_broad', 'parent_granularity_status': 'target_pass', 'absorbed_child_count': 326, 'absorbed_sample_count': 57031, 'child_conflict_warning_count': 13, 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'partial'}}`

## Lifecycle AI Context
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_ai_context/lifecycle_ai_context_2026-06-09.json`
- context_version: `lifecycle_ai_context_v1_2026-06-09` / authority: `ai_advisory_prompt_context_only`
- prompt_stage_count: `3` / runtime_effect: `False`
- stage_contexts: `[{'stage': 'entry', 'prompt_injection_allowed': True, 'policy_key': 'entry:weighted_adm_v1', 'alignment_hint': 'BUY_DEFENSIVE', 'context_contribution_score': -0.3075, 'attribution_quality_status': 'observational_only_pending_outcome'}, {'stage': 'submit', 'prompt_injection_allowed': False, 'policy_key': 'submit:weighted_adm_v1', 'alignment_hint': 'NO_CHANGE', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'holding', 'prompt_injection_allowed': True, 'policy_key': 'holding:weighted_adm_v1', 'alignment_hint': 'EXIT', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'scale_in', 'prompt_injection_allowed': False, 'policy_key': 'scale_in:weighted_adm_v1', 'alignment_hint': 'NO_CHANGE', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'exit', 'prompt_injection_allowed': True, 'policy_key': 'exit:weighted_adm_v1', 'alignment_hint': 'EXIT', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}]`

## Lifecycle AI Context Attribution
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_ai_context_attribution/lifecycle_ai_context_attribution_2026-06-09.json`
- eligible/applied/skipped: `3869` / `3869` / `0`
- replay_budget: `30`
- implementation_status: `implemented`
- stage_attribution: `{'entry': {'context_contribution_score': -0.3075, 'bounded_auxiliary_weight': -0.0461, 'attribution_quality_status': 'observational_only_pending_outcome', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': 0.0607, 'no_context_replay_observed': 0}, 'submit': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'holding': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'scale_in': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'exit': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}}`

## Institutional Flow Context
- artifact: `/home/ubuntu/KORStockScan/data/report/institutional_flow_context/institutional_flow_context_2026-06-09.json`
- status: `pass` / authority: `source_only_lifecycle_feature`
- rows ok/partial/missing/token_error: `120` / `0` / `0` / `0`
- join_rate_pct: `100.0`
- source_mix: `{'ka10059+ka10061': 120}`
- top_net_buy: `[{'stock_code': '093370', 'smart_money_net': 2164898, 'foreign_net_roll5': 1491615, 'inst_net_roll5': 1068840, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '403870', 'smart_money_net': 1991687, 'foreign_net_roll5': 2187693, 'inst_net_roll5': 630589, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '323410', 'smart_money_net': 1188789, 'foreign_net_roll5': 1422575, 'inst_net_roll5': 766851, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '089030', 'smart_money_net': 994605, 'foreign_net_roll5': 877610, 'inst_net_roll5': 549162, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '001740', 'smart_money_net': 587010, 'foreign_net_roll5': 3239527, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}, {'stock_code': '085620', 'smart_money_net': 586048, 'foreign_net_roll5': 0, 'inst_net_roll5': 1029611, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '000270', 'smart_money_net': 540380, 'foreign_net_roll5': 749555, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}, {'stock_code': '043260', 'smart_money_net': 463182, 'foreign_net_roll5': 986058, 'inst_net_roll5': 631623, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '125020', 'smart_money_net': 376441, 'foreign_net_roll5': 226150, 'inst_net_roll5': 192483, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '388790', 'smart_money_net': 374873, 'foreign_net_roll5': 0, 'inst_net_roll5': 241890, 'regime': 'INSTITUTION_ACCUMULATION'}]`

## Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-06-09.json`
- fresh: gemini=`False` claude=`True`
- consensus/orders/family_candidates: `0` / `7` / `0`

## Swing Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_2026-06-09.json`
- deepseek_lab_available: `True`
- findings/orders: `6` / `5`
- data_quality_warnings: `1`
- top_level_data_quality_warnings: `0`
- resolved_data_quality_warnings: `1`
- ofi_qi_stale_missing_unique_records: `4`
- ofi_qi_stale_missing_reasons: `{'micro_missing': 11973, 'micro_stale': 0, 'observer_unhealthy': 0, 'micro_not_ready': 11983, 'state_insufficient': 11983}`
- ofi_qi_stale_missing_reason_combinations: `{'micro_not_ready+state_insufficient': 10, 'micro_missing+micro_not_ready+state_insufficient': 11973}`
- ofi_qi_stale_missing_reason_combination_unique_records: `{'micro_missing+micro_not_ready+state_insufficient': 4}`
- ofi_qi_observer_unhealthy_overlap: `{'observer_unhealthy_total': 0, 'observer_unhealthy_with_other_reason': 0, 'observer_unhealthy_only': 0}`
- source_quality_blocked_families: `[{'family': 'swing_entry_ofi_qi_execution_quality', 'stage': 'entry', 'metric_role': 'source_quality_gate', 'decision_authority': 'swing_pattern_lab_analysis_workorder_source_only', 'window_policy': 'same_day_pattern_lab_source_quality', 'sample_floor': 1, 'primary_decision_metric': 'source_quality_gate', 'source_quality_gate': 'swing_orderbook_micro_context_ready_or_blocker_provenance_recorded', 'source_contract_version': 'swing_micro_context_source_quality_v1', 'source_contract_status': 'implemented', 'source_quality_blockers': ['entry_ofi_qi_invalid_micro_context'], 'invalid_micro_context_unique_record_count': 4, 'invalid_reason_combination_unique_record_counts': {'micro_missing+micro_not_ready+state_insufficient': 4}, 'reason_counts': {'micro_missing': 11973, 'micro_stale': 0, 'observer_unhealthy': 0, 'micro_not_ready': 11983, 'state_insufficient': 11983}, 'reason_combination_counts': {'micro_not_ready+state_insufficient': 10, 'micro_missing+micro_not_ready+state_insufficient': 11973}, 'observer_unhealthy_overlap': {'observer_unhealthy_total': 0, 'observer_unhealthy_with_other_reason': 0, 'observer_unhealthy_only': 0}, 'automation_input': True, 'runtime_effect': False, 'allowed_runtime_apply': False, 'forbidden_uses': ['swing_real_order_enable', 'one_share_real_canary', 'scale_in_real_canary', 'runtime_threshold_mutation', 'provider_route_change', 'bot_restart', 'recommendation_history_replace'], 'provenance_gap_count': 0, 'readiness_counts': {'micro_ready_count': 0, 'micro_insufficient_samples_count': 11983, 'micro_not_ready_count': 11983, 'state_insufficient_count': 11983}, 'spread_quality': {'wide_spread_threshold_ticks': 10, 'wide_spread_count': 0, 'wide_spread_rate': 0.0, 'max_spread_ticks': None, 'hard_block': False, 'decision_use': 'source_quality_adjusted_ev_penalty_or_filter_candidate'}, 'source_quality_reason_stage_split': {'micro_missing': 11973, 'micro_not_ready': 11983, 'state_insufficient': 11983, 'observer_unhealthy': 0, 'provenance_gap': 0}}, {'family': 'swing_scale_in_ofi_qi_confirmation', 'stage': 'scale_in', 'metric_role': 'source_quality_gate', 'decision_authority': 'swing_pattern_lab_analysis_workorder_source_only', 'window_policy': 'same_day_pattern_lab_source_quality', 'sample_floor': 1, 'primary_decision_metric': 'source_quality_gate', 'source_quality_gate': 'swing_orderbook_micro_context_ready_or_blocker_provenance_recorded', 'source_contract_version': 'swing_micro_context_source_quality_v1', 'source_contract_status': 'implemented', 'source_quality_blockers': ['scale_in_ofi_qi_invalid_micro_context'], 'invalid_micro_context_unique_record_count': 1, 'invalid_reason_combination_unique_record_counts': {'micro_missing+micro_not_ready+state_insufficient': 4}, 'reason_counts': {'micro_missing': 11973, 'micro_stale': 0, 'observer_unhealthy': 0, 'micro_not_ready': 11983, 'state_insufficient': 11983}, 'reason_combination_counts': {'micro_not_ready+state_insufficient': 10, 'micro_missing+micro_not_ready+state_insufficient': 11973}, 'observer_unhealthy_overlap': {'observer_unhealthy_total': 0, 'observer_unhealthy_with_other_reason': 0, 'observer_unhealthy_only': 0}, 'automation_input': True, 'runtime_effect': False, 'allowed_runtime_apply': False, 'forbidden_uses': ['swing_real_order_enable', 'one_share_real_canary', 'scale_in_real_canary', 'runtime_threshold_mutation', 'provider_route_change', 'bot_restart', 'recommendation_history_replace'], 'provenance_gap_count': 0, 'readiness_counts': {'micro_ready_count': 0, 'micro_insufficient_samples_count': 11983, 'micro_not_ready_count': 11983, 'state_insufficient_count': 11983}, 'spread_quality': {'wide_spread_threshold_ticks': 10, 'wide_spread_count': 0, 'wide_spread_rate': 0.0, 'max_spread_ticks': None, 'hard_block': False, 'decision_use': 'source_quality_adjusted_ev_penalty_or_filter_candidate'}, 'source_quality_reason_stage_split': {'micro_missing': 11973, 'micro_not_ready': 11983, 'state_insufficient': 11983, 'observer_unhealthy': 0, 'provenance_gap': 0}}]`
- carryover_warnings: `0`
- population_split_available: `True`

## Swing Strategy Discovery Sim
- artifact: `/home/ubuntu/KORStockScan/data/report/swing_strategy_discovery_ev/swing_strategy_discovery_ev_2026-06-09.json`
- authority: `swing_sim_exploration_only` / source_only: `True`
- candidate/arm/policy_exit_rows: `298` / `1903` / `1903`
- labeled/pending_future_quotes: `187` / `1601`
- implementation_status: `implemented`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- surviving/avoid_bucket_count: `1` / `20`
- runtime_effect: `False`

## Pipeline Event Verbosity
- artifact: `/home/ubuntu/KORStockScan/data/report/pipeline_event_verbosity/pipeline_event_verbosity_2026-06-09.json`
- state: `v2_shadow_pending_flush`
- recommended_workorder_state: `observe_pending_next_flush`
- high_volume_line_count: `43275`
- high_volume_byte_share_pct: `6.29`
- parity_ok: `False`
- suppress_eligibility: `False`

## Codebase Performance Workorder Source
- artifact: `/home/ubuntu/KORStockScan/data/report/codebase_performance_workorder/codebase_performance_workorder_2026-06-09.json`
- authority: `ops_performance_workorder_source`
- accepted/deferred/rejected: `7` / `3` / `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`

## Pattern Lab Audits
- currentness: status=`pass` fail=`0` orders=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-06-09.json`
- ai_review: status=`pass` orders=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_ai_review/pattern_lab_ai_review_2026-06-09.json`
- time_window_regime_counterfactual: status=`pass` artifact=`/home/ubuntu/KORStockScan/data/report/time_window_regime_counterfactual/time_window_regime_counterfactual_2026-06-09.json`
- producer_gap_discovery: status=`pass` orders=`0` artifact=`/home/ubuntu/KORStockScan/data/report/producer_gap_discovery/producer_gap_discovery_2026-06-09.json`
- stage_hook_workorder_discovery: status=`warning` orders=`2` artifact=`/home/ubuntu/KORStockScan/data/report/stage_hook_workorder_discovery/stage_hook_workorder_discovery_2026-06-09.json`
- propagation: status=`warning` fail=`0` warnings=`2` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_2026-06-09.json`

## Swing Runtime Approval
- request_report: `/home/ubuntu/KORStockScan/data/report/swing_runtime_approval/swing_runtime_approval_2026-06-08.json`
- approval_artifact: `-`
- requested/approved/live_dry_run: `0` / `0` / `0`
- dry_run_forced: `False`
- legacy_phase0_real_canary_ignored: `False`
- blocked: `[]`

## Code Improvement Workorder
- artifact: `/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-06-09.json`
- markdown: `/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-06-09.md`
- selected_order_count: `115`
- decision_counts: `{'attach_existing_family': 137, 'design_family_candidate': 4, 'defer_evidence': 8, 'reject': 2}`

## Approval Requests
- `position_sizing_cap_release` sample=`65/30` reason=`window_policy primary=rolling_10d 기준 재평가: 1주 cap 해제 efficient trade-off 기준 충족(score=0.20/0.70): 자동 적용하지 않고 사용자 승인 요청 artifact로만 승격한다.` contract=`final_user_approval_required` live_ready=`False`

## Swing Approval Requests
- none

## Calibration Decisions
## Code Improvement Top Orders
- `order_entry_submit_drought_auto_resolution` decision=`attach_existing_family` subsystem=`runtime_instrumentation`
- `order_entry_broker_receipt_contract_gap_review` decision=`attach_existing_family` subsystem=`runtime_instrumentation`
- `order_entry_fill_quality_contract_gap_review` decision=`attach_existing_family` subsystem=`runtime_instrumentation`

- `soft_stop_whipsaw_confirmation`: `adjust_up` sample=`7708/10`
- `holding_flow_ofi_smoothing`: `hold` sample=`2606/20`
- `protect_trailing_smoothing`: `adjust_down` sample=`39/20`
- `trailing_continuation`: `freeze` sample=`404/20`
- `market_regime_continuous_thresholds`: `hold_sample` sample=`4/10`
- `pre_submit_price_guard`: `hold` sample=`0/1`
- `dynamic_entry_price_resolver`: `hold_sample` sample=`5140/20`
- `entry_price_execution_quality`: `hold` sample=`35/5`
- `score65_74_recovery_probe`: `adjust_up` sample=`279/20`
- `strength_momentum_soft_gate_p1`: `hold` sample=`43179/20`
- `overbought_pullback_guard_p1`: `hold` sample=`11097/20`
- `liquidity_pre_submit_guard_p1`: `hold` sample=`5196/20`
- `bad_entry_refined_canary`: `adjust_up` sample=`84336/10`
- `holding_exit_decision_matrix_advisory`: `hold_no_edge` sample=`11/1`
- `lifecycle_decision_matrix_runtime`: `adjust_up` sample=`20862/20`
- `scale_in_price_guard`: `hold` sample=`378/20`
- `position_sizing_cap_release`: `approval_required` sample=`65/30`
- `position_sizing_dynamic_formula`: `hold_sample` sample=`65/30`

## Warnings
- `scalp_entry_adm:unknown_bucket_source_quality_gap`
- `lifecycle_bucket_discovery:source_contract_drift_warning`
- `lifecycle_bucket_discovery:source_contract_drift_warning`
- `swing_strategy_discovery:pending_future_quotes`
- `swing_strategy_discovery:clean_tuning_baseline_swing_discovery_lookback_filtered`
- `swing_lifecycle_decision_matrix:pending_future_quotes`
- `swing_lifecycle_decision_matrix:clean_tuning_baseline_swing_discovery_lookback_filtered`
- `pattern_lab_propagation_audit_warning`
