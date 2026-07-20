# Scalp Entry Action Decision Matrix - 2026-07-20

## Contract
- status: `warning`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `322`
- joined_sample/sample_floor: `3` / `20`
- prompt_applied_count: `12`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 322}`
- forced_action_counts: `{'-': 322}`
- action_counts: `{'WAIT_REQUOTE': 225, 'NO_BUY_AI': 57, 'SKIP_STALE': 4, 'BUY_DEFENSIVE': 29, 'SKIP_PRE_SUBMIT_SAFETY': 5, 'BUY_NOW': 2}`
- missing_actions: `[]`
- zero_sample_actions: `['SKIP_SOURCE_QUALITY']`
- unknown_bucket_affected_rows: `45`
- unknown_dimension_occurrence_count: `46`
- unknown_bucket_not_available_rows: `310`
- not_available_dimension_occurrence_count: `1055`
- unknown_bucket_dimension_counts: `{'risk_context_bucket': 45, 'price_resolution_bucket': 1}`
- unknown_bucket_not_available_dimension_counts: `{'stale_bucket': 242, 'price_resolution_bucket': 197, 'liquidity_bucket': 305, 'overbought_bucket': 305, 'risk_context_bucket': 5, 'score_bucket': 1}`
- score_source_missing_count: `0`
- score_source_missing_provenance: `{}`
- adm_source_bucket_used_count: `12`
- recomputed_unknown_count: `2159`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 2 | 0 | 0.0 | None | 0 | 0 |
| `WAIT_REQUOTE` | 225 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 4 | 0 | 0.0 | None | 0 | 0 |
| `BUY_DEFENSIVE` | 29 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 57 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_SOURCE_QUALITY` | 0 | 0 | None | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 5 | 3 | -0.55 | -0.9167 | 1 | 1 |

## Top Buckets
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1200_1400` sample=`38` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1000_1200` sample=`35` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_0900_1000` sample=`25` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`21` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|risk_unknown|-|stale_not_available|defensive_limit|liquidity_not_available|overbought_not_available|time_1000_1200` sample=`17` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_lt50|weak_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1000_1200` sample=`17` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|weak_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_0900_1000` sample=`15` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|risk_unknown|-|stale_not_available|defensive_limit|liquidity_not_available|overbought_not_available|time_1200_1400` sample=`12` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_lt50|risk_unknown|-|stale_not_available|defensive_limit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`8` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_lt50|weak_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1200_1400` sample=`8` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`

## Warnings
- `joined_sample_below_sample_floor`
- `unknown_bucket_source_quality_gap`
