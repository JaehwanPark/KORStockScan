# BUY Funnel Sentinel 2026-06-04

## 판정

- primary: `SUBMIT_DROUGHT_CRITICAL`
- secondary: `LATENCY_DROUGHT, UPSTREAM_AI_THRESHOLD`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `false`
- followup_route: `entry_submit_drought_auto_workorder`
- followup_owner: `postclose_threshold_cycle_and_lifecycle_decision_matrix`
- runtime_effect: `auto_workorder_no_intraday_mutation`
- submit_contract_downstream: `code_improvement_workorder, lifecycle_decision_matrix.submit_bucket_attribution, threshold_cycle_ev_report, runtime_approval_summary, postclose_verifier`
- submit_contract_weak_matches: `BROKER_RECEIPT, BUDGET_PASS_COLLAPSE, FILL_QUALITY, LATENCY_PRE_SUBMIT, SIM_REAL_AUTHORITY, SOURCE_TAXONOMY_LEAKAGE, TELEGRAM_POST_SUBMIT_ONLY, UPSTREAM_GATE`

## 근거

- as_of: `2026-06-04T15:20:05`
- baseline_date: `2026-06-02`
- ai_confirmed unique: `39`
- budget_pass unique: `16`
- latency_pass unique: `12`
- submitted unique: `1`
- holding_started unique: `0`
- budget/ai unique: `41.0%` (baseline `58.5`)
- submitted/ai unique: `2.6%` (baseline `13.6`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `latency_block:latency_state_danger=4332, blocked_swing_score_vpw:-=3495, blocked_swing_gap:-=836, blocked_overbought:-=824, blocked_strength_momentum:below_window_buy_value=701`
- upstream blockers: `blocked_ai_score:ai_score_50_buy_hold_override=86, blocked_ai_score:score_62.0=67, blocked_ai_score:score_60.0=38, first_ai_wait:-=29, blocked_ai_score:score_58.0=15`
- latency blockers: `latency_block:latency_state_danger=4332`
- price guards: `entry_ai_price_canary_fallback:invalid_price=7, entry_ai_price_canary_fallback:pre_submit_price_guard=1`

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

- `5m`: ai=0, budget=11, latency=6, submitted=0, top=`latency_block:latency_state_danger=978, blocked_swing_score_vpw:-=822, blocked_swing_gap:-=162`, upstream=`-`
- `10m`: ai=0, budget=11, latency=6, submitted=0, top=`latency_block:latency_state_danger=1755, blocked_swing_score_vpw:-=1447, blocked_swing_gap:-=318`, upstream=`-`
- `30m`: ai=28, budget=14, latency=8, submitted=1, top=`latency_block:latency_state_danger=3012, blocked_swing_score_vpw:-=2448, blocked_swing_gap:-=569`, upstream=`blocked_ai_score:score_62.0=30, blocked_ai_score:ai_score_50_buy_hold_override=18, blocked_ai_score:score_60.0=13`
