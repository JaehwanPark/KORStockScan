# Scalp Entry Action Decision Matrix - 2026-07-23

## Contract
- status: `warning`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `198`
- joined_sample/sample_floor: `0` / `20`
- prompt_applied_count: `65`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 198}`
- forced_action_counts: `{'-': 198}`
- action_counts: `{'BUY_DEFENSIVE': 20, 'WAIT_REQUOTE': 96, 'NO_BUY_AI': 76, 'SKIP_STALE': 2, 'SKIP_SOURCE_QUALITY': 2, 'SKIP_PRE_SUBMIT_SAFETY': 2}`
- missing_actions: `[]`
- zero_sample_actions: `['BUY_NOW']`
- unknown_bucket_affected_rows: `6`
- unknown_dimension_occurrence_count: `7`
- unknown_bucket_not_available_rows: `133`
- not_available_dimension_occurrence_count: `381`
- unknown_bucket_dimension_counts: `{'score_bucket': 2, 'risk_context_bucket': 4, 'price_resolution_bucket': 1}`
- unknown_bucket_not_available_dimension_counts: `{'liquidity_bucket': 132, 'overbought_bucket': 120, 'price_resolution_bucket': 66, 'risk_context_bucket': 3, 'stale_bucket': 59, 'score_bucket': 1}`
- score_source_missing_count: `2`
- score_source_missing_provenance: `{'gap': 'score_bucket_source_score_missing', 'expected_source_fields': ['ai_score', 'ai_score_after_bonus', 'current_ai_score', 'ai_score_raw', 'entry_score', 'score', 'swing_entry_recovery_gate_score'], 'recommended_resolution': 'join_or_emit_entry_score_before_adm_bucket_decision', 'decision_authority': 'source_quality_gap_discovery', 'runtime_effect': False, 'allowed_runtime_apply': False}`
- adm_source_bucket_used_count: `65`
- recomputed_unknown_count: `983`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 0 | 0 | None | None | 0 | 0 |
| `WAIT_REQUOTE` | 96 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 2 | 0 | 0.0 | None | 0 | 0 |
| `BUY_DEFENSIVE` | 20 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 76 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_SOURCE_QUALITY` | 2 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 2 | 0 | 0.0 | None | 0 | 0 |

## Top Buckets
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`27` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`24` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1200_1400` sample=`22` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_watch|defensive_limit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`14` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|weak_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`11` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|weak_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1200_1400` sample=`8` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_watch|defensive_limit|liquidity_not_available|overbought_not_available|time_1000_1200` sample=`5` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_watch|defensive_limit|liquidity_not_available|overbought_not_available|time_1200_1400` sample=`5` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score50_64|strong_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`4` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_0900_1000` sample=`4` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`

## Warnings
- `joined_sample_below_sample_floor`
- `unknown_bucket_source_quality_gap`
