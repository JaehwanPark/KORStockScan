# Scalp Entry Action Decision Matrix - 2026-07-27

## Contract
- status: `warning`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `38`
- joined_sample/sample_floor: `0` / `20`
- prompt_applied_count: `17`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 38}`
- forced_action_counts: `{'-': 38}`
- action_counts: `{'WAIT_REQUOTE': 13, 'NO_BUY_AI': 21, 'BUY_NOW': 2, 'BUY_DEFENSIVE': 2}`
- missing_actions: `[]`
- zero_sample_actions: `['SKIP_STALE', 'SKIP_SOURCE_QUALITY', 'SKIP_PRE_SUBMIT_SAFETY']`
- unknown_bucket_affected_rows: `2`
- unknown_dimension_occurrence_count: `2`
- unknown_bucket_not_available_rows: `21`
- not_available_dimension_occurrence_count: `69`
- unknown_bucket_dimension_counts: `{'risk_context_bucket': 2}`
- unknown_bucket_not_available_dimension_counts: `{'stale_bucket': 16, 'price_resolution_bucket': 14, 'liquidity_bucket': 21, 'overbought_bucket': 18}`
- score_source_missing_count: `0`
- score_source_missing_provenance: `{}`
- adm_source_bucket_used_count: `17`
- recomputed_unknown_count: `164`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 2 | 0 | 0.0 | None | 0 | 0 |
| `WAIT_REQUOTE` | 13 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 0 | 0 | None | None | 0 | 0 |
| `BUY_DEFENSIVE` | 2 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 21 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_SOURCE_QUALITY` | 0 | 0 | None | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 0 | 0 | None | None | 0 | 0 |

## Top Buckets
- `score_lt50|neutral_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_0900_1000` sample=`9` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_0900_1000` sample=`5` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|weak_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_0900_1000` sample=`4` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score65_74|neutral_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_0900_1000` sample=`2` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_watch|defensive_limit|liquidity_not_available|overbought_not_available|time_0900_1000` sample=`2` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|strong_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_chase_risk|time_0900_1000` sample=`2` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_lt50|weak_strength_momentum|-|stale_watch|resolved_price|liquidity_not_available|overbought_not_available|time_0900_1000` sample=`2` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|neutral_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_chase_risk|time_0900_1000` sample=`1` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_chase_risk|time_0900_1000` sample=`1` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_normal|time_1000_1200` sample=`1` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`

## Warnings
- `joined_sample_below_sample_floor`
- `unknown_bucket_source_quality_gap`
