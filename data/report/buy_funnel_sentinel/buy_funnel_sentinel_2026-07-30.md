# BUY Funnel Sentinel 2026-07-30

## 판정

- primary: `NORMAL`
- secondary: `-`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `false`
- followup_route: `normal_no_action`
- followup_owner: `none`
- runtime_effect: `report_only_no_mutation`
- submit_contract_downstream: `code_improvement_workorder, lifecycle_decision_matrix.submit_bucket_attribution, threshold_cycle_ev_report, runtime_approval_summary, postclose_verifier`
- submit_contract_weak_matches: `-`

## 근거

- as_of: `2026-07-30T15:20:02`
- baseline_date: `2026-07-29`
- ai_confirmed unique: `5`
- budget_pass unique: `1`
- latency_pass unique: `0`
- submitted unique: `0`
- holding_started unique: `0`
- budget/ai unique: `20.0%` (baseline `66.7`)
- submitted/ai unique: `0.0%` (baseline `11.1`)
- economic bundles: `observed=0, valid=0, probe_only=0, partial_residual=0, full=0`
- economic submitted/requested: `qty=0/0 (0.0%), notional=0/0 (0.0%)`
- economic participation by venue: `{}`
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:below_window_buy_value=160, blocked_strength_momentum:insufficient_history=49, blocked_ai_score:ai_score_50_buy_hold_override=16, first_ai_wait:-=12, blocked_ai_score:score_0.0=10`
- swing blockers: `-`
- upstream blockers: `blocked_ai_score:ai_score_50_buy_hold_override=16, first_ai_wait:-=12, blocked_ai_score:score_0.0=10, blocked_ai_score:score_11.0=8, blocked_ai_score:score_65.0=3`
- AI terminal reasons: `ai_terminal:entry_policy_no_buy_score_prior=25, ai_terminal:first_ai_wait_big_bite_not_confirmed=12`
- latency blockers: `latency_block:latency_state_danger=6`
- price guards: `-`
- quote refresh: `attempted=1, applied=1, latency_recovered=0, submitted_after_refresh=0`
- quote refresh downstream: `{}`

## 금지된 자동변경

- `score_threshold_relaxation`
- `spread_cap_relaxation`
- `fallback_reenable`
- `live_threshold_runtime_mutation`
- `bot_restart`

## 권고 액션

- Continue monitoring; no dynamic action required.

## Window Summary

- `5m`: ai=0, budget=0, latency=0, submitted=0, top=`-`, swing=`-`, upstream=`-`, ai_terminal=`-`
- `10m`: ai=0, budget=0, latency=0, submitted=0, top=`-`, swing=`-`, upstream=`-`, ai_terminal=`-`
- `30m`: ai=0, budget=0, latency=0, submitted=0, top=`-`, swing=`-`, upstream=`-`, ai_terminal=`-`
