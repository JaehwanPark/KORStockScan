# BUY Funnel Sentinel 2026-05-18

## 판정

- primary: `UPSTREAM_AI_THRESHOLD`
- secondary: `-`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `false`
- followup_route: `score65_74_counterfactual_review`
- followup_owner: `postclose_threshold_cycle`
- runtime_effect: `report_only_no_mutation`

## 근거

- as_of: `2026-05-18T13:10:09`
- baseline_date: `2026-05-15`
- ai_confirmed unique: `65`
- budget_pass unique: `2`
- latency_pass unique: `0`
- submitted unique: `0`
- holding_started unique: `0`
- budget/ai unique: `3.1%` (baseline `0.0`)
- submitted/ai unique: `0.0%` (baseline `0.0`)
- top blockers: `blocked_swing_score_vpw:-=314989, blocked_strength_momentum:below_window_buy_value=118916, blocked_strength_momentum:below_strength_base=105516, blocked_overbought:-=47836, blocked_swing_gap:-=38626`
- upstream blockers: `blocked_ai_score:score_62.0=268, blocked_ai_score:ai_score_50_buy_hold_override=146, first_ai_wait:-=88, blocked_ai_score:score_60.0=49, blocked_ai_score:score_58.0=36`
- latency blockers: `latency_block:latency_state_danger=121`
- price guards: `-`

## 금지된 자동변경

- `score_threshold_relaxation`
- `spread_cap_relaxation`
- `fallback_reenable`
- `live_threshold_runtime_mutation`
- `bot_restart`

## 권고 액션

- Append score50/wait65_74 missed-winner and avoided-loser cohorts to report-only review.
- Do not relax score threshold or revive fallback without a new single-axis workorder.

## Window Summary

- `5m`: ai=18, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=5394, blocked_strength_momentum:below_window_buy_value=1972, blocked_overbought:-=1529`, upstream=`blocked_ai_score:score_62.0=13, first_ai_wait:-=9, blocked_ai_score:ai_score_50_buy_hold_override=6`
- `10m`: ai=19, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=11136, blocked_strength_momentum:below_window_buy_value=4010, blocked_overbought:-=3586`, upstream=`blocked_ai_score:score_62.0=21, first_ai_wait:-=12, blocked_ai_score:ai_score_50_buy_hold_override=9`
- `30m`: ai=25, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=34035, blocked_strength_momentum:below_window_buy_value=11950, blocked_overbought:-=9453`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=41, blocked_ai_score:score_62.0=40, first_ai_wait:-=35`
