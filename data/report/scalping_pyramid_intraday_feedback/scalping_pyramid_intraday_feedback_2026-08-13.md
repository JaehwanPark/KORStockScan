# 2026-08-13 Scalping Pyramid Intraday Feedback

- generated_at: 2026-08-13T20:17:25+09:00
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
- probe_residual_pyramid_evaluation_seen_count: 1
- normal_winner_expansion: {"by_effective_venue": [{"allowed_runtime_apply": false, "effective_venue": "KRX", "notional_weighted_ev_pct": -4.6034, "realized_incremental_winner_count": 0, "runtime_effect": false, "sample_count": 1}], "by_market_session_bucket": [{"allowed_runtime_apply": false, "market_session_bucket": "krx_regular", "notional_weighted_ev_pct": -4.6034, "realized_incremental_winner_count": 0, "runtime_effect": false, "sample_count": 1}], "candidate_count": 1, "closed_candidate_count": 1, "correctly_not_expanded_or_reversal_count": 1, "diagnostic_win_rate": 0.0, "equal_weight_avg_profit_pct": -4.6034, "feature_axis_metrics": {"ai_score": [{"bucket": "lt_60", "daily_only_live_authority": false, "notional_weighted_ev_pct": -4.6034, "realized_incremental_winner_count": 0, "sample_count": 1}], "blocker_reason": [{"bucket": "profit_not_enough", "daily_only_live_authority": false, "notional_weighted_ev_pct": -4.6034, "realized_incremental_winner_count": 0, "sample_count": 1}], "buy_pressure_10t": [{"bucket": "ge_70", "daily_only_live_authority": false, "notional_weighted_ev_pct": -4.6034, "realized_incremental_winner_count": 0, "sample_count": 1}], "entry_profit_pct": [{"bucket": "lt_0.4", "daily_only_live_authority": false, "notional_weighted_ev_pct": -4.6034, "realized_incremental_winner_count": 0, "sample_count": 1}], "micro_vwap_side": [{"bucket": "non_negative", "daily_only_live_authority": false, "notional_weighted_ev_pct": -4.6034, "realized_incremental_winner_count": 0, "sample_count": 1}], "tick_acceleration_ratio": [{"bucket": "ge_1", "daily_only_live_authority": false, "notional_weighted_ev_pct": -4.6034, "realized_incremental_winner_count": 0, "sample_count": 1}]}, "label_counts": [{"count": 1, "label": "correctly_not_expanded_or_reversal"}], "notional_weighted_ev_pct": -4.6034, "probe_confirmation_signature_metrics": [{"diagnostic_win_rate": 0.0, "realized_incremental_winner_count": 0, "sample_count": 1, "signature": "no_directional_confirmation"}], "realized_incremental_winner_count": 0, "source_quality_blocked_candidate_count": 0, "source_quality_valid_candidate_count": 1, "temporal_inversion_candidate_count": 0, "transient_extension_exit_timing_needed_count": 0, "venue_source_quality_blocked_closed_count": 0, "venue_source_quality_valid_closed_count": 1}
- whole_day_real_entry_lifecycle: {"by_effective_venue": [{"allowed_runtime_apply": false, "canceled_unfilled_cycle_count": 0, "closed_cycle_count": 3, "diagnostic_win_rate": 0.6667, "effective_venue": "KRX", "equal_weight_avg_profit_pct": -0.4767, "filled_cycle_count": 5, "flat_count": 0, "holding_cycle_count": 2, "loss_count": 1, "multi_leg_probe_cycle_count": 1, "realized_pnl_krw_known_count": 0, "realized_pnl_krw_known_sum": 0, "runtime_effect": false, "single_share_plan_closed_winner_count": 2, "submitted_cycle_count": 5, "winner_count": 2}], "by_market_session_bucket": [{"allowed_runtime_apply": false, "canceled_unfilled_cycle_count": 0, "closed_cycle_count": 3, "diagnostic_win_rate": 0.6667, "equal_weight_avg_profit_pct": -0.4767, "filled_cycle_count": 5, "flat_count": 0, "holding_cycle_count": 2, "loss_count": 1, "market_session_bucket": "krx_regular", "multi_leg_probe_cycle_count": 1, "realized_pnl_krw_known_count": 0, "realized_pnl_krw_known_sum": 0, "runtime_effect": false, "single_share_plan_closed_winner_count": 2, "submitted_cycle_count": 5, "winner_count": 2}], "canceled_unfilled_cycle_count": 0, "closed_cycle_count": 3, "diagnostic_win_rate": 0.6667, "equal_weight_avg_profit_pct": -0.4767, "filled_cycle_count": 5, "flat_count": 0, "holding_cycle_count": 2, "loss_count": 1, "multi_leg_probe_cycle_count": 1, "multi_leg_zero_residual_fill_count": 1, "pending_entry_cycle_count": 0, "realized_pnl_krw_known_count": 0, "realized_pnl_krw_known_sum": 0, "realized_pnl_krw_missing_count": 3, "realized_pnl_source_quality_state": "partial_missing_realized_pnl", "single_share_plan_closed_winner_count": 2, "submitted_cycle_count": 5, "venue_source_quality_invalid_count": 0, "venue_source_quality_valid_count": 5, "winner_count": 2}
- real_scale_in_performance: {"active_unrealized_count": 0, "avg_down_execution_count": 0, "by_outcome_cohort": {"avg_down": {"active_unrealized_count": 0, "closed_count": 0, "closed_loss_or_flat_count": 0, "closed_winner_count": 0, "equal_weight_avg_final_position_profit_pct": null, "execution_count": 0, "runtime_apply_authority": false}, "normal_pyramid": {"active_unrealized_count": 0, "closed_count": 0, "closed_loss_or_flat_count": 0, "closed_winner_count": 0, "equal_weight_avg_final_position_profit_pct": null, "execution_count": 0, "runtime_apply_authority": false}, "unknown": {"active_unrealized_count": 0, "closed_count": 0, "closed_loss_or_flat_count": 0, "closed_winner_count": 0, "equal_weight_avg_final_position_profit_pct": null, "execution_count": 0, "runtime_apply_authority": false}, "winner_recovery": {"active_unrealized_count": 0, "closed_count": 0, "closed_loss_or_flat_count": 0, "closed_winner_count": 0, "equal_weight_avg_final_position_profit_pct": null, "execution_count": 0, "runtime_apply_authority": false}}, "closed_count": 0, "completed_outcome_available": false, "execution_count": 0, "normal_pyramid_execution_count": 0, "source_quality_adjusted_ev_available": false, "source_quality_adjusted_ev_unavailable_reason": "no_closed_scale_in_position", "winner_expansion_vs_avg_down_asymmetry_observed": false, "winner_recovery_execution_count": 0, "winner_recovery_qty_cap_invalid_count": 0}
- pyramid_min_profit_pct: 1.1
- pyramid_threshold_source: same_day_unique_runtime_pyramid_evaluation

## Blocker Metrics

- blocker=profit_not_enough sample=6 recovered_rate=0.00 reversal_rate=0.17 blocked_then_recovered_rate=0.00

## Rows

- record_id= code=189330 name=씨이랩 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.7 final=None ai=50.0 tick=0.0 micro_vwap=0.0
- record_id=31480 code=144960 name=뉴파워프라즈마 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=-0.0 final=-4.01 ai=38.0 tick=1.0 micro_vwap=-41.54
- record_id= code=009150 name=삼성전기 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.29 final=None ai=41.0 tick=0.0 micro_vwap=13.24
- record_id= code=119850 name=지엔씨에너지 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.66 final=None ai=46.0 tick=1.0 micro_vwap=-21.05
- record_id= code=402340 name=SK스퀘어 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.13 final=None ai=50.0 tick=0.5 micro_vwap=-2.84
- record_id= code=114190 name=강원에너지 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.93 final=None ai=61.0 tick=0.75 micro_vwap=31.72

## Real Scale-In Performance Rows


## One Share Opportunity Rows

- record_id=31480 code=144960 name=뉴파워프라즈마 label=pyramid_correctly_blocked canonical=expansion_correctly_not_expanded opportunity_seen=False opportunity_profit=None max_profit=0.45 opportunity_cost=0.45 final=-4.01 residual_zero_fill=True residual_soft_abort=False residual_missed_candidate=False post_probe_real_outcome=loss_or_flat_zero_fill_no_confirmation confirmation_ready=False runtime_confirmation_ready=False confirmation_alignment=not_runtime_confirmed recovery_evaluation_seen=True recovery_confirmation_ready=False confirmation_source_quality_blockers=- first_leg_qty=None first_leg_profit_proxy_krw=None

## Whole-Day Real Entry Lifecycle Rows

- record_id=31480 code=144960 name=뉴파워프라즈마 venue=KRX session=krx_regular state=closed planned_qty=21 submitted_qty=1 filled_qty=1 final=-4.01 realized_pnl_krw=None canonical=expansion_correctly_not_expanded
- record_id=31484 code=090460 name=비에이치 venue=KRX session=krx_regular state=closed planned_qty=1 submitted_qty=1 filled_qty=1 final=1.63 realized_pnl_krw=None canonical=None
- record_id=31397 code=093370 name=후성 venue=KRX session=krx_regular state=holding planned_qty=1 submitted_qty=1 filled_qty=1 final=None realized_pnl_krw=None canonical=None
- record_id=31494 code=476060 name=온코닉테라퓨틱스 venue=KRX session=krx_regular state=holding planned_qty=1 submitted_qty=1 filled_qty=1 final=None realized_pnl_krw=None canonical=None
- record_id=31631 code=387690 name=레메디 venue=KRX session=krx_regular state=closed planned_qty=1 submitted_qty=1 filled_qty=1 final=0.95 realized_pnl_krw=None canonical=None

## Normal Winner Expansion Rows

- record_id=31480 code=144960 name=뉴파워프라즈마 label=correctly_not_expanded_or_reversal entry_profit=0.38 incremental_mfe=-0.1603 incremental_final=-4.6034 confirmation=no_directional_confirmation
