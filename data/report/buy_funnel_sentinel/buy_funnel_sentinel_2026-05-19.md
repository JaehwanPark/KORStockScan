# BUY Funnel Sentinel 2026-05-19

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

- as_of: `2026-05-19T15:20:08`
- baseline_date: `2026-05-18`
- ai_confirmed unique: `128`
- budget_pass unique: `7`
- latency_pass unique: `2`
- submitted unique: `0`
- holding_started unique: `0`
- budget/ai unique: `5.5%` (baseline `3.0`)
- submitted/ai unique: `0.0%` (baseline `0.0`)
- top blockers: `blocked_swing_score_vpw:-=197289, blocked_strength_momentum:below_strength_base=23038, blocked_overbought:-=18107, blocked_swing_gap:-=14396, blocked_strength_momentum:below_window_buy_value=14155`
- upstream blockers: `blocked_ai_score:ai_score_50_buy_hold_override=1250, blocked_ai_score:score_62.0=870, blocked_ai_score:score_58.0=222, first_ai_wait:-=138, blocked_ai_score:score_60.0=125`
- latency blockers: `latency_block:latency_state_danger=565`
- price guards: `scale_in_price_guard_block:micro_vwap_bp>60.0=103, entry_ai_price_canary_fallback:invalid_price=89, scale_in_price_guard_block:micro_vwap_bp<-5.0=64, scale_in_price_guard_block:spread_bps>80.0=18, entry_ai_price_canary_fallback:pre_submit_price_guard=3`

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

- `5m`: ai=0, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=2970`, upstream=`-`
- `10m`: ai=0, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=5670`, upstream=`-`
- `30m`: ai=30, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=15246, blocked_strength_momentum:below_strength_base=285, blocked_overbought:-=231`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=44, blocked_ai_score:score_62.0=24, blocked_ai_score:score_58.0=7`
