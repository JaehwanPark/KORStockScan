# BUY Funnel Sentinel 2026-05-27

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

- as_of: `2026-05-27T15:20:07`
- baseline_date: `2026-05-26`
- ai_confirmed unique: `128`
- budget_pass unique: `73`
- latency_pass unique: `27`
- submitted unique: `11`
- holding_started unique: `6`
- budget/ai unique: `57.0%` (baseline `47.9`)
- submitted/ai unique: `8.6%` (baseline `11.8`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `latency_block:latency_state_danger=36795, blocked_swing_score_vpw:-=33767, blocked_overbought:-=8813, blocked_strength_momentum:below_strength_base=8450, blocked_strength_momentum:below_window_buy_value=4807`
- upstream blockers: `blocked_ai_score:score_62.0=1063, blocked_ai_score:ai_score_50_buy_hold_override=909, first_ai_wait:-=456, blocked_ai_score:score_60.0=141, blocked_ai_score:score_58.0=123`
- latency blockers: `latency_block:latency_state_danger=36795`
- price guards: `entry_ai_price_canary_fallback:low_confidence=249, entry_ai_price_canary_fallback:invalid_price=40, entry_ai_price_canary_fallback:pre_submit_price_guard=22, entry_ai_price_canary_fallback:above_best_ask=5, scale_in_price_guard_block:micro_vwap_bp>60.0=5`

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

- `5m`: ai=0, budget=7, latency=0, submitted=0, top=`latency_block:latency_state_danger=849, blocked_swing_score_vpw:-=848, blocked_swing_gap:-=122`, upstream=`-`
- `10m`: ai=0, budget=7, latency=0, submitted=0, top=`latency_block:latency_state_danger=1610, blocked_swing_score_vpw:-=1610, blocked_swing_gap:-=230`, upstream=`-`
- `30m`: ai=25, budget=9, latency=1, submitted=0, top=`latency_block:latency_state_danger=4305, blocked_swing_score_vpw:-=4293, blocked_swing_gap:-=610`, upstream=`blocked_ai_score:score_62.0=35, blocked_ai_score:ai_score_50_buy_hold_override=10, blocked_ai_score:score_60.0=6`
