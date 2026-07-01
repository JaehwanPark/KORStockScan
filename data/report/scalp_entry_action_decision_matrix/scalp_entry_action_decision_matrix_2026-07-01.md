# Scalp Entry Action Decision Matrix - 2026-07-01

## Contract
- status: `warning`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `290`
- joined_sample/sample_floor: `12` / `20`
- prompt_applied_count: `109`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 290}`
- forced_action_counts: `{'-': 290}`
- action_counts: `{'NO_BUY_AI': 130, 'BUY_DEFENSIVE': 54, 'WAIT_REQUOTE': 66, 'BUY_NOW': 7, 'SKIP_PRE_SUBMIT_SAFETY': 10, 'SKIP_STALE': 21, 'SKIP_SOURCE_QUALITY': 2}`
- missing_actions: `[]`
- zero_sample_actions: `[]`
- unknown_bucket_affected_rows: `62`
- unknown_dimension_occurrence_count: `66`
- unknown_bucket_not_available_rows: `181`
- not_available_dimension_occurrence_count: `676`
- unknown_bucket_dimension_counts: `{'risk_context_bucket': 62, 'price_resolution_bucket': 4}`
- unknown_bucket_not_available_dimension_counts: `{'stale_bucket': 147, 'liquidity_bucket': 171, 'overbought_bucket': 153, 'risk_context_bucket': 92, 'price_resolution_bucket': 109, 'score_bucket': 4}`
- adm_source_bucket_used_count: `109`
- recomputed_unknown_count: `1321`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 7 | 2 | -0.2286 | -0.8 | 0 | 0 |
| `WAIT_REQUOTE` | 66 | 4 | 0.0127 | 0.21 | 1 | 0 |
| `SKIP_STALE` | 21 | 0 | 0.0 | None | 0 | 0 |
| `BUY_DEFENSIVE` | 54 | 1 | 0.0304 | 1.64 | 0 | 0 |
| `NO_BUY_AI` | 127 | 4 | 0.0632 | 2.0075 | 0 | 0 |
| `SKIP_SOURCE_QUALITY` | 2 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 10 | 1 | 0.206 | 2.06 | 0 | 0 |

## Top Buckets
- `score65_74|risk_context_not_available|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_0900_1000` sample=`20` joined=`3` action=`WAIT_REQUOTE` sq_ev=`-0.021`
- `score65_74|risk_unknown|-|stale_not_available|defensive_limit|liquidity_not_available|overbought_not_available|time_0900_1000` sample=`17` joined=`0` action=`BUY_DEFENSIVE` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1200_1400` sample=`16` joined=`2` action=`NO_BUY_AI` sq_ev=`0.1881`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`15` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1400_close` sample=`15` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_lt50|risk_context_not_available|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1200_1400` sample=`8` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|risk_unknown|-|stale_not_available|defensive_limit|liquidity_not_available|overbought_not_available|time_1000_1200` sample=`8` joined=`0` action=`BUY_DEFENSIVE` sq_ev=`0.0`
- `score65_74|risk_context_not_available|-|stale_block|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`7` joined=`0` action=`SKIP_STALE` sq_ev=`0.0`
- `score65_74|risk_context_not_available|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1200_1400` sample=`7` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score65_74|risk_context_not_available|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`7` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`

## Warnings
- `joined_sample_below_sample_floor`
- `unknown_bucket_source_quality_gap`
- `ai_numeric_consistency_rows_excluded_from_aggregates`
