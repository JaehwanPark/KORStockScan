# 2026-06-19 Scalping Pyramid Intraday Feedback

- generated_at: 2026-07-03T13:24:07+09:00
- decision_authority: source_only_pyramid_intraday_feedback_no_runtime_mutation
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: intraday_threshold_mutation, intraday_runtime_apply, hard_safety_relaxation, broker_guard_bypass, order_guard_relaxation, stale_quote_bypass, cooldown_bypass, quantity_guard_relaxation, position_cap_release, provider_route_change, bot_restart, real_execution_quality_approval

## Summary

- pyramid_feedback_row_count: 39
- closed_pyramid_row_count: 1
- pyramid_would_have_helped_count: 1
- pyramid_correctly_blocked_count: 0
- pyramid_overheat_or_reversal_risk_count: 0
- pyramid_open_unresolved_count: 38
- one_share_event_count: 0
- one_share_closed_count: 0
- one_share_pyramid_opportunity_count: 0
- one_share_pyramid_missed_upside_count: 0
- one_share_pyramid_missed_upside_rate: 0.00
- one_share_pyramid_avg_opportunity_cost_pct: 0.00

## Blocker Metrics

- blocker=profit_not_enough sample=36 recovered_rate=0.03 reversal_rate=0.00 blocked_then_recovered_rate=0.03
- blocker=scalping_cutoff sample=1 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00
- blocker=trend_not_strong sample=2 recovered_rate=0.00 reversal_rate=0.00 blocked_then_recovered_rate=0.00

## Rows

- record_id=11677 code=089970 name=브이엠 label=pyramid_would_have_helped blocker=profit_not_enough profit=0.41 final=1.38 ai=72.0 tick=0.0 micro_vwap=-79.89
- record_id= code=311320 name=지오엘리먼트 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.27 final=None ai=54.0 tick=3.0 micro_vwap=-164.56
- record_id= code=462870 name=시프트업 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.88 final=None ai=70.0 tick=0.0 micro_vwap=-164.3
- record_id= code=003490 name=대한항공 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.28 final=None ai=72.0 tick=0.5 micro_vwap=-40.74
- record_id= code=383310 name=에코프로에이치엔 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.21 final=None ai=66.0 tick=2.5 micro_vwap=-108.85
- record_id= code=001440 name=대한전선 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.4 final=None ai=76.0 tick=3.0 micro_vwap=-42.8
- record_id= code=126340 name=비나텍 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.99 final=None ai=68.0 tick=0.0 micro_vwap=-21.63
- record_id= code=032830 name=삼성생명 label=pyramid_open_unresolved blocker=trend_not_strong profit=2.48 final=None ai=72.0 tick=0.6 micro_vwap=-34.88
- record_id= code=011790 name=SKC label=pyramid_open_unresolved blocker=profit_not_enough profit=0.17 final=None ai=74.0 tick=1.0 micro_vwap=-31.03
- record_id= code=001740 name=SK네트웍스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.32 final=None ai=74.0 tick=1.5 micro_vwap=-29.0
- record_id= code=006400 name=삼성SDI label=pyramid_open_unresolved blocker=profit_not_enough profit=1.39 final=None ai=73.0 tick=1.0 micro_vwap=-17.52
- record_id= code=000150 name=KoAct 미국나스닥성장기업액티브 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.42 final=None ai=74.0 tick=1.667 micro_vwap=-3.13
- record_id= code=141080 name=리가켐바이오 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.56 final=None ai=71.0 tick=2.0 micro_vwap=-8.66
- record_id= code=034220 name=LG디스플레이 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.28 final=None ai=74.0 tick=1.0 micro_vwap=22.56
- record_id= code=066970 name=엘앤에프 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.38 final=None ai=72.0 tick=2.0 micro_vwap=-33.6
- record_id= code=466930 name=SOL 자동차TOP3플러스 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.41 final=None ai=71.0 tick=0.364 micro_vwap=-34.13
- record_id= code=009150 name=삼성전기 label=pyramid_open_unresolved blocker=trend_not_strong profit=2.84 final=None ai=74.0 tick=0.0 micro_vwap=22.89
- record_id= code=095340 name=ISC label=pyramid_open_unresolved blocker=profit_not_enough profit=0.19 final=None ai=68.0 tick=10.333 micro_vwap=-11.99
- record_id= code=010120 name=LS ELECTRIC label=pyramid_open_unresolved blocker=profit_not_enough profit=0.51 final=None ai=75.0 tick=1.0 micro_vwap=-30.59
- record_id= code=417200 name=LS머트리얼즈 label=pyramid_open_unresolved blocker=profit_not_enough profit=-0.0 final=None ai=74.0 tick=5.0 micro_vwap=15.0
- record_id= code=005380 name=현대차 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.26 final=None ai=74.0 tick=0.333 micro_vwap=3.55
- record_id= code=149950 name=아바텍 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.28 final=None ai=73.0 tick=9.0 micro_vwap=-15.24
- record_id= code=091590 name=남화토건 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.29 final=None ai=68.0 tick=0.211 micro_vwap=76.45
- record_id= code=042940 name=상지건설 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.83 final=None ai=68.0 tick=0.473 micro_vwap=32.83
- record_id= code=034730 name=SK label=pyramid_open_unresolved blocker=profit_not_enough profit=0.04 final=None ai=69.0 tick=0.0 micro_vwap=22.67
- record_id= code=000990 name=DB하이텍 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.48 final=None ai=72.0 tick=1.0 micro_vwap=14.9
- record_id= code=148020 name=RISE 200 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.19 final=None ai=68.0 tick=0.0 micro_vwap=-30.66
- record_id= code=483320 name=ACE 엔비디아밸류체인액티브 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.08 final=None ai=74.0 tick=1.087 micro_vwap=-0.31
- record_id= code=031330 name=에스에이엠티 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.62 final=None ai=62.0 tick=0.0 micro_vwap=-999.0
- record_id= code=495060 name=TIME 코리아밸류업액티브 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.02 final=None ai=66.0 tick=0.1 micro_vwap=7.0
- record_id= code=330350 name=위더스제약 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.25 final=None ai=68.0 tick=0.0 micro_vwap=-146.06
- record_id= code=347850 name=디앤디파마텍 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.59 final=None ai=76.0 tick=1.0 micro_vwap=6.83
- record_id= code=276730 name=한울앤제주 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.86 final=None ai=60.0 tick=0.559 micro_vwap=-5.61
- record_id= code=442580 name=PLUS 글로벌HBM반도체 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.06 final=None ai=67.0 tick=0.5 micro_vwap=-1.39
- record_id= code=426030 name=TIME 미국나스닥100액티브 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.07 final=None ai=62.0 tick=0.0 micro_vwap=-999.0
- record_id= code=010690 name=화신 label=pyramid_open_unresolved blocker=profit_not_enough profit=1.02 final=None ai=62.0 tick=0.0 micro_vwap=-47.76
- record_id= code=402340 name=SK스퀘어 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.06 final=None ai=68.0 tick=0.0 micro_vwap=9.7
- record_id= code=000660 name=SK하이닉스 label=pyramid_open_unresolved blocker=profit_not_enough profit=0.14 final=None ai=61.0 tick=0.0 micro_vwap=-999.0
- record_id= code=082740 name=한화엔진 label=pyramid_open_unresolved blocker=scalping_cutoff profit=0.77 final=None ai=73.0 tick=2.0 micro_vwap=2.34

## One Share Opportunity Rows
