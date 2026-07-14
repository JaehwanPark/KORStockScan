# Scalp Entry Action Decision Matrix - 2026-07-14

## Contract
- status: `warning`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `122`
- joined_sample/sample_floor: `0` / `20`
- prompt_applied_count: `28`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 122}`
- forced_action_counts: `{'-': 122}`
- action_counts: `{'WAIT_REQUOTE': 53, 'NO_BUY_AI': 52, 'SKIP_PRE_SUBMIT_SAFETY': 8, 'BUY_DEFENSIVE': 8, 'SKIP_STALE': 1}`
- missing_actions: `[]`
- zero_sample_actions: `['BUY_NOW', 'SKIP_SOURCE_QUALITY']`
- unknown_bucket_affected_rows: `10`
- unknown_dimension_occurrence_count: `11`
- unknown_bucket_not_available_rows: `94`
- not_available_dimension_occurrence_count: `276`
- unknown_bucket_dimension_counts: `{'score_bucket': 1, 'risk_context_bucket': 9, 'price_resolution_bucket': 1}`
- unknown_bucket_not_available_dimension_counts: `{'liquidity_bucket': 86, 'overbought_bucket': 71, 'price_resolution_bucket': 52, 'risk_context_bucket': 9, 'stale_bucket': 57, 'score_bucket': 1}`
- score_source_missing_count: `1`
- score_source_missing_provenance: `{'gap': 'score_bucket_source_score_missing', 'expected_source_fields': ['ai_score', 'ai_score_after_bonus', 'current_ai_score', 'ai_score_raw', 'entry_score', 'score', 'swing_entry_recovery_gate_score'], 'recommended_resolution': 'join_or_emit_entry_score_before_adm_bucket_decision', 'decision_authority': 'source_quality_gap_discovery', 'runtime_effect': False, 'allowed_runtime_apply': False}`
- adm_source_bucket_used_count: `28`
- recomputed_unknown_count: `673`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 0 | 0 | None | None | 0 | 0 |
| `WAIT_REQUOTE` | 53 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 1 | 0 | 0.0 | None | 0 | 0 |
| `BUY_DEFENSIVE` | 8 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 52 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_SOURCE_QUALITY` | 0 | 0 | None | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 8 | 0 | 0.0 | None | 0 | 0 |

## Top Buckets
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`23` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|weak_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`13` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_watch|defensive_limit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`9` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1200_1400` sample=`8` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_lt50|risk_unknown|-|stale_not_available|defensive_limit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`8` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|strong_strength_momentum|-|stale_block|price_not_available_pre_submit|liquidity_not_available|overbought_normal|time_1000_1200` sample=`5` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`5` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|risk_context_not_available|-|stale_not_available|defensive_limit|below_min_liquidity|overbought_ok|time_1200_1400` sample=`4` joined=`0` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`0.0`
- `score50_64|risk_context_not_available|-|stale_not_available|defensive_limit|below_min_liquidity|overbought_ok|time_1000_1200` sample=`3` joined=`0` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`0.0`
- `score50_64|neutral_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1200_1400` sample=`2` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`

## Warnings
- `joined_sample_below_sample_floor`
- `unknown_bucket_source_quality_gap`
