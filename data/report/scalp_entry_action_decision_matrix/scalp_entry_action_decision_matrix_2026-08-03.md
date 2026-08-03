# Scalp Entry Action Decision Matrix - 2026-08-03

## Contract
- status: `warning`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `1098`
- joined_sample/sample_floor: `2` / `20`
- prompt_applied_count: `378`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 1098}`
- forced_action_counts: `{'-': 1098}`
- action_counts: `{'WAIT_REQUOTE': 378, 'BUY_DEFENSIVE': 50, 'SKIP_STALE': 8, 'NO_BUY_AI': 519, 'SKIP_PRE_SUBMIT_SAFETY': 143}`
- missing_actions: `[]`
- zero_sample_actions: `['BUY_NOW', 'SKIP_SOURCE_QUALITY']`
- unknown_bucket_affected_rows: `4`
- unknown_dimension_occurrence_count: `4`
- unknown_bucket_not_available_rows: `720`
- not_available_dimension_occurrence_count: `2571`
- unknown_bucket_dimension_counts: `{'risk_context_bucket': 4}`
- unknown_bucket_not_available_dimension_counts: `{'stale_bucket': 533, 'price_resolution_bucket': 597, 'liquidity_bucket': 720, 'overbought_bucket': 582, 'risk_context_bucket': 139}`
- score_source_missing_count: `0`
- score_source_missing_provenance: `{}`
- adm_source_bucket_used_count: `378`
- recomputed_unknown_count: `5404`
- entry_price_skip_followup_cumulative_status: `collecting_mature_followups`
- entry_price_skip_followup_90s_sample/floor: `0` / `20`
- entry_price_skip_followup_sample_floor_met: `False`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 0 | 0 | None | None | 0 | 0 |
| `WAIT_REQUOTE` | 378 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 8 | 0 | 0.0 | None | 0 | 0 |
| `BUY_DEFENSIVE` | 50 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 519 | 1 | 0.0021 | 1.11 | 0 | 0 |
| `SKIP_SOURCE_QUALITY` | 0 | 0 | None | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 143 | 1 | -0.0112 | -1.6 | 1 | 1 |

## Top Buckets
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_0900_1000` sample=`129` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`116` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_1400_close` sample=`54` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_0900_1000` sample=`41` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score65_74|risk_context_not_available|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1000_1200` sample=`38` joined=`0` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_1000_1200` sample=`35` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_1200_1400` sample=`29` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_lt50|weak_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_0900_1000` sample=`27` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score65_74|risk_context_not_available|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1200_1400` sample=`25` joined=`0` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|fresh|defensive_limit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`22` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`

## Warnings
- `joined_sample_below_sample_floor`
- `sim_post_sell_outcome_source_below_sample_floor`
- `unknown_bucket_source_quality_gap`
