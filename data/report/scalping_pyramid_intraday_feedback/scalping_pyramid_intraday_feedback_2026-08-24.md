# 2026-08-24 Scalping Pyramid Intraday Feedback

- generated_at: 2026-08-24T20:18:14+09:00
- decision_authority: source_only_pyramid_intraday_feedback_no_runtime_mutation
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: intraday_threshold_mutation, intraday_runtime_apply, hard_safety_relaxation, broker_guard_bypass, order_guard_relaxation, stale_quote_bypass, cooldown_bypass, quantity_guard_relaxation, position_cap_release, provider_route_change, bot_restart, real_execution_quality_approval

## Summary

- pyramid_feedback_row_count: 4
- closed_pyramid_row_count: 2
- pyramid_would_have_helped_count: 0
- pyramid_correctly_blocked_count: 1
- pyramid_overheat_or_reversal_risk_count: 1
- pyramid_open_unresolved_count: 2
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
- whole_day_real_entry_lifecycle: {"by_effective_venue": [{"allowed_runtime_apply": false, "canceled_unfilled_cycle_count": 2, "closed_cycle_count": 8, "diagnostic_win_rate": 0.625, "effective_venue": "KRX", "equal_weight_avg_profit_pct": -0.64, "filled_cycle_count": 9, "flat_count": 0, "holding_cycle_count": 1, "loss_count": 3, "multi_leg_probe_cycle_count": 0, "realized_pnl_krw_known_count": 8, "realized_pnl_krw_known_sum": -3639, "runtime_effect": false, "single_share_plan_closed_winner_count": 5, "submitted_cycle_count": 11, "winner_count": 5}, {"allowed_runtime_apply": false, "canceled_unfilled_cycle_count": 1, "closed_cycle_count": 0, "diagnostic_win_rate": 0.0, "effective_venue": "PREMARKET_KRX_LIKE", "equal_weight_avg_profit_pct": 0.0, "filled_cycle_count": 0, "flat_count": 0, "holding_cycle_count": 0, "loss_count": 0, "multi_leg_probe_cycle_count": 0, "realized_pnl_krw_known_count": 0, "realized_pnl_krw_known_sum": 0, "runtime_effect": false, "single_share_plan_closed_winner_count": 0, "submitted_cycle_count": 1, "winner_count": 0}], "by_market_session_bucket": [{"allowed_runtime_apply": false, "canceled_unfilled_cycle_count": 1, "closed_cycle_count": 0, "diagnostic_win_rate": 0.0, "equal_weight_avg_profit_pct": 0.0, "filled_cycle_count": 0, "flat_count": 0, "holding_cycle_count": 0, "loss_count": 0, "market_session_bucket": "krx_like_premarket", "multi_leg_probe_cycle_count": 0, "realized_pnl_krw_known_count": 0, "realized_pnl_krw_known_sum": 0, "runtime_effect": false, "single_share_plan_closed_winner_count": 0, "submitted_cycle_count": 1, "winner_count": 0}, {"allowed_runtime_apply": false, "canceled_unfilled_cycle_count": 2, "closed_cycle_count": 8, "diagnostic_win_rate": 0.625, "equal_weight_avg_profit_pct": -0.64, "filled_cycle_count": 9, "flat_count": 0, "holding_cycle_count": 1, "loss_count": 3, "market_session_bucket": "krx_regular", "multi_leg_probe_cycle_count": 0, "realized_pnl_krw_known_count": 8, "realized_pnl_krw_known_sum": -3639, "runtime_effect": false, "single_share_plan_closed_winner_count": 5, "submitted_cycle_count": 11, "winner_count": 5}], "canceled_unfilled_cycle_count": 3, "closed_cycle_count": 8, "diagnostic_win_rate": 0.625, "equal_weight_avg_profit_pct": -0.64, "filled_cycle_count": 9, "flat_count": 0, "holding_cycle_count": 1, "loss_count": 3, "multi_leg_probe_cycle_count": 0, "multi_leg_zero_residual_fill_count": 0, "pending_entry_cycle_count": 0, "realized_pnl_krw_known_count": 8, "realized_pnl_krw_known_sum": -3639, "realized_pnl_krw_missing_count": 0, "realized_pnl_krw_source_counts": [{"count": 5, "source": "broker_fill_prices_fee_aware"}, {"count": 1, "source": "reconciled_same_cycle_broker_fill_prices_fee_aware"}, {"count": 2, "source": "sell_completed_event"}], "realized_pnl_source_quality_state": "complete", "single_share_plan_closed_winner_count": 5, "submitted_cycle_count": 12, "venue_source_quality_invalid_count": 0, "venue_source_quality_valid_count": 12, "winner_count": 5}
- real_scale_in_performance: {"active_unrealized_count": 0, "avg_down_execution_count": 0, "by_outcome_cohort": {"avg_down": {"active_unrealized_count": 0, "closed_count": 0, "closed_loss_or_flat_count": 0, "closed_winner_count": 0, "equal_weight_avg_final_position_profit_pct": null, "equal_weight_avg_scale_in_leg_net_return_pct": null, "execution_count": 0, "runtime_apply_authority": false, "scale_in_leg_diagnostic_win_rate": null, "scale_in_leg_net_pnl_proxy_krw_sum": null, "source_quality_adjusted_ev_pct": null, "source_quality_blocked_closed_count": 0, "source_quality_valid_closed_count": 0}, "normal_pyramid": {"active_unrealized_count": 0, "closed_count": 0, "closed_loss_or_flat_count": 0, "closed_winner_count": 0, "equal_weight_avg_final_position_profit_pct": null, "equal_weight_avg_scale_in_leg_net_return_pct": null, "execution_count": 0, "runtime_apply_authority": false, "scale_in_leg_diagnostic_win_rate": null, "scale_in_leg_net_pnl_proxy_krw_sum": null, "source_quality_adjusted_ev_pct": null, "source_quality_blocked_closed_count": 0, "source_quality_valid_closed_count": 0}, "unknown": {"active_unrealized_count": 0, "closed_count": 0, "closed_loss_or_flat_count": 0, "closed_winner_count": 0, "equal_weight_avg_final_position_profit_pct": null, "equal_weight_avg_scale_in_leg_net_return_pct": null, "execution_count": 0, "runtime_apply_authority": false, "scale_in_leg_diagnostic_win_rate": null, "scale_in_leg_net_pnl_proxy_krw_sum": null, "source_quality_adjusted_ev_pct": null, "source_quality_blocked_closed_count": 0, "source_quality_valid_closed_count": 0}, "winner_recovery": {"active_unrealized_count": 0, "closed_count": 0, "closed_loss_or_flat_count": 0, "closed_winner_count": 0, "equal_weight_avg_final_position_profit_pct": null, "equal_weight_avg_scale_in_leg_net_return_pct": null, "execution_count": 0, "runtime_apply_authority": false, "scale_in_leg_diagnostic_win_rate": null, "scale_in_leg_net_pnl_proxy_krw_sum": null, "source_quality_adjusted_ev_pct": null, "source_quality_blocked_closed_count": 0, "source_quality_valid_closed_count": 0}}, "closed_count": 0, "completed_outcome_available": false, "equal_weight_avg_scale_in_leg_net_return_pct": null, "execution_count": 0, "normal_pyramid_execution_count": 0, "scale_in_leg_diagnostic_win_rate": null, "scale_in_leg_net_pnl_proxy_krw_sum": null, "source_quality_adjusted_ev_available": false, "source_quality_adjusted_ev_pct": null, "source_quality_adjusted_ev_unavailable_reason": "no_closed_scale_in_position", "source_quality_blocked_closed_count": 0, "source_quality_valid_closed_count": 0, "winner_expansion_vs_avg_down_asymmetry_observed": false, "winner_recovery_by_ai_parent_prompt_version": [], "winner_recovery_by_ai_thesis_state": [], "winner_recovery_by_holding_ai_action": [], "winner_recovery_by_holding_ai_data_quality": [], "winner_recovery_execution_count": 0, "winner_recovery_qty_cap_invalid_count": 0}
- pyramid_min_profit_pct: 1.1
- pyramid_threshold_source: same_day_unique_runtime_pyramid_evaluation

## Blocker Metrics

- blocker=profit_not_enough sample=4 recovered_rate=0.00 reversal_rate=0.25 blocked_then_recovered_rate=0.00

## Rows

- record_id= code=161890 name=한국콜마 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.34 final=None ai=50.0 tick=2.0 micro_vwap=-34.81
- record_id=34639 code=003350 name=한국화장품제조 label=pyramid_correctly_blocked blocker=profit_not_enough profit=0.03 final=0.37 ai=48.0 tick=1.0 micro_vwap=100.4
- record_id= code=267270 name=HD건설기계 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.99 final=None ai=53.0 tick=0.0 micro_vwap=19.7
- record_id=34960 code=249420 name=일동제약 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=0.16 final=-0.1 ai=45.0 tick=0.0 micro_vwap=0.0

## Real Scale-In Performance Rows


## One Share Opportunity Rows


## Whole-Day Real Entry Lifecycle Rows

- record_id=34521 code=302440 name=SK바이오사이언스 venue=PREMARKET_KRX_LIKE session=krx_like_premarket state=canceled_unfilled planned_qty=1 submitted_qty=1 filled_qty=0 final=None realized_pnl_krw=None realized_pnl_source=None canonical=None
- record_id=34620 code=003530 name=한화투자증권 venue=KRX session=krx_regular state=closed planned_qty=1 submitted_qty=1 filled_qty=1 final=0.36 realized_pnl_krw=18 realized_pnl_source=reconciled_same_cycle_broker_fill_prices_fee_aware canonical=None
- record_id=34639 code=003350 name=한국화장품제조 venue=KRX session=krx_regular state=closed planned_qty=1 submitted_qty=1 filled_qty=1 final=0.37 realized_pnl_krw=43 realized_pnl_source=broker_fill_prices_fee_aware canonical=None
- record_id=34691 code=084370 name=유진테크 venue=KRX session=krx_regular state=canceled_unfilled planned_qty=1 submitted_qty=1 filled_qty=0 final=None realized_pnl_krw=None realized_pnl_source=None canonical=None
- record_id=34843 code=237690 name=에스티팜 venue=KRX session=krx_regular state=closed planned_qty=1 submitted_qty=1 filled_qty=1 final=0.33 realized_pnl_krw=351 realized_pnl_source=broker_fill_prices_fee_aware canonical=None
- record_id=34524 code=249420 name=일동제약 venue=KRX session=krx_regular state=closed planned_qty=1 submitted_qty=1 filled_qty=1 final=0.29 realized_pnl_krw=44 realized_pnl_source=broker_fill_prices_fee_aware canonical=None
- record_id=34702 code=003350 name=한국화장품제조 venue=KRX session=krx_regular state=canceled_unfilled planned_qty=1 submitted_qty=1 filled_qty=0 final=None realized_pnl_krw=None realized_pnl_source=None canonical=None
- record_id=34702 code=003350 name=한국화장품제조 venue=KRX session=krx_regular state=closed planned_qty=1 submitted_qty=1 filled_qty=1 final=0.71 realized_pnl_krw=83 realized_pnl_source=broker_fill_prices_fee_aware canonical=None
- record_id=34960 code=249420 name=일동제약 venue=KRX session=krx_regular state=closed planned_qty=1 submitted_qty=1 filled_qty=1 final=-0.1 realized_pnl_krw=-15 realized_pnl_source=sell_completed_event canonical=None
- record_id=34662 code=091580 name=상신이디피 venue=KRX session=krx_regular state=holding planned_qty=1 submitted_qty=1 filled_qty=1 final=None realized_pnl_krw=None realized_pnl_source=None canonical=None
- record_id=34609 code=950260 name=인제니아테라퓨틱스(Reg.S) venue=KRX session=krx_regular state=closed planned_qty=1 submitted_qty=1 filled_qty=1 final=-3.89 realized_pnl_krw=-615 realized_pnl_source=broker_fill_prices_fee_aware canonical=None
- record_id=34973 code=237690 name=에스티팜 venue=KRX session=krx_regular state=closed planned_qty=1 submitted_qty=1 filled_qty=1 final=-3.19 realized_pnl_krw=-3548 realized_pnl_source=sell_completed_event canonical=None

## Normal Winner Expansion Rows
