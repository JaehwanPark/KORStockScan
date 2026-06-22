# BUY Funnel Sentinel 2026-06-22

## 판정

- primary: `SUBMIT_DROUGHT_CRITICAL`
- secondary: `PRICE_GUARD_DROUGHT, LATENCY_DROUGHT, UPSTREAM_AI_THRESHOLD`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `false`
- followup_route: `entry_submit_drought_auto_workorder`
- followup_owner: `postclose_threshold_cycle_and_lifecycle_decision_matrix`
- runtime_effect: `auto_workorder_no_intraday_mutation`
- submit_contract_downstream: `code_improvement_workorder, lifecycle_decision_matrix.submit_bucket_attribution, threshold_cycle_ev_report, runtime_approval_summary, postclose_verifier`
- submit_contract_weak_matches: `BROKER_RECEIPT, BUDGET_PASS_COLLAPSE, FILL_QUALITY, LATENCY_PRE_SUBMIT, PRICE_REVALIDATION, SIM_REAL_AUTHORITY, TELEGRAM_POST_SUBMIT_ONLY, UPSTREAM_GATE`

## 근거

- as_of: `2026-06-22T15:20:02`
- baseline_date: `2026-06-19`
- ai_confirmed unique: `172`
- budget_pass unique: `44`
- latency_pass unique: `11`
- submitted unique: `1`
- holding_started unique: `0`
- budget/ai unique: `25.6%` (baseline `19.1`)
- submitted/ai unique: `0.6%` (baseline `0.0`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `latency_block:latency_state_danger=734, first_ai_wait:-=412, blocked_strength_momentum:below_window_buy_value=346, blocked_liquidity:-=229, blocked_strength_momentum:below_strength_base=191`
- swing blockers: `blocked_swing_score_vpw:-=592, blocked_swing_gap:-=65`
- upstream blockers: `first_ai_wait:-=412, blocked_ai_score:ai_score_50_buy_hold_override=175, blocked_ai_score:score_62.0=88, wait65_79_ev_candidate:score_74.0=37, blocked_ai_score:score_58.0=11`
- AI terminal reasons: `ai_terminal:first_ai_wait_big_bite_not_confirmed=412, ai_terminal:blocked_ai_score_below_buy_score_threshold=149`
- latency blockers: `latency_block:latency_state_danger=734`
- price guards: `entry_ai_price_canary_fallback:invalid_price=154, scale_in_price_guard_block:micro_vwap_bp>60.0=39, scale_in_price_guard_block:micro_vwap_bp<-5.0=11, entry_ai_price_canary_fallback:pre_submit_price_guard=4, scale_in_price_guard_block:spread_bps>80.0=2`
- quote refresh: `attempted=44, applied=33, latency_recovered=9, submitted_after_refresh=0`
- quote refresh downstream: `{'armed_expired_before_submit': 3, 'budget_pass_no_submit_event': 2, 'no_downstream_event': 1, 'upstream_block_after_latency_recovery': 3}`

## 금지된 자동변경

- `score_threshold_relaxation`
- `spread_cap_relaxation`
- `fallback_reenable`
- `live_threshold_runtime_mutation`
- `bot_restart`

## 권고 액션

- Auto-route ai_confirmed -> budget_pass -> latency_pass -> order_bundle_submitted drought into postclose workorder/LDM handoff.
- Split root cause into upstream gate, budget pass, latency/pre-submit guard, and broker receipt buckets before tuning thresholds.
- Do not require operator approval for submitted drought surfacing or downstream workorder generation.

## Window Summary

- `5m`: ai=0, budget=7, latency=0, submitted=0, top=`latency_block:latency_state_danger=12, blocked_gatekeeper_reject:전량 회피=4, blocked_zero_qty:-=1`, swing=`blocked_swing_score_vpw:-=9, blocked_swing_gap:-=1`, upstream=`-`, ai_terminal=`-`
- `10m`: ai=0, budget=7, latency=1, submitted=0, top=`latency_block:latency_state_danger=20, blocked_gatekeeper_reject:전량 회피=6, blocked_zero_qty:-=1`, swing=`blocked_swing_score_vpw:-=16, blocked_swing_gap:-=3`, upstream=`-`, ai_terminal=`-`
- `30m`: ai=12, budget=7, latency=1, submitted=0, top=`latency_block:latency_state_danger=32, blocked_liquidity:-=18, first_ai_wait:-=11`, swing=`blocked_swing_score_vpw:-=28, blocked_swing_gap:-=5`, upstream=`first_ai_wait:-=11, blocked_ai_score:ai_score_50_buy_hold_override=6, wait65_79_ev_candidate:score_65.0=1`, ai_terminal=`ai_terminal:first_ai_wait_big_bite_not_confirmed=11, ai_terminal:blocked_ai_score_below_buy_score_threshold=1`
