# BUY Funnel Sentinel 2026-07-10

## 판정

- primary: `SUBMIT_DROUGHT_CRITICAL`
- secondary: `PRICE_GUARD_DROUGHT, LATENCY_DROUGHT, UPSTREAM_AI_THRESHOLD`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `false`
- followup_route: `entry_submit_drought_auto_workorder`
- followup_owner: `postclose_threshold_cycle_and_lifecycle_decision_matrix`
- runtime_effect: `auto_workorder_no_intraday_mutation`
- submit_contract_downstream: `code_improvement_workorder, lifecycle_decision_matrix.submit_bucket_attribution, threshold_cycle_ev_report, runtime_approval_summary, postclose_verifier`
- submit_contract_weak_matches: `BROKER_RECEIPT, BUDGET_PASS_COLLAPSE, FILL_QUALITY, LATENCY_PRE_SUBMIT, PRICE_REVALIDATION, SIM_REAL_AUTHORITY, TELEGRAM_POST_SUBMIT_ONLY, UPSTREAM_GATE`

## 근거

- as_of: `2026-07-10T14:55:03`
- baseline_date: `2026-07-09`
- ai_confirmed unique: `122`
- budget_pass unique: `62`
- latency_pass unique: `16`
- submitted unique: `11`
- holding_started unique: `10`
- budget/ai unique: `50.8%` (baseline `67.9`)
- submitted/ai unique: `9.0%` (baseline `42.9`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:below_window_buy_value=421, latency_block:latency_state_danger=130, first_ai_wait:-=119, blocked_liquidity:-=53, blocked_ai_score:score_62.0=38`
- swing blockers: `-`
- upstream blockers: `first_ai_wait:-=119, blocked_ai_score:score_62.0=38, blocked_ai_score:ai_score_50_buy_hold_override=22, blocked_ai_score:score_0.0=7, blocked_ai_score:score_58.0=7`
- AI terminal reasons: `ai_terminal:first_ai_wait_big_bite_not_confirmed=119, ai_terminal:entry_policy_no_buy_score_prior=64`
- latency blockers: `latency_block:latency_state_danger=130`
- price guards: `pre_submit_entry_ai_authority_guard_block:entry_ai_score_unavailable=8, entry_ai_price_canary_fallback:above_best_ask=2, entry_ai_price_canary_skip_order:orderbook_micro is bearish with negative OFI and weak execution context=1, entry_ai_price_canary_skip_order:orderbook_micro is bearish with negative OFI and high top_depth_ratio, indicating downward pressure=1, entry_ai_price_canary_skip_order:orderbook_micro is bearish with negative OFI and low execution potential=1`
- quote refresh: `attempted=53, applied=49, latency_recovered=10, submitted_after_refresh=5`
- quote refresh downstream: `{'order_bundle_submitted': 5, 'price_guard_or_revalidation': 5}`

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

- `5m`: ai=3, budget=2, latency=0, submitted=0, top=`latency_block:latency_state_danger=3`, swing=`-`, upstream=`-`, ai_terminal=`-`
- `10m`: ai=5, budget=6, latency=0, submitted=0, top=`latency_block:latency_state_danger=8`, swing=`-`, upstream=`-`, ai_terminal=`-`
- `30m`: ai=12, budget=12, latency=0, submitted=0, top=`latency_block:latency_state_danger=11`, swing=`-`, upstream=`-`, ai_terminal=`-`
