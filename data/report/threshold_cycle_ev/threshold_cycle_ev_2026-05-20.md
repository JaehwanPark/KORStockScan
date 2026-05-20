# Threshold Cycle Daily EV Report - 2026-05-20

## Runtime Apply
- status: `auto_bounded_live_ready`
- runtime_change: `True`
- selected_families: `soft_stop_whipsaw_confirmation, latency_classifier_runtime_profile, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, lifecycle_decision_matrix_runtime`

## Daily EV
- completed: `2` / open: `0`
- win/loss: `1` / `1` (`50.0`%)
- avg_profit_rate: `-0.27`%
- realized_pnl_krw: `-10747`
- full_fill_completed_avg_profit_rate: `0.0`%

## Entry Funnel
- budget_pass_to_submitted: `0` / `624` (`0.0`%)
- latency pass/block: `0` / `624`
- full/partial fill: `9` / `9`

## Holding Exit
- holding_reviews: `1754`
- exit_signals: `163`
- holding_review_ms_p95: `1721.0`

## Scalp Simulator
- authority: `equal_weight` / fill_policy: `signal_inclusive_best_ask_v1`
- armed/filled/sold: `238` / `238` / `238`
- expired/unpriced/duplicate: `0` / `0` / `717`
- entry_ai_price applied/skip: `0` / `6`
- submit_revalidation warning/block: `221` / `0`
- scale_in filled/unfilled: `0` / `12`
- overnight decision/sell/hold/carry_restored: `0` / `0` / `0` / `0`
- completed_profit_summary: `{'sample': 238, 'win_count': 63, 'loss_count': 175, 'avg_profit_rate': -0.5116, 'median_profit_rate': -0.47, 'downside_p10_profit_rate': -2.58, 'upside_p90_profit_rate': 1.98, 'win_rate': 0.2647, 'loss_rate': 0.7353, 'stddev_profit_rate': 1.8809}`
- post_sell_join: joined=`238` / pending=`0`
- post_sell_mfe_mae_10m: mfe=`1.3586`% / mae=`-4.3584`% / close=`-0.2243`%

## Missed Probe Counterfactual
- book: `scalp_score65_74_probe_counterfactual` / role: `missed_buy_probe_counterfactual`
- total/score65_74: `25` / `0`
- avg_expected_ev: `6.7725`% / score65_74_avg_expected_ev: `0.0`%
- actual_order_submitted: `False` / broker_order_forbidden: `True`
- authority: `missed_probe_ev_only_not_broker_execution`

## Scalp Entry ADM
- artifact: `/home/ubuntu/KORStockScan/data/report/scalp_entry_action_decision_matrix/scalp_entry_action_decision_matrix_2026-05-20.json`
- status: `pass` / authority: `entry_advisory_prompt_context_only`
- total/joined/floor: `652` / `154` / `20`
- prompt_applied_count: `557`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 652}`
- forced_action_counts: `{'-': 652}`
- missing_actions: `[]`
- zero_sample_actions: `['SKIP_STALE', 'BUY_DEFENSIVE', 'SKIP_PRE_SUBMIT_SAFETY']`
- top_actions: `[{'action': 'BUY_NOW', 'sample_count': 2, 'joined_sample': 2, 'source_quality_adjusted_ev_pct': 0.485}, {'action': 'WAIT_REQUOTE', 'sample_count': 4, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'NO_BUY_AI', 'sample_count': 645, 'joined_sample': 152, 'source_quality_adjusted_ev_pct': -0.0527}, {'action': 'SKIP_SOURCE_QUALITY', 'sample_count': 1, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}]`

## Lifecycle Decision Matrix
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-05-20.json`
- status: `pass` / version: `lifecycle_decision_matrix_v1_2026-05-20`
- total/joined: `2000` / `1607`
- policy_pass/promote_ready: `3` / `1`
- fixed_threshold_roles: `{'hard_safety': ['broker_submit_guard', 'stale_quote_submit_block', 'price_freshness_guard', 'hard_stop', 'protect_stop', 'emergency_stop', 'account_order_cooldown_qty_guard'], 'baseline_prior': ['BUY_SCORE_THRESHOLD', 'VPW_MIN_SCORE', 'strength_momentum_cutoff', 'entry_score_cutoff'], 'bounded_tunable': ['SCALP_ENTRY_LATENCY_MAX_WS_AGE_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_WS_JITTER_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_SPREAD_RATIO_FOR_CAUTION', 'score65_74_recovery_probe', 'soft_stop_whipsaw_confirmation', 'holding_flow_override', 'scale_in_price_guard'], 'legacy_archive': ['fallback_scout_main', 'fallback_single', 'latency_fallback_split_entry', 'legacy_latency_composite', 'closed_shadow_axes']}`
- policy_entries: `[{'stage': 'entry', 'sample': 442, 'joined_sample': 49, 'stage_ev_composite_pct': 2.0917, 'confidence': 0.5432, 'selected_action': 'BUY_DEFENSIVE', 'source_quality_gate': 'pass', 'promote_ready': True}, {'stage': 'submit', 'sample': 0, 'joined_sample': 0, 'stage_ev_composite_pct': None, 'confidence': 0.0, 'selected_action': 'NO_CHANGE', 'source_quality_gate': 'hold_sample', 'promote_ready': False}, {'stage': 'holding', 'sample': 0, 'joined_sample': 0, 'stage_ev_composite_pct': None, 'confidence': 0.0, 'selected_action': 'NO_CHANGE', 'source_quality_gate': 'hold_sample', 'promote_ready': False}, {'stage': 'scale_in', 'sample': 1194, 'joined_sample': 1194, 'stage_ev_composite_pct': -0.2647, 'confidence': 1.0, 'selected_action': 'NO_CHANGE', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'exit', 'sample': 364, 'joined_sample': 364, 'stage_ev_composite_pct': -0.5841, 'confidence': 1.0, 'selected_action': 'EXIT', 'source_quality_gate': 'pass', 'promote_ready': False}]`

## Lifecycle AI Context
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_ai_context/lifecycle_ai_context_2026-05-20.json`
- context_version: `lifecycle_ai_context_v1_2026-05-20` / authority: `ai_advisory_prompt_context_only`
- prompt_stage_count: `3` / runtime_effect: `False`
- stage_contexts: `[{'stage': 'entry', 'prompt_injection_allowed': True, 'policy_key': 'entry:weighted_adm_v1', 'alignment_hint': 'BUY_DEFENSIVE', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'submit', 'prompt_injection_allowed': False, 'policy_key': 'submit:weighted_adm_v1', 'alignment_hint': 'NO_CHANGE', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'holding', 'prompt_injection_allowed': True, 'policy_key': 'holding:weighted_adm_v1', 'alignment_hint': 'NO_CHANGE', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'scale_in', 'prompt_injection_allowed': False, 'policy_key': 'scale_in:weighted_adm_v1', 'alignment_hint': 'NO_CHANGE', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'exit', 'prompt_injection_allowed': True, 'policy_key': 'exit:weighted_adm_v1', 'alignment_hint': 'EXIT', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}]`

## Lifecycle AI Context Attribution
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_ai_context_attribution/lifecycle_ai_context_attribution_2026-05-20.json`
- eligible/applied/skipped: `0` / `0` / `0`
- replay_budget: `30`
- implementation_status: `implemented`
- stage_attribution: `{'entry': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'submit': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'holding': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'scale_in': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'exit': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}}`

## Institutional Flow Context
- artifact: `/home/ubuntu/KORStockScan/data/report/institutional_flow_context/institutional_flow_context_2026-05-20.json`
- status: `pass` / authority: `source_only_lifecycle_feature`
- rows ok/partial/missing/token_error: `120` / `0` / `0` / `0`
- join_rate_pct: `100.0`
- source_mix: `{'ka10059+ka10061': 120}`
- top_net_buy: `[{'stock_code': '047040', 'smart_money_net': 1182718, 'foreign_net_roll5': 0, 'inst_net_roll5': 0, 'regime': 'UNKNOWN'}, {'stock_code': '005950', 'smart_money_net': 605514, 'foreign_net_roll5': 749879, 'inst_net_roll5': 619534, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '011200', 'smart_money_net': 233368, 'foreign_net_roll5': 875066, 'inst_net_roll5': 58934, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '187790', 'smart_money_net': 223491, 'foreign_net_roll5': 0, 'inst_net_roll5': 820524, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '001450', 'smart_money_net': 217783, 'foreign_net_roll5': 2239301, 'inst_net_roll5': 1213689, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '456010', 'smart_money_net': 205305, 'foreign_net_roll5': 246898, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}, {'stock_code': '032640', 'smart_money_net': 199618, 'foreign_net_roll5': 231962, 'inst_net_roll5': 668701, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '036540', 'smart_money_net': 196389, 'foreign_net_roll5': 847062, 'inst_net_roll5': 190760, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '054210', 'smart_money_net': 146323, 'foreign_net_roll5': 0, 'inst_net_roll5': 77310, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '024060', 'smart_money_net': 143665, 'foreign_net_roll5': 385880, 'inst_net_roll5': 187, 'regime': 'DUAL_ACCUMULATION'}]`

## Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-05-20.json`
- fresh: gemini=`True` claude=`True`
- consensus/orders/family_candidates: `6` / `13` / `3`

## Swing Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_2026-05-20.json`
- deepseek_lab_available: `True`
- findings/orders: `5` / `4`
- data_quality_warnings: `1`
- top_level_data_quality_warnings: `0`
- resolved_data_quality_warnings: `1`
- ofi_qi_stale_missing_unique_records: `2`
- ofi_qi_stale_missing_reasons: `{'micro_missing': 636, 'micro_stale': 0, 'observer_unhealthy': 1, 'micro_not_ready': 20, 'state_insufficient': 20}`
- ofi_qi_stale_missing_reason_combinations: `{'micro_missing': 615, 'micro_missing+observer_unhealthy': 1, 'micro_missing+micro_not_ready+state_insufficient': 20}`
- ofi_qi_stale_missing_reason_combination_unique_records: `{'micro_missing+micro_not_ready+state_insufficient': 2}`
- ofi_qi_observer_unhealthy_overlap: `{'observer_unhealthy_total': 1, 'observer_unhealthy_with_other_reason': 1, 'observer_unhealthy_only': 0}`
- source_quality_blocked_families: `[{'family': 'swing_scale_in_ofi_qi_confirmation', 'stage': 'scale_in', 'source_quality_blockers': ['scale_in_ofi_qi_invalid_micro_context'], 'invalid_micro_context_unique_record_count': 2, 'invalid_reason_combination_unique_record_counts': {'micro_missing+micro_not_ready+state_insufficient': 2}, 'automation_input': True, 'runtime_effect': False}]`
- carryover_warnings: `0`
- population_split_available: `True`

## Swing Strategy Discovery Sim
- artifact: `/home/ubuntu/KORStockScan/data/report/swing_strategy_discovery_ev/swing_strategy_discovery_ev_2026-05-20.json`
- authority: `swing_sim_exploration_only` / source_only: `True`
- candidate/arm/policy_exit_rows: `50` / `400` / `400`
- labeled/pending_future_quotes: `0` / `400`
- implementation_status: `implemented`
- top_surviving_arm: `-`
- surviving/avoid_bucket_count: `0` / `0`
- runtime_effect: `False`

## Pipeline Event Verbosity
- artifact: `/home/ubuntu/KORStockScan/data/report/pipeline_event_verbosity/pipeline_event_verbosity_2026-05-20.json`
- state: `v2_shadow_pending_flush`
- recommended_workorder_state: `observe_pending_next_flush`
- high_volume_line_count: `469263`
- high_volume_byte_share_pct: `56.52`
- parity_ok: `False`
- suppress_eligibility: `False`

## Codebase Performance Workorder Source
- artifact: `/home/ubuntu/KORStockScan/data/report/codebase_performance_workorder/codebase_performance_workorder_2026-05-20.json`
- authority: `ops_performance_workorder_source`
- accepted/deferred/rejected: `7` / `3` / `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`

## Pattern Lab Audits
- currentness: status=`pass` fail=`0` orders=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-05-20.json`
- propagation: status=`pass` fail=`0` warnings=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_2026-05-20.json`

## Swing Runtime Approval
- request_report: `/home/ubuntu/KORStockScan/data/report/swing_runtime_approval/swing_runtime_approval_2026-05-19.json`
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
- artifact: `/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-05-20.json`
- markdown: `/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-05-20.md`
- selected_order_count: `12`
- decision_counts: `{'attach_existing_family': 18, 'design_family_candidate': 6, 'defer_evidence': 11, 'reject': 3}`

## Approval Requests
- none

## Swing Approval Requests
- none

## Calibration Decisions
## Code Improvement Top Orders
- `order_ai_threshold_dominance` decision=`attach_existing_family` subsystem=`entry_funnel`
- `order_perf_buy_funnel_json_scan` decision=`attach_existing_family` subsystem=`buy_funnel_sentinel`
- `order_ai_threshold_miss_ev_recovery` decision=`attach_existing_family` subsystem=`entry_funnel`

## Pattern Lab Top Findings
- `AI threshold dominance` route=`existing_family` family=`score65_74_recovery_probe`
- `AI threshold miss EV recovery` route=`existing_family` family=`score65_74_recovery_probe`
- `Budget pass without submit` route=`auto_family_candidate` family=`-`

- `soft_stop_whipsaw_confirmation`: `adjust_up` sample=`3076/10`
- `holding_flow_ofi_smoothing`: `hold` sample=`4323/20`
- `protect_trailing_smoothing`: `adjust_down` sample=`96/20`
- `trailing_continuation`: `freeze` sample=`104/20`
- `pre_submit_price_guard`: `freeze` sample=`624/20`
- `score65_74_recovery_probe`: `adjust_up` sample=`60/20`
- `strength_momentum_soft_gate_p1`: `hold` sample=`91122/20`
- `overbought_pullback_guard_p1`: `hold` sample=`61881/20`
- `liquidity_pre_submit_guard_p1`: `hold` sample=`8571/20`
- `bad_entry_refined_canary`: `adjust_up` sample=`18005/10`
- `holding_exit_decision_matrix_advisory`: `hold_no_edge` sample=`3/1`
- `lifecycle_decision_matrix_runtime`: `adjust_up` sample=`2000/20`
- `scale_in_price_guard`: `hold` sample=`679/20`
- `position_sizing_cap_release`: `hold_sample` sample=`24/30`
- `position_sizing_dynamic_formula`: `hold_sample` sample=`2/30`

## Warnings
- `lifecycle_ai_context_attribution:lifecycle_ai_context_runtime_provenance_missing`
- `swing_strategy_discovery:pending_future_quotes`
- `swing_strategy_discovery:sample_floor_not_met`
