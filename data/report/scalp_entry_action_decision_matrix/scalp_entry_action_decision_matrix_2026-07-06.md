# Scalp Entry Action Decision Matrix - 2026-07-06

## Contract
- status: `warning`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `247`
- joined_sample/sample_floor: `18` / `20`
- prompt_applied_count: `138`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 247}`
- forced_action_counts: `{'-': 247}`
- action_counts: `{'WAIT_REQUOTE': 22, 'BUY_DEFENSIVE': 30, 'NO_BUY_AI': 150, 'BUY_NOW': 13, 'SKIP_PRE_SUBMIT_SAFETY': 30, 'SKIP_SOURCE_QUALITY': 2}`
- missing_actions: `[]`
- zero_sample_actions: `['SKIP_STALE']`
- unknown_bucket_affected_rows: `27`
- unknown_dimension_occurrence_count: `29`
- unknown_bucket_not_available_rows: `109`
- not_available_dimension_occurrence_count: `313`
- unknown_bucket_dimension_counts: `{'risk_context_bucket': 27, 'score_bucket': 1, 'price_resolution_bucket': 1}`
- unknown_bucket_not_available_dimension_counts: `{'stale_bucket': 104, 'price_resolution_bucket': 45, 'liquidity_bucket': 78, 'overbought_bucket': 55, 'risk_context_bucket': 30, 'score_bucket': 1}`
- adm_source_bucket_used_count: `138`
- recomputed_unknown_count: `846`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 13 | 0 | 0.0 | None | 0 | 0 |
| `WAIT_REQUOTE` | 22 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 0 | 0 | None | None | 0 | 0 |
| `BUY_DEFENSIVE` | 30 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 150 | 6 | -0.0357 | -0.8933 | 1 | 4 |
| `SKIP_SOURCE_QUALITY` | 2 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 30 | 12 | -0.8083 | -2.0208 | 4 | 9 |

## Top Buckets
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1400_close` sample=`22` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1200_1400` sample=`21` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`17` joined=`2` action=`NO_BUY_AI` sq_ev=`-0.1976`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_0900_1000` sample=`12` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score65_74|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`10` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score50_64|risk_context_not_available|-|stale_not_available|defensive_limit|below_min_liquidity|overbought_ok|time_1400_close` sample=`9` joined=`3` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-0.2056`
- `score50_64|risk_context_not_available|-|stale_not_available|defensive_limit|below_min_liquidity|overbought_ok|time_1200_1400` sample=`7` joined=`1` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-0.2886`
- `score65_74|risk_unknown|-|stale_not_available|defensive_limit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`7` joined=`0` action=`BUY_DEFENSIVE` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_watch|time_1400_close` sample=`6` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_0900_1000` sample=`5` joined=`1` action=`NO_BUY_AI` sq_ev=`0.286`

## Warnings
- `joined_sample_below_sample_floor`
- `unknown_bucket_source_quality_gap`
