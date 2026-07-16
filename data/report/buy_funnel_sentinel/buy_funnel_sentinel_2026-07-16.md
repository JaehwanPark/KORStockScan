# BUY Funnel Sentinel 2026-07-16

## 판정

- primary: `UPSTREAM_AI_THRESHOLD`
- secondary: `-`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `false`
- followup_route: `score65_74_counterfactual_review`
- followup_owner: `postclose_threshold_cycle`
- runtime_effect: `report_only_no_mutation`
- submit_contract_downstream: `code_improvement_workorder, lifecycle_decision_matrix.submit_bucket_attribution, threshold_cycle_ev_report, runtime_approval_summary, postclose_verifier`
- submit_contract_weak_matches: `UPSTREAM_GATE`

## 근거

- as_of: `2026-07-16T15:20:02`
- baseline_date: `2026-07-15`
- ai_confirmed unique: `17`
- budget_pass unique: `0`
- latency_pass unique: `0`
- submitted unique: `0`
- holding_started unique: `0`
- budget/ai unique: `0.0%` (baseline `65.7`)
- submitted/ai unique: `0.0%` (baseline `11.4`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_zero_qty:-=289, blocked_strength_momentum:below_window_buy_value=83, first_ai_wait:-=12, blocked_ai_score:ai_score_50_buy_hold_override=11, blocked_ai_score:score_62.0=10`
- swing blockers: `-`
- upstream blockers: `first_ai_wait:-=12, blocked_ai_score:ai_score_50_buy_hold_override=11, blocked_ai_score:score_62.0=10, blocked_ai_score:score_58.0=6, blocked_ai_score:score_0.0=3`
- AI terminal reasons: `ai_terminal:entry_policy_no_buy_score_prior=21, ai_terminal:first_ai_wait_big_bite_not_confirmed=12`
- latency blockers: `-`
- price guards: `-`
- quote refresh: `attempted=0, applied=0, latency_recovered=0, submitted_after_refresh=0`
- quote refresh downstream: `{}`

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

- `5m`: ai=0, budget=0, latency=0, submitted=0, top=`blocked_zero_qty:-=4`, swing=`-`, upstream=`-`, ai_terminal=`-`
- `10m`: ai=0, budget=0, latency=0, submitted=0, top=`blocked_zero_qty:-=6`, swing=`-`, upstream=`-`, ai_terminal=`-`
- `30m`: ai=0, budget=0, latency=0, submitted=0, top=`blocked_zero_qty:-=22`, swing=`-`, upstream=`-`, ai_terminal=`-`
