# Swing Daily Simulation - 2026-05-20

- runtime_change: `False`
- recommendation_rows: `25` / live `25` / diagnostic `0`
- recommendation_sources: `{'recommendation_history': 22, 'daily_recommendations_v2_csv': 3}`
- db_recommendation_rows: `22`
- source_signal_dates: `['2026-05-19', '2026-05-20']`
- simulated_count: `25`
- closed_count: `0`
- planned_or_open_count: `25`
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
| `gap_pass` | 25 | 0 | 0.00% | 0.00% | `{'PENDING_ENTRY': 25}` |
| `gatekeeper_pass` | 25 | 0 | 0.00% | 0.00% | `{'PENDING_ENTRY': 25}` |
| `selection_only` | 25 | 0 | 0.00% | 0.00% | `{'PENDING_ENTRY': 25}` |

## Runtime Entry Funnel

- source: `/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-05-20.jsonl`

| stage | raw | unique_records | examples |
| --- | ---: | ---: | --- |
| `blocked_swing_gap` | 416 | 1 | 현대모비스(012330), 현대모비스(012330), 현대모비스(012330), 현대모비스(012330), 현대모비스(012330) |
| `blocked_gatekeeper_reject` | 87 | 9 | 한국타이어앤테크놀로지(161390), HL만도(204320), SK텔레콤(017670), 현대지에프홀딩스(005440), LG유플러스(032640) |

## Simulated Trades

| code | name | source | status | guard | qty | entry | exit | net_ret | reason |
| --- | --- | --- | --- | --- | ---: | --- | --- | ---: | --- |
| `000240` | 한국앤컴퍼니 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `001450` | 현대해상 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `003490` | 대한항공 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `005440` | 현대지에프홀딩스 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `011200` | HMM | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `011210` | 현대위아 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `012330` | 현대모비스 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `017670` | SK텔레콤 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `028670` | 팬오션 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `032640` | LG유플러스 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `034220` | LG디스플레이 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `035250` | 강원랜드 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `036460` | 한국가스공사 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `078930` | GS | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `086280` | 현대글로비스 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `091810` | 트리니티항공 | `daily_recommendations_v2_csv` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `105560` | KB금융 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `138930` | BNK금융지주 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `139130` | iM금융지주 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `161390` | 한국타이어앤테크놀로지 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `204320` | HL만도 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `244920` | 에이플러스에셋 | `daily_recommendations_v2_csv` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `251270` | 넷마블 | `daily_recommendations_v2_csv` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `352820` | 하이브 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `454910` | 두산로보틱스 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
