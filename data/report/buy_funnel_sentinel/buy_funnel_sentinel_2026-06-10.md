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

- as_of: `2026-06-10T12:45:08`
- baseline_date: `2026-06-09`
- ai_confirmed unique: `126`
- budget_pass unique: `127`
- latency_pass unique: `53`
- submitted unique: `19`
- holding_started unique: `5`
- budget/ai unique: `100.8%` (baseline `35.3`)
- submitted/ai unique: `15.1%` (baseline `2.4`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `latency_block:latency_state_danger=9824, blocked_swing_score_vpw:-=6379, blocked_strength_momentum:below_window_buy_value=2641, blocked_strength_momentum:below_strength_base=1848, blocked_vpw:-=1783`
- upstream blockers: `blocked_ai_score:ai_score_50_buy_hold_override=455, blocked_ai_score:score_62.0=249, first_ai_wait:-=220, blocked_ai_score:score_58.0=149, wait65_79_ev_candidate:score_65.0=39`
- latency blockers: `latency_block:latency_state_danger=9824`
- price guards: `entry_ai_price_canary_fallback:pre_submit_price_guard=90, scale_in_price_guard_block:micro_vwap_bp>60.0=65, scale_in_price_guard_block:micro_vwap_bp<-5.0=52, entry_ai_price_canary_fallback:invalid_price=45, entry_ai_price_canary_fallback:skip_low_confidence=3`

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

- `5m`: ai=16, budget=22, latency=4, submitted=1, top=`latency_block:latency_state_danger=211, blocked_swing_score_vpw:-=141, blocked_strength_momentum:below_window_buy_value=69`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=7, blocked_ai_score:score_62.0=5, blocked_ai_score:score_57.0=3`
- `10m`: ai=29, budget=32, latency=7, submitted=3, top=`latency_block:latency_state_danger=506, blocked_swing_score_vpw:-=326, blocked_strength_momentum:below_window_buy_value=156`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=16, blocked_ai_score:score_62.0=12, blocked_ai_score:score_58.0=8`
- `30m`: ai=43, budget=45, latency=13, submitted=5, top=`latency_block:latency_state_danger=2044, blocked_swing_score_vpw:-=1316, blocked_strength_momentum:below_window_buy_value=500`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=63, blocked_ai_score:score_62.0=41, blocked_ai_score:score_58.0=22`
