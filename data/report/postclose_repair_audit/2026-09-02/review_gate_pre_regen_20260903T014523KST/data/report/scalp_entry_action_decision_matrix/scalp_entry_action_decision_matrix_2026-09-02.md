# Scalp Entry Action Decision Matrix - 2026-09-02

## Contract
- status: `warning`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `769`
- joined_sample/sample_floor: `11` / `20`
- joined_sample_cumulative/floor_met: `2638` / `True`
- prompt_applied_count: `221`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 769}`
- forced_action_counts: `{'-': 769}`
- action_counts: `{'NO_BUY_AI': 249, 'WAIT_REQUOTE': 388, 'BUY_DEFENSIVE': 74, 'SKIP_PRE_SUBMIT_SAFETY': 53, 'SKIP_SOURCE_QUALITY': 2, 'SKIP_STALE': 3}`
- missing_actions: `[]`
- zero_sample_actions: `['BUY_NOW']`
- unknown_bucket_affected_rows: `2`
- unknown_dimension_occurrence_count: `2`
- unknown_bucket_not_available_rows: `548`
- not_available_dimension_occurrence_count: `1793`
- unknown_bucket_dimension_counts: `{'risk_context_bucket': 2}`
- unknown_bucket_not_available_dimension_counts: `{'stale_bucket': 369, 'liquidity_bucket': 539, 'overbought_bucket': 508, 'price_resolution_bucket': 323, 'risk_context_bucket': 54}`
- score_source_missing_count: `0`
- score_source_missing_provenance: `{}`
- adm_source_bucket_used_count: `221`
- recomputed_unknown_count: `4054`
- entry_price_skip_followup_cumulative_status: `collecting_mature_followups`
- entry_price_skip_followup_90s_sample/floor: `0` / `20`
- entry_price_skip_followup_sample_floor_met: `False`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 0 | 0 | None | None | 0 | 0 |
| `WAIT_REQUOTE` | 388 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 3 | 0 | 0.0 | None | 0 | 0 |
| `BUY_DEFENSIVE` | 74 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 248 | 3 | -0.0123 | -1.0167 | 0 | 2 |
| `SKIP_SOURCE_QUALITY` | 2 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 53 | 8 | -0.2132 | -1.4125 | 3 | 5 |

## Top Buckets
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1000_1200` sample=`73` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`68` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1200_1400` sample=`62` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_0900_1000` sample=`34` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|weak_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1000_1200` sample=`22` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_ok|time_1000_1200` sample=`18` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_0900_1000` sample=`16` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_1000_1200` sample=`15` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_1200_1400` sample=`15` joined=`1` action=`NO_BUY_AI` sq_ev=`-0.1193`
- `score_lt50|weak_strength_momentum|-|fresh|defensive_limit|liquidity_not_available|overbought_not_available|time_1200_1400` sample=`15` joined=`0` action=`BUY_DEFENSIVE` sq_ev=`0.0`

## Warnings
- `sim_post_sell_outcome_join_contract_gap`
