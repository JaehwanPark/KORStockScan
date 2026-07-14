# BUY Funnel Sentinel 2026-07-14

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

- as_of: `2026-07-14T15:20:03`
- baseline_date: `2026-07-13`
- ai_confirmed unique: `25`
- budget_pass unique: `44`
- latency_pass unique: `7`
- submitted unique: `4`
- holding_started unique: `3`
- budget/ai unique: `176.0%` (baseline `200.0`)
- submitted/ai unique: `16.0%` (baseline `12.0`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:below_window_buy_value=141, latency_block:latency_state_danger=35, blocked_liquidity:-=31, first_ai_wait:-=26, blocked_vpw:-=11`
- swing blockers: `-`
- upstream blockers: `first_ai_wait:-=26, blocked_ai_score:ai_score_50_buy_hold_override=11, blocked_ai_score:score_62.0=11, blocked_ai_score:score_64.0=8, blocked_ai_score:score_58.0=7`
- AI terminal reasons: `ai_terminal:entry_policy_no_buy_score_prior=36, ai_terminal:first_ai_wait_big_bite_not_confirmed=26`
- latency blockers: `latency_block:latency_state_danger=35`
- price guards: `entry_ai_price_canary_fallback:skip_low_confidence=2, pre_submit_entry_ai_authority_guard_block:entry_ai_score_unavailable=1`
- quote refresh: `attempted=28, applied=23, latency_recovered=5, submitted_after_refresh=3`
- quote refresh downstream: `{'budget_pass_no_submit_event': 1, 'order_bundle_submitted': 3, 'price_guard_or_revalidation': 1}`

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

- `5m`: ai=1, budget=1, latency=0, submitted=0, top=`blocked_liquidity:-=1, blocked_ai_score:score_62.0=1, latency_block:latency_state_danger=1`, swing=`-`, upstream=`blocked_ai_score:score_62.0=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=1`
- `10m`: ai=1, budget=3, latency=0, submitted=0, top=`blocked_liquidity:-=2, blocked_ai_score:score_62.0=2, blocked_strength_momentum:below_window_buy_value=2`, swing=`-`, upstream=`blocked_ai_score:score_62.0=2`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=2`
- `30m`: ai=1, budget=12, latency=0, submitted=0, top=`blocked_strength_momentum:below_window_buy_value=10, latency_block:latency_state_danger=9, blocked_ai_score:score_62.0=5`, swing=`-`, upstream=`blocked_ai_score:score_62.0=5`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=5`
