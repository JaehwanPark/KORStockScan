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

- as_of: `2026-06-10T09:20:02`
- baseline_date: `2026-06-09`
- ai_confirmed unique: `39`
- budget_pass unique: `46`
- latency_pass unique: `6`
- submitted unique: `0`
- holding_started unique: `0`
- budget/ai unique: `117.9%` (baseline `18.2`)
- submitted/ai unique: `0.0%` (baseline `0.0`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `latency_block:latency_state_danger=190, blocked_swing_score_vpw:-=82, blocked_gatekeeper_reject:전량 회피=78, blocked_strength_momentum:below_strength_base=63, blocked_vpw:-=49`
- upstream blockers: `first_ai_wait:-=39, blocked_ai_score:ai_score_50_buy_hold_override=17, wait65_79_ev_candidate:score_65.0=4, wait65_79_ev_candidate:score_74.0=4, blocked_ai_score:score_58.0=3`
- latency blockers: `latency_block:latency_state_danger=190`
- price guards: `entry_ai_price_canary_fallback:invalid_price=27, entry_ai_price_canary_fallback:pre_submit_price_guard=4, scale_in_price_guard_block:micro_vwap_bp<-5.0=4`

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

- `5m`: ai=22, budget=33, latency=3, submitted=0, top=`latency_block:latency_state_danger=67, blocked_swing_score_vpw:-=30, blocked_strength_momentum:below_strength_base=25`, upstream=`first_ai_wait:-=10, blocked_ai_score:ai_score_50_buy_hold_override=5, blocked_ai_score:score_58.0=3`
- `10m`: ai=35, budget=42, latency=4, submitted=0, top=`latency_block:latency_state_danger=119, blocked_swing_score_vpw:-=53, blocked_strength_momentum:below_strength_base=50`, upstream=`first_ai_wait:-=30, blocked_ai_score:ai_score_50_buy_hold_override=13, wait65_79_ev_candidate:score_65.0=4`
- `30m`: ai=39, budget=46, latency=6, submitted=0, top=`latency_block:latency_state_danger=190, blocked_swing_score_vpw:-=82, blocked_gatekeeper_reject:전량 회피=78`, upstream=`first_ai_wait:-=39, blocked_ai_score:ai_score_50_buy_hold_override=17, wait65_79_ev_candidate:score_65.0=4`
