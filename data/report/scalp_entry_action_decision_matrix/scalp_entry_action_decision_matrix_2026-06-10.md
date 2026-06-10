# Scalp Entry Action Decision Matrix - 2026-06-10

## Contract
- status: `warning`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `613`
- joined_sample/sample_floor: `260` / `20`
- prompt_applied_count: `296`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 613}`
- forced_action_counts: `{'-': 613}`
- action_counts: `{'WAIT_REQUOTE': 22, 'BUY_NOW': 9, 'NO_BUY_AI': 355, 'SKIP_PRE_SUBMIT_SAFETY': 189, 'SKIP_SOURCE_QUALITY': 13, 'BUY_DEFENSIVE': 25}`
- missing_actions: `[]`
- zero_sample_actions: `['SKIP_STALE']`
- unknown_bucket_affected_rows: `315`
- unknown_dimension_occurrence_count: `580`
- unknown_bucket_not_available_rows: `317`
- not_available_dimension_occurrence_count: `483`
- unknown_bucket_dimension_counts: `{'price_resolution_bucket': 100, 'score_bucket': 240, 'risk_context_bucket': 240}`
- unknown_bucket_not_available_dimension_counts: `{'stale_bucket': 286, 'liquidity_bucket': 128, 'overbought_bucket': 69}`
- adm_source_bucket_used_count: `296`
- recomputed_unknown_count: `2515`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 9 | 3 | -0.6489 | -1.9467 | 1 | 0 |
| `WAIT_REQUOTE` | 22 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 0 | 0 | None | None | 0 | 0 |
| `BUY_DEFENSIVE` | 25 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 355 | 101 | -0.4847 | -1.7038 | 33 | 86 |
| `SKIP_SOURCE_QUALITY` | 13 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 189 | 156 | -1.1208 | -1.3579 | 70 | 123 |

## Top Buckets
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`114` joined=`32` action=`NO_BUY_AI` sq_ev=`-0.4724`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_0900_1000` sample=`61` joined=`26` action=`NO_BUY_AI` sq_ev=`-0.7677`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1200_1400` sample=`44` joined=`19` action=`NO_BUY_AI` sq_ev=`-0.8241`
- `score_unknown|risk_unknown|-|stale_not_available|defensive_limit|below_min_liquidity|overbought_ok|time_1000_1200` sample=`43` joined=`42` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-1.2128`
- `score_unknown|risk_unknown|-|stale_not_available|resolved_price|below_min_liquidity|overbought_ok|time_0900_1000` sample=`28` joined=`23` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-0.6021`
- `score_unknown|risk_unknown|-|stale_not_available|price_unknown|liquidity_not_available|overbought_not_available|time_1400_close` sample=`25` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_unknown|risk_unknown|-|stale_not_available|defensive_limit|below_min_liquidity|overbought_ok|time_1200_1400` sample=`20` joined=`20` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-1.904`
- `score50_64|weak_strength_momentum|-|stale_block|price_unknown|liquidity_not_available|overbought_normal|time_0900_1000` sample=`15` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_unknown|risk_unknown|-|stale_not_available|resolved_price|below_min_liquidity|overbought_ok|time_1200_1400` sample=`14` joined=`14` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-1.23`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_0900_1000` sample=`13` joined=`4` action=`NO_BUY_AI` sq_ev=`-0.6838`

## Warnings
- `unknown_bucket_source_quality_gap`
