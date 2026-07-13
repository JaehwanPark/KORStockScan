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

- as_of: `2026-07-13T14:10:01`
- baseline_date: `2026-07-10`
- ai_confirmed unique: `24`
- budget_pass unique: `43`
- latency_pass unique: `1`
- submitted unique: `3`
- holding_started unique: `3`
- budget/ai unique: `179.2%` (baseline `50.0`)
- submitted/ai unique: `12.5%` (baseline `9.5`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:below_window_buy_value=248, blocked_liquidity:-=35, blocked_ai_score:ai_score_50_buy_hold_override=24, first_ai_wait:-=20, blocked_strength_momentum:insufficient_history=15`
- swing blockers: `-`
- upstream blockers: `blocked_ai_score:ai_score_50_buy_hold_override=24, first_ai_wait:-=20, blocked_ai_score:score_0.0=7, blocked_ai_score:score_58.0=6, blocked_ai_score:score_62.0=6`
- AI terminal reasons: `ai_terminal:entry_policy_no_buy_score_prior=41, ai_terminal:first_ai_wait_big_bite_not_confirmed=20`
- latency blockers: `latency_block:latency_state_danger=12`
- price guards: `pre_submit_entry_ai_authority_guard_block:entry_ai_score_unavailable=3, entry_ai_price_canary_fallback:low_confidence=1, entry_ai_price_canary_fallback:above_best_ask=1`
- quote refresh: `attempted=9, applied=7, latency_recovered=0, submitted_after_refresh=0`
- quote refresh downstream: `{}`

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

- `5m`: ai=0, budget=1, latency=0, submitted=0, top=`-`, swing=`-`, upstream=`-`, ai_terminal=`-`
- `10m`: ai=0, budget=4, latency=0, submitted=0, top=`latency_block:latency_state_danger=1`, swing=`-`, upstream=`-`, ai_terminal=`-`
- `30m`: ai=0, budget=12, latency=0, submitted=0, top=`latency_block:latency_state_danger=10`, swing=`-`, upstream=`-`, ai_terminal=`-`
