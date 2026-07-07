# 2026-07-07 One Share Threshold Opportunity

- generated_at: 2026-07-07T20:10:44+09:00
- window: 2026-06-04 -> 2026-07-07
- decision_authority: source_only_threshold_opportunity_audit
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: runtime_threshold_mutation, buy_score_threshold_relaxation_without_preopen_apply, stale_submit_bypass, broker_guard_bypass, order_guard_relaxation, provider_route_change, bot_restart, forced_one_share_success_counting, real_execution_quality_approval
- ai_review_status: parsed

## Summary

- forced_record_count: 75
- post_sell_joined_count: 40
- profitable_joined_count: 30
- loss_or_flat_joined_count: 10
- threshold_opportunity_count: 5
- code_improvement_order_count: 2

## Opportunities

### strength_momentum_vpw

- candidate_id: one_share_threshold_strength_momentum_vpw
- mapped_family: entry_strength_momentum_recheck
- sample: 37
- valid_profit_sample: 37
- equal_weight_avg_profit_pct: 0.046216
- profitable_count: 28
- loss_or_flat_count: 9

### latency_or_freshness

- candidate_id: one_share_threshold_latency_or_freshness
- mapped_family: latency_classifier_runtime_profile
- sample: 40
- valid_profit_sample: 40
- equal_weight_avg_profit_pct: 0.0115
- profitable_count: 30
- loss_or_flat_count: 10

### ai_score_near_buy

- candidate_id: one_share_threshold_ai_score_near_buy
- mapped_family: entry_opportunity_recheck_runtime
- sample: 34
- valid_profit_sample: 34
- equal_weight_avg_profit_pct: -0.161176
- profitable_count: 26
- loss_or_flat_count: 8

### cooldown_or_hard_safety

- candidate_id: one_share_threshold_cooldown_or_hard_safety
- mapped_family: hard_safety_observation_only
- sample: 36
- valid_profit_sample: 36
- equal_weight_avg_profit_pct: -0.193611
- profitable_count: 26
- loss_or_flat_count: 10

### overbought_or_liquidity

- candidate_id: one_share_threshold_overbought_or_liquidity
- mapped_family: pre_submit_guard_attribution
- sample: 28
- valid_profit_sample: 28
- equal_weight_avg_profit_pct: -0.3925
- profitable_count: 20
- loss_or_flat_count: 8

## Workorders

### order_one_share_threshold_strength_momentum_vpw_entry_hook_review

- mapped_family: entry_strength_momentum_recheck
- runtime_effect: false
- allowed_runtime_apply: false
- ai_recommended_disposition: attach_existing_entry_hook
- evidence:
  - threshold_group=strength_momentum_vpw
  - sample=37
  - valid_profit_sample=37
  - profitable_count=28
  - loss_or_flat_count=9
  - equal_weight_avg_profit_pct=0.046216
  - runtime_effect=false
  - allowed_runtime_apply=false

### order_one_share_threshold_latency_or_freshness_entry_hook_review

- mapped_family: latency_classifier_runtime_profile
- runtime_effect: false
- allowed_runtime_apply: false
- ai_recommended_disposition: keep_collecting
- evidence:
  - threshold_group=latency_or_freshness
  - sample=40
  - valid_profit_sample=40
  - profitable_count=30
  - loss_or_flat_count=10
  - equal_weight_avg_profit_pct=0.0115
  - runtime_effect=false
  - allowed_runtime_apply=false
