# Scalp Sim Overnight 2026-09-02

- generated_at: `2026-09-02T21:22:24`
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
| 2026-09-02T15:10:07.488883 | `scalp_sim_overnight_decision` | ISC(095340) | `SELL_TODAY` | 97 | -1.7853 | - | 5777 |
| 2026-09-02T15:10:07.489398 | `scalp_sim_overnight_sell_today` | ISC(095340) | `SELL_TODAY` | 97 | -1.7853 | -1.79 | 5777 |
| 2026-09-02T15:10:07.489703 | `scalp_sim_sell_order_assumed_filled` | ISC(095340) | `-` | - | - | -1.79 | - |
| 2026-09-02T15:10:08.782423 | `scalp_sim_overnight_decision` | 흥구석유(024060) | `SELL_TODAY` | 99 | -1.017 | - | 5291 |
| 2026-09-02T15:10:08.782759 | `scalp_sim_overnight_sell_today` | 흥구석유(024060) | `SELL_TODAY` | 99 | -1.017 | -1.02 | 5291 |
| 2026-09-02T15:10:08.782960 | `scalp_sim_sell_order_assumed_filled` | 흥구석유(024060) | `-` | - | - | -1.02 | - |
