# Scalp Entry Action Decision Matrix - 2026-08-05

## Contract
- status: `warning`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `640`
- joined_sample/sample_floor: `4` / `20`
- prompt_applied_count: `478`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 640}`
- forced_action_counts: `{'-': 640}`
- action_counts: `{'NO_BUY_AI': 578, 'SKIP_PRE_SUBMIT_SAFETY': 51, 'SKIP_SOURCE_QUALITY': 8, 'BUY_DEFENSIVE': 2, 'WAIT_REQUOTE': 1}`
- missing_actions: `[]`
- zero_sample_actions: `['BUY_NOW', 'SKIP_STALE']`
- unknown_bucket_affected_rows: `0`
- unknown_dimension_occurrence_count: `0`
- unknown_bucket_not_available_rows: `162`
- not_available_dimension_occurrence_count: `548`
- unknown_bucket_dimension_counts: `{}`
- unknown_bucket_not_available_dimension_counts: `{'stale_bucket': 119, 'price_resolution_bucket': 160, 'liquidity_bucket': 162, 'risk_context_bucket': 51, 'overbought_bucket': 56}`
- score_source_missing_count: `0`
- score_source_missing_provenance: `{}`
- adm_source_bucket_used_count: `478`
- recomputed_unknown_count: `1612`
- entry_price_skip_followup_cumulative_status: `collecting_mature_followups`
- entry_price_skip_followup_90s_sample/floor: `0` / `20`
- entry_price_skip_followup_sample_floor_met: `False`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 0 | 0 | None | None | 0 | 0 |
| `WAIT_REQUOTE` | 1 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 0 | 0 | None | None | 0 | 0 |
| `BUY_DEFENSIVE` | 2 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 578 | 1 | 0.0023 | 1.35 | 0 | 0 |
| `SKIP_SOURCE_QUALITY` | 8 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 51 | 3 | -0.1247 | -2.12 | 3 | 3 |

## Top Buckets
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_1000_1200` sample=`79` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1400_close` sample=`52` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_1200_1400` sample=`47` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_0900_1000` sample=`41` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_1400_close` sample=`36` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`29` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1200_1400` sample=`28` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_ok|time_1400_close` sample=`20` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|neutral_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_1200_1400` sample=`18` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|risk_context_not_available|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1000_1200` sample=`14` joined=`2` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-0.3536`

## Warnings
- `joined_sample_below_sample_floor`
- `sim_post_sell_outcome_source_below_sample_floor`
