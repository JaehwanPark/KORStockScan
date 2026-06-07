# Swing Daily Simulation - 2026-06-05

- runtime_change: `False`
- recommendation_rows: `16` / live `16` / diagnostic `0`
- recommendation_sources: `{'recommendation_history': 13, 'daily_recommendations_v2_csv': 3}`
- db_recommendation_rows: `13`
- source_signal_dates: `['2026-06-05']`
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

- source: `/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-06-05.jsonl`

| stage | raw | unique_records | examples |
| --- | ---: | ---: | --- |
| `blocked_swing_gap` | 4854 | 6 | 한올바이오파마(009420), 신한지주(055550), KB금융(105560), 한올바이오파마(009420), 한올바이오파마(009420) |
| `blocked_gatekeeper_reject` | 723 | 5 | 삼성전기(009150), LG전자(066570), LG씨엔에스(064400), 케이뱅크(279570), LG씨엔에스(064400) |
| `swing_sim_buy_order_assumed_filled` | 15 | 8 | iM금융지주(139130), 신한지주(055550), LG씨엔에스(064400), 코리안리(003690), 코리안리(003690) |
| `swing_sim_holding_started` | 15 | 8 | iM금융지주(139130), 신한지주(055550), LG씨엔에스(064400), 코리안리(003690), 코리안리(003690) |
| `swing_sim_order_bundle_assumed_filled` | 15 | 8 | iM금융지주(139130), 신한지주(055550), LG씨엔에스(064400), 코리안리(003690), 코리안리(003690) |

## Simulated Trades

| code | name | source | status | guard | qty | entry | exit | net_ret | reason |
| --- | --- | --- | --- | --- | ---: | --- | --- | ---: | --- |
| `000240` | 한국앤컴퍼니 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `000660` | SK하이닉스 | `daily_recommendations_v2_csv` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `003550` | LG | `daily_recommendations_v2_csv` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `003690` | 코리안리 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `005385` | 현대차우 | `daily_recommendations_v2_csv` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `007660` | 이수페타시스 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `009150` | 삼성전기 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `009420` | 한올바이오파마 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `010950` | S-Oil | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `028260` | 삼성물산 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `055550` | 신한지주 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `078930` | GS | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `105560` | KB금융 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `139130` | iM금융지주 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `180640` | 한진칼 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `279570` | 케이뱅크 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
