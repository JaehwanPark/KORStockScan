# 2026-07-21 Rising Missed Scout Workorder

- generated_at: 2026-07-21T20:56:30+09:00
- decision_authority: source_only_operational_workorder
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: runtime_threshold_mutation, stale_submit_bypass, broker_guard_bypass, order_guard_relaxation, provider_route_change, bot_restart, forced_one_share_success_counting, real_execution_quality_approval

## Summary

- forced_scout_record_count: 323
- forced_scout_with_post_sell_count: 3
- profitable_forced_scout_count: 0
- loss_or_flat_forced_scout_count: 3
- winner_avg_profit_rate: None
- loser_avg_profit_rate: -1.2633
- forced_initial_entry_equal_weight_avg_profit_pct: -1.263333
- forced_initial_entry_notional_weighted_ev_pct: -1.144369
- forced_initial_entry_estimated_gross_pnl_krw: -12944.702
- total_position_estimated_gross_pnl_krw: -11459.551
- scale_in_delta_after_initial_entry_row_count: 0
- net_pnl_unavailable_reason: fee_tax_fields_missing
- shared_source_signature_count: 0
- take_profit_runner_review_candidate_count: 0
- take_profit_avg_giveback_pct: None
- current_missed_count: 0
- scale_in_price_guard_block_record_count: 0
- scale_in_qty_block_record_count: 0
- scale_in_executed_record_count: 0
- code_improvement_order_count: 2

## Workorders

### order_rising_missed_classifier_prior_feedback_bridge

- title: rising missed cumulative classifier prior bridge
- mapped_family: rising_missed_classifier_prior_feedback_bridge
- runtime_effect: false
- allowed_runtime_apply: false
- evidence:
  - prior_count=84
  - recommendation_counts={"hold_sample": 47, "loss_filter": 29, "positive_prior": 1, "source_quality_blocked": 7}
  - runtime_effect=false

### order_rising_missed_scout_loss_filter

- title: rising missed scout loss filter before any expansion
- mapped_family: rising_missed_scout_loss_filter
- runtime_effect: false
- allowed_runtime_apply: false
- evidence:
  - loser_count=3
  - loser_avg_profit_rate=-1.2633
  - loser_avg_peak_profit=0.53
  - shared_source_signature_count=0
  - losers_also_had_latency_pass=False
  - losers_also_had_order_bundle_submitted=True
