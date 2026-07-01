# Scalp Sim Overnight 2026-07-01

- generated_at: `2026-07-01T20:10:58`
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
| 2026-07-01T15:10:06.609091 | `scalp_sim_overnight_decision` | 티에스이(131290) | `SELL_TODAY` | 98 | -1.6527 | - | 1454 |
| 2026-07-01T15:10:06.609609 | `scalp_sim_overnight_sell_today` | 티에스이(131290) | `SELL_TODAY` | 98 | -1.6527 | -1.65 | 1454 |
| 2026-07-01T15:10:06.609833 | `scalp_sim_sell_order_assumed_filled` | 티에스이(131290) | `-` | - | - | -1.65 | - |
| 2026-07-01T15:10:08.798870 | `scalp_sim_overnight_decision` | 삼일씨엔에스(004440) | `SELL_TODAY` | 98 | -1.5445 | - | 1458 |
| 2026-07-01T15:10:08.799269 | `scalp_sim_overnight_sell_today` | 삼일씨엔에스(004440) | `SELL_TODAY` | 98 | -1.5445 | -1.54 | 1458 |
| 2026-07-01T15:10:08.799538 | `scalp_sim_sell_order_assumed_filled` | 삼일씨엔에스(004440) | `-` | - | - | -1.54 | - |
| 2026-07-01T15:10:10.124383 | `scalp_sim_overnight_decision` | SK이터닉스(475150) | `SELL_TODAY` | 98 | -2.3424 | - | 1460 |
| 2026-07-01T15:10:10.124721 | `scalp_sim_overnight_sell_today` | SK이터닉스(475150) | `SELL_TODAY` | 98 | -2.3424 | -2.34 | 1460 |
| 2026-07-01T15:10:10.124880 | `scalp_sim_sell_order_assumed_filled` | SK이터닉스(475150) | `-` | - | - | -2.34 | - |
| 2026-07-01T15:10:11.801245 | `scalp_sim_overnight_decision` | 주성엔지니어링(036930) | `SELL_TODAY` | 99 | -1.0512 | - | 226 |
| 2026-07-01T15:10:11.801571 | `scalp_sim_overnight_sell_today` | 주성엔지니어링(036930) | `SELL_TODAY` | 99 | -1.0512 | -1.05 | 226 |
| 2026-07-01T15:10:11.801735 | `scalp_sim_sell_order_assumed_filled` | 주성엔지니어링(036930) | `-` | - | - | -1.05 | - |
