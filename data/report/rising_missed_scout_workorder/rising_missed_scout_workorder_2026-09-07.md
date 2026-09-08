# 2026-09-07 Rising Missed Scout Workorder

- generated_at: 2026-09-07T21:43:16+09:00
- decision_authority: source_only_operational_workorder
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: runtime_threshold_mutation, stale_submit_bypass, broker_guard_bypass, order_guard_relaxation, provider_route_change, bot_restart, forced_one_share_success_counting, real_execution_quality_approval

## Summary

- forced_scout_record_count: 401
- forced_scout_with_post_sell_count: 2
- forced_scout_post_sell_join_coverage_pct: 0.498753
- forced_scout_outcome_coverage_state: partial
- forced_scout_outcome_join_ready: True
- forced_scout_outcome_contrast_ready: False
- forced_scout_outcome_economic_inference_ready: False
- profitable_forced_scout_count: 2
- loss_or_flat_forced_scout_count: 0
- winner_avg_profit_rate: 0.7105
- loser_avg_profit_rate: None
- forced_initial_entry_equal_weight_avg_profit_pct: 0.7105
- forced_initial_entry_notional_weighted_ev_pct: 0.723534
- forced_initial_entry_estimated_gross_pnl_krw: 229.577
- total_position_estimated_gross_pnl_krw: 453.228
- scale_in_delta_after_initial_entry_row_count: 2
- net_pnl_unavailable_reason: fee_tax_fields_missing
- shared_source_signature_count: 0
- take_profit_runner_review_candidate_count: 1
- take_profit_avg_giveback_pct: 0.4945
- current_missed_count: 0
- scale_in_price_guard_block_record_count: 0
- scale_in_qty_block_record_count: 1
- scale_in_executed_record_count: 2
- code_improvement_order_count: 3

## Workorders

### order_rising_missed_classifier_prior_feedback_bridge

- title: rising missed cumulative classifier prior bridge
- mapped_family: rising_missed_classifier_prior_feedback_bridge
- runtime_effect: false
- allowed_runtime_apply: false
- evidence:
  - prior_count=86
  - recommendation_counts={"hold_sample": 43, "loss_filter": 43}
  - runtime_effect=false

### order_rising_missed_scout_scale_in_qty_evidence_split

- title: rising missed scout scale-in quantity and evidence blocker split
- mapped_family: rising_missed_scout_scale_in_qty_evidence_split
- runtime_effect: false
- allowed_runtime_apply: false
- evidence:
  - profitable_forced_scout_count=2
  - qty_block_record_count=1
  - scale_in_executed_record_count=2
  - qty_block_reason_counts=pyramid_evidence_insufficient:ai_score_below_min,tick_accel_below_min=1,pyramid_evidence_insufficient:ai_score_below_min,buy_pressure_below_min=1
  - price_guard_block_record_count=0

### order_rising_missed_entry_turn_bbo_coverage

- title: rising missed entry-turn executable BBO coverage closure
- mapped_family: rising_missed_entry_turn_point_replay
- runtime_effect: false
- allowed_runtime_apply: false
- evidence:
  - entry_turn_replay_status=source_quality_blocked
  - candidate_count=353
  - runtime_instrumentation_reflected=true
  - pre_anchor_bbo_path_event_count=2044
  - exact_ws_bbo_join_coverage_pct=3.170029
  - pre_anchor_bbo_coverage_pct=4.034582
  - paired_coverage_pct=0
  - primary_right_censored_pct=0
  - source_quality_gap_counts={"causal_turn_not_confirmed": 3, "current_outcome_non_executable_or_unresolved": 344, "exact_venue_session_ws_bbo_missing": 332, "pre_anchor_path_missing_or_insufficient": 8, "symbol_master:missing": 6}
