# Scalp Entry Action Decision Matrix - 2026-06-25

## Contract
- status: `warning`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `561`
- joined_sample/sample_floor: `61` / `20`
- prompt_applied_count: `463`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 561}`
- forced_action_counts: `{'-': 561}`
- action_counts: `{'NO_BUY_AI': 502, 'SKIP_PRE_SUBMIT_SAFETY': 33, 'BUY_NOW': 20, 'SKIP_SOURCE_QUALITY': 1, 'BUY_DEFENSIVE': 5}`
- missing_actions: `[]`
- zero_sample_actions: `['WAIT_REQUOTE', 'SKIP_STALE']`
- unknown_bucket_affected_rows: `12`
- unknown_dimension_occurrence_count: `16`
- unknown_bucket_not_available_rows: `98`
- not_available_dimension_occurrence_count: `239`
- unknown_bucket_dimension_counts: `{'risk_context_bucket': 12, 'price_resolution_bucket': 4}`
- unknown_bucket_not_available_dimension_counts: `{'stale_bucket': 73, 'price_resolution_bucket': 53, 'liquidity_bucket': 62, 'overbought_bucket': 14, 'risk_context_bucket': 33, 'score_bucket': 4}`
- adm_source_bucket_used_count: `463`
- recomputed_unknown_count: `1111`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 20 | 2 | -0.16 | -1.6 | 0 | 0 |
| `WAIT_REQUOTE` | 0 | 0 | None | None | 0 | 0 |
| `SKIP_STALE` | 0 | 0 | None | None | 0 | 0 |
| `BUY_DEFENSIVE` | 5 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 497 | 36 | -0.1128 | -1.5578 | 18 | 32 |
| `SKIP_SOURCE_QUALITY` | 1 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 33 | 23 | -1.0336 | -1.483 | 11 | 18 |

## Top Buckets
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1400_close` sample=`68` joined=`1` action=`NO_BUY_AI` sq_ev=`-0.0313`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_0900_1000` sample=`41` joined=`4` action=`NO_BUY_AI` sq_ev=`-0.2222`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`39` joined=`2` action=`NO_BUY_AI` sq_ev=`-0.0995`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1200_1400` sample=`34` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_0900_1000` sample=`24` joined=`5` action=`NO_BUY_AI` sq_ev=`-0.4329`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_0900_1000` sample=`22` joined=`2` action=`NO_BUY_AI` sq_ev=`-0.2559`
- `score50_64|neutral_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1400_close` sample=`21` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|strong_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1400_close` sample=`19` joined=`1` action=`NO_BUY_AI` sq_ev=`-0.1126`
- `score50_64|strong_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1400_close` sample=`16` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1200_1400` sample=`13` joined=`2` action=`NO_BUY_AI` sq_ev=`-0.2877`

## Warnings
- `ai_numeric_consistency_rows_excluded_from_aggregates`
