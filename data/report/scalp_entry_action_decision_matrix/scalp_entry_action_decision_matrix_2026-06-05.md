# Scalp Entry Action Decision Matrix - 2026-06-05

## Contract
- status: `warning`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `471`
- joined_sample/sample_floor: `105` / `20`
- prompt_applied_count: `271`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 471}`
- forced_action_counts: `{'-': 471}`
- action_counts: `{'WAIT_REQUOTE': 6, 'BUY_NOW': 2, 'NO_BUY_AI': 388, 'SKIP_PRE_SUBMIT_SAFETY': 73, 'SKIP_SOURCE_QUALITY': 1, 'BUY_DEFENSIVE': 1}`
- missing_actions: `[]`
- zero_sample_actions: `['SKIP_STALE']`
- unknown_bucket_affected_rows: `469`
- unknown_bucket_dimension_counts: `{'price_resolution_bucket': 395, 'risk_context_bucket': 356, 'score_bucket': 88}`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 2 | 0 | 0.0 | None | 0 | 0 |
| `WAIT_REQUOTE` | 6 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 0 | 0 | None | None | 0 | 0 |
| `BUY_DEFENSIVE` | 1 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 388 | 39 | -0.1199 | -1.1933 | 14 | 29 |
| `SKIP_SOURCE_QUALITY` | 1 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 73 | 66 | -0.906 | -1.0021 | 36 | 47 |

## Top Buckets
- `score50_64|risk_unknown|-|fresh|price_unknown|liquidity_not_available|overbought_not_available|time_1000_1200` sample=`92` joined=`11` action=`NO_BUY_AI` sq_ev=`-0.1889`
- `score50_64|risk_unknown|-|fresh|price_unknown|liquidity_not_available|overbought_not_available|time_0900_1000` sample=`64` joined=`1` action=`NO_BUY_AI` sq_ev=`-0.0331`
- `score50_64|risk_unknown|-|fresh|price_unknown|liquidity_not_available|overbought_not_available|time_1200_1400` sample=`37` joined=`16` action=`NO_BUY_AI` sq_ev=`-0.1673`
- `score_unknown|risk_unknown|-|stale_not_available|resolved_price|below_min_liquidity|overbought_ok|time_1200_1400` sample=`28` joined=`27` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-0.6018`
- `score_unknown|risk_unknown|-|stale_not_available|resolved_price|below_min_liquidity|overbought_ok|time_1400_close` sample=`17` joined=`14` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-1.677`
- `score50_64|risk_unknown|-|fresh|price_unknown|liquidity_not_available|overbought_not_available|time_1400_close` sample=`15` joined=`6` action=`NO_BUY_AI` sq_ev=`-0.584`
- `score50_64|weak_strength_momentum|-|fresh|price_unknown|liquidity_not_available|overbought_normal|time_0900_1000` sample=`15` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|stale_not_available|price_unknown|liquidity_not_available|overbought_normal|time_0900_1000` sample=`15` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_unknown|risk_unknown|-|stale_not_available|resolved_price|below_min_liquidity|overbought_ok|time_1000_1200` sample=`15` joined=`15` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-0.8253`
- `score_unknown|risk_unknown|-|stale_not_available|price_unknown|liquidity_not_available|overbought_not_available|time_1400_close` sample=`14` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`

## Warnings
- `unknown_bucket_source_quality_gap`
