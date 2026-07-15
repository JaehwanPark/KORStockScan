# Scalp Entry Action Decision Matrix - 2026-07-15

## Contract
- status: `warning`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `396`
- joined_sample/sample_floor: `4` / `20`
- prompt_applied_count: `199`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 396}`
- forced_action_counts: `{'-': 396}`
- action_counts: `{'WAIT_REQUOTE': 109, 'NO_BUY_AI': 254, 'SKIP_PRE_SUBMIT_SAFETY': 8, 'BUY_DEFENSIVE': 16, 'BUY_NOW': 4, 'SKIP_SOURCE_QUALITY': 5}`
- missing_actions: `[]`
- zero_sample_actions: `['SKIP_STALE']`
- unknown_bucket_affected_rows: `37`
- unknown_dimension_occurrence_count: `38`
- unknown_bucket_not_available_rows: `197`
- not_available_dimension_occurrence_count: `624`
- unknown_bucket_dimension_counts: `{'risk_context_bucket': 37, 'price_resolution_bucket': 1}`
- unknown_bucket_not_available_dimension_counts: `{'stale_bucket': 145, 'price_resolution_bucket': 117, 'liquidity_bucket': 190, 'overbought_bucket': 164, 'risk_context_bucket': 7, 'score_bucket': 1}`
- score_source_missing_count: `0`
- score_source_missing_provenance: `{}`
- adm_source_bucket_used_count: `199`
- recomputed_unknown_count: `1561`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 4 | 0 | 0.0 | None | 0 | 0 |
| `WAIT_REQUOTE` | 109 | 1 | 0.0116 | 1.26 | 0 | 0 |
| `SKIP_STALE` | 0 | 0 | None | None | 0 | 0 |
| `BUY_DEFENSIVE` | 16 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 254 | 2 | -0.0278 | -3.535 | 1 | 2 |
| `SKIP_SOURCE_QUALITY` | 5 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 8 | 1 | -0.0437 | -0.35 | 1 | 1 |

## Top Buckets
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`71` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1200_1400` sample=`65` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`27` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|risk_unknown|-|stale_not_available|defensive_limit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`20` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`11` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1000_1200` sample=`11` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score50_64|neutral_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1200_1400` sample=`10` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_lt50|weak_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`10` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score50_64|neutral_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1200_1400` sample=`8` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_0900_1000` sample=`8` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`

## Warnings
- `joined_sample_below_sample_floor`
- `unknown_bucket_source_quality_gap`
