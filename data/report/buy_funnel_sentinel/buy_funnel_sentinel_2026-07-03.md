# BUY Funnel Sentinel 2026-07-03

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

- as_of: `2026-07-03T10:45:03`
- baseline_date: `2026-07-02`
- ai_confirmed unique: `8`
- budget_pass unique: `1`
- latency_pass unique: `0`
- submitted unique: `0`
- holding_started unique: `0`
- budget/ai unique: `12.5%` (baseline `0.0`)
- submitted/ai unique: `0.0%` (baseline `0.0`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:below_window_buy_value=56, blocked_strength_momentum:insufficient_history=37, blocked_strength_momentum:below_strength_base=10, blocked_vpw:-=8, first_ai_wait:-=8`
- swing blockers: `-`
- upstream blockers: `first_ai_wait:-=8, blocked_ai_score:ai_score_50_buy_hold_override=3, blocked_ai_score:score_62.0=1, wait65_79_ev_candidate:score_74.0=1, blocked_ai_score:score_58.0=1`
- AI terminal reasons: `ai_terminal:first_ai_wait_big_bite_not_confirmed=8, ai_terminal:blocked_ai_score_below_buy_score_threshold=2`
- latency blockers: `latency_block:latency_state_danger=1`
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

- `5m`: ai=3, budget=0, latency=0, submitted=0, top=`blocked_strength_momentum:insufficient_history=12, blocked_strength_momentum:below_window_buy_value=7, blocked_strength_momentum:below_strength_base=4`, swing=`-`, upstream=`first_ai_wait:-=3, blocked_ai_score:ai_score_50_buy_hold_override=1, wait65_79_ev_candidate:score_68.0=1`, ai_terminal=`ai_terminal:first_ai_wait_big_bite_not_confirmed=3`
- `10m`: ai=5, budget=0, latency=0, submitted=0, top=`blocked_strength_momentum:below_window_buy_value=32, blocked_strength_momentum:insufficient_history=17, blocked_strength_momentum:below_strength_base=8`, swing=`-`, upstream=`first_ai_wait:-=4, blocked_ai_score:ai_score_50_buy_hold_override=3, blocked_ai_score:score_58.0=1`, ai_terminal=`ai_terminal:first_ai_wait_big_bite_not_confirmed=4, ai_terminal:blocked_ai_score_below_buy_score_threshold=1`
- `30m`: ai=8, budget=1, latency=0, submitted=0, top=`blocked_strength_momentum:below_window_buy_value=56, blocked_strength_momentum:insufficient_history=37, blocked_strength_momentum:below_strength_base=10`, swing=`-`, upstream=`first_ai_wait:-=8, blocked_ai_score:ai_score_50_buy_hold_override=3, blocked_ai_score:score_62.0=1`, ai_terminal=`ai_terminal:first_ai_wait_big_bite_not_confirmed=8, ai_terminal:blocked_ai_score_below_buy_score_threshold=2`
