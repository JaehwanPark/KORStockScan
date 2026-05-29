# BUY Funnel Sentinel 2026-05-29

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

- as_of: `2026-05-29T15:05:06`
- baseline_date: `2026-05-28`
- ai_confirmed unique: `104`
- budget_pass unique: `58`
- latency_pass unique: `22`
- submitted unique: `6`
- holding_started unique: `3`
- budget/ai unique: `55.8%` (baseline `51.9`)
- submitted/ai unique: `5.8%` (baseline `1.9`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:insufficient_history=15635, latency_block:latency_state_danger=14066, blocked_overbought:-=11867, blocked_swing_score_vpw:-=10288, blocked_strength_momentum:below_window_buy_value=5714`
- upstream blockers: `blocked_ai_score:score_62.0=549, blocked_ai_score:ai_score_50_buy_hold_override=444, first_ai_wait:-=269, blocked_ai_score:score_60.0=169, blocked_ai_score:score_58.0=97`
- latency blockers: `latency_block:latency_state_danger=14066`
- price guards: `entry_ai_price_canary_fallback:low_confidence=115, entry_ai_price_canary_fallback:pre_submit_price_guard=19, entry_ai_price_canary_fallback:invalid_price=12, entry_ai_price_canary_fallback:above_best_ask=5, scale_in_price_guard_block:micro_vwap_bp>60.0=4`

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

- `5m`: ai=0, budget=2, latency=0, submitted=0, top=`latency_block:latency_state_danger=276, blocked_swing_gap:-=274, blocked_gatekeeper_reject:눌림 대기=203`, upstream=`-`
- `10m`: ai=10, budget=3, latency=1, submitted=0, top=`blocked_strength_momentum:insufficient_history=1518, blocked_overbought:-=727, latency_block:latency_state_danger=485`, upstream=`blocked_ai_score:score_62.0=7, blocked_ai_score:score_63.0=2, wait65_79_ev_candidate:score_65.0=1`
- `30m`: ai=15, budget=4, latency=2, submitted=1, top=`blocked_strength_momentum:insufficient_history=9245, blocked_overbought:-=4347, latency_block:latency_state_danger=1530`, upstream=`blocked_ai_score:score_62.0=26, first_ai_wait:-=10, blocked_ai_score:score_58.0=9`
