# Scalp Entry Action Decision Matrix - 2026-06-02

## Contract
- status: `pass`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `563`
- joined_sample/sample_floor: `236` / `20`
- prompt_applied_count: `195`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 563}`
- forced_action_counts: `{'-': 563}`
- action_counts: `{'WAIT_REQUOTE': 7, 'BUY_NOW': 11, 'NO_BUY_AI': 291, 'SKIP_PRE_SUBMIT_SAFETY': 228, 'SKIP_SOURCE_QUALITY': 6, 'BUY_DEFENSIVE': 20}`
- missing_actions: `[]`
- zero_sample_actions: `['SKIP_STALE']`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 11 | 8 | -0.0009 | -0.0013 | 2 | 0 |
| `WAIT_REQUOTE` | 7 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 0 | 0 | None | None | 0 | 0 |
| `BUY_DEFENSIVE` | 20 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 291 | 34 | -0.0142 | -0.1218 | 8 | 16 |
| `SKIP_SOURCE_QUALITY` | 6 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 228 | 194 | -1.0236 | -1.203 | 109 | 143 |

## Top Buckets
- `score_unknown|risk_unknown|-|stale_unknown|resolved_price|below_min_liquidity|overbought_unknown|time_0900_1000` sample=`63` joined=`59` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-1.3478`
- `score_unknown|risk_unknown|-|stale_unknown|resolved_price|below_min_liquidity|overbought_unknown|time_1000_1200` sample=`52` joined=`49` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-1.0675`
- `score_unknown|risk_unknown|-|stale_unknown|resolved_price|below_min_liquidity|overbought_unknown|time_1200_1400` sample=`44` joined=`39` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-0.8575`
- `score50_64|risk_unknown|-|fresh|price_unknown|liquidity_unknown|overbought_unknown|time_1000_1200` sample=`37` joined=`10` action=`NO_BUY_AI` sq_ev=`-0.2649`
- `score50_64|risk_unknown|-|fresh|price_unknown|liquidity_unknown|overbought_unknown|time_1200_1400` sample=`27` joined=`11` action=`NO_BUY_AI` sq_ev=`0.1933`
- `score_unknown|risk_unknown|-|stale_unknown|resolved_price|below_min_liquidity|overbought_unknown|time_1400_close` sample=`26` joined=`18` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-0.6127`
- `score50_64|risk_unknown|-|fresh|price_unknown|liquidity_unknown|overbought_unknown|time_0900_1000` sample=`25` joined=`3` action=`NO_BUY_AI` sq_ev=`-0.1548`
- `score50_64|risk_unknown|-|fresh|price_unknown|liquidity_unknown|overbought_unknown|time_1400_close` sample=`18` joined=`5` action=`NO_BUY_AI` sq_ev=`-0.035`
- `score_unknown|risk_unknown|-|stale_unknown|price_unknown|liquidity_unknown|overbought_unknown|time_1400_close` sample=`17` joined=`2` action=`NO_BUY_AI` sq_ev=`0.1753`
- `score50_64|weak_strength_momentum|-|fresh|price_unknown|liquidity_unknown|overbought_watch|time_0900_1000` sample=`14` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
