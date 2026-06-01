# Swing Daily Simulation - 2026-05-18

- runtime_change: `False`
- recommendation_rows: `39` / live `39` / diagnostic `0`
- recommendation_sources: `{'recommendation_history': 39}`
- db_recommendation_rows: `39`
- source_signal_dates: `['2026-05-18']`
- simulated_count: `39`
- closed_count: `0`
- planned_or_open_count: `39`
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
| `gap_pass` | 39 | 0 | 0.00% | 0.00% | `{'PLANNED_ENTRY': 39}` |
| `gatekeeper_pass` | 39 | 0 | 0.00% | 0.00% | `{'PLANNED_ENTRY': 39}` |
| `selection_only` | 39 | 0 | 0.00% | 0.00% | `{'PLANNED_ENTRY': 39}` |

## Runtime Entry Funnel

- source: `/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-05-18.jsonl.gz`

| stage | raw | unique_records | examples |
| --- | ---: | ---: | --- |
| `blocked_swing_gap` | 139697 | 8 | 현대해상(001450), 에이치브이엠(295310), 현대해상(001450), 에이치브이엠(295310), 현대해상(001450) |
| `blocked_gatekeeper_reject` | 154 | 20 | 두산퓨얼셀(336260), DN오토모티브(007340), DB하이텍(000990), DB손해보험(005830), 기아(000270) |

## Simulated Trades

| code | name | source | status | guard | qty | entry | exit | net_ret | reason |
| --- | --- | --- | --- | --- | ---: | --- | --- | ---: | --- |
| `000270` | 기아 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-20 |  |  |  |
| `000720` | 현대건설 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-20 |  |  |  |
| `000810` | 삼성화재 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-20 |  |  |  |
| `000880` | 한화 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-20 |  |  |  |
| `000990` | DB하이텍 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-20 |  |  |  |
| `001040` | CJ | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-20 |  |  |  |
| `001430` | 세아베스틸지주 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-20 |  |  |  |
| `001450` | 현대해상 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_SWING_GAP` | 0 | 2026-05-20 |  |  |  |
| `003490` | 대한항공 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-20 |  |  |  |
| `004020` | 현대제철 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-20 |  |  |  |
| `005387` | 현대차2우B | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-20 |  |  |  |
| `005440` | 현대지에프홀딩스 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-20 |  |  |  |
| `005830` | DB손해보험 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-20 |  |  |  |
| `007070` | GS리테일 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-20 |  |  |  |
| `007340` | DN오토모티브 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-20 |  |  |  |
| `009420` | 한올바이오파마 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-20 |  |  |  |
| `017670` | SK텔레콤 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-20 |  |  |  |
| `018260` | 삼성에스디에스 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-20 |  |  |  |
| `018880` | 한온시스템 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-20 |  |  |  |
| `028670` | 팬오션 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-20 |  |  |  |
| `031430` | 신세계인터내셔날 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-20 |  |  |  |
| `034220` | LG디스플레이 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-20 |  |  |  |
| `036460` | 한국가스공사 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-20 |  |  |  |
| `042700` | 한미반도체 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-20 |  |  |  |
| `060980` | HL홀딩스 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-20 |  |  |  |
| `078930` | GS | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-20 |  |  |  |
| `081660` | 미스토홀딩스 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_SWING_GAP` | 0 | 2026-05-20 |  |  |  |
| `086280` | 현대글로비스 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-20 |  |  |  |
| `088350` | 한화생명 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_SWING_GAP` | 0 | 2026-05-20 |  |  |  |
| `105560` | KB금융 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-20 |  |  |  |
| `128940` | 한미약품 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-20 |  |  |  |
| `139130` | iM금융지주 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-20 |  |  |  |
| `161390` | 한국타이어앤테크놀로지 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-20 |  |  |  |
| `204320` | HL만도 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-20 |  |  |  |
| `241560` | 두산밥캣 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-20 |  |  |  |
| `295310` | 에이치브이엠 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_SWING_GAP` | 0 | 2026-05-20 |  |  |  |
| `336260` | 두산퓨얼셀 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-20 |  |  |  |
| `353200` | 대덕전자 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-20 |  |  |  |
| `402340` | SK스퀘어 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-20 |  |  |  |
