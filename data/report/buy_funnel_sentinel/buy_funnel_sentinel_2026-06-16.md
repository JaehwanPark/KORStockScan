# BUY Funnel Sentinel 2026-06-16

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

- as_of: `2026-06-16T15:20:09`
- baseline_date: `2026-06-15`
- ai_confirmed unique: `225`
- budget_pass unique: `85`
- latency_pass unique: `38`
- submitted unique: `3`
- holding_started unique: `0`
- budget/ai unique: `37.8%` (baseline `42.7`)
- submitted/ai unique: `1.3%` (baseline `5.3`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `latency_block:latency_state_danger=20976, blocked_gatekeeper_reject:눌림 대기=5935, blocked_gatekeeper_reject:전량 회피=3476, blocked_strength_momentum:below_window_buy_value=3362, blocked_strength_momentum:below_strength_base=2339`
- swing blockers: `blocked_swing_score_vpw:-=11275, blocked_swing_gap:-=2169`
- upstream blockers: `blocked_ai_score:score_62.0=904, blocked_ai_score:ai_score_50_buy_hold_override=848, first_ai_wait:-=451, blocked_ai_score:score_60.0=225, blocked_ai_score:score_58.0=106`
- latency blockers: `latency_block:latency_state_danger=20976`
- price guards: `entry_ai_price_canary_fallback:invalid_price=172, scale_in_price_guard_block:micro_vwap_bp>60.0=93, scale_in_price_guard_block:invalid_spread=39, scale_in_price_guard_block:micro_vwap_bp<-5.0=31, entry_ai_price_canary_fallback:pre_submit_price_guard=12`

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

- `5m`: ai=0, budget=13, latency=2, submitted=0, top=`latency_block:latency_state_danger=940, blocked_gatekeeper_reject:눌림 대기=321, blocked_gatekeeper_reject:전량 회피=194`, swing=`blocked_swing_score_vpw:-=427, blocked_swing_gap:-=229`, upstream=`-`
- `10m`: ai=0, budget=13, latency=2, submitted=0, top=`latency_block:latency_state_danger=1930, blocked_gatekeeper_reject:눌림 대기=723, blocked_gatekeeper_reject:전량 회피=325`, swing=`blocked_swing_score_vpw:-=884, blocked_swing_gap:-=477`, upstream=`-`
- `30m`: ai=33, budget=14, latency=2, submitted=0, top=`latency_block:latency_state_danger=3258, blocked_gatekeeper_reject:눌림 대기=1215, blocked_gatekeeper_reject:전량 회피=538`, swing=`blocked_swing_score_vpw:-=1508, blocked_swing_gap:-=733`, upstream=`blocked_ai_score:score_62.0=29, blocked_ai_score:ai_score_50_buy_hold_override=23, blocked_ai_score:score_60.0=4`
