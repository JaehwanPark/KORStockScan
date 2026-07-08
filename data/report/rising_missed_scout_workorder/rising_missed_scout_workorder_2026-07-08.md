# 2026-07-08 Rising Missed Scout Workorder

- generated_at: 2026-07-08T21:29:47+09:00
- decision_authority: source_only_operational_workorder
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: runtime_threshold_mutation, stale_submit_bypass, broker_guard_bypass, order_guard_relaxation, provider_route_change, bot_restart, forced_one_share_success_counting, real_execution_quality_approval

## Summary

- forced_scout_record_count: 38
- forced_scout_with_post_sell_count: 18
- profitable_forced_scout_count: 7
- loss_or_flat_forced_scout_count: 11
- winner_avg_profit_rate: 1.7257
- loser_avg_profit_rate: -4.2627
- shared_source_signature_count: 3
- take_profit_runner_review_candidate_count: 4
- take_profit_avg_giveback_pct: 0.2471
- current_missed_count: 0
- scale_in_price_guard_block_record_count: 0
- scale_in_qty_block_record_count: 0
- scale_in_executed_record_count: 2
- code_improvement_order_count: 4

## Workorders

### order_rising_missed_classifier_prior_feedback_bridge

- title: rising missed cumulative classifier prior bridge
- mapped_family: rising_missed_classifier_prior_feedback_bridge
- runtime_effect: false
- allowed_runtime_apply: false
- evidence:
  - prior_count=32
  - recommendation_counts={"hold_sample": 12, "loss_filter": 5, "positive_prior": 7, "recheck_prior": 1, "source_quality_blocked": 7}
  - runtime_effect=false

### order_rising_missed_scout_post_sell_bridge

- title: rising missed scout post-sell bridge for normal-entry recheck
- mapped_family: rising_missed_scout_post_sell_bridge
- runtime_effect: false
- allowed_runtime_apply: false
- evidence:
  - winner_count=7
  - loser_count=11
  - winner_avg_profit_rate=1.7257
  - shared_source_signature_count=3
  - runner_review_candidate_count=4
  - current_missed_count=0
  - current_missed_eligible_count=0
  - all_winner_rows_had_latency_pass=False
  - all_winner_rows_had_order_bundle_submitted=False

### order_rising_missed_scout_take_profit_capture_review

- title: rising missed scout take-profit capture review
- mapped_family: rising_missed_scout_take_profit_capture_review
- runtime_effect: false
- allowed_runtime_apply: false
- evidence:
  - winner_count=7
  - evaluated_capture_count=7
  - avg_peak_profit=1.9729
  - avg_profit_rate=1.7257
  - avg_giveback_pct=0.2471
  - runner_review_candidate_count=4
  - runtime_effect=false

### order_rising_missed_scout_loss_filter

- title: rising missed scout loss filter before any expansion
- mapped_family: rising_missed_scout_loss_filter
- runtime_effect: false
- allowed_runtime_apply: false
- evidence:
  - loser_count=11
  - loser_avg_profit_rate=-4.2627
  - loser_avg_peak_profit=0.0618
  - shared_source_signature_count=3
  - losers_also_had_latency_pass=False
  - losers_also_had_order_bundle_submitted=True
