# Swing Daily Simulation - 2026-06-15

- runtime_change: `False`
- recommendation_rows: `17` / live `17` / diagnostic `0`
- recommendation_sources: `{'recommendation_history': 14, 'daily_recommendations_v2_csv': 3}`
- db_recommendation_rows: `14`
- source_signal_dates: `['2026-06-12', '2026-06-15']`
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
| `gap_pass` | 17 | 0 | 0.00% | 0.00% | `{'PENDING_ENTRY': 17}` |
| `gatekeeper_pass` | 17 | 0 | 0.00% | 0.00% | `{'PENDING_ENTRY': 17}` |
| `selection_only` | 17 | 0 | 0.00% | 0.00% | `{'PENDING_ENTRY': 17}` |

## Runtime Entry Funnel

- source: `/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-06-15.jsonl`

| stage | raw | unique_records | examples |
| --- | ---: | ---: | --- |
| `blocked_gatekeeper_reject` | 9920 | 15 | iM금융지주(139130), 한국가스공사(036460), 기아(000270), 미스토홀딩스(081660), JB금융지주(175330) |
| `blocked_swing_gap` | 9200 | 11 | 대한항공(003490), 일진홀딩스(015860), 대한항공(003490), 일진홀딩스(015860), 대한항공(003490) |
| `swing_sim_buy_order_assumed_filled` | 69 | 17 | 기아(000270), KB금융(105560), 한전기술(052690), KT&G(033780), BNK금융지주(138930) |
| `swing_sim_holding_started` | 69 | 17 | 기아(000270), KB금융(105560), 한전기술(052690), KT&G(033780), BNK금융지주(138930) |
| `swing_sim_order_bundle_assumed_filled` | 69 | 17 | 기아(000270), KB금융(105560), 한전기술(052690), KT&G(033780), BNK금융지주(138930) |

## Simulated Trades

| code | name | source | status | guard | qty | entry | exit | net_ret | reason |
| --- | --- | --- | --- | --- | ---: | --- | --- | ---: | --- |
| `000270` | 기아 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `003490` | 대한항공 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `004560` | 현대비앤지스틸 | `daily_recommendations_v2_csv` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `011200` | HMM | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `015860` | 일진홀딩스 | `daily_recommendations_v2_csv` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `024110` | 기업은행 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `033780` | KT&G | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `036460` | 한국가스공사 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `052690` | 한전기술 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `081660` | 미스토홀딩스 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `105560` | KB금융 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `108320` | LX세미콘 | `daily_recommendations_v2_csv` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `138930` | BNK금융지주 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `139130` | iM금융지주 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `175330` | JB금융지주 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `204320` | HL만도 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `323410` | 카카오뱅크 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
