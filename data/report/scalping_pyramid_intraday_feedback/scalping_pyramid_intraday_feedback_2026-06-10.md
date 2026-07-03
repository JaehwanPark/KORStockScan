# 2026-06-10 Scalping Pyramid Intraday Feedback

- generated_at: 2026-07-03T13:22:59+09:00
- decision_authority: source_only_pyramid_intraday_feedback_no_runtime_mutation
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: intraday_threshold_mutation, intraday_runtime_apply, hard_safety_relaxation, broker_guard_bypass, order_guard_relaxation, stale_quote_bypass, cooldown_bypass, quantity_guard_relaxation, position_cap_release, provider_route_change, bot_restart, real_execution_quality_approval

## Summary

- pyramid_feedback_row_count: 89
- closed_pyramid_row_count: 9
- pyramid_would_have_helped_count: 0
- pyramid_correctly_blocked_count: 0
- pyramid_overheat_or_reversal_risk_count: 9
- pyramid_open_unresolved_count: 80
- one_share_event_count: 0
- one_share_closed_count: 0
- one_share_pyramid_opportunity_count: 0
- one_share_pyramid_missed_upside_count: 0
- one_share_pyramid_missed_upside_rate: 0.00
- one_share_pyramid_avg_opportunity_cost_pct: 0.00

## Blocker Metrics

- blocker=add_judgment_locked sample=5 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=profit_not_enough sample=65 recovered_rate=0.00 reversal_rate=0.06 blocked_then_recovered_rate=0.00
- blocker=scalping_cutoff sample=10 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=trend_not_strong sample=9 recovered_rate=0.00 reversal_rate=0.56 blocked_then_recovered_rate=0.00

## Rows

- record_id= code=272210 name=한화시스템 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.21 final=None ai=71.0 tick=0.5 micro_vwap=-1.09
- record_id= code=067310 name=하나마이크론 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.0 final=None ai=75.0 tick=0.5 micro_vwap=3.12
- record_id= code=476080 name=M83 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.08 final=None ai=66.0 tick=0.429 micro_vwap=-1.63
- record_id= code=112610 name=씨에스윈드 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.0 final=None ai=69.0 tick=4.0 micro_vwap=-85.25
- record_id= code=077360 name=덕산하이메탈 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.13 final=None ai=74.0 tick=2.333 micro_vwap=-112.11
- record_id= code=178320 name=서진시스템 label=pyramid_open_unresolved blocker=add_judgment_locked profit=0.17 final=None ai=71.0 tick=0.0 micro_vwap=-41.74
- record_id= code=007390 name=네이처셀 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.08 final=None ai=65.0 tick=3.0 micro_vwap=-122.99
- record_id= code=002220 name=한일철강 label=pyramid_open_unresolved blocker=add_judgment_locked profit=2.83 final=None ai=65.0 tick=0.0 micro_vwap=-999.0
- record_id= code=267270 name=HD건설기계 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.12 final=None ai=66.0 tick=0.0 micro_vwap=7.06
- record_id= code=088130 name=동아엘텍 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.91 final=None ai=62.0 tick=0.0 micro_vwap=-999.0
- record_id= code=010690 name=화신 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.13 final=None ai=76.0 tick=2.0 micro_vwap=-55.45
- record_id= code=319400 name=현대무벡스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.18 final=None ai=75.0 tick=2.0 micro_vwap=-35.52
- record_id= code=090710 name=휴림로봇 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.68 final=None ai=73.0 tick=2.0 micro_vwap=-66.78
- record_id= code=120110 name=코오롱인더 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.21 final=None ai=70.0 tick=0.4 micro_vwap=-99.16
- record_id= code=062040 name=산일전기 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.86 final=None ai=60.0 tick=1.6 micro_vwap=3.93
- record_id= code=240810 name=원익IPS label=pyramid_open_unresolved blocker=trend_not_strong profit=2.4 final=None ai=69.0 tick=0.667 micro_vwap=-11.03
- record_id=9886 code=131970 name=두산테스나 label=pyramid_overheat_or_reversal_risk blocker=trend_not_strong profit=3.44 final=3.22 ai=73.0 tick=0.0 micro_vwap=-76.74
- record_id= code=064400 name=LG씨엔에스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.08 final=None ai=73.0 tick=0.5 micro_vwap=14.23
- record_id= code=489790 name=한화비전 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.34 final=None ai=73.0 tick=1.167 micro_vwap=-24.06
- record_id=9860 code=011070 name=LG이노텍 label=pyramid_overheat_or_reversal_risk blocker=trend_not_strong profit=2.3 final=2.2 ai=68.0 tick=2.0 micro_vwap=-7.72
- record_id= code=005690 name=파미셀 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.35 final=None ai=72.0 tick=0.312 micro_vwap=-20.84
- record_id= code=475830 name=오름테라퓨틱 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.07 final=None ai=70.0 tick=0.2 micro_vwap=-62.09
- record_id=9865 code=319660 name=피에스케이 label=pyramid_overheat_or_reversal_risk blocker=trend_not_strong profit=3.05 final=2.8 ai=67.0 tick=0.0 micro_vwap=-81.29
- record_id= code=357880 name=SKAI label=pyramid_open_unresolved blocker=profit_not_enough profit=0.96 final=None ai=75.0 tick=1.0 micro_vwap=-101.21
- record_id= code=074600 name=원익QnC label=pyramid_open_unresolved blocker=profit_not_enough profit=0.05 final=None ai=74.0 tick=2.6 micro_vwap=-52.45
- record_id=9851 code=454910 name=두산로보틱스 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=1.41 final=1.04 ai=73.0 tick=2.0 micro_vwap=-26.93
- record_id= code=222800 name=심텍 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.19 final=None ai=72.0 tick=1.0 micro_vwap=-101.24
- record_id= code=454910 name=두산로보틱스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.04 final=None ai=59.0 tick=0.0 micro_vwap=-27.61
- record_id= code=475300 name=SOL 반도체전공정 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.21 final=None ai=74.0 tick=0.955 micro_vwap=-7.26
- record_id= code=455850 name=SOL AI반도체소부장 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.24 final=None ai=73.0 tick=0.5 micro_vwap=-36.74
- record_id= code=017900 name=광전자 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.18 final=None ai=69.0 tick=1.0 micro_vwap=-61.72
- record_id= code=448900 name=한국피아이엠 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.35 final=None ai=66.0 tick=3.0 micro_vwap=-43.32
- record_id= code=475310 name=SOL 반도체후공정 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.09 final=None ai=72.0 tick=1.29 micro_vwap=-28.86
- record_id= code=095610 name=테스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.1 final=None ai=70.0 tick=1.0 micro_vwap=-107.86
- record_id= code=290550 name=디케이티 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.46 final=None ai=73.0 tick=0.667 micro_vwap=-23.66
- record_id= code=000250 name=삼천당제약 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.14 final=None ai=70.0 tick=0.0 micro_vwap=-103.54
- record_id= code=034230 name=파라다이스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.09 final=None ai=67.0 tick=0.545 micro_vwap=-7.89
- record_id= code=119850 name=지엔씨에너지 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.2 final=None ai=63.0 tick=0.381 micro_vwap=-110.2
- record_id= code=089030 name=테크윙 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.59 final=None ai=73.0 tick=0.0 micro_vwap=-32.56
- record_id= code=024060 name=흥구석유 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.1 final=None ai=74.0 tick=0.0 micro_vwap=-32.98
- record_id= code=084370 name=유진테크 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.21 final=None ai=58.0 tick=2.0 micro_vwap=1.42
- record_id= code=194370 name=제이에스코퍼레이션 label=pyramid_open_unresolved blocker=add_judgment_locked profit=0.2 final=None ai=65.0 tick=11.0 micro_vwap=-45.13
- record_id=9948 code=000720 name=현대건설 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=1.06 final=0.68 ai=74.0 tick=1.0 micro_vwap=-25.13
- record_id= code=475150 name=SK이터닉스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.92 final=None ai=69.0 tick=0.55 micro_vwap=0.0
- record_id= code=499790 name=GS피앤엘 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.16 final=None ai=74.0 tick=0.0 micro_vwap=-25.33
- record_id= code=083450 name=GST label=pyramid_open_unresolved blocker=profit_not_enough profit=0.45 final=None ai=71.0 tick=1.167 micro_vwap=-35.41
- record_id= code=069960 name=현대백화점 label=pyramid_open_unresolved blocker=profit_not_enough profit=-0.0 final=None ai=74.0 tick=2.0 micro_vwap=-49.69
- record_id= code=267260 name=HD현대일렉트릭 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.07 final=None ai=76.0 tick=0.75 micro_vwap=-62.05
- record_id= code=125210 name=아모그린텍 label=pyramid_open_unresolved blocker=add_judgment_locked profit=0.21 final=None ai=71.0 tick=1.556 micro_vwap=-2.29
- record_id= code=328130 name=루닛 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.15 final=None ai=72.0 tick=8.0 micro_vwap=-48.39
- record_id= code=042700 name=한미반도체 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.5 final=None ai=60.0 tick=0.0 micro_vwap=-999.0
- record_id= code=319660 name=피에스케이 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.1 final=None ai=65.0 tick=0.0 micro_vwap=-999.0
- record_id= code=310210 name=보로노이 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.08 final=None ai=65.0 tick=0.0 micro_vwap=-32.98
- record_id=9911 code=042700 name=한미반도체 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=0.14 final=-1.89 ai=69.0 tick=0.5 micro_vwap=-27.38
- record_id=9973 code=006220 name=제주은행 label=pyramid_overheat_or_reversal_risk blocker=trend_not_strong profit=4.9 final=4.82 ai=75.0 tick=0.0 micro_vwap=-73.02
- record_id= code=030960 name=양지사 label=pyramid_open_unresolved blocker=trend_not_strong profit=2.45 final=None ai=67.0 tick=1.125 micro_vwap=-53.23
- record_id= code=279570 name=케이뱅크 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.23 final=None ai=51.0 tick=1.0 micro_vwap=-30.16
- record_id= code=000660 name=SK하이닉스 label=pyramid_open_unresolved blocker=add_judgment_locked profit=0.02 final=None ai=73.0 tick=0.0 micro_vwap=1.97
- record_id= code=009150 name=삼성전기 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.21 final=None ai=63.0 tick=0.0 micro_vwap=-42.23
- record_id=9994 code=006220 name=제주은행 label=pyramid_overheat_or_reversal_risk blocker=trend_not_strong profit=3.1 final=2.03 ai=52.0 tick=1.0 micro_vwap=-59.87
- record_id=9961 code=319660 name=피에스케이 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=0.3 final=-1.82 ai=71.0 tick=2.0 micro_vwap=-3.99
- record_id= code=307950 name=현대오토에버 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.12 final=None ai=62.0 tick=0.0 micro_vwap=-999.0
- record_id= code=183300 name=코미코 label=pyramid_open_unresolved blocker=trend_not_strong profit=2.47 final=None ai=73.0 tick=0.6 micro_vwap=-41.48
- record_id= code=443060 name=HD현대마린솔루션 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.11 final=None ai=61.0 tick=0.75 micro_vwap=-5.87
- record_id= code=093370 name=후성 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.19 final=None ai=51.0 tick=1.0 micro_vwap=-32.56
- record_id= code=114810 name=한솔아이원스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.14 final=None ai=70.0 tick=0.0 micro_vwap=-10.45
- record_id= code=420770 name=기가비스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.3 final=None ai=72.0 tick=5.0 micro_vwap=-61.19
- record_id= code=417860 name=오브젠 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.54 final=None ai=61.0 tick=2.0 micro_vwap=-179.23
- record_id= code=036930 name=주성엔지니어링 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.12 final=None ai=67.0 tick=0.0 micro_vwap=27.54
- record_id= code=089970 name=브이엠 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.02 final=None ai=64.0 tick=1.0 micro_vwap=-11.0
- record_id= code=006220 name=제주은행 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.08 final=None ai=55.0 tick=0.0 micro_vwap=-78.99
- record_id= code=100090 name=SK오션플랜트 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.1 final=None ai=70.0 tick=1.0 micro_vwap=-51.38
- record_id= code=000720 name=현대건설 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.0 final=None ai=68.0 tick=4.0 micro_vwap=39.09
- record_id= code=217590 name=티엠씨 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.44 final=None ai=69.0 tick=0.0 micro_vwap=17.48
- record_id= code=042660 name=한화오션 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.14 final=None ai=61.0 tick=0.333 micro_vwap=18.13
- record_id= code=008830 name=대동기어 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.08 final=None ai=55.0 tick=0.595 micro_vwap=18.03
- record_id= code=295310 name=에이치브이엠 label=pyramid_open_unresolved blocker=trend_not_strong profit=1.57 final=None ai=52.0 tick=0.182 micro_vwap=-45.82
- record_id= code=011070 name=LG이노텍 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.44 final=None ai=71.0 tick=3.0 micro_vwap=43.36
- record_id= code=017890 name=한국알콜 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.51 final=None ai=70.0 tick=0.524 micro_vwap=4.07
- record_id= code=131970 name=두산테스나 label=pyramid_open_unresolved blocker=scalping_cutoff profit=0.45 final=None ai=61.0 tick=1.0 micro_vwap=18.9
- record_id= code=347700 name=스피어 label=pyramid_open_unresolved blocker=scalping_cutoff profit=0.96 final=None ai=63.0 tick=2.0 micro_vwap=-29.26
- record_id= code=031980 name=피에스케이홀딩스 label=pyramid_open_unresolved blocker=scalping_cutoff profit=0.28 final=None ai=72.0 tick=1.0 micro_vwap=12.01
- record_id= code=059090 name=미코 label=pyramid_open_unresolved blocker=scalping_cutoff profit=1.32 final=None ai=64.0 tick=2.0 micro_vwap=-33.31
- record_id= code=047810 name=한국항공우주 label=pyramid_open_unresolved blocker=scalping_cutoff profit=0.14 final=None ai=56.0 tick=0.667 micro_vwap=30.33
- record_id= code=010120 name=LS ELECTRIC label=pyramid_open_unresolved blocker=scalping_cutoff profit=0.64 final=None ai=70.0 tick=1.0 micro_vwap=30.18
- record_id= code=041830 name=인바디 label=pyramid_open_unresolved blocker=scalping_cutoff profit=0.21 final=None ai=70.0 tick=2.0 micro_vwap=24.98
- record_id= code=402340 name=SK스퀘어 label=pyramid_open_unresolved blocker=scalping_cutoff profit=1.33 final=None ai=68.0 tick=2.0 micro_vwap=30.28
- record_id= code=437730 name=삼현 label=pyramid_open_unresolved blocker=scalping_cutoff profit=0.69 final=None ai=69.0 tick=1.071 micro_vwap=1.44
- record_id= code=336370 name=솔루스첨단소재 label=pyramid_open_unresolved blocker=scalping_cutoff profit=0.05 final=None ai=72.0 tick=0.0 micro_vwap=37.28

## One Share Opportunity Rows
