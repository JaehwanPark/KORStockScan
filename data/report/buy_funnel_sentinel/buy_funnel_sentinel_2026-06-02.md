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

- as_of: `2026-06-02T11:00:03`
- baseline_date: `2026-06-01`
- ai_confirmed unique: `102`
- budget_pass unique: `50`
- latency_pass unique: `15`
- submitted unique: `4`
- holding_started unique: `4`
- budget/ai unique: `49.0%` (baseline `46.2`)
- submitted/ai unique: `3.9%` (baseline `5.8`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `latency_block:latency_state_danger=5238, blocked_swing_score_vpw:-=3201, blocked_strength_momentum:below_strength_base=2222, blocked_overbought:-=2124, blocked_strength_momentum:insufficient_history=1582`
- upstream blockers: `blocked_ai_score:score_62.0=368, blocked_ai_score:ai_score_50_buy_hold_override=127, first_ai_wait:-=100, blocked_ai_score:score_60.0=64, blocked_ai_score:score_58.0=63`
- latency blockers: `latency_block:latency_state_danger=5238`
- price guards: `entry_ai_price_canary_fallback:invalid_price=108, entry_ai_price_canary_fallback:pre_submit_price_guard=29, scale_in_price_guard_block:micro_vwap_bp>60.0=14, entry_ai_price_canary_fallback:above_best_ask=8, entry_ai_price_canary_skip_order:orderbook_micro is bearish with negative OFI and high top_depth_ratio, indicating unfavorable entry conditions=1`

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

- `5m`: ai=19, budget=7, latency=1, submitted=0, top=`latency_block:latency_state_danger=225, blocked_swing_score_vpw:-=124, blocked_overbought:-=122`, upstream=`blocked_ai_score:score_62.0=12, blocked_ai_score:ai_score_50_buy_hold_override=10, blocked_ai_score:score_60.0=3`
- `10m`: ai=27, budget=10, latency=2, submitted=0, top=`latency_block:latency_state_danger=543, blocked_swing_score_vpw:-=309, blocked_overbought:-=237`, upstream=`blocked_ai_score:score_62.0=28, blocked_ai_score:ai_score_50_buy_hold_override=18, blocked_ai_score:score_58.0=7`
- `30m`: ai=45, budget=19, latency=5, submitted=2, top=`latency_block:latency_state_danger=1912, blocked_swing_score_vpw:-=1158, blocked_overbought:-=810`, upstream=`blocked_ai_score:score_62.0=80, blocked_ai_score:ai_score_50_buy_hold_override=34, blocked_ai_score:score_58.0=25`
