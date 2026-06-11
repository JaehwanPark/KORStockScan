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

- as_of: `2026-06-11T12:35:07`
- baseline_date: `2026-06-10`
- ai_confirmed unique: `122`
- budget_pass unique: `102`
- latency_pass unique: `33`
- submitted unique: `14`
- holding_started unique: `2`
- budget/ai unique: `83.6%` (baseline `100.8`)
- submitted/ai unique: `11.5%` (baseline `12.7`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `latency_block:latency_state_danger=6656, blocked_swing_score_vpw:-=4267, blocked_strength_momentum:below_window_buy_value=1727, blocked_gatekeeper_reject:전량 회피=1379, blocked_vpw:-=1127`
- upstream blockers: `blocked_ai_score:score_62.0=379, blocked_ai_score:ai_score_50_buy_hold_override=300, first_ai_wait:-=182, blocked_ai_score:score_58.0=124, blocked_ai_score:score_60.0=96`
- latency blockers: `latency_block:latency_state_danger=6656`
- price guards: `entry_ai_price_canary_fallback:invalid_price=102, entry_ai_price_canary_fallback:pre_submit_price_guard=50, entry_ai_price_canary_fallback:low_confidence=1, entry_ai_price_canary_fallback:skip_low_confidence=1`

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

- `5m`: ai=25, budget=37, latency=3, submitted=2, top=`latency_block:latency_state_danger=264, blocked_swing_score_vpw:-=133, blocked_strength_momentum:below_window_buy_value=96`, upstream=`blocked_ai_score:score_58.0=6, blocked_ai_score:score_62.0=6, blocked_ai_score:ai_score_50_buy_hold_override=3`
- `10m`: ai=36, budget=46, latency=5, submitted=4, top=`latency_block:latency_state_danger=511, blocked_swing_score_vpw:-=256, blocked_strength_momentum:below_window_buy_value=180`, upstream=`blocked_ai_score:score_62.0=13, blocked_ai_score:score_58.0=8, blocked_ai_score:ai_score_50_buy_hold_override=7`
- `30m`: ai=48, budget=62, latency=13, submitted=9, top=`latency_block:latency_state_danger=1206, blocked_swing_score_vpw:-=612, blocked_strength_momentum:below_window_buy_value=403`, upstream=`blocked_ai_score:score_62.0=37, blocked_ai_score:ai_score_50_buy_hold_override=29, blocked_ai_score:score_58.0=14`
