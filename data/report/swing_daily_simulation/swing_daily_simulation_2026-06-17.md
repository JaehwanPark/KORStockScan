# Swing Daily Simulation - 2026-06-17

- runtime_change: `False`
- recommendation_rows: `16` / live `16` / diagnostic `0`
- recommendation_sources: `{'recommendation_history': 13, 'daily_recommendations_v2_csv': 3}`
- db_recommendation_rows: `13`
- source_signal_dates: `['2026-06-17']`
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

- source: `/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-06-17.jsonl`

| stage | raw | unique_records | examples |
| --- | ---: | ---: | --- |
| `blocked_gatekeeper_reject` | 8769 | 10 | 코리안리(003690), 한화생명(088350), 한국가스공사(036460), 코웨이(021240), HMM(011200) |
| `blocked_swing_gap` | 2104 | 4 | 한화생명(088350), HMM(011200), TKG휴켐스(069260), 한화생명(088350), HMM(011200) |
| `swing_sim_buy_order_assumed_filled` | 31 | 16 | 기아(000270), 코리안리(003690), KT&G(033780), TKG휴켐스(069260), 한화생명(088350) |
| `swing_sim_holding_started` | 31 | 16 | 기아(000270), 코리안리(003690), KT&G(033780), TKG휴켐스(069260), 한화생명(088350) |
| `swing_sim_order_bundle_assumed_filled` | 31 | 16 | 기아(000270), 코리안리(003690), KT&G(033780), TKG휴켐스(069260), 한화생명(088350) |

## Simulated Trades

| code | name | source | status | guard | qty | entry | exit | net_ret | reason |
| --- | --- | --- | --- | --- | ---: | --- | --- | ---: | --- |
| `000270` | 기아 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `003690` | 코리안리 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `005850` | 에스엘 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `005950` | 이수화학 | `daily_recommendations_v2_csv` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `011200` | HMM | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `018880` | 한온시스템 | `daily_recommendations_v2_csv` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `021240` | 코웨이 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `033780` | KT&G | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `036460` | 한국가스공사 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `064350` | 현대로템 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `081660` | 미스토홀딩스 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `088350` | 한화생명 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `093370` | 후성 | `daily_recommendations_v2_csv` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `161390` | 한국타이어앤테크놀로지 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `316140` | 우리금융지주 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `323410` | 카카오뱅크 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
