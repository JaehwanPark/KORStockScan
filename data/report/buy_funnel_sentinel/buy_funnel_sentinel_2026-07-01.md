# BUY Funnel Sentinel 2026-07-01

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

- as_of: `2026-07-01T15:20:03`
- baseline_date: `2026-06-30`
- ai_confirmed unique: `43`
- budget_pass unique: `34`
- latency_pass unique: `30`
- submitted unique: `29`
- holding_started unique: `20`
- budget/ai unique: `79.1%` (baseline `120.0`)
- submitted/ai unique: `67.4%` (baseline `100.0`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `latency_block:latency_state_danger=642, blocked_overbought:-=189, blocked_strength_momentum:below_window_buy_value=136, blocked_strength_momentum:below_buy_ratio=106, blocked_strength_momentum:below_strength_base=97`
- swing blockers: `-`
- upstream blockers: `first_ai_wait:-=53, blocked_ai_score:score_62.0=42, blocked_ai_score:ai_score_50_buy_hold_override=32, blocked_ai_score:score_58.0=13, blocked_ai_score:score_72.0=10`
- AI terminal reasons: `ai_terminal:blocked_ai_score_below_buy_score_threshold=133, ai_terminal:first_ai_wait_big_bite_not_confirmed=53`
- latency blockers: `latency_block:latency_state_danger=642`
- price guards: `scale_in_price_guard_block:micro_vwap_bp>60.0=28, scale_in_price_guard_block:quote_stale=21, entry_ai_price_canary_fallback:above_best_ask=5, entry_ai_price_canary_fallback:pre_submit_price_guard=4, entry_ai_price_canary_fallback:skip_low_confidence=2`
- quote refresh: `attempted=34, applied=33, latency_recovered=9, submitted_after_refresh=8`
- quote refresh downstream: `{'order_bundle_submitted': 8, 'upstream_block_after_latency_recovery': 1}`

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

- `5m`: ai=3, budget=4, latency=2, submitted=2, top=`latency_block:latency_state_danger=6, blocked_vpw:-=3, blocked_strength_momentum:below_window_buy_value=3`, swing=`-`, upstream=`blocked_ai_score:score_62.0=2, blocked_ai_score:score_72.0=1, first_ai_wait:-=1`, ai_terminal=`ai_terminal:blocked_ai_score_below_buy_score_threshold=3, ai_terminal:first_ai_wait_big_bite_not_confirmed=1`
- `10m`: ai=5, budget=5, latency=3, submitted=3, top=`latency_block:latency_state_danger=11, blocked_strength_momentum:below_window_buy_value=5, blocked_vpw:-=4`, swing=`-`, upstream=`first_ai_wait:-=3, blocked_ai_score:score_62.0=2, blocked_ai_score:score_67.0=1`, ai_terminal=`ai_terminal:blocked_ai_score_below_buy_score_threshold=4, ai_terminal:first_ai_wait_big_bite_not_confirmed=3`
- `30m`: ai=6, budget=7, latency=5, submitted=5, top=`latency_block:latency_state_danger=58, blocked_strength_momentum:below_window_buy_value=6, first_ai_wait:-=5`, swing=`-`, upstream=`first_ai_wait:-=5, blocked_ai_score:score_62.0=2, blocked_ai_score:score_61.0=1`, ai_terminal=`ai_terminal:first_ai_wait_big_bite_not_confirmed=5, ai_terminal:blocked_ai_score_below_buy_score_threshold=5`
