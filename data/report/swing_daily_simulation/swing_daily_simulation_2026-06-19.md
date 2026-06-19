# Swing Daily Simulation - 2026-06-19

- runtime_change: `False`
- recommendation_rows: `20` / live `20` / diagnostic `0`
- recommendation_sources: `{'recommendation_history': 17, 'daily_recommendations_v2_csv': 3}`
- db_recommendation_rows: `17`
- source_signal_dates: `['2026-06-18', '2026-06-19']`
- simulated_count: `20`
- closed_count: `0`
- planned_or_open_count: `20`
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
| `gap_pass` | 20 | 0 | 0.00% | 0.00% | `{'PENDING_ENTRY': 20}` |
| `gatekeeper_pass` | 20 | 0 | 0.00% | 0.00% | `{'PENDING_ENTRY': 20}` |
| `selection_only` | 20 | 0 | 0.00% | 0.00% | `{'PENDING_ENTRY': 20}` |

## Runtime Entry Funnel

- source: `/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-06-19.jsonl`

| stage | raw | unique_records | examples |
| --- | ---: | ---: | --- |
| `blocked_gatekeeper_reject` | 332 | 14 | HD현대마린솔루션(443060), LS(006260), 산일전기(062040), BNK금융지주(138930), 삼성E&A(028050) |
| `swing_sim_buy_order_assumed_filled` | 133 | 20 | 후성(093370), 현대건설(000720), HMM(011200), BNK금융지주(138930), KT&G(033780) |
| `swing_sim_holding_started` | 133 | 20 | 후성(093370), 현대건설(000720), HMM(011200), BNK금융지주(138930), KT&G(033780) |
| `swing_sim_order_bundle_assumed_filled` | 133 | 20 | 후성(093370), 현대건설(000720), HMM(011200), BNK금융지주(138930), KT&G(033780) |
| `blocked_swing_gap` | 130 | 6 | LS(006260), 산일전기(062040), 미래에셋생명(085620), LS(006260), 산일전기(062040) |

## Simulated Trades

| code | name | source | status | guard | qty | entry | exit | net_ret | reason |
| --- | --- | --- | --- | --- | ---: | --- | --- | ---: | --- |
| `000720` | 현대건설 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `003690` | 코리안리 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `005440` | 현대지에프홀딩스 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `006260` | LS | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `007340` | DN오토모티브 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `011200` | HMM | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `012330` | 현대모비스 | `daily_recommendations_v2_csv` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `021240` | 코웨이 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `028050` | 삼성E&A | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `033780` | KT&G | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `062040` | 산일전기 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `085620` | 미래에셋생명 | `daily_recommendations_v2_csv` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `088350` | 한화생명 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `093370` | 후성 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `097230` | HJ중공업 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `138930` | BNK금융지주 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `336260` | 두산퓨얼셀 | `daily_recommendations_v2_csv` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `352820` | 하이브 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `375500` | DL이앤씨 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `443060` | HD현대마린솔루션 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
