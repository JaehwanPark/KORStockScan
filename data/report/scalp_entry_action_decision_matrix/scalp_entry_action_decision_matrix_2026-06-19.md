# Scalp Entry Action Decision Matrix - 2026-06-19

## Contract
- status: `warning`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `728`
- joined_sample/sample_floor: `68` / `20`
- prompt_applied_count: `583`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 728}`
- forced_action_counts: `{'-': 728}`
- action_counts: `{'WAIT_REQUOTE': 17, 'BUY_NOW': 27, 'NO_BUY_AI': 631, 'SKIP_PRE_SUBMIT_SAFETY': 51, 'SKIP_SOURCE_QUALITY': 2}`
- missing_actions: `[]`
- zero_sample_actions: `['SKIP_STALE', 'BUY_DEFENSIVE']`
- unknown_bucket_affected_rows: `20`
- unknown_dimension_occurrence_count: `40`
- unknown_bucket_not_available_rows: `145`
- not_available_dimension_occurrence_count: `401`
- unknown_bucket_dimension_counts: `{'risk_context_bucket': 20, 'price_resolution_bucket': 20}`
- unknown_bucket_not_available_dimension_counts: `{'price_resolution_bucket': 71, 'liquidity_bucket': 94, 'overbought_bucket': 43, 'stale_bucket': 122, 'risk_context_bucket': 51, 'score_bucket': 20}`
- adm_source_bucket_used_count: `583`
- recomputed_unknown_count: `1547`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 27 | 3 | -0.2733 | -2.46 | 2 | 0 |
| `WAIT_REQUOTE` | 17 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 0 | 0 | None | None | 0 | 0 |
| `BUY_DEFENSIVE` | 0 | 0 | None | None | 0 | 0 |
| `NO_BUY_AI` | 614 | 30 | -0.108 | -2.21 | 17 | 26 |
| `SKIP_SOURCE_QUALITY` | 2 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 51 | 35 | -1.9582 | -2.8534 | 22 | 32 |

## Top Buckets
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`110` joined=`4` action=`NO_BUY_AI` sq_ev=`-0.0809`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_0900_1000` sample=`98` joined=`15` action=`NO_BUY_AI` sq_ev=`-0.2884`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1200_1400` sample=`84` joined=`3` action=`NO_BUY_AI` sq_ev=`-0.0775`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1400_close` sample=`58` joined=`1` action=`NO_BUY_AI` sq_ev=`-0.0472`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_0900_1000` sample=`39` joined=`3` action=`NO_BUY_AI` sq_ev=`-0.0703`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_0900_1000` sample=`24` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|strong_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`20` joined=`1` action=`NO_BUY_AI` sq_ev=`-0.1525`
- `score_not_available|risk_unknown|-|stale_not_available|price_unknown|liquidity_not_available|overbought_not_available|time_1400_close` sample=`20` joined=`1` action=`NO_BUY_AI` sq_ev=`-0.4585`
- `score50_64|strong_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_0900_1000` sample=`19` joined=`4` action=`NO_BUY_AI` sq_ev=`-0.4979`
- `score50_64|risk_context_not_available|-|stale_not_available|resolved_price|below_min_liquidity|overbought_ok|time_1200_1400` sample=`17` joined=`7` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-1.3694`

## Warnings
- `ai_numeric_consistency_rows_excluded_from_aggregates`
