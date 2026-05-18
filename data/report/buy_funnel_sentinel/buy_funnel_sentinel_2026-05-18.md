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

- as_of: `2026-05-18T15:20:12`
- baseline_date: `2026-05-15`
- ai_confirmed unique: `67`
- budget_pass unique: `2`
- latency_pass unique: `0`
- submitted unique: `0`
- holding_started unique: `0`
- budget/ai unique: `3.0%` (baseline `1.0`)
- submitted/ai unique: `0.0%` (baseline `0.0`)
- top blockers: `blocked_swing_score_vpw:-=480944, blocked_strength_momentum:below_window_buy_value=179281, blocked_strength_momentum:below_strength_base=132857, blocked_overbought:-=77587, blocked_swing_gap:-=75557`
- upstream blockers: `blocked_ai_score:score_62.0=413, blocked_ai_score:ai_score_50_buy_hold_override=238, first_ai_wait:-=116, blocked_ai_score:score_60.0=72, blocked_ai_score:score_58.0=54`
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

- `5m`: ai=0, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=6323, blocked_swing_gap:-=1669, blocked_gatekeeper_reject:눌림 대기=5`, upstream=`-`
- `10m`: ai=0, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=13859, blocked_swing_gap:-=3716, blocked_gatekeeper_reject:눌림 대기=5`, upstream=`-`
- `30m`: ai=12, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=41510, blocked_swing_gap:-=10286, blocked_strength_momentum:below_window_buy_value=6526`, upstream=`blocked_ai_score:score_62.0=14, blocked_ai_score:ai_score_50_buy_hold_override=6, blocked_ai_score:score_60.0=5`
