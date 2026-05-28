# Swing Daily Simulation - 2026-05-28

- runtime_change: `False`
- recommendation_rows: `19` / live `19` / diagnostic `0`
- recommendation_sources: `{'recommendation_history': 16, 'daily_recommendations_v2_csv': 3}`
- db_recommendation_rows: `16`
- source_signal_dates: `['2026-05-27', '2026-05-28']`
- simulated_count: `19`
- closed_count: `0`
- planned_or_open_count: `19`
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
| `gap_pass` | 19 | 0 | 0.00% | 0.00% | `{'PENDING_ENTRY': 19}` |
| `gatekeeper_pass` | 19 | 0 | 0.00% | 0.00% | `{'PENDING_ENTRY': 19}` |
| `selection_only` | 19 | 0 | 0.00% | 0.00% | `{'PENDING_ENTRY': 19}` |

## Runtime Entry Funnel

- source: `/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-05-28.jsonl`

| stage | raw | unique_records | examples |
| --- | ---: | ---: | --- |
| `blocked_gatekeeper_reject` | 3964 | 10 | iM금융지주(139130), 삼성생명(032830), LG(003550), KT&G(033780), 현대위아(011210) |
| `blocked_swing_gap` | 1105 | 4 | HL만도(204320), 현대위아(011210), LG디스플레이(034220), 현대위아(011210), LG디스플레이(034220) |
| `swing_sim_buy_order_assumed_filled` | 10 | 5 | 한화오션(042660), KT&G(033780), LG디스플레이(034220), LG(003550), iM금융지주(139130) |
| `swing_sim_holding_started` | 10 | 5 | 한화오션(042660), KT&G(033780), LG디스플레이(034220), LG(003550), iM금융지주(139130) |
| `swing_sim_order_bundle_assumed_filled` | 10 | 5 | 한화오션(042660), KT&G(033780), LG디스플레이(034220), LG(003550), iM금융지주(139130) |

## Simulated Trades

| code | name | source | status | guard | qty | entry | exit | net_ret | reason |
| --- | --- | --- | --- | --- | ---: | --- | --- | ---: | --- |
| `001440` | 대한전선 | `daily_recommendations_v2_csv` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `001450` | 현대해상 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `003490` | 대한항공 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `003550` | LG | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `005850` | 에스엘 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `006280` | 녹십자 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `006280` | 녹십자 | `daily_recommendations_v2_csv` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `011210` | 현대위아 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `018260` | 삼성에스디에스 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `028260` | 삼성물산 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `032830` | 삼성생명 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `033780` | KT&G | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `034220` | LG디스플레이 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `042660` | 한화오션 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `068270` | 셀트리온 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `139130` | iM금융지주 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `161390` | 한국타이어앤테크놀로지 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `192650` | 드림텍 | `daily_recommendations_v2_csv` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
| `204320` | HL만도 | `recommendation_history` | `PENDING_ENTRY` | `WAITING_FOR_NEXT_SESSION_QUOTE` | 0 |  |  |  |  |
