# BUY Funnel Sentinel 2026-06-29

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

- as_of: `2026-06-29T15:20:03`
- baseline_date: `2026-06-26`
- ai_confirmed unique: `178`
- budget_pass unique: `31`
- latency_pass unique: `13`
- submitted unique: `1`
- holding_started unique: `1`
- budget/ai unique: `17.4%` (baseline `28.2`)
- submitted/ai unique: `0.6%` (baseline `7.7`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:below_window_buy_value=365, blocked_overbought:-=293, first_ai_wait:-=274, blocked_liquidity:-=254, blocked_strength_momentum:insufficient_history=180`
- swing blockers: `-`
- upstream blockers: `first_ai_wait:-=274, blocked_ai_score:ai_score_50_buy_hold_override=107, blocked_ai_score:score_62.0=98, wait65_79_ev_candidate:score_74.0=40, blocked_ai_score:score_58.0=16`
- AI terminal reasons: `ai_terminal:first_ai_wait_big_bite_not_confirmed=274, ai_terminal:blocked_ai_score_below_buy_score_threshold=172`
- latency blockers: `latency_block:latency_state_danger=26`
- price guards: `entry_ai_price_canary_fallback:invalid_price=19, scale_in_price_guard_block:quote_consistency_diverged=1`
- quote refresh: `attempted=31, applied=23, latency_recovered=10, submitted_after_refresh=1`
- quote refresh downstream: `{'armed_expired_before_submit': 3, 'budget_pass_no_submit_event': 1, 'no_downstream_event': 1, 'order_bundle_submitted': 1, 'other:first_ai_wait': 1, 'upstream_block_after_latency_recovery': 3}`

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

- `5m`: ai=6, budget=0, latency=0, submitted=0, top=`first_ai_wait:-=5, blocked_liquidity:-=4, blocked_overbought:-=4`, swing=`-`, upstream=`first_ai_wait:-=5, blocked_ai_score:ai_score_50_buy_hold_override=2, blocked_ai_score:score_62.0=1`, ai_terminal=`ai_terminal:first_ai_wait_big_bite_not_confirmed=5, ai_terminal:blocked_ai_score_below_buy_score_threshold=3`
- `10m`: ai=7, budget=0, latency=0, submitted=0, top=`blocked_overbought:-=8, blocked_liquidity:-=5, first_ai_wait:-=5`, swing=`-`, upstream=`first_ai_wait:-=5, blocked_ai_score:score_62.0=3, blocked_ai_score:ai_score_50_buy_hold_override=3`, ai_terminal=`ai_terminal:blocked_ai_score_below_buy_score_threshold=6, ai_terminal:first_ai_wait_big_bite_not_confirmed=5`
- `30m`: ai=11, budget=0, latency=0, submitted=0, top=`blocked_overbought:-=12, blocked_liquidity:-=11, blocked_ai_score:ai_score_50_buy_hold_override=9`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=9, blocked_ai_score:score_62.0=8, first_ai_wait:-=8`, ai_terminal=`ai_terminal:blocked_ai_score_below_buy_score_threshold=14, ai_terminal:first_ai_wait_big_bite_not_confirmed=8`
