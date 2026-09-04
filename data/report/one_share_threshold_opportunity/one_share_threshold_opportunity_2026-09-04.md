# 2026-09-04 One Share Threshold Opportunity

- generated_at: 2026-09-04T20:41:47+09:00
- window: 2026-06-05 -> 2026-09-04
- decision_authority: source_only_threshold_opportunity_audit
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: runtime_threshold_mutation, buy_score_threshold_relaxation_without_preopen_apply, stale_submit_bypass, broker_guard_bypass, order_guard_relaxation, provider_route_change, bot_restart, forced_one_share_success_counting, real_execution_quality_approval
- ai_review_status: blocked_source_coverage
- source_coverage_status: source_coverage_gap
- source_coverage_gap_count: 3285

## Summary

- forced_record_count: 5523
- post_sell_joined_count: 0
- profitable_joined_count: 0
- loss_or_flat_joined_count: 0
- threshold_opportunity_count: 0
- configured_threshold_group_count: 5
- observed_threshold_group_evaluation_count: 0
- primary_blocker_evaluation_count: 0
- primary_attributed_opportunity_count: 0
- actionable_candidate_count: 0
- actionable_candidate_scope: source_only_existing_family_review_not_implement_now
- source_only_existing_family_evidence_count: 0
- automatic_implementation_candidate_count: 0
- code_improvement_order_count: 0
- candidate_change_status: unchanged
- source_processing_mode: partition_index_cache
- source_file_count: 67
- cache_hit_count: 65
- cache_miss_count: 2
- source_bytes_scanned: 4536195205
- source_bytes_reused: 7565665872
- source_io_bytes_estimated: 9072390410
- cache_miss_source_pass_count: 4
- source_reuse_pct: 62.5165
- elapsed_seconds: 61.976108
- probe_split_attribution_status: observed
- probe_intent_record_count: 5523
- actual_submit_observed_count: 525
- submitted_split_provenance_gap_count: 0
- probe_to_residual_status: instrumentation_gap
- probe_to_residual_resolution_count: 87
- probe_to_residual_resolution_coverage_pct: 82.8571
- residual_submitted_record_count: 16
- residual_blocked_record_count: 92
- residual_not_submitted_record_count: 72
- residual_not_submitted_source_counts: {"explicit_terminal_outcome": 49, "legacy_aborted_phase_fallback": 23}
- residual_terminal_abort_reason_counts: {"entry_setup_bounded_exploration_probe_only": 3, "exit_authority_precedence": 3, "fresh_ai_drop_veto": 5, "post_probe_wait_single_residual_leg_cap": 1, "probe_fill_after_timeout": 1, "probe_fill_slippage_above_cap": 3, "probe_fill_submit_contract_missing": 1, "probe_runtime_quantity_invariant": 1, "probe_timeout": 2, "residual_leg_direction_deferred": 1, "residual_revalidation_timeout": 51}
- residual_terminal_abort_detail_reason_counts: {"missing_fields:entry_split_probe_bundle_id,entry_split_probe_requested_qty,entry_split_probe_continuation,entry_split_probe_submit_best_ask": 1, "timeout_ai_authority_expired": 13, "timeout_negative_group_persisted": 10, "timeout_quote_source_conflict": 3, "timeout_wait_confirmation_not_reached": 3, "unknown": 42}
- residual_terminal_failure_signature_coverage_count: 48
- probe_to_residual_unresolved_record_count: 18
- target_date_probe_to_residual: {"probe_first_submit_provenance_gap_count": 0, "probe_first_submit_with_provenance_count": 2, "probe_first_submitted_count": 2, "residual_blocked_record_count": 2, "residual_not_submitted_record_count": 2, "residual_not_submitted_source_counts": {"explicit_terminal_outcome": 2}, "residual_submitted_record_count": 0, "residual_terminal_abort_detail_reason_counts": {"unknown": 2}, "resolution_count": 2, "resolution_coverage_pct": 100.0, "status": "observed", "unresolved_record_count": 0}

## Fixed Taxonomy Group Evaluations

## Primary-blocker Evaluations

## Threshold Opportunities

## Workorders
