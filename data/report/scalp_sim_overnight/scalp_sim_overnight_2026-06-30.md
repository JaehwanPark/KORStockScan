# Scalp Sim Overnight 2026-06-30

- generated_at: `2026-06-30T20:10:35`
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
| 2026-06-30T15:10:06.582172 | `scalp_sim_overnight_decision` | 후성(093370) | `SELL_TODAY` | 97 | -0.4295 | - | 5253 |
| 2026-06-30T15:10:06.582596 | `scalp_sim_overnight_sell_today` | 후성(093370) | `SELL_TODAY` | 97 | -0.4295 | -0.43 | 5253 |
| 2026-06-30T15:10:06.582771 | `scalp_sim_sell_order_assumed_filled` | 후성(093370) | `-` | - | - | -0.43 | - |
| 2026-06-30T15:10:09.377220 | `scalp_sim_overnight_decision` | 제주반도체(080220) | `SELL_TODAY` | 96 | -0.1343 | - | 5008 |
| 2026-06-30T15:10:09.377595 | `scalp_sim_overnight_sell_today` | 제주반도체(080220) | `SELL_TODAY` | 96 | -0.1343 | -0.13 | 5008 |
| 2026-06-30T15:10:09.377776 | `scalp_sim_sell_order_assumed_filled` | 제주반도체(080220) | `-` | - | - | -0.13 | - |
| 2026-06-30T15:10:10.560592 | `scalp_sim_overnight_decision` | SK스퀘어(402340) | `SELL_TODAY` | 96 | 1.1018 | - | 3290 |
| 2026-06-30T15:10:10.560973 | `scalp_sim_overnight_sell_today` | SK스퀘어(402340) | `SELL_TODAY` | 96 | 1.1018 | +1.10 | 3290 |
| 2026-06-30T15:10:10.561143 | `scalp_sim_sell_order_assumed_filled` | SK스퀘어(402340) | `-` | - | - | +1.10 | - |
| 2026-06-30T15:10:11.747818 | `scalp_sim_overnight_decision` | 삼성E&A(028050) | `SELL_TODAY` | 96 | -1.6789 | - | 1680 |
| 2026-06-30T15:10:11.748209 | `scalp_sim_overnight_sell_today` | 삼성E&A(028050) | `SELL_TODAY` | 96 | -1.6789 | -1.68 | 1680 |
| 2026-06-30T15:10:11.748372 | `scalp_sim_sell_order_assumed_filled` | 삼성E&A(028050) | `-` | - | - | -1.68 | - |
