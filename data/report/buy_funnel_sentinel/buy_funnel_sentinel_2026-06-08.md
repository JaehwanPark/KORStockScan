# BUY Funnel Sentinel 2026-06-08

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

- as_of: `2026-06-08T11:50:05`
- baseline_date: `2026-06-05`
- ai_confirmed unique: `85`
- budget_pass unique: `89`
- latency_pass unique: `41`
- submitted unique: `12`
- holding_started unique: `12`
- budget/ai unique: `104.7%` (baseline `14.1`)
- submitted/ai unique: `14.1%` (baseline `0.0`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `latency_block:latency_state_danger=6786, blocked_strength_momentum:below_window_buy_value=3926, blocked_gatekeeper_reject:전량 회피=2467, blocked_swing_score_vpw:-=2138, blocked_strength_momentum:below_buy_ratio=1923`
- upstream blockers: `blocked_ai_score:score_62.0=180, blocked_ai_score:ai_score_50_buy_hold_override=169, first_ai_wait:-=78, blocked_ai_score:score_58.0=61, blocked_ai_score:score_60.0=46`
- latency blockers: `latency_block:latency_state_danger=6786`
- price guards: `entry_ai_price_canary_fallback:pre_submit_price_guard=63, entry_ai_price_canary_fallback:invalid_price=33, scale_in_price_guard_block:micro_vwap_bp>60.0=17, entry_ai_price_canary_skip_order:orderbook_micro is bearish with negative ofi and weak bid-side depth=1, entry_ai_price_canary_fallback:above_best_ask=1`

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

- `5m`: ai=12, budget=23, latency=1, submitted=1, top=`latency_block:latency_state_danger=98, blocked_strength_momentum:below_window_buy_value=41, entry_armed_expired:qualification_passed=39`, upstream=`blocked_ai_score:score_60.0=1, wait65_79_ev_candidate:score_66.0=1, blocked_ai_score:score_62.0=1`
- `10m`: ai=21, budget=27, latency=1, submitted=1, top=`latency_block:latency_state_danger=196, blocked_strength_momentum:below_window_buy_value=91, entry_armed_expired:qualification_passed=77`, upstream=`blocked_ai_score:score_62.0=6, blocked_ai_score:score_74.0=3, wait65_79_ev_candidate:score_74.0=3`
- `30m`: ai=31, budget=37, latency=7, submitted=5, top=`latency_block:latency_state_danger=693, blocked_strength_momentum:below_window_buy_value=312, blocked_overbought:-=236`, upstream=`blocked_ai_score:score_62.0=19, blocked_ai_score:ai_score_50_buy_hold_override=15, wait65_79_ev_candidate:score_74.0=11`
