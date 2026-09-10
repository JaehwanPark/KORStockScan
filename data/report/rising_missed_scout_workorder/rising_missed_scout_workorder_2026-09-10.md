# 2026-09-10 Rising Missed Scout Workorder

- generated_at: 2026-09-10T22:06:40+09:00
- decision_authority: source_only_operational_workorder
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: runtime_threshold_mutation, stale_submit_bypass, broker_guard_bypass, order_guard_relaxation, provider_route_change, bot_restart, forced_one_share_success_counting, real_execution_quality_approval

## Summary

- forced_scout_record_count: 416
- forced_scout_with_post_sell_count: 5
- forced_scout_post_sell_join_coverage_pct: 1.201923
- forced_scout_outcome_coverage_state: partial
- forced_scout_outcome_join_ready: True
- forced_scout_outcome_contrast_ready: True
- forced_scout_outcome_economic_inference_ready: False
- profitable_forced_scout_count: 3
- loss_or_flat_forced_scout_count: 2
- winner_avg_profit_rate: 1.1323
- loser_avg_profit_rate: -0.7855
- forced_initial_entry_equal_weight_avg_profit_pct: 0.3652
- forced_initial_entry_notional_weighted_ev_pct: -0.056816
- forced_initial_entry_estimated_gross_pnl_krw: -28.401
- total_position_estimated_gross_pnl_krw: -15.975
- scale_in_delta_after_initial_entry_row_count: 0
- net_pnl_unavailable_reason: fee_tax_fields_missing
- shared_source_signature_count: 0
- take_profit_runner_review_candidate_count: 2
- take_profit_avg_giveback_pct: 0.641
- current_missed_count: 0
- scale_in_price_guard_block_record_count: 0
- scale_in_qty_block_record_count: 0
- scale_in_executed_record_count: 0
- code_improvement_order_count: 5

## Workorders

### order_rising_missed_classifier_prior_feedback_bridge

- title: rising missed cumulative classifier prior bridge
- mapped_family: rising_missed_classifier_prior_feedback_bridge
- runtime_effect: false
- allowed_runtime_apply: false
- evidence:
  - prior_count=98
  - recommendation_counts={"hold_sample": 63, "loss_filter": 35}
  - runtime_effect=false

### order_rising_missed_scout_post_sell_bridge

- title: rising missed scout post-sell bridge for normal-entry recheck
- mapped_family: rising_missed_scout_post_sell_bridge
- runtime_effect: false
- allowed_runtime_apply: false
- evidence:
  - winner_count=3
  - loser_count=2
  - winner_avg_profit_rate=1.1323
  - shared_source_signature_count=0
  - runner_review_candidate_count=2
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
  - avg_peak_profit=1.7733
  - avg_profit_rate=1.1323
  - avg_giveback_pct=0.641
  - runner_review_candidate_count=2
  - runtime_effect=false

### order_rising_missed_scout_loss_filter

- title: rising missed scout loss filter before any expansion
- mapped_family: rising_missed_scout_loss_filter
- runtime_effect: false
- allowed_runtime_apply: false
- evidence:
  - loser_count=2
  - loser_avg_profit_rate=-0.7855
  - loser_avg_peak_profit=0.41
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
  - candidate_count=402
  - runtime_instrumentation_reflected=true
  - pre_anchor_bbo_path_event_count=2607
  - exact_ws_bbo_join_coverage_pct=0
  - pre_anchor_bbo_coverage_pct=0
  - paired_coverage_pct=0
  - primary_right_censored_pct=100.0
  - source_quality_gap_counts={"current_outcome_non_executable_or_unresolved": 402, "symbol_master:master_unavailable": 402}
