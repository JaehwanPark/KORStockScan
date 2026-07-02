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

- as_of: `2026-07-02T13:40:02`
- baseline_date: `2026-07-01`
- ai_confirmed unique: `50`
- budget_pass unique: `24`
- latency_pass unique: `15`
- submitted unique: `12`
- holding_started unique: `8`
- budget/ai unique: `48.0%` (baseline `94.3`)
- submitted/ai unique: `24.0%` (baseline `65.7`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:below_window_buy_value=262, blocked_strength_momentum:below_strength_base=237, blocked_strength_momentum:insufficient_history=139, blocked_overbought:-=108, blocked_liquidity:-=100`
- swing blockers: `-`
- upstream blockers: `first_ai_wait:-=64, blocked_ai_score:score_62.0=42, blocked_ai_score:ai_score_50_buy_hold_override=42, blocked_ai_score:score_58.0=13, wait65_79_ev_candidate:score_74.0=11`
- AI terminal reasons: `ai_terminal:blocked_ai_score_below_buy_score_threshold=85, ai_terminal:first_ai_wait_big_bite_not_confirmed=64`
- latency blockers: `latency_block:latency_state_danger=94`
- price guards: `scale_in_price_guard_block:micro_vwap_bp>60.0=8, scale_in_price_guard_block:quote_stale=4, entry_ai_price_canary_fallback:pre_submit_price_guard=2, scale_in_price_guard_block:invalid_quote=1`
- quote refresh: `attempted=24, applied=21, latency_recovered=6, submitted_after_refresh=3`
- quote refresh downstream: `{'armed_expired_before_submit': 1, 'budget_pass_no_submit_event': 1, 'no_downstream_event': 1, 'order_bundle_submitted': 3}`

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

- `5m`: ai=1, budget=1, latency=0, submitted=0, top=`blocked_strength_momentum:below_window_buy_value=3, blocked_overbought:-=3, latency_block:latency_state_danger=2`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=2, blocked_ai_score:score_58.0=1`, ai_terminal=`ai_terminal:blocked_ai_score_below_buy_score_threshold=1`
- `10m`: ai=2, budget=2, latency=1, submitted=0, top=`latency_block:latency_state_danger=6, blocked_overbought:-=5, blocked_liquidity:-=4`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=3, blocked_ai_score:score_62.0=2, blocked_ai_score:score_58.0=1`, ai_terminal=`ai_terminal:blocked_ai_score_below_buy_score_threshold=3`
- `30m`: ai=9, budget=4, latency=2, submitted=1, top=`blocked_strength_momentum:below_window_buy_value=45, blocked_overbought:-=31, blocked_strength_momentum:below_strength_base=27`, swing=`-`, upstream=`first_ai_wait:-=6, blocked_ai_score:score_62.0=5, blocked_ai_score:ai_score_50_buy_hold_override=5`, ai_terminal=`ai_terminal:blocked_ai_score_below_buy_score_threshold=9, ai_terminal:first_ai_wait_big_bite_not_confirmed=6`
