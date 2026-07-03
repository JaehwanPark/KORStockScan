# 2026-06-23 Scalping Pyramid Intraday Feedback

- generated_at: 2026-07-03T13:24:12+09:00
- decision_authority: source_only_pyramid_intraday_feedback_no_runtime_mutation
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: intraday_threshold_mutation, intraday_runtime_apply, hard_safety_relaxation, broker_guard_bypass, order_guard_relaxation, stale_quote_bypass, cooldown_bypass, quantity_guard_relaxation, position_cap_release, provider_route_change, bot_restart, real_execution_quality_approval

## Summary

- pyramid_feedback_row_count: 35
- closed_pyramid_row_count: 1
- pyramid_would_have_helped_count: 0
- pyramid_correctly_blocked_count: 0
- pyramid_overheat_or_reversal_risk_count: 1
- pyramid_open_unresolved_count: 34
- one_share_event_count: 0
- one_share_closed_count: 0
- one_share_pyramid_opportunity_count: 0
- one_share_pyramid_missed_upside_count: 0
- one_share_pyramid_missed_upside_rate: 0.00
- one_share_pyramid_avg_opportunity_cost_pct: 0.00

## Blocker Metrics

- blocker=add_judgment_locked sample=2 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=profit_not_enough sample=29 recovered_rate=0.00 reversal_rate=0.03 blocked_then_recovered_rate=0.00
- blocker=scalping_buy_window_blocked sample=3 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=trend_not_strong sample=1 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00

## Rows

- record_id= code=028260 name=삼성물산 label=pyramid_open_unresolved blocker=scalping_buy_window_blocked profit=0.88 final=None ai=78.0 tick=2.0 micro_vwap=3.86
- record_id= code=195870 name=해성디에스 label=pyramid_open_unresolved blocker=scalping_buy_window_blocked profit=0.82 final=None ai=74.0 tick=1.606 micro_vwap=-23.14
- record_id= code=064400 name=LG씨엔에스 label=pyramid_open_unresolved blocker=scalping_buy_window_blocked profit=0.21 final=None ai=74.0 tick=0.0 micro_vwap=-11.12
- record_id= code=000990 name=DB하이텍 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.17 final=None ai=72.0 tick=2.0 micro_vwap=-50.62
- record_id= code=009830 name=한화솔루션 label=pyramid_open_unresolved blocker=add_judgment_locked profit=0.03 final=None ai=72.0 tick=2.0 micro_vwap=-46.39
- record_id= code=010690 name=화신 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.07 final=None ai=61.0 tick=0.0 micro_vwap=-38.6
- record_id= code=015760 name=한국전력 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.46 final=None ai=37.0 tick=0.0 micro_vwap=-0.51
- record_id= code=001820 name=삼화콘덴서 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.34 final=None ai=64.0 tick=0.0 micro_vwap=-61.54
- record_id= code=032820 name=우리기술 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.05 final=None ai=63.0 tick=2.0 micro_vwap=-140.45
- record_id= code=010140 name=삼성중공업 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.52 final=None ai=72.0 tick=1.0 micro_vwap=-48.04
- record_id= code=034020 name=두산에너빌리티 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.08 final=None ai=72.0 tick=1.0 micro_vwap=16.94
- record_id= code=368770 name=파이버프로 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.77 final=None ai=69.0 tick=0.333 micro_vwap=21.39
- record_id= code=055550 name=신한지주 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.35 final=None ai=68.0 tick=0.571 micro_vwap=-69.43
- record_id= code=001440 name=대한전선 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.43 final=None ai=69.0 tick=0.0 micro_vwap=-44.69
- record_id= code=330350 name=위더스제약 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.55 final=None ai=70.0 tick=1.333 micro_vwap=-107.77
- record_id= code=120110 name=코오롱인더 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.25 final=None ai=72.0 tick=4.0 micro_vwap=-17.39
- record_id= code=084670 name=동양고속 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.55 final=None ai=67.0 tick=3.0 micro_vwap=-80.41
- record_id=12663 code=006340 name=대원전선 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=1.3 final=1.12 ai=50.0 tick=1.0 micro_vwap=-8.91
- record_id= code=336570 name=원텍 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.75 final=None ai=64.0 tick=0.143 micro_vwap=-37.75
- record_id= code=053260 name=금강철강 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.06 final=None ai=63.0 tick=0.0 micro_vwap=52.16
- record_id= code=006220 name=제주은행 label=pyramid_open_unresolved blocker=add_judgment_locked profit=0.59 final=None ai=72.0 tick=1.557 micro_vwap=26.76
- record_id= code=034730 name=SK label=pyramid_open_unresolved blocker=profit_not_enough profit=0.17 final=None ai=71.0 tick=0.767 micro_vwap=-19.16
- record_id= code=122640 name=예스티 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.38 final=None ai=73.0 tick=0.0 micro_vwap=9.7
- record_id= code=475430 name=키스트론 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.88 final=None ai=64.0 tick=0.0 micro_vwap=24.94
- record_id= code=058430 name=포스코스틸리온 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.25 final=None ai=69.0 tick=1.0 micro_vwap=-7.09
- record_id= code=006340 name=대원전선 label=pyramid_open_unresolved blocker=trend_not_strong profit=2.64 final=None ai=62.0 tick=1.229 micro_vwap=-27.96
- record_id= code=264900 name=크라운제과 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.43 final=None ai=64.0 tick=1.5 micro_vwap=-14.59
- record_id= code=005740 name=크라운해태홀딩스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.12 final=None ai=64.0 tick=3.385 micro_vwap=3.6
- record_id= code=092790 name=넥스틸 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.88 final=None ai=74.0 tick=0.333 micro_vwap=-31.68
- record_id= code=320000 name=한울반도체 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.48 final=None ai=77.0 tick=1.0 micro_vwap=-249.9
- record_id= code=402340 name=SK스퀘어 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.08 final=None ai=66.0 tick=0.0 micro_vwap=50.8
- record_id= code=462870 name=시프트업 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.36 final=None ai=70.0 tick=1.0 micro_vwap=-37.42
- record_id= code=030960 name=양지사 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.2 final=None ai=80.0 tick=3.0 micro_vwap=-139.34
- record_id= code=290650 name=엘앤씨바이오 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.11 final=None ai=59.0 tick=1.111 micro_vwap=10.39
- record_id= code=356680 name=엑스게이트 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.64 final=None ai=60.0 tick=1.0 micro_vwap=-149.3

## One Share Opportunity Rows
