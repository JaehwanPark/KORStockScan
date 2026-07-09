# 2026-07-09 One Share Threshold Opportunity

- generated_at: 2026-07-09T20:10:48+09:00
- window: 2026-06-04 -> 2026-07-09
- decision_authority: source_only_threshold_opportunity_audit
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: runtime_threshold_mutation, buy_score_threshold_relaxation_without_preopen_apply, stale_submit_bypass, broker_guard_bypass, order_guard_relaxation, provider_route_change, bot_restart, forced_one_share_success_counting, real_execution_quality_approval
- ai_review_status: parsed

## Summary

- forced_record_count: 174
- post_sell_joined_count: 5
- profitable_joined_count: 3
- loss_or_flat_joined_count: 2
- threshold_opportunity_count: 5
- code_improvement_order_count: 0

## Opportunities

### latency_or_freshness

- candidate_id: one_share_threshold_latency_or_freshness
- mapped_family: latency_classifier_runtime_profile
- sample: 5
- valid_profit_sample: 5
- equal_weight_avg_profit_pct: -0.034
- profitable_count: 3
- loss_or_flat_count: 2

### ai_score_near_buy

- candidate_id: one_share_threshold_ai_score_near_buy
- mapped_family: entry_opportunity_recheck_runtime
- sample: 4
- valid_profit_sample: 4
- equal_weight_avg_profit_pct: -0.155
- profitable_count: 2
- loss_or_flat_count: 2

### strength_momentum_vpw

- candidate_id: one_share_threshold_strength_momentum_vpw
- mapped_family: entry_strength_momentum_recheck
- sample: 4
- valid_profit_sample: 4
- equal_weight_avg_profit_pct: -0.155
- profitable_count: 2
- loss_or_flat_count: 2

### overbought_or_liquidity

- candidate_id: one_share_threshold_overbought_or_liquidity
- mapped_family: pre_submit_guard_attribution
- sample: 4
- valid_profit_sample: 4
- equal_weight_avg_profit_pct: -0.155
- profitable_count: 2
- loss_or_flat_count: 2

### cooldown_or_hard_safety

- candidate_id: one_share_threshold_cooldown_or_hard_safety
- mapped_family: hard_safety_observation_only
- sample: 4
- valid_profit_sample: 4
- equal_weight_avg_profit_pct: -0.905
- profitable_count: 2
- loss_or_flat_count: 2

## Workorders
