# 2026-07-31 One Share Threshold Opportunity

- generated_at: 2026-08-01T21:10:28+09:00
- window: 2026-06-05 -> 2026-07-31
- decision_authority: source_only_threshold_opportunity_audit
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: runtime_threshold_mutation, buy_score_threshold_relaxation_without_preopen_apply, stale_submit_bypass, broker_guard_bypass, order_guard_relaxation, provider_route_change, bot_restart, forced_one_share_success_counting, real_execution_quality_approval
- ai_review_status: parsed
- source_coverage_status: pass
- source_coverage_gap_count: 0

## Summary

- forced_record_count: 1425
- post_sell_joined_count: 258
- profitable_joined_count: 167
- loss_or_flat_joined_count: 91
- threshold_opportunity_count: 5
- code_improvement_order_count: 1
- probe_split_attribution_status: observed
- probe_intent_record_count: 1425
- actual_submit_observed_count: 387
- submitted_split_provenance_gap_count: 0
- probe_to_residual_status: instrumentation_gap
- probe_to_residual_resolution_count: 38
- probe_to_residual_resolution_coverage_pct: 67.8571
- residual_submitted_record_count: 15
- residual_blocked_record_count: 43
- residual_not_submitted_record_count: 23
- residual_not_submitted_source_counts: {"legacy_aborted_phase_fallback": 23}
- probe_to_residual_unresolved_record_count: 18
- target_date_probe_to_residual: {"probe_first_submit_provenance_gap_count": 0, "probe_first_submit_with_provenance_count": 5, "probe_first_submitted_count": 5, "residual_blocked_record_count": 5, "residual_not_submitted_record_count": 5, "residual_not_submitted_source_counts": {"legacy_aborted_phase_fallback": 5}, "residual_submitted_record_count": 0, "resolution_count": 5, "resolution_coverage_pct": 100.0, "status": "observed", "unresolved_record_count": 0}

## Opportunities

### strength_momentum_vpw

- candidate_id: one_share_threshold_strength_momentum_vpw
- mapped_family: entry_strength_momentum_recheck
- sample: 166
- valid_profit_sample: 166
- equal_weight_avg_profit_pct: 0.009277
- profitable_count: 111
- loss_or_flat_count: 55

### ai_score_near_buy

- candidate_id: one_share_threshold_ai_score_near_buy
- mapped_family: entry_opportunity_recheck_runtime
- sample: 143
- valid_profit_sample: 143
- equal_weight_avg_profit_pct: -0.094895
- profitable_count: 95
- loss_or_flat_count: 48

### latency_or_freshness

- candidate_id: one_share_threshold_latency_or_freshness
- mapped_family: latency_classifier_runtime_profile
- sample: 258
- valid_profit_sample: 258
- equal_weight_avg_profit_pct: -0.120698
- profitable_count: 167
- loss_or_flat_count: 91

### overbought_or_liquidity

- candidate_id: one_share_threshold_overbought_or_liquidity
- mapped_family: pre_submit_guard_attribution
- sample: 161
- valid_profit_sample: 161
- equal_weight_avg_profit_pct: -0.129752
- profitable_count: 105
- loss_or_flat_count: 56

### cooldown_or_hard_safety

- candidate_id: one_share_threshold_cooldown_or_hard_safety
- mapped_family: hard_safety_observation_only
- sample: 186
- valid_profit_sample: 186
- equal_weight_avg_profit_pct: -0.419946
- profitable_count: 109
- loss_or_flat_count: 77

## Workorders

### order_one_share_threshold_strength_momentum_vpw_entry_hook_review

- mapped_family: entry_strength_momentum_recheck
- runtime_effect: false
- allowed_runtime_apply: false
- ai_recommended_disposition: attach_existing_entry_hook
- evidence:
  - threshold_group=strength_momentum_vpw
  - sample=166
  - valid_profit_sample=166
  - profitable_count=111
  - loss_or_flat_count=55
  - equal_weight_avg_profit_pct=0.009277
  - runtime_effect=false
  - allowed_runtime_apply=false
