# BUY Funnel Sentinel 2026-08-05

## 판정

- primary: `SUBMIT_DROUGHT_CRITICAL`
- secondary: `PRICE_GUARD_DROUGHT, LATENCY_DROUGHT, UPSTREAM_AI_THRESHOLD`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `false`
- followup_route: `entry_submit_drought_auto_workorder`
- followup_owner: `postclose_threshold_cycle_and_lifecycle_decision_matrix`
- runtime_effect: `auto_workorder_no_intraday_mutation`
- submit_contract_downstream: `code_improvement_workorder, lifecycle_decision_matrix.submit_bucket_attribution, threshold_cycle_ev_report, runtime_approval_summary, postclose_verifier`
- submit_contract_weak_matches: `BROKER_RECEIPT, BUDGET_PASS_COLLAPSE, FILL_QUALITY, LATENCY_PRE_SUBMIT, PRICE_REVALIDATION, SIM_REAL_AUTHORITY, TELEGRAM_POST_SUBMIT_ONLY, UPSTREAM_GATE`

## 근거

- as_of: `2026-08-05T19:49:58`
- baseline_date: `2026-08-04`
- ai_confirmed unique: `173`
- budget_pass unique: `3`
- latency_pass unique: `2`
- submitted unique: `0`
- holding_started unique: `0`
- budget/ai unique: `1.7%` (baseline `43.9`)
- submitted/ai unique: `0.0%` (baseline `5.7`)
- economic bundles: `observed=0, valid=0, probe_only=0, partial_residual=0, full=0`
- economic submitted/requested: `qty=0/0 (0.0%), notional=0/0 (0.0%)`
- economic participation by venue: `{}`
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:insufficient_history=1998, blocked_strength_momentum:below_window_buy_value=1360, blocked_overbought:-=565, blocked_strength_momentum:below_strength_base=523, blocked_zero_qty:-=410`
- swing blockers: `-`
- upstream blockers: `blocked_ai_score:ai_score_50_buy_hold_override=241, first_ai_wait:-=144, blocked_ai_score:score_11.0=65, blocked_ai_score:score_0.0=65, wait65_79_ev_candidate:score_65.0=37`
- AI terminal reasons: `ai_terminal:entry_policy_no_buy_score_prior=314, ai_terminal:first_ai_wait_big_bite_not_confirmed=144`
- latency blockers: `latency_block:latency_state_danger=2`
- price guards: `pre_submit_entry_ai_authority_guard_block:fresh_ai_wait_observation_only_probe_veto=2, pre_submit_entry_ai_authority_guard_block:entry_ai_result_stale_or_untrusted=1, pre_submit_entry_ai_authority_guard_block:fresh_ai_drop_real_buy_veto=1`
- quote refresh: `attempted=3, applied=0, latency_recovered=0, submitted_after_refresh=0`
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

- `5m`: ai=0, budget=0, latency=0, submitted=0, top=`blocked_strength_momentum:below_window_buy_value=4, blocked_strength_momentum:insufficient_history=4, blocked_ai_score:ai_score_50_buy_hold_override=1`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=1`, ai_terminal=`-`
- `10m`: ai=2, budget=0, latency=0, submitted=0, top=`blocked_strength_momentum:below_window_buy_value=21, blocked_strength_momentum:insufficient_history=10, blocked_strength_momentum:below_strength_base=3`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=2, blocked_ai_score:score_11.0=1, blocked_ai_score:score_0.0=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=2`
- `30m`: ai=6, budget=0, latency=0, submitted=0, top=`blocked_strength_momentum:insufficient_history=77, blocked_strength_momentum:below_window_buy_value=47, blocked_overbought:-=10`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=7, blocked_ai_score:score_0.0=2, blocked_ai_score:score_13.0=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=4`
