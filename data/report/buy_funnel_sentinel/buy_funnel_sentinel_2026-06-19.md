# BUY Funnel Sentinel 2026-06-19

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
- submit_contract_weak_matches: `BROKER_RECEIPT, BUDGET_PASS_COLLAPSE, FILL_QUALITY, LATENCY_PRE_SUBMIT, PRICE_REVALIDATION, SIM_REAL_AUTHORITY, TELEGRAM_POST_SUBMIT_ONLY, UPSTREAM_GATE`

## 근거

- as_of: `2026-06-19T13:40:05`
- baseline_date: `2026-06-18`
- ai_confirmed unique: `136`
- budget_pass unique: `29`
- latency_pass unique: `19`
- submitted unique: `0`
- holding_started unique: `0`
- budget/ai unique: `21.3%` (baseline `43.8`)
- submitted/ai unique: `0.0%` (baseline `7.5`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:below_window_buy_value=755, latency_block:latency_state_danger=737, blocked_strength_momentum:below_strength_base=631, blocked_vpw:-=409, first_ai_wait:-=388`
- swing blockers: `blocked_swing_score_vpw:-=534, blocked_swing_gap:-=126`
- upstream blockers: `first_ai_wait:-=388, blocked_ai_score:score_62.0=125, blocked_ai_score:ai_score_50_buy_hold_override=114, wait65_79_ev_candidate:score_74.0=38, blocked_ai_score:score_60.0=17`
- latency blockers: `latency_block:latency_state_danger=737`
- price guards: `entry_ai_price_canary_fallback:invalid_price=95, scale_in_price_guard_block:micro_vwap_bp<-5.0=8, scale_in_price_guard_block:micro_vwap_bp>60.0=4`
- quote refresh: `attempted=29, applied=27, latency_recovered=8, submitted_after_refresh=0`
- quote refresh downstream: `{'budget_pass_no_submit_event': 7, 'upstream_block_after_latency_recovery': 1}`

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

- `5m`: ai=5, budget=19, latency=4, submitted=0, top=`latency_block:latency_state_danger=30, blocked_strength_momentum:below_strength_base=9, blocked_vpw:-=6`, swing=`blocked_swing_score_vpw:-=31`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=5, blocked_ai_score:score_62.0=3, first_ai_wait:-=1`
- `10m`: ai=8, budget=19, latency=4, submitted=0, top=`latency_block:latency_state_danger=30, blocked_strength_momentum:below_strength_base=13, blocked_vpw:-=9`, swing=`blocked_swing_score_vpw:-=31`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=9, first_ai_wait:-=5, blocked_ai_score:score_62.0=3`
- `30m`: ai=21, budget=19, latency=4, submitted=0, top=`latency_block:latency_state_danger=30, blocked_vpw:-=25, blocked_strength_momentum:below_strength_base=25`, swing=`blocked_swing_score_vpw:-=31`, upstream=`first_ai_wait:-=24, blocked_ai_score:ai_score_50_buy_hold_override=11, blocked_ai_score:score_62.0=3`
