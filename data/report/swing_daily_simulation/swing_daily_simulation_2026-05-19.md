# Swing Daily Simulation - 2026-05-19

- runtime_change: `False`
- recommendation_rows: `17` / live `17` / diagnostic `0`
- recommendation_sources: `{'recommendation_history': 17}`
- db_recommendation_rows: `17`
- source_signal_dates: `['2026-05-19']`
- simulated_count: `17`
- closed_count: `0`
- planned_or_open_count: `17`
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
| `gap_pass` | 17 | 0 | 0.00% | 0.00% | `{'PLANNED_ENTRY': 17}` |
| `gatekeeper_pass` | 17 | 0 | 0.00% | 0.00% | `{'PLANNED_ENTRY': 17}` |
| `selection_only` | 17 | 0 | 0.00% | 0.00% | `{'PLANNED_ENTRY': 17}` |

## Runtime Entry Funnel

- source: `/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-05-19.jsonl.gz`

| stage | raw | unique_records | examples |
| --- | ---: | ---: | --- |
| `blocked_swing_gap` | 14396 | 2 | LX홀딩스(383800), LX홀딩스(383800), LX홀딩스(383800), LX홀딩스(383800), LX홀딩스(383800) |
| `blocked_gatekeeper_reject` | 40 | 8 | 현대지에프홀딩스(005440), 미스토홀딩스(081660), KT&G(033780), DB손해보험(005830), 현대해상(001450) |

## Simulated Trades

| code | name | source | status | guard | qty | entry | exit | net_ret | reason |
| --- | --- | --- | --- | --- | ---: | --- | --- | ---: | --- |
| `000270` | 기아 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-20 |  |  |  |
| `001450` | 현대해상 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-20 |  |  |  |
| `003490` | 대한항공 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-20 |  |  |  |
| `004020` | 현대제철 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-20 |  |  |  |
| `005440` | 현대지에프홀딩스 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-20 |  |  |  |
| `005830` | DB손해보험 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-20 |  |  |  |
| `005850` | 에스엘 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-20 |  |  |  |
| `011210` | 현대위아 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-20 |  |  |  |
| `018260` | 삼성에스디에스 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-20 |  |  |  |
| `028260` | 삼성물산 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-20 |  |  |  |
| `032640` | LG유플러스 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-20 |  |  |  |
| `033780` | KT&G | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-20 |  |  |  |
| `034220` | LG디스플레이 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-20 |  |  |  |
| `081660` | 미스토홀딩스 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-20 |  |  |  |
| `086280` | 현대글로비스 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-20 |  |  |  |
| `204320` | HL만도 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-20 |  |  |  |
| `307950` | 현대오토에버 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-20 |  |  |  |
