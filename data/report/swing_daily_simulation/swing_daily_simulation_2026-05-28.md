# Swing Daily Simulation - 2026-05-28

- runtime_change: `False`
- recommendation_rows: `16` / live `16` / diagnostic `0`
- recommendation_sources: `{'recommendation_history': 16}`
- db_recommendation_rows: `16`
- source_signal_dates: `['2026-05-28']`
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
| `gap_pass` | 16 | 0 | 0.00% | 0.00% | `{'PLANNED_ENTRY': 16}` |
| `gatekeeper_pass` | 16 | 0 | 0.00% | 0.00% | `{'PLANNED_ENTRY': 16}` |
| `selection_only` | 16 | 0 | 0.00% | 0.00% | `{'PLANNED_ENTRY': 16}` |

## Runtime Entry Funnel

- source: `/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-05-28.jsonl.gz`

| stage | raw | unique_records | examples |
| --- | ---: | ---: | --- |
| `blocked_gatekeeper_reject` | 5311 | 10 | iM금융지주(139130), 삼성생명(032830), LG(003550), KT&G(033780), 현대위아(011210) |
| `blocked_swing_gap` | 1491 | 4 | HL만도(204320), 현대위아(011210), LG디스플레이(034220), 현대위아(011210), LG디스플레이(034220) |
| `swing_sim_buy_order_assumed_filled` | 27 | 13 | 한화오션(042660), KT&G(033780), LG디스플레이(034220), LG(003550), iM금융지주(139130) |
| `swing_sim_holding_started` | 27 | 13 | 한화오션(042660), KT&G(033780), LG디스플레이(034220), LG(003550), iM금융지주(139130) |
| `swing_sim_order_bundle_assumed_filled` | 27 | 13 | 한화오션(042660), KT&G(033780), LG디스플레이(034220), LG(003550), iM금융지주(139130) |

## Simulated Trades

| code | name | source | status | guard | qty | entry | exit | net_ret | reason |
| --- | --- | --- | --- | --- | ---: | --- | --- | ---: | --- |
| `001450` | 현대해상 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-29 |  |  |  |
| `003490` | 대한항공 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-29 |  |  |  |
| `003550` | LG | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_SWING_GAP` | 0 | 2026-05-29 |  |  |  |
| `005850` | 에스엘 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_SWING_GAP` | 0 | 2026-05-29 |  |  |  |
| `006280` | 녹십자 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-29 |  |  |  |
| `011210` | 현대위아 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-29 |  |  |  |
| `018260` | 삼성에스디에스 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-29 |  |  |  |
| `028260` | 삼성물산 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-29 |  |  |  |
| `032830` | 삼성생명 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-29 |  |  |  |
| `033780` | KT&G | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-29 |  |  |  |
| `034220` | LG디스플레이 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_SWING_GAP` | 0 | 2026-05-29 |  |  |  |
| `042660` | 한화오션 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-29 |  |  |  |
| `068270` | 셀트리온 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-29 |  |  |  |
| `139130` | iM금융지주 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-29 |  |  |  |
| `161390` | 한국타이어앤테크놀로지 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-29 |  |  |  |
| `204320` | HL만도 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-29 |  |  |  |
