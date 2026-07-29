# Scalp Entry Action Decision Matrix - 2026-07-29

## Contract
- status: `warning`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `85`
- joined_sample/sample_floor: `3` / `20`
- prompt_applied_count: `15`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 85}`
- forced_action_counts: `{'-': 85}`
- action_counts: `{'WAIT_REQUOTE': 28, 'BUY_DEFENSIVE': 13, 'BUY_NOW': 6, 'SKIP_STALE': 2, 'NO_BUY_AI': 25, 'SKIP_PRE_SUBMIT_SAFETY': 11}`
- missing_actions: `[]`
- zero_sample_actions: `['SKIP_SOURCE_QUALITY']`
- unknown_bucket_affected_rows: `2`
- unknown_dimension_occurrence_count: `3`
- unknown_bucket_not_available_rows: `70`
- not_available_dimension_occurrence_count: `202`
- unknown_bucket_dimension_counts: `{'score_bucket': 1, 'risk_context_bucket': 1, 'price_resolution_bucket': 1}`
- unknown_bucket_not_available_dimension_counts: `{'stale_bucket': 20, 'price_resolution_bucket': 37, 'liquidity_bucket': 70, 'overbought_bucket': 63, 'risk_context_bucket': 11, 'score_bucket': 1}`
- score_source_missing_count: `1`
- score_source_missing_provenance: `{'gap': 'score_bucket_source_score_missing', 'expected_source_fields': ['ai_score', 'ai_score_after_bonus', 'current_ai_score', 'ai_score_raw', 'entry_score', 'score', 'scalp_sim_candidate_window_original_score', 'swing_entry_recovery_gate_score'], 'recommended_resolution': 'join_or_emit_entry_score_before_adm_bucket_decision', 'decision_authority': 'source_quality_gap_discovery', 'runtime_effect': False, 'allowed_runtime_apply': False}`
- adm_source_bucket_used_count: `15`
- recomputed_unknown_count: `495`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 6 | 0 | 0.0 | None | 0 | 0 |
| `WAIT_REQUOTE` | 28 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 2 | 0 | 0.0 | None | 0 | 0 |
| `BUY_DEFENSIVE` | 13 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 25 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_SOURCE_QUALITY` | 0 | 0 | None | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 11 | 3 | -0.2427 | -0.89 | 0 | 2 |

## Top Buckets
- `score50_64|risk_context_not_available|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1000_1200` sample=`9` joined=`2` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-0.3156`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`7` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|strong_strength_momentum|-|stale_watch|defensive_limit|liquidity_not_available|overbought_not_available|time_0900_1000` sample=`5` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score50_64|strong_strength_momentum|-|stale_watch|resolved_price|liquidity_not_available|overbought_not_available|time_0900_1000` sample=`4` joined=`0` action=`BUY_NOW` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_0900_1000` sample=`4` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score75_84|strong_strength_momentum|-|stale_watch|defensive_limit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`4` joined=`0` action=`BUY_DEFENSIVE` sq_ev=`0.0`
- `score50_64|strong_strength_momentum|-|stale_watch|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_0900_1000` sample=`3` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_0900_1000` sample=`3` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`3` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score50_64|neutral_strength_momentum|-|stale_watch|defensive_limit|liquidity_not_available|overbought_not_available|time_0900_1000` sample=`2` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`

## Warnings
- `joined_sample_below_sample_floor`
- `unknown_bucket_source_quality_gap`
