# Swing Daily Simulation - 2026-05-22

- runtime_change: `False`
- recommendation_rows: `12` / live `12` / diagnostic `0`
- recommendation_sources: `{'recommendation_history': 12}`
- db_recommendation_rows: `12`
- source_signal_dates: `['2026-05-22']`
- simulated_count: `12`
- closed_count: `0`
- planned_or_open_count: `12`
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
| `gap_pass` | 12 | 0 | 0.00% | 0.00% | `{'PLANNED_ENTRY': 12}` |
| `gatekeeper_pass` | 12 | 0 | 0.00% | 0.00% | `{'PLANNED_ENTRY': 12}` |
| `selection_only` | 12 | 0 | 0.00% | 0.00% | `{'PLANNED_ENTRY': 12}` |

## Runtime Entry Funnel

- source: `/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-05-22.jsonl.gz`

| stage | raw | unique_records | examples |
| --- | ---: | ---: | --- |
| `blocked_swing_gap` | 58064 | 9 | 디아이씨(092200), 유한양행(000100), 디아이씨(092200), 유한양행(000100), 디아이씨(092200) |
| `blocked_gatekeeper_reject` | 113 | 11 | 현대해상(001450), 한국타이어앤테크놀로지(161390), HMM(011200), 코리안리(003690), 현대위아(011210) |

## Simulated Trades

| code | name | source | status | guard | qty | entry | exit | net_ret | reason |
| --- | --- | --- | --- | --- | ---: | --- | --- | ---: | --- |
| `001450` | 현대해상 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-27 |  |  |  |
| `003490` | 대한항공 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-27 |  |  |  |
| `003690` | 코리안리 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-27 |  |  |  |
| `011200` | HMM | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-27 |  |  |  |
| `011210` | 현대위아 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-27 |  |  |  |
| `018260` | 삼성에스디에스 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_SWING_GAP` | 0 | 2026-05-27 |  |  |  |
| `028670` | 팬오션 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_SWING_GAP` | 0 | 2026-05-27 |  |  |  |
| `033780` | KT&G | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-27 |  |  |  |
| `034220` | LG디스플레이 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_SWING_GAP` | 0 | 2026-05-27 |  |  |  |
| `036460` | 한국가스공사 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-27 |  |  |  |
| `088350` | 한화생명 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-27 |  |  |  |
| `161390` | 한국타이어앤테크놀로지 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_SWING_GAP` | 0 | 2026-05-27 |  |  |  |
