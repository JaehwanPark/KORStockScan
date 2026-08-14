# 2026-08-14 Scalping Pyramid Intraday Feedback

- generated_at: 2026-08-14T16:45:02+09:00
- decision_authority: source_only_pyramid_intraday_feedback_no_runtime_mutation
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: intraday_threshold_mutation, intraday_runtime_apply, hard_safety_relaxation, broker_guard_bypass, order_guard_relaxation, stale_quote_bypass, cooldown_bypass, quantity_guard_relaxation, position_cap_release, provider_route_change, bot_restart, real_execution_quality_approval

## Summary

- pyramid_feedback_row_count: 6
- closed_pyramid_row_count: 4
- pyramid_would_have_helped_count: 1
- pyramid_correctly_blocked_count: 0
- pyramid_overheat_or_reversal_risk_count: 3
- pyramid_open_unresolved_count: 2
- one_share_event_count: 1
- one_share_closed_count: 1
- one_share_pyramid_opportunity_count: 0
- one_share_pyramid_missed_upside_count: 0
- one_share_pyramid_missed_upside_rate: 0.00
- one_share_pyramid_avg_opportunity_cost_pct: 0.00
- probe_residual_zero_fill_count: 1
- probe_residual_soft_abort_count: 0
- probe_residual_missed_upside_candidate_count: 0
- probe_residual_pyramid_threshold_missed_upside_candidate_count: 0
- probe_residual_real_outcome_closed_count: 1
- probe_residual_realized_winner_zero_fill_count: 0
- probe_residual_realized_loss_or_flat_zero_fill_count: 1
- probe_residual_realized_winner_confirmation_ready_count: 0
- probe_residual_realized_loss_or_flat_confirmation_ready_count: 0
- post_hard_abort_recovery_evaluation_seen_count: 1
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
- whole_day_real_entry_lifecycle: {"by_effective_venue": [{"allowed_runtime_apply": false, "canceled_unfilled_cycle_count": 3, "closed_cycle_count": 5, "diagnostic_win_rate": 0.8, "effective_venue": "KRX", "equal_weight_avg_profit_pct": 0.008, "filled_cycle_count": 6, "flat_count": 0, "holding_cycle_count": 1, "loss_count": 1, "multi_leg_probe_cycle_count": 1, "realized_pnl_krw_known_count": 5, "realized_pnl_krw_known_sum": 135, "runtime_effect": false, "single_share_plan_closed_winner_count": 4, "submitted_cycle_count": 10, "winner_count": 4}], "by_market_session_bucket": [{"allowed_runtime_apply": false, "canceled_unfilled_cycle_count": 3, "closed_cycle_count": 5, "diagnostic_win_rate": 0.8, "equal_weight_avg_profit_pct": 0.008, "filled_cycle_count": 6, "flat_count": 0, "holding_cycle_count": 1, "loss_count": 1, "market_session_bucket": "krx_regular", "multi_leg_probe_cycle_count": 1, "realized_pnl_krw_known_count": 5, "realized_pnl_krw_known_sum": 135, "runtime_effect": false, "single_share_plan_closed_winner_count": 4, "submitted_cycle_count": 10, "winner_count": 4}], "canceled_unfilled_cycle_count": 3, "closed_cycle_count": 5, "diagnostic_win_rate": 0.8, "equal_weight_avg_profit_pct": 0.008, "filled_cycle_count": 6, "flat_count": 0, "holding_cycle_count": 1, "loss_count": 1, "multi_leg_probe_cycle_count": 1, "multi_leg_zero_residual_fill_count": 1, "pending_entry_cycle_count": 1, "realized_pnl_krw_known_count": 5, "realized_pnl_krw_known_sum": 135, "realized_pnl_krw_missing_count": 0, "realized_pnl_krw_source_counts": [{"count": 1, "source": "broker_fill_prices_fee_aware"}, {"count": 4, "source": "reconstructed_same_cycle_full_close_fee_aware"}], "realized_pnl_source_quality_state": "complete", "single_share_plan_closed_winner_count": 4, "submitted_cycle_count": 10, "venue_source_quality_invalid_count": 0, "venue_source_quality_valid_count": 10, "winner_count": 4}
- real_scale_in_performance: {"active_unrealized_count": 0, "avg_down_execution_count": 0, "by_outcome_cohort": {"avg_down": {"active_unrealized_count": 0, "closed_count": 0, "closed_loss_or_flat_count": 0, "closed_winner_count": 0, "equal_weight_avg_final_position_profit_pct": null, "execution_count": 0, "runtime_apply_authority": false}, "normal_pyramid": {"active_unrealized_count": 0, "closed_count": 0, "closed_loss_or_flat_count": 0, "closed_winner_count": 0, "equal_weight_avg_final_position_profit_pct": null, "execution_count": 0, "runtime_apply_authority": false}, "unknown": {"active_unrealized_count": 0, "closed_count": 0, "closed_loss_or_flat_count": 0, "closed_winner_count": 0, "equal_weight_avg_final_position_profit_pct": null, "execution_count": 0, "runtime_apply_authority": false}, "winner_recovery": {"active_unrealized_count": 0, "closed_count": 0, "closed_loss_or_flat_count": 0, "closed_winner_count": 0, "equal_weight_avg_final_position_profit_pct": null, "execution_count": 0, "runtime_apply_authority": false}}, "closed_count": 0, "completed_outcome_available": false, "execution_count": 0, "normal_pyramid_execution_count": 0, "source_quality_adjusted_ev_available": false, "source_quality_adjusted_ev_unavailable_reason": "no_closed_scale_in_position", "winner_expansion_vs_avg_down_asymmetry_observed": false, "winner_recovery_execution_count": 0, "winner_recovery_qty_cap_invalid_count": 0}
- pyramid_min_profit_pct: 1.1
- pyramid_threshold_source: same_day_unique_runtime_pyramid_evaluation

## Blocker Metrics

- blocker=profit_not_enough sample=3 recovered_rate=0.00 reversal_rate=0.33 blocked_then_recovered_rate=0.00
- blocker=pyramid_hard_blocked:micro_vwap_severe_overheated,fresh_micro_confirmation_missing sample=1 recovered_rate=1.00 reversal_rate=0.00 blocked_then_recovered_rate=1.00
- blocker=rising_missed_scout_pyramid_bridge_blocked:fresh_micro_confirmation_missing,micro_vwap_severe_overheated sample=1 recovered_rate=0.00 reversal_rate=1.00 blocked_then_recovered_rate=0.00
- blocker=rising_missed_scout_pyramid_bridge_blocked:profit_not_enough sample=1 recovered_rate=0.00 reversal_rate=1.00 blocked_then_recovered_rate=0.00

## Rows

- record_id= code=108490 name=로보티즈 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.33 final=None ai=44.0 tick=1.5 micro_vwap=-41.92
- record_id=31397 code=093370 name=후성 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=0.26 final=-0.15 ai=54.0 tick=2.0 micro_vwap=-41.83
- record_id=32002 code=125490 name=한라캐스트 label=pyramid_overheat_or_reversal_risk blocker=rising_missed_scout_pyramid_bridge_blocked:profit_not_enough profit=0.31 final=0.23 ai=59.0 tick=2.0 micro_vwap=68.15
- record_id=32227 code=125490 name=한라캐스트 label=pyramid_would_have_helped blocker=pyramid_hard_blocked:micro_vwap_severe_overheated,fresh_micro_confirmation_missing profit=1.7 final=1.86 ai=72.0 tick=1.0 micro_vwap=81.97
- record_id=32279 code=125490 name=한라캐스트 label=pyramid_overheat_or_reversal_risk blocker=rising_missed_scout_pyramid_bridge_blocked:fresh_micro_confirmation_missing,micro_vwap_severe_overheated profit=0.83 final=0.3 ai=50.0 tick=0.0 micro_vwap=108.65
- record_id=32310 code=036930 name=주성엔지니어링 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.31 final=None ai=58.0 tick=3.0 micro_vwap=-3.32

## Real Scale-In Performance Rows


## One Share Opportunity Rows

- record_id=32053 code=317400 name=자이에스앤디 label=pyramid_correctly_blocked canonical=expansion_correctly_not_expanded opportunity_seen=False opportunity_profit=None max_profit=0.16 opportunity_cost=0.16 final=-3.22 residual_zero_fill=True residual_soft_abort=False residual_missed_candidate=False post_probe_real_outcome=loss_or_flat_zero_fill_no_confirmation confirmation_ready=False runtime_confirmation_ready=False confirmation_alignment=not_runtime_confirmed recovery_evaluation_seen=True recovery_confirmation_ready=False confirmation_source_quality_blockers=- first_leg_qty=None first_leg_profit_proxy_krw=None

## Whole-Day Real Entry Lifecycle Rows

- record_id=32002 code=125490 name=한라캐스트 venue=KRX session=krx_regular state=closed planned_qty=1 submitted_qty=1 filled_qty=1 final=0.23 realized_pnl_krw=30 realized_pnl_source=reconstructed_same_cycle_full_close_fee_aware canonical=None
- record_id=32138 code=004370 name=농심 venue=KRX session=krx_regular state=canceled_unfilled planned_qty=1 submitted_qty=1 filled_qty=0 final=None realized_pnl_krw=None realized_pnl_source=None canonical=None
- record_id=32227 code=125490 name=한라캐스트 venue=KRX session=krx_regular state=closed planned_qty=1 submitted_qty=1 filled_qty=1 final=1.86 realized_pnl_krw=240 realized_pnl_source=reconstructed_same_cycle_full_close_fee_aware canonical=None
- record_id=32279 code=125490 name=한라캐스트 venue=KRX session=krx_regular state=closed planned_qty=1 submitted_qty=1 filled_qty=1 final=0.3 realized_pnl_krw=40 realized_pnl_source=reconstructed_same_cycle_full_close_fee_aware canonical=None
- record_id=31943 code=475560 name=더본코리아 venue=KRX session=krx_regular state=canceled_unfilled planned_qty=1 submitted_qty=1 filled_qty=0 final=None realized_pnl_krw=None realized_pnl_source=None canonical=None
- record_id=32053 code=317400 name=자이에스앤디 venue=KRX session=krx_regular state=closed planned_qty=3 submitted_qty=1 filled_qty=1 final=-3.22 realized_pnl_krw=-333 realized_pnl_source=reconstructed_same_cycle_full_close_fee_aware canonical=expansion_correctly_not_expanded
- record_id=32310 code=036930 name=주성엔지니어링 venue=KRX session=krx_regular state=pending_entry planned_qty=1 submitted_qty=1 filled_qty=0 final=None realized_pnl_krw=None realized_pnl_source=None canonical=None
- record_id=32285 code=125490 name=한라캐스트 venue=KRX session=krx_regular state=canceled_unfilled planned_qty=1 submitted_qty=1 filled_qty=0 final=None realized_pnl_krw=None realized_pnl_source=None canonical=None
- record_id=32034 code=487400 name=케이앤에스아이앤씨 venue=KRX session=krx_regular state=holding planned_qty=1 submitted_qty=1 filled_qty=1 final=None realized_pnl_krw=None realized_pnl_source=None canonical=None
- record_id=32292 code=019210 name=와이지-원 venue=KRX session=krx_regular state=closed planned_qty=1 submitted_qty=1 filled_qty=1 final=0.87 realized_pnl_krw=158 realized_pnl_source=broker_fill_prices_fee_aware canonical=None

## Normal Winner Expansion Rows
