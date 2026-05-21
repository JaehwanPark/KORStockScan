# Scalp Entry Action Decision Matrix - 2026-05-21

## Contract
- status: `pass`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `1450`
- joined_sample/sample_floor: `175` / `20`
- prompt_applied_count: `1280`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 1450}`
- forced_action_counts: `{'-': 1450}`
- action_counts: `{'NO_BUY_AI': 1440, 'BUY_DEFENSIVE': 5, 'SKIP_SOURCE_QUALITY': 2, 'SKIP_PRE_SUBMIT_SAFETY': 2, 'WAIT_REQUOTE': 1}`
- missing_actions: `[]`
- zero_sample_actions: `['BUY_NOW', 'SKIP_STALE']`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 0 | 0 | None | None | 0 | 0 |
| `WAIT_REQUOTE` | 1 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 0 | 0 | None | None | 0 | 0 |
| `BUY_DEFENSIVE` | 5 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 1440 | 174 | -0.0322 | -0.2668 | 57 | 104 |
| `SKIP_SOURCE_QUALITY` | 2 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 2 | 1 | 2.785 | 5.57 | 0 | 0 |

## Top Buckets
- `score50_64|risk_unknown|-|fresh|price_unknown|liquidity_unknown|overbought_unknown|time_1000_1200` sample=`229` joined=`51` action=`NO_BUY_AI` sq_ev=`-0.0496`
- `score50_64|risk_unknown|-|fresh|price_unknown|liquidity_unknown|overbought_unknown|time_1200_1400` sample=`202` joined=`10` action=`NO_BUY_AI` sq_ev=`-0.0303`
- `score50_64|risk_unknown|-|stale_unknown|price_unknown|liquidity_unknown|overbought_unknown|time_1200_1400` sample=`202` joined=`5` action=`NO_BUY_AI` sq_ev=`-0.0149`
- `score50_64|risk_unknown|-|stale_unknown|price_unknown|liquidity_unknown|overbought_unknown|time_1000_1200` sample=`143` joined=`11` action=`NO_BUY_AI` sq_ev=`0.0181`
- `score50_64|risk_unknown|-|fresh|price_unknown|liquidity_unknown|overbought_unknown|time_0900_1000` sample=`109` joined=`48` action=`NO_BUY_AI` sq_ev=`-0.0095`
- `score50_64|risk_unknown|-|stale_unknown|price_unknown|liquidity_unknown|overbought_unknown|time_0900_1000` sample=`75` joined=`12` action=`NO_BUY_AI` sq_ev=`-0.0847`
- `score50_64|risk_unknown|-|fresh|price_unknown|liquidity_unknown|overbought_unknown|time_1400_close` sample=`60` joined=`6` action=`NO_BUY_AI` sq_ev=`-0.0352`
- `score50_64|risk_unknown|-|stale_unknown|price_unknown|liquidity_unknown|overbought_unknown|time_1400_close` sample=`56` joined=`1` action=`NO_BUY_AI` sq_ev=`-0.0275`
- `score50_64|risk_unknown|-|stale_block|price_unknown|liquidity_unknown|overbought_unknown|time_1200_1400` sample=`30` joined=`1` action=`NO_BUY_AI` sq_ev=`-0.052`
- `score50_64|strong_strength_momentum|-|fresh|price_unknown|liquidity_unknown|overbought_normal|time_0900_1000` sample=`28` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
