# BUY Funnel Sentinel 2026-06-10

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

- as_of: `2026-06-10T15:20:09`
- baseline_date: `2026-06-09`
- ai_confirmed unique: `132`
- budget_pass unique: `134`
- latency_pass unique: `69`
- submitted unique: `26`
- holding_started unique: `9`
- budget/ai unique: `101.5%` (baseline `34.7`)
- submitted/ai unique: `19.7%` (baseline `2.7`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `latency_block:latency_state_danger=21663, blocked_swing_score_vpw:-=15224, blocked_strength_momentum:below_strength_base=4031, blocked_strength_momentum:below_window_buy_value=3852, blocked_vpw:-=3029`
- upstream blockers: `blocked_ai_score:ai_score_50_buy_hold_override=680, blocked_ai_score:score_62.0=475, first_ai_wait:-=239, blocked_ai_score:score_58.0=230, blocked_ai_score:score_57.0=100`
- latency blockers: `latency_block:latency_state_danger=21663`
- price guards: `entry_ai_price_canary_fallback:pre_submit_price_guard=149, scale_in_price_guard_block:micro_vwap_bp>60.0=87, scale_in_price_guard_block:micro_vwap_bp<-5.0=52, entry_ai_price_canary_fallback:invalid_price=45, entry_ai_price_canary_fallback:skip_low_confidence=5`

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

- `5m`: ai=0, budget=11, latency=6, submitted=0, top=`latency_block:latency_state_danger=1200, blocked_swing_score_vpw:-=955, blocked_gatekeeper_reject:전량 회피=120`, upstream=`-`
- `10m`: ai=0, budget=11, latency=6, submitted=0, top=`latency_block:latency_state_danger=2276, blocked_swing_score_vpw:-=1820, blocked_gatekeeper_reject:전량 회피=265`, upstream=`-`
- `30m`: ai=15, budget=21, latency=10, submitted=1, top=`latency_block:latency_state_danger=3903, blocked_swing_score_vpw:-=3219, blocked_gatekeeper_reject:전량 회피=325`, upstream=`blocked_ai_score:score_62.0=23, blocked_ai_score:score_57.0=9, blocked_ai_score:ai_score_50_buy_hold_override=8`
