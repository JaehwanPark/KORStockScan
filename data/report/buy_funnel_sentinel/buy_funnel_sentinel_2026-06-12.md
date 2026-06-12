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
- submit_contract_weak_matches: `BROKER_RECEIPT, BUDGET_PASS_COLLAPSE, FILL_QUALITY, LATENCY_PRE_SUBMIT, PRICE_REVALIDATION, SIM_REAL_AUTHORITY, TELEGRAM_POST_SUBMIT_ONLY, UPSTREAM_GATE`

## 근거

- as_of: `2026-06-12T17:35:59`
- baseline_date: `2026-06-11`
- ai_confirmed unique: `205`
- budget_pass unique: `171`
- latency_pass unique: `66`
- submitted unique: `17`
- holding_started unique: `2`
- budget/ai unique: `83.4%` (baseline `89.3`)
- submitted/ai unique: `8.3%` (baseline `12.1`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `latency_block:latency_state_danger=12179, blocked_strength_momentum:below_window_buy_value=4617, blocked_gatekeeper_reject:전량 회피=3156, blocked_gatekeeper_reject:눌림 대기=2037, blocked_overbought:-=2022`
- swing blockers: `blocked_swing_score_vpw:-=5198, blocked_swing_gap:-=2761`
- upstream blockers: `blocked_ai_score:ai_score_50_buy_hold_override=503, first_ai_wait:-=379, blocked_ai_score:score_58.0=266, blocked_ai_score:score_62.0=239, blocked_ai_score:score_60.0=128`
- latency blockers: `latency_block:latency_state_danger=12179`
- price guards: `entry_ai_price_canary_fallback:invalid_price=131, entry_ai_price_canary_fallback:pre_submit_price_guard=84, scale_in_price_guard_block:micro_vwap_bp>60.0=36, scale_in_price_guard_block:micro_vwap_bp<-5.0=34, scale_in_price_guard_block:invalid_spread=5`

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

- `5m`: ai=0, budget=0, latency=0, submitted=0, top=`-`, swing=`-`, upstream=`-`
- `10m`: ai=0, budget=0, latency=0, submitted=0, top=`-`, swing=`-`, upstream=`-`
- `30m`: ai=0, budget=0, latency=0, submitted=0, top=`-`, swing=`-`, upstream=`-`
