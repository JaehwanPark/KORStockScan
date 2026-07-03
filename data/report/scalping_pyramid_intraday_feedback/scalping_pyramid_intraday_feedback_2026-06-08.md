# 2026-06-08 Scalping Pyramid Intraday Feedback

- generated_at: 2026-07-03T13:22:41+09:00
- decision_authority: source_only_pyramid_intraday_feedback_no_runtime_mutation
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: intraday_threshold_mutation, intraday_runtime_apply, hard_safety_relaxation, broker_guard_bypass, order_guard_relaxation, stale_quote_bypass, cooldown_bypass, quantity_guard_relaxation, position_cap_release, provider_route_change, bot_restart, real_execution_quality_approval

## Summary

- pyramid_feedback_row_count: 87
- closed_pyramid_row_count: 19
- pyramid_would_have_helped_count: 5
- pyramid_correctly_blocked_count: 0
- pyramid_overheat_or_reversal_risk_count: 14
- pyramid_open_unresolved_count: 68
- one_share_event_count: 0
- one_share_closed_count: 0
- one_share_pyramid_opportunity_count: 0
- one_share_pyramid_missed_upside_count: 0
- one_share_pyramid_missed_upside_rate: 0.00
- one_share_pyramid_avg_opportunity_cost_pct: 0.00

## Blocker Metrics

- blocker=add_judgment_locked sample=5 recovered_rate=0.00 reversal_rate=0.40 blocked_then_recovered_rate=0.00
- blocker=profit_not_enough sample=72 recovered_rate=0.04 reversal_rate=0.15 blocked_then_recovered_rate=0.04
- blocker=scalping_cutoff sample=3 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=trend_not_strong sample=7 recovered_rate=0.29 reversal_rate=0.14 blocked_then_recovered_rate=0.29

## Rows

- record_id= code=052020 name=에스티큐브 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.22 final=None ai=74.0 tick=0.0 micro_vwap=-113.53
- record_id= code=010170 name=대한광통신 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.24 final=None ai=62.0 tick=0.0 micro_vwap=-999.0
- record_id= code=240810 name=원익IPS label=pyramid_open_unresolved blocker=profit_not_enough profit=0.17 final=None ai=67.0 tick=3.0 micro_vwap=-56.99
- record_id= code=043260 name=성호전자 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.2 final=None ai=72.0 tick=1.0 micro_vwap=-19.52
- record_id= code=089970 name=브이엠 label=pyramid_open_unresolved blocker=add_judgment_locked profit=3.4 final=None ai=64.0 tick=0.5 micro_vwap=-88.7
- record_id= code=090710 name=휴림로봇 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.52 final=None ai=73.0 tick=1.0 micro_vwap=-34.5
- record_id= code=095610 name=테스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.13 final=None ai=72.0 tick=1.0 micro_vwap=-21.07
- record_id= code=092190 name=서울바이오시스 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.38 final=None ai=73.0 tick=4.429 micro_vwap=-40.31
- record_id= code=086520 name=에코프로 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.32 final=None ai=73.0 tick=4.0 micro_vwap=-40.23
- record_id= code=027360 name=아주IB투자 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.47 final=None ai=71.0 tick=0.333 micro_vwap=30.33
- record_id= code=036930 name=주성엔지니어링 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.2 final=None ai=72.0 tick=1.0 micro_vwap=70.97
- record_id=9405 code=064400 name=LG씨엔에스 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=0.76 final=-2.67 ai=75.0 tick=1.0 micro_vwap=-64.24
- record_id= code=067310 name=하나마이크론 label=pyramid_open_unresolved blocker=add_judgment_locked profit=0.26 final=None ai=73.0 tick=0.857 micro_vwap=-69.0
- record_id=9390 code=454910 name=두산로보틱스 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=0.36 final=-2.51 ai=75.0 tick=0.0 micro_vwap=-82.6
- record_id= code=417860 name=오브젠 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.45 final=None ai=73.0 tick=0.853 micro_vwap=0.0
- record_id=9393 code=017670 name=SK텔레콤 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=1.24 final=0.51 ai=71.0 tick=1.0 micro_vwap=-34.71
- record_id= code=272110 name=케이엔제이 label=pyramid_open_unresolved blocker=add_judgment_locked profit=1.69 final=None ai=68.0 tick=2.222 micro_vwap=44.25
- record_id=9480 code=064400 name=LG씨엔에스 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=1.17 final=0.71 ai=66.0 tick=0.0 micro_vwap=-26.39
- record_id=9411 code=011070 name=LG이노텍 label=pyramid_would_have_helped blocker=trend_not_strong profit=2.83 final=4.04 ai=76.0 tick=1.0 micro_vwap=-17.9
- record_id=9481 code=454910 name=두산로보틱스 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=1.21 final=1.1 ai=64.0 tick=0.0 micro_vwap=-9.15
- record_id=9484 code=017670 name=SK텔레콤 label=pyramid_overheat_or_reversal_risk blocker=trend_not_strong profit=2.45 final=1.29 ai=68.0 tick=0.0 micro_vwap=-111.88
- record_id= code=090360 name=로보스타 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.19 final=None ai=76.0 tick=0.0 micro_vwap=-56.36
- record_id= code=225570 name=넥슨게임즈 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.37 final=None ai=70.0 tick=0.089 micro_vwap=-3.06
- record_id= code=100790 name=미래에셋벤처투자 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.33 final=None ai=68.0 tick=1.0 micro_vwap=-60.25
- record_id=9489 code=064400 name=LG씨엔에스 label=pyramid_would_have_helped blocker=profit_not_enough profit=0.13 final=1.12 ai=73.0 tick=0.0 micro_vwap=-20.62
- record_id= code=454910 name=두산로보틱스 label=pyramid_open_unresolved blocker=trend_not_strong profit=1.68 final=None ai=68.0 tick=0.0 micro_vwap=-43.13
- record_id= code=017900 name=광전자 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.41 final=None ai=73.0 tick=1.7 micro_vwap=-27.19
- record_id= code=005090 name=SGC에너지 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.75 final=None ai=71.0 tick=0.5 micro_vwap=-44.46
- record_id=9490 code=454910 name=두산로보틱스 label=pyramid_would_have_helped blocker=profit_not_enough profit=0.47 final=1.39 ai=72.0 tick=0.0 micro_vwap=47.26
- record_id= code=005930 name=삼성전자 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.01 final=None ai=73.0 tick=0.0 micro_vwap=-44.15
- record_id= code=046970 name=우리로 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.21 final=None ai=72.0 tick=1.455 micro_vwap=-51.18
- record_id= code=066570 name=LG전자 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.12 final=None ai=71.0 tick=0.0 micro_vwap=-32.92
- record_id= code=064400 name=LG씨엔에스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.4 final=None ai=76.0 tick=1.0 micro_vwap=-12.16
- record_id=9492 code=017670 name=SK텔레콤 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=0.04 final=-1.74 ai=52.0 tick=2.0 micro_vwap=4.63
- record_id= code=024060 name=흥구석유 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.44 final=None ai=72.0 tick=1.615 micro_vwap=25.99
- record_id= code=494340 name=ACE 글로벌AI맞춤형반도체 label=pyramid_open_unresolved blocker=profit_not_enough profit=-0.0 final=None ai=73.0 tick=0.625 micro_vwap=-13.9
- record_id= code=173130 name=오파스넷 label=pyramid_open_unresolved blocker=trend_not_strong profit=2.02 final=None ai=72.0 tick=1.778 micro_vwap=-38.21
- record_id=9391 code=090360 name=로보스타 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=0.23 final=-2.28 ai=60.0 tick=1.0 micro_vwap=-40.52
- record_id= code=462350 name=이노스페이스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.15 final=None ai=69.0 tick=0.0 micro_vwap=-38.72
- record_id= code=353200 name=대덕전자 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.67 final=None ai=62.0 tick=0.0 micro_vwap=-999.0
- record_id= code=002220 name=한일철강 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.69 final=None ai=66.0 tick=0.0 micro_vwap=-93.11
- record_id= code=052710 name=아모텍 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.49 final=None ai=73.0 tick=4.0 micro_vwap=-60.16
- record_id= code=012330 name=현대모비스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.25 final=None ai=76.0 tick=1.0 micro_vwap=-26.72
- record_id= code=031330 name=에스에이엠티 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.49 final=None ai=73.0 tick=0.0 micro_vwap=-15.43
- record_id= code=007390 name=네이처셀 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.83 final=None ai=68.0 tick=5.667 micro_vwap=-15.83
- record_id= code=403870 name=HPSP label=pyramid_open_unresolved blocker=profit_not_enough profit=0.81 final=None ai=73.0 tick=3.75 micro_vwap=-22.06
- record_id= code=332570 name=PS일렉트로닉스 label=pyramid_open_unresolved blocker=trend_not_strong profit=2.26 final=None ai=72.0 tick=49.0 micro_vwap=-68.53
- record_id= code=476080 name=M83 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.08 final=None ai=78.0 tick=0.0 micro_vwap=-999.0
- record_id=9416 code=010170 name=대한광통신 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=0.0 final=-1.73 ai=60.0 tick=0.25 micro_vwap=-12.92
- record_id=9494 code=064400 name=LG씨엔에스 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=0.04 final=-1.95 ai=74.0 tick=3.0 micro_vwap=-24.96
- record_id= code=077360 name=덕산하이메탈 label=pyramid_open_unresolved blocker=trend_not_strong profit=2.95 final=None ai=72.0 tick=1.25 micro_vwap=-16.16
- record_id= code=440110 name=파두 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.41 final=None ai=70.0 tick=0.0 micro_vwap=-15.93
- record_id= code=034020 name=두산에너빌리티 label=pyramid_open_unresolved blocker=profit_not_enough profit=-0.0 final=None ai=72.0 tick=1.0 micro_vwap=-18.58
- record_id= code=125490 name=한라캐스트 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.04 final=None ai=73.0 tick=0.0 micro_vwap=-27.27
- record_id= code=092200 name=디아이씨 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.31 final=None ai=62.0 tick=0.0 micro_vwap=-999.0
- record_id=9463 code=222800 name=심텍 label=pyramid_would_have_helped blocker=profit_not_enough profit=0.43 final=0.52 ai=74.0 tick=2.333 micro_vwap=10.17
- record_id= code=030960 name=양지사 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.11 final=None ai=72.0 tick=2.667 micro_vwap=-128.16
- record_id= code=000660 name=SK하이닉스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.17 final=None ai=73.0 tick=0.0 micro_vwap=25.26
- record_id= code=001740 name=SK네트웍스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.72 final=None ai=78.0 tick=0.0 micro_vwap=-999.0
- record_id= code=017670 name=SK텔레콤 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.31 final=None ai=75.0 tick=0.0 micro_vwap=-27.99
- record_id=9499 code=017670 name=SK텔레콤 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=1.4 final=1.22 ai=71.0 tick=0.0 micro_vwap=-83.09
- record_id= code=054920 name=한컴위드 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.08 final=None ai=69.0 tick=0.0 micro_vwap=-102.92
- record_id= code=457370 name=한켐 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.05 final=None ai=74.0 tick=3.0 micro_vwap=-19.3
- record_id= code=108490 name=로보티즈 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.27 final=None ai=62.0 tick=1.0 micro_vwap=-25.56
- record_id= code=200470 name=에이팩트 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.0 final=None ai=67.0 tick=0.5 micro_vwap=-22.3
- record_id= code=035420 name=NAVER label=pyramid_open_unresolved blocker=profit_not_enough profit=0.12 final=None ai=74.0 tick=0.0 micro_vwap=-24.03
- record_id= code=080220 name=제주반도체 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.28 final=None ai=59.0 tick=0.0 micro_vwap=-18.61
- record_id=9470 code=353200 name=대덕전자 label=pyramid_overheat_or_reversal_risk blocker=add_judgment_locked profit=0.11 final=-2.16 ai=72.0 tick=3.0 micro_vwap=-27.86
- record_id= code=005380 name=현대차 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.08 final=None ai=73.0 tick=0.0 micro_vwap=-43.98
- record_id= code=032580 name=피델릭스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.14 final=None ai=65.0 tick=0.259 micro_vwap=-67.98
- record_id=9439 code=092200 name=디아이씨 label=pyramid_overheat_or_reversal_risk blocker=add_judgment_locked profit=0.15 final=-2.05 ai=57.0 tick=0.111 micro_vwap=-38.95
- record_id= code=320000 name=한울반도체 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.28 final=None ai=65.0 tick=1.5 micro_vwap=-11.18
- record_id=9426 code=001740 name=SK네트웍스 label=pyramid_would_have_helped blocker=trend_not_strong profit=3.66 final=4.03 ai=78.0 tick=0.667 micro_vwap=0.0
- record_id= code=039860 name=나노엔텍 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.35 final=None ai=65.0 tick=0.0 micro_vwap=-62.26
- record_id= code=328130 name=루닛 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.22 final=None ai=72.0 tick=0.0 micro_vwap=-100.33
- record_id= code=222800 name=심텍 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.24 final=None ai=73.0 tick=4.0 micro_vwap=-95.3
- record_id= code=388790 name=라이콤 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.45 final=None ai=72.0 tick=0.0 micro_vwap=-272.0
- record_id= code=040350 name=크레오에스지 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.43 final=None ai=66.0 tick=0.167 micro_vwap=-9.2
- record_id= code=036170 name=에이치엠넥스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.86 final=None ai=59.0 tick=1.5 micro_vwap=-165.15
- record_id= code=085620 name=미래에셋생명 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.24 final=None ai=75.0 tick=1.0 micro_vwap=-73.97
- record_id= code=025560 name=미래산업 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.71 final=None ai=72.0 tick=3.692 micro_vwap=-62.13
- record_id= code=242040 name=나무기술 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.89 final=None ai=72.0 tick=0.0 micro_vwap=-295.7
- record_id= code=003220 name=대원제약 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.16 final=None ai=75.0 tick=0.0 micro_vwap=-108.17
- record_id=9488 code=011070 name=LG이노텍 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=0.87 final=0.5 ai=76.0 tick=0.0 micro_vwap=-14.01
- record_id= code=009150 name=삼성전기 label=pyramid_open_unresolved blocker=scalping_cutoff profit=0.43 final=None ai=72.0 tick=0.0 micro_vwap=-26.13
- record_id= code=011070 name=LG이노텍 label=pyramid_open_unresolved blocker=scalping_cutoff profit=0.13 final=None ai=58.0 tick=0.0 micro_vwap=-79.3
- record_id= code=001820 name=삼화콘덴서 label=pyramid_open_unresolved blocker=scalping_cutoff profit=0.78 final=None ai=76.0 tick=1.0 micro_vwap=-84.75

## One Share Opportunity Rows
