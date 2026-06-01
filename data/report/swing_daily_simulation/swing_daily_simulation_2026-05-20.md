# Swing Daily Simulation - 2026-05-20

- runtime_change: `False`
- recommendation_rows: `22` / live `22` / diagnostic `0`
- recommendation_sources: `{'recommendation_history': 22}`
- db_recommendation_rows: `22`
- source_signal_dates: `['2026-05-20']`
- simulated_count: `22`
- closed_count: `0`
- planned_or_open_count: `22`
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
| `gap_pass` | 22 | 0 | 0.00% | 0.00% | `{'PLANNED_ENTRY': 22}` |
| `gatekeeper_pass` | 22 | 0 | 0.00% | 0.00% | `{'PLANNED_ENTRY': 22}` |
| `selection_only` | 22 | 0 | 0.00% | 0.00% | `{'PLANNED_ENTRY': 22}` |

## Runtime Entry Funnel

- source: `/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-05-20.jsonl.gz`

| stage | raw | unique_records | examples |
| --- | ---: | ---: | --- |
| `blocked_swing_gap` | 416 | 1 | 현대모비스(012330), 현대모비스(012330), 현대모비스(012330), 현대모비스(012330), 현대모비스(012330) |
| `blocked_gatekeeper_reject` | 87 | 9 | 한국타이어앤테크놀로지(161390), HL만도(204320), SK텔레콤(017670), 현대지에프홀딩스(005440), LG유플러스(032640) |

## Simulated Trades

| code | name | source | status | guard | qty | entry | exit | net_ret | reason |
| --- | --- | --- | --- | --- | ---: | --- | --- | ---: | --- |
| `000240` | 한국앤컴퍼니 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-22 |  |  |  |
| `001450` | 현대해상 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-22 |  |  |  |
| `003490` | 대한항공 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_SWING_GAP` | 0 | 2026-05-22 |  |  |  |
| `005440` | 현대지에프홀딩스 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-22 |  |  |  |
| `011200` | HMM | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-22 |  |  |  |
| `011210` | 현대위아 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_SWING_GAP` | 0 | 2026-05-22 |  |  |  |
| `012330` | 현대모비스 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_SWING_GAP` | 0 | 2026-05-22 |  |  |  |
| `017670` | SK텔레콤 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_SWING_GAP` | 0 | 2026-05-22 |  |  |  |
| `028670` | 팬오션 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-22 |  |  |  |
| `032640` | LG유플러스 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_SWING_GAP` | 0 | 2026-05-22 |  |  |  |
| `034220` | LG디스플레이 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_SWING_GAP` | 0 | 2026-05-22 |  |  |  |
| `035250` | 강원랜드 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-22 |  |  |  |
| `036460` | 한국가스공사 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-22 |  |  |  |
| `078930` | GS | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-22 |  |  |  |
| `086280` | 현대글로비스 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_SWING_GAP` | 0 | 2026-05-22 |  |  |  |
| `105560` | KB금융 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-22 |  |  |  |
| `138930` | BNK금융지주 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-22 |  |  |  |
| `139130` | iM금융지주 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-22 |  |  |  |
| `161390` | 한국타이어앤테크놀로지 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_SWING_GAP` | 0 | 2026-05-22 |  |  |  |
| `204320` | HL만도 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_SWING_GAP` | 0 | 2026-05-22 |  |  |  |
| `352820` | 하이브 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-22 |  |  |  |
| `454910` | 두산로보틱스 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_SWING_GAP` | 0 | 2026-05-22 |  |  |  |
