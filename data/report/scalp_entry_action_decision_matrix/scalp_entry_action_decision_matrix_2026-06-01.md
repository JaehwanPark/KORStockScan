# Scalp Entry Action Decision Matrix - 2026-06-01

## Contract
- status: `pass`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `684`
- joined_sample/sample_floor: `262` / `20`
- prompt_applied_count: `305`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 684}`
- forced_action_counts: `{'-': 684}`
- action_counts: `{'NO_BUY_AI': 418, 'WAIT_REQUOTE': 5, 'SKIP_PRE_SUBMIT_SAFETY': 229, 'BUY_NOW': 13, 'BUY_DEFENSIVE': 17, 'SKIP_SOURCE_QUALITY': 2}`
- missing_actions: `[]`
- zero_sample_actions: `['SKIP_STALE']`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 13 | 11 | 0.0207 | 0.0245 | 3 | 0 |
| `WAIT_REQUOTE` | 5 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 0 | 0 | None | None | 0 | 0 |
| `BUY_DEFENSIVE` | 17 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 418 | 41 | -0.1342 | -1.3678 | 22 | 34 |
| `SKIP_SOURCE_QUALITY` | 2 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 229 | 210 | -0.8135 | -0.8871 | 83 | 140 |

## Top Buckets
- `score50_64|risk_unknown|-|fresh|price_unknown|liquidity_unknown|overbought_unknown|time_1000_1200` sample=`85` joined=`10` action=`NO_BUY_AI` sq_ev=`-0.1258`
- `score_unknown|risk_unknown|-|stale_unknown|resolved_price|below_min_liquidity|overbought_unknown|time_0900_1000` sample=`74` joined=`74` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-0.9935`
- `score_unknown|risk_unknown|-|stale_unknown|resolved_price|below_min_liquidity|overbought_unknown|time_1000_1200` sample=`60` joined=`60` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-0.255`
- `score50_64|risk_unknown|-|fresh|price_unknown|liquidity_unknown|overbought_unknown|time_0900_1000` sample=`35` joined=`5` action=`NO_BUY_AI` sq_ev=`-0.0423`
- `score50_64|risk_unknown|-|fresh|price_unknown|liquidity_unknown|overbought_unknown|time_1200_1400` sample=`32` joined=`10` action=`NO_BUY_AI` sq_ev=`-0.6472`
- `score_unknown|risk_unknown|-|stale_unknown|resolved_price|below_min_liquidity|overbought_unknown|time_1400_close` sample=`25` joined=`19` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-1.0072`
- `score50_64|risk_unknown|-|stale_block|price_unknown|liquidity_unknown|overbought_unknown|time_1000_1200` sample=`21` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|risk_unknown|-|stale_block|price_unknown|liquidity_unknown|overbought_unknown|time_1200_1400` sample=`16` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|risk_unknown|-|fresh|price_unknown|liquidity_unknown|overbought_ok|time_1000_1200` sample=`15` joined=`6` action=`NO_BUY_AI` sq_ev=`-0.7947`
- `score_unknown|risk_unknown|-|stale_unknown|price_unknown|liquidity_unknown|overbought_unknown|time_1400_close` sample=`14` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
