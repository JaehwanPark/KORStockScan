# Scalp Sim Overnight 2026-07-08

- generated_at: `2026-07-08T21:29:21`
- artifact_role: `postclose_source_packet_for_scalp_sim_overnight_ai_carry`
- runtime_effect: `false`
- decision_authority: `sim_observation_only`
- decision_target: `4`
- sell_today: `4`
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

- `scalp_sim_overnight_decision`: `4`
- `scalp_sim_overnight_sell_today`: `4`
- `scalp_sim_sell_order_assumed_filled`: `4`

## Rows

| time | stage | stock | action | confidence | profit/live | sell_profit | held_sec |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| 2026-07-08T15:10:04.180134 | `scalp_sim_overnight_decision` | 금호타이어(073240) | `SELL_TODAY` | 96 | 0.0832 | - | 2841 |
| 2026-07-08T15:10:04.181160 | `scalp_sim_overnight_sell_today` | 금호타이어(073240) | `SELL_TODAY` | 96 | 0.0832 | +0.08 | 2841 |
| 2026-07-08T15:10:04.181428 | `scalp_sim_sell_order_assumed_filled` | 금호타이어(073240) | `-` | - | - | +0.08 | - |
| 2026-07-08T15:10:06.262775 | `scalp_sim_overnight_decision` | 기아(000270) | `SELL_TODAY` | 96 | -0.1006 | - | 2843 |
| 2026-07-08T15:10:06.263346 | `scalp_sim_overnight_sell_today` | 기아(000270) | `SELL_TODAY` | 96 | -0.1006 | -0.10 | 2843 |
| 2026-07-08T15:10:06.263598 | `scalp_sim_sell_order_assumed_filled` | 기아(000270) | `-` | - | - | -0.10 | - |
| 2026-07-08T15:10:07.671320 | `scalp_sim_overnight_decision` | 동국제약(086450) | `SELL_TODAY` | 96 | 1.2841 | - | 2586 |
| 2026-07-08T15:10:07.671746 | `scalp_sim_overnight_sell_today` | 동국제약(086450) | `SELL_TODAY` | 96 | 1.2841 | +1.28 | 2586 |
| 2026-07-08T15:10:07.671986 | `scalp_sim_sell_order_assumed_filled` | 동국제약(086450) | `-` | - | - | +1.28 | - |
| 2026-07-08T15:10:08.935171 | `scalp_sim_overnight_decision` | GST(083450) | `SELL_TODAY` | 96 | 0.2368 | - | 2073 |
| 2026-07-08T15:10:08.935521 | `scalp_sim_overnight_sell_today` | GST(083450) | `SELL_TODAY` | 96 | 0.2368 | +0.24 | 2073 |
| 2026-07-08T15:10:08.935718 | `scalp_sim_sell_order_assumed_filled` | GST(083450) | `-` | - | - | +0.24 | - |
