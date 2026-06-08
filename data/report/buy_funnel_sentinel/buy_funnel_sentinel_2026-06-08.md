# BUY Funnel Sentinel 2026-06-08

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

- as_of: `2026-06-08T10:15:09`
- baseline_date: `2026-06-05`
- ai_confirmed unique: `72`
- budget_pass unique: `71`
- latency_pass unique: `34`
- submitted unique: `4`
- holding_started unique: `2`
- budget/ai unique: `98.6%` (baseline `17.5`)
- submitted/ai unique: `5.6%` (baseline `0.0`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `latency_block:latency_state_danger=4149, blocked_strength_momentum:below_window_buy_value=2503, blocked_gatekeeper_reject:전량 회피=1608, blocked_swing_score_vpw:-=1440, blocked_strength_momentum:below_buy_ratio=1246`
- upstream blockers: `blocked_ai_score:ai_score_50_buy_hold_override=84, blocked_ai_score:score_62.0=77, first_ai_wait:-=72, blocked_ai_score:score_58.0=28, blocked_ai_score:score_60.0=13`
- latency blockers: `latency_block:latency_state_danger=4149`
- price guards: `entry_ai_price_canary_fallback:invalid_price=33, entry_ai_price_canary_fallback:pre_submit_price_guard=30, entry_ai_price_canary_skip_order:orderbook_micro is bearish with negative ofi and weak bid-side depth=1`

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

- `5m`: ai=14, budget=18, latency=4, submitted=2, top=`latency_block:latency_state_danger=153, blocked_strength_momentum:below_window_buy_value=83, blocked_gatekeeper_reject:전량 회피=60`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=10, blocked_ai_score:score_62.0=4, first_ai_wait:-=3`
- `10m`: ai=19, budget=23, latency=6, submitted=3, top=`latency_block:latency_state_danger=290, blocked_strength_momentum:below_window_buy_value=170, blocked_gatekeeper_reject:전량 회피=107`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=21, blocked_ai_score:score_62.0=8, blocked_ai_score:score_58.0=5`
- `30m`: ai=29, budget=29, latency=11, submitted=4, top=`blocked_strength_momentum:below_window_buy_value=2006, latency_block:latency_state_danger=1839, blocked_strength_momentum:below_buy_ratio=1092`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=41, blocked_ai_score:score_62.0=24, blocked_ai_score:score_58.0=7`
