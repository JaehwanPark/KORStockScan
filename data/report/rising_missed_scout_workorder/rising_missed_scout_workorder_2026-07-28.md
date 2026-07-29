# 2026-07-28 Rising Missed Scout Workorder

- generated_at: 2026-07-29T08:17:22+09:00
- decision_authority: source_only_operational_workorder
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: runtime_threshold_mutation, stale_submit_bypass, broker_guard_bypass, order_guard_relaxation, provider_route_change, bot_restart, forced_one_share_success_counting, real_execution_quality_approval

## Summary

- forced_scout_record_count: 151
- forced_scout_with_post_sell_count: 12
- profitable_forced_scout_count: 7
- loss_or_flat_forced_scout_count: 5
- winner_avg_profit_rate: 0.8714
- loser_avg_profit_rate: -2.098
- forced_initial_entry_equal_weight_avg_profit_pct: -0.365833
- forced_initial_entry_notional_weighted_ev_pct: -0.701882
- forced_initial_entry_estimated_gross_pnl_krw: -5002.312
- total_position_estimated_gross_pnl_krw: -5001.744
- scale_in_delta_after_initial_entry_row_count: 0
- net_pnl_unavailable_reason: fee_tax_fields_missing
- shared_source_signature_count: 2
- take_profit_runner_review_candidate_count: 4
- take_profit_avg_giveback_pct: 0.5429
- current_missed_count: 0
- scale_in_price_guard_block_record_count: 0
- scale_in_qty_block_record_count: 0
- scale_in_executed_record_count: 0
- code_improvement_order_count: 4

## Workorders

### order_rising_missed_classifier_prior_feedback_bridge

- title: rising missed cumulative classifier prior bridge
- mapped_family: rising_missed_classifier_prior_feedback_bridge
- runtime_effect: false
- allowed_runtime_apply: false
- evidence:
  - prior_count=46
  - recommendation_counts={"hold_sample": 34, "loss_filter": 8, "source_quality_blocked": 4}
  - runtime_effect=false

### order_rising_missed_scout_post_sell_bridge

- title: rising missed scout post-sell bridge for normal-entry recheck
- mapped_family: rising_missed_scout_post_sell_bridge
- runtime_effect: false
- allowed_runtime_apply: false
- evidence:
  - winner_count=7
  - loser_count=5
  - winner_avg_profit_rate=0.8714
  - shared_source_signature_count=2
  - runner_review_candidate_count=4
  - current_missed_count=0
  - current_missed_eligible_count=0
  - all_winner_rows_had_latency_pass=True
  - all_winner_rows_had_order_bundle_submitted=True

### order_rising_missed_scout_take_profit_capture_review

- title: rising missed scout take-profit capture review
- mapped_family: rising_missed_scout_take_profit_capture_review
- runtime_effect: false
- allowed_runtime_apply: false
- evidence:
  - winner_count=7
  - evaluated_capture_count=7
  - avg_peak_profit=1.4143
  - avg_profit_rate=0.8714
  - avg_giveback_pct=0.5429
  - runner_review_candidate_count=4
  - runtime_effect=false

### order_rising_missed_scout_loss_filter

- title: rising missed scout loss filter before any expansion
- mapped_family: rising_missed_scout_loss_filter
- runtime_effect: false
- allowed_runtime_apply: false
- evidence:
  - loser_count=5
  - loser_avg_profit_rate=-2.098
  - loser_avg_peak_profit=0.134
  - shared_source_signature_count=2
  - losers_also_had_latency_pass=True
  - losers_also_had_order_bundle_submitted=True
