# 2026-07-24 Scalping Pyramid Intraday Feedback

- generated_at: 2026-07-24T12:35:02+09:00
- decision_authority: source_only_pyramid_intraday_feedback_no_runtime_mutation
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: intraday_threshold_mutation, intraday_runtime_apply, hard_safety_relaxation, broker_guard_bypass, order_guard_relaxation, stale_quote_bypass, cooldown_bypass, quantity_guard_relaxation, position_cap_release, provider_route_change, bot_restart, real_execution_quality_approval

## Summary

- pyramid_feedback_row_count: 1
- closed_pyramid_row_count: 1
- pyramid_would_have_helped_count: 0
- pyramid_correctly_blocked_count: 0
- pyramid_overheat_or_reversal_risk_count: 1
- pyramid_open_unresolved_count: 0
- one_share_event_count: 2
- one_share_closed_count: 1
- one_share_pyramid_opportunity_count: 0
- one_share_pyramid_missed_upside_count: 0
- one_share_pyramid_missed_upside_rate: 0.00
- one_share_pyramid_avg_opportunity_cost_pct: 0.00
- probe_residual_zero_fill_count: 2
- probe_residual_soft_abort_count: 0
- probe_residual_missed_upside_candidate_count: 0
- probe_residual_pyramid_evaluation_seen_count: 1
- normal_winner_expansion: {"by_effective_venue": [{"allowed_runtime_apply": false, "effective_venue": "KRX", "notional_weighted_ev_pct": -0.0702, "realized_incremental_winner_count": 0, "runtime_effect": false, "sample_count": 1}], "by_market_session_bucket": [{"allowed_runtime_apply": false, "market_session_bucket": "krx_regular", "notional_weighted_ev_pct": -0.0702, "realized_incremental_winner_count": 0, "runtime_effect": false, "sample_count": 1}], "candidate_count": 1, "closed_candidate_count": 1, "correctly_not_expanded_or_reversal_count": 1, "diagnostic_win_rate": 0.0, "equal_weight_avg_profit_pct": -0.0702, "feature_axis_metrics": {"ai_score": [{"bucket": "lt_60", "daily_only_live_authority": false, "notional_weighted_ev_pct": -0.0702, "realized_incremental_winner_count": 0, "sample_count": 1}], "blocker_reason": [{"bucket": "profit_not_enough", "daily_only_live_authority": false, "notional_weighted_ev_pct": -0.0702, "realized_incremental_winner_count": 0, "sample_count": 1}], "buy_pressure_10t": [{"bucket": "ge_70", "daily_only_live_authority": false, "notional_weighted_ev_pct": -0.0702, "realized_incremental_winner_count": 0, "sample_count": 1}], "entry_profit_pct": [{"bucket": "lt_0.4", "daily_only_live_authority": false, "notional_weighted_ev_pct": -0.0702, "realized_incremental_winner_count": 0, "sample_count": 1}], "micro_vwap_side": [{"bucket": "non_negative", "daily_only_live_authority": false, "notional_weighted_ev_pct": -0.0702, "realized_incremental_winner_count": 0, "sample_count": 1}], "tick_acceleration_ratio": [{"bucket": "ge_1", "daily_only_live_authority": false, "notional_weighted_ev_pct": -0.0702, "realized_incremental_winner_count": 0, "sample_count": 1}]}, "label_counts": [{"count": 1, "label": "correctly_not_expanded_or_reversal"}], "notional_weighted_ev_pct": -0.0702, "probe_confirmation_signature_metrics": [{"diagnostic_win_rate": 0.0, "realized_incremental_winner_count": 0, "sample_count": 1, "signature": "negative_group_seen"}], "realized_incremental_winner_count": 0, "source_quality_blocked_candidate_count": 0, "source_quality_valid_candidate_count": 1, "transient_extension_exit_timing_needed_count": 0, "venue_source_quality_blocked_closed_count": 0, "venue_source_quality_valid_closed_count": 1}
- pyramid_min_profit_pct: 1.1
- pyramid_threshold_source: same_day_unique_runtime_pyramid_evaluation

## Blocker Metrics

- blocker=profit_not_enough sample=1 recovered_rate=0.00 reversal_rate=1.00 blocked_then_recovered_rate=0.00

## Rows

- record_id=23735 code=096770 name=SK이노베이션 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=0.46 final=0.31 ai=60.0 tick=1.5 micro_vwap=31.23

## One Share Opportunity Rows

- record_id=23735 code=096770 name=SK이노베이션 label=pyramid_correctly_blocked opportunity_seen=False opportunity_profit=None max_profit=0.84 opportunity_cost=0.84 final=0.31 residual_zero_fill=True residual_soft_abort=False residual_missed_candidate=False
- record_id=23752 code=100090 name=SK오션플랜트 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=-0.13 opportunity_cost=0.0 final=None residual_zero_fill=True residual_soft_abort=False residual_missed_candidate=False

## Normal Winner Expansion Rows

- record_id=23735 code=096770 name=SK이노베이션 label=correctly_not_expanded_or_reversal entry_profit=0.15 incremental_mfe=0.459 incremental_final=-0.0702 confirmation=negative_group_seen
