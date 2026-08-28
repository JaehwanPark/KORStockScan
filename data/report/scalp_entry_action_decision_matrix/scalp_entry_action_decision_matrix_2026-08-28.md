# Scalp Entry Action Decision Matrix - 2026-08-28

## Contract
- status: `pass`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `649`
- joined_sample/sample_floor: `9` / `20`
- joined_sample_cumulative/floor_met: `2606` / `True`
- prompt_applied_count: `291`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 649}`
- forced_action_counts: `{'-': 649}`
- action_counts: `{'WAIT_REQUOTE': 219, 'BUY_DEFENSIVE': 59, 'NO_BUY_AI': 318, 'SKIP_PRE_SUBMIT_SAFETY': 44, 'SKIP_SOURCE_QUALITY': 4, 'SKIP_STALE': 5}`
- missing_actions: `[]`
- zero_sample_actions: `['BUY_NOW']`
- unknown_bucket_affected_rows: `0`
- unknown_dimension_occurrence_count: `0`
- unknown_bucket_not_available_rows: `358`
- not_available_dimension_occurrence_count: `1172`
- unknown_bucket_dimension_counts: `{}`
- unknown_bucket_not_available_dimension_counts: `{'liquidity_bucket': 356, 'overbought_bucket': 325, 'stale_bucket': 234, 'price_resolution_bucket': 212, 'risk_context_bucket': 45}`
- score_source_missing_count: `0`
- score_source_missing_provenance: `{}`
- adm_source_bucket_used_count: `291`
- recomputed_unknown_count: `2789`
- entry_price_skip_followup_cumulative_status: `collecting_mature_followups`
- entry_price_skip_followup_90s_sample/floor: `0` / `20`
- entry_price_skip_followup_sample_floor_met: `False`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 0 | 0 | None | None | 0 | 0 |
| `WAIT_REQUOTE` | 219 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 5 | 0 | 0.0 | None | 0 | 0 |
| `BUY_DEFENSIVE` | 59 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 318 | 7 | -0.0208 | -0.9443 | 2 | 5 |
| `SKIP_SOURCE_QUALITY` | 4 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 44 | 2 | -0.1093 | -2.405 | 1 | 2 |

## Top Buckets
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1200_1400` sample=`47` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1400_close` sample=`44` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1000_1200` sample=`34` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`32` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_1400_close` sample=`30` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`26` joined=`3` action=`NO_BUY_AI` sq_ev=`-0.1038`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_1200_1400` sample=`26` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_0900_1000` sample=`18` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_1000_1200` sample=`17` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_lt50|strong_strength_momentum|-|fresh|defensive_limit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`16` joined=`0` action=`BUY_DEFENSIVE` sq_ev=`0.0`
