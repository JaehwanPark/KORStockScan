# Scalp Entry Action Decision Matrix - 2026-07-30

## Contract
- status: `warning`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `32`
- joined_sample/sample_floor: `2` / `20`
- prompt_applied_count: `15`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 32}`
- forced_action_counts: `{'-': 32}`
- action_counts: `{'BUY_DEFENSIVE': 4, 'WAIT_REQUOTE': 3, 'SKIP_PRE_SUBMIT_SAFETY': 5, 'NO_BUY_AI': 20}`
- missing_actions: `[]`
- zero_sample_actions: `['BUY_NOW', 'SKIP_STALE', 'SKIP_SOURCE_QUALITY']`
- unknown_bucket_affected_rows: `2`
- unknown_dimension_occurrence_count: `3`
- unknown_bucket_not_available_rows: `17`
- not_available_dimension_occurrence_count: `52`
- unknown_bucket_dimension_counts: `{'score_bucket': 1, 'risk_context_bucket': 1, 'price_resolution_bucket': 1}`
- unknown_bucket_not_available_dimension_counts: `{'liquidity_bucket': 17, 'overbought_bucket': 13, 'stale_bucket': 7, 'price_resolution_bucket': 10, 'risk_context_bucket': 4, 'score_bucket': 1}`
- score_source_missing_count: `1`
- score_source_missing_provenance: `{'gap': 'score_bucket_source_score_missing', 'expected_source_fields': ['ai_score', 'ai_score_after_bonus', 'current_ai_score', 'ai_score_raw', 'entry_score', 'score', 'scalp_sim_candidate_window_original_score', 'swing_entry_recovery_gate_score'], 'recommended_resolution': 'join_or_emit_entry_score_before_adm_bucket_decision', 'decision_authority': 'source_quality_gap_discovery', 'runtime_effect': False, 'allowed_runtime_apply': False}`
- adm_source_bucket_used_count: `15`
- recomputed_unknown_count: `132`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 0 | 0 | None | None | 0 | 0 |
| `WAIT_REQUOTE` | 3 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 0 | 0 | None | None | 0 | 0 |
| `BUY_DEFENSIVE` | 4 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 20 | 1 | 0.0045 | 0.09 | 0 | 0 |
| `SKIP_SOURCE_QUALITY` | 0 | 0 | None | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 5 | 1 | -0.296 | -1.48 | 1 | 1 |

## Top Buckets
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_0900_1000` sample=`5` joined=`1` action=`NO_BUY_AI` sq_ev=`0.018`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`5` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1200_1400` sample=`3` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|neutral_strength_momentum|-|fresh|defensive_limit|liquidity_not_available|overbought_not_available|time_0900_1000` sample=`2` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score50_64|strong_strength_momentum|-|fresh|defensive_limit|liquidity_not_available|overbought_not_available|time_0900_1000` sample=`2` joined=`0` action=`BUY_DEFENSIVE` sq_ev=`0.0`
- `score50_64|strong_strength_momentum|-|fresh|price_not_available_pre_submit|liquidity_not_available|overbought_normal|time_0900_1000` sample=`2` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score65_74|neutral_strength_momentum|-|fresh|defensive_limit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`2` joined=`0` action=`BUY_DEFENSIVE` sq_ev=`0.0`
- `score65_74|risk_context_not_available|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1000_1200` sample=`2` joined=`1` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-0.74`
- `score50_64|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_watch|time_1200_1400` sample=`1` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|risk_context_not_available|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_0900_1000` sample=`1` joined=`0` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`0.0`

## Warnings
- `joined_sample_below_sample_floor`
- `unknown_bucket_source_quality_gap`
