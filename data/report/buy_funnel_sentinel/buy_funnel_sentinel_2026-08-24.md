# BUY Funnel Sentinel 2026-08-24

## 판정

- primary: `SUBMIT_DROUGHT_CRITICAL`
- secondary: `ENTRY_AI_AUTHORITY_DROUGHT, LATENCY_DROUGHT, UPSTREAM_AI_THRESHOLD`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `false`
- followup_route: `entry_submit_drought_auto_workorder`
- followup_owner: `postclose_threshold_cycle_and_lifecycle_decision_matrix`
- runtime_effect: `auto_workorder_no_intraday_mutation`
- submit_contract_downstream: `code_improvement_workorder, lifecycle_decision_matrix.submit_bucket_attribution, threshold_cycle_ev_report, runtime_approval_summary, postclose_verifier`
- submit_contract_weak_matches: `BROKER_RECEIPT, BUDGET_PASS_COLLAPSE, ECONOMIC_PARTICIPATION, ENTRY_AI_AUTHORITY_REVALIDATION, FILL_QUALITY, LATENCY_PRE_SUBMIT, SIM_REAL_AUTHORITY, TELEGRAM_POST_SUBMIT_ONLY, UPSTREAM_GATE`

## 근거

- as_of: `2026-08-24T15:20:04`
- baseline_date: `2026-08-21`
- ai_confirmed unique: `85`
- budget_pass unique: `80`
- latency_pass unique: `33`
- submitted unique: `10`
- holding_started unique: `9`
- budget/ai unique: `94.1%` (baseline `173.1`)
- submitted/ai unique: `11.8%` (baseline `23.1`)
- economic bundles: `observed=11, valid=11, probe_only=11, partial_residual=0, full=0`
- economic submitted/requested: `qty=11/11 (100.0%), notional=461750/461750 (100.0%)`
- economic participation by venue: `{'KRX': {'bundle_count': 11, 'probe_only_bundle_count': 11, 'partial_residual_bundle_count': 0, 'full_submitted_bundle_count': 0, 'requested_qty': 11, 'submitted_qty': 11, 'requested_notional_krw': 461750, 'submitted_notional_krw': 461750, 'submitted_qty_to_requested_qty_pct': 100.0, 'submitted_notional_to_requested_notional_pct': 100.0}}`
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:below_window_buy_value=619, blocked_overbought:-=372, latency_block:latency_state_danger=317, blocked_strength_momentum:insufficient_history=270, blocked_liquidity:-=186`
- swing blockers: `-`
- upstream blockers: `blocked_ai_score:ai_score_50_buy_hold_override=107, first_ai_wait:-=62, wait65_79_ev_candidate:score_70.0=57, blocked_ai_score:score_70.0=22, blocked_ai_score:score_0.0=19`
- AI terminal reasons: `ai_terminal:entry_policy_no_buy_score_prior=123, ai_terminal:first_ai_wait_big_bite_not_confirmed=62`
- AI actions: `events={'DROP': 168, 'NOT_EVALUATED': 1, 'WAIT': 125}, unique={'DROP': 168, 'NOT_EVALUATED': 1, 'WAIT': 125}`
- budget/AI lineage: `{'status': 'explicit_ai_trace_budget_block_observed', 'pipeline_stage_order_contract': 'latest_watching_ai_to_budget_precheck_to_final_authority_revalidation', 'raw_ai_budget_census_is_causal': False, 'ai_trace_count': 319, 'ai_trace_source_stage_counts': {'ai_confirmed': 294, 'early_accel_strong_bundle_recheck_corrected': 15, 'early_accel_strong_bundle_recheck_failed': 10}, 'budget_or_block_event_count': 629, 'lineage_contract_event_count': 629, 'lineage_contract_coverage_pct': 100.0, 'pre_ai_parent_not_expected_event_count': 554, 'lineage_join_eligible_event_count': 28, 'lineage_contract_missing_event_count': 0, 'lineage_field_present_count': 28, 'parent_trace_missing_when_expected_event_count': 0, 'parent_attempt_without_trusted_result_event_count': 47, 'ai_attempt_result_unavailable_parent_not_expected_event_count': 47, 'parent_trace_missing_without_attempt_event_count': 0, 'lineage_exact_trusted_count': 26, 'lineage_untrusted_or_stale_event_count': 2, 'lineage_untrusted_or_stale_reason_counts': {'source_stale': 2}, 'lineage_joined_event_count': 26, 'exact_parent_trace_unresolved_event_count': 0, 'lineage_join_coverage_pct': 92.86, 'raw_event_lineage_join_coverage_pct': 4.13, 'lineage_join_coverage_denominator': 'events_with_a_trusted_ai_result_expected; excludes_pre_ai_and_explicit_attempt_result_unavailable', 'linked_budget_pass_trace_count': 16, 'linked_budget_block_trace_count': 6, 'linked_stage_counts': {'blocked_zero_qty': 6, 'budget_pass': 20}, 'runtime_effect': False, 'allowed_runtime_apply': False}`
- latency blockers: `latency_block:latency_state_danger=317, latency_block:tp1_direct_recheck_expired=5`
- price guards: `entry_ai_price_canary_fallback:pre_submit_price_guard=4, entry_ai_price_canary_fallback:skip_low_confidence=1`
- quote refresh: `attempted=74, applied=64, latency_recovered=23, submitted_after_refresh=5`
- quote refresh downstream: `{'entry_ai_authority_revalidation': 16, 'no_downstream_event': 1, 'order_bundle_submitted': 5, 'upstream_block_after_latency_recovery': 1}`

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

- `5m`: ai=3, budget=2, latency=0, submitted=0, top=`blocked_overbought:-=9, latency_block:latency_state_danger=5, blocked_vpw:-=3`, swing=`-`, upstream=`blocked_ai_score:score_7.0=1, wait65_79_ev_candidate:score_70.0=1, blocked_ai_score:score_70.0=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=3, ai_terminal:first_ai_wait_big_bite_not_confirmed=1`
- `10m`: ai=6, budget=4, latency=1, submitted=0, top=`blocked_overbought:-=19, latency_block:latency_state_danger=7, blocked_vpw:-=6`, swing=`-`, upstream=`first_ai_wait:-=2, wait65_79_ev_candidate:score_70.0=2, blocked_ai_score:score_70.0=2`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=6, ai_terminal:first_ai_wait_big_bite_not_confirmed=2`
- `30m`: ai=14, budget=7, latency=4, submitted=1, top=`blocked_overbought:-=41, blocked_strength_momentum:below_strength_base=15, latency_block:latency_state_danger=12`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=9, first_ai_wait:-=4, wait65_79_ev_candidate:score_70.0=3`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=7, ai_terminal:first_ai_wait_big_bite_not_confirmed=4`
