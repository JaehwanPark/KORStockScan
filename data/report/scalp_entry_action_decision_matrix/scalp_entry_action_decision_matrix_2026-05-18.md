# Scalp Entry Action Decision Matrix - 2026-05-18

## Contract
- status: `warning`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `73`
- joined_sample/sample_floor: `2` / `20`
- prompt_applied_count: `0`
- action_counts: `{'NO_BUY_AI': 70, 'BUY_NOW': 2, 'SKIP_SOURCE_QUALITY': 1}`
- missing_actions: `['WAIT_REQUOTE', 'SKIP_STALE', 'BUY_DEFENSIVE', 'SKIP_PRE_SUBMIT_SAFETY']`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 2 | 2 | -2.225 | -2.225 | 1 | 0 |
| `WAIT_REQUOTE` | 0 | 0 | None | None | 0 | 0 |
| `SKIP_STALE` | 0 | 0 | None | None | 0 | 0 |
| `BUY_DEFENSIVE` | 0 | 0 | None | None | 0 | 0 |
| `NO_BUY_AI` | 70 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_SOURCE_QUALITY` | 1 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 0 | 0 | None | None | 0 | 0 |

## Top Buckets
- `score50_64|strong_strength_momentum|fresh|price_unknown|liquidity_unknown|overbought_normal|time_0900_1000` sample=`7` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|strong_strength_momentum|fresh|price_unknown|liquidity_unknown|overbought_watch|time_0900_1000` sample=`7` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|strong_strength_momentum|fresh|price_unknown|liquidity_unknown|overbought_normal|time_1000_1200` sample=`6` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|neutral_strength_momentum|fresh|price_unknown|liquidity_unknown|overbought_normal|time_0900_1000` sample=`5` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|neutral_strength_momentum|fresh|price_unknown|liquidity_unknown|overbought_watch|time_1000_1200` sample=`5` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|strong_strength_momentum|fresh|price_unknown|liquidity_unknown|overbought_normal|time_1200_1400` sample=`4` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|fresh|price_unknown|liquidity_unknown|overbought_watch|time_0900_1000` sample=`4` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|strong_strength_momentum|stale_unknown|price_unknown|liquidity_unknown|overbought_watch|time_0900_1000` sample=`3` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|neutral_strength_momentum|fresh|price_unknown|liquidity_unknown|overbought_normal|time_1000_1200` sample=`2` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|neutral_strength_momentum|stale_unknown|price_unknown|liquidity_unknown|overbought_watch|time_0900_1000` sample=`2` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`

## Warnings
- `joined_sample_below_sample_floor`
- `missing_action_bucket`
- `prompt_context_not_loaded`
