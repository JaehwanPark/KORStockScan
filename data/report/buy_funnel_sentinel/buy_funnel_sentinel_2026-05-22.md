# BUY Funnel Sentinel 2026-05-22

## 판정

- primary: `PRICE_GUARD_DROUGHT`
- secondary: `LATENCY_DROUGHT, UPSTREAM_AI_THRESHOLD`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `false`
- followup_route: `pre_submit_price_guard_review`
- followup_owner: `postclose_threshold_cycle`
- runtime_effect: `report_only_no_mutation`

## 근거

- as_of: `2026-05-22T15:20:06`
- baseline_date: `2026-05-21`
- ai_confirmed unique: `235`
- budget_pass unique: `3`
- latency_pass unique: `3`
- submitted unique: `0`
- holding_started unique: `0`
- budget/ai unique: `1.3%` (baseline `6.2`)
- submitted/ai unique: `0.0%` (baseline `2.2`)
- top blockers: `blocked_swing_score_vpw:-=62701, blocked_swing_gap:-=42854, blocked_strength_momentum:below_window_buy_value=33321, blocked_overbought:-=24884, blocked_strength_momentum:insufficient_history=17837`
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

- Review top price guard block labels and affected symbols.
- Keep threshold/runtime mutation blocked before ThresholdOpsTransition0506.

## Window Summary

- `5m`: ai=0, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=1314, blocked_swing_gap:-=1095`, upstream=`-`
- `10m`: ai=0, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=2556, blocked_swing_gap:-=2130, blocked_gatekeeper_reject:눌림 대기=3`, upstream=`-`
- `30m`: ai=30, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=7308, blocked_swing_gap:-=6090, blocked_strength_momentum:below_window_buy_value=2097`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=28, blocked_ai_score:score_62.0=21, blocked_ai_score:score_60.0=5`
