# 2026-07-28 Scalping Pyramid Intraday Feedback

- generated_at: 2026-07-28T21:44:58+09:00
- decision_authority: source_only_pyramid_intraday_feedback_no_runtime_mutation
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: intraday_threshold_mutation, intraday_runtime_apply, hard_safety_relaxation, broker_guard_bypass, order_guard_relaxation, stale_quote_bypass, cooldown_bypass, quantity_guard_relaxation, position_cap_release, provider_route_change, bot_restart, real_execution_quality_approval

## Summary

- pyramid_feedback_row_count: 2
- closed_pyramid_row_count: 2
- pyramid_would_have_helped_count: 0
- pyramid_correctly_blocked_count: 0
- pyramid_overheat_or_reversal_risk_count: 2
- pyramid_open_unresolved_count: 0
- one_share_event_count: 11
- one_share_closed_count: 11
- one_share_pyramid_opportunity_count: 4
- one_share_pyramid_missed_upside_count: 3
- one_share_pyramid_missed_upside_rate: 0.27
- one_share_pyramid_avg_opportunity_cost_pct: 0.24
- probe_residual_zero_fill_count: 10
- probe_residual_soft_abort_count: 0
- probe_residual_missed_upside_candidate_count: 3
- probe_residual_pyramid_evaluation_seen_count: 3
- normal_winner_expansion: {"by_effective_venue": [{"allowed_runtime_apply": false, "effective_venue": "KRX", "notional_weighted_ev_pct": -0.3, "realized_incremental_winner_count": 0, "runtime_effect": false, "sample_count": 1}, {"allowed_runtime_apply": false, "effective_venue": "PREMARKET_KRX_LIKE", "notional_weighted_ev_pct": -3.4867, "realized_incremental_winner_count": 0, "runtime_effect": false, "sample_count": 1}], "by_market_session_bucket": [{"allowed_runtime_apply": false, "market_session_bucket": "krx_like_premarket", "notional_weighted_ev_pct": -3.4867, "realized_incremental_winner_count": 0, "runtime_effect": false, "sample_count": 1}, {"allowed_runtime_apply": false, "market_session_bucket": "krx_regular", "notional_weighted_ev_pct": -0.3, "realized_incremental_winner_count": 0, "runtime_effect": false, "sample_count": 1}], "candidate_count": 3, "closed_candidate_count": 2, "correctly_not_expanded_or_reversal_count": 2, "diagnostic_win_rate": 0.0, "equal_weight_avg_profit_pct": -1.8933, "feature_axis_metrics": {"ai_score": [{"bucket": "lt_60", "daily_only_live_authority": false, "notional_weighted_ev_pct": -2.4499, "realized_incremental_winner_count": 0, "sample_count": 2}], "blocker_reason": [{"bucket": "profit_not_enough", "daily_only_live_authority": false, "notional_weighted_ev_pct": -2.4499, "realized_incremental_winner_count": 0, "sample_count": 2}], "buy_pressure_10t": [{"bucket": "lt_50", "daily_only_live_authority": false, "notional_weighted_ev_pct": -2.4499, "realized_incremental_winner_count": 0, "sample_count": 2}], "entry_profit_pct": [{"bucket": "lt_0.4", "daily_only_live_authority": false, "notional_weighted_ev_pct": -2.4499, "realized_incremental_winner_count": 0, "sample_count": 2}], "micro_vwap_side": [{"bucket": "non_negative", "daily_only_live_authority": false, "notional_weighted_ev_pct": -2.4499, "realized_incremental_winner_count": 0, "sample_count": 2}], "tick_acceleration_ratio": [{"bucket": "ge_1", "daily_only_live_authority": false, "notional_weighted_ev_pct": -2.4499, "realized_incremental_winner_count": 0, "sample_count": 2}]}, "label_counts": [{"count": 2, "label": "correctly_not_expanded_or_reversal"}, {"count": 1, "label": "source_quality_blocked"}], "notional_weighted_ev_pct": -2.4499, "probe_confirmation_signature_metrics": [{"diagnostic_win_rate": 0.0, "realized_incremental_winner_count": 0, "sample_count": 1, "signature": "negative_group_seen"}, {"diagnostic_win_rate": 0.0, "realized_incremental_winner_count": 0, "sample_count": 1, "signature": "no_directional_confirmation"}], "realized_incremental_winner_count": 0, "source_quality_blocked_candidate_count": 1, "source_quality_valid_candidate_count": 2, "temporal_inversion_candidate_count": 1, "transient_extension_exit_timing_needed_count": 0, "venue_source_quality_blocked_closed_count": 0, "venue_source_quality_valid_closed_count": 2}
- pyramid_min_profit_pct: 1.1
- pyramid_threshold_source: same_day_unique_runtime_pyramid_evaluation

## Blocker Metrics

- blocker=profit_not_enough sample=2 recovered_rate=0.00 reversal_rate=1.00 blocked_then_recovered_rate=0.00

## Rows

- record_id=24654 code=047920 name=HLB제약 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=0.1 final=-3.16 ai=50.0 tick=0.75 micro_vwap=-34.67
- record_id=24641 code=460930 name=현대힘스 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=0.03 final=-0.04 ai=50.0 tick=0.0 micro_vwap=0.0

## One Share Opportunity Rows

- record_id=24642 code=304100 name=솔트룩스 label=pyramid_correctly_blocked opportunity_seen=True opportunity_profit=1.5 max_profit=1.72 opportunity_cost=0.22 final=0.57 residual_zero_fill=False residual_soft_abort=False residual_missed_candidate=False
- record_id=24649 code=042700 name=한미반도체 label=pyramid_correctly_blocked opportunity_seen=False opportunity_profit=None max_profit=0.66 opportunity_cost=0.66 final=-0.02 residual_zero_fill=True residual_soft_abort=False residual_missed_candidate=False
- record_id=24655 code=010120 name=LS ELECTRIC label=pyramid_correctly_blocked opportunity_seen=False opportunity_profit=None max_profit=0.66 opportunity_cost=0.66 final=0.09 residual_zero_fill=True residual_soft_abort=False residual_missed_candidate=False
- record_id=24646 code=199430 name=케이엔알시스템 label=pyramid_would_have_helped opportunity_seen=True opportunity_profit=1.5 max_profit=1.79 opportunity_cost=0.29 final=1.37 residual_zero_fill=True residual_soft_abort=False residual_missed_candidate=True
- record_id=24659 code=199430 name=케이엔알시스템 label=pyramid_would_have_helped opportunity_seen=True opportunity_profit=1.7 max_profit=2.16 opportunity_cost=0.46 final=1.64 residual_zero_fill=True residual_soft_abort=False residual_missed_candidate=True
- record_id=24651 code=304100 name=솔트룩스 label=pyramid_would_have_helped opportunity_seen=True opportunity_profit=1.91 max_profit=1.91 opportunity_cost=0.0 final=1.48 residual_zero_fill=True residual_soft_abort=False residual_missed_candidate=True
- record_id=24654 code=047920 name=HLB제약 label=pyramid_correctly_blocked opportunity_seen=False opportunity_profit=None max_profit=0.2 opportunity_cost=0.2 final=-3.16 residual_zero_fill=True residual_soft_abort=False residual_missed_candidate=False
- record_id=24652 code=058610 name=에스피지 label=pyramid_correctly_blocked opportunity_seen=False opportunity_profit=None max_profit=0.61 opportunity_cost=0.61 final=0.33 residual_zero_fill=True residual_soft_abort=False residual_missed_candidate=False
- record_id=24672 code=304100 name=솔트룩스 label=pyramid_correctly_blocked opportunity_seen=False opportunity_profit=None max_profit=0.04 opportunity_cost=0.04 final=-3.56 residual_zero_fill=True residual_soft_abort=False residual_missed_candidate=False
- record_id=24641 code=460930 name=현대힘스 label=pyramid_correctly_blocked opportunity_seen=False opportunity_profit=None max_profit=0.42 opportunity_cost=0.42 final=-0.04 residual_zero_fill=True residual_soft_abort=False residual_missed_candidate=False
- record_id=24842 code=460930 name=현대힘스 label=pyramid_correctly_blocked opportunity_seen=False opportunity_profit=None max_profit=1.05 opportunity_cost=1.05 final=0.62 residual_zero_fill=True residual_soft_abort=False residual_missed_candidate=False

## Normal Winner Expansion Rows

- record_id=24654 code=047920 name=HLB제약 label=correctly_not_expanded_or_reversal entry_profit=0.1 incremental_mfe=-0.1301 incremental_final=-3.4867 confirmation=negative_group_seen
- record_id=24641 code=460930 name=현대힘스 label=correctly_not_expanded_or_reversal entry_profit=0.03 incremental_mfe=0.1599 incremental_final=-0.3 confirmation=no_directional_confirmation
- record_id=24842 code=460930 name=현대힘스 label=source_quality_blocked entry_profit=None incremental_mfe=None incremental_final=None confirmation=None
