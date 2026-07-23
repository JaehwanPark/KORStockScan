# BUY Funnel Sentinel 2026-07-23

## 판정

- primary: `UPSTREAM_AI_THRESHOLD`
- secondary: `LATENCY_DROUGHT`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `false`
- followup_route: `score65_74_counterfactual_review`
- followup_owner: `postclose_threshold_cycle`
- runtime_effect: `report_only_no_mutation`
- submit_contract_downstream: `code_improvement_workorder, lifecycle_decision_matrix.submit_bucket_attribution, threshold_cycle_ev_report, runtime_approval_summary, postclose_verifier`
- submit_contract_weak_matches: `ECONOMIC_PARTICIPATION, LATENCY_PRE_SUBMIT, UPSTREAM_GATE`

## 근거

- as_of: `2026-07-23T15:20:02`
- baseline_date: `2026-07-22`
- ai_confirmed unique: `33`
- budget_pass unique: `56`
- latency_pass unique: `4`
- submitted unique: `8`
- holding_started unique: `8`
- budget/ai unique: `169.7%` (baseline `246.4`)
- submitted/ai unique: `24.2%` (baseline `32.1`)
- economic bundles: `observed=8, valid=8, probe_only=6, partial_residual=0, full=2`
- economic submitted/requested: `qty=112/1281 (8.7%), notional=3855283/12305394 (31.3%)`
- economic participation by venue: `{'KRX': {'bundle_count': 8, 'probe_only_bundle_count': 6, 'partial_residual_bundle_count': 0, 'full_submitted_bundle_count': 2, 'requested_qty': 1281, 'submitted_qty': 112, 'requested_notional_krw': 12305394, 'submitted_notional_krw': 3855283, 'submitted_qty_to_requested_qty_pct': 8.7, 'submitted_notional_to_requested_notional_pct': 31.3}}`
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:below_window_buy_value=134, first_ai_wait:-=34, latency_block:latency_state_danger=27, blocked_strength_momentum:insufficient_history=22, blocked_vpw:-=10`
- swing blockers: `-`
- upstream blockers: `first_ai_wait:-=34, blocked_ai_score:score_52.0=4, blocked_ai_score:ai_score_50_buy_hold_override=4, blocked_ai_score:score_34.0=3, blocked_ai_score:score_58.0=3`
- AI terminal reasons: `ai_terminal:entry_policy_no_buy_score_prior=43, ai_terminal:first_ai_wait_big_bite_not_confirmed=34`
- latency blockers: `latency_block:latency_state_danger=27, latency_block:tp1_direct_recheck_expired=3`
- price guards: `pre_submit_entry_ai_authority_guard_block:fresh_ai_drop_real_buy_veto=2, pre_submit_entry_ai_authority_guard_block:entry_ai_result_stale_or_untrusted=1`
- quote refresh: `attempted=23, applied=22, latency_recovered=4, submitted_after_refresh=2`
- quote refresh downstream: `{'budget_pass_no_submit_event': 1, 'order_bundle_submitted': 2, 'price_guard_or_revalidation': 1}`

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

- `5m`: ai=1, budget=1, latency=1, submitted=1, top=`-`, swing=`-`, upstream=`-`, ai_terminal=`-`
- `10m`: ai=1, budget=1, latency=1, submitted=1, top=`-`, swing=`-`, upstream=`-`, ai_terminal=`-`
- `30m`: ai=2, budget=4, latency=2, submitted=1, top=`latency_block:latency_state_danger=3, pre_submit_entry_ai_authority_guard_block:fresh_ai_drop_real_buy_veto=1, blocked_ai_score:ai_score_50_buy_hold_override=1`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=1`, ai_terminal=`-`
