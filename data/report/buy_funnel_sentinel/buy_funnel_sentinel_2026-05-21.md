# BUY Funnel Sentinel 2026-05-21

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

- as_of: `2026-05-21T12:00:05`
- baseline_date: `2026-05-20`
- ai_confirmed unique: `195`
- budget_pass unique: `9`
- latency_pass unique: `5`
- submitted unique: `4`
- holding_started unique: `0`
- budget/ai unique: `4.6%` (baseline `1.9`)
- submitted/ai unique: `2.1%` (baseline `0.0`)
- top blockers: `blocked_swing_score_vpw:-=33749, blocked_swing_gap:-=28754, blocked_overbought:-=9303, blocked_strength_momentum:below_window_buy_value=8177, blocked_strength_momentum:insufficient_history=5793`
- upstream blockers: `blocked_ai_score:ai_score_50_buy_hold_override=616, blocked_ai_score:score_62.0=462, first_ai_wait:-=220, blocked_ai_score:score_60.0=106, blocked_ai_score:score_58.0=68`
- latency blockers: `latency_block:latency_state_danger=196`
- price guards: `entry_ai_price_canary_fallback:invalid_price=140, entry_ai_price_canary_fallback:skip_low_confidence=1, entry_ai_price_canary_skip_order:orderbook_micro missing and raw tape shows sell pressure with weak bid follow-through; spread is wide so entry is unfavorable=1`

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

- `5m`: ai=36, budget=0, latency=0, submitted=0, top=`blocked_swing_gap:-=1240, blocked_swing_score_vpw:-=948, blocked_overbought:-=604`, upstream=`blocked_ai_score:score_62.0=20, blocked_ai_score:ai_score_50_buy_hold_override=18, first_ai_wait:-=6`
- `10m`: ai=48, budget=0, latency=0, submitted=0, top=`blocked_swing_gap:-=2623, blocked_swing_score_vpw:-=2213, blocked_overbought:-=838`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=45, blocked_ai_score:score_62.0=31, first_ai_wait:-=26`
- `30m`: ai=77, budget=1, latency=1, submitted=1, top=`blocked_swing_score_vpw:-=7777, blocked_swing_gap:-=6440, blocked_overbought:-=2793`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=163, blocked_ai_score:score_62.0=78, first_ai_wait:-=50`
