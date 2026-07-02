# 2026-07-02 Rising Missed Scout Workorder

- generated_at: 2026-07-02T20:10:25+09:00
- decision_authority: source_only_operational_workorder
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: runtime_threshold_mutation, stale_submit_bypass, broker_guard_bypass, order_guard_relaxation, provider_route_change, bot_restart, forced_one_share_success_counting, real_execution_quality_approval

## Summary

- forced_scout_record_count: 39
- forced_scout_with_post_sell_count: 14
- profitable_forced_scout_count: 11
- loss_or_flat_forced_scout_count: 3
- winner_avg_profit_rate: 1.9091
- loser_avg_profit_rate: -3.0467
- current_missed_count: 3
- scale_in_price_guard_block_record_count: 7
- scale_in_qty_block_record_count: 1
- scale_in_executed_record_count: 2
- code_improvement_order_count: 5

## Workorders

### order_rising_missed_initial_quality_feedback_loop

- title: rising missed initial quality feedback loop
- mapped_family: rising_missed_initial_quality_feedback_loop
- runtime_effect: false
- allowed_runtime_apply: false
- evidence:
  - rising_missed_avg_down_ge2_count=1
  - initial_quality_fail_count=1
  - feedback_label_counts=rising_missed_initial_quality_fail=1
  - runtime_effect=false

### order_rising_missed_scout_post_sell_bridge

- title: rising missed scout post-sell bridge for normal-entry recheck
- mapped_family: rising_missed_scout_post_sell_bridge
- runtime_effect: false
- allowed_runtime_apply: false
- evidence:
  - winner_count=11
  - loser_count=3
  - winner_avg_profit_rate=1.9091
  - current_missed_count=3
  - current_missed_eligible_count=0
  - all_winner_rows_had_latency_pass=True
  - all_winner_rows_had_order_bundle_submitted=True

### order_rising_missed_scout_scale_in_price_guard_split

- title: rising missed scout profitable scale-in price guard split
- mapped_family: rising_missed_scout_scale_in_price_guard_split
- runtime_effect: false
- allowed_runtime_apply: false
- evidence:
  - profitable_forced_scout_count=11
  - record_with_scale_in_event_count=11
  - pyramid_ok_record_count=7
  - price_guard_block_record_count=7
  - scale_in_executed_record_count=2
  - price_guard_reason_counts=micro_vwap_bp>60.0=11,quote_stale=5
  - pyramid_reason_counts=profit_not_enough=36,scalping_pyramid_ok=17,scalping_buy_window_blocked=4,pyramid_quality_blocked:tick_accel_below_min,micro_vwap_overheated=2,add_judgment_locked=1,trend_not_strong=1,scale_in_cooldown=1,pyramid_quality_blocked:ai_score_below_min,micro_vwap_overheated=1,pyramid_quality_blocked:ai_score_below_min,tick_accel_below_min,micro_vwap_overheated=1

### order_rising_missed_scout_scale_in_qty_evidence_split

- title: rising missed scout scale-in quantity and evidence blocker split
- mapped_family: rising_missed_scout_scale_in_qty_evidence_split
- runtime_effect: false
- allowed_runtime_apply: false
- evidence:
  - profitable_forced_scout_count=11
  - qty_block_record_count=1
  - scale_in_executed_record_count=2
  - qty_block_reason_counts=pyramid_evidence_insufficient:ai_score_ok=1
  - price_guard_block_record_count=7

### order_rising_missed_scout_loss_filter

- title: rising missed scout loss filter before any expansion
- mapped_family: rising_missed_scout_loss_filter
- runtime_effect: false
- allowed_runtime_apply: false
- evidence:
  - loser_count=3
  - loser_avg_profit_rate=-3.0467
  - losers_also_had_latency_pass=True
  - losers_also_had_order_bundle_submitted=True
