# Swing Daily Simulation - 2026-06-23

- runtime_change: `False`
- recommendation_rows: `5` / live `5` / diagnostic `0`
- recommendation_sources: `{'recommendation_history': 3, 'daily_recommendations_v2_csv': 2}`
- db_recommendation_rows: `3`
- source_signal_dates: `['2026-06-23']`
- simulated_count: `5`
- closed_count: `0`
- planned_or_open_count: `5`
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
| `gap_pass` | 5 | 0 | 0.00% | 0.00% | `{'PENDING_ENTRY': 5}` |
| `gatekeeper_pass` | 5 | 0 | 0.00% | 0.00% | `{'PENDING_ENTRY': 5}` |
| `selection_only` | 5 | 0 | 0.00% | 0.00% | `{'PENDING_ENTRY': 5}` |

## Runtime Entry Funnel

- source: `/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-06-23.jsonl.gz`

| stage | raw | unique_records | examples |
| --- | ---: | ---: | --- |
| `blocked_swing_gap` | 184 | 1 | 코오롱인더(120110), 코오롱인더(120110), 코오롱인더(120110), 코오롱인더(120110), 코오롱인더(120110) |
| `blocked_gatekeeper_reject` | 87 | 3 | SK아이이테크놀로지(361610), HJ중공업(097230), SK아이이테크놀로지(361610), HJ중공업(097230), SK아이이테크놀로지(361610) |
| `swing_sim_buy_order_assumed_filled` | 43 | 4 | 에스엘(005850), SK아이이테크놀로지(361610), SK아이이테크놀로지(361610), SK아이이테크놀로지(361610), SK아이이테크놀로지(361610) |
| `swing_sim_holding_started` | 43 | 4 | 에스엘(005850), SK아이이테크놀로지(361610), SK아이이테크놀로지(361610), SK아이이테크놀로지(361610), SK아이이테크놀로지(361610) |
| `swing_sim_order_bundle_assumed_filled` | 43 | 4 | 에스엘(005850), SK아이이테크놀로지(361610), SK아이이테크놀로지(361610), SK아이이테크놀로지(361610), SK아이이테크놀로지(361610) |

## Simulated Trades

| code | name | source | status | guard | qty | entry | exit | net_ret | reason |
| --- | --- | --- | --- | --- | ---: | --- | --- | ---: | --- |
| `000150` | 두산 | `daily_recommendations_v2_csv` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `000990` | DB하이텍 | `daily_recommendations_v2_csv` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `088350` | 한화생명 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `097230` | HJ중공업 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `361610` | SK아이이테크놀로지 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
