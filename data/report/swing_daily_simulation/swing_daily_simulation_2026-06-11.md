# Swing Daily Simulation - 2026-06-11

- runtime_change: `False`
- recommendation_rows: `31` / live `31` / diagnostic `0`
- recommendation_sources: `{'recommendation_history': 29, 'daily_recommendations_v2_csv': 2}`
- db_recommendation_rows: `29`
- source_signal_dates: `['2026-06-11']`
- simulated_count: `31`
- closed_count: `0`
- planned_or_open_count: `31`
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
| `gap_pass` | 31 | 0 | 0.00% | 0.00% | `{'PENDING_ENTRY': 31}` |
| `gatekeeper_pass` | 31 | 0 | 0.00% | 0.00% | `{'PENDING_ENTRY': 31}` |
| `selection_only` | 31 | 0 | 0.00% | 0.00% | `{'PENDING_ENTRY': 31}` |

## Runtime Entry Funnel

- source: `/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-06-11.jsonl`

| stage | raw | unique_records | examples |
| --- | ---: | ---: | --- |
| `blocked_gatekeeper_reject` | 2782 | 22 | 호텔신라(008770), 제일기획(030000), 한진칼(180640), 삼성생명(032830), SK네트웍스(001740) |
| `blocked_swing_gap` | 1169 | 12 | SK네트웍스(001740), SK네트웍스(001740), SK네트웍스(001740), SK네트웍스(001740), SK네트웍스(001740) |
| `swing_sim_buy_order_assumed_filled` | 57 | 30 | HJ중공업(097230), KB금융(105560), 하이브(352820), 제일기획(030000), 한진칼(180640) |
| `swing_sim_holding_started` | 57 | 30 | HJ중공업(097230), KB금융(105560), 하이브(352820), 제일기획(030000), 한진칼(180640) |
| `swing_sim_order_bundle_assumed_filled` | 57 | 30 | HJ중공업(097230), KB금융(105560), 하이브(352820), 제일기획(030000), 한진칼(180640) |

## Simulated Trades

| code | name | source | status | guard | qty | entry | exit | net_ret | reason |
| --- | --- | --- | --- | --- | ---: | --- | --- | ---: | --- |
| `000270` | 기아 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `001740` | SK네트웍스 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `002790` | 아모레퍼시픽홀딩스 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `003490` | 대한항공 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `005440` | 현대지에프홀딩스 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `005940` | NH투자증권 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `006360` | GS건설 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `008770` | 호텔신라 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `009540` | HD한국조선해양 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `010950` | S-Oil | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `011790` | SKC | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `015760` | 한국전력 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `021240` | 코웨이 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `024110` | 기업은행 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `030000` | 제일기획 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `032830` | 삼성생명 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `051910` | LG화학 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `055550` | 신한지주 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `071050` | 한국금융지주 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `097230` | HJ중공업 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `105560` | KB금융 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `161390` | 한국타이어앤테크놀로지 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `175330` | JB금융지주 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `180640` | 한진칼 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `241590` | 화승엔터프라이즈 | `daily_recommendations_v2_csv` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `251270` | 넷마블 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `267260` | HD현대일렉트릭 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `329180` | HD현대중공업 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `330590` | 롯데리츠 | `daily_recommendations_v2_csv` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `352820` | 하이브 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `377300` | 카카오페이 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
