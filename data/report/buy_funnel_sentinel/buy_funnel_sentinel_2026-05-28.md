# BUY Funnel Sentinel 2026-05-28

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

- as_of: `2026-05-28T14:00:04`
- baseline_date: `2026-05-27`
- ai_confirmed unique: `107`
- budget_pass unique: `55`
- latency_pass unique: `20`
- submitted unique: `0`
- holding_started unique: `0`
- budget/ai unique: `51.4%` (baseline `59.0`)
- submitted/ai unique: `0.0%` (baseline `9.0`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `latency_block:latency_state_danger=16127, blocked_swing_score_vpw:-=10849, blocked_gatekeeper_reject:눌림 대기=3135, blocked_strength_momentum:below_window_buy_value=2650, blocked_strength_momentum:below_strength_base=2293`
- upstream blockers: `blocked_ai_score:score_62.0=753, blocked_ai_score:ai_score_50_buy_hold_override=411, first_ai_wait:-=147, blocked_ai_score:score_60.0=134, blocked_ai_score:score_58.0=93`
- latency blockers: `latency_block:latency_state_danger=16127`
- price guards: `entry_ai_price_canary_fallback:low_confidence=99, entry_ai_price_canary_fallback:invalid_price=24, entry_ai_price_canary_fallback:pre_submit_price_guard=17, scale_in_price_guard_block:micro_vwap_bp>60.0=4, entry_ai_price_canary_fallback:above_best_ask=4`

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

- `5m`: ai=17, budget=11, latency=1, submitted=0, top=`latency_block:latency_state_danger=694, blocked_swing_score_vpw:-=515, blocked_gatekeeper_reject:전량 회피=143`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=14, blocked_ai_score:score_62.0=12, first_ai_wait:-=7`
- `10m`: ai=27, budget=14, latency=4, submitted=0, top=`latency_block:latency_state_danger=735, blocked_swing_score_vpw:-=553, blocked_strength_momentum:below_strength_base=181`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=29, first_ai_wait:-=21, blocked_ai_score:score_62.0=17`
- `30m`: ai=27, budget=14, latency=4, submitted=0, top=`latency_block:latency_state_danger=735, blocked_swing_score_vpw:-=553, blocked_strength_momentum:below_strength_base=181`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=29, first_ai_wait:-=21, blocked_ai_score:score_62.0=17`
