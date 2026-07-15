# BUY Funnel Sentinel 2026-07-15

## 판정

- primary: `SUBMIT_DROUGHT_CRITICAL`
- secondary: `LATENCY_DROUGHT, UPSTREAM_AI_THRESHOLD`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `false`
- followup_route: `entry_submit_drought_auto_workorder`
- followup_owner: `postclose_threshold_cycle_and_lifecycle_decision_matrix`
- runtime_effect: `auto_workorder_no_intraday_mutation`
- submit_contract_downstream: `code_improvement_workorder, lifecycle_decision_matrix.submit_bucket_attribution, threshold_cycle_ev_report, runtime_approval_summary, postclose_verifier`
- submit_contract_weak_matches: `BROKER_RECEIPT, BUDGET_PASS_COLLAPSE, FILL_QUALITY, LATENCY_PRE_SUBMIT, SIM_REAL_AUTHORITY, TELEGRAM_POST_SUBMIT_ONLY, UPSTREAM_GATE`

## 근거

- as_of: `2026-07-15T15:20:03`
- baseline_date: `2026-07-14`
- ai_confirmed unique: `73`
- budget_pass unique: `46`
- latency_pass unique: `12`
- submitted unique: `8`
- holding_started unique: `8`
- budget/ai unique: `63.0%` (baseline `183.3`)
- submitted/ai unique: `11.0%` (baseline `16.7`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:below_window_buy_value=506, first_ai_wait:-=114, blocked_liquidity:-=90, blocked_vpw:-=69, blocked_strength_momentum:insufficient_history=60`
- swing blockers: `-`
- upstream blockers: `first_ai_wait:-=114, blocked_ai_score:ai_score_50_buy_hold_override=40, blocked_ai_score:score_62.0=23, blocked_ai_score:score_0.0=14, blocked_ai_score:score_58.0=11`
- AI terminal reasons: `ai_terminal:first_ai_wait_big_bite_not_confirmed=114, ai_terminal:entry_policy_no_buy_score_prior=66`
- latency blockers: `latency_block:latency_state_danger=57`
- price guards: `pre_submit_entry_ai_authority_guard_block:entry_ai_score_unavailable=4, entry_ai_price_canary_skip_order:orderbook_micro is bearish with strong negative OFI and quote depth imbalance=1, entry_ai_price_canary_fallback:above_best_ask=1, entry_ai_price_canary_fallback:skip_low_confidence=1, entry_ai_price_canary_fallback:pre_submit_price_guard=1`
- quote refresh: `attempted=36, applied=33, latency_recovered=10, submitted_after_refresh=6`
- quote refresh downstream: `{'order_bundle_submitted': 6, 'price_guard_or_revalidation': 4}`

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

- `5m`: ai=1, budget=2, latency=1, submitted=1, top=`-`, swing=`-`, upstream=`-`, ai_terminal=`-`
- `10m`: ai=1, budget=5, latency=1, submitted=1, top=`latency_block:latency_state_danger=2`, swing=`-`, upstream=`-`, ai_terminal=`-`
- `30m`: ai=2, budget=15, latency=2, submitted=2, top=`latency_block:latency_state_danger=7`, swing=`-`, upstream=`-`, ai_terminal=`-`
