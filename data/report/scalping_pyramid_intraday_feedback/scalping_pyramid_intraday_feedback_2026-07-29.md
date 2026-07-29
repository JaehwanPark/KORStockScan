# 2026-07-29 Scalping Pyramid Intraday Feedback

- generated_at: 2026-07-29T22:05:24+09:00
- decision_authority: source_only_pyramid_intraday_feedback_no_runtime_mutation
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: intraday_threshold_mutation, intraday_runtime_apply, hard_safety_relaxation, broker_guard_bypass, order_guard_relaxation, stale_quote_bypass, cooldown_bypass, quantity_guard_relaxation, position_cap_release, provider_route_change, bot_restart, real_execution_quality_approval

## Summary

- pyramid_feedback_row_count: 3
- closed_pyramid_row_count: 2
- pyramid_would_have_helped_count: 0
- pyramid_correctly_blocked_count: 0
- pyramid_overheat_or_reversal_risk_count: 2
- pyramid_open_unresolved_count: 1
- one_share_event_count: 4
- one_share_closed_count: 3
- one_share_pyramid_opportunity_count: 0
- one_share_pyramid_missed_upside_count: 0
- one_share_pyramid_missed_upside_rate: 0.00
- one_share_pyramid_avg_opportunity_cost_pct: 0.00
- probe_residual_zero_fill_count: 4
- probe_residual_soft_abort_count: 3
- probe_residual_missed_upside_candidate_count: 1
- probe_residual_pyramid_threshold_missed_upside_candidate_count: 0
- probe_residual_real_outcome_closed_count: 3
- probe_residual_realized_winner_zero_fill_count: 1
- probe_residual_realized_loss_or_flat_zero_fill_count: 2
- probe_residual_realized_winner_confirmation_ready_count: 1
- probe_residual_realized_loss_or_flat_confirmation_ready_count: 0
- canonical_expansion_missed_upside_count: 1
- post_probe_legacy_label_conflict_count: 1
- post_probe_confirmation_false_positive_loss_or_flat_count: 0
- probe_residual_confirmation_ready_equal_weight_avg_profit_pct: 0.2700
- probe_residual_confirmation_ready_notional_weighted_ev_pct: 0.2700
- probe_residual_confirmation_ready_simple_sum_profit_proxy_krw: 130.46
- probe_residual_pyramid_evaluation_seen_count: 0
- normal_winner_expansion: {"by_effective_venue": [], "by_market_session_bucket": [], "candidate_count": 0, "closed_candidate_count": 0, "correctly_not_expanded_or_reversal_count": 0, "diagnostic_win_rate": 0.0, "equal_weight_avg_profit_pct": 0.0, "feature_axis_metrics": {"ai_score": [], "blocker_reason": [], "buy_pressure_10t": [], "entry_profit_pct": [], "micro_vwap_side": [], "tick_acceleration_ratio": []}, "label_counts": [], "notional_weighted_ev_pct": 0.0, "probe_confirmation_signature_metrics": [], "realized_incremental_winner_count": 0, "source_quality_blocked_candidate_count": 0, "source_quality_valid_candidate_count": 0, "temporal_inversion_candidate_count": 0, "transient_extension_exit_timing_needed_count": 0, "venue_source_quality_blocked_closed_count": 0, "venue_source_quality_valid_closed_count": 0}
- whole_day_real_entry_lifecycle: {"by_effective_venue": [{"allowed_runtime_apply": false, "canceled_unfilled_cycle_count": 0, "closed_cycle_count": 1, "diagnostic_win_rate": 0.0, "effective_venue": "KRX", "equal_weight_avg_profit_pct": -0.23, "filled_cycle_count": 1, "flat_count": 0, "holding_cycle_count": 0, "loss_count": 1, "multi_leg_probe_cycle_count": 1, "realized_pnl_krw_known_count": 0, "realized_pnl_krw_known_sum": 0, "runtime_effect": false, "single_share_plan_closed_winner_count": 0, "submitted_cycle_count": 1, "winner_count": 0}, {"allowed_runtime_apply": false, "canceled_unfilled_cycle_count": 2, "closed_cycle_count": 1, "diagnostic_win_rate": 1.0, "effective_venue": "NXT", "equal_weight_avg_profit_pct": 0.27, "filled_cycle_count": 2, "flat_count": 0, "holding_cycle_count": 1, "loss_count": 0, "multi_leg_probe_cycle_count": 2, "realized_pnl_krw_known_count": 1, "realized_pnl_krw_known_sum": 16, "runtime_effect": false, "single_share_plan_closed_winner_count": 0, "submitted_cycle_count": 4, "winner_count": 1}, {"allowed_runtime_apply": false, "canceled_unfilled_cycle_count": 2, "closed_cycle_count": 3, "diagnostic_win_rate": 0.6667, "effective_venue": "PREMARKET_KRX_LIKE", "equal_weight_avg_profit_pct": -1.0, "filled_cycle_count": 3, "flat_count": 0, "holding_cycle_count": 0, "loss_count": 1, "multi_leg_probe_cycle_count": 1, "realized_pnl_krw_known_count": 0, "realized_pnl_krw_known_sum": 0, "runtime_effect": false, "single_share_plan_closed_winner_count": 2, "submitted_cycle_count": 5, "winner_count": 2}], "by_market_session_bucket": [{"allowed_runtime_apply": false, "canceled_unfilled_cycle_count": 2, "closed_cycle_count": 3, "diagnostic_win_rate": 0.6667, "equal_weight_avg_profit_pct": -1.0, "filled_cycle_count": 3, "flat_count": 0, "holding_cycle_count": 0, "loss_count": 1, "market_session_bucket": "krx_like_premarket", "multi_leg_probe_cycle_count": 1, "realized_pnl_krw_known_count": 0, "realized_pnl_krw_known_sum": 0, "runtime_effect": false, "single_share_plan_closed_winner_count": 2, "submitted_cycle_count": 5, "winner_count": 2}, {"allowed_runtime_apply": false, "canceled_unfilled_cycle_count": 0, "closed_cycle_count": 1, "diagnostic_win_rate": 0.0, "equal_weight_avg_profit_pct": -0.23, "filled_cycle_count": 1, "flat_count": 0, "holding_cycle_count": 0, "loss_count": 1, "market_session_bucket": "krx_regular", "multi_leg_probe_cycle_count": 1, "realized_pnl_krw_known_count": 0, "realized_pnl_krw_known_sum": 0, "runtime_effect": false, "single_share_plan_closed_winner_count": 0, "submitted_cycle_count": 1, "winner_count": 0}, {"allowed_runtime_apply": false, "canceled_unfilled_cycle_count": 0, "closed_cycle_count": 1, "diagnostic_win_rate": 1.0, "equal_weight_avg_profit_pct": 0.27, "filled_cycle_count": 2, "flat_count": 0, "holding_cycle_count": 1, "loss_count": 0, "market_session_bucket": "nxt", "multi_leg_probe_cycle_count": 2, "realized_pnl_krw_known_count": 1, "realized_pnl_krw_known_sum": 16, "runtime_effect": false, "single_share_plan_closed_winner_count": 0, "submitted_cycle_count": 2, "winner_count": 1}, {"allowed_runtime_apply": false, "canceled_unfilled_cycle_count": 2, "closed_cycle_count": 0, "diagnostic_win_rate": 0.0, "equal_weight_avg_profit_pct": 0.0, "filled_cycle_count": 0, "flat_count": 0, "holding_cycle_count": 0, "loss_count": 0, "market_session_bucket": "nxt_entry_window", "multi_leg_probe_cycle_count": 0, "realized_pnl_krw_known_count": 0, "realized_pnl_krw_known_sum": 0, "runtime_effect": false, "single_share_plan_closed_winner_count": 0, "submitted_cycle_count": 2, "winner_count": 0}], "canceled_unfilled_cycle_count": 4, "closed_cycle_count": 5, "diagnostic_win_rate": 0.6, "equal_weight_avg_profit_pct": -0.592, "filled_cycle_count": 6, "flat_count": 0, "holding_cycle_count": 1, "loss_count": 2, "multi_leg_probe_cycle_count": 4, "multi_leg_zero_residual_fill_count": 4, "pending_entry_cycle_count": 0, "realized_pnl_krw_known_count": 1, "realized_pnl_krw_known_sum": 16, "realized_pnl_krw_missing_count": 4, "realized_pnl_source_quality_state": "partial_missing_realized_pnl", "single_share_plan_closed_winner_count": 2, "submitted_cycle_count": 10, "venue_source_quality_invalid_count": 0, "venue_source_quality_valid_count": 10, "winner_count": 3}
- pyramid_min_profit_pct: 1.1
- pyramid_threshold_source: same_day_unique_runtime_pyramid_evaluation

## Blocker Metrics

- blocker=profit_not_enough sample=1 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=rising_missed_scout_pyramid_bridge_blocked:profit_not_enough sample=2 recovered_rate=0.00 reversal_rate=1.00 blocked_then_recovered_rate=0.00

## Rows

- record_id=24983 code=095610 name=테스 label=pyramid_overheat_or_reversal_risk blocker=rising_missed_scout_pyramid_bridge_blocked:profit_not_enough profit=0.43 final=0.43 ai=51.0 tick=3.0 micro_vwap=62.41
- record_id=24975 code=035420 name=NAVER label=pyramid_overheat_or_reversal_risk blocker=rising_missed_scout_pyramid_bridge_blocked:profit_not_enough profit=0.48 final=0.24 ai=72.0 tick=1.0 micro_vwap=12.12
- record_id= code=090430 name=아모레퍼시픽 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.33 final=None ai=50.0 tick=0.0 micro_vwap=-16.22

## One Share Opportunity Rows

- record_id=24963 code=270660 name=에브리봇 label=pyramid_correctly_blocked canonical=expansion_correctly_not_expanded opportunity_seen=False opportunity_profit=None max_profit=-0.15 opportunity_cost=0.0 final=-3.67 residual_zero_fill=True residual_soft_abort=True residual_missed_candidate=False post_probe_real_outcome=loss_or_flat_zero_fill_no_confirmation confirmation_ready=False first_leg_qty=2 first_leg_profit_proxy_krw=-937.32
- record_id=25063 code=475040 name=스트라드비젼 label=pyramid_correctly_blocked canonical=expansion_correctly_not_expanded opportunity_seen=False opportunity_profit=None max_profit=0.94 opportunity_cost=0.94 final=-0.23 residual_zero_fill=True residual_soft_abort=True residual_missed_candidate=False post_probe_real_outcome=loss_or_flat_zero_fill_no_confirmation confirmation_ready=False first_leg_qty=17 first_leg_profit_proxy_krw=-116.91
- record_id=25106 code=073240 name=금호타이어 label=pyramid_correctly_blocked canonical=expansion_missed_upside_confirmation_ready opportunity_seen=False opportunity_profit=None max_profit=0.76 opportunity_cost=0.76 final=0.27 residual_zero_fill=True residual_soft_abort=False residual_missed_candidate=True post_probe_real_outcome=profitable_zero_fill_confirmation_ready confirmation_ready=True first_leg_qty=8 first_leg_profit_proxy_krw=130.46
- record_id=24980 code=034020 name=두산에너빌리티 label=pyramid_open_unresolved canonical=expansion_source_quality_blocked opportunity_seen=False opportunity_profit=None max_profit=0.1 opportunity_cost=0.1 final=None residual_zero_fill=True residual_soft_abort=True residual_missed_candidate=False post_probe_real_outcome=source_quality_blocked confirmation_ready=False first_leg_qty=1 first_leg_profit_proxy_krw=None

## Whole-Day Real Entry Lifecycle Rows

- record_id=24973 code=017670 name=SK텔레콤 venue=PREMARKET_KRX_LIKE session=krx_like_premarket state=canceled_unfilled planned_qty=1 submitted_qty=1 filled_qty=0 final=None realized_pnl_krw=None canonical=None
- record_id=24975 code=035420 name=NAVER venue=PREMARKET_KRX_LIKE session=krx_like_premarket state=closed planned_qty=1 submitted_qty=1 filled_qty=1 final=0.24 realized_pnl_krw=None canonical=None
- record_id=24983 code=095610 name=테스 venue=PREMARKET_KRX_LIKE session=krx_like_premarket state=closed planned_qty=1 submitted_qty=1 filled_qty=1 final=0.43 realized_pnl_krw=None canonical=None
- record_id=24963 code=270660 name=에브리봇 venue=PREMARKET_KRX_LIKE session=krx_like_premarket state=closed planned_qty=7 submitted_qty=1 filled_qty=1 final=-3.67 realized_pnl_krw=None canonical=expansion_correctly_not_expanded
- record_id=24990 code=108490 name=로보티즈 venue=PREMARKET_KRX_LIKE session=krx_like_premarket state=canceled_unfilled planned_qty=1 submitted_qty=1 filled_qty=0 final=None realized_pnl_krw=None canonical=None
- record_id=25063 code=475040 name=스트라드비젼 venue=KRX session=krx_regular state=closed planned_qty=43 submitted_qty=1 filled_qty=1 final=-0.23 realized_pnl_krw=None canonical=expansion_correctly_not_expanded
- record_id=25106 code=073240 name=금호타이어 venue=NXT session=nxt state=closed planned_qty=21 submitted_qty=1 filled_qty=1 final=0.27 realized_pnl_krw=16 canonical=expansion_missed_upside_confirmation_ready
- record_id=24997 code=035420 name=NAVER venue=NXT session=nxt_entry_window state=canceled_unfilled planned_qty=1 submitted_qty=1 filled_qty=0 final=None realized_pnl_krw=None canonical=None
- record_id=25098 code=066570 name=LG전자 venue=NXT session=nxt_entry_window state=canceled_unfilled planned_qty=1 submitted_qty=1 filled_qty=0 final=None realized_pnl_krw=None canonical=None
- record_id=24980 code=034020 name=두산에너빌리티 venue=NXT session=nxt state=holding planned_qty=2 submitted_qty=1 filled_qty=1 final=None realized_pnl_krw=None canonical=expansion_source_quality_blocked

## Normal Winner Expansion Rows
