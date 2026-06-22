# BUY Funnel Sentinel 2026-06-22

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

- as_of: `2026-06-22T10:05:05`
- baseline_date: `2026-06-19`
- ai_confirmed unique: `129`
- budget_pass unique: `33`
- latency_pass unique: `7`
- submitted unique: `1`
- holding_started unique: `0`
- budget/ai unique: `25.6%` (baseline `30.8`)
- submitted/ai unique: `0.8%` (baseline `0.0`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `latency_block:latency_state_danger=309, blocked_strength_momentum:below_window_buy_value=296, blocked_liquidity:-=209, blocked_strength_momentum:below_strength_base=164, blocked_vpw:-=155`
- swing blockers: `blocked_swing_score_vpw:-=231, blocked_swing_gap:-=19`
- upstream blockers: `first_ai_wait:-=154, blocked_ai_score:ai_score_50_buy_hold_override=77, blocked_ai_score:score_62.0=52, wait65_79_ev_candidate:score_74.0=17, blocked_ai_score:score_58.0=8`
- latency blockers: `latency_block:latency_state_danger=309`
- price guards: `scale_in_price_guard_block:micro_vwap_bp>60.0=39, entry_ai_price_canary_fallback:invalid_price=33, scale_in_price_guard_block:micro_vwap_bp<-5.0=11, entry_ai_price_canary_fallback:pre_submit_price_guard=2, scale_in_price_guard_block:spread_bps>80.0=2`
- quote refresh: `attempted=33, applied=24, latency_recovered=6, submitted_after_refresh=0`
- quote refresh downstream: `{'armed_expired_before_submit': 3, 'budget_pass_no_submit_event': 2, 'upstream_block_after_latency_recovery': 1}`

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

- `5m`: ai=9, budget=6, latency=1, submitted=0, top=`latency_block:latency_state_danger=29, blocked_strength_momentum:below_window_buy_value=15, blocked_strength_momentum:below_strength_base=13`, swing=`blocked_swing_score_vpw:-=26`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=8, first_ai_wait:-=6, blocked_ai_score:score_62.0=3`
- `10m`: ai=23, budget=6, latency=1, submitted=0, top=`latency_block:latency_state_danger=63, blocked_strength_momentum:below_window_buy_value=33, blocked_strength_momentum:below_strength_base=25`, swing=`blocked_swing_score_vpw:-=56`, upstream=`first_ai_wait:-=18, blocked_ai_score:ai_score_50_buy_hold_override=14, blocked_ai_score:score_62.0=5`
- `30m`: ai=79, budget=19, latency=3, submitted=0, top=`latency_block:latency_state_danger=196, blocked_strength_momentum:below_window_buy_value=129, blocked_liquidity:-=92`, swing=`blocked_swing_score_vpw:-=162, blocked_swing_gap:-=10`, upstream=`first_ai_wait:-=67, blocked_ai_score:ai_score_50_buy_hold_override=41, blocked_ai_score:score_62.0=23`
