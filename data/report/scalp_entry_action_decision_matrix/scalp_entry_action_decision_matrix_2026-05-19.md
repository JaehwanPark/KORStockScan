# Scalp Entry Action Decision Matrix - 2026-05-19

## Contract
- status: `warning`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `614`
- joined_sample/sample_floor: `72` / `20`
- prompt_applied_count: `506`
- action_counts: `{'NO_BUY_AI': 609, 'SKIP_PRE_SUBMIT_SAFETY': 2, 'BUY_NOW': 1, 'SKIP_SOURCE_QUALITY': 2}`
- missing_actions: `['WAIT_REQUOTE', 'SKIP_STALE', 'BUY_DEFENSIVE']`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 1 | 1 | -1.77 | -1.77 | 0 | 0 |
| `WAIT_REQUOTE` | 0 | 0 | None | None | 0 | 0 |
| `SKIP_STALE` | 0 | 0 | None | None | 0 | 0 |
| `BUY_DEFENSIVE` | 0 | 0 | None | None | 0 | 0 |
| `NO_BUY_AI` | 609 | 71 | -0.0269 | -0.2307 | 22 | 34 |
| `SKIP_SOURCE_QUALITY` | 2 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 2 | 0 | 0.0 | None | 0 | 0 |

## Top Buckets
- `score50_64|risk_unknown|fresh|price_unknown|liquidity_unknown|overbought_unknown|time_0900_1000` sample=`85` joined=`1` action=`NO_BUY_AI` sq_ev=`-0.0271`
- `score50_64|risk_unknown|fresh|price_unknown|liquidity_unknown|overbought_unknown|time_1000_1200` sample=`85` joined=`1` action=`NO_BUY_AI` sq_ev=`-0.0246`
- `score50_64|risk_unknown|fresh|price_unknown|liquidity_unknown|overbought_unknown|time_1200_1400` sample=`76` joined=`35` action=`NO_BUY_AI` sq_ev=`-0.1435`
- `score50_64|risk_unknown|stale_unknown|price_unknown|liquidity_unknown|overbought_unknown|time_1200_1400` sample=`52` joined=`14` action=`NO_BUY_AI` sq_ev=`-0.1596`
- `score50_64|risk_unknown|stale_unknown|price_unknown|liquidity_unknown|overbought_unknown|time_1000_1200` sample=`44` joined=`1` action=`NO_BUY_AI` sq_ev=`-0.0418`
- `score50_64|risk_unknown|stale_unknown|price_unknown|liquidity_unknown|overbought_unknown|time_0900_1000` sample=`42` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|risk_unknown|fresh|price_unknown|liquidity_unknown|overbought_unknown|time_1400_close` sample=`22` joined=`2` action=`NO_BUY_AI` sq_ev=`0.075`
- `score50_64|risk_unknown|stale_unknown|price_unknown|liquidity_unknown|overbought_unknown|time_1400_close` sample=`22` joined=`2` action=`NO_BUY_AI` sq_ev=`-0.0173`
- `score50_64|weak_strength_momentum|stale_unknown|price_unknown|liquidity_unknown|overbought_normal|time_0900_1000` sample=`16` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|risk_unknown|stale_block|price_unknown|liquidity_unknown|overbought_unknown|time_1200_1400` sample=`13` joined=`9` action=`NO_BUY_AI` sq_ev=`0.2808`

## Warnings
- `missing_action_bucket`
