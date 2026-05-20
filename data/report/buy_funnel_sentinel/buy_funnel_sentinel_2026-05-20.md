# BUY Funnel Sentinel 2026-05-20

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

- as_of: `2026-05-20T11:45:05`
- baseline_date: `2026-05-19`
- ai_confirmed unique: `101`
- budget_pass unique: `2`
- latency_pass unique: `0`
- submitted unique: `0`
- holding_started unique: `0`
- budget/ai unique: `2.0%` (baseline `4.3`)
- submitted/ai unique: `0.0%` (baseline `0.0`)
- top blockers: `blocked_swing_score_vpw:-=109324, blocked_overbought:-=7206, blocked_strength_momentum:below_window_buy_value=6093, blocked_strength_momentum:below_strength_base=5639, blocked_strength_momentum:insufficient_history=2348`
- upstream blockers: `blocked_ai_score:score_62.0=518, blocked_ai_score:ai_score_50_buy_hold_override=451, blocked_ai_score:score_58.0=130, first_ai_wait:-=101, blocked_ai_score:score_63.0=63`
- latency blockers: `latency_block:latency_state_danger=58`
- price guards: `scale_in_price_guard_block:micro_vwap_bp>60.0=142, entry_ai_price_canary_fallback:invalid_price=75, scale_in_price_guard_block:spread_bps>80.0=16, scale_in_price_guard_block:micro_vwap_bp<-5.0=5, entry_ai_price_canary_skip_order:Wide ask overhang and weak micro setup; bid depth is thin and orderbook_micro is insufficient, so submit expectancy is poor now.=1`

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

- `5m`: ai=24, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=4937, blocked_strength_momentum:below_strength_base=473, blocked_overbought:-=472`, upstream=`blocked_ai_score:score_62.0=14, blocked_ai_score:ai_score_50_buy_hold_override=14, blocked_ai_score:score_58.0=4`
- `10m`: ai=26, budget=1, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=9174, blocked_overbought:-=920, blocked_strength_momentum:below_strength_base=785`, upstream=`blocked_ai_score:score_62.0=30, blocked_ai_score:ai_score_50_buy_hold_override=29, blocked_ai_score:score_58.0=6`
- `30m`: ai=53, budget=1, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=25472, blocked_overbought:-=2183, blocked_strength_momentum:below_strength_base=1809`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=102, blocked_ai_score:score_62.0=97, first_ai_wait:-=30`
