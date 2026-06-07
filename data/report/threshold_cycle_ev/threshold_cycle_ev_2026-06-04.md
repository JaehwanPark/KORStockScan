# Threshold Cycle Daily EV Report - 2026-06-04

## Runtime Apply
- status: `auto_bounded_live_ready`
- runtime_change: `True`
- selected_families: `bad_entry_refined_canary, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, lifecycle_decision_matrix_runtime`

## Daily EV
- completed: `8` / open: `0`
- win/loss: `2` / `6` (`25.0`%)
- avg_profit_rate: `-1.41`%
- realized_pnl_krw: `-13049`
- full_fill_completed_avg_profit_rate: `0.0`%

## Entry Funnel
- budget_pass_to_submitted: `1` / `4527` (`0.02`%)
- latency pass/block: `24` / `4501`
- latency submit routing: `latency_classifier_runtime_semantics_gap`
- latency recommended action: `reject` (`recovery_count=0 below floor=450`)
- latency profile generation: `{'mode': 'grid_quantile_search', 'profile_count': 900, 'age_cap_ms': 1500, 'jitter_cap_ms': 1500, 'spread_cap_ratio': 0.012, 'counterfactual_sample_floor': 3, 'recovery_event_floor_ratio': 0.1}`
- safe/caution_normal/recovery: `0` / `0` / `0`
- recovery attempts/cf sample/cf ev: `0` / `0` / `None`%
- recovered/lost labels: `0` / `0`
- stale/broker override excluded: `0` / `0`
- full/partial fill: `0` / `0`

## Holding Exit
- holding_reviews: `451`
- exit_signals: `17`
- holding_review_ms_p95: `2417.0`

## Scalp Simulator
- authority: `equal_weight` / fill_policy: `signal_inclusive_best_ask_v1`
- armed/filled/sold: `11` / `11` / `31`
- expired/unpriced/duplicate: `0` / `0` / `38`
- entry_ai_price applied/skip: `3` / `0`
- submit_revalidation warning/block: `8` / `0`
- scale_in filled/unfilled: `0` / `0`
- overnight decision/sell/hold/carry_restored: `18` / `18` / `0` / `0`
- completed_profit_summary: `{'sample': 31, 'win_count': 5, 'loss_count': 26, 'avg_profit_rate': -0.9874, 'median_profit_rate': -1.12, 'downside_p10_profit_rate': -1.87, 'upside_p90_profit_rate': 0.44, 'win_rate': 0.1613, 'loss_rate': 0.8387, 'stddev_profit_rate': 0.971}`
- post_sell_join: joined=`24` / pending=`7`
- post_sell_mfe_mae_10m: mfe=`1.4362`% / mae=`-6.4893`% / close=`0.3115`%

## Missed Probe Counterfactual
- book: `scalp_score65_74_probe_counterfactual` / role: `missed_buy_probe_counterfactual`
- total/score65_74: `2` / `0`
- avg_expected_ev: `-0.1878`% / score65_74_avg_expected_ev: `0.0`%
- actual_order_submitted: `False` / broker_order_forbidden: `True`
- authority: `missed_probe_ev_only_not_broker_execution`

## Scalp Entry ADM
- artifact: `/home/ubuntu/KORStockScan/data/report/scalp_entry_action_decision_matrix/scalp_entry_action_decision_matrix_2026-06-04.json`
- status: `warning` / authority: `entry_advisory_prompt_context_only`
- total/joined/floor: `136` / `13` / `20`
- prompt_applied_count: `0`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 136}`
- forced_action_counts: `{'-': 136}`
- missing_actions: `[]`
- zero_sample_actions: `['SKIP_STALE']`
- top_actions: `[{'action': 'BUY_NOW', 'sample_count': 5, 'joined_sample': 1, 'source_quality_adjusted_ev_pct': -0.42}, {'action': 'WAIT_REQUOTE', 'sample_count': 7, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'BUY_DEFENSIVE', 'sample_count': 1, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'NO_BUY_AI', 'sample_count': 113, 'joined_sample': 10, 'source_quality_adjusted_ev_pct': -0.12}, {'action': 'SKIP_SOURCE_QUALITY', 'sample_count': 2, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}]`

## Lifecycle Decision Matrix
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-06-04.json`
- status: `pass` / version: `lifecycle_decision_matrix_v1_2026-06-04`
- total/joined: `2558` / `2417`
- policy_pass/promote_ready: `4` / `0`
- lifecycle_flow buckets/complete/runtime/workorders: `62` / `4` / `0` / `20`
- holding/exit buckets: `23` / `51`
- holding/exit workorders: `7` / `10`
- lifecycle identity missing/join_rate: `0` / `1.0`
- lifecycle complete_flow_rate: `0.0017`
- incomplete_flow_reason_counts: `{'missing_entry': 2240, 'missing_holding': 2275, 'missing_exit': 2167, 'missing_submit': 2282, 'postclose_exit_without_entry': 97, 'candidate_id_only': 2147, 'sim_record_id_only': 31}`
- fixed_threshold_roles: `{'hard_safety': ['broker_submit_guard', 'stale_quote_submit_block', 'price_freshness_guard', 'hard_stop', 'protect_stop', 'emergency_stop', 'account_order_cooldown_qty_guard'], 'baseline_prior': ['BUY_SCORE_THRESHOLD', 'VPW_MIN_SCORE', 'strength_momentum_cutoff', 'entry_score_cutoff'], 'bounded_tunable': ['SCALP_ENTRY_LATENCY_MAX_WS_AGE_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_WS_JITTER_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_SPREAD_RATIO_FOR_CAUTION', 'score65_74_recovery_probe', 'soft_stop_whipsaw_confirmation', 'holding_flow_override', 'scale_in_price_guard'], 'legacy_archive': ['fallback_scout_main', 'fallback_single', 'latency_fallback_split_entry', 'legacy_latency_composite', 'closed_shadow_axes']}`
- policy_entries: `[{'stage': 'entry', 'sample': 102, 'joined_sample': 4, 'stage_ev_composite_pct': -1.404, 'confidence': 0.0157, 'selected_action': 'WAIT_REQUOTE', 'source_quality_gate': 'hold_sample', 'promote_ready': False}, {'stage': 'submit', 'sample': 25, 'joined_sample': 11, 'stage_ev_composite_pct': -0.6676, 'confidence': 0.484, 'selected_action': 'NO_CHANGE', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'holding', 'sample': 29, 'joined_sample': 11, 'stage_ev_composite_pct': -0.9616, 'confidence': 0.4172, 'selected_action': 'EXIT', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'scale_in', 'sample': 2154, 'joined_sample': 2154, 'stage_ev_composite_pct': -0.5457, 'confidence': 1.0, 'selected_action': 'NO_CHANGE', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'exit', 'sample': 248, 'joined_sample': 237, 'stage_ev_composite_pct': -0.948, 'confidence': 1.0, 'selected_action': 'EXIT', 'source_quality_gate': 'pass', 'promote_ready': False}]`

## Lifecycle Bucket Discovery
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-06-04.json`
- status: `pass` / human_intervention_required: `False`
- candidates/surfaced: `434` / `148`
- sim_auto/live_auto/new_bucket: `86` / `0` / `0`
- role/window: `new_pattern_detection` / `same_day_source_bundle_plus_rolling_threshold_cycle_consumer`
- parent_count/granularity/conflict: `43` / `target_pass` / `2`
- state_counts: `{'source_only_keep_collecting': 348, 'sim_auto_approved': 86}`
- top_surfaced: `[{'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 1871, 'source_quality_adjusted_ev_pct': -0.6765}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_pyramid_', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 261, 'source_quality_adjusted_ev_pct': 0.4071}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_none_exit_ex', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 12, 'source_quality_adjusted_ev_pct': -1.9011}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_none_exit_ex', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 10, 'source_quality_adjusted_ev_pct': -2.0274}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_none_exit_ex', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 9, 'source_quality_adjusted_ev_pct': -0.8524}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_none_exit_ex', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 9, 'source_quality_adjusted_ev_pct': -0.7924}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_none_exit_ex', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 7, 'source_quality_adjusted_ev_pct': -1.0192}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_unknown_liquid', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 5, 'source_quality_adjusted_ev_pct': -0.1805}]`

## Lifecycle Bucket Windows
- promotion_window: `mtd`
- confirmation_windows: `['rolling5d', 'rolling10d']`
- windows: `{'rolling5d': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-06-04_rolling5d.json', 'window_role': 'rolling_confirmation', 'window_policy': 'rolling5d', 'status': 'pass', 'parent_bucket_count': 43, 'selected_parent_level': 'L3_detailed', 'parent_granularity_status': 'target_pass', 'absorbed_child_count': 62, 'absorbed_sample_count': 2303, 'child_conflict_warning_count': 2, 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'parsed'}, 'rolling10d': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-06-04_rolling10d.json', 'window_role': 'rolling_confirmation', 'window_policy': 'rolling10d', 'status': 'pass', 'parent_bucket_count': 43, 'selected_parent_level': 'L3_detailed', 'parent_granularity_status': 'target_pass', 'absorbed_child_count': 62, 'absorbed_sample_count': 2303, 'child_conflict_warning_count': 2, 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'parsed'}, 'mtd': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-06-04_mtd.json', 'window_role': 'promotion_confirmation', 'window_policy': 'mtd', 'status': 'pass', 'parent_bucket_count': 43, 'selected_parent_level': 'L3_detailed', 'parent_granularity_status': 'target_pass', 'absorbed_child_count': 62, 'absorbed_sample_count': 2303, 'child_conflict_warning_count': 2, 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'parsed'}}`

## Lifecycle AI Context
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_ai_context/lifecycle_ai_context_2026-06-04.json`
- context_version: `lifecycle_ai_context_v1_2026-06-04` / authority: `ai_advisory_prompt_context_only`
- prompt_stage_count: `3` / runtime_effect: `False`
- stage_contexts: `[{'stage': 'entry', 'prompt_injection_allowed': True, 'policy_key': 'entry:weighted_adm_v1', 'alignment_hint': 'WAIT_REQUOTE', 'context_contribution_score': 0.0, 'attribution_quality_status': 'observational_only_pending_outcome'}, {'stage': 'submit', 'prompt_injection_allowed': False, 'policy_key': 'submit:weighted_adm_v1', 'alignment_hint': 'NO_CHANGE', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'holding', 'prompt_injection_allowed': True, 'policy_key': 'holding:weighted_adm_v1', 'alignment_hint': 'EXIT', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'scale_in', 'prompt_injection_allowed': False, 'policy_key': 'scale_in:weighted_adm_v1', 'alignment_hint': 'NO_CHANGE', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'exit', 'prompt_injection_allowed': True, 'policy_key': 'exit:weighted_adm_v1', 'alignment_hint': 'EXIT', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}]`

## Lifecycle AI Context Attribution
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_ai_context_attribution/lifecycle_ai_context_attribution_2026-06-04.json`
- eligible/applied/skipped: `213` / `213` / `0`
- replay_budget: `30`
- implementation_status: `implemented`
- stage_attribution: `{'entry': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'observational_only_pending_outcome', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'submit': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'holding': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'scale_in': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'exit': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}}`

## Institutional Flow Context
- artifact: `/home/ubuntu/KORStockScan/data/report/institutional_flow_context/institutional_flow_context_2026-06-04.json`
- status: `pass` / authority: `source_only_lifecycle_feature`
- rows ok/partial/missing/token_error: `73` / `0` / `0` / `0`
- join_rate_pct: `100.0`
- source_mix: `{'ka10059+ka10061': 73}`
- top_net_buy: `[{'stock_code': '034220', 'smart_money_net': 993775, 'foreign_net_roll5': 261734, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}, {'stock_code': '038500', 'smart_money_net': 954187, 'foreign_net_roll5': 1469232, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}, {'stock_code': '489790', 'smart_money_net': 719561, 'foreign_net_roll5': 820244, 'inst_net_roll5': 45577, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '089970', 'smart_money_net': 425949, 'foreign_net_roll5': 669071, 'inst_net_roll5': 86870, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '055550', 'smart_money_net': 409176, 'foreign_net_roll5': 568007, 'inst_net_roll5': 101545, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '105560', 'smart_money_net': 319533, 'foreign_net_roll5': 389688, 'inst_net_roll5': 41948, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '042700', 'smart_money_net': 281195, 'foreign_net_roll5': 0, 'inst_net_roll5': 0, 'regime': 'UNKNOWN'}, {'stock_code': '036930', 'smart_money_net': 265508, 'foreign_net_roll5': 0, 'inst_net_roll5': 0, 'regime': 'UNKNOWN'}, {'stock_code': '077360', 'smart_money_net': 230664, 'foreign_net_roll5': 1166288, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}, {'stock_code': '005290', 'smart_money_net': 208663, 'foreign_net_roll5': 96735, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}]`

## Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-06-04.json`
- fresh: gemini=`True` claude=`True`
- consensus/orders/family_candidates: `5` / `11` / `3`

## Swing Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_2026-06-04.json`
- deepseek_lab_available: `True`
- findings/orders: `5` / `3`
- data_quality_warnings: `0`
- top_level_data_quality_warnings: `0`
- resolved_data_quality_warnings: `0`
- ofi_qi_stale_missing_unique_records: `13`
- ofi_qi_stale_missing_reasons: `{'micro_missing': 293, 'micro_stale': 0, 'observer_unhealthy': 8, 'micro_not_ready': 294, 'state_insufficient': 294}`
- ofi_qi_stale_missing_reason_combinations: `{'micro_not_ready+state_insufficient': 1, 'micro_missing+micro_not_ready+state_insufficient': 285, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 8}`
- ofi_qi_stale_missing_reason_combination_unique_records: `{'micro_missing+micro_not_ready+state_insufficient': 13, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 2}`
- ofi_qi_observer_unhealthy_overlap: `{'observer_unhealthy_total': 8, 'observer_unhealthy_with_other_reason': 8, 'observer_unhealthy_only': 0}`
- source_quality_blocked_families: `[{'family': 'swing_entry_ofi_qi_execution_quality', 'stage': 'entry', 'metric_role': 'source_quality_gate', 'decision_authority': 'swing_pattern_lab_analysis_workorder_source_only', 'window_policy': 'same_day_pattern_lab_source_quality', 'sample_floor': 1, 'primary_decision_metric': 'source_quality_gate', 'source_quality_gate': 'swing_orderbook_micro_context_ready_or_blocker_provenance_recorded', 'source_contract_version': 'swing_micro_context_source_quality_v1', 'source_contract_status': 'implemented', 'source_quality_blockers': ['entry_ofi_qi_invalid_micro_context'], 'invalid_micro_context_unique_record_count': 13, 'invalid_reason_combination_unique_record_counts': {'micro_missing+micro_not_ready+state_insufficient': 13, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 2}, 'reason_counts': {'micro_missing': 293, 'micro_stale': 0, 'observer_unhealthy': 8, 'micro_not_ready': 294, 'state_insufficient': 294}, 'reason_combination_counts': {'micro_not_ready+state_insufficient': 1, 'micro_missing+micro_not_ready+state_insufficient': 285, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 8}, 'observer_unhealthy_overlap': {'observer_unhealthy_total': 8, 'observer_unhealthy_with_other_reason': 8, 'observer_unhealthy_only': 0}, 'automation_input': True, 'runtime_effect': False, 'allowed_runtime_apply': False, 'forbidden_uses': ['swing_real_order_enable', 'one_share_real_canary', 'scale_in_real_canary', 'runtime_threshold_mutation', 'provider_route_change', 'bot_restart', 'recommendation_history_replace']}]`
- carryover_warnings: `0`
- population_split_available: `True`

## Swing Strategy Discovery Sim
- artifact: `/home/ubuntu/KORStockScan/data/report/swing_strategy_discovery_ev/swing_strategy_discovery_ev_2026-06-04.json`
- authority: `swing_sim_exploration_only` / source_only: `True`
- candidate/arm/policy_exit_rows: `50` / `400` / `400`
- labeled/pending_future_quotes: `0` / `400`
- implementation_status: `implemented`
- top_surviving_arm: `-`
- surviving/avoid_bucket_count: `0` / `0`
- runtime_effect: `False`

## Pipeline Event Verbosity
- artifact: `/home/ubuntu/KORStockScan/data/report/pipeline_event_verbosity/pipeline_event_verbosity_2026-06-04.json`
- state: `v2_shadow_pending_flush`
- recommended_workorder_state: `observe_pending_next_flush`
- high_volume_line_count: `8763`
- high_volume_byte_share_pct: `5.49`
- parity_ok: `False`
- suppress_eligibility: `False`

## Codebase Performance Workorder Source
- artifact: `/home/ubuntu/KORStockScan/data/report/codebase_performance_workorder/codebase_performance_workorder_2026-06-04.json`
- authority: `ops_performance_workorder_source`
- accepted/deferred/rejected: `7` / `3` / `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`

## Pattern Lab Audits
- currentness: status=`pass` fail=`0` orders=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-06-04.json`
- ai_review: status=`warning` orders=`6` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_ai_review/pattern_lab_ai_review_2026-06-04.json`
- time_window_regime_counterfactual: status=`pass` artifact=`/home/ubuntu/KORStockScan/data/report/time_window_regime_counterfactual/time_window_regime_counterfactual_2026-06-04.json`
- producer_gap_discovery: status=`pass` orders=`0` artifact=`/home/ubuntu/KORStockScan/data/report/producer_gap_discovery/producer_gap_discovery_2026-06-04.json`
- stage_hook_workorder_discovery: status=`pass` orders=`0` artifact=`/home/ubuntu/KORStockScan/data/report/stage_hook_workorder_discovery/stage_hook_workorder_discovery_2026-06-04.json`
- propagation: status=`pass` fail=`0` warnings=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_2026-06-04.json`

## Swing Runtime Approval
- request_report: `/home/ubuntu/KORStockScan/data/report/swing_runtime_approval/swing_runtime_approval_2026-06-02.json`
- approval_artifact: `-`
- requested/approved/live_dry_run: `0` / `0` / `0`
- dry_run_forced: `False`
- legacy_phase0_real_canary_ignored: `False`
- blocked: `[]`

## Code Improvement Workorder
- artifact: `/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-06-04.json`
- markdown: `/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-06-04.md`
- selected_order_count: `100`
- decision_counts: `{'implement_now': 20, 'attach_existing_family': 102, 'design_family_candidate': 5, 'defer_evidence': 10, 'reject': 3}`

## Approval Requests
- `position_sizing_cap_release` sample=`58/30` reason=`window_policy primary=rolling_10d 기준 재평가: 1주 cap 해제 efficient trade-off 기준 충족(score=0.19/0.70): 자동 적용하지 않고 사용자 승인 요청 artifact로만 승격한다.` contract=`final_user_approval_required` live_ready=`False`

## Swing Approval Requests
- none

## Calibration Decisions
## Code Improvement Top Orders
- `order_conversion_lane_key_lineage_ldm_hypothesis_00d0b765311ad7aa` decision=`implement_now` subsystem=`sim_to_real_conversion_lineage`
- `order_conversion_lane_key_lineage_ldm_hypothesis_0f038214d5ac5a30` decision=`implement_now` subsystem=`sim_to_real_conversion_lineage`
- `order_conversion_lane_key_lineage_ldm_hypothesis_4782cc3ea9609ffc` decision=`implement_now` subsystem=`sim_to_real_conversion_lineage`

## Pattern Lab Top Findings
- `AI threshold miss EV recovery` route=`existing_family` family=`score65_74_recovery_probe`
- `No acute observability alert` route=`auto_family_candidate` family=`-`
- `latency guard miss EV recovery` route=`instrumentation_order` family=`-`

- `soft_stop_whipsaw_confirmation`: `adjust_up` sample=`4474/10`
- `holding_flow_ofi_smoothing`: `hold` sample=`338/20`
- `protect_trailing_smoothing`: `adjust_down` sample=`39/20`
- `trailing_continuation`: `freeze` sample=`200/20`
- `market_regime_continuous_thresholds`: `hold_sample` sample=`1/10`
- `pre_submit_price_guard`: `hold_sample` sample=`4418/20`
- `score65_74_recovery_probe`: `hold_sample` sample=`2/20`
- `strength_momentum_soft_gate_p1`: `hold` sample=`46370/20`
- `overbought_pullback_guard_p1`: `hold` sample=`24200/20`
- `liquidity_pre_submit_guard_p1`: `hold` sample=`2766/20`
- `bad_entry_refined_canary`: `adjust_up` sample=`38177/10`
- `holding_exit_decision_matrix_advisory`: `hold_no_edge` sample=`11/1`
- `lifecycle_decision_matrix_runtime`: `adjust_up` sample=`2558/20`
- `scale_in_price_guard`: `hold` sample=`108/20`
- `position_sizing_cap_release`: `approval_required` sample=`58/30`
- `position_sizing_dynamic_formula`: `hold_sample` sample=`58/30`

## Warnings
- `scalp_entry_adm:joined_sample_below_sample_floor`
- `scalp_entry_adm:unknown_bucket_source_quality_gap`
- `scalp_entry_adm:prompt_context_not_loaded`
- `swing_strategy_discovery:pending_future_quotes`
- `swing_strategy_discovery:sample_floor_not_met`
- `swing_strategy_discovery:clean_tuning_baseline_swing_discovery_lookback_filtered`
- `swing_lifecycle_decision_matrix:pending_future_quotes`
- `swing_lifecycle_decision_matrix:clean_tuning_baseline_swing_discovery_lookback_filtered`
- `pattern_lab_ai_review_warning`
- `pattern_lab_ai_review_ai_review_followup_required`
