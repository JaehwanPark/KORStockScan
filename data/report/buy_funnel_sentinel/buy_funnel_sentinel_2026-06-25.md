# BUY Funnel Sentinel 2026-06-25

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

- as_of: `2026-06-25T22:30:32`
- baseline_date: `2026-06-24`
- ai_confirmed unique: `66`
- budget_pass unique: `20`
- latency_pass unique: `11`
- submitted unique: `5`
- holding_started unique: `2`
- budget/ai unique: `30.3%` (baseline `27.8`)
- submitted/ai unique: `7.6%` (baseline `8.2`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:insufficient_history=452, blocked_strength_momentum:below_strength_base=429, blocked_liquidity:-=342, first_ai_wait:-=291, blocked_ai_score:score_62.0=270`
- swing blockers: `-`
- upstream blockers: `first_ai_wait:-=291, blocked_ai_score:score_62.0=270, blocked_ai_score:ai_score_50_buy_hold_override=197, blocked_ai_score:score_60.0=37, blocked_ai_score:score_58.0=26`
- AI terminal reasons: `ai_terminal:blocked_ai_score_below_buy_score_threshold=413, ai_terminal:first_ai_wait_big_bite_not_confirmed=291`
- latency blockers: `latency_block:latency_state_danger=23, latency_block:quote_fresh_composite_orderbook_micro_block=1`
- price guards: `entry_ai_price_canary_fallback:invalid_price=67, scale_in_price_guard_block:micro_vwap_bp<-5.0=2, scale_in_price_guard_block:micro_vwap_bp>60.0=1, entry_ai_price_canary_fallback:pre_submit_price_guard=1, entry_ai_price_canary_skip_order:orderbook_micro is ready and micro_state is bearish, indicating unfavorable submission conditions=1`
- quote refresh: `attempted=20, applied=16, latency_recovered=10, submitted_after_refresh=3`
- quote refresh downstream: `{'armed_expired_before_submit': 4, 'order_bundle_submitted': 3, 'upstream_block_after_latency_recovery': 3}`

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
- `30m`: ai=0, budget=0, latency=0, submitted=0, top=`-`, swing=`-`, upstream=`-`, ai_terminal=`-`
