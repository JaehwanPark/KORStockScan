# Scalp Entry Action Decision Matrix - 2026-06-26

## Contract
- status: `warning`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `543`
- joined_sample/sample_floor: `63` / `20`
- prompt_applied_count: `440`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 543}`
- forced_action_counts: `{'-': 543}`
- action_counts: `{'NO_BUY_AI': 486, 'SKIP_PRE_SUBMIT_SAFETY': 32, 'BUY_NOW': 14, 'BUY_DEFENSIVE': 9, 'SKIP_SOURCE_QUALITY': 1, 'SKIP_STALE': 1}`
- missing_actions: `[]`
- zero_sample_actions: `['WAIT_REQUOTE']`
- unknown_bucket_affected_rows: `14`
- unknown_dimension_occurrence_count: `18`
- unknown_bucket_not_available_rows: `103`
- not_available_dimension_occurrence_count: `264`
- unknown_bucket_dimension_counts: `{'risk_context_bucket': 13, 'price_resolution_bucket': 4, 'score_bucket': 1}`
- unknown_bucket_not_available_dimension_counts: `{'stale_bucket': 80, 'price_resolution_bucket': 57, 'liquidity_bucket': 71, 'risk_context_bucket': 33, 'overbought_bucket': 19, 'score_bucket': 4}`
- adm_source_bucket_used_count: `440`
- recomputed_unknown_count: `1120`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 14 | 3 | -0.5222 | -2.4367 | 2 | 0 |
| `WAIT_REQUOTE` | 0 | 0 | None | None | 0 | 0 |
| `SKIP_STALE` | 1 | 0 | 0.0 | None | 0 | 0 |
| `BUY_DEFENSIVE` | 9 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 481 | 36 | -0.105 | -1.4028 | 20 | 29 |
| `SKIP_SOURCE_QUALITY` | 1 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 32 | 24 | -1.1822 | -1.5762 | 18 | 21 |

## Top Buckets
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_0900_1000` sample=`54` joined=`5` action=`NO_BUY_AI` sq_ev=`-0.2185`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1400_close` sample=`51` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`48` joined=`5` action=`NO_BUY_AI` sq_ev=`-0.2002`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1200_1400` sample=`40` joined=`6` action=`NO_BUY_AI` sq_ev=`-0.2505`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_0900_1000` sample=`29` joined=`4` action=`NO_BUY_AI` sq_ev=`-0.2414`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_watch|time_0900_1000` sample=`23` joined=`1` action=`NO_BUY_AI` sq_ev=`-0.1165`
- `score50_64|strong_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1400_close` sample=`15` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|neutral_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`13` joined=`2` action=`NO_BUY_AI` sq_ev=`-0.28`
- `score50_64|neutral_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1400_close` sample=`12` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|neutral_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`10` joined=`2` action=`NO_BUY_AI` sq_ev=`-0.155`

## Warnings
- `unknown_bucket_source_quality_gap`
- `ai_numeric_consistency_rows_excluded_from_aggregates`
