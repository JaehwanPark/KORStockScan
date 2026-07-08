# 2026-07-08 One Share Threshold Opportunity

- generated_at: 2026-07-08T20:10:48+09:00
- window: 2026-06-04 -> 2026-07-08
- decision_authority: source_only_threshold_opportunity_audit
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: runtime_threshold_mutation, buy_score_threshold_relaxation_without_preopen_apply, stale_submit_bypass, broker_guard_bypass, order_guard_relaxation, provider_route_change, bot_restart, forced_one_share_success_counting, real_execution_quality_approval
- ai_review_status: parsed

## Summary

- forced_record_count: 38
- post_sell_joined_count: 18
- profitable_joined_count: 7
- loss_or_flat_joined_count: 11
- threshold_opportunity_count: 5
- code_improvement_order_count: 0

## Opportunities

### latency_or_freshness

- candidate_id: one_share_threshold_latency_or_freshness
- mapped_family: latency_classifier_runtime_profile
- sample: 18
- valid_profit_sample: 18
- equal_weight_avg_profit_pct: -1.933889
- profitable_count: 7
- loss_or_flat_count: 11

### ai_score_near_buy

- candidate_id: one_share_threshold_ai_score_near_buy
- mapped_family: entry_opportunity_recheck_runtime
- sample: 10
- valid_profit_sample: 10
- equal_weight_avg_profit_pct: -2.124
- profitable_count: 3
- loss_or_flat_count: 7

### strength_momentum_vpw

- candidate_id: one_share_threshold_strength_momentum_vpw
- mapped_family: entry_strength_momentum_recheck
- sample: 12
- valid_profit_sample: 12
- equal_weight_avg_profit_pct: -2.128333
- profitable_count: 4
- loss_or_flat_count: 8

### cooldown_or_hard_safety

- candidate_id: one_share_threshold_cooldown_or_hard_safety
- mapped_family: hard_safety_observation_only
- sample: 15
- valid_profit_sample: 15
- equal_weight_avg_profit_pct: -2.204667
- profitable_count: 5
- loss_or_flat_count: 10

### overbought_or_liquidity

- candidate_id: one_share_threshold_overbought_or_liquidity
- mapped_family: pre_submit_guard_attribution
- sample: 10
- valid_profit_sample: 10
- equal_weight_avg_profit_pct: -2.824
- profitable_count: 2
- loss_or_flat_count: 8

## Workorders
