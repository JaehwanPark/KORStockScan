# 2026-07-03 One Share Threshold Opportunity

- generated_at: 2026-07-03T20:10:59+09:00
- window: 2026-06-04 -> 2026-07-03
- decision_authority: source_only_threshold_opportunity_audit
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: runtime_threshold_mutation, buy_score_threshold_relaxation_without_preopen_apply, stale_submit_bypass, broker_guard_bypass, order_guard_relaxation, provider_route_change, bot_restart, forced_one_share_success_counting, real_execution_quality_approval
- ai_review_status: parsed

## Summary

- forced_record_count: 44
- post_sell_joined_count: 18
- profitable_joined_count: 15
- loss_or_flat_joined_count: 3
- threshold_opportunity_count: 5
- code_improvement_order_count: 3

## Opportunities

### latency_or_freshness

- candidate_id: one_share_threshold_latency_or_freshness
- mapped_family: latency_classifier_runtime_profile
- sample: 18
- valid_profit_sample: 18
- equal_weight_avg_profit_pct: 0.42
- profitable_count: 15
- loss_or_flat_count: 3

### strength_momentum_vpw

- candidate_id: one_share_threshold_strength_momentum_vpw
- mapped_family: entry_strength_momentum_recheck
- sample: 18
- valid_profit_sample: 18
- equal_weight_avg_profit_pct: 0.42
- profitable_count: 15
- loss_or_flat_count: 3

### overbought_or_liquidity

- candidate_id: one_share_threshold_overbought_or_liquidity
- mapped_family: pre_submit_guard_attribution
- sample: 12
- valid_profit_sample: 12
- equal_weight_avg_profit_pct: 0.1325
- profitable_count: 10
- loss_or_flat_count: 2

### cooldown_or_hard_safety

- candidate_id: one_share_threshold_cooldown_or_hard_safety
- mapped_family: hard_safety_observation_only
- sample: 16
- valid_profit_sample: 16
- equal_weight_avg_profit_pct: 0.0525
- profitable_count: 13
- loss_or_flat_count: 3

### ai_score_near_buy

- candidate_id: one_share_threshold_ai_score_near_buy
- mapped_family: entry_opportunity_recheck_runtime
- sample: 14
- valid_profit_sample: 14
- equal_weight_avg_profit_pct: -0.113571
- profitable_count: 11
- loss_or_flat_count: 3

## Workorders

### order_one_share_threshold_latency_or_freshness_entry_hook_review

- mapped_family: latency_classifier_runtime_profile
- runtime_effect: false
- allowed_runtime_apply: false
- ai_recommended_disposition: attach_existing_entry_hook
- evidence:
  - threshold_group=latency_or_freshness
  - sample=18
  - valid_profit_sample=18
  - profitable_count=15
  - loss_or_flat_count=3
  - equal_weight_avg_profit_pct=0.42
  - runtime_effect=false
  - allowed_runtime_apply=false

### order_one_share_threshold_strength_momentum_vpw_entry_hook_review

- mapped_family: entry_strength_momentum_recheck
- runtime_effect: false
- allowed_runtime_apply: false
- ai_recommended_disposition: attach_existing_entry_hook
- evidence:
  - threshold_group=strength_momentum_vpw
  - sample=18
  - valid_profit_sample=18
  - profitable_count=15
  - loss_or_flat_count=3
  - equal_weight_avg_profit_pct=0.42
  - runtime_effect=false
  - allowed_runtime_apply=false

### order_one_share_threshold_overbought_or_liquidity_entry_hook_review

- mapped_family: pre_submit_guard_attribution
- runtime_effect: false
- allowed_runtime_apply: false
- ai_recommended_disposition: keep_collecting
- evidence:
  - threshold_group=overbought_or_liquidity
  - sample=12
  - valid_profit_sample=12
  - profitable_count=10
  - loss_or_flat_count=2
  - equal_weight_avg_profit_pct=0.1325
  - runtime_effect=false
  - allowed_runtime_apply=false
