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

- as_of: `2026-07-02T14:25:03`
- baseline_date: `2026-07-01`
- ai_confirmed unique: `51`
- budget_pass unique: `26`
- latency_pass unique: `17`
- submitted unique: `15`
- holding_started unique: `10`
- budget/ai unique: `51.0%` (baseline `91.7`)
- submitted/ai unique: `29.4%` (baseline `66.7`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:below_window_buy_value=295, blocked_strength_momentum:below_strength_base=252, blocked_strength_momentum:insufficient_history=142, latency_block:latency_state_danger=141, blocked_overbought:-=115`
- swing blockers: `-`
- upstream blockers: `first_ai_wait:-=74, blocked_ai_score:score_62.0=46, blocked_ai_score:ai_score_50_buy_hold_override=44, blocked_ai_score:score_58.0=15, wait65_79_ev_candidate:score_74.0=11`
- AI terminal reasons: `ai_terminal:blocked_ai_score_below_buy_score_threshold=106, ai_terminal:first_ai_wait_big_bite_not_confirmed=74`
- latency blockers: `latency_block:latency_state_danger=141`
- price guards: `scale_in_price_guard_block:micro_vwap_bp>60.0=11, scale_in_price_guard_block:quote_stale=4, entry_ai_price_canary_fallback:pre_submit_price_guard=2, scale_in_price_guard_block:invalid_quote=1`
- quote refresh: `attempted=26, applied=23, latency_recovered=7, submitted_after_refresh=4`
- quote refresh downstream: `{'armed_expired_before_submit': 1, 'budget_pass_no_submit_event': 1, 'no_downstream_event': 1, 'order_bundle_submitted': 4}`

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

- `5m`: ai=1, budget=1, latency=0, submitted=0, top=`blocked_strength_momentum:below_strength_base=4, blocked_vpw:-=2, blocked_overbought:-=2`, swing=`-`, upstream=`blocked_ai_score:score_54.0=1, blocked_ai_score:score_68.0=1, blocked_ai_score:score_62.0=1`, ai_terminal=`ai_terminal:blocked_ai_score_below_buy_score_threshold=3`
- `10m`: ai=2, budget=2, latency=1, submitted=1, top=`latency_block:latency_state_danger=5, blocked_strength_momentum:below_strength_base=4, blocked_vpw:-=3`, swing=`-`, upstream=`blocked_ai_score:score_54.0=2, blocked_ai_score:score_60.0=1, first_ai_wait:-=1`, ai_terminal=`ai_terminal:blocked_ai_score_below_buy_score_threshold=5, ai_terminal:first_ai_wait_big_bite_not_confirmed=1`
- `30m`: ai=9, budget=3, latency=2, submitted=2, top=`latency_block:latency_state_danger=18, blocked_strength_momentum:below_window_buy_value=16, blocked_strength_momentum:below_strength_base=9`, swing=`-`, upstream=`first_ai_wait:-=6, blocked_ai_score:score_54.0=5, blocked_ai_score:score_60.0=4`, ai_terminal=`ai_terminal:blocked_ai_score_below_buy_score_threshold=18, ai_terminal:first_ai_wait_big_bite_not_confirmed=6`
