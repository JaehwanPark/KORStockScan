# Scalp Sim EV Midcheck 2026-05-19

- generated_at: `2026-05-19T16:03:56`
- latest_event_at: `2026-05-19T16:03:56.227030`
- source: `/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-05-19.jsonl`
- judgement: `non_positive_or_no_sample`
- runtime_mutation: `false`
- synthetic_excluded: `0`

## Summary

- completed: `100`
- sum_profit_pct: `-22.60%`
- avg_profit_pct: `-0.23%`
- median_profit_pct: `+0.05%`
- win_rate_pct: `50.0%`
- gross_win_pct: `+71.85%`
- gross_loss_pct: `-94.45%`

## Sim Stage Counts

- ai_live_call: `1753`
- ai_reuse: `0`
- ai_deferred: `35`
- ai_budget_exhausted: `35`
- ai_critical_bypass: `1729`
- ai_critical_bypass_ratio_pct: `98.63`
- ai_deferred_ratio_pct: `1.96`
- ai_reuse_ratio_pct: `0.0`

## Overnight

- decision: `13`
- sell_today: `13`
- hold_overnight: `0`
- sell_assumed_filled: `13`
- carry_open_count: `0`
- decision_authority: `sim_observation_only`
- runtime_effect: `false`

## AI Budget Critical Classes

- `unknown`: `1788`

## AI Budget Critical Reasons

- `unknown`: `1788`

- `scalp_sim_ai_holding_deferred`: `35`
- `scalp_sim_ai_holding_live_call`: `1753`
- `scalp_sim_buy_order_assumed_filled`: `100`
- `scalp_sim_buy_order_virtual_pending`: `100`
- `scalp_sim_candidate_window_discarded`: `469`
- `scalp_sim_duplicate_buy_signal`: `768`
- `scalp_sim_entry_ai_price_applied`: `7`
- `scalp_sim_entry_ai_price_skip_order`: `4`
- `scalp_sim_entry_armed`: `100`
- `scalp_sim_entry_submit_revalidation_warning`: `92`
- `scalp_sim_holding_started`: `100`
- `scalp_sim_overnight_decision`: `13`
- `scalp_sim_overnight_sell_today`: `13`
- `scalp_sim_scale_in_order_unfilled`: `8`
- `scalp_sim_sell_order_assumed_filled`: `100`
- `sim_ai_budget_exhausted`: `35`
- `sim_ai_critical_bypass`: `1729`

## Arm Split

| arm | completed | avg | median | win_rate | sum |
| --- | ---: | ---: | ---: | ---: | ---: |
| `avg_down` | 0 | - | - | -% | +0.00% |
| `exit_only` | 100 | -0.23% | +0.05% | 50.0% | -22.60% |
| `mixed_scale_in` | 0 | - | - | -% | +0.00% |
| `pyramid` | 0 | - | - | -% | +0.00% |

## Scale-In Summary

- positions_completed: `100`
- positions_with_scale_in: `0`
- positions_without_scale_in: `100`
- filled_events: `0`
- unfilled_events: `8`
- completed_filled_events: `0`
- completed_unfilled_events: `8`
- filled_by_add_type: `{}`
- unfilled_by_add_type: `{'PYRAMID': 8}`
- actual_order_submitted_false_only: `true`
- actual_order_checked_values: `637`

## Scale-In Position Outcomes

| 종목 | arm | add filled/unfilled | post-add MFE | post-add MAE | final exit | actual_order |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| 제너셈(217190) | `exit_only` | 0/0 | - | - | - | False |
| 제너셈(217190) | `exit_only` | 0/0 | - | - | - | False |
| 네이처셀(007390) | `exit_only` | 0/0 | - | - | - | False |
| 엘앤케이바이오(156100) | `exit_only` | 0/0 | - | - | - | False |
| 에스엠(041510) | `exit_only` | 0/0 | - | - | - | False |
| 피델릭스(032580) | `exit_only` | 0/0 | - | - | - | False |
| 수젠텍(253840) | `exit_only` | 0/0 | - | - | - | False |
| 바이오니아(064550) | `exit_only` | 0/0 | - | - | - | False |
| 이수화학(005950) | `exit_only` | 0/0 | - | - | - | False |
| 안국약품(001540) | `exit_only` | 0/0 | - | - | - | False |
| 한화손해보험(000370) | `exit_only` | 0/0 | - | - | - | False |
| 엠케이전자(033160) | `exit_only` | 0/0 | - | - | - | False |
| 제주반도체(080220) | `exit_only` | 0/0 | - | - | - | False |
| 파두(440110) | `exit_only` | 0/3 | - | - | - | False |
| 두산에너빌리티(034020) | `exit_only` | 0/0 | - | - | - | False |
| 삼성전자(005930) | `exit_only` | 0/0 | - | - | - | False |
| 주성엔지니어링(036930) | `exit_only` | 0/0 | - | - | - | False |
| 엑스게이트(356680) | `exit_only` | 0/0 | - | - | - | False |
| 태성(323280) | `exit_only` | 0/0 | - | - | - | False |
| LIG디펜스앤에어로스페이스(079550) | `exit_only` | 0/0 | - | - | - | False |
| SK하이닉스(000660) | `exit_only` | 0/0 | - | - | - | False |
| 원익IPS(240810) | `exit_only` | 0/0 | - | - | - | False |
| 가온그룹(078890) | `exit_only` | 0/0 | - | - | - | False |
| 휴온스(243070) | `exit_only` | 0/0 | - | - | - | False |
| 두산로보틱스(454910) | `exit_only` | 0/0 | - | - | - | False |
| 녹십자엠에스(142280) | `exit_only` | 0/0 | - | - | - | False |
| LG이노텍(011070) | `exit_only` | 0/0 | - | - | - | False |
| 콘텐트리중앙(036420) | `exit_only` | 0/1 | - | - | - | False |
| 에프엔에스테크(083500) | `exit_only` | 0/0 | - | - | - | False |
| 코스맥스엔비티(222040) | `exit_only` | 0/0 | - | - | - | False |
| 한컴위드(054920) | `exit_only` | 0/0 | - | - | - | False |
| LG전자(066570) | `exit_only` | 0/0 | - | - | - | False |
| 태성(323280) | `exit_only` | 0/0 | - | - | - | False |
| 한화에어로스페이스(012450) | `exit_only` | 0/0 | - | - | - | False |
| 마녀공장(439090) | `exit_only` | 0/0 | - | - | - | False |
| 현대차(005380) | `exit_only` | 0/0 | - | - | - | False |
| 주성엔지니어링(036930) | `exit_only` | 0/2 | - | - | - | False |
| 아주IB투자(027360) | `exit_only` | 0/1 | - | - | - | False |
| 삼성전자(005930) | `exit_only` | 0/0 | - | - | - | False |
| 폴라리스AI파마(041910) | `exit_only` | 0/0 | - | - | - | False |
| 삼아알미늄(006110) | `exit_only` | 0/0 | - | - | - | False |
| 바이오니아(064550) | `exit_only` | 0/0 | - | - | - | False |
| 피델릭스(032580) | `exit_only` | 0/0 | - | - | - | False |
| 메가터치(446540) | `exit_only` | 0/0 | - | - | - | False |
| 한솔테크닉스(004710) | `exit_only` | 0/0 | - | - | - | False |
| 콘텐트리중앙(036420) | `exit_only` | 0/0 | - | - | - | False |
| 한화손해보험(000370) | `exit_only` | 0/0 | - | - | - | False |
| 한선엔지니어링(452280) | `exit_only` | 0/0 | - | - | - | False |
| 엘앤씨바이오(290650) | `exit_only` | 0/0 | - | - | - | False |
| 앤씨앤(092600) | `exit_only` | 0/0 | - | - | - | False |
| 앤씨앤(092600) | `exit_only` | 0/0 | - | - | - | False |
| 앤씨앤(092600) | `exit_only` | 0/0 | - | - | - | False |
| 지니언스(263860) | `exit_only` | 0/0 | - | - | - | False |
| 소룩스(290690) | `exit_only` | 0/0 | - | - | - | False |
| 엘티씨(170920) | `exit_only` | 0/0 | - | - | - | False |
| LG전자(066570) | `exit_only` | 0/0 | - | - | - | False |
| 앤씨앤(092600) | `exit_only` | 0/0 | - | - | - | False |
| 한선엔지니어링(452280) | `exit_only` | 0/0 | - | - | - | False |
| 에이플러스에셋(244920) | `exit_only` | 0/0 | - | - | - | False |
| 콘텐트리중앙(036420) | `exit_only` | 0/0 | - | - | - | False |
| 바이오니아(064550) | `exit_only` | 0/0 | - | - | - | False |
| 노바렉스(194700) | `exit_only` | 0/0 | - | - | - | False |
| 코스맥스엔비티(222040) | `exit_only` | 0/0 | - | - | - | False |
| 소룩스(290690) | `exit_only` | 0/0 | - | - | - | False |
| 엠케이전자(033160) | `exit_only` | 0/0 | - | - | - | False |
| 소룩스(290690) | `exit_only` | 0/0 | - | - | - | False |
| 한선엔지니어링(452280) | `exit_only` | 0/0 | - | - | - | False |
| 바이오니아(064550) | `exit_only` | 0/0 | - | - | - | False |
| 휴온스(243070) | `exit_only` | 0/0 | - | - | - | False |
| 이연제약(102460) | `exit_only` | 0/0 | - | - | - | False |
| 소룩스(290690) | `exit_only` | 0/0 | - | - | - | False |
| 한선엔지니어링(452280) | `exit_only` | 0/0 | - | - | - | False |
| 이수화학(005950) | `exit_only` | 0/0 | - | - | - | False |
| 제주반도체(080220) | `exit_only` | 0/0 | - | - | - | False |
| 엘티씨(170920) | `exit_only` | 0/0 | - | - | - | False |
| 엘앤씨바이오(290650) | `exit_only` | 0/0 | - | - | - | False |
| 태성(323280) | `exit_only` | 0/0 | - | - | - | False |
| 큐라클(365270) | `exit_only` | 0/0 | - | - | - | False |
| 알테오젠(196170) | `exit_only` | 0/0 | - | - | - | False |
| 엠케이전자(033160) | `exit_only` | 0/0 | - | - | - | False |
| 큐라클(365270) | `exit_only` | 0/0 | - | - | - | False |
| 피엠티(147760) | `exit_only` | 0/0 | - | - | - | False |
| 에이플러스에셋(244920) | `exit_only` | 0/1 | - | - | - | False |
| 두산로보틱스(454910) | `exit_only` | 0/0 | - | - | - | False |
| 엑스게이트(356680) | `exit_only` | 0/0 | - | - | - | False |
| 오킨스전자(080580) | `exit_only` | 0/0 | - | - | - | False |
| 큐라클(365270) | `exit_only` | 0/0 | - | - | - | False |
| 이수화학(005950) | `exit_only` | 0/0 | - | - | - | False |
| 주성엔지니어링(036930) | `exit_only` | 0/0 | - | - | - | False |
| 엠케이전자(033160) | `exit_only` | 0/0 | - | - | - | False |
| 엑스게이트(356680) | `exit_only` | 0/0 | - | - | - | False |
| 켄코아에어로스페이스(274090) | `exit_only` | 0/0 | - | - | - | False |
| 메가터치(446540) | `exit_only` | 0/0 | - | - | - | False |
| 폴라리스AI(039980) | `exit_only` | 0/0 | - | - | - | False |
| LG전자(066570) | `exit_only` | 0/0 | - | - | - | False |
| SK하이닉스(000660) | `exit_only` | 0/0 | - | - | - | False |
| 삼성전자(005930) | `exit_only` | 0/0 | - | - | - | False |
| 동성화인텍(033500) | `exit_only` | 0/0 | - | - | - | False |
| 제이에스링크(127120) | `exit_only` | 0/0 | - | - | - | False |
| 파두(440110) | `exit_only` | 0/0 | - | - | - | False |

## Initial Qty Provenance

- method: `actual_sim_qty_provenance_only`
- sample: `100`
- qty_sum: `9437`
- uncapped_qty_sum: `9437`
- cap_applied_count: `0`
- uncapped_qty_source_count: `0`
- virtual_budget_qty_source_count: `100`
- fixed_qty_source_count: `0`

| 종목 | sim_qty | uncapped_qty | qty_source | cap_applied | final exit |
| --- | ---: | ---: | --- | --- | ---: |
| 태성(323280) | 13 | 13 | `sim_virtual_budget_dynamic_formula` | false | +5.62% |
| 앤씨앤(092600) | 600 | 600 | `sim_virtual_budget_dynamic_formula` | false | +3.93% |
| 엑스게이트(356680) | 51 | 51 | `sim_virtual_budget_dynamic_formula` | false | +3.73% |
| 한컴위드(054920) | 150 | 150 | `sim_virtual_budget_dynamic_formula` | false | +3.58% |
| 소룩스(290690) | 155 | 155 | `sim_virtual_budget_dynamic_formula` | false | +3.34% |
| 피델릭스(032580) | 197 | 197 | `sim_virtual_budget_dynamic_formula` | false | +3.20% |
| 안국약품(001540) | 84 | 84 | `sim_virtual_budget_dynamic_formula` | false | +2.62% |
| 엘티씨(170920) | 22 | 22 | `sim_virtual_budget_dynamic_formula` | false | +2.53% |
| 피엠티(147760) | 134 | 134 | `sim_virtual_budget_dynamic_formula` | false | +2.31% |
| 주성엔지니어링(036930) | 5 | 5 | `sim_virtual_budget_dynamic_formula` | false | +1.97% |
| 엠케이전자(033160) | 30 | 30 | `sim_virtual_budget_dynamic_formula` | false | +1.97% |
| 엠케이전자(033160) | 30 | 30 | `sim_virtual_budget_dynamic_formula` | false | +1.87% |
| 주성엔지니어링(036930) | 5 | 5 | `sim_virtual_budget_dynamic_formula` | false | +1.78% |
| 앤씨앤(092600) | 600 | 600 | `sim_virtual_budget_dynamic_formula` | false | +1.77% |
| 파두(440110) | 8 | 8 | `sim_virtual_budget_dynamic_formula` | false | +1.56% |
| 엠케이전자(033160) | 31 | 31 | `sim_virtual_budget_dynamic_formula` | false | +1.44% |
| 한선엔지니어링(452280) | 28 | 28 | `sim_virtual_budget_dynamic_formula` | false | +1.41% |
| 콘텐트리중앙(036420) | 167 | 167 | `sim_virtual_budget_dynamic_formula` | false | +1.35% |
| 오킨스전자(080580) | 47 | 47 | `sim_virtual_budget_dynamic_formula` | false | +1.33% |
| 바이오니아(064550) | 91 | 91 | `sim_virtual_budget_dynamic_formula` | false | +1.31% |
| 엘티씨(170920) | 23 | 23 | `sim_virtual_budget_dynamic_formula` | false | +1.25% |
| 엠케이전자(033160) | 31 | 31 | `sim_virtual_budget_dynamic_formula` | false | +1.25% |
| 에이플러스에셋(244920) | 82 | 82 | `sim_virtual_budget_dynamic_formula` | false | +1.24% |
| 마녀공장(439090) | 56 | 56 | `sim_virtual_budget_dynamic_formula` | false | +1.20% |
| 엘앤씨바이오(290650) | 15 | 15 | `sim_virtual_budget_dynamic_formula` | false | +1.20% |
| 이수화학(005950) | 81 | 81 | `sim_virtual_budget_dynamic_formula` | false | +1.06% |
| 엑스게이트(356680) | 52 | 52 | `sim_virtual_budget_dynamic_formula` | false | +1.04% |
| 이수화학(005950) | 84 | 84 | `sim_virtual_budget_dynamic_formula` | false | +0.92% |
| 엑스게이트(356680) | 53 | 53 | `sim_virtual_budget_dynamic_formula` | false | +0.90% |
| 이수화학(005950) | 83 | 83 | `sim_virtual_budget_dynamic_formula` | false | +0.90% |
| 아주IB투자(027360) | 54 | 54 | `sim_virtual_budget_dynamic_formula` | false | +0.86% |
| 켄코아에어로스페이스(274090) | 34 | 34 | `sim_virtual_budget_dynamic_formula` | false | +0.85% |
| LG전자(066570) | 5 | 5 | `sim_virtual_budget_dynamic_formula` | false | +0.83% |
| 코스맥스엔비티(222040) | 110 | 110 | `sim_virtual_budget_dynamic_formula` | false | +0.82% |
| 주성엔지니어링(036930) | 5 | 5 | `sim_virtual_budget_dynamic_formula` | false | +0.80% |
| 지니언스(263860) | 60 | 60 | `sim_virtual_budget_dynamic_formula` | false | +0.78% |
| 소룩스(290690) | 157 | 157 | `sim_virtual_budget_dynamic_formula` | false | +0.76% |
| 바이오니아(064550) | 93 | 93 | `sim_virtual_budget_dynamic_formula` | false | +0.75% |
| 한선엔지니어링(452280) | 28 | 28 | `sim_virtual_budget_dynamic_formula` | false | +0.66% |
| LG전자(066570) | 4 | 4 | `sim_virtual_budget_dynamic_formula` | false | +0.66% |
| 제주반도체(080220) | 9 | 9 | `sim_virtual_budget_dynamic_formula` | false | +0.61% |
| 노바렉스(194700) | 52 | 52 | `sim_virtual_budget_dynamic_formula` | false | +0.60% |
| 이연제약(102460) | 78 | 78 | `sim_virtual_budget_dynamic_formula` | false | +0.60% |
| 알테오젠(196170) | 2 | 2 | `sim_virtual_budget_dynamic_formula` | false | +0.59% |
| 한선엔지니어링(452280) | 30 | 30 | `sim_virtual_budget_dynamic_formula` | false | +0.57% |
| 삼성전자(005930) | 3 | 3 | `sim_virtual_budget_dynamic_formula` | false | +0.50% |
| 엘앤씨바이오(290650) | 14 | 14 | `sim_virtual_budget_dynamic_formula` | false | +0.39% |
| 콘텐트리중앙(036420) | 167 | 167 | `sim_virtual_budget_dynamic_formula` | false | +0.30% |
| 동성화인텍(033500) | 41 | 41 | `sim_virtual_budget_dynamic_formula` | false | +0.21% |
| 폴라리스AI(039980) | 115 | 115 | `sim_virtual_budget_dynamic_formula` | false | +0.13% |
| 두산로보틱스(454910) | 9 | 9 | `sim_virtual_budget_dynamic_formula` | false | -0.03% |
| 두산에너빌리티(034020) | 8 | 8 | `sim_virtual_budget_dynamic_formula` | false | -0.32% |
| 메가터치(446540) | 337 | 337 | `sim_virtual_budget_dynamic_formula` | false | -0.47% |
| 휴온스(243070) | 24 | 24 | `sim_virtual_budget_dynamic_formula` | false | -0.62% |
| 삼성전자(005930) | 3 | 3 | `sim_virtual_budget_dynamic_formula` | false | -0.77% |
| SK하이닉스(000660) | 1 | 1 | `sim_virtual_budget_dynamic_formula` | false | -1.25% |
| 제이에스링크(127120) | 26 | 26 | `sim_virtual_budget_dynamic_formula` | false | -1.33% |
| 파두(440110) | 8 | 8 | `sim_virtual_budget_dynamic_formula` | false | -1.34% |
| 콘텐트리중앙(036420) | 165 | 165 | `sim_virtual_budget_dynamic_formula` | false | -1.62% |
| SK하이닉스(000660) | 1 | 1 | `sim_virtual_budget_dynamic_formula` | false | -1.63% |
| 폴라리스AI파마(041910) | 133 | 133 | `sim_virtual_budget_dynamic_formula` | false | -1.63% |
| 휴온스(243070) | 24 | 24 | `sim_virtual_budget_dynamic_formula` | false | -1.65% |
| 에프엔에스테크(083500) | 45 | 45 | `sim_virtual_budget_dynamic_formula` | false | -1.66% |
| 메가터치(446540) | 117 | 117 | `sim_virtual_budget_dynamic_formula` | false | -1.70% |
| 큐라클(365270) | 69 | 69 | `sim_virtual_budget_dynamic_formula` | false | -1.70% |
| 현대차(005380) | 1 | 1 | `sim_virtual_budget_dynamic_formula` | false | -1.71% |
| 큐라클(365270) | 70 | 70 | `sim_virtual_budget_dynamic_formula` | false | -1.71% |
| LG이노텍(011070) | 1 | 1 | `sim_virtual_budget_dynamic_formula` | false | -1.73% |
| 코스맥스엔비티(222040) | 111 | 111 | `sim_virtual_budget_dynamic_formula` | false | -1.74% |
| LG전자(066570) | 4 | 4 | `sim_virtual_budget_dynamic_formula` | false | -1.74% |
| 한화손해보험(000370) | 121 | 121 | `sim_virtual_budget_dynamic_formula` | false | -1.76% |
| 에스엠(041510) | 31 | 31 | `sim_virtual_budget_dynamic_formula` | false | -1.77% |
| 한화에어로스페이스(012450) | 1 | 1 | `sim_virtual_budget_dynamic_formula` | false | -1.77% |
| 에이플러스에셋(244920) | 81 | 81 | `sim_virtual_budget_dynamic_formula` | false | -1.77% |
| 한화손해보험(000370) | 123 | 123 | `sim_virtual_budget_dynamic_formula` | false | -1.78% |
| 큐라클(365270) | 70 | 70 | `sim_virtual_budget_dynamic_formula` | false | -1.79% |
| 두산로보틱스(454910) | 9 | 9 | `sim_virtual_budget_dynamic_formula` | false | -1.80% |
| 원익IPS(240810) | 8 | 8 | `sim_virtual_budget_dynamic_formula` | false | -1.82% |
| 네이처셀(007390) | 153 | 153 | `sim_virtual_budget_dynamic_formula` | false | -1.84% |
| 삼성전자(005930) | 3 | 3 | `sim_virtual_budget_dynamic_formula` | false | -1.86% |
| 삼아알미늄(006110) | 10 | 10 | `sim_virtual_budget_dynamic_formula` | false | -1.86% |
| 한솔테크닉스(004710) | 66 | 66 | `sim_virtual_budget_dynamic_formula` | false | -1.97% |
| 소룩스(290690) | 152 | 152 | `sim_virtual_budget_dynamic_formula` | false | -1.99% |
| 가온그룹(078890) | 99 | 99 | `sim_virtual_budget_dynamic_formula` | false | -2.00% |
| 소룩스(290690) | 154 | 154 | `sim_virtual_budget_dynamic_formula` | false | -2.02% |
| LIG디펜스앤에어로스페이스(079550) | 1 | 1 | `sim_virtual_budget_dynamic_formula` | false | -2.06% |
| 엘앤케이바이오(156100) | 442 | 442 | `sim_virtual_budget_dynamic_formula` | false | -2.09% |
| 제주반도체(080220) | 10 | 10 | `sim_virtual_budget_dynamic_formula` | false | -2.12% |
| 제너셈(217190) | 395 | 395 | `sim_virtual_budget_dynamic_formula` | false | -2.30% |
| 앤씨앤(092600) | 572 | 572 | `sim_virtual_budget_dynamic_formula` | false | -2.33% |
| 수젠텍(253840) | 137 | 137 | `sim_virtual_budget_dynamic_formula` | false | -2.53% |
| 녹십자엠에스(142280) | 190 | 190 | `sim_virtual_budget_dynamic_formula` | false | -2.53% |
| 바이오니아(064550) | 90 | 90 | `sim_virtual_budget_dynamic_formula` | false | -2.60% |
| 태성(323280) | 13 | 13 | `sim_virtual_budget_dynamic_formula` | false | -2.62% |
| 태성(323280) | 13 | 13 | `sim_virtual_budget_dynamic_formula` | false | -2.75% |
| 한선엔지니어링(452280) | 27 | 27 | `sim_virtual_budget_dynamic_formula` | false | -2.79% |
| 제너셈(217190) | 387 | 387 | `sim_virtual_budget_dynamic_formula` | false | -2.80% |
| 바이오니아(064550) | 90 | 90 | `sim_virtual_budget_dynamic_formula` | false | -2.88% |
| 앤씨앤(092600) | 580 | 580 | `sim_virtual_budget_dynamic_formula` | false | -3.28% |
| 피델릭스(032580) | 183 | 183 | `sim_virtual_budget_dynamic_formula` | false | -4.62% |

## Completed Rows

| 종목 | 수익률 | exit_rule | source |
| --- | ---: | --- | --- |
| 태성(323280) | +5.62% | scalp_trailing_take_profit | HOLDING_FLOW_OVERRIDE |
| 앤씨앤(092600) | +3.93% | scalp_trailing_take_profit | HOLDING_FLOW_OVERRIDE |
| 엑스게이트(356680) | +3.73% | scalp_trailing_take_profit | HOLDING_FLOW_OVERRIDE |
| 한컴위드(054920) | +3.58% | scalp_trailing_take_profit | HOLDING_FLOW_OVERRIDE |
| 소룩스(290690) | +3.34% | scalp_trailing_take_profit | HOLDING_FLOW_OVERRIDE |
| 피델릭스(032580) | +3.20% | scalp_trailing_take_profit | HOLDING_FLOW_OVERRIDE |
| 안국약품(001540) | +2.62% | scalp_trailing_take_profit | HOLDING_FLOW_OVERRIDE |
| 엘티씨(170920) | +2.53% | scalp_trailing_take_profit | HOLDING_FLOW_OVERRIDE |
| 피엠티(147760) | +2.31% | scalp_trailing_take_profit | HOLDING_FLOW_OVERRIDE |
| 주성엔지니어링(036930) | +1.97% | scalp_trailing_take_profit | HOLDING_FLOW_OVERRIDE |
| 엠케이전자(033160) | +1.97% | scalp_trailing_take_profit | HOLDING_FLOW_OVERRIDE |
| 엠케이전자(033160) | +1.87% | scalp_trailing_take_profit | HOLDING_FLOW_OVERRIDE |
| 주성엔지니어링(036930) | +1.78% | scalp_trailing_take_profit | HOLDING_FLOW_OVERRIDE |
| 앤씨앤(092600) | +1.77% | scalp_trailing_take_profit | HOLDING_FLOW_OVERRIDE |
| 파두(440110) | +1.56% | scalp_trailing_take_profit | HOLDING_FLOW_OVERRIDE |
| 엠케이전자(033160) | +1.44% | scalp_trailing_take_profit | HOLDING_FLOW_OVERRIDE |
| 한선엔지니어링(452280) | +1.41% | scalp_trailing_take_profit | HOLDING_FLOW_OVERRIDE |
| 콘텐트리중앙(036420) | +1.35% | scalp_trailing_take_profit | HOLDING_FLOW_OVERRIDE |
| 오킨스전자(080580) | +1.33% | scalp_trailing_take_profit | HOLDING_FLOW_OVERRIDE |
| 바이오니아(064550) | +1.31% | scalp_trailing_take_profit | HOLDING_FLOW_OVERRIDE |
| 엘티씨(170920) | +1.25% | scalp_trailing_take_profit | HOLDING_FLOW_OVERRIDE |
| 엠케이전자(033160) | +1.25% | scalp_trailing_take_profit | HOLDING_FLOW_OVERRIDE |
| 에이플러스에셋(244920) | +1.24% | scalp_trailing_take_profit | HOLDING_FLOW_OVERRIDE |
| 엘앤씨바이오(290650) | +1.20% | scalp_trailing_take_profit | HOLDING_FLOW_OVERRIDE |
| 마녀공장(439090) | +1.20% | scalp_trailing_take_profit | HOLDING_FLOW_OVERRIDE |
| 이수화학(005950) | +1.06% | scalp_trailing_take_profit | HOLDING_FLOW_OVERRIDE |
| 엑스게이트(356680) | +1.04% | scalp_trailing_take_profit | HOLDING_FLOW_OVERRIDE |
| 이수화학(005950) | +0.92% | scalp_trailing_take_profit | HOLDING_FLOW_OVERRIDE |
| 엑스게이트(356680) | +0.90% | scalp_trailing_take_profit | HOLDING_FLOW_OVERRIDE |
| 이수화학(005950) | +0.90% | scalp_trailing_take_profit | HOLDING_FLOW_OVERRIDE |
| 아주IB투자(027360) | +0.86% | scalp_trailing_take_profit | HOLDING_FLOW_OVERRIDE |
| 켄코아에어로스페이스(274090) | +0.85% | scalp_trailing_take_profit | HOLDING_FLOW_OVERRIDE |
| LG전자(066570) | +0.83% | scalp_trailing_take_profit | HOLDING_FLOW_OVERRIDE |
| 코스맥스엔비티(222040) | +0.82% | scalp_sim_overnight_sell_today | overnight_v1 |
| 주성엔지니어링(036930) | +0.80% | scalp_trailing_take_profit | HOLDING_FLOW_OVERRIDE |
| 지니언스(263860) | +0.78% | scalp_sim_overnight_sell_today | overnight_v1 |
| 소룩스(290690) | +0.76% | scalp_trailing_take_profit | HOLDING_FLOW_OVERRIDE |
| 바이오니아(064550) | +0.75% | scalp_trailing_take_profit | HOLDING_FLOW_OVERRIDE |
| 한선엔지니어링(452280) | +0.66% | scalp_trailing_take_profit | HOLDING_FLOW_OVERRIDE |
| LG전자(066570) | +0.66% | scalp_sim_overnight_sell_today | overnight_v1 |
| 제주반도체(080220) | +0.61% | scalp_trailing_take_profit | HOLDING_FLOW_OVERRIDE |
| 이연제약(102460) | +0.60% | scalp_trailing_take_profit | HOLDING_FLOW_OVERRIDE |
| 노바렉스(194700) | +0.60% | scalp_trailing_take_profit | HOLDING_FLOW_OVERRIDE |
| 알테오젠(196170) | +0.59% | scalp_trailing_take_profit | HOLDING_FLOW_OVERRIDE |
| 한선엔지니어링(452280) | +0.57% | scalp_trailing_take_profit | HOLDING_FLOW_OVERRIDE |
| 삼성전자(005930) | +0.50% | scalp_trailing_take_profit | HOLDING_FLOW_OVERRIDE |
| 엘앤씨바이오(290650) | +0.39% | scalp_trailing_take_profit | HOLDING_FLOW_OVERRIDE |
| 콘텐트리중앙(036420) | +0.30% | scalp_trailing_take_profit | HOLDING_FLOW_OVERRIDE |
| 동성화인텍(033500) | +0.21% | scalp_sim_overnight_sell_today | overnight_v1 |
| 폴라리스AI(039980) | +0.13% | scalp_sim_overnight_sell_today | overnight_v1 |
| 두산로보틱스(454910) | -0.03% | scalp_sim_overnight_sell_today | overnight_v1 |
| 두산에너빌리티(034020) | -0.32% | scalp_sim_overnight_sell_today | overnight_v1 |
| 메가터치(446540) | -0.47% | scalp_sim_overnight_sell_today | overnight_v1 |
| 휴온스(243070) | -0.62% | scalp_sim_overnight_sell_today | overnight_v1 |
| 삼성전자(005930) | -0.77% | scalp_sim_overnight_sell_today | overnight_v1 |
| SK하이닉스(000660) | -1.25% | scalp_sim_overnight_sell_today | overnight_v1 |
| 제이에스링크(127120) | -1.33% | scalp_sim_overnight_sell_today | overnight_v1 |
| 파두(440110) | -1.34% | scalp_sim_overnight_sell_today | overnight_v1 |
| 콘텐트리중앙(036420) | -1.62% | scalp_soft_stop_pct | HOLDING_FLOW_OVERRIDE |
| SK하이닉스(000660) | -1.63% | scalp_soft_stop_pct | HOLDING_FLOW_OVERRIDE |
| 폴라리스AI파마(041910) | -1.63% | scalp_soft_stop_pct | HOLDING_FLOW_OVERRIDE |
| 휴온스(243070) | -1.65% | scalp_soft_stop_pct | HOLDING_FLOW_OVERRIDE |
| 에프엔에스테크(083500) | -1.66% | scalp_soft_stop_pct | HOLDING_FLOW_OVERRIDE |
| 메가터치(446540) | -1.70% | scalp_soft_stop_pct | HOLDING_FLOW_OVERRIDE |
| 큐라클(365270) | -1.70% | scalp_soft_stop_pct | HOLDING_FLOW_OVERRIDE |
| 현대차(005380) | -1.71% | scalp_soft_stop_pct | HOLDING_FLOW_OVERRIDE |
| 큐라클(365270) | -1.71% | scalp_soft_stop_pct | HOLDING_FLOW_OVERRIDE |
| LG이노텍(011070) | -1.73% | scalp_soft_stop_pct | HOLDING_FLOW_OVERRIDE |
| 코스맥스엔비티(222040) | -1.74% | scalp_soft_stop_pct | HOLDING_FLOW_OVERRIDE |
| LG전자(066570) | -1.74% | scalp_soft_stop_pct | HOLDING_FLOW_OVERRIDE |
| 한화손해보험(000370) | -1.76% | scalp_soft_stop_pct | HOLDING_FLOW_OVERRIDE |
| 에스엠(041510) | -1.77% | scalp_soft_stop_pct | HOLDING_FLOW_OVERRIDE |
| 에이플러스에셋(244920) | -1.77% | scalp_soft_stop_pct | HOLDING_FLOW_OVERRIDE |
| 한화에어로스페이스(012450) | -1.77% | scalp_soft_stop_pct | HOLDING_FLOW_OVERRIDE |
| 한화손해보험(000370) | -1.78% | scalp_soft_stop_pct | HOLDING_FLOW_OVERRIDE |
| 큐라클(365270) | -1.79% | scalp_soft_stop_pct | HOLDING_FLOW_OVERRIDE |
| 두산로보틱스(454910) | -1.80% | scalp_soft_stop_pct | HOLDING_FLOW_OVERRIDE |
| 원익IPS(240810) | -1.82% | scalp_soft_stop_pct | HOLDING_FLOW_OVERRIDE |
| 네이처셀(007390) | -1.84% | scalp_soft_stop_pct | HOLDING_FLOW_OVERRIDE |
| 삼아알미늄(006110) | -1.86% | scalp_soft_stop_pct | HOLDING_FLOW_OVERRIDE |
| 삼성전자(005930) | -1.86% | scalp_soft_stop_pct | HOLDING_FLOW_OVERRIDE |
| 한솔테크닉스(004710) | -1.97% | scalp_soft_stop_pct | HOLDING_FLOW_OVERRIDE |
| 소룩스(290690) | -1.99% | scalp_soft_stop_pct | HOLDING_FLOW_OVERRIDE |
| 가온그룹(078890) | -2.00% | scalp_soft_stop_pct | HOLDING_FLOW_OVERRIDE |
| 소룩스(290690) | -2.02% | scalp_soft_stop_pct | HOLDING_FLOW_OVERRIDE |
| LIG디펜스앤에어로스페이스(079550) | -2.06% | scalp_soft_stop_pct | HOLDING_FLOW_OVERRIDE |
| 엘앤케이바이오(156100) | -2.09% | scalp_soft_stop_pct | HOLDING_FLOW_OVERRIDE |
| 제주반도체(080220) | -2.12% | scalp_soft_stop_pct | HOLDING_FLOW_OVERRIDE |
| 제너셈(217190) | -2.30% | scalp_soft_stop_pct | HOLDING_FLOW_OVERRIDE |
| 앤씨앤(092600) | -2.33% | scalp_soft_stop_pct | HOLDING_FLOW_OVERRIDE |
| 수젠텍(253840) | -2.53% | scalp_hard_stop_pct | MANUAL |
| 녹십자엠에스(142280) | -2.53% | scalp_hard_stop_pct | MANUAL |
| 바이오니아(064550) | -2.60% | scalp_hard_stop_pct | MANUAL |
| 태성(323280) | -2.62% | scalp_hard_stop_pct | MANUAL |
| 태성(323280) | -2.75% | scalp_hard_stop_pct | MANUAL |
| 한선엔지니어링(452280) | -2.79% | scalp_hard_stop_pct | MANUAL |
| 제너셈(217190) | -2.80% | scalp_hard_stop_pct | MANUAL |
| 바이오니아(064550) | -2.88% | scalp_hard_stop_pct | MANUAL |
| 앤씨앤(092600) | -3.28% | scalp_hard_stop_pct | MANUAL |
| 피델릭스(032580) | -4.62% | scalp_hard_stop_pct | MANUAL |

## Expired Entries

| 종목 | limit_price | parent |
| --- | ---: | --- |

## Real Completed Reference

| 종목 | 수익률 | exit_rule |
| --- | ---: | --- |
