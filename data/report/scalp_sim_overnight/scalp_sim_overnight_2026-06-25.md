# Scalp Sim Overnight 2026-06-25

- generated_at: `2026-06-25T21:24:04`
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
| 2026-06-25T15:10:05.107310 | `scalp_sim_overnight_decision` | 대한항공(003490) | `SELL_TODAY` | 98 | -0.7408 | - | 7341 |
| 2026-06-25T15:10:05.107744 | `scalp_sim_overnight_sell_today` | 대한항공(003490) | `SELL_TODAY` | 98 | -0.7408 | -0.74 | 7341 |
| 2026-06-25T15:10:05.107957 | `scalp_sim_sell_order_assumed_filled` | 대한항공(003490) | `-` | - | - | -0.74 | - |
| 2026-06-25T15:10:06.692481 | `scalp_sim_overnight_decision` | SK(034730) | `SELL_TODAY` | 99 | -0.1148 | - | 2608 |
| 2026-06-25T15:10:06.692868 | `scalp_sim_overnight_sell_today` | SK(034730) | `SELL_TODAY` | 99 | -0.1148 | -0.11 | 2608 |
| 2026-06-25T15:10:06.693046 | `scalp_sim_sell_order_assumed_filled` | SK(034730) | `-` | - | - | -0.11 | - |
| 2026-06-25T15:10:08.152478 | `scalp_sim_overnight_decision` | 이노테크(469610) | `SELL_TODAY` | 98 | -0.8899 | - | 2331 |
| 2026-06-25T15:10:08.152863 | `scalp_sim_overnight_sell_today` | 이노테크(469610) | `SELL_TODAY` | 98 | -0.8899 | -0.89 | 2331 |
| 2026-06-25T15:10:08.153050 | `scalp_sim_sell_order_assumed_filled` | 이노테크(469610) | `-` | - | - | -0.89 | - |
| 2026-06-25T15:10:09.664696 | `scalp_sim_overnight_decision` | SK네트웍스(001740) | `SELL_TODAY` | 97 | -0.3217 | - | 363 |
| 2026-06-25T15:10:09.665086 | `scalp_sim_overnight_sell_today` | SK네트웍스(001740) | `SELL_TODAY` | 97 | -0.3217 | -0.32 | 363 |
| 2026-06-25T15:10:09.665259 | `scalp_sim_sell_order_assumed_filled` | SK네트웍스(001740) | `-` | - | - | -0.32 | - |
