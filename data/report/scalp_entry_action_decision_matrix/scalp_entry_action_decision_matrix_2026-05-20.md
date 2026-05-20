# Scalp Entry Action Decision Matrix - 2026-05-20

## Contract
- status: `pass`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `652`
- joined_sample/sample_floor: `154` / `20`
- prompt_applied_count: `551`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 652}`
- forced_action_counts: `{'-': 652}`
- action_counts: `{'NO_BUY_AI': 639, 'SKIP_PRE_SUBMIT_SAFETY': 6, 'SKIP_SOURCE_QUALITY': 1, 'BUY_NOW': 2, 'WAIT_REQUOTE': 4}`
- missing_actions: `[]`
- zero_sample_actions: `['SKIP_STALE', 'BUY_DEFENSIVE']`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 2 | 2 | 0.485 | 0.485 | 1 | 0 |
| `WAIT_REQUOTE` | 4 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 0 | 0 | None | None | 0 | 0 |
| `BUY_DEFENSIVE` | 0 | 0 | None | None | 0 | 0 |
| `NO_BUY_AI` | 639 | 147 | -0.043 | -0.1869 | 59 | 94 |
| `SKIP_SOURCE_QUALITY` | 1 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 6 | 5 | -1.0833 | -1.3 | 4 | 4 |

## Top Buckets
- `score50_64|risk_unknown|fresh|price_unknown|liquidity_unknown|overbought_unknown|time_1200_1400` sample=`115` joined=`75` action=`NO_BUY_AI` sq_ev=`-0.1299`
- `score50_64|risk_unknown|fresh|price_unknown|liquidity_unknown|overbought_unknown|time_1000_1200` sample=`106` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|risk_unknown|stale_unknown|price_unknown|liquidity_unknown|overbought_unknown|time_1000_1200` sample=`68` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|risk_unknown|fresh|price_unknown|liquidity_unknown|overbought_unknown|time_0900_1000` sample=`61` joined=`38` action=`NO_BUY_AI` sq_ev=`-0.2726`
- `score50_64|risk_unknown|stale_unknown|price_unknown|liquidity_unknown|overbought_unknown|time_1200_1400` sample=`48` joined=`13` action=`NO_BUY_AI` sq_ev=`0.1029`
- `score50_64|risk_unknown|stale_unknown|price_unknown|liquidity_unknown|overbought_unknown|time_0900_1000` sample=`32` joined=`4` action=`NO_BUY_AI` sq_ev=`0.3072`
- `score50_64|risk_unknown|fresh|price_unknown|liquidity_unknown|overbought_unknown|time_1400_close` sample=`30` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|risk_unknown|stale_unknown|price_unknown|liquidity_unknown|overbought_unknown|time_1400_close` sample=`19` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|risk_unknown|stale_block|price_unknown|liquidity_unknown|overbought_unknown|time_1200_1400` sample=`18` joined=`15` action=`NO_BUY_AI` sq_ev=`-0.7244`
- `score50_64|weak_strength_momentum|stale_unknown|price_unknown|liquidity_unknown|overbought_normal|time_0900_1000` sample=`17` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
