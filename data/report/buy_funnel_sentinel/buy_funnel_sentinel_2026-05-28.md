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

- as_of: `2026-05-28T15:20:04`
- baseline_date: `2026-05-27`
- ai_confirmed unique: `108`
- budget_pass unique: `56`
- latency_pass unique: `28`
- submitted unique: `2`
- holding_started unique: `1`
- budget/ai unique: `51.9%` (baseline `57.0`)
- submitted/ai unique: `1.9%` (baseline `8.6`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `latency_block:latency_state_danger=20789, blocked_swing_score_vpw:-=14359, blocked_gatekeeper_reject:눌림 대기=3852, blocked_strength_momentum:below_window_buy_value=2770, blocked_strength_momentum:below_strength_base=2742`
- upstream blockers: `blocked_ai_score:score_62.0=795, blocked_ai_score:ai_score_50_buy_hold_override=463, first_ai_wait:-=165, blocked_ai_score:score_60.0=144, blocked_ai_score:score_58.0=98`
- latency blockers: `latency_block:latency_state_danger=20789`
- price guards: `entry_ai_price_canary_fallback:low_confidence=99, entry_ai_price_canary_fallback:invalid_price=24, entry_ai_price_canary_fallback:pre_submit_price_guard=19, scale_in_price_guard_block:micro_vwap_bp>60.0=4, entry_ai_price_canary_fallback:above_best_ask=4`

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

- `5m`: ai=0, budget=8, latency=6, submitted=0, top=`latency_block:latency_state_danger=1054, blocked_swing_score_vpw:-=798, blocked_gatekeeper_reject:눌림 대기=174`, upstream=`-`
- `10m`: ai=0, budget=8, latency=6, submitted=0, top=`latency_block:latency_state_danger=1950, blocked_swing_score_vpw:-=1470, blocked_gatekeeper_reject:눌림 대기=286`, upstream=`-`
- `30m`: ai=13, budget=12, latency=10, submitted=0, top=`latency_block:latency_state_danger=3101, blocked_swing_score_vpw:-=2343, blocked_gatekeeper_reject:눌림 대기=475`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=20, first_ai_wait:-=13, blocked_ai_score:score_62.0=3`
