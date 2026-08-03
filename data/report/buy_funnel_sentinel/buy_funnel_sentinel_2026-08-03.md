# BUY Funnel Sentinel 2026-08-03

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
- submit_contract_weak_matches: `BROKER_RECEIPT, BUDGET_PASS_COLLAPSE, ECONOMIC_PARTICIPATION, FILL_QUALITY, LATENCY_PRE_SUBMIT, SIM_REAL_AUTHORITY, TELEGRAM_POST_SUBMIT_ONLY, UPSTREAM_GATE`

## 근거

- as_of: `2026-08-03T15:20:05`
- baseline_date: `2026-07-31`
- ai_confirmed unique: `198`
- budget_pass unique: `128`
- latency_pass unique: `31`
- submitted unique: `9`
- holding_started unique: `8`
- budget/ai unique: `64.6%` (baseline `65.4`)
- submitted/ai unique: `4.5%` (baseline `3.7`)
- economic bundles: `observed=7, valid=7, probe_only=7, partial_residual=0, full=0`
- economic submitted/requested: `qty=7/199 (3.5%), notional=348450/2398370 (14.5%)`
- economic participation by venue: `{'KRX': {'bundle_count': 7, 'probe_only_bundle_count': 7, 'partial_residual_bundle_count': 0, 'full_submitted_bundle_count': 0, 'requested_qty': 199, 'submitted_qty': 7, 'requested_notional_krw': 2398370, 'submitted_notional_krw': 348450, 'submitted_qty_to_requested_qty_pct': 3.5, 'submitted_notional_to_requested_notional_pct': 14.5}}`
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_overbought:-=755, blocked_strength_momentum:insufficient_history=705, blocked_strength_momentum:below_window_buy_value=638, blocked_liquidity:-=481, blocked_strength_momentum:below_strength_base=429`
- swing blockers: `-`
- upstream blockers: `first_ai_wait:-=298, blocked_ai_score:ai_score_50_buy_hold_override=139, wait65_79_ev_candidate:score_65.0=105, blocked_ai_score:score_65.0=53, blocked_ai_score:score_11.0=52`
- AI terminal reasons: `ai_terminal:first_ai_wait_big_bite_not_confirmed=298, ai_terminal:entry_policy_no_buy_score_prior=261`
- latency blockers: `latency_block:latency_state_danger=358`
- price guards: `pre_submit_entry_ai_authority_guard_block:fresh_ai_drop_real_buy_veto=11, pre_submit_entry_ai_authority_guard_block:fresh_ai_wait_observation_only_probe_veto=9, pre_submit_entry_ai_authority_guard_block:entry_ai_result_stale_or_untrusted=6, pre_submit_entry_ai_authority_guard_block:entry_ai_score_unavailable=3`
- quote refresh: `attempted=116, applied=47, latency_recovered=3, submitted_after_refresh=2`
- quote refresh downstream: `{'order_bundle_submitted': 2, 'price_guard_or_revalidation': 1}`

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

- `5m`: ai=4, budget=8, latency=3, submitted=0, top=`latency_block:latency_state_danger=15, pre_submit_entry_ai_authority_guard_block:fresh_ai_wait_observation_only_probe_veto=2, blocked_strength_momentum:insufficient_history=2`, swing=`-`, upstream=`blocked_ai_score:score_13.0=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=1`
- `10m`: ai=7, budget=18, latency=6, submitted=0, top=`latency_block:latency_state_danger=28, blocked_overbought:-=11, blocked_strength_momentum:insufficient_history=9`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=3, blocked_ai_score:score_13.0=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=1`
- `30m`: ai=22, budget=39, latency=7, submitted=0, top=`latency_block:latency_state_danger=73, blocked_strength_momentum:insufficient_history=58, blocked_overbought:-=38`, swing=`-`, upstream=`first_ai_wait:-=12, blocked_ai_score:ai_score_50_buy_hold_override=8, wait65_79_ev_candidate:score_65.0=4`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=14, ai_terminal:first_ai_wait_big_bite_not_confirmed=12`
