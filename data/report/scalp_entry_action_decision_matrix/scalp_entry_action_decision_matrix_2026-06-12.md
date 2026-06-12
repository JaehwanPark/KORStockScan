# Scalp Entry Action Decision Matrix - 2026-06-12

## Contract
- status: `warning`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `1190`
- joined_sample/sample_floor: `178` / `20`
- prompt_applied_count: `741`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 1190}`
- forced_action_counts: `{'-': 1190}`
- action_counts: `{'NO_BUY_AI': 821, 'WAIT_REQUOTE': 27, 'SKIP_PRE_SUBMIT_SAFETY': 271, 'SKIP_SOURCE_QUALITY': 54, 'BUY_DEFENSIVE': 17}`
- missing_actions: `[]`
- zero_sample_actions: `['BUY_NOW', 'SKIP_STALE']`
- unknown_bucket_affected_rows: `334`
- unknown_dimension_occurrence_count: `389`
- unknown_bucket_not_available_rows: `449`
- not_available_dimension_occurrence_count: `1057`
- unknown_bucket_dimension_counts: `{'score_bucket': 334, 'risk_context_bucket': 36, 'price_resolution_bucket': 19}`
- unknown_bucket_not_available_dimension_counts: `{'stale_bucket': 386, 'price_resolution_bucket': 115, 'liquidity_bucket': 180, 'overbought_bucket': 78, 'risk_context_bucket': 298}`
- adm_source_bucket_used_count: `741`
- recomputed_unknown_count: `3884`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 0 | 0 | None | None | 0 | 0 |
| `WAIT_REQUOTE` | 27 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 0 | 0 | None | None | 0 | 0 |
| `BUY_DEFENSIVE` | 17 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 821 | 70 | -0.143 | -1.6771 | 35 | 61 |
| `SKIP_SOURCE_QUALITY` | 54 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 271 | 108 | -0.7513 | -1.8853 | 61 | 96 |

## Top Buckets
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`204` joined=`11` action=`NO_BUY_AI` sq_ev=`-0.094`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1200_1400` sample=`196` joined=`21` action=`NO_BUY_AI` sq_ev=`-0.1681`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_0900_1000` sample=`83` joined=`5` action=`NO_BUY_AI` sq_ev=`0.1457`
- `score_unknown|risk_context_not_available|-|stale_not_available|defensive_limit|below_min_liquidity|overbought_ok|time_1000_1200` sample=`58` joined=`11` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-0.3002`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1400_close` sample=`42` joined=`9` action=`NO_BUY_AI` sq_ev=`-0.585`
- `score_unknown|risk_context_not_available|-|stale_not_available|resolved_price|below_min_liquidity|overbought_ok|time_1000_1200` sample=`41` joined=`9` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-0.2224`
- `score_unknown|risk_context_not_available|-|stale_not_available|defensive_limit|below_min_liquidity|overbought_ok|time_1400_close` sample=`29` joined=`23` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-2.0424`
- `score_unknown|risk_context_not_available|-|stale_not_available|resolved_price|below_min_liquidity|overbought_ok|time_1200_1400` sample=`26` joined=`13` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-0.7781`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_0900_1000` sample=`25` joined=`2` action=`NO_BUY_AI` sq_ev=`-0.2012`
- `score50_64|strong_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`24` joined=`1` action=`NO_BUY_AI` sq_ev=`-0.0858`

## Warnings
- `unknown_bucket_source_quality_gap`
