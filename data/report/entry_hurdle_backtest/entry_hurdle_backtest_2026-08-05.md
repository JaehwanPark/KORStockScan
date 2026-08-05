# Entry Hurdle Backtest 2026-08-05

- runtime_effect: `False`
- source_dates: `2026-06-05, 2026-06-08, 2026-06-09, 2026-06-10, 2026-06-11, 2026-06-12, 2026-06-15, 2026-06-16, 2026-06-17, 2026-06-18, 2026-06-19, 2026-06-22, 2026-06-23, 2026-06-24, 2026-06-25, 2026-06-26, 2026-06-29, 2026-06-30, 2026-07-01, 2026-07-02, 2026-07-03, 2026-07-06, 2026-07-07, 2026-07-08, 2026-07-09, 2026-07-10, 2026-07-13, 2026-07-14, 2026-07-15, 2026-07-16, 2026-07-20, 2026-07-21, 2026-07-22, 2026-07-23, 2026-07-24, 2026-07-27, 2026-07-28, 2026-07-29, 2026-07-30, 2026-07-31, 2026-08-03, 2026-08-04, 2026-08-05`
- submitted/ai unique: `9.74%`
- submitted/budget unique: `17.07%`
- missing_artifacts: `20`

## Implemented Policy Backtest
- eligible attempts: `10`
- unique symbols upper bound: `9`
- conservative estimated submit success: `0`
- upper bound submit-path reentry: `10`
- liquidity relief eligible/success: `0`/`0`
- AI 60-74 recheck eligible/success: `10`/`0`

## Recommended Next Actions
- `trace_latency_refresh_recovered_downstream_blocker`: priority=1, decision=instrumentation_or_guard_overlap_candidate, reason=quote refresh recovered latency pass but did not always reach broker submit

## Overbought Gate Counterfactual
- decision: `hold_sample_or_balanced`
- evaluated/missed/avoided: `327`/`89`/`59`
- missed/avoided rate: `27.22%`/`18.04%`
- executable BBO / first-hit / joint rows: `0`/`0`/`0`
- runtime_effect: `False`
- code_improvement_orders: `0`

## Blocker Tradeoff
- `blocked_ai_score`: evaluated=1452, missed=22.18%, avoided=22.73%, decision=balanced_or_unclear
- `blocked_gap_from_scan`: evaluated=14, missed=14.29%, avoided=7.14%, decision=balanced_or_unclear
- `blocked_liquidity`: evaluated=100, missed=34.0%, avoided=34.0%, decision=balanced_or_unclear
- `blocked_overbought`: evaluated=327, missed=27.22%, avoided=18.04%, decision=balanced_or_unclear
- `blocked_strength_momentum`: evaluated=2117, missed=20.64%, avoided=20.78%, decision=balanced_or_unclear
- `early_accel_strong_bundle_recheck_failed`: evaluated=377, missed=26.79%, avoided=25.2%, decision=balanced_or_unclear
- `first_ai_wait`: evaluated=135, missed=27.41%, avoided=19.26%, decision=balanced_or_unclear
- `latency_block`: evaluated=1337, missed=45.25%, avoided=32.83%, decision=balanced_or_unclear
- `pre_submit_weak_context_late_entry_guard_block`: evaluated=3, missed=0.0%, avoided=33.33%, decision=balanced_or_unclear
- `real_weak_pullback_entry_block`: evaluated=29, missed=13.79%, avoided=0.0%, decision=balanced_or_unclear
- `scalp_entry_action_decision_snapshot`: evaluated=652, missed=38.34%, avoided=33.13%, decision=balanced_or_unclear
- `scalp_sim_pre_submit_liquidity_guard_would_block`: evaluated=171, missed=17.54%, avoided=16.37%, decision=balanced_or_unclear
- `scalping_scanner_real_source_guard_block`: evaluated=474, missed=40.08%, avoided=39.24%, decision=balanced_or_unclear
- `blocked_zero_qty`: evaluated=71, missed=53.52%, avoided=32.39%, decision=overblocking_candidate
- `pre_submit_liquidity_guard_block`: evaluated=2, missed=0.0%, avoided=0.0%, decision=hold_sample
- `pre_submit_entry_ai_authority_guard_block`: evaluated=135, missed=52.59%, avoided=39.26%, decision=balanced_or_unclear
- `pre_submit_price_guard_block`: evaluated=4, missed=75.0%, avoided=25.0%, decision=overblocking_candidate
- `real_weak_ai_micro_entry_block`: evaluated=268, missed=49.63%, avoided=36.19%, decision=balanced_or_unclear
- `entry_price_canary_submit_block`: evaluated=12, missed=66.67%, avoided=25.0%, decision=overblocking_candidate
- `rising_missed_tick_speed_entry_block`: evaluated=180, missed=50.0%, avoided=41.11%, decision=balanced_or_unclear
- `entry_submit_revalidation_block`: evaluated=10, missed=50.0%, avoided=50.0%, decision=balanced_or_unclear
- `krx_direct_canary_live_ai_wait_submit_block`: evaluated=8, missed=37.5%, avoided=62.5%, decision=protective_hurdle_candidate
- `entry_ai_price_candle_source_block`: evaluated=8, missed=75.0%, avoided=25.0%, decision=overblocking_candidate
- `entry_ai_price_feature_packet_source_block`: evaluated=8, missed=0.0%, avoided=75.0%, decision=protective_hurdle_candidate
- `entry_ai_price_input_preflight_block`: evaluated=153, missed=37.91%, avoided=40.52%, decision=balanced_or_unclear
- `pre_submit_micro_unavailable_block`: evaluated=3, missed=33.33%, avoided=66.67%, decision=protective_hurdle_candidate
