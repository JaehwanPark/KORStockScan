# Scalp Entry Action Decision Matrix - 2026-06-29

## Contract
- status: `warning`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `741`
- joined_sample/sample_floor: `23` / `20`
- prompt_applied_count: `628`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 741}`
- forced_action_counts: `{'-': 741}`
- action_counts: `{'SKIP_PRE_SUBMIT_SAFETY': 15, 'NO_BUY_AI': 675, 'BUY_NOW': 38, 'SKIP_STALE': 10, 'SKIP_SOURCE_QUALITY': 1, 'BUY_DEFENSIVE': 2}`
- missing_actions: `[]`
- zero_sample_actions: `['WAIT_REQUOTE']`
- unknown_bucket_affected_rows: `16`
- unknown_dimension_occurrence_count: `20`
- unknown_bucket_not_available_rows: `113`
- not_available_dimension_occurrence_count: `323`
- unknown_bucket_dimension_counts: `{'score_bucket': 10, 'risk_context_bucket': 6, 'price_resolution_bucket': 4}`
- unknown_bucket_not_available_dimension_counts: `{'risk_context_bucket': 25, 'stale_bucket': 87, 'price_resolution_bucket': 82, 'liquidity_bucket': 98, 'overbought_bucket': 27, 'score_bucket': 4}`
- adm_source_bucket_used_count: `628`
- recomputed_unknown_count: `1402`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 38 | 0 | 0.0 | None | 0 | 0 |
| `WAIT_REQUOTE` | 0 | 0 | None | None | 0 | 0 |
| `SKIP_STALE` | 10 | 0 | 0.0 | None | 0 | 0 |
| `BUY_DEFENSIVE` | 2 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 666 | 15 | -0.0015 | -0.0667 | 3 | 7 |
| `SKIP_SOURCE_QUALITY` | 1 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 15 | 8 | -1.0347 | -1.94 | 4 | 5 |

## Top Buckets
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`117` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_0900_1000` sample=`69` joined=`2` action=`NO_BUY_AI` sq_ev=`0.0878`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1200_1400` sample=`63` joined=`1` action=`NO_BUY_AI` sq_ev=`-0.081`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_watch|time_0900_1000` sample=`41` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_0900_1000` sample=`33` joined=`2` action=`NO_BUY_AI` sq_ev=`0.1491`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1400_close` sample=`30` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|neutral_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`17` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|strong_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`15` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_ok|time_1200_1400` sample=`15` joined=`1` action=`NO_BUY_AI` sq_ev=`0.1693`
- `score50_64|strong_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_0900_1000` sample=`14` joined=`1` action=`NO_BUY_AI` sq_ev=`-0.5043`

## Warnings
- `unknown_bucket_source_quality_gap`
- `ai_numeric_consistency_rows_excluded_from_aggregates`
