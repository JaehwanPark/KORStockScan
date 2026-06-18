# BUY Funnel Sentinel 2026-06-18

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

- as_of: `2026-06-18T13:00:07`
- baseline_date: `2026-06-17`
- ai_confirmed unique: `191`
- budget_pass unique: `74`
- latency_pass unique: `55`
- submitted unique: `11`
- holding_started unique: `5`
- budget/ai unique: `38.7%` (baseline `21.5`)
- submitted/ai unique: `5.8%` (baseline `1.4`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:insufficient_history=5629, blocked_strength_momentum:below_strength_base=3926, latency_block:latency_state_danger=3184, blocked_strength_momentum:below_window_buy_value=2769, blocked_vpw:-=1803`
- swing blockers: `blocked_swing_score_vpw:-=2452, blocked_swing_gap:-=7`
- upstream blockers: `blocked_ai_score:score_62.0=684, first_ai_wait:-=582, blocked_ai_score:ai_score_50_buy_hold_override=566, blocked_ai_score:score_58.0=104, blocked_ai_score:score_60.0=91`
- latency blockers: `latency_block:latency_state_danger=3184`
- price guards: `entry_ai_price_canary_fallback:invalid_price=168, entry_ai_price_canary_fallback:pre_submit_price_guard=15, scale_in_price_guard_block:spread_bps>80.0=1, entry_ai_price_canary_fallback:skip_low_confidence=1, entry_ai_price_canary_skip_order:orderbook_micro is ready and micro_state is bearish, indicating unfavorable entry conditions=1`
- quote refresh: `attempted=74, applied=72, latency_recovered=33, submitted_after_refresh=4`
- quote refresh downstream: `{'armed_expired_before_submit': 4, 'budget_pass_no_submit_event': 22, 'order_bundle_submitted': 4, 'upstream_block_after_latency_recovery': 3}`

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

- `5m`: ai=9, budget=19, latency=6, submitted=0, top=`blocked_strength_momentum:below_strength_base=30, blocked_strength_momentum:below_window_buy_value=28, blocked_strength_momentum:insufficient_history=27`, swing=`blocked_swing_score_vpw:-=29, blocked_swing_gap:-=1`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=20, first_ai_wait:-=9, blocked_ai_score:score_58.0=1`
- `10m`: ai=34, budget=23, latency=16, submitted=1, top=`blocked_strength_momentum:insufficient_history=213, latency_block:latency_state_danger=141, blocked_strength_momentum:below_strength_base=114`, swing=`blocked_swing_score_vpw:-=115, blocked_swing_gap:-=1`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=36, first_ai_wait:-=31, blocked_ai_score:score_62.0=21`
- `30m`: ai=74, budget=35, latency=25, submitted=5, top=`blocked_strength_momentum:insufficient_history=1319, blocked_strength_momentum:below_strength_base=777, blocked_strength_momentum:below_window_buy_value=470`, swing=`blocked_swing_score_vpw:-=117, blocked_swing_gap:-=1`, upstream=`blocked_ai_score:score_62.0=82, blocked_ai_score:ai_score_50_buy_hold_override=68, first_ai_wait:-=55`
