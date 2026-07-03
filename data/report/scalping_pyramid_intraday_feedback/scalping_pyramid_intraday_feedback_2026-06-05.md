# 2026-06-05 Scalping Pyramid Intraday Feedback

- generated_at: 2026-07-03T13:22:30+09:00
- decision_authority: source_only_pyramid_intraday_feedback_no_runtime_mutation
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: intraday_threshold_mutation, intraday_runtime_apply, hard_safety_relaxation, broker_guard_bypass, order_guard_relaxation, stale_quote_bypass, cooldown_bypass, quantity_guard_relaxation, position_cap_release, provider_route_change, bot_restart, real_execution_quality_approval

## Summary

- pyramid_feedback_row_count: 42
- closed_pyramid_row_count: 0
- pyramid_would_have_helped_count: 0
- pyramid_correctly_blocked_count: 0
- pyramid_overheat_or_reversal_risk_count: 0
- pyramid_open_unresolved_count: 42
- one_share_event_count: 0
- one_share_closed_count: 0
- one_share_pyramid_opportunity_count: 0
- one_share_pyramid_missed_upside_count: 0
- one_share_pyramid_missed_upside_rate: 0.00
- one_share_pyramid_avg_opportunity_cost_pct: 0.00

## Blocker Metrics

- blocker=add_judgment_locked sample=10 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=profit_not_enough sample=30 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=trend_not_strong sample=2 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00

## Rows

- record_id= code=316140 name=우리금융지주 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.24 final=None ai=70.0 tick=1.0 micro_vwap=-44.42
- record_id= code=487580 name=폴레드 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.21 final=None ai=73.0 tick=9.0 micro_vwap=128.93
- record_id= code=089970 name=브이엠 label=pyramid_open_unresolved blocker=add_judgment_locked profit=0.04 final=None ai=71.0 tick=2.5 micro_vwap=-46.5
- record_id= code=402340 name=SK스퀘어 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.0 final=None ai=69.0 tick=1.0 micro_vwap=-24.19
- record_id= code=074600 name=원익QnC label=pyramid_open_unresolved blocker=profit_not_enough profit=0.05 final=None ai=68.0 tick=3.0 micro_vwap=-30.57
- record_id= code=488280 name=에스투더블유 label=pyramid_open_unresolved blocker=add_judgment_locked profit=1.94 final=None ai=66.0 tick=2.4 micro_vwap=-4.24
- record_id= code=004710 name=한솔테크닉스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.08 final=None ai=68.0 tick=1.4 micro_vwap=-35.56
- record_id= code=095610 name=테스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.04 final=None ai=63.0 tick=0.0 micro_vwap=-42.38
- record_id= code=093370 name=후성 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.46 final=None ai=72.0 tick=0.0 micro_vwap=-29.12
- record_id= code=006220 name=제주은행 label=pyramid_open_unresolved blocker=add_judgment_locked profit=5.26 final=None ai=70.0 tick=0.0 micro_vwap=128.93
- record_id= code=181710 name=NHN label=pyramid_open_unresolved blocker=trend_not_strong profit=1.88 final=None ai=67.0 tick=0.0 micro_vwap=-39.84
- record_id= code=388790 name=라이콤 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.29 final=None ai=66.0 tick=0.0 micro_vwap=-82.51
- record_id= code=069960 name=현대백화점 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.27 final=None ai=67.0 tick=0.75 micro_vwap=-43.51
- record_id= code=031980 name=피에스케이홀딩스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.46 final=None ai=67.0 tick=3.0 micro_vwap=-0.71
- record_id= code=109740 name=디에스케이 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.42 final=None ai=59.0 tick=0.647 micro_vwap=3.3
- record_id= code=454910 name=두산로보틱스 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.42 final=None ai=66.0 tick=0.0 micro_vwap=-41.67
- record_id= code=457370 name=한켐 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.32 final=None ai=72.0 tick=1.095 micro_vwap=0.0
- record_id= code=149950 name=아바텍 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.33 final=None ai=72.0 tick=0.0 micro_vwap=-999.0
- record_id= code=439960 name=코스모로보틱스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.1 final=None ai=72.0 tick=0.667 micro_vwap=-4.05
- record_id= code=388870 name=파로스아이바이오 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.43 final=None ai=60.0 tick=0.0 micro_vwap=-999.0
- record_id= code=000880 name=메쥬 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.34 final=None ai=69.0 tick=0.0 micro_vwap=30.19
- record_id= code=183300 name=코미코 label=pyramid_open_unresolved blocker=trend_not_strong profit=2.88 final=None ai=63.0 tick=0.5 micro_vwap=-24.89
- record_id= code=242040 name=나무기술 label=pyramid_open_unresolved blocker=add_judgment_locked profit=2.74 final=None ai=61.0 tick=0.0 micro_vwap=109.86
- record_id= code=090360 name=로보스타 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.36 final=None ai=68.0 tick=0.0 micro_vwap=-89.8
- record_id= code=417860 name=오브젠 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.35 final=None ai=57.99999999999999 tick=0.0 micro_vwap=-999.0
- record_id= code=304360 name=에스바이오메딕스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.09 final=None ai=61.0 tick=0.0 micro_vwap=-8.55
- record_id= code=092220 name=KEC label=pyramid_open_unresolved blocker=profit_not_enough profit=0.89 final=None ai=66.0 tick=4.167 micro_vwap=-25.86
- record_id= code=319660 name=피에스케이 label=pyramid_open_unresolved blocker=add_judgment_locked profit=0.16 final=None ai=65.0 tick=3.0 micro_vwap=-10.92
- record_id= code=005380 name=현대차 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.93 final=None ai=66.0 tick=0.0 micro_vwap=-93.62
- record_id= code=011070 name=LG이노텍 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.37 final=None ai=70.0 tick=2.0 micro_vwap=-3.17
- record_id= code=499790 name=GS피앤엘 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.08 final=None ai=63.0 tick=0.1 micro_vwap=-18.11
- record_id= code=012330 name=현대모비스 label=pyramid_open_unresolved blocker=add_judgment_locked profit=2.33 final=None ai=68.0 tick=1.0 micro_vwap=-122.89
- record_id= code=055550 name=신한지주 label=pyramid_open_unresolved blocker=add_judgment_locked profit=0.05 final=None ai=72.0 tick=1.0 micro_vwap=-5.71
- record_id= code=000660 name=SK하이닉스 label=pyramid_open_unresolved blocker=add_judgment_locked profit=0.0 final=None ai=65.0 tick=0.0 micro_vwap=-35.85
- record_id= code=089030 name=테크윙 label=pyramid_open_unresolved blocker=add_judgment_locked profit=0.13 final=None ai=73.0 tick=3.0 micro_vwap=-35.29
- record_id= code=336260 name=두산퓨얼셀 label=pyramid_open_unresolved blocker=add_judgment_locked profit=0.12 final=None ai=62.0 tick=2.0 micro_vwap=35.06
- record_id= code=240810 name=원익IPS label=pyramid_open_unresolved blocker=profit_not_enough profit=0.14 final=None ai=72.0 tick=0.0 micro_vwap=-69.01
- record_id= code=128940 name=한미약품 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.07 final=None ai=68.0 tick=1.333 micro_vwap=7.68
- record_id= code=105330 name=케이엔더블유 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.09 final=None ai=60.0 tick=0.0 micro_vwap=-999.0
- record_id= code=040350 name=크레오에스지 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.27 final=None ai=64.0 tick=54.0 micro_vwap=-39.39
- record_id= code=307950 name=현대오토에버 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.73 final=None ai=64.0 tick=0.0 micro_vwap=-20.45
- record_id= code=001820 name=삼화콘덴서 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.83 final=None ai=66.0 tick=2.0 micro_vwap=-12.93

## One Share Opportunity Rows
