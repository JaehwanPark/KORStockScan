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

- as_of: `2026-07-13T12:15:03`
- baseline_date: `2026-07-10`
- ai_confirmed unique: `20`
- budget_pass unique: `27`
- latency_pass unique: `2`
- submitted unique: `1`
- holding_started unique: `1`
- budget/ai unique: `135.0%` (baseline `48.4`)
- submitted/ai unique: `5.0%` (baseline `6.3`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:below_window_buy_value=178, latency_block:latency_state_danger=36, blocked_liquidity:-=26, blocked_ai_score:ai_score_50_buy_hold_override=26, first_ai_wait:-=17`
- swing blockers: `-`
- upstream blockers: `blocked_ai_score:ai_score_50_buy_hold_override=26, first_ai_wait:-=17, blocked_ai_score:score_0.0=10, blocked_ai_score:score_58.0=7, blocked_ai_score:score_62.0=5`
- AI terminal reasons: `ai_terminal:entry_policy_no_buy_score_prior=26, ai_terminal:first_ai_wait_big_bite_not_confirmed=17`
- latency blockers: `latency_block:latency_state_danger=36`
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

- `5m`: ai=0, budget=1, latency=0, submitted=0, top=`blocked_liquidity:-=2, blocked_ai_score:ai_score_50_buy_hold_override=2, blocked_strength_momentum:below_window_buy_value=2`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=2`, ai_terminal=`-`
- `10m`: ai=1, budget=1, latency=0, submitted=0, top=`blocked_strength_momentum:below_window_buy_value=7, blocked_liquidity:-=4, blocked_ai_score:ai_score_50_buy_hold_override=3`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=3, blocked_ai_score:score_0.0=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=1`
- `30m`: ai=4, budget=3, latency=0, submitted=0, top=`blocked_strength_momentum:below_window_buy_value=45, blocked_ai_score:ai_score_50_buy_hold_override=6, blocked_liquidity:-=6`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=6, blocked_ai_score:score_0.0=3, blocked_ai_score:score_57.0=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=5`
