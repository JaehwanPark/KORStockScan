# BUY Funnel Sentinel 2026-07-28

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

- as_of: `2026-07-28T15:20:03`
- baseline_date: `2026-07-27`
- ai_confirmed unique: `1`
- budget_pass unique: `11`
- latency_pass unique: `1`
- submitted unique: `1`
- holding_started unique: `1`
- budget/ai unique: `1100.0%` (baseline `166.7`)
- submitted/ai unique: `100.0%` (baseline `4.8`)
- economic bundles: `observed=1, valid=1, probe_only=1, partial_residual=0, full=0`
- economic submitted/requested: `qty=1/20 (5.0%), notional=15390/306800 (5.0%)`
- economic participation by venue: `{'KRX': {'bundle_count': 1, 'probe_only_bundle_count': 1, 'partial_residual_bundle_count': 0, 'full_submitted_bundle_count': 0, 'requested_qty': 20, 'submitted_qty': 1, 'requested_notional_krw': 306800, 'submitted_notional_krw': 15390, 'submitted_qty_to_requested_qty_pct': 5.0, 'submitted_notional_to_requested_notional_pct': 5.0}}`
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `latency_block:latency_state_danger=19, blocked_zero_qty:-=16, entry_ai_price_canary_fallback:parse_or_ai_fail=5`
- swing blockers: `-`
- upstream blockers: `-`
- AI terminal reasons: `-`
- latency blockers: `latency_block:latency_state_danger=19`
- price guards: `entry_ai_price_canary_fallback:parse_or_ai_fail=5`
- quote refresh: `attempted=9, applied=9, latency_recovered=1, submitted_after_refresh=1`
- quote refresh downstream: `{'order_bundle_submitted': 1}`

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

- `5m`: ai=0, budget=0, latency=0, submitted=0, top=`blocked_zero_qty:-=1`, swing=`-`, upstream=`-`, ai_terminal=`-`
- `10m`: ai=0, budget=0, latency=0, submitted=0, top=`blocked_zero_qty:-=4`, swing=`-`, upstream=`-`, ai_terminal=`-`
- `30m`: ai=0, budget=0, latency=0, submitted=0, top=`blocked_zero_qty:-=9`, swing=`-`, upstream=`-`, ai_terminal=`-`
