# Scalp Sim Overnight 2026-07-07

- generated_at: `2026-07-07T20:11:29`
- artifact_role: `postclose_source_packet_for_scalp_sim_overnight_ai_carry`
- runtime_effect: `false`
- decision_authority: `sim_observation_only`
- decision_target: `4`
- sell_today: `4`
- hold_overnight: `0`
- carry_open_count: `0`
- active_eligible_before_report: `4`
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
| 2026-07-07T15:10:03.809575 | `scalp_sim_overnight_decision` | 디앤디파마텍(347850) | `SELL_TODAY` | 97 | -0.8128 | - | 2477 |
| 2026-07-07T15:10:03.810017 | `scalp_sim_overnight_sell_today` | 디앤디파마텍(347850) | `SELL_TODAY` | 97 | -0.8128 | -0.81 | 2477 |
| 2026-07-07T15:10:03.810200 | `scalp_sim_sell_order_assumed_filled` | 디앤디파마텍(347850) | `-` | - | - | -0.81 | - |
| 2026-07-07T15:10:05.117734 | `scalp_sim_overnight_decision` | 한국타이어앤테크놀로지(161390) | `SELL_TODAY` | 98 | -1.4517 | - | 2478 |
| 2026-07-07T15:10:05.118120 | `scalp_sim_overnight_sell_today` | 한국타이어앤테크놀로지(161390) | `SELL_TODAY` | 98 | -1.4517 | -1.45 | 2478 |
| 2026-07-07T15:10:05.118306 | `scalp_sim_sell_order_assumed_filled` | 한국타이어앤테크놀로지(161390) | `-` | - | - | -1.45 | - |
| 2026-07-07T15:10:06.693466 | `scalp_sim_overnight_decision` | 주성엔지니어링(036930) | `SELL_TODAY` | 99 | -0.23 | - | 1677 |
| 2026-07-07T15:10:06.693836 | `scalp_sim_overnight_sell_today` | 주성엔지니어링(036930) | `SELL_TODAY` | 99 | -0.23 | -0.23 | 1677 |
| 2026-07-07T15:10:06.694019 | `scalp_sim_sell_order_assumed_filled` | 주성엔지니어링(036930) | `-` | - | - | -0.23 | - |
| 2026-07-07T15:10:08.291880 | `scalp_sim_overnight_decision` | SK오션플랜트(100090) | `SELL_TODAY` | 96 | -0.367 | - | 1639 |
| 2026-07-07T15:10:08.292270 | `scalp_sim_overnight_sell_today` | SK오션플랜트(100090) | `SELL_TODAY` | 96 | -0.367 | -0.37 | 1639 |
| 2026-07-07T15:10:08.292454 | `scalp_sim_sell_order_assumed_filled` | SK오션플랜트(100090) | `-` | - | - | -0.37 | - |
