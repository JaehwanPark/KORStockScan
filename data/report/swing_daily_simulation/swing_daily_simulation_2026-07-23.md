# Swing Daily Simulation - 2026-07-23

- runtime_change: `False`
- recommendation_rows: `2` / live `2` / diagnostic `0`
- recommendation_sources: `{'daily_recommendations_v2_csv': 2}`
- db_recommendation_rows: `0`
- source_signal_dates: `['2026-07-23']`
- simulated_count: `2`
- closed_count: `0`
- planned_or_open_count: `2`
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
| `gap_pass` | 2 | 0 | 0.00% | 0.00% | `{'PENDING_ENTRY': 2}` |
| `gatekeeper_pass` | 2 | 0 | 0.00% | 0.00% | `{'PENDING_ENTRY': 2}` |
| `selection_only` | 2 | 0 | 0.00% | 0.00% | `{'PENDING_ENTRY': 2}` |

## Runtime Entry Funnel

- source: `/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-23.jsonl`

| stage | raw | unique_records | examples |
| --- | ---: | ---: | --- |

## Simulated Trades

| code | name | source | status | guard | qty | entry | exit | net_ret | reason |
| --- | --- | --- | --- | --- | ---: | --- | --- | ---: | --- |
| `004020` | 현대제철 | `daily_recommendations_v2_csv` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `015860` | 일진홀딩스 | `daily_recommendations_v2_csv` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
