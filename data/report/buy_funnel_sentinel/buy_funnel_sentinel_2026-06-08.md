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

- as_of: `2026-06-08T10:25:07`
- baseline_date: `2026-06-05`
- ai_confirmed unique: `73`
- budget_pass unique: `71`
- latency_pass unique: `34`
- submitted unique: `5`
- holding_started unique: `3`
- budget/ai unique: `97.3%` (baseline `17.2`)
- submitted/ai unique: `6.8%` (baseline `0.0`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `latency_block:latency_state_danger=4437, blocked_strength_momentum:below_window_buy_value=2687, blocked_gatekeeper_reject:전량 회피=1712, blocked_swing_score_vpw:-=1521, blocked_strength_momentum:below_buy_ratio=1332`
- upstream blockers: `blocked_ai_score:ai_score_50_buy_hold_override=99, blocked_ai_score:score_62.0=96, first_ai_wait:-=73, blocked_ai_score:score_58.0=32, blocked_ai_score:score_60.0=16`
- latency blockers: `latency_block:latency_state_danger=4437`
- price guards: `entry_ai_price_canary_fallback:invalid_price=33, entry_ai_price_canary_fallback:pre_submit_price_guard=33, entry_ai_price_canary_skip_order:orderbook_micro is bearish with negative ofi and weak bid-side depth=1`

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

- `5m`: ai=13, budget=13, latency=1, submitted=0, top=`latency_block:latency_state_danger=148, blocked_strength_momentum:below_window_buy_value=101, blocked_gatekeeper_reject:전량 회피=56`, upstream=`blocked_ai_score:score_62.0=10, blocked_ai_score:ai_score_50_buy_hold_override=6, blocked_ai_score:score_60.0=2`
- `10m`: ai=18, budget=15, latency=2, submitted=1, top=`latency_block:latency_state_danger=288, blocked_strength_momentum:below_window_buy_value=184, blocked_gatekeeper_reject:전량 회피=103`, upstream=`blocked_ai_score:score_62.0=19, blocked_ai_score:ai_score_50_buy_hold_override=15, blocked_ai_score:score_58.0=4`
- `30m`: ai=29, budget=28, latency=10, submitted=5, top=`latency_block:latency_state_danger=1135, blocked_strength_momentum:below_window_buy_value=897, blocked_strength_momentum:below_buy_ratio=432`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=48, blocked_ai_score:score_62.0=35, blocked_ai_score:score_58.0=11`
