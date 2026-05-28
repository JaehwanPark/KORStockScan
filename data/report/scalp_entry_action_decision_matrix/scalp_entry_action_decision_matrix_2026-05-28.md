# Scalp Entry Action Decision Matrix - 2026-05-28

## Contract
- status: `pass`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `482`
- joined_sample/sample_floor: `184` / `20`
- prompt_applied_count: `193`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 482}`
- forced_action_counts: `{'-': 482}`
- action_counts: `{'WAIT_REQUOTE': 11, 'NO_BUY_AI': 304, 'SKIP_PRE_SUBMIT_SAFETY': 153, 'SKIP_SOURCE_QUALITY': 4, 'BUY_NOW': 8, 'BUY_DEFENSIVE': 2}`
- missing_actions: `[]`
- zero_sample_actions: `['SKIP_STALE']`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 8 | 5 | -0.4437 | -0.71 | 0 | 0 |
| `WAIT_REQUOTE` | 11 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 0 | 0 | None | None | 0 | 0 |
| `BUY_DEFENSIVE` | 2 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 304 | 27 | 0.0589 | 0.6637 | 5 | 11 |
| `SKIP_SOURCE_QUALITY` | 4 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 153 | 152 | -0.6905 | -0.695 | 54 | 89 |

## Top Buckets
- `score_unknown|risk_unknown|-|stale_unknown|resolved_price|below_min_liquidity|overbought_unknown|time_0900_1000` sample=`55` joined=`55` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-0.8833`
- `score50_64|risk_unknown|-|fresh|price_unknown|liquidity_unknown|overbought_unknown|time_1000_1200` sample=`39` joined=`5` action=`NO_BUY_AI` sq_ev=`-0.1887`
- `score50_64|risk_unknown|-|fresh|price_unknown|liquidity_unknown|overbought_unknown|time_0900_1000` sample=`35` joined=`4` action=`NO_BUY_AI` sq_ev=`-0.0346`
- `score_unknown|risk_unknown|-|stale_unknown|resolved_price|below_min_liquidity|overbought_unknown|time_1200_1400` sample=`35` joined=`34` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-0.5386`
- `score_unknown|risk_unknown|-|stale_unknown|resolved_price|below_min_liquidity|overbought_unknown|time_1000_1200` sample=`31` joined=`31` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-0.8997`
- `score50_64|risk_unknown|-|fresh|price_unknown|liquidity_unknown|overbought_unknown|time_1200_1400` sample=`26` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|price_unknown|liquidity_unknown|overbought_normal|time_0900_1000` sample=`20` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_unknown|risk_unknown|-|stale_unknown|defensive_limit|below_min_liquidity|overbought_unknown|time_1000_1200` sample=`18` joined=`18` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-0.1161`
- `score_unknown|risk_unknown|-|stale_unknown|price_unknown|liquidity_unknown|overbought_unknown|time_1400_close` sample=`16` joined=`16` action=`NO_BUY_AI` sq_ev=`1.7625`
- `score50_64|risk_unknown|-|fresh|price_unknown|liquidity_unknown|overbought_unknown|time_1400_close` sample=`15` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
