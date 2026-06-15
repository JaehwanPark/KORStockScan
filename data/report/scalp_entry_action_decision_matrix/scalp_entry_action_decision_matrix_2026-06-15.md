# Scalp Entry Action Decision Matrix - 2026-06-15

## Contract
- status: `warning`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `1144`
- joined_sample/sample_floor: `103` / `20`
- prompt_applied_count: `894`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 1144}`
- forced_action_counts: `{'-': 1144}`
- action_counts: `{'SKIP_SOURCE_QUALITY': 14, 'WAIT_REQUOTE': 18, 'NO_BUY_AI': 1004, 'SKIP_PRE_SUBMIT_SAFETY': 89, 'BUY_NOW': 10, 'BUY_DEFENSIVE': 9}`
- missing_actions: `[]`
- zero_sample_actions: `['SKIP_STALE']`
- unknown_bucket_affected_rows: `26`
- unknown_dimension_occurrence_count: `41`
- unknown_bucket_not_available_rows: `250`
- not_available_dimension_occurrence_count: `608`
- unknown_bucket_dimension_counts: `{'score_bucket': 2, 'risk_context_bucket': 24, 'price_resolution_bucket': 15}`
- unknown_bucket_not_available_dimension_counts: `{'risk_context_bucket': 91, 'stale_bucket': 153, 'liquidity_bucket': 161, 'price_resolution_bucket': 135, 'overbought_bucket': 53, 'score_bucket': 15}`
- adm_source_bucket_used_count: `894`
- recomputed_unknown_count: `2546`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 10 | 3 | -0.699 | -2.33 | 2 | 0 |
| `WAIT_REQUOTE` | 18 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 0 | 0 | None | None | 0 | 0 |
| `BUY_DEFENSIVE` | 9 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 1004 | 61 | -0.0646 | -1.0628 | 17 | 48 |
| `SKIP_SOURCE_QUALITY` | 14 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 89 | 39 | -0.5599 | -1.2777 | 16 | 31 |

## Top Buckets
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`283` joined=`13` action=`NO_BUY_AI` sq_ev=`-0.0507`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1200_1400` sample=`224` joined=`17` action=`NO_BUY_AI` sq_ev=`-0.1101`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_0900_1000` sample=`147` joined=`19` action=`NO_BUY_AI` sq_ev=`-0.0473`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1400_close` sample=`44` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_0900_1000` sample=`35` joined=`3` action=`NO_BUY_AI` sq_ev=`0.024`
- `score50_64|strong_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`23` joined=`3` action=`NO_BUY_AI` sq_ev=`-0.203`
- `score50_64|risk_context_not_available|-|stale_not_available|resolved_price|below_min_liquidity|overbought_ok|time_1200_1400` sample=`20` joined=`5` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`0.237`
- `score50_64|strong_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_0900_1000` sample=`18` joined=`1` action=`NO_BUY_AI` sq_ev=`-0.1328`
- `score50_64|risk_context_not_available|-|stale_not_available|resolved_price|below_min_liquidity|overbought_ok|time_0900_1000` sample=`16` joined=`15` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-2.0425`
- `score50_64|strong_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1200_1400` sample=`16` joined=`1` action=`NO_BUY_AI` sq_ev=`-0.1225`

## Warnings
- `unknown_bucket_source_quality_gap`
