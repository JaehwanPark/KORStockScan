# 2026-06-26 Scalping Pyramid Intraday Feedback

- generated_at: 2026-07-03T13:24:28+09:00
- decision_authority: source_only_pyramid_intraday_feedback_no_runtime_mutation
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: intraday_threshold_mutation, intraday_runtime_apply, hard_safety_relaxation, broker_guard_bypass, order_guard_relaxation, stale_quote_bypass, cooldown_bypass, quantity_guard_relaxation, position_cap_release, provider_route_change, bot_restart, real_execution_quality_approval

## Summary

- pyramid_feedback_row_count: 28
- closed_pyramid_row_count: 6
- pyramid_would_have_helped_count: 1
- pyramid_correctly_blocked_count: 0
- pyramid_overheat_or_reversal_risk_count: 5
- pyramid_open_unresolved_count: 22
- one_share_event_count: 0
- one_share_closed_count: 0
- one_share_pyramid_opportunity_count: 0
- one_share_pyramid_missed_upside_count: 0
- one_share_pyramid_missed_upside_rate: 0.00
- one_share_pyramid_avg_opportunity_cost_pct: 0.00

## Blocker Metrics

- blocker=add_judgment_locked sample=1 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=profit_not_enough sample=22 recovered_rate=0.05 reversal_rate=0.18 blocked_then_recovered_rate=0.05
- blocker=scalping_buy_window_blocked sample=1 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=trend_not_strong sample=4 recovered_rate=0.00 reversal_rate=0.25 blocked_then_recovered_rate=0.00

## Rows

- record_id=13653 code=018260 name=삼성에스디에스 label=pyramid_would_have_helped blocker=profit_not_enough profit=0.51 final=2.75 ai=50.0 tick=0.0 micro_vwap=-756.37
- record_id= code=011790 name=SKC label=pyramid_open_unresolved blocker=profit_not_enough profit=1.43 final=None ai=70.0 tick=1.0 micro_vwap=-34.25
- record_id= code=017670 name=SK텔레콤 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.5 final=None ai=70.0 tick=1.0 micro_vwap=-4.28
- record_id=13634 code=376900 name=로킷헬스케어 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=0.1 final=-0.12 ai=83.0 tick=1.0 micro_vwap=-1146.33
- record_id= code=204270 name=제이앤티씨 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.77 final=None ai=73.0 tick=0.0 micro_vwap=-21.78
- record_id= code=037710 name=광주신세계 label=pyramid_open_unresolved blocker=add_judgment_locked profit=0.21 final=None ai=60.0 tick=0.0 micro_vwap=-999.0
- record_id= code=058970 name=엠로 label=pyramid_open_unresolved blocker=scalping_buy_window_blocked profit=0.4 final=None ai=72.0 tick=0.5 micro_vwap=-43.66
- record_id= code=036930 name=주성엔지니어링 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.84 final=None ai=72.0 tick=0.25 micro_vwap=21.37
- record_id= code=002990 name=금호건설 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.24 final=None ai=70.0 tick=2.0 micro_vwap=-324.31
- record_id=13632 code=003200 name=일신방직 label=pyramid_overheat_or_reversal_risk blocker=trend_not_strong profit=2.7 final=2.21 ai=82.0 tick=1.0 micro_vwap=112.36
- record_id=13633 code=037710 name=광주신세계 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=0.49 final=-2.51 ai=77.0 tick=0.0 micro_vwap=-197.51
- record_id=13689 code=353200 name=대덕전자 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=0.19 final=-1.74 ai=65.0 tick=0.333 micro_vwap=10.19
- record_id= code=383310 name=에코프로에이치엔 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.11 final=None ai=69.0 tick=1.333 micro_vwap=-76.73
- record_id= code=161890 name=한국콜마 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.32 final=None ai=73.0 tick=4.0 micro_vwap=-13.7
- record_id= code=011070 name=LG이노텍 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.31 final=None ai=67.0 tick=1.0 micro_vwap=184.68
- record_id= code=095610 name=테스 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.48 final=None ai=68.0 tick=4.0 micro_vwap=-20.69
- record_id= code=079650 name=서산 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.81 final=None ai=62.0 tick=0.0 micro_vwap=-999.0
- record_id= code=403870 name=HPSP label=pyramid_open_unresolved blocker=profit_not_enough profit=0.72 final=None ai=73.0 tick=1.333 micro_vwap=-29.34
- record_id= code=477850 name=마키나락스 label=pyramid_open_unresolved blocker=trend_not_strong profit=1.91 final=None ai=76.0 tick=5.0 micro_vwap=-24.6
- record_id= code=014950 name=삼익제약 label=pyramid_open_unresolved blocker=profit_not_enough profit=-0.0 final=None ai=72.0 tick=1.647 micro_vwap=-28.56
- record_id= code=000500 name=가온전선 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.39 final=None ai=62.0 tick=0.0 micro_vwap=-999.0
- record_id=13672 code=095610 name=테스 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=0.11 final=-0.12 ai=50.0 tick=0.5 micro_vwap=-13.93
- record_id= code=003200 name=일신방직 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.19 final=None ai=75.0 tick=0.0 micro_vwap=121.34
- record_id= code=089970 name=브이엠 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.01 final=None ai=73.0 tick=0.0 micro_vwap=27.0
- record_id= code=389260 name=대명에너지 label=pyramid_open_unresolved blocker=trend_not_strong profit=4.03 final=None ai=73.0 tick=1.0 micro_vwap=64.17
- record_id= code=376900 name=로킷헬스케어 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.48 final=None ai=62.0 tick=0.6 micro_vwap=2.69
- record_id= code=240810 name=원익IPS label=pyramid_open_unresolved blocker=profit_not_enough profit=0.38 final=None ai=76.0 tick=0.001 micro_vwap=273.66
- record_id= code=319660 name=피에스케이 label=pyramid_open_unresolved blocker=trend_not_strong profit=2.66 final=None ai=69.0 tick=1.0 micro_vwap=-90.83

## One Share Opportunity Rows
