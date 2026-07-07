# 2026-07-07 Scalping Pyramid Intraday Feedback

- generated_at: 2026-07-07T20:10:41+09:00
- decision_authority: source_only_pyramid_intraday_feedback_no_runtime_mutation
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: intraday_threshold_mutation, intraday_runtime_apply, hard_safety_relaxation, broker_guard_bypass, order_guard_relaxation, stale_quote_bypass, cooldown_bypass, quantity_guard_relaxation, position_cap_release, provider_route_change, bot_restart, real_execution_quality_approval

## Summary

- pyramid_feedback_row_count: 13
- closed_pyramid_row_count: 7
- pyramid_would_have_helped_count: 1
- pyramid_correctly_blocked_count: 3
- pyramid_overheat_or_reversal_risk_count: 3
- pyramid_open_unresolved_count: 6
- one_share_event_count: 39
- one_share_closed_count: 19
- one_share_pyramid_opportunity_count: 17
- one_share_pyramid_missed_upside_count: 7
- one_share_pyramid_missed_upside_rate: 0.37
- one_share_pyramid_avg_opportunity_cost_pct: 1.14

## Blocker Metrics

- blocker=profit_not_enough sample=2 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=pyramid_quality_blocked:ai_score_below_min,tick_aggressor_pressure_unusable,tick_accel_stale,micro_context_stale sample=1 recovered_rate=0.00 reversal_rate=1.00 blocked_then_recovered_rate=0.00
- blocker=pyramid_quality_blocked:ai_score_unavailable,tick_aggressor_pressure_unusable,tick_accel_stale,micro_context_stale sample=2 recovered_rate=0.00 reversal_rate=0.50 blocked_then_recovered_rate=0.00
- blocker=rising_missed_scout_pyramid_bridge_blocked:micro_context_stale,tick_aggressor_pressure_unusable,fresh_micro_confirmation_missing,tick_accel_stale sample=1 recovered_rate=0.00 reversal_rate=1.00 blocked_then_recovered_rate=0.00
- blocker=rising_missed_scout_pyramid_bridge_blocked:profit_not_enough sample=1 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=rising_missed_scout_pyramid_bridge_blocked:profit_not_enough,buy_pressure_severe_below_min,large_sell_detected sample=1 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=rising_missed_scout_pyramid_bridge_blocked:profit_not_enough,micro_context_stale,tick_aggressor_pressure_unusable,fresh_micro_confirmation_missing,tick_accel_stale sample=4 recovered_rate=0.25 reversal_rate=0.00 blocked_then_recovered_rate=0.25
- blocker=rising_missed_scout_pyramid_bridge_blocked:profit_not_enough,quote_stale,micro_context_stale,tick_aggressor_pressure_unusable,fresh_micro_confirmation_missing,tick_accel_stale sample=1 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00

## Rows

- record_id=15640 code=200710 name=에이디테크놀로지 label=pyramid_overheat_or_reversal_risk blocker=pyramid_quality_blocked:ai_score_below_min,tick_aggressor_pressure_unusable,tick_accel_stale,micro_context_stale profit=1.4 final=0.91 ai=50.0 tick=0.278 micro_vwap=-4.83
- record_id= code=161390 name=한국타이어앤테크놀로지 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.18 final=None ai=55.0 tick=1.0 micro_vwap=-12.07
- record_id=15777 code=399720 name=가온칩스 label=pyramid_would_have_helped blocker=rising_missed_scout_pyramid_bridge_blocked:profit_not_enough,micro_context_stale,tick_aggressor_pressure_unusable,fresh_micro_confirmation_missing,tick_accel_stale profit=0.08 final=0.28 ai=54.0 tick=1.333 micro_vwap=41.68
- record_id=15638 code=073240 name=금호타이어 label=pyramid_overheat_or_reversal_risk blocker=rising_missed_scout_pyramid_bridge_blocked:micro_context_stale,tick_aggressor_pressure_unusable,fresh_micro_confirmation_missing,tick_accel_stale profit=0.88 final=0.56 ai=50.0 tick=1.0 micro_vwap=4.7
- record_id=15842 code=073240 name=금호타이어 label=pyramid_overheat_or_reversal_risk blocker=pyramid_quality_blocked:ai_score_unavailable,tick_aggressor_pressure_unusable,tick_accel_stale,micro_context_stale profit=1.64 final=1.17 ai=50.0 tick=1.0 micro_vwap=-38.37
- record_id=15857 code=073240 name=금호타이어 label=pyramid_correctly_blocked blocker=rising_missed_scout_pyramid_bridge_blocked:profit_not_enough,micro_context_stale,tick_aggressor_pressure_unusable,fresh_micro_confirmation_missing,tick_accel_stale profit=0.08 final=0.4 ai=58.0 tick=1.667 micro_vwap=9.35
- record_id=15878 code=073240 name=금호타이어 label=pyramid_open_unresolved blocker=rising_missed_scout_pyramid_bridge_blocked:profit_not_enough,buy_pressure_severe_below_min,large_sell_detected profit=0.08 final=None ai=50.0 tick=1.333 micro_vwap=-28.44
- record_id= code=073240 name=금호타이어 label=pyramid_open_unresolved blocker=rising_missed_scout_pyramid_bridge_blocked:profit_not_enough profit=0.55 final=None ai=61.0 tick=1.0 micro_vwap=13.95
- record_id=15814 code=439090 name=마녀공장 label=pyramid_correctly_blocked blocker=rising_missed_scout_pyramid_bridge_blocked:profit_not_enough,micro_context_stale,tick_aggressor_pressure_unusable,fresh_micro_confirmation_missing,tick_accel_stale profit=0.09 final=0.4 ai=50.0 tick=13.0 micro_vwap=27.19
- record_id=15761 code=237880 name=클리오 label=pyramid_open_unresolved blocker=rising_missed_scout_pyramid_bridge_blocked:profit_not_enough,micro_context_stale,tick_aggressor_pressure_unusable,fresh_micro_confirmation_missing,tick_accel_stale profit=0.44 final=None ai=64.0 tick=2.0 micro_vwap=83.4
- record_id= code=439090 name=마녀공장 label=pyramid_open_unresolved blocker=pyramid_quality_blocked:ai_score_unavailable,tick_aggressor_pressure_unusable,tick_accel_stale,micro_context_stale profit=2.62 final=None ai=61.0 tick=0.333 micro_vwap=-48.92
- record_id=15635 code=399720 name=가온칩스 label=pyramid_correctly_blocked blocker=rising_missed_scout_pyramid_bridge_blocked:profit_not_enough,quote_stale,micro_context_stale,tick_aggressor_pressure_unusable,fresh_micro_confirmation_missing,tick_accel_stale profit=0.18 final=0.28 ai=63.0 tick=0.15 micro_vwap=-7.52
- record_id=15780 code=123420 name=위메이드플레이 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.25 final=None ai=50.0 tick=0.003 micro_vwap=0.0

## One Share Opportunity Rows

- record_id=15633 code=004980 name=성신양회 label=pyramid_correctly_blocked opportunity_seen=False opportunity_profit=None max_profit=-0.02 opportunity_cost=0.0 final=-5.3
- record_id=15634 code=037710 name=광주신세계 label=pyramid_correctly_blocked opportunity_seen=False opportunity_profit=None max_profit=0.56 opportunity_cost=0.56 final=-5.16
- record_id=15644 code=095500 name=미래나노텍 label=pyramid_would_have_helped opportunity_seen=True opportunity_profit=2.61 max_profit=2.61 opportunity_cost=0.0 final=1.07
- record_id=15639 code=094360 name=칩스앤미디어 label=pyramid_correctly_blocked opportunity_seen=False opportunity_profit=None max_profit=1.11 opportunity_cost=1.11 final=0.13
- record_id=15637 code=114190 name=강원에너지 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=15656 code=095500 name=미래나노텍 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=15654 code=101730 name=위메이드맥스 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=15642 code=086520 name=에코프로 label=pyramid_correctly_blocked opportunity_seen=False opportunity_profit=None max_profit=0.82 opportunity_cost=0.82 final=0.82
- record_id=15647 code=399720 name=가온칩스 label=pyramid_would_have_helped opportunity_seen=True opportunity_profit=1.81 max_profit=4.71 opportunity_cost=2.9 final=3.31
- record_id=15662 code=002990 name=금호건설 label=pyramid_would_have_helped opportunity_seen=True opportunity_profit=1.58 max_profit=4.22 opportunity_cost=2.64 final=3.53
- record_id=15692 code=002990 name=금호건설 label=pyramid_would_have_helped opportunity_seen=True opportunity_profit=2.76 max_profit=2.76 opportunity_cost=0.0 final=1.93
- record_id=15699 code=002990 name=금호건설 label=pyramid_correctly_blocked opportunity_seen=False opportunity_profit=None max_profit=1.2 opportunity_cost=1.2 final=-6.8
- record_id=15724 code=005720 name=넥센 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=0.1 opportunity_cost=0.1 final=None
- record_id=15704 code=365660 name=레몬헬스케어 label=pyramid_open_unresolved opportunity_seen=True opportunity_profit=2.18 max_profit=10.98 opportunity_cost=8.8 final=None
- record_id=15665 code=153890 name=져스텍 label=pyramid_would_have_helped opportunity_seen=True opportunity_profit=4.32 max_profit=4.32 opportunity_cost=0.0 final=3.27
- record_id=15730 code=365660 name=레몬헬스케어 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=15737 code=153890 name=져스텍 label=pyramid_correctly_blocked opportunity_seen=False opportunity_profit=None max_profit=0.37 opportunity_cost=0.37 final=-7.98
- record_id=15718 code=399720 name=가온칩스 label=pyramid_would_have_helped opportunity_seen=True opportunity_profit=1.66 max_profit=1.77 opportunity_cost=0.11 final=1.35
- record_id=15757 code=475040 name=스트라드비젼 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=15640 code=200710 name=에이디테크놀로지 label=pyramid_overheat_or_reversal_risk opportunity_seen=True opportunity_profit=1.4 max_profit=1.4 opportunity_cost=0.0 final=0.91
- record_id=15780 code=123420 name=위메이드플레이 label=pyramid_open_unresolved opportunity_seen=True opportunity_profit=0.25 max_profit=0.74 opportunity_cost=0.49 final=None
- record_id=15771 code=282720 name=금양그린파워 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=15777 code=399720 name=가온칩스 label=pyramid_would_have_helped opportunity_seen=True opportunity_profit=0.08 max_profit=1.92 opportunity_cost=1.84 final=0.28
- record_id=15725 code=002990 name=금호건설 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=15703 code=066570 name=LG전자 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=15638 code=073240 name=금호타이어 label=pyramid_overheat_or_reversal_risk opportunity_seen=True opportunity_profit=0.88 max_profit=1.51 opportunity_cost=0.63 final=0.56
- record_id=15842 code=073240 name=금호타이어 label=pyramid_overheat_or_reversal_risk opportunity_seen=True opportunity_profit=1.64 max_profit=1.8 opportunity_cost=0.16 final=1.17
- record_id=15857 code=073240 name=금호타이어 label=pyramid_correctly_blocked opportunity_seen=True opportunity_profit=0.08 max_profit=0.4 opportunity_cost=0.32 final=0.4
- record_id=15878 code=073240 name=금호타이어 label=pyramid_open_unresolved opportunity_seen=True opportunity_profit=0.08 max_profit=0.4 opportunity_cost=0.32 final=None
- record_id=15814 code=439090 name=마녀공장 label=pyramid_correctly_blocked opportunity_seen=True opportunity_profit=0.09 max_profit=0.53 opportunity_cost=0.44 final=0.4
- record_id=15677 code=086520 name=에코프로 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=15761 code=237880 name=클리오 label=pyramid_open_unresolved opportunity_seen=True opportunity_profit=0.44 max_profit=0.44 opportunity_cost=0.0 final=None
- record_id=15658 code=094360 name=칩스앤미디어 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=15790 code=200710 name=에이디테크놀로지 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=15653 code=004980 name=성신양회 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=15635 code=399720 name=가온칩스 label=pyramid_correctly_blocked opportunity_seen=True opportunity_profit=0.18 max_profit=0.89 opportunity_cost=0.71 final=0.28
- record_id=15904 code=073240 name=금호타이어 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=15896 code=008930 name=한미사이언스 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
- record_id=15661 code=018260 name=삼성에스디에스 label=pyramid_open_unresolved opportunity_seen=False opportunity_profit=None max_profit=None opportunity_cost=0.0 final=None
