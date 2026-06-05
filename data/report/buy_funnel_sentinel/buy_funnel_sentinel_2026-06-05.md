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

- as_of: `2026-06-05T12:20:07`
- baseline_date: `2026-06-04`
- ai_confirmed unique: `97`
- budget_pass unique: `14`
- latency_pass unique: `6`
- submitted unique: `0`
- holding_started unique: `0`
- budget/ai unique: `14.4%` (baseline `0.0`)
- submitted/ai unique: `0.0%` (baseline `0.0`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `latency_block:latency_state_danger=14135, blocked_swing_score_vpw:-=12281, blocked_strength_momentum:below_strength_base=3233, blocked_swing_gap:-=2188, blocked_strength_momentum:below_window_buy_value=2035`
- upstream blockers: `blocked_ai_score:score_60.0=310, blocked_ai_score:ai_score_50_buy_hold_override=275, blocked_ai_score:score_62.0=199, blocked_ai_score:score_58.0=166, first_ai_wait:-=136`
- latency blockers: `latency_block:latency_state_danger=14135`
- price guards: `entry_ai_price_canary_fallback:invalid_price=39, entry_ai_price_canary_fallback:skip_low_confidence=6, entry_ai_price_canary_fallback:pre_submit_price_guard=2, entry_ai_price_canary_skip_order:orderbook_micro indicates bearish state with negative OFI and high top_depth_ratio=1, entry_ai_price_canary_skip_order:orderbook_micro is bearish with negative OFI and high top_depth_ratio indicating downward pressure=1`

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

- `5m`: ai=21, budget=4, latency=0, submitted=0, top=`latency_block:latency_state_danger=296, blocked_swing_score_vpw:-=296, blocked_strength_momentum:insufficient_history=84`, upstream=`blocked_ai_score:score_60.0=11, blocked_ai_score:ai_score_50_buy_hold_override=8, blocked_ai_score:score_62.0=7`
- `10m`: ai=30, budget=5, latency=0, submitted=0, top=`latency_block:latency_state_danger=606, blocked_swing_score_vpw:-=584, blocked_strength_momentum:insufficient_history=214`, upstream=`blocked_ai_score:score_60.0=17, blocked_ai_score:ai_score_50_buy_hold_override=15, blocked_ai_score:score_62.0=12`
- `30m`: ai=46, budget=5, latency=0, submitted=0, top=`latency_block:latency_state_danger=1639, blocked_swing_score_vpw:-=1621, blocked_strength_momentum:insufficient_history=685`, upstream=`blocked_ai_score:score_60.0=47, blocked_ai_score:ai_score_50_buy_hold_override=42, blocked_ai_score:score_62.0=31`
