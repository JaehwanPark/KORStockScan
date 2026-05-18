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

- as_of: `2026-05-18T10:50:05`
- baseline_date: `2026-05-15`
- ai_confirmed unique: `43`
- budget_pass unique: `1`
- latency_pass unique: `0`
- submitted unique: `0`
- holding_started unique: `0`
- budget/ai unique: `2.3%` (baseline `0.0`)
- submitted/ai unique: `0.0%` (baseline `0.0`)
- top blockers: `blocked_swing_score_vpw:-=132586, blocked_strength_momentum:below_strength_base=61283, blocked_strength_momentum:below_window_buy_value=44273, blocked_overbought:-=8785, blocked_swing_gap:-=7347`
- upstream blockers: `blocked_ai_score:score_62.0=106, blocked_ai_score:ai_score_50_buy_hold_override=48, first_ai_wait:-=40, blocked_ai_score:score_60.0=28, blocked_ai_score:score_58.0=9`
- latency blockers: `latency_block:latency_state_danger=7`
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

- `5m`: ai=10, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=7028, blocked_strength_momentum:below_window_buy_value=3208, blocked_strength_momentum:below_strength_base=1557`, upstream=`blocked_ai_score:score_62.0=8, blocked_ai_score:score_60.0=2, blocked_ai_score:score_68.0=1`
- `10m`: ai=13, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=14276, blocked_strength_momentum:below_window_buy_value=6850, blocked_strength_momentum:below_strength_base=3648`, upstream=`blocked_ai_score:score_62.0=13, blocked_ai_score:score_60.0=2, blocked_ai_score:score_55.0=1`
- `30m`: ai=21, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=40465, blocked_strength_momentum:below_window_buy_value=16379, blocked_strength_momentum:below_strength_base=13558`, upstream=`blocked_ai_score:score_62.0=31, blocked_ai_score:ai_score_50_buy_hold_override=10, blocked_ai_score:score_60.0=9`
