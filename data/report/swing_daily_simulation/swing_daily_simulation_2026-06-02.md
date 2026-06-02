# Swing Daily Simulation - 2026-06-02

- runtime_change: `False`
- recommendation_rows: `16` / live `16` / diagnostic `0`
- recommendation_sources: `{'recommendation_history': 13, 'daily_recommendations_v2_csv': 3}`
- db_recommendation_rows: `13`
- source_signal_dates: `['2026-06-01', '2026-06-02']`
- simulated_count: `16`
- closed_count: `0`
- planned_or_open_count: `16`
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
| `gap_pass` | 16 | 0 | 0.00% | 0.00% | `{'PENDING_ENTRY': 16}` |
| `gatekeeper_pass` | 16 | 0 | 0.00% | 0.00% | `{'PENDING_ENTRY': 16}` |
| `selection_only` | 16 | 0 | 0.00% | 0.00% | `{'PENDING_ENTRY': 16}` |

## Runtime Entry Funnel

- source: `/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-06-02.jsonl`

| stage | raw | unique_records | examples |
| --- | ---: | ---: | --- |
| `blocked_gatekeeper_reject` | 8916 | 7 | 대한항공(003490), 삼성SDI(006400), 두산퓨얼셀(336260), 두산퓨얼셀(336260), 두산퓨얼셀(336260) |
| `blocked_swing_gap` | 713 | 3 | 삼성전자(005930), NC(036570), NC(036570), NC(036570), NC(036570) |
| `swing_sim_buy_order_assumed_filled` | 8 | 5 | 한화오션(042660), 한화오션(042660), 한화오션(042660), 대한항공(003490), 한화오션(042660) |
| `swing_sim_holding_started` | 8 | 5 | 한화오션(042660), 한화오션(042660), 한화오션(042660), 대한항공(003490), 한화오션(042660) |
| `swing_sim_order_bundle_assumed_filled` | 8 | 5 | 한화오션(042660), 한화오션(042660), 한화오션(042660), 대한항공(003490), 한화오션(042660) |

## Simulated Trades

| code | name | source | status | guard | qty | entry | exit | net_ret | reason |
| --- | --- | --- | --- | --- | ---: | --- | --- | ---: | --- |
| `000270` | 기아 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `003490` | 대한항공 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `005850` | 에스엘 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `005930` | 삼성전자 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `006260` | LS | `daily_recommendations_v2_csv` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `006400` | 삼성SDI | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `033780` | KT&G | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `036570` | NC | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `042660` | 한화오션 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `055550` | 신한지주 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `068270` | 셀트리온 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `082740` | 한화엔진 | `daily_recommendations_v2_csv` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `161390` | 한국타이어앤테크놀로지 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `267250` | HD현대 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `336260` | 두산퓨얼셀 | `daily_recommendations_v2_csv` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `443060` | HD현대마린솔루션 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
