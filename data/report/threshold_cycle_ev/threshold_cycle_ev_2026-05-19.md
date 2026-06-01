# Threshold Cycle Daily EV Report - 2026-05-19

## Runtime Apply
- status: `auto_bounded_live_ready`
- runtime_change: `True`
- selected_families: `soft_stop_whipsaw_confirmation, latency_classifier_runtime_profile, score65_74_recovery_probe`

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
- latency recommended action: `-` (`-`)
- latency profile generation: `{}`
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
- armed/filled/sold: `100` / `100` / `100`
- expired/unpriced/duplicate: `0` / `0` / `768`
- entry_ai_price applied/skip: `7` / `4`
- submit_revalidation warning/block: `92` / `0`
- scale_in filled/unfilled: `0` / `8`
- overnight decision/sell/hold/carry_restored: `0` / `0` / `0` / `0`
- completed_profit_summary: `{'sample': 100, 'win_count': 50, 'loss_count': 50, 'avg_profit_rate': -0.226, 'median_profit_rate': -0.03, 'downside_p10_profit_rate': -2.53, 'upside_p90_profit_rate': 1.97, 'win_rate': 0.5, 'loss_rate': 0.5, 'stddev_profit_rate': 1.9191}`
- post_sell_join: joined=`95` / pending=`5`
- post_sell_mfe_mae_10m: mfe=`1.6161`% / mae=`-5.8971`% / close=`0.0764`%

## Missed Probe Counterfactual
- book: `-` / role: `-`
- total/score65_74: `None` / `None`
- avg_expected_ev: `None`% / score65_74_avg_expected_ev: `None`%
- actual_order_submitted: `None` / broker_order_forbidden: `None`
- authority: `-`

## Scalp Entry ADM
- artifact: `/home/ubuntu/KORStockScan/data/report/scalp_entry_action_decision_matrix/scalp_entry_action_decision_matrix_2026-05-19.json`
- status: `pass` / authority: `entry_advisory_prompt_context_only`
- total/joined/floor: `614` / `72` / `20`
- prompt_applied_count: `506`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 614}`
- forced_action_counts: `{'-': 614}`
- missing_actions: `[]`
- zero_sample_actions: `['WAIT_REQUOTE', 'SKIP_STALE', 'BUY_DEFENSIVE']`
- top_actions: `[{'action': 'BUY_NOW', 'sample_count': 1, 'joined_sample': 1, 'source_quality_adjusted_ev_pct': -1.77}, {'action': 'NO_BUY_AI', 'sample_count': 609, 'joined_sample': 71, 'source_quality_adjusted_ev_pct': -0.0269}, {'action': 'SKIP_SOURCE_QUALITY', 'sample_count': 2, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'SKIP_PRE_SUBMIT_SAFETY', 'sample_count': 2, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}]`

## Lifecycle Decision Matrix
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-05-19.json`
- status: `pass` / version: `lifecycle_decision_matrix_v1_2026-05-19`
- total/joined: `13886` / `13393`
- policy_pass/promote_ready: `4` / `0`
- lifecycle_flow buckets/complete/runtime/workorders: `35` / `0` / `0` / `20`
- holding/exit buckets: `28` / `41`
- holding/exit workorders: `10` / `10`
- lifecycle identity missing/join_rate: `0` / `1.0`
- lifecycle complete_flow_rate: `0.0`
- incomplete_flow_reason_counts: `{'missing_submit': 13552, 'missing_holding': 13552, 'missing_exit': 13552, 'missing_entry': 13602}`
- fixed_threshold_roles: `{'hard_safety': ['broker_submit_guard', 'stale_quote_submit_block', 'price_freshness_guard', 'hard_stop', 'protect_stop', 'emergency_stop', 'account_order_cooldown_qty_guard'], 'baseline_prior': ['BUY_SCORE_THRESHOLD', 'VPW_MIN_SCORE', 'strength_momentum_cutoff', 'entry_score_cutoff'], 'bounded_tunable': ['SCALP_ENTRY_LATENCY_MAX_WS_AGE_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_WS_JITTER_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_SPREAD_RATIO_FOR_CAUTION', 'score65_74_recovery_probe', 'soft_stop_whipsaw_confirmation', 'holding_flow_override', 'scale_in_price_guard'], 'legacy_archive': ['fallback_scout_main', 'fallback_single', 'latency_fallback_split_entry', 'legacy_latency_composite', 'closed_shadow_axes']}`
- policy_entries: `[{'stage': 'entry', 'sample': 50, 'joined_sample': 0, 'stage_ev_composite_pct': None, 'confidence': 0.0, 'selected_action': 'NO_CHANGE', 'source_quality_gate': 'hold_sample', 'promote_ready': False}, {'stage': 'submit', 'sample': 100, 'joined_sample': 100, 'stage_ev_composite_pct': -0.6895, 'confidence': 1.0, 'selected_action': 'NO_CHANGE', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'holding', 'sample': 113, 'joined_sample': 100, 'stage_ev_composite_pct': -0.4847, 'confidence': 1.0, 'selected_action': 'EXIT', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'scale_in', 'sample': 13510, 'joined_sample': 13080, 'stage_ev_composite_pct': -0.1662, 'confidence': 1.0, 'selected_action': 'NO_CHANGE', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'exit', 'sample': 113, 'joined_sample': 113, 'stage_ev_composite_pct': -0.4446, 'confidence': 1.0, 'selected_action': 'EXIT', 'source_quality_gate': 'pass', 'promote_ready': False}]`

## Lifecycle Bucket Discovery
- artifact: `-`
- status: `missing` / human_intervention_required: `False`
- candidates/surfaced: `0` / `0`
- sim_auto/live_auto/new_bucket: `0` / `0` / `0`
- role/window: `new_pattern_detection` / `daily_only`
- parent_count/granularity/conflict: `None` / `None` / `None`
- state_counts: `{}`
- top_surfaced: `[]`

## Lifecycle Bucket Windows
- promotion_window: `mtd`
- confirmation_windows: `['rolling5d', 'rolling10d']`
- windows: `{'rolling5d': {'available': False, 'artifact': None, 'window_role': 'rolling_confirmation', 'window_policy': 'rolling5d', 'status': 'missing', 'parent_bucket_count': 0, 'selected_parent_level': None, 'parent_granularity_status': None, 'absorbed_child_count': 0, 'absorbed_sample_count': 0, 'child_conflict_warning_count': 0, 'live_auto_apply_ready_count': 0, 'source_contract_status': None, 'ai_two_pass_review_status': None}, 'rolling10d': {'available': False, 'artifact': None, 'window_role': 'rolling_confirmation', 'window_policy': 'rolling10d', 'status': 'missing', 'parent_bucket_count': 0, 'selected_parent_level': None, 'parent_granularity_status': None, 'absorbed_child_count': 0, 'absorbed_sample_count': 0, 'child_conflict_warning_count': 0, 'live_auto_apply_ready_count': 0, 'source_contract_status': None, 'ai_two_pass_review_status': None}, 'mtd': {'available': False, 'artifact': None, 'window_role': 'promotion_confirmation', 'window_policy': 'mtd', 'status': 'missing', 'parent_bucket_count': 0, 'selected_parent_level': None, 'parent_granularity_status': None, 'absorbed_child_count': 0, 'absorbed_sample_count': 0, 'child_conflict_warning_count': 0, 'live_auto_apply_ready_count': 0, 'source_contract_status': None, 'ai_two_pass_review_status': None}}`

## Lifecycle AI Context
- artifact: `-`
- context_version: `-` / authority: `ai_advisory_prompt_context_only`
- prompt_stage_count: `0` / runtime_effect: `False`
- stage_contexts: `[]`

## Lifecycle AI Context Attribution
- artifact: `-`
- eligible/applied/skipped: `0` / `0` / `None`
- replay_budget: `None`
- implementation_status: `-`
- stage_attribution: `{}`

## Institutional Flow Context
- artifact: `-`
- status: `missing` / authority: `source_only_lifecycle_feature`
- rows ok/partial/missing/token_error: `None` / `None` / `None` / `None`
- join_rate_pct: `0.0`
- source_mix: `{}`
- top_net_buy: `[]`

## Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-05-19.json`
- fresh: gemini=`True` claude=`True`
- consensus/orders/family_candidates: `6` / `13` / `3`

## Swing Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_2026-05-19.json`
- deepseek_lab_available: `True`
- findings/orders: `5` / `4`
- data_quality_warnings: `1`
- top_level_data_quality_warnings: `0`
- resolved_data_quality_warnings: `1`
- ofi_qi_stale_missing_unique_records: `5`
- ofi_qi_stale_missing_reasons: `{'micro_missing': 470, 'micro_stale': 0, 'observer_unhealthy': 1, 'micro_not_ready': 24, 'state_insufficient': 24}`
- ofi_qi_stale_missing_reason_combinations: `{'micro_missing': 446, 'micro_missing+micro_not_ready+state_insufficient': 23, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 1}`
- ofi_qi_stale_missing_reason_combination_unique_records: `{'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 1, 'micro_missing+micro_not_ready+state_insufficient': 4}`
- ofi_qi_observer_unhealthy_overlap: `{'observer_unhealthy_total': 1, 'observer_unhealthy_with_other_reason': 1, 'observer_unhealthy_only': 0}`
- source_quality_blocked_families: `[{'family': 'swing_scale_in_ofi_qi_confirmation', 'stage': 'scale_in', 'source_quality_blockers': ['scale_in_ofi_qi_invalid_micro_context'], 'invalid_micro_context_unique_record_count': 1, 'invalid_reason_combination_unique_record_counts': {'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 1, 'micro_missing+micro_not_ready+state_insufficient': 4}, 'automation_input': True, 'runtime_effect': False}]`
- carryover_warnings: `0`
- population_split_available: `True`

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
- artifact: `/home/ubuntu/KORStockScan/data/report/pipeline_event_verbosity/pipeline_event_verbosity_2026-05-19.json`
- state: `v2_shadow_pending_flush`
- recommended_workorder_state: `observe_pending_next_flush`
- high_volume_line_count: `412500`
- high_volume_byte_share_pct: `68.45`
- parity_ok: `False`
- suppress_eligibility: `False`

## Codebase Performance Workorder Source
- artifact: `/home/ubuntu/KORStockScan/data/report/codebase_performance_workorder/codebase_performance_workorder_2026-05-19.json`
- authority: `ops_performance_workorder_source`
- accepted/deferred/rejected: `7` / `3` / `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`

## Pattern Lab Audits
- currentness: status=`pass` fail=`0` orders=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-05-19.json`
- ai_review: status=`missing` orders=`0` artifact=`-`
- time_window_regime_counterfactual: status=`missing` artifact=`-`
- producer_gap_discovery: status=`missing` orders=`0` artifact=`-`
- stage_hook_workorder_discovery: status=`missing` orders=`0` artifact=`-`
- propagation: status=`pass` fail=`0` warnings=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_2026-05-19.json`

## Swing Runtime Approval
- request_report: `/home/ubuntu/KORStockScan/data/report/swing_runtime_approval/swing_runtime_approval_2026-05-18.json`
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
- artifact: `/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-05-19.json`
- markdown: `/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-05-19.md`
- selected_order_count: `58`
- decision_counts: `{'implement_now': 16, 'attach_existing_family': 59, 'design_family_candidate': 7, 'defer_evidence': 10, 'reject': 3}`

## Approval Requests
- none

## Swing Approval Requests
- none

## Calibration Decisions
## Code Improvement Top Orders
- `order_entry_sim_submit_path_bucket_instrumentation` decision=`implement_now` subsystem=`runtime_instrumentation`
- `order_lifecycle_exit_bucket_combo_exit_result_source_scalp_sim_overnight_sell_today_rule_scalp_sim_overnight_sell_tod_7b698c08` decision=`implement_now` subsystem=`lifecycle_decision_matrix`
- `order_lifecycle_exit_bucket_combo_exit_result_source_scalp_sim_overnight_sell_today_rule_scalp_sim_overnight_sell_tod_d982edbd` decision=`implement_now` subsystem=`lifecycle_decision_matrix`

## Pattern Lab Top Findings
- `AI threshold dominance` route=`existing_family` family=`score65_74_recovery_probe`
- `AI threshold miss EV recovery` route=`existing_family` family=`score65_74_recovery_probe`
- `Budget pass without submit` route=`auto_family_candidate` family=`-`

- `soft_stop_whipsaw_confirmation`: `adjust_up` sample=`1757/10`
- `holding_flow_ofi_smoothing`: `hold` sample=`3523/20`
- `protect_trailing_smoothing`: `adjust_down` sample=`96/20`
- `trailing_continuation`: `freeze` sample=`96/20`
- `pre_submit_price_guard`: `freeze` sample=`716/20`
- `score65_74_recovery_probe`: `hold` sample=`54/20`
- `strength_momentum_soft_gate_p1`: `hold` sample=`50152/20`
- `overbought_pullback_guard_p1`: `hold` sample=`95448/20`
- `liquidity_pre_submit_guard_p1`: `hold` sample=`15527/20`
- `bad_entry_refined_canary`: `adjust_up` sample=`11684/10`
- `holding_exit_decision_matrix_advisory`: `hold_no_edge` sample=`0/1`
- `lifecycle_decision_matrix_runtime`: `adjust_up` sample=`207/20`
- `scale_in_price_guard`: `hold` sample=`482/20`
- `position_sizing_cap_release`: `hold_sample` sample=`19/30`
- `position_sizing_dynamic_formula`: `hold_sample` sample=`0/30`

## Warnings
- `trade_review_missing`
- `performance_tuning_missing`
- `lifecycle_bucket_discovery_missing`
- `lifecycle_bucket_discovery_missing`
- `lifecycle_bucket_windows:rolling5d_missing`
- `lifecycle_bucket_windows:rolling10d_missing`
- `lifecycle_bucket_windows:mtd_missing`
- `lifecycle_ai_context_missing`
- `lifecycle_ai_context_attribution_missing`
- `swing_strategy_discovery_ev_missing`
- `swing_lifecycle_decision_matrix:swing_strategy_discovery_sim_missing`
- `institutional_flow_context_missing`
- `pattern_lab_ai_review_missing`
- `time_window_regime_counterfactual_missing`
- `producer_gap_discovery_missing`
- `stage_hook_workorder_discovery_missing`
- `stage_hook_runtime_scaffold_missing`
