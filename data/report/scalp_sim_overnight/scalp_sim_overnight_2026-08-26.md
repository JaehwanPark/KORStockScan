# Scalp Sim Overnight 2026-08-26

- generated_at: `2026-08-26T21:07:31`
- artifact_role: `postclose_source_packet_for_scalp_sim_overnight_ai_carry`
- runtime_effect: `false`
- decision_authority: `sim_observation_only`
- decision_target: `3`
- sell_today: `3`
- hold_overnight: `0`
- carry_open_count: `0`
- active_eligible_before_report: `2`
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
| 2026-08-26T15:10:05.904649 | `scalp_sim_overnight_decision` | 일진전기(103590) | `SELL_TODAY` | 98 | 0.0575 | - | 11553 |
| 2026-08-26T15:10:05.905054 | `scalp_sim_overnight_sell_today` | 일진전기(103590) | `SELL_TODAY` | 98 | 0.0575 | +0.06 | 11553 |
| 2026-08-26T15:10:05.905285 | `scalp_sim_sell_order_assumed_filled` | 일진전기(103590) | `-` | - | - | +0.06 | - |
| 2026-08-26T15:10:07.455372 | `scalp_sim_overnight_decision` | 태광(023160) | `SELL_TODAY` | 96 | -2.6149 | - | 5412 |
| 2026-08-26T15:10:07.455697 | `scalp_sim_overnight_sell_today` | 태광(023160) | `SELL_TODAY` | 96 | -2.6149 | -2.61 | 5412 |
| 2026-08-26T15:10:07.455914 | `scalp_sim_sell_order_assumed_filled` | 태광(023160) | `-` | - | - | -2.61 | - |
| 2026-08-26T15:10:09.078119 | `scalp_sim_overnight_decision` | 한전산업(130660) | `SELL_TODAY` | 96 | -0.3806 | - | 2360 |
| 2026-08-26T15:10:09.078550 | `scalp_sim_overnight_sell_today` | 한전산업(130660) | `SELL_TODAY` | 96 | -0.3806 | -0.38 | 2360 |
| 2026-08-26T15:10:09.078838 | `scalp_sim_sell_order_assumed_filled` | 한전산업(130660) | `-` | - | - | -0.38 | - |
