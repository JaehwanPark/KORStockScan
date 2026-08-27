# BUY Funnel Sentinel 2026-08-28

## 판정

- primary: `NOT_YET_DUE`
- secondary: `-`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `false`
- followup_route: `not_yet_due`
- followup_owner: `scheduled_buy_funnel_sentinel`
- runtime_effect: `report_only_no_mutation`
- submit_contract_downstream: `code_improvement_workorder, lifecycle_decision_matrix.submit_bucket_attribution, threshold_cycle_ev_report, runtime_approval_summary, postclose_verifier`
- submit_contract_weak_matches: `-`

## 근거

- as_of: `2026-08-28T08:37:54`
- baseline_date: `2026-08-27`
- ai_confirmed unique: `0`
- budget_pass unique: `0`
- latency_pass unique: `0`
- submitted unique: `0`
- holding_started unique: `0`
- budget/ai unique: `0.0%` (baseline `0.0`)
- submitted/ai unique: `0.0%` (baseline `0.0`)
- economic bundles: `observed=0, valid=0, probe_only=0, partial_residual=0, full=0`
- economic submitted/requested: `qty=0/0 (0.0%), notional=0/0 (0.0%)`
- economic participation by venue: `{}`
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `-`
- swing blockers: `-`
- upstream blockers: `-`
- AI terminal reasons: `-`
- AI actions: `events={}, unique={}`
- budget/AI lineage: `{'status': 'not_applicable_before_sentinel_start', 'pipeline_stage_order_contract': 'latest_watching_ai_to_budget_precheck_to_final_authority_revalidation', 'raw_ai_budget_census_is_causal': False, 'ai_trace_count': 0, 'ai_trace_source_stage_counts': {}, 'budget_or_block_event_count': 0, 'lineage_contract_event_count': 0, 'lineage_contract_coverage_pct': 0.0, 'pre_ai_parent_not_expected_event_count': 0, 'lineage_join_eligible_event_count': 0, 'lineage_contract_missing_event_count': 0, 'lineage_field_present_count': 0, 'parent_trace_missing_when_expected_event_count': 0, 'parent_attempt_without_trusted_result_event_count': 0, 'ai_attempt_result_unavailable_parent_not_expected_event_count': 0, 'parent_trace_missing_without_attempt_event_count': 0, 'lineage_exact_trusted_count': 0, 'lineage_untrusted_or_stale_event_count': 0, 'lineage_untrusted_or_stale_reason_counts': {}, 'lineage_joined_event_count': 0, 'exact_parent_trace_unresolved_event_count': 0, 'lineage_join_coverage_pct': 0.0, 'raw_event_lineage_join_coverage_pct': 0.0, 'lineage_join_coverage_denominator': 'events_with_a_trusted_ai_result_expected; excludes_pre_ai_and_explicit_attempt_result_unavailable', 'linked_budget_pass_trace_count': 0, 'linked_budget_block_trace_count': 0, 'linked_stage_counts': {}, 'runtime_effect': False, 'allowed_runtime_apply': False, 'canonical_source_state': 'no_current_signal'}`
- latency blockers: `-`
- price guards: `-`
- quote refresh: `attempted=0, applied=0, latency_recovered=0, submitted_after_refresh=0`
- quote refresh downstream: `{}`

## 금지된 자동변경

- `score_threshold_relaxation`
- `spread_cap_relaxation`
- `fallback_reenable`
- `live_threshold_runtime_mutation`
- `bot_restart`

## 권고 액션

- Wait for the sentinel session window; no runtime action is required.

## Window Summary

- `5m`: ai=0, budget=0, latency=0, submitted=0, top=`-`, swing=`-`, upstream=`-`, ai_terminal=`-`
- `10m`: ai=0, budget=0, latency=0, submitted=0, top=`-`, swing=`-`, upstream=`-`, ai_terminal=`-`
- `30m`: ai=0, budget=0, latency=0, submitted=0, top=`-`, swing=`-`, upstream=`-`, ai_terminal=`-`
