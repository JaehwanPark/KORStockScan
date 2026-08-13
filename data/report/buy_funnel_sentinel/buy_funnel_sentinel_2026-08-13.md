# BUY Funnel Sentinel 2026-08-13

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

- as_of: `2026-08-13T15:20:04`
- baseline_date: `2026-08-12`
- ai_confirmed unique: `80`
- budget_pass unique: `76`
- latency_pass unique: `29`
- submitted unique: `5`
- holding_started unique: `5`
- budget/ai unique: `95.0%` (baseline `114.0`)
- submitted/ai unique: `6.2%` (baseline `0.0`)
- economic bundles: `observed=1, valid=1, probe_only=1, partial_residual=0, full=0`
- economic submitted/requested: `qty=1/21 (4.8%), notional=13190/276570 (4.8%)`
- economic participation by venue: `{'KRX': {'bundle_count': 1, 'probe_only_bundle_count': 1, 'partial_residual_bundle_count': 0, 'full_submitted_bundle_count': 0, 'requested_qty': 21, 'submitted_qty': 1, 'requested_notional_krw': 276570, 'submitted_notional_krw': 13190, 'submitted_qty_to_requested_qty_pct': 4.8, 'submitted_notional_to_requested_notional_pct': 4.8}}`
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:insufficient_history=740, blocked_strength_momentum:below_window_buy_value=562, blocked_overbought:-=284, blocked_zero_qty:-=161, blocked_vpw:-=156`
- swing blockers: `-`
- upstream blockers: `blocked_ai_score:ai_score_50_buy_hold_override=89, wait65_79_ev_candidate:score_70.0=53, first_ai_wait:-=44, blocked_ai_score:score_4.0=32, blocked_ai_score:score_70.0=23`
- AI terminal reasons: `ai_terminal:entry_policy_no_buy_score_prior=130, ai_terminal:first_ai_wait_big_bite_not_confirmed=44`
- AI actions: `events={'DROP': 171, 'NOT_EVALUATED': 3, 'WAIT': 128}, unique={'DROP': 171, 'NOT_EVALUATED': 3, 'WAIT': 128}`
- budget/AI lineage: `{'status': 'explicit_ai_trace_budget_block_observed', 'pipeline_stage_order_contract': 'latest_watching_ai_to_budget_precheck_to_final_authority_revalidation', 'raw_ai_budget_census_is_causal': False, 'ai_trace_count': 328, 'ai_trace_source_stage_counts': {'ai_confirmed': 302, 'early_accel_strong_bundle_recheck_corrected': 7, 'early_accel_strong_bundle_recheck_failed': 19}, 'budget_or_block_event_count': 517, 'lineage_contract_event_count': 517, 'lineage_contract_coverage_pct': 100.0, 'pre_ai_parent_not_expected_event_count': 385, 'lineage_join_eligible_event_count': 132, 'lineage_contract_missing_event_count': 0, 'lineage_field_present_count': 34, 'parent_trace_missing_when_expected_event_count': 98, 'parent_attempt_without_trusted_result_event_count': 98, 'parent_trace_missing_without_attempt_event_count': 0, 'lineage_exact_trusted_count': 28, 'lineage_untrusted_or_stale_event_count': 6, 'lineage_untrusted_or_stale_reason_counts': {'source_stale': 3, 'trace_id_mismatch': 1, 'trace_id_mismatch_and_source_stale': 2}, 'lineage_joined_event_count': 28, 'exact_parent_trace_unresolved_event_count': 0, 'lineage_join_coverage_pct': 21.21, 'raw_event_lineage_join_coverage_pct': 5.42, 'lineage_join_coverage_denominator': 'all_events_except_explicit_pre_ai_parent_not_expected', 'linked_budget_pass_trace_count': 14, 'linked_budget_block_trace_count': 7, 'linked_stage_counts': {'blocked_zero_qty': 7, 'budget_pass': 21}, 'runtime_effect': False, 'allowed_runtime_apply': False}`
- latency blockers: `latency_block:latency_state_danger=129`
- price guards: `entry_ai_price_canary_fallback:skip_low_confidence=4`
- quote refresh: `attempted=67, applied=30, latency_recovered=8, submitted_after_refresh=0`
- quote refresh downstream: `{'budget_pass_no_submit_event': 2, 'entry_ai_authority_revalidation': 6}`

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

- `5m`: ai=3, budget=4, latency=1, submitted=0, top=`latency_block:latency_state_danger=6, blocked_strength_momentum:insufficient_history=6, blocked_strength_momentum:below_window_buy_value=3`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=1, wait65_79_ev_candidate:score_70.0=1`, ai_terminal=`-`
- `10m`: ai=7, budget=8, latency=3, submitted=1, top=`blocked_overbought:-=12, blocked_strength_momentum:insufficient_history=11, latency_block:latency_state_danger=7`, swing=`-`, upstream=`first_ai_wait:-=1, blocked_ai_score:score_0.0=1, blocked_ai_score:score_8.0=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=2, ai_terminal:first_ai_wait_big_bite_not_confirmed=1`
- `30m`: ai=17, budget=14, latency=5, submitted=2, top=`blocked_overbought:-=24, blocked_strength_momentum:insufficient_history=22, blocked_strength_momentum:below_strength_base=16`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=4, wait65_79_ev_candidate:score_70.0=4, blocked_ai_score:score_0.0=3`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=9, ai_terminal:first_ai_wait_big_bite_not_confirmed=2`
