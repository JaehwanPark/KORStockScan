# Entry Hurdle Backtest 2026-07-02

- runtime_effect: `False`
- source_dates: `2026-06-04, 2026-06-05, 2026-06-08, 2026-06-09, 2026-06-10, 2026-06-11, 2026-06-12, 2026-06-15, 2026-06-16, 2026-06-17, 2026-06-18, 2026-06-19, 2026-06-22, 2026-06-23, 2026-06-24, 2026-06-25, 2026-06-26, 2026-06-29, 2026-06-30, 2026-07-01, 2026-07-02`
- submitted/ai unique: `8.19%`
- submitted/budget unique: `18.02%`
- missing_artifacts: `0`

## Implemented Policy Backtest
- eligible attempts: `772`
- unique symbols upper bound: `244`
- conservative estimated submit success: `90`
- upper bound submit-path reentry: `772`
- liquidity relief eligible/success: `4`/`1`
- AI 60-74 recheck eligible/success: `768`/`89`

## Recommended Next Actions
- `trace_latency_refresh_recovered_downstream_blocker`: priority=1, decision=instrumentation_or_guard_overlap_candidate, reason=quote refresh recovered latency pass but did not always reach broker submit
- `review_pre_submit_liquidity_relief_scope`: priority=2, decision=bounded_report_only_policy_candidate, reason=liquidity blocker has missed-winner skew in existing counterfactual data
- `review_overbought_gate_miss_ev_recovery_scope`: priority=3, decision=source_only_counterfactual_candidate, reason=overbought blocker has missed-winner skew in existing counterfactual data
- `review_ai_wait_score_recheck_scope`: priority=4, decision=recheck_scope_candidate_not_threshold_relaxation, reason=AI wait/score blocker has missed-winner skew but broad BUY threshold relaxation is forbidden
- `audit_late_entry_price_drift_guard_context`: priority=5, decision=price_context_audit_candidate, reason=late price drift guard blocks possible winners; changing entry price is forbidden

## Overbought Gate Counterfactual
- decision: `source_only_recovery_design_candidate`
- evaluated/missed/avoided: `582`/`459`/`98`
- missed/avoided rate: `78.87%`/`16.84%`
- runtime_effect: `False`
- code_improvement_orders: `1`

## Blocker Tradeoff
- `blocked_strength_momentum`: evaluated=2870, missed=62.82%, avoided=26.03%, decision=overblocking_candidate
- `latency_block`: evaluated=2304, missed=58.2%, avoided=32.68%, decision=overblocking_candidate
- `scalp_sim_pre_submit_liquidity_guard_would_block`: evaluated=480, missed=77.71%, avoided=18.54%, decision=overblocking_candidate
- `blocked_ai_score`: evaluated=2287, missed=64.1%, avoided=23.7%, decision=overblocking_candidate
- `blocked_overbought`: evaluated=580, missed=78.79%, avoided=16.9%, decision=overblocking_candidate
- `blocked_zero_qty`: evaluated=7, missed=85.71%, avoided=14.29%, decision=overblocking_candidate
- `blocked_liquidity`: evaluated=437, missed=72.54%, avoided=25.17%, decision=overblocking_candidate
- `pre_submit_liquidity_guard_block`: evaluated=57, missed=84.21%, avoided=8.77%, decision=overblocking_candidate
- `real_weak_pullback_entry_block`: evaluated=166, missed=64.46%, avoided=24.7%, decision=overblocking_candidate
- `scalp_sim_pre_submit_overbought_guard_would_block`: evaluated=2, missed=100.0%, avoided=0.0%, decision=hold_sample
- `first_ai_wait`: evaluated=171, missed=57.31%, avoided=25.15%, decision=overblocking_candidate
- `order_bundle_failed`: evaluated=9, missed=44.44%, avoided=22.22%, decision=overblocking_candidate
- `pre_submit_late_entry_price_drift_guard_block`: evaluated=15, missed=86.67%, avoided=0.0%, decision=overblocking_candidate
- `scalp_entry_action_decision_snapshot`: evaluated=236, missed=62.71%, avoided=21.61%, decision=overblocking_candidate
- `scalping_scanner_real_source_guard_block`: evaluated=492, missed=59.96%, avoided=28.66%, decision=overblocking_candidate
- `blocked_gap_from_scan`: evaluated=37, missed=75.68%, avoided=13.51%, decision=overblocking_candidate
- `early_accel_strong_bundle_recheck_failed`: evaluated=788, missed=62.44%, avoided=30.33%, decision=overblocking_candidate
- `buy_like_no_submit_terminal`: evaluated=1, missed=100.0%, avoided=0.0%, decision=hold_sample
- `entry_armed_expired`: evaluated=1, missed=100.0%, avoided=0.0%, decision=hold_sample
- `pre_submit_weak_context_late_entry_guard_block`: evaluated=23, missed=56.52%, avoided=34.78%, decision=overblocking_candidate
- `entry_submit_revalidation_block`: evaluated=17, missed=82.35%, avoided=11.76%, decision=overblocking_candidate
