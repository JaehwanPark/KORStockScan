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

- as_of: `2026-06-19T11:20:03`
- baseline_date: `2026-06-18`
- ai_confirmed unique: `119`
- budget_pass unique: `28`
- latency_pass unique: `18`
- submitted unique: `0`
- holding_started unique: `0`
- budget/ai unique: `23.5%` (baseline `26.2`)
- submitted/ai unique: `0.0%` (baseline `2.4`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `latency_block:latency_state_danger=575, blocked_strength_momentum:below_window_buy_value=533, blocked_strength_momentum:below_strength_base=465, blocked_vpw:-=304, first_ai_wait:-=275`
- swing blockers: `blocked_swing_score_vpw:-=385, blocked_swing_gap:-=119`
- upstream blockers: `first_ai_wait:-=275, blocked_ai_score:score_62.0=106, blocked_ai_score:ai_score_50_buy_hold_override=65, wait65_79_ev_candidate:score_74.0=28, blocked_ai_score:score_60.0=15`
- latency blockers: `latency_block:latency_state_danger=575`
- price guards: `entry_ai_price_canary_fallback:invalid_price=61, scale_in_price_guard_block:micro_vwap_bp<-5.0=8, scale_in_price_guard_block:micro_vwap_bp>60.0=4`
- quote refresh: `attempted=28, applied=26, latency_recovered=8, submitted_after_refresh=0`
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

- `5m`: ai=1, budget=0, latency=0, submitted=0, top=`blocked_strength_momentum:below_strength_base=8, blocked_strength_momentum:insufficient_history=5, blocked_strength_momentum:below_window_buy_value=3`, swing=`-`, upstream=`wait65_79_ev_candidate:score_74.0=1, first_ai_wait:-=1`
- `10m`: ai=3, budget=13, latency=0, submitted=0, top=`blocked_strength_momentum:below_strength_base=29, blocked_strength_momentum:below_window_buy_value=18, latency_block:latency_state_danger=12`, swing=`blocked_swing_score_vpw:-=7, blocked_swing_gap:-=1`, upstream=`first_ai_wait:-=2, blocked_ai_score:score_58.0=1, wait65_79_ev_candidate:score_74.0=1`
- `30m`: ai=24, budget=20, latency=6, submitted=0, top=`blocked_strength_momentum:below_window_buy_value=101, blocked_strength_momentum:below_strength_base=76, latency_block:latency_state_danger=74`, swing=`blocked_swing_score_vpw:-=50, blocked_swing_gap:-=7`, upstream=`first_ai_wait:-=32, blocked_ai_score:ai_score_50_buy_hold_override=15, blocked_ai_score:score_62.0=5`
