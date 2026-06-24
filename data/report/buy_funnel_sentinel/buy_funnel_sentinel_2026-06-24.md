# BUY Funnel Sentinel 2026-06-24

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

- as_of: `2026-06-24T15:20:04`
- baseline_date: `2026-06-23`
- ai_confirmed unique: `85`
- budget_pass unique: `22`
- latency_pass unique: `11`
- submitted unique: `7`
- holding_started unique: `3`
- budget/ai unique: `25.9%` (baseline `38.5`)
- submitted/ai unique: `8.2%` (baseline `2.6`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:below_strength_base=452, blocked_strength_momentum:insufficient_history=408, blocked_liquidity:-=397, blocked_overbought:-=286, first_ai_wait:-=282`
- swing blockers: `-`
- upstream blockers: `first_ai_wait:-=282, blocked_ai_score:ai_score_50_buy_hold_override=205, blocked_ai_score:score_62.0=141, wait65_79_ev_candidate:score_68.0=28, blocked_ai_score:score_60.0=26`
- AI terminal reasons: `ai_terminal:first_ai_wait_big_bite_not_confirmed=282, ai_terminal:blocked_ai_score_below_buy_score_threshold=264`
- latency blockers: `latency_block:latency_state_danger=33`
- price guards: `entry_ai_price_canary_fallback:invalid_price=91, entry_ai_price_canary_fallback:pre_submit_price_guard=2, scale_in_price_guard_block:micro_vwap_bp>60.0=2, scale_in_price_guard_block:invalid_quote=1`
- quote refresh: `attempted=22, applied=18, latency_recovered=9, submitted_after_refresh=6`
- quote refresh downstream: `{'budget_pass_no_submit_event': 1, 'no_downstream_event': 2, 'order_bundle_submitted': 6}`

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

- `5m`: ai=5, budget=0, latency=0, submitted=0, top=`blocked_overbought:-=5, blocked_strength_momentum:insufficient_history=5, blocked_liquidity:-=3`, swing=`-`, upstream=`first_ai_wait:-=2, wait65_79_ev_candidate:score_72.0=2, blocked_ai_score:score_72.0=2`, ai_terminal=`ai_terminal:blocked_ai_score_below_buy_score_threshold=7, ai_terminal:first_ai_wait_big_bite_not_confirmed=2`
- `10m`: ai=9, budget=1, latency=0, submitted=0, top=`blocked_liquidity:-=10, blocked_overbought:-=8, blocked_strength_momentum:insufficient_history=7`, swing=`-`, upstream=`blocked_ai_score:score_62.0=6, first_ai_wait:-=4, blocked_ai_score:ai_score_50_buy_hold_override=2`, ai_terminal=`ai_terminal:blocked_ai_score_below_buy_score_threshold=12, ai_terminal:first_ai_wait_big_bite_not_confirmed=4`
- `30m`: ai=17, budget=2, latency=0, submitted=0, top=`blocked_liquidity:-=22, first_ai_wait:-=21, blocked_strength_momentum:below_strength_base=19`, swing=`-`, upstream=`first_ai_wait:-=21, blocked_ai_score:score_62.0=18, blocked_ai_score:ai_score_50_buy_hold_override=8`, ai_terminal=`ai_terminal:blocked_ai_score_below_buy_score_threshold=33, ai_terminal:first_ai_wait_big_bite_not_confirmed=21`
