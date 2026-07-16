# 2026-07-16 One Share Threshold Opportunity

- generated_at: 2026-07-16T20:15:20+09:00
- window: 2026-06-04 -> 2026-07-16
- decision_authority: source_only_threshold_opportunity_audit
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: runtime_threshold_mutation, buy_score_threshold_relaxation_without_preopen_apply, stale_submit_bypass, broker_guard_bypass, order_guard_relaxation, provider_route_change, bot_restart, forced_one_share_success_counting, real_execution_quality_approval
- ai_review_status: parsed
- source_coverage_status: source_coverage_gap
- source_coverage_gap_count: 5

## Summary

- forced_record_count: 1841
- post_sell_joined_count: 184
- profitable_joined_count: 121
- loss_or_flat_joined_count: 63
- threshold_opportunity_count: 5
- code_improvement_order_count: 0

## Opportunities

### strength_momentum_vpw

- candidate_id: one_share_threshold_strength_momentum_vpw
- mapped_family: entry_strength_momentum_recheck
- sample: 159
- valid_profit_sample: 159
- equal_weight_avg_profit_pct: 0.074528
- profitable_count: 108
- loss_or_flat_count: 51

### latency_or_freshness

- candidate_id: one_share_threshold_latency_or_freshness
- mapped_family: latency_classifier_runtime_profile
- sample: 184
- valid_profit_sample: 184
- equal_weight_avg_profit_pct: -0.050163
- profitable_count: 121
- loss_or_flat_count: 63

### ai_score_near_buy

- candidate_id: one_share_threshold_ai_score_near_buy
- mapped_family: entry_opportunity_recheck_runtime
- sample: 138
- valid_profit_sample: 138
- equal_weight_avg_profit_pct: -0.051884
- profitable_count: 93
- loss_or_flat_count: 45

### overbought_or_liquidity

- candidate_id: one_share_threshold_overbought_or_liquidity
- mapped_family: pre_submit_guard_attribution
- sample: 109
- valid_profit_sample: 109
- equal_weight_avg_profit_pct: -0.194771
- profitable_count: 70
- loss_or_flat_count: 39

### cooldown_or_hard_safety

- candidate_id: one_share_threshold_cooldown_or_hard_safety
- mapped_family: hard_safety_observation_only
- sample: 160
- valid_profit_sample: 160
- equal_weight_avg_profit_pct: -0.271687
- profitable_count: 101
- loss_or_flat_count: 59

## Workorders
