# 2026-07-03 Rising Missed Scout Workorder

- generated_at: 2026-07-03T14:27:13+09:00
- decision_authority: source_only_operational_workorder
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: runtime_threshold_mutation, stale_submit_bypass, broker_guard_bypass, order_guard_relaxation, provider_route_change, bot_restart, forced_one_share_success_counting, real_execution_quality_approval

## Summary

- forced_scout_record_count: 30
- forced_scout_with_post_sell_count: 14
- profitable_forced_scout_count: 11
- loss_or_flat_forced_scout_count: 3
- winner_avg_profit_rate: 1.4736
- loser_avg_profit_rate: -4.5967
- current_missed_count: 5
- scale_in_price_guard_block_record_count: 0
- scale_in_qty_block_record_count: 0
- scale_in_executed_record_count: 4
- code_improvement_order_count: 3

## Workorders

### order_rising_missed_initial_quality_feedback_loop

- title: rising missed initial quality feedback loop
- mapped_family: rising_missed_initial_quality_feedback_loop
- runtime_effect: false
- allowed_runtime_apply: false
- evidence:
  - rising_missed_avg_down_ge2_count=4
  - initial_quality_fail_count=3
  - feedback_label_counts=rising_missed_initial_quality_fail=3,rising_missed_scale_in_rescue_warning=1
  - runtime_effect=false

### order_rising_missed_scout_post_sell_bridge

- title: rising missed scout post-sell bridge for normal-entry recheck
- mapped_family: rising_missed_scout_post_sell_bridge
- runtime_effect: false
- allowed_runtime_apply: false
- evidence:
  - winner_count=11
  - loser_count=3
  - winner_avg_profit_rate=1.4736
  - current_missed_count=5
  - current_missed_eligible_count=0
  - all_winner_rows_had_latency_pass=True
  - all_winner_rows_had_order_bundle_submitted=True

### order_rising_missed_scout_loss_filter

- title: rising missed scout loss filter before any expansion
- mapped_family: rising_missed_scout_loss_filter
- runtime_effect: false
- allowed_runtime_apply: false
- evidence:
  - loser_count=3
  - loser_avg_profit_rate=-4.5967
  - losers_also_had_latency_pass=True
  - losers_also_had_order_bundle_submitted=True
