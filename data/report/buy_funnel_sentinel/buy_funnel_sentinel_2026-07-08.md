# BUY Funnel Sentinel 2026-07-08

## 판정

- primary: `PRICE_GUARD_DROUGHT`
- secondary: `LATENCY_DROUGHT, UPSTREAM_AI_THRESHOLD`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `false`
- followup_route: `pre_submit_price_guard_review`
- followup_owner: `postclose_threshold_cycle`
- runtime_effect: `report_only_no_mutation`
- submit_contract_downstream: `code_improvement_workorder, lifecycle_decision_matrix.submit_bucket_attribution, threshold_cycle_ev_report, runtime_approval_summary, postclose_verifier`
- submit_contract_weak_matches: `LATENCY_PRE_SUBMIT, PRICE_REVALIDATION, UPSTREAM_GATE`

## 근거

- as_of: `2026-07-08T10:00:03`
- baseline_date: `2026-07-07`
- ai_confirmed unique: `12`
- budget_pass unique: `3`
- latency_pass unique: `1`
- submitted unique: `1`
- holding_started unique: `1`
- budget/ai unique: `25.0%` (baseline `16.7`)
- submitted/ai unique: `8.3%` (baseline `16.7`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `first_ai_wait:-=12, blocked_strength_momentum:below_window_buy_value=11, blocked_vpw:-=8, blocked_strength_momentum:below_buy_ratio=7, blocked_strength_momentum:below_strength_base=7`
- swing blockers: `-`
- upstream blockers: `first_ai_wait:-=12, blocked_ai_score:score_62.0=2, blocked_ai_score:ai_score_50_buy_hold_override=1, blocked_ai_score:score_0.0=1`
- AI terminal reasons: `ai_terminal:first_ai_wait_big_bite_not_confirmed=12, ai_terminal:entry_policy_no_buy_score_prior=3`
- latency blockers: `latency_block:latency_state_danger=5`
- price guards: `pre_submit_price_guard_block:ai_tier2_use_defensive=2, scale_in_price_guard_block:invalid_spread=1`
- quote refresh: `attempted=3, applied=2, latency_recovered=0, submitted_after_refresh=0`
- quote refresh downstream: `{}`

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

- `5m`: ai=2, budget=0, latency=0, submitted=0, top=`blocked_strength_momentum:below_window_buy_value=3, blocked_ai_score:score_62.0=2, blocked_vpw:-=1`, swing=`-`, upstream=`blocked_ai_score:score_62.0=2, first_ai_wait:-=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=2, ai_terminal:first_ai_wait_big_bite_not_confirmed=1`
- `10m`: ai=2, budget=1, latency=0, submitted=0, top=`blocked_strength_momentum:below_window_buy_value=3, blocked_ai_score:score_62.0=2, latency_block:latency_state_danger=1`, swing=`-`, upstream=`blocked_ai_score:score_62.0=2, first_ai_wait:-=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=2, ai_terminal:first_ai_wait_big_bite_not_confirmed=1`
- `30m`: ai=7, budget=2, latency=0, submitted=0, top=`first_ai_wait:-=7, blocked_vpw:-=6, latency_block:latency_state_danger=4`, swing=`-`, upstream=`first_ai_wait:-=7, blocked_ai_score:score_62.0=2`, ai_terminal=`ai_terminal:first_ai_wait_big_bite_not_confirmed=7, ai_terminal:entry_policy_no_buy_score_prior=2`
