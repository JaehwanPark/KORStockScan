# BUY Funnel Sentinel 2026-06-05

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

- as_of: `2026-06-05T15:20:10`
- baseline_date: `2026-06-04`
- ai_confirmed unique: `105`
- budget_pass unique: `19`
- latency_pass unique: `11`
- submitted unique: `1`
- holding_started unique: `1`
- budget/ai unique: `18.1%` (baseline `41.0`)
- submitted/ai unique: `1.0%` (baseline `2.6`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `latency_block:latency_state_danger=24790, blocked_swing_score_vpw:-=22949, blocked_strength_momentum:insufficient_history=5568, blocked_strength_momentum:below_strength_base=5532, blocked_swing_gap:-=4850`
- upstream blockers: `blocked_ai_score:score_60.0=590, blocked_ai_score:ai_score_50_buy_hold_override=461, blocked_ai_score:score_62.0=360, blocked_ai_score:score_58.0=291, blocked_ai_score:score_54.0=162`
- latency blockers: `latency_block:latency_state_danger=24790`
- price guards: `entry_ai_price_canary_fallback:invalid_price=133, entry_ai_price_canary_fallback:skip_low_confidence=6, entry_ai_price_canary_skip_order:orderbook_micro is bearish with negative OFI and high top_depth_ratio indicating downward pressure=2, entry_ai_price_canary_fallback:pre_submit_price_guard=2, entry_ai_price_canary_fallback:above_best_ask=2`

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

- `5m`: ai=0, budget=4, latency=3, submitted=0, top=`latency_block:latency_state_danger=717, blocked_swing_score_vpw:-=714, blocked_swing_gap:-=178`, upstream=`-`
- `10m`: ai=0, budget=4, latency=3, submitted=0, top=`blocked_swing_score_vpw:-=1414, latency_block:latency_state_danger=1413, blocked_swing_gap:-=353`, upstream=`-`
- `30m`: ai=25, budget=4, latency=3, submitted=0, top=`blocked_swing_score_vpw:-=2720, latency_block:latency_state_danger=2709, blocked_swing_gap:-=679`, upstream=`blocked_ai_score:score_60.0=19, blocked_ai_score:ai_score_50_buy_hold_override=10, blocked_ai_score:score_58.0=7`
