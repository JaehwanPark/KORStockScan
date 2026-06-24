# Scalp Entry Action Decision Matrix - 2026-06-24

## Contract
- status: `warning`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `571`
- joined_sample/sample_floor: `61` / `20`
- prompt_applied_count: `442`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 571}`
- forced_action_counts: `{'-': 571}`
- action_counts: `{'NO_BUY_AI': 483, 'BUY_NOW': 25, 'SKIP_PRE_SUBMIT_SAFETY': 51, 'BUY_DEFENSIVE': 8, 'SKIP_SOURCE_QUALITY': 4}`
- missing_actions: `[]`
- zero_sample_actions: `['WAIT_REQUOTE', 'SKIP_STALE']`
- unknown_bucket_affected_rows: `16`
- unknown_dimension_occurrence_count: `20`
- unknown_bucket_not_available_rows: `129`
- not_available_dimension_occurrence_count: `306`
- unknown_bucket_dimension_counts: `{'risk_context_bucket': 16, 'price_resolution_bucket': 4}`
- unknown_bucket_not_available_dimension_counts: `{'stale_bucket': 97, 'price_resolution_bucket': 62, 'liquidity_bucket': 75, 'risk_context_bucket': 51, 'overbought_bucket': 17, 'score_bucket': 4}`
- adm_source_bucket_used_count: `442`
- recomputed_unknown_count: `1286`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 25 | 1 | -0.1 | -2.5 | 1 | 0 |
| `WAIT_REQUOTE` | 0 | 0 | None | None | 0 | 0 |
| `SKIP_STALE` | 0 | 0 | None | None | 0 | 0 |
| `BUY_DEFENSIVE` | 8 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 470 | 33 | -0.0614 | -0.8742 | 15 | 24 |
| `SKIP_SOURCE_QUALITY` | 4 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 51 | 27 | -1.2086 | -2.283 | 21 | 23 |

## Top Buckets
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1400_close` sample=`68` joined=`1` action=`NO_BUY_AI` sq_ev=`0.0032`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1200_1400` sample=`33` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_0900_1000` sample=`32` joined=`6` action=`NO_BUY_AI` sq_ev=`-0.2806`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`29` joined=`4` action=`NO_BUY_AI` sq_ev=`-0.1586`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`25` joined=`5` action=`NO_BUY_AI` sq_ev=`-0.476`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_0900_1000` sample=`25` joined=`2` action=`NO_BUY_AI` sq_ev=`-0.0524`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_0900_1000` sample=`19` joined=`2` action=`NO_BUY_AI` sq_ev=`-0.0284`
- `score50_64|strong_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1400_close` sample=`17` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|risk_context_not_available|-|stale_not_available|resolved_price|below_min_liquidity|overbought_ok|time_1200_1400` sample=`15` joined=`8` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-1.034`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_watch|time_0900_1000` sample=`15` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`

## Warnings
- `ai_numeric_consistency_rows_excluded_from_aggregates`
