# BUY Funnel Sentinel 2026-07-06

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

- as_of: `2026-07-06T15:20:02`
- baseline_date: `2026-07-03`
- ai_confirmed unique: `48`
- budget_pass unique: `21`
- latency_pass unique: `13`
- submitted unique: `12`
- holding_started unique: `11`
- budget/ai unique: `43.8%` (baseline `48.6`)
- submitted/ai unique: `25.0%` (baseline `32.4`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:below_window_buy_value=386, blocked_strength_momentum:below_strength_base=230, blocked_vpw:-=161, blocked_liquidity:-=141, blocked_overbought:-=123`
- swing blockers: `-`
- upstream blockers: `first_ai_wait:-=89, blocked_ai_score:ai_score_50_buy_hold_override=70, blocked_ai_score:score_62.0=48, blocked_ai_score:score_58.0=33, blocked_ai_score:score_54.0=20`
- AI terminal reasons: `ai_terminal:blocked_ai_score_below_buy_score_threshold=127, ai_terminal:first_ai_wait_big_bite_not_confirmed=89, ai_terminal:entry_policy_no_buy_score_prior=23`
- latency blockers: `latency_block:latency_state_danger=111`
- price guards: `entry_ai_price_canary_skip_order:orderbook_micro is ready and micro_state is bearish with negative OFI and high top_depth_ratio indicating weak bid-side support=1, entry_ai_price_canary_fallback:above_best_ask=1, entry_ai_price_canary_fallback:low_confidence=1`
- quote refresh: `attempted=21, applied=19, latency_recovered=6, submitted_after_refresh=5`
- quote refresh downstream: `{'budget_pass_no_submit_event': 1, 'order_bundle_submitted': 5}`

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

- `5m`: ai=4, budget=1, latency=1, submitted=1, top=`blocked_strength_momentum:below_strength_base=5, blocked_vpw:-=3, blocked_liquidity:-=2`, swing=`-`, upstream=`blocked_ai_score:score_62.0=2, blocked_ai_score:score_58.0=1, first_ai_wait:-=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=3, ai_terminal:first_ai_wait_big_bite_not_confirmed=1`
- `10m`: ai=4, budget=1, latency=1, submitted=1, top=`blocked_strength_momentum:below_strength_base=8, blocked_vpw:-=4, blocked_strength_momentum:below_window_buy_value=4`, swing=`-`, upstream=`first_ai_wait:-=2, blocked_ai_score:score_62.0=2, wait65_79_ev_candidate:score_74.0=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=3, ai_terminal:first_ai_wait_big_bite_not_confirmed=2`
- `30m`: ai=7, budget=1, latency=1, submitted=1, top=`blocked_strength_momentum:below_strength_base=17, blocked_strength_momentum:below_window_buy_value=13, blocked_vpw:-=12`, swing=`-`, upstream=`first_ai_wait:-=6, blocked_ai_score:score_58.0=2, blocked_ai_score:score_62.0=2`, ai_terminal=`ai_terminal:first_ai_wait_big_bite_not_confirmed=6, ai_terminal:entry_policy_no_buy_score_prior=6`
