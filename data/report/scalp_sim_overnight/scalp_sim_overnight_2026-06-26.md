# Scalp Sim Overnight 2026-06-26

- generated_at: `2026-06-26T21:17:37`
- artifact_role: `postclose_source_packet_for_scalp_sim_overnight_ai_carry`
- runtime_effect: `false`
- decision_authority: `sim_observation_only`
- decision_target: `4`
- sell_today: `4`
- hold_overnight: `0`
- carry_open_count: `0`
- active_eligible_before_report: `1`
- active_undecided_count: `0`
- decision_coverage_rate: `1.0`
- source_quality_status: `pass`
- source_quality_warnings: `[]`
- ai_failure_fallback: `4`
- ai_timeout_fallback: `0`
- ai_engine_disabled_fallback: `0`

## Stage Counts

- `scalp_sim_overnight_decision`: `4`
- `scalp_sim_overnight_sell_today`: `4`
- `scalp_sim_sell_order_assumed_filled`: `4`

## Rows

| time | stage | stock | action | confidence | profit/live | sell_profit | held_sec |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| 2026-06-26T15:10:04.730879 | `scalp_sim_overnight_decision` | 브이엠(089970) | `SELL_TODAY` | 98 | 1.0064 | - | 3908 |
| 2026-06-26T15:10:04.731327 | `scalp_sim_overnight_sell_today` | 브이엠(089970) | `SELL_TODAY` | 98 | 1.0064 | +1.01 | 3908 |
| 2026-06-26T15:10:04.731515 | `scalp_sim_sell_order_assumed_filled` | 브이엠(089970) | `-` | - | - | +1.01 | - |
| 2026-06-26T15:10:06.420537 | `scalp_sim_overnight_decision` | 일신방직(003200) | `SELL_TODAY` | 96 | 6.4551 | - | 3038 |
| 2026-06-26T15:10:06.420928 | `scalp_sim_overnight_sell_today` | 일신방직(003200) | `SELL_TODAY` | 96 | 6.4551 | +6.46 | 3038 |
| 2026-06-26T15:10:06.421107 | `scalp_sim_sell_order_assumed_filled` | 일신방직(003200) | `-` | - | - | +6.46 | - |
| 2026-06-26T15:10:08.028769 | `scalp_sim_overnight_decision` | 주성엔지니어링(036930) | `SELL_TODAY` | 98 | -1.3002 | - | 2240 |
| 2026-06-26T15:10:08.029427 | `scalp_sim_overnight_sell_today` | 주성엔지니어링(036930) | `SELL_TODAY` | 98 | -1.3002 | -1.30 | 2240 |
| 2026-06-26T15:10:08.029624 | `scalp_sim_sell_order_assumed_filled` | 주성엔지니어링(036930) | `-` | - | - | -1.30 | - |
| 2026-06-26T15:10:09.808098 | `scalp_sim_overnight_decision` | 삼성에스디에스(018260) | `SELL_TODAY` | 96 | -0.7518 | - | 903 |
| 2026-06-26T15:10:09.808466 | `scalp_sim_overnight_sell_today` | 삼성에스디에스(018260) | `SELL_TODAY` | 96 | -0.7518 | -0.75 | 903 |
| 2026-06-26T15:10:09.808646 | `scalp_sim_sell_order_assumed_filled` | 삼성에스디에스(018260) | `-` | - | - | -0.75 | - |
