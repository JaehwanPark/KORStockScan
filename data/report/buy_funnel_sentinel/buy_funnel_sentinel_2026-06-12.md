# BUY Funnel Sentinel 2026-06-12

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

- as_of: `2026-06-12T10:55:09`
- baseline_date: `2026-06-11`
- ai_confirmed unique: `146`
- budget_pass unique: `131`
- latency_pass unique: `42`
- submitted unique: `15`
- holding_started unique: `1`
- budget/ai unique: `89.7%` (baseline `49.5`)
- submitted/ai unique: `10.3%` (baseline `0.9`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `latency_block:latency_state_danger=6685, blocked_swing_score_vpw:-=3789, blocked_strength_momentum:below_window_buy_value=2240, blocked_swing_gap:-=1321, blocked_gatekeeper_reject:전량 회피=1318`
- upstream blockers: `first_ai_wait:-=146, blocked_ai_score:ai_score_50_buy_hold_override=115, blocked_ai_score:score_58.0=110, blocked_ai_score:score_62.0=92, blocked_ai_score:score_54.0=55`
- latency blockers: `latency_block:latency_state_danger=6685`
- price guards: `entry_ai_price_canary_fallback:invalid_price=59, entry_ai_price_canary_fallback:pre_submit_price_guard=38, scale_in_price_guard_block:micro_vwap_bp>60.0=17, entry_ai_price_canary_fallback:above_best_ask=3, scale_in_price_guard_block:micro_vwap_bp<-5.0=2`

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

- `5m`: ai=35, budget=43, latency=6, submitted=5, top=`latency_block:latency_state_danger=325, blocked_swing_score_vpw:-=152, blocked_strength_momentum:below_window_buy_value=69`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=6, blocked_ai_score:score_62.0=5, blocked_ai_score:score_58.0=4`
- `10m`: ai=53, budget=50, latency=7, submitted=5, top=`latency_block:latency_state_danger=1257, blocked_swing_score_vpw:-=690, blocked_swing_gap:-=287`, upstream=`blocked_ai_score:score_62.0=17, blocked_ai_score:score_58.0=10, blocked_ai_score:score_60.0=10`
- `30m`: ai=82, budget=83, latency=20, submitted=12, top=`latency_block:latency_state_danger=2718, blocked_swing_score_vpw:-=1434, blocked_strength_momentum:below_window_buy_value=682`, upstream=`blocked_ai_score:score_62.0=41, blocked_ai_score:ai_score_50_buy_hold_override=37, blocked_ai_score:score_58.0=31`
