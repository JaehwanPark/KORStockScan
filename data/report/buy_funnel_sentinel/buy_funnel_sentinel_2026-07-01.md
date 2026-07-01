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

- as_of: `2026-07-01T11:50:02`
- baseline_date: `2026-06-30`
- ai_confirmed unique: `22`
- budget_pass unique: `22`
- latency_pass unique: `18`
- submitted unique: `17`
- holding_started unique: `12`
- budget/ai unique: `100.0%` (baseline `147.1`)
- submitted/ai unique: `77.3%` (baseline `123.5`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `latency_block:latency_state_danger=192, blocked_overbought:-=101, blocked_strength_momentum:below_window_buy_value=80, blocked_strength_momentum:insufficient_history=76, blocked_strength_momentum:below_buy_ratio=73`
- swing blockers: `-`
- upstream blockers: `first_ai_wait:-=26, blocked_ai_score:ai_score_50_buy_hold_override=22, blocked_ai_score:score_62.0=20, blocked_ai_score:score_58.0=8, blocked_ai_score:score_72.0=6`
- AI terminal reasons: `ai_terminal:blocked_ai_score_below_buy_score_threshold=64, ai_terminal:first_ai_wait_big_bite_not_confirmed=26`
- latency blockers: `latency_block:latency_state_danger=192`
- price guards: `scale_in_price_guard_block:micro_vwap_bp>60.0=25, scale_in_price_guard_block:quote_stale=17, entry_ai_price_canary_fallback:above_best_ask=3, entry_ai_price_canary_fallback:pre_submit_price_guard=2, entry_ai_price_canary_fallback:skip_low_confidence=1`
- quote refresh: `attempted=22, applied=21, latency_recovered=3, submitted_after_refresh=2`
- quote refresh downstream: `{'order_bundle_submitted': 2, 'upstream_block_after_latency_recovery': 1}`

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

- `5m`: ai=0, budget=4, latency=0, submitted=0, top=`latency_block:latency_state_danger=15`, swing=`-`, upstream=`-`, ai_terminal=`-`
- `10m`: ai=1, budget=5, latency=0, submitted=0, top=`latency_block:latency_state_danger=31, blocked_ai_score:score_58.0=1, blocked_gap_from_scan:-=1`, swing=`-`, upstream=`blocked_ai_score:score_58.0=1, blocked_ai_score:score_62.0=1`, ai_terminal=`ai_terminal:blocked_ai_score_below_buy_score_threshold=2`
- `30m`: ai=5, budget=6, latency=1, submitted=1, top=`latency_block:latency_state_danger=60, blocked_strength_momentum:below_window_buy_value=17, blocked_ai_score:score_62.0=11`, swing=`-`, upstream=`blocked_ai_score:score_62.0=11, blocked_ai_score:score_58.0=3, blocked_ai_score:ai_score_50_buy_hold_override=2`, ai_terminal=`ai_terminal:blocked_ai_score_below_buy_score_threshold=16, ai_terminal:first_ai_wait_big_bite_not_confirmed=1`
