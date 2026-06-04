# Swing Daily Simulation - 2026-06-04

- runtime_change: `False`
- recommendation_rows: `14` / live `14` / diagnostic `0`
- recommendation_sources: `{'recommendation_history': 11, 'daily_recommendations_v2_csv': 3}`
- db_recommendation_rows: `11`
- source_signal_dates: `['2026-06-02', '2026-06-04']`
- simulated_count: `14`
- closed_count: `0`
- planned_or_open_count: `14`
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
| `gap_pass` | 14 | 0 | 0.00% | 0.00% | `{'PENDING_ENTRY': 14}` |
| `gatekeeper_pass` | 14 | 0 | 0.00% | 0.00% | `{'PENDING_ENTRY': 14}` |
| `selection_only` | 14 | 0 | 0.00% | 0.00% | `{'PENDING_ENTRY': 14}` |

## Runtime Entry Funnel

- source: `/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-06-04.jsonl`

| stage | raw | unique_records | examples |
| --- | ---: | ---: | --- |
| `blocked_swing_gap` | 923 | 5 | 삼성화재(000810), KB금융(105560), 한솔테크닉스(004710), 신한지주(055550), 한국앤컴퍼니(000240) |
| `blocked_gatekeeper_reject` | 829 | 3 | KB금융(105560), 신한지주(055550), 한국앤컴퍼니(000240), KB금융(105560), 신한지주(055550) |
| `swing_sim_buy_order_assumed_filled` | 17 | 11 | 넷마블(251270), LG디스플레이(034220), HL만도(204320), 한솔테크닉스(004710), 신한지주(055550) |
| `swing_sim_holding_started` | 17 | 11 | 넷마블(251270), LG디스플레이(034220), HL만도(204320), 한솔테크닉스(004710), 신한지주(055550) |
| `swing_sim_order_bundle_assumed_filled` | 17 | 11 | 넷마블(251270), LG디스플레이(034220), HL만도(204320), 한솔테크닉스(004710), 신한지주(055550) |

## Simulated Trades

| code | name | source | status | guard | qty | entry | exit | net_ret | reason |
| --- | --- | --- | --- | --- | ---: | --- | --- | ---: | --- |
| `000240` | 한국앤컴퍼니 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `000270` | 기아 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `000810` | 삼성화재 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `004710` | 한솔테크닉스 | `daily_recommendations_v2_csv` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `009150` | 삼성전기 | `daily_recommendations_v2_csv` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `009420` | 한올바이오파마 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `011210` | 현대위아 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `022100` | 포스코DX | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `028050` | 삼성E&A | `daily_recommendations_v2_csv` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `034220` | LG디스플레이 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `055550` | 신한지주 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `105560` | KB금융 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `204320` | HL만도 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `251270` | 넷마블 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
