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

- as_of: `2026-07-07T15:20:01`
- baseline_date: `2026-07-06`
- ai_confirmed unique: `65`
- budget_pass unique: `19`
- latency_pass unique: `15`
- submitted unique: `15`
- holding_started unique: `13`
- budget/ai unique: `29.2%` (baseline `43.8`)
- submitted/ai unique: `23.1%` (baseline `25.0`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:below_strength_base=277, blocked_strength_momentum:below_window_buy_value=254, blocked_vpw:-=161, first_ai_wait:-=126, blocked_liquidity:-=116`
- swing blockers: `-`
- upstream blockers: `first_ai_wait:-=126, blocked_ai_score:ai_score_50_buy_hold_override=67, blocked_ai_score:score_62.0=58, blocked_ai_score:score_0.0=23, blocked_ai_score:score_58.0=7`
- AI terminal reasons: `ai_terminal:first_ai_wait_big_bite_not_confirmed=126, ai_terminal:entry_policy_no_buy_score_prior=98`
- latency blockers: `latency_block:latency_state_danger=59`
- price guards: `entry_ai_price_canary_fallback:skip_low_confidence=1, entry_ai_price_canary_skip_order:orderbook_micro is bearish with negative OFI and low quote depth=1`
- quote refresh: `attempted=19, applied=18, latency_recovered=11, submitted_after_refresh=10`
- quote refresh downstream: `{'armed_expired_before_submit': 1, 'order_bundle_submitted': 10}`

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

- `5m`: ai=1, budget=0, latency=0, submitted=0, top=`blocked_ai_score:score_58.0=1, blocked_strength_momentum:below_window_buy_value=1`, swing=`-`, upstream=`blocked_ai_score:score_58.0=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=1`
- `10m`: ai=2, budget=0, latency=0, submitted=0, top=`blocked_strength_momentum:below_strength_base=2, blocked_ai_score:score_62.0=1, blocked_ai_score:score_58.0=1`, swing=`-`, upstream=`blocked_ai_score:score_62.0=1, blocked_ai_score:score_58.0=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=2`
- `30m`: ai=6, budget=0, latency=1, submitted=1, top=`blocked_strength_momentum:below_window_buy_value=12, blocked_strength_momentum:below_strength_base=9, blocked_vpw:-=5`, swing=`-`, upstream=`first_ai_wait:-=5, blocked_ai_score:score_62.0=3, blocked_ai_score:ai_score_50_buy_hold_override=2`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=5, ai_terminal:first_ai_wait_big_bite_not_confirmed=5`
