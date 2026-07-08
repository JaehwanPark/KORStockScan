# 2026-07-08 Scalping Pyramid Intraday Feedback

- generated_at: 2026-07-08T20:10:45+09:00
- decision_authority: source_only_pyramid_intraday_feedback_no_runtime_mutation
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: intraday_threshold_mutation, intraday_runtime_apply, hard_safety_relaxation, broker_guard_bypass, order_guard_relaxation, stale_quote_bypass, cooldown_bypass, quantity_guard_relaxation, position_cap_release, provider_route_change, bot_restart, real_execution_quality_approval

## Summary

- pyramid_feedback_row_count: 13
- closed_pyramid_row_count: 3
- pyramid_would_have_helped_count: 1
- pyramid_correctly_blocked_count: 0
- pyramid_overheat_or_reversal_risk_count: 2
- pyramid_open_unresolved_count: 10
- one_share_event_count: 38
- one_share_closed_count: 18
- one_share_pyramid_opportunity_count: 8
- one_share_pyramid_missed_upside_count: 5
- one_share_pyramid_missed_upside_rate: 0.28
- one_share_pyramid_avg_opportunity_cost_pct: 0.58

## Blocker Metrics

- blocker=profit_not_enough sample=6 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=pyramid_quality_blocked:ai_score_below_min,tick_accel_stale,micro_context_stale sample=1 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=pyramid_quality_blocked:ai_score_unavailable,tick_aggressor_pressure_unusable,tick_accel_stale,micro_context_stale sample=1 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=rising_missed_scout_pyramid_bridge_blocked:micro_context_stale,tick_accel_stale,tick_aggressor_pressure_unusable,fresh_micro_confirmation_missing sample=2 recovered_rate=0.50 reversal_rate=0.00 blocked_then_recovered_rate=0.50
- blocker=rising_missed_scout_pyramid_bridge_blocked:profit_not_enough,micro_context_stale,tick_accel_stale,tick_aggressor_pressure_unusable,fresh_micro_confirmation_missing sample=2 recovered_rate=0.00 reversal_rate=1.00 blocked_then_recovered_rate=0.00
- blocker=rising_missed_scout_pyramid_bridge_blocked:profit_not_enough,quote_stale,micro_context_stale,tick_accel_stale,tick_aggressor_pressure_unusable,fresh_micro_confirmation_missing sample=1 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00

## Rows

- record_id= code=477850 name=마키나락스 label=pyramid_open_unresolved blocker=pyramid_quality_blocked:ai_score_below_min,tick_accel_stale,micro_context_stale profit=1.93 final=None ai=61.0 tick=0.0 micro_vwap=64.34
- record_id= code=000270 name=기아 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.03 final=None ai=57.0 tick=1.0 micro_vwap=-14.82
- record_id= code=086450 name=동국제약 label=pyramid_open_unresolved blocker=pyramid_quality_blocked:ai_score_unavailable,tick_aggressor_pressure_unusable,tick_accel_stale,micro_context_stale profit=1.18 final=None ai=50.0 tick=0.706 micro_vwap=-2.67
- record_id= code=083450 name=GST label=pyramid_open_unresolved blocker=profit_not_enough profit=0.12 final=None ai=58.0 tick=0.25 micro_vwap=-13.27
- record_id= code=073240 name=금호타이어 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.08 final=None ai=58.0 tick=0.111 micro_vwap=-17.29
- record_id=16124 code=372320 name=큐로셀 label=pyramid_would_have_helped blocker=rising_missed_scout_pyramid_bridge_blocked:micro_context_stale,tick_accel_stale,tick_aggressor_pressure_unusable,fresh_micro_confirmation_missing profit=0.95 final=1.43 ai=50.0 tick=2.13 micro_vwap=10.75
- record_id=15974 code=092730 name=네오팜 label=pyramid_overheat_or_reversal_risk blocker=rising_missed_scout_pyramid_bridge_blocked:profit_not_enough,micro_context_stale,tick_accel_stale,tick_aggressor_pressure_unusable,fresh_micro_confirmation_missing profit=0.02 final=-3.43 ai=50.0 tick=0.735 micro_vwap=-28.41
- record_id= code=372320 name=큐로셀 label=pyramid_open_unresolved blocker=rising_missed_scout_pyramid_bridge_blocked:micro_context_stale,tick_accel_stale,tick_aggressor_pressure_unusable,fresh_micro_confirmation_missing profit=0.71 final=None ai=50.0 tick=2.188 micro_vwap=-40.09
- record_id=16154 code=181710 name=NHN label=pyramid_overheat_or_reversal_risk blocker=rising_missed_scout_pyramid_bridge_blocked:profit_not_enough,micro_context_stale,tick_accel_stale,tick_aggressor_pressure_unusable,fresh_micro_confirmation_missing profit=0.42 final=-3.86 ai=50.0 tick=0.0 micro_vwap=-199.97
- record_id= code=237880 name=클리오 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.1 final=None ai=58.0 tick=0.286 micro_vwap=36.56
- record_id= code=439090 name=마녀공장 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.01 final=None ai=54.0 tick=2.0 micro_vwap=71.74
- record_id=16165 code=000810 name=삼성화재 label=pyramid_open_unresolved blocker=rising_missed_scout_pyramid_bridge_blocked:profit_not_enough,quote_stale,micro_context_stale,tick_accel_stale,tick_aggressor_pressure_unusable,fresh_micro_confirmation_missing profit=0.06 final=None ai=50.0 tick=0.077 micro_vwap=0.0
- record_id= code=028300 name=HLB label=pyramid_open_unresolved blocker=profit_not_enough profit=0.59 final=None ai=50.0 tick=1.071 micro_vwap=0.0

## One Share Opportunity Rows

- record_id=15970 code=018260 name=삼성에스디에스 label=pyramid_correctly_blocked opportunity_seen=False opportunity_profit=None max_profit=0.49 opportunity_cost=0.49 final=-4.56
- record_id=15960 code=042660 name=한화오션 label=pyramid_correctly_blocked opportunity_seen=False opportunity_profit=None max_profit=0.1 opportunity_cost=0.1 final=-4.6
- record_id=15957 code=352820 name=하이브 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=15969 code=226320 name=잇츠한불 label=pyramid_correctly_blocked opportunity_seen=False opportunity_profit=None max_profit=0.39 opportunity_cost=0.39 final=-4.32
- record_id=15964 code=114840 name=아이패밀리에스씨 label=pyramid_correctly_blocked opportunity_seen=False opportunity_profit=None max_profit=0.29 opportunity_cost=0.29 final=-5.39
- record_id=15973 code=008930 name=한미사이언스 label=pyramid_correctly_blocked opportunity_seen=False opportunity_profit=None max_profit=-0.15 opportunity_cost=0.0 final=-3.17
- record_id=15984 code=399720 name=가온칩스 label=pyramid_correctly_blocked opportunity_seen=False opportunity_profit=None max_profit=0.89 opportunity_cost=0.89 final=1.35
- record_id=15979 code=200710 name=에이디테크놀로지 label=pyramid_would_have_helped opportunity_seen=True opportunity_profit=1.71 max_profit=1.71 opportunity_cost=0.0 final=1.39
- record_id=15971 code=086520 name=에코프로 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=15986 code=078160 name=메디포스트 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=0.76 opportunity_cost=0.76 final=None
- record_id=16000 code=365660 name=레몬헬스케어 label=pyramid_correctly_blocked opportunity_seen=False opportunity_profit=None max_profit=-0.23 opportunity_cost=0.0 final=-5.69
- record_id=16017 code=014970 name=삼륭물산 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=16016 code=402340 name=SK스퀘어 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=15954 code=073240 name=금호타이어 label=pyramid_would_have_helped opportunity_seen=True opportunity_profit=2.02 max_profit=5.24 opportunity_cost=3.22 final=4.6
- record_id=15996 code=042040 name=케이피엠테크 label=pyramid_correctly_blocked opportunity_seen=False opportunity_profit=None max_profit=0.94 opportunity_cost=0.94 final=-3.14
- record_id=16013 code=009150 name=삼성전기 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=16027 code=365660 name=레몬헬스케어 label=pyramid_would_have_helped opportunity_seen=True opportunity_profit=1.63 max_profit=1.63 opportunity_cost=0.0 final=1.48
- record_id=16012 code=042660 name=한화오션 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=16057 code=365660 name=레몬헬스케어 label=pyramid_would_have_helped opportunity_seen=True opportunity_profit=1.62 max_profit=1.62 opportunity_cost=0.0 final=1.1
- record_id=16060 code=365660 name=레몬헬스케어 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=15998 code=043260 name=성호전자 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=16077 code=365660 name=레몬헬스케어 label=pyramid_correctly_blocked opportunity_seen=False opportunity_profit=None max_profit=1.18 opportunity_cost=1.18 final=0.73
- record_id=16090 code=365660 name=레몬헬스케어 label=pyramid_correctly_blocked opportunity_seen=False opportunity_profit=None max_profit=0.87 opportunity_cost=0.87 final=-5.58
- record_id=16063 code=024060 name=흥구석유 label=pyramid_correctly_blocked opportunity_seen=False opportunity_profit=None max_profit=0.16 opportunity_cost=0.16 final=-3.15
- record_id=15994 code=477850 name=마키나락스 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=16116 code=308080 name=바이젠셀 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=16003 code=079650 name=서산 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=16124 code=372320 name=큐로셀 label=pyramid_would_have_helped opportunity_seen=True opportunity_profit=0.95 max_profit=1.91 opportunity_cost=0.96 final=1.43
- record_id=15974 code=092730 name=네오팜 label=pyramid_overheat_or_reversal_risk opportunity_seen=True opportunity_profit=0.02 max_profit=0.51 opportunity_cost=0.49 final=-3.43
- record_id=15985 code=114840 name=아이패밀리에스씨 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=16143 code=372320 name=큐로셀 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=16154 code=181710 name=NHN label=pyramid_overheat_or_reversal_risk opportunity_seen=True opportunity_profit=0.42 max_profit=0.42 opportunity_cost=0.0 final=-3.86
- record_id=16148 code=092730 name=네오팜 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=16159 code=006110 name=삼아알미늄 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=16165 code=000810 name=삼성화재 label=pyramid_open_unresolved opportunity_seen=True opportunity_profit=0.06 max_profit=0.06 opportunity_cost=0.0 final=None
- record_id=15992 code=008930 name=한미사이언스 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=15982 code=226320 name=잇츠한불 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=15961 code=010950 name=S-Oil label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
