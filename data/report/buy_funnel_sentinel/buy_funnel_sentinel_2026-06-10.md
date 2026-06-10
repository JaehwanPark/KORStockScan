# BUY Funnel Sentinel 2026-06-10

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

- as_of: `2026-06-10T11:50:05`
- baseline_date: `2026-06-09`
- ai_confirmed unique: `118`
- budget_pass unique: `120`
- latency_pass unique: `45`
- submitted unique: `12`
- holding_started unique: `5`
- budget/ai unique: `101.7%` (baseline `33.5`)
- submitted/ai unique: `10.2%` (baseline `1.2`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `latency_block:latency_state_danger=5493, blocked_swing_score_vpw:-=3451, blocked_strength_momentum:below_window_buy_value=1658, blocked_strength_momentum:below_strength_base=1236, blocked_vpw:-=1162`
- upstream blockers: `blocked_ai_score:ai_score_50_buy_hold_override=322, first_ai_wait:-=195, blocked_ai_score:score_62.0=173, blocked_ai_score:score_58.0=106, wait65_79_ev_candidate:score_65.0=33`
- latency blockers: `latency_block:latency_state_danger=5493`
- price guards: `entry_ai_price_canary_fallback:pre_submit_price_guard=77, scale_in_price_guard_block:micro_vwap_bp>60.0=65, scale_in_price_guard_block:micro_vwap_bp<-5.0=52, entry_ai_price_canary_fallback:invalid_price=45, scale_in_price_guard_block:spread_bps>80.0=3`

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

- `5m`: ai=21, budget=27, latency=4, submitted=1, top=`latency_block:latency_state_danger=271, blocked_swing_score_vpw:-=154, blocked_strength_momentum:below_window_buy_value=101`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=12, blocked_ai_score:score_62.0=11, blocked_ai_score:score_58.0=5`
- `10m`: ai=28, budget=34, latency=5, submitted=2, top=`latency_block:latency_state_danger=641, blocked_swing_score_vpw:-=361, blocked_strength_momentum:below_window_buy_value=196`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=20, blocked_ai_score:score_62.0=19, blocked_ai_score:score_58.0=8`
- `30m`: ai=44, budget=46, latency=11, submitted=2, top=`latency_block:latency_state_danger=1941, blocked_swing_score_vpw:-=1248, blocked_strength_momentum:below_window_buy_value=532`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=66, blocked_ai_score:score_62.0=60, blocked_ai_score:score_58.0=20`
