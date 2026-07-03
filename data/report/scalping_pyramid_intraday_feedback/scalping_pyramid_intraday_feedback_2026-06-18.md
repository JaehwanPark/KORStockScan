# 2026-06-18 Scalping Pyramid Intraday Feedback

- generated_at: 2026-07-03T13:23:59+09:00
- decision_authority: source_only_pyramid_intraday_feedback_no_runtime_mutation
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: intraday_threshold_mutation, intraday_runtime_apply, hard_safety_relaxation, broker_guard_bypass, order_guard_relaxation, stale_quote_bypass, cooldown_bypass, quantity_guard_relaxation, position_cap_release, provider_route_change, bot_restart, real_execution_quality_approval

## Summary

- pyramid_feedback_row_count: 80
- closed_pyramid_row_count: 4
- pyramid_would_have_helped_count: 1
- pyramid_correctly_blocked_count: 0
- pyramid_overheat_or_reversal_risk_count: 3
- pyramid_open_unresolved_count: 76
- one_share_event_count: 0
- one_share_closed_count: 0
- one_share_pyramid_opportunity_count: 0
- one_share_pyramid_missed_upside_count: 0
- one_share_pyramid_missed_upside_rate: 0.00
- one_share_pyramid_avg_opportunity_cost_pct: 0.00

## Blocker Metrics

- blocker=add_judgment_locked sample=8 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=profit_not_enough sample=58 recovered_rate=0.02 reversal_rate=0.02 blocked_then_recovered_rate=0.02
- blocker=scalping_cutoff sample=6 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=trend_not_strong sample=8 recovered_rate=0.00 reversal_rate=0.25 blocked_then_recovered_rate=0.00

## Rows

- record_id= code=204320 name=HL만도 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.03 final=None ai=69.0 tick=1.0 micro_vwap=-47.67
- record_id= code=061970 name=LB세미콘 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.3 final=None ai=71.0 tick=0.0 micro_vwap=-338.5
- record_id= code=204620 name=글로벌텍스프리 label=pyramid_open_unresolved blocker=trend_not_strong profit=5.25 final=None ai=72.0 tick=15.0 micro_vwap=-1.83
- record_id= code=450950 name=아스테라시스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.13 final=None ai=64.0 tick=6.5 micro_vwap=-53.18
- record_id= code=122870 name=와이지엔터테인먼트 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.02 final=None ai=73.0 tick=0.3 micro_vwap=-20.51
- record_id= code=475150 name=SK이터닉스 label=pyramid_open_unresolved blocker=trend_not_strong profit=3.44 final=None ai=70.0 tick=0.5 micro_vwap=-33.72
- record_id= code=319660 name=피에스케이 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.45 final=None ai=63.0 tick=1.5 micro_vwap=-32.17
- record_id= code=192650 name=드림텍 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.1 final=None ai=68.0 tick=0.0 micro_vwap=-101.35
- record_id= code=047920 name=HLB제약 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.06 final=None ai=72.0 tick=1.083 micro_vwap=-3.75
- record_id= code=353200 name=대덕전자 label=pyramid_open_unresolved blocker=profit_not_enough profit=-0.0 final=None ai=68.0 tick=1.0 micro_vwap=-76.92
- record_id= code=083450 name=GST label=pyramid_open_unresolved blocker=profit_not_enough profit=0.27 final=None ai=72.0 tick=0.857 micro_vwap=3.95
- record_id= code=475300 name=SOL 반도체전공정 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.07 final=None ai=74.0 tick=7.0 micro_vwap=-55.19
- record_id= code=196170 name=알테오젠 label=pyramid_open_unresolved blocker=add_judgment_locked profit=0.17 final=None ai=74.0 tick=0.5 micro_vwap=-17.14
- record_id= code=028300 name=HLB label=pyramid_open_unresolved blocker=profit_not_enough profit=1.13 final=None ai=76.0 tick=0.0 micro_vwap=-50.6
- record_id= code=046970 name=우리로 label=pyramid_open_unresolved blocker=trend_not_strong profit=4.03 final=None ai=73.0 tick=1.0 micro_vwap=-23.27
- record_id= code=338220 name=뷰노 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.52 final=None ai=69.0 tick=0.636 micro_vwap=3.29
- record_id= code=009470 name=삼화전기 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.19 final=None ai=73.0 tick=0.862 micro_vwap=0.0
- record_id= code=126730 name=코칩 label=pyramid_open_unresolved blocker=trend_not_strong profit=4.14 final=None ai=74.0 tick=1.0 micro_vwap=96.8
- record_id=11742 code=279570 name=케이뱅크 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=0.05 final=-2.18 ai=65.0 tick=1.0 micro_vwap=-8.5
- record_id= code=322310 name=오로스테크놀로지 label=pyramid_open_unresolved blocker=add_judgment_locked profit=0.1 final=None ai=73.0 tick=0.844 micro_vwap=-20.36
- record_id= code=394420 name=리센스메디컬 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.92 final=None ai=70.0 tick=0.692 micro_vwap=-14.98
- record_id= code=017900 name=광전자 label=pyramid_open_unresolved blocker=trend_not_strong profit=3.09 final=None ai=78.0 tick=0.917 micro_vwap=27.45
- record_id= code=161000 name=애경케미칼 label=pyramid_open_unresolved blocker=add_judgment_locked profit=0.12 final=None ai=68.0 tick=0.0 micro_vwap=-999.0
- record_id= code=006220 name=제주은행 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.96 final=None ai=73.0 tick=0.067 micro_vwap=-53.94
- record_id= code=036010 name=아비코전자 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.77 final=None ai=66.0 tick=14.0 micro_vwap=47.59
- record_id= code=322510 name=제이엘케이 label=pyramid_open_unresolved blocker=add_judgment_locked profit=0.46 final=None ai=73.0 tick=0.0 micro_vwap=-1.75
- record_id= code=003490 name=대한항공 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.11 final=None ai=70.0 tick=1.333 micro_vwap=-9.04
- record_id= code=488280 name=에스투더블유 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.3 final=None ai=69.0 tick=1.0 micro_vwap=10.72
- record_id= code=432720 name=퀄리타스반도체 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.05 final=None ai=70.0 tick=1.213 micro_vwap=0.71
- record_id= code=009150 name=삼성전기 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.19 final=None ai=69.0 tick=0.0 micro_vwap=-16.32
- record_id= code=355690 name=에이텀 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.12 final=None ai=88.0 tick=0.611 micro_vwap=-7.16
- record_id= code=181710 name=NHN label=pyramid_open_unresolved blocker=profit_not_enough profit=0.38 final=None ai=66.0 tick=6.0 micro_vwap=-44.9
- record_id= code=382840 name=원준 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.15 final=None ai=76.0 tick=0.952 micro_vwap=-1.29
- record_id= code=425040 name=티이엠씨 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.39 final=None ai=68.0 tick=0.0 micro_vwap=54.57
- record_id= code=004310 name=현대약품 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.19 final=None ai=62.0 tick=0.0 micro_vwap=-999.0
- record_id= code=265740 name=엔에프씨 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.33 final=None ai=73.0 tick=1.095 micro_vwap=-20.51
- record_id= code=330350 name=위더스제약 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.0 final=None ai=70.0 tick=0.444 micro_vwap=-62.34
- record_id= code=298000 name=효성화학 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.25 final=None ai=62.0 tick=0.0 micro_vwap=-999.0
- record_id= code=469610 name=이노테크 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.91 final=None ai=69.0 tick=0.0 micro_vwap=56.23
- record_id=11666 code=439960 name=코스모로보틱스 label=pyramid_would_have_helped blocker=profit_not_enough profit=0.14 final=0.87 ai=41.0 tick=1.0 micro_vwap=57.79
- record_id= code=044490 name=태웅 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.14 final=None ai=71.0 tick=1.5 micro_vwap=-38.48
- record_id= code=093370 name=후성 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.7 final=None ai=82.0 tick=0.0 micro_vwap=-999.0
- record_id= code=482630 name=삼양엔씨켐 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.66 final=None ai=68.0 tick=0.5 micro_vwap=31.64
- record_id= code=090360 name=로보스타 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.63 final=None ai=62.0 tick=0.0 micro_vwap=-999.0
- record_id= code=484590 name=삼양컴텍 label=pyramid_open_unresolved blocker=add_judgment_locked profit=0.49 final=None ai=68.0 tick=0.0 micro_vwap=8.42
- record_id= code=114190 name=강원에너지 label=pyramid_open_unresolved blocker=add_judgment_locked profit=0.74 final=None ai=72.0 tick=18.0 micro_vwap=-40.41
- record_id= code=149950 name=아바텍 label=pyramid_open_unresolved blocker=add_judgment_locked profit=0.29 final=None ai=74.0 tick=1.0 micro_vwap=-6.11
- record_id= code=439960 name=코스모로보틱스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.13 final=None ai=72.0 tick=1.0 micro_vwap=-28.54
- record_id= code=010170 name=대한광통신 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.09 final=None ai=75.0 tick=1.0 micro_vwap=-44.77
- record_id= code=032580 name=피델릭스 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.0 final=None ai=76.0 tick=0.25 micro_vwap=103.58
- record_id= code=080220 name=제주반도체 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.02 final=None ai=74.0 tick=1.0 micro_vwap=-3.4
- record_id= code=457370 name=한켐 label=pyramid_open_unresolved blocker=add_judgment_locked profit=0.34 final=None ai=70.0 tick=0.5 micro_vwap=-44.81
- record_id= code=031330 name=에스에이엠티 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.14 final=None ai=62.0 tick=0.5 micro_vwap=-32.85
- record_id=11863 code=093370 name=후성 label=pyramid_overheat_or_reversal_risk blocker=trend_not_strong profit=1.83 final=1.34 ai=74.0 tick=0.5 micro_vwap=-19.23
- record_id=11788 code=067310 name=하나마이크론 label=pyramid_overheat_or_reversal_risk blocker=trend_not_strong profit=1.54 final=-1.17 ai=71.0 tick=2.0 micro_vwap=-68.49
- record_id= code=085620 name=미래에셋생명 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.08 final=None ai=63.0 tick=1.0 micro_vwap=-51.29
- record_id= code=005950 name=이수화학 label=pyramid_open_unresolved blocker=trend_not_strong profit=3.65 final=None ai=61.0 tick=0.333 micro_vwap=-66.36
- record_id= code=347850 name=디앤디파마텍 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.33 final=None ai=67.0 tick=0.0 micro_vwap=8.49
- record_id= code=095610 name=테스 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.32 final=None ai=63.0 tick=3.0 micro_vwap=-31.63
- record_id= code=011070 name=LG이노텍 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.36 final=None ai=68.0 tick=0.0 micro_vwap=7.48
- record_id= code=212710 name=아이에스티이 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.34 final=None ai=72.0 tick=0.75 micro_vwap=46.93
- record_id= code=383310 name=에코프로에이치엔 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.07 final=None ai=59.0 tick=7.8 micro_vwap=-9.27
- record_id= code=089970 name=브이엠 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.2 final=None ai=82.0 tick=0.0 micro_vwap=-999.0
- record_id= code=367760 name=RISE 네트워크인프라 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.39 final=None ai=72.0 tick=0.667 micro_vwap=-13.98
- record_id= code=000660 name=SK하이닉스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.93 final=None ai=73.0 tick=0.0 micro_vwap=-27.56
- record_id= code=240810 name=원익IPS label=pyramid_open_unresolved blocker=profit_not_enough profit=0.44 final=None ai=71.0 tick=0.5 micro_vwap=-3.14
- record_id= code=474590 name=WON 반도체밸류체인액티브 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.38 final=None ai=70.0 tick=21.5 micro_vwap=-28.52
- record_id= code=019210 name=와이지-원 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.23 final=None ai=56.0 tick=2.0 micro_vwap=-6.83
- record_id= code=000810 name=삼성화재 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.2 final=None ai=57.0 tick=2.0 micro_vwap=-23.34
- record_id= code=290130 name=RISE ESG사회책임투자 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.29 final=None ai=74.0 tick=None micro_vwap=None
- record_id= code=469150 name=ACE AI반도체TOP3+ label=pyramid_open_unresolved blocker=profit_not_enough profit=0.21 final=None ai=63.0 tick=0.0 micro_vwap=6.2
- record_id=11857 code=451060 name=1Q 200액티브 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.27 final=None ai=66.0 tick=0.033 micro_vwap=-33.0
- record_id=11677 code=089970 name=브이엠 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.63 final=None ai=66.0 tick=1.0 micro_vwap=-5.02
- record_id=11645 code=402340 name=SK스퀘어 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.48 final=None ai=57.0 tick=0.5 micro_vwap=-2.06
- record_id= code=064290 name=인텍플러스 label=pyramid_open_unresolved blocker=scalping_cutoff profit=0.38 final=None ai=71.0 tick=4.0 micro_vwap=-21.4
- record_id= code=148020 name=RISE 200 label=pyramid_open_unresolved blocker=scalping_cutoff profit=0.09 final=None ai=76.0 tick=1.375 micro_vwap=7.45
- record_id= code=451060 name=1Q 200액티브 label=pyramid_open_unresolved blocker=scalping_cutoff profit=0.41 final=None ai=65.0 tick=0.0 micro_vwap=14.28
- record_id= code=402340 name=SK스퀘어 label=pyramid_open_unresolved blocker=scalping_cutoff profit=1.29 final=None ai=73.0 tick=0.0 micro_vwap=23.36
- record_id= code=456600 name=TIME 글로벌AI인공지능액티브 label=pyramid_open_unresolved blocker=scalping_cutoff profit=0.05 final=None ai=67.0 tick=4.0 micro_vwap=5.71
- record_id= code=084370 name=유진테크 label=pyramid_open_unresolved blocker=scalping_cutoff profit=0.05 final=None ai=71.0 tick=3.0 micro_vwap=-62.86

## One Share Opportunity Rows
