# Scalp Entry Action Decision Matrix - 2026-05-29

## Contract
- status: `pass`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `545`
- joined_sample/sample_floor: `153` / `20`
- prompt_applied_count: `271`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 545}`
- forced_action_counts: `{'-': 545}`
- action_counts: `{'SKIP_PRE_SUBMIT_SAFETY': 152, 'NO_BUY_AI': 365, 'WAIT_REQUOTE': 11, 'BUY_NOW': 13, 'SKIP_SOURCE_QUALITY': 2, 'BUY_DEFENSIVE': 2}`
- missing_actions: `[]`
- zero_sample_actions: `['SKIP_STALE']`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 13 | 7 | 0.0246 | 0.0457 | 1 | 0 |
| `WAIT_REQUOTE` | 11 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 0 | 0 | None | None | 0 | 0 |
| `BUY_DEFENSIVE` | 2 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 365 | 14 | -0.0118 | -0.3079 | 1 | 7 |
| `SKIP_SOURCE_QUALITY` | 2 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 152 | 132 | -0.3054 | -0.3517 | 40 | 69 |

## Top Buckets
- `score50_64|risk_unknown|-|fresh|price_unknown|liquidity_unknown|overbought_unknown|time_1200_1400` sample=`68` joined=`1` action=`NO_BUY_AI` sq_ev=`0.0363`
- `score50_64|risk_unknown|-|fresh|price_unknown|liquidity_unknown|overbought_unknown|time_1000_1200` sample=`61` joined=`3` action=`NO_BUY_AI` sq_ev=`-0.0585`
- `score_unknown|risk_unknown|-|stale_unknown|resolved_price|below_min_liquidity|overbought_unknown|time_0900_1000` sample=`50` joined=`50` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-0.4406`
- `score_unknown|risk_unknown|-|stale_unknown|resolved_price|below_min_liquidity|overbought_unknown|time_1000_1200` sample=`45` joined=`41` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`0.0786`
- `score_unknown|risk_unknown|-|stale_unknown|resolved_price|below_min_liquidity|overbought_unknown|time_1200_1400` sample=`30` joined=`22` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-0.5807`
- `score50_64|risk_unknown|-|fresh|price_unknown|liquidity_unknown|overbought_unknown|time_0900_1000` sample=`21` joined=`5` action=`NO_BUY_AI` sq_ev=`0.0495`
- `score50_64|risk_unknown|-|stale_block|price_unknown|liquidity_unknown|overbought_unknown|time_1200_1400` sample=`17` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|stale_unknown|price_unknown|liquidity_unknown|overbought_normal|time_0900_1000` sample=`15` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_unknown|risk_unknown|-|stale_unknown|price_unknown|liquidity_unknown|overbought_unknown|time_1400_close` sample=`15` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|risk_unknown|-|stale_block|price_unknown|liquidity_unknown|overbought_unknown|time_1000_1200` sample=`13` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
