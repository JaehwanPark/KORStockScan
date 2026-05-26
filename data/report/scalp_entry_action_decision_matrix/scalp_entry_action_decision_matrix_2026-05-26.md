# Scalp Entry Action Decision Matrix - 2026-05-26

## Contract
- status: `pass`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `1159`
- joined_sample/sample_floor: `168` / `20`
- prompt_applied_count: `784`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 1159}`
- forced_action_counts: `{'-': 1159}`
- action_counts: `{'SKIP_PRE_SUBMIT_SAFETY': 205, 'WAIT_REQUOTE': 1, 'NO_BUY_AI': 892, 'BUY_NOW': 43, 'SKIP_SOURCE_QUALITY': 3, 'BUY_DEFENSIVE': 15}`
- missing_actions: `[]`
- zero_sample_actions: `['SKIP_STALE']`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 43 | 26 | -0.2474 | -0.4092 | 6 | 0 |
| `WAIT_REQUOTE` | 1 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 0 | 0 | None | None | 0 | 0 |
| `BUY_DEFENSIVE` | 15 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 892 | 20 | -0.0237 | -1.0575 | 7 | 15 |
| `SKIP_SOURCE_QUALITY` | 3 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 205 | 122 | -0.3903 | -0.6558 | 45 | 69 |

## Top Buckets
- `score50_64|risk_unknown|-|fresh|price_unknown|liquidity_unknown|overbought_unknown|time_1000_1200` sample=`161` joined=`7` action=`NO_BUY_AI` sq_ev=`-0.0193`
- `score50_64|risk_unknown|-|fresh|price_unknown|liquidity_unknown|overbought_unknown|time_1200_1400` sample=`135` joined=`6` action=`NO_BUY_AI` sq_ev=`-0.0668`
- `score50_64|risk_unknown|-|fresh|price_unknown|liquidity_unknown|overbought_unknown|time_0900_1000` sample=`100` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_unknown|risk_unknown|-|stale_unknown|resolved_price|below_min_liquidity|overbought_unknown|time_0900_1000` sample=`96` joined=`41` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-0.3897`
- `score50_64|risk_unknown|-|fresh|price_unknown|liquidity_unknown|overbought_unknown|time_1400_close` sample=`52` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|risk_unknown|-|stale_block|price_unknown|liquidity_unknown|overbought_unknown|time_1200_1400` sample=`40` joined=`2` action=`NO_BUY_AI` sq_ev=`-0.1198`
- `score_unknown|risk_unknown|-|stale_unknown|resolved_price|below_min_liquidity|overbought_unknown|time_1000_1200` sample=`37` joined=`33` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-0.3638`
- `score50_64|risk_unknown|-|stale_block|price_unknown|liquidity_unknown|overbought_unknown|time_1000_1200` sample=`34` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|risk_unknown|-|fresh|price_unknown|liquidity_unknown|overbought_ok|time_1000_1200` sample=`28` joined=`1` action=`NO_BUY_AI` sq_ev=`0.0175`
- `score50_64|strong_strength_momentum|-|fresh|price_unknown|liquidity_unknown|overbought_normal|time_0900_1000` sample=`27` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
