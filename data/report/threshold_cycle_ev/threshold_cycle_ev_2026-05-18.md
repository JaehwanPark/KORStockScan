# Threshold Cycle Daily EV Report - 2026-05-18

## Runtime Apply
- status: `auto_bounded_live_ready`
- runtime_change: `True`
- selected_families: `bad_entry_refined_canary, swing_one_share_real_canary_phase0, swing_gatekeeper_reject_cooldown`

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
- exit_signals: `31`
- holding_review_ms_p95: `1429.0`

## Scalp Simulator
- authority: `equal_weight` / fill_policy: `signal_inclusive_best_ask_v1`
- armed/filled/sold: `1` / `1` / `1`
- expired/unpriced/duplicate: `0` / `0` / `10`
- entry_ai_price applied/skip: `1` / `0`
- submit_revalidation warning/block: `0` / `0`
- scale_in filled/unfilled: `0` / `0`
- completed_profit_summary: `{'sample': 1, 'win_count': 0, 'loss_count': 1, 'avg_profit_rate': -2.54, 'median_profit_rate': -2.54, 'downside_p10_profit_rate': -2.54, 'upside_p90_profit_rate': -2.54, 'win_rate': 0.0, 'loss_rate': 1.0, 'stddev_profit_rate': None}`
- post_sell_join: joined=`1` / pending=`0`
- post_sell_mfe_mae_10m: mfe=`-0.475`% / mae=`-4.179`% / close=`-2.754`%

## Missed Probe Counterfactual
- book: `scalp_score65_74_probe_counterfactual` / role: `missed_buy_probe_counterfactual`
- total/score65_74: `5` / `0`
- avg_expected_ev: `3.7463`% / score65_74_avg_expected_ev: `0.0`%
- actual_order_submitted: `False` / broker_order_forbidden: `True`
- authority: `missed_probe_ev_only_not_broker_execution`

## Pattern Lab Automation
- artifact: `-`
- fresh: gemini=`False` claude=`False`
- consensus/orders/family_candidates: `0` / `0` / `0`

## Swing Pattern Lab Automation
- artifact: `-`
- deepseek_lab_available: `None`
- findings/orders: `0` / `0`
- data_quality_warnings: `0`
- ofi_qi_stale_missing_unique_records: `0`
- ofi_qi_stale_missing_reasons: `{}`
- ofi_qi_stale_missing_reason_combinations: `{}`
- ofi_qi_stale_missing_reason_combination_unique_records: `{}`
- ofi_qi_observer_unhealthy_overlap: `{}`
- source_quality_blocked_families: `[]`
- carryover_warnings: `0`
- population_split_available: `False`

## Pipeline Event Verbosity
- artifact: `-`
- state: `missing`
- recommended_workorder_state: `missing`
- high_volume_line_count: `None`
- high_volume_byte_share_pct: `None`
- parity_ok: `None`
- suppress_eligibility: `None`

## Codebase Performance Workorder Source
- artifact: `-`
- authority: `-`
- accepted/deferred/rejected: `0` / `0` / `0`
- runtime_effect: `False`
- strategy_effect: `None`
- data_quality_effect: `None`
- tuning_axis_effect: `None`

## Pattern Lab Audits
- currentness: status=`warning` fail=`9` orders=`9` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-05-18.json`
- propagation: status=`fail` fail=`7` warnings=`2` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_2026-05-18.json`

## Swing Runtime Approval
- request_report: `/home/ubuntu/KORStockScan/data/report/swing_runtime_approval/swing_runtime_approval_2026-05-15.json`
- approval_artifact: `/home/ubuntu/KORStockScan/data/threshold_cycle/approvals/swing_runtime_approvals_2026-05-15.json`
- requested/approved/live_dry_run: `3` / `3` / `2`
- dry_run_forced: `True`
- real_canary_policy: `swing_one_share_real_canary_phase0`
- one_share_real_canary_artifact: `/home/ubuntu/KORStockScan/data/threshold_cycle/approvals/swing_one_share_real_canary_2026-05-15.json`
- selected_one_share_real_canary: `1`
- real_order_allowed_actions: `BUY_INITIAL, SELL_CLOSE`
- sim_only_actions: `AVG_DOWN, PYRAMID, SCALE_IN`
- scale_in_real_canary_policy: `swing_scale_in_real_canary_phase0`
- selected_scale_in_real_canary: `0`
- scale_in_real_execution_quality: `{'one_share_canary_selected': 1, 'scale_in_canary_selected': 0, 'execution_quality_source': 'real_only', 'sim_probe_ev_source': 'separate_from_broker_execution_quality'}`
- blocked: `[]`

## Code Improvement Workorder
- artifact: `-`
- markdown: `-`
- selected_order_count: `0`
- decision_counts: `{}`

## Approval Requests
- none

## Swing Approval Requests
- `swing_model_floor` approval_id=`swing_runtime_approval:2026-05-15:swing_model_floor` score=`0.8361` target_env_keys=`['SWING_FLOOR_BULL', 'SWING_FLOOR_BEAR']`
- `swing_gatekeeper_reject_cooldown` approval_id=`swing_runtime_approval:2026-05-15:swing_gatekeeper_reject_cooldown` score=`0.8361` target_env_keys=`['ML_GATEKEEPER_REJECT_COOLDOWN']`
- `swing_one_share_real_canary_phase0` approval_id=`swing_one_share_real_canary:2026-05-15:phase0` score=`0.8361` target_env_keys=`['SWING_ONE_SHARE_REAL_CANARY_ENABLED', 'SWING_ONE_SHARE_REAL_CANARY_ALLOWED_CODES', 'SWING_ONE_SHARE_REAL_CANARY_MAX_QTY', 'SWING_ONE_SHARE_REAL_CANARY_MAX_NEW_ENTRIES_PER_DAY', 'SWING_ONE_SHARE_REAL_CANARY_MAX_OPEN_POSITIONS', 'SWING_ONE_SHARE_REAL_CANARY_MAX_TOTAL_NOTIONAL_KRW', 'SWING_ONE_SHARE_REAL_CANARY_REQUIRE_APPROVAL_ARTIFACT']`

## Calibration Decisions
- `soft_stop_whipsaw_confirmation`: `adjust_up` sample=`144/10`
- `holding_flow_ofi_smoothing`: `hold_sample` sample=`12/20`
- `protect_trailing_smoothing`: `adjust_down` sample=`84/20`
- `trailing_continuation`: `freeze` sample=`84/20`
- `pre_submit_price_guard`: `hold_sample` sample=`11/20`
- `score65_74_recovery_probe`: `adjust_up` sample=`43/20`
- `liquidity_gate_refined_candidate`: `hold` sample=`17121/20`
- `overbought_gate_refined_candidate`: `hold` sample=`152563/20`
- `bad_entry_refined_canary`: `adjust_up` sample=`1599/10`
- `holding_exit_decision_matrix_advisory`: `hold_no_edge` sample=`0/1`
- `scale_in_price_guard`: `hold` sample=`289/20`
- `position_sizing_cap_release`: `hold_sample` sample=`12/30`
- `position_sizing_dynamic_formula`: `hold_sample` sample=`0/30`

## Warnings
- `pattern_lab_automation_missing`
- `swing_pattern_lab_automation_missing`
- `pipeline_event_verbosity_missing`
- `codebase_performance_workorder_missing`
- `pattern_lab_currentness_audit_warning`
- `pattern_lab_propagation_audit_fail`
- `code_improvement_workorder_missing`
