# BUY Funnel Sentinel 2026-07-07

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

- as_of: `2026-07-07T14:25:09`
- baseline_date: `2026-07-06`
- ai_confirmed unique: `59`
- budget_pass unique: `17`
- latency_pass unique: `14`
- submitted unique: `13`
- holding_started unique: `12`
- budget/ai unique: `28.8%` (baseline `42.6`)
- submitted/ai unique: `22.0%` (baseline `23.4`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:below_strength_base=253, blocked_strength_momentum:below_window_buy_value=238, blocked_vpw:-=150, first_ai_wait:-=114, blocked_liquidity:-=109`
- swing blockers: `-`
- upstream blockers: `first_ai_wait:-=114, blocked_ai_score:ai_score_50_buy_hold_override=62, blocked_ai_score:score_62.0=55, blocked_ai_score:score_0.0=22, blocked_ai_score:score_58.0=6`
- AI terminal reasons: `ai_terminal:first_ai_wait_big_bite_not_confirmed=114, ai_terminal:entry_policy_no_buy_score_prior=93`
- latency blockers: `latency_block:latency_state_danger=53`
- price guards: `entry_ai_price_canary_fallback:skip_low_confidence=1, entry_ai_price_canary_skip_order:orderbook_micro is bearish with negative OFI and low quote depth=1`
- quote refresh: `attempted=17, applied=16, latency_recovered=10, submitted_after_refresh=9`
- quote refresh downstream: `{'armed_expired_before_submit': 1, 'order_bundle_submitted': 9}`

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

- `5m`: ai=1, budget=0, latency=0, submitted=0, top=`blocked_strength_momentum:below_strength_base=7, blocked_vpw:-=5, blocked_ai_score:ai_score_50_buy_hold_override=4`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=4, blocked_ai_score:score_0.0=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=1`
- `10m`: ai=3, budget=1, latency=1, submitted=1, top=`blocked_strength_momentum:below_strength_base=10, blocked_vpw:-=7, blocked_liquidity:-=5`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=5, first_ai_wait:-=2, blocked_ai_score:score_0.0=1`, ai_terminal=`ai_terminal:first_ai_wait_big_bite_not_confirmed=2, ai_terminal:entry_policy_no_buy_score_prior=1`
- `30m`: ai=10, budget=4, latency=3, submitted=3, top=`blocked_strength_momentum:below_strength_base=38, blocked_vpw:-=19, blocked_strength_momentum:below_window_buy_value=19`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=9, first_ai_wait:-=5, blocked_ai_score:score_62.0=3`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=8, ai_terminal:first_ai_wait_big_bite_not_confirmed=5`
