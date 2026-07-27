# 2026-07-28 Scalping Pyramid Intraday Feedback

- generated_at: 2026-07-28T08:40:02+09:00
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
- one_share_event_count: 9
- one_share_closed_count: 8
- one_share_pyramid_opportunity_count: 4
- one_share_pyramid_missed_upside_count: 3
- one_share_pyramid_missed_upside_rate: 0.38
- one_share_pyramid_avg_opportunity_cost_pct: 0.24
- probe_residual_zero_fill_count: 8
- probe_residual_soft_abort_count: 0
- probe_residual_missed_upside_candidate_count: 3
- probe_residual_pyramid_evaluation_seen_count: 1
- normal_winner_expansion: {"by_effective_venue": [], "by_market_session_bucket": [], "candidate_count": 1, "closed_candidate_count": 0, "correctly_not_expanded_or_reversal_count": 0, "diagnostic_win_rate": 0.0, "equal_weight_avg_profit_pct": 0.0, "feature_axis_metrics": {"ai_score": [], "blocker_reason": [], "buy_pressure_10t": [], "entry_profit_pct": [], "micro_vwap_side": [], "tick_acceleration_ratio": []}, "label_counts": [{"count": 1, "label": "open_unresolved"}], "notional_weighted_ev_pct": 0.0, "probe_confirmation_signature_metrics": [{"diagnostic_win_rate": 0.0, "realized_incremental_winner_count": 0, "sample_count": 1, "signature": "negative_group_seen"}], "realized_incremental_winner_count": 0, "source_quality_blocked_candidate_count": 0, "source_quality_valid_candidate_count": 1, "transient_extension_exit_timing_needed_count": 0, "venue_source_quality_blocked_closed_count": 0, "venue_source_quality_valid_closed_count": 0}
- pyramid_min_profit_pct: 1.1
- pyramid_threshold_source: same_day_unique_runtime_pyramid_evaluation

## Blocker Metrics

- blocker=profit_not_enough sample=1 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00

## Rows

- record_id=24654 code=047920 name=HLB제약 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.1 final=None ai=45.0 tick=2.0 micro_vwap=9.99

## One Share Opportunity Rows

- record_id=24642 code=304100 name=솔트룩스 label=pyramid_correctly_blocked opportunity_seen=True opportunity_profit=1.5 max_profit=1.72 opportunity_cost=0.22 final=0.57 residual_zero_fill=False residual_soft_abort=False residual_missed_candidate=False
- record_id=24649 code=042700 name=한미반도체 label=pyramid_correctly_blocked opportunity_seen=False opportunity_profit=None max_profit=0.66 opportunity_cost=0.66 final=-0.02 residual_zero_fill=True residual_soft_abort=False residual_missed_candidate=False
- record_id=24655 code=010120 name=LS ELECTRIC label=pyramid_correctly_blocked opportunity_seen=False opportunity_profit=None max_profit=0.66 opportunity_cost=0.66 final=0.09 residual_zero_fill=True residual_soft_abort=False residual_missed_candidate=False
- record_id=24646 code=199430 name=케이엔알시스템 label=pyramid_would_have_helped opportunity_seen=True opportunity_profit=1.5 max_profit=1.79 opportunity_cost=0.29 final=1.37 residual_zero_fill=True residual_soft_abort=False residual_missed_candidate=True
- record_id=24659 code=199430 name=케이엔알시스템 label=pyramid_would_have_helped opportunity_seen=True opportunity_profit=1.7 max_profit=2.16 opportunity_cost=0.46 final=1.64 residual_zero_fill=True residual_soft_abort=False residual_missed_candidate=True
- record_id=24651 code=304100 name=솔트룩스 label=pyramid_would_have_helped opportunity_seen=True opportunity_profit=1.91 max_profit=1.91 opportunity_cost=0.0 final=1.48 residual_zero_fill=True residual_soft_abort=False residual_missed_candidate=True
- record_id=24654 code=047920 name=HLB제약 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=0.2 opportunity_cost=0.2 final=None residual_zero_fill=True residual_soft_abort=False residual_missed_candidate=False
- record_id=24652 code=058610 name=에스피지 label=pyramid_correctly_blocked opportunity_seen=False opportunity_profit=None max_profit=0.61 opportunity_cost=0.61 final=0.33 residual_zero_fill=True residual_soft_abort=False residual_missed_candidate=False
- record_id=24672 code=304100 name=솔트룩스 label=pyramid_correctly_blocked opportunity_seen=False opportunity_profit=None max_profit=0.04 opportunity_cost=0.04 final=-3.56 residual_zero_fill=True residual_soft_abort=False residual_missed_candidate=False

## Normal Winner Expansion Rows

- record_id=24654 code=047920 name=HLB제약 label=open_unresolved entry_profit=0.1 incremental_mfe=-0.1301 incremental_final=None confirmation=negative_group_seen
