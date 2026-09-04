# Scalp Entry Action Decision Matrix - 2026-09-04

## Contract
- status: `pass`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `538`
- joined_sample/sample_floor: `2` / `20`
- joined_sample_cumulative/floor_met: `2652` / `True`
- prompt_applied_count: `254`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 538}`
- forced_action_counts: `{'-': 538}`
- action_counts: `{'WAIT_REQUOTE': 195, 'NO_BUY_AI': 284, 'SKIP_PRE_SUBMIT_SAFETY': 38, 'SKIP_STALE': 6, 'SKIP_SOURCE_QUALITY': 4, 'BUY_DEFENSIVE': 11}`
- missing_actions: `[]`
- zero_sample_actions: `['BUY_NOW']`
- unknown_bucket_affected_rows: `1`
- unknown_dimension_occurrence_count: `2`
- unknown_bucket_not_available_rows: `284`
- not_available_dimension_occurrence_count: `1027`
- unknown_bucket_dimension_counts: `{'risk_context_bucket': 1, 'price_resolution_bucket': 1}`
- unknown_bucket_not_available_dimension_counts: `{'stale_bucket': 243, 'price_resolution_bucket': 216, 'liquidity_bucket': 283, 'overbought_bucket': 251, 'risk_context_bucket': 33, 'score_bucket': 1}`
- score_source_missing_count: `0`
- score_source_missing_provenance: `{}`
- adm_source_bucket_used_count: `254`
- recomputed_unknown_count: `2233`
- entry_price_skip_followup_cumulative_status: `collecting_mature_followups`
- entry_price_skip_followup_90s_sample/floor: `0` / `20`
- entry_price_skip_followup_sample_floor_met: `False`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 0 | 0 | None | None | 0 | 0 |
| `WAIT_REQUOTE` | 195 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 6 | 0 | 0.0 | None | 0 | 0 |
| `BUY_DEFENSIVE` | 11 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 283 | 2 | -0.0112 | -1.59 | 1 | 2 |
| `SKIP_SOURCE_QUALITY` | 4 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 38 | 0 | 0.0 | None | 0 | 0 |

## Top Buckets
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`65` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1200_1400` sample=`32` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_0900_1000` sample=`23` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1000_1200` sample=`23` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1400_close` sample=`21` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_watch|time_1200_1400` sample=`21` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`20` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_watch|time_1400_close` sample=`19` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1200_1400` sample=`16` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_lt50|weak_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`16` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
