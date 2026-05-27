# Scalp Entry Action Decision Matrix - 2026-05-27

## Contract
- status: `pass`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `804`
- joined_sample/sample_floor: `154` / `20`
- prompt_applied_count: `361`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 804}`
- forced_action_counts: `{'-': 804}`
- action_counts: `{'SKIP_PRE_SUBMIT_SAFETY': 310, 'WAIT_REQUOTE': 18, 'BUY_NOW': 20, 'NO_BUY_AI': 448, 'SKIP_SOURCE_QUALITY': 3, 'BUY_DEFENSIVE': 5}`
- missing_actions: `[]`
- zero_sample_actions: `['SKIP_STALE']`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 20 | 5 | -0.578 | -2.312 | 3 | 0 |
| `WAIT_REQUOTE` | 18 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 0 | 0 | None | None | 0 | 0 |
| `BUY_DEFENSIVE` | 5 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 448 | 13 | -0.0279 | -0.9623 | 6 | 8 |
| `SKIP_SOURCE_QUALITY` | 3 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 310 | 136 | -0.5938 | -1.3536 | 62 | 103 |

## Top Buckets
- `score_unknown|risk_unknown|-|stale_unknown|resolved_price|below_min_liquidity|overbought_unknown|time_0900_1000` sample=`153` joined=`43` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-0.3248`
- `score50_64|risk_unknown|-|fresh|price_unknown|liquidity_unknown|overbought_unknown|time_1000_1200` sample=`100` joined=`9` action=`NO_BUY_AI` sq_ev=`-0.09`
- `score50_64|risk_unknown|-|fresh|price_unknown|liquidity_unknown|overbought_unknown|time_0900_1000` sample=`72` joined=`1` action=`NO_BUY_AI` sq_ev=`0.0164`
- `score_unknown|risk_unknown|-|stale_unknown|resolved_price|below_min_liquidity|overbought_unknown|time_1000_1200` sample=`48` joined=`37` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-0.97`
- `score_unknown|risk_unknown|-|stale_unknown|resolved_price|below_min_liquidity|overbought_unknown|time_1200_1400` sample=`41` joined=`17` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-0.689`
- `score_unknown|risk_unknown|-|stale_unknown|resolved_price|below_min_liquidity|overbought_unknown|time_1400_close` sample=`36` joined=`17` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-0.7495`
- `score50_64|risk_unknown|-|fresh|price_unknown|liquidity_unknown|overbought_unknown|time_1200_1400` sample=`26` joined=`2` action=`NO_BUY_AI` sq_ev=`-0.0915`
- `score50_64|risk_unknown|-|fresh|price_unknown|liquidity_unknown|overbought_unknown|time_1400_close` sample=`20` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|stale_block|price_unknown|liquidity_unknown|overbought_normal|time_0900_1000` sample=`14` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_unknown|risk_unknown|-|stale_unknown|defensive_limit|below_min_liquidity|overbought_unknown|time_1000_1200` sample=`14` joined=`10` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-0.5086`
