# 2026-08-26 Rising Missed Scout Workorder

- generated_at: 2026-08-26T21:30:48+09:00
- decision_authority: source_only_operational_workorder
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: runtime_threshold_mutation, stale_submit_bypass, broker_guard_bypass, order_guard_relaxation, provider_route_change, bot_restart, forced_one_share_success_counting, real_execution_quality_approval

## Summary

- forced_scout_record_count: 428
- forced_scout_with_post_sell_count: 0
- forced_scout_post_sell_join_coverage_pct: 0.0
- forced_scout_outcome_coverage_state: no_closed_outcome
- profitable_forced_scout_count: 0
- loss_or_flat_forced_scout_count: 0
- winner_avg_profit_rate: None
- loser_avg_profit_rate: None
- forced_initial_entry_equal_weight_avg_profit_pct: None
- forced_initial_entry_notional_weighted_ev_pct: None
- forced_initial_entry_estimated_gross_pnl_krw: None
- total_position_estimated_gross_pnl_krw: None
- scale_in_delta_after_initial_entry_row_count: 0
- net_pnl_unavailable_reason: None
- shared_source_signature_count: 0
- take_profit_runner_review_candidate_count: 0
- take_profit_avg_giveback_pct: None
- current_missed_count: 0
- scale_in_price_guard_block_record_count: 0
- scale_in_qty_block_record_count: 0
- scale_in_executed_record_count: 0
- code_improvement_order_count: 1

## Workorders

### order_rising_missed_classifier_prior_feedback_bridge

- title: rising missed cumulative classifier prior bridge
- mapped_family: rising_missed_classifier_prior_feedback_bridge
- runtime_effect: false
- allowed_runtime_apply: false
- evidence:
  - prior_count=123
  - recommendation_counts={"hold_sample": 67, "loss_filter": 53, "positive_prior": 1, "source_quality_blocked": 2}
  - runtime_effect=false
