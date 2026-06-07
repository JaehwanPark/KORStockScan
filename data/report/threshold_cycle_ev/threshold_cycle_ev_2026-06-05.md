# Threshold Cycle Daily EV Report - 2026-06-05

## Runtime Apply
- status: `auto_bounded_live_ready`
- runtime_change: `True`
- selected_families: `soft_stop_whipsaw_confirmation`

## Daily EV
- completed: `1` / open: `0`
- win/loss: `0` / `1` (`0.0`%)
- avg_profit_rate: `-2.52`%
- realized_pnl_krw: `-3184`
- full_fill_completed_avg_profit_rate: `-2.52`%

## Entry Funnel
- budget_pass_to_submitted: `1` / `25126` (`0.0`%)
- latency pass/block: `330` / `24790`
- latency submit routing: `latency_classifier_runtime_semantics_gap`
- latency recommended action: `reject` (`recovery_count=0 below floor=2479`)
- latency profile generation: `{'mode': 'grid_quantile_search', 'profile_count': 810, 'age_cap_ms': 1500, 'jitter_cap_ms': 1500, 'spread_cap_ratio': 0.012, 'counterfactual_sample_floor': 3, 'recovery_event_floor_ratio': 0.1}`
- safe/caution_normal/recovery: `0` / `0` / `0`
- recovery attempts/cf sample/cf ev: `0` / `0` / `None`%
- recovered/lost labels: `0` / `0`
- stale/broker override excluded: `0` / `0`
- full/partial fill: `1` / `0`

## Holding Exit
- holding_reviews: `2741`
- exit_signals: `163`
- holding_review_ms_p95: `2172.0`

## Scalp Simulator
- authority: `equal_weight` / fill_policy: `signal_inclusive_best_ask_v1`
- armed/filled/sold: `151` / `151` / `151`
- expired/unpriced/duplicate: `0` / `0` / `1701`
- entry_ai_price applied/skip: `14` / `0`
- submit_revalidation warning/block: `137` / `0`
- scale_in filled/unfilled: `0` / `0`
- overnight decision/sell/hold/carry_restored: `14` / `14` / `0` / `0`
- completed_profit_summary: `{'sample': 151, 'win_count': 33, 'loss_count': 118, 'avg_profit_rate': -1.2421, 'median_profit_rate': -1.86, 'downside_p10_profit_rate': -2.69, 'upside_p90_profit_rate': 1.36, 'win_rate': 0.2185, 'loss_rate': 0.7815, 'stddev_profit_rate': 1.742}`
- post_sell_join: joined=`147` / pending=`4`
- post_sell_mfe_mae_10m: mfe=`1.4101`% / mae=`-5.6477`% / close=`0.1895`%

## Missed Probe Counterfactual
- book: `scalp_score65_74_probe_counterfactual` / role: `missed_buy_probe_counterfactual`
- total/score65_74: `52` / `0`
- avg_expected_ev: `3.3263`% / score65_74_avg_expected_ev: `0.0`%
- actual_order_submitted: `False` / broker_order_forbidden: `True`
- authority: `missed_probe_ev_only_not_broker_execution`

## Scalp Entry ADM
- artifact: `/home/ubuntu/KORStockScan/data/report/scalp_entry_action_decision_matrix/scalp_entry_action_decision_matrix_2026-06-05.json`
- status: `warning` / authority: `entry_advisory_prompt_context_only`
- total/joined/floor: `471` / `105` / `20`
- prompt_applied_count: `271`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 471}`
- forced_action_counts: `{'-': 471}`
- missing_actions: `[]`
- zero_sample_actions: `['SKIP_STALE']`
- top_actions: `[{'action': 'BUY_NOW', 'sample_count': 2, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'WAIT_REQUOTE', 'sample_count': 6, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'BUY_DEFENSIVE', 'sample_count': 1, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'NO_BUY_AI', 'sample_count': 388, 'joined_sample': 39, 'source_quality_adjusted_ev_pct': -0.1199}, {'action': 'SKIP_SOURCE_QUALITY', 'sample_count': 1, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}]`

## Lifecycle Decision Matrix
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-06-05.json`
- status: `pass` / version: `lifecycle_decision_matrix_v1_2026-06-05`
- total/joined: `13164` / `12500`
- policy_pass/promote_ready: `5` / `1`
- lifecycle_flow buckets/complete/runtime/workorders: `85` / `56` / `0` / `20`
- holding/exit buckets: `32` / `48`
- holding/exit workorders: `10` / `10`
- lifecycle identity missing/join_rate: `0` / `1.0`
- lifecycle complete_flow_rate: `0.0046`
- incomplete_flow_reason_counts: `{'missing_entry': 11981, 'missing_holding': 12220, 'missing_exit': 11950, 'missing_submit': 12226, 'candidate_id_only': 12024, 'sim_record_id_only': 151, 'postclose_exit_without_entry': 288}`
- fixed_threshold_roles: `{'hard_safety': ['broker_submit_guard', 'stale_quote_submit_block', 'price_freshness_guard', 'hard_stop', 'protect_stop', 'emergency_stop', 'account_order_cooldown_qty_guard'], 'baseline_prior': ['BUY_SCORE_THRESHOLD', 'VPW_MIN_SCORE', 'strength_momentum_cutoff', 'entry_score_cutoff'], 'bounded_tunable': ['SCALP_ENTRY_LATENCY_MAX_WS_AGE_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_WS_JITTER_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_SPREAD_RATIO_FOR_CAUTION', 'score65_74_recovery_probe', 'soft_stop_whipsaw_confirmation', 'holding_flow_override', 'scale_in_price_guard'], 'legacy_archive': ['fallback_scout_main', 'fallback_single', 'latency_fallback_split_entry', 'legacy_latency_composite', 'closed_shadow_axes']}`
- policy_entries: `[{'stage': 'entry', 'sample': 577, 'joined_sample': 91, 'stage_ev_composite_pct': 1.1838, 'confidence': 1.0, 'selected_action': 'BUY_DEFENSIVE', 'source_quality_gate': 'pass', 'promote_ready': True}, {'stage': 'submit', 'sample': 163, 'joined_sample': 151, 'stage_ev_composite_pct': -0.6645, 'confidence': 1.0, 'selected_action': 'NO_CHANGE', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'holding', 'sample': 165, 'joined_sample': 151, 'stage_ev_composite_pct': -1.0122, 'confidence': 1.0, 'selected_action': 'EXIT', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'scale_in', 'sample': 11822, 'joined_sample': 11821, 'stage_ev_composite_pct': -0.5105, 'confidence': 1.0, 'selected_action': 'NO_CHANGE', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'exit', 'sample': 437, 'joined_sample': 286, 'stage_ev_composite_pct': -0.9847, 'confidence': 1.0, 'selected_action': 'EXIT', 'source_quality_gate': 'pass', 'promote_ready': False}]`

## Lifecycle Bucket Discovery
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-06-05.json`
- status: `pass` / human_intervention_required: `False`
- candidates/surfaced: `500` / `255`
- sim_auto/live_auto/new_bucket: `165` / `0` / `0`
- role/window: `new_pattern_detection` / `same_day_source_bundle_plus_rolling_threshold_cycle_consumer`
- parent_count/granularity/conflict: `34` / `target_pass` / `4`
- state_counts: `{'source_only_keep_collecting': 323, 'lifecycle_flow_sim_probe_candidate': 7, 'sim_auto_approved': 165, 'entry_only_sim_auto_approved': 5}`
- top_surfaced: `[{'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 10142, 'source_quality_adjusted_ev_pct': -0.666}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_pyramid_', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 1542, 'source_quality_adjusted_ev_pct': 0.5452}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 119, 'source_quality_adjusted_ev_pct': -1.0654}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wait6579_ev_cohort_stale_fresh_or_unflagge', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 33, 'source_quality_adjusted_ev_pct': 2.1037}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait6579_ev_cohort_stale_fresh_or_unflagged_', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 10, 'source_quality_adjusted_ev_pct': 1.441}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wait6579_ev_cohort_stale_fresh_or_unflagge', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 9, 'source_quality_adjusted_ev_pct': 2.7732}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_combo_holding_flow_source_scalp_sim_ov', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 6, 'source_quality_adjusted_ev_pct': -1.03}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_combo_holding_flow_source_scalp_sim_ov', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 5, 'source_quality_adjusted_ev_pct': -0.752}]`

## Lifecycle Bucket Windows
- promotion_window: `mtd`
- confirmation_windows: `['rolling5d', 'rolling10d']`
- windows: `{'rolling5d': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-06-05_rolling5d.json', 'window_role': 'rolling_confirmation', 'window_policy': 'rolling5d', 'status': 'pass', 'parent_bucket_count': 48, 'selected_parent_level': 'L2_default', 'parent_granularity_status': 'target_pass', 'absorbed_child_count': 134, 'absorbed_sample_count': 14597, 'child_conflict_warning_count': 7, 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'parsed'}, 'rolling10d': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-06-05_rolling10d.json', 'window_role': 'rolling_confirmation', 'window_policy': 'rolling10d', 'status': 'pass', 'parent_bucket_count': 48, 'selected_parent_level': 'L2_default', 'parent_granularity_status': 'target_pass', 'absorbed_child_count': 134, 'absorbed_sample_count': 14597, 'child_conflict_warning_count': 7, 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'parsed'}, 'mtd': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-06-05_mtd.json', 'window_role': 'promotion_confirmation', 'window_policy': 'mtd', 'status': 'pass', 'parent_bucket_count': 48, 'selected_parent_level': 'L2_default', 'parent_granularity_status': 'target_pass', 'absorbed_child_count': 134, 'absorbed_sample_count': 14597, 'child_conflict_warning_count': 7, 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'parsed'}}`

## Lifecycle AI Context
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_ai_context/lifecycle_ai_context_2026-06-05.json`
- context_version: `lifecycle_ai_context_v1_2026-06-05` / authority: `ai_advisory_prompt_context_only`
- prompt_stage_count: `3` / runtime_effect: `False`
- stage_contexts: `[{'stage': 'entry', 'prompt_injection_allowed': True, 'policy_key': 'entry:weighted_adm_v1', 'alignment_hint': 'BUY_DEFENSIVE', 'context_contribution_score': 0.3408, 'attribution_quality_status': 'observational_only_pending_outcome'}, {'stage': 'submit', 'prompt_injection_allowed': False, 'policy_key': 'submit:weighted_adm_v1', 'alignment_hint': 'NO_CHANGE', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'holding', 'prompt_injection_allowed': True, 'policy_key': 'holding:weighted_adm_v1', 'alignment_hint': 'EXIT', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'scale_in', 'prompt_injection_allowed': False, 'policy_key': 'scale_in:weighted_adm_v1', 'alignment_hint': 'NO_CHANGE', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'exit', 'prompt_injection_allowed': True, 'policy_key': 'exit:weighted_adm_v1', 'alignment_hint': 'EXIT', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}]`

## Lifecycle AI Context Attribution
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_ai_context_attribution/lifecycle_ai_context_attribution_2026-06-05.json`
- eligible/applied/skipped: `3179` / `3179` / `0`
- replay_budget: `30`
- implementation_status: `implemented`
- stage_attribution: `{'entry': {'context_contribution_score': 0.3408, 'bounded_auxiliary_weight': 0.0511, 'attribution_quality_status': 'observational_only_pending_outcome', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': 0.9868, 'no_context_replay_observed': 0}, 'submit': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'holding': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'scale_in': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'exit': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}}`

## Institutional Flow Context
- artifact: `/home/ubuntu/KORStockScan/data/report/institutional_flow_context/institutional_flow_context_2026-06-05.json`
- status: `pass` / authority: `source_only_lifecycle_feature`
- rows ok/partial/missing/token_error: `120` / `0` / `0` / `0`
- join_rate_pct: `100.0`
- source_mix: `{'ka10059+ka10061': 120}`
- top_net_buy: `[{'stock_code': '403870', 'smart_money_net': 872520, 'foreign_net_roll5': 921503, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}, {'stock_code': '240810', 'smart_money_net': 521576, 'foreign_net_roll5': 553678, 'inst_net_roll5': 168992, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '055550', 'smart_money_net': 460876, 'foreign_net_roll5': 880849, 'inst_net_roll5': 429648, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '092220', 'smart_money_net': 436410, 'foreign_net_roll5': 1331243, 'inst_net_roll5': 7397, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '033790', 'smart_money_net': 406757, 'foreign_net_roll5': 1450810, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}, {'stock_code': '319400', 'smart_money_net': 351563, 'foreign_net_roll5': 569781, 'inst_net_roll5': 40187, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '089030', 'smart_money_net': 335260, 'foreign_net_roll5': 284867, 'inst_net_roll5': 221590, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '034230', 'smart_money_net': 291436, 'foreign_net_roll5': 685774, 'inst_net_roll5': 281939, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '323410', 'smart_money_net': 258011, 'foreign_net_roll5': 1181961, 'inst_net_roll5': 143554, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '242040', 'smart_money_net': 253961, 'foreign_net_roll5': 352070, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}]`

## Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-06-05.json`
- fresh: gemini=`True` claude=`True`
- consensus/orders/family_candidates: `5` / `8` / `2`

## Swing Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_2026-06-05.json`
- deepseek_lab_available: `True`
- findings/orders: `5` / `3`
- data_quality_warnings: `0`
- top_level_data_quality_warnings: `0`
- resolved_data_quality_warnings: `0`
- ofi_qi_stale_missing_unique_records: `15`
- ofi_qi_stale_missing_reasons: `{'micro_missing': 2992, 'micro_stale': 0, 'observer_unhealthy': 6, 'micro_not_ready': 2999, 'state_insufficient': 2999}`
- ofi_qi_stale_missing_reason_combinations: `{'micro_not_ready+state_insufficient': 7, 'micro_missing+micro_not_ready+state_insufficient': 2986, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 6}`
- ofi_qi_stale_missing_reason_combination_unique_records: `{'micro_missing+micro_not_ready+state_insufficient': 14, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 3}`
- ofi_qi_observer_unhealthy_overlap: `{'observer_unhealthy_total': 6, 'observer_unhealthy_with_other_reason': 6, 'observer_unhealthy_only': 0}`
- source_quality_blocked_families: `[{'family': 'swing_entry_ofi_qi_execution_quality', 'stage': 'entry', 'metric_role': 'source_quality_gate', 'decision_authority': 'swing_pattern_lab_analysis_workorder_source_only', 'window_policy': 'same_day_pattern_lab_source_quality', 'sample_floor': 1, 'primary_decision_metric': 'source_quality_gate', 'source_quality_gate': 'swing_orderbook_micro_context_ready_or_blocker_provenance_recorded', 'source_contract_version': 'swing_micro_context_source_quality_v1', 'source_contract_status': 'implemented', 'source_quality_blockers': ['entry_ofi_qi_invalid_micro_context'], 'invalid_micro_context_unique_record_count': 15, 'invalid_reason_combination_unique_record_counts': {'micro_missing+micro_not_ready+state_insufficient': 14, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 3}, 'reason_counts': {'micro_missing': 2992, 'micro_stale': 0, 'observer_unhealthy': 6, 'micro_not_ready': 2999, 'state_insufficient': 2999}, 'reason_combination_counts': {'micro_not_ready+state_insufficient': 7, 'micro_missing+micro_not_ready+state_insufficient': 2986, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 6}, 'observer_unhealthy_overlap': {'observer_unhealthy_total': 6, 'observer_unhealthy_with_other_reason': 6, 'observer_unhealthy_only': 0}, 'automation_input': True, 'runtime_effect': False, 'allowed_runtime_apply': False, 'forbidden_uses': ['swing_real_order_enable', 'one_share_real_canary', 'scale_in_real_canary', 'runtime_threshold_mutation', 'provider_route_change', 'bot_restart', 'recommendation_history_replace']}]`
- carryover_warnings: `0`
- population_split_available: `True`

## Swing Strategy Discovery Sim
- artifact: `/home/ubuntu/KORStockScan/data/report/swing_strategy_discovery_ev/swing_strategy_discovery_ev_2026-06-05.json`
- authority: `swing_sim_exploration_only` / source_only: `True`
- candidate/arm/policy_exit_rows: `143` / `982` / `982`
- labeled/pending_future_quotes: `0` / `982`
- implementation_status: `implemented`
- top_surviving_arm: `-`
- surviving/avoid_bucket_count: `0` / `0`
- runtime_effect: `False`

## Pipeline Event Verbosity
- artifact: `/home/ubuntu/KORStockScan/data/report/pipeline_event_verbosity/pipeline_event_verbosity_2026-06-05.json`
- state: `v2_shadow_pending_flush`
- recommended_workorder_state: `observe_pending_next_flush`
- high_volume_line_count: `61370`
- high_volume_byte_share_pct: `6.27`
- parity_ok: `False`
- suppress_eligibility: `False`

## Codebase Performance Workorder Source
- artifact: `/home/ubuntu/KORStockScan/data/report/codebase_performance_workorder/codebase_performance_workorder_2026-06-05.json`
- authority: `ops_performance_workorder_source`
- accepted/deferred/rejected: `7` / `3` / `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`

## Pattern Lab Audits
- currentness: status=`pass` fail=`0` orders=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-06-05.json`
- ai_review: status=`pass` orders=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_ai_review/pattern_lab_ai_review_2026-06-05.json`
- time_window_regime_counterfactual: status=`pass` artifact=`/home/ubuntu/KORStockScan/data/report/time_window_regime_counterfactual/time_window_regime_counterfactual_2026-06-05.json`
- producer_gap_discovery: status=`pass` orders=`0` artifact=`/home/ubuntu/KORStockScan/data/report/producer_gap_discovery/producer_gap_discovery_2026-06-05.json`
- stage_hook_workorder_discovery: status=`pass` orders=`0` artifact=`/home/ubuntu/KORStockScan/data/report/stage_hook_workorder_discovery/stage_hook_workorder_discovery_2026-06-05.json`
- propagation: status=`pass` fail=`0` warnings=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_2026-06-05.json`

## Swing Runtime Approval
- request_report: `/home/ubuntu/KORStockScan/data/report/swing_runtime_approval/swing_runtime_approval_2026-06-04.json`
- approval_artifact: `-`
- requested/approved/live_dry_run: `0` / `0` / `0`
- dry_run_forced: `False`
- legacy_phase0_real_canary_ignored: `False`
- blocked: `[]`

## Code Improvement Workorder
- artifact: `/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-06-05.json`
- markdown: `/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-06-05.md`
- selected_order_count: `106`
- decision_counts: `{'attach_existing_family': 129, 'design_family_candidate': 4, 'defer_evidence': 5, 'reject': 2}`

## Approval Requests
- `position_sizing_cap_release` sample=`52/30` reason=`window_policy primary=rolling_10d 기준 재평가: 1주 cap 해제 efficient trade-off 기준 충족(score=0.17/0.70): 자동 적용하지 않고 사용자 승인 요청 artifact로만 승격한다.` contract=`final_user_approval_required` live_ready=`False`

## Swing Approval Requests
- none

## Calibration Decisions
## Code Improvement Top Orders
- `order_entry_submit_drought_auto_resolution` decision=`attach_existing_family` subsystem=`runtime_instrumentation`
- `order_ai_threshold_dominance` decision=`attach_existing_family` subsystem=`entry_funnel`
- `order_conversion_lane_submit_drought_submit_drought_broker_receipt` decision=`attach_existing_family` subsystem=`sim_to_real_conversion_lineage`

## Pattern Lab Top Findings
- `AI threshold dominance` route=`existing_family` family=`score65_74_recovery_probe`
- `AI threshold miss EV recovery` route=`existing_family` family=`score65_74_recovery_probe`
- `latency guard miss EV recovery` route=`instrumentation_order` family=`-`

- `soft_stop_whipsaw_confirmation`: `adjust_up` sample=`5894/10`
- `holding_flow_ofi_smoothing`: `hold` sample=`2816/20`
- `protect_trailing_smoothing`: `adjust_down` sample=`39/20`
- `trailing_continuation`: `freeze` sample=`233/20`
- `market_regime_continuous_thresholds`: `hold_sample` sample=`2/10`
- `pre_submit_price_guard`: `hold_sample` sample=`24790/20`
- `score65_74_recovery_probe`: `adjust_up` sample=`54/20`
- `strength_momentum_soft_gate_p1`: `hold` sample=`61496/20`
- `overbought_pullback_guard_p1`: `hold` sample=`27394/20`
- `liquidity_pre_submit_guard_p1`: `hold` sample=`4272/20`
- `bad_entry_refined_canary`: `adjust_up` sample=`48314/10`
- `holding_exit_decision_matrix_advisory`: `hold_no_edge` sample=`11/1`
- `lifecycle_decision_matrix_runtime`: `adjust_up` sample=`13164/20`
- `scale_in_price_guard`: `hold` sample=`136/20`
- `position_sizing_cap_release`: `approval_required` sample=`52/30`
- `position_sizing_dynamic_formula`: `hold_sample` sample=`52/30`

## Warnings
- `scalp_entry_adm:unknown_bucket_source_quality_gap`
- `swing_strategy_discovery:pending_future_quotes`
- `swing_strategy_discovery:sample_floor_not_met`
- `swing_strategy_discovery:clean_tuning_baseline_swing_discovery_lookback_filtered`
- `swing_lifecycle_decision_matrix:pending_future_quotes`
- `swing_lifecycle_decision_matrix:clean_tuning_baseline_swing_discovery_lookback_filtered`
