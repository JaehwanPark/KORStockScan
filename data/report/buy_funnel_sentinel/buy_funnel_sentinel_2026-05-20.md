# BUY Funnel Sentinel 2026-05-20

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

- as_of: `2026-05-20T15:20:07`
- baseline_date: `2026-05-19`
- ai_confirmed unique: `118`
- budget_pass unique: `3`
- latency_pass unique: `0`
- submitted unique: `0`
- holding_started unique: `0`
- budget/ai unique: `2.5%` (baseline `5.5`)
- submitted/ai unique: `0.0%` (baseline `0.0`)
- top blockers: `blocked_swing_score_vpw:-=261699, blocked_overbought:-=18403, blocked_strength_momentum:below_strength_base=17567, blocked_strength_momentum:below_window_buy_value=13797, blocked_strength_momentum:insufficient_history=8438`
- upstream blockers: `blocked_ai_score:ai_score_50_buy_hold_override=1087, blocked_ai_score:score_62.0=1067, blocked_ai_score:score_58.0=260, first_ai_wait:-=223, blocked_ai_score:score_63.0=116`
- latency blockers: `latency_block:latency_state_danger=401`
- price guards: `entry_ai_price_canary_fallback:invalid_price=235, scale_in_price_guard_block:micro_vwap_bp>60.0=142, scale_in_price_guard_block:spread_bps>80.0=16, scale_in_price_guard_block:micro_vwap_bp<-5.0=5, entry_ai_price_canary_fallback:low_confidence=3`

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

- `5m`: ai=0, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=5305, blocked_gatekeeper_reject:눌림 대기=1`, upstream=`-`
- `10m`: ai=0, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=10597, blocked_gatekeeper_reject:눌림 대기=3, blocked_gatekeeper_reject:전량 회피=1`, upstream=`-`
- `30m`: ai=41, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=30527, blocked_strength_momentum:below_strength_base=1242, blocked_overbought:-=644`, upstream=`blocked_ai_score:score_62.0=36, blocked_ai_score:ai_score_50_buy_hold_override=15, blocked_ai_score:score_60.0=7`
