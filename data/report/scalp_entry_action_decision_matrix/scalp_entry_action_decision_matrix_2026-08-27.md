# Scalp Entry Action Decision Matrix - 2026-08-27

## Contract
- status: `pass`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `701`
- joined_sample/sample_floor: `10` / `20`
- joined_sample_cumulative/floor_met: `2597` / `True`
- prompt_applied_count: `259`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 701}`
- forced_action_counts: `{'-': 701}`
- action_counts: `{'WAIT_REQUOTE': 293, 'BUY_DEFENSIVE': 61, 'NO_BUY_AI': 291, 'SKIP_PRE_SUBMIT_SAFETY': 47, 'SKIP_SOURCE_QUALITY': 4, 'SKIP_STALE': 4, 'BUY_NOW': 1}`
- missing_actions: `[]`
- zero_sample_actions: `[]`
- unknown_bucket_affected_rows: `0`
- unknown_dimension_occurrence_count: `0`
- unknown_bucket_not_available_rows: `442`
- not_available_dimension_occurrence_count: `1411`
- unknown_bucket_dimension_counts: `{}`
- unknown_bucket_not_available_dimension_counts: `{'stale_bucket': 276, 'price_resolution_bucket': 253, 'liquidity_bucket': 436, 'overbought_bucket': 397, 'risk_context_bucket': 49}`
- score_source_missing_count: `0`
- score_source_missing_provenance: `{}`
- adm_source_bucket_used_count: `259`
- recomputed_unknown_count: `3346`
- entry_price_skip_followup_cumulative_status: `collecting_mature_followups`
- entry_price_skip_followup_90s_sample/floor: `0` / `20`
- entry_price_skip_followup_sample_floor_met: `False`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 1 | 0 | 0.0 | None | 0 | 0 |
| `WAIT_REQUOTE` | 293 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 4 | 0 | 0.0 | None | 0 | 0 |
| `BUY_DEFENSIVE` | 61 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 291 | 4 | -0.0004 | -0.03 | 0 | 1 |
| `SKIP_SOURCE_QUALITY` | 4 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 47 | 6 | 0.0336 | 0.2633 | 1 | 1 |

## Top Buckets
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1000_1200` sample=`49` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1200_1400` sample=`48` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_0900_1000` sample=`45` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_1400_close` sample=`26` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_1000_1200` sample=`25` joined=`1` action=`NO_BUY_AI` sq_ev=`-0.1208`
- `score_lt50|strong_strength_momentum|-|fresh|defensive_limit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`22` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1400_close` sample=`21` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`20` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score50_64|strong_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1400_close` sample=`18` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_ok|time_1000_1200` sample=`16` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
