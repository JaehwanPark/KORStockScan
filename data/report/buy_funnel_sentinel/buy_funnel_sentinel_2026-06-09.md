# BUY Funnel Sentinel 2026-06-09

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

- as_of: `2026-06-09T11:00:06`
- baseline_date: `2026-06-08`
- ai_confirmed unique: `161`
- budget_pass unique: `46`
- latency_pass unique: `8`
- submitted unique: `0`
- holding_started unique: `0`
- budget/ai unique: `28.6%` (baseline `103.8`)
- submitted/ai unique: `0.0%` (baseline `9.0`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `latency_block:latency_state_danger=2702, blocked_swing_gap:-=1279, blocked_strength_momentum:below_window_buy_value=1261, blocked_gatekeeper_reject:전량 회피=1225, blocked_swing_score_vpw:-=704`
- upstream blockers: `blocked_ai_score:score_62.0=399, blocked_ai_score:ai_score_50_buy_hold_override=179, first_ai_wait:-=160, blocked_ai_score:score_60.0=78, blocked_ai_score:score_58.0=61`
- latency blockers: `latency_block:latency_state_danger=2702`
- price guards: `entry_ai_price_canary_fallback:invalid_price=132, entry_ai_price_canary_fallback:pre_submit_price_guard=8, entry_ai_price_canary_fallback:above_best_ask=2`

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

- `5m`: ai=26, budget=5, latency=0, submitted=0, top=`latency_block:latency_state_danger=201, blocked_swing_gap:-=189, blocked_gatekeeper_reject:전량 회피=96`, upstream=`blocked_ai_score:score_62.0=15, blocked_ai_score:ai_score_50_buy_hold_override=13, blocked_ai_score:score_60.0=5`
- `10m`: ai=40, budget=9, latency=0, submitted=0, top=`latency_block:latency_state_danger=400, blocked_swing_gap:-=340, blocked_gatekeeper_reject:전량 회피=194`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=30, blocked_ai_score:score_62.0=26, blocked_ai_score:score_60.0=6`
- `30m`: ai=75, budget=16, latency=2, submitted=0, top=`latency_block:latency_state_danger=961, blocked_swing_gap:-=714, blocked_gatekeeper_reject:전량 회피=452`, upstream=`blocked_ai_score:score_62.0=96, blocked_ai_score:ai_score_50_buy_hold_override=62, blocked_ai_score:score_58.0=21`
