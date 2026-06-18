# Scalp Entry Action Decision Matrix - 2026-06-18

## Contract
- status: `warning`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `1109`
- joined_sample/sample_floor: `174` / `20`
- prompt_applied_count: `652`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 1109}`
- forced_action_counts: `{'-': 1109}`
- action_counts: `{'SKIP_PRE_SUBMIT_SAFETY': 172, 'NO_BUY_AI': 801, 'WAIT_REQUOTE': 16, 'BUY_NOW': 79, 'SKIP_SOURCE_QUALITY': 21, 'BUY_DEFENSIVE': 20}`
- missing_actions: `[]`
- zero_sample_actions: `['SKIP_STALE']`
- unknown_bucket_affected_rows: `91`
- unknown_dimension_occurrence_count: `162`
- unknown_bucket_not_available_rows: `457`
- not_available_dimension_occurrence_count: `1024`
- unknown_bucket_dimension_counts: `{'score_bucket': 45, 'risk_context_bucket': 91, 'price_resolution_bucket': 26}`
- unknown_bucket_not_available_dimension_counts: `{'risk_context_bucket': 172, 'stale_bucket': 311, 'price_resolution_bucket': 190, 'liquidity_bucket': 240, 'overbought_bucket': 85, 'score_bucket': 26}`
- adm_source_bucket_used_count: `652`
- recomputed_unknown_count: `3659`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 79 | 47 | -0.9899 | -1.6638 | 23 | 0 |
| `WAIT_REQUOTE` | 16 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 0 | 0 | None | None | 0 | 0 |
| `BUY_DEFENSIVE` | 20 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 775 | 18 | -0.0297 | -1.2783 | 6 | 14 |
| `SKIP_SOURCE_QUALITY` | 21 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 172 | 109 | -0.7298 | -1.1516 | 53 | 79 |

## Top Buckets
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1200_1400` sample=`230` joined=`15` action=`NO_BUY_AI` sq_ev=`-0.0891`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`144` joined=`3` action=`NO_BUY_AI` sq_ev=`-0.0158`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1400_close` sample=`73` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1400_close` sample=`41` joined=`3` action=`NO_BUY_AI` sq_ev=`-0.1544`
- `score_unknown|risk_unknown|-|stale_not_available|quote_based|liquidity_ok|overbought_ok|time_0900_1000` sample=`32` joined=`29` action=`BUY_NOW` sq_ev=`-1.3622`
- `score50_64|risk_context_not_available|-|stale_not_available|resolved_price|below_min_liquidity|overbought_ok|time_0900_1000` sample=`29` joined=`29` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-1.1355`
- `score_not_available|risk_unknown|-|stale_not_available|price_unknown|liquidity_not_available|overbought_not_available|time_1400_close` sample=`26` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|risk_context_not_available|-|stale_not_available|resolved_price|below_min_liquidity|overbought_ok|time_1000_1200` sample=`25` joined=`20` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-1.0136`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_ok|time_1200_1400` sample=`22` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|risk_context_not_available|-|stale_not_available|resolved_price|below_min_liquidity|overbought_ok|time_1200_1400` sample=`18` joined=`5` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-0.4472`

## Warnings
- `unknown_bucket_source_quality_gap`
- `ai_numeric_consistency_rows_excluded_from_aggregates`
