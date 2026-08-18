# 2026-08-18 Scalping Pyramid Intraday Feedback

- generated_at: 2026-08-18T20:19:32+09:00
- decision_authority: source_only_pyramid_intraday_feedback_no_runtime_mutation
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: intraday_threshold_mutation, intraday_runtime_apply, hard_safety_relaxation, broker_guard_bypass, order_guard_relaxation, stale_quote_bypass, cooldown_bypass, quantity_guard_relaxation, position_cap_release, provider_route_change, bot_restart, real_execution_quality_approval

## Summary

- pyramid_feedback_row_count: 10
- closed_pyramid_row_count: 2
- pyramid_would_have_helped_count: 0
- pyramid_correctly_blocked_count: 0
- pyramid_overheat_or_reversal_risk_count: 2
- pyramid_open_unresolved_count: 8
- one_share_event_count: 2
- one_share_closed_count: 2
- one_share_pyramid_opportunity_count: 0
- one_share_pyramid_missed_upside_count: 0
- one_share_pyramid_missed_upside_rate: 0.00
- one_share_pyramid_avg_opportunity_cost_pct: 0.00
- probe_residual_zero_fill_count: 1
- probe_residual_soft_abort_count: 2
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
- probe_residual_pyramid_evaluation_seen_count: 2
- normal_winner_expansion: {"by_effective_venue": [{"allowed_runtime_apply": false, "effective_venue": "KRX", "notional_weighted_ev_pct": -0.5497, "realized_incremental_winner_count": 0, "runtime_effect": false, "sample_count": 1}], "by_market_session_bucket": [{"allowed_runtime_apply": false, "market_session_bucket": "krx_regular", "notional_weighted_ev_pct": -0.5497, "realized_incremental_winner_count": 0, "runtime_effect": false, "sample_count": 1}], "candidate_count": 1, "closed_candidate_count": 1, "correctly_not_expanded_or_reversal_count": 0, "diagnostic_win_rate": 0.0, "equal_weight_avg_profit_pct": -0.5497, "feature_axis_metrics": {"ai_score": [{"bucket": "lt_60", "daily_only_live_authority": false, "notional_weighted_ev_pct": -0.5497, "realized_incremental_winner_count": 0, "sample_count": 1}], "blocker_reason": [{"bucket": "rising_missed_scout_pyramid_bridge_blocked:profit_not_enough,micro_vwap_severe_overheated", "daily_only_live_authority": false, "notional_weighted_ev_pct": -0.5497, "realized_incremental_winner_count": 0, "sample_count": 1}], "buy_pressure_10t": [{"bucket": "ge_70", "daily_only_live_authority": false, "notional_weighted_ev_pct": -0.5497, "realized_incremental_winner_count": 0, "sample_count": 1}], "entry_profit_pct": [{"bucket": "lt_0.4", "daily_only_live_authority": false, "notional_weighted_ev_pct": -0.5497, "realized_incremental_winner_count": 0, "sample_count": 1}], "micro_vwap_side": [{"bucket": "non_negative", "daily_only_live_authority": false, "notional_weighted_ev_pct": -0.5497, "realized_incremental_winner_count": 0, "sample_count": 1}], "tick_acceleration_ratio": [{"bucket": "ge_1", "daily_only_live_authority": false, "notional_weighted_ev_pct": -0.5497, "realized_incremental_winner_count": 0, "sample_count": 1}]}, "label_counts": [{"count": 1, "label": "transient_extension_exit_timing_needed"}], "notional_weighted_ev_pct": -0.5497, "probe_confirmation_signature_metrics": [{"diagnostic_win_rate": 0.0, "realized_incremental_winner_count": 0, "sample_count": 1, "signature": "negative_group_seen"}], "realized_incremental_winner_count": 0, "source_quality_blocked_candidate_count": 0, "source_quality_valid_candidate_count": 1, "temporal_inversion_candidate_count": 0, "transient_extension_exit_timing_needed_count": 1, "venue_source_quality_blocked_closed_count": 0, "venue_source_quality_valid_closed_count": 1}
- whole_day_real_entry_lifecycle: {"by_effective_venue": [{"allowed_runtime_apply": false, "canceled_unfilled_cycle_count": 0, "closed_cycle_count": 2, "diagnostic_win_rate": 0.5, "effective_venue": "KRX", "equal_weight_avg_profit_pct": 0.05, "filled_cycle_count": 2, "flat_count": 0, "holding_cycle_count": 0, "loss_count": 1, "multi_leg_probe_cycle_count": 2, "realized_pnl_krw_known_count": 2, "realized_pnl_krw_known_sum": 400, "runtime_effect": false, "single_share_plan_closed_winner_count": 0, "submitted_cycle_count": 2, "winner_count": 1}], "by_market_session_bucket": [{"allowed_runtime_apply": false, "canceled_unfilled_cycle_count": 0, "closed_cycle_count": 2, "diagnostic_win_rate": 0.5, "equal_weight_avg_profit_pct": 0.05, "filled_cycle_count": 2, "flat_count": 0, "holding_cycle_count": 0, "loss_count": 1, "market_session_bucket": "krx_regular", "multi_leg_probe_cycle_count": 2, "realized_pnl_krw_known_count": 2, "realized_pnl_krw_known_sum": 400, "runtime_effect": false, "single_share_plan_closed_winner_count": 0, "submitted_cycle_count": 2, "winner_count": 1}], "canceled_unfilled_cycle_count": 0, "closed_cycle_count": 2, "diagnostic_win_rate": 0.5, "equal_weight_avg_profit_pct": 0.05, "filled_cycle_count": 2, "flat_count": 0, "holding_cycle_count": 0, "loss_count": 1, "multi_leg_probe_cycle_count": 2, "multi_leg_zero_residual_fill_count": 1, "pending_entry_cycle_count": 0, "realized_pnl_krw_known_count": 2, "realized_pnl_krw_known_sum": 400, "realized_pnl_krw_missing_count": 0, "realized_pnl_krw_source_counts": [{"count": 2, "source": "broker_fill_prices_fee_aware"}], "realized_pnl_source_quality_state": "complete", "single_share_plan_closed_winner_count": 0, "submitted_cycle_count": 2, "venue_source_quality_invalid_count": 0, "venue_source_quality_valid_count": 2, "winner_count": 1}
- real_scale_in_performance: {"active_unrealized_count": 0, "avg_down_execution_count": 0, "by_outcome_cohort": {"avg_down": {"active_unrealized_count": 0, "closed_count": 0, "closed_loss_or_flat_count": 0, "closed_winner_count": 0, "equal_weight_avg_final_position_profit_pct": null, "execution_count": 0, "runtime_apply_authority": false}, "normal_pyramid": {"active_unrealized_count": 0, "closed_count": 0, "closed_loss_or_flat_count": 0, "closed_winner_count": 0, "equal_weight_avg_final_position_profit_pct": null, "execution_count": 0, "runtime_apply_authority": false}, "unknown": {"active_unrealized_count": 0, "closed_count": 0, "closed_loss_or_flat_count": 0, "closed_winner_count": 0, "equal_weight_avg_final_position_profit_pct": null, "execution_count": 0, "runtime_apply_authority": false}, "winner_recovery": {"active_unrealized_count": 0, "closed_count": 0, "closed_loss_or_flat_count": 0, "closed_winner_count": 0, "equal_weight_avg_final_position_profit_pct": null, "execution_count": 0, "runtime_apply_authority": false}}, "closed_count": 0, "completed_outcome_available": false, "execution_count": 0, "normal_pyramid_execution_count": 0, "source_quality_adjusted_ev_available": false, "source_quality_adjusted_ev_unavailable_reason": "no_closed_scale_in_position", "winner_expansion_vs_avg_down_asymmetry_observed": false, "winner_recovery_execution_count": 0, "winner_recovery_qty_cap_invalid_count": 0}
- pyramid_min_profit_pct: 1.1
- pyramid_threshold_source: same_day_unique_runtime_pyramid_evaluation

## Blocker Metrics

- blocker=micro_vwap_overheated sample=1 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=profit_not_enough sample=6 recovered_rate=0.00 reversal_rate=0.17 blocked_then_recovered_rate=0.00
- blocker=pyramid_hard_blocked:buy_pressure_severe_below_min,micro_vwap_severe_overheated,large_sell_detected sample=1 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=rising_missed_scout_pyramid_bridge_blocked:profit_not_enough,micro_vwap_severe_overheated sample=1 recovered_rate=0.00 reversal_rate=1.00 blocked_then_recovered_rate=0.00
- blocker=trend_not_strong sample=1 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00

## Rows

- record_id= code=092870 name=엑시콘 label=pyramid_open_unresolved blocker=pyramid_hard_blocked:buy_pressure_severe_below_min,micro_vwap_severe_overheated,large_sell_detected profit=1.76 final=None ai=51.0 tick=1.0 micro_vwap=143.32
- record_id= code=067310 name=하나마이크론 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.24 final=None ai=43.0 tick=0.5 micro_vwap=0.71
- record_id=32661 code=322000 name=HD현대에너지솔루션 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=0.32 final=0.32 ai=48.0 tick=1.0 micro_vwap=44.0
- record_id= code=377450 name=리파인 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.01 final=None ai=50.0 tick=0.5 micro_vwap=-17.57
- record_id=32701 code=419050 name=삼기에너지솔루션즈 label=pyramid_overheat_or_reversal_risk blocker=rising_missed_scout_pyramid_bridge_blocked:profit_not_enough,micro_vwap_severe_overheated profit=0.1 final=-0.22 ai=48.0 tick=1.3 micro_vwap=-21.93
- record_id= code=222800 name=심텍 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.92 final=None ai=63.0 tick=0.0 micro_vwap=53.34
- record_id= code=006110 name=삼아알미늄 label=pyramid_open_unresolved blocker=micro_vwap_overheated profit=1.24 final=None ai=39.0 tick=1.667 micro_vwap=-101.99
- record_id= code=025980 name=아난티 label=pyramid_open_unresolved blocker=trend_not_strong profit=1.51 final=None ai=52.0 tick=0.0 micro_vwap=18.25
- record_id= code=475560 name=더본코리아 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.75 final=None ai=50.0 tick=0.0 micro_vwap=55.92
- record_id= code=007660 name=이수페타시스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.06 final=None ai=50.0 tick=3.857 micro_vwap=-9.15

## Real Scale-In Performance Rows


## One Share Opportunity Rows

- record_id=32661 code=322000 name=HD현대에너지솔루션 label=pyramid_correctly_blocked canonical=expansion_not_applicable_residual_filled opportunity_seen=False opportunity_profit=None max_profit=0.78 opportunity_cost=0.78 final=0.32 residual_zero_fill=False residual_soft_abort=True residual_missed_candidate=False post_probe_real_outcome=not_zero_fill confirmation_ready=False runtime_confirmation_ready=False confirmation_alignment=not_runtime_confirmed recovery_evaluation_seen=False recovery_confirmation_ready=False confirmation_source_quality_blockers=tick_context_not_fresh first_leg_qty=None first_leg_profit_proxy_krw=None
- record_id=32701 code=419050 name=삼기에너지솔루션즈 label=pyramid_correctly_blocked canonical=expansion_correctly_not_expanded opportunity_seen=False opportunity_profit=None max_profit=0.86 opportunity_cost=0.86 final=-0.22 residual_zero_fill=True residual_soft_abort=True residual_missed_candidate=False post_probe_real_outcome=loss_or_flat_zero_fill_no_confirmation confirmation_ready=False runtime_confirmation_ready=False confirmation_alignment=not_runtime_confirmed recovery_evaluation_seen=True recovery_confirmation_ready=False confirmation_source_quality_blockers=tick_context_not_fresh first_leg_qty=None first_leg_profit_proxy_krw=None

## Whole-Day Real Entry Lifecycle Rows

- record_id=32661 code=322000 name=HD현대에너지솔루션 venue=KRX session=krx_regular state=closed planned_qty=4 submitted_qty=1 filled_qty=1 final=0.32 realized_pnl_krw=404 realized_pnl_source=broker_fill_prices_fee_aware canonical=expansion_not_applicable_residual_filled
- record_id=32701 code=419050 name=삼기에너지솔루션즈 venue=KRX session=krx_regular state=closed planned_qty=267 submitted_qty=1 filled_qty=1 final=-0.22 realized_pnl_krw=-4 realized_pnl_source=broker_fill_prices_fee_aware canonical=expansion_correctly_not_expanded

## Normal Winner Expansion Rows

- record_id=32661 code=322000 name=HD현대에너지솔루션 label=not_underexpanded entry_profit=0.32 incremental_mfe=0.2285 incremental_final=-0.23 confirmation=None
- record_id=32701 code=419050 name=삼기에너지솔루션즈 label=transient_extension_exit_timing_needed entry_profit=0.1 incremental_mfe=0.5292 incremental_final=-0.5497 confirmation=negative_group_seen
