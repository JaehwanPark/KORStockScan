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

- as_of: `2026-07-06T12:10:02`
- baseline_date: `2026-07-03`
- ai_confirmed unique: `34`
- budget_pass unique: `16`
- latency_pass unique: `9`
- submitted unique: `8`
- holding_started unique: `7`
- budget/ai unique: `47.1%` (baseline `27.8`)
- submitted/ai unique: `23.5%` (baseline `11.1`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:below_window_buy_value=162, blocked_strength_momentum:below_strength_base=79, latency_block:latency_state_danger=72, blocked_overbought:-=70, blocked_liquidity:-=67`
- swing blockers: `-`
- upstream blockers: `first_ai_wait:-=35, blocked_ai_score:score_62.0=31, blocked_ai_score:ai_score_50_buy_hold_override=29, blocked_ai_score:score_58.0=18, blocked_ai_score:score_54.0=10`
- AI terminal reasons: `ai_terminal:blocked_ai_score_below_buy_score_threshold=87, ai_terminal:first_ai_wait_big_bite_not_confirmed=35`
- latency blockers: `latency_block:latency_state_danger=72`
- price guards: `entry_ai_price_canary_skip_order:orderbook_micro is ready and micro_state is bearish with negative OFI and high top_depth_ratio indicating weak bid-side support=1, entry_ai_price_canary_fallback:above_best_ask=1`
- quote refresh: `attempted=16, applied=15, latency_recovered=5, submitted_after_refresh=4`
- quote refresh downstream: `{'budget_pass_no_submit_event': 1, 'order_bundle_submitted': 4}`

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

- `5m`: ai=2, budget=1, latency=0, submitted=0, top=`blocked_strength_momentum:below_strength_base=6, blocked_strength_momentum:below_window_buy_value=6, blocked_ai_score:score_54.0=2`, swing=`-`, upstream=`blocked_ai_score:score_54.0=2, blocked_ai_score:score_62.0=2, blocked_ai_score:score_58.0=1`, ai_terminal=`ai_terminal:blocked_ai_score_below_buy_score_threshold=5`
- `10m`: ai=5, budget=1, latency=0, submitted=0, top=`blocked_strength_momentum:below_window_buy_value=12, blocked_strength_momentum:below_strength_base=9, blocked_liquidity:-=7`, swing=`-`, upstream=`blocked_ai_score:score_54.0=4, blocked_ai_score:score_62.0=4, blocked_ai_score:score_58.0=3`, ai_terminal=`ai_terminal:blocked_ai_score_below_buy_score_threshold=11, ai_terminal:first_ai_wait_big_bite_not_confirmed=1`
- `30m`: ai=11, budget=1, latency=0, submitted=0, top=`blocked_strength_momentum:below_window_buy_value=28, blocked_strength_momentum:below_strength_base=27, blocked_liquidity:-=26`, swing=`-`, upstream=`blocked_ai_score:score_62.0=12, blocked_ai_score:score_54.0=7, first_ai_wait:-=4`, ai_terminal=`ai_terminal:blocked_ai_score_below_buy_score_threshold=32, ai_terminal:first_ai_wait_big_bite_not_confirmed=4`
