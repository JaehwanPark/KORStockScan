# 2026-06-12 Scalping Pyramid Intraday Feedback

- generated_at: 2026-07-03T13:23:16+09:00
- decision_authority: source_only_pyramid_intraday_feedback_no_runtime_mutation
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: intraday_threshold_mutation, intraday_runtime_apply, hard_safety_relaxation, broker_guard_bypass, order_guard_relaxation, stale_quote_bypass, cooldown_bypass, quantity_guard_relaxation, position_cap_release, provider_route_change, bot_restart, real_execution_quality_approval

## Summary

- pyramid_feedback_row_count: 93
- closed_pyramid_row_count: 1
- pyramid_would_have_helped_count: 0
- pyramid_correctly_blocked_count: 0
- pyramid_overheat_or_reversal_risk_count: 1
- pyramid_open_unresolved_count: 92
- one_share_event_count: 0
- one_share_closed_count: 0
- one_share_pyramid_opportunity_count: 0
- one_share_pyramid_missed_upside_count: 0
- one_share_pyramid_missed_upside_rate: 0.00
- one_share_pyramid_avg_opportunity_cost_pct: 0.00

## Blocker Metrics

- blocker=profit_not_enough sample=85 recovered_rate=0.00 reversal_rate=0.01 blocked_then_recovered_rate=0.00
- blocker=scalping_cutoff sample=3 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=trend_not_strong sample=5 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00

## Rows

- record_id= code=006800 name=미래에셋증권 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.86 final=None ai=74.0 tick=0.0 micro_vwap=81.8
- record_id= code=000720 name=현대건설 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.21 final=None ai=71.0 tick=0.0 micro_vwap=209.74
- record_id= code=204320 name=HL만도 label=pyramid_open_unresolved blocker=trend_not_strong profit=5.58 final=None ai=70.0 tick=2.0 micro_vwap=-307.69
- record_id= code=085620 name=미래에셋생명 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.32 final=None ai=72.0 tick=0.0 micro_vwap=-459.14
- record_id= code=101490 name=에스앤에스텍 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.36 final=None ai=70.0 tick=0.0 micro_vwap=-92.16
- record_id= code=192650 name=드림텍 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.53 final=None ai=69.0 tick=0.0 micro_vwap=-3.75
- record_id= code=004710 name=한솔테크닉스 label=pyramid_open_unresolved blocker=trend_not_strong profit=2.56 final=None ai=71.0 tick=8.0 micro_vwap=-52.48
- record_id= code=082920 name=비츠로셀 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.79 final=None ai=72.0 tick=0.0 micro_vwap=-33.19
- record_id= code=003670 name=포스코퓨처엠 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.01 final=None ai=67.0 tick=0.833 micro_vwap=6.06
- record_id= code=126640 name=화신정공 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.08 final=None ai=64.0 tick=0.0 micro_vwap=-999.0
- record_id= code=034220 name=LG디스플레이 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.06 final=None ai=75.0 tick=0.5 micro_vwap=7.77
- record_id=10231 code=093370 name=후성 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=0.43 final=-1.9 ai=73.0 tick=1.0 micro_vwap=-9.25
- record_id= code=319400 name=현대무벡스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.13 final=None ai=71.0 tick=0.0 micro_vwap=-41.48
- record_id= code=417860 name=오브젠 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.02 final=None ai=72.0 tick=0.19 micro_vwap=-23.24
- record_id= code=270660 name=에브리봇 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.68 final=None ai=69.0 tick=0.0 micro_vwap=-32.15
- record_id= code=010060 name=OCI홀딩스 label=pyramid_open_unresolved blocker=trend_not_strong profit=3.58 final=None ai=74.0 tick=1.333 micro_vwap=9.38
- record_id= code=066970 name=엘앤에프 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.06 final=None ai=62.0 tick=0.0 micro_vwap=-999.0
- record_id= code=078600 name=대주전자재료 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.46 final=None ai=64.0 tick=0.2 micro_vwap=-16.15
- record_id= code=083450 name=GST label=pyramid_open_unresolved blocker=profit_not_enough profit=0.37 final=None ai=70.0 tick=2.25 micro_vwap=213.1
- record_id= code=105560 name=KB금융 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.13 final=None ai=60.0 tick=0.0 micro_vwap=-999.0
- record_id= code=277810 name=레인보우로보틱스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.22 final=None ai=68.0 tick=0.0 micro_vwap=-26.02
- record_id= code=348340 name=뉴로메카 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.73 final=None ai=68.0 tick=0.75 micro_vwap=16.92
- record_id= code=001340 name=PKC label=pyramid_open_unresolved blocker=profit_not_enough profit=0.09 final=None ai=60.0 tick=None micro_vwap=None
- record_id= code=004170 name=신세계 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.3 final=None ai=62.0 tick=None micro_vwap=None
- record_id= code=399720 name=가온칩스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.57 final=None ai=68.0 tick=2.5 micro_vwap=-10.86
- record_id= code=464080 name=에스오에스랩 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.07 final=None ai=58.0 tick=0.5 micro_vwap=-102.99
- record_id= code=077500 name=유니퀘스트 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.4 final=None ai=75.0 tick=1.143 micro_vwap=6.16
- record_id= code=425040 name=티이엠씨 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.27 final=None ai=62.0 tick=0.0 micro_vwap=-999.0
- record_id= code=463020 name=뉴엔AI label=pyramid_open_unresolved blocker=profit_not_enough profit=0.82 final=None ai=55.0 tick=0.0 micro_vwap=-1.94
- record_id= code=108490 name=로보티즈 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.18 final=None ai=60.0 tick=0.0 micro_vwap=-999.0
- record_id= code=448900 name=한국피아이엠 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.21 final=None ai=61.0 tick=0.875 micro_vwap=-30.8
- record_id= code=466100 name=클로봇 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.16 final=None ai=73.0 tick=0.0 micro_vwap=-16.55
- record_id= code=000240 name=한국앤컴퍼니 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.81 final=None ai=66.0 tick=1.0 micro_vwap=-23.68
- record_id= code=475150 name=SK이터닉스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.21 final=None ai=70.0 tick=5.0 micro_vwap=-12.89
- record_id= code=482630 name=삼양엔씨켐 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.16 final=None ai=48.0 tick=1.0 micro_vwap=-86.76
- record_id= code=403870 name=HPSP label=pyramid_open_unresolved blocker=profit_not_enough profit=0.33 final=None ai=62.0 tick=0.0 micro_vwap=-999.0
- record_id= code=140670 name=알에스오토메이션 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.57 final=None ai=58.0 tick=6.5 micro_vwap=-26.93
- record_id= code=288180 name=케이피항공산업 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.44 final=None ai=71.0 tick=1.4 micro_vwap=1.43
- record_id= code=073490 name=LIG아큐버 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.18 final=None ai=72.0 tick=1.208 micro_vwap=-21.75
- record_id= code=004560 name=현대비앤지스틸 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.04 final=None ai=37.0 tick=0.1 micro_vwap=-41.55
- record_id= code=455900 name=엔젤로보틱스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.15 final=None ai=53.0 tick=0.438 micro_vwap=29.28
- record_id= code=144960 name=뉴파워프라즈마 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.9 final=None ai=76.0 tick=0.125 micro_vwap=-62.6
- record_id= code=347700 name=스피어 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.02 final=None ai=76.0 tick=1.0 micro_vwap=-15.34
- record_id= code=038500 name=삼표시멘트 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.01 final=None ai=69.0 tick=0.8 micro_vwap=3.29
- record_id= code=484810 name=티엑스알로보틱스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.09 final=None ai=57.0 tick=0.65 micro_vwap=25.55
- record_id= code=100590 name=머큐리 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.29 final=None ai=72.0 tick=0.135 micro_vwap=-45.33
- record_id= code=125490 name=한라캐스트 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.19 final=None ai=62.0 tick=0.0 micro_vwap=-16.06
- record_id= code=010170 name=대한광통신 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.07 final=None ai=73.0 tick=0.0 micro_vwap=-39.22
- record_id= code=437730 name=삼현 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.13 final=None ai=71.0 tick=0.0 micro_vwap=20.91
- record_id= code=338220 name=뷰노 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.79 final=None ai=73.0 tick=0.6 micro_vwap=-87.71
- record_id= code=304360 name=에스바이오메딕스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.08 final=None ai=67.0 tick=1.0 micro_vwap=-26.35
- record_id= code=035420 name=NAVER label=pyramid_open_unresolved blocker=profit_not_enough profit=0.54 final=None ai=71.0 tick=0.0 micro_vwap=-23.25
- record_id= code=011070 name=LG이노텍 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.13 final=None ai=48.0 tick=0.0 micro_vwap=34.09
- record_id= code=093370 name=후성 label=pyramid_open_unresolved blocker=trend_not_strong profit=2.59 final=None ai=57.0 tick=1.0 micro_vwap=7.44
- record_id= code=009150 name=삼성전기 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.1 final=None ai=63.0 tick=0.0 micro_vwap=2.21
- record_id= code=357780 name=솔브레인 label=pyramid_open_unresolved blocker=trend_not_strong profit=4.19 final=None ai=64.0 tick=0.0 micro_vwap=-999.0
- record_id= code=090360 name=로보스타 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.18 final=None ai=76.0 tick=0.75 micro_vwap=55.3
- record_id= code=484870 name=엠앤씨솔루션 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.65 final=None ai=50.0 tick=0.4 micro_vwap=4.25
- record_id= code=000660 name=SK하이닉스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.47 final=None ai=67.0 tick=0.0 micro_vwap=-73.12
- record_id= code=124500 name=아이티센글로벌 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.52 final=None ai=70.0 tick=0.0 micro_vwap=-20.41
- record_id= code=005290 name=동진쎄미켐 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.26 final=None ai=75.0 tick=0.0 micro_vwap=36.9
- record_id= code=240810 name=원익IPS label=pyramid_open_unresolved blocker=profit_not_enough profit=1.21 final=None ai=74.0 tick=1.0 micro_vwap=0.0
- record_id= code=035720 name=카카오 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.95 final=None ai=73.0 tick=2.0 micro_vwap=15.19
- record_id= code=065350 name=신성델타테크 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.12 final=None ai=76.0 tick=0.189 micro_vwap=-21.63
- record_id= code=019210 name=와이지-원 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.08 final=None ai=70.0 tick=0.0 micro_vwap=8.04
- record_id= code=064350 name=현대로템 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.25 final=None ai=69.0 tick=0.0 micro_vwap=-63.02
- record_id= code=001740 name=SK네트웍스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.07 final=None ai=62.0 tick=0.0 micro_vwap=-999.0
- record_id= code=272210 name=한화시스템 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.48 final=None ai=60.0 tick=0.0 micro_vwap=-999.0
- record_id= code=417840 name=저스템 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.03 final=None ai=58.0 tick=0.0 micro_vwap=-93.17
- record_id= code=025560 name=미래산업 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.29 final=None ai=60.0 tick=1.0 micro_vwap=-290.25
- record_id= code=032940 name=원익 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.09 final=None ai=65.0 tick=0.0 micro_vwap=-999.0
- record_id= code=489790 name=한화비전 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.51 final=None ai=58.0 tick=0.0 micro_vwap=-74.25
- record_id= code=098460 name=고영 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.01 final=None ai=69.0 tick=3.0 micro_vwap=10.6
- record_id= code=092870 name=엑시콘 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.37 final=None ai=70.0 tick=0.071 micro_vwap=-10.58
- record_id= code=089970 name=브이엠 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.77 final=None ai=76.0 tick=0.0 micro_vwap=-4.55
- record_id= code=095340 name=ISC label=pyramid_open_unresolved blocker=profit_not_enough profit=0.18 final=None ai=57.0 tick=0.0 micro_vwap=-21.66
- record_id= code=402340 name=SK스퀘어 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.2 final=None ai=57.0 tick=1.0 micro_vwap=-142.88
- record_id= code=042700 name=한미반도체 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.32 final=None ai=76.0 tick=0.0 micro_vwap=-36.86
- record_id= code=252990 name=샘씨엔에스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.01 final=None ai=66.0 tick=0.0 micro_vwap=22.67
- record_id= code=267260 name=HD현대일렉트릭 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.03 final=None ai=60.0 tick=0.0 micro_vwap=-59.49
- record_id= code=039440 name=에스티아이 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.08 final=None ai=58.0 tick=0.556 micro_vwap=-34.45
- record_id= code=036200 name=유니셈 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.08 final=None ai=69.0 tick=0.5 micro_vwap=15.24
- record_id= code=005950 name=이수화학 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.0 final=None ai=63.0 tick=0.333 micro_vwap=61.23
- record_id= code=086390 name=유니테스트 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.0 final=None ai=63.0 tick=1.167 micro_vwap=-53.6
- record_id= code=381970 name=케이카 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.39 final=None ai=54.0 tick=1.5 micro_vwap=-212.77
- record_id= code=005930 name=삼성전자 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.08 final=None ai=55.0 tick=1.0 micro_vwap=-20.21
- record_id= code=074600 name=원익QnC label=pyramid_open_unresolved blocker=profit_not_enough profit=0.58 final=None ai=69.0 tick=0.0 micro_vwap=34.67
- record_id= code=319660 name=피에스케이 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.16 final=None ai=67.0 tick=1.0 micro_vwap=-100.62
- record_id= code=020150 name=롯데에너지머티리얼즈 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.12 final=None ai=75.0 tick=2.0 micro_vwap=-47.26
- record_id= code=039030 name=이오테크닉스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.77 final=None ai=70.0 tick=0.0 micro_vwap=-46.67
- record_id= code=241770 name=메카로 label=pyramid_open_unresolved blocker=scalping_cutoff profit=0.2 final=None ai=59.0 tick=1.625 micro_vwap=11.53
- record_id= code=281820 name=케이씨텍 label=pyramid_open_unresolved blocker=scalping_cutoff profit=-0.0 final=None ai=62.0 tick=1.5 micro_vwap=-22.22
- record_id= code=159010 name=아스플로 label=pyramid_open_unresolved blocker=scalping_cutoff profit=0.22 final=None ai=59.0 tick=16.0 micro_vwap=-55.72

## One Share Opportunity Rows
