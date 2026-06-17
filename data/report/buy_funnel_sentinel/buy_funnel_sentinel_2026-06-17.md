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

- as_of: `2026-06-17T09:45:11`
- baseline_date: `2026-06-16`
- ai_confirmed unique: `154`
- budget_pass unique: `26`
- latency_pass unique: `9`
- submitted unique: `1`
- holding_started unique: `0`
- budget/ai unique: `16.9%` (baseline `37.5`)
- submitted/ai unique: `0.6%` (baseline `1.1`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `latency_block:latency_state_danger=1046, blocked_strength_momentum:below_strength_base=333, blocked_liquidity:-=294, blocked_strength_momentum:below_window_buy_value=286, blocked_vpw:-=261`
- swing blockers: `blocked_swing_score_vpw:-=643, blocked_swing_gap:-=11`
- upstream blockers: `first_ai_wait:-=154, blocked_ai_score:score_62.0=136, blocked_ai_score:ai_score_50_buy_hold_override=65, blocked_ai_score:score_58.0=29, blocked_ai_score:score_64.0=24`
- latency blockers: `latency_block:latency_state_danger=1046`
- price guards: `scale_in_price_guard_block:micro_vwap_bp>60.0=70, entry_ai_price_canary_fallback:invalid_price=60, scale_in_price_guard_block:spread_bps>80.0=4, scale_in_price_guard_block:micro_vwap_bp<-5.0=2`

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

- `5m`: ai=34, budget=12, latency=0, submitted=0, top=`latency_block:latency_state_danger=204, blocked_gatekeeper_reject:눌림 대기=67, blocked_strength_momentum:below_strength_base=58`, swing=`blocked_swing_score_vpw:-=111`, upstream=`blocked_ai_score:score_62.0=20, first_ai_wait:-=10, blocked_ai_score:ai_score_50_buy_hold_override=8`
- `10m`: ai=66, budget=14, latency=1, submitted=1, top=`latency_block:latency_state_danger=333, blocked_strength_momentum:below_strength_base=114, blocked_gatekeeper_reject:눌림 대기=100`, swing=`blocked_swing_score_vpw:-=181`, upstream=`blocked_ai_score:score_62.0=43, first_ai_wait:-=33, blocked_ai_score:ai_score_50_buy_hold_override=20`
- `30m`: ai=141, budget=21, latency=2, submitted=1, top=`latency_block:latency_state_danger=829, blocked_strength_momentum:below_strength_base=304, blocked_strength_momentum:below_window_buy_value=256`, swing=`blocked_swing_score_vpw:-=516, blocked_swing_gap:-=2`, upstream=`first_ai_wait:-=116, blocked_ai_score:score_62.0=114, blocked_ai_score:ai_score_50_buy_hold_override=53`
