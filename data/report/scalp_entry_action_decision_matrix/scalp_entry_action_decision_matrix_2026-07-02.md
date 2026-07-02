# Scalp Entry Action Decision Matrix - 2026-07-02

## Contract
- status: `warning`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `277`
- joined_sample/sample_floor: `18` / `20`
- prompt_applied_count: `171`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 277}`
- forced_action_counts: `{'-': 277}`
- action_counts: `{'NO_BUY_AI': 181, 'BUY_DEFENSIVE': 39, 'BUY_NOW': 19, 'SKIP_PRE_SUBMIT_SAFETY': 30, 'WAIT_REQUOTE': 3, 'SKIP_STALE': 5}`
- missing_actions: `[]`
- zero_sample_actions: `['SKIP_SOURCE_QUALITY']`
- unknown_bucket_affected_rows: `46`
- unknown_dimension_occurrence_count: `49`
- unknown_bucket_not_available_rows: `106`
- not_available_dimension_occurrence_count: `279`
- unknown_bucket_dimension_counts: `{'risk_context_bucket': 46, 'score_bucket': 2, 'price_resolution_bucket': 1}`
- unknown_bucket_not_available_dimension_counts: `{'stale_bucket': 90, 'liquidity_bucket': 71, 'overbought_bucket': 51, 'price_resolution_bucket': 30, 'risk_context_bucket': 36, 'score_bucket': 1}`
- adm_source_bucket_used_count: `171`
- recomputed_unknown_count: `844`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 19 | 2 | -0.1516 | -1.44 | 1 | 0 |
| `WAIT_REQUOTE` | 3 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 5 | 0 | 0.0 | None | 0 | 0 |
| `BUY_DEFENSIVE` | 39 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 180 | 7 | -0.1423 | -3.66 | 6 | 6 |
| `SKIP_SOURCE_QUALITY` | 0 | 0 | None | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 30 | 9 | -0.6133 | -2.0444 | 4 | 6 |

## Top Buckets
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`28` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1400_close` sample=`28` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1200_1400` sample=`19` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_0900_1000` sample=`15` joined=`1` action=`NO_BUY_AI` sq_ev=`-0.248`
- `score50_64|risk_context_not_available|-|stale_not_available|defensive_limit|below_min_liquidity|overbought_ok|time_1400_close` sample=`10` joined=`5` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-0.82`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`10` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score65_74|risk_unknown|-|stale_not_available|defensive_limit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`9` joined=`0` action=`BUY_DEFENSIVE` sq_ev=`0.0`
- `score65_74|risk_unknown|-|stale_not_available|defensive_limit|liquidity_not_available|overbought_not_available|time_0900_1000` sample=`8` joined=`0` action=`BUY_DEFENSIVE` sq_ev=`0.0`
- `score50_64|risk_context_not_available|-|stale_not_available|defensive_limit|below_min_liquidity|overbought_ok|time_1000_1200` sample=`7` joined=`2` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-0.3186`
- `score50_64|strong_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`6` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`

## Warnings
- `joined_sample_below_sample_floor`
- `unknown_bucket_source_quality_gap`
- `ai_numeric_consistency_rows_excluded_from_aggregates`
