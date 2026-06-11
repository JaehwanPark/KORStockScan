# Scalp Entry Action Decision Matrix - 2026-06-11

## Contract
- status: `warning`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `759`
- joined_sample/sample_floor: `264` / `20`
- prompt_applied_count: `398`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 759}`
- forced_action_counts: `{'-': 759}`
- action_counts: `{'WAIT_REQUOTE': 31, 'NO_BUY_AI': 502, 'SKIP_PRE_SUBMIT_SAFETY': 199, 'BUY_NOW': 6, 'SKIP_SOURCE_QUALITY': 4, 'BUY_DEFENSIVE': 17}`
- missing_actions: `[]`
- zero_sample_actions: `['SKIP_STALE']`
- unknown_bucket_affected_rows: `255`
- unknown_dimension_occurrence_count: `350`
- unknown_bucket_not_available_rows: `361`
- not_available_dimension_occurrence_count: `861`
- unknown_bucket_dimension_counts: `{'score_bucket': 255, 'risk_context_bucket': 56, 'price_resolution_bucket': 39}`
- unknown_bucket_not_available_dimension_counts: `{'stale_bucket': 302, 'price_resolution_bucket': 106, 'liquidity_bucket': 162, 'overbought_bucket': 92, 'risk_context_bucket': 199}`
- adm_source_bucket_used_count: `398`
- recomputed_unknown_count: `2925`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 6 | 3 | 0.7483 | 1.4967 | 1 | 0 |
| `WAIT_REQUOTE` | 31 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 0 | 0 | None | None | 0 | 0 |
| `BUY_DEFENSIVE` | 17 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 502 | 105 | -0.1788 | -0.8547 | 41 | 64 |
| `SKIP_SOURCE_QUALITY` | 4 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 199 | 156 | -0.4699 | -0.5994 | 61 | 91 |

## Top Buckets
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`76` joined=`19` action=`NO_BUY_AI` sq_ev=`-0.3255`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_0900_1000` sample=`54` joined=`14` action=`NO_BUY_AI` sq_ev=`0.0531`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1200_1400` sample=`51` joined=`12` action=`NO_BUY_AI` sq_ev=`-0.1157`
- `score_unknown|risk_unknown|-|stale_not_available|price_unknown|liquidity_not_available|overbought_not_available|time_1400_close` sample=`39` joined=`2` action=`NO_BUY_AI` sq_ev=`0.0303`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_0900_1000` sample=`33` joined=`6` action=`NO_BUY_AI` sq_ev=`-0.2142`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1400_close` sample=`30` joined=`6` action=`NO_BUY_AI` sq_ev=`-0.144`
- `score_unknown|risk_context_not_available|-|stale_not_available|defensive_limit|below_min_liquidity|overbought_ok|time_1000_1200` sample=`30` joined=`23` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-1.4767`
- `score_unknown|risk_context_not_available|-|stale_not_available|defensive_limit|below_min_liquidity|overbought_ok|time_1200_1400` sample=`30` joined=`23` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-0.345`
- `score_unknown|risk_context_not_available|-|stale_not_available|resolved_price|below_min_liquidity|overbought_ok|time_0900_1000` sample=`28` joined=`28` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`0.9825`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_ok|time_1400_close` sample=`26` joined=`6` action=`NO_BUY_AI` sq_ev=`-0.4646`

## Warnings
- `unknown_bucket_source_quality_gap`
