# Threshold Cycle Daily EV Report - 2026-05-27

## Runtime Apply
- status: `auto_bounded_live_ready`
- runtime_change: `True`
- selected_families: `soft_stop_whipsaw_confirmation, score65_74_recovery_probe, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, lifecycle_decision_matrix_runtime, entry_wait6579_score66_69_recovery_gate_v1`

## Daily EV
- completed: `5` / open: `1`
- win/loss: `2` / `3` (`40.0`%)
- avg_profit_rate: `-0.34`%
- realized_pnl_krw: `408`
- full_fill_completed_avg_profit_rate: `-0.342`%

## Entry Funnel
- budget_pass_to_submitted: `13` / `37059` (`0.04`%)
- latency pass/block: `231` / `36812`
- latency submit routing: `latency_classifier_runtime_semantics_gap`
- latency recommended action: `reject` (`recovery_count=0 below floor=3680`)
- latency profile generation: `{'mode': 'grid_quantile_search', 'profile_count': 810, 'age_cap_ms': 1500, 'jitter_cap_ms': 1500, 'spread_cap_ratio': 0.012, 'counterfactual_sample_floor': 3, 'recovery_event_floor_ratio': 0.1}`
- safe/caution_normal/recovery: `0` / `0` / `0`
- recovery attempts/cf sample/cf ev: `0` / `0` / `None`%
- recovered/lost labels: `0` / `0`
- stale/broker override excluded: `0` / `0`
- full/partial fill: `39` / `36`

## Holding Exit
- holding_reviews: `4252`
- exit_signals: `253`
- holding_review_ms_p95: `1721.0`

## Scalp Simulator
- authority: `equal_weight` / fill_policy: `signal_inclusive_best_ask_v1`
- armed/filled/sold: `389` / `389` / `167`
- expired/unpriced/duplicate: `0` / `0` / `2444`
- entry_ai_price applied/skip: `65` / `2`
- submit_revalidation warning/block: `345` / `0`
- scale_in filled/unfilled: `0` / `0`
- overnight decision/sell/hold/carry_restored: `1` / `1` / `0` / `0`
- completed_profit_summary: `{'sample': 167, 'win_count': 41, 'loss_count': 126, 'avg_profit_rate': -1.3751, 'median_profit_rate': -2.09, 'downside_p10_profit_rate': -2.78, 'upside_p90_profit_rate': 1.25, 'win_rate': 0.2455, 'loss_rate': 0.7545, 'stddev_profit_rate': 1.8164}`
- post_sell_join: joined=`166` / pending=`1`
- post_sell_mfe_mae_10m: mfe=`1.421`% / mae=`-5.3703`% / close=`-0.3224`%

## Missed Probe Counterfactual
- book: `scalp_score65_74_probe_counterfactual` / role: `missed_buy_probe_counterfactual`
- total/score65_74: `130` / `0`
- avg_expected_ev: `3.6585`% / score65_74_avg_expected_ev: `0.0`%
- actual_order_submitted: `False` / broker_order_forbidden: `True`
- authority: `missed_probe_ev_only_not_broker_execution`

## Scalp Entry ADM
- artifact: `/home/ubuntu/KORStockScan/data/report/scalp_entry_action_decision_matrix/scalp_entry_action_decision_matrix_2026-05-27.json`
- status: `pass` / authority: `entry_advisory_prompt_context_only`
- total/joined/floor: `804` / `154` / `20`
- prompt_applied_count: `361`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 804}`
- forced_action_counts: `{'-': 804}`
- missing_actions: `[]`
- zero_sample_actions: `['SKIP_STALE']`
- top_actions: `[{'action': 'BUY_NOW', 'sample_count': 20, 'joined_sample': 5, 'source_quality_adjusted_ev_pct': -0.578}, {'action': 'WAIT_REQUOTE', 'sample_count': 18, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'BUY_DEFENSIVE', 'sample_count': 5, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'NO_BUY_AI', 'sample_count': 448, 'joined_sample': 13, 'source_quality_adjusted_ev_pct': -0.0279}, {'action': 'SKIP_SOURCE_QUALITY', 'sample_count': 3, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}]`

## Lifecycle Decision Matrix
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-05-27.json`
- status: `pass` / version: `lifecycle_decision_matrix_v1_2026-05-27`
- total/joined: `41172` / `39464`
- policy_pass/promote_ready: `5` / `1`
- fixed_threshold_roles: `{'hard_safety': ['broker_submit_guard', 'stale_quote_submit_block', 'price_freshness_guard', 'hard_stop', 'protect_stop', 'emergency_stop', 'account_order_cooldown_qty_guard'], 'baseline_prior': ['BUY_SCORE_THRESHOLD', 'VPW_MIN_SCORE', 'strength_momentum_cutoff', 'entry_score_cutoff'], 'bounded_tunable': ['SCALP_ENTRY_LATENCY_MAX_WS_AGE_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_WS_JITTER_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_SPREAD_RATIO_FOR_CAUTION', 'score65_74_recovery_probe', 'soft_stop_whipsaw_confirmation', 'holding_flow_override', 'scale_in_price_guard'], 'legacy_archive': ['fallback_scout_main', 'fallback_single', 'latency_fallback_split_entry', 'legacy_latency_composite', 'closed_shadow_axes']}`
- policy_entries: `[{'stage': 'entry', 'sample': 985, 'joined_sample': 148, 'stage_ev_composite_pct': 1.8842, 'confidence': 1.0, 'selected_action': 'BUY_DEFENSIVE', 'source_quality_gate': 'pass', 'promote_ready': True}, {'stage': 'submit', 'sample': 424, 'joined_sample': 183, 'stage_ev_composite_pct': -0.8487, 'confidence': 1.0, 'selected_action': 'NO_CHANGE', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'holding', 'sample': 390, 'joined_sample': 183, 'stage_ev_composite_pct': -1.1027, 'confidence': 1.0, 'selected_action': 'EXIT', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'scale_in', 'sample': 38083, 'joined_sample': 38041, 'stage_ev_composite_pct': -0.4229, 'confidence': 1.0, 'selected_action': 'NO_CHANGE', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'exit', 'sample': 1290, 'joined_sample': 909, 'stage_ev_composite_pct': -0.7019, 'confidence': 1.0, 'selected_action': 'EXIT', 'source_quality_gate': 'pass', 'promote_ready': False}]`

## Lifecycle Bucket Discovery
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-05-27.json`
- status: `pass` / human_intervention_required: `False`
- candidates/surfaced: `379` / `186`
- sim_auto/live_auto/new_bucket: `185` / `1` / `0`
- state_counts: `{'live_auto_apply_ready': 1, 'sim_auto_approved': 185, 'source_only_keep_collecting': 193}`
- top_surfaced: `[{'bucket_id': 'entry:combo_entry_spot:score_score_66_69_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_unknown', 'stage': 'entry', 'classification_state': 'live_auto_apply_ready', 'live_auto_apply_family': 'entry_wait6579_score66_69_recovery_gate_v1', 'recommended_action': 'relax_or_recover', 'joined_sample': 49, 'source_quality_adjusted_ev_pct': 1.5253}, {'bucket_id': 'entry:source_stage:wait6579_ev_cohort', 'stage': 'entry', 'classification_state': 'sim_auto_approved', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 130, 'source_quality_adjusted_ev_pct': 2.2594}, {'bucket_id': 'entry:stale_bucket:fresh_or_unflagged', 'stage': 'entry', 'classification_state': 'sim_auto_approved', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 130, 'source_quality_adjusted_ev_pct': 2.2594}, {'bucket_id': 'entry:time_bucket:time_unknown', 'stage': 'entry', 'classification_state': 'sim_auto_approved', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 130, 'source_quality_adjusted_ev_pct': 2.2594}, {'bucket_id': 'entry:score_band:score_70p', 'stage': 'entry', 'classification_state': 'sim_auto_approved', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 81, 'source_quality_adjusted_ev_pct': 2.4554}, {'bucket_id': 'entry:combo_entry_spot:score_score_70p_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_unknown_o', 'stage': 'entry', 'classification_state': 'sim_auto_approved', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 76, 'source_quality_adjusted_ev_pct': 2.6587}, {'bucket_id': 'entry:score_band:score_66_69', 'stage': 'entry', 'classification_state': 'sim_auto_approved', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 49, 'source_quality_adjusted_ev_pct': 1.5253}, {'bucket_id': 'entry:source_stage:scalp_entry_action_decision_snapshot', 'stage': 'entry', 'classification_state': 'sim_auto_approved', 'live_auto_apply_family': None, 'recommended_action': 'tighten_or_exclude', 'joined_sample': 18, 'source_quality_adjusted_ev_pct': -0.826}]`

## Lifecycle AI Context
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_ai_context/lifecycle_ai_context_2026-05-27.json`
- context_version: `lifecycle_ai_context_v1_2026-05-27` / authority: `ai_advisory_prompt_context_only`
- prompt_stage_count: `3` / runtime_effect: `False`
- stage_contexts: `[{'stage': 'entry', 'prompt_injection_allowed': True, 'policy_key': 'entry:weighted_adm_v1', 'alignment_hint': 'BUY_DEFENSIVE', 'context_contribution_score': -0.2988, 'attribution_quality_status': 'observational_only_pending_outcome'}, {'stage': 'submit', 'prompt_injection_allowed': False, 'policy_key': 'submit:weighted_adm_v1', 'alignment_hint': 'NO_CHANGE', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'holding', 'prompt_injection_allowed': True, 'policy_key': 'holding:weighted_adm_v1', 'alignment_hint': 'EXIT', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'scale_in', 'prompt_injection_allowed': False, 'policy_key': 'scale_in:weighted_adm_v1', 'alignment_hint': 'NO_CHANGE', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'exit', 'prompt_injection_allowed': True, 'policy_key': 'exit:weighted_adm_v1', 'alignment_hint': 'EXIT', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}]`

## Lifecycle AI Context Attribution
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_ai_context_attribution/lifecycle_ai_context_attribution_2026-05-27.json`
- eligible/applied/skipped: `2596` / `2596` / `0`
- replay_budget: `30`
- implementation_status: `implemented`
- stage_attribution: `{'entry': {'context_contribution_score': -0.2988, 'bounded_auxiliary_weight': -0.0448, 'attribution_quality_status': 'observational_only_pending_outcome', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': 0.0732, 'no_context_replay_observed': 0}, 'submit': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'holding': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'scale_in': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'exit': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}}`

## Institutional Flow Context
- artifact: `/home/ubuntu/KORStockScan/data/report/institutional_flow_context/institutional_flow_context_2026-05-27.json`
- status: `pass` / authority: `source_only_lifecycle_feature`
- rows ok/partial/missing/token_error: `120` / `0` / `0` / `0`
- join_rate_pct: `100.0`
- source_mix: `{'ka10059+ka10061': 120}`
- top_net_buy: `[{'stock_code': '005930', 'smart_money_net': 1277945, 'foreign_net_roll5': 0, 'inst_net_roll5': 9506452, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '200470', 'smart_money_net': 1089521, 'foreign_net_roll5': 1106929, 'inst_net_roll5': 15061, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '000660', 'smart_money_net': 513910, 'foreign_net_roll5': 0, 'inst_net_roll5': 2170394, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '347850', 'smart_money_net': 489811, 'foreign_net_roll5': 0, 'inst_net_roll5': 554016, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '417840', 'smart_money_net': 367130, 'foreign_net_roll5': 0, 'inst_net_roll5': 966345, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '196170', 'smart_money_net': 302831, 'foreign_net_roll5': 119510, 'inst_net_roll5': 280764, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '232680', 'smart_money_net': 302181, 'foreign_net_roll5': 322397, 'inst_net_roll5': 157250, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '042660', 'smart_money_net': 236599, 'foreign_net_roll5': 1717489, 'inst_net_roll5': 445302, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '397030', 'smart_money_net': 218973, 'foreign_net_roll5': 31272, 'inst_net_roll5': 228716, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '226950', 'smart_money_net': 191822, 'foreign_net_roll5': 119533, 'inst_net_roll5': 220903, 'regime': 'DUAL_ACCUMULATION'}]`

## Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-05-27.json`
- fresh: gemini=`True` claude=`True`
- consensus/orders/family_candidates: `5` / `12` / `3`

## Swing Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_2026-05-27.json`
- deepseek_lab_available: `True`
- findings/orders: `5` / `3`
- data_quality_warnings: `0`
- top_level_data_quality_warnings: `0`
- resolved_data_quality_warnings: `0`
- ofi_qi_stale_missing_unique_records: `20`
- ofi_qi_stale_missing_reasons: `{'micro_missing': 3832, 'micro_stale': 0, 'observer_unhealthy': 39, 'micro_not_ready': 3835, 'state_insufficient': 3835}`
- ofi_qi_stale_missing_reason_combinations: `{'micro_not_ready+state_insufficient': 3, 'micro_missing+micro_not_ready+state_insufficient': 3793, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 39}`
- ofi_qi_stale_missing_reason_combination_unique_records: `{'micro_missing+micro_not_ready+state_insufficient': 20, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 11}`
- ofi_qi_observer_unhealthy_overlap: `{'observer_unhealthy_total': 39, 'observer_unhealthy_with_other_reason': 39, 'observer_unhealthy_only': 0}`
- source_quality_blocked_families: `[{'family': 'swing_entry_ofi_qi_execution_quality', 'stage': 'entry', 'source_quality_blockers': ['entry_ofi_qi_invalid_micro_context'], 'invalid_micro_context_unique_record_count': 19, 'invalid_reason_combination_unique_record_counts': {'micro_missing+micro_not_ready+state_insufficient': 20, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 11}, 'automation_input': True, 'runtime_effect': False}, {'family': 'swing_scale_in_ofi_qi_confirmation', 'stage': 'scale_in', 'source_quality_blockers': ['scale_in_ofi_qi_invalid_micro_context'], 'invalid_micro_context_unique_record_count': 2, 'invalid_reason_combination_unique_record_counts': {'micro_missing+micro_not_ready+state_insufficient': 20, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 11}, 'automation_input': True, 'runtime_effect': False}]`
- carryover_warnings: `0`
- population_split_available: `True`

## Swing Strategy Discovery Sim
- artifact: `/home/ubuntu/KORStockScan/data/report/swing_strategy_discovery_ev/swing_strategy_discovery_ev_2026-05-27.json`
- authority: `swing_sim_exploration_only` / source_only: `True`
- candidate/arm/policy_exit_rows: `284` / `2272` / `2272`
- labeled/pending_future_quotes: `84` / `2056`
- implementation_status: `implemented`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- surviving/avoid_bucket_count: `1` / `2`
- runtime_effect: `False`

## Pipeline Event Verbosity
- artifact: `/home/ubuntu/KORStockScan/data/report/pipeline_event_verbosity/pipeline_event_verbosity_2026-05-27.json`
- state: `v2_shadow_pending_flush`
- recommended_workorder_state: `observe_pending_next_flush`
- high_volume_line_count: `83288`
- high_volume_byte_share_pct: `6.15`
- parity_ok: `False`
- suppress_eligibility: `False`

## Codebase Performance Workorder Source
- artifact: `/home/ubuntu/KORStockScan/data/report/codebase_performance_workorder/codebase_performance_workorder_2026-05-27.json`
- authority: `ops_performance_workorder_source`
- accepted/deferred/rejected: `7` / `3` / `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`

## Pattern Lab Audits
- currentness: status=`pass` fail=`0` orders=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-05-27.json`
- ai_review: status=`warning` orders=`1` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_ai_review/pattern_lab_ai_review_2026-05-27.json`
- time_window_regime_counterfactual: status=`pass` artifact=`/home/ubuntu/KORStockScan/data/report/time_window_regime_counterfactual/time_window_regime_counterfactual_2026-05-27.json`
- producer_gap_discovery: status=`warning` orders=`8` artifact=`/home/ubuntu/KORStockScan/data/report/producer_gap_discovery/producer_gap_discovery_2026-05-27.json`
- stage_hook_workorder_discovery: status=`warning` orders=`2` artifact=`/home/ubuntu/KORStockScan/data/report/stage_hook_workorder_discovery/stage_hook_workorder_discovery_2026-05-27.json`
- propagation: status=`pass` fail=`0` warnings=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_2026-05-27.json`

## Swing Runtime Approval
- request_report: `/home/ubuntu/KORStockScan/data/report/swing_runtime_approval/swing_runtime_approval_2026-05-26.json`
- approval_artifact: `-`
- requested/approved/live_dry_run: `0` / `0` / `0`
- dry_run_forced: `False`
- real_canary_policy: `swing_one_share_real_canary_phase0`
- one_share_real_canary_artifact: `-`
- selected_one_share_real_canary: `0`
- real_order_allowed_actions: `BUY_INITIAL, SELL_CLOSE`
- sim_only_actions: `AVG_DOWN, PYRAMID, SCALE_IN`
- scale_in_real_canary_policy: `swing_scale_in_real_canary_phase0`
- selected_scale_in_real_canary: `0`
- scale_in_real_execution_quality: `{'one_share_canary_selected': 0, 'scale_in_canary_selected': 0, 'execution_quality_source': 'real_only', 'sim_probe_ev_source': 'separate_from_broker_execution_quality'}`
- blocked: `[]`

## Code Improvement Workorder
- artifact: `/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-05-27.json`
- markdown: `/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-05-27.md`
- selected_order_count: `57`
- decision_counts: `{'attach_existing_family': 75, 'design_family_candidate': 7, 'defer_evidence': 10, 'reject': 3}`

## Approval Requests
- none

## Swing Approval Requests
- none

## Calibration Decisions
## Code Improvement Top Orders
- `order_entry_submit_drought_auto_resolution` decision=`attach_existing_family` subsystem=`runtime_instrumentation`
- `order_ai_threshold_miss_ev_recovery` decision=`attach_existing_family` subsystem=`entry_funnel`
- `order_entry_broker_receipt_contract_gap_review` decision=`attach_existing_family` subsystem=`runtime_instrumentation`

## Pattern Lab Top Findings
- `AI threshold miss EV recovery` route=`existing_family` family=`score65_74_recovery_probe`
- `No acute observability alert` route=`auto_family_candidate` family=`-`
- `latency guard miss EV recovery` route=`instrumentation_order` family=`-`

- `soft_stop_whipsaw_confirmation`: `adjust_up` sample=`9435/10`
- `holding_flow_ofi_smoothing`: `hold` sample=`3337/20`
- `protect_trailing_smoothing`: `adjust_down` sample=`120/20`
- `trailing_continuation`: `freeze` sample=`295/20`
- `market_regime_continuous_thresholds`: `hold_sample` sample=`4/10`
- `pre_submit_price_guard`: `hold_sample` sample=`36812/20`
- `score65_74_recovery_probe`: `adjust_up` sample=`293/20`
- `strength_momentum_soft_gate_p1`: `hold` sample=`50877/20`
- `overbought_pullback_guard_p1`: `hold` sample=`29662/20`
- `liquidity_pre_submit_guard_p1`: `hold` sample=`2645/20`
- `bad_entry_refined_canary`: `adjust_up` sample=`84480/10`
- `holding_exit_decision_matrix_advisory`: `hold_no_edge` sample=`11/1`
- `lifecycle_decision_matrix_runtime`: `adjust_up` sample=`41172/20`
- `scale_in_price_guard`: `hold` sample=`810/20`
- `position_sizing_cap_release`: `hold_sample` sample=`77/30`
- `position_sizing_dynamic_formula`: `hold_sample` sample=`13/30`

## Warnings
- `swing_strategy_discovery:pending_future_quotes`
- `swing_lifecycle_decision_matrix:pending_future_quotes`
- `pattern_lab_ai_review_warning`
