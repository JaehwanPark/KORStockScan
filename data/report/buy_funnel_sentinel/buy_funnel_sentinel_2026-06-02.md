# BUY Funnel Sentinel 2026-06-02

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

- as_of: `2026-06-02T15:20:06`
- baseline_date: `2026-06-01`
- ai_confirmed unique: `147`
- budget_pass unique: `86`
- latency_pass unique: `40`
- submitted unique: `20`
- holding_started unique: `17`
- budget/ai unique: `58.5%` (baseline `56.8`)
- submitted/ai unique: `13.6%` (baseline `11.6`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `latency_block:latency_state_danger=23889, blocked_swing_score_vpw:-=15188, blocked_overbought:-=10705, blocked_strength_momentum:insufficient_history=9443, blocked_strength_momentum:below_strength_base=7278`
- upstream blockers: `blocked_ai_score:score_62.0=1012, blocked_ai_score:ai_score_50_buy_hold_override=449, first_ai_wait:-=181, blocked_ai_score:score_60.0=173, blocked_ai_score:score_58.0=171`
- latency blockers: `latency_block:latency_state_danger=23889`
- price guards: `entry_ai_price_canary_fallback:invalid_price=204, entry_ai_price_canary_fallback:pre_submit_price_guard=54, scale_in_price_guard_block:micro_vwap_bp>60.0=33, entry_ai_price_canary_fallback:above_best_ask=10, entry_ai_price_canary_skip_order:orderbook_micro is bearish with negative OFI and high top_depth_ratio, indicating unfavorable entry conditions=1`

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

- `5m`: ai=0, budget=5, latency=5, submitted=0, top=`latency_block:latency_state_danger=822, blocked_swing_score_vpw:-=495, blocked_gatekeeper_reject:전량 회피=166`, upstream=`-`
- `10m`: ai=0, budget=7, latency=7, submitted=0, top=`latency_block:latency_state_danger=1475, blocked_swing_score_vpw:-=927, blocked_gatekeeper_reject:전량 회피=281`, upstream=`-`
- `30m`: ai=21, budget=10, latency=8, submitted=0, top=`latency_block:latency_state_danger=2883, blocked_swing_score_vpw:-=1854, blocked_gatekeeper_reject:눌림 대기=515`, upstream=`blocked_ai_score:score_62.0=18, blocked_ai_score:ai_score_50_buy_hold_override=17, blocked_ai_score:score_58.0=5`
