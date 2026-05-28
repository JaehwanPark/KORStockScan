# Scalp Entry Action Decision Matrix - 2026-05-28

## Contract
- status: `pass`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `416`
- joined_sample/sample_floor: `139` / `20`
- prompt_applied_count: `160`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 416}`
- forced_action_counts: `{'-': 416}`
- action_counts: `{'WAIT_REQUOTE': 12, 'BUY_NOW': 7, 'NO_BUY_AI': 254, 'SKIP_PRE_SUBMIT_SAFETY': 139, 'SKIP_SOURCE_QUALITY': 4}`
- missing_actions: `[]`
- zero_sample_actions: `['SKIP_STALE', 'BUY_DEFENSIVE']`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 7 | 4 | -0.13 | -0.2275 | 0 | 0 |
| `WAIT_REQUOTE` | 12 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 0 | 0 | None | None | 0 | 0 |
| `BUY_DEFENSIVE` | 0 | 0 | None | None | 0 | 0 |
| `NO_BUY_AI` | 254 | 10 | -0.0333 | -0.847 | 4 | 6 |
| `SKIP_SOURCE_QUALITY` | 4 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 139 | 125 | -0.8227 | -0.9148 | 46 | 78 |

## Top Buckets
- `score_unknown|risk_unknown|-|stale_unknown|resolved_price|below_min_liquidity|overbought_unknown|time_0900_1000` sample=`55` joined=`55` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-0.8833`
- `score50_64|risk_unknown|-|fresh|price_unknown|liquidity_unknown|overbought_unknown|time_1000_1200` sample=`39` joined=`4` action=`NO_BUY_AI` sq_ev=`-0.1423`
- `score50_64|risk_unknown|-|fresh|price_unknown|liquidity_unknown|overbought_unknown|time_0900_1000` sample=`35` joined=`4` action=`NO_BUY_AI` sq_ev=`-0.0346`
- `score_unknown|risk_unknown|-|stale_unknown|resolved_price|below_min_liquidity|overbought_unknown|time_1000_1200` sample=`31` joined=`31` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-0.8997`
- `score_unknown|risk_unknown|-|stale_unknown|resolved_price|below_min_liquidity|overbought_unknown|time_1200_1400` sample=`22` joined=`12` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-1.0286`
- `score50_64|weak_strength_momentum|-|fresh|price_unknown|liquidity_unknown|overbought_normal|time_0900_1000` sample=`21` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|risk_unknown|-|fresh|price_unknown|liquidity_unknown|overbought_unknown|time_1200_1400` sample=`19` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_unknown|risk_unknown|-|stale_unknown|defensive_limit|below_min_liquidity|overbought_unknown|time_1000_1200` sample=`18` joined=`17` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-0.1111`
- `score50_64|risk_unknown|-|stale_block|price_unknown|liquidity_unknown|overbought_unknown|time_1000_1200` sample=`15` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|strong_strength_momentum|-|fresh|price_unknown|liquidity_unknown|overbought_normal|time_0900_1000` sample=`10` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
