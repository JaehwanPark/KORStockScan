# 2026-06-11 Scalping Pyramid Intraday Feedback

- generated_at: 2026-07-03T13:23:10+09:00
- decision_authority: source_only_pyramid_intraday_feedback_no_runtime_mutation
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: intraday_threshold_mutation, intraday_runtime_apply, hard_safety_relaxation, broker_guard_bypass, order_guard_relaxation, stale_quote_bypass, cooldown_bypass, quantity_guard_relaxation, position_cap_release, provider_route_change, bot_restart, real_execution_quality_approval

## Summary

- pyramid_feedback_row_count: 97
- closed_pyramid_row_count: 2
- pyramid_would_have_helped_count: 0
- pyramid_correctly_blocked_count: 0
- pyramid_overheat_or_reversal_risk_count: 2
- pyramid_open_unresolved_count: 95
- one_share_event_count: 0
- one_share_closed_count: 0
- one_share_pyramid_opportunity_count: 0
- one_share_pyramid_missed_upside_count: 0
- one_share_pyramid_missed_upside_rate: 0.00
- one_share_pyramid_avg_opportunity_cost_pct: 0.00

## Blocker Metrics

- blocker=profit_not_enough sample=86 recovered_rate=0.00 reversal_rate=0.02 blocked_then_recovered_rate=0.00
- blocker=scalping_cutoff sample=1 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=trend_not_strong sample=10 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00

## Rows

- record_id= code=010690 name=화신 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.07 final=None ai=74.0 tick=0.0 micro_vwap=-13.48
- record_id= code=017900 name=광전자 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.08 final=None ai=62.0 tick=None micro_vwap=None
- record_id= code=089970 name=브이엠 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.26 final=None ai=68.0 tick=4.0 micro_vwap=-73.24
- record_id= code=095610 name=테스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.72 final=None ai=74.0 tick=3.333 micro_vwap=-31.94
- record_id= code=000430 name=대원강업 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.32 final=None ai=69.0 tick=0.667 micro_vwap=-19.75
- record_id= code=114090 name=GKL label=pyramid_open_unresolved blocker=profit_not_enough profit=0.01 final=None ai=71.0 tick=0.143 micro_vwap=-17.42
- record_id= code=217590 name=티엠씨 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.1 final=None ai=73.0 tick=0.0 micro_vwap=-180.79
- record_id= code=050890 name=쏠리드 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.25 final=None ai=72.0 tick=0.0 micro_vwap=77.52
- record_id= code=064400 name=LG씨엔에스 label=pyramid_open_unresolved blocker=trend_not_strong profit=2.3 final=None ai=73.0 tick=1.0 micro_vwap=-33.98
- record_id= code=183300 name=코미코 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.98 final=None ai=72.0 tick=0.739 micro_vwap=0.0
- record_id= code=035420 name=NAVER label=pyramid_open_unresolved blocker=profit_not_enough profit=0.44 final=None ai=69.0 tick=0.0 micro_vwap=-89.2
- record_id= code=083450 name=GST label=pyramid_open_unresolved blocker=trend_not_strong profit=5.45 final=None ai=74.0 tick=2.0 micro_vwap=-122.81
- record_id= code=006800 name=미래에셋증권 label=pyramid_open_unresolved blocker=trend_not_strong profit=2.36 final=None ai=73.0 tick=1.0 micro_vwap=-11.38
- record_id= code=080580 name=오킨스전자 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.04 final=None ai=75.0 tick=0.0 micro_vwap=-63.78
- record_id= code=031980 name=피에스케이홀딩스 label=pyramid_open_unresolved blocker=trend_not_strong profit=2.63 final=None ai=70.0 tick=0.0 micro_vwap=-26.03
- record_id= code=160980 name=싸이맥스 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.12 final=None ai=71.0 tick=1.25 micro_vwap=-113.55
- record_id= code=025560 name=미래산업 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.03 final=None ai=58.0 tick=3.5 micro_vwap=-86.13
- record_id= code=005290 name=동진쎄미켐 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.3 final=None ai=73.0 tick=1.0 micro_vwap=-64.32
- record_id= code=417840 name=저스템 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.29 final=None ai=74.0 tick=2.25 micro_vwap=-17.54
- record_id= code=141080 name=리가켐바이오 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.21 final=None ai=73.0 tick=0.0 micro_vwap=-79.17
- record_id= code=353200 name=대덕전자 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.73 final=None ai=73.0 tick=3.0 micro_vwap=-120.82
- record_id= code=490470 name=세미파이브 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.14 final=None ai=72.0 tick=1.556 micro_vwap=-42.4
- record_id= code=399720 name=가온칩스 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.33 final=None ai=69.0 tick=0.0 micro_vwap=-556.47
- record_id= code=039440 name=에스티아이 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.11 final=None ai=59.0 tick=0.368 micro_vwap=-5.33
- record_id= code=319660 name=피에스케이 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.99 final=None ai=70.0 tick=4.0 micro_vwap=-68.53
- record_id=10058 code=222800 name=심텍 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=0.15 final=-1.96 ai=72.0 tick=1.0 micro_vwap=2.08
- record_id= code=484590 name=삼양컴텍 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.37 final=None ai=68.0 tick=0.75 micro_vwap=-59.04
- record_id= code=200470 name=에이팩트 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.37 final=None ai=74.0 tick=0.0 micro_vwap=-999.0
- record_id= code=059090 name=미코 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.18 final=None ai=64.0 tick=0.0 micro_vwap=-999.0
- record_id= code=196170 name=알테오젠 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.06 final=None ai=72.0 tick=0.286 micro_vwap=-69.98
- record_id= code=288180 name=케이피항공산업 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.11 final=None ai=73.0 tick=0.5 micro_vwap=29.06
- record_id= code=042660 name=한화오션 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.32 final=None ai=72.0 tick=0.667 micro_vwap=-27.16
- record_id= code=034020 name=두산에너빌리티 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.7 final=None ai=73.0 tick=0.0 micro_vwap=-9.1
- record_id= code=463480 name=모티브링크 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.11 final=None ai=65.0 tick=1.968 micro_vwap=-37.92
- record_id= code=078350 name=한양디지텍 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.32 final=None ai=71.0 tick=0.6 micro_vwap=-96.09
- record_id=10171 code=125490 name=한라캐스트 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=0.08 final=-2.39 ai=70.0 tick=2.0 micro_vwap=-39.22
- record_id= code=122640 name=예스티 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.7 final=None ai=70.0 tick=0.833 micro_vwap=24.25
- record_id= code=377300 name=카카오페이 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.04 final=None ai=68.0 tick=0.778 micro_vwap=0.23
- record_id= code=475830 name=오름테라퓨틱 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.15 final=None ai=70.0 tick=5.0 micro_vwap=-44.14
- record_id= code=281820 name=케이씨텍 label=pyramid_open_unresolved blocker=trend_not_strong profit=4.1 final=None ai=67.0 tick=0.0 micro_vwap=0.4
- record_id= code=131970 name=두산테스나 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.11 final=None ai=58.0 tick=4.0 micro_vwap=-12.83
- record_id= code=195870 name=해성디에스 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.27 final=None ai=66.0 tick=2.0 micro_vwap=-59.64
- record_id= code=251370 name=와이엠티 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.44 final=None ai=71.0 tick=0.463 micro_vwap=-40.58
- record_id= code=005930 name=삼성전자 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.1 final=None ai=74.0 tick=0.0 micro_vwap=-16.77
- record_id= code=114810 name=한솔아이원스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.09 final=None ai=59.0 tick=0.25 micro_vwap=-8.43
- record_id= code=222800 name=심텍 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.22 final=None ai=73.0 tick=2.0 micro_vwap=-28.81
- record_id= code=330860 name=네패스아크 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.41 final=None ai=75.0 tick=0.429 micro_vwap=-17.36
- record_id= code=030530 name=원익홀딩스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.6 final=None ai=70.0 tick=0.0 micro_vwap=-60.05
- record_id= code=456160 name=지투지바이오 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.21 final=None ai=66.0 tick=0.0 micro_vwap=53.72
- record_id= code=240810 name=원익IPS label=pyramid_open_unresolved blocker=trend_not_strong profit=3.87 final=None ai=69.0 tick=1.0 micro_vwap=-43.11
- record_id= code=000660 name=SK하이닉스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.15 final=None ai=73.0 tick=0.0 micro_vwap=41.55
- record_id= code=475150 name=SK이터닉스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.01 final=None ai=62.0 tick=3.0 micro_vwap=8.12
- record_id= code=005380 name=현대차 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.11 final=None ai=66.0 tick=0.25 micro_vwap=10.04
- record_id= code=036200 name=유니셈 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.23 final=None ai=68.0 tick=1.667 micro_vwap=-21.47
- record_id= code=036710 name=심텍홀딩스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.37 final=None ai=70.0 tick=0.64 micro_vwap=0.0
- record_id= code=067310 name=하나마이크론 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.18 final=None ai=66.0 tick=0.333 micro_vwap=-10.64
- record_id= code=187870 name=디바이스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.58 final=None ai=70.0 tick=1.76 micro_vwap=-47.1
- record_id= code=252990 name=샘씨엔에스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.53 final=None ai=67.0 tick=1.25 micro_vwap=10.43
- record_id= code=166090 name=하나머티리얼즈 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.43 final=None ai=64.0 tick=0.667 micro_vwap=-40.52
- record_id= code=147760 name=피엠티 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.48 final=None ai=65.0 tick=2.909 micro_vwap=73.88
- record_id= code=064290 name=인텍플러스 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.14 final=None ai=72.0 tick=1.667 micro_vwap=26.74
- record_id= code=086520 name=에코프로 label=pyramid_open_unresolved blocker=trend_not_strong profit=3.22 final=None ai=74.0 tick=1.0 micro_vwap=-45.73
- record_id= code=124500 name=아이티센글로벌 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.08 final=None ai=65.0 tick=1.0 micro_vwap=-20.92
- record_id= code=290650 name=엘앤씨바이오 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.87 final=None ai=60.0 tick=0.0 micro_vwap=-999.0
- record_id= code=170920 name=엘티씨 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.11 final=None ai=73.0 tick=0.6 micro_vwap=-41.61
- record_id= code=043260 name=성호전자 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.1 final=None ai=62.0 tick=0.0 micro_vwap=-999.0
- record_id= code=066570 name=LG전자 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.22 final=None ai=66.0 tick=1.0 micro_vwap=-3.2
- record_id= code=443060 name=HD현대마린솔루션 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.17 final=None ai=62.0 tick=1.0 micro_vwap=21.0
- record_id= code=036930 name=주성엔지니어링 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.17 final=None ai=60.0 tick=0.0 micro_vwap=30.11
- record_id= code=040350 name=크레오에스지 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.13 final=None ai=61.0 tick=4.0 micro_vwap=-43.76
- record_id= code=084370 name=유진테크 label=pyramid_open_unresolved blocker=trend_not_strong profit=1.87 final=None ai=76.0 tick=0.333 micro_vwap=-53.34
- record_id= code=358570 name=지아이이노베이션 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.8 final=None ai=67.0 tick=2.0 micro_vwap=-295.02
- record_id= code=039030 name=이오테크닉스 label=pyramid_open_unresolved blocker=trend_not_strong profit=1.8 final=None ai=74.0 tick=1.0 micro_vwap=-34.99
- record_id= code=131290 name=티에스이 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.11 final=None ai=74.0 tick=1.0 micro_vwap=-42.22
- record_id= code=098460 name=고영 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.06 final=None ai=74.0 tick=1.0 micro_vwap=-23.87
- record_id= code=356860 name=티엘비 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.92 final=None ai=68.0 tick=5.0 micro_vwap=-37.57
- record_id= code=125490 name=한라캐스트 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.07 final=None ai=72.0 tick=0.667 micro_vwap=-19.28
- record_id= code=011790 name=SKC label=pyramid_open_unresolved blocker=profit_not_enough profit=0.07 final=None ai=72.0 tick=1.0 micro_vwap=1.43
- record_id= code=007810 name=코리아써키트 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.31 final=None ai=73.0 tick=1.5 micro_vwap=15.37
- record_id= code=348370 name=엔켐 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.05 final=None ai=63.0 tick=1.0 micro_vwap=-47.98
- record_id= code=425420 name=티에프이 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.3 final=None ai=65.0 tick=16.0 micro_vwap=26.66
- record_id= code=319400 name=현대무벡스 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.39 final=None ai=73.0 tick=0.0 micro_vwap=-70.49
- record_id= code=041510 name=에스엠 label=pyramid_open_unresolved blocker=profit_not_enough profit=-0.0 final=None ai=74.0 tick=2.0 micro_vwap=-29.86
- record_id= code=001820 name=삼화콘덴서 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.44 final=None ai=70.0 tick=0.0 micro_vwap=-32.73
- record_id= code=011070 name=LG이노텍 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.24 final=None ai=66.0 tick=1.0 micro_vwap=-19.08
- record_id= code=005950 name=이수화학 label=pyramid_open_unresolved blocker=trend_not_strong profit=1.8 final=None ai=68.0 tick=0.167 micro_vwap=-22.66
- record_id= code=361610 name=SK아이이테크놀로지 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.95 final=None ai=67.0 tick=1.0 micro_vwap=53.59
- record_id= code=033160 name=엠케이전자 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.13 final=None ai=69.0 tick=0.333 micro_vwap=61.64
- record_id= code=093370 name=후성 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.02 final=None ai=60.0 tick=1.0 micro_vwap=-25.61
- record_id= code=009150 name=삼성전기 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.22 final=None ai=76.0 tick=2.0 micro_vwap=13.06
- record_id= code=161890 name=한국콜마 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.7 final=None ai=67.0 tick=2.333 micro_vwap=-19.13
- record_id= code=007660 name=이수페타시스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.1 final=None ai=73.0 tick=1.0 micro_vwap=28.84
- record_id= code=081660 name=미스토홀딩스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.22 final=None ai=71.0 tick=1.0 micro_vwap=13.63
- record_id= code=347700 name=스피어 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.16 final=None ai=66.0 tick=0.0 micro_vwap=14.21
- record_id= code=402340 name=SK스퀘어 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.52 final=None ai=60.0 tick=0.0 micro_vwap=-999.0
- record_id= code=100790 name=미래에셋벤처투자 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.37 final=None ai=62.0 tick=0.0 micro_vwap=-999.0
- record_id= code=388790 name=라이콤 label=pyramid_open_unresolved blocker=scalping_cutoff profit=1.28 final=None ai=70.0 tick=0.667 micro_vwap=-24.16

## One Share Opportunity Rows
