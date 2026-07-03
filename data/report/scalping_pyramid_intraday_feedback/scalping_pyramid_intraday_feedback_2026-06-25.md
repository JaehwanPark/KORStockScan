# 2026-06-25 Scalping Pyramid Intraday Feedback

- generated_at: 2026-07-03T13:24:22+09:00
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

- record_id= code=376900 name=로킷헬스케어 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.65 final=None ai=66.0 tick=0.667 micro_vwap=14.88
- record_id= code=006800 name=미래에셋증권 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.55 final=None ai=71.0 tick=1.0 micro_vwap=-62.95
- record_id= code=001820 name=삼화콘덴서 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.27 final=None ai=72.0 tick=1.0 micro_vwap=32.02
- record_id=13299 code=222800 name=심텍 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=0.61 final=0.07 ai=72.0 tick=1.25 micro_vwap=-31.06
- record_id= code=073240 name=금호타이어 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.19 final=None ai=70.0 tick=1.0 micro_vwap=-12.74
- record_id= code=009420 name=한올바이오파마 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.09 final=None ai=68.0 tick=9.0 micro_vwap=-18.13
- record_id= code=475430 name=키스트론 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.17 final=None ai=72.0 tick=1.0 micro_vwap=-140.19
- record_id= code=037710 name=광주신세계 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.23 final=None ai=71.0 tick=0.136 micro_vwap=2.33
- record_id= code=100090 name=SK오션플랜트 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.11 final=None ai=70.0 tick=0.333 micro_vwap=-4.85
- record_id= code=014950 name=삼익제약 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.42 final=None ai=72.0 tick=2.0 micro_vwap=-105.17
- record_id= code=003490 name=대한항공 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.11 final=None ai=70.0 tick=0.0 micro_vwap=2.06
- record_id= code=034730 name=SK label=pyramid_open_unresolved blocker=profit_not_enough profit=0.23 final=None ai=73.0 tick=2.0 micro_vwap=-19.3
- record_id= code=469610 name=이노테크 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.23 final=None ai=74.0 tick=0.064 micro_vwap=-18.61
- record_id= code=001740 name=SK네트웍스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.23 final=None ai=72.0 tick=0.0 micro_vwap=-43.53
- record_id= code=439090 name=마녀공장 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.05 final=None ai=73.0 tick=0.125 micro_vwap=46.84
- record_id= code=389260 name=대명에너지 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.25 final=None ai=73.0 tick=0.0 micro_vwap=-11.07

## One Share Opportunity Rows
