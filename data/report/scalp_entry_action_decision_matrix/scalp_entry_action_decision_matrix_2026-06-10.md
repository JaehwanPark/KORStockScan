# Scalp Entry Action Decision Matrix - 2026-06-10

## Contract
- status: `warning`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `506`
- joined_sample/sample_floor: `0` / `20`
- prompt_applied_count: `263`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 506}`
- forced_action_counts: `{'-': 506}`
- action_counts: `{'WAIT_REQUOTE': 23, 'BUY_NOW': 24, 'NO_BUY_AI': 298, 'SKIP_PRE_SUBMIT_SAFETY': 145, 'SKIP_SOURCE_QUALITY': 16}`
- missing_actions: `[]`
- zero_sample_actions: `['SKIP_STALE', 'BUY_DEFENSIVE']`
- unknown_bucket_affected_rows: `243`
- unknown_dimension_occurrence_count: `447`
- unknown_bucket_not_available_rows: `243`
- not_available_dimension_occurrence_count: `371`
- unknown_bucket_dimension_counts: `{'price_resolution_bucket': 115, 'score_bucket': 166, 'risk_context_bucket': 166}`
- unknown_bucket_not_available_dimension_counts: `{'stale_bucket': 215, 'liquidity_bucket': 118, 'overbought_bucket': 38}`
- adm_source_bucket_used_count: `263`
- recomputed_unknown_count: `1964`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 24 | 0 | 0.0 | None | 0 | 0 |
| `WAIT_REQUOTE` | 23 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 0 | 0 | None | None | 0 | 0 |
| `BUY_DEFENSIVE` | 0 | 0 | None | None | 0 | 0 |
| `NO_BUY_AI` | 298 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_SOURCE_QUALITY` | 16 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 145 | 0 | 0.0 | None | 0 | 0 |

## Top Buckets
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`114` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_0900_1000` sample=`61` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_unknown|risk_unknown|-|stale_not_available|defensive_limit|below_min_liquidity|overbought_ok|time_1000_1200` sample=`42` joined=`0` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`0.0`
- `score_unknown|risk_unknown|-|stale_not_available|resolved_price|below_min_liquidity|overbought_ok|time_0900_1000` sample=`28` joined=`0` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`0.0`
- `score_unknown|risk_unknown|-|stale_not_available|price_unknown|liquidity_not_available|overbought_not_available|time_1000_1200` sample=`24` joined=`0` action=`BUY_NOW` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1200_1400` sample=`18` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|stale_block|price_unknown|liquidity_not_available|overbought_normal|time_0900_1000` sample=`15` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|stale_not_available|price_unknown|liquidity_not_available|overbought_normal|time_0900_1000` sample=`14` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_0900_1000` sample=`13` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_unknown|risk_unknown|-|stale_not_available|defensive_limit|below_min_liquidity|not_evaluated|time_0900_1000` sample=`11` joined=`0` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`0.0`

## Warnings
- `joined_sample_below_sample_floor`
- `unknown_bucket_source_quality_gap`
