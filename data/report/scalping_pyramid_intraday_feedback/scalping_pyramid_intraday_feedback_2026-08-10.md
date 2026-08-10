# 2026-08-10 Scalping Pyramid Intraday Feedback

- generated_at: 2026-08-10T21:14:08+09:00
- decision_authority: source_only_pyramid_intraday_feedback_no_runtime_mutation
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: intraday_threshold_mutation, intraday_runtime_apply, hard_safety_relaxation, broker_guard_bypass, order_guard_relaxation, stale_quote_bypass, cooldown_bypass, quantity_guard_relaxation, position_cap_release, provider_route_change, bot_restart, real_execution_quality_approval

## Summary

- pyramid_feedback_row_count: 5
- closed_pyramid_row_count: 0
- pyramid_would_have_helped_count: 0
- pyramid_correctly_blocked_count: 0
- pyramid_overheat_or_reversal_risk_count: 0
- pyramid_open_unresolved_count: 5
- one_share_event_count: 0
- one_share_closed_count: 0
- one_share_pyramid_opportunity_count: 0
- one_share_pyramid_missed_upside_count: 0
- one_share_pyramid_missed_upside_rate: 0.00
- one_share_pyramid_avg_opportunity_cost_pct: 0.00
- probe_residual_zero_fill_count: 0
- probe_residual_soft_abort_count: 0
- probe_residual_missed_upside_candidate_count: 0
- probe_residual_pyramid_threshold_missed_upside_candidate_count: 0
- probe_residual_real_outcome_closed_count: 0
- probe_residual_realized_winner_zero_fill_count: 0
- probe_residual_realized_loss_or_flat_zero_fill_count: 0
- probe_residual_realized_winner_confirmation_ready_count: 0
- probe_residual_realized_loss_or_flat_confirmation_ready_count: 0
- post_hard_abort_recovery_evaluation_seen_count: 0
- post_hard_abort_recovery_confirmation_ready_count: 0
- post_hard_abort_recovery_evaluation_not_run_profitable_count: 0
- canonical_expansion_missed_upside_count: 0
- canonical_expansion_source_quality_valid_missed_upside_count: 0
- post_probe_runtime_confirmation_source_quality_disputed_count: 0
- post_probe_legacy_label_conflict_count: 0
- post_probe_confirmation_false_positive_loss_or_flat_count: 0
- probe_residual_confirmation_ready_equal_weight_avg_profit_pct: 0.0000
- probe_residual_confirmation_ready_notional_weighted_ev_pct: 0.0000
- probe_residual_confirmation_ready_simple_sum_profit_proxy_krw: 0.00
- probe_residual_pyramid_evaluation_seen_count: 0
- normal_winner_expansion: {"by_effective_venue": [], "by_market_session_bucket": [], "candidate_count": 0, "closed_candidate_count": 0, "correctly_not_expanded_or_reversal_count": 0, "diagnostic_win_rate": 0.0, "equal_weight_avg_profit_pct": 0.0, "feature_axis_metrics": {"ai_score": [], "blocker_reason": [], "buy_pressure_10t": [], "entry_profit_pct": [], "micro_vwap_side": [], "tick_acceleration_ratio": []}, "label_counts": [], "notional_weighted_ev_pct": 0.0, "probe_confirmation_signature_metrics": [], "realized_incremental_winner_count": 0, "source_quality_blocked_candidate_count": 0, "source_quality_valid_candidate_count": 0, "temporal_inversion_candidate_count": 0, "transient_extension_exit_timing_needed_count": 0, "venue_source_quality_blocked_closed_count": 0, "venue_source_quality_valid_closed_count": 0}
- whole_day_real_entry_lifecycle: {"by_effective_venue": [], "by_market_session_bucket": [], "canceled_unfilled_cycle_count": 0, "closed_cycle_count": 0, "diagnostic_win_rate": 0.0, "equal_weight_avg_profit_pct": 0.0, "filled_cycle_count": 0, "flat_count": 0, "holding_cycle_count": 0, "loss_count": 0, "multi_leg_probe_cycle_count": 0, "multi_leg_zero_residual_fill_count": 0, "pending_entry_cycle_count": 0, "realized_pnl_krw_known_count": 0, "realized_pnl_krw_known_sum": 0, "realized_pnl_krw_missing_count": 0, "realized_pnl_source_quality_state": "not_applicable_no_closed_cycle", "single_share_plan_closed_winner_count": 0, "submitted_cycle_count": 0, "venue_source_quality_invalid_count": 0, "venue_source_quality_valid_count": 0, "winner_count": 0}
- real_scale_in_performance: {"active_unrealized_count": 0, "avg_down_execution_count": 0, "by_outcome_cohort": {"avg_down": {"active_unrealized_count": 0, "closed_count": 0, "closed_loss_or_flat_count": 0, "closed_winner_count": 0, "equal_weight_avg_final_position_profit_pct": null, "execution_count": 0, "runtime_apply_authority": false}, "normal_pyramid": {"active_unrealized_count": 0, "closed_count": 0, "closed_loss_or_flat_count": 0, "closed_winner_count": 0, "equal_weight_avg_final_position_profit_pct": null, "execution_count": 0, "runtime_apply_authority": false}, "unknown": {"active_unrealized_count": 0, "closed_count": 0, "closed_loss_or_flat_count": 0, "closed_winner_count": 0, "equal_weight_avg_final_position_profit_pct": null, "execution_count": 0, "runtime_apply_authority": false}, "winner_recovery": {"active_unrealized_count": 0, "closed_count": 0, "closed_loss_or_flat_count": 0, "closed_winner_count": 0, "equal_weight_avg_final_position_profit_pct": null, "execution_count": 0, "runtime_apply_authority": false}}, "closed_count": 0, "completed_outcome_available": false, "execution_count": 0, "normal_pyramid_execution_count": 0, "source_quality_adjusted_ev_available": false, "source_quality_adjusted_ev_unavailable_reason": "no_closed_scale_in_position", "winner_expansion_vs_avg_down_asymmetry_observed": false, "winner_recovery_execution_count": 0, "winner_recovery_qty_cap_invalid_count": 0}
- pyramid_min_profit_pct: 1.1
- pyramid_threshold_source: same_day_unique_runtime_pyramid_evaluation

## Blocker Metrics

- blocker=profit_not_enough sample=4 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=pyramid_hard_blocked:micro_vwap_severe_overheated,large_sell_detected,fresh_micro_confirmation_missing sample=1 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00

## Rows

- record_id= code=032820 name=우리기술 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.19 final=None ai=50.0 tick=0.25 micro_vwap=-35.42
- record_id= code=001440 name=대한전선 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.64 final=None ai=52.0 tick=1.0 micro_vwap=48.95
- record_id= code=082740 name=한화엔진 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.43 final=None ai=50.0 tick=0.615 micro_vwap=-7.48
- record_id= code=138080 name=오이솔루션 label=pyramid_open_unresolved blocker=pyramid_hard_blocked:micro_vwap_severe_overheated,large_sell_detected,fresh_micro_confirmation_missing profit=1.17 final=None ai=59.0 tick=0.0 micro_vwap=249.79
- record_id= code=217590 name=티엠씨 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.12 final=None ai=50.0 tick=1.157 micro_vwap=30.68

## Real Scale-In Performance Rows


## One Share Opportunity Rows


## Whole-Day Real Entry Lifecycle Rows


## Normal Winner Expansion Rows
