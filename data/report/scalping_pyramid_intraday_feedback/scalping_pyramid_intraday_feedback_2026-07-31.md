# 2026-07-31 Scalping Pyramid Intraday Feedback

- generated_at: 2026-08-01T15:11:33+09:00
- decision_authority: source_only_pyramid_intraday_feedback_no_runtime_mutation
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: intraday_threshold_mutation, intraday_runtime_apply, hard_safety_relaxation, broker_guard_bypass, order_guard_relaxation, stale_quote_bypass, cooldown_bypass, quantity_guard_relaxation, position_cap_release, provider_route_change, bot_restart, real_execution_quality_approval

## Summary

- pyramid_feedback_row_count: 6
- closed_pyramid_row_count: 3
- pyramid_would_have_helped_count: 2
- pyramid_correctly_blocked_count: 0
- pyramid_overheat_or_reversal_risk_count: 1
- pyramid_open_unresolved_count: 3
- one_share_event_count: 5
- one_share_closed_count: 4
- one_share_pyramid_opportunity_count: 1
- one_share_pyramid_missed_upside_count: 1
- one_share_pyramid_missed_upside_rate: 0.25
- one_share_pyramid_avg_opportunity_cost_pct: 0.18
- probe_residual_zero_fill_count: 5
- probe_residual_soft_abort_count: 2
- probe_residual_missed_upside_candidate_count: 0
- probe_residual_pyramid_threshold_missed_upside_candidate_count: 1
- probe_residual_real_outcome_closed_count: 4
- probe_residual_realized_winner_zero_fill_count: 4
- probe_residual_realized_loss_or_flat_zero_fill_count: 0
- probe_residual_realized_winner_confirmation_ready_count: 0
- probe_residual_realized_loss_or_flat_confirmation_ready_count: 0
- canonical_expansion_missed_upside_count: 1
- canonical_expansion_source_quality_valid_missed_upside_count: 0
- post_probe_runtime_confirmation_source_quality_disputed_count: 1
- post_probe_legacy_label_conflict_count: 0
- post_probe_confirmation_false_positive_loss_or_flat_count: 0
- probe_residual_confirmation_ready_equal_weight_avg_profit_pct: 0.0000
- probe_residual_confirmation_ready_notional_weighted_ev_pct: 0.0000
- probe_residual_confirmation_ready_simple_sum_profit_proxy_krw: 0.00
- probe_residual_pyramid_evaluation_seen_count: 2
- normal_winner_expansion: {"by_effective_venue": [{"allowed_runtime_apply": false, "effective_venue": "KRX", "notional_weighted_ev_pct": 0.451, "realized_incremental_winner_count": 2, "runtime_effect": false, "sample_count": 2}], "by_market_session_bucket": [{"allowed_runtime_apply": false, "market_session_bucket": "krx_regular", "notional_weighted_ev_pct": 0.451, "realized_incremental_winner_count": 2, "runtime_effect": false, "sample_count": 2}], "candidate_count": 2, "closed_candidate_count": 2, "correctly_not_expanded_or_reversal_count": 0, "diagnostic_win_rate": 1.0, "equal_weight_avg_profit_pct": 0.4496, "feature_axis_metrics": {"ai_score": [{"bucket": "lt_60", "daily_only_live_authority": false, "notional_weighted_ev_pct": 0.451, "realized_incremental_winner_count": 2, "sample_count": 2}], "blocker_reason": [{"bucket": "profit_not_enough", "daily_only_live_authority": false, "notional_weighted_ev_pct": 0.7696, "realized_incremental_winner_count": 1, "sample_count": 1}, {"bucket": "rising_missed_scout_pyramid_bridge_blocked:profit_not_enough,large_sell_detected", "daily_only_live_authority": false, "notional_weighted_ev_pct": 0.1295, "realized_incremental_winner_count": 1, "sample_count": 1}], "buy_pressure_10t": [{"bucket": "lt_50", "daily_only_live_authority": false, "notional_weighted_ev_pct": 0.451, "realized_incremental_winner_count": 2, "sample_count": 2}], "entry_profit_pct": [{"bucket": "lt_0.4", "daily_only_live_authority": false, "notional_weighted_ev_pct": 0.451, "realized_incremental_winner_count": 2, "sample_count": 2}], "micro_vwap_side": [{"bucket": "non_negative", "daily_only_live_authority": false, "notional_weighted_ev_pct": 0.451, "realized_incremental_winner_count": 2, "sample_count": 2}], "tick_acceleration_ratio": [{"bucket": "0.5_to_1", "daily_only_live_authority": false, "notional_weighted_ev_pct": 0.1295, "realized_incremental_winner_count": 1, "sample_count": 1}, {"bucket": "ge_1", "daily_only_live_authority": false, "notional_weighted_ev_pct": 0.7696, "realized_incremental_winner_count": 1, "sample_count": 1}]}, "label_counts": [{"count": 2, "label": "realized_incremental_winner"}], "notional_weighted_ev_pct": 0.451, "probe_confirmation_signature_metrics": [{"diagnostic_win_rate": 1.0, "realized_incremental_winner_count": 1, "sample_count": 1, "signature": "negative_group_seen"}, {"diagnostic_win_rate": 1.0, "realized_incremental_winner_count": 1, "sample_count": 1, "signature": "no_directional_confirmation"}], "realized_incremental_winner_count": 2, "source_quality_blocked_candidate_count": 0, "source_quality_valid_candidate_count": 2, "temporal_inversion_candidate_count": 0, "transient_extension_exit_timing_needed_count": 0, "venue_source_quality_blocked_closed_count": 0, "venue_source_quality_valid_closed_count": 2}
- whole_day_real_entry_lifecycle: {"by_effective_venue": [{"allowed_runtime_apply": false, "canceled_unfilled_cycle_count": 0, "closed_cycle_count": 4, "diagnostic_win_rate": 1.0, "effective_venue": "KRX", "equal_weight_avg_profit_pct": 0.61, "filled_cycle_count": 5, "flat_count": 0, "holding_cycle_count": 1, "loss_count": 0, "multi_leg_probe_cycle_count": 5, "realized_pnl_krw_known_count": 0, "realized_pnl_krw_known_sum": 0, "runtime_effect": false, "single_share_plan_closed_winner_count": 0, "submitted_cycle_count": 5, "winner_count": 4}], "by_market_session_bucket": [{"allowed_runtime_apply": false, "canceled_unfilled_cycle_count": 0, "closed_cycle_count": 4, "diagnostic_win_rate": 1.0, "equal_weight_avg_profit_pct": 0.61, "filled_cycle_count": 5, "flat_count": 0, "holding_cycle_count": 1, "loss_count": 0, "market_session_bucket": "krx_regular", "multi_leg_probe_cycle_count": 5, "realized_pnl_krw_known_count": 0, "realized_pnl_krw_known_sum": 0, "runtime_effect": false, "single_share_plan_closed_winner_count": 0, "submitted_cycle_count": 5, "winner_count": 4}], "canceled_unfilled_cycle_count": 0, "closed_cycle_count": 4, "diagnostic_win_rate": 1.0, "equal_weight_avg_profit_pct": 0.61, "filled_cycle_count": 5, "flat_count": 0, "holding_cycle_count": 1, "loss_count": 0, "multi_leg_probe_cycle_count": 5, "multi_leg_zero_residual_fill_count": 5, "pending_entry_cycle_count": 0, "realized_pnl_krw_known_count": 0, "realized_pnl_krw_known_sum": 0, "realized_pnl_krw_missing_count": 4, "realized_pnl_source_quality_state": "partial_missing_realized_pnl", "single_share_plan_closed_winner_count": 0, "submitted_cycle_count": 5, "venue_source_quality_invalid_count": 0, "venue_source_quality_valid_count": 5, "winner_count": 4}
- pyramid_min_profit_pct: 1.1
- pyramid_threshold_source: same_day_unique_runtime_pyramid_evaluation

## Blocker Metrics

- blocker=profit_not_enough sample=5 recovered_rate=0.20 reversal_rate=0.20 blocked_then_recovered_rate=0.20
- blocker=rising_missed_scout_pyramid_bridge_blocked:profit_not_enough,large_sell_detected sample=1 recovered_rate=1.00 reversal_rate=0.00 blocked_then_recovered_rate=1.00

## Rows

- record_id=25413 code=005930 name=삼성전자 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=0.78 final=0.38 ai=50.0 tick=0.0 micro_vwap=48.79
- record_id= code=204320 name=HL만도 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.56 final=None ai=53.0 tick=0.667 micro_vwap=-37.6
- record_id=25439 code=096770 name=SK이노베이션 label=pyramid_would_have_helped blocker=rising_missed_scout_pyramid_bridge_blocked:profit_not_enough,large_sell_detected profit=0.14 final=0.5 ai=65.0 tick=1.0 micro_vwap=43.28
- record_id= code=064400 name=LG씨엔에스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.08 final=None ai=39.0 tick=2.0 micro_vwap=5.83
- record_id= code=298380 name=에이비엘바이오 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.07 final=None ai=50.0 tick=0.429 micro_vwap=55.42
- record_id=25712 code=096770 name=SK이노베이션 label=pyramid_would_have_helped blocker=profit_not_enough profit=0.04 final=1.04 ai=50.0 tick=2.0 micro_vwap=2.69

## One Share Opportunity Rows

- record_id=25678 code=000250 name=삼천당제약 label=pyramid_correctly_blocked canonical=expansion_missed_upside_runtime_confirmed_source_quality_disputed opportunity_seen=False opportunity_profit=None max_profit=1.06 opportunity_cost=1.06 final=0.38 residual_zero_fill=True residual_soft_abort=False residual_missed_candidate=False post_probe_real_outcome=profitable_zero_fill_no_confirmation confirmation_ready=False runtime_confirmation_ready=True confirmation_alignment=runtime_confirmed_source_quality_disputed confirmation_source_quality_blockers=tick_context_not_fresh first_leg_qty=1 first_leg_profit_proxy_krw=557.08
- record_id=25691 code=000250 name=삼천당제약 label=pyramid_correctly_blocked canonical=expansion_correctly_not_expanded_no_confirmation opportunity_seen=False opportunity_profit=None max_profit=0.85 opportunity_cost=0.85 final=0.52 residual_zero_fill=True residual_soft_abort=False residual_missed_candidate=False post_probe_real_outcome=profitable_zero_fill_no_confirmation confirmation_ready=False runtime_confirmation_ready=False confirmation_alignment=not_runtime_confirmed confirmation_source_quality_blockers=- first_leg_qty=1 first_leg_profit_proxy_krw=765.96
- record_id=25439 code=096770 name=SK이노베이션 label=pyramid_correctly_blocked canonical=expansion_correctly_not_expanded_no_confirmation opportunity_seen=False opportunity_profit=None max_profit=0.96 opportunity_cost=0.96 final=0.5 residual_zero_fill=True residual_soft_abort=True residual_missed_candidate=False post_probe_real_outcome=profitable_zero_fill_no_confirmation confirmation_ready=False runtime_confirmation_ready=False confirmation_alignment=not_runtime_confirmed confirmation_source_quality_blockers=tick_context_not_fresh first_leg_qty=1 first_leg_profit_proxy_krw=544.0
- record_id=25712 code=096770 name=SK이노베이션 label=pyramid_would_have_helped canonical=expansion_correctly_not_expanded_no_confirmation opportunity_seen=True opportunity_profit=1.13 max_profit=1.31 opportunity_cost=0.18 final=1.04 residual_zero_fill=True residual_soft_abort=False residual_missed_candidate=False post_probe_real_outcome=profitable_zero_fill_no_confirmation confirmation_ready=False runtime_confirmation_ready=False confirmation_alignment=not_runtime_confirmed confirmation_source_quality_blockers=- first_leg_qty=1 first_leg_profit_proxy_krw=1142.96
- record_id=25602 code=066570 name=LG전자 label=pyramid_open_unresolved canonical=expansion_source_quality_blocked opportunity_seen=False opportunity_profit=None max_profit=0.51 opportunity_cost=0.51 final=None residual_zero_fill=True residual_soft_abort=True residual_missed_candidate=False post_probe_real_outcome=source_quality_blocked confirmation_ready=False runtime_confirmation_ready=False confirmation_alignment=not_runtime_confirmed confirmation_source_quality_blockers=tick_context_not_fresh first_leg_qty=1 first_leg_profit_proxy_krw=None

## Whole-Day Real Entry Lifecycle Rows

- record_id=25678 code=000250 name=삼천당제약 venue=KRX session=krx_regular state=closed planned_qty=3 submitted_qty=1 filled_qty=1 final=0.38 realized_pnl_krw=None canonical=expansion_missed_upside_runtime_confirmed_source_quality_disputed
- record_id=25691 code=000250 name=삼천당제약 venue=KRX session=krx_regular state=closed planned_qty=3 submitted_qty=1 filled_qty=1 final=0.52 realized_pnl_krw=None canonical=expansion_correctly_not_expanded_no_confirmation
- record_id=25439 code=096770 name=SK이노베이션 venue=KRX session=krx_regular state=closed planned_qty=5 submitted_qty=1 filled_qty=1 final=0.5 realized_pnl_krw=None canonical=expansion_correctly_not_expanded_no_confirmation
- record_id=25712 code=096770 name=SK이노베이션 venue=KRX session=krx_regular state=closed planned_qty=5 submitted_qty=1 filled_qty=1 final=1.04 realized_pnl_krw=None canonical=expansion_correctly_not_expanded_no_confirmation
- record_id=25602 code=066570 name=LG전자 venue=KRX session=krx_regular state=holding planned_qty=2 submitted_qty=1 filled_qty=1 final=None realized_pnl_krw=None canonical=expansion_source_quality_blocked

## Normal Winner Expansion Rows

- record_id=25439 code=096770 name=SK이노베이션 label=realized_incremental_winner entry_profit=0.14 incremental_mfe=0.5889 incremental_final=0.1295 confirmation=negative_group_seen
- record_id=25712 code=096770 name=SK이노베이션 label=realized_incremental_winner entry_profit=0.04 incremental_mfe=1.0395 incremental_final=0.7696 confirmation=no_directional_confirmation
