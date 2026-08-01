# Scalp Entry Action Decision Matrix - 2026-07-31

## Contract
- status: `warning`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `645`
- joined_sample/sample_floor: `3` / `20`
- prompt_applied_count: `245`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 645}`
- forced_action_counts: `{'-': 645}`
- action_counts: `{'BUY_DEFENSIVE': 28, 'NO_BUY_AI': 358, 'WAIT_REQUOTE': 181, 'SKIP_PRE_SUBMIT_SAFETY': 76, 'SKIP_STALE': 2}`
- missing_actions: `[]`
- zero_sample_actions: `['BUY_NOW', 'SKIP_SOURCE_QUALITY']`
- unknown_bucket_affected_rows: `0`
- unknown_dimension_occurrence_count: `0`
- unknown_bucket_not_available_rows: `400`
- not_available_dimension_occurrence_count: `1417`
- unknown_bucket_dimension_counts: `{}`
- unknown_bucket_not_available_dimension_counts: `{'liquidity_bucket': 400, 'overbought_bucket': 294, 'stale_bucket': 305, 'price_resolution_bucket': 343, 'risk_context_bucket': 75}`
- score_source_missing_count: `0`
- score_source_missing_provenance: `{}`
- adm_source_bucket_used_count: `245`
- recomputed_unknown_count: `3029`
- entry_price_skip_followup_cumulative_status: `collecting_mature_followups`
- entry_price_skip_followup_90s_sample/floor: `0` / `20`
- entry_price_skip_followup_sample_floor_met: `False`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 0 | 0 | None | None | 0 | 0 |
| `WAIT_REQUOTE` | 181 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 2 | 0 | 0.0 | None | 0 | 0 |
| `BUY_DEFENSIVE` | 28 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 358 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_SOURCE_QUALITY` | 0 | 0 | None | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 76 | 3 | -0.0722 | -1.83 | 2 | 2 |

## Top Buckets
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_0900_1000` sample=`53` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_ok|time_1400_close` sample=`48` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`41` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_0900_1000` sample=`26` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|neutral_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_ok|time_1400_close` sample=`24` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_1000_1200` sample=`24` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_lt50|weak_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_0900_1000` sample=`22` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1000_1200` sample=`21` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score65_74|risk_context_not_available|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`20` joined=`0` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`19` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`

## Warnings
- `joined_sample_below_sample_floor`
- `sim_post_sell_outcome_source_below_sample_floor`
