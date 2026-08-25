# 2026-08-25 Scalping Pyramid Intraday Feedback

- generated_at: 2026-08-25T20:18:35+09:00
- decision_authority: source_only_pyramid_intraday_feedback_no_runtime_mutation
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: intraday_threshold_mutation, intraday_runtime_apply, hard_safety_relaxation, broker_guard_bypass, order_guard_relaxation, stale_quote_bypass, cooldown_bypass, quantity_guard_relaxation, position_cap_release, provider_route_change, bot_restart, real_execution_quality_approval

## Summary

- pyramid_feedback_row_count: 4
- closed_pyramid_row_count: 1
- pyramid_would_have_helped_count: 0
- pyramid_correctly_blocked_count: 0
- pyramid_overheat_or_reversal_risk_count: 1
- pyramid_open_unresolved_count: 3
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
- whole_day_real_entry_lifecycle: {"by_effective_venue": [{"allowed_runtime_apply": false, "canceled_unfilled_cycle_count": 6, "closed_cycle_count": 8, "diagnostic_win_rate": 0.875, "effective_venue": "KRX", "equal_weight_avg_profit_pct": 0.53, "filled_cycle_count": 9, "flat_count": 0, "holding_cycle_count": 1, "loss_count": 1, "multi_leg_probe_cycle_count": 0, "realized_pnl_krw_known_count": 8, "realized_pnl_krw_known_sum": 1777, "runtime_effect": false, "single_share_plan_closed_winner_count": 7, "submitted_cycle_count": 15, "winner_count": 7}], "by_market_session_bucket": [{"allowed_runtime_apply": false, "canceled_unfilled_cycle_count": 6, "closed_cycle_count": 8, "diagnostic_win_rate": 0.875, "equal_weight_avg_profit_pct": 0.53, "filled_cycle_count": 9, "flat_count": 0, "holding_cycle_count": 1, "loss_count": 1, "market_session_bucket": "krx_regular", "multi_leg_probe_cycle_count": 0, "realized_pnl_krw_known_count": 8, "realized_pnl_krw_known_sum": 1777, "runtime_effect": false, "single_share_plan_closed_winner_count": 7, "submitted_cycle_count": 15, "winner_count": 7}], "canceled_unfilled_cycle_count": 6, "closed_cycle_count": 8, "diagnostic_win_rate": 0.875, "equal_weight_avg_profit_pct": 0.53, "filled_cycle_count": 9, "flat_count": 0, "holding_cycle_count": 1, "loss_count": 1, "multi_leg_probe_cycle_count": 0, "multi_leg_zero_residual_fill_count": 0, "pending_entry_cycle_count": 0, "realized_pnl_krw_known_count": 8, "realized_pnl_krw_known_sum": 1777, "realized_pnl_krw_missing_count": 0, "realized_pnl_krw_source_counts": [{"count": 7, "source": "broker_fill_prices_fee_aware"}, {"count": 1, "source": "sell_completed_event"}], "realized_pnl_source_quality_state": "complete", "single_share_plan_closed_winner_count": 7, "submitted_cycle_count": 15, "venue_source_quality_invalid_count": 0, "venue_source_quality_valid_count": 15, "winner_count": 7}
- real_scale_in_performance: {"active_unrealized_count": 0, "avg_down_execution_count": 0, "by_outcome_cohort": {"avg_down": {"active_unrealized_count": 0, "closed_count": 0, "closed_loss_or_flat_count": 0, "closed_winner_count": 0, "equal_weight_avg_final_position_profit_pct": null, "equal_weight_avg_scale_in_leg_net_return_pct": null, "execution_count": 0, "runtime_apply_authority": false, "scale_in_leg_diagnostic_win_rate": null, "scale_in_leg_net_pnl_proxy_krw_sum": null, "source_quality_adjusted_ev_pct": null, "source_quality_blocked_closed_count": 0, "source_quality_valid_closed_count": 0}, "normal_pyramid": {"active_unrealized_count": 0, "closed_count": 0, "closed_loss_or_flat_count": 0, "closed_winner_count": 0, "equal_weight_avg_final_position_profit_pct": null, "equal_weight_avg_scale_in_leg_net_return_pct": null, "execution_count": 0, "runtime_apply_authority": false, "scale_in_leg_diagnostic_win_rate": null, "scale_in_leg_net_pnl_proxy_krw_sum": null, "source_quality_adjusted_ev_pct": null, "source_quality_blocked_closed_count": 0, "source_quality_valid_closed_count": 0}, "unknown": {"active_unrealized_count": 0, "closed_count": 0, "closed_loss_or_flat_count": 0, "closed_winner_count": 0, "equal_weight_avg_final_position_profit_pct": null, "equal_weight_avg_scale_in_leg_net_return_pct": null, "execution_count": 0, "runtime_apply_authority": false, "scale_in_leg_diagnostic_win_rate": null, "scale_in_leg_net_pnl_proxy_krw_sum": null, "source_quality_adjusted_ev_pct": null, "source_quality_blocked_closed_count": 0, "source_quality_valid_closed_count": 0}, "winner_recovery": {"active_unrealized_count": 0, "closed_count": 0, "closed_loss_or_flat_count": 0, "closed_winner_count": 0, "equal_weight_avg_final_position_profit_pct": null, "equal_weight_avg_scale_in_leg_net_return_pct": null, "execution_count": 0, "runtime_apply_authority": false, "scale_in_leg_diagnostic_win_rate": null, "scale_in_leg_net_pnl_proxy_krw_sum": null, "source_quality_adjusted_ev_pct": null, "source_quality_blocked_closed_count": 0, "source_quality_valid_closed_count": 0}}, "closed_count": 0, "completed_outcome_available": false, "equal_weight_avg_scale_in_leg_net_return_pct": null, "execution_count": 0, "normal_pyramid_execution_count": 0, "scale_in_leg_diagnostic_win_rate": null, "scale_in_leg_net_pnl_proxy_krw_sum": null, "source_quality_adjusted_ev_available": false, "source_quality_adjusted_ev_pct": null, "source_quality_adjusted_ev_unavailable_reason": "no_closed_scale_in_position", "source_quality_blocked_closed_count": 0, "source_quality_valid_closed_count": 0, "winner_expansion_vs_avg_down_asymmetry_observed": false, "winner_recovery_by_ai_parent_prompt_version": [], "winner_recovery_by_ai_thesis_state": [], "winner_recovery_by_holding_ai_action": [], "winner_recovery_by_holding_ai_data_quality": [], "winner_recovery_execution_count": 0, "winner_recovery_qty_cap_invalid_count": 0}
- pyramid_min_profit_pct: 1.1
- pyramid_threshold_source: same_day_unique_runtime_pyramid_evaluation

## Blocker Metrics

- blocker=profit_not_enough sample=3 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=rising_missed_scout_pyramid_bridge_blocked:buy_pressure_severe_below_min,large_sell_detected sample=1 recovered_rate=0.00 reversal_rate=1.00 blocked_then_recovered_rate=0.00

## Rows

- record_id= code=055550 name=신한지주 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.05 final=None ai=50.0 tick=0.4 micro_vwap=19.85
- record_id=35391 code=059090 name=미코 label=pyramid_overheat_or_reversal_risk blocker=rising_missed_scout_pyramid_bridge_blocked:buy_pressure_severe_below_min,large_sell_detected profit=0.84 final=0.41 ai=54.0 tick=14.0 micro_vwap=33.52
- record_id= code=009520 name=포스코엠텍 label=pyramid_open_unresolved blocker=profit_not_enough profit=-0.0 final=None ai=54.0 tick=0.0 micro_vwap=0.0
- record_id= code=052690 name=한전기술 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.23 final=None ai=50.0 tick=1.0 micro_vwap=11.51

## Real Scale-In Performance Rows


## One Share Opportunity Rows


## Whole-Day Real Entry Lifecycle Rows

- record_id=35317 code=356860 name=티엘비 venue=KRX session=krx_regular state=closed planned_qty=1 submitted_qty=1 filled_qty=1 final=0.92 realized_pnl_krw=319 realized_pnl_source=broker_fill_prices_fee_aware canonical=None
- record_id=35224 code=000720 name=현대건설 venue=KRX session=krx_regular state=closed planned_qty=1 submitted_qty=1 filled_qty=1 final=-0.23 realized_pnl_krw=-264 realized_pnl_source=broker_fill_prices_fee_aware canonical=None
- record_id=35378 code=036930 name=주성엔지니어링 venue=KRX session=krx_regular state=canceled_unfilled planned_qty=1 submitted_qty=1 filled_qty=0 final=None realized_pnl_krw=None realized_pnl_source=None canonical=None
- record_id=35355 code=000720 name=현대건설 venue=KRX session=krx_regular state=closed planned_qty=1 submitted_qty=1 filled_qty=1 final=0.2 realized_pnl_krw=232 realized_pnl_source=broker_fill_prices_fee_aware canonical=None
- record_id=35225 code=052690 name=한전기술 venue=KRX session=krx_regular state=closed planned_qty=1 submitted_qty=1 filled_qty=1 final=1.07 realized_pnl_krw=1067 realized_pnl_source=broker_fill_prices_fee_aware canonical=None
- record_id=35391 code=059090 name=미코 venue=KRX session=krx_regular state=closed planned_qty=1 submitted_qty=1 filled_qty=1 final=0.41 realized_pnl_krw=77 realized_pnl_source=broker_fill_prices_fee_aware canonical=None
- record_id=35211 code=005380 name=현대차 venue=KRX session=krx_regular state=canceled_unfilled planned_qty=1 submitted_qty=1 filled_qty=0 final=None realized_pnl_krw=None realized_pnl_source=None canonical=None
- record_id=35447 code=000720 name=현대건설 venue=KRX session=krx_regular state=canceled_unfilled planned_qty=1 submitted_qty=1 filled_qty=0 final=None realized_pnl_krw=None realized_pnl_source=None canonical=None
- record_id=35321 code=003350 name=한국화장품제조 venue=KRX session=krx_regular state=canceled_unfilled planned_qty=1 submitted_qty=1 filled_qty=0 final=None realized_pnl_krw=None realized_pnl_source=None canonical=None
- record_id=35399 code=080580 name=오킨스전자 venue=KRX session=krx_regular state=closed planned_qty=1 submitted_qty=1 filled_qty=1 final=1.04 realized_pnl_krw=196 realized_pnl_source=broker_fill_prices_fee_aware canonical=None
- record_id=35596 code=080580 name=오킨스전자 venue=KRX session=krx_regular state=closed planned_qty=1 submitted_qty=1 filled_qty=1 final=0.61 realized_pnl_krw=116 realized_pnl_source=broker_fill_prices_fee_aware canonical=None
- record_id=35337 code=356860 name=티엘비 venue=KRX session=krx_regular state=canceled_unfilled planned_qty=1 submitted_qty=1 filled_qty=0 final=None realized_pnl_krw=None realized_pnl_source=None canonical=None
- record_id=35220 code=484810 name=티엑스알로보틱스 venue=KRX session=krx_regular state=closed planned_qty=1 submitted_qty=1 filled_qty=1 final=0.22 realized_pnl_krw=34 realized_pnl_source=sell_completed_event canonical=None
- record_id=35388 code=035420 name=NAVER venue=KRX session=krx_regular state=canceled_unfilled planned_qty=1 submitted_qty=1 filled_qty=0 final=None realized_pnl_krw=None realized_pnl_source=None canonical=None
- record_id=35556 code=225570 name=넥슨게임즈 venue=KRX session=krx_regular state=holding planned_qty=1 submitted_qty=1 filled_qty=1 final=None realized_pnl_krw=None realized_pnl_source=None canonical=None

## Normal Winner Expansion Rows
