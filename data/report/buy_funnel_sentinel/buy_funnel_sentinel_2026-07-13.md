# BUY Funnel Sentinel 2026-07-13

## 판정

- primary: `SUBMIT_DROUGHT_CRITICAL`
- secondary: `LATENCY_DROUGHT`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `false`
- followup_route: `entry_submit_drought_auto_workorder`
- followup_owner: `postclose_threshold_cycle_and_lifecycle_decision_matrix`
- runtime_effect: `auto_workorder_no_intraday_mutation`
- submit_contract_downstream: `code_improvement_workorder, lifecycle_decision_matrix.submit_bucket_attribution, threshold_cycle_ev_report, runtime_approval_summary, postclose_verifier`
- submit_contract_weak_matches: `BROKER_RECEIPT, BUDGET_PASS_COLLAPSE, FILL_QUALITY, LATENCY_PRE_SUBMIT, SIM_REAL_AUTHORITY, TELEGRAM_POST_SUBMIT_ONLY`

## 근거

- as_of: `2026-07-13T10:10:02`
- baseline_date: `2026-07-10`
- ai_confirmed unique: `7`
- budget_pass unique: `11`
- latency_pass unique: `1`
- submitted unique: `0`
- holding_started unique: `0`
- budget/ai unique: `157.1%` (baseline `63.2`)
- submitted/ai unique: `0.0%` (baseline `2.6`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:below_window_buy_value=16, latency_block:latency_state_danger=10, blocked_ai_score:ai_score_50_buy_hold_override=9, first_ai_wait:-=6, blocked_vpw:-=4`
- swing blockers: `-`
- upstream blockers: `blocked_ai_score:ai_score_50_buy_hold_override=9, first_ai_wait:-=6`
- AI terminal reasons: `ai_terminal:first_ai_wait_big_bite_not_confirmed=6`
- latency blockers: `latency_block:latency_state_danger=10`
- price guards: `pre_submit_entry_ai_authority_guard_block:entry_ai_score_unavailable=1`
- quote refresh: `attempted=8, applied=7, latency_recovered=0, submitted_after_refresh=0`
- quote refresh downstream: `{}`

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

- `5m`: ai=0, budget=0, latency=0, submitted=0, top=`blocked_strength_momentum:below_window_buy_value=1`, swing=`-`, upstream=`-`, ai_terminal=`-`
- `10m`: ai=0, budget=0, latency=0, submitted=0, top=`blocked_strength_momentum:below_window_buy_value=2`, swing=`-`, upstream=`-`, ai_terminal=`-`
- `30m`: ai=7, budget=3, latency=1, submitted=0, top=`blocked_strength_momentum:below_window_buy_value=13, first_ai_wait:-=6, blocked_ai_score:ai_score_50_buy_hold_override=4`, swing=`-`, upstream=`first_ai_wait:-=6, blocked_ai_score:ai_score_50_buy_hold_override=4`, ai_terminal=`ai_terminal:first_ai_wait_big_bite_not_confirmed=6`
