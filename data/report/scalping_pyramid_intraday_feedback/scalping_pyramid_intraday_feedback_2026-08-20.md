# 2026-08-20 Scalping Pyramid Intraday Feedback

- generated_at: 2026-08-20T12:45:02+09:00
- decision_authority: source_only_pyramid_intraday_feedback_no_runtime_mutation
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: intraday_threshold_mutation, intraday_runtime_apply, hard_safety_relaxation, broker_guard_bypass, order_guard_relaxation, stale_quote_bypass, cooldown_bypass, quantity_guard_relaxation, position_cap_release, provider_route_change, bot_restart, real_execution_quality_approval

## Summary

- pyramid_feedback_row_count: 4
- closed_pyramid_row_count: 2
- pyramid_would_have_helped_count: 1
- pyramid_correctly_blocked_count: 0
- pyramid_overheat_or_reversal_risk_count: 1
- pyramid_open_unresolved_count: 2
- one_share_event_count: 8
- one_share_closed_count: 5
- one_share_pyramid_opportunity_count: 3
- one_share_pyramid_missed_upside_count: 1
- one_share_pyramid_missed_upside_rate: 0.20
- one_share_pyramid_avg_opportunity_cost_pct: 0.19
- probe_residual_zero_fill_count: 8
- probe_residual_soft_abort_count: 7
- probe_residual_missed_upside_candidate_count: 0
- probe_residual_pyramid_threshold_missed_upside_candidate_count: 3
- probe_residual_real_outcome_closed_count: 5
- probe_residual_realized_winner_zero_fill_count: 4
- probe_residual_realized_loss_or_flat_zero_fill_count: 1
- probe_residual_realized_winner_confirmation_ready_count: 0
- probe_residual_realized_loss_or_flat_confirmation_ready_count: 0
- post_hard_abort_recovery_evaluation_seen_count: 5
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
- probe_residual_pyramid_evaluation_seen_count: 3
- normal_winner_expansion: {"by_effective_venue": [{"allowed_runtime_apply": false, "effective_venue": "KRX", "notional_weighted_ev_pct": 0.9489, "realized_incremental_winner_count": 1, "runtime_effect": false, "sample_count": 1}], "by_market_session_bucket": [{"allowed_runtime_apply": false, "market_session_bucket": "krx_regular", "notional_weighted_ev_pct": 0.9489, "realized_incremental_winner_count": 1, "runtime_effect": false, "sample_count": 1}], "candidate_count": 3, "closed_candidate_count": 1, "correctly_not_expanded_or_reversal_count": 0, "diagnostic_win_rate": 1.0, "equal_weight_avg_profit_pct": 0.9489, "feature_axis_metrics": {"ai_score": [{"bucket": "lt_60", "daily_only_live_authority": false, "notional_weighted_ev_pct": 0.9489, "realized_incremental_winner_count": 1, "sample_count": 1}], "blocker_reason": [{"bucket": "rising_missed_scout_pyramid_bridge_blocked:profit_not_enough", "daily_only_live_authority": false, "notional_weighted_ev_pct": 0.9489, "realized_incremental_winner_count": 1, "sample_count": 1}], "buy_pressure_10t": [{"bucket": "50_to_70", "daily_only_live_authority": false, "notional_weighted_ev_pct": 0.9489, "realized_incremental_winner_count": 1, "sample_count": 1}], "entry_profit_pct": [{"bucket": "lt_0.4", "daily_only_live_authority": false, "notional_weighted_ev_pct": 0.9489, "realized_incremental_winner_count": 1, "sample_count": 1}], "micro_vwap_side": [{"bucket": "non_negative", "daily_only_live_authority": false, "notional_weighted_ev_pct": 0.9489, "realized_incremental_winner_count": 1, "sample_count": 1}], "tick_acceleration_ratio": [{"bucket": "lt_0.5", "daily_only_live_authority": false, "notional_weighted_ev_pct": 0.9489, "realized_incremental_winner_count": 1, "sample_count": 1}]}, "label_counts": [{"count": 1, "label": "realized_incremental_winner"}, {"count": 1, "label": "source_quality_blocked"}, {"count": 1, "label": "open_unresolved"}], "notional_weighted_ev_pct": 0.9489, "probe_confirmation_signature_metrics": [{"diagnostic_win_rate": 0.5, "realized_incremental_winner_count": 1, "sample_count": 2, "signature": "no_directional_confirmation"}], "realized_incremental_winner_count": 1, "source_quality_blocked_candidate_count": 1, "source_quality_valid_candidate_count": 2, "temporal_inversion_candidate_count": 0, "transient_extension_exit_timing_needed_count": 0, "venue_source_quality_blocked_closed_count": 0, "venue_source_quality_valid_closed_count": 1}
- whole_day_real_entry_lifecycle: {"by_effective_venue": [{"allowed_runtime_apply": false, "canceled_unfilled_cycle_count": 0, "closed_cycle_count": 5, "diagnostic_win_rate": 0.8, "effective_venue": "KRX", "equal_weight_avg_profit_pct": -0.34, "filled_cycle_count": 9, "flat_count": 0, "holding_cycle_count": 4, "loss_count": 1, "multi_leg_probe_cycle_count": 8, "realized_pnl_krw_known_count": 5, "realized_pnl_krw_known_sum": -549, "runtime_effect": false, "single_share_plan_closed_winner_count": 0, "submitted_cycle_count": 9, "winner_count": 4}], "by_market_session_bucket": [{"allowed_runtime_apply": false, "canceled_unfilled_cycle_count": 0, "closed_cycle_count": 5, "diagnostic_win_rate": 0.8, "equal_weight_avg_profit_pct": -0.34, "filled_cycle_count": 9, "flat_count": 0, "holding_cycle_count": 4, "loss_count": 1, "market_session_bucket": "krx_regular", "multi_leg_probe_cycle_count": 8, "realized_pnl_krw_known_count": 5, "realized_pnl_krw_known_sum": -549, "runtime_effect": false, "single_share_plan_closed_winner_count": 0, "submitted_cycle_count": 9, "winner_count": 4}], "canceled_unfilled_cycle_count": 0, "closed_cycle_count": 5, "diagnostic_win_rate": 0.8, "equal_weight_avg_profit_pct": -0.34, "filled_cycle_count": 9, "flat_count": 0, "holding_cycle_count": 4, "loss_count": 1, "multi_leg_probe_cycle_count": 8, "multi_leg_zero_residual_fill_count": 8, "pending_entry_cycle_count": 0, "realized_pnl_krw_known_count": 5, "realized_pnl_krw_known_sum": -549, "realized_pnl_krw_missing_count": 0, "realized_pnl_krw_source_counts": [{"count": 5, "source": "broker_fill_prices_fee_aware"}], "realized_pnl_source_quality_state": "complete", "single_share_plan_closed_winner_count": 0, "submitted_cycle_count": 9, "venue_source_quality_invalid_count": 0, "venue_source_quality_valid_count": 9, "winner_count": 4}
- real_scale_in_performance: {"active_unrealized_count": 1, "avg_down_execution_count": 0, "by_outcome_cohort": {"avg_down": {"active_unrealized_count": 0, "closed_count": 0, "closed_loss_or_flat_count": 0, "closed_winner_count": 0, "equal_weight_avg_final_position_profit_pct": null, "execution_count": 0, "runtime_apply_authority": false}, "normal_pyramid": {"active_unrealized_count": 1, "closed_count": 0, "closed_loss_or_flat_count": 0, "closed_winner_count": 0, "equal_weight_avg_final_position_profit_pct": null, "execution_count": 1, "runtime_apply_authority": false}, "unknown": {"active_unrealized_count": 0, "closed_count": 0, "closed_loss_or_flat_count": 0, "closed_winner_count": 0, "equal_weight_avg_final_position_profit_pct": null, "execution_count": 0, "runtime_apply_authority": false}, "winner_recovery": {"active_unrealized_count": 0, "closed_count": 0, "closed_loss_or_flat_count": 0, "closed_winner_count": 0, "equal_weight_avg_final_position_profit_pct": null, "execution_count": 0, "runtime_apply_authority": false}}, "closed_count": 0, "completed_outcome_available": false, "execution_count": 1, "normal_pyramid_execution_count": 1, "source_quality_adjusted_ev_available": false, "source_quality_adjusted_ev_unavailable_reason": "no_closed_scale_in_position", "winner_expansion_vs_avg_down_asymmetry_observed": false, "winner_recovery_execution_count": 0, "winner_recovery_qty_cap_invalid_count": 0}
- pyramid_min_profit_pct: 1.1
- pyramid_threshold_source: same_day_unique_runtime_pyramid_evaluation

## Blocker Metrics

- blocker=profit_not_enough sample=1 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=pyramid_submitted sample=1 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=rising_missed_scout_pyramid_bridge_blocked:profit_not_enough sample=1 recovered_rate=1.00 reversal_rate=0.00 blocked_then_recovered_rate=1.00
- blocker=rising_missed_scout_pyramid_bridge_blocked:profit_not_enough,micro_context_stale,tick_accel_stale,tick_aggressor_pressure_unusable,fresh_micro_confirmation_missing sample=1 recovered_rate=0.00 reversal_rate=1.00 blocked_then_recovered_rate=0.00

## Rows

- record_id=33493 code=299660 name=셀리드 label=pyramid_would_have_helped blocker=rising_missed_scout_pyramid_bridge_blocked:profit_not_enough profit=0.09 final=1.27 ai=58.0 tick=1.0 micro_vwap=132.07
- record_id=33703 code=299660 name=셀리드 label=pyramid_overheat_or_reversal_risk blocker=rising_missed_scout_pyramid_bridge_blocked:profit_not_enough,micro_context_stale,tick_accel_stale,tick_aggressor_pressure_unusable,fresh_micro_confirmation_missing profit=0.55 final=0.26 ai=50.0 tick=2.286 micro_vwap=67.46
- record_id=33388 code=124500 name=아이티센글로벌 label=pyramid_open_unresolved blocker=pyramid_submitted profit=0.1 final=None ai=65.0 tick=0.25 micro_vwap=6.47
- record_id= code=000100 name=유한양행 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.61 final=None ai=50.0 tick=6.2 micro_vwap=-3.81

## Real Scale-In Performance Rows

- record_id=33388 code=124500 name=아이티센글로벌 cohort=normal_pyramid type=PYRAMID reason=rising_missed_scout_pyramid_bridge_ok fill=30950.0x1 closed=False latest=0.09 final=None leg_gross_proxy=None

## One Share Opportunity Rows

- record_id=33494 code=006660 name=삼성공조 label=pyramid_correctly_blocked canonical=expansion_correctly_not_expanded opportunity_seen=False opportunity_profit=None max_profit=-0.04 opportunity_cost=0.0 final=-4.49 residual_zero_fill=True residual_soft_abort=True residual_missed_candidate=False post_probe_real_outcome=loss_or_flat_zero_fill_no_confirmation confirmation_ready=False runtime_confirmation_ready=False confirmation_alignment=not_runtime_confirmed recovery_evaluation_seen=True recovery_confirmation_ready=False confirmation_source_quality_blockers=tick_context_not_fresh first_leg_qty=None first_leg_profit_proxy_krw=None
- record_id=33629 code=091590 name=남화토건 label=pyramid_correctly_blocked canonical=expansion_correctly_not_expanded_recovery_not_confirmed opportunity_seen=True opportunity_profit=1.1 max_profit=1.37 opportunity_cost=0.27 final=0.74 residual_zero_fill=True residual_soft_abort=False residual_missed_candidate=False post_probe_real_outcome=profitable_zero_fill_recovery_not_confirmed confirmation_ready=False runtime_confirmation_ready=False confirmation_alignment=not_runtime_confirmed recovery_evaluation_seen=True recovery_confirmation_ready=False confirmation_source_quality_blockers=- first_leg_qty=None first_leg_profit_proxy_krw=None
- record_id=33493 code=299660 name=셀리드 label=pyramid_would_have_helped canonical=expansion_correctly_not_expanded_no_confirmation opportunity_seen=True opportunity_profit=1.73 max_profit=1.94 opportunity_cost=0.21 final=1.27 residual_zero_fill=True residual_soft_abort=True residual_missed_candidate=False post_probe_real_outcome=profitable_zero_fill_no_confirmation confirmation_ready=False runtime_confirmation_ready=False confirmation_alignment=not_runtime_confirmed recovery_evaluation_seen=True recovery_confirmation_ready=False confirmation_source_quality_blockers=- first_leg_qty=None first_leg_profit_proxy_krw=None
- record_id=33703 code=299660 name=셀리드 label=pyramid_correctly_blocked canonical=expansion_correctly_not_expanded_no_confirmation opportunity_seen=False opportunity_profit=None max_profit=0.65 opportunity_cost=0.65 final=0.26 residual_zero_fill=True residual_soft_abort=True residual_missed_candidate=False post_probe_real_outcome=profitable_zero_fill_no_confirmation confirmation_ready=False runtime_confirmation_ready=False confirmation_alignment=not_runtime_confirmed recovery_evaluation_seen=True recovery_confirmation_ready=False confirmation_source_quality_blockers=tick_context_not_fresh first_leg_qty=None first_leg_profit_proxy_krw=None
- record_id=33537 code=002990 name=금호건설 label=pyramid_correctly_blocked canonical=expansion_correctly_not_expanded_no_confirmation opportunity_seen=True opportunity_profit=1.1 max_profit=1.2 opportunity_cost=0.1 final=0.52 residual_zero_fill=True residual_soft_abort=True residual_missed_candidate=False post_probe_real_outcome=profitable_zero_fill_no_confirmation confirmation_ready=False runtime_confirmation_ready=False confirmation_alignment=not_runtime_confirmed recovery_evaluation_seen=True recovery_confirmation_ready=False confirmation_source_quality_blockers=tick_context_not_fresh first_leg_qty=None first_leg_profit_proxy_krw=None
- record_id=33470 code=064260 name=다날 label=pyramid_open_unresolved canonical=expansion_source_quality_blocked opportunity_seen=False opportunity_profit=None max_profit=-0.04 opportunity_cost=0.0 final=None residual_zero_fill=True residual_soft_abort=True residual_missed_candidate=False post_probe_real_outcome=source_quality_blocked confirmation_ready=False runtime_confirmation_ready=False confirmation_alignment=not_runtime_confirmed recovery_evaluation_seen=True recovery_confirmation_ready=False confirmation_source_quality_blockers=tick_context_not_fresh first_leg_qty=None first_leg_profit_proxy_krw=None
- record_id=33388 code=124500 name=아이티센글로벌 label=pyramid_open_unresolved canonical=expansion_source_quality_blocked opportunity_seen=False opportunity_profit=None max_profit=1.07 opportunity_cost=1.07 final=None residual_zero_fill=True residual_soft_abort=True residual_missed_candidate=False post_probe_real_outcome=source_quality_blocked confirmation_ready=False runtime_confirmation_ready=False confirmation_alignment=not_runtime_confirmed recovery_evaluation_seen=True recovery_confirmation_ready=False confirmation_source_quality_blockers=tick_context_not_fresh first_leg_qty=None first_leg_profit_proxy_krw=None
- record_id=33389 code=138610 name=나이벡 label=pyramid_open_unresolved canonical=expansion_source_quality_blocked opportunity_seen=False opportunity_profit=None max_profit=0.09 opportunity_cost=0.09 final=None residual_zero_fill=True residual_soft_abort=True residual_missed_candidate=False post_probe_real_outcome=source_quality_blocked confirmation_ready=False runtime_confirmation_ready=False confirmation_alignment=not_runtime_confirmed recovery_evaluation_seen=True recovery_confirmation_ready=False confirmation_source_quality_blockers=tick_context_not_fresh first_leg_qty=None first_leg_profit_proxy_krw=None

## Whole-Day Real Entry Lifecycle Rows

- record_id=33494 code=006660 name=삼성공조 venue=KRX session=krx_regular state=closed planned_qty=10 submitted_qty=1 filled_qty=1 final=-4.49 realized_pnl_krw=-704 realized_pnl_source=broker_fill_prices_fee_aware canonical=expansion_correctly_not_expanded
- record_id=33629 code=091590 name=남화토건 venue=KRX session=krx_regular state=closed planned_qty=28 submitted_qty=1 filled_qty=1 final=0.74 realized_pnl_krw=46 realized_pnl_source=broker_fill_prices_fee_aware canonical=expansion_correctly_not_expanded_recovery_not_confirmed
- record_id=33654 code=059090 name=미코 venue=KRX session=krx_regular state=holding planned_qty=1 submitted_qty=1 filled_qty=1 final=None realized_pnl_krw=None realized_pnl_source=None canonical=None
- record_id=33493 code=299660 name=셀리드 venue=KRX session=krx_regular state=closed planned_qty=92 submitted_qty=1 filled_qty=1 final=1.27 realized_pnl_krw=24 realized_pnl_source=broker_fill_prices_fee_aware canonical=expansion_correctly_not_expanded_no_confirmation
- record_id=33703 code=299660 name=셀리드 venue=KRX session=krx_regular state=closed planned_qty=90 submitted_qty=1 filled_qty=1 final=0.26 realized_pnl_krw=5 realized_pnl_source=broker_fill_prices_fee_aware canonical=expansion_correctly_not_expanded_no_confirmation
- record_id=33537 code=002990 name=금호건설 venue=KRX session=krx_regular state=closed planned_qty=8 submitted_qty=1 filled_qty=1 final=0.52 realized_pnl_krw=80 realized_pnl_source=broker_fill_prices_fee_aware canonical=expansion_correctly_not_expanded_no_confirmation
- record_id=33470 code=064260 name=다날 venue=KRX session=krx_regular state=holding planned_qty=15 submitted_qty=1 filled_qty=1 final=None realized_pnl_krw=None realized_pnl_source=None canonical=expansion_source_quality_blocked
- record_id=33388 code=124500 name=아이티센글로벌 venue=KRX session=krx_regular state=holding planned_qty=2 submitted_qty=1 filled_qty=1 final=None realized_pnl_krw=None realized_pnl_source=None canonical=expansion_source_quality_blocked
- record_id=33389 code=138610 name=나이벡 venue=KRX session=krx_regular state=holding planned_qty=4 submitted_qty=1 filled_qty=1 final=None realized_pnl_krw=None realized_pnl_source=None canonical=expansion_source_quality_blocked

## Normal Winner Expansion Rows

- record_id=33493 code=299660 name=셀리드 label=realized_incremental_winner entry_profit=0.09 incremental_mfe=1.6183 incremental_final=0.9489 confirmation=no_directional_confirmation
- record_id=33703 code=299660 name=셀리드 label=source_quality_blocked entry_profit=0.55 incremental_mfe=-0.1305 incremental_final=-0.5184 confirmation=None
- record_id=33388 code=124500 name=아이티센글로벌 label=open_unresolved entry_profit=0.1 incremental_mfe=0.739 incremental_final=None confirmation=no_directional_confirmation
