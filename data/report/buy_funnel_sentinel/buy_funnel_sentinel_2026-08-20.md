# BUY Funnel Sentinel 2026-08-20

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

- as_of: `2026-08-20T12:45:04`
- baseline_date: `2026-08-19`
- ai_confirmed unique: `82`
- budget_pass unique: `100`
- latency_pass unique: `31`
- submitted unique: `9`
- holding_started unique: `9`
- budget/ai unique: `122.0%` (baseline `107.9`)
- submitted/ai unique: `11.0%` (baseline `10.5`)
- economic bundles: `observed=8, valid=8, probe_only=8, partial_residual=0, full=0`
- economic submitted/requested: `qty=8/249 (3.2%), notional=95848/1010172 (9.5%)`
- economic participation by venue: `{'KRX': {'bundle_count': 8, 'probe_only_bundle_count': 8, 'partial_residual_bundle_count': 0, 'full_submitted_bundle_count': 0, 'requested_qty': 249, 'submitted_qty': 8, 'requested_notional_krw': 1010172, 'submitted_notional_krw': 95848, 'submitted_qty_to_requested_qty_pct': 3.2, 'submitted_notional_to_requested_notional_pct': 9.5}}`
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:below_window_buy_value=469, blocked_strength_momentum:insufficient_history=455, latency_block:latency_state_danger=291, blocked_strength_momentum:below_strength_base=109, blocked_overbought:-=107`
- swing blockers: `-`
- upstream blockers: `blocked_ai_score:ai_score_50_buy_hold_override=106, wait65_79_ev_candidate:score_70.0=40, blocked_ai_score:score_70.0=32, first_ai_wait:-=25, blocked_ai_score:score_4.0=22`
- AI terminal reasons: `ai_terminal:entry_policy_no_buy_score_prior=122, ai_terminal:first_ai_wait_big_bite_not_confirmed=25`
- AI actions: `events={'DROP': 127, 'NOT_EVALUATED': 1, 'WAIT': 102}, unique={'DROP': 127, 'NOT_EVALUATED': 1, 'WAIT': 102}`
- budget/AI lineage: `{'status': 'explicit_ai_trace_budget_pass_only', 'pipeline_stage_order_contract': 'latest_watching_ai_to_budget_precheck_to_final_authority_revalidation', 'raw_ai_budget_census_is_causal': False, 'ai_trace_count': 254, 'ai_trace_source_stage_counts': {'ai_confirmed': 230, 'early_accel_strong_bundle_recheck_corrected': 6, 'early_accel_strong_bundle_recheck_failed': 18}, 'budget_or_block_event_count': 444, 'lineage_contract_event_count': 444, 'lineage_contract_coverage_pct': 100.0, 'pre_ai_parent_not_expected_event_count': 428, 'lineage_join_eligible_event_count': 10, 'lineage_contract_missing_event_count': 0, 'lineage_field_present_count': 10, 'parent_trace_missing_when_expected_event_count': 0, 'parent_attempt_without_trusted_result_event_count': 6, 'ai_attempt_result_unavailable_parent_not_expected_event_count': 6, 'parent_trace_missing_without_attempt_event_count': 0, 'lineage_exact_trusted_count': 9, 'lineage_untrusted_or_stale_event_count': 1, 'lineage_untrusted_or_stale_reason_counts': {'source_stale': 1}, 'lineage_joined_event_count': 9, 'exact_parent_trace_unresolved_event_count': 0, 'lineage_join_coverage_pct': 90.0, 'raw_event_lineage_join_coverage_pct': 2.03, 'lineage_join_coverage_denominator': 'events_with_a_trusted_ai_result_expected; excludes_pre_ai_and_explicit_attempt_result_unavailable', 'linked_budget_pass_trace_count': 7, 'linked_budget_block_trace_count': 0, 'linked_stage_counts': {'budget_pass': 9}, 'runtime_effect': False, 'allowed_runtime_apply': False}`
- latency blockers: `latency_block:latency_state_danger=291, latency_block:tp1_direct_recheck_expired=1`
- price guards: `entry_ai_price_canary_fallback:pre_submit_price_guard=2, entry_ai_price_canary_fallback:skip_low_confidence=1`
- quote refresh: `attempted=87, applied=53, latency_recovered=12, submitted_after_refresh=2`
- quote refresh downstream: `{'budget_pass_no_submit_event': 3, 'entry_ai_authority_revalidation': 6, 'no_downstream_event': 1, 'order_bundle_submitted': 2}`

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

- `5m`: ai=2, budget=8, latency=1, submitted=1, top=`blocked_strength_momentum:below_window_buy_value=9, latency_block:latency_state_danger=7, blocked_strength_momentum:below_strength_base=4`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=3, blocked_ai_score:score_11.0=1, blocked_ai_score:score_61.0=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=2`
- `10m`: ai=6, budget=13, latency=1, submitted=1, top=`blocked_strength_momentum:insufficient_history=26, latency_block:latency_state_danger=12, blocked_strength_momentum:below_window_buy_value=12`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=4, blocked_ai_score:score_0.0=1, blocked_ai_score:score_14.0=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=5`
- `30m`: ai=23, budget=28, latency=7, submitted=3, top=`blocked_strength_momentum:insufficient_history=86, blocked_strength_momentum:below_window_buy_value=45, latency_block:latency_state_danger=32`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=14, wait65_79_ev_candidate:score_70.0=4, blocked_ai_score:score_70.0=4`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=17, ai_terminal:first_ai_wait_big_bite_not_confirmed=1`
