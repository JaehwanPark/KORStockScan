# BUY Funnel Sentinel 2026-07-02

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

- as_of: `2026-07-02T15:20:03`
- baseline_date: `2026-07-01`
- ai_confirmed unique: `56`
- budget_pass unique: `32`
- latency_pass unique: `21`
- submitted unique: `19`
- holding_started unique: `12`
- budget/ai unique: `57.1%` (baseline `79.1`)
- submitted/ai unique: `33.9%` (baseline `67.4`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:below_window_buy_value=312, blocked_strength_momentum:below_strength_base=295, latency_block:latency_state_danger=193, blocked_strength_momentum:insufficient_history=145, blocked_vpw:-=133`
- swing blockers: `-`
- upstream blockers: `first_ai_wait:-=88, blocked_ai_score:ai_score_50_buy_hold_override=63, blocked_ai_score:score_62.0=53, blocked_ai_score:score_58.0=18, wait65_79_ev_candidate:score_74.0=11`
- AI terminal reasons: `ai_terminal:blocked_ai_score_below_buy_score_threshold=122, ai_terminal:first_ai_wait_big_bite_not_confirmed=88`
- latency blockers: `latency_block:latency_state_danger=193`
- price guards: `scale_in_price_guard_block:micro_vwap_bp>60.0=11, scale_in_price_guard_block:quote_stale=4, entry_ai_price_canary_fallback:pre_submit_price_guard=2, scale_in_price_guard_block:invalid_quote=1, entry_ai_price_canary_fallback:above_best_ask=1`
- quote refresh: `attempted=32, applied=29, latency_recovered=7, submitted_after_refresh=4`
- quote refresh downstream: `{'armed_expired_before_submit': 1, 'budget_pass_no_submit_event': 1, 'no_downstream_event': 1, 'order_bundle_submitted': 4}`

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

- `5m`: ai=2, budget=2, latency=0, submitted=0, top=`latency_block:latency_state_danger=6, blocked_strength_momentum:below_window_buy_value=3, blocked_vpw:-=2`, swing=`-`, upstream=`blocked_ai_score:score_59.0=1, blocked_ai_score:score_62.0=1`, ai_terminal=`ai_terminal:blocked_ai_score_below_buy_score_threshold=2`
- `10m`: ai=4, budget=2, latency=0, submitted=0, top=`latency_block:latency_state_danger=11, blocked_strength_momentum:below_strength_base=7, blocked_vpw:-=6`, swing=`-`, upstream=`first_ai_wait:-=3, blocked_ai_score:ai_score_50_buy_hold_override=3, wait65_79_ev_candidate:score_67.0=1`, ai_terminal=`ai_terminal:first_ai_wait_big_bite_not_confirmed=3, ai_terminal:blocked_ai_score_below_buy_score_threshold=2`
- `30m`: ai=8, budget=4, latency=1, submitted=1, top=`latency_block:latency_state_danger=33, blocked_strength_momentum:below_strength_base=20, blocked_vpw:-=14`, swing=`-`, upstream=`first_ai_wait:-=9, blocked_ai_score:ai_score_50_buy_hold_override=7, blocked_ai_score:score_62.0=3`, ai_terminal=`ai_terminal:first_ai_wait_big_bite_not_confirmed=9, ai_terminal:blocked_ai_score_below_buy_score_threshold=7`
