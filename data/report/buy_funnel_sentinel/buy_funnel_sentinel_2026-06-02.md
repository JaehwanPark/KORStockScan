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

- as_of: `2026-06-02T12:50:04`
- baseline_date: `2026-06-01`
- ai_confirmed unique: `127`
- budget_pass unique: `62`
- latency_pass unique: `20`
- submitted unique: `10`
- holding_started unique: `10`
- budget/ai unique: `48.8%` (baseline `48.8`)
- submitted/ai unique: `7.9%` (baseline `10.2`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `latency_block:latency_state_danger=13214, blocked_swing_score_vpw:-=8321, blocked_overbought:-=6654, blocked_strength_momentum:insufficient_history=5435, blocked_strength_momentum:below_strength_base=4964`
- upstream blockers: `blocked_ai_score:score_62.0=675, blocked_ai_score:ai_score_50_buy_hold_override=276, first_ai_wait:-=149, blocked_ai_score:score_60.0=122, blocked_ai_score:score_58.0=114`
- latency blockers: `latency_block:latency_state_danger=13214`
- price guards: `entry_ai_price_canary_fallback:invalid_price=162, entry_ai_price_canary_fallback:pre_submit_price_guard=42, scale_in_price_guard_block:micro_vwap_bp>60.0=22, entry_ai_price_canary_fallback:above_best_ask=10, entry_ai_price_canary_skip_order:orderbook_micro is bearish with negative OFI and high top_depth_ratio, indicating unfavorable entry conditions=1`

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

- `5m`: ai=20, budget=10, latency=0, submitted=0, top=`latency_block:latency_state_danger=357, blocked_swing_score_vpw:-=199, blocked_overbought:-=125`, upstream=`blocked_ai_score:score_62.0=13, blocked_ai_score:score_60.0=5, blocked_ai_score:score_58.0=3`
- `10m`: ai=32, budget=11, latency=1, submitted=0, top=`latency_block:latency_state_danger=811, blocked_swing_score_vpw:-=527, blocked_strength_momentum:insufficient_history=384`, upstream=`blocked_ai_score:score_62.0=26, blocked_ai_score:score_60.0=8, blocked_ai_score:score_63.0=6`
- `30m`: ai=46, budget=17, latency=2, submitted=1, top=`latency_block:latency_state_danger=2432, blocked_swing_score_vpw:-=1676, blocked_strength_momentum:insufficient_history=1352`, upstream=`blocked_ai_score:score_62.0=77, blocked_ai_score:ai_score_50_buy_hold_override=31, blocked_ai_score:score_60.0=18`
