# BUY Funnel Sentinel 2026-06-08

## 판정

- primary: `PRICE_GUARD_DROUGHT`
- secondary: `LATENCY_DROUGHT, UPSTREAM_AI_THRESHOLD`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `false`
- followup_route: `pre_submit_price_guard_review`
- followup_owner: `postclose_threshold_cycle`
- runtime_effect: `report_only_no_mutation`
- submit_contract_downstream: `code_improvement_workorder, lifecycle_decision_matrix.submit_bucket_attribution, threshold_cycle_ev_report, runtime_approval_summary, postclose_verifier`
- submit_contract_weak_matches: `LATENCY_PRE_SUBMIT, PRICE_REVALIDATION, SOURCE_TAXONOMY_LEAKAGE, UPSTREAM_GATE`

## 근거

- as_of: `2026-06-08T15:20:09`
- baseline_date: `2026-06-05`
- ai_confirmed unique: `109`
- budget_pass unique: `110`
- latency_pass unique: `60`
- submitted unique: `28`
- holding_started unique: `25`
- budget/ai unique: `100.9%` (baseline `18.1`)
- submitted/ai unique: `25.7%` (baseline `1.0`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `latency_block:latency_state_danger=14820, blocked_strength_momentum:below_window_buy_value=7565, blocked_swing_score_vpw:-=5911, blocked_overbought:-=4403, blocked_strength_momentum:below_strength_base=4317`
- upstream blockers: `blocked_ai_score:score_62.0=322, blocked_ai_score:ai_score_50_buy_hold_override=319, blocked_ai_score:score_58.0=148, blocked_ai_score:score_60.0=123, first_ai_wait:-=105`
- latency blockers: `latency_block:latency_state_danger=14820`
- price guards: `scale_in_price_guard_block:invalid_spread=161, entry_ai_price_canary_fallback:pre_submit_price_guard=134, entry_ai_price_canary_fallback:invalid_price=34, scale_in_price_guard_block:micro_vwap_bp>60.0=21, entry_ai_price_canary_fallback:above_best_ask=2`

## 금지된 자동변경

- `score_threshold_relaxation`
- `spread_cap_relaxation`
- `fallback_reenable`
- `live_threshold_runtime_mutation`
- `bot_restart`

## 권고 액션

- Review top price guard block labels and affected symbols.
- Keep threshold/runtime mutation blocked before ThresholdOpsTransition0506.

## Window Summary

- `5m`: ai=0, budget=12, latency=5, submitted=0, top=`latency_block:latency_state_danger=652, blocked_swing_score_vpw:-=413, blocked_gatekeeper_reject:전량 회피=197`, upstream=`-`
- `10m`: ai=0, budget=12, latency=5, submitted=0, top=`latency_block:latency_state_danger=1372, blocked_swing_score_vpw:-=845, blocked_gatekeeper_reject:전량 회피=390`, upstream=`-`
- `30m`: ai=18, budget=18, latency=7, submitted=0, top=`latency_block:latency_state_danger=2537, blocked_swing_score_vpw:-=1461, blocked_strength_momentum:below_strength_base=755`, upstream=`blocked_ai_score:score_62.0=9, blocked_ai_score:ai_score_50_buy_hold_override=7, blocked_ai_score:score_60.0=4`
