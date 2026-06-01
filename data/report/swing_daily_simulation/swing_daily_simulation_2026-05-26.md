# Swing Daily Simulation - 2026-05-26

- runtime_change: `False`
- recommendation_rows: `19` / live `19` / diagnostic `0`
- recommendation_sources: `{'recommendation_history': 19}`
- db_recommendation_rows: `19`
- source_signal_dates: `['2026-05-26']`
- simulated_count: `19`
- closed_count: `0`
- planned_or_open_count: `19`
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
| `gap_pass` | 19 | 0 | 0.00% | 0.00% | `{'PLANNED_ENTRY': 19}` |
| `gatekeeper_pass` | 19 | 0 | 0.00% | 0.00% | `{'PLANNED_ENTRY': 19}` |
| `selection_only` | 19 | 0 | 0.00% | 0.00% | `{'PLANNED_ENTRY': 19}` |

## Runtime Entry Funnel

- source: `/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-05-26.jsonl.gz`

| stage | raw | unique_records | examples |
| --- | ---: | ---: | --- |
| `blocked_swing_gap` | 13766 | 5 | 한온시스템(018880), LG디스플레이(034220), 대한항공(003490), 한온시스템(018880), LG디스플레이(034220) |
| `blocked_gatekeeper_reject` | 33 | 6 | 현대위아(011210), 팬오션(028670), 오리온(271560), 신한알파리츠(293940), 신한알파리츠(293940) |

## Simulated Trades

| code | name | source | status | guard | qty | entry | exit | net_ret | reason |
| --- | --- | --- | --- | --- | ---: | --- | --- | ---: | --- |
| `000810` | 삼성화재 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_SWING_GAP` | 0 | 2026-05-27 |  |  |  |
| `001450` | 현대해상 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-27 |  |  |  |
| `003490` | 대한항공 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-27 |  |  |  |
| `007070` | GS리테일 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-27 |  |  |  |
| `011200` | HMM | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-27 |  |  |  |
| `011210` | 현대위아 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-27 |  |  |  |
| `018880` | 한온시스템 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_SWING_GAP` | 0 | 2026-05-27 |  |  |  |
| `028670` | 팬오션 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-27 |  |  |  |
| `033780` | KT&G | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-27 |  |  |  |
| `034220` | LG디스플레이 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_SWING_GAP` | 0 | 2026-05-27 |  |  |  |
| `036570` | NC | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-27 |  |  |  |
| `068270` | 셀트리온 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-27 |  |  |  |
| `078930` | GS | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-27 |  |  |  |
| `105560` | KB금융 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-27 |  |  |  |
| `161390` | 한국타이어앤테크놀로지 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-27 |  |  |  |
| `259960` | 크래프톤 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-27 |  |  |  |
| `271560` | 오리온 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-27 |  |  |  |
| `302440` | SK바이오사이언스 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-27 |  |  |  |
| `326030` | SK바이오팜 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-27 |  |  |  |
