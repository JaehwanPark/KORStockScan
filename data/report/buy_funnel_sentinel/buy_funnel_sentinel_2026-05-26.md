# BUY Funnel Sentinel 2026-05-26

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

- as_of: `2026-05-26T15:20:07`
- baseline_date: `2026-05-22`
- ai_confirmed unique: `169`
- budget_pass unique: `81`
- latency_pass unique: `37`
- submitted unique: `20`
- holding_started unique: `7`
- budget/ai unique: `47.9%` (baseline `1.3`)
- submitted/ai unique: `11.8%` (baseline `0.0`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_swing_score_vpw:-=138819, blocked_overbought:-=20849, blocked_strength_momentum:below_strength_base=11868, blocked_swing_gap:-=11093, blocked_strength_momentum:insufficient_history=10511`
- upstream blockers: `blocked_ai_score:score_62.0=1247, blocked_ai_score:ai_score_50_buy_hold_override=738, first_ai_wait:-=344, blocked_ai_score:score_60.0=221, blocked_ai_score:score_58.0=167`
- latency blockers: `latency_block:latency_state_danger=2382`
- price guards: `entry_ai_price_canary_fallback:invalid_price=112, entry_ai_price_canary_fallback:low_confidence=21, entry_ai_price_canary_fallback:pre_submit_price_guard=16, scale_in_price_guard_block:micro_vwap_bp>60.0=7, entry_ai_price_canary_fallback:above_best_ask=4`

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

- `5m`: ai=0, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=2844, blocked_swing_gap:-=158, blocked_gatekeeper_reject:눌림 대기=1`, upstream=`-`
- `10m`: ai=0, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=5580, blocked_swing_gap:-=310, blocked_gatekeeper_reject:눌림 대기=1`, upstream=`-`
- `30m`: ai=33, budget=7, latency=3, submitted=1, top=`blocked_swing_score_vpw:-=13645, blocked_overbought:-=972, blocked_strength_momentum:insufficient_history=549`, upstream=`blocked_ai_score:score_62.0=27, blocked_ai_score:ai_score_50_buy_hold_override=17, blocked_ai_score:score_63.0=5`
