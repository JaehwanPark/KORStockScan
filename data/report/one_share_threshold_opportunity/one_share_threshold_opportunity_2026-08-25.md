# 2026-08-25 One Share Threshold Opportunity

- generated_at: 2026-08-25T20:52:24+09:00
- window: 2026-06-05 -> 2026-08-25
- decision_authority: source_only_threshold_opportunity_audit
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: runtime_threshold_mutation, buy_score_threshold_relaxation_without_preopen_apply, stale_submit_bypass, broker_guard_bypass, order_guard_relaxation, provider_route_change, bot_restart, forced_one_share_success_counting, real_execution_quality_approval
- ai_review_status: parsed
- source_coverage_status: source_coverage_gap
- source_coverage_gap_count: 1

## Summary

- forced_record_count: 4320
- post_sell_joined_count: 343
- profitable_joined_count: 223
- loss_or_flat_joined_count: 120
- threshold_opportunity_count: 5
- code_improvement_order_count: 0
- probe_split_attribution_status: observed
- probe_intent_record_count: 4320
- actual_submit_observed_count: 499
- submitted_split_provenance_gap_count: 0
- probe_to_residual_status: instrumentation_gap
- probe_to_residual_resolution_count: 82
- probe_to_residual_resolution_coverage_pct: 82.0
- residual_submitted_record_count: 16
- residual_blocked_record_count: 87
- residual_not_submitted_record_count: 67
- residual_not_submitted_source_counts: {"explicit_terminal_outcome": 44, "legacy_aborted_phase_fallback": 23}
- residual_terminal_abort_reason_counts: {"entry_setup_bounded_exploration_probe_only": 2, "exit_authority_precedence": 3, "fresh_ai_drop_veto": 5, "post_probe_wait_single_residual_leg_cap": 1, "probe_fill_after_timeout": 1, "probe_fill_slippage_above_cap": 3, "probe_fill_submit_contract_missing": 1, "probe_runtime_quantity_invariant": 1, "residual_leg_direction_deferred": 1, "residual_revalidation_timeout": 49}
- residual_terminal_abort_detail_reason_counts: {"missing_fields:entry_split_probe_bundle_id,entry_split_probe_requested_qty,entry_split_probe_continuation,entry_split_probe_submit_best_ask": 1, "timeout_ai_authority_expired": 13, "timeout_negative_group_persisted": 9, "timeout_quote_source_conflict": 3, "timeout_wait_confirmation_not_reached": 2, "unknown": 39}
- residual_terminal_failure_signature_coverage_count: 43
- probe_to_residual_unresolved_record_count: 18
- target_date_probe_to_residual: {"probe_first_submit_provenance_gap_count": 0, "probe_first_submit_with_provenance_count": 0, "probe_first_submitted_count": 0, "residual_blocked_record_count": 0, "residual_not_submitted_record_count": 0, "residual_not_submitted_source_counts": {}, "residual_submitted_record_count": 0, "residual_terminal_abort_detail_reason_counts": {}, "resolution_count": 0, "resolution_coverage_pct": null, "status": "no_natural_sample", "unresolved_record_count": 0}

## Opportunities

### strength_momentum_vpw

- candidate_id: one_share_threshold_strength_momentum_vpw
- mapped_family: entry_strength_momentum_recheck
- sample: 188
- valid_profit_sample: 188
- equal_weight_avg_profit_pct: 0.039548
- profitable_count: 128
- loss_or_flat_count: 60

### overbought_or_liquidity

- candidate_id: one_share_threshold_overbought_or_liquidity
- mapped_family: pre_submit_guard_attribution
- sample: 223
- valid_profit_sample: 223
- equal_weight_avg_profit_pct: -0.066206
- profitable_count: 149
- loss_or_flat_count: 74

### ai_score_near_buy

- candidate_id: one_share_threshold_ai_score_near_buy
- mapped_family: entry_opportunity_recheck_runtime
- sample: 160
- valid_profit_sample: 160
- equal_weight_avg_profit_pct: -0.101919
- profitable_count: 107
- loss_or_flat_count: 53

### latency_or_freshness

- candidate_id: one_share_threshold_latency_or_freshness
- mapped_family: latency_classifier_runtime_profile
- sample: 343
- valid_profit_sample: 343
- equal_weight_avg_profit_pct: -0.109741
- profitable_count: 223
- loss_or_flat_count: 120

### cooldown_or_hard_safety

- candidate_id: one_share_threshold_cooldown_or_hard_safety
- mapped_family: hard_safety_observation_only
- sample: 223
- valid_profit_sample: 223
- equal_weight_avg_profit_pct: -0.492009
- profitable_count: 128
- loss_or_flat_count: 95

## Workorders
