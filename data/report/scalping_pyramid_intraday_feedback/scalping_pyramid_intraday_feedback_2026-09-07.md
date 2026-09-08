# 2026-09-07 Scalping Pyramid Intraday Feedback

- generated_at: 2026-09-07T20:25:31+09:00
- decision_authority: source_only_pyramid_intraday_feedback_no_runtime_mutation
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: intraday_threshold_mutation, intraday_runtime_apply, hard_safety_relaxation, broker_guard_bypass, order_guard_relaxation, stale_quote_bypass, cooldown_bypass, quantity_guard_relaxation, position_cap_release, provider_route_change, bot_restart, real_execution_quality_approval

## Summary

- pyramid_feedback_row_count: 6
- closed_pyramid_row_count: 2
- pyramid_would_have_helped_count: 1
- pyramid_correctly_blocked_count: 1
- pyramid_overheat_or_reversal_risk_count: 0
- pyramid_open_unresolved_count: 4
- one_share_event_count: 2
- one_share_closed_count: 2
- one_share_pyramid_opportunity_count: 1
- one_share_pyramid_missed_upside_count: 1
- one_share_pyramid_missed_upside_rate: 0.50
- one_share_pyramid_avg_opportunity_cost_pct: 0.00
- probe_residual_zero_fill_count: 2
- probe_residual_soft_abort_count: 2
- probe_residual_missed_upside_candidate_count: 0
- probe_residual_pyramid_threshold_missed_upside_candidate_count: 1
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
- probe_residual_pyramid_evaluation_seen_count: 2
- normal_winner_expansion: {"by_effective_venue": [], "by_market_session_bucket": [], "candidate_count": 2, "closed_candidate_count": 0, "correctly_not_expanded_or_reversal_count": 0, "diagnostic_win_rate": 0.0, "equal_weight_avg_profit_pct": 0.0, "feature_axis_metrics": {"ai_score": [], "blocker_reason": [], "buy_pressure_10t": [], "entry_profit_pct": [], "micro_vwap_side": [], "recovery_ai_parent_prompt_version": [], "recovery_ai_tape_substitution": [], "recovery_ai_thesis_state": [], "recovery_holding_ai_action": [], "recovery_holding_ai_data_quality": [], "tick_acceleration_ratio": []}, "label_counts": [{"count": 2, "label": "source_quality_blocked"}], "notional_weighted_ev_pct": 0.0, "probe_confirmation_signature_metrics": [], "realized_incremental_winner_count": 0, "source_quality_blocked_candidate_count": 2, "source_quality_valid_candidate_count": 0, "temporal_inversion_candidate_count": 0, "transient_extension_exit_timing_needed_count": 0, "venue_source_quality_blocked_closed_count": 0, "venue_source_quality_valid_closed_count": 0}
- winner_recovery_runtime_funnel: {"allowed_runtime_apply": false, "decision_authority": "source_only_winner_recovery_runtime_funnel_attribution", "dominant_non_execution_layer": "none", "downstream_guard_block_reason_counts": [], "forbidden_uses": ["intraday_threshold_mutation", "intraday_runtime_apply", "hard_safety_relaxation", "broker_guard_bypass", "order_guard_relaxation", "stale_quote_bypass", "cooldown_bypass", "quantity_guard_relaxation", "position_cap_release", "provider_route_change", "bot_restart", "real_execution_quality_approval"], "invalid_timestamp_event_count": 0, "runtime_effect": false, "runtime_gate_block_reason_counts": [], "runtime_gate_blocked_count": 0, "runtime_gate_evaluation_count": 0, "runtime_gate_selected_count": 0, "selected_closed_without_submit_count": 0, "selected_downstream_guard_blocked_count": 0, "selected_executed_count": 0, "selected_open_or_unresolved_count": 0, "selected_order_submitted_count": 0, "selection_to_execution_rate": 0.0, "selection_to_submit_rate": 0.0, "source_quality_status": "pass", "state": "no_runtime_gate_observation"}
- whole_day_real_entry_lifecycle: {"by_effective_venue": [{"allowed_runtime_apply": false, "canceled_unfilled_cycle_count": 1, "closed_cycle_count": 0, "diagnostic_win_rate": 0.0, "effective_venue": "KRX", "equal_weight_avg_profit_pct": 0.0, "filled_cycle_count": 0, "flat_count": 0, "holding_cycle_count": 0, "loss_count": 0, "multi_leg_probe_cycle_count": 0, "realized_pnl_krw_known_count": 0, "realized_pnl_krw_known_sum": 0, "runtime_effect": false, "single_share_plan_closed_winner_count": 0, "submitted_cycle_count": 1, "winner_count": 0}, {"allowed_runtime_apply": false, "canceled_unfilled_cycle_count": 0, "closed_cycle_count": 2, "diagnostic_win_rate": 1.0, "effective_venue": "NXT", "equal_weight_avg_profit_pct": 0.71, "filled_cycle_count": 2, "flat_count": 0, "holding_cycle_count": 0, "loss_count": 0, "multi_leg_probe_cycle_count": 2, "realized_pnl_krw_known_count": 2, "realized_pnl_krw_known_sum": 453, "runtime_effect": false, "single_share_plan_closed_winner_count": 0, "submitted_cycle_count": 2, "winner_count": 2}], "by_market_session_bucket": [{"allowed_runtime_apply": false, "canceled_unfilled_cycle_count": 1, "closed_cycle_count": 0, "diagnostic_win_rate": 0.0, "equal_weight_avg_profit_pct": 0.0, "filled_cycle_count": 0, "flat_count": 0, "holding_cycle_count": 0, "loss_count": 0, "market_session_bucket": "krx_regular", "multi_leg_probe_cycle_count": 0, "realized_pnl_krw_known_count": 0, "realized_pnl_krw_known_sum": 0, "runtime_effect": false, "single_share_plan_closed_winner_count": 0, "submitted_cycle_count": 1, "winner_count": 0}, {"allowed_runtime_apply": false, "canceled_unfilled_cycle_count": 0, "closed_cycle_count": 2, "diagnostic_win_rate": 1.0, "equal_weight_avg_profit_pct": 0.71, "filled_cycle_count": 2, "flat_count": 0, "holding_cycle_count": 0, "loss_count": 0, "market_session_bucket": "nxt", "multi_leg_probe_cycle_count": 2, "realized_pnl_krw_known_count": 2, "realized_pnl_krw_known_sum": 453, "runtime_effect": false, "single_share_plan_closed_winner_count": 0, "submitted_cycle_count": 2, "winner_count": 2}], "canceled_unfilled_cycle_count": 1, "closed_cycle_count": 2, "diagnostic_win_rate": 1.0, "equal_weight_avg_profit_pct": 0.71, "filled_cycle_count": 2, "flat_count": 0, "holding_cycle_count": 0, "loss_count": 0, "multi_leg_probe_cycle_count": 2, "multi_leg_zero_residual_fill_count": 2, "pending_entry_cycle_count": 0, "realized_pnl_krw_known_count": 2, "realized_pnl_krw_known_sum": 453, "realized_pnl_krw_missing_count": 0, "realized_pnl_krw_source_counts": [{"count": 2, "source": "broker_fill_prices_fee_aware"}], "realized_pnl_source_quality_state": "complete", "single_share_plan_closed_winner_count": 0, "submitted_cycle_count": 3, "venue_source_quality_invalid_count": 0, "venue_source_quality_valid_count": 3, "winner_count": 2}
- real_scale_in_performance: {"active_unrealized_count": 0, "avg_down_execution_count": 1, "by_outcome_cohort": {"avg_down": {"active_unrealized_count": 0, "closed_count": 1, "closed_loss_or_flat_count": 0, "closed_winner_count": 1, "equal_weight_avg_final_position_profit_pct": 1.23, "equal_weight_avg_scale_in_leg_net_return_pct": 2.9733, "execution_count": 1, "runtime_apply_authority": false, "scale_in_leg_diagnostic_win_rate": 1.0, "scale_in_leg_net_pnl_proxy_krw_sum": 468.0, "source_quality_adjusted_ev_pct": 2.9733, "source_quality_blocked_closed_count": 0, "source_quality_valid_closed_count": 1}, "normal_pyramid": {"active_unrealized_count": 0, "closed_count": 1, "closed_loss_or_flat_count": 0, "closed_winner_count": 1, "equal_weight_avg_final_position_profit_pct": 0.19, "equal_weight_avg_scale_in_leg_net_return_pct": -0.2947, "execution_count": 1, "runtime_apply_authority": false, "scale_in_leg_diagnostic_win_rate": 0.0, "scale_in_leg_net_pnl_proxy_krw_sum": -46.0, "source_quality_adjusted_ev_pct": -0.2947, "source_quality_blocked_closed_count": 0, "source_quality_valid_closed_count": 1}, "unknown": {"active_unrealized_count": 0, "closed_count": 0, "closed_loss_or_flat_count": 0, "closed_winner_count": 0, "equal_weight_avg_final_position_profit_pct": null, "equal_weight_avg_scale_in_leg_net_return_pct": null, "execution_count": 0, "runtime_apply_authority": false, "scale_in_leg_diagnostic_win_rate": null, "scale_in_leg_net_pnl_proxy_krw_sum": null, "source_quality_adjusted_ev_pct": null, "source_quality_blocked_closed_count": 0, "source_quality_valid_closed_count": 0}, "winner_recovery": {"active_unrealized_count": 0, "closed_count": 0, "closed_loss_or_flat_count": 0, "closed_winner_count": 0, "equal_weight_avg_final_position_profit_pct": null, "equal_weight_avg_scale_in_leg_net_return_pct": null, "execution_count": 0, "runtime_apply_authority": false, "scale_in_leg_diagnostic_win_rate": null, "scale_in_leg_net_pnl_proxy_krw_sum": null, "source_quality_adjusted_ev_pct": null, "source_quality_blocked_closed_count": 0, "source_quality_valid_closed_count": 0}}, "closed_count": 2, "completed_outcome_available": true, "equal_weight_avg_scale_in_leg_net_return_pct": 1.3393, "execution_count": 2, "normal_pyramid_execution_count": 1, "scale_in_leg_diagnostic_win_rate": 0.5, "scale_in_leg_net_pnl_proxy_krw_sum": 422.0, "source_quality_adjusted_ev_available": true, "source_quality_adjusted_ev_pct": 1.3461, "source_quality_adjusted_ev_unavailable_reason": "-", "source_quality_blocked_closed_count": 0, "source_quality_valid_closed_count": 2, "winner_expansion_vs_avg_down_asymmetry_observed": false, "winner_recovery_by_ai_parent_prompt_version": [], "winner_recovery_by_ai_thesis_state": [], "winner_recovery_by_holding_ai_action": [], "winner_recovery_by_holding_ai_data_quality": [], "winner_recovery_execution_count": 0, "winner_recovery_qty_cap_invalid_count": 0}
- pyramid_min_profit_pct: 1.1
- pyramid_threshold_source: same_day_unique_runtime_pyramid_evaluation

## Blocker Metrics

- blocker=profit_not_enough sample=3 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=pyramid_submitted sample=1 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=scalping_cutoff sample=1 recovered_rate=1.00 reversal_rate=0.00 blocked_then_recovered_rate=1.00
- blocker=trend_not_strong sample=1 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00

## Rows

- record_id= code=028050 name=삼성E&A label=pyramid_open_unresolved blocker=profit_not_enough profit=0.5 final=None ai=50.0 tick=0.0 micro_vwap=0.0
- record_id= code=375500 name=DL이앤씨 label=pyramid_open_unresolved blocker=trend_not_strong profit=1.2 final=None ai=52.0 tick=0.0 micro_vwap=0.0
- record_id= code=190510 name=나무가 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.07 final=None ai=50.0 tick=0.0 micro_vwap=38.15
- record_id=40942 code=249420 name=일동제약 label=pyramid_correctly_blocked blocker=pyramid_submitted profit=0.03 final=0.19 ai=64.0 tick=1.0 micro_vwap=4.48
- record_id= code=000660 name=SK하이닉스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.05 final=None ai=50.0 tick=0.0 micro_vwap=0.0
- record_id=40904 code=304100 name=솔트룩스 label=pyramid_would_have_helped blocker=scalping_cutoff profit=0.52 final=1.23 ai=45.0 tick=1.0 micro_vwap=0.0

## Real Scale-In Performance Rows

- record_id=40942 code=249420 name=일동제약 cohort=normal_pyramid type=PYRAMID reason=rising_missed_scout_pyramid_bridge_ok fill=15610.0x1 closed=True latest=0.19 final=0.19 leg_gross_proxy=-0.0641 leg_net_proxy=-0.2947 source_quality=True
- record_id=40904 code=304100 name=솔트룩스 cohort=avg_down type=AVG_DOWN reason=late_loss_avg_down_retry fill=15740.0x1 closed=True latest=1.23 final=1.23 leg_gross_proxy=3.2084 leg_net_proxy=2.9733 source_quality=True

## Winner Recovery Runtime Funnel Rows


## One Share Opportunity Rows

- record_id=40904 code=304100 name=솔트룩스 label=pyramid_would_have_helped canonical=expansion_source_quality_blocked opportunity_seen=True opportunity_profit=1.58 max_profit=1.58 opportunity_cost=0.0 final=1.23 residual_zero_fill=True residual_soft_abort=True residual_missed_candidate=False post_probe_real_outcome=source_quality_blocked confirmation_ready=False runtime_confirmation_ready=False confirmation_alignment=not_runtime_confirmed recovery_evaluation_seen=False recovery_confirmation_ready=False confirmation_source_quality_blockers=tick_context_not_fresh first_leg_qty=None first_leg_profit_proxy_krw=None
- record_id=40942 code=249420 name=일동제약 label=pyramid_correctly_blocked canonical=expansion_source_quality_blocked opportunity_seen=False opportunity_profit=None max_profit=0.83 opportunity_cost=0.83 final=0.19 residual_zero_fill=True residual_soft_abort=True residual_missed_candidate=False post_probe_real_outcome=source_quality_blocked confirmation_ready=False runtime_confirmation_ready=False confirmation_alignment=not_runtime_confirmed recovery_evaluation_seen=False recovery_confirmation_ready=False confirmation_source_quality_blockers=- first_leg_qty=None first_leg_profit_proxy_krw=None

## Whole-Day Real Entry Lifecycle Rows

- record_id=40581 code=387690 name=레메디 venue=KRX session=krx_regular state=canceled_unfilled planned_qty=1 submitted_qty=1 filled_qty=0 final=None realized_pnl_krw=None realized_pnl_source=None canonical=None
- record_id=40904 code=304100 name=솔트룩스 venue=NXT session=nxt state=closed planned_qty=17 submitted_qty=1 filled_qty=1 final=1.23 realized_pnl_krw=395 realized_pnl_source=broker_fill_prices_fee_aware canonical=expansion_source_quality_blocked
- record_id=40942 code=249420 name=일동제약 venue=NXT session=nxt state=closed planned_qty=18 submitted_qty=1 filled_qty=1 final=0.19 realized_pnl_krw=58 realized_pnl_source=broker_fill_prices_fee_aware canonical=expansion_source_quality_blocked

## Normal Winner Expansion Rows

- record_id=40904 code=304100 name=솔트룩스 label=source_quality_blocked entry_profit=0.52 incremental_mfe=0.8245 incremental_final=0.4763 confirmation=None
- record_id=40942 code=249420 name=일동제약 label=source_quality_blocked entry_profit=0.03 incremental_mfe=0.5698 incremental_final=-0.07 confirmation=None
