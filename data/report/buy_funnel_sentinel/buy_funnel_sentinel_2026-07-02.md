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

- as_of: `2026-07-02T12:30:02`
- baseline_date: `2026-07-01`
- ai_confirmed unique: `33`
- budget_pass unique: `17`
- latency_pass unique: `11`
- submitted unique: `9`
- holding_started unique: `5`
- budget/ai unique: `51.5%` (baseline `100.0`)
- submitted/ai unique: `27.3%` (baseline `82.6`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:below_strength_base=178, blocked_strength_momentum:below_window_buy_value=155, blocked_strength_momentum:insufficient_history=106, blocked_liquidity:-=72, latency_block:latency_state_danger=70`
- swing blockers: `-`
- upstream blockers: `first_ai_wait:-=43, blocked_ai_score:score_62.0=33, blocked_ai_score:ai_score_50_buy_hold_override=26, blocked_ai_score:score_58.0=12, wait65_79_ev_candidate:score_74.0=9`
- AI terminal reasons: `ai_terminal:blocked_ai_score_below_buy_score_threshold=65, ai_terminal:first_ai_wait_big_bite_not_confirmed=43`
- latency blockers: `latency_block:latency_state_danger=70`
- price guards: `scale_in_price_guard_block:micro_vwap_bp>60.0=5, scale_in_price_guard_block:quote_stale=4, entry_ai_price_canary_fallback:pre_submit_price_guard=1, scale_in_price_guard_block:invalid_quote=1`
- quote refresh: `attempted=17, applied=14, latency_recovered=5, submitted_after_refresh=2`
- quote refresh downstream: `{'armed_expired_before_submit': 1, 'budget_pass_no_submit_event': 1, 'no_downstream_event': 1, 'order_bundle_submitted': 2}`

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

- `5m`: ai=2, budget=3, latency=1, submitted=1, top=`latency_block:latency_state_danger=11, blocked_strength_momentum:below_strength_base=5, blocked_strength_momentum:below_window_buy_value=3`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=1, blocked_ai_score:score_63.0=1`, ai_terminal=`ai_terminal:blocked_ai_score_below_buy_score_threshold=1`
- `10m`: ai=5, budget=3, latency=1, submitted=1, top=`latency_block:latency_state_danger=12, blocked_strength_momentum:below_strength_base=12, blocked_strength_momentum:below_window_buy_value=9`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=3, blocked_ai_score:score_62.0=2, blocked_ai_score:score_58.0=1`, ai_terminal=`ai_terminal:blocked_ai_score_below_buy_score_threshold=4`
- `30m`: ai=7, budget=3, latency=2, submitted=2, top=`blocked_strength_momentum:below_window_buy_value=46, blocked_strength_momentum:below_strength_base=32, blocked_strength_momentum:insufficient_history=31`, swing=`-`, upstream=`blocked_ai_score:score_62.0=9, blocked_ai_score:ai_score_50_buy_hold_override=9, first_ai_wait:-=4`, ai_terminal=`ai_terminal:blocked_ai_score_below_buy_score_threshold=13, ai_terminal:first_ai_wait_big_bite_not_confirmed=4`
