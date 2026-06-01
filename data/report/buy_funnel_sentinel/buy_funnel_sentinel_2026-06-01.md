# BUY Funnel Sentinel 2026-06-01

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

- as_of: `2026-06-01T15:20:06`
- baseline_date: `2026-05-29`
- ai_confirmed unique: `146`
- budget_pass unique: `83`
- latency_pass unique: `32`
- submitted unique: `17`
- holding_started unique: `12`
- budget/ai unique: `56.8%` (baseline `55.8`)
- submitted/ai unique: `11.6%` (baseline `5.8`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `latency_block:latency_state_danger=25212, blocked_swing_score_vpw:-=18679, blocked_overbought:-=12671, blocked_strength_momentum:below_strength_base=8046, blocked_strength_momentum:insufficient_history=7710`
- upstream blockers: `blocked_ai_score:score_62.0=1167, blocked_ai_score:ai_score_50_buy_hold_override=434, blocked_ai_score:score_60.0=204, first_ai_wait:-=174, blocked_ai_score:score_58.0=133`
- latency blockers: `latency_block:latency_state_danger=25212`
- price guards: `entry_ai_price_canary_fallback:invalid_price=172, entry_ai_price_canary_fallback:pre_submit_price_guard=38, entry_ai_price_canary_fallback:above_best_ask=7, scale_in_price_guard_block:micro_vwap_bp>60.0=5, entry_ai_price_canary_fallback:skip_low_confidence=3`

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

- `5m`: ai=0, budget=4, latency=2, submitted=0, top=`latency_block:latency_state_danger=750, blocked_swing_score_vpw:-=748, blocked_swing_gap:-=34`, upstream=`-`
- `10m`: ai=0, budget=4, latency=2, submitted=0, top=`latency_block:latency_state_danger=1446, blocked_swing_score_vpw:-=1427, blocked_swing_gap:-=81`, upstream=`-`
- `30m`: ai=25, budget=9, latency=2, submitted=0, top=`latency_block:latency_state_danger=2877, blocked_swing_score_vpw:-=2437, blocked_gatekeeper_reject:전량 회피=354`, upstream=`blocked_ai_score:score_62.0=38, blocked_ai_score:ai_score_50_buy_hold_override=12, blocked_ai_score:score_60.0=2`
