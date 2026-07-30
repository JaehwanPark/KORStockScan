# 2026-07-30 Scalping Pyramid Intraday Feedback

- generated_at: 2026-07-30T21:01:48+09:00
- decision_authority: source_only_pyramid_intraday_feedback_no_runtime_mutation
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: intraday_threshold_mutation, intraday_runtime_apply, hard_safety_relaxation, broker_guard_bypass, order_guard_relaxation, stale_quote_bypass, cooldown_bypass, quantity_guard_relaxation, position_cap_release, provider_route_change, bot_restart, real_execution_quality_approval

## Summary

- pyramid_feedback_row_count: 1
- closed_pyramid_row_count: 0
- pyramid_would_have_helped_count: 0
- pyramid_correctly_blocked_count: 0
- pyramid_overheat_or_reversal_risk_count: 0
- pyramid_open_unresolved_count: 1
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
- probe_residual_real_outcome_closed_count: 0
- probe_residual_realized_winner_zero_fill_count: 0
- probe_residual_realized_loss_or_flat_zero_fill_count: 0
- probe_residual_realized_winner_confirmation_ready_count: 0
- probe_residual_realized_loss_or_flat_confirmation_ready_count: 0
- canonical_expansion_missed_upside_count: 0
- post_probe_legacy_label_conflict_count: 0
- post_probe_confirmation_false_positive_loss_or_flat_count: 0
- probe_residual_confirmation_ready_equal_weight_avg_profit_pct: 0.0000
- probe_residual_confirmation_ready_notional_weighted_ev_pct: 0.0000
- probe_residual_confirmation_ready_simple_sum_profit_proxy_krw: 0.00
- probe_residual_pyramid_evaluation_seen_count: 0
- normal_winner_expansion: {"by_effective_venue": [], "by_market_session_bucket": [], "candidate_count": 0, "closed_candidate_count": 0, "correctly_not_expanded_or_reversal_count": 0, "diagnostic_win_rate": 0.0, "equal_weight_avg_profit_pct": 0.0, "feature_axis_metrics": {"ai_score": [], "blocker_reason": [], "buy_pressure_10t": [], "entry_profit_pct": [], "micro_vwap_side": [], "tick_acceleration_ratio": []}, "label_counts": [], "notional_weighted_ev_pct": 0.0, "probe_confirmation_signature_metrics": [], "realized_incremental_winner_count": 0, "source_quality_blocked_candidate_count": 0, "source_quality_valid_candidate_count": 0, "temporal_inversion_candidate_count": 0, "transient_extension_exit_timing_needed_count": 0, "venue_source_quality_blocked_closed_count": 0, "venue_source_quality_valid_closed_count": 0}
- whole_day_real_entry_lifecycle: {"by_effective_venue": [{"allowed_runtime_apply": false, "canceled_unfilled_cycle_count": 1, "closed_cycle_count": 0, "diagnostic_win_rate": 0.0, "effective_venue": "NXT", "equal_weight_avg_profit_pct": 0.0, "filled_cycle_count": 0, "flat_count": 0, "holding_cycle_count": 0, "loss_count": 0, "multi_leg_probe_cycle_count": 0, "realized_pnl_krw_known_count": 0, "realized_pnl_krw_known_sum": 0, "runtime_effect": false, "single_share_plan_closed_winner_count": 0, "submitted_cycle_count": 1, "winner_count": 0}, {"allowed_runtime_apply": false, "canceled_unfilled_cycle_count": 0, "closed_cycle_count": 1, "diagnostic_win_rate": 0.0, "effective_venue": "PREMARKET_KRX_LIKE", "equal_weight_avg_profit_pct": -5.19, "filled_cycle_count": 1, "flat_count": 0, "holding_cycle_count": 0, "loss_count": 1, "multi_leg_probe_cycle_count": 1, "realized_pnl_krw_known_count": 0, "realized_pnl_krw_known_sum": 0, "runtime_effect": false, "single_share_plan_closed_winner_count": 0, "submitted_cycle_count": 1, "winner_count": 0}], "by_market_session_bucket": [{"allowed_runtime_apply": false, "canceled_unfilled_cycle_count": 0, "closed_cycle_count": 1, "diagnostic_win_rate": 0.0, "equal_weight_avg_profit_pct": -5.19, "filled_cycle_count": 1, "flat_count": 0, "holding_cycle_count": 0, "loss_count": 1, "market_session_bucket": "krx_like_premarket", "multi_leg_probe_cycle_count": 1, "realized_pnl_krw_known_count": 0, "realized_pnl_krw_known_sum": 0, "runtime_effect": false, "single_share_plan_closed_winner_count": 0, "submitted_cycle_count": 1, "winner_count": 0}, {"allowed_runtime_apply": false, "canceled_unfilled_cycle_count": 1, "closed_cycle_count": 0, "diagnostic_win_rate": 0.0, "equal_weight_avg_profit_pct": 0.0, "filled_cycle_count": 0, "flat_count": 0, "holding_cycle_count": 0, "loss_count": 0, "market_session_bucket": "nxt_entry_window", "multi_leg_probe_cycle_count": 0, "realized_pnl_krw_known_count": 0, "realized_pnl_krw_known_sum": 0, "runtime_effect": false, "single_share_plan_closed_winner_count": 0, "submitted_cycle_count": 1, "winner_count": 0}], "canceled_unfilled_cycle_count": 1, "closed_cycle_count": 1, "diagnostic_win_rate": 0.0, "equal_weight_avg_profit_pct": -5.19, "filled_cycle_count": 1, "flat_count": 0, "holding_cycle_count": 0, "loss_count": 1, "multi_leg_probe_cycle_count": 1, "multi_leg_zero_residual_fill_count": 1, "pending_entry_cycle_count": 0, "realized_pnl_krw_known_count": 0, "realized_pnl_krw_known_sum": 0, "realized_pnl_krw_missing_count": 1, "realized_pnl_source_quality_state": "partial_missing_realized_pnl", "single_share_plan_closed_winner_count": 0, "submitted_cycle_count": 2, "venue_source_quality_invalid_count": 0, "venue_source_quality_valid_count": 2, "winner_count": 0}
- pyramid_min_profit_pct: 1.1
- pyramid_threshold_source: same_day_unique_runtime_pyramid_evaluation

## Blocker Metrics

- blocker=profit_not_enough sample=1 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00

## Rows

- record_id= code=138040 name=메리츠금융지주 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.66 final=None ai=50.0 tick=0.0 micro_vwap=-27.15

## One Share Opportunity Rows

- record_id=25173 code=119850 name=지엔씨에너지 label=pyramid_correctly_blocked canonical=expansion_source_quality_blocked opportunity_seen=False opportunity_profit=None max_profit=-0.23 opportunity_cost=0.0 final=-5.19 residual_zero_fill=True residual_soft_abort=True residual_missed_candidate=False post_probe_real_outcome=source_quality_blocked confirmation_ready=False first_leg_qty=1 first_leg_profit_proxy_krw=-1564.79

## Whole-Day Real Entry Lifecycle Rows

- record_id=25173 code=119850 name=지엔씨에너지 venue=PREMARKET_KRX_LIKE session=krx_like_premarket state=closed planned_qty=4 submitted_qty=1 filled_qty=1 final=-5.19 realized_pnl_krw=None canonical=expansion_source_quality_blocked
- record_id=25183 code=042700 name=한미반도체 venue=NXT session=nxt_entry_window state=canceled_unfilled planned_qty=1 submitted_qty=1 filled_qty=0 final=None realized_pnl_krw=None canonical=None

## Normal Winner Expansion Rows
