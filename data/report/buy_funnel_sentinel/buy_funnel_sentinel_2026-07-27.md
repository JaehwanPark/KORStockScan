# BUY Funnel Sentinel 2026-07-27

## 판정

- primary: `SUBMIT_DROUGHT_CRITICAL`
- secondary: `PRICE_GUARD_DROUGHT, LATENCY_DROUGHT`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `false`
- followup_route: `entry_submit_drought_auto_workorder`
- followup_owner: `postclose_threshold_cycle_and_lifecycle_decision_matrix`
- runtime_effect: `auto_workorder_no_intraday_mutation`
- submit_contract_downstream: `code_improvement_workorder, lifecycle_decision_matrix.submit_bucket_attribution, threshold_cycle_ev_report, runtime_approval_summary, postclose_verifier`
- submit_contract_weak_matches: `BROKER_RECEIPT, BUDGET_PASS_COLLAPSE, ECONOMIC_PARTICIPATION, FILL_QUALITY, LATENCY_PRE_SUBMIT, PRICE_REVALIDATION, SIM_REAL_AUTHORITY, TELEGRAM_POST_SUBMIT_ONLY`

## 근거

- as_of: `2026-07-27T15:20:03`
- baseline_date: `2026-07-24`
- ai_confirmed unique: `21`
- budget_pass unique: `35`
- latency_pass unique: `6`
- submitted unique: `1`
- holding_started unique: `1`
- budget/ai unique: `166.7%` (baseline `175.0`)
- submitted/ai unique: `4.8%` (baseline `5.0`)
- economic bundles: `observed=1, valid=1, probe_only=1, partial_residual=0, full=0`
- economic submitted/requested: `qty=1/6 (16.7%), notional=198300/1187400 (16.7%)`
- economic participation by venue: `{'KRX': {'bundle_count': 1, 'probe_only_bundle_count': 1, 'partial_residual_bundle_count': 0, 'full_submitted_bundle_count': 0, 'requested_qty': 6, 'submitted_qty': 1, 'requested_notional_krw': 1187400, 'submitted_notional_krw': 198300, 'submitted_qty_to_requested_qty_pct': 16.7, 'submitted_notional_to_requested_notional_pct': 16.7}}`
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `latency_block:latency_state_danger=34, entry_ai_price_canary_fallback:parse_or_ai_fail=26, blocked_strength_momentum:below_window_buy_value=12, blocked_ai_score:score_0.0=4, first_ai_wait:-=3`
- swing blockers: `-`
- upstream blockers: `blocked_ai_score:score_0.0=4, first_ai_wait:-=3, blocked_ai_score:ai_score_50_buy_hold_override=3`
- AI terminal reasons: `ai_terminal:entry_policy_no_buy_score_prior=4, ai_terminal:first_ai_wait_big_bite_not_confirmed=3`
- latency blockers: `latency_block:latency_state_danger=34, latency_block:tp1_direct_recheck_expired=1`
- price guards: `entry_ai_price_canary_fallback:parse_or_ai_fail=26, pre_submit_entry_ai_authority_guard_block:entry_ai_result_stale_or_untrusted=3, pre_submit_entry_ai_authority_guard_block:fresh_ai_drop_real_buy_veto=2`
- quote refresh: `attempted=27, applied=19, latency_recovered=3, submitted_after_refresh=1`
- quote refresh downstream: `{'order_bundle_submitted': 1, 'price_guard_or_revalidation': 2}`

## 금지된 자동변경

- `score_threshold_relaxation`
- `spread_cap_relaxation`
- `fallback_reenable`
- `live_threshold_runtime_mutation`
- `bot_restart`

## 권고 액션

- Auto-route ai_confirmed -> budget_pass -> latency_pass -> order_bundle_submitted drought into postclose workorder/LDM handoff.
- Split root cause into upstream gate, budget pass, latency/pre-submit guard, and broker receipt buckets before tuning thresholds.
- Do not require operator approval for submitted drought surfacing or downstream workorder generation.

## Window Summary

- `5m`: ai=0, budget=0, latency=0, submitted=0, top=`-`, swing=`-`, upstream=`-`, ai_terminal=`-`
- `10m`: ai=0, budget=0, latency=0, submitted=0, top=`-`, swing=`-`, upstream=`-`, ai_terminal=`-`
- `30m`: ai=1, budget=1, latency=0, submitted=0, top=`latency_block:latency_state_danger=1`, swing=`-`, upstream=`-`, ai_terminal=`-`
