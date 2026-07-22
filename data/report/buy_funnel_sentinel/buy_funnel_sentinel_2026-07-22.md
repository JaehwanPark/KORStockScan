# BUY Funnel Sentinel 2026-07-22

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

- as_of: `2026-07-22T09:10:01`
- baseline_date: `2026-07-21`
- ai_confirmed unique: `2`
- budget_pass unique: `2`
- latency_pass unique: `1`
- submitted unique: `0`
- holding_started unique: `0`
- budget/ai unique: `100.0%` (baseline `0.0`)
- submitted/ai unique: `0.0%` (baseline `0.0`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:insufficient_history=9, blocked_strength_momentum:below_window_buy_value=3, latency_block:latency_state_danger=1, pre_submit_entry_ai_authority_guard_block:entry_ai_score_unavailable=1, blocked_liquidity:-=1`
- swing blockers: `-`
- upstream blockers: `first_ai_wait:-=1`
- AI terminal reasons: `ai_terminal:first_ai_wait_big_bite_not_confirmed=1`
- latency blockers: `latency_block:latency_state_danger=1`
- price guards: `pre_submit_entry_ai_authority_guard_block:entry_ai_score_unavailable=1`
- quote refresh: `attempted=2, applied=2, latency_recovered=1, submitted_after_refresh=0`
- quote refresh downstream: `{'price_guard_or_revalidation': 1}`

## 금지된 자동변경

- `score_threshold_relaxation`
- `spread_cap_relaxation`
- `fallback_reenable`
- `live_threshold_runtime_mutation`
- `bot_restart`

## 권고 액션

- Continue monitoring; no dynamic action required.

## Window Summary

- `5m`: ai=2, budget=2, latency=1, submitted=0, top=`blocked_strength_momentum:insufficient_history=9, blocked_strength_momentum:below_window_buy_value=3, latency_block:latency_state_danger=1`, swing=`-`, upstream=`first_ai_wait:-=1`, ai_terminal=`ai_terminal:first_ai_wait_big_bite_not_confirmed=1`
- `10m`: ai=2, budget=2, latency=1, submitted=0, top=`blocked_strength_momentum:insufficient_history=9, blocked_strength_momentum:below_window_buy_value=3, latency_block:latency_state_danger=1`, swing=`-`, upstream=`first_ai_wait:-=1`, ai_terminal=`ai_terminal:first_ai_wait_big_bite_not_confirmed=1`
- `30m`: ai=2, budget=2, latency=1, submitted=0, top=`blocked_strength_momentum:insufficient_history=9, blocked_strength_momentum:below_window_buy_value=3, latency_block:latency_state_danger=1`, swing=`-`, upstream=`first_ai_wait:-=1`, ai_terminal=`ai_terminal:first_ai_wait_big_bite_not_confirmed=1`
