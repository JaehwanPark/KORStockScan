# Scalp Entry Action Decision Matrix - 2026-06-30

## Contract
- status: `warning`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `256`
- joined_sample/sample_floor: `13` / `20`
- prompt_applied_count: `93`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 256}`
- forced_action_counts: `{'-': 256}`
- action_counts: `{'BUY_NOW': 18, 'BUY_DEFENSIVE': 57, 'NO_BUY_AI': 135, 'SKIP_PRE_SUBMIT_SAFETY': 14, 'SKIP_STALE': 9, 'WAIT_REQUOTE': 22, 'SKIP_SOURCE_QUALITY': 1}`
- missing_actions: `[]`
- zero_sample_actions: `[]`
- unknown_bucket_affected_rows: `76`
- unknown_dimension_occurrence_count: `89`
- unknown_bucket_not_available_rows: `163`
- not_available_dimension_occurrence_count: `482`
- unknown_bucket_dimension_counts: `{'risk_context_bucket': 75, 'score_bucket': 10, 'price_resolution_bucket': 4}`
- unknown_bucket_not_available_dimension_counts: `{'stale_bucket': 126, 'liquidity_bucket': 140, 'overbought_bucket': 97, 'risk_context_bucket': 42, 'price_resolution_bucket': 73, 'score_bucket': 4}`
- adm_source_bucket_used_count: `93`
- recomputed_unknown_count: `1164`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 18 | 2 | 0.1461 | 1.315 | 0 | 0 |
| `WAIT_REQUOTE` | 22 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 9 | 0 | 0.0 | None | 0 | 0 |
| `BUY_DEFENSIVE` | 57 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 129 | 7 | -0.0095 | -0.1743 | 3 | 3 |
| `SKIP_SOURCE_QUALITY` | 1 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 14 | 4 | -0.5543 | -1.94 | 2 | 3 |

## Top Buckets
- `score65_74|risk_context_not_available|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`15` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1200_1400` sample=`14` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1400_close` sample=`14` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score65_74|risk_unknown|-|stale_not_available|defensive_limit|liquidity_not_available|overbought_not_available|time_1000_1200` sample=`13` joined=`0` action=`BUY_DEFENSIVE` sq_ev=`0.0`
- `score65_74|risk_unknown|-|stale_not_available|defensive_limit|liquidity_not_available|overbought_not_available|time_0900_1000` sample=`12` joined=`0` action=`BUY_DEFENSIVE` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`11` joined=`1` action=`NO_BUY_AI` sq_ev=`0.3009`
- `score_lt50|risk_unknown|-|stale_not_available|defensive_limit|liquidity_not_available|overbought_not_available|time_0900_1000` sample=`11` joined=`0` action=`BUY_DEFENSIVE` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_ok|time_1000_1200` sample=`7` joined=`1` action=`NO_BUY_AI` sq_ev=`-0.4714`
- `score65_74|risk_unknown|-|stale_not_available|defensive_limit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`7` joined=`0` action=`BUY_DEFENSIVE` sq_ev=`0.0`
- `score65_74|strong_strength_momentum|-|stale_block|price_not_available_pre_submit|liquidity_not_available|overbought_watch|time_1200_1400` sample=`6` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`

## Warnings
- `joined_sample_below_sample_floor`
- `unknown_bucket_source_quality_gap`
- `ai_numeric_consistency_rows_excluded_from_aggregates`
