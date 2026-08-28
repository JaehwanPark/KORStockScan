# 2026-08-28 One Share Threshold Opportunity

- generated_at: 2026-08-28T20:53:47+09:00
- window: 2026-06-05 -> 2026-08-28
- decision_authority: source_only_threshold_opportunity_audit
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: runtime_threshold_mutation, buy_score_threshold_relaxation_without_preopen_apply, stale_submit_bypass, broker_guard_bypass, order_guard_relaxation, provider_route_change, bot_restart, forced_one_share_success_counting, real_execution_quality_approval
- ai_review_status: parsed
- source_coverage_status: source_coverage_gap
- source_coverage_gap_count: 1

## Summary

- forced_record_count: 4789
- post_sell_joined_count: 351
- profitable_joined_count: 229
- loss_or_flat_joined_count: 122
- threshold_opportunity_count: 5
- code_improvement_order_count: 0
- probe_split_attribution_status: observed
- probe_intent_record_count: 4789
- actual_submit_observed_count: 510
- submitted_split_provenance_gap_count: 0
- probe_to_residual_status: instrumentation_gap
- probe_to_residual_resolution_count: 84
- probe_to_residual_resolution_coverage_pct: 82.3529
- residual_submitted_record_count: 16
- residual_blocked_record_count: 89
- residual_not_submitted_record_count: 69
- residual_not_submitted_source_counts: {"explicit_terminal_outcome": 46, "legacy_aborted_phase_fallback": 23}
- residual_terminal_abort_reason_counts: {"entry_setup_bounded_exploration_probe_only": 2, "exit_authority_precedence": 3, "fresh_ai_drop_veto": 5, "post_probe_wait_single_residual_leg_cap": 1, "probe_fill_after_timeout": 1, "probe_fill_slippage_above_cap": 3, "probe_fill_submit_contract_missing": 1, "probe_runtime_quantity_invariant": 1, "residual_leg_direction_deferred": 1, "residual_revalidation_timeout": 51}
- residual_terminal_abort_detail_reason_counts: {"missing_fields:entry_split_probe_bundle_id,entry_split_probe_requested_qty,entry_split_probe_continuation,entry_split_probe_submit_best_ask": 1, "timeout_ai_authority_expired": 13, "timeout_negative_group_persisted": 10, "timeout_quote_source_conflict": 3, "timeout_wait_confirmation_not_reached": 3, "unknown": 39}
- residual_terminal_failure_signature_coverage_count: 45
- probe_to_residual_unresolved_record_count: 18
- target_date_probe_to_residual: {"probe_first_submit_provenance_gap_count": 0, "probe_first_submit_with_provenance_count": 1, "probe_first_submitted_count": 1, "residual_blocked_record_count": 1, "residual_not_submitted_record_count": 1, "residual_not_submitted_source_counts": {"explicit_terminal_outcome": 1}, "residual_submitted_record_count": 0, "residual_terminal_abort_detail_reason_counts": {"timeout_negative_group_persisted": 1}, "resolution_count": 1, "resolution_coverage_pct": 100.0, "status": "observed", "unresolved_record_count": 0}

## Opportunities

### strength_momentum_vpw

- candidate_id: one_share_threshold_strength_momentum_vpw
- mapped_family: entry_strength_momentum_recheck
- sample: 191
- valid_profit_sample: 191
- equal_weight_avg_profit_pct: 0.027173
- profitable_count: 130
- loss_or_flat_count: 61

### overbought_or_liquidity

- candidate_id: one_share_threshold_overbought_or_liquidity
- mapped_family: pre_submit_guard_attribution
- sample: 230
- valid_profit_sample: 230
- equal_weight_avg_profit_pct: -0.077883
- profitable_count: 154
- loss_or_flat_count: 76

### ai_score_near_buy

- candidate_id: one_share_threshold_ai_score_near_buy
- mapped_family: entry_opportunity_recheck_runtime
- sample: 163
- valid_profit_sample: 163
- equal_weight_avg_profit_pct: -0.113816
- profitable_count: 109
- loss_or_flat_count: 54

### latency_or_freshness

- candidate_id: one_share_threshold_latency_or_freshness
- mapped_family: latency_classifier_runtime_profile
- sample: 351
- valid_profit_sample: 351
- equal_weight_avg_profit_pct: -0.115875
- profitable_count: 229
- loss_or_flat_count: 122

### cooldown_or_hard_safety

- candidate_id: one_share_threshold_cooldown_or_hard_safety
- mapped_family: hard_safety_observation_only
- sample: 228
- valid_profit_sample: 228
- equal_weight_avg_profit_pct: -0.50107
- profitable_count: 131
- loss_or_flat_count: 97

## Workorders
