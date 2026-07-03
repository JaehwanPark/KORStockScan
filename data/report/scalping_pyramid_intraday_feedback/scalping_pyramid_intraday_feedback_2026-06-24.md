# 2026-06-24 Scalping Pyramid Intraday Feedback

- generated_at: 2026-07-03T13:24:16+09:00
- decision_authority: source_only_pyramid_intraday_feedback_no_runtime_mutation
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: intraday_threshold_mutation, intraday_runtime_apply, hard_safety_relaxation, broker_guard_bypass, order_guard_relaxation, stale_quote_bypass, cooldown_bypass, quantity_guard_relaxation, position_cap_release, provider_route_change, bot_restart, real_execution_quality_approval

## Summary

- pyramid_feedback_row_count: 24
- closed_pyramid_row_count: 3
- pyramid_would_have_helped_count: 1
- pyramid_correctly_blocked_count: 0
- pyramid_overheat_or_reversal_risk_count: 2
- pyramid_open_unresolved_count: 21
- one_share_event_count: 0
- one_share_closed_count: 0
- one_share_pyramid_opportunity_count: 0
- one_share_pyramid_missed_upside_count: 0
- one_share_pyramid_missed_upside_rate: 0.00
- one_share_pyramid_avg_opportunity_cost_pct: 0.00

## Blocker Metrics

- blocker=profit_not_enough sample=23 recovered_rate=0.04 reversal_rate=0.09 blocked_then_recovered_rate=0.04
- blocker=trend_not_strong sample=1 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00

## Rows

- record_id= code=122640 name=예스티 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.13 final=None ai=70.0 tick=0.667 micro_vwap=16.44
- record_id= code=042660 name=한화오션 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.46 final=None ai=48.0 tick=2.0 micro_vwap=3.29
- record_id= code=001820 name=삼화콘덴서 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.17 final=None ai=58.0 tick=1.0 micro_vwap=-185.57
- record_id= code=012200 name=계양전기 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.49 final=None ai=66.0 tick=5.0 micro_vwap=69.39
- record_id= code=001740 name=SK네트웍스 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.39 final=None ai=62.0 tick=0.5 micro_vwap=-107.57
- record_id= code=009420 name=한올바이오파마 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.12 final=None ai=65.0 tick=0.826 micro_vwap=-3.75
- record_id=12793 code=095500 name=미래나노텍 label=pyramid_would_have_helped blocker=profit_not_enough profit=0.64 final=3.14 ai=66.0 tick=1.0 micro_vwap=65.35
- record_id= code=141080 name=리가켐바이오 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.29 final=None ai=62.0 tick=0.0 micro_vwap=-999.0
- record_id= code=032830 name=삼성생명 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.46 final=None ai=71.0 tick=0.5 micro_vwap=26.51
- record_id= code=095500 name=미래나노텍 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.16 final=None ai=69.0 tick=1.0 micro_vwap=79.07
- record_id= code=454910 name=두산로보틱스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.18 final=None ai=72.0 tick=0.5 micro_vwap=45.43
- record_id= code=090360 name=로보스타 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.21 final=None ai=67.0 tick=0.0 micro_vwap=-95.29
- record_id= code=002070 name=비비안 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.78 final=None ai=62.0 tick=0.0 micro_vwap=-999.0
- record_id= code=004310 name=현대약품 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.68 final=None ai=70.0 tick=2.0 micro_vwap=-29.9
- record_id= code=196170 name=알테오젠 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.18 final=None ai=69.0 tick=8.0 micro_vwap=2.37
- record_id= code=068270 name=셀트리온 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.35 final=None ai=56.0 tick=0.333 micro_vwap=-9.8
- record_id=12843 code=030960 name=양지사 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=0.05 final=-2.35 ai=58.0 tick=0.778 micro_vwap=-87.51
- record_id= code=290650 name=엘앤씨바이오 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.3 final=None ai=66.0 tick=0.38 micro_vwap=2.24
- record_id=12790 code=037710 name=광주신세계 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=0.13 final=-3.22 ai=67.0 tick=0.0 micro_vwap=-235.79
- record_id= code=014950 name=삼익제약 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.85 final=None ai=70.0 tick=1.0 micro_vwap=45.12
- record_id= code=439090 name=마녀공장 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.1 final=None ai=73.0 tick=0.5 micro_vwap=29.11
- record_id= code=397030 name=에이프릴바이오 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.01 final=None ai=72.0 tick=0.571 micro_vwap=22.22
- record_id= code=000660 name=SK하이닉스 label=pyramid_open_unresolved blocker=trend_not_strong profit=3.2 final=None ai=72.0 tick=1.0 micro_vwap=-6.76
- record_id= code=037710 name=광주신세계 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.03 final=None ai=72.0 tick=2.0 micro_vwap=32.91

## One Share Opportunity Rows
