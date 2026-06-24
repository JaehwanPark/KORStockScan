# Scalp Sim Overnight 2026-06-24

- generated_at: `2026-06-24T20:10:58`
- artifact_role: `postclose_source_packet_for_scalp_sim_overnight_ai_carry`
- runtime_effect: `false`
- decision_authority: `sim_observation_only`
- decision_target: `4`
- sell_today: `4`
- hold_overnight: `0`
- carry_open_count: `0`
- active_eligible_before_report: `3`
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
| 2026-06-24T15:10:04.859118 | `scalp_sim_overnight_decision` | 알테오젠(196170) | `SELL_TODAY` | 99 | -0.7642 | - | 191 |
| 2026-06-24T15:10:04.859501 | `scalp_sim_overnight_sell_today` | 알테오젠(196170) | `SELL_TODAY` | 99 | -0.7642 | -0.76 | 191 |
| 2026-06-24T15:10:04.859685 | `scalp_sim_sell_order_assumed_filled` | 알테오젠(196170) | `-` | - | - | -0.76 | - |
| 2026-06-24T15:10:06.237177 | `scalp_sim_overnight_decision` | 펩트론(087010) | `SELL_TODAY` | 96 | -1.1391 | - | 193 |
| 2026-06-24T15:10:06.237506 | `scalp_sim_overnight_sell_today` | 펩트론(087010) | `SELL_TODAY` | 96 | -1.1391 | -1.14 | 193 |
| 2026-06-24T15:10:06.237662 | `scalp_sim_sell_order_assumed_filled` | 펩트론(087010) | `-` | - | - | -1.14 | - |
| 2026-06-24T15:10:07.757494 | `scalp_sim_overnight_decision` | 소룩스(290690) | `SELL_TODAY` | 98 | -0.9253 | - | 142 |
| 2026-06-24T15:10:07.757834 | `scalp_sim_overnight_sell_today` | 소룩스(290690) | `SELL_TODAY` | 98 | -0.9253 | -0.93 | 142 |
| 2026-06-24T15:10:07.757998 | `scalp_sim_sell_order_assumed_filled` | 소룩스(290690) | `-` | - | - | -0.93 | - |
| 2026-06-24T15:10:08.971998 | `scalp_sim_overnight_decision` | 리가켐바이오(141080) | `SELL_TODAY` | 99 | -0.4896 | - | 144 |
| 2026-06-24T15:10:08.972350 | `scalp_sim_overnight_sell_today` | 리가켐바이오(141080) | `SELL_TODAY` | 99 | -0.4896 | -0.49 | 144 |
| 2026-06-24T15:10:08.972521 | `scalp_sim_sell_order_assumed_filled` | 리가켐바이오(141080) | `-` | - | - | -0.49 | - |
