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

- as_of: `2026-07-06T13:40:02`
- baseline_date: `2026-07-03`
- ai_confirmed unique: `41`
- budget_pass unique: `20`
- latency_pass unique: `11`
- submitted unique: `10`
- holding_started unique: `9`
- budget/ai unique: `48.8%` (baseline `38.5`)
- submitted/ai unique: `24.4%` (baseline `19.2`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:below_window_buy_value=302, blocked_strength_momentum:below_strength_base=160, blocked_liquidity:-=115, blocked_vpw:-=105, latency_block:latency_state_danger=103`
- swing blockers: `-`
- upstream blockers: `blocked_ai_score:ai_score_50_buy_hold_override=58, first_ai_wait:-=51, blocked_ai_score:score_62.0=42, blocked_ai_score:score_58.0=29, blocked_ai_score:score_54.0=19`
- AI terminal reasons: `ai_terminal:blocked_ai_score_below_buy_score_threshold=127, ai_terminal:first_ai_wait_big_bite_not_confirmed=51, ai_terminal:entry_policy_no_buy_score_prior=4`
- latency blockers: `latency_block:latency_state_danger=103`
- price guards: `entry_ai_price_canary_skip_order:orderbook_micro is ready and micro_state is bearish with negative OFI and high top_depth_ratio indicating weak bid-side support=1, entry_ai_price_canary_fallback:above_best_ask=1`
- quote refresh: `attempted=20, applied=18, latency_recovered=5, submitted_after_refresh=4`
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

- `5m`: ai=2, budget=3, latency=0, submitted=0, top=`blocked_strength_momentum:below_window_buy_value=7, latency_block:latency_state_danger=4, blocked_liquidity:-=2`, swing=`-`, upstream=`first_ai_wait:-=2, blocked_ai_score:score_62.0=2, blocked_ai_score:ai_score_50_buy_hold_override=1`, ai_terminal=`ai_terminal:first_ai_wait_big_bite_not_confirmed=2, ai_terminal:entry_policy_no_buy_score_prior=2`
- `10m`: ai=3, budget=4, latency=0, submitted=0, top=`latency_block:latency_state_danger=11, blocked_strength_momentum:below_window_buy_value=11, blocked_liquidity:-=4`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=3, first_ai_wait:-=2, blocked_ai_score:score_62.0=2`, ai_terminal=`ai_terminal:first_ai_wait_big_bite_not_confirmed=2, ai_terminal:entry_policy_no_buy_score_prior=2`
- `30m`: ai=9, budget=6, latency=1, submitted=1, top=`blocked_strength_momentum:below_window_buy_value=37, latency_block:latency_state_danger=24, blocked_strength_momentum:below_strength_base=17`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=12, first_ai_wait:-=7, blocked_ai_score:score_62.0=3`, ai_terminal=`ai_terminal:first_ai_wait_big_bite_not_confirmed=7, ai_terminal:entry_policy_no_buy_score_prior=4, ai_terminal:blocked_ai_score_below_buy_score_threshold=1`
