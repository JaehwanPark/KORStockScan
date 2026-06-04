# Scalp Entry Action Decision Matrix - 2026-06-04

## Contract
- status: `warning`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `136`
- joined_sample/sample_floor: `13` / `20`
- prompt_applied_count: `0`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 136}`
- forced_action_counts: `{'-': 136}`
- action_counts: `{'BUY_NOW': 5, 'WAIT_REQUOTE': 7, 'NO_BUY_AI': 113, 'SKIP_SOURCE_QUALITY': 2, 'SKIP_PRE_SUBMIT_SAFETY': 8, 'BUY_DEFENSIVE': 1}`
- missing_actions: `[]`
- zero_sample_actions: `['SKIP_STALE']`
- unknown_bucket_affected_rows: `136`
- unknown_bucket_dimension_counts: `{'stale_bucket': 71, 'liquidity_bucket': 119, 'price_resolution_bucket': 114, 'risk_context_bucket': 75, 'overbought_bucket': 50, 'score_bucket': 36}`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 5 | 1 | -0.42 | -2.1 | 1 | 0 |
| `WAIT_REQUOTE` | 7 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 0 | 0 | None | None | 0 | 0 |
| `BUY_DEFENSIVE` | 1 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 113 | 10 | -0.12 | -1.356 | 2 | 8 |
| `SKIP_SOURCE_QUALITY` | 2 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 8 | 2 | -0.4487 | -1.795 | 2 | 2 |

## Top Buckets
- `score50_64|risk_unknown|-|fresh|price_unknown|liquidity_unknown|overbought_unknown|time_1400_close` sample=`22` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_unknown|risk_unknown|-|stale_unknown|price_unknown|liquidity_unknown|overbought_unknown|time_1400_close` sample=`18` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|neutral_strength_momentum|-|stale_unknown|price_unknown|liquidity_unknown|overbought_watch|time_1400_close` sample=`14` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|stale_unknown|price_unknown|liquidity_unknown|overbought_normal|time_1400_close` sample=`9` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|risk_unknown|-|fresh|price_unknown|liquidity_unknown|overbought_ok|time_1400_close` sample=`6` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|price_unknown|liquidity_unknown|overbought_watch|time_1400_close` sample=`5` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_unknown|risk_unknown|-|stale_unknown|quote_based|liquidity_ok|overbought_ok|time_1400_close` sample=`5` joined=`5` action=`NO_BUY_AI` sq_ev=`-1.34`
- `score50_64|neutral_strength_momentum|-|fresh|price_unknown|liquidity_unknown|overbought_watch|time_1400_close` sample=`4` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|risk_unknown|-|stale_block|price_unknown|liquidity_unknown|overbought_unknown|time_1400_close` sample=`4` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|neutral_strength_momentum|-|stale_unknown|price_unknown|liquidity_unknown|overbought_normal|time_1400_close` sample=`3` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`

## Warnings
- `joined_sample_below_sample_floor`
- `unknown_bucket_source_quality_gap`
- `prompt_context_not_loaded`
