# Scalp Sim Overnight 2026-07-09

- generated_at: `2026-07-09T20:11:39`
- artifact_role: `postclose_source_packet_for_scalp_sim_overnight_ai_carry`
- runtime_effect: `false`
- decision_authority: `sim_observation_only`
- decision_target: `2`
- sell_today: `2`
- hold_overnight: `0`
- carry_open_count: `0`
- active_eligible_before_report: `0`
- active_undecided_count: `0`
- decision_coverage_rate: `1.0`
- source_quality_status: `pass`
- source_quality_warnings: `[]`
- ai_failure_fallback: `1`
- ai_timeout_fallback: `1`
- ai_engine_disabled_fallback: `0`

## Stage Counts

- `scalp_sim_overnight_decision`: `2`
- `scalp_sim_overnight_sell_today`: `2`
- `scalp_sim_sell_order_assumed_filled`: `2`

## Rows

| time | stage | stock | action | confidence | profit/live | sell_profit | held_sec |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| 2026-07-09T15:10:04.489877 | `scalp_sim_overnight_decision` | 비에이치(090460) | `SELL_TODAY` | 96 | -1.3831 | - | 6663 |
| 2026-07-09T15:10:04.490356 | `scalp_sim_overnight_sell_today` | 비에이치(090460) | `SELL_TODAY` | 96 | -1.3831 | -1.38 | 6663 |
| 2026-07-09T15:10:04.490542 | `scalp_sim_sell_order_assumed_filled` | 비에이치(090460) | `-` | - | - | -1.38 | - |
| 2026-07-09T15:10:16.513018 | `scalp_sim_overnight_decision` | 티엘비(356860) | `SELL_TODAY` | 0 | -1.5332 | - | 5137 |
| 2026-07-09T15:10:16.513296 | `scalp_sim_overnight_sell_today` | 티엘비(356860) | `SELL_TODAY` | 0 | -1.5332 | -1.53 | 5137 |
| 2026-07-09T15:10:16.513468 | `scalp_sim_sell_order_assumed_filled` | 티엘비(356860) | `-` | - | - | -1.53 | - |
