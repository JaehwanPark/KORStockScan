# Scalp Entry Action Decision Matrix - 2026-08-24

## Contract
- status: `pass`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `673`
- joined_sample/sample_floor: `19` / `20`
- joined_sample_cumulative/floor_met: `2549` / `True`
- prompt_applied_count: `253`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 673}`
- forced_action_counts: `{'-': 673}`
- action_counts: `{'WAIT_REQUOTE': 283, 'BUY_DEFENSIVE': 54, 'NO_BUY_AI': 286, 'SKIP_SOURCE_QUALITY': 3, 'SKIP_STALE': 5, 'SKIP_PRE_SUBMIT_SAFETY': 42}`
- missing_actions: `[]`
- zero_sample_actions: `['BUY_NOW']`
- unknown_bucket_affected_rows: `3`
- unknown_dimension_occurrence_count: `6`
- unknown_bucket_not_available_rows: `420`
- not_available_dimension_occurrence_count: `1412`
- unknown_bucket_dimension_counts: `{'risk_context_bucket': 3, 'price_resolution_bucket': 3}`
- unknown_bucket_not_available_dimension_counts: `{'stale_bucket': 301, 'price_resolution_bucket': 288, 'liquidity_bucket': 405, 'overbought_bucket': 373, 'risk_context_bucket': 42, 'score_bucket': 3}`
- score_source_missing_count: `0`
- score_source_missing_provenance: `{}`
- adm_source_bucket_used_count: `253`
- recomputed_unknown_count: `3166`
- entry_price_skip_followup_cumulative_status: `collecting_mature_followups`
- entry_price_skip_followup_90s_sample/floor: `0` / `20`
- entry_price_skip_followup_sample_floor_met: `False`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 0 | 0 | None | None | 0 | 0 |
| `WAIT_REQUOTE` | 283 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 5 | 0 | 0.0 | None | 0 | 0 |
| `BUY_DEFENSIVE` | 54 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 283 | 8 | -0.0234 | -0.8287 | 2 | 6 |
| `SKIP_SOURCE_QUALITY` | 3 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 42 | 11 | -0.084 | -0.3209 | 4 | 7 |

## Top Buckets
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1200_1400` sample=`52` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1000_1200` sample=`48` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`46` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_0900_1000` sample=`45` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1400_close` sample=`35` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_1400_close` sample=`27` joined=`1` action=`NO_BUY_AI` sq_ev=`-0.037`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_1000_1200` sample=`23` joined=`1` action=`NO_BUY_AI` sq_ev=`-0.0687`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_0900_1000` sample=`21` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`16` joined=`3` action=`NO_BUY_AI` sq_ev=`-0.1637`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_1200_1400` sample=`16` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
