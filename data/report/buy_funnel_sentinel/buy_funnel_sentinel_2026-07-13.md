# BUY Funnel Sentinel 2026-07-13

## 판정

- primary: `SUBMIT_DROUGHT_CRITICAL`
- secondary: `LATENCY_DROUGHT, UPSTREAM_AI_THRESHOLD`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `false`
- followup_route: `entry_submit_drought_auto_workorder`
- followup_owner: `postclose_threshold_cycle_and_lifecycle_decision_matrix`
- runtime_effect: `auto_workorder_no_intraday_mutation`
- submit_contract_downstream: `code_improvement_workorder, lifecycle_decision_matrix.submit_bucket_attribution, threshold_cycle_ev_report, runtime_approval_summary, postclose_verifier`
- submit_contract_weak_matches: `BROKER_RECEIPT, BUDGET_PASS_COLLAPSE, FILL_QUALITY, LATENCY_PRE_SUBMIT, SIM_REAL_AUTHORITY, TELEGRAM_POST_SUBMIT_ONLY, UPSTREAM_GATE`

## 근거

- as_of: `2026-07-13T12:00:02`
- baseline_date: `2026-07-10`
- ai_confirmed unique: `19`
- budget_pass unique: `27`
- latency_pass unique: `2`
- submitted unique: `1`
- holding_started unique: `1`
- budget/ai unique: `142.1%` (baseline `46.6`)
- submitted/ai unique: `5.3%` (baseline `4.5`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:below_window_buy_value=157, latency_block:latency_state_danger=34, blocked_liquidity:-=22, blocked_ai_score:ai_score_50_buy_hold_override=22, first_ai_wait:-=17`
- swing blockers: `-`
- upstream blockers: `blocked_ai_score:ai_score_50_buy_hold_override=22, first_ai_wait:-=17, blocked_ai_score:score_0.0=9, blocked_ai_score:score_58.0=7, blocked_ai_score:score_62.0=5`
- AI terminal reasons: `ai_terminal:entry_policy_no_buy_score_prior=25, ai_terminal:first_ai_wait_big_bite_not_confirmed=17`
- latency blockers: `latency_block:latency_state_danger=34`
- price guards: `pre_submit_entry_ai_authority_guard_block:entry_ai_score_unavailable=1`
- quote refresh: `attempted=20, applied=17, latency_recovered=1, submitted_after_refresh=1`
- quote refresh downstream: `{'order_bundle_submitted': 1}`

## 금지된 자동변경

- `score_threshold_relaxation`
- `spread_cap_relaxation`
- `fallback_reenable`
- `live_threshold_runtime_mutation`
- `bot_restart`

## 권고 액션

- Auto-route ai_confirmed -> budget_pass -> latency_pass -> order_bundle_submitted drought into postclose workorder/LDM handoff.
- Split root cause into upstream gate, budget pass, latency/pre-submit guard, and broker receipt buckets before tuning thresholds.
- Do not require operator approval for submitted drought surfacing or downstream workorder generation.

## Window Summary

- `5m`: ai=2, budget=1, latency=0, submitted=0, top=`blocked_strength_momentum:below_window_buy_value=8, latency_block:latency_state_danger=4, blocked_ai_score:score_62.0=1`, swing=`-`, upstream=`blocked_ai_score:score_62.0=1, blocked_ai_score:score_0.0=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=2`
- `10m`: ai=2, budget=1, latency=0, submitted=0, top=`blocked_strength_momentum:below_window_buy_value=20, latency_block:latency_state_danger=4, blocked_ai_score:score_57.0=1`, swing=`-`, upstream=`blocked_ai_score:score_57.0=1, blocked_ai_score:ai_score_50_buy_hold_override=1, blocked_ai_score:score_62.0=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=3`
- `30m`: ai=8, budget=5, latency=0, submitted=0, top=`blocked_strength_momentum:below_window_buy_value=52, blocked_ai_score:score_0.0=6, blocked_liquidity:-=5`, swing=`-`, upstream=`blocked_ai_score:score_0.0=6, blocked_ai_score:ai_score_50_buy_hold_override=5, first_ai_wait:-=3`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=9, ai_terminal:first_ai_wait_big_bite_not_confirmed=3`
