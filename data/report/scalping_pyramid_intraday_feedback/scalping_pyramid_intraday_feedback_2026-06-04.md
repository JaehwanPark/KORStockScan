# 2026-06-04 Scalping Pyramid Intraday Feedback

- generated_at: 2026-07-03T13:22:28+09:00
- decision_authority: source_only_pyramid_intraday_feedback_no_runtime_mutation
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: intraday_threshold_mutation, intraday_runtime_apply, hard_safety_relaxation, broker_guard_bypass, order_guard_relaxation, stale_quote_bypass, cooldown_bypass, quantity_guard_relaxation, position_cap_release, provider_route_change, bot_restart, real_execution_quality_approval

## Summary

- pyramid_feedback_row_count: 9
- closed_pyramid_row_count: 0
- pyramid_would_have_helped_count: 0
- pyramid_correctly_blocked_count: 0
- pyramid_overheat_or_reversal_risk_count: 0
- pyramid_open_unresolved_count: 9
- one_share_event_count: 0
- one_share_closed_count: 0
- one_share_pyramid_opportunity_count: 0
- one_share_pyramid_missed_upside_count: 0
- one_share_pyramid_missed_upside_rate: 0.00
- one_share_pyramid_avg_opportunity_cost_pct: 0.00

## Blocker Metrics

- blocker=profit_not_enough sample=7 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=scalping_cutoff sample=1 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=trend_not_strong sample=1 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00

## Rows

- record_id= code=090360 name=로보스타 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.2 final=None ai=78.0 tick=2.0 micro_vwap=-10.2
- record_id= code=000660 name=SK하이닉스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.2 final=None ai=73.0 tick=0.0 micro_vwap=-14.3
- record_id= code=011790 name=SKC label=pyramid_open_unresolved blocker=profit_not_enough profit=0.03 final=None ai=73.0 tick=1.0 micro_vwap=8.29
- record_id= code=031980 name=피에스케이홀딩스 label=pyramid_open_unresolved blocker=trend_not_strong profit=1.55 final=None ai=74.0 tick=0.5 micro_vwap=-27.4
- record_id= code=064400 name=LG씨엔에스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.48 final=None ai=68.0 tick=2.0 micro_vwap=-25.7
- record_id= code=098070 name=한텍 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.04 final=None ai=75.0 tick=0.846 micro_vwap=1.91
- record_id= code=023530 name=롯데쇼핑 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.12 final=None ai=72.0 tick=0.0 micro_vwap=46.3
- record_id= code=077360 name=덕산하이메탈 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.44 final=None ai=77.0 tick=0.52 micro_vwap=0.0
- record_id= code=036930 name=주성엔지니어링 label=pyramid_open_unresolved blocker=scalping_cutoff profit=0.58 final=None ai=76.0 tick=1.0 micro_vwap=55.89

## One Share Opportunity Rows
