# Scalp Entry Action Decision Matrix - 2026-07-09

## Contract
- status: `warning`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `148`
- joined_sample/sample_floor: `10` / `20`
- prompt_applied_count: `49`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 148}`
- forced_action_counts: `{'-': 148}`
- action_counts: `{'NO_BUY_AI': 60, 'SKIP_PRE_SUBMIT_SAFETY': 9, 'WAIT_REQUOTE': 55, 'BUY_DEFENSIVE': 22, 'SKIP_SOURCE_QUALITY': 1, 'SKIP_STALE': 1}`
- missing_actions: `[]`
- zero_sample_actions: `['BUY_NOW']`
- unknown_bucket_affected_rows: `7`
- unknown_dimension_occurrence_count: `9`
- unknown_bucket_not_available_rows: `99`
- not_available_dimension_occurrence_count: `307`
- unknown_bucket_dimension_counts: `{'risk_context_bucket': 7, 'price_resolution_bucket': 2}`
- unknown_bucket_not_available_dimension_counts: `{'stale_bucket': 69, 'price_resolution_bucket': 54, 'liquidity_bucket': 90, 'overbought_bucket': 83, 'risk_context_bucket': 9, 'score_bucket': 2}`
- score_source_missing_count: `0`
- score_source_missing_provenance: `{}`
- adm_source_bucket_used_count: `49`
- recomputed_unknown_count: `721`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 0 | 0 | None | None | 0 | 0 |
| `WAIT_REQUOTE` | 55 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 1 | 0 | 0.0 | None | 0 | 0 |
| `BUY_DEFENSIVE` | 22 | 1 | -0.2805 | -6.17 | 1 | 0 |
| `NO_BUY_AI` | 60 | 3 | 0.016 | 0.32 | 1 | 1 |
| `SKIP_SOURCE_QUALITY` | 1 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 9 | 6 | -1.9311 | -2.8967 | 3 | 5 |

## Top Buckets
- `score65_74|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`16` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_0900_1000` sample=`9` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score65_74|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1200_1400` sample=`7` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_0900_1000` sample=`6` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_0900_1000` sample=`6` joined=`1` action=`NO_BUY_AI` sq_ev=`0.2717`
- `score65_74|neutral_strength_momentum|-|stale_high|defensive_limit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`6` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score65_74|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1000_1200` sample=`6` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score65_74|neutral_strength_momentum|-|stale_watch|defensive_limit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`6` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score65_74|weak_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`5` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score50_64|risk_context_not_available|-|stale_not_available|defensive_limit|below_min_liquidity|overbought_ok|time_0900_1000` sample=`4` joined=`3` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-1.3175`

## Warnings
- `joined_sample_below_sample_floor`
