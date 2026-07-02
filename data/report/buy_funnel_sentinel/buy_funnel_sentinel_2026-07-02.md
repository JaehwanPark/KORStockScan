# BUY Funnel Sentinel 2026-07-02

## 판정

- primary: `PRICE_GUARD_DROUGHT`
- secondary: `LATENCY_DROUGHT, UPSTREAM_AI_THRESHOLD`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `false`
- followup_route: `pre_submit_price_guard_review`
- followup_owner: `postclose_threshold_cycle`
- runtime_effect: `report_only_no_mutation`
- submit_contract_downstream: `code_improvement_workorder, lifecycle_decision_matrix.submit_bucket_attribution, threshold_cycle_ev_report, runtime_approval_summary, postclose_verifier`
- submit_contract_weak_matches: `LATENCY_PRE_SUBMIT, PRICE_REVALIDATION, UPSTREAM_GATE`

## 근거

- as_of: `2026-07-02T11:55:02`
- baseline_date: `2026-07-01`
- ai_confirmed unique: `32`
- budget_pass unique: `15`
- latency_pass unique: `9`
- submitted unique: `7`
- holding_started unique: `5`
- budget/ai unique: `46.9%` (baseline `100.0`)
- submitted/ai unique: `21.9%` (baseline `77.3`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:below_strength_base=138, blocked_strength_momentum:below_window_buy_value=104, blocked_strength_momentum:insufficient_history=73, blocked_liquidity:-=57, latency_block:latency_state_danger=48`
- swing blockers: `-`
- upstream blockers: `first_ai_wait:-=36, blocked_ai_score:score_62.0=21, blocked_ai_score:ai_score_50_buy_hold_override=16, blocked_ai_score:score_58.0=9, wait65_79_ev_candidate:score_74.0=6`
- AI terminal reasons: `ai_terminal:blocked_ai_score_below_buy_score_threshold=48, ai_terminal:first_ai_wait_big_bite_not_confirmed=36`
- latency blockers: `latency_block:latency_state_danger=48`
- price guards: `scale_in_price_guard_block:micro_vwap_bp>60.0=5, scale_in_price_guard_block:quote_stale=4, entry_ai_price_canary_fallback:pre_submit_price_guard=1`
- quote refresh: `attempted=15, applied=12, latency_recovered=4, submitted_after_refresh=2`
- quote refresh downstream: `{'armed_expired_before_submit': 1, 'no_downstream_event': 1, 'order_bundle_submitted': 2}`

## 금지된 자동변경

- `score_threshold_relaxation`
- `spread_cap_relaxation`
- `fallback_reenable`
- `live_threshold_runtime_mutation`
- `bot_restart`

## 권고 액션

- Review top price guard block labels and affected symbols.
- Keep threshold/runtime mutation blocked before ThresholdOpsTransition0506.

## Window Summary

- `5m`: ai=5, budget=1, latency=0, submitted=0, top=`blocked_strength_momentum:below_window_buy_value=8, blocked_strength_momentum:below_strength_base=6, latency_block:latency_state_danger=4`, swing=`-`, upstream=`blocked_ai_score:score_58.0=3, blocked_ai_score:score_62.0=2, blocked_ai_score:ai_score_50_buy_hold_override=1`, ai_terminal=`ai_terminal:blocked_ai_score_below_buy_score_threshold=6`
- `10m`: ai=8, budget=2, latency=1, submitted=0, top=`blocked_strength_momentum:below_window_buy_value=16, blocked_strength_momentum:below_strength_base=13, latency_block:latency_state_danger=9`, swing=`-`, upstream=`blocked_ai_score:score_62.0=6, blocked_ai_score:score_58.0=5, blocked_ai_score:ai_score_50_buy_hold_override=2`, ai_terminal=`ai_terminal:blocked_ai_score_below_buy_score_threshold=13, ai_terminal:first_ai_wait_big_bite_not_confirmed=1`
- `30m`: ai=13, budget=5, latency=3, submitted=2, top=`blocked_strength_momentum:below_strength_base=55, blocked_strength_momentum:below_window_buy_value=41, latency_block:latency_state_danger=24`, swing=`-`, upstream=`blocked_ai_score:score_62.0=12, blocked_ai_score:ai_score_50_buy_hold_override=7, first_ai_wait:-=6`, ai_terminal=`ai_terminal:blocked_ai_score_below_buy_score_threshold=26, ai_terminal:first_ai_wait_big_bite_not_confirmed=6`
