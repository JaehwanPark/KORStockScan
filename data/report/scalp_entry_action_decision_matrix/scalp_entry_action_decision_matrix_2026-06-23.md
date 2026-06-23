# Scalp Entry Action Decision Matrix - 2026-06-23

## Contract
- status: `warning`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `560`
- joined_sample/sample_floor: `127` / `20`
- prompt_applied_count: `355`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 560}`
- forced_action_counts: `{'-': 560}`
- action_counts: `{'NO_BUY_AI': 427, 'SKIP_PRE_SUBMIT_SAFETY': 104, 'BUY_NOW': 19, 'WAIT_REQUOTE': 6, 'SKIP_SOURCE_QUALITY': 2, 'BUY_DEFENSIVE': 2}`
- missing_actions: `[]`
- zero_sample_actions: `['SKIP_STALE']`
- unknown_bucket_affected_rows: `24`
- unknown_dimension_occurrence_count: `33`
- unknown_bucket_not_available_rows: `205`
- not_available_dimension_occurrence_count: `475`
- unknown_bucket_dimension_counts: `{'risk_context_bucket': 24, 'price_resolution_bucket': 9}`
- unknown_bucket_not_available_dimension_counts: `{'stale_bucket': 172, 'price_resolution_bucket': 76, 'liquidity_bucket': 88, 'overbought_bucket': 25, 'risk_context_bucket': 105, 'score_bucket': 9}`
- adm_source_bucket_used_count: `355`
- recomputed_unknown_count: `1683`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 19 | 7 | -1.0558 | -2.8657 | 6 | 0 |
| `WAIT_REQUOTE` | 6 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 0 | 0 | None | None | 0 | 0 |
| `BUY_DEFENSIVE` | 2 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 421 | 53 | -0.202 | -1.6049 | 24 | 43 |
| `SKIP_SOURCE_QUALITY` | 2 | 1 | -1.41 | -2.82 | 0 | 1 |
| `SKIP_PRE_SUBMIT_SAFETY` | 104 | 66 | -1.2099 | -1.9065 | 43 | 55 |

## Top Buckets
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_0900_1000` sample=`76` joined=`8` action=`NO_BUY_AI` sq_ev=`-0.1658`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`45` joined=`5` action=`NO_BUY_AI` sq_ev=`-0.1729`
- `score50_64|risk_context_not_available|-|stale_not_available|resolved_price|below_min_liquidity|overbought_ok|time_1000_1200` sample=`32` joined=`16` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-0.8065`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_0900_1000` sample=`32` joined=`8` action=`NO_BUY_AI` sq_ev=`-0.5391`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1400_close` sample=`23` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|risk_context_not_available|-|stale_not_available|resolved_price|below_min_liquidity|overbought_ok|time_1200_1400` sample=`21` joined=`18` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-1.0224`
- `score50_64|strong_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_0900_1000` sample=`17` joined=`1` action=`NO_BUY_AI` sq_ev=`-0.1124`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_watch|time_0900_1000` sample=`17` joined=`4` action=`NO_BUY_AI` sq_ev=`-0.2565`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1200_1400` sample=`15` joined=`1` action=`NO_BUY_AI` sq_ev=`-0.1467`
- `score50_64|risk_context_not_available|-|stale_not_available|resolved_price|below_min_liquidity|overbought_ok|time_0900_1000` sample=`11` joined=`11` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-2.4927`

## Warnings
- `ai_numeric_consistency_rows_excluded_from_aggregates`
