# Scalp Sim Overnight 2026-08-25

- generated_at: `2026-08-25T21:05:15`
- artifact_role: `postclose_source_packet_for_scalp_sim_overnight_ai_carry`
- runtime_effect: `false`
- decision_authority: `sim_observation_only`
- decision_target: `2`
- sell_today: `2`
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

- `scalp_sim_overnight_decision`: `2`
- `scalp_sim_overnight_sell_today`: `2`
- `scalp_sim_sell_order_assumed_filled`: `2`

## Rows

| time | stage | stock | action | confidence | profit/live | sell_profit | held_sec |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| 2026-08-25T15:10:07.034581 | `scalp_sim_overnight_decision` | 미코(059090) | `SELL_TODAY` | 97 | -0.5334 | - | 591 |
| 2026-08-25T15:10:07.034927 | `scalp_sim_overnight_sell_today` | 미코(059090) | `SELL_TODAY` | 97 | -0.5334 | -0.53 | 591 |
| 2026-08-25T15:10:07.035304 | `scalp_sim_sell_order_assumed_filled` | 미코(059090) | `-` | - | - | -0.53 | - |
| 2026-08-25T15:10:09.616522 | `scalp_sim_overnight_decision` | 티엘비(356860) | `SELL_TODAY` | 98 | -1.1277 | - | 98 |
| 2026-08-25T15:10:09.616817 | `scalp_sim_overnight_sell_today` | 티엘비(356860) | `SELL_TODAY` | 98 | -1.1277 | -1.13 | 98 |
| 2026-08-25T15:10:09.617130 | `scalp_sim_sell_order_assumed_filled` | 티엘비(356860) | `-` | - | - | -1.13 | - |
