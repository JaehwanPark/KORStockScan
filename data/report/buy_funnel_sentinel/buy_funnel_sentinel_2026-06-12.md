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

- as_of: `2026-06-12T11:50:05`
- baseline_date: `2026-06-11`
- ai_confirmed unique: `163`
- budget_pass unique: `143`
- latency_pass unique: `43`
- submitted unique: `15`
- holding_started unique: `1`
- budget/ai unique: `87.7%` (baseline `76.1`)
- submitted/ai unique: `9.2%` (baseline `7.7`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `latency_block:latency_state_danger=7380, blocked_swing_score_vpw:-=3948, blocked_strength_momentum:below_window_buy_value=2673, blocked_swing_gap:-=1595, blocked_gatekeeper_reject:전량 회피=1494`
- upstream blockers: `first_ai_wait:-=213, blocked_ai_score:ai_score_50_buy_hold_override=170, blocked_ai_score:score_58.0=133, blocked_ai_score:score_62.0=130, blocked_ai_score:score_60.0=68`
- latency blockers: `latency_block:latency_state_danger=7380`
- price guards: `entry_ai_price_canary_fallback:invalid_price=78, entry_ai_price_canary_fallback:pre_submit_price_guard=49, scale_in_price_guard_block:micro_vwap_bp>60.0=19, scale_in_price_guard_block:micro_vwap_bp<-5.0=8, entry_ai_price_canary_fallback:above_best_ask=3`

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

- `5m`: ai=25, budget=33, latency=0, submitted=0, top=`latency_block:latency_state_danger=71, blocked_strength_momentum:below_window_buy_value=38, blocked_swing_gap:-=30`, upstream=`blocked_ai_score:score_62.0=8, first_ai_wait:-=2, wait65_79_ev_candidate:score_65.0=2`
- `10m`: ai=34, budget=37, latency=0, submitted=0, top=`latency_block:latency_state_danger=132, blocked_strength_momentum:below_window_buy_value=94, blocked_swing_gap:-=54`, upstream=`blocked_ai_score:score_62.0=12, blocked_ai_score:ai_score_50_buy_hold_override=8, blocked_ai_score:score_58.0=4`
- `30m`: ai=70, budget=62, latency=0, submitted=0, top=`latency_block:latency_state_danger=377, blocked_strength_momentum:below_window_buy_value=237, blocked_swing_gap:-=153`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=31, blocked_ai_score:score_62.0=26, first_ai_wait:-=16`
