# BUY Funnel Sentinel 2026-07-03

## 판정

- primary: `UPSTREAM_AI_THRESHOLD`
- secondary: `LATENCY_DROUGHT`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `false`
- followup_route: `score65_74_counterfactual_review`
- followup_owner: `postclose_threshold_cycle`
- runtime_effect: `report_only_no_mutation`
- submit_contract_downstream: `code_improvement_workorder, lifecycle_decision_matrix.submit_bucket_attribution, threshold_cycle_ev_report, runtime_approval_summary, postclose_verifier`
- submit_contract_weak_matches: `LATENCY_PRE_SUBMIT, UPSTREAM_GATE`

## 근거

- as_of: `2026-07-03T15:20:02`
- baseline_date: `2026-07-02`
- ai_confirmed unique: `37`
- budget_pass unique: `18`
- latency_pass unique: `12`
- submitted unique: `12`
- holding_started unique: `11`
- budget/ai unique: `48.6%` (baseline `57.1`)
- submitted/ai unique: `32.4%` (baseline `33.9`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:below_window_buy_value=576, blocked_strength_momentum:insufficient_history=453, blocked_strength_momentum:below_strength_base=290, blocked_vpw:-=101, blocked_overbought:-=76`
- swing blockers: `-`
- upstream blockers: `first_ai_wait:-=54, blocked_ai_score:score_62.0=27, blocked_ai_score:ai_score_50_buy_hold_override=17, blocked_ai_score:score_60.0=12, blocked_ai_score:score_64.0=10`
- AI terminal reasons: `ai_terminal:blocked_ai_score_below_buy_score_threshold=85, ai_terminal:first_ai_wait_big_bite_not_confirmed=54`
- latency blockers: `latency_block:latency_state_danger=73`
- price guards: `scale_in_price_guard_block:micro_vwap_bp<-5.0=2, entry_ai_price_canary_fallback:above_best_ask=1`
- quote refresh: `attempted=18, applied=11, latency_recovered=1, submitted_after_refresh=1`
- quote refresh downstream: `{'order_bundle_submitted': 1}`

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

- `5m`: ai=0, budget=2, latency=1, submitted=1, top=`blocked_strength_momentum:insufficient_history=11, blocked_strength_momentum:below_strength_base=6, latency_block:latency_state_danger=1`, swing=`-`, upstream=`-`, ai_terminal=`-`
- `10m`: ai=1, budget=3, latency=2, submitted=2, top=`blocked_strength_momentum:insufficient_history=20, blocked_strength_momentum:below_strength_base=11, latency_block:latency_state_danger=3`, swing=`-`, upstream=`first_ai_wait:-=1, blocked_ai_score:score_69.0=1`, ai_terminal=`ai_terminal:first_ai_wait_big_bite_not_confirmed=1, ai_terminal:blocked_ai_score_below_buy_score_threshold=1`
- `30m`: ai=6, budget=4, latency=3, submitted=3, top=`blocked_strength_momentum:insufficient_history=57, blocked_strength_momentum:below_strength_base=24, latency_block:latency_state_danger=13`, swing=`-`, upstream=`first_ai_wait:-=3, blocked_ai_score:score_60.0=2, blocked_ai_score:score_69.0=2`, ai_terminal=`ai_terminal:blocked_ai_score_below_buy_score_threshold=7, ai_terminal:first_ai_wait_big_bite_not_confirmed=3`
