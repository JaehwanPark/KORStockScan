# Scalp Entry Action Decision Matrix - 2026-06-17

## Contract
- status: `pass`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `1666`
- joined_sample/sample_floor: `165` / `20`
- prompt_applied_count: `1204`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 1666}`
- forced_action_counts: `{'-': 1666}`
- action_counts: `{'WAIT_REQUOTE': 15, 'BUY_NOW': 11, 'NO_BUY_AI': 1489, 'SKIP_PRE_SUBMIT_SAFETY': 115, 'SKIP_SOURCE_QUALITY': 31, 'BUY_DEFENSIVE': 5}`
- missing_actions: `[]`
- zero_sample_actions: `['SKIP_STALE']`
- unknown_bucket_affected_rows: `24`
- unknown_dimension_occurrence_count: `40`
- unknown_bucket_not_available_rows: `462`
- not_available_dimension_occurrence_count: `1054`
- unknown_bucket_dimension_counts: `{'risk_context_bucket': 24, 'price_resolution_bucket': 16}`
- unknown_bucket_not_available_dimension_counts: `{'price_resolution_bucket': 322, 'liquidity_bucket': 344, 'overbought_bucket': 51, 'stale_bucket': 206, 'risk_context_bucket': 115, 'score_bucket': 16}`
- adm_source_bucket_used_count: `1204`
- recomputed_unknown_count: `4318`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 11 | 9 | 0.6191 | 0.7567 | 0 | 0 |
| `WAIT_REQUOTE` | 15 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 0 | 0 | None | None | 0 | 0 |
| `BUY_DEFENSIVE` | 5 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 1489 | 59 | -0.0468 | -1.1822 | 22 | 44 |
| `SKIP_SOURCE_QUALITY` | 31 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 115 | 97 | -1.0765 | -1.2763 | 47 | 77 |

## Top Buckets
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`366` joined=`14` action=`NO_BUY_AI` sq_ev=`-0.0467`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1200_1400` sample=`287` joined=`11` action=`NO_BUY_AI` sq_ev=`-0.0551`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_0900_1000` sample=`180` joined=`27` action=`NO_BUY_AI` sq_ev=`-0.1559`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1400_close` sample=`143` joined=`1` action=`NO_BUY_AI` sq_ev=`-0.015`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_0900_1000` sample=`36` joined=`3` action=`NO_BUY_AI` sq_ev=`0.2144`
- `score50_64|strong_strength_momentum|-|fresh|price_not_available_pre_submit|liquidity_not_available|overbought_normal|time_0900_1000` sample=`29` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|price_not_available_pre_submit|liquidity_not_available|overbought_normal|time_1000_1200` sample=`28` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|price_not_available_pre_submit|liquidity_not_available|overbought_normal|time_0900_1000` sample=`26` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|risk_context_not_available|-|stale_not_available|resolved_price|below_min_liquidity|overbought_ok|time_0900_1000` sample=`21` joined=`21` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-1.3667`
- `score50_64|strong_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1200_1400` sample=`21` joined=`1` action=`NO_BUY_AI` sq_ev=`-0.1224`
