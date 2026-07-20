# 2026-07-20 Rising Missed Scout Workorder

- generated_at: 2026-07-20T21:02:52+09:00
- decision_authority: source_only_operational_workorder
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: runtime_threshold_mutation, stale_submit_bypass, broker_guard_bypass, order_guard_relaxation, provider_route_change, bot_restart, forced_one_share_success_counting, real_execution_quality_approval

## Summary

- forced_scout_record_count: 224
- forced_scout_with_post_sell_count: 15
- profitable_forced_scout_count: 12
- loss_or_flat_forced_scout_count: 3
- winner_avg_profit_rate: 0.8942
- loser_avg_profit_rate: -2.9867
- forced_initial_entry_equal_weight_avg_profit_pct: 0.118
- forced_initial_entry_notional_weighted_ev_pct: 0.124401
- forced_initial_entry_estimated_gross_pnl_krw: 7328.818
- total_position_estimated_gross_pnl_krw: -1354.453
- scale_in_delta_after_initial_entry_row_count: 0
- net_pnl_unavailable_reason: fee_tax_fields_missing
- shared_source_signature_count: 1
- take_profit_runner_review_candidate_count: 8
- take_profit_avg_giveback_pct: 1.0475
- current_missed_count: 0
- scale_in_price_guard_block_record_count: 0
- scale_in_qty_block_record_count: 1
- scale_in_executed_record_count: 0
- code_improvement_order_count: 5

## Workorders

### order_rising_missed_classifier_prior_feedback_bridge

- title: rising missed cumulative classifier prior bridge
- mapped_family: rising_missed_classifier_prior_feedback_bridge
- runtime_effect: false
- allowed_runtime_apply: false
- evidence:
  - prior_count=92
  - recommendation_counts={"hold_sample": 51, "loss_filter": 32, "positive_prior": 1, "source_quality_blocked": 8}
  - runtime_effect=false

### order_rising_missed_scout_post_sell_bridge

- title: rising missed scout post-sell bridge for normal-entry recheck
- mapped_family: rising_missed_scout_post_sell_bridge
- runtime_effect: false
- allowed_runtime_apply: false
- evidence:
  - winner_count=12
  - loser_count=3
  - winner_avg_profit_rate=0.8942
  - shared_source_signature_count=1
  - runner_review_candidate_count=8
  - current_missed_count=0
  - current_missed_eligible_count=0
  - all_winner_rows_had_latency_pass=False
  - all_winner_rows_had_order_bundle_submitted=True

### order_rising_missed_scout_take_profit_capture_review

- title: rising missed scout take-profit capture review
- mapped_family: rising_missed_scout_take_profit_capture_review
- runtime_effect: false
- allowed_runtime_apply: false
- evidence:
  - winner_count=12
  - evaluated_capture_count=12
  - avg_peak_profit=1.9417
  - avg_profit_rate=0.8942
  - avg_giveback_pct=1.0475
  - runner_review_candidate_count=8
  - runtime_effect=false

### order_rising_missed_scout_scale_in_qty_evidence_split

- title: rising missed scout scale-in quantity and evidence blocker split
- mapped_family: rising_missed_scout_scale_in_qty_evidence_split
- runtime_effect: false
- allowed_runtime_apply: false
- evidence:
  - profitable_forced_scout_count=12
  - qty_block_record_count=1
  - scale_in_executed_record_count=0
  - qty_block_reason_counts=pyramid_evidence_insufficient:ai_score_below_min,tick_accel_below_min=1
  - price_guard_block_record_count=0

### order_rising_missed_scout_loss_filter

- title: rising missed scout loss filter before any expansion
- mapped_family: rising_missed_scout_loss_filter
- runtime_effect: false
- allowed_runtime_apply: false
- evidence:
  - loser_count=3
  - loser_avg_profit_rate=-2.9867
  - loser_avg_peak_profit=0.1867
  - shared_source_signature_count=1
  - losers_also_had_latency_pass=False
  - losers_also_had_order_bundle_submitted=True
