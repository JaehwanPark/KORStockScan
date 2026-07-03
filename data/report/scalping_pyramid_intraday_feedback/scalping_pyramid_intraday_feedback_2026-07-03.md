# 2026-07-03 Scalping Pyramid Intraday Feedback

- generated_at: 2026-07-03T13:24:54+09:00
- decision_authority: source_only_pyramid_intraday_feedback_no_runtime_mutation
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: intraday_threshold_mutation, intraday_runtime_apply, hard_safety_relaxation, broker_guard_bypass, order_guard_relaxation, stale_quote_bypass, cooldown_bypass, quantity_guard_relaxation, position_cap_release, provider_route_change, bot_restart, real_execution_quality_approval

## Summary

- pyramid_feedback_row_count: 24
- closed_pyramid_row_count: 10
- pyramid_would_have_helped_count: 1
- pyramid_correctly_blocked_count: 1
- pyramid_overheat_or_reversal_risk_count: 8
- pyramid_open_unresolved_count: 14
- one_share_event_count: 29
- one_share_closed_count: 12
- one_share_pyramid_opportunity_count: 15
- one_share_pyramid_missed_upside_count: 2
- one_share_pyramid_missed_upside_rate: 0.17
- one_share_pyramid_avg_opportunity_cost_pct: 0.85

## Blocker Metrics

- blocker=ai_score_below_min sample=1 recovered_rate=0.00 reversal_rate=1.00 blocked_then_recovered_rate=0.00
- blocker=profit_not_enough sample=18 recovered_rate=0.06 reversal_rate=0.22 blocked_then_recovered_rate=0.06
- blocker=pyramid_quality_blocked:ai_score_below_min,tick_accel_below_min sample=1 recovered_rate=0.00 reversal_rate=1.00 blocked_then_recovered_rate=0.00
- blocker=pyramid_quality_blocked:ai_score_below_min,tick_accel_below_min,micro_vwap_overheated sample=1 recovered_rate=0.00 reversal_rate=1.00 blocked_then_recovered_rate=0.00
- blocker=tick_accel_below_min sample=2 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=trend_not_strong sample=1 recovered_rate=0.00 reversal_rate=1.00 blocked_then_recovered_rate=0.00

## Rows

- record_id=15209 code=000500 name=가온전선 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=0.73 final=0.57 ai=57.0 tick=0.0 micro_vwap=130.45
- record_id=15204 code=161890 name=한국콜마 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=1.35 final=1.02 ai=40.0 tick=1.0 micro_vwap=139.81
- record_id= code=042660 name=한화오션 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.14 final=None ai=62.0 tick=0.0 micro_vwap=-999.0
- record_id=15206 code=042660 name=한화오션 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=0.4 final=-3.64 ai=50.0 tick=3.0 micro_vwap=-48.5
- record_id=15212 code=009520 name=포스코엠텍 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.05 final=None ai=50.0 tick=0.0 micro_vwap=-999.0
- record_id=15215 code=025320 name=시노펙스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.37 final=None ai=57.0 tick=1.667 micro_vwap=-66.9
- record_id=15227 code=376900 name=로킷헬스케어 label=pyramid_overheat_or_reversal_risk blocker=ai_score_below_min profit=2.57 final=1.86 ai=52.0 tick=0.5 micro_vwap=89.14
- record_id=15217 code=441270 name=파인엠텍 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=0.95 final=-4.64 ai=71.0 tick=2.0 micro_vwap=-46.51
- record_id=15233 code=095500 name=미래나노텍 label=pyramid_overheat_or_reversal_risk blocker=pyramid_quality_blocked:ai_score_below_min,tick_accel_below_min profit=5.15 final=4.13 ai=62.0 tick=1.0 micro_vwap=212.92
- record_id=15225 code=000500 name=가온전선 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.75 final=None ai=54.0 tick=1.0 micro_vwap=-809.46
- record_id=15213 code=037710 name=광주신세계 label=pyramid_would_have_helped blocker=profit_not_enough profit=0.09 final=0.34 ai=65.0 tick=1.0 micro_vwap=32.44
- record_id= code=161890 name=한국콜마 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.11 final=None ai=67.0 tick=0.0 micro_vwap=-31.04
- record_id= code=950160 name=코오롱티슈진 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.11 final=None ai=72.0 tick=1.857 micro_vwap=-69.17
- record_id= code=037070 name=파세코 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.05 final=None ai=65.0 tick=4.0 micro_vwap=-98.58
- record_id= code=000660 name=SK하이닉스 label=pyramid_open_unresolved blocker=tick_accel_below_min profit=1.54 final=None ai=71.0 tick=1.0 micro_vwap=-18.19
- record_id= code=005950 name=이수화학 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.4 final=None ai=72.0 tick=0.5 micro_vwap=56.02
- record_id=15241 code=037710 name=광주신세계 label=pyramid_overheat_or_reversal_risk blocker=trend_not_strong profit=1.55 final=1.3 ai=70.0 tick=2.5 micro_vwap=-6.77
- record_id= code=153890 name=져스텍 label=pyramid_open_unresolved blocker=tick_accel_below_min profit=2.33 final=None ai=70.0 tick=0.0 micro_vwap=20.42
- record_id=15240 code=095500 name=미래나노텍 label=pyramid_overheat_or_reversal_risk blocker=pyramid_quality_blocked:ai_score_below_min,tick_accel_below_min,micro_vwap_overheated profit=4.91 final=4.2 ai=50.0 tick=2.0 micro_vwap=-29.73
- record_id= code=119850 name=지엔씨에너지 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.65 final=None ai=76.0 tick=0.714 micro_vwap=11.12
- record_id= code=477850 name=마키나락스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.52 final=None ai=71.0 tick=0.5 micro_vwap=106.91
- record_id=15242 code=441270 name=파인엠텍 label=pyramid_correctly_blocked blocker=profit_not_enough profit=0.33 final=0.47 ai=72.0 tick=0.0 micro_vwap=30.95
- record_id= code=138930 name=BNK금융지주 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.41 final=None ai=70.0 tick=5.0 micro_vwap=51.57
- record_id= code=006340 name=대원전선 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.08 final=None ai=63.0 tick=0.0 micro_vwap=17.75

## One Share Opportunity Rows

- record_id=15203 code=094360 name=칩스앤미디어 label=pyramid_correctly_blocked opportunity_seen=False opportunity_profit=None max_profit=0.93 opportunity_cost=0.93 final=-5.51
- record_id=15209 code=000500 name=가온전선 label=pyramid_overheat_or_reversal_risk opportunity_seen=True opportunity_profit=0.73 max_profit=1.52 opportunity_cost=0.79 final=0.57
- record_id=15206 code=042660 name=한화오션 label=pyramid_overheat_or_reversal_risk opportunity_seen=True opportunity_profit=0.4 max_profit=0.67 opportunity_cost=0.27 final=-3.64
- record_id=15212 code=009520 name=포스코엠텍 label=pyramid_open_unresolved opportunity_seen=True opportunity_profit=0.05 max_profit=0.12 opportunity_cost=0.07 final=None
- record_id=15211 code=484810 name=티엑스알로보틱스 label=pyramid_would_have_helped opportunity_seen=True opportunity_profit=1.88 max_profit=2.43 opportunity_cost=0.55 final=1.09
- record_id=15205 code=010120 name=LS ELECTRIC label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=15204 code=161890 name=한국콜마 label=pyramid_overheat_or_reversal_risk opportunity_seen=True opportunity_profit=1.35 max_profit=2.1 opportunity_cost=0.75 final=1.02
- record_id=15215 code=025320 name=시노펙스 label=pyramid_open_unresolved opportunity_seen=True opportunity_profit=0.37 max_profit=1.16 opportunity_cost=0.79 final=None
- record_id=15213 code=037710 name=광주신세계 label=pyramid_would_have_helped opportunity_seen=True opportunity_profit=0.09 max_profit=1.46 opportunity_cost=1.37 final=0.34
- record_id=15227 code=376900 name=로킷헬스케어 label=pyramid_overheat_or_reversal_risk opportunity_seen=True opportunity_profit=2.57 max_profit=2.57 opportunity_cost=0.0 final=1.86
- record_id=15224 code=090460 name=비에이치 label=pyramid_open_unresolved opportunity_seen=True opportunity_profit=5.94 max_profit=13.07 opportunity_cost=7.13 final=None
- record_id=15217 code=441270 name=파인엠텍 label=pyramid_overheat_or_reversal_risk opportunity_seen=True opportunity_profit=0.95 max_profit=0.95 opportunity_cost=0.0 final=-4.64
- record_id=15231 code=486990 name=노타 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=-0.23 opportunity_cost=0.0 final=None
- record_id=15233 code=095500 name=미래나노텍 label=pyramid_overheat_or_reversal_risk opportunity_seen=True opportunity_profit=5.15 max_profit=5.15 opportunity_cost=0.0 final=4.13
- record_id=15219 code=010120 name=LS ELECTRIC label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=-0.43 opportunity_cost=0.0 final=None
- record_id=15225 code=000500 name=가온전선 label=pyramid_open_unresolved opportunity_seen=True opportunity_profit=0.75 max_profit=1.08 opportunity_cost=0.33 final=None
- record_id=15208 code=373220 name=LG에너지솔루션 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=15222 code=062040 name=산일전기 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=15220 code=033100 name=제룡전기 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=15230 code=161890 name=한국콜마 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=15221 code=010140 name=삼성중공업 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=15226 code=484810 name=티엑스알로보틱스 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=15234 code=222800 name=심텍 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=15241 code=037710 name=광주신세계 label=pyramid_overheat_or_reversal_risk opportunity_seen=True opportunity_profit=1.55 max_profit=1.93 opportunity_cost=0.38 final=1.3
- record_id=15242 code=441270 name=파인엠텍 label=pyramid_correctly_blocked opportunity_seen=True opportunity_profit=0.33 max_profit=0.47 opportunity_cost=0.14 final=0.47
- record_id=15240 code=095500 name=미래나노텍 label=pyramid_overheat_or_reversal_risk opportunity_seen=True opportunity_profit=4.91 max_profit=5.15 opportunity_cost=0.24 final=4.2
- record_id=15261 code=004440 name=삼일씨엔에스 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=15239 code=376900 name=로킷헬스케어 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=15297 code=095500 name=미래나노텍 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
