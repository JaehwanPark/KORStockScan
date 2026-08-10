# Scalp Entry Action Decision Matrix - 2026-08-10

## Contract
- status: `warning`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `643`
- joined_sample/sample_floor: `13` / `20`
- prompt_applied_count: `399`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 643}`
- forced_action_counts: `{'-': 643}`
- action_counts: `{'NO_BUY_AI': 480, 'SKIP_PRE_SUBMIT_SAFETY': 94, 'WAIT_REQUOTE': 57, 'SKIP_SOURCE_QUALITY': 7, 'BUY_DEFENSIVE': 4, 'SKIP_STALE': 1}`
- missing_actions: `[]`
- zero_sample_actions: `['BUY_NOW']`
- unknown_bucket_affected_rows: `4`
- unknown_dimension_occurrence_count: `5`
- unknown_bucket_not_available_rows: `244`
- not_available_dimension_occurrence_count: `907`
- unknown_bucket_dimension_counts: `{'risk_context_bucket': 4, 'price_resolution_bucket': 1}`
- unknown_bucket_not_available_dimension_counts: `{'risk_context_bucket': 91, 'stale_bucket': 185, 'price_resolution_bucket': 228, 'liquidity_bucket': 244, 'overbought_bucket': 158, 'score_bucket': 1}`
- score_source_missing_count: `0`
- score_source_missing_provenance: `{}`
- adm_source_bucket_used_count: `399`
- recomputed_unknown_count: `2107`
- entry_price_skip_followup_cumulative_status: `collecting_mature_followups`
- entry_price_skip_followup_90s_sample/floor: `0` / `20`
- entry_price_skip_followup_sample_floor_met: `False`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 0 | 0 | None | None | 0 | 0 |
| `WAIT_REQUOTE` | 57 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 1 | 0 | 0.0 | None | 0 | 0 |
| `BUY_DEFENSIVE` | 4 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 480 | 1 | -0.0005 | -0.23 | 0 | 1 |
| `SKIP_SOURCE_QUALITY` | 7 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 94 | 12 | -0.1606 | -1.2583 | 5 | 7 |

## Top Buckets
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_ok|time_1400_close` sample=`52` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_0900_1000` sample=`40` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|risk_context_not_available|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1000_1200` sample=`39` joined=`4` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-0.1128`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`34` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1400_close` sample=`32` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_1000_1200` sample=`26` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_ok|time_1000_1200` sample=`25` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_1400_close` sample=`24` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_ok|time_1200_1400` sample=`19` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_1200_1400` sample=`15` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`

## Warnings
- `joined_sample_below_sample_floor`
- `sim_post_sell_outcome_source_below_sample_floor`
- `unknown_bucket_source_quality_gap`
