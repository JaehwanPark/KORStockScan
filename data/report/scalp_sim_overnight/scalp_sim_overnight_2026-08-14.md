# Scalp Sim Overnight 2026-08-14

- generated_at: `2026-08-14T22:12:52`
- artifact_role: `postclose_source_packet_for_scalp_sim_overnight_ai_carry`
- runtime_effect: `false`
- decision_authority: `sim_observation_only`
- decision_target: `2`
- sell_today: `2`
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

- `scalp_sim_overnight_decision`: `2`
- `scalp_sim_overnight_sell_today`: `2`
- `scalp_sim_sell_order_assumed_filled`: `2`

## Rows

| time | stage | stock | action | confidence | profit/live | sell_profit | held_sec |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| 2026-08-14T15:10:05.561554 | `scalp_sim_overnight_decision` | 에이직랜드(445090) | `SELL_TODAY` | 99 | -2.3085 | - | 1265 |
| 2026-08-14T15:10:05.562164 | `scalp_sim_overnight_sell_today` | 에이직랜드(445090) | `SELL_TODAY` | 99 | -2.3085 | -2.31 | 1265 |
| 2026-08-14T15:10:05.562433 | `scalp_sim_sell_order_assumed_filled` | 에이직랜드(445090) | `-` | - | - | -2.31 | - |
| 2026-08-14T15:10:06.936579 | `scalp_sim_overnight_decision` | 네오오토(212560) | `SELL_TODAY` | 98 | -2.6482 | - | 886 |
| 2026-08-14T15:10:06.936911 | `scalp_sim_overnight_sell_today` | 네오오토(212560) | `SELL_TODAY` | 98 | -2.6482 | -2.65 | 886 |
| 2026-08-14T15:10:06.937148 | `scalp_sim_sell_order_assumed_filled` | 네오오토(212560) | `-` | - | - | -2.65 | - |
