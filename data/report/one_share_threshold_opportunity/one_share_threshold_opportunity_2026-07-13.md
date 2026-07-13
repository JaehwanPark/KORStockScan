# 2026-07-13 One Share Threshold Opportunity

- generated_at: 2026-07-13T20:14:12+09:00
- window: 2026-06-04 -> 2026-07-13
- decision_authority: source_only_threshold_opportunity_audit
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: runtime_threshold_mutation, buy_score_threshold_relaxation_without_preopen_apply, stale_submit_bypass, broker_guard_bypass, order_guard_relaxation, provider_route_change, bot_restart, forced_one_share_success_counting, real_execution_quality_approval
- ai_review_status: parsed
- source_coverage_status: source_coverage_gap
- source_coverage_gap_count: 5

## Summary

- forced_record_count: 1056
- post_sell_joined_count: 171
- profitable_joined_count: 114
- loss_or_flat_joined_count: 57
- threshold_opportunity_count: 5
- code_improvement_order_count: 0

## Opportunities

### strength_momentum_vpw

- candidate_id: one_share_threshold_strength_momentum_vpw
- mapped_family: entry_strength_momentum_recheck
- sample: 155
- valid_profit_sample: 155
- equal_weight_avg_profit_pct: 0.087806
- profitable_count: 106
- loss_or_flat_count: 49

### latency_or_freshness

- candidate_id: one_share_threshold_latency_or_freshness
- mapped_family: latency_classifier_runtime_profile
- sample: 171
- valid_profit_sample: 171
- equal_weight_avg_profit_pct: -0.025263
- profitable_count: 114
- loss_or_flat_count: 57

### ai_score_near_buy

- candidate_id: one_share_threshold_ai_score_near_buy
- mapped_family: entry_opportunity_recheck_runtime
- sample: 135
- valid_profit_sample: 135
- equal_weight_avg_profit_pct: -0.041704
- profitable_count: 91
- loss_or_flat_count: 44

### overbought_or_liquidity

- candidate_id: one_share_threshold_overbought_or_liquidity
- mapped_family: pre_submit_guard_attribution
- sample: 100
- valid_profit_sample: 100
- equal_weight_avg_profit_pct: -0.1656
- profitable_count: 65
- loss_or_flat_count: 35

### cooldown_or_hard_safety

- candidate_id: one_share_threshold_cooldown_or_hard_safety
- mapped_family: hard_safety_observation_only
- sample: 156
- valid_profit_sample: 156
- equal_weight_avg_profit_pct: -0.236859
- profitable_count: 100
- loss_or_flat_count: 56

## Workorders
