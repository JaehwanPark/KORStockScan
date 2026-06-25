# Entry Hurdle Backtest 2026-06-25

- runtime_effect: `False`
- source_dates: `2026-06-04, 2026-06-05, 2026-06-08, 2026-06-09, 2026-06-10, 2026-06-11, 2026-06-12, 2026-06-15, 2026-06-16, 2026-06-17, 2026-06-18, 2026-06-19, 2026-06-22, 2026-06-23, 2026-06-24, 2026-06-25`
- submitted/ai unique: `5.95%`
- submitted/budget unique: `12.9%`
- missing_artifacts: `0`

## Recommended Next Actions
- `trace_latency_refresh_recovered_downstream_blocker`: priority=1, decision=instrumentation_or_guard_overlap_candidate, reason=quote refresh recovered latency pass but did not always reach broker submit
- `review_pre_submit_liquidity_relief_scope`: priority=2, decision=bounded_report_only_policy_candidate, reason=liquidity blocker has missed-winner skew in existing counterfactual data
- `review_ai_wait_score_recheck_scope`: priority=3, decision=recheck_scope_candidate_not_threshold_relaxation, reason=AI wait/score blocker has missed-winner skew but broad BUY threshold relaxation is forbidden
- `audit_late_entry_price_drift_guard_context`: priority=4, decision=price_context_audit_candidate, reason=late price drift guard blocks possible winners; changing entry price is forbidden

## Blocker Tradeoff
- `blocked_strength_momentum`: evaluated=1956, missed=63.29%, avoided=25.05%, decision=overblocking_candidate
- `latency_block`: evaluated=1189, missed=71.99%, avoided=20.61%, decision=overblocking_candidate
- `scalp_sim_pre_submit_liquidity_guard_would_block`: evaluated=402, missed=77.11%, avoided=19.15%, decision=overblocking_candidate
- `blocked_ai_score`: evaluated=1422, missed=64.28%, avoided=21.87%, decision=overblocking_candidate
- `blocked_overbought`: evaluated=304, missed=81.91%, avoided=14.47%, decision=overblocking_candidate
- `blocked_zero_qty`: evaluated=3, missed=66.67%, avoided=33.33%, decision=overblocking_candidate
- `blocked_liquidity`: evaluated=255, missed=74.12%, avoided=24.31%, decision=overblocking_candidate
- `pre_submit_liquidity_guard_block`: evaluated=49, missed=85.71%, avoided=10.2%, decision=overblocking_candidate
- `real_weak_pullback_entry_block`: evaluated=115, missed=65.22%, avoided=21.74%, decision=overblocking_candidate
- `scalp_sim_pre_submit_overbought_guard_would_block`: evaluated=2, missed=100.0%, avoided=0.0%, decision=hold_sample
- `first_ai_wait`: evaluated=91, missed=56.04%, avoided=28.57%, decision=overblocking_candidate
- `order_bundle_failed`: evaluated=7, missed=42.86%, avoided=14.29%, decision=overblocking_candidate
- `pre_submit_late_entry_price_drift_guard_block`: evaluated=15, missed=86.67%, avoided=0.0%, decision=overblocking_candidate
- `scalp_entry_action_decision_snapshot`: evaluated=134, missed=67.16%, avoided=15.67%, decision=overblocking_candidate
- `scalping_scanner_real_source_guard_block`: evaluated=333, missed=60.06%, avoided=28.83%, decision=overblocking_candidate
- `blocked_gap_from_scan`: evaluated=16, missed=87.5%, avoided=12.5%, decision=overblocking_candidate
- `early_accel_strong_bundle_recheck_failed`: evaluated=491, missed=64.97%, avoided=29.53%, decision=overblocking_candidate
- `buy_like_no_submit_terminal`: evaluated=1, missed=100.0%, avoided=0.0%, decision=hold_sample
- `entry_armed_expired`: evaluated=1, missed=100.0%, avoided=0.0%, decision=hold_sample
- `pre_submit_weak_context_late_entry_guard_block`: evaluated=1, missed=100.0%, avoided=0.0%, decision=hold_sample
