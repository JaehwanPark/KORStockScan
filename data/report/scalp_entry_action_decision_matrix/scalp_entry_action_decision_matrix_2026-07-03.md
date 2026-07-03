# Scalp Entry Action Decision Matrix - 2026-07-03

## Contract
- status: `warning`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `220`
- joined_sample/sample_floor: `14` / `20`
- prompt_applied_count: `112`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 220}`
- forced_action_counts: `{'-': 220}`
- action_counts: `{'BUY_DEFENSIVE': 39, 'SKIP_PRE_SUBMIT_SAFETY': 15, 'NO_BUY_AI': 129, 'BUY_NOW': 8, 'SKIP_SOURCE_QUALITY': 5, 'WAIT_REQUOTE': 21, 'SKIP_STALE': 3}`
- missing_actions: `[]`
- zero_sample_actions: `[]`
- unknown_bucket_affected_rows: `48`
- unknown_dimension_occurrence_count: `53`
- unknown_bucket_not_available_rows: `108`
- not_available_dimension_occurrence_count: `339`
- unknown_bucket_dimension_counts: `{'risk_context_bucket': 48, 'score_bucket': 1, 'price_resolution_bucket': 4}`
- unknown_bucket_not_available_dimension_counts: `{'stale_bucket': 90, 'liquidity_bucket': 92, 'overbought_bucket': 72, 'risk_context_bucket': 36, 'price_resolution_bucket': 45, 'score_bucket': 4}`
- adm_source_bucket_used_count: `112`
- recomputed_unknown_count: `816`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 8 | 1 | -0.3875 | -3.1 | 0 | 0 |
| `WAIT_REQUOTE` | 21 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 3 | 0 | 0.0 | None | 0 | 0 |
| `BUY_DEFENSIVE` | 39 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 127 | 6 | -0.117 | -2.4767 | 4 | 4 |
| `SKIP_SOURCE_QUALITY` | 5 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 15 | 7 | -0.4407 | -0.9443 | 3 | 3 |

## Top Buckets
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1400_close` sample=`29` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1200_1400` sample=`17` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_lt50|risk_unknown|-|stale_not_available|defensive_limit|liquidity_not_available|overbought_not_available|time_0900_1000` sample=`17` joined=`0` action=`BUY_DEFENSIVE` sq_ev=`0.0`
- `score65_74|risk_context_not_available|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`14` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`9` joined=`2` action=`NO_BUY_AI` sq_ev=`-0.3422`
- `score65_74|risk_unknown|-|stale_not_available|defensive_limit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`9` joined=`0` action=`BUY_DEFENSIVE` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_0900_1000` sample=`8` joined=`1` action=`NO_BUY_AI` sq_ev=`-0.5012`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`7` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_lt50|risk_unknown|-|stale_not_available|defensive_limit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`6` joined=`0` action=`BUY_DEFENSIVE` sq_ev=`0.0`
- `score50_64|strong_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1400_close` sample=`5` joined=`1` action=`NO_BUY_AI` sq_ev=`0.306`

## Warnings
- `joined_sample_below_sample_floor`
- `unknown_bucket_source_quality_gap`
- `ai_numeric_consistency_rows_excluded_from_aggregates`
