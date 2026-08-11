# 2026-08-11 One Share Threshold Opportunity

- generated_at: 2026-08-11T20:40:32+09:00
- window: 2026-06-05 -> 2026-08-11
- decision_authority: source_only_threshold_opportunity_audit
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: runtime_threshold_mutation, buy_score_threshold_relaxation_without_preopen_apply, stale_submit_bypass, broker_guard_bypass, order_guard_relaxation, provider_route_change, bot_restart, forced_one_share_success_counting, real_execution_quality_approval
- ai_review_status: parsed
- source_coverage_status: pass
- source_coverage_gap_count: 0

## Summary

- forced_record_count: 2770
- post_sell_joined_count: 285
- profitable_joined_count: 184
- loss_or_flat_joined_count: 101
- threshold_opportunity_count: 5
- code_improvement_order_count: 1
- probe_split_attribution_status: observed
- probe_intent_record_count: 2770
- actual_submit_observed_count: 414
- submitted_split_provenance_gap_count: 0
- probe_to_residual_status: instrumentation_gap
- probe_to_residual_resolution_count: 59
- probe_to_residual_resolution_coverage_pct: 76.6234
- residual_submitted_record_count: 16
- residual_blocked_record_count: 64
- residual_not_submitted_record_count: 44
- residual_not_submitted_source_counts: {"explicit_terminal_outcome": 21, "legacy_aborted_phase_fallback": 23}
- residual_terminal_abort_reason_counts: {"exit_authority_precedence": 3, "fresh_ai_drop_veto": 5, "post_probe_wait_single_residual_leg_cap": 1, "probe_fill_after_timeout": 1, "probe_fill_slippage_above_cap": 1, "residual_leg_direction_deferred": 1, "residual_revalidation_timeout": 32}
- residual_terminal_abort_detail_reason_counts: {"timeout_negative_group_persisted": 9, "timeout_quote_source_conflict": 1, "unknown": 34}
- residual_terminal_failure_signature_coverage_count: 20
- probe_to_residual_unresolved_record_count: 18
- target_date_probe_to_residual: {"probe_first_submit_provenance_gap_count": 0, "probe_first_submit_with_provenance_count": 0, "probe_first_submitted_count": 0, "residual_blocked_record_count": 0, "residual_not_submitted_record_count": 0, "residual_not_submitted_source_counts": {}, "residual_submitted_record_count": 0, "residual_terminal_abort_detail_reason_counts": {}, "resolution_count": 0, "resolution_coverage_pct": null, "status": "no_natural_sample", "unresolved_record_count": 0}

## Opportunities

### strength_momentum_vpw

- candidate_id: one_share_threshold_strength_momentum_vpw
- mapped_family: entry_strength_momentum_recheck
- sample: 174
- valid_profit_sample: 174
- equal_weight_avg_profit_pct: 0.014598
- profitable_count: 116
- loss_or_flat_count: 58

### overbought_or_liquidity

- candidate_id: one_share_threshold_overbought_or_liquidity
- mapped_family: pre_submit_guard_attribution
- sample: 187
- valid_profit_sample: 187
- equal_weight_avg_profit_pct: -0.067594
- profitable_count: 122
- loss_or_flat_count: 65

### latency_or_freshness

- candidate_id: one_share_threshold_latency_or_freshness
- mapped_family: latency_classifier_runtime_profile
- sample: 285
- valid_profit_sample: 285
- equal_weight_avg_profit_pct: -0.092
- profitable_count: 184
- loss_or_flat_count: 101

### ai_score_near_buy

- candidate_id: one_share_threshold_ai_score_near_buy
- mapped_family: entry_opportunity_recheck_runtime
- sample: 149
- valid_profit_sample: 149
- equal_weight_avg_profit_pct: -0.119799
- profitable_count: 98
- loss_or_flat_count: 51

### cooldown_or_hard_safety

- candidate_id: one_share_threshold_cooldown_or_hard_safety
- mapped_family: hard_safety_observation_only
- sample: 198
- valid_profit_sample: 198
- equal_weight_avg_profit_pct: -0.469091
- profitable_count: 113
- loss_or_flat_count: 85

## Workorders

### order_one_share_threshold_strength_momentum_vpw_entry_hook_review

- mapped_family: entry_strength_momentum_recheck
- runtime_effect: false
- allowed_runtime_apply: false
- ai_recommended_disposition: attach_existing_entry_hook
- evidence:
  - threshold_group=strength_momentum_vpw
  - sample=174
  - valid_profit_sample=174
  - profitable_count=116
  - loss_or_flat_count=58
  - equal_weight_avg_profit_pct=0.014598
  - runtime_effect=false
  - allowed_runtime_apply=false
