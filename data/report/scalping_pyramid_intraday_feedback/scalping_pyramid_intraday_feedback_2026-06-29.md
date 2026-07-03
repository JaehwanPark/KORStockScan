# 2026-06-29 Scalping Pyramid Intraday Feedback

- generated_at: 2026-07-03T13:24:35+09:00
- decision_authority: source_only_pyramid_intraday_feedback_no_runtime_mutation
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: intraday_threshold_mutation, intraday_runtime_apply, hard_safety_relaxation, broker_guard_bypass, order_guard_relaxation, stale_quote_bypass, cooldown_bypass, quantity_guard_relaxation, position_cap_release, provider_route_change, bot_restart, real_execution_quality_approval

## Summary

- pyramid_feedback_row_count: 16
- closed_pyramid_row_count: 1
- pyramid_would_have_helped_count: 0
- pyramid_correctly_blocked_count: 0
- pyramid_overheat_or_reversal_risk_count: 1
- pyramid_open_unresolved_count: 15
- one_share_event_count: 0
- one_share_closed_count: 0
- one_share_pyramid_opportunity_count: 0
- one_share_pyramid_missed_upside_count: 0
- one_share_pyramid_missed_upside_rate: 0.00
- one_share_pyramid_avg_opportunity_cost_pct: 0.00

## Blocker Metrics

- blocker=profit_not_enough sample=16 recovered_rate=0.00 reversal_rate=0.06 blocked_then_recovered_rate=0.00

## Rows

- record_id= code=089970 name=브이엠 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.39 final=None ai=70.0 tick=1.5 micro_vwap=26.06
- record_id= code=095610 name=테스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.92 final=None ai=72.0 tick=0.0 micro_vwap=139.78
- record_id= code=003200 name=일신방직 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.69 final=None ai=69.0 tick=0.143 micro_vwap=-48.04
- record_id= code=034230 name=파라다이스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.93 final=None ai=70.0 tick=1.0 micro_vwap=-101.24
- record_id= code=009150 name=삼성전기 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.47 final=None ai=68.0 tick=0.0 micro_vwap=45.91
- record_id= code=004310 name=현대약품 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.15 final=None ai=41.0 tick=2.25 micro_vwap=353.46
- record_id= code=010120 name=LS ELECTRIC label=pyramid_open_unresolved blocker=profit_not_enough profit=0.44 final=None ai=70.0 tick=0.5 micro_vwap=-13.91
- record_id= code=009420 name=한올바이오파마 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.35 final=None ai=72.0 tick=5.0 micro_vwap=-40.36
- record_id=14081 code=373220 name=LG에너지솔루션 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=1.18 final=1.05 ai=73.0 tick=2.0 micro_vwap=-22.18
- record_id= code=004980 name=성신양회 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.57 final=None ai=75.0 tick=0.443 micro_vwap=15.21
- record_id= code=093370 name=후성 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.58 final=None ai=70.0 tick=0.644 micro_vwap=43.5
- record_id=13961 code=226950 name=올릭스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.91 final=None ai=68.0 tick=3.8 micro_vwap=3.87
- record_id= code=006400 name=삼성SDI label=pyramid_open_unresolved blocker=profit_not_enough profit=0.16 final=None ai=75.0 tick=0.0 micro_vwap=43.71
- record_id= code=226950 name=올릭스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.72 final=None ai=66.0 tick=4.222 micro_vwap=1.61
- record_id= code=247540 name=에코프로비엠 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.33 final=None ai=59.0 tick=0.001 micro_vwap=564.36
- record_id= code=086520 name=에코프로 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.42 final=None ai=62.0 tick=0.235 micro_vwap=469.87

## One Share Opportunity Rows
