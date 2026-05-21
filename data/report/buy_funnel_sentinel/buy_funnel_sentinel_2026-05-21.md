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

- as_of: `2026-05-21T15:20:08`
- baseline_date: `2026-05-20`
- ai_confirmed unique: `224`
- budget_pass unique: `14`
- latency_pass unique: `6`
- submitted unique: `5`
- holding_started unique: `1`
- budget/ai unique: `6.2%` (baseline `2.5`)
- submitted/ai unique: `2.2%` (baseline `0.0`)
- top blockers: `blocked_swing_score_vpw:-=95350, blocked_swing_gap:-=77791, blocked_overbought:-=29807, blocked_strength_momentum:below_window_buy_value=18903, blocked_strength_momentum:insufficient_history=17949`
- upstream blockers: `blocked_ai_score:ai_score_50_buy_hold_override=1401, blocked_ai_score:score_62.0=888, first_ai_wait:-=412, blocked_ai_score:score_60.0=205, blocked_ai_score:score_58.0=148`
- latency blockers: `latency_block:latency_state_danger=254`
- price guards: `entry_ai_price_canary_fallback:invalid_price=167, scale_in_price_guard_block:micro_vwap_bp>60.0=23, entry_ai_price_canary_fallback:skip_low_confidence=1, entry_ai_price_canary_skip_order:orderbook_micro missing and raw tape shows sell pressure with weak bid follow-through; spread is wide so entry is unfavorable=1, entry_ai_price_canary_fallback:pre_submit_price_guard=1`

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

- `5m`: ai=0, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=1417, blocked_swing_gap:-=1355`, upstream=`-`
- `10m`: ai=0, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=3171, blocked_swing_gap:-=2961, blocked_gatekeeper_reject:눌림 대기=3`, upstream=`-`
- `30m`: ai=28, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=11052, blocked_swing_gap:-=8153, blocked_overbought:-=1596`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=35, blocked_ai_score:score_62.0=16, blocked_ai_score:score_60.0=4`
