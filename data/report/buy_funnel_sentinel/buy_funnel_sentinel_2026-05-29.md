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

- as_of: `2026-05-29T14:40:04`
- baseline_date: `2026-05-28`
- ai_confirmed unique: `103`
- budget_pass unique: `57`
- latency_pass unique: `20`
- submitted unique: `5`
- holding_started unique: `3`
- budget/ai unique: `55.3%` (baseline `51.9`)
- submitted/ai unique: `4.9%` (baseline `1.9`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `latency_block:latency_state_danger=12729, blocked_swing_score_vpw:-=10215, blocked_strength_momentum:insufficient_history=8819, blocked_overbought:-=8506, blocked_strength_momentum:below_window_buy_value=5366`
- upstream blockers: `blocked_ai_score:score_62.0=530, blocked_ai_score:ai_score_50_buy_hold_override=440, first_ai_wait:-=265, blocked_ai_score:score_60.0=161, blocked_ai_score:score_58.0=90`
- latency blockers: `latency_block:latency_state_danger=12729`
- price guards: `entry_ai_price_canary_fallback:low_confidence=115, entry_ai_price_canary_fallback:pre_submit_price_guard=18, entry_ai_price_canary_fallback:invalid_price=12, entry_ai_price_canary_fallback:above_best_ask=5, scale_in_price_guard_block:micro_vwap_bp>60.0=4`

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

- `5m`: ai=11, budget=1, latency=0, submitted=0, top=`blocked_strength_momentum:insufficient_history=2429, blocked_overbought:-=986, blocked_strength_momentum:below_window_buy_value=252`, upstream=`blocked_ai_score:score_62.0=7, first_ai_wait:-=6, blocked_ai_score:score_58.0=2`
- `10m`: ai=11, budget=3, latency=1, submitted=0, top=`blocked_strength_momentum:insufficient_history=4956, blocked_overbought:-=2033, blocked_swing_gap:-=381`, upstream=`first_ai_wait:-=11, blocked_ai_score:score_62.0=9, blocked_ai_score:score_57.0=2`
- `30m`: ai=11, budget=10, latency=2, submitted=0, top=`blocked_strength_momentum:insufficient_history=4980, blocked_overbought:-=2041, blocked_swing_gap:-=387`, upstream=`first_ai_wait:-=11, blocked_ai_score:score_62.0=9, blocked_ai_score:score_57.0=2`
