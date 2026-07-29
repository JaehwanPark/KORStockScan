# Scalp Entry Action Decision Matrix - 2026-07-28

## Contract
- status: `warning`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `77`
- joined_sample/sample_floor: `0` / `20`
- prompt_applied_count: `2`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 77}`
- forced_action_counts: `{'-': 77}`
- action_counts: `{'BUY_NOW': 14, 'WAIT_REQUOTE': 46, 'BUY_DEFENSIVE': 9, 'NO_BUY_AI': 8}`
- missing_actions: `[]`
- zero_sample_actions: `['SKIP_STALE', 'SKIP_SOURCE_QUALITY', 'SKIP_PRE_SUBMIT_SAFETY']`
- unknown_bucket_affected_rows: `10`
- unknown_dimension_occurrence_count: `11`
- unknown_bucket_not_available_rows: `75`
- not_available_dimension_occurrence_count: `206`
- unknown_bucket_dimension_counts: `{'risk_context_bucket': 10, 'price_resolution_bucket': 1}`
- unknown_bucket_not_available_dimension_counts: `{'liquidity_bucket': 75, 'overbought_bucket': 75, 'stale_bucket': 16, 'price_resolution_bucket': 39, 'score_bucket': 1}`
- score_source_missing_count: `0`
- score_source_missing_provenance: `{}`
- adm_source_bucket_used_count: `2`
- recomputed_unknown_count: `515`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 14 | 0 | 0.0 | None | 0 | 0 |
| `WAIT_REQUOTE` | 46 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 0 | 0 | None | None | 0 | 0 |
| `BUY_DEFENSIVE` | 9 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 8 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_SOURCE_QUALITY` | 0 | 0 | None | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 0 | 0 | None | None | 0 | 0 |

## Top Buckets
- `score50_64|risk_unknown|-|stale_watch|resolved_price|liquidity_not_available|overbought_not_available|time_0900_1000` sample=`8` joined=`0` action=`BUY_NOW` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_0900_1000` sample=`8` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score50_64|neutral_strength_momentum|-|stale_watch|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_0900_1000` sample=`6` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score50_64|strong_strength_momentum|-|stale_watch|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1000_1200` sample=`6` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score50_64|strong_strength_momentum|-|stale_watch|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_0900_1000` sample=`5` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score50_64|neutral_strength_momentum|-|stale_watch|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1000_1200` sample=`4` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score50_64|strong_strength_momentum|-|stale_watch|defensive_limit|liquidity_not_available|overbought_not_available|time_0900_1000` sample=`4` joined=`0` action=`BUY_DEFENSIVE` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1000_1200` sample=`4` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score50_64|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1000_1200` sample=`2` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score50_64|neutral_strength_momentum|-|stale_watch|defensive_limit|liquidity_not_available|overbought_not_available|time_0900_1000` sample=`2` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`

## Warnings
- `joined_sample_below_sample_floor`
