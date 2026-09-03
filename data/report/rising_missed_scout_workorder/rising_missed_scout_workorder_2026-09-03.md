# 2026-09-03 Rising Missed Scout Workorder

- generated_at: 2026-09-03T23:51:28+09:00
- decision_authority: source_only_operational_workorder
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: runtime_threshold_mutation, stale_submit_bypass, broker_guard_bypass, order_guard_relaxation, provider_route_change, bot_restart, forced_one_share_success_counting, real_execution_quality_approval

## Summary

- forced_scout_record_count: 457
- forced_scout_with_post_sell_count: 3
- forced_scout_post_sell_join_coverage_pct: 0.656455
- forced_scout_outcome_coverage_state: partial
- profitable_forced_scout_count: 2
- loss_or_flat_forced_scout_count: 1
- winner_avg_profit_rate: 1.206
- loser_avg_profit_rate: -3.037
- forced_initial_entry_equal_weight_avg_profit_pct: -0.208333
- forced_initial_entry_notional_weighted_ev_pct: 0.085049
- forced_initial_entry_estimated_gross_pnl_krw: 139.932
- total_position_estimated_gross_pnl_krw: 140.351
- scale_in_delta_after_initial_entry_row_count: 0
- net_pnl_unavailable_reason: fee_tax_fields_missing
- shared_source_signature_count: 0
- take_profit_runner_review_candidate_count: 0
- take_profit_avg_giveback_pct: 0.299
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
  - prior_count=111
  - recommendation_counts={"hold_sample": 54, "loss_filter": 55, "positive_prior": 1, "source_quality_blocked": 1}
  - runtime_effect=false

### order_rising_missed_scout_post_sell_bridge

- title: rising missed scout post-sell bridge for normal-entry recheck
- mapped_family: rising_missed_scout_post_sell_bridge
- runtime_effect: false
- allowed_runtime_apply: false
- evidence:
  - winner_count=2
  - loser_count=1
  - winner_avg_profit_rate=1.206
  - shared_source_signature_count=0
  - runner_review_candidate_count=0
  - current_missed_count=0
  - current_missed_eligible_count=0
  - all_winner_rows_had_latency_pass=True
  - all_winner_rows_had_order_bundle_submitted=True

### order_rising_missed_scout_loss_filter

- title: rising missed scout loss filter before any expansion
- mapped_family: rising_missed_scout_loss_filter
- runtime_effect: false
- allowed_runtime_apply: false
- evidence:
  - loser_count=1
  - loser_avg_profit_rate=-3.037
  - loser_avg_peak_profit=0.23
  - shared_source_signature_count=0
  - losers_also_had_latency_pass=True
  - losers_also_had_order_bundle_submitted=True

### order_rising_missed_entry_turn_bbo_coverage

- title: rising missed entry-turn executable BBO coverage closure
- mapped_family: rising_missed_entry_turn_point_replay
- runtime_effect: false
- allowed_runtime_apply: false
- evidence:
  - entry_turn_replay_status=source_quality_blocked
  - candidate_count=399
  - exact_ws_bbo_join_coverage_pct=2.261307
  - pre_anchor_bbo_coverage_pct=3.015075
  - paired_coverage_pct=16.666667
  - primary_right_censored_pct=14.285714
  - source_quality_gap_counts={"causal_turn_not_confirmed": 3, "current_outcome_non_executable_or_unresolved": 391, "exact_venue_session_ws_bbo_missing": 383, "pre_anchor_path_missing_or_insufficient": 5, "symbol_master:missing": 1}
