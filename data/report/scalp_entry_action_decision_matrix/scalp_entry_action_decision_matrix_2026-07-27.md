# Scalp Entry Action Decision Matrix - 2026-07-27

## Contract
- status: `warning`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `165`
- joined_sample/sample_floor: `0` / `20`
- prompt_applied_count: `73`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 165}`
- forced_action_counts: `{'-': 165}`
- action_counts: `{'WAIT_REQUOTE': 58, 'NO_BUY_AI': 92, 'BUY_NOW': 7, 'BUY_DEFENSIVE': 7, 'SKIP_STALE': 1}`
- missing_actions: `[]`
- zero_sample_actions: `['SKIP_SOURCE_QUALITY', 'SKIP_PRE_SUBMIT_SAFETY']`
- unknown_bucket_affected_rows: `21`
- unknown_dimension_occurrence_count: `22`
- unknown_bucket_not_available_rows: `92`
- not_available_dimension_occurrence_count: `283`
- unknown_bucket_dimension_counts: `{'risk_context_bucket': 21, 'price_resolution_bucket': 1}`
- unknown_bucket_not_available_dimension_counts: `{'stale_bucket': 60, 'price_resolution_bucket': 41, 'liquidity_bucket': 92, 'overbought_bucket': 89, 'score_bucket': 1}`
- score_source_missing_count: `0`
- score_source_missing_provenance: `{}`
- adm_source_bucket_used_count: `73`
- recomputed_unknown_count: `715`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 7 | 0 | 0.0 | None | 0 | 0 |
| `WAIT_REQUOTE` | 58 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 1 | 0 | 0.0 | None | 0 | 0 |
| `BUY_DEFENSIVE` | 7 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 92 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_SOURCE_QUALITY` | 0 | 0 | None | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 0 | 0 | None | None | 0 | 0 |

## Top Buckets
- `score_lt50|risk_unknown|-|stale_not_available|defensive_limit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`12` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1400_close` sample=`11` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_1400_close` sample=`10` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_0900_1000` sample=`9` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`9` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|fresh|defensive_limit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`8` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_0900_1000` sample=`5` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score65_74|neutral_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1400_close` sample=`4` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score65_74|neutral_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_1200_1400` sample=`4` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_1000_1200` sample=`4` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`

## Warnings
- `joined_sample_below_sample_floor`
- `unknown_bucket_source_quality_gap`
