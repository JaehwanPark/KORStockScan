# Scalp Entry Action Decision Matrix - 2026-06-09

## Contract
- status: `warning`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `1238`
- joined_sample/sample_floor: `230` / `20`
- prompt_applied_count: `870`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 1238}`
- forced_action_counts: `{'-': 1238}`
- action_counts: `{'NO_BUY_AI': 1021, 'SKIP_PRE_SUBMIT_SAFETY': 159, 'WAIT_REQUOTE': 7, 'BUY_NOW': 21, 'SKIP_SOURCE_QUALITY': 25, 'BUY_DEFENSIVE': 5}`
- missing_actions: `[]`
- zero_sample_actions: `['SKIP_STALE']`
- unknown_bucket_affected_rows: `368`
- unknown_dimension_occurrence_count: `565`
- unknown_bucket_not_available_rows: `368`
- not_available_dimension_occurrence_count: `455`
- unknown_bucket_dimension_counts: `{'score_bucket': 181, 'risk_context_bucket': 181, 'price_resolution_bucket': 203}`
- unknown_bucket_not_available_dimension_counts: `{'stale_bucket': 219, 'liquidity_bucket': 209, 'overbought_bucket': 27}`
- adm_source_bucket_used_count: `870`
- recomputed_unknown_count: `2208`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 21 | 16 | -0.0638 | -0.0838 | 3 | 0 |
| `WAIT_REQUOTE` | 7 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 0 | 0 | None | None | 0 | 0 |
| `BUY_DEFENSIVE` | 5 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 1021 | 71 | -0.074 | -1.0637 | 39 | 53 |
| `SKIP_SOURCE_QUALITY` | 25 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 159 | 143 | -1.0153 | -1.1289 | 69 | 102 |

## Top Buckets
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1200_1400` sample=`275` joined=`8` action=`NO_BUY_AI` sq_ev=`-0.0236`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`215` joined=`25` action=`NO_BUY_AI` sq_ev=`-0.0051`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_0900_1000` sample=`58` joined=`18` action=`NO_BUY_AI` sq_ev=`-0.5971`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1400_close` sample=`57` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_ok|time_1200_1400` sample=`43` joined=`3` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_unknown|risk_unknown|-|stale_not_available|resolved_price|below_min_liquidity|overbought_ok|time_0900_1000` sample=`39` joined=`39` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-1.3908`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_0900_1000` sample=`36` joined=`13` action=`NO_BUY_AI` sq_ev=`-0.5911`
- `score_unknown|risk_unknown|-|stale_not_available|resolved_price|below_min_liquidity|overbought_ok|time_1000_1200` sample=`26` joined=`26` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-0.4381`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_ok|time_1000_1200` sample=`25` joined=`1` action=`NO_BUY_AI` sq_ev=`-0.1136`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_ok|time_1400_close` sample=`24` joined=`1` action=`NO_BUY_AI` sq_ev=`-0.0671`

## Warnings
- `unknown_bucket_source_quality_gap`
