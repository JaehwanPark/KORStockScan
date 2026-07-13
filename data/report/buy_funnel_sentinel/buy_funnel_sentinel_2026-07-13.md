# BUY Funnel Sentinel 2026-07-13

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

- as_of: `2026-07-13T13:10:02`
- baseline_date: `2026-07-10`
- ai_confirmed unique: `23`
- budget_pass unique: `32`
- latency_pass unique: `4`
- submitted unique: `3`
- holding_started unique: `3`
- budget/ai unique: `139.1%` (baseline `46.7`)
- submitted/ai unique: `13.0%` (baseline `8.4`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:below_window_buy_value=203, latency_block:latency_state_danger=55, blocked_liquidity:-=35, blocked_ai_score:ai_score_50_buy_hold_override=27, first_ai_wait:-=20`
- swing blockers: `-`
- upstream blockers: `blocked_ai_score:ai_score_50_buy_hold_override=27, first_ai_wait:-=20, blocked_ai_score:score_0.0=12, blocked_ai_score:score_58.0=10, blocked_ai_score:score_62.0=7`
- AI terminal reasons: `ai_terminal:entry_policy_no_buy_score_prior=38, ai_terminal:first_ai_wait_big_bite_not_confirmed=20`
- latency blockers: `latency_block:latency_state_danger=55`
- price guards: `pre_submit_entry_ai_authority_guard_block:entry_ai_score_unavailable=2, entry_ai_price_canary_fallback:low_confidence=1, entry_ai_price_canary_fallback:above_best_ask=1`
- quote refresh: `attempted=26, applied=24, latency_recovered=3, submitted_after_refresh=2`
- quote refresh downstream: `{'order_bundle_submitted': 2, 'price_guard_or_revalidation': 1}`

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

- `5m`: ai=0, budget=1, latency=0, submitted=0, top=`blocked_strength_momentum:below_window_buy_value=1`, swing=`-`, upstream=`-`, ai_terminal=`-`
- `10m`: ai=1, budget=4, latency=0, submitted=0, top=`blocked_strength_momentum:below_window_buy_value=4, latency_block:latency_state_danger=3, blocked_ai_score:ai_score_50_buy_hold_override=1`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=1, blocked_ai_score:score_62.0=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=1`
- `30m`: ai=3, budget=10, latency=2, submitted=2, top=`latency_block:latency_state_danger=17, blocked_strength_momentum:below_window_buy_value=6, blocked_liquidity:-=3`, swing=`-`, upstream=`blocked_ai_score:score_70.0=2, blocked_ai_score:score_62.0=2, blocked_ai_score:score_58.0=2`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=7, ai_terminal:first_ai_wait_big_bite_not_confirmed=1`
