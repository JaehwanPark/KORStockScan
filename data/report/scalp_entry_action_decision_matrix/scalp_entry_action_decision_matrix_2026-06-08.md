# Scalp Entry Action Decision Matrix - 2026-06-08

## Contract
- status: `warning`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `338`
- joined_sample/sample_floor: `158` / `20`
- prompt_applied_count: `119`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 338}`
- forced_action_counts: `{'-': 338}`
- action_counts: `{'WAIT_REQUOTE': 15, 'NO_BUY_AI': 160, 'SKIP_PRE_SUBMIT_SAFETY': 121, 'SKIP_SOURCE_QUALITY': 12, 'BUY_DEFENSIVE': 28, 'BUY_NOW': 2}`
- missing_actions: `[]`
- zero_sample_actions: `['SKIP_STALE']`
- unknown_bucket_affected_rows: `219`
- unknown_dimension_occurrence_count: `388`
- unknown_bucket_not_available_rows: `219`
- not_available_dimension_occurrence_count: `330`
- unknown_bucket_dimension_counts: `{'price_resolution_bucket': 70, 'score_bucket': 159, 'risk_context_bucket': 159}`
- unknown_bucket_not_available_dimension_counts: `{'liquidity_bucket': 98, 'stale_bucket': 187, 'overbought_bucket': 45}`
- adm_source_bucket_used_count: `119`
- recomputed_unknown_count: `1314`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 2 | 0 | 0.0 | None | 0 | 0 |
| `WAIT_REQUOTE` | 15 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 0 | 0 | None | None | 0 | 0 |
| `BUY_DEFENSIVE` | 28 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 160 | 53 | -0.289 | -0.8726 | 20 | 37 |
| `SKIP_SOURCE_QUALITY` | 12 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 121 | 105 | -0.9459 | -1.09 | 65 | 74 |

## Top Buckets
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_0900_1000` sample=`36` joined=`12` action=`NO_BUY_AI` sq_ev=`-0.1239`
- `score_unknown|risk_unknown|-|stale_not_available|resolved_price|below_min_liquidity|overbought_ok|time_0900_1000` sample=`23` joined=`23` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-1.5687`
- `score_unknown|risk_unknown|-|stale_not_available|defensive_limit|below_min_liquidity|overbought_ok|time_1000_1200` sample=`22` joined=`21` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-0.1218`
- `score_unknown|risk_unknown|-|stale_not_available|defensive_limit|below_min_liquidity|overbought_ok|time_1200_1400` sample=`16` joined=`14` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-2.3818`
- `score50_64|weak_strength_momentum|-|stale_block|price_unknown|liquidity_not_available|overbought_normal|time_0900_1000` sample=`14` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_0900_1000` sample=`13` joined=`9` action=`NO_BUY_AI` sq_ev=`0.3877`
- `score_unknown|risk_unknown|-|stale_not_available|defensive_limit|liquidity_not_available|overbought_not_available|time_1000_1200` sample=`13` joined=`0` action=`BUY_DEFENSIVE` sq_ev=`0.0`
- `score_unknown|risk_unknown|-|stale_not_available|defensive_limit|below_min_liquidity|overbought_ok|time_0900_1000` sample=`11` joined=`11` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`0.7018`
- `score_unknown|risk_unknown|-|stale_not_available|price_unknown|liquidity_not_available|overbought_not_available|time_1400_close` sample=`10` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1200_1400` sample=`9` joined=`7` action=`NO_BUY_AI` sq_ev=`-1.6933`

## Warnings
- `unknown_bucket_source_quality_gap`
