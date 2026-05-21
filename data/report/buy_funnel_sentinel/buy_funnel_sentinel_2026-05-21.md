# BUY Funnel Sentinel 2026-05-21

## 판정

- primary: `PRICE_GUARD_DROUGHT`
- secondary: `UPSTREAM_AI_THRESHOLD`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `false`
- followup_route: `pre_submit_price_guard_review`
- followup_owner: `postclose_threshold_cycle`
- runtime_effect: `report_only_no_mutation`

## 근거

- as_of: `2026-05-21T09:20:02`
- baseline_date: `2026-05-20`
- ai_confirmed unique: `94`
- budget_pass unique: `2`
- latency_pass unique: `1`
- submitted unique: `1`
- holding_started unique: `0`
- budget/ai unique: `2.1%` (baseline `0.0`)
- submitted/ai unique: `1.1%` (baseline `0.0`)
- top blockers: `blocked_swing_score_vpw:-=1486, blocked_swing_gap:-=848, blocked_strength_momentum:insufficient_history=456, blocked_strength_momentum:below_window_buy_value=310, blocked_overbought:-=122`
- upstream blockers: `blocked_ai_score:ai_score_50_buy_hold_override=67, first_ai_wait:-=62, blocked_ai_score:score_62.0=62, blocked_ai_score:score_60.0=7, blocked_ai_score:score_63.0=4`
- latency blockers: `latency_block:latency_state_danger=1`
- price guards: `entry_ai_price_canary_fallback:invalid_price=41, entry_ai_price_canary_fallback:skip_low_confidence=1`

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

- `5m`: ai=48, budget=1, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=588, blocked_swing_gap:-=394, blocked_strength_momentum:insufficient_history=188`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=28, blocked_ai_score:score_62.0=20, first_ai_wait:-=13`
- `10m`: ai=72, budget=2, latency=1, submitted=1, top=`blocked_swing_score_vpw:-=1004, blocked_swing_gap:-=601, blocked_strength_momentum:insufficient_history=274`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=54, blocked_ai_score:score_62.0=42, first_ai_wait:-=30`
- `30m`: ai=94, budget=2, latency=1, submitted=1, top=`blocked_swing_score_vpw:-=1486, blocked_swing_gap:-=848, blocked_strength_momentum:insufficient_history=456`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=67, first_ai_wait:-=62, blocked_ai_score:score_62.0=62`
