# 2026-09-02 Rising Missed Scout Workorder

- generated_at: 2026-09-02T18:24:12+09:00
- decision_authority: source_only_operational_workorder
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: runtime_threshold_mutation, stale_submit_bypass, broker_guard_bypass, order_guard_relaxation, provider_route_change, bot_restart, forced_one_share_success_counting, real_execution_quality_approval

## Summary

- forced_scout_record_count: 360
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

### order_rising_missed_entry_turn_bbo_coverage

- title: rising missed entry-turn executable BBO coverage closure
- mapped_family: rising_missed_entry_turn_point_replay
- runtime_effect: false
- allowed_runtime_apply: false
- evidence:
  - entry_turn_replay_status=source_quality_blocked
  - candidate_count=457
  - exact_ws_bbo_join_coverage_pct=0.224215
  - pre_anchor_bbo_coverage_pct=0
  - paired_coverage_pct=0
  - primary_right_censored_pct=100.0
  - source_quality_gap_counts={"current_outcome_non_executable_or_unresolved": 456, "exact_venue_session_ws_bbo_missing": 445, "pre_anchor_path_missing_or_insufficient": 1, "symbol_master:missing": 11}
