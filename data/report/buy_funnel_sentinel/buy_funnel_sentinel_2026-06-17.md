# BUY Funnel Sentinel 2026-06-17

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

- as_of: `2026-06-17T20:02:42`
- baseline_date: `2026-06-16`
- ai_confirmed unique: `333`
- budget_pass unique: `78`
- latency_pass unique: `36`
- submitted unique: `5`
- holding_started unique: `0`
- budget/ai unique: `23.4%` (baseline `37.8`)
- submitted/ai unique: `1.5%` (baseline `1.3`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `latency_block:latency_state_danger=45315, blocked_gatekeeper_reject:눌림 대기=8308, blocked_strength_momentum:insufficient_history=5460, blocked_strength_momentum:below_window_buy_value=4312, blocked_strength_momentum:below_strength_base=3286`
- swing blockers: `blocked_swing_score_vpw:-=35987, blocked_swing_gap:-=2104`
- upstream blockers: `blocked_ai_score:score_62.0=1075, blocked_ai_score:ai_score_50_buy_hold_override=614, first_ai_wait:-=563, blocked_ai_score:score_60.0=185, blocked_ai_score:score_58.0=166`
- latency blockers: `latency_block:latency_state_danger=45315`
- price guards: `scale_in_price_guard_block:micro_vwap_bp>60.0=141, entry_ai_price_canary_fallback:invalid_price=117, scale_in_price_guard_block:spread_bps>80.0=12, scale_in_price_guard_block:micro_vwap_bp<-5.0=7, entry_ai_price_canary_fallback:pre_submit_price_guard=6`
- quote refresh: `attempted=77, applied=66, latency_recovered=21, submitted_after_refresh=4`
- quote refresh downstream: `{'armed_expired_before_submit': 1, 'budget_pass_no_submit_event': 12, 'no_downstream_event': 4, 'order_bundle_submitted': 4}`

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
