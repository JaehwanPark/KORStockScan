# Scalp Entry Action Decision Matrix - 2026-07-13

## Contract
- status: `warning`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `186`
- joined_sample/sample_floor: `0` / `20`
- prompt_applied_count: `53`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 186}`
- forced_action_counts: `{'-': 186}`
- action_counts: `{'WAIT_REQUOTE': 104, 'BUY_DEFENSIVE': 3, 'BUY_NOW': 4, 'SKIP_STALE': 2, 'NO_BUY_AI': 68, 'SKIP_PRE_SUBMIT_SAFETY': 5}`
- missing_actions: `[]`
- zero_sample_actions: `['SKIP_SOURCE_QUALITY']`
- unknown_bucket_affected_rows: `15`
- unknown_dimension_occurrence_count: `19`
- unknown_bucket_not_available_rows: `133`
- not_available_dimension_occurrence_count: `467`
- unknown_bucket_dimension_counts: `{'risk_context_bucket': 15, 'price_resolution_bucket': 4}`
- unknown_bucket_not_available_dimension_counts: `{'stale_bucket': 113, 'price_resolution_bucket': 97, 'liquidity_bucket': 128, 'overbought_bucket': 124, 'risk_context_bucket': 5}`
- score_source_missing_count: `0`
- score_source_missing_provenance: `{}`
- adm_source_bucket_used_count: `53`
- recomputed_unknown_count: `975`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 4 | 0 | 0.0 | None | 0 | 0 |
| `WAIT_REQUOTE` | 104 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 2 | 0 | 0.0 | None | 0 | 0 |
| `BUY_DEFENSIVE` | 3 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 68 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_SOURCE_QUALITY` | 0 | 0 | None | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 5 | 0 | 0.0 | None | 0 | 0 |

## Top Buckets
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`28` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1200_1400` sample=`19` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_0900_1000` sample=`18` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1000_1200` sample=`13` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|weak_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_0900_1000` sample=`13` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_0900_1000` sample=`8` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_lt50|weak_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1000_1200` sample=`8` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1200_1400` sample=`7` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_lt50|risk_unknown|-|stale_not_available|defensive_limit|liquidity_not_available|overbought_not_available|time_1200_1400` sample=`6` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_lt50|weak_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1200_1400` sample=`6` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`

## Warnings
- `joined_sample_below_sample_floor`
- `unknown_bucket_source_quality_gap`
