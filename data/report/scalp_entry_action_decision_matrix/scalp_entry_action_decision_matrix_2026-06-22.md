# Scalp Entry Action Decision Matrix - 2026-06-22

## Contract
- status: `warning`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `737`
- joined_sample/sample_floor: `97` / `20`
- prompt_applied_count: `531`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 737}`
- forced_action_counts: `{'-': 737}`
- action_counts: `{'SKIP_PRE_SUBMIT_SAFETY': 103, 'WAIT_REQUOTE': 7, 'NO_BUY_AI': 601, 'BUY_NOW': 22, 'SKIP_SOURCE_QUALITY': 3, 'BUY_DEFENSIVE': 1}`
- missing_actions: `[]`
- zero_sample_actions: `['SKIP_STALE']`
- unknown_bucket_affected_rows: `21`
- unknown_dimension_occurrence_count: `41`
- unknown_bucket_not_available_rows: `206`
- not_available_dimension_occurrence_count: `533`
- unknown_bucket_dimension_counts: `{'risk_context_bucket': 21, 'price_resolution_bucket': 20}`
- unknown_bucket_not_available_dimension_counts: `{'risk_context_bucket': 105, 'stale_bucket': 186, 'price_resolution_bucket': 80, 'liquidity_bucket': 103, 'overbought_bucket': 39, 'score_bucket': 20}`
- adm_source_bucket_used_count: `531`
- recomputed_unknown_count: `1867`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 22 | 8 | 0.0 | 0.0 | 3 | 0 |
| `WAIT_REQUOTE` | 7 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 0 | 0 | None | None | 0 | 0 |
| `BUY_DEFENSIVE` | 1 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 592 | 26 | -0.0475 | -1.0815 | 12 | 18 |
| `SKIP_SOURCE_QUALITY` | 3 | 1 | -0.8467 | -2.54 | 1 | 1 |
| `SKIP_PRE_SUBMIT_SAFETY` | 103 | 62 | -1.4429 | -2.3971 | 49 | 59 |

## Top Buckets
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`121` joined=`4` action=`NO_BUY_AI` sq_ev=`-0.0721`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_0900_1000` sample=`90` joined=`8` action=`NO_BUY_AI` sq_ev=`-0.0928`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1200_1400` sample=`53` joined=`3` action=`NO_BUY_AI` sq_ev=`-0.1887`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_0900_1000` sample=`45` joined=`3` action=`NO_BUY_AI` sq_ev=`0.1304`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_0900_1000` sample=`42` joined=`2` action=`NO_BUY_AI` sq_ev=`-0.1112`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1400_close` sample=`34` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|risk_context_not_available|-|stale_not_available|resolved_price|below_min_liquidity|overbought_ok|time_1000_1200` sample=`26` joined=`12` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-1.2188`
- `score_not_available|risk_unknown|-|stale_not_available|price_unknown|liquidity_not_available|overbought_not_available|time_1400_close` sample=`20` joined=`2` action=`NO_BUY_AI` sq_ev=`0.1255`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`19` joined=`2` action=`NO_BUY_AI` sq_ev=`-0.2184`
- `score75_84|risk_context_not_available|-|stale_not_available|defensive_limit|below_min_liquidity|not_evaluated|time_0900_1000` sample=`15` joined=`15` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-1.8`

## Warnings
- `ai_numeric_consistency_rows_excluded_from_aggregates`
