# 2026-06-09 Scalping Pyramid Intraday Feedback

- generated_at: 2026-07-03T13:22:50+09:00
- decision_authority: source_only_pyramid_intraday_feedback_no_runtime_mutation
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: intraday_threshold_mutation, intraday_runtime_apply, hard_safety_relaxation, broker_guard_bypass, order_guard_relaxation, stale_quote_bypass, cooldown_bypass, quantity_guard_relaxation, position_cap_release, provider_route_change, bot_restart, real_execution_quality_approval

## Summary

- pyramid_feedback_row_count: 77
- closed_pyramid_row_count: 2
- pyramid_would_have_helped_count: 0
- pyramid_correctly_blocked_count: 0
- pyramid_overheat_or_reversal_risk_count: 2
- pyramid_open_unresolved_count: 75
- one_share_event_count: 0
- one_share_closed_count: 0
- one_share_pyramid_opportunity_count: 0
- one_share_pyramid_missed_upside_count: 0
- one_share_pyramid_missed_upside_rate: 0.00
- one_share_pyramid_avg_opportunity_cost_pct: 0.00

## Blocker Metrics

- blocker=add_judgment_locked sample=8 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=profit_not_enough sample=54 recovered_rate=0.00 reversal_rate=0.02 blocked_then_recovered_rate=0.00
- blocker=scalping_cutoff sample=1 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=trend_not_strong sample=14 recovered_rate=0.00 reversal_rate=0.07 blocked_then_recovered_rate=0.00

## Rows

- record_id= code=240810 name=원익IPS label=pyramid_open_unresolved blocker=profit_not_enough profit=0.29 final=None ai=61.0 tick=0.0 micro_vwap=45.72
- record_id= code=425040 name=티이엠씨 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.87 final=None ai=73.0 tick=4.0 micro_vwap=-62.15
- record_id= code=010170 name=대한광통신 label=pyramid_open_unresolved blocker=trend_not_strong profit=2.07 final=None ai=57.0 tick=0.0 micro_vwap=-50.36
- record_id= code=007660 name=이수페타시스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.03 final=None ai=78.0 tick=1.0 micro_vwap=-77.88
- record_id= code=010120 name=LS ELECTRIC label=pyramid_open_unresolved blocker=profit_not_enough profit=-0.0 final=None ai=70.0 tick=0.667 micro_vwap=-58.64
- record_id= code=178320 name=서진시스템 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.89 final=None ai=69.0 tick=2.0 micro_vwap=-23.19
- record_id= code=125490 name=한라캐스트 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.03 final=None ai=75.0 tick=1.667 micro_vwap=-105.82
- record_id= code=012330 name=현대모비스 label=pyramid_open_unresolved blocker=add_judgment_locked profit=0.11 final=None ai=71.0 tick=2.0 micro_vwap=-55.05
- record_id= code=033160 name=엠케이전자 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.37 final=None ai=71.0 tick=0.9 micro_vwap=-149.88
- record_id= code=457370 name=한켐 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.63 final=None ai=69.0 tick=0.0 micro_vwap=-138.24
- record_id= code=038500 name=삼표시멘트 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.09 final=None ai=65.0 tick=0.167 micro_vwap=-30.7
- record_id= code=187660 name=페니트리움바이오 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.28 final=None ai=64.0 tick=0.667 micro_vwap=68.13
- record_id= code=232140 name=와이씨 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.47 final=None ai=74.0 tick=0.3 micro_vwap=14.75
- record_id= code=090430 name=아모레퍼시픽 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.03 final=None ai=67.0 tick=0.667 micro_vwap=-55.21
- record_id= code=253590 name=네오셈 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.93 final=None ai=72.0 tick=0.091 micro_vwap=-2.3
- record_id= code=084370 name=유진테크 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.28 final=None ai=70.0 tick=0.0 micro_vwap=-26.84
- record_id= code=001450 name=현대해상 label=pyramid_open_unresolved blocker=trend_not_strong profit=2.02 final=None ai=76.0 tick=1.0 micro_vwap=-45.04
- record_id= code=242040 name=나무기술 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.11 final=None ai=75.0 tick=0.0 micro_vwap=-85.08
- record_id= code=200710 name=에이디테크놀로지 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.33 final=None ai=71.0 tick=10.0 micro_vwap=97.66
- record_id= code=041960 name=코미팜 label=pyramid_open_unresolved blocker=add_judgment_locked profit=3.44 final=None ai=46.0 tick=2.6 micro_vwap=-5.93
- record_id= code=328130 name=루닛 label=pyramid_open_unresolved blocker=trend_not_strong profit=1.5 final=None ai=69.0 tick=0.4 micro_vwap=-41.25
- record_id= code=316140 name=우리금융지주 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.44 final=None ai=72.0 tick=1.0 micro_vwap=-49.1
- record_id= code=043260 name=성호전자 label=pyramid_open_unresolved blocker=add_judgment_locked profit=0.39 final=None ai=72.0 tick=1.0 micro_vwap=-60.62
- record_id= code=101490 name=에스앤에스텍 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.1 final=None ai=61.0 tick=1.0 micro_vwap=-6.75
- record_id= code=200470 name=에이팩트 label=pyramid_open_unresolved blocker=trend_not_strong profit=5.46 final=None ai=73.0 tick=2.333 micro_vwap=-30.78
- record_id= code=110990 name=디아이티 label=pyramid_open_unresolved blocker=add_judgment_locked profit=0.9 final=None ai=71.0 tick=1.214 micro_vwap=-4.49
- record_id= code=173130 name=오파스넷 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.28 final=None ai=69.0 tick=1.526 micro_vwap=-81.59
- record_id= code=021240 name=코웨이 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.2 final=None ai=70.0 tick=0.9 micro_vwap=-30.62
- record_id= code=388790 name=라이콤 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.77 final=None ai=72.0 tick=2.333 micro_vwap=3.8
- record_id= code=347850 name=디앤디파마텍 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.1 final=None ai=49.0 tick=0.2 micro_vwap=-30.48
- record_id= code=011070 name=LG이노텍 label=pyramid_open_unresolved blocker=trend_not_strong profit=3.06 final=None ai=71.0 tick=0.0 micro_vwap=-66.1
- record_id= code=058470 name=리노공업 label=pyramid_open_unresolved blocker=trend_not_strong profit=2.02 final=None ai=71.0 tick=0.0 micro_vwap=-24.31
- record_id= code=017900 name=광전자 label=pyramid_open_unresolved blocker=add_judgment_locked profit=1.1 final=None ai=73.0 tick=0.6 micro_vwap=-15.55
- record_id=9576 code=454910 name=두산로보틱스 label=pyramid_overheat_or_reversal_risk blocker=trend_not_strong profit=1.88 final=1.52 ai=73.0 tick=3.0 micro_vwap=-29.86
- record_id= code=000270 name=기아 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.39 final=None ai=69.0 tick=0.25 micro_vwap=23.51
- record_id= code=017670 name=SK텔레콤 label=pyramid_open_unresolved blocker=trend_not_strong profit=1.63 final=None ai=68.0 tick=1.0 micro_vwap=3.66
- record_id= code=069960 name=현대백화점 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.93 final=None ai=76.0 tick=2.0 micro_vwap=-102.98
- record_id= code=089030 name=테크윙 label=pyramid_open_unresolved blocker=trend_not_strong profit=2.55 final=None ai=66.0 tick=1.0 micro_vwap=-53.12
- record_id= code=252990 name=샘씨엔에스 label=pyramid_open_unresolved blocker=add_judgment_locked profit=1.17 final=None ai=73.0 tick=0.833 micro_vwap=-2.92
- record_id= code=319660 name=피에스케이 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.73 final=None ai=62.0 tick=0.75 micro_vwap=-26.05
- record_id= code=023530 name=롯데쇼핑 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.06 final=None ai=69.0 tick=0.0 micro_vwap=-38.25
- record_id= code=000150 name=그린광학 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.48 final=None ai=53.0 tick=0.0 micro_vwap=-106.34
- record_id= code=093370 name=후성 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.82 final=None ai=51.0 tick=0.5 micro_vwap=-3.72
- record_id= code=085620 name=미래에셋생명 label=pyramid_open_unresolved blocker=trend_not_strong profit=2.22 final=None ai=70.0 tick=1.0 micro_vwap=-69.67
- record_id= code=402340 name=SK스퀘어 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.34 final=None ai=74.0 tick=1.0 micro_vwap=-45.37
- record_id= code=950160 name=코오롱티슈진 label=pyramid_open_unresolved blocker=trend_not_strong profit=1.96 final=None ai=72.0 tick=0.333 micro_vwap=-3.31
- record_id= code=141080 name=리가켐바이오 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.08 final=None ai=52.0 tick=2.333 micro_vwap=-28.22
- record_id= code=482630 name=삼양엔씨켐 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.16 final=None ai=58.0 tick=9.0 micro_vwap=51.87
- record_id= code=425420 name=티에프이 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.93 final=None ai=58.0 tick=0.714 micro_vwap=-33.48
- record_id= code=094480 name=갤럭시아머니트리 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.48 final=None ai=55.0 tick=0.109 micro_vwap=-40.38
- record_id= code=086390 name=유니테스트 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.05 final=None ai=66.0 tick=0.083 micro_vwap=32.65
- record_id= code=005930 name=삼성전자 label=pyramid_open_unresolved blocker=trend_not_strong profit=4.65 final=None ai=70.0 tick=0.0 micro_vwap=-53.37
- record_id= code=034020 name=두산에너빌리티 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.19 final=None ai=68.0 tick=1.0 micro_vwap=-32.43
- record_id= code=006910 name=보성파워텍 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.33 final=None ai=72.0 tick=0.0 micro_vwap=-49.87
- record_id=9721 code=090710 name=휴림로봇 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=1.31 final=0.93 ai=73.0 tick=1.4 micro_vwap=-30.41
- record_id= code=090710 name=휴림로봇 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.12 final=None ai=72.0 tick=1.25 micro_vwap=-31.36
- record_id= code=008770 name=호텔신라 label=pyramid_open_unresolved blocker=add_judgment_locked profit=0.13 final=None ai=64.0 tick=2.333 micro_vwap=-55.35
- record_id= code=383220 name=F&F label=pyramid_open_unresolved blocker=profit_not_enough profit=0.03 final=None ai=65.0 tick=1.25 micro_vwap=-5.46
- record_id= code=314130 name=지놈앤컴퍼니 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.16 final=None ai=70.0 tick=0.0 micro_vwap=1.72
- record_id= code=454910 name=두산로보틱스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.62 final=None ai=72.0 tick=1.0 micro_vwap=53.32
- record_id= code=475830 name=오름테라퓨틱 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.09 final=None ai=66.0 tick=0.083 micro_vwap=-41.31
- record_id= code=046890 name=서울반도체 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.35 final=None ai=64.0 tick=3.0 micro_vwap=26.94
- record_id= code=082270 name=젬백스 label=pyramid_open_unresolved blocker=trend_not_strong profit=1.78 final=None ai=63.0 tick=4.0 micro_vwap=-49.41
- record_id= code=330860 name=네패스아크 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.47 final=None ai=75.0 tick=1.167 micro_vwap=-138.95
- record_id= code=403870 name=HPSP label=pyramid_open_unresolved blocker=profit_not_enough profit=0.12 final=None ai=66.0 tick=0.0 micro_vwap=-36.9
- record_id= code=160980 name=싸이맥스 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.17 final=None ai=60.0 tick=0.0 micro_vwap=25.29
- record_id= code=003160 name=디아이 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.13 final=None ai=53.0 tick=3.167 micro_vwap=-25.61
- record_id= code=064400 name=LG씨엔에스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.27 final=None ai=71.0 tick=0.0 micro_vwap=-4.9
- record_id= code=095610 name=테스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.26 final=None ai=50.0 tick=0.0 micro_vwap=-56.75
- record_id= code=083500 name=에프엔에스테크 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.2 final=None ai=48.0 tick=1.35 micro_vwap=3.83
- record_id= code=031980 name=피에스케이홀딩스 label=pyramid_open_unresolved blocker=add_judgment_locked profit=0.0 final=None ai=45.0 tick=2.0 micro_vwap=-32.44
- record_id= code=098460 name=고영 label=pyramid_open_unresolved blocker=trend_not_strong profit=1.95 final=None ai=65.0 tick=1.0 micro_vwap=6.52
- record_id= code=089970 name=브이엠 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.16 final=None ai=72.0 tick=0.0 micro_vwap=26.12
- record_id= code=030530 name=원익홀딩스 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.18 final=None ai=67.0 tick=1.0 micro_vwap=25.11
- record_id= code=100790 name=미래에셋벤처투자 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.47 final=None ai=68.0 tick=0.25 micro_vwap=42.89
- record_id= code=219130 name=타이거일렉 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.88 final=None ai=72.0 tick=0.618 micro_vwap=0.0
- record_id= code=000370 name=한화손해보험 label=pyramid_open_unresolved blocker=scalping_cutoff profit=0.08 final=None ai=43.0 tick=0.0 micro_vwap=-48.35

## One Share Opportunity Rows
