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

- as_of: `2026-05-21T10:05:02`
- baseline_date: `2026-05-20`
- ai_confirmed unique: `130`
- budget_pass unique: `4`
- latency_pass unique: `2`
- submitted unique: `1`
- holding_started unique: `0`
- budget/ai unique: `3.1%` (baseline `1.4`)
- submitted/ai unique: `0.8%` (baseline `0.0`)
- top blockers: `blocked_swing_score_vpw:-=8139, blocked_swing_gap:-=6838, blocked_strength_momentum:below_window_buy_value=2315, blocked_overbought:-=1983, blocked_strength_momentum:insufficient_history=1153`
- upstream blockers: `blocked_ai_score:score_62.0=184, blocked_ai_score:ai_score_50_buy_hold_override=184, first_ai_wait:-=85, blocked_ai_score:score_60.0=44, blocked_ai_score:score_58.0=23`
- latency blockers: `latency_block:latency_state_danger=117`
- price guards: `entry_ai_price_canary_fallback:invalid_price=78, entry_ai_price_canary_fallback:skip_low_confidence=1`

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

- `5m`: ai=26, budget=0, latency=0, submitted=0, top=`blocked_swing_gap:-=817, blocked_swing_score_vpw:-=604, blocked_overbought:-=261`, upstream=`blocked_ai_score:score_62.0=17, blocked_ai_score:score_60.0=6, blocked_ai_score:ai_score_50_buy_hold_override=5`
- `10m`: ai=42, budget=0, latency=0, submitted=0, top=`blocked_swing_gap:-=2132, blocked_swing_score_vpw:-=1532, blocked_overbought:-=516`, upstream=`blocked_ai_score:score_62.0=29, blocked_ai_score:ai_score_50_buy_hold_override=18, blocked_ai_score:score_60.0=9`
- `30m`: ai=75, budget=1, latency=0, submitted=0, top=`blocked_swing_gap:-=4875, blocked_swing_score_vpw:-=4787, blocked_strength_momentum:below_window_buy_value=1496`, upstream=`blocked_ai_score:score_62.0=80, blocked_ai_score:ai_score_50_buy_hold_override=70, blocked_ai_score:score_60.0=21`
