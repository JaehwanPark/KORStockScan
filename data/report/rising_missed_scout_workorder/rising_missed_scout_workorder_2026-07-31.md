# 2026-07-31 Rising Missed Scout Workorder

- generated_at: 2026-08-01T01:21:26+09:00
- decision_authority: source_only_operational_workorder
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: runtime_threshold_mutation, stale_submit_bypass, broker_guard_bypass, order_guard_relaxation, provider_route_change, bot_restart, forced_one_share_success_counting, real_execution_quality_approval

## Summary

- forced_scout_record_count: 472
- forced_scout_with_post_sell_count: 5
- profitable_forced_scout_count: 5
- loss_or_flat_forced_scout_count: 0
- winner_avg_profit_rate: 0.564
- loser_avg_profit_rate: None
- forced_initial_entry_equal_weight_avg_profit_pct: 0.564
- forced_initial_entry_notional_weighted_ev_pct: 0.520383
- forced_initial_entry_estimated_gross_pnl_krw: 3935.66
- total_position_estimated_gross_pnl_krw: 96490.0
- scale_in_delta_after_initial_entry_row_count: 1
- net_pnl_unavailable_reason: fee_tax_fields_missing
- shared_source_signature_count: 0
- take_profit_runner_review_candidate_count: 0
- take_profit_avg_giveback_pct: 0.428
- current_missed_count: 0
- scale_in_price_guard_block_record_count: 1
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
  - prior_count=63
  - recommendation_counts={"hold_sample": 50, "loss_filter": 8, "positive_prior": 1, "source_quality_blocked": 4}
  - runtime_effect=false

### order_rising_missed_scout_post_sell_bridge

- title: rising missed scout post-sell bridge for normal-entry recheck
- mapped_family: rising_missed_scout_post_sell_bridge
- runtime_effect: false
- allowed_runtime_apply: false
- evidence:
  - winner_count=5
  - loser_count=0
  - winner_avg_profit_rate=0.564
  - shared_source_signature_count=0
  - runner_review_candidate_count=0
  - current_missed_count=0
  - current_missed_eligible_count=0
  - all_winner_rows_had_latency_pass=False
  - all_winner_rows_had_order_bundle_submitted=False

### order_rising_missed_scout_scale_in_price_guard_split

- title: rising missed scout profitable scale-in price guard split
- mapped_family: rising_missed_scout_scale_in_price_guard_split
- runtime_effect: false
- allowed_runtime_apply: false
- evidence:
  - profitable_forced_scout_count=5
  - record_with_scale_in_event_count=3
  - pyramid_ok_record_count=1
  - price_guard_block_record_count=1
  - scale_in_executed_record_count=0
  - price_guard_reason_counts=micro_vwap_bp>60.0=2
  - pyramid_reason_counts=profit_not_enough=23,rising_missed_scout_pyramid_bridge_blocked:profit_not_enough,large_sell_detected=4,rising_missed_scout_pyramid_bridge_blocked:profit_not_enough=2,rising_missed_scout_pyramid_bridge_ok=2,scalping_pyramid_ok=2,pyramid_hard_blocked:buy_pressure_severe_below_min,large_sell_detected=1

### order_rising_missed_scout_scale_in_qty_evidence_split

- title: rising missed scout scale-in quantity and evidence blocker split
- mapped_family: rising_missed_scout_scale_in_qty_evidence_split
- runtime_effect: false
- allowed_runtime_apply: false
- evidence:
  - profitable_forced_scout_count=5
  - qty_block_record_count=1
  - scale_in_executed_record_count=0
  - qty_block_reason_counts=position_cap_or_budget=2
  - price_guard_block_record_count=1
