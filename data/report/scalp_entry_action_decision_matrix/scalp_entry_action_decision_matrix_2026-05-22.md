# Scalp Entry Action Decision Matrix - 2026-05-22

## Contract
- status: `pass`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `1327`
- joined_sample/sample_floor: `102` / `20`
- prompt_applied_count: `1132`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 1327}`
- forced_action_counts: `{'-': 1327}`
- action_counts: `{'NO_BUY_AI': 1317, 'SKIP_PRE_SUBMIT_SAFETY': 4, 'SKIP_SOURCE_QUALITY': 1, 'WAIT_REQUOTE': 5}`
- missing_actions: `[]`
- zero_sample_actions: `['BUY_NOW', 'SKIP_STALE', 'BUY_DEFENSIVE']`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 0 | 0 | None | None | 0 | 0 |
| `WAIT_REQUOTE` | 5 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 0 | 0 | None | None | 0 | 0 |
| `BUY_DEFENSIVE` | 0 | 0 | None | None | 0 | 0 |
| `NO_BUY_AI` | 1317 | 102 | -0.0523 | -0.6758 | 43 | 62 |
| `SKIP_SOURCE_QUALITY` | 1 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 4 | 0 | 0.0 | None | 0 | 0 |

## Top Buckets
- `score50_64|risk_unknown|-|fresh|price_unknown|liquidity_unknown|overbought_unknown|time_1000_1200` sample=`220` joined=`25` action=`NO_BUY_AI` sq_ev=`-0.1174`
- `score50_64|risk_unknown|-|fresh|price_unknown|liquidity_unknown|overbought_unknown|time_1200_1400` sample=`175` joined=`3` action=`NO_BUY_AI` sq_ev=`-0.018`
- `score50_64|risk_unknown|-|stale_unknown|price_unknown|liquidity_unknown|overbought_unknown|time_1200_1400` sample=`167` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|risk_unknown|-|stale_unknown|price_unknown|liquidity_unknown|overbought_unknown|time_1000_1200` sample=`118` joined=`2` action=`NO_BUY_AI` sq_ev=`-0.009`
- `score50_64|risk_unknown|-|fresh|price_unknown|liquidity_unknown|overbought_unknown|time_0900_1000` sample=`112` joined=`47` action=`NO_BUY_AI` sq_ev=`-0.2564`
- `score50_64|risk_unknown|-|stale_unknown|price_unknown|liquidity_unknown|overbought_unknown|time_0900_1000` sample=`71` joined=`11` action=`NO_BUY_AI` sq_ev=`-0.1182`
- `score50_64|risk_unknown|-|fresh|price_unknown|liquidity_unknown|overbought_unknown|time_1400_close` sample=`58` joined=`1` action=`NO_BUY_AI` sq_ev=`0.0267`
- `score50_64|risk_unknown|-|stale_unknown|price_unknown|liquidity_unknown|overbought_unknown|time_1400_close` sample=`37` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|risk_unknown|-|stale_block|price_unknown|liquidity_unknown|overbought_unknown|time_1200_1400` sample=`22` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|strong_strength_momentum|-|fresh|price_unknown|liquidity_unknown|overbought_normal|time_0900_1000` sample=`21` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
