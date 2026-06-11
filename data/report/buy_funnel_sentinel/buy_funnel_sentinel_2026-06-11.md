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

- as_of: `2026-06-11T15:20:07`
- baseline_date: `2026-06-10`
- ai_confirmed unique: `140`
- budget_pass unique: `125`
- latency_pass unique: `37`
- submitted unique: `17`
- holding_started unique: `2`
- budget/ai unique: `89.3%` (baseline `101.5`)
- submitted/ai unique: `12.1%` (baseline `19.7`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `latency_block:latency_state_danger=10026, blocked_swing_score_vpw:-=6008, blocked_strength_momentum:below_window_buy_value=2786, blocked_gatekeeper_reject:전량 회피=2246, blocked_vpw:-=1660`
- upstream blockers: `blocked_ai_score:ai_score_50_buy_hold_override=539, blocked_ai_score:score_62.0=473, first_ai_wait:-=235, blocked_ai_score:score_58.0=183, blocked_ai_score:score_60.0=125`
- latency blockers: `latency_block:latency_state_danger=10026`
- price guards: `entry_ai_price_canary_fallback:invalid_price=102, entry_ai_price_canary_fallback:pre_submit_price_guard=77, entry_ai_price_canary_fallback:low_confidence=1, entry_ai_price_canary_fallback:skip_low_confidence=1, scale_in_price_guard_block:micro_vwap_bp>60.0=1`

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

- `5m`: ai=0, budget=22, latency=0, submitted=0, top=`latency_block:latency_state_danger=508, blocked_swing_score_vpw:-=316, blocked_gatekeeper_reject:전량 회피=149`, upstream=`-`
- `10m`: ai=0, budget=24, latency=1, submitted=0, top=`latency_block:latency_state_danger=691, blocked_swing_score_vpw:-=428, blocked_gatekeeper_reject:전량 회피=203`, upstream=`-`
- `30m`: ai=25, budget=41, latency=2, submitted=1, top=`latency_block:latency_state_danger=915, blocked_swing_score_vpw:-=550, blocked_gatekeeper_reject:전량 회피=271`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=21, blocked_ai_score:score_58.0=5, blocked_ai_score:score_62.0=4`
