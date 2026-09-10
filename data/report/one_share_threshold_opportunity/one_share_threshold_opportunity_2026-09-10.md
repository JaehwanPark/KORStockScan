# 2026-09-10 One Share Threshold Opportunity

- generated_at: 2026-09-10T21:32:57+09:00
- window: 2026-06-05 -> 2026-09-10
- decision_authority: source_only_threshold_opportunity_audit
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: runtime_threshold_mutation, buy_score_threshold_relaxation_without_preopen_apply, stale_submit_bypass, broker_guard_bypass, order_guard_relaxation, provider_route_change, bot_restart, forced_one_share_success_counting, real_execution_quality_approval
- ai_review_status: parsed
- source_coverage_status: partial_row_exclusion
- source_coverage_gap_count: 6
- source_coverage_decision_input_allowed: True
- source_coverage_fail_closed_scope: affected_rows_only

## Summary

- forced_record_count: 6061
- post_sell_joined_count: 367
- profitable_joined_count: 241
- loss_or_flat_joined_count: 126
- threshold_opportunity_count: 2
- configured_threshold_group_count: 5
- observed_threshold_group_evaluation_count: 5
- primary_blocker_evaluation_count: 4
- primary_attributed_opportunity_count: 2
- actionable_candidate_count: 2
- actionable_candidate_scope: source_only_existing_family_review_not_implement_now
- source_only_existing_family_evidence_count: 2
- automatic_implementation_candidate_count: 0
- code_improvement_order_count: 2
- candidate_change_status: changed
- source_processing_mode: partition_index_cache
- source_file_count: 71
- cache_hit_count: 69
- cache_miss_count: 2
- source_bytes_scanned: 6346821813
- source_bytes_reused: 8634392259
- source_io_bytes_estimated: 12693643626
- cache_miss_source_pass_count: 4
- source_reuse_pct: 57.6348
- elapsed_seconds: 111.184953
- probe_split_attribution_status: observed
- probe_intent_record_count: 6061
- actual_submit_observed_count: 534
- submitted_split_provenance_gap_count: 0
- probe_to_residual_status: instrumentation_gap
- probe_to_residual_resolution_count: 89
- probe_to_residual_resolution_coverage_pct: 83.1776
- residual_submitted_record_count: 16
- residual_blocked_record_count: 94
- residual_not_submitted_record_count: 74
- residual_not_submitted_source_counts: {"explicit_terminal_outcome": 51, "legacy_aborted_phase_fallback": 23}
- residual_terminal_abort_reason_counts: {"entry_setup_bounded_exploration_probe_only": 3, "exit_authority_precedence": 3, "fresh_ai_drop_veto": 5, "post_probe_wait_single_residual_leg_cap": 1, "probe_fill_after_timeout": 1, "probe_fill_slippage_above_cap": 3, "probe_fill_submit_contract_missing": 1, "probe_runtime_quantity_invariant": 1, "probe_timeout": 2, "residual_leg_direction_deferred": 1, "residual_revalidation_timeout": 53}
- residual_terminal_abort_detail_reason_counts: {"missing_fields:entry_split_probe_bundle_id,entry_split_probe_requested_qty,entry_split_probe_continuation,entry_split_probe_submit_best_ask": 1, "timeout_ai_authority_expired": 13, "timeout_negative_group_persisted": 11, "timeout_quote_source_conflict": 3, "timeout_revalidation_not_completed": 1, "timeout_wait_confirmation_not_reached": 3, "unknown": 42}
- residual_terminal_failure_signature_coverage_count: 50
- probe_to_residual_unresolved_record_count: 18
- target_date_probe_to_residual: {"probe_first_submit_provenance_gap_count": 0, "probe_first_submit_with_provenance_count": 0, "probe_first_submitted_count": 0, "residual_blocked_record_count": 0, "residual_not_submitted_record_count": 0, "residual_not_submitted_source_counts": {}, "residual_submitted_record_count": 0, "residual_terminal_abort_detail_reason_counts": {}, "resolution_count": 0, "resolution_coverage_pct": null, "status": "no_natural_sample", "unresolved_record_count": 0}

## Fixed Taxonomy Group Evaluations

### strength_momentum_vpw

- evaluation_id: one_share_threshold_group_strength_momentum_vpw
- classification_role: overlapping_fixed_taxonomy_diagnostic
- is_actionable_candidate: false
- sample: 194
- valid_profit_sample: 194
- equal_weight_avg_profit_pct: 0.041469

### overbought_or_liquidity

- evaluation_id: one_share_threshold_group_overbought_or_liquidity
- classification_role: overlapping_fixed_taxonomy_diagnostic
- is_actionable_candidate: false
- sample: 240
- valid_profit_sample: 240
- equal_weight_avg_profit_pct: -0.031079

### latency_or_freshness

- evaluation_id: one_share_threshold_group_latency_or_freshness
- classification_role: overlapping_fixed_taxonomy_diagnostic
- is_actionable_candidate: false
- sample: 367
- valid_profit_sample: 367
- equal_weight_avg_profit_pct: -0.091823

### ai_score_near_buy

- evaluation_id: one_share_threshold_group_ai_score_near_buy
- classification_role: overlapping_fixed_taxonomy_diagnostic
- is_actionable_candidate: false
- sample: 165
- valid_profit_sample: 165
- equal_weight_avg_profit_pct: -0.104867

### cooldown_or_hard_safety

- evaluation_id: one_share_threshold_group_cooldown_or_hard_safety
- classification_role: overlapping_fixed_taxonomy_diagnostic
- is_actionable_candidate: false
- sample: 227
- valid_profit_sample: 227
- equal_weight_avg_profit_pct: -0.441286

## Primary-blocker Evaluations

### ai_score_near_buy

- candidate_id: one_share_threshold_ai_score_near_buy
- mapped_family: entry_opportunity_recheck_runtime
- classification_role: exclusive_first_observed_blocker_evaluation
- candidate_status: eligible_for_existing_family_evidence
- is_actionable_candidate: true
- sample: 4
- valid_profit_sample: 4
- equal_weight_avg_profit_pct: 0.2375
- profitable_count: 2
- loss_or_flat_count: 2

### strength_momentum_vpw

- candidate_id: one_share_threshold_strength_momentum_vpw
- mapped_family: entry_strength_momentum_recheck
- classification_role: exclusive_first_observed_blocker_evaluation
- candidate_status: eligible_for_existing_family_evidence
- is_actionable_candidate: true
- sample: 58
- valid_profit_sample: 58
- equal_weight_avg_profit_pct: 0.209862
- profitable_count: 39
- loss_or_flat_count: 19

### cooldown_or_hard_safety

- candidate_id: one_share_threshold_cooldown_or_hard_safety
- mapped_family: hard_safety_observation_only
- classification_role: exclusive_first_observed_blocker_evaluation
- candidate_status: diagnostic_not_actionable
- is_actionable_candidate: false
- sample: 12
- valid_profit_sample: 12
- equal_weight_avg_profit_pct: 0.713333
- profitable_count: 9
- loss_or_flat_count: 3

### latency_or_freshness

- candidate_id: one_share_threshold_latency_or_freshness
- mapped_family: buy_funnel_sentinel
- classification_role: exclusive_first_observed_blocker_evaluation
- candidate_status: diagnostic_not_actionable
- is_actionable_candidate: false
- sample: 41
- valid_profit_sample: 41
- equal_weight_avg_profit_pct: -0.093244
- profitable_count: 23
- loss_or_flat_count: 18

## Threshold Opportunities

### ai_score_near_buy

- candidate_id: one_share_threshold_ai_score_near_buy
- mapped_family: entry_opportunity_recheck_runtime
- classification_role: eligible_existing_family_evidence_candidate
- sample: 4
- valid_profit_sample: 4
- equal_weight_avg_profit_pct: 0.2375

### strength_momentum_vpw

- candidate_id: one_share_threshold_strength_momentum_vpw
- mapped_family: entry_strength_momentum_recheck
- classification_role: eligible_existing_family_evidence_candidate
- sample: 58
- valid_profit_sample: 58
- equal_weight_avg_profit_pct: 0.209862

## Workorders

### order_one_share_threshold_ai_score_near_buy_entry_hook_review

- mapped_family: entry_opportunity_recheck_runtime
- runtime_effect: false
- allowed_runtime_apply: false
- ai_recommended_disposition: keep_collecting
- evidence:
  - threshold_group=ai_score_near_buy
  - sample=4
  - valid_profit_sample=4
  - profitable_count=2
  - loss_or_flat_count=2
  - equal_weight_avg_profit_pct=0.2375
  - runtime_effect=false
  - allowed_runtime_apply=false

### order_one_share_threshold_strength_momentum_vpw_entry_hook_review

- mapped_family: entry_strength_momentum_recheck
- runtime_effect: false
- allowed_runtime_apply: false
- ai_recommended_disposition: attach_existing_entry_hook
- evidence:
  - threshold_group=strength_momentum_vpw
  - sample=58
  - valid_profit_sample=58
  - profitable_count=39
  - loss_or_flat_count=19
  - equal_weight_avg_profit_pct=0.209862
  - runtime_effect=false
  - allowed_runtime_apply=false
