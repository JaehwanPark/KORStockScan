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

- as_of: `2026-06-19T12:40:03`
- baseline_date: `2026-06-18`
- ai_confirmed unique: `128`
- budget_pass unique: `29`
- latency_pass unique: `19`
- submitted unique: `0`
- holding_started unique: `0`
- budget/ai unique: `22.7%` (baseline `37.3`)
- submitted/ai unique: `0.0%` (baseline `4.3`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:below_window_buy_value=716, latency_block:latency_state_danger=707, blocked_strength_momentum:below_strength_base=576, blocked_vpw:-=360, first_ai_wait:-=339`
- swing blockers: `blocked_swing_score_vpw:-=503, blocked_swing_gap:-=126`
- upstream blockers: `first_ai_wait:-=339, blocked_ai_score:score_62.0=122, blocked_ai_score:ai_score_50_buy_hold_override=96, wait65_79_ev_candidate:score_74.0=37, blocked_ai_score:score_60.0=16`
- latency blockers: `latency_block:latency_state_danger=707`
- price guards: `entry_ai_price_canary_fallback:invalid_price=71, scale_in_price_guard_block:micro_vwap_bp<-5.0=8, scale_in_price_guard_block:micro_vwap_bp>60.0=4`
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

- `5m`: ai=5, budget=0, latency=0, submitted=0, top=`first_ai_wait:-=6, blocked_vpw:-=6, entry_ai_price_canary_fallback:invalid_price=4`, swing=`-`, upstream=`first_ai_wait:-=6, blocked_ai_score:ai_score_50_buy_hold_override=2`
- `10m`: ai=8, budget=0, latency=0, submitted=0, top=`first_ai_wait:-=11, blocked_vpw:-=9, blocked_strength_momentum:below_strength_base=7`, swing=`-`, upstream=`first_ai_wait:-=11, blocked_ai_score:ai_score_50_buy_hold_override=3, wait65_79_ev_candidate:score_68.0=1`
- `30m`: ai=25, budget=14, latency=2, submitted=0, top=`blocked_strength_momentum:below_window_buy_value=56, blocked_vpw:-=29, first_ai_wait:-=28`, swing=`blocked_swing_score_vpw:-=21, blocked_swing_gap:-=1`, upstream=`first_ai_wait:-=28, blocked_ai_score:ai_score_50_buy_hold_override=12, blocked_ai_score:score_62.0=3`
