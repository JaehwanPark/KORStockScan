# Swing Daily Simulation - 2026-05-21

- runtime_change: `False`
- recommendation_rows: `22` / live `22` / diagnostic `0`
- recommendation_sources: `{'recommendation_history': 22}`
- db_recommendation_rows: `22`
- source_signal_dates: `['2026-05-21']`
- simulated_count: `22`
- closed_count: `0`
- planned_or_open_count: `22`
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
| `gap_pass` | 22 | 0 | 0.00% | 0.00% | `{'PLANNED_ENTRY': 22}` |
| `gatekeeper_pass` | 22 | 0 | 0.00% | 0.00% | `{'PLANNED_ENTRY': 22}` |
| `selection_only` | 22 | 0 | 0.00% | 0.00% | `{'PLANNED_ENTRY': 22}` |

## Runtime Entry Funnel

- source: `/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-05-21.jsonl.gz`

| stage | raw | unique_records | examples |
| --- | ---: | ---: | --- |
| `blocked_swing_gap` | 119651 | 17 | 삼성화재(000810), 한국항공우주(047810), 현대모비스(012330), LG씨엔에스(064400), 대한항공(003490) |
| `blocked_gatekeeper_reject` | 143 | 19 | GS(078930), HMM(011200), KB금융(105560), 기업은행(024110), 한국타이어앤테크놀로지(161390) |

## Simulated Trades

| code | name | source | status | guard | qty | entry | exit | net_ret | reason |
| --- | --- | --- | --- | --- | ---: | --- | --- | ---: | --- |
| `000100` | 유한양행 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_SWING_GAP` | 0 | 2026-05-22 |  |  |  |
| `000810` | 삼성화재 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_SWING_GAP` | 0 | 2026-05-22 |  |  |  |
| `003490` | 대한항공 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_SWING_GAP` | 0 | 2026-05-22 |  |  |  |
| `007070` | GS리테일 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_SWING_GAP` | 0 | 2026-05-22 |  |  |  |
| `011200` | HMM | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-22 |  |  |  |
| `012330` | 현대모비스 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_SWING_GAP` | 0 | 2026-05-22 |  |  |  |
| `012450` | 한화에어로스페이스 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-22 |  |  |  |
| `024110` | 기업은행 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-22 |  |  |  |
| `032640` | LG유플러스 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_SWING_GAP` | 0 | 2026-05-22 |  |  |  |
| `033780` | KT&G | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-22 |  |  |  |
| `034220` | LG디스플레이 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_SWING_GAP` | 0 | 2026-05-22 |  |  |  |
| `047810` | 한국항공우주 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-22 |  |  |  |
| `064400` | LG씨엔에스 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_SWING_GAP` | 0 | 2026-05-22 |  |  |  |
| `068270` | 셀트리온 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_SWING_GAP` | 0 | 2026-05-22 |  |  |  |
| `078930` | GS | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-22 |  |  |  |
| `088350` | 한화생명 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_SWING_GAP` | 0 | 2026-05-22 |  |  |  |
| `105560` | KB금융 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_SWING_GAP` | 0 | 2026-05-22 |  |  |  |
| `138930` | BNK금융지주 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_SWING_GAP` | 0 | 2026-05-22 |  |  |  |
| `161390` | 한국타이어앤테크놀로지 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_SWING_GAP` | 0 | 2026-05-22 |  |  |  |
| `175330` | JB금융지주 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-22 |  |  |  |
| `326030` | SK바이오팜 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_SWING_GAP` | 0 | 2026-05-22 |  |  |  |
| `352820` | 하이브 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-22 |  |  |  |
