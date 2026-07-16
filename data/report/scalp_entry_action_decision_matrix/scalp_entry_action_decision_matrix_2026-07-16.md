# Scalp Entry Action Decision Matrix - 2026-07-16

## Contract
- status: `warning`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `99`
- joined_sample/sample_floor: `6` / `20`
- prompt_applied_count: `40`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 99}`
- forced_action_counts: `{'-': 99}`
- action_counts: `{'NO_BUY_AI': 62, 'SKIP_PRE_SUBMIT_SAFETY': 3, 'SKIP_SOURCE_QUALITY': 1, 'WAIT_REQUOTE': 27, 'BUY_DEFENSIVE': 4, 'SKIP_STALE': 2}`
- missing_actions: `[]`
- zero_sample_actions: `['BUY_NOW']`
- unknown_bucket_affected_rows: `20`
- unknown_dimension_occurrence_count: `21`
- unknown_bucket_not_available_rows: `59`
- not_available_dimension_occurrence_count: `177`
- unknown_bucket_dimension_counts: `{'risk_context_bucket': 19, 'price_resolution_bucket': 1, 'score_bucket': 1}`
- unknown_bucket_not_available_dimension_counts: `{'stale_bucket': 42, 'price_resolution_bucket': 22, 'liquidity_bucket': 56, 'risk_context_bucket': 4, 'score_bucket': 1, 'overbought_bucket': 52}`
- score_source_missing_count: `1`
- score_source_missing_provenance: `{'gap': 'score_bucket_source_score_missing', 'expected_source_fields': ['ai_score', 'ai_score_after_bonus', 'current_ai_score', 'ai_score_raw', 'entry_score', 'score', 'swing_entry_recovery_gate_score'], 'recommended_resolution': 'join_or_emit_entry_score_before_adm_bucket_decision', 'decision_authority': 'source_quality_gap_discovery', 'runtime_effect': False, 'allowed_runtime_apply': False}`
- adm_source_bucket_used_count: `40`
- recomputed_unknown_count: `449`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 0 | 0 | None | None | 0 | 0 |
| `WAIT_REQUOTE` | 27 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 2 | 0 | 0.0 | None | 0 | 0 |
| `BUY_DEFENSIVE` | 4 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 62 | 5 | 0.006 | 0.074 | 1 | 1 |
| `SKIP_SOURCE_QUALITY` | 1 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 3 | 1 | -1.06 | -3.18 | 1 | 1 |

## Top Buckets
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1200_1400` sample=`21` joined=`1` action=`NO_BUY_AI` sq_ev=`0.0424`
- `score_lt50|risk_unknown|-|stale_not_available|defensive_limit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`18` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`13` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_watch|defensive_limit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`9` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`6` joined=`3` action=`NO_BUY_AI` sq_ev=`0.625`
- `score_lt50|neutral_strength_momentum|-|stale_high|defensive_limit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`3` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|weak_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`3` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score50_64|neutral_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1400_close` sample=`2` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_0900_1000` sample=`2` joined=`1` action=`NO_BUY_AI` sq_ev=`-2.135`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_0900_1000` sample=`2` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`

## Warnings
- `joined_sample_below_sample_floor`
- `unknown_bucket_source_quality_gap`
