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
- prompt_applied_count: `557`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 652}`
- forced_action_counts: `{'-': 652}`
- action_counts: `{'NO_BUY_AI': 645, 'SKIP_SOURCE_QUALITY': 1, 'BUY_NOW': 2, 'WAIT_REQUOTE': 4}`
- missing_actions: `[]`
- zero_sample_actions: `['SKIP_STALE', 'BUY_DEFENSIVE', 'SKIP_PRE_SUBMIT_SAFETY']`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 2 | 2 | 0.485 | 0.485 | 1 | 0 |
| `WAIT_REQUOTE` | 4 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 0 | 0 | None | None | 0 | 0 |
| `BUY_DEFENSIVE` | 0 | 0 | None | None | 0 | 0 |
| `NO_BUY_AI` | 645 | 152 | -0.0527 | -0.2236 | 63 | 98 |
| `SKIP_SOURCE_QUALITY` | 1 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 0 | 0 | None | None | 0 | 0 |

## Top Buckets
- `score50_64|risk_unknown|fresh|price_unknown|liquidity_unknown|overbought_unknown|time_1200_1400` sample=`117` joined=`76` action=`NO_BUY_AI` sq_ev=`-0.1486`
- `score50_64|risk_unknown|fresh|price_unknown|liquidity_unknown|overbought_unknown|time_1000_1200` sample=`106` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|risk_unknown|stale_unknown|price_unknown|liquidity_unknown|overbought_unknown|time_1000_1200` sample=`68` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|risk_unknown|fresh|price_unknown|liquidity_unknown|overbought_unknown|time_0900_1000` sample=`64` joined=`41` action=`NO_BUY_AI` sq_ev=`-0.3606`
- `score50_64|risk_unknown|stale_unknown|price_unknown|liquidity_unknown|overbought_unknown|time_1200_1400` sample=`48` joined=`13` action=`NO_BUY_AI` sq_ev=`0.1029`
- `score50_64|risk_unknown|stale_unknown|price_unknown|liquidity_unknown|overbought_unknown|time_0900_1000` sample=`32` joined=`4` action=`NO_BUY_AI` sq_ev=`0.3072`
- `score50_64|risk_unknown|fresh|price_unknown|liquidity_unknown|overbought_unknown|time_1400_close` sample=`30` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|risk_unknown|stale_unknown|price_unknown|liquidity_unknown|overbought_unknown|time_1400_close` sample=`19` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|risk_unknown|stale_block|price_unknown|liquidity_unknown|overbought_unknown|time_1200_1400` sample=`18` joined=`15` action=`NO_BUY_AI` sq_ev=`-0.7244`
- `score50_64|weak_strength_momentum|stale_unknown|price_unknown|liquidity_unknown|overbought_normal|time_0900_1000` sample=`17` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
