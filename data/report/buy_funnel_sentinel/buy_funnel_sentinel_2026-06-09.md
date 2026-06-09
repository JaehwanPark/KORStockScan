# BUY Funnel Sentinel 2026-06-09

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

- as_of: `2026-06-09T15:20:08`
- baseline_date: `2026-06-08`
- ai_confirmed unique: `219`
- budget_pass unique: `76`
- latency_pass unique: `19`
- submitted unique: `6`
- holding_started unique: `1`
- budget/ai unique: `34.7%` (baseline `100.9`)
- submitted/ai unique: `2.7%` (baseline `25.7`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `latency_block:latency_state_danger=14036, blocked_swing_gap:-=11049, blocked_strength_momentum:below_window_buy_value=5410, blocked_gatekeeper_reject:전량 회피=5407, blocked_swing_score_vpw:-=4712`
- upstream blockers: `blocked_ai_score:score_62.0=1116, blocked_ai_score:ai_score_50_buy_hold_override=613, first_ai_wait:-=339, blocked_ai_score:score_60.0=211, blocked_ai_score:score_58.0=201`
- latency blockers: `latency_block:latency_state_danger=14036`
- price guards: `entry_ai_price_canary_fallback:invalid_price=166, entry_ai_price_canary_fallback:pre_submit_price_guard=14, entry_ai_price_canary_fallback:above_best_ask=2, entry_ai_price_canary_fallback:skip_low_confidence=2, entry_ai_price_canary_skip_order:orderbook_micro is bearish with strong negative OFI and high top_depth_ratio indicating downward pressure=1`

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

- `5m`: ai=0, budget=4, latency=1, submitted=0, top=`latency_block:latency_state_danger=487, blocked_swing_gap:-=366, blocked_swing_score_vpw:-=244`, upstream=`-`
- `10m`: ai=0, budget=4, latency=1, submitted=0, top=`latency_block:latency_state_danger=1070, blocked_swing_gap:-=804, blocked_swing_score_vpw:-=536`, upstream=`-`
- `30m`: ai=36, budget=9, latency=1, submitted=0, top=`latency_block:latency_state_danger=2000, blocked_swing_gap:-=1466, blocked_swing_score_vpw:-=977`, upstream=`blocked_ai_score:score_62.0=28, blocked_ai_score:ai_score_50_buy_hold_override=25, blocked_ai_score:score_60.0=5`
