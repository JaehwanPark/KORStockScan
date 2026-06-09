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

- as_of: `2026-06-09T13:20:06`
- baseline_date: `2026-06-08`
- ai_confirmed unique: `197`
- budget_pass unique: `63`
- latency_pass unique: `15`
- submitted unique: `4`
- holding_started unique: `1`
- budget/ai unique: `32.0%` (baseline `102.2`)
- submitted/ai unique: `2.0%` (baseline `19.6`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `latency_block:latency_state_danger=8459, blocked_swing_gap:-=6593, blocked_gatekeeper_reject:전량 회피=3844, blocked_strength_momentum:below_window_buy_value=3662, blocked_swing_score_vpw:-=2432`
- upstream blockers: `blocked_ai_score:score_62.0=802, blocked_ai_score:ai_score_50_buy_hold_override=424, first_ai_wait:-=286, blocked_ai_score:score_60.0=152, blocked_ai_score:score_58.0=146`
- latency blockers: `latency_block:latency_state_danger=8459`
- price guards: `entry_ai_price_canary_fallback:invalid_price=143, entry_ai_price_canary_fallback:pre_submit_price_guard=11, entry_ai_price_canary_fallback:above_best_ask=2, entry_ai_price_canary_fallback:skip_low_confidence=2, entry_ai_price_canary_skip_order:orderbook_micro is bearish with strong negative OFI and high top_depth_ratio indicating downward pressure=1`

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

- `5m`: ai=26, budget=5, latency=0, submitted=0, top=`blocked_strength_momentum:insufficient_history=255, latency_block:latency_state_danger=230, blocked_swing_gap:-=173`, upstream=`blocked_ai_score:score_62.0=13, first_ai_wait:-=11, blocked_ai_score:ai_score_50_buy_hold_override=9`
- `10m`: ai=44, budget=6, latency=0, submitted=0, top=`latency_block:latency_state_danger=467, blocked_strength_momentum:insufficient_history=349, blocked_swing_gap:-=341`, upstream=`first_ai_wait:-=33, blocked_ai_score:score_62.0=32, blocked_ai_score:ai_score_50_buy_hold_override=16`
- `30m`: ai=88, budget=13, latency=3, submitted=0, top=`latency_block:latency_state_danger=1259, blocked_swing_gap:-=1105, blocked_strength_momentum:insufficient_history=725`, upstream=`blocked_ai_score:score_62.0=97, first_ai_wait:-=93, blocked_ai_score:ai_score_50_buy_hold_override=46`
