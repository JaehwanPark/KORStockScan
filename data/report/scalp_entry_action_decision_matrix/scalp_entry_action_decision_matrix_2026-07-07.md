# Scalp Entry Action Decision Matrix - 2026-07-07

## Contract
- status: `warning`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `318`
- joined_sample/sample_floor: `17` / `20`
- prompt_applied_count: `215`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 318}`
- forced_action_counts: `{'-': 318}`
- action_counts: `{'BUY_DEFENSIVE': 40, 'NO_BUY_AI': 233, 'SKIP_PRE_SUBMIT_SAFETY': 15, 'BUY_NOW': 6, 'WAIT_REQUOTE': 20, 'SKIP_SOURCE_QUALITY': 4}`
- missing_actions: `[]`
- zero_sample_actions: `['SKIP_STALE']`
- unknown_bucket_affected_rows: `36`
- unknown_dimension_occurrence_count: `41`
- unknown_bucket_not_available_rows: `103`
- not_available_dimension_occurrence_count: `316`
- unknown_bucket_dimension_counts: `{'risk_context_bucket': 36, 'score_bucket': 1, 'price_resolution_bucket': 4}`
- unknown_bucket_not_available_dimension_counts: `{'stale_bucket': 100, 'liquidity_bucket': 87, 'overbought_bucket': 70, 'risk_context_bucket': 15, 'price_resolution_bucket': 40, 'score_bucket': 4}`
- score_source_missing_count: `1`
- score_source_missing_provenance: `{'gap': 'score_bucket_source_score_missing', 'expected_source_fields': ['ai_score', 'ai_score_after_bonus', 'current_ai_score', 'ai_score_raw', 'entry_score', 'score', 'swing_entry_recovery_gate_score'], 'recommended_resolution': 'join_or_emit_entry_score_before_adm_bucket_decision', 'decision_authority': 'source_quality_gap_discovery', 'runtime_effect': False, 'allowed_runtime_apply': False}`
- adm_source_bucket_used_count: `215`
- recomputed_unknown_count: `890`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 6 | 1 | -0.7783 | -4.67 | 1 | 0 |
| `WAIT_REQUOTE` | 20 | 1 | 0.051 | 1.02 | 0 | 0 |
| `SKIP_STALE` | 0 | 0 | None | None | 0 | 0 |
| `BUY_DEFENSIVE` | 40 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 233 | 5 | -0.0345 | -1.61 | 2 | 4 |
| `SKIP_SOURCE_QUALITY` | 4 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 15 | 10 | -1.3527 | -2.029 | 4 | 6 |

## Top Buckets
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`58` joined=`2` action=`NO_BUY_AI` sq_ev=`-0.1176`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1400_close` sample=`40` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1200_1400` sample=`35` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_not_available|defensive_limit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`11` joined=`0` action=`BUY_DEFENSIVE` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`11` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|risk_unknown|-|stale_not_available|defensive_limit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`11` joined=`0` action=`BUY_DEFENSIVE` sq_ev=`0.0`
- `score50_64|risk_context_not_available|-|stale_not_available|defensive_limit|below_min_liquidity|overbought_ok|time_0900_1000` sample=`7` joined=`5` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-2.3257`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`7` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|neutral_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_0900_1000` sample=`5` joined=`1` action=`NO_BUY_AI` sq_ev=`-0.712`
- `score50_64|strong_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`5` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`

## Warnings
- `joined_sample_below_sample_floor`
- `unknown_bucket_source_quality_gap`
