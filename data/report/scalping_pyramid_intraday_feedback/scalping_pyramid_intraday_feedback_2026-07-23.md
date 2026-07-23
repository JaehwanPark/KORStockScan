# 2026-07-23 Scalping Pyramid Intraday Feedback

- generated_at: 2026-07-23T18:50:02+09:00
- decision_authority: source_only_pyramid_intraday_feedback_no_runtime_mutation
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: intraday_threshold_mutation, intraday_runtime_apply, hard_safety_relaxation, broker_guard_bypass, order_guard_relaxation, stale_quote_bypass, cooldown_bypass, quantity_guard_relaxation, position_cap_release, provider_route_change, bot_restart, real_execution_quality_approval

## Summary

- pyramid_feedback_row_count: 5
- closed_pyramid_row_count: 5
- pyramid_would_have_helped_count: 0
- pyramid_correctly_blocked_count: 1
- pyramid_overheat_or_reversal_risk_count: 4
- pyramid_open_unresolved_count: 0
- one_share_event_count: 12
- one_share_closed_count: 11
- one_share_pyramid_opportunity_count: 2
- one_share_pyramid_missed_upside_count: 0
- one_share_pyramid_missed_upside_rate: 0.00
- one_share_pyramid_avg_opportunity_cost_pct: 0.10
- probe_residual_zero_fill_count: 8
- probe_residual_soft_abort_count: 6
- probe_residual_missed_upside_candidate_count: 1
- probe_residual_pyramid_evaluation_seen_count: 5
- normal_winner_expansion: {"by_effective_venue": [{"allowed_runtime_apply": false, "effective_venue": "KRX", "notional_weighted_ev_pct": -0.4995, "realized_incremental_winner_count": 1, "runtime_effect": false, "sample_count": 3}, {"allowed_runtime_apply": false, "effective_venue": "NXT", "notional_weighted_ev_pct": 0.1441, "realized_incremental_winner_count": 2, "runtime_effect": false, "sample_count": 2}], "by_market_session_bucket": [{"allowed_runtime_apply": false, "market_session_bucket": "krx_regular", "notional_weighted_ev_pct": -0.4995, "realized_incremental_winner_count": 1, "runtime_effect": false, "sample_count": 3}, {"allowed_runtime_apply": false, "market_session_bucket": "nxt_entry_window", "notional_weighted_ev_pct": 0.1441, "realized_incremental_winner_count": 2, "runtime_effect": false, "sample_count": 2}], "candidate_count": 5, "closed_candidate_count": 5, "correctly_not_expanded_or_reversal_count": 2, "diagnostic_win_rate": 0.6, "equal_weight_avg_profit_pct": -0.2072, "feature_axis_metrics": {"ai_score": [{"bucket": "60_to_70", "daily_only_live_authority": false, "notional_weighted_ev_pct": -1.2044, "realized_incremental_winner_count": 0, "sample_count": 1}, {"bucket": "lt_60", "daily_only_live_authority": false, "notional_weighted_ev_pct": 0.0389, "realized_incremental_winner_count": 3, "sample_count": 4}], "blocker_reason": [{"bucket": "profit_not_enough", "daily_only_live_authority": false, "notional_weighted_ev_pct": -0.4171, "realized_incremental_winner_count": 2, "sample_count": 3}, {"bucket": "rising_missed_scout_pyramid_bridge_blocked:profit_not_enough", "daily_only_live_authority": false, "notional_weighted_ev_pct": 0.0252, "realized_incremental_winner_count": 1, "sample_count": 2}], "buy_pressure_10t": [{"bucket": "50_to_70", "daily_only_live_authority": false, "notional_weighted_ev_pct": 0.2898, "realized_incremental_winner_count": 1, "sample_count": 1}, {"bucket": "ge_70", "daily_only_live_authority": false, "notional_weighted_ev_pct": -0.4171, "realized_incremental_winner_count": 2, "sample_count": 3}, {"bucket": "lt_50", "daily_only_live_authority": false, "notional_weighted_ev_pct": -0.23, "realized_incremental_winner_count": 0, "sample_count": 1}], "entry_profit_pct": [{"bucket": "0.4_to_0.8", "daily_only_live_authority": false, "notional_weighted_ev_pct": -1.2044, "realized_incremental_winner_count": 0, "sample_count": 1}, {"bucket": "lt_0.4", "daily_only_live_authority": false, "notional_weighted_ev_pct": 0.0389, "realized_incremental_winner_count": 3, "sample_count": 4}], "micro_vwap_side": [{"bucket": "negative", "daily_only_live_authority": false, "notional_weighted_ev_pct": -1.2044, "realized_incremental_winner_count": 0, "sample_count": 1}, {"bucket": "non_negative", "daily_only_live_authority": false, "notional_weighted_ev_pct": 0.0389, "realized_incremental_winner_count": 3, "sample_count": 4}], "tick_acceleration_ratio": [{"bucket": "ge_1", "daily_only_live_authority": false, "notional_weighted_ev_pct": -0.4393, "realized_incremental_winner_count": 1, "sample_count": 3}, {"bucket": "lt_0.5", "daily_only_live_authority": false, "notional_weighted_ev_pct": 0.0523, "realized_incremental_winner_count": 2, "sample_count": 2}]}, "label_counts": [{"count": 3, "label": "realized_incremental_winner"}, {"count": 2, "label": "correctly_not_expanded_or_reversal"}], "notional_weighted_ev_pct": -0.2486, "probe_confirmation_signature_metrics": [{"diagnostic_win_rate": 0.5, "realized_incremental_winner_count": 2, "sample_count": 4, "signature": "negative_group_seen"}, {"diagnostic_win_rate": 1.0, "realized_incremental_winner_count": 1, "sample_count": 1, "signature": "no_directional_confirmation"}], "realized_incremental_winner_count": 3, "source_quality_blocked_candidate_count": 0, "source_quality_valid_candidate_count": 5, "transient_extension_exit_timing_needed_count": 0, "venue_source_quality_blocked_closed_count": 0, "venue_source_quality_valid_closed_count": 5}
- pyramid_min_profit_pct: 1.1
- pyramid_threshold_source: same_day_unique_runtime_pyramid_evaluation

## Blocker Metrics

- blocker=profit_not_enough sample=5 recovered_rate=0.00 reversal_rate=0.80 blocked_then_recovered_rate=0.00

## Rows

- record_id=23101 code=001520 name=동양 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=0.57 final=-0.41 ai=63.0 tick=3.8 micro_vwap=-17.71
- record_id=23086 code=066570 name=LG전자 label=pyramid_correctly_blocked blocker=profit_not_enough profit=0.56 final=0.67 ai=63.0 tick=2.5 micro_vwap=-4.46
- record_id=23336 code=036930 name=주성엔지니어링 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=0.46 final=0.27 ai=58.0 tick=1.0 micro_vwap=38.23
- record_id=22785 code=095610 name=테스 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=0.55 final=0.55 ai=63.0 tick=0.417 micro_vwap=-1.55
- record_id=22759 code=058610 name=에스피지 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=0.49 final=0.37 ai=67.0 tick=2.857 micro_vwap=6.79

## One Share Opportunity Rows

- record_id=22762 code=117730 name=티로보틱스 label=pyramid_correctly_blocked opportunity_seen=True opportunity_profit=1.1 max_profit=1.25 opportunity_cost=0.15 final=0.19 residual_zero_fill=False residual_soft_abort=False residual_missed_candidate=False
- record_id=22735 code=459510 name=나우로보틱스 label=pyramid_correctly_blocked opportunity_seen=False opportunity_profit=None max_profit=0.82 opportunity_cost=0.82 final=-1.22 residual_zero_fill=False residual_soft_abort=False residual_missed_candidate=False
- record_id=22888 code=002990 name=금호건설 label=pyramid_correctly_blocked opportunity_seen=False opportunity_profit=None max_profit=0.77 opportunity_cost=0.77 final=-1.79 residual_zero_fill=False residual_soft_abort=False residual_missed_candidate=False
- record_id=22855 code=066570 name=LG전자 label=pyramid_correctly_blocked opportunity_seen=False opportunity_profit=None max_profit=0.75 opportunity_cost=0.75 final=0.26 residual_zero_fill=False residual_soft_abort=False residual_missed_candidate=False
- record_id=22974 code=439960 name=코스모로보틱스 label=pyramid_correctly_blocked opportunity_seen=False opportunity_profit=None max_profit=0.34 opportunity_cost=0.34 final=-3.68 residual_zero_fill=True residual_soft_abort=True residual_missed_candidate=False
- record_id=22732 code=119850 name=지엔씨에너지 label=pyramid_correctly_blocked opportunity_seen=False opportunity_profit=None max_profit=0.86 opportunity_cost=0.86 final=0.38 residual_zero_fill=True residual_soft_abort=False residual_missed_candidate=False
- record_id=23086 code=066570 name=LG전자 label=pyramid_correctly_blocked opportunity_seen=False opportunity_profit=None max_profit=0.73 opportunity_cost=0.73 final=0.67 residual_zero_fill=True residual_soft_abort=True residual_missed_candidate=False
- record_id=23101 code=001520 name=동양 label=pyramid_overheat_or_reversal_risk opportunity_seen=True opportunity_profit=1.5 max_profit=1.55 opportunity_cost=0.05 final=-0.41 residual_zero_fill=True residual_soft_abort=False residual_missed_candidate=True
- record_id=23336 code=036930 name=주성엔지니어링 label=pyramid_correctly_blocked opportunity_seen=False opportunity_profit=None max_profit=0.77 opportunity_cost=0.77 final=0.27 residual_zero_fill=True residual_soft_abort=True residual_missed_candidate=False
- record_id=22758 code=096770 name=SK이노베이션 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=0.53 opportunity_cost=0.53 final=None residual_zero_fill=True residual_soft_abort=True residual_missed_candidate=False
- record_id=22785 code=095610 name=테스 label=pyramid_correctly_blocked opportunity_seen=False opportunity_profit=None max_profit=0.61 opportunity_cost=0.61 final=0.55 residual_zero_fill=True residual_soft_abort=True residual_missed_candidate=False
- record_id=22759 code=058610 name=에스피지 label=pyramid_correctly_blocked opportunity_seen=False opportunity_profit=None max_profit=0.49 opportunity_cost=0.49 final=0.37 residual_zero_fill=True residual_soft_abort=True residual_missed_candidate=False

## Normal Winner Expansion Rows

- record_id=23086 code=066570 name=LG전자 label=realized_incremental_winner entry_profit=0.34 incremental_mfe=0.1587 incremental_final=0.0989 confirmation=negative_group_seen
- record_id=23101 code=001520 name=동양 label=correctly_not_expanded_or_reversal entry_profit=0.57 incremental_mfe=-0.1405 incremental_final=-1.2044 confirmation=negative_group_seen
- record_id=23336 code=036930 name=주성엔지니어링 label=correctly_not_expanded_or_reversal entry_profit=0.27 incremental_mfe=0.2687 incremental_final=-0.23 confirmation=negative_group_seen
- record_id=22785 code=095610 name=테스 label=realized_incremental_winner entry_profit=0.03 incremental_mfe=0.3498 incremental_final=0.2898 confirmation=no_directional_confirmation
- record_id=22759 code=058610 name=에스피지 label=realized_incremental_winner entry_profit=0.13 incremental_mfe=0.1295 incremental_final=0.0097 confirmation=negative_group_seen
