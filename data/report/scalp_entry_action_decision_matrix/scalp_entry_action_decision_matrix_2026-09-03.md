# Scalp Entry Action Decision Matrix - 2026-09-03

## Contract
- status: `pass`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `672`
- joined_sample/sample_floor: `12` / `20`
- joined_sample_cumulative/floor_met: `2650` / `True`
- prompt_applied_count: `289`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 672}`
- forced_action_counts: `{'-': 672}`
- action_counts: `{'WAIT_REQUOTE': 259, 'SKIP_STALE': 5, 'BUY_DEFENSIVE': 43, 'NO_BUY_AI': 326, 'SKIP_PRE_SUBMIT_SAFETY': 32, 'SKIP_SOURCE_QUALITY': 7}`
- missing_actions: `[]`
- zero_sample_actions: `['BUY_NOW']`
- unknown_bucket_affected_rows: `0`
- unknown_dimension_occurrence_count: `0`
- unknown_bucket_not_available_rows: `383`
- not_available_dimension_occurrence_count: `1269`
- unknown_bucket_dimension_counts: `{}`
- unknown_bucket_not_available_dimension_counts: `{'stale_bucket': 264, 'price_resolution_bucket': 252, 'liquidity_bucket': 379, 'overbought_bucket': 339, 'risk_context_bucket': 35}`
- score_source_missing_count: `0`
- score_source_missing_provenance: `{}`
- adm_source_bucket_used_count: `289`
- recomputed_unknown_count: `2961`
- entry_price_skip_followup_cumulative_status: `collecting_mature_followups`
- entry_price_skip_followup_90s_sample/floor: `0` / `20`
- entry_price_skip_followup_sample_floor_met: `False`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 0 | 0 | None | None | 0 | 0 |
| `WAIT_REQUOTE` | 259 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 5 | 0 | 0.0 | None | 0 | 0 |
| `BUY_DEFENSIVE` | 43 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 326 | 9 | -0.0519 | -1.88 | 3 | 9 |
| `SKIP_SOURCE_QUALITY` | 7 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 32 | 3 | -0.1913 | -2.04 | 1 | 2 |

## Top Buckets
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1200_1400` sample=`37` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_0900_1000` sample=`36` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`36` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_1400_close` sample=`35` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1000_1200` sample=`31` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_1000_1200` sample=`29` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_1200_1400` sample=`25` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`21` joined=`4` action=`NO_BUY_AI` sq_ev=`-0.2738`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1200_1400` sample=`19` joined=`1` action=`NO_BUY_AI` sq_ev=`-0.0847`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1400_close` sample=`16` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
