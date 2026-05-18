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

- as_of: `2026-05-18T12:55:08`
- baseline_date: `2026-05-15`
- ai_confirmed unique: `62`
- budget_pass unique: `2`
- latency_pass unique: `0`
- submitted unique: `0`
- holding_started unique: `0`
- budget/ai unique: `3.2%` (baseline `0.0`)
- submitted/ai unique: `0.0%` (baseline `0.0`)
- top blockers: `blocked_swing_score_vpw:-=298214, blocked_strength_momentum:below_window_buy_value=112668, blocked_strength_momentum:below_strength_base=101735, blocked_overbought:-=42918, blocked_swing_gap:-=35090`
- upstream blockers: `blocked_ai_score:score_62.0=242, blocked_ai_score:ai_score_50_buy_hold_override=126, first_ai_wait:-=67, blocked_ai_score:score_60.0=49, blocked_ai_score:score_58.0=34`
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

- `5m`: ai=10, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=5571, blocked_strength_momentum:below_window_buy_value=1626, blocked_overbought:-=1593`, upstream=`blocked_ai_score:score_62.0=6, blocked_ai_score:ai_score_50_buy_hold_override=5, first_ai_wait:-=4`
- `10m`: ai=12, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=12404, blocked_strength_momentum:below_window_buy_value=4083, blocked_strength_momentum:below_strength_base=3806`, upstream=`first_ai_wait:-=10, blocked_ai_score:ai_score_50_buy_hold_override=10, blocked_ai_score:score_62.0=9`
- `30m`: ai=21, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=37080, blocked_strength_momentum:below_window_buy_value=14884, blocked_overbought:-=10369`, upstream=`blocked_ai_score:score_62.0=33, blocked_ai_score:ai_score_50_buy_hold_override=29, first_ai_wait:-=15`
