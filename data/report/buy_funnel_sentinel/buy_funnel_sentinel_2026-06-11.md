# BUY Funnel Sentinel 2026-06-11

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
- submit_contract_weak_matches: `BROKER_RECEIPT, BUDGET_PASS_COLLAPSE, FILL_QUALITY, LATENCY_PRE_SUBMIT, PRICE_REVALIDATION, SIM_REAL_AUTHORITY, SOURCE_TAXONOMY_LEAKAGE, TELEGRAM_POST_SUBMIT_ONLY, UPSTREAM_GATE`

## 근거

- as_of: `2026-06-11T12:40:27`
- baseline_date: `2026-06-10`
- ai_confirmed unique: `122`
- budget_pass unique: `102`
- latency_pass unique: `33`
- submitted unique: `14`
- holding_started unique: `2`
- budget/ai unique: `83.6%` (baseline `100.8`)
- submitted/ai unique: `11.5%` (baseline `14.3`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `latency_block:latency_state_danger=6815, blocked_swing_score_vpw:-=4356, blocked_strength_momentum:below_window_buy_value=1788, blocked_gatekeeper_reject:전량 회피=1417, blocked_vpw:-=1151`
- upstream blockers: `blocked_ai_score:score_62.0=382, blocked_ai_score:ai_score_50_buy_hold_override=316, first_ai_wait:-=196, blocked_ai_score:score_58.0=125, blocked_ai_score:score_60.0=96`
- latency blockers: `latency_block:latency_state_danger=6815`
- price guards: `entry_ai_price_canary_fallback:invalid_price=102, entry_ai_price_canary_fallback:pre_submit_price_guard=52, entry_ai_price_canary_fallback:low_confidence=1, entry_ai_price_canary_fallback:skip_low_confidence=1`

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

- `5m`: ai=21, budget=42, latency=5, submitted=1, top=`latency_block:latency_state_danger=135, blocked_swing_score_vpw:-=75, blocked_strength_momentum:below_window_buy_value=53`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=16, first_ai_wait:-=14, blocked_ai_score:score_62.0=3`
- `10m`: ai=38, budget=51, latency=8, submitted=3, top=`latency_block:latency_state_danger=399, blocked_swing_score_vpw:-=208, blocked_strength_momentum:below_window_buy_value=148`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=19, first_ai_wait:-=15, blocked_ai_score:score_62.0=9`
- `30m`: ai=50, budget=68, latency=16, submitted=8, top=`latency_block:latency_state_danger=1187, blocked_swing_score_vpw:-=610, blocked_strength_momentum:below_window_buy_value=406`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=37, blocked_ai_score:score_62.0=33, first_ai_wait:-=19`
