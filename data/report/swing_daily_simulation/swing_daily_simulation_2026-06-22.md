# Swing Daily Simulation - 2026-06-22

- runtime_change: `False`
- recommendation_rows: `26` / live `26` / diagnostic `0`
- recommendation_sources: `{'recommendation_history': 23, 'daily_recommendations_v2_csv': 3}`
- db_recommendation_rows: `23`
- source_signal_dates: `['2026-06-22']`
- simulated_count: `26`
- closed_count: `0`
- planned_or_open_count: `26`
- closed win_rate: `0.00%`
- closed avg_net_ret: `0.00%`

## Model Backtest Snapshot

- range: `2026-01-02` ~ `2026-03-16`
- trades: `123`
- win_rate: `47.15%`
- avg_net_ret: `1.51%`
- sum_net_ret: `185.32%`

## Runtime Dry-Run Policy

- mode: `runtime_order_dry_run_daily_proxy`
- entry: `runtime guard dry-run, no broker order submit`
- order_type: `최유리지정가` (`6`)
- simulation_cash_krw: `10000000`

## Observation Arms

| arm | simulated | closed | win_rate | avg_net_ret | status_counts |
| --- | ---: | ---: | ---: | ---: | --- |
| `gap_pass` | 26 | 0 | 0.00% | 0.00% | `{'PENDING_ENTRY': 26}` |
| `gatekeeper_pass` | 26 | 0 | 0.00% | 0.00% | `{'PENDING_ENTRY': 26}` |
| `selection_only` | 26 | 0 | 0.00% | 0.00% | `{'PENDING_ENTRY': 26}` |

## Runtime Entry Funnel

- source: `/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-06-22.jsonl`

| stage | raw | unique_records | examples |
| --- | ---: | ---: | --- |
| `blocked_gatekeeper_reject` | 208 | 4 | 삼성중공업(010140), 제일기획(030000), 케이씨텍(281820), 두산퓨얼셀(336260), 제일기획(030000) |
| `blocked_swing_gap` | 69 | 1 | 케이씨텍(281820), 케이씨텍(281820), 케이씨텍(281820), 케이씨텍(281820), 케이씨텍(281820) |
| `swing_sim_buy_order_assumed_filled` | 66 | 4 | 제일기획(030000), 제일기획(030000), 제일기획(030000), 제일기획(030000), 제일기획(030000) |
| `swing_sim_holding_started` | 66 | 4 | 제일기획(030000), 제일기획(030000), 제일기획(030000), 제일기획(030000), 제일기획(030000) |
| `swing_sim_order_bundle_assumed_filled` | 66 | 4 | 제일기획(030000), 제일기획(030000), 제일기획(030000), 제일기획(030000), 제일기획(030000) |

## Simulated Trades

| code | name | source | status | guard | qty | entry | exit | net_ret | reason |
| --- | --- | --- | --- | --- | ---: | --- | --- | ---: | --- |
| `001680` | 대상 | `daily_recommendations_v2_csv` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `003490` | 대한항공 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `005850` | 에스엘 | `daily_recommendations_v2_csv` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `010140` | 삼성중공업 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `012450` | 한화에어로스페이스 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `024110` | 기업은행 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `030000` | 제일기획 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `033780` | KT&G | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `042660` | 한화오션 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `047810` | 한국항공우주 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `055550` | 신한지주 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `064350` | 현대로템 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `086280` | 현대글로비스 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `086790` | 하나금융지주 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `088350` | 한화생명 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `093370` | 후성 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `097230` | HJ중공업 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `120110` | 코오롱인더 | `daily_recommendations_v2_csv` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `138930` | BNK금융지주 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `204320` | HL만도 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `229640` | LS에코에너지 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `281820` | 케이씨텍 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `329180` | HD현대중공업 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `352820` | 하이브 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `361610` | SK아이이테크놀로지 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `462870` | 시프트업 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
