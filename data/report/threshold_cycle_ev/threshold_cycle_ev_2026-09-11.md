# Threshold Cycle Daily EV Report - 2026-09-11

## Summary
- status: `warning`
- warning_count: `15`
- warning_contract active/disabled/raw: `15` / `4` / `19`
- source_quality: status=`warning` allowed=`True`
- samples real/sim: `0` / `10`
- live_auto_ready_count: `0`
- primary_verdict: `real_primary_evidence_present`

## Runtime Apply
- status: `auto_bounded_live_ready`
- runtime_change: `True`
- selected_families: `score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, latency_spread_relief_real_operator_override, quote_consistency_normalization, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, post_probe_winner_recovery, entry_opportunity_recheck_runtime, holding_decision_context_v1, early_accel_recheck_runtime, real_pyramid_scale_in_quality_guard_runtime, sell_side_open_time_block_runtime, pre_submit_liquidity_relief_runtime, weak_context_late_entry_guard_runtime, rising_missed_normal_buy_bridge, persistent_operator_overrides_2026_06_26`

## Daily EV
- completed: `0` / open: `11`
- win/loss: `0` / `0` (`0.0`%)
- avg_profit_rate: `0.0`%
- realized_pnl_krw: `None`
- realized_pnl_status: `unresolved_trade_review_count_mismatch`
- full_fill_completed_avg_profit_rate: `0.0`%

## Entry Funnel
- budget_pass_to_submitted: `12` / `471` (`2.55`%)
- latency pass/block: `83` / `262`
- latency submit routing: `buy_funnel_diagnostic_only`
- latency recommendation: `retired` (`independent latency threshold recommendation retired; no PREOPEN calibration candidate`)
- latency diagnostic owner: `buy_funnel_sentinel+performance_tuning+daily_threshold_cycle_report`
- full/partial fill: `1` / `10`
- entry_split_order_plan: status=`pass` candidates=`1` policy=`entry_split_order_plan:2026-09-11:a3dc5947d9`
- scale_in_split_order_plan: status=`pass` candidates=`1` policy=`scale_in_split_order_plan:2026-09-11:dfef4ae66496`

## Holding Exit
- holding_reviews: `815`
- exit_signals: `20`
- holding_review_ms_p95: `9231.0`

## Scalp Simulator
- authority: `equal_weight` / fill_policy: `signal_inclusive_best_ask_v1`
- armed/filled/sold: `11` / `11` / `10`
- expired/unpriced/duplicate: `0` / `0` / `8`
- entry_ai_price applied/skip: `10` / `5`
- submit_revalidation warning/block: `0` / `0`
- scale_in filled/unfilled: `0` / `0`
- overnight decision/sell/hold/carry_restored: `0` / `0` / `0` / `0`
- completed_profit_summary: `{'sample': 10, 'win_count': 3, 'loss_count': 7, 'avg_profit_rate': -0.905, 'median_profit_rate': -1.4, 'downside_p10_profit_rate': -5.19, 'upside_p90_profit_rate': 1.62, 'win_rate': 0.3, 'loss_rate': 0.7, 'stddev_profit_rate': 2.3663}`
- post_sell_join: joined=`10` / pending=`0`
- post_sell_mfe_mae_10m: mfe=`0.9393`% / mae=`-9.3081`% / close=`-0.3877`%

## Missed Probe Counterfactual
- book: `scalp_score65_74_probe_counterfactual` / role: `missed_buy_probe_counterfactual`
- total/raw_score60_74/economic_eligible_score60_74: `24` / `0` / `0`
- avg_gross_counterfactual_ev: `-0.1292`% / avg_cost_adjusted_counterfactual_ev: `None`%
- score60_74_cost_adjusted_ev: `None`% / cost_contract_complete: `False` / source_quality_or_cost_excluded: `0`
- actual_order_submitted: `False` / broker_order_forbidden: `True`
- authority: `missed_probe_ev_only_not_broker_execution` / gross_runtime_authority: `forbidden`

## Scalp Entry ADM
- artifact: `-`
- status: `retired` / authority: `archive_only`
- total/joined/floor: `None` / `None` / `None`
- prompt_applied_count: `None`
- runtime_bias_applied_count: `None`
- runtime_effect_counts: `{}`
- forced_action_counts: `{}`
- missing_actions: `[]`
- zero_sample_actions: `[]`
- outcome_join_diagnostic: `{}`
- top_actions: `[]`

## Lifecycle Decision Matrix
- artifact: `-`
- status: `retired` / version: `-`
- total/joined: `None` / `None`
- policy_pass/promote_ready: `None` / `None`
- lifecycle_flow buckets/complete/runtime/workorders: `None` / `None` / `None` / `None`
- holding/exit buckets: `None` / `None`
- holding/exit workorders: `None` / `None`
- lifecycle identity missing/join_rate: `None` / `None`
- lifecycle complete_flow_rate: `None`
- incomplete_flow_reason_counts: `{}`
- fixed_threshold_roles: `{}`
- policy_entries: `[]`

## Lifecycle Bucket Discovery
- artifact: `-`
- status: `retired` / human_intervention_required: `None`
- candidates/surfaced: `None` / `None`
- sim_auto/live_auto/new_bucket: `None` / `None` / `None`
- role/window: `None` / `None`
- parent_count/granularity/conflict: `None` / `None` / `None`
- positive_parent/sample_ready/conflict: `0` / `0` / `0`
- active_positive_seed/nonpositive_seed: `0` / `0`
- positive_sim_auto/nonpositive_sim_auto: `0` / `0`
- state_counts: `{}`
- top_surfaced: `[]`
- top_sample_ready_positive_parent_buckets: `[]`
- top_active_positive_seeds: `[]`
- top_positive_sim_auto_approved: `[]`
- top_nonpositive_sim_auto_approved: `[]`

## Lifecycle Bucket Windows
- promotion_window: `None`
- confirmation_windows: `None`
- windows: `{}`

## Lifecycle AI Context
- artifact: `-`
- context_version: `-` / authority: `archive_only`
- prompt_stage_count: `None` / runtime_effect: `False`
- stage_contexts: `[]`

## Lifecycle AI Context Attribution
- artifact: `-`
- eligible/applied/skipped: `None` / `None` / `None`
- replay_budget: `None`
- implementation_status: `-`
- stage_attribution: `{}`

## Institutional Flow Context
- artifact: `-`
- status: `retired` / authority: `archive_only`
- rows ok/partial/missing/token_error: `None` / `None` / `None` / `None`
- join_rate_pct: `None`
- source_mix: `{}`
- top_net_buy: `[]`

## Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-09-11.json`
- fresh: gemini=`False` claude=`False`
- consensus/orders/family_candidates: `0` / `0` / `0`

## Swing Pattern Lab Automation
- artifact: `-`
- deepseek_lab_available: `None`
- findings/orders: `0` / `0`
- data_quality_warnings: `0`
- top_level_data_quality_warnings: `None`
- resolved_data_quality_warnings: `None`
- ofi_qi_stale_missing_unique_records: `0`
- ofi_qi_stale_missing_reasons: `{}`
- ofi_qi_stale_missing_reason_combinations: `{}`
- ofi_qi_stale_missing_reason_combination_unique_records: `{}`
- ofi_qi_observer_unhealthy_overlap: `{}`
- source_quality_blocked_families: `[]`
- carryover_warnings: `0`
- population_split_available: `False`

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
- artifact: `/home/ubuntu/KORStockScan/data/report/pipeline_event_verbosity/pipeline_event_verbosity_2026-09-11.json`
- state: `v2_shadow_parity_fail`
- recommended_workorder_state: `block_suppress_and_fix_shadow`
- high_volume_line_count: `155243`
- high_volume_byte_share_pct: `21.65`
- parity_ok: `False`
- suppress_eligibility: `False`

## Codebase Performance Workorder Source
- artifact: `-`
- authority: `-`
- accepted/deferred/rejected: `0` / `0` / `0`
- runtime_effect: `False`
- strategy_effect: `None`
- data_quality_effect: `None`
- tuning_axis_effect: `None`

## Pattern Lab Audits
- currentness: status=`warning` fail=`7` orders=`7` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-09-11.json`
- ai_review: status=`warning` orders=`12` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_ai_review/pattern_lab_ai_review_2026-09-11.json`
- time_window_regime_counterfactual: status=`missing` artifact=`-`
- producer_gap_discovery: status=`missing` orders=`0` artifact=`-`
- stage_hook_workorder_discovery: status=`missing` orders=`0` artifact=`-`
- propagation: status=`warning` fail=`0` warnings=`2` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_2026-09-11.json`

## Swing Runtime Approval
- request_report: `-`
- approval_artifact: `-`
- requested/approved/live_dry_run: `0` / `0` / `0`
- dry_run_forced: `False`
- legacy_phase0_real_canary_ignored: `False`
- blocked: `[]`

## Code Improvement Workorder
- artifact: `/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-09-11.json`
- markdown: `/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-09-11.md`
- selected_order_count: `38`
- decision_counts: `{'implement_now': 27, 'attach_existing_family': 26, 'defer_evidence': 7}`

## Approval Requests
- none

## Swing Approval Requests
- none

## Calibration Decisions
## Code Improvement Top Orders
- `order_entry_broker_receipt_contract_gap_review` decision=`implement_now` subsystem=`runtime_instrumentation`
- `order_entry_fill_quality_contract_gap_review` decision=`implement_now` subsystem=`runtime_instrumentation`
- `order_entry_post_submit_contract_gap_review` decision=`implement_now` subsystem=`runtime_instrumentation`

- `soft_stop_whipsaw_confirmation`: `hold_sample` sample=`1166/10`
- `holding_flow_ofi_smoothing`: `hold_sample` sample=`3/20`
- `protect_trailing_smoothing`: `hold_sample` sample=`15/20`
- `trailing_continuation`: `freeze` sample=`65/20`
- `market_regime_continuous_thresholds`: `hold_sample` sample=`8/10`
- `pre_submit_price_guard`: `hold` sample=`0/1`
- `dynamic_entry_price_resolver`: `hold_sample` sample=`16248/20`
- `entry_split_order_plan`: `hold` sample=`180/20`
- `scale_in_split_order_plan`: `hold_sample` sample=`0/3`
- `entry_price_execution_quality`: `hold` sample=`32/5`
- `score65_74_recovery_probe`: `source_quality_blocked` sample=`0/20`
- `strength_momentum_soft_gate_p1`: `hold` sample=`1105/20`
- `overbought_pullback_guard_p1`: `hold` sample=`1135/20`
- `liquidity_pre_submit_guard_p1`: `hold` sample=`660/20`
- `bad_entry_refined_canary`: `hold_sample` sample=`9/10`
- `scale_in_price_guard`: `hold_sample` sample=`2/20`
- `position_sizing_dynamic_formula`: `hold_sample` sample=`0/30`
- `scalping_avg_down_recovery_quality_gate`: `hold_runtime_scope` sample=`0/10`
- `scalping_pyramid_quality_gate`: `source_quality_blocked` sample=`87/20`

## Warnings
- `pattern_lab_claude_stale`
- `microstructure_reaction_context:diagnostic_contract:evaluation_venue_missing_or_conflicting`
- `microstructure_reaction_context:diagnostic_contract:evaluation_anchor_contract_missing`
- `microstructure_reaction_context:clean_baseline:daily_rollup_missing_or_stale_dates_excluded`
- `microstructure_reaction_context:clean_baseline:exact_attempt_time_outcome_coverage_incomplete`
- `codebase_performance_workorder_missing`
- `pattern_lab_currentness_audit_warning`
- `pattern_lab_ai_review_warning`
- `pattern_lab_ai_review_ai_review_followup_required`
- `time_window_regime_counterfactual_missing`
- `producer_gap_discovery_missing`
- `stage_hook_workorder_discovery_missing`
- `stage_hook_runtime_scaffold_missing`
- `pattern_lab_propagation_audit_warning`
- `trade_review_calibration_count_mismatch`
