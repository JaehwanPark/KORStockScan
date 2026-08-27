# 2026-08-27 Scalping Pyramid Intraday Feedback

- generated_at: 2026-08-27T20:19:57+09:00
- decision_authority: source_only_pyramid_intraday_feedback_no_runtime_mutation
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: intraday_threshold_mutation, intraday_runtime_apply, hard_safety_relaxation, broker_guard_bypass, order_guard_relaxation, stale_quote_bypass, cooldown_bypass, quantity_guard_relaxation, position_cap_release, provider_route_change, bot_restart, real_execution_quality_approval

## Summary

- pyramid_feedback_row_count: 12
- closed_pyramid_row_count: 2
- pyramid_would_have_helped_count: 1
- pyramid_correctly_blocked_count: 1
- pyramid_overheat_or_reversal_risk_count: 0
- pyramid_open_unresolved_count: 10
- one_share_event_count: 1
- one_share_closed_count: 1
- one_share_pyramid_opportunity_count: 1
- one_share_pyramid_missed_upside_count: 1
- one_share_pyramid_missed_upside_rate: 1.00
- one_share_pyramid_avg_opportunity_cost_pct: 0.23
- probe_residual_zero_fill_count: 1
- probe_residual_soft_abort_count: 1
- probe_residual_missed_upside_candidate_count: 0
- probe_residual_pyramid_threshold_missed_upside_candidate_count: 1
- probe_residual_real_outcome_closed_count: 1
- probe_residual_realized_winner_zero_fill_count: 1
- probe_residual_realized_loss_or_flat_zero_fill_count: 0
- probe_residual_realized_winner_confirmation_ready_count: 0
- probe_residual_realized_loss_or_flat_confirmation_ready_count: 0
- post_hard_abort_recovery_evaluation_seen_count: 1
- post_hard_abort_recovery_confirmation_ready_count: 1
- post_terminal_abort_recovery_confirmation_preserved_gap_count: 0
- post_terminal_abort_recovery_ai_supportive_evaluation_count: 2
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
- normal_winner_expansion: {"by_effective_venue": [], "by_market_session_bucket": [], "candidate_count": 1, "closed_candidate_count": 0, "correctly_not_expanded_or_reversal_count": 0, "diagnostic_win_rate": 0.0, "equal_weight_avg_profit_pct": 0.0, "feature_axis_metrics": {"ai_score": [], "blocker_reason": [], "buy_pressure_10t": [], "entry_profit_pct": [], "micro_vwap_side": [], "recovery_ai_parent_prompt_version": [], "recovery_ai_tape_substitution": [], "recovery_ai_thesis_state": [], "recovery_holding_ai_action": [], "recovery_holding_ai_data_quality": [], "tick_acceleration_ratio": []}, "label_counts": [{"count": 1, "label": "source_quality_blocked"}], "notional_weighted_ev_pct": 0.0, "probe_confirmation_signature_metrics": [], "realized_incremental_winner_count": 0, "source_quality_blocked_candidate_count": 1, "source_quality_valid_candidate_count": 0, "temporal_inversion_candidate_count": 0, "transient_extension_exit_timing_needed_count": 0, "venue_source_quality_blocked_closed_count": 0, "venue_source_quality_valid_closed_count": 0}
- whole_day_real_entry_lifecycle: {"by_effective_venue": [{"allowed_runtime_apply": false, "canceled_unfilled_cycle_count": 3, "closed_cycle_count": 2, "diagnostic_win_rate": 1.0, "effective_venue": "KRX", "equal_weight_avg_profit_pct": 0.94, "filled_cycle_count": 2, "flat_count": 0, "holding_cycle_count": 0, "loss_count": 0, "multi_leg_probe_cycle_count": 1, "realized_pnl_krw_known_count": 2, "realized_pnl_krw_known_sum": 1471, "runtime_effect": false, "single_share_plan_closed_winner_count": 1, "submitted_cycle_count": 5, "winner_count": 2}], "by_market_session_bucket": [{"allowed_runtime_apply": false, "canceled_unfilled_cycle_count": 3, "closed_cycle_count": 2, "diagnostic_win_rate": 1.0, "equal_weight_avg_profit_pct": 0.94, "filled_cycle_count": 2, "flat_count": 0, "holding_cycle_count": 0, "loss_count": 0, "market_session_bucket": "krx_regular", "multi_leg_probe_cycle_count": 1, "realized_pnl_krw_known_count": 2, "realized_pnl_krw_known_sum": 1471, "runtime_effect": false, "single_share_plan_closed_winner_count": 1, "submitted_cycle_count": 5, "winner_count": 2}], "canceled_unfilled_cycle_count": 3, "closed_cycle_count": 2, "diagnostic_win_rate": 1.0, "equal_weight_avg_profit_pct": 0.94, "filled_cycle_count": 2, "flat_count": 0, "holding_cycle_count": 0, "loss_count": 0, "multi_leg_probe_cycle_count": 1, "multi_leg_zero_residual_fill_count": 1, "pending_entry_cycle_count": 0, "realized_pnl_krw_known_count": 2, "realized_pnl_krw_known_sum": 1471, "realized_pnl_krw_missing_count": 0, "realized_pnl_krw_source_counts": [{"count": 2, "source": "broker_fill_prices_fee_aware"}], "realized_pnl_source_quality_state": "complete", "single_share_plan_closed_winner_count": 1, "submitted_cycle_count": 5, "venue_source_quality_invalid_count": 0, "venue_source_quality_valid_count": 5, "winner_count": 2}
- real_scale_in_performance: {"active_unrealized_count": 0, "avg_down_execution_count": 0, "by_outcome_cohort": {"avg_down": {"active_unrealized_count": 0, "closed_count": 0, "closed_loss_or_flat_count": 0, "closed_winner_count": 0, "equal_weight_avg_final_position_profit_pct": null, "equal_weight_avg_scale_in_leg_net_return_pct": null, "execution_count": 0, "runtime_apply_authority": false, "scale_in_leg_diagnostic_win_rate": null, "scale_in_leg_net_pnl_proxy_krw_sum": null, "source_quality_adjusted_ev_pct": null, "source_quality_blocked_closed_count": 0, "source_quality_valid_closed_count": 0}, "normal_pyramid": {"active_unrealized_count": 0, "closed_count": 0, "closed_loss_or_flat_count": 0, "closed_winner_count": 0, "equal_weight_avg_final_position_profit_pct": null, "equal_weight_avg_scale_in_leg_net_return_pct": null, "execution_count": 0, "runtime_apply_authority": false, "scale_in_leg_diagnostic_win_rate": null, "scale_in_leg_net_pnl_proxy_krw_sum": null, "source_quality_adjusted_ev_pct": null, "source_quality_blocked_closed_count": 0, "source_quality_valid_closed_count": 0}, "unknown": {"active_unrealized_count": 0, "closed_count": 0, "closed_loss_or_flat_count": 0, "closed_winner_count": 0, "equal_weight_avg_final_position_profit_pct": null, "equal_weight_avg_scale_in_leg_net_return_pct": null, "execution_count": 0, "runtime_apply_authority": false, "scale_in_leg_diagnostic_win_rate": null, "scale_in_leg_net_pnl_proxy_krw_sum": null, "source_quality_adjusted_ev_pct": null, "source_quality_blocked_closed_count": 0, "source_quality_valid_closed_count": 0}, "winner_recovery": {"active_unrealized_count": 0, "closed_count": 0, "closed_loss_or_flat_count": 0, "closed_winner_count": 0, "equal_weight_avg_final_position_profit_pct": null, "equal_weight_avg_scale_in_leg_net_return_pct": null, "execution_count": 0, "runtime_apply_authority": false, "scale_in_leg_diagnostic_win_rate": null, "scale_in_leg_net_pnl_proxy_krw_sum": null, "source_quality_adjusted_ev_pct": null, "source_quality_blocked_closed_count": 0, "source_quality_valid_closed_count": 0}}, "closed_count": 0, "completed_outcome_available": false, "equal_weight_avg_scale_in_leg_net_return_pct": null, "execution_count": 0, "normal_pyramid_execution_count": 0, "scale_in_leg_diagnostic_win_rate": null, "scale_in_leg_net_pnl_proxy_krw_sum": null, "source_quality_adjusted_ev_available": false, "source_quality_adjusted_ev_pct": null, "source_quality_adjusted_ev_unavailable_reason": "no_closed_scale_in_position", "source_quality_blocked_closed_count": 0, "source_quality_valid_closed_count": 0, "winner_expansion_vs_avg_down_asymmetry_observed": false, "winner_recovery_by_ai_parent_prompt_version": [], "winner_recovery_by_ai_thesis_state": [], "winner_recovery_by_holding_ai_action": [], "winner_recovery_by_holding_ai_data_quality": [], "winner_recovery_execution_count": 0, "winner_recovery_qty_cap_invalid_count": 0}
- pyramid_min_profit_pct: 1.1
- pyramid_threshold_source: same_day_unique_runtime_pyramid_evaluation

## Blocker Metrics

- blocker=profit_not_enough sample=7 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=pyramid_hard_blocked:buy_pressure_severe_below_min,large_sell_detected sample=1 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=pyramid_hard_blocked:micro_vwap_severe_overheated,fresh_micro_confirmation_missing sample=2 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=rising_missed_scout_pyramid_bridge_blocked:profit_not_enough sample=1 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=rising_missed_scout_pyramid_bridge_blocked:profit_not_enough,micro_context_stale,tick_aggressor_pressure_unusable,fresh_micro_confirmation_missing,tick_accel_stale sample=1 recovered_rate=1.00 reversal_rate=0.00 blocked_then_recovered_rate=1.00

## Rows

- record_id= code=078600 name=대주전자재료 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.65 final=None ai=50.0 tick=0.75 micro_vwap=38.59
- record_id= code=247540 name=에코프로비엠 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.29 final=None ai=49.0 tick=0.667 micro_vwap=38.07
- record_id= code=086520 name=에코프로 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.87 final=None ai=50.0 tick=0.5 micro_vwap=53.17
- record_id= code=107640 name=한중엔시에스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.78 final=None ai=66.0 tick=0.333 micro_vwap=36.85
- record_id= code=049080 name=기가레인 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.77 final=None ai=50.0 tick=1.667 micro_vwap=-58.88
- record_id=36427 code=062040 name=산일전기 label=pyramid_correctly_blocked blocker=rising_missed_scout_pyramid_bridge_blocked:profit_not_enough profit=0.55 final=0.65 ai=50.0 tick=1.5 micro_vwap=16.43
- record_id= code=043200 name=파루 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.46 final=None ai=57.0 tick=0.333 micro_vwap=76.34
- record_id=36518 code=950260 name=인제니아테라퓨틱스(Reg.S) label=pyramid_would_have_helped blocker=rising_missed_scout_pyramid_bridge_blocked:profit_not_enough,micro_context_stale,tick_aggressor_pressure_unusable,fresh_micro_confirmation_missing,tick_accel_stale profit=0.11 final=1.23 ai=57.0 tick=0.0 micro_vwap=92.1
- record_id= code=272210 name=한화시스템 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.42 final=None ai=50.0 tick=5.5 micro_vwap=16.45
- record_id= code=302430 name=이노메트리 label=pyramid_open_unresolved blocker=pyramid_hard_blocked:micro_vwap_severe_overheated,fresh_micro_confirmation_missing profit=1.8 final=None ai=56.0 tick=0.0 micro_vwap=174.52
- record_id= code=441270 name=파인엠텍 label=pyramid_open_unresolved blocker=pyramid_hard_blocked:buy_pressure_severe_below_min,large_sell_detected profit=2.96 final=None ai=50.0 tick=1.0 micro_vwap=57.33
- record_id= code=000500 name=가온전선 label=pyramid_open_unresolved blocker=pyramid_hard_blocked:micro_vwap_severe_overheated,fresh_micro_confirmation_missing profit=2.62 final=None ai=49.0 tick=0.0 micro_vwap=157.96

## Real Scale-In Performance Rows


## One Share Opportunity Rows

- record_id=36518 code=950260 name=인제니아테라퓨틱스(Reg.S) label=pyramid_would_have_helped canonical=expansion_correctly_not_expanded_no_confirmation opportunity_seen=True opportunity_profit=1.45 max_profit=1.68 opportunity_cost=0.23 final=1.23 residual_zero_fill=True residual_soft_abort=True residual_missed_candidate=False post_probe_real_outcome=profitable_zero_fill_no_confirmation confirmation_ready=False runtime_confirmation_ready=False confirmation_alignment=not_runtime_confirmed recovery_evaluation_seen=True recovery_confirmation_ready=True confirmation_source_quality_blockers=tick_context_not_fresh first_leg_qty=None first_leg_profit_proxy_krw=None

## Whole-Day Real Entry Lifecycle Rows

- record_id=36587 code=006220 name=제주은행 venue=KRX session=krx_regular state=canceled_unfilled planned_qty=1 submitted_qty=1 filled_qty=0 final=None realized_pnl_krw=None realized_pnl_source=None canonical=None
- record_id=36411 code=488280 name=에스투더블유 venue=KRX session=krx_regular state=canceled_unfilled planned_qty=1 submitted_qty=1 filled_qty=0 final=None realized_pnl_krw=None realized_pnl_source=None canonical=None
- record_id=36411 code=488280 name=에스투더블유 venue=KRX session=krx_regular state=canceled_unfilled planned_qty=1 submitted_qty=1 filled_qty=0 final=None realized_pnl_krw=None realized_pnl_source=None canonical=None
- record_id=36427 code=062040 name=산일전기 venue=KRX session=krx_regular state=closed planned_qty=1 submitted_qty=1 filled_qty=1 final=0.65 realized_pnl_krw=1252 realized_pnl_source=broker_fill_prices_fee_aware canonical=None
- record_id=36518 code=950260 name=인제니아테라퓨틱스(Reg.S) venue=KRX session=krx_regular state=closed planned_qty=12 submitted_qty=1 filled_qty=1 final=1.23 realized_pnl_krw=219 realized_pnl_source=broker_fill_prices_fee_aware canonical=expansion_correctly_not_expanded_no_confirmation

## Normal Winner Expansion Rows

- record_id=36518 code=950260 name=인제니아테라퓨틱스(Reg.S) label=source_quality_blocked entry_profit=0.11 incremental_mfe=1.3383 incremental_final=0.8888 confirmation=None
