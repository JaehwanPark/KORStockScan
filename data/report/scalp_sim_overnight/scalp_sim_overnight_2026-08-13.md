# Scalp Sim Overnight 2026-08-13

- generated_at: `2026-08-13T20:59:09`
- artifact_role: `postclose_source_packet_for_scalp_sim_overnight_ai_carry`
- runtime_effect: `false`
- decision_authority: `sim_observation_only`
- decision_target: `3`
- sell_today: `3`
- hold_overnight: `0`
- carry_open_count: `0`
- active_eligible_before_report: `4`
- active_undecided_count: `0`
- decision_coverage_rate: `1.0`
- source_quality_status: `pass`
- source_quality_warnings: `[]`
- ai_failure_fallback: `0`
- ai_timeout_fallback: `0`
- ai_engine_disabled_fallback: `0`

## Stage Counts

- `scalp_sim_overnight_decision`: `3`
- `scalp_sim_overnight_sell_today`: `3`
- `scalp_sim_sell_order_assumed_filled`: `3`

## Rows

| time | stage | stock | action | confidence | profit/live | sell_profit | held_sec |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| 2026-08-13T15:10:06.175707 | `scalp_sim_overnight_decision` | 삼성전기(009150) | `SELL_TODAY` | 95 | -0.4941 | - | 31 |
| 2026-08-13T15:10:06.176004 | `scalp_sim_overnight_sell_today` | 삼성전기(009150) | `SELL_TODAY` | 95 | -0.4941 | -0.49 | 31 |
| 2026-08-13T15:10:06.176176 | `scalp_sim_sell_order_assumed_filled` | 삼성전기(009150) | `-` | - | - | -0.49 | - |
| 2026-08-13T15:10:07.695837 | `scalp_sim_overnight_decision` | 씨이랩(189330) | `SELL_TODAY` | 99 | -0.23 | - | 26 |
| 2026-08-13T15:10:07.696100 | `scalp_sim_overnight_sell_today` | 씨이랩(189330) | `SELL_TODAY` | 99 | -0.23 | -0.23 | 26 |
| 2026-08-13T15:10:07.696260 | `scalp_sim_sell_order_assumed_filled` | 씨이랩(189330) | `-` | - | - | -0.23 | - |
| 2026-08-13T15:10:08.834655 | `scalp_sim_overnight_decision` | 이노테크(469610) | `SELL_TODAY` | 99 | -0.23 | - | 21 |
| 2026-08-13T15:10:08.834904 | `scalp_sim_overnight_sell_today` | 이노테크(469610) | `SELL_TODAY` | 99 | -0.23 | -0.23 | 21 |
| 2026-08-13T15:10:08.835105 | `scalp_sim_sell_order_assumed_filled` | 이노테크(469610) | `-` | - | - | -0.23 | - |
