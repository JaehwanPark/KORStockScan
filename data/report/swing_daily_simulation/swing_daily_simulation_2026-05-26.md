# Swing Daily Simulation - 2026-05-26

- runtime_change: `False`
- recommendation_rows: `22` / live `22` / diagnostic `0`
- recommendation_sources: `{'recommendation_history': 19, 'daily_recommendations_v2_csv': 3}`
- db_recommendation_rows: `19`
- source_signal_dates: `['2026-05-26']`
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
| `gap_pass` | 22 | 0 | 0.00% | 0.00% | `{'PENDING_ENTRY': 22}` |
| `gatekeeper_pass` | 22 | 0 | 0.00% | 0.00% | `{'PENDING_ENTRY': 22}` |
| `selection_only` | 22 | 0 | 0.00% | 0.00% | `{'PENDING_ENTRY': 22}` |

## Runtime Entry Funnel

- source: `/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-05-26.jsonl`

| stage | raw | unique_records | examples |
| --- | ---: | ---: | --- |
| `blocked_swing_gap` | 13766 | 5 | 한온시스템(018880), LG디스플레이(034220), 대한항공(003490), 한온시스템(018880), LG디스플레이(034220) |
| `blocked_gatekeeper_reject` | 33 | 6 | 현대위아(011210), 팬오션(028670), 오리온(271560), 신한알파리츠(293940), 신한알파리츠(293940) |

## Simulated Trades

| code | name | source | status | guard | qty | entry | exit | net_ret | reason |
| --- | --- | --- | --- | --- | ---: | --- | --- | ---: | --- |
| `000810` | 삼성화재 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `001450` | 현대해상 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `003490` | 대한항공 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `005680` | 삼영전자 | `daily_recommendations_v2_csv` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `005930` | 삼성전자 | `daily_recommendations_v2_csv` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `007070` | GS리테일 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `010580` | 에스엠벡셀 | `daily_recommendations_v2_csv` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `011200` | HMM | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `011210` | 현대위아 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `018880` | 한온시스템 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `028670` | 팬오션 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `033780` | KT&G | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `034220` | LG디스플레이 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `036570` | NC | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `068270` | 셀트리온 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `078930` | GS | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `105560` | KB금융 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `161390` | 한국타이어앤테크놀로지 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `259960` | 크래프톤 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `271560` | 오리온 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `302440` | SK바이오사이언스 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `326030` | SK바이오팜 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
