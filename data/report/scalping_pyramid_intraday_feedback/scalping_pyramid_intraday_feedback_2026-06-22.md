# 2026-06-22 Scalping Pyramid Intraday Feedback

- generated_at: 2026-07-03T13:24:09+09:00
- decision_authority: source_only_pyramid_intraday_feedback_no_runtime_mutation
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: intraday_threshold_mutation, intraday_runtime_apply, hard_safety_relaxation, broker_guard_bypass, order_guard_relaxation, stale_quote_bypass, cooldown_bypass, quantity_guard_relaxation, position_cap_release, provider_route_change, bot_restart, real_execution_quality_approval

## Summary

- pyramid_feedback_row_count: 50
- closed_pyramid_row_count: 0
- pyramid_would_have_helped_count: 0
- pyramid_correctly_blocked_count: 0
- pyramid_overheat_or_reversal_risk_count: 0
- pyramid_open_unresolved_count: 50
- one_share_event_count: 0
- one_share_closed_count: 0
- one_share_pyramid_opportunity_count: 0
- one_share_pyramid_missed_upside_count: 0
- one_share_pyramid_missed_upside_rate: 0.00
- one_share_pyramid_avg_opportunity_cost_pct: 0.00

## Blocker Metrics

- blocker=near_market_close sample=6 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=profit_not_enough sample=40 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=trend_not_strong sample=4 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00

## Rows

- record_id= code=031330 name=에스에이엠티 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.0 final=None ai=76.0 tick=2.333 micro_vwap=-30.23
- record_id= code=112610 name=씨에스윈드 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.46 final=None ai=74.0 tick=1.0 micro_vwap=-39.71
- record_id= code=089030 name=테크윙 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.05 final=None ai=70.0 tick=1.154 micro_vwap=14.79
- record_id= code=138080 name=오이솔루션 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.28 final=None ai=74.0 tick=0.484 micro_vwap=-31.21
- record_id= code=242040 name=나무기술 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.41 final=None ai=69.0 tick=1.6 micro_vwap=-27.7
- record_id= code=067310 name=하나마이크론 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.51 final=None ai=68.0 tick=0.5 micro_vwap=20.99
- record_id= code=001820 name=삼화콘덴서 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.05 final=None ai=63.0 tick=0.667 micro_vwap=-5.01
- record_id= code=222800 name=심텍 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.12 final=None ai=71.0 tick=2.0 micro_vwap=9.42
- record_id= code=074600 name=원익QnC label=pyramid_open_unresolved blocker=profit_not_enough profit=0.16 final=None ai=75.0 tick=1.5 micro_vwap=-27.69
- record_id= code=059090 name=미코 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.67 final=None ai=57.99999999999999 tick=0.0 micro_vwap=-999.0
- record_id= code=112290 name=와이씨켐 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.08 final=None ai=72.0 tick=2.667 micro_vwap=-139.17
- record_id= code=131970 name=두산테스나 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.11 final=None ai=51.0 tick=7.0 micro_vwap=-12.03
- record_id= code=420770 name=기가비스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.33 final=None ai=65.0 tick=0.769 micro_vwap=6.93
- record_id= code=170920 name=엘티씨 label=pyramid_open_unresolved blocker=trend_not_strong profit=2.0 final=None ai=70.0 tick=13.0 micro_vwap=-17.34
- record_id= code=195870 name=해성디에스 label=pyramid_open_unresolved blocker=trend_not_strong profit=7.27 final=None ai=56.0 tick=0.833 micro_vwap=4.13
- record_id= code=033640 name=네패스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.2 final=None ai=72.0 tick=0.8 micro_vwap=-41.31
- record_id= code=095610 name=테스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.67 final=None ai=66.0 tick=1.0 micro_vwap=-29.88
- record_id= code=475430 name=키스트론 label=pyramid_open_unresolved blocker=trend_not_strong profit=4.79 final=None ai=62.0 tick=0.452 micro_vwap=33.2
- record_id= code=028260 name=삼성물산 label=pyramid_open_unresolved blocker=trend_not_strong profit=1.89 final=None ai=64.0 tick=0.5 micro_vwap=22.01
- record_id= code=046970 name=우리로 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.69 final=None ai=68.0 tick=1.667 micro_vwap=-40.93
- record_id= code=000500 name=가온전선 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.35 final=None ai=61.0 tick=0.667 micro_vwap=-7.32
- record_id= code=290650 name=엘앤씨바이오 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.11 final=None ai=75.0 tick=0.125 micro_vwap=1.62
- record_id= code=089970 name=브이엠 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.47 final=None ai=74.0 tick=0.0 micro_vwap=-25.3
- record_id= code=426030 name=TIME 미국나스닥100액티브 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.02 final=None ai=73.0 tick=1.0 micro_vwap=0.32
- record_id= code=003550 name=LG label=pyramid_open_unresolved blocker=profit_not_enough profit=0.21 final=None ai=70.0 tick=3.0 micro_vwap=-9.66
- record_id= code=368770 name=파이버프로 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.69 final=None ai=73.0 tick=0.75 micro_vwap=-26.02
- record_id= code=311320 name=지오엘리먼트 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.22 final=None ai=74.0 tick=0.514 micro_vwap=66.51
- record_id= code=031980 name=피에스케이홀딩스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.01 final=None ai=72.0 tick=0.083 micro_vwap=-62.1
- record_id= code=025560 name=미래산업 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.56 final=None ai=62.0 tick=1.31 micro_vwap=-5.01
- record_id= code=475580 name=에이럭스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.33 final=None ai=69.0 tick=0.4 micro_vwap=-55.94
- record_id= code=004310 name=현대약품 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.57 final=None ai=73.0 tick=1.0 micro_vwap=-198.55
- record_id= code=474590 name=WON 반도체밸류체인액티브 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.03 final=None ai=74.0 tick=0.114 micro_vwap=-9.45
- record_id= code=004710 name=한솔테크닉스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.02 final=None ai=68.0 tick=1.0 micro_vwap=11.12
- record_id= code=482630 name=삼양엔씨켐 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.26 final=None ai=62.0 tick=0.0 micro_vwap=-999.0
- record_id= code=319660 name=피에스케이 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.32 final=None ai=72.0 tick=1.0 micro_vwap=-36.68
- record_id= code=240810 name=원익IPS label=pyramid_open_unresolved blocker=profit_not_enough profit=0.6 final=None ai=73.0 tick=0.0 micro_vwap=-25.61
- record_id= code=442580 name=PLUS 글로벌HBM반도체 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.02 final=None ai=76.0 tick=0.375 micro_vwap=6.9
- record_id= code=320000 name=한울반도체 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.21 final=None ai=77.0 tick=0.667 micro_vwap=-28.86
- record_id= code=093370 name=후성 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.21 final=None ai=67.0 tick=0.667 micro_vwap=4.23
- record_id= code=293490 name=카카오게임즈 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.83 final=None ai=69.0 tick=0.5 micro_vwap=5.93
- record_id= code=077360 name=덕산하이메탈 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.94 final=None ai=62.0 tick=0.4 micro_vwap=0.0
- record_id= code=119830 name=아이텍 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.57 final=None ai=70.0 tick=2.2 micro_vwap=-53.76
- record_id= code=440110 name=파두 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.64 final=None ai=66.0 tick=0.667 micro_vwap=-8.71
- record_id= code=080220 name=제주반도체 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.69 final=None ai=60.0 tick=1.0 micro_vwap=44.97
- record_id= code=011070 name=LG이노텍 label=pyramid_open_unresolved blocker=near_market_close profit=0.02 final=None ai=73.0 tick=1.0 micro_vwap=-1.64
- record_id= code=064400 name=LG씨엔에스 label=pyramid_open_unresolved blocker=near_market_close profit=0.1 final=None ai=71.0 tick=1.5 micro_vwap=-7.12
- record_id= code=356680 name=엑스게이트 label=pyramid_open_unresolved blocker=near_market_close profit=0.31 final=None ai=75.0 tick=0.333 micro_vwap=26.83
- record_id= code=402340 name=SK스퀘어 label=pyramid_open_unresolved blocker=near_market_close profit=0.01 final=None ai=72.0 tick=0.0 micro_vwap=8.38
- record_id= code=090360 name=로보스타 label=pyramid_open_unresolved blocker=near_market_close profit=0.07 final=None ai=58.0 tick=2.5 micro_vwap=23.4
- record_id= code=000990 name=DB하이텍 label=pyramid_open_unresolved blocker=near_market_close profit=0.29 final=None ai=59.0 tick=0.667 micro_vwap=12.41

## One Share Opportunity Rows
