# 2026-08-27 Rising Missed Scout Workorder

- generated_at: 2026-08-27T21:34:00+09:00
- decision_authority: source_only_operational_workorder
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: runtime_threshold_mutation, stale_submit_bypass, broker_guard_bypass, order_guard_relaxation, provider_route_change, bot_restart, forced_one_share_success_counting, real_execution_quality_approval

## Summary

- forced_scout_record_count: 379
- forced_scout_with_post_sell_count: 2
- forced_scout_post_sell_join_coverage_pct: 0.527704
- forced_scout_outcome_coverage_state: partial
- profitable_forced_scout_count: 2
- loss_or_flat_forced_scout_count: 0
- winner_avg_profit_rate: 0.94
- loser_avg_profit_rate: None
- forced_initial_entry_equal_weight_avg_profit_pct: 0.94
- forced_initial_entry_notional_weighted_ev_pct: 0.697162
- forced_initial_entry_estimated_gross_pnl_krw: 1474.148
- total_position_estimated_gross_pnl_krw: 1470.338
- scale_in_delta_after_initial_entry_row_count: 0
- net_pnl_unavailable_reason: fee_tax_fields_missing
- shared_source_signature_count: 0
- take_profit_runner_review_candidate_count: 1
- take_profit_avg_giveback_pct: 0.225
- current_missed_count: 0
- scale_in_price_guard_block_record_count: 0
- scale_in_qty_block_record_count: 1
- scale_in_executed_record_count: 0
- code_improvement_order_count: 4

## Workorders

### order_rising_missed_classifier_prior_feedback_bridge

- title: rising missed cumulative classifier prior bridge
- mapped_family: rising_missed_classifier_prior_feedback_bridge
- runtime_effect: false
- allowed_runtime_apply: false
- evidence:
  - prior_count=138
  - recommendation_counts={"hold_sample": 93, "loss_filter": 42, "positive_prior": 1, "source_quality_blocked": 2}
  - runtime_effect=false

### order_rising_missed_scout_post_sell_bridge

- title: rising missed scout post-sell bridge for normal-entry recheck
- mapped_family: rising_missed_scout_post_sell_bridge
- runtime_effect: false
- allowed_runtime_apply: false
- evidence:
  - winner_count=2
  - loser_count=0
  - winner_avg_profit_rate=0.94
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
  - winner_count=2
  - evaluated_capture_count=2
  - avg_peak_profit=1.165
  - avg_profit_rate=0.94
  - avg_giveback_pct=0.225
  - runner_review_candidate_count=1
  - runtime_effect=false

### order_rising_missed_scout_scale_in_qty_evidence_split

- title: rising missed scout scale-in quantity and evidence blocker split
- mapped_family: rising_missed_scout_scale_in_qty_evidence_split
- runtime_effect: false
- allowed_runtime_apply: false
- evidence:
  - profitable_forced_scout_count=2
  - qty_block_record_count=1
  - scale_in_executed_record_count=0
  - qty_block_reason_counts=real_pyramid_ai_score_no_submit_authority:ai_score_sentinel_50=1
  - price_guard_block_record_count=0
