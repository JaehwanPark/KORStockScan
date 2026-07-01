# 2026-07-01 Rising Missed Scout Workorder

- generated_at: 2026-07-01T13:32:14+09:00
- decision_authority: source_only_operational_workorder
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: runtime_threshold_mutation, stale_submit_bypass, broker_guard_bypass, order_guard_relaxation, provider_route_change, bot_restart, forced_one_share_success_counting, real_execution_quality_approval

## Summary

- forced_scout_record_count: 39
- forced_scout_with_post_sell_count: 23
- profitable_forced_scout_count: 17
- loss_or_flat_forced_scout_count: 6
- winner_avg_profit_rate: 2.0112
- loser_avg_profit_rate: -3.365
- current_missed_count: 14
- scale_in_price_guard_block_record_count: 16
- scale_in_qty_block_record_count: 4
- scale_in_executed_record_count: 4
- code_improvement_order_count: 4

## Workorders

### order_rising_missed_scout_post_sell_bridge

- title: rising missed scout post-sell bridge for normal-entry recheck
- mapped_family: rising_missed_scout_post_sell_bridge
- runtime_effect: false
- allowed_runtime_apply: false
- evidence:
  - winner_count=17
  - loser_count=6
  - winner_avg_profit_rate=2.0112
  - current_missed_count=14
  - current_missed_eligible_count=0
  - all_winner_rows_had_latency_pass=True
  - all_winner_rows_had_order_bundle_submitted=True

### order_rising_missed_scout_scale_in_price_guard_split

- title: rising missed scout profitable scale-in price guard split
- mapped_family: rising_missed_scout_scale_in_price_guard_split
- runtime_effect: false
- allowed_runtime_apply: false
- evidence:
  - profitable_forced_scout_count=17
  - record_with_scale_in_event_count=17
  - pyramid_ok_record_count=17
  - price_guard_block_record_count=16
  - scale_in_executed_record_count=4
  - price_guard_reason_counts=micro_vwap_bp>60.0=25,quote_stale=19
  - pyramid_reason_counts=profit_not_enough=170,scalping_pyramid_ok=57,trend_not_strong=7,scale_in_cooldown=2

### order_rising_missed_scout_scale_in_qty_evidence_split

- title: rising missed scout scale-in quantity and evidence blocker split
- mapped_family: rising_missed_scout_scale_in_qty_evidence_split
- runtime_effect: false
- allowed_runtime_apply: false
- evidence:
  - profitable_forced_scout_count=17
  - qty_block_record_count=4
  - scale_in_executed_record_count=4
  - qty_block_reason_counts=pyramid_exposure_cap=5,pyramid_evidence_insufficient:ai_score_ok,buy_pressure_ok=2,pyramid_evidence_insufficient:tick_accel_ok=2,pyramid_evidence_insufficient:buy_pressure_ok,tick_accel_ok=1
  - price_guard_block_record_count=16

### order_rising_missed_scout_loss_filter

- title: rising missed scout loss filter before any expansion
- mapped_family: rising_missed_scout_loss_filter
- runtime_effect: false
- allowed_runtime_apply: false
- evidence:
  - loser_count=6
  - loser_avg_profit_rate=-3.365
  - losers_also_had_latency_pass=True
  - losers_also_had_order_bundle_submitted=True
