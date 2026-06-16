# Scalp Entry Action Decision Matrix - 2026-06-16

## Contract
- status: `pass`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `1145`
- joined_sample/sample_floor: `149` / `20`
- prompt_applied_count: `797`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 1145}`
- forced_action_counts: `{'-': 1145}`
- action_counts: `{'NO_BUY_AI': 980, 'WAIT_REQUOTE': 20, 'BUY_NOW': 20, 'SKIP_PRE_SUBMIT_SAFETY': 101, 'SKIP_SOURCE_QUALITY': 21, 'BUY_DEFENSIVE': 3}`
- missing_actions: `[]`
- zero_sample_actions: `['SKIP_STALE']`
- unknown_bucket_affected_rows: `23`
- unknown_dimension_occurrence_count: `43`
- unknown_bucket_not_available_rows: `348`
- not_available_dimension_occurrence_count: `826`
- unknown_bucket_dimension_counts: `{'risk_context_bucket': 23, 'price_resolution_bucket': 20}`
- unknown_bucket_not_available_dimension_counts: `{'stale_bucket': 176, 'price_resolution_bucket': 223, 'liquidity_bucket': 247, 'overbought_bucket': 59, 'risk_context_bucket': 101, 'score_bucket': 20}`
- adm_source_bucket_used_count: `797`
- recomputed_unknown_count: `3129`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 20 | 10 | -0.1755 | -0.351 | 4 | 0 |
| `WAIT_REQUOTE` | 20 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 0 | 0 | None | None | 0 | 0 |
| `BUY_DEFENSIVE` | 3 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 980 | 74 | -0.0818 | -1.0832 | 23 | 53 |
| `SKIP_SOURCE_QUALITY` | 21 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 101 | 65 | -1.2638 | -1.9637 | 32 | 59 |

## Top Buckets
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1200_1400` sample=`193` joined=`7` action=`NO_BUY_AI` sq_ev=`-0.0289`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`166` joined=`25` action=`NO_BUY_AI` sq_ev=`-0.1012`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1400_close` sample=`161` joined=`1` action=`NO_BUY_AI` sq_ev=`-0.0104`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_0900_1000` sample=`64` joined=`25` action=`NO_BUY_AI` sq_ev=`-0.3728`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_0900_1000` sample=`25` joined=`6` action=`NO_BUY_AI` sq_ev=`-0.898`
- `score50_64|strong_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`23` joined=`3` action=`NO_BUY_AI` sq_ev=`-0.213`
- `score50_64|strong_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1200_1400` sample=`20` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_not_available|risk_unknown|-|stale_not_available|price_unknown|liquidity_not_available|overbought_not_available|time_1400_close` sample=`20` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|risk_context_not_available|-|stale_not_available|resolved_price|below_min_liquidity|overbought_ok|time_0900_1000` sample=`17` joined=`14` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-1.7`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_ok|time_1000_1200` sample=`17` joined=`1` action=`NO_BUY_AI` sq_ev=`0.0618`
