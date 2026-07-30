# 2026-07-30 One Share Threshold Opportunity

- generated_at: 2026-07-30T21:05:58+09:00
- window: 2026-06-04 -> 2026-07-30
- decision_authority: source_only_threshold_opportunity_audit
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: runtime_threshold_mutation, buy_score_threshold_relaxation_without_preopen_apply, stale_submit_bypass, broker_guard_bypass, order_guard_relaxation, provider_route_change, bot_restart, forced_one_share_success_counting, real_execution_quality_approval
- ai_review_status: parsed
- source_coverage_status: source_coverage_gap
- source_coverage_gap_count: 6

## Summary

- forced_record_count: 3655
- post_sell_joined_count: 255
- profitable_joined_count: 163
- loss_or_flat_joined_count: 92
- threshold_opportunity_count: 5
- code_improvement_order_count: 0

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
- sample: 255
- valid_profit_sample: 255
- equal_weight_avg_profit_pct: -0.132588
- profitable_count: 163
- loss_or_flat_count: 92

### overbought_or_liquidity

- candidate_id: one_share_threshold_overbought_or_liquidity
- mapped_family: pre_submit_guard_attribution
- sample: 157
- valid_profit_sample: 157
- equal_weight_avg_profit_pct: -0.148599
- profitable_count: 101
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
