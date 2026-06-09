# Swing Daily Simulation - 2026-06-09

- runtime_change: `False`
- recommendation_rows: `10` / live `10` / diagnostic `0`
- recommendation_sources: `{'recommendation_history': 7, 'daily_recommendations_v2_csv': 3}`
- db_recommendation_rows: `7`
- source_signal_dates: `['2026-06-09']`
- simulated_count: `10`
- closed_count: `0`
- planned_or_open_count: `10`
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
| `gap_pass` | 10 | 0 | 0.00% | 0.00% | `{'PENDING_ENTRY': 10}` |
| `gatekeeper_pass` | 10 | 0 | 0.00% | 0.00% | `{'PENDING_ENTRY': 10}` |
| `selection_only` | 10 | 0 | 0.00% | 0.00% | `{'PENDING_ENTRY': 10}` |

## Runtime Entry Funnel

- source: `/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-06-09.jsonl`

| stage | raw | unique_records | examples |
| --- | ---: | ---: | --- |
| `blocked_swing_gap` | 11055 | 7 | 삼성전기(009150), 유진투자증권(001200), 유진투자증권(001200), 유진투자증권(001200), 유진투자증권(001200) |
| `blocked_gatekeeper_reject` | 8377 | 8 | 카카오뱅크(323410), JB금융지주(175330), S-Oil(010950), 사조동아원(008040), 유진투자증권(001200) |
| `swing_sim_buy_order_assumed_filled` | 13 | 7 | S-Oil(010950), 신한지주(055550), KB금융(105560), KB금융(105560), S-Oil(010950) |
| `swing_sim_holding_started` | 13 | 7 | S-Oil(010950), 신한지주(055550), KB금융(105560), KB금융(105560), S-Oil(010950) |
| `swing_sim_order_bundle_assumed_filled` | 13 | 7 | S-Oil(010950), 신한지주(055550), KB금융(105560), KB금융(105560), S-Oil(010950) |

## Simulated Trades

| code | name | source | status | guard | qty | entry | exit | net_ret | reason |
| --- | --- | --- | --- | --- | ---: | --- | --- | ---: | --- |
| `009150` | 삼성전기 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `010950` | S-Oil | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `016360` | 삼성증권 | `daily_recommendations_v2_csv` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `032830` | 삼성생명 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `055550` | 신한지주 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `105560` | KB금융 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `175330` | JB금융지주 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `248070` | 솔루엠 | `daily_recommendations_v2_csv` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `323410` | 카카오뱅크 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `404990` | 신한서부티엔디리츠 | `daily_recommendations_v2_csv` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
