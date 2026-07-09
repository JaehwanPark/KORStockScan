# BUY Funnel Sentinel 2026-07-09

## 판정

- primary: `UPSTREAM_AI_THRESHOLD`
- secondary: `LATENCY_DROUGHT`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `false`
- followup_route: `score65_74_counterfactual_review`
- followup_owner: `postclose_threshold_cycle`
- runtime_effect: `report_only_no_mutation`
- submit_contract_downstream: `code_improvement_workorder, lifecycle_decision_matrix.submit_bucket_attribution, threshold_cycle_ev_report, runtime_approval_summary, postclose_verifier`
- submit_contract_weak_matches: `LATENCY_PRE_SUBMIT, UPSTREAM_GATE`

## 근거

- as_of: `2026-07-09T15:20:02`
- baseline_date: `2026-07-08`
- ai_confirmed unique: `28`
- budget_pass unique: `19`
- latency_pass unique: `14`
- submitted unique: `12`
- holding_started unique: `4`
- budget/ai unique: `67.9%` (baseline `23.9`)
- submitted/ai unique: `42.9%` (baseline `12.7`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:below_window_buy_value=63, latency_block:latency_state_danger=53, blocked_liquidity:-=20, first_ai_wait:-=19, blocked_vpw:-=14`
- swing blockers: `-`
- upstream blockers: `first_ai_wait:-=19, blocked_ai_score:score_62.0=7, blocked_ai_score:ai_score_50_buy_hold_override=5, blocked_ai_score:score_58.0=4, blocked_ai_score:score_0.0=3`
- AI terminal reasons: `ai_terminal:first_ai_wait_big_bite_not_confirmed=19, ai_terminal:entry_policy_no_buy_score_prior=16`
- latency blockers: `latency_block:latency_state_danger=53`
- price guards: `pre_submit_entry_ai_authority_guard_block:entry_ai_score_unavailable=5, entry_ai_price_canary_fallback:above_best_ask=1, entry_ai_price_canary_skip_order:orderbook_micro is bearish with negative OFI and high top_depth_ratio indicating downward pressure=1`
- quote refresh: `attempted=18, applied=17, latency_recovered=8, submitted_after_refresh=5`
- quote refresh downstream: `{'order_bundle_submitted': 5, 'price_guard_or_revalidation': 3}`

## 금지된 자동변경

- `score_threshold_relaxation`
- `spread_cap_relaxation`
- `fallback_reenable`
- `live_threshold_runtime_mutation`
- `bot_restart`

## 권고 액션

- Append score50/wait65_74 missed-winner and avoided-loser cohorts to report-only review.
- Do not relax score threshold or revive fallback without a new single-axis workorder.

## Window Summary

- `5m`: ai=0, budget=0, latency=0, submitted=0, top=`-`, swing=`-`, upstream=`-`, ai_terminal=`-`
- `10m`: ai=0, budget=0, latency=0, submitted=0, top=`-`, swing=`-`, upstream=`-`, ai_terminal=`-`
- `30m`: ai=0, budget=0, latency=0, submitted=0, top=`-`, swing=`-`, upstream=`-`, ai_terminal=`-`
