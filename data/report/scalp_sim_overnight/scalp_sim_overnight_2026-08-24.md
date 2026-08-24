# Scalp Sim Overnight 2026-08-24

- generated_at: `2026-08-24T21:04:31`
- artifact_role: `postclose_source_packet_for_scalp_sim_overnight_ai_carry`
- runtime_effect: `false`
- decision_authority: `sim_observation_only`
- decision_target: `3`
- sell_today: `3`
- hold_overnight: `0`
- carry_open_count: `0`
- active_eligible_before_report: `1`
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
| 2026-08-24T15:10:06.825064 | `scalp_sim_overnight_decision` | 엘앤에프(066970) | `SELL_TODAY` | 96 | -1.0037 | - | 1697 |
| 2026-08-24T15:10:06.825402 | `scalp_sim_overnight_sell_today` | 엘앤에프(066970) | `SELL_TODAY` | 96 | -1.0037 | -1.00 | 1697 |
| 2026-08-24T15:10:06.825577 | `scalp_sim_sell_order_assumed_filled` | 엘앤에프(066970) | `-` | - | - | -1.00 | - |
| 2026-08-24T15:10:08.007031 | `scalp_sim_overnight_decision` | 솔트룩스(304100) | `SELL_TODAY` | 99 | -1.9326 | - | 1222 |
| 2026-08-24T15:10:08.007312 | `scalp_sim_overnight_sell_today` | 솔트룩스(304100) | `SELL_TODAY` | 99 | -1.9326 | -1.93 | 1222 |
| 2026-08-24T15:10:08.007486 | `scalp_sim_sell_order_assumed_filled` | 솔트룩스(304100) | `-` | - | - | -1.93 | - |
| 2026-08-24T15:10:09.562149 | `scalp_sim_overnight_decision` | 솔브레인홀딩스(036830) | `SELL_TODAY` | 96 | -1.6792 | - | 1032 |
| 2026-08-24T15:10:09.562462 | `scalp_sim_overnight_sell_today` | 솔브레인홀딩스(036830) | `SELL_TODAY` | 96 | -1.6792 | -1.68 | 1032 |
| 2026-08-24T15:10:09.562626 | `scalp_sim_sell_order_assumed_filled` | 솔브레인홀딩스(036830) | `-` | - | - | -1.68 | - |
