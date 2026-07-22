# 2026-07-22 Scalping Pyramid Intraday Feedback

- generated_at: 2026-07-22T20:11:42+09:00
- decision_authority: source_only_pyramid_intraday_feedback_no_runtime_mutation
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: intraday_threshold_mutation, intraday_runtime_apply, hard_safety_relaxation, broker_guard_bypass, order_guard_relaxation, stale_quote_bypass, cooldown_bypass, quantity_guard_relaxation, position_cap_release, provider_route_change, bot_restart, real_execution_quality_approval

## Summary

- pyramid_feedback_row_count: 12
- closed_pyramid_row_count: 9
- pyramid_would_have_helped_count: 0
- pyramid_correctly_blocked_count: 0
- pyramid_overheat_or_reversal_risk_count: 9
- pyramid_open_unresolved_count: 3
- one_share_event_count: 15
- one_share_closed_count: 14
- one_share_pyramid_opportunity_count: 9
- one_share_pyramid_missed_upside_count: 2
- one_share_pyramid_missed_upside_rate: 0.14
- one_share_pyramid_avg_opportunity_cost_pct: 0.29
- probe_residual_zero_fill_count: 8
- probe_residual_soft_abort_count: 5
- probe_residual_missed_upside_candidate_count: 5
- probe_residual_pyramid_evaluation_seen_count: 6
- pyramid_min_profit_pct: 1.1
- pyramid_threshold_source: same_day_unique_runtime_pyramid_evaluation

## Blocker Metrics

- blocker=profit_not_enough sample=8 recovered_rate=0.00 reversal_rate=0.62 blocked_then_recovered_rate=0.00
- blocker=pyramid_quality_blocked:ai_score_unavailable,tick_aggressor_pressure_unusable,tick_accel_stale,micro_context_stale sample=1 recovered_rate=0.00 reversal_rate=1.00 blocked_then_recovered_rate=0.00
- blocker=pyramid_quality_blocked:buy_pressure_below_min,tick_accel_below_min,micro_vwap_overheated sample=1 recovered_rate=0.00 reversal_rate=1.00 blocked_then_recovered_rate=0.00
- blocker=rising_missed_scout_pyramid_bridge_blocked:micro_context_stale,tick_aggressor_pressure_unusable,fresh_micro_confirmation_missing,tick_accel_stale sample=1 recovered_rate=0.00 reversal_rate=1.00 blocked_then_recovered_rate=0.00
- blocker=rising_missed_scout_pyramid_bridge_blocked:profit_not_enough,micro_vwap_severe_overheated sample=1 recovered_rate=0.00 reversal_rate=1.00 blocked_then_recovered_rate=0.00

## Rows

- record_id=20932 code=064820 name=케이프 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=0.63 final=0.63 ai=77.0 tick=1.25 micro_vwap=27.91
- record_id= code=047810 name=한국항공우주 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.04 final=None ai=50.0 tick=0.75 micro_vwap=25.53
- record_id=22101 code=049080 name=기가레인 label=pyramid_overheat_or_reversal_risk blocker=pyramid_quality_blocked:buy_pressure_below_min,tick_accel_below_min,micro_vwap_overheated profit=1.65 final=1.44 ai=74.0 tick=0.0 micro_vwap=78.76
- record_id=21924 code=017670 name=SK텔레콤 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=0.03 final=-3.26 ai=45.0 tick=1.5 micro_vwap=-19.2
- record_id=22035 code=012690 name=모나리자 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=1.07 final=0.29 ai=69.0 tick=1.0 micro_vwap=-5.2
- record_id=22400 code=012690 name=모나리자 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.03 final=None ai=55.0 tick=0.0 micro_vwap=-63.42
- record_id=21913 code=066570 name=LG전자 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=0.89 final=0.3 ai=72.0 tick=1.0 micro_vwap=-33.45
- record_id=22041 code=006340 name=대원전선 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=0.31 final=-0.08 ai=61.0 tick=1.0 micro_vwap=-36.08
- record_id= code=112610 name=씨에스윈드 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.02 final=None ai=50.0 tick=3.5 micro_vwap=-22.97
- record_id=22380 code=287840 name=인투셀 label=pyramid_overheat_or_reversal_risk blocker=rising_missed_scout_pyramid_bridge_blocked:profit_not_enough,micro_vwap_severe_overheated profit=0.5 final=0.29 ai=64.0 tick=0.0 micro_vwap=59.05
- record_id=21933 code=486990 name=노타 label=pyramid_overheat_or_reversal_risk blocker=rising_missed_scout_pyramid_bridge_blocked:micro_context_stale,tick_aggressor_pressure_unusable,fresh_micro_confirmation_missing,tick_accel_stale profit=0.73 final=-0.26 ai=46.0 tick=1.0 micro_vwap=-2.76
- record_id=21838 code=270660 name=에브리봇 label=pyramid_overheat_or_reversal_risk blocker=pyramid_quality_blocked:ai_score_unavailable,tick_aggressor_pressure_unusable,tick_accel_stale,micro_context_stale profit=2.31 final=-0.08 ai=50.0 tick=0.111 micro_vwap=-3.74

## One Share Opportunity Rows

- record_id=21847 code=102940 name=코오롱생명과학 label=pyramid_overheat_or_reversal_risk opportunity_seen=True opportunity_profit=1.1 max_profit=1.4 opportunity_cost=0.3 final=0.0 residual_zero_fill=True residual_soft_abort=False residual_missed_candidate=True
- record_id=21848 code=460930 name=현대힘스 label=pyramid_would_have_helped opportunity_seen=True opportunity_profit=1.5 max_profit=1.57 opportunity_cost=0.07 final=1.1 residual_zero_fill=True residual_soft_abort=True residual_missed_candidate=True
- record_id=21845 code=459510 name=나우로보틱스 label=pyramid_would_have_helped opportunity_seen=True opportunity_profit=1.66 max_profit=2.77 opportunity_cost=1.11 final=2.35 residual_zero_fill=True residual_soft_abort=False residual_missed_candidate=True
- record_id=21841 code=090360 name=로보스타 label=pyramid_correctly_blocked opportunity_seen=False opportunity_profit=None max_profit=-0.23 opportunity_cost=0.0 final=-3.9 residual_zero_fill=True residual_soft_abort=True residual_missed_candidate=False
- record_id=22175 code=389260 name=대명에너지 label=pyramid_correctly_blocked opportunity_seen=True opportunity_profit=1.1 max_profit=1.26 opportunity_cost=0.16 final=0.24 residual_zero_fill=True residual_soft_abort=True residual_missed_candidate=True
- record_id=22101 code=049080 name=기가레인 label=pyramid_overheat_or_reversal_risk opportunity_seen=True opportunity_profit=1.44 max_profit=1.86 opportunity_cost=0.42 final=1.44 residual_zero_fill=False residual_soft_abort=False residual_missed_candidate=False
- record_id=22296 code=043260 name=성호전자 label=pyramid_correctly_blocked opportunity_seen=False opportunity_profit=None max_profit=-0.23 opportunity_cost=0.0 final=-3.18 residual_zero_fill=True residual_soft_abort=True residual_missed_candidate=False
- record_id=22035 code=012690 name=모나리자 label=pyramid_overheat_or_reversal_risk opportunity_seen=True opportunity_profit=1.13 max_profit=1.13 opportunity_cost=0.0 final=0.29 residual_zero_fill=True residual_soft_abort=False residual_missed_candidate=True
- record_id=22041 code=006340 name=대원전선 label=pyramid_correctly_blocked opportunity_seen=False opportunity_profit=None max_profit=0.77 opportunity_cost=0.77 final=-0.08 residual_zero_fill=True residual_soft_abort=True residual_missed_candidate=False
- record_id=22380 code=287840 name=인투셀 label=pyramid_overheat_or_reversal_risk opportunity_seen=True opportunity_profit=1.1 max_profit=1.35 opportunity_cost=0.25 final=0.29 residual_zero_fill=False residual_soft_abort=False residual_missed_candidate=False
- record_id=21933 code=486990 name=노타 label=pyramid_correctly_blocked opportunity_seen=False opportunity_profit=None max_profit=0.73 opportunity_cost=0.73 final=-0.26 residual_zero_fill=False residual_soft_abort=False residual_missed_candidate=False
- record_id=21838 code=270660 name=에브리봇 label=pyramid_overheat_or_reversal_risk opportunity_seen=True opportunity_profit=2.31 max_profit=2.31 opportunity_cost=0.0 final=-0.08 residual_zero_fill=False residual_soft_abort=False residual_missed_candidate=False
- record_id=22703 code=300080 name=플리토 label=pyramid_correctly_blocked opportunity_seen=False opportunity_profit=None max_profit=0.39 opportunity_cost=0.39 final=-3.82 residual_zero_fill=False residual_soft_abort=False residual_missed_candidate=False
- record_id=22271 code=017670 name=SK텔레콤 label=pyramid_overheat_or_reversal_risk opportunity_seen=True opportunity_profit=1.1 max_profit=1.39 opportunity_cost=0.29 final=-0.23 residual_zero_fill=False residual_soft_abort=False residual_missed_candidate=False
- record_id=22160 code=073240 name=금호타이어 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=0.26 opportunity_cost=0.26 final=None residual_zero_fill=False residual_soft_abort=False residual_missed_candidate=False
