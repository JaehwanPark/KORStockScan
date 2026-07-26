# Scalp Entry Action Decision Matrix - 2026-07-24

## Contract
- status: `warning`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `179`
- joined_sample/sample_floor: `0` / `20`
- prompt_applied_count: `54`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 179}`
- forced_action_counts: `{'-': 179}`
- action_counts: `{'WAIT_REQUOTE': 80, 'NO_BUY_AI': 55, 'BUY_DEFENSIVE': 8, 'SKIP_PRE_SUBMIT_SAFETY': 36}`
- missing_actions: `[]`
- zero_sample_actions: `['BUY_NOW', 'SKIP_STALE', 'SKIP_SOURCE_QUALITY']`
- unknown_bucket_affected_rows: `37`
- unknown_dimension_occurrence_count: `38`
- unknown_bucket_not_available_rows: `125`
- not_available_dimension_occurrence_count: `430`
- unknown_bucket_dimension_counts: `{'risk_context_bucket': 37, 'price_resolution_bucket': 1}`
- unknown_bucket_not_available_dimension_counts: `{'stale_bucket': 108, 'price_resolution_bucket': 71, 'liquidity_bucket': 125, 'overbought_bucket': 125, 'score_bucket': 1}`
- score_source_missing_count: `0`
- score_source_missing_provenance: `{}`
- adm_source_bucket_used_count: `54`
- recomputed_unknown_count: `928`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 0 | 0 | None | None | 0 | 0 |
| `WAIT_REQUOTE` | 80 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 0 | 0 | None | None | 0 | 0 |
| `BUY_DEFENSIVE` | 8 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 55 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_SOURCE_QUALITY` | 0 | 0 | None | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 36 | 0 | 0.0 | None | 0 | 0 |

## Top Buckets
- `score_lt50|neutral_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1400_close` sample=`19` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_lt50|risk_unknown|-|stale_not_available|defensive_limit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`18` joined=`0` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`15` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score65_74|risk_unknown|-|stale_not_available|defensive_limit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`14` joined=`0` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_0900_1000` sample=`14` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|weak_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_0900_1000` sample=`9` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score65_74|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`8` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score65_74|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_0900_1000` sample=`7` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score65_74|neutral_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1400_close` sample=`5` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score65_74|neutral_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1200_1400` sample=`4` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`

## Warnings
- `joined_sample_below_sample_floor`
- `unknown_bucket_source_quality_gap`
