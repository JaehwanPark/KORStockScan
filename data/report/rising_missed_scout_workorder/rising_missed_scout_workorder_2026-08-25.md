# 2026-08-25 Rising Missed Scout Workorder

- generated_at: 2026-08-26T02:48:52+09:00
- decision_authority: source_only_operational_workorder
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: runtime_threshold_mutation, stale_submit_bypass, broker_guard_bypass, order_guard_relaxation, provider_route_change, bot_restart, forced_one_share_success_counting, real_execution_quality_approval

## Summary

- forced_scout_record_count: 404
- forced_scout_with_post_sell_count: 8
- forced_scout_post_sell_join_coverage_pct: 1.980198
- forced_scout_outcome_coverage_state: partial
- profitable_forced_scout_count: 7
- loss_or_flat_forced_scout_count: 1
- winner_avg_profit_rate: 0.638
- loser_avg_profit_rate: -0.23
- forced_initial_entry_equal_weight_avg_profit_pct: 0.5295
- forced_initial_entry_notional_weighted_ev_pct: 0.405618
- forced_initial_entry_estimated_gross_pnl_krw: 1780.217
- total_position_estimated_gross_pnl_krw: 1777.832
- scale_in_delta_after_initial_entry_row_count: 0
- net_pnl_unavailable_reason: fee_tax_fields_missing
- shared_source_signature_count: 0
- take_profit_runner_review_candidate_count: 0
- take_profit_avg_giveback_pct: 0.412
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
  - prior_count=144
  - recommendation_counts={"hold_sample": 75, "loss_filter": 66, "positive_prior": 1, "source_quality_blocked": 2}
  - runtime_effect=false

### order_rising_missed_scout_post_sell_bridge

- title: rising missed scout post-sell bridge for normal-entry recheck
- mapped_family: rising_missed_scout_post_sell_bridge
- runtime_effect: false
- allowed_runtime_apply: false
- evidence:
  - winner_count=7
  - loser_count=1
  - winner_avg_profit_rate=0.638
  - shared_source_signature_count=0
  - runner_review_candidate_count=0
  - current_missed_count=0
  - current_missed_eligible_count=0
  - all_winner_rows_had_latency_pass=True
  - all_winner_rows_had_order_bundle_submitted=True

### order_rising_missed_scout_scale_in_qty_evidence_split

- title: rising missed scout scale-in quantity and evidence blocker split
- mapped_family: rising_missed_scout_scale_in_qty_evidence_split
- runtime_effect: false
- allowed_runtime_apply: false
- evidence:
  - profitable_forced_scout_count=7
  - qty_block_record_count=1
  - scale_in_executed_record_count=0
  - qty_block_reason_counts=position_cap_or_budget=3
  - price_guard_block_record_count=0

### order_rising_missed_scout_loss_filter

- title: rising missed scout loss filter before any expansion
- mapped_family: rising_missed_scout_loss_filter
- runtime_effect: false
- allowed_runtime_apply: false
- evidence:
  - loser_count=1
  - loser_avg_profit_rate=-0.23
  - loser_avg_peak_profit=0.81
  - shared_source_signature_count=0
  - losers_also_had_latency_pass=True
  - losers_also_had_order_bundle_submitted=True
