# 2026-09-09 Scalping Pyramid Intraday Feedback

- generated_at: 2026-09-09T20:40:21+09:00
- decision_authority: source_only_pyramid_intraday_feedback_no_runtime_mutation
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: intraday_threshold_mutation, intraday_runtime_apply, hard_safety_relaxation, broker_guard_bypass, order_guard_relaxation, stale_quote_bypass, cooldown_bypass, quantity_guard_relaxation, position_cap_release, provider_route_change, bot_restart, real_execution_quality_approval

## Summary

- pyramid_feedback_row_count: 11
- closed_pyramid_row_count: 0
- pyramid_would_have_helped_count: 0
- pyramid_correctly_blocked_count: 0
- pyramid_overheat_or_reversal_risk_count: 0
- pyramid_open_unresolved_count: 11
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
- post_terminal_abort_recovery_confirmation_preserved_gap_count: 0
- post_terminal_abort_recovery_ai_supportive_evaluation_count: 0
- post_terminal_abort_recovery_ai_tape_substitution_count: 0
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
- normal_winner_expansion: {"by_effective_venue": [], "by_market_session_bucket": [], "candidate_count": 0, "closed_candidate_count": 0, "correctly_not_expanded_or_reversal_count": 0, "diagnostic_win_rate": 0.0, "equal_weight_avg_profit_pct": 0.0, "feature_axis_metrics": {"ai_score": [], "blocker_reason": [], "buy_pressure_10t": [], "entry_profit_pct": [], "micro_vwap_side": [], "recovery_ai_parent_prompt_version": [], "recovery_ai_tape_substitution": [], "recovery_ai_thesis_state": [], "recovery_holding_ai_action": [], "recovery_holding_ai_data_quality": [], "tick_acceleration_ratio": []}, "label_counts": [], "notional_weighted_ev_pct": 0.0, "probe_confirmation_signature_metrics": [], "realized_incremental_winner_count": 0, "source_quality_blocked_candidate_count": 0, "source_quality_valid_candidate_count": 0, "temporal_inversion_candidate_count": 0, "transient_extension_exit_timing_needed_count": 0, "venue_source_quality_blocked_closed_count": 0, "venue_source_quality_valid_closed_count": 0}
- winner_recovery_runtime_funnel: {"allowed_runtime_apply": false, "decision_authority": "source_only_winner_recovery_runtime_funnel_attribution", "dominant_non_execution_layer": "none", "downstream_guard_block_reason_counts": [], "forbidden_uses": ["intraday_threshold_mutation", "intraday_runtime_apply", "hard_safety_relaxation", "broker_guard_bypass", "order_guard_relaxation", "stale_quote_bypass", "cooldown_bypass", "quantity_guard_relaxation", "position_cap_release", "provider_route_change", "bot_restart", "real_execution_quality_approval"], "invalid_timestamp_event_count": 0, "runtime_effect": false, "runtime_gate_block_reason_counts": [], "runtime_gate_blocked_count": 0, "runtime_gate_evaluation_count": 0, "runtime_gate_selected_count": 0, "selected_closed_without_submit_count": 0, "selected_downstream_guard_blocked_count": 0, "selected_executed_count": 0, "selected_open_or_unresolved_count": 0, "selected_order_submitted_count": 0, "selection_to_execution_rate": 0.0, "selection_to_submit_rate": 0.0, "source_quality_status": "pass", "state": "no_runtime_gate_observation"}
- whole_day_real_entry_lifecycle: {"by_effective_venue": [], "by_market_session_bucket": [], "canceled_unfilled_cycle_count": 0, "closed_cycle_count": 0, "diagnostic_win_rate": 0.0, "equal_weight_avg_profit_pct": 0.0, "filled_cycle_count": 0, "flat_count": 0, "holding_cycle_count": 0, "loss_count": 0, "multi_leg_probe_cycle_count": 0, "multi_leg_zero_residual_fill_count": 0, "pending_entry_cycle_count": 0, "realized_pnl_krw_known_count": 0, "realized_pnl_krw_known_sum": 0, "realized_pnl_krw_missing_count": 0, "realized_pnl_krw_source_counts": [], "realized_pnl_source_quality_state": "not_applicable_no_closed_cycle", "single_share_plan_closed_winner_count": 0, "submitted_cycle_count": 0, "venue_source_quality_invalid_count": 0, "venue_source_quality_valid_count": 0, "winner_count": 0}
- real_scale_in_performance: {"active_unrealized_count": 0, "avg_down_execution_count": 0, "by_outcome_cohort": {"avg_down": {"active_unrealized_count": 0, "closed_count": 0, "closed_loss_or_flat_count": 0, "closed_winner_count": 0, "equal_weight_avg_final_position_profit_pct": null, "equal_weight_avg_scale_in_leg_net_return_pct": null, "execution_count": 0, "runtime_apply_authority": false, "scale_in_leg_diagnostic_win_rate": null, "scale_in_leg_net_pnl_proxy_krw_sum": null, "source_quality_adjusted_ev_pct": null, "source_quality_blocked_closed_count": 0, "source_quality_valid_closed_count": 0}, "normal_pyramid": {"active_unrealized_count": 0, "closed_count": 0, "closed_loss_or_flat_count": 0, "closed_winner_count": 0, "equal_weight_avg_final_position_profit_pct": null, "equal_weight_avg_scale_in_leg_net_return_pct": null, "execution_count": 0, "runtime_apply_authority": false, "scale_in_leg_diagnostic_win_rate": null, "scale_in_leg_net_pnl_proxy_krw_sum": null, "source_quality_adjusted_ev_pct": null, "source_quality_blocked_closed_count": 0, "source_quality_valid_closed_count": 0}, "unknown": {"active_unrealized_count": 0, "closed_count": 0, "closed_loss_or_flat_count": 0, "closed_winner_count": 0, "equal_weight_avg_final_position_profit_pct": null, "equal_weight_avg_scale_in_leg_net_return_pct": null, "execution_count": 0, "runtime_apply_authority": false, "scale_in_leg_diagnostic_win_rate": null, "scale_in_leg_net_pnl_proxy_krw_sum": null, "source_quality_adjusted_ev_pct": null, "source_quality_blocked_closed_count": 0, "source_quality_valid_closed_count": 0}, "winner_recovery": {"active_unrealized_count": 0, "closed_count": 0, "closed_loss_or_flat_count": 0, "closed_winner_count": 0, "equal_weight_avg_final_position_profit_pct": null, "equal_weight_avg_scale_in_leg_net_return_pct": null, "execution_count": 0, "runtime_apply_authority": false, "scale_in_leg_diagnostic_win_rate": null, "scale_in_leg_net_pnl_proxy_krw_sum": null, "source_quality_adjusted_ev_pct": null, "source_quality_blocked_closed_count": 0, "source_quality_valid_closed_count": 0}}, "closed_count": 0, "completed_outcome_available": false, "equal_weight_avg_scale_in_leg_net_return_pct": null, "execution_count": 0, "normal_pyramid_execution_count": 0, "scale_in_leg_diagnostic_win_rate": null, "scale_in_leg_net_pnl_proxy_krw_sum": null, "source_quality_adjusted_ev_available": false, "source_quality_adjusted_ev_pct": null, "source_quality_adjusted_ev_unavailable_reason": "no_closed_scale_in_position", "source_quality_blocked_closed_count": 0, "source_quality_valid_closed_count": 0, "winner_expansion_vs_avg_down_asymmetry_observed": false, "winner_recovery_by_ai_parent_prompt_version": [], "winner_recovery_by_ai_thesis_state": [], "winner_recovery_by_holding_ai_action": [], "winner_recovery_by_holding_ai_data_quality": [], "winner_recovery_execution_count": 0, "winner_recovery_qty_cap_invalid_count": 0}
- pyramid_min_profit_pct: 1.1
- pyramid_threshold_source: same_day_unique_runtime_pyramid_evaluation

## Blocker Metrics

- blocker=profit_not_enough sample=8 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=pyramid_quality_blocked:ai_score_below_min,buy_pressure_below_min,tick_accel_stale,micro_context_stale sample=1 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=pyramid_quality_blocked:ai_score_below_min,tick_accel_stale,micro_context_stale sample=1 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=trend_not_strong sample=1 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00

## Rows

- record_id= code=126340 name=비나텍 label=pyramid_open_unresolved blocker=pyramid_quality_blocked:ai_score_below_min,buy_pressure_below_min,tick_accel_stale,micro_context_stale profit=1.76 final=None ai=50.0 tick=0.873 micro_vwap=-12.05
- record_id= code=000500 name=가온전선 label=pyramid_open_unresolved blocker=trend_not_strong profit=1.31 final=None ai=50.0 tick=0.857 micro_vwap=0.58
- record_id= code=001440 name=대한전선 label=pyramid_open_unresolved blocker=pyramid_quality_blocked:ai_score_below_min,tick_accel_stale,micro_context_stale profit=2.22 final=None ai=69.0 tick=0.0 micro_vwap=0.0
- record_id= code=006340 name=대원전선 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.42 final=None ai=49.0 tick=1.0 micro_vwap=-16.17
- record_id= code=454910 name=두산로보틱스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.6 final=None ai=61.0 tick=0.0 micro_vwap=0.0
- record_id= code=009830 name=한화솔루션 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.75 final=None ai=50.0 tick=0.0 micro_vwap=0.0
- record_id= code=322000 name=HD현대에너지솔루션 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.03 final=None ai=56.0 tick=0.0 micro_vwap=0.0
- record_id= code=011170 name=롯데케미칼 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.82 final=None ai=50.0 tick=0.0 micro_vwap=0.0
- record_id= code=047050 name=포스코인터내셔널 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.64 final=None ai=50.0 tick=0.0 micro_vwap=-21.73
- record_id= code=484870 name=엠앤씨솔루션 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.62 final=None ai=62.0 tick=0.0 micro_vwap=0.0
- record_id= code=006650 name=대한유화 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.85 final=None ai=50.0 tick=0.0 micro_vwap=0.0

## Real Scale-In Performance Rows


## Winner Recovery Runtime Funnel Rows


## One Share Opportunity Rows


## Whole-Day Real Entry Lifecycle Rows


## Normal Winner Expansion Rows
