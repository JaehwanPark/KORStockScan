# Scalp Sim Overnight 2026-06-29

- generated_at: `2026-06-29T20:10:54`
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
| 2026-06-29T15:10:04.776215 | `scalp_sim_overnight_decision` | RELIEF(555555) | `SELL_TODAY` | 97 | -0.23 | - | 7430 |
| 2026-06-29T15:10:04.776643 | `scalp_sim_overnight_sell_today` | RELIEF(555555) | `SELL_TODAY` | 97 | -0.23 | -0.23 | 7430 |
| 2026-06-29T15:10:04.776861 | `scalp_sim_sell_order_assumed_filled` | RELIEF(555555) | `-` | - | - | -0.23 | - |
| 2026-06-29T15:10:06.794827 | `scalp_sim_overnight_decision` | 삼성E&A(028050) | `SELL_TODAY` | 98 | -1.7857 | - | 7382 |
| 2026-06-29T15:10:06.795242 | `scalp_sim_overnight_sell_today` | 삼성E&A(028050) | `SELL_TODAY` | 98 | -1.7857 | -1.79 | 7382 |
| 2026-06-29T15:10:06.795420 | `scalp_sim_sell_order_assumed_filled` | 삼성E&A(028050) | `-` | - | - | -1.79 | - |
| 2026-06-29T15:10:10.361965 | `scalp_sim_overnight_decision` | 한올바이오파마(009420) | `SELL_TODAY` | 96 | -0.3752 | - | 4976 |
| 2026-06-29T15:10:10.362409 | `scalp_sim_overnight_sell_today` | 한올바이오파마(009420) | `SELL_TODAY` | 96 | -0.3752 | -0.38 | 4976 |
| 2026-06-29T15:10:10.362660 | `scalp_sim_sell_order_assumed_filled` | 한올바이오파마(009420) | `-` | - | - | -0.38 | - |
| 2026-06-29T15:10:12.073139 | `scalp_sim_overnight_decision` | 성신양회(004980) | `SELL_TODAY` | 98 | 1.1654 | - | 3254 |
| 2026-06-29T15:10:12.073527 | `scalp_sim_overnight_sell_today` | 성신양회(004980) | `SELL_TODAY` | 98 | 1.1654 | +1.17 | 3254 |
| 2026-06-29T15:10:12.073718 | `scalp_sim_sell_order_assumed_filled` | 성신양회(004980) | `-` | - | - | +1.17 | - |
