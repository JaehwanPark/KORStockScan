# Scalp Entry Action Decision Matrix - 2026-08-25

## Contract
- status: `pass`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `701`
- joined_sample/sample_floor: `23` / `20`
- joined_sample_cumulative/floor_met: `2572` / `True`
- prompt_applied_count: `254`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 701}`
- forced_action_counts: `{'-': 701}`
- action_counts: `{'WAIT_REQUOTE': 281, 'BUY_DEFENSIVE': 89, 'NO_BUY_AI': 275, 'SKIP_PRE_SUBMIT_SAFETY': 49, 'SKIP_STALE': 3, 'SKIP_SOURCE_QUALITY': 4}`
- missing_actions: `[]`
- zero_sample_actions: `['BUY_NOW']`
- unknown_bucket_affected_rows: `1`
- unknown_dimension_occurrence_count: `1`
- unknown_bucket_not_available_rows: `447`
- not_available_dimension_occurrence_count: `1401`
- unknown_bucket_dimension_counts: `{'risk_context_bucket': 1}`
- unknown_bucket_not_available_dimension_counts: `{'stale_bucket': 273, 'price_resolution_bucket': 239, 'liquidity_bucket': 432, 'overbought_bucket': 407, 'risk_context_bucket': 50}`
- score_source_missing_count: `0`
- score_source_missing_provenance: `{}`
- adm_source_bucket_used_count: `254`
- recomputed_unknown_count: `3355`
- entry_price_skip_followup_cumulative_status: `collecting_mature_followups`
- entry_price_skip_followup_90s_sample/floor: `0` / `20`
- entry_price_skip_followup_sample_floor_met: `False`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 0 | 0 | None | None | 0 | 0 |
| `WAIT_REQUOTE` | 281 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 3 | 0 | 0.0 | None | 0 | 0 |
| `BUY_DEFENSIVE` | 89 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 275 | 9 | -0.0466 | -1.4233 | 1 | 7 |
| `SKIP_SOURCE_QUALITY` | 4 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 49 | 14 | -0.2192 | -0.7671 | 6 | 8 |

## Top Buckets
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1200_1400` sample=`58` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_1400_close` sample=`42` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_0900_1000` sample=`37` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1000_1200` sample=`37` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_1000_1200` sample=`35` joined=`1` action=`NO_BUY_AI` sq_ev=`-0.108`
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`31` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_ok|time_1400_close` sample=`24` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_lt50|strong_strength_momentum|-|fresh|defensive_limit|liquidity_not_available|overbought_not_available|time_1200_1400` sample=`17` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|strong_strength_momentum|-|fresh|defensive_limit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`15` joined=`0` action=`BUY_DEFENSIVE` sq_ev=`0.0`
- `score_lt50|weak_strength_momentum|-|fresh|defensive_limit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`15` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
