# 2026-09-04 Rising Missed Scout Workorder

- generated_at: 2026-09-05T00:52:30+09:00
- decision_authority: source_only_operational_workorder
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: runtime_threshold_mutation, stale_submit_bypass, broker_guard_bypass, order_guard_relaxation, provider_route_change, bot_restart, forced_one_share_success_counting, real_execution_quality_approval

## Summary

- forced_scout_record_count: 359
- forced_scout_with_post_sell_count: 1
- forced_scout_post_sell_join_coverage_pct: 0.278552
- forced_scout_outcome_coverage_state: partial
- forced_scout_outcome_join_ready: True
- forced_scout_outcome_contrast_ready: False
- forced_scout_outcome_economic_inference_ready: False
- profitable_forced_scout_count: 1
- loss_or_flat_forced_scout_count: 0
- winner_avg_profit_rate: 0.757
- loser_avg_profit_rate: None
- forced_initial_entry_equal_weight_avg_profit_pct: 0.757
- forced_initial_entry_notional_weighted_ev_pct: 0.757
- forced_initial_entry_estimated_gross_pnl_krw: 145.193
- total_position_estimated_gross_pnl_krw: 145.041
- scale_in_delta_after_initial_entry_row_count: 0
- net_pnl_unavailable_reason: fee_tax_fields_missing
- shared_source_signature_count: 0
- take_profit_runner_review_candidate_count: 0
- take_profit_avg_giveback_pct: 0.053
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
  - prior_count=92
  - recommendation_counts={"hold_sample": 61, "loss_filter": 27, "positive_prior": 1, "recheck_prior": 3}
  - runtime_effect=false

### order_rising_missed_entry_turn_bbo_coverage

- title: rising missed entry-turn executable BBO coverage closure
- mapped_family: rising_missed_entry_turn_point_replay
- runtime_effect: false
- allowed_runtime_apply: false
- evidence:
  - entry_turn_replay_status=source_quality_blocked
  - candidate_count=317
  - runtime_instrumentation_reflected=true
  - pre_anchor_bbo_path_event_count=2690
  - exact_ws_bbo_join_coverage_pct=2.866242
  - pre_anchor_bbo_coverage_pct=2.229299
  - paired_coverage_pct=0
  - primary_right_censored_pct=0
  - source_quality_gap_counts={"causal_turn_not_confirmed": 1, "current_outcome_non_executable_or_unresolved": 312, "exact_venue_session_ws_bbo_missing": 302, "pre_anchor_path_missing_or_insufficient": 8, "symbol_master:missing": 3}
