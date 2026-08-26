# Scalp Entry Action Decision Matrix - 2026-08-26

## Contract
- status: `pass`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `711`
- joined_sample/sample_floor: `15` / `20`
- joined_sample_cumulative/floor_met: `2587` / `True`
- prompt_applied_count: `261`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 711}`
- forced_action_counts: `{'-': 711}`
- action_counts: `{'WAIT_REQUOTE': 315, 'SKIP_PRE_SUBMIT_SAFETY': 34, 'BUY_DEFENSIVE': 55, 'NO_BUY_AI': 300, 'SKIP_STALE': 4, 'SKIP_SOURCE_QUALITY': 3}`
- missing_actions: `[]`
- zero_sample_actions: `['BUY_NOW']`
- unknown_bucket_affected_rows: `0`
- unknown_dimension_occurrence_count: `0`
- unknown_bucket_not_available_rows: `450`
- not_available_dimension_occurrence_count: `1494`
- unknown_bucket_dimension_counts: `{}`
- unknown_bucket_not_available_dimension_counts: `{'stale_bucket': 308, 'price_resolution_bucket': 299, 'liquidity_bucket': 446, 'overbought_bucket': 406, 'risk_context_bucket': 35}`
- score_source_missing_count: `0`
- score_source_missing_provenance: `{}`
- adm_source_bucket_used_count: `261`
- recomputed_unknown_count: `3410`
- entry_price_skip_followup_cumulative_status: `collecting_mature_followups`
- entry_price_skip_followup_90s_sample/floor: `0` / `20`
- entry_price_skip_followup_sample_floor_met: `False`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 0 | 0 | None | None | 0 | 0 |
| `WAIT_REQUOTE` | 315 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 4 | 0 | 0.0 | None | 0 | 0 |
| `BUY_DEFENSIVE` | 55 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 300 | 11 | -0.0507 | -1.3836 | 4 | 7 |
| `SKIP_SOURCE_QUALITY` | 3 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 34 | 4 | 0.0588 | 0.5 | 0 | 2 |

## Top Buckets
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1200_1400` sample=`57` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1000_1200` sample=`50` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`47` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_0900_1000` sample=`40` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_1400_close` sample=`25` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|fresh|defensive_limit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`21` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_1000_1200` sample=`17` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_1200_1400` sample=`17` joined=`1` action=`NO_BUY_AI` sq_ev=`-0.1535`
- `score50_64|neutral_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_ok|time_1400_close` sample=`16` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_lt50|weak_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_0900_1000` sample=`15` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
