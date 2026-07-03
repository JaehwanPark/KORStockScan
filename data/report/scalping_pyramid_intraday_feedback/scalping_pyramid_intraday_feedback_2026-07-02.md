# 2026-07-02 Scalping Pyramid Intraday Feedback

- generated_at: 2026-07-03T13:24:49+09:00
- decision_authority: source_only_pyramid_intraday_feedback_no_runtime_mutation
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: intraday_threshold_mutation, intraday_runtime_apply, hard_safety_relaxation, broker_guard_bypass, order_guard_relaxation, stale_quote_bypass, cooldown_bypass, quantity_guard_relaxation, position_cap_release, provider_route_change, bot_restart, real_execution_quality_approval

## Summary

- pyramid_feedback_row_count: 38
- closed_pyramid_row_count: 17
- pyramid_would_have_helped_count: 6
- pyramid_correctly_blocked_count: 0
- pyramid_overheat_or_reversal_risk_count: 11
- pyramid_open_unresolved_count: 21
- one_share_event_count: 39
- one_share_closed_count: 16
- one_share_pyramid_opportunity_count: 21
- one_share_pyramid_missed_upside_count: 6
- one_share_pyramid_missed_upside_rate: 0.38
- one_share_pyramid_avg_opportunity_cost_pct: 0.83

## Blocker Metrics

- blocker=add_judgment_locked sample=1 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=profit_not_enough sample=27 recovered_rate=0.15 reversal_rate=0.19 blocked_then_recovered_rate=0.15
- blocker=pyramid_quality_blocked:ai_score_below_min,large_sell_detected,micro_vwap_overheated sample=1 recovered_rate=0.00 reversal_rate=1.00 blocked_then_recovered_rate=0.00
- blocker=pyramid_quality_blocked:ai_score_below_min,tick_accel_below_min,large_sell_detected,micro_vwap_missing sample=1 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=pyramid_quality_blocked:ai_score_below_min,tick_accel_below_min,micro_vwap_overheated sample=2 recovered_rate=0.00 reversal_rate=0.50 blocked_then_recovered_rate=0.00
- blocker=pyramid_quality_blocked:tick_accel_below_min,micro_vwap_overheated sample=1 recovered_rate=0.00 reversal_rate=1.00 blocked_then_recovered_rate=0.00
- blocker=scale_in_cooldown sample=1 recovered_rate=1.00 reversal_rate=0.00 blocked_then_recovered_rate=1.00
- blocker=scalping_buy_window_blocked sample=1 recovered_rate=1.00 reversal_rate=0.00 blocked_then_recovered_rate=1.00
- blocker=trend_not_strong sample=3 recovered_rate=0.00 reversal_rate=1.00 blocked_then_recovered_rate=0.00

## Rows

- record_id=14774 code=033100 name=제룡전기 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.35 final=None ai=60.0 tick=0.0 micro_vwap=63.66
- record_id=14980 code=073240 name=금호타이어 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.16 final=None ai=70.0 tick=1.0 micro_vwap=-75.43
- record_id=14984 code=082740 name=한화엔진 label=pyramid_overheat_or_reversal_risk blocker=trend_not_strong profit=2.38 final=1.68 ai=66.0 tick=0.0 micro_vwap=190.14
- record_id=14976 code=037710 name=광주신세계 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.19 final=None ai=67.0 tick=2.0 micro_vwap=-616.3
- record_id=14966 code=378340 name=필에너지 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.3 final=None ai=72.0 tick=0.5 micro_vwap=-81.25
- record_id=14969 code=018260 name=삼성에스디에스 label=pyramid_open_unresolved blocker=add_judgment_locked profit=0.01 final=None ai=69.0 tick=1.0 micro_vwap=-340.15
- record_id=14996 code=082740 name=한화엔진 label=pyramid_would_have_helped blocker=scalping_buy_window_blocked profit=0.64 final=2.19 ai=73.0 tick=1.0 micro_vwap=56.93
- record_id=14723 code=005930 name=삼성전자 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=1.38 final=1.13 ai=70.0 tick=0.0 micro_vwap=-4.93
- record_id= code=018260 name=삼성에스디에스 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.46 final=None ai=69.0 tick=1.0 micro_vwap=26.66
- record_id= code=006400 name=삼성SDI label=pyramid_open_unresolved blocker=profit_not_enough profit=0.08 final=None ai=65.0 tick=2.0 micro_vwap=-14.31
- record_id=15035 code=001260 name=남광토건 label=pyramid_would_have_helped blocker=profit_not_enough profit=1.02 final=4.14 ai=68.0 tick=0.4 micro_vwap=65.96
- record_id=14974 code=486990 name=노타 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=0.21 final=-3.32 ai=71.0 tick=0.235 micro_vwap=-10.04
- record_id=15056 code=001260 name=남광토건 label=pyramid_would_have_helped blocker=profit_not_enough profit=1.25 final=1.6 ai=72.0 tick=1.333 micro_vwap=29.99
- record_id= code=001260 name=남광토건 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.63 final=None ai=62.0 tick=0.0 micro_vwap=-999.0
- record_id=14999 code=378340 name=필에너지 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=0.2 final=0.06 ai=71.0 tick=1.0 micro_vwap=93.08
- record_id=15011 code=005930 name=삼성전자 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=0.02 final=-3.25 ai=71.0 tick=0.0 micro_vwap=-10.48
- record_id= code=024840 name=KBI메탈 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.73 final=None ai=68.0 tick=1.0 micro_vwap=119.74
- record_id= code=042940 name=상지건설 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.62 final=None ai=78.0 tick=0.0 micro_vwap=-999.0
- record_id=15062 code=001260 name=남광토건 label=pyramid_would_have_helped blocker=profit_not_enough profit=0.09 final=0.42 ai=69.0 tick=0.333 micro_vwap=117.02
- record_id=15068 code=007610 name=선도전기 label=pyramid_overheat_or_reversal_risk blocker=trend_not_strong profit=1.71 final=1.23 ai=65.0 tick=0.857 micro_vwap=-22.28
- record_id=15089 code=007610 name=선도전기 label=pyramid_would_have_helped blocker=scale_in_cooldown profit=0.34 final=1.52 ai=61.0 tick=1.0 micro_vwap=180.04
- record_id= code=064400 name=LG씨엔에스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.14 final=None ai=69.0 tick=1.0 micro_vwap=-32.85
- record_id= code=052420 name=오성첨단소재 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.96 final=None ai=61.0 tick=0.9 micro_vwap=84.94
- record_id=15036 code=013580 name=계룡건설 label=pyramid_would_have_helped blocker=profit_not_enough profit=0.71 final=3.53 ai=70.0 tick=0.0 micro_vwap=44.19
- record_id= code=028670 name=팬오션 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.16 final=None ai=70.0 tick=1.0 micro_vwap=27.91
- record_id= code=012450 name=한화에어로스페이스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.72 final=None ai=60.0 tick=0.0 micro_vwap=-49.9
- record_id=15100 code=007610 name=선도전기 label=pyramid_overheat_or_reversal_risk blocker=pyramid_quality_blocked:ai_score_below_min,tick_accel_below_min,micro_vwap_overheated profit=3.3 final=2.98 ai=50.0 tick=1.0 micro_vwap=46.95
- record_id=15106 code=007610 name=선도전기 label=pyramid_overheat_or_reversal_risk blocker=trend_not_strong profit=2.74 final=-1.17 ai=70.0 tick=0.0 micro_vwap=-59.64
- record_id= code=007610 name=선도전기 label=pyramid_open_unresolved blocker=pyramid_quality_blocked:ai_score_below_min,tick_accel_below_min,large_sell_detected,micro_vwap_missing profit=2.58 final=None ai=60.0 tick=0.0 micro_vwap=None
- record_id=15105 code=013580 name=계룡건설 label=pyramid_overheat_or_reversal_risk blocker=pyramid_quality_blocked:tick_accel_below_min,micro_vwap_overheated profit=3.98 final=1.65 ai=69.0 tick=0.333 micro_vwap=52.63
- record_id= code=101730 name=위메이드맥스 label=pyramid_open_unresolved blocker=pyramid_quality_blocked:ai_score_below_min,tick_accel_below_min,micro_vwap_overheated profit=1.9 final=None ai=70.0 tick=1.625 micro_vwap=6.08
- record_id=14997 code=101730 name=위메이드맥스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.17 final=None ai=66.0 tick=0.3 micro_vwap=-14.14
- record_id=15064 code=378340 name=필에너지 label=pyramid_overheat_or_reversal_risk blocker=pyramid_quality_blocked:ai_score_below_min,large_sell_detected,micro_vwap_overheated profit=2.17 final=1.93 ai=64.0 tick=0.0 micro_vwap=69.31
- record_id=15082 code=486990 name=노타 label=pyramid_overheat_or_reversal_risk blocker=profit_not_enough profit=0.47 final=0.24 ai=65.0 tick=1.049 micro_vwap=-109.79
- record_id=14989 code=094360 name=칩스앤미디어 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.1 final=None ai=68.0 tick=2.0 micro_vwap=-153.89
- record_id= code=094360 name=칩스앤미디어 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.38 final=None ai=69.0 tick=0.0 micro_vwap=-58.6
- record_id= code=035420 name=NAVER label=pyramid_open_unresolved blocker=profit_not_enough profit=0.22 final=None ai=70.0 tick=1.0 micro_vwap=-0.25
- record_id= code=055550 name=신한지주 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.14 final=None ai=65.0 tick=1.0 micro_vwap=-29.5

## One Share Opportunity Rows

- record_id=14973 code=042660 name=한화오션 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=14970 code=010060 name=OCI홀딩스 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=14968 code=488280 name=에스투더블유 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=14969 code=018260 name=삼성에스디에스 label=pyramid_open_unresolved opportunity_seen=True opportunity_profit=0.01 max_profit=0.49 opportunity_cost=0.48 final=None
- record_id=14980 code=073240 name=금호타이어 label=pyramid_open_unresolved opportunity_seen=True opportunity_profit=0.16 max_profit=0.36 opportunity_cost=0.2 final=None
- record_id=14984 code=082740 name=한화엔진 label=pyramid_overheat_or_reversal_risk opportunity_seen=True opportunity_profit=2.38 max_profit=2.38 opportunity_cost=0.0 final=1.68
- record_id=14993 code=010140 name=삼성중공업 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=14976 code=037710 name=광주신세계 label=pyramid_open_unresolved opportunity_seen=True opportunity_profit=0.19 max_profit=0.19 opportunity_cost=0.0 final=None
- record_id=14996 code=082740 name=한화엔진 label=pyramid_would_have_helped opportunity_seen=True opportunity_profit=0.64 max_profit=2.89 opportunity_cost=2.25 final=2.19
- record_id=14966 code=378340 name=필에너지 label=pyramid_open_unresolved opportunity_seen=True opportunity_profit=0.3 max_profit=0.3 opportunity_cost=0.0 final=None
- record_id=14994 code=010140 name=삼성중공업 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=14985 code=488280 name=에스투더블유 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=14999 code=378340 name=필에너지 label=pyramid_overheat_or_reversal_risk opportunity_seen=True opportunity_profit=0.2 max_profit=0.49 opportunity_cost=0.29 final=0.06
- record_id=15035 code=001260 name=남광토건 label=pyramid_would_have_helped opportunity_seen=True opportunity_profit=1.02 max_profit=5.39 opportunity_cost=4.37 final=4.14
- record_id=14974 code=486990 name=노타 label=pyramid_overheat_or_reversal_risk opportunity_seen=True opportunity_profit=0.21 max_profit=0.87 opportunity_cost=0.66 final=-3.32
- record_id=15056 code=001260 name=남광토건 label=pyramid_would_have_helped opportunity_seen=True opportunity_profit=1.25 max_profit=2.55 opportunity_cost=1.3 final=1.6
- record_id=15045 code=007610 name=선도전기 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=15062 code=001260 name=남광토건 label=pyramid_would_have_helped opportunity_seen=True opportunity_profit=0.09 max_profit=0.98 opportunity_cost=0.89 final=0.42
- record_id=15068 code=007610 name=선도전기 label=pyramid_overheat_or_reversal_risk opportunity_seen=True opportunity_profit=1.71 max_profit=2.03 opportunity_cost=0.32 final=1.23
- record_id=15040 code=267260 name=HD현대일렉트릭 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=15084 code=001260 name=남광토건 label=pyramid_correctly_blocked opportunity_seen=False opportunity_profit=None max_profit=0.3 opportunity_cost=0.3 final=-4.65
- record_id=15089 code=007610 name=선도전기 label=pyramid_would_have_helped opportunity_seen=True opportunity_profit=0.34 max_profit=1.86 opportunity_cost=1.52 final=1.52
- record_id=15036 code=013580 name=계룡건설 label=pyramid_would_have_helped opportunity_seen=True opportunity_profit=0.71 max_profit=4.29 opportunity_cost=3.58 final=3.53
- record_id=15100 code=007610 name=선도전기 label=pyramid_overheat_or_reversal_risk opportunity_seen=True opportunity_profit=3.3 max_profit=3.78 opportunity_cost=0.48 final=2.98
- record_id=15104 code=013580 name=계룡건설 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=15105 code=013580 name=계룡건설 label=pyramid_overheat_or_reversal_risk opportunity_seen=True opportunity_profit=3.98 max_profit=3.98 opportunity_cost=0.0 final=1.65
- record_id=15106 code=007610 name=선도전기 label=pyramid_overheat_or_reversal_risk opportunity_seen=True opportunity_profit=2.74 max_profit=3.05 opportunity_cost=0.31 final=-1.17
- record_id=15101 code=001260 name=남광토건 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=15111 code=007610 name=선도전기 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=15065 code=477850 name=마키나락스 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=15112 code=013580 name=계룡건설 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=14997 code=101730 name=위메이드맥스 label=pyramid_open_unresolved opportunity_seen=True opportunity_profit=0.17 max_profit=0.37 opportunity_cost=0.2 final=None
- record_id=15064 code=378340 name=필에너지 label=pyramid_overheat_or_reversal_risk opportunity_seen=True opportunity_profit=2.17 max_profit=2.17 opportunity_cost=0.0 final=1.93
- record_id=15142 code=101730 name=위메이드맥스 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=-0.23 opportunity_cost=0.0 final=None
- record_id=15082 code=486990 name=노타 label=pyramid_overheat_or_reversal_risk opportunity_seen=True opportunity_profit=0.47 max_profit=0.7 opportunity_cost=0.23 final=0.24
- record_id=14989 code=094360 name=칩스앤미디어 label=pyramid_open_unresolved opportunity_seen=True opportunity_profit=0.1 max_profit=0.49 opportunity_cost=0.39 final=None
- record_id=15161 code=378340 name=필에너지 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=15164 code=094360 name=칩스앤미디어 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=15162 code=486990 name=노타 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
