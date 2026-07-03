# Scalp Sim Overnight 2026-07-03

- generated_at: `2026-07-03T20:11:44`
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
| 2026-07-03T15:10:05.598961 | `scalp_sim_overnight_decision` | 실리콘투(257720) | `SELL_TODAY` | 99 | -0.23 | - | 8883 |
| 2026-07-03T15:10:05.599873 | `scalp_sim_overnight_sell_today` | 실리콘투(257720) | `SELL_TODAY` | 99 | -0.23 | -0.23 | 8883 |
| 2026-07-03T15:10:05.600343 | `scalp_sim_sell_order_assumed_filled` | 실리콘투(257720) | `-` | - | - | -0.23 | - |
| 2026-07-03T15:10:07.226506 | `scalp_sim_overnight_decision` | 지엔씨에너지(119850) | `SELL_TODAY` | 96 | -1.2914 | - | 8886 |
| 2026-07-03T15:10:07.226870 | `scalp_sim_overnight_sell_today` | 지엔씨에너지(119850) | `SELL_TODAY` | 96 | -1.2914 | -1.29 | 8886 |
| 2026-07-03T15:10:07.227049 | `scalp_sim_sell_order_assumed_filled` | 지엔씨에너지(119850) | `-` | - | - | -1.29 | - |
| 2026-07-03T15:10:08.841032 | `scalp_sim_overnight_decision` | BNK금융지주(138930) | `SELL_TODAY` | 96 | 1.058 | - | 8802 |
| 2026-07-03T15:10:08.841376 | `scalp_sim_overnight_sell_today` | BNK금융지주(138930) | `SELL_TODAY` | 96 | 1.058 | +1.06 | 8802 |
| 2026-07-03T15:10:08.841539 | `scalp_sim_sell_order_assumed_filled` | BNK금융지주(138930) | `-` | - | - | +1.06 | - |
| 2026-07-03T15:10:10.604660 | `scalp_sim_overnight_decision` | 미래에셋증권(006800) | `SELL_TODAY` | 98 | 0.0056 | - | 4937 |
| 2026-07-03T15:10:10.605008 | `scalp_sim_overnight_sell_today` | 미래에셋증권(006800) | `SELL_TODAY` | 98 | 0.0056 | +0.01 | 4937 |
| 2026-07-03T15:10:10.605176 | `scalp_sim_sell_order_assumed_filled` | 미래에셋증권(006800) | `-` | - | - | +0.01 | - |
