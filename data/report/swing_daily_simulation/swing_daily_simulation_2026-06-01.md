# Swing Daily Simulation - 2026-06-01

- runtime_change: `False`
- recommendation_rows: `7` / live `7` / diagnostic `0`
- recommendation_sources: `{'recommendation_history': 4, 'daily_recommendations_v2_csv': 3}`
- db_recommendation_rows: `4`
- source_signal_dates: `['2026-05-29', '2026-06-01']`
- simulated_count: `7`
- closed_count: `0`
- planned_or_open_count: `7`
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
| `gap_pass` | 7 | 0 | 0.00% | 0.00% | `{'PENDING_ENTRY': 7}` |
| `gatekeeper_pass` | 7 | 0 | 0.00% | 0.00% | `{'PENDING_ENTRY': 7}` |
| `selection_only` | 7 | 0 | 0.00% | 0.00% | `{'PENDING_ENTRY': 7}` |

## Runtime Entry Funnel

- source: `/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-06-01.jsonl`

| stage | raw | unique_records | examples |
| --- | ---: | ---: | --- |
| `blocked_swing_gap` | 4214 | 3 | 비에이치(090460), 비에이치(090460), 비에이치(090460), 비에이치(090460), 비에이치(090460) |
| `blocked_gatekeeper_reject` | 4136 | 2 | 에스엘(005850), STX엔진(077970), 에스엘(005850), STX엔진(077970), 에스엘(005850) |
| `swing_sim_buy_order_assumed_filled` | 5 | 5 | 한국타이어앤테크놀로지(161390), STX엔진(077970), 한화엔진(082740), 비에이치(090460), 에스엘(005850) |
| `swing_sim_holding_started` | 5 | 5 | 한국타이어앤테크놀로지(161390), STX엔진(077970), 한화엔진(082740), 비에이치(090460), 에스엘(005850) |
| `swing_sim_order_bundle_assumed_filled` | 5 | 5 | 한국타이어앤테크놀로지(161390), STX엔진(077970), 한화엔진(082740), 비에이치(090460), 에스엘(005850) |

## Simulated Trades

| code | name | source | status | guard | qty | entry | exit | net_ret | reason |
| --- | --- | --- | --- | --- | ---: | --- | --- | ---: | --- |
| `000810` | 삼성화재 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `005850` | 에스엘 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `068270` | 셀트리온 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `077970` | STX엔진 | `daily_recommendations_v2_csv` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `082740` | 한화엔진 | `daily_recommendations_v2_csv` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `090460` | 비에이치 | `daily_recommendations_v2_csv` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `161390` | 한국타이어앤테크놀로지 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
