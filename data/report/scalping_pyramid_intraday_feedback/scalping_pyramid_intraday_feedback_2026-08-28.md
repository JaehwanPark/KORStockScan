# 2026-08-28 Scalping Pyramid Intraday Feedback

- generated_at: 2026-08-28T20:18:26+09:00
- decision_authority: source_only_pyramid_intraday_feedback_no_runtime_mutation
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: intraday_threshold_mutation, intraday_runtime_apply, hard_safety_relaxation, broker_guard_bypass, order_guard_relaxation, stale_quote_bypass, cooldown_bypass, quantity_guard_relaxation, position_cap_release, provider_route_change, bot_restart, real_execution_quality_approval

## Summary

- pyramid_feedback_row_count: 6
- closed_pyramid_row_count: 1
- pyramid_would_have_helped_count: 0
- pyramid_correctly_blocked_count: 0
- pyramid_overheat_or_reversal_risk_count: 1
- pyramid_open_unresolved_count: 5
- one_share_event_count: 1
- one_share_closed_count: 1
- one_share_pyramid_opportunity_count: 0
- one_share_pyramid_missed_upside_count: 0
- one_share_pyramid_missed_upside_rate: 0.00
- one_share_pyramid_avg_opportunity_cost_pct: 0.00
- probe_residual_zero_fill_count: 1
- probe_residual_soft_abort_count: 1
- probe_residual_missed_upside_candidate_count: 0
- probe_residual_pyramid_threshold_missed_upside_candidate_count: 0
- probe_residual_real_outcome_closed_count: 1
- probe_residual_realized_winner_zero_fill_count: 1
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
- probe_residual_pyramid_evaluation_seen_count: 1
- normal_winner_expansion: {"by_effective_venue": [{"allowed_runtime_apply": false, "effective_venue": "NXT", "notional_weighted_ev_pct": -0.7067, "realized_incremental_winner_count": 0, "runtime_effect": false, "sample_count": 1}], "by_market_session_bucket": [{"allowed_runtime_apply": false, "market_session_bucket": "nxt_entry_window", "notional_weighted_ev_pct": -0.7067, "realized_incremental_winner_count": 0, "runtime_effect": false, "sample_count": 1}], "candidate_count": 1, "closed_candidate_count": 1, "correctly_not_expanded_or_reversal_count": 1, "diagnostic_win_rate": 0.0, "equal_weight_avg_profit_pct": -0.7067, "feature_axis_metrics": {"ai_score": [{"bucket": "60_to_70", "daily_only_live_authority": false, "notional_weighted_ev_pct": -0.7067, "realized_incremental_winner_count": 0, "sample_count": 1}], "blocker_reason": [{"bucket": "rising_missed_scout_pyramid_bridge_blocked:profit_not_enough,buy_pressure_severe_below_min,micro_vwap_severe_overheated", "daily_only_live_authority": false, "notional_weighted_ev_pct": -0.7067, "realized_incremental_winner_count": 0, "sample_count": 1}], "buy_pressure_10t": [{"bucket": "lt_50", "daily_only_live_authority": false, "notional_weighted_ev_pct": -0.7067, "realized_incremental_winner_count": 0, "sample_count": 1}], "entry_profit_pct": [{"bucket": "0.4_to_0.8", "daily_only_live_authority": false, "notional_weighted_ev_pct": -0.7067, "realized_incremental_winner_count": 0, "sample_count": 1}], "micro_vwap_side": [{"bucket": "non_negative", "daily_only_live_authority": false, "notional_weighted_ev_pct": -0.7067, "realized_incremental_winner_count": 0, "sample_count": 1}], "recovery_ai_parent_prompt_version": [{"bucket": "unreported", "daily_only_live_authority": false, "notional_weighted_ev_pct": -0.7067, "realized_incremental_winner_count": 0, "sample_count": 1}], "recovery_ai_tape_substitution": [{"bucket": "not_applied", "daily_only_live_authority": false, "notional_weighted_ev_pct": -0.7067, "realized_incremental_winner_count": 0, "sample_count": 1}], "recovery_ai_thesis_state": [{"bucket": "unreported", "daily_only_live_authority": false, "notional_weighted_ev_pct": -0.7067, "realized_incremental_winner_count": 0, "sample_count": 1}], "recovery_holding_ai_action": [{"bucket": "unreported", "daily_only_live_authority": false, "notional_weighted_ev_pct": -0.7067, "realized_incremental_winner_count": 0, "sample_count": 1}], "recovery_holding_ai_data_quality": [{"bucket": "unreported", "daily_only_live_authority": false, "notional_weighted_ev_pct": -0.7067, "realized_incremental_winner_count": 0, "sample_count": 1}], "tick_acceleration_ratio": [{"bucket": "ge_1", "daily_only_live_authority": false, "notional_weighted_ev_pct": -0.7067, "realized_incremental_winner_count": 0, "sample_count": 1}]}, "label_counts": [{"count": 1, "label": "correctly_not_expanded_or_reversal"}], "notional_weighted_ev_pct": -0.7067, "probe_confirmation_signature_metrics": [{"diagnostic_win_rate": 0.0, "realized_incremental_winner_count": 0, "sample_count": 1, "signature": "negative_group_seen"}], "realized_incremental_winner_count": 0, "source_quality_blocked_candidate_count": 0, "source_quality_valid_candidate_count": 1, "temporal_inversion_candidate_count": 0, "transient_extension_exit_timing_needed_count": 0, "venue_source_quality_blocked_closed_count": 0, "venue_source_quality_valid_closed_count": 1}
- whole_day_real_entry_lifecycle: {"by_effective_venue": [{"allowed_runtime_apply": false, "canceled_unfilled_cycle_count": 2, "closed_cycle_count": 3, "diagnostic_win_rate": 0.6667, "effective_venue": "KRX", "equal_weight_avg_profit_pct": -0.8867, "filled_cycle_count": 3, "flat_count": 0, "holding_cycle_count": 0, "loss_count": 1, "multi_leg_probe_cycle_count": 0, "realized_pnl_krw_known_count": 3, "realized_pnl_krw_known_sum": -3206, "runtime_effect": false, "single_share_plan_closed_winner_count": 2, "submitted_cycle_count": 5, "winner_count": 2}, {"allowed_runtime_apply": false, "canceled_unfilled_cycle_count": 0, "closed_cycle_count": 2, "diagnostic_win_rate": 1.0, "effective_venue": "NXT", "equal_weight_avg_profit_pct": 0.485, "filled_cycle_count": 2, "flat_count": 0, "holding_cycle_count": 0, "loss_count": 0, "multi_leg_probe_cycle_count": 1, "realized_pnl_krw_known_count": 2, "realized_pnl_krw_known_sum": 168, "runtime_effect": false, "single_share_plan_closed_winner_count": 1, "submitted_cycle_count": 2, "winner_count": 2}], "by_market_session_bucket": [{"allowed_runtime_apply": false, "canceled_unfilled_cycle_count": 2, "closed_cycle_count": 3, "diagnostic_win_rate": 0.6667, "equal_weight_avg_profit_pct": -0.8867, "filled_cycle_count": 3, "flat_count": 0, "holding_cycle_count": 0, "loss_count": 1, "market_session_bucket": "krx_regular", "multi_leg_probe_cycle_count": 0, "realized_pnl_krw_known_count": 3, "realized_pnl_krw_known_sum": -3206, "runtime_effect": false, "single_share_plan_closed_winner_count": 2, "submitted_cycle_count": 5, "winner_count": 2}, {"allowed_runtime_apply": false, "canceled_unfilled_cycle_count": 0, "closed_cycle_count": 2, "diagnostic_win_rate": 1.0, "equal_weight_avg_profit_pct": 0.485, "filled_cycle_count": 2, "flat_count": 0, "holding_cycle_count": 0, "loss_count": 0, "market_session_bucket": "nxt", "multi_leg_probe_cycle_count": 1, "realized_pnl_krw_known_count": 2, "realized_pnl_krw_known_sum": 168, "runtime_effect": false, "single_share_plan_closed_winner_count": 1, "submitted_cycle_count": 2, "winner_count": 2}], "canceled_unfilled_cycle_count": 2, "closed_cycle_count": 5, "diagnostic_win_rate": 0.8, "equal_weight_avg_profit_pct": -0.338, "filled_cycle_count": 5, "flat_count": 0, "holding_cycle_count": 0, "loss_count": 1, "multi_leg_probe_cycle_count": 1, "multi_leg_zero_residual_fill_count": 1, "pending_entry_cycle_count": 0, "realized_pnl_krw_known_count": 5, "realized_pnl_krw_known_sum": -3038, "realized_pnl_krw_missing_count": 0, "realized_pnl_krw_source_counts": [{"count": 5, "source": "broker_fill_prices_fee_aware"}], "realized_pnl_source_quality_state": "complete", "single_share_plan_closed_winner_count": 3, "submitted_cycle_count": 7, "venue_source_quality_invalid_count": 0, "venue_source_quality_valid_count": 7, "winner_count": 4}
- real_scale_in_performance: {"active_unrealized_count": 0, "avg_down_execution_count": 0, "by_outcome_cohort": {"avg_down": {"active_unrealized_count": 0, "closed_count": 0, "closed_loss_or_flat_count": 0, "closed_winner_count": 0, "equal_weight_avg_final_position_profit_pct": null, "equal_weight_avg_scale_in_leg_net_return_pct": null, "execution_count": 0, "runtime_apply_authority": false, "scale_in_leg_diagnostic_win_rate": null, "scale_in_leg_net_pnl_proxy_krw_sum": null, "source_quality_adjusted_ev_pct": null, "source_quality_blocked_closed_count": 0, "source_quality_valid_closed_count": 0}, "normal_pyramid": {"active_unrealized_count": 0, "closed_count": 0, "closed_loss_or_flat_count": 0, "closed_winner_count": 0, "equal_weight_avg_final_position_profit_pct": null, "equal_weight_avg_scale_in_leg_net_return_pct": null, "execution_count": 0, "runtime_apply_authority": false, "scale_in_leg_diagnostic_win_rate": null, "scale_in_leg_net_pnl_proxy_krw_sum": null, "source_quality_adjusted_ev_pct": null, "source_quality_blocked_closed_count": 0, "source_quality_valid_closed_count": 0}, "unknown": {"active_unrealized_count": 0, "closed_count": 0, "closed_loss_or_flat_count": 0, "closed_winner_count": 0, "equal_weight_avg_final_position_profit_pct": null, "equal_weight_avg_scale_in_leg_net_return_pct": null, "execution_count": 0, "runtime_apply_authority": false, "scale_in_leg_diagnostic_win_rate": null, "scale_in_leg_net_pnl_proxy_krw_sum": null, "source_quality_adjusted_ev_pct": null, "source_quality_blocked_closed_count": 0, "source_quality_valid_closed_count": 0}, "winner_recovery": {"active_unrealized_count": 0, "closed_count": 0, "closed_loss_or_flat_count": 0, "closed_winner_count": 0, "equal_weight_avg_final_position_profit_pct": null, "equal_weight_avg_scale_in_leg_net_return_pct": null, "execution_count": 0, "runtime_apply_authority": false, "scale_in_leg_diagnostic_win_rate": null, "scale_in_leg_net_pnl_proxy_krw_sum": null, "source_quality_adjusted_ev_pct": null, "source_quality_blocked_closed_count": 0, "source_quality_valid_closed_count": 0}}, "closed_count": 0, "completed_outcome_available": false, "equal_weight_avg_scale_in_leg_net_return_pct": null, "execution_count": 0, "normal_pyramid_execution_count": 0, "scale_in_leg_diagnostic_win_rate": null, "scale_in_leg_net_pnl_proxy_krw_sum": null, "source_quality_adjusted_ev_available": false, "source_quality_adjusted_ev_pct": null, "source_quality_adjusted_ev_unavailable_reason": "no_closed_scale_in_position", "source_quality_blocked_closed_count": 0, "source_quality_valid_closed_count": 0, "winner_expansion_vs_avg_down_asymmetry_observed": false, "winner_recovery_by_ai_parent_prompt_version": [], "winner_recovery_by_ai_thesis_state": [], "winner_recovery_by_holding_ai_action": [], "winner_recovery_by_holding_ai_data_quality": [], "winner_recovery_execution_count": 0, "winner_recovery_qty_cap_invalid_count": 0}
- pyramid_min_profit_pct: 1.1
- pyramid_threshold_source: same_day_unique_runtime_pyramid_evaluation

## Blocker Metrics

- blocker=profit_not_enough sample=5 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=rising_missed_scout_pyramid_bridge_blocked:profit_not_enough,buy_pressure_severe_below_min,micro_vwap_severe_overheated sample=1 recovered_rate=0.00 reversal_rate=1.00 blocked_then_recovered_rate=0.00

## Rows

- record_id= code=088350 name=한화생명 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.82 final=None ai=50.0 tick=0.333 micro_vwap=-20.9
- record_id= code=060250 name=NHN KCP label=pyramid_open_unresolved blocker=profit_not_enough profit=0.02 final=None ai=50.0 tick=1.75 micro_vwap=-34.8
- record_id= code=001210 name=금호전기 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.07 final=None ai=47.0 tick=1.0 micro_vwap=-18.04
- record_id= code=090430 name=아모레퍼시픽 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.3 final=None ai=50.0 tick=1.889 micro_vwap=3.44
- record_id= code=294570 name=쿠콘 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.25 final=None ai=37.0 tick=0.999 micro_vwap=23.225
- record_id=37511 code=484870 name=엠앤씨솔루션 label=pyramid_overheat_or_reversal_risk blocker=rising_missed_scout_pyramid_bridge_blocked:profit_not_enough,buy_pressure_severe_below_min,micro_vwap_severe_overheated profit=0.69 final=0.21 ai=63.0 tick=1.0 micro_vwap=43.05

## Real Scale-In Performance Rows


## One Share Opportunity Rows

- record_id=37511 code=484870 name=엠앤씨솔루션 label=pyramid_correctly_blocked canonical=expansion_correctly_not_expanded_no_confirmation opportunity_seen=False opportunity_profit=None max_profit=0.69 opportunity_cost=0.69 final=0.21 residual_zero_fill=True residual_soft_abort=True residual_missed_candidate=False post_probe_real_outcome=profitable_zero_fill_no_confirmation confirmation_ready=False runtime_confirmation_ready=False confirmation_alignment=not_runtime_confirmed recovery_evaluation_seen=False recovery_confirmation_ready=False confirmation_source_quality_blockers=- first_leg_qty=None first_leg_profit_proxy_krw=None

## Whole-Day Real Entry Lifecycle Rows

- record_id=36974 code=001820 name=삼화콘덴서 venue=KRX session=krx_regular state=closed planned_qty=1 submitted_qty=1 filled_qty=1 final=0.73 realized_pnl_krw=834 realized_pnl_source=broker_fill_prices_fee_aware canonical=None
- record_id=37040 code=003350 name=한국화장품제조 venue=KRX session=krx_regular state=closed planned_qty=1 submitted_qty=1 filled_qty=1 final=0.12 realized_pnl_krw=17 realized_pnl_source=broker_fill_prices_fee_aware canonical=None
- record_id=37095 code=001820 name=삼화콘덴서 venue=KRX session=krx_regular state=closed planned_qty=1 submitted_qty=1 filled_qty=1 final=-3.51 realized_pnl_krw=-4057 realized_pnl_source=broker_fill_prices_fee_aware canonical=None
- record_id=37005 code=060250 name=NHN KCP venue=KRX session=krx_regular state=canceled_unfilled planned_qty=1 submitted_qty=1 filled_qty=0 final=None realized_pnl_krw=None realized_pnl_source=None canonical=None
- record_id=37186 code=103140 name=풍산 venue=KRX session=krx_regular state=canceled_unfilled planned_qty=1 submitted_qty=1 filled_qty=0 final=None realized_pnl_krw=None realized_pnl_source=None canonical=None
- record_id=37421 code=484870 name=엠앤씨솔루션 venue=NXT session=nxt state=closed planned_qty=1 submitted_qty=1 filled_qty=1 final=0.76 realized_pnl_krw=130 realized_pnl_source=broker_fill_prices_fee_aware canonical=None
- record_id=37511 code=484870 name=엠앤씨솔루션 venue=NXT session=nxt state=closed planned_qty=6 submitted_qty=1 filled_qty=1 final=0.21 realized_pnl_krw=38 realized_pnl_source=broker_fill_prices_fee_aware canonical=expansion_correctly_not_expanded_no_confirmation

## Normal Winner Expansion Rows

- record_id=37511 code=484870 name=엠앤씨솔루션 label=correctly_not_expanded_or_reversal entry_profit=0.69 incremental_mfe=-0.23 incremental_final=-0.7067 confirmation=negative_group_seen
