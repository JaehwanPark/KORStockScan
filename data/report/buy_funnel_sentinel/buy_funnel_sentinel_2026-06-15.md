# BUY Funnel Sentinel 2026-06-15

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

- as_of: `2026-06-15T15:20:08`
- baseline_date: `2026-06-12`
- ai_confirmed unique: `171`
- budget_pass unique: `73`
- latency_pass unique: `40`
- submitted unique: `9`
- holding_started unique: `0`
- budget/ai unique: `42.7%` (baseline `83.4`)
- submitted/ai unique: `5.3%` (baseline `8.3`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `latency_block:latency_state_danger=16402, blocked_gatekeeper_reject:눌림 대기=8413, blocked_strength_momentum:below_window_buy_value=3995, blocked_strength_momentum:insufficient_history=2443, blocked_strength_momentum:below_strength_base=1890`
- swing blockers: `blocked_swing_gap:-=9193, blocked_swing_score_vpw:-=6082`
- upstream blockers: `blocked_ai_score:ai_score_50_buy_hold_override=853, blocked_ai_score:score_62.0=806, first_ai_wait:-=495, blocked_ai_score:score_58.0=253, blocked_ai_score:score_60.0=166`
- latency blockers: `latency_block:latency_state_danger=16402`
- price guards: `entry_ai_price_canary_fallback:invalid_price=192, scale_in_price_guard_block:micro_vwap_bp>60.0=13, entry_ai_price_canary_fallback:pre_submit_price_guard=9, pre_submit_price_guard_block:ai_tier2_use_defensive|panic_gap_weight=2, entry_ai_price_canary_skip_order:orderbook_micro is bearish with negative OFI and weak execution strength=2`

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

- `5m`: ai=0, budget=11, latency=3, submitted=0, top=`latency_block:latency_state_danger=537, blocked_gatekeeper_reject:눌림 대기=307, blocked_gatekeeper_reject:전량 회피=135`, swing=`blocked_swing_gap:-=232, blocked_swing_score_vpw:-=98`, upstream=`-`
- `10m`: ai=0, budget=11, latency=3, submitted=0, top=`latency_block:latency_state_danger=1120, blocked_gatekeeper_reject:눌림 대기=631, blocked_gatekeeper_reject:전량 회피=288`, swing=`blocked_swing_gap:-=497, blocked_swing_score_vpw:-=204`, upstream=`-`
- `30m`: ai=30, budget=11, latency=4, submitted=0, top=`latency_block:latency_state_danger=1884, blocked_gatekeeper_reject:눌림 대기=1054, blocked_gatekeeper_reject:전량 회피=452`, swing=`blocked_swing_gap:-=817, blocked_swing_score_vpw:-=381`, upstream=`blocked_ai_score:score_62.0=27, blocked_ai_score:ai_score_50_buy_hold_override=25, blocked_ai_score:score_58.0=8`
