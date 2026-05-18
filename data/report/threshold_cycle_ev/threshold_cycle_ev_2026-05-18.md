# Threshold Cycle Daily EV Report - 2026-05-18

## Runtime Apply
- status: `auto_bounded_live_ready`
- runtime_change: `True`
- selected_families: `score65_74_recovery_probe, bad_entry_refined_canary, swing_one_share_real_canary_phase0, swing_gatekeeper_reject_cooldown`

## Daily EV
- completed: `0` / open: `0`
- win/loss: `0` / `0` (`0.0`%)
- avg_profit_rate: `0.0`%
- realized_pnl_krw: `0`
- full_fill_completed_avg_profit_rate: `0.0`%

## Entry Funnel
- budget_pass_to_submitted: `0` / `11` (`0.0`%)
- latency pass/block: `0` / `11`
- full/partial fill: `0` / `0`

## Holding Exit
- holding_reviews: `5`
- exit_signals: `37`
- holding_review_ms_p95: `1429.0`

## Scalp Simulator
- authority: `equal_weight` / fill_policy: `signal_inclusive_best_ask_v1`
- armed/filled/sold: `2` / `2` / `2`
- expired/unpriced/duplicate: `0` / `0` / `123`
- entry_ai_price applied/skip: `2` / `0`
- submit_revalidation warning/block: `1` / `0`
- scale_in filled/unfilled: `0` / `0`
- completed_profit_summary: `{'sample': 2, 'win_count': 0, 'loss_count': 2, 'avg_profit_rate': -2.225, 'median_profit_rate': -2.54, 'downside_p10_profit_rate': -2.54, 'upside_p90_profit_rate': -1.91, 'win_rate': 0.0, 'loss_rate': 1.0, 'stddev_profit_rate': 0.4455}`
- post_sell_join: joined=`2` / pending=`0`
- post_sell_mfe_mae_10m: mfe=`-0.1425`% / mae=`-3.7055`% / close=`-1.472`%

## Missed Probe Counterfactual
- book: `scalp_score65_74_probe_counterfactual` / role: `missed_buy_probe_counterfactual`
- total/score65_74: `12` / `0`
- avg_expected_ev: `4.5216`% / score65_74_avg_expected_ev: `0.0`%
- actual_order_submitted: `False` / broker_order_forbidden: `True`
- authority: `missed_probe_ev_only_not_broker_execution`

## Scalp Entry ADM
- artifact: `/home/ubuntu/KORStockScan/data/report/scalp_entry_action_decision_matrix/scalp_entry_action_decision_matrix_2026-05-18.json`
- status: `warning` / authority: `entry_advisory_prompt_context_only`
- total/joined/floor: `73` / `2` / `20`
- prompt_applied_count: `0`
- missing_actions: `['WAIT_REQUOTE', 'SKIP_STALE', 'BUY_DEFENSIVE', 'SKIP_PRE_SUBMIT_SAFETY']`
- top_actions: `[{'action': 'BUY_NOW', 'sample_count': 2, 'joined_sample': 2, 'source_quality_adjusted_ev_pct': -2.225}, {'action': 'NO_BUY_AI', 'sample_count': 70, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'SKIP_SOURCE_QUALITY', 'sample_count': 1, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}]`

## Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-05-18.json`
- fresh: gemini=`True` claude=`True`
- consensus/orders/family_candidates: `6` / `13` / `3`

## Swing Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_2026-05-18.json`
- deepseek_lab_available: `True`
- findings/orders: `5` / `4`
- data_quality_warnings: `1`
- ofi_qi_stale_missing_unique_records: `2`
- ofi_qi_stale_missing_reasons: `{'micro_missing': 68, 'micro_stale': 0, 'observer_unhealthy': 6, 'micro_not_ready': 6, 'state_insufficient': 6}`
- ofi_qi_stale_missing_reason_combinations: `{'micro_missing': 62, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 6}`
- ofi_qi_stale_missing_reason_combination_unique_records: `{'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 2}`
- ofi_qi_observer_unhealthy_overlap: `{'observer_unhealthy_total': 6, 'observer_unhealthy_with_other_reason': 6, 'observer_unhealthy_only': 0}`
- source_quality_blocked_families: `[{'family': 'swing_scale_in_ofi_qi_confirmation', 'stage': 'scale_in', 'source_quality_blockers': ['scale_in_ofi_qi_invalid_micro_context'], 'invalid_micro_context_unique_record_count': 2, 'invalid_reason_combination_unique_record_counts': {'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 2}, 'automation_input': True, 'runtime_effect': False}]`
- carryover_warnings: `0`
- population_split_available: `True`

## Pipeline Event Verbosity
- artifact: `/home/ubuntu/KORStockScan/data/report/pipeline_event_verbosity/pipeline_event_verbosity_2026-05-18.json`
- state: `v2_shadow_missing`
- recommended_workorder_state: `open_shadow_order`
- high_volume_line_count: `1443016`
- high_volume_byte_share_pct: `96.59`
- parity_ok: `False`
- suppress_eligibility: `False`

## Codebase Performance Workorder Source
- artifact: `/home/ubuntu/KORStockScan/data/report/codebase_performance_workorder/codebase_performance_workorder_2026-05-18.json`
- authority: `ops_performance_workorder_source`
- accepted/deferred/rejected: `7` / `3` / `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`

## Pattern Lab Audits
- currentness: status=`pass` fail=`0` orders=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-05-18.json`
- propagation: status=`warning` fail=`0` warnings=`1` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_2026-05-18.json`

## Swing Runtime Approval
- request_report: `-`
- approval_artifact: `-`
- requested/approved/live_dry_run: `0` / `0` / `0`
- dry_run_forced: `False`
- real_canary_policy: `-`
- one_share_real_canary_artifact: `-`
- selected_one_share_real_canary: `0`
- real_order_allowed_actions: ``
- sim_only_actions: ``
- scale_in_real_canary_policy: `-`
- selected_scale_in_real_canary: `0`
- scale_in_real_execution_quality: `{'one_share_canary_selected': 0, 'scale_in_canary_selected': 0, 'execution_quality_source': 'real_only', 'sim_probe_ev_source': 'separate_from_broker_execution_quality'}`
- blocked: `[]`

## Code Improvement Workorder
- artifact: `/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-05-18.json`
- markdown: `/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-05-18.md`
- selected_order_count: `12`
- decision_counts: `{'implement_now': 3, 'attach_existing_family': 15, 'design_family_candidate': 6, 'defer_evidence': 11, 'reject': 3}`

## Approval Requests
- none

## Swing Approval Requests
- none

## Calibration Decisions
## Code Improvement Top Orders
- `order_pipeline_event_compaction_v2_shadow` decision=`implement_now` subsystem=`runtime_instrumentation`
- `order_high_volume_diagnostic_stage_contract_labels` decision=`implement_now` subsystem=`runtime_instrumentation`
- `order_scalp_entry_adm_daily_tuning_coverage` decision=`implement_now` subsystem=`entry_funnel`

## Pattern Lab Top Findings
- `AI threshold dominance` route=`existing_family` family=`score65_74_recovery_probe`
- `AI threshold miss EV recovery` route=`existing_family` family=`score65_74_recovery_probe`
- `Budget pass without submit` route=`auto_family_candidate` family=`-`

- `soft_stop_whipsaw_confirmation`: `adjust_up` sample=`316/10`
- `holding_flow_ofi_smoothing`: `hold` sample=`334/20`
- `protect_trailing_smoothing`: `adjust_down` sample=`96/20`
- `trailing_continuation`: `freeze` sample=`96/20`
- `pre_submit_price_guard`: `hold_sample` sample=`11/20`
- `score65_74_recovery_probe`: `adjust_up` sample=`50/20`
- `strength_momentum_soft_gate_p1`: `hold_sample` sample=`0/20`
- `overbought_pullback_guard_p1`: `hold` sample=`173269/20`
- `liquidity_pre_submit_guard_p1`: `hold` sample=`19880/20`
- `bad_entry_refined_canary`: `adjust_up` sample=`2076/10`
- `holding_exit_decision_matrix_advisory`: `hold_no_edge` sample=`0/1`
- `scale_in_price_guard`: `hold` sample=`303/20`
- `position_sizing_cap_release`: `hold_sample` sample=`19/30`
- `position_sizing_dynamic_formula`: `hold_sample` sample=`0/30`

## Warnings
- `swing_lab_dq:OFI/QI stale/missing ratio: 0.4304 (68/158); reasons: micro_missing=68, observer_unhealthy=6, micro_not_ready=6, state_insufficient=6`
- `scalp_entry_adm:joined_sample_below_sample_floor`
- `scalp_entry_adm:missing_action_bucket`
- `scalp_entry_adm:prompt_context_not_loaded`
- `pattern_lab_propagation_audit_warning`
