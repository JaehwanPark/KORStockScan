# Scalp Sim Overnight 2026-07-14

- generated_at: `2026-07-14T20:21:56`
- artifact_role: `postclose_source_packet_for_scalp_sim_overnight_ai_carry`
- runtime_effect: `false`
- decision_authority: `sim_observation_only`
- decision_target: `1`
- sell_today: `1`
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

- `scalp_sim_overnight_decision`: `1`
- `scalp_sim_overnight_sell_today`: `1`
- `scalp_sim_sell_order_assumed_filled`: `1`

## Rows

| time | stage | stock | action | confidence | profit/live | sell_profit | held_sec |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| 2026-07-14T15:10:04.562845 | `scalp_sim_overnight_decision` | 코웨이(021240) | `SELL_TODAY` | 96 | -1.2747 | - | 1434 |
| 2026-07-14T15:10:04.563243 | `scalp_sim_overnight_sell_today` | 코웨이(021240) | `SELL_TODAY` | 96 | -1.2747 | -1.27 | 1434 |
| 2026-07-14T15:10:04.563440 | `scalp_sim_sell_order_assumed_filled` | 코웨이(021240) | `-` | - | - | -1.27 | - |
