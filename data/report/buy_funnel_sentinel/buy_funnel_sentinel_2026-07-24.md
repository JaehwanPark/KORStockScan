# BUY Funnel Sentinel 2026-07-24

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

- as_of: `2026-07-24T15:20:01`
- baseline_date: `2026-07-23`
- ai_confirmed unique: `20`
- budget_pass unique: `35`
- latency_pass unique: `8`
- submitted unique: `1`
- holding_started unique: `2`
- budget/ai unique: `175.0%` (baseline `169.7`)
- submitted/ai unique: `5.0%` (baseline `24.2`)
- economic bundles: `observed=1, valid=1, probe_only=1, partial_residual=0, full=0`
- economic submitted/requested: `qty=1/53 (1.9%), notional=19100/1009650 (1.9%)`
- economic participation by venue: `{'KRX': {'bundle_count': 1, 'probe_only_bundle_count': 1, 'partial_residual_bundle_count': 0, 'full_submitted_bundle_count': 0, 'requested_qty': 53, 'submitted_qty': 1, 'requested_notional_krw': 1009650, 'submitted_notional_krw': 19100, 'submitted_qty_to_requested_qty_pct': 1.9, 'submitted_notional_to_requested_notional_pct': 1.9}}`
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `latency_block:latency_state_danger=44, pre_submit_entry_ai_authority_guard_block:entry_ai_result_stale_or_untrusted=8, first_ai_wait:-=2, latency_block:tp1_direct_recheck_expired=2, pre_submit_entry_ai_authority_guard_block:fresh_ai_drop_real_buy_veto=2`
- swing blockers: `-`
- upstream blockers: `first_ai_wait:-=2, blocked_ai_score:score_0.0=1`
- AI terminal reasons: `ai_terminal:first_ai_wait_big_bite_not_confirmed=2, ai_terminal:entry_policy_no_buy_score_prior=1`
- latency blockers: `latency_block:latency_state_danger=44, latency_block:tp1_direct_recheck_expired=2`
- price guards: `pre_submit_entry_ai_authority_guard_block:entry_ai_result_stale_or_untrusted=8, pre_submit_entry_ai_authority_guard_block:fresh_ai_drop_real_buy_veto=2`
- quote refresh: `attempted=26, applied=25, latency_recovered=8, submitted_after_refresh=0`
- quote refresh downstream: `{'no_downstream_event': 1, 'price_guard_or_revalidation': 7}`

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
- `10m`: ai=2, budget=3, latency=1, submitted=0, top=`pre_submit_entry_ai_authority_guard_block:fresh_ai_drop_real_buy_veto=1, latency_block:latency_state_danger=1`, swing=`-`, upstream=`-`, ai_terminal=`-`
- `30m`: ai=8, budget=13, latency=1, submitted=0, top=`latency_block:latency_state_danger=8, blocked_vpw:-=1, blocked_liquidity:-=1`, swing=`-`, upstream=`first_ai_wait:-=1`, ai_terminal=`ai_terminal:first_ai_wait_big_bite_not_confirmed=1`
