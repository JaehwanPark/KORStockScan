# 2026-06-15 Scalping Pyramid Intraday Feedback

- generated_at: 2026-07-03T13:23:22+09:00
- decision_authority: source_only_pyramid_intraday_feedback_no_runtime_mutation
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: intraday_threshold_mutation, intraday_runtime_apply, hard_safety_relaxation, broker_guard_bypass, order_guard_relaxation, stale_quote_bypass, cooldown_bypass, quantity_guard_relaxation, position_cap_release, provider_route_change, bot_restart, real_execution_quality_approval

## Summary

- pyramid_feedback_row_count: 48
- closed_pyramid_row_count: 0
- pyramid_would_have_helped_count: 0
- pyramid_correctly_blocked_count: 0
- pyramid_overheat_or_reversal_risk_count: 0
- pyramid_open_unresolved_count: 48
- one_share_event_count: 0
- one_share_closed_count: 0
- one_share_pyramid_opportunity_count: 0
- one_share_pyramid_missed_upside_count: 0
- one_share_pyramid_missed_upside_rate: 0.00
- one_share_pyramid_avg_opportunity_cost_pct: 0.00

## Blocker Metrics

- blocker=add_judgment_locked sample=8 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=profit_not_enough sample=35 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=scalping_cutoff sample=2 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=trend_not_strong sample=3 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00

## Rows

- record_id= code=009150 name=삼성전기 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.14 final=None ai=60.0 tick=0.0 micro_vwap=-40.78
- record_id= code=328130 name=루닛 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.16 final=None ai=75.0 tick=0.333 micro_vwap=-38.47
- record_id= code=006400 name=삼성SDI label=pyramid_open_unresolved blocker=profit_not_enough profit=0.3 final=None ai=72.0 tick=1.0 micro_vwap=-20.39
- record_id= code=066570 name=LG전자 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.59 final=None ai=68.0 tick=0.0 micro_vwap=-6.17
- record_id= code=477850 name=마키나락스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.01 final=None ai=73.0 tick=1.111 micro_vwap=25.42
- record_id= code=089030 name=테크윙 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.93 final=None ai=70.0 tick=1.0 micro_vwap=-20.76
- record_id= code=064350 name=현대로템 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.0 final=None ai=57.0 tick=3.0 micro_vwap=7.37
- record_id= code=010120 name=LS ELECTRIC label=pyramid_open_unresolved blocker=trend_not_strong profit=5.55 final=None ai=63.0 tick=0.0 micro_vwap=-72.49
- record_id= code=005380 name=현대차 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.86 final=None ai=74.0 tick=0.0 micro_vwap=-17.63
- record_id= code=096770 name=SK이노베이션 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.03 final=None ai=74.0 tick=1.0 micro_vwap=-30.65
- record_id= code=077970 name=STX엔진 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.2 final=None ai=63.0 tick=0.556 micro_vwap=-47.85
- record_id= code=005850 name=에스엘 label=pyramid_open_unresolved blocker=add_judgment_locked profit=0.05 final=None ai=57.0 tick=0.357 micro_vwap=-37.67
- record_id= code=267260 name=HD현대일렉트릭 label=pyramid_open_unresolved blocker=add_judgment_locked profit=0.03 final=None ai=74.0 tick=0.0 micro_vwap=-999.0
- record_id= code=000660 name=SK하이닉스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.91 final=None ai=75.0 tick=1.0 micro_vwap=26.88
- record_id= code=034020 name=두산에너빌리티 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.08 final=None ai=67.0 tick=1.0 micro_vwap=44.5
- record_id= code=316140 name=우리금융지주 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.23 final=None ai=62.0 tick=0.0 micro_vwap=-999.0
- record_id= code=001820 name=삼화콘덴서 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.12 final=None ai=70.0 tick=2.0 micro_vwap=-32.51
- record_id= code=464080 name=에스오에스랩 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.6 final=None ai=74.0 tick=1.0 micro_vwap=-123.98
- record_id= code=247540 name=에코프로비엠 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.09 final=None ai=69.0 tick=1.0 micro_vwap=23.58
- record_id= code=457370 name=한켐 label=pyramid_open_unresolved blocker=trend_not_strong profit=2.2 final=None ai=62.0 tick=0.364 micro_vwap=-29.39
- record_id= code=078930 name=GS label=pyramid_open_unresolved blocker=add_judgment_locked profit=0.03 final=None ai=68.0 tick=0.125 micro_vwap=15.17
- record_id= code=000720 name=현대건설 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.11 final=None ai=72.0 tick=1.0 micro_vwap=-3.52
- record_id= code=010140 name=삼성중공업 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.3 final=None ai=74.0 tick=0.0 micro_vwap=-999.0
- record_id= code=003550 name=LG label=pyramid_open_unresolved blocker=profit_not_enough profit=0.56 final=None ai=56.0 tick=0.0 micro_vwap=41.23
- record_id= code=005290 name=동진쎄미켐 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.26 final=None ai=75.0 tick=0.333 micro_vwap=-25.22
- record_id= code=004710 name=한솔테크닉스 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.24 final=None ai=62.0 tick=0.0 micro_vwap=-999.0
- record_id= code=062040 name=산일전기 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.16 final=None ai=70.0 tick=0.5 micro_vwap=-15.33
- record_id= code=139130 name=iM금융지주 label=pyramid_open_unresolved blocker=add_judgment_locked profit=0.15 final=None ai=74.0 tick=0.0 micro_vwap=14.31
- record_id= code=403870 name=HPSP label=pyramid_open_unresolved blocker=add_judgment_locked profit=0.21 final=None ai=70.0 tick=0.0 micro_vwap=-94.97
- record_id= code=452280 name=한선엔지니어링 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.2 final=None ai=73.0 tick=3.25 micro_vwap=-30.92
- record_id= code=279570 name=케이뱅크 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.78 final=None ai=70.0 tick=1.5 micro_vwap=32.97
- record_id= code=011210 name=현대위아 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.01 final=None ai=67.0 tick=0.357 micro_vwap=-6.06
- record_id= code=079550 name=LIG디펜스앤에어로스페이스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.12 final=None ai=73.0 tick=1.0 micro_vwap=-72.1
- record_id= code=071970 name=HD현대마린엔진 label=pyramid_open_unresolved blocker=add_judgment_locked profit=0.19 final=None ai=69.0 tick=0.286 micro_vwap=2.25
- record_id= code=365270 name=큐라클 label=pyramid_open_unresolved blocker=add_judgment_locked profit=0.52 final=None ai=74.0 tick=6.0 micro_vwap=-77.5
- record_id= code=330860 name=네패스아크 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.25 final=None ai=57.99999999999999 tick=0.0 micro_vwap=-999.0
- record_id= code=000240 name=한국앤컴퍼니 label=pyramid_open_unresolved blocker=add_judgment_locked profit=0.08 final=None ai=76.0 tick=0.0 micro_vwap=-47.39
- record_id= code=042660 name=한화오션 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.09 final=None ai=60.0 tick=1.0 micro_vwap=15.26
- record_id= code=103140 name=풍산 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.03 final=None ai=58.0 tick=0.667 micro_vwap=6.09
- record_id= code=311320 name=지오엘리먼트 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.18 final=None ai=70.0 tick=0.364 micro_vwap=-10.26
- record_id= code=004380 name=삼익THK label=pyramid_open_unresolved blocker=profit_not_enough profit=0.56 final=None ai=59.0 tick=3.9 micro_vwap=13.61
- record_id= code=028260 name=삼성물산 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.27 final=None ai=73.0 tick=0.333 micro_vwap=21.63
- record_id= code=011070 name=LG이노텍 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.94 final=None ai=47.0 tick=2.0 micro_vwap=-0.15
- record_id= code=356680 name=엑스게이트 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.19 final=None ai=51.0 tick=0.0 micro_vwap=-77.89
- record_id= code=281740 name=레이크머티리얼즈 label=pyramid_open_unresolved blocker=trend_not_strong profit=1.74 final=None ai=71.0 tick=1.667 micro_vwap=-84.76
- record_id= code=020560 name=아시아나항공 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.65 final=None ai=74.0 tick=5.0 micro_vwap=18.69
- record_id= code=402340 name=SK스퀘어 label=pyramid_open_unresolved blocker=scalping_cutoff profit=0.06 final=None ai=69.0 tick=1.0 micro_vwap=-0.71
- record_id= code=240810 name=원익IPS label=pyramid_open_unresolved blocker=scalping_cutoff profit=-0.0 final=None ai=60.0 tick=1.0 micro_vwap=14.16

## One Share Opportunity Rows
