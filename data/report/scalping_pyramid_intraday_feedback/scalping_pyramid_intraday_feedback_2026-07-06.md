# 2026-07-06 Scalping Pyramid Intraday Feedback

- generated_at: 2026-07-06T20:15:16+09:00
- decision_authority: source_only_pyramid_intraday_feedback_no_runtime_mutation
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: intraday_threshold_mutation, intraday_runtime_apply, hard_safety_relaxation, broker_guard_bypass, order_guard_relaxation, stale_quote_bypass, cooldown_bypass, quantity_guard_relaxation, position_cap_release, provider_route_change, bot_restart, real_execution_quality_approval

## Summary

- pyramid_feedback_row_count: 23
- closed_pyramid_row_count: 8
- pyramid_would_have_helped_count: 1
- pyramid_correctly_blocked_count: 4
- pyramid_overheat_or_reversal_risk_count: 3
- pyramid_open_unresolved_count: 15
- one_share_event_count: 36
- one_share_closed_count: 18
- one_share_pyramid_opportunity_count: 15
- one_share_pyramid_missed_upside_count: 4
- one_share_pyramid_missed_upside_rate: 0.22
- one_share_pyramid_avg_opportunity_cost_pct: 0.64

## Blocker Metrics

- blocker=profit_not_enough sample=16 recovered_rate=0.00 reversal_rate=0.12 blocked_then_recovered_rate=0.00
- blocker=pyramid_hard_blocked:buy_pressure_severe_below_min,fresh_micro_confirmation_missing sample=1 recovered_rate=0.00 reversal_rate=1.00 blocked_then_recovered_rate=0.00
- blocker=pyramid_hard_blocked:large_sell_detected,fresh_micro_confirmation_missing sample=1 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=pyramid_quality_blocked:ai_score_below_min,tick_aggressor_pressure_unusable,tick_accel_stale,micro_context_stale sample=1 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=rising_missed_scout_pyramid_bridge_blocked:profit_not_enough,ai_score_below_min,quote_stale,micro_context_stale,tick_aggressor_pressure_unusable,fresh_micro_confirmation_missing,tick_accel_stale sample=1 recovered_rate=1.00 reversal_rate=0.00 blocked_then_recovered_rate=1.00
- blocker=rising_missed_scout_pyramid_bridge_blocked:profit_not_enough,quote_stale,micro_context_stale,tick_aggressor_pressure_unusable,fresh_micro_confirmation_missing,tick_accel_stale sample=2 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=trend_not_strong sample=1 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00

## Rows

- record_id= code=096770 name=SK이노베이션 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.08 final=None ai=54.0 tick=0.394 micro_vwap=-3.64
- record_id=15506 code=042660 name=한화오션 label=pyramid_correctly_blocked blocker=profit_not_enough profit=0.01 final=0.45 ai=66.0 tick=1.0 micro_vwap=40.61
- record_id= code=477850 name=마키나락스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.67 final=None ai=50.0 tick=0.0 micro_vwap=None
- record_id=15541 code=024840 name=KBI메탈 label=pyramid_would_have_helped blocker=rising_missed_scout_pyramid_bridge_blocked:profit_not_enough,ai_score_below_min,quote_stale,micro_context_stale,tick_aggressor_pressure_unusable,fresh_micro_confirmation_missing,tick_accel_stale profit=0.15 final=0.9 ai=58.0 tick=1.0 micro_vwap=84.51
- record_id= code=024840 name=KBI메탈 label=pyramid_open_unresolved blocker=rising_missed_scout_pyramid_bridge_blocked:profit_not_enough,quote_stale,micro_context_stale,tick_aggressor_pressure_unusable,fresh_micro_confirmation_missing,tick_accel_stale profit=0.14 final=None ai=50.0 tick=1.0 micro_vwap=-26.35
- record_id= code=499790 name=GS피앤엘 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.02 final=None ai=63.0 tick=0.647 micro_vwap=40.47
- record_id=15533 code=200710 name=에이디테크놀로지 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=0.0 final=-2.12 ai=58.0 tick=1.0 micro_vwap=-46.45
- record_id= code=112040 name=위메이드 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.12 final=None ai=53.0 tick=0.059 micro_vwap=-32.01
- record_id= code=006660 name=삼성공조 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.04 final=None ai=50.0 tick=0.167 micro_vwap=-11.15
- record_id= code=365660 name=레몬헬스케어 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.53 final=None ai=50.0 tick=0.0 micro_vwap=-92.39
- record_id= code=089030 name=테크윙 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.2 final=None ai=61.0 tick=1.0 micro_vwap=15.77
- record_id=15479 code=399720 name=가온칩스 label=pyramid_overheat_or_reversal_risk blocker=pyramid_hard_blocked:buy_pressure_severe_below_min,fresh_micro_confirmation_missing profit=1.44 final=1.09 ai=67.0 tick=0.5 micro_vwap=7.58
- record_id=15570 code=399720 name=가온칩스 label=pyramid_correctly_blocked blocker=profit_not_enough profit=0.01 final=0.25 ai=54.0 tick=0.8 micro_vwap=39.54
- record_id=15578 code=300720 name=한일시멘트 label=pyramid_correctly_blocked blocker=profit_not_enough profit=0.21 final=0.56 ai=69.0 tick=2.0 micro_vwap=18.26
- record_id=15577 code=004980 name=성신양회 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=0.07 final=-3.51 ai=63.0 tick=1.0 micro_vwap=4.12
- record_id= code=094360 name=칩스앤미디어 label=pyramid_open_unresolved blocker=pyramid_quality_blocked:ai_score_below_min,tick_aggressor_pressure_unusable,tick_accel_stale,micro_context_stale profit=1.77 final=None ai=61.0 tick=2.0 micro_vwap=-3.8
- record_id=15579 code=003200 name=일신방직 label=pyramid_correctly_blocked blocker=profit_not_enough profit=0.16 final=0.32 ai=63.0 tick=2.0 micro_vwap=14.02
- record_id= code=003200 name=일신방직 label=pyramid_open_unresolved blocker=pyramid_hard_blocked:large_sell_detected,fresh_micro_confirmation_missing profit=2.18 final=None ai=50.0 tick=0.0 micro_vwap=0.0
- record_id=15585 code=300720 name=한일시멘트 label=pyramid_open_unresolved blocker=rising_missed_scout_pyramid_bridge_blocked:profit_not_enough,quote_stale,micro_context_stale,tick_aggressor_pressure_unusable,fresh_micro_confirmation_missing,tick_accel_stale profit=0.03 final=None ai=57.0 tick=2.0 micro_vwap=21.24
- record_id= code=028260 name=삼성물산 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.1 final=None ai=50.0 tick=0.089 micro_vwap=-7.21
- record_id= code=042660 name=한화오션 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.73 final=None ai=62.0 tick=0.5 micro_vwap=12.96
- record_id= code=382900 name=범한퓨얼셀 label=pyramid_open_unresolved blocker=trend_not_strong profit=1.22 final=None ai=50.0 tick=0.423 micro_vwap=-22.93
- record_id=15590 code=399720 name=가온칩스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.13 final=None ai=67.0 tick=2.333 micro_vwap=23.09

## One Share Opportunity Rows

- record_id=15465 code=042660 name=한화오션 label=pyramid_would_have_helped opportunity_seen=True opportunity_profit=2.6 max_profit=2.87 opportunity_cost=0.27 final=1.89
- record_id=15471 code=011070 name=LG이노텍 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=15480 code=200710 name=에이디테크놀로지 label=pyramid_would_have_helped opportunity_seen=True opportunity_profit=2.95 max_profit=6.12 opportunity_cost=3.17 final=4.54
- record_id=15473 code=042700 name=한미반도체 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=-0.02 opportunity_cost=0.0 final=None
- record_id=15472 code=086520 name=에코프로 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=15469 code=000500 name=가온전선 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=15467 code=000660 name=SK하이닉스 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=15468 code=034020 name=두산에너빌리티 label=pyramid_correctly_blocked opportunity_seen=False opportunity_profit=None max_profit=-0.01 opportunity_cost=0.0 final=-3.16
- record_id=15489 code=272210 name=한화시스템 label=pyramid_correctly_blocked opportunity_seen=True opportunity_profit=1.55 max_profit=1.55 opportunity_cost=0.0 final=0.59
- record_id=15506 code=042660 name=한화오션 label=pyramid_correctly_blocked opportunity_seen=True opportunity_profit=0.01 max_profit=0.45 opportunity_cost=0.44 final=0.45
- record_id=15487 code=200710 name=에이디테크놀로지 label=pyramid_correctly_blocked opportunity_seen=False opportunity_profit=None max_profit=0.61 opportunity_cost=0.61 final=0.78
- record_id=15523 code=002990 name=금호건설 label=pyramid_correctly_blocked opportunity_seen=False opportunity_profit=None max_profit=-3.07 opportunity_cost=0.0 final=-3.16
- record_id=15526 code=002990 name=금호건설 label=pyramid_would_have_helped opportunity_seen=True opportunity_profit=2.86 max_profit=2.86 opportunity_cost=0.0 final=2.55
- record_id=15494 code=402340 name=SK스퀘어 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=15518 code=024840 name=KBI메탈 label=pyramid_correctly_blocked opportunity_seen=True opportunity_profit=1.66 max_profit=1.66 opportunity_cost=0.0 final=0.52
- record_id=15536 code=001260 name=남광토건 label=pyramid_correctly_blocked opportunity_seen=False opportunity_profit=None max_profit=-1.21 opportunity_cost=0.0 final=-5.32
- record_id=15541 code=024840 name=KBI메탈 label=pyramid_would_have_helped opportunity_seen=True opportunity_profit=0.15 max_profit=1.09 opportunity_cost=0.94 final=0.9
- record_id=15533 code=200710 name=에이디테크놀로지 label=pyramid_overheat_or_reversal_risk opportunity_seen=True opportunity_profit=0.0 max_profit=1.59 opportunity_cost=1.59 final=-2.12
- record_id=15555 code=024840 name=KBI메탈 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=15479 code=399720 name=가온칩스 label=pyramid_overheat_or_reversal_risk opportunity_seen=True opportunity_profit=1.44 max_profit=1.44 opportunity_cost=0.0 final=1.09
- record_id=15537 code=002990 name=금호건설 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=15564 code=003200 name=일신방직 label=pyramid_correctly_blocked opportunity_seen=False opportunity_profit=None max_profit=0.87 opportunity_cost=0.87 final=0.79
- record_id=15547 code=001260 name=남광토건 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=15507 code=477850 name=마키나락스 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=15570 code=399720 name=가온칩스 label=pyramid_correctly_blocked opportunity_seen=True opportunity_profit=0.01 max_profit=0.37 opportunity_cost=0.36 final=0.25
- record_id=15577 code=004980 name=성신양회 label=pyramid_overheat_or_reversal_risk opportunity_seen=True opportunity_profit=0.07 max_profit=1.16 opportunity_cost=1.09 final=-3.51
- record_id=15579 code=003200 name=일신방직 label=pyramid_correctly_blocked opportunity_seen=True opportunity_profit=0.16 max_profit=0.94 opportunity_cost=0.78 final=0.32
- record_id=15578 code=300720 name=한일시멘트 label=pyramid_correctly_blocked opportunity_seen=True opportunity_profit=0.21 max_profit=0.69 opportunity_cost=0.48 final=0.56
- record_id=15585 code=300720 name=한일시멘트 label=pyramid_open_unresolved opportunity_seen=True opportunity_profit=0.03 max_profit=0.03 opportunity_cost=0.0 final=None
- record_id=15590 code=399720 name=가온칩스 label=pyramid_open_unresolved opportunity_seen=True opportunity_profit=0.13 max_profit=0.61 opportunity_cost=0.48 final=None
- record_id=15597 code=323280 name=태성 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=15481 code=094360 name=칩스앤미디어 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=1.28 opportunity_cost=1.28 final=None
- record_id=15466 code=005930 name=삼성전자 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=15587 code=003200 name=일신방직 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=1.18 opportunity_cost=1.18 final=None
- record_id=15520 code=272210 name=한화시스템 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=15563 code=200710 name=에이디테크놀로지 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
