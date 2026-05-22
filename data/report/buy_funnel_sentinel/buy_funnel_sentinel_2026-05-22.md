# BUY Funnel Sentinel 2026-05-22

## 판정

- primary: `SUBMIT_DROUGHT_CRITICAL`
- secondary: `PRICE_GUARD_DROUGHT, LATENCY_DROUGHT, UPSTREAM_AI_THRESHOLD`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `false`
- followup_route: `entry_submit_drought_auto_workorder`
- followup_owner: `postclose_threshold_cycle_and_lifecycle_decision_matrix`
- runtime_effect: `auto_workorder_no_intraday_mutation`

## 근거

- as_of: `2026-05-22T22:58:55`
- baseline_date: `2026-05-21`
- ai_confirmed unique: `235`
- budget_pass unique: `3`
- latency_pass unique: `3`
- submitted unique: `0`
- holding_started unique: `0`
- budget/ai unique: `1.3%` (baseline `6.2`)
- submitted/ai unique: `0.0%` (baseline `2.2`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_swing_score_vpw:-=80953, blocked_swing_gap:-=58064, blocked_strength_momentum:below_window_buy_value=33321, blocked_overbought:-=24884, blocked_strength_momentum:insufficient_history=17837`
- upstream blockers: `blocked_ai_score:ai_score_50_buy_hold_override=1158, blocked_ai_score:score_62.0=931, first_ai_wait:-=198, blocked_ai_score:score_58.0=150, blocked_ai_score:score_60.0=123`
- latency blockers: `latency_block:latency_state_danger=64`
- price guards: `entry_ai_price_canary_fallback:invalid_price=119, entry_ai_price_canary_fallback:low_confidence=1, entry_ai_price_canary_skip_order:spread is wide and micro snapshot is missing, while liquidity is weak and the tape shows recent pullback risk=1, scale_in_price_guard_block:micro_vwap_bp<-5.0=1, entry_ai_price_canary_fallback:pre_submit_price_guard=1`

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

- `5m`: ai=0, budget=0, latency=0, submitted=0, top=`-`, upstream=`-`
- `10m`: ai=0, budget=0, latency=0, submitted=0, top=`-`, upstream=`-`
- `30m`: ai=0, budget=0, latency=0, submitted=0, top=`-`, upstream=`-`
