# Scalp Entry Action Decision Matrix - 2026-07-22

## Contract
- status: `warning`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `338`
- joined_sample/sample_floor: `6` / `20`
- prompt_applied_count: `41`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 338}`
- forced_action_counts: `{'-': 338}`
- action_counts: `{'WAIT_REQUOTE': 207, 'BUY_DEFENSIVE': 38, 'NO_BUY_AI': 86, 'SKIP_STALE': 5, 'SKIP_PRE_SUBMIT_SAFETY': 2}`
- missing_actions: `[]`
- zero_sample_actions: `['BUY_NOW', 'SKIP_SOURCE_QUALITY']`
- unknown_bucket_affected_rows: `44`
- unknown_dimension_occurrence_count: `45`
- unknown_bucket_not_available_rows: `297`
- not_available_dimension_occurrence_count: `970`
- unknown_bucket_dimension_counts: `{'risk_context_bucket': 41, 'score_bucket': 3, 'price_resolution_bucket': 1}`
- unknown_bucket_not_available_dimension_counts: `{'stale_bucket': 208, 'price_resolution_bucket': 170, 'liquidity_bucket': 296, 'overbought_bucket': 291, 'risk_context_bucket': 4, 'score_bucket': 1}`
- score_source_missing_count: `3`
- score_source_missing_provenance: `{'gap': 'score_bucket_source_score_missing', 'expected_source_fields': ['ai_score', 'ai_score_after_bonus', 'current_ai_score', 'ai_score_raw', 'entry_score', 'score', 'swing_entry_recovery_gate_score'], 'recommended_resolution': 'join_or_emit_entry_score_before_adm_bucket_decision', 'decision_authority': 'source_quality_gap_discovery', 'runtime_effect': False, 'allowed_runtime_apply': False}`
- adm_source_bucket_used_count: `41`
- recomputed_unknown_count: `2097`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 0 | 0 | None | None | 0 | 0 |
| `WAIT_REQUOTE` | 207 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 5 | 0 | 0.0 | None | 0 | 0 |
| `BUY_DEFENSIVE` | 38 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 86 | 5 | -0.0862 | -1.482 | 3 | 5 |
| `SKIP_SOURCE_QUALITY` | 0 | 0 | None | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 2 | 1 | -1.695 | -3.39 | 1 | 1 |

## Top Buckets
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`45` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1000_1200` sample=`28` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1200_1400` sample=`26` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_0900_1000` sample=`20` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_watch|defensive_limit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`18` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`14` joined=`1` action=`NO_BUY_AI` sq_ev=`-0.1057`
- `score_lt50|risk_unknown|-|stale_not_available|defensive_limit|liquidity_not_available|overbought_not_available|time_1000_1200` sample=`14` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_lt50|risk_unknown|-|stale_not_available|defensive_limit|liquidity_not_available|overbought_not_available|time_1200_1400` sample=`13` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_lt50|weak_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_0900_1000` sample=`12` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|risk_unknown|-|stale_not_available|defensive_limit|liquidity_not_available|overbought_not_available|time_0900_1000` sample=`8` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`

## Warnings
- `joined_sample_below_sample_floor`
- `unknown_bucket_source_quality_gap`
