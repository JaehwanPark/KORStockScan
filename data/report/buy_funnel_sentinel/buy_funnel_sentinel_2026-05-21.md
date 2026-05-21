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

- as_of: `2026-05-21T14:45:08`
- baseline_date: `2026-05-20`
- ai_confirmed unique: `222`
- budget_pass unique: `14`
- latency_pass unique: `6`
- submitted unique: `5`
- holding_started unique: `1`
- budget/ai unique: `6.3%` (baseline `2.6`)
- submitted/ai unique: `2.3%` (baseline `0.0`)
- top blockers: `blocked_swing_score_vpw:-=82608, blocked_swing_gap:-=68914, blocked_overbought:-=27335, blocked_strength_momentum:below_window_buy_value=18056, blocked_strength_momentum:insufficient_history=16624`
- upstream blockers: `blocked_ai_score:ai_score_50_buy_hold_override=1337, blocked_ai_score:score_62.0=861, first_ai_wait:-=410, blocked_ai_score:score_60.0=197, blocked_ai_score:score_58.0=143`
- latency blockers: `latency_block:latency_state_danger=254`
- price guards: `entry_ai_price_canary_fallback:invalid_price=164, scale_in_price_guard_block:micro_vwap_bp>60.0=23, entry_ai_price_canary_fallback:skip_low_confidence=1, entry_ai_price_canary_skip_order:orderbook_micro missing and raw tape shows sell pressure with weak bid follow-through; spread is wide so entry is unfavorable=1, entry_ai_price_canary_fallback:pre_submit_price_guard=1`

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

- `5m`: ai=40, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=1872, blocked_swing_gap:-=779, blocked_overbought:-=531`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=18, blocked_ai_score:score_62.0=14, blocked_ai_score:score_60.0=5`
- `10m`: ai=45, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=3965, blocked_swing_gap:-=1932, blocked_overbought:-=1187`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=29, blocked_ai_score:score_62.0=24, blocked_ai_score:score_60.0=7`
- `30m`: ai=52, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=11682, blocked_swing_gap:-=6063, blocked_overbought:-=4453`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=102, blocked_ai_score:score_62.0=65, first_ai_wait:-=22`
