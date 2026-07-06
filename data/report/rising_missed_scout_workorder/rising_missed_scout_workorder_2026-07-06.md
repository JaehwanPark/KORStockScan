# 2026-07-06 Rising Missed Scout Workorder

- generated_at: 2026-07-06T20:43:54+09:00
- decision_authority: source_only_operational_workorder
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: runtime_threshold_mutation, stale_submit_bypass, broker_guard_bypass, order_guard_relaxation, provider_route_change, bot_restart, forced_one_share_success_counting, real_execution_quality_approval

## Summary

- forced_scout_record_count: 36
- forced_scout_with_post_sell_count: 18
- profitable_forced_scout_count: 13
- loss_or_flat_forced_scout_count: 5
- winner_avg_profit_rate: 1.1715
- loser_avg_profit_rate: -3.454
- current_missed_count: 4
- scale_in_price_guard_block_record_count: 0
- scale_in_qty_block_record_count: 0
- scale_in_executed_record_count: 4
- code_improvement_order_count: 3

## Workorders

### order_rising_missed_classifier_prior_feedback_bridge

- title: rising missed cumulative classifier prior bridge
- mapped_family: rising_missed_classifier_prior_feedback_bridge
- runtime_effect: false
- allowed_runtime_apply: false
- evidence:
  - prior_count=28
  - recommendation_counts={"hold_sample": 14, "loss_filter": 1, "positive_prior": 7, "recheck_prior": 1, "source_quality_blocked": 5}
  - runtime_effect=false

### order_rising_missed_scout_post_sell_bridge

- title: rising missed scout post-sell bridge for normal-entry recheck
- mapped_family: rising_missed_scout_post_sell_bridge
- runtime_effect: false
- allowed_runtime_apply: false
- evidence:
  - winner_count=13
  - loser_count=5
  - winner_avg_profit_rate=1.1715
  - current_missed_count=4
  - current_missed_eligible_count=1
  - all_winner_rows_had_latency_pass=True
  - all_winner_rows_had_order_bundle_submitted=True

### order_rising_missed_scout_loss_filter

- title: rising missed scout loss filter before any expansion
- mapped_family: rising_missed_scout_loss_filter
- runtime_effect: false
- allowed_runtime_apply: false
- evidence:
  - loser_count=5
  - loser_avg_profit_rate=-3.454
  - losers_also_had_latency_pass=True
  - losers_also_had_order_bundle_submitted=True
