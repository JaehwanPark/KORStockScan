# 2026-06-16 Scalping Pyramid Intraday Feedback

- generated_at: 2026-07-03T13:23:31+09:00
- decision_authority: source_only_pyramid_intraday_feedback_no_runtime_mutation
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: intraday_threshold_mutation, intraday_runtime_apply, hard_safety_relaxation, broker_guard_bypass, order_guard_relaxation, stale_quote_bypass, cooldown_bypass, quantity_guard_relaxation, position_cap_release, provider_route_change, bot_restart, real_execution_quality_approval

## Summary

- pyramid_feedback_row_count: 69
- closed_pyramid_row_count: 0
- pyramid_would_have_helped_count: 0
- pyramid_correctly_blocked_count: 0
- pyramid_overheat_or_reversal_risk_count: 0
- pyramid_open_unresolved_count: 69
- one_share_event_count: 0
- one_share_closed_count: 0
- one_share_pyramid_opportunity_count: 0
- one_share_pyramid_missed_upside_count: 0
- one_share_pyramid_missed_upside_rate: 0.00
- one_share_pyramid_avg_opportunity_cost_pct: 0.00

## Blocker Metrics

- blocker=add_judgment_locked sample=2 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=profit_not_enough sample=58 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=scalping_cutoff sample=4 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=trend_not_strong sample=5 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00

## Rows

- record_id= code=035420 name=NAVER label=pyramid_open_unresolved blocker=profit_not_enough profit=0.16 final=None ai=73.0 tick=1.0 micro_vwap=-67.15
- record_id= code=011790 name=SKC label=pyramid_open_unresolved blocker=profit_not_enough profit=0.64 final=None ai=72.0 tick=1.0 micro_vwap=-114.23
- record_id= code=060720 name=KH바텍 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.63 final=None ai=73.0 tick=0.4 micro_vwap=-30.43
- record_id= code=064350 name=현대로템 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.3 final=None ai=72.0 tick=1.5 micro_vwap=10.18
- record_id= code=449450 name=PLUS K방산 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.11 final=None ai=72.0 tick=0.0 micro_vwap=-3.76
- record_id= code=298040 name=효성중공업 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.7 final=None ai=74.0 tick=0.0 micro_vwap=47.68
- record_id= code=272110 name=케이엔제이 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.68 final=None ai=64.0 tick=0.562 micro_vwap=-2.82
- record_id= code=036010 name=아비코전자 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.66 final=None ai=73.0 tick=9.0 micro_vwap=-33.22
- record_id= code=421320 name=PLUS 우주항공 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.08 final=None ai=79.0 tick=0.5 micro_vwap=-20.77
- record_id= code=047810 name=한국항공우주 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.46 final=None ai=65.0 tick=5.0 micro_vwap=-36.74
- record_id= code=006800 name=미래에셋증권 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.05 final=None ai=72.0 tick=0.0 micro_vwap=78.55
- record_id= code=218410 name=RFHIC label=pyramid_open_unresolved blocker=profit_not_enough profit=0.35 final=None ai=67.0 tick=2.0 micro_vwap=10.94
- record_id= code=474610 name=RF시스템즈 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.24 final=None ai=69.0 tick=1.407 micro_vwap=-6.31
- record_id= code=086790 name=하나금융지주 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.74 final=None ai=67.0 tick=0.0 micro_vwap=-54.26
- record_id= code=000720 name=현대건설 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.87 final=None ai=70.0 tick=0.0 micro_vwap=-118.56
- record_id= code=028050 name=삼성E&A label=pyramid_open_unresolved blocker=profit_not_enough profit=0.12 final=None ai=72.0 tick=1.0 micro_vwap=14.92
- record_id= code=103140 name=풍산 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.63 final=None ai=65.0 tick=1.143 micro_vwap=-73.08
- record_id= code=241560 name=두산밥캣 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.05 final=None ai=73.0 tick=0.25 micro_vwap=7.48
- record_id= code=375500 name=DL이앤씨 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.43 final=None ai=62.0 tick=0.0 micro_vwap=-999.0
- record_id= code=439960 name=코스모로보틱스 label=pyramid_open_unresolved blocker=trend_not_strong profit=7.57 final=None ai=73.0 tick=0.0 micro_vwap=125.94
- record_id= code=383310 name=에코프로에이치엔 label=pyramid_open_unresolved blocker=add_judgment_locked profit=0.37 final=None ai=72.0 tick=1.333 micro_vwap=-49.9
- record_id= code=008770 name=호텔신라 label=pyramid_open_unresolved blocker=trend_not_strong profit=1.5 final=None ai=73.0 tick=1.333 micro_vwap=-43.14
- record_id= code=006220 name=제주은행 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.46 final=None ai=73.0 tick=0.333 micro_vwap=-57.79
- record_id= code=311320 name=지오엘리먼트 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.2 final=None ai=70.0 tick=0.067 micro_vwap=-54.1
- record_id= code=079550 name=LIG디펜스앤에어로스페이스 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.34 final=None ai=72.0 tick=0.5 micro_vwap=15.14
- record_id= code=011070 name=LG이노텍 label=pyramid_open_unresolved blocker=trend_not_strong profit=2.62 final=None ai=72.0 tick=0.0 micro_vwap=-39.59
- record_id= code=458870 name=씨어스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.24 final=None ai=71.0 tick=1.0 micro_vwap=6.91
- record_id= code=032640 name=LG유플러스 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.06 final=None ai=75.0 tick=5.0 micro_vwap=11.49
- record_id= code=042660 name=한화오션 label=pyramid_open_unresolved blocker=trend_not_strong profit=1.96 final=None ai=73.0 tick=1.0 micro_vwap=-5.45
- record_id= code=463020 name=뉴엔AI label=pyramid_open_unresolved blocker=profit_not_enough profit=0.12 final=None ai=66.0 tick=0.0 micro_vwap=-999.0
- record_id= code=009540 name=HD한국조선해양 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.44 final=None ai=70.0 tick=1.333 micro_vwap=19.32
- record_id= code=129920 name=대성하이텍 label=pyramid_open_unresolved blocker=add_judgment_locked profit=0.07 final=None ai=71.0 tick=1.222 micro_vwap=61.87
- record_id= code=078930 name=GS label=pyramid_open_unresolved blocker=profit_not_enough profit=0.15 final=None ai=62.0 tick=0.5 micro_vwap=-0.25
- record_id= code=316140 name=우리금융지주 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.07 final=None ai=69.0 tick=2.0 micro_vwap=18.44
- record_id= code=017960 name=한국카본 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.34 final=None ai=55.0 tick=0.714 micro_vwap=9.03
- record_id= code=012450 name=한화에어로스페이스 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.49 final=None ai=62.0 tick=0.0 micro_vwap=-999.0
- record_id= code=000150 name=그린광학 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.11 final=None ai=72.0 tick=0.833 micro_vwap=-0.85
- record_id= code=034020 name=두산에너빌리티 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.22 final=None ai=74.0 tick=0.0 micro_vwap=2.59
- record_id= code=200880 name=서연이화 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.96 final=None ai=72.0 tick=0.0 micro_vwap=-21.95
- record_id= code=004310 name=현대약품 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.32 final=None ai=74.0 tick=1.0 micro_vwap=-51.25
- record_id= code=009150 name=삼성전기 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.11 final=None ai=60.0 tick=0.0 micro_vwap=-999.0
- record_id= code=010060 name=OCI홀딩스 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.06 final=None ai=75.0 tick=1.0 micro_vwap=51.87
- record_id= code=047050 name=포스코인터내셔널 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.99 final=None ai=72.0 tick=0.0 micro_vwap=-33.32
- record_id= code=009830 name=한화솔루션 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.82 final=None ai=75.0 tick=1.0 micro_vwap=30.42
- record_id= code=069960 name=현대백화점 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.68 final=None ai=74.0 tick=1.6 micro_vwap=-17.93
- record_id= code=475150 name=SK이터닉스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.59 final=None ai=73.0 tick=0.0 micro_vwap=180.43
- record_id= code=024060 name=흥구석유 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.56 final=None ai=65.0 tick=None micro_vwap=None
- record_id= code=042940 name=상지건설 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.22 final=None ai=70.0 tick=0.5 micro_vwap=17.17
- record_id= code=282720 name=금양그린파워 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.09 final=None ai=66.0 tick=0.846 micro_vwap=-32.64
- record_id= code=389260 name=대명에너지 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.56 final=None ai=73.0 tick=1.0 micro_vwap=-114.69
- record_id= code=322000 name=HD현대에너지솔루션 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.22 final=None ai=70.0 tick=0.0 micro_vwap=17.46
- record_id= code=358570 name=지아이이노베이션 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.16 final=None ai=72.0 tick=0.2 micro_vwap=0.8
- record_id= code=100090 name=SK오션플랜트 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.47 final=None ai=73.0 tick=1.0 micro_vwap=-44.04
- record_id= code=004490 name=세방전지 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.09 final=None ai=75.0 tick=0.0 micro_vwap=22.99
- record_id= code=484590 name=삼양컴텍 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.0 final=None ai=66.0 tick=1.118 micro_vwap=-16.31
- record_id= code=004440 name=삼일씨엔에스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.35 final=None ai=70.0 tick=5.136 micro_vwap=-7.85
- record_id= code=000660 name=SK하이닉스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.02 final=None ai=77.0 tick=0.0 micro_vwap=-2.52
- record_id= code=482630 name=삼양엔씨켐 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.16 final=None ai=75.0 tick=1.167 micro_vwap=4.97
- record_id= code=085620 name=미래에셋생명 label=pyramid_open_unresolved blocker=trend_not_strong profit=2.79 final=None ai=67.0 tick=1.0 micro_vwap=34.48
- record_id= code=126340 name=비나텍 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.07 final=None ai=57.0 tick=1.5 micro_vwap=-53.34
- record_id= code=010820 name=퍼스텍 label=pyramid_open_unresolved blocker=profit_not_enough profit=-0.0 final=None ai=71.0 tick=0.429 micro_vwap=31.85
- record_id= code=402340 name=SK스퀘어 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.11 final=None ai=75.0 tick=1.0 micro_vwap=21.14
- record_id= code=017900 name=광전자 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.34 final=None ai=73.0 tick=0.0 micro_vwap=18.28
- record_id= code=001820 name=삼화콘덴서 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.59 final=None ai=76.0 tick=2.0 micro_vwap=0.74
- record_id= code=204320 name=HL만도 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.56 final=None ai=76.0 tick=0.0 micro_vwap=41.69
- record_id= code=175330 name=JB금융지주 label=pyramid_open_unresolved blocker=scalping_cutoff profit=0.47 final=None ai=61.0 tick=7.0 micro_vwap=46.34
- record_id= code=347850 name=디앤디파마텍 label=pyramid_open_unresolved blocker=scalping_cutoff profit=0.21 final=None ai=72.0 tick=1.0 micro_vwap=0.54
- record_id= code=032820 name=우리기술 label=pyramid_open_unresolved blocker=scalping_cutoff profit=0.03 final=None ai=66.0 tick=1.0 micro_vwap=-23.1
- record_id= code=030200 name=KT label=pyramid_open_unresolved blocker=scalping_cutoff profit=0.29 final=None ai=67.0 tick=3.0 micro_vwap=25.19

## One Share Opportunity Rows
