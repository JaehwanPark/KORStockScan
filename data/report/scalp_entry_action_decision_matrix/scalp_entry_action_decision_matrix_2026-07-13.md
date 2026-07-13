# Scalp Entry Action Decision Matrix - 2026-07-13

## Contract
- status: `warning`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `202`
- joined_sample/sample_floor: `9` / `20`
- prompt_applied_count: `55`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 202}`
- forced_action_counts: `{'-': 202}`
- action_counts: `{'BUY_DEFENSIVE': 7, 'WAIT_REQUOTE': 107, 'NO_BUY_AI': 82, 'SKIP_PRE_SUBMIT_SAFETY': 5, 'SKIP_STALE': 1}`
- missing_actions: `[]`
- zero_sample_actions: `['BUY_NOW', 'SKIP_SOURCE_QUALITY']`
- unknown_bucket_affected_rows: `23`
- unknown_dimension_occurrence_count: `24`
- unknown_bucket_not_available_rows: `147`
- not_available_dimension_occurrence_count: `468`
- unknown_bucket_dimension_counts: `{'risk_context_bucket': 23, 'price_resolution_bucket': 1}`
- unknown_bucket_not_available_dimension_counts: `{'liquidity_bucket': 142, 'overbought_bucket': 138, 'stale_bucket': 103, 'price_resolution_bucket': 79, 'risk_context_bucket': 5, 'score_bucket': 1}`
- score_source_missing_count: `0`
- score_source_missing_provenance: `{}`
- adm_source_bucket_used_count: `55`
- recomputed_unknown_count: `1075`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 0 | 0 | None | None | 0 | 0 |
| `WAIT_REQUOTE` | 107 | 2 | -0.0299 | -1.6 | 0 | 0 |
| `SKIP_STALE` | 1 | 0 | 0.0 | None | 0 | 0 |
| `BUY_DEFENSIVE` | 7 | 2 | -0.32 | -1.12 | 1 | 0 |
| `NO_BUY_AI` | 82 | 3 | -0.1211 | -3.31 | 2 | 3 |
| `SKIP_SOURCE_QUALITY` | 0 | 0 | None | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 5 | 2 | -1.286 | -3.215 | 2 | 2 |

## Top Buckets
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`35` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`28` joined=`1` action=`NO_BUY_AI` sq_ev=`-0.1096`
- `score_lt50|risk_unknown|-|stale_not_available|defensive_limit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`20` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_lt50|weak_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`12` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_0900_1000` sample=`8` joined=`1` action=`NO_BUY_AI` sq_ev=`-0.23`
- `score65_74|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`8` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1200_1400` sample=`7` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|fresh|defensive_limit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`6` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1200_1400` sample=`6` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_watch|defensive_limit|liquidity_not_available|overbought_not_available|time_0900_1000` sample=`6` joined=`1` action=`WAIT_REQUOTE` sq_ev=`0.2133`

## Warnings
- `joined_sample_below_sample_floor`
- `unknown_bucket_source_quality_gap`
