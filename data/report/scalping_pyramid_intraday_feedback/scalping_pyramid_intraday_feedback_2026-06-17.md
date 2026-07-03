# 2026-06-17 Scalping Pyramid Intraday Feedback

- generated_at: 2026-07-03T13:23:41+09:00
- decision_authority: source_only_pyramid_intraday_feedback_no_runtime_mutation
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: intraday_threshold_mutation, intraday_runtime_apply, hard_safety_relaxation, broker_guard_bypass, order_guard_relaxation, stale_quote_bypass, cooldown_bypass, quantity_guard_relaxation, position_cap_release, provider_route_change, bot_restart, real_execution_quality_approval

## Summary

- pyramid_feedback_row_count: 72
- closed_pyramid_row_count: 0
- pyramid_would_have_helped_count: 0
- pyramid_correctly_blocked_count: 0
- pyramid_overheat_or_reversal_risk_count: 0
- pyramid_open_unresolved_count: 72
- one_share_event_count: 0
- one_share_closed_count: 0
- one_share_pyramid_opportunity_count: 0
- one_share_pyramid_missed_upside_count: 0
- one_share_pyramid_missed_upside_rate: 0.00
- one_share_pyramid_avg_opportunity_cost_pct: 0.00

## Blocker Metrics

- blocker=add_judgment_locked sample=9 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=profit_not_enough sample=46 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=trend_not_strong sample=17 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00

## Rows

- record_id= code=036930 name=주성엔지니어링 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.2 final=None ai=72.0 tick=1.0 micro_vwap=-2.76
- record_id= code=042660 name=한화오션 label=pyramid_open_unresolved blocker=add_judgment_locked profit=0.21 final=None ai=73.0 tick=1.0 micro_vwap=0.07
- record_id= code=200470 name=에이팩트 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.84 final=None ai=72.0 tick=3.0 micro_vwap=47.69
- record_id= code=064290 name=인텍플러스 label=pyramid_open_unresolved blocker=profit_not_enough profit=-0.0 final=None ai=70.0 tick=0.0 micro_vwap=-108.02
- record_id= code=033160 name=엠케이전자 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.09 final=None ai=72.0 tick=2.0 micro_vwap=-35.59
- record_id= code=006220 name=제주은행 label=pyramid_open_unresolved blocker=add_judgment_locked profit=2.86 final=None ai=74.0 tick=0.0 micro_vwap=-32.08
- record_id= code=005290 name=동진쎄미켐 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.08 final=None ai=75.0 tick=1.0 micro_vwap=-43.92
- record_id= code=011070 name=LG이노텍 label=pyramid_open_unresolved blocker=trend_not_strong profit=1.83 final=None ai=73.0 tick=0.5 micro_vwap=1.23
- record_id= code=240810 name=원익IPS label=pyramid_open_unresolved blocker=profit_not_enough profit=0.18 final=None ai=73.0 tick=1.0 micro_vwap=-5.33
- record_id= code=067310 name=하나마이크론 label=pyramid_open_unresolved blocker=trend_not_strong profit=2.45 final=None ai=73.0 tick=1.333 micro_vwap=-54.72
- record_id= code=161890 name=한국콜마 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.37 final=None ai=74.0 tick=1.0 micro_vwap=-12.22
- record_id= code=016380 name=KG스틸 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.25 final=None ai=73.0 tick=2.062 micro_vwap=-16.18
- record_id= code=232140 name=와이씨 label=pyramid_open_unresolved blocker=trend_not_strong profit=2.62 final=None ai=73.0 tick=0.0 micro_vwap=-21.47
- record_id= code=463020 name=뉴엔AI label=pyramid_open_unresolved blocker=profit_not_enough profit=0.12 final=None ai=70.0 tick=7.5 micro_vwap=-52.93
- record_id= code=032580 name=피델릭스 label=pyramid_open_unresolved blocker=trend_not_strong profit=1.62 final=None ai=74.0 tick=3.143 micro_vwap=-70.01
- record_id= code=053260 name=금강철강 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.07 final=None ai=73.0 tick=6.0 micro_vwap=-141.7
- record_id= code=101490 name=에스앤에스텍 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.08 final=None ai=75.0 tick=1.0 micro_vwap=-37.24
- record_id= code=040350 name=크레오에스지 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.81 final=None ai=72.0 tick=0.368 micro_vwap=5.69
- record_id= code=455850 name=SOL AI반도체소부장 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.06 final=None ai=73.0 tick=2.0 micro_vwap=-21.61
- record_id= code=095610 name=테스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.4 final=None ai=72.0 tick=1.25 micro_vwap=4.55
- record_id= code=389650 name=넥스트바이오메디컬 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.75 final=None ai=67.0 tick=7.0 micro_vwap=-73.35
- record_id= code=082740 name=한화엔진 label=pyramid_open_unresolved blocker=trend_not_strong profit=4.75 final=None ai=70.0 tick=0.5 micro_vwap=-60.5
- record_id= code=419530 name=SAMG엔터 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.1 final=None ai=68.0 tick=0.371 micro_vwap=-21.22
- record_id= code=126640 name=화신정공 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.73 final=None ai=69.0 tick=4.0 micro_vwap=-93.67
- record_id= code=075580 name=세진중공업 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.3 final=None ai=73.0 tick=1.0 micro_vwap=-19.9
- record_id= code=071970 name=HD현대마린엔진 label=pyramid_open_unresolved blocker=trend_not_strong profit=3.1 final=None ai=73.0 tick=0.0 micro_vwap=-51.58
- record_id= code=466920 name=SOL 조선TOP3플러스 label=pyramid_open_unresolved blocker=trend_not_strong profit=2.51 final=None ai=71.0 tick=0.0 micro_vwap=-46.09
- record_id= code=329180 name=HD현대중공업 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.32 final=None ai=74.0 tick=1.0 micro_vwap=-57.86
- record_id= code=032940 name=원익 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.15 final=None ai=69.0 tick=48.0 micro_vwap=12.76
- record_id= code=034020 name=두산에너빌리티 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.15 final=None ai=73.0 tick=0.5 micro_vwap=-4.54
- record_id= code=009830 name=한화솔루션 label=pyramid_open_unresolved blocker=add_judgment_locked profit=0.01 final=None ai=72.0 tick=1.5 micro_vwap=0.72
- record_id= code=000500 name=가온전선 label=pyramid_open_unresolved blocker=trend_not_strong profit=6.69 final=None ai=72.0 tick=0.0 micro_vwap=38.37
- record_id= code=012450 name=한화에어로스페이스 label=pyramid_open_unresolved blocker=trend_not_strong profit=2.97 final=None ai=70.0 tick=2.0 micro_vwap=-15.07
- record_id= code=019210 name=와이지-원 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.01 final=None ai=75.0 tick=0.222 micro_vwap=-21.79
- record_id= code=006340 name=대원전선 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.33 final=None ai=72.0 tick=0.0 micro_vwap=-51.63
- record_id= code=290650 name=엘앤씨바이오 label=pyramid_open_unresolved blocker=trend_not_strong profit=3.41 final=None ai=76.0 tick=1.0 micro_vwap=-57.3
- record_id= code=226950 name=올릭스 label=pyramid_open_unresolved blocker=trend_not_strong profit=2.86 final=None ai=71.0 tick=1.0 micro_vwap=-34.67
- record_id= code=092790 name=넥스틸 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.01 final=None ai=76.0 tick=1.0 micro_vwap=-34.56
- record_id= code=314130 name=지놈앤컴퍼니 label=pyramid_open_unresolved blocker=trend_not_strong profit=1.86 final=None ai=72.0 tick=0.2 micro_vwap=-122.2
- record_id= code=037030 name=파워넷 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.12 final=None ai=73.0 tick=3.2 micro_vwap=-29.84
- record_id= code=066970 name=엘앤에프 label=pyramid_open_unresolved blocker=add_judgment_locked profit=0.04 final=None ai=72.0 tick=0.0 micro_vwap=-28.63
- record_id= code=006910 name=보성파워텍 label=pyramid_open_unresolved blocker=trend_not_strong profit=2.49 final=None ai=70.0 tick=0.0 micro_vwap=-27.61
- record_id= code=048410 name=현대바이오 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.42 final=None ai=70.0 tick=0.429 micro_vwap=9.13
- record_id= code=462900 name=KoAct 바이오헬스케어액티브 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.32 final=None ai=76.0 tick=0.588 micro_vwap=-8.46
- record_id= code=035420 name=NAVER label=pyramid_open_unresolved blocker=profit_not_enough profit=0.18 final=None ai=75.0 tick=1.0 micro_vwap=10.07
- record_id= code=328130 name=루닛 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.99 final=None ai=71.0 tick=0.13 micro_vwap=-12.04
- record_id= code=015760 name=한국전력 label=pyramid_open_unresolved blocker=add_judgment_locked profit=0.01 final=None ai=76.0 tick=0.0 micro_vwap=14.29
- record_id= code=010140 name=삼성중공업 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.11 final=None ai=74.0 tick=1.0 micro_vwap=-17.65
- record_id= code=007340 name=DN오토모티브 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.31 final=None ai=72.0 tick=0.69 micro_vwap=-3.09
- record_id= code=009420 name=한올바이오파마 label=pyramid_open_unresolved blocker=trend_not_strong profit=1.54 final=None ai=72.0 tick=0.0 micro_vwap=15.21
- record_id= code=039200 name=오스코텍 label=pyramid_open_unresolved blocker=trend_not_strong profit=2.17 final=None ai=69.0 tick=4.333 micro_vwap=-70.34
- record_id= code=078890 name=가온그룹 label=pyramid_open_unresolved blocker=add_judgment_locked profit=3.5 final=None ai=72.0 tick=1.0 micro_vwap=-17.13
- record_id= code=228760 name=지노믹트리 label=pyramid_open_unresolved blocker=profit_not_enough profit=-0.0 final=None ai=68.0 tick=99.0 micro_vwap=-6.12
- record_id= code=411060 name=ACE KRX금현물 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.01 final=None ai=71.0 tick=4.0 micro_vwap=-4.46
- record_id= code=000660 name=SK하이닉스 label=pyramid_open_unresolved blocker=trend_not_strong profit=2.01 final=None ai=71.0 tick=0.0 micro_vwap=-27.09
- record_id= code=004710 name=한솔테크닉스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.63 final=None ai=71.0 tick=0.0 micro_vwap=-46.05
- record_id= code=047810 name=한국항공우주 label=pyramid_open_unresolved blocker=add_judgment_locked profit=0.02 final=None ai=73.0 tick=0.25 micro_vwap=4.34
- record_id= code=394420 name=리센스메디컬 label=pyramid_open_unresolved blocker=add_judgment_locked profit=-0.0 final=None ai=68.0 tick=2.9 micro_vwap=-46.65
- record_id= code=039830 name=오로라 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.34 final=None ai=72.0 tick=0.379 micro_vwap=-42.04
- record_id= code=122640 name=예스티 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.7 final=None ai=68.0 tick=0.889 micro_vwap=28.3
- record_id= code=308080 name=바이젠셀 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.29 final=None ai=73.0 tick=1.667 micro_vwap=-39.27
- record_id= code=031330 name=에스에이엠티 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.15 final=None ai=74.0 tick=0.0 micro_vwap=-5.83
- record_id= code=148020 name=RISE 200 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.06 final=None ai=73.0 tick=0.917 micro_vwap=-4.2
- record_id= code=194370 name=제이에스코퍼레이션 label=pyramid_open_unresolved blocker=add_judgment_locked profit=0.01 final=None ai=75.0 tick=0.222 micro_vwap=-22.81
- record_id= code=388790 name=라이콤 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.18 final=None ai=73.0 tick=1.0 micro_vwap=-19.43
- record_id= code=389260 name=대명에너지 label=pyramid_open_unresolved blocker=trend_not_strong profit=3.48 final=None ai=76.0 tick=0.0 micro_vwap=93.92
- record_id= code=196170 name=알테오젠 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.44 final=None ai=76.0 tick=0.5 micro_vwap=-5.63
- record_id= code=372320 name=큐로셀 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.4 final=None ai=72.0 tick=1.0 micro_vwap=-13.02
- record_id= code=253590 name=네오셈 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.29 final=None ai=75.0 tick=1.773 micro_vwap=3.68
- record_id= code=163730 name=핑거 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.01 final=None ai=75.0 tick=9.625 micro_vwap=9.12
- record_id= code=007810 name=코리아써키트 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.27 final=None ai=73.0 tick=2.0 micro_vwap=43.68
- record_id= code=397030 name=에이프릴바이오 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.31 final=None ai=74.0 tick=0.5 micro_vwap=-19.23

## One Share Opportunity Rows
