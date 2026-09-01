# 2026-09-01 Rising Missed Scout Workorder

- generated_at: 2026-09-01T21:40:18+09:00
- decision_authority: source_only_operational_workorder
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: runtime_threshold_mutation, stale_submit_bypass, broker_guard_bypass, order_guard_relaxation, provider_route_change, bot_restart, forced_one_share_success_counting, real_execution_quality_approval

## Summary

- forced_scout_record_count: 424
- forced_scout_with_post_sell_count: 3
- forced_scout_post_sell_join_coverage_pct: 0.707547
- forced_scout_outcome_coverage_state: partial
- profitable_forced_scout_count: 3
- loss_or_flat_forced_scout_count: 0
- winner_avg_profit_rate: 0.5927
- loser_avg_profit_rate: None
- forced_initial_entry_equal_weight_avg_profit_pct: 0.592667
- forced_initial_entry_notional_weighted_ev_pct: 0.688283
- forced_initial_entry_estimated_gross_pnl_krw: 292.245
- total_position_estimated_gross_pnl_krw: 291.954
- scale_in_delta_after_initial_entry_row_count: 0
- net_pnl_unavailable_reason: fee_tax_fields_missing
- shared_source_signature_count: 0
- take_profit_runner_review_candidate_count: 1
- take_profit_avg_giveback_pct: 0.4207
- current_missed_count: 0
- scale_in_price_guard_block_record_count: 0
- scale_in_qty_block_record_count: 0
- scale_in_executed_record_count: 0
- code_improvement_order_count: 3

## Workorders

### order_rising_missed_classifier_prior_feedback_bridge

- title: rising missed cumulative classifier prior bridge
- mapped_family: rising_missed_classifier_prior_feedback_bridge
- runtime_effect: false
- allowed_runtime_apply: false
- evidence:
  - prior_count=110
  - recommendation_counts={"hold_sample": 67, "loss_filter": 41, "positive_prior": 1, "source_quality_blocked": 1}
  - runtime_effect=false

### order_rising_missed_scout_post_sell_bridge

- title: rising missed scout post-sell bridge for normal-entry recheck
- mapped_family: rising_missed_scout_post_sell_bridge
- runtime_effect: false
- allowed_runtime_apply: false
- evidence:
  - winner_count=3
  - loser_count=0
  - winner_avg_profit_rate=0.5927
  - shared_source_signature_count=0
  - runner_review_candidate_count=1
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
  - winner_count=3
  - evaluated_capture_count=3
  - avg_peak_profit=1.0133
  - avg_profit_rate=0.5927
  - avg_giveback_pct=0.4207
  - runner_review_candidate_count=1
  - runtime_effect=false
