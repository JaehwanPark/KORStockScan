# 2026-07-27 Scalping Pyramid Intraday Feedback

- generated_at: 2026-07-27T21:46:12+09:00
- decision_authority: source_only_pyramid_intraday_feedback_no_runtime_mutation
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: intraday_threshold_mutation, intraday_runtime_apply, hard_safety_relaxation, broker_guard_bypass, order_guard_relaxation, stale_quote_bypass, cooldown_bypass, quantity_guard_relaxation, position_cap_release, provider_route_change, bot_restart, real_execution_quality_approval

## Summary

- pyramid_feedback_row_count: 1
- closed_pyramid_row_count: 1
- pyramid_would_have_helped_count: 0
- pyramid_correctly_blocked_count: 1
- pyramid_overheat_or_reversal_risk_count: 0
- pyramid_open_unresolved_count: 0
- one_share_event_count: 2
- one_share_closed_count: 2
- one_share_pyramid_opportunity_count: 1
- one_share_pyramid_missed_upside_count: 0
- one_share_pyramid_missed_upside_rate: 0.00
- one_share_pyramid_avg_opportunity_cost_pct: 0.00
- probe_residual_zero_fill_count: 2
- probe_residual_soft_abort_count: 0
- probe_residual_missed_upside_candidate_count: 1
- probe_residual_pyramid_evaluation_seen_count: 1
- normal_winner_expansion: {"by_effective_venue": [], "by_market_session_bucket": [], "candidate_count": 1, "closed_candidate_count": 0, "correctly_not_expanded_or_reversal_count": 0, "diagnostic_win_rate": 0.0, "equal_weight_avg_profit_pct": 0.0, "feature_axis_metrics": {"ai_score": [], "blocker_reason": [], "buy_pressure_10t": [], "entry_profit_pct": [], "micro_vwap_side": [], "tick_acceleration_ratio": []}, "label_counts": [{"count": 1, "label": "source_quality_blocked"}], "notional_weighted_ev_pct": 0.0, "probe_confirmation_signature_metrics": [], "realized_incremental_winner_count": 0, "source_quality_blocked_candidate_count": 1, "source_quality_valid_candidate_count": 0, "transient_extension_exit_timing_needed_count": 0, "venue_source_quality_blocked_closed_count": 0, "venue_source_quality_valid_closed_count": 0}
- pyramid_min_profit_pct: 1.1
- pyramid_threshold_source: same_day_unique_runtime_pyramid_evaluation

## Blocker Metrics

- blocker=profit_not_enough sample=1 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00

## Rows

- record_id=24195 code=010120 name=LS ELECTRIC label=pyramid_correctly_blocked blocker=profit_not_enough profit=0.58 final=0.63 ai=50.0 tick=1.0 micro_vwap=22.51

## One Share Opportunity Rows

- record_id=24195 code=010120 name=LS ELECTRIC label=pyramid_correctly_blocked opportunity_seen=True opportunity_profit=1.13 max_profit=1.13 opportunity_cost=0.0 final=0.63 residual_zero_fill=True residual_soft_abort=False residual_missed_candidate=True
- record_id=24492 code=439090 name=마녀공장 label=pyramid_correctly_blocked opportunity_seen=False opportunity_profit=None max_profit=0.33 opportunity_cost=0.33 final=-0.11 residual_zero_fill=True residual_soft_abort=False residual_missed_candidate=False

## Normal Winner Expansion Rows

- record_id=24195 code=010120 name=LS ELECTRIC label=source_quality_blocked entry_profit=0.07 incremental_mfe=0.8293 incremental_final=0.3296 confirmation=None
