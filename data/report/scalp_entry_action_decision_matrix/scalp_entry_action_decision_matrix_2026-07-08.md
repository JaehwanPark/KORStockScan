# Scalp Entry Action Decision Matrix - 2026-07-08

## Contract
- status: `warning`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `362`
- joined_sample/sample_floor: `25` / `20`
- prompt_applied_count: `251`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 362}`
- forced_action_counts: `{'-': 362}`
- action_counts: `{'NO_BUY_AI': 286, 'SKIP_PRE_SUBMIT_SAFETY': 29, 'BUY_DEFENSIVE': 28, 'BUY_NOW': 3, 'WAIT_REQUOTE': 16}`
- missing_actions: `[]`
- zero_sample_actions: `['SKIP_STALE', 'SKIP_SOURCE_QUALITY']`
- unknown_bucket_affected_rows: `21`
- unknown_dimension_occurrence_count: `26`
- unknown_bucket_not_available_rows: `111`
- not_available_dimension_occurrence_count: `303`
- unknown_bucket_dimension_counts: `{'risk_context_bucket': 21, 'score_bucket': 1, 'price_resolution_bucket': 4}`
- unknown_bucket_not_available_dimension_counts: `{'stale_bucket': 92, 'price_resolution_bucket': 44, 'liquidity_bucket': 81, 'risk_context_bucket': 29, 'overbought_bucket': 53, 'score_bucket': 4}`
- score_source_missing_count: `1`
- score_source_missing_provenance: `{'gap': 'score_bucket_source_score_missing', 'expected_source_fields': ['ai_score', 'ai_score_after_bonus', 'current_ai_score', 'ai_score_raw', 'entry_score', 'score', 'swing_entry_recovery_gate_score'], 'recommended_resolution': 'join_or_emit_entry_score_before_adm_bucket_decision', 'decision_authority': 'source_quality_gap_discovery', 'runtime_effect': False, 'allowed_runtime_apply': False}`
- adm_source_bucket_used_count: `251`
- recomputed_unknown_count: `975`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 3 | 0 | 0.0 | None | 0 | 0 |
| `WAIT_REQUOTE` | 16 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 0 | 0 | None | None | 0 | 0 |
| `BUY_DEFENSIVE` | 28 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 286 | 15 | -0.1201 | -2.2907 | 7 | 12 |
| `SKIP_SOURCE_QUALITY` | 0 | 0 | None | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 29 | 10 | -1.4531 | -4.214 | 7 | 9 |

## Top Buckets
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`48` joined=`2` action=`NO_BUY_AI` sq_ev=`-0.1483`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1400_close` sample=`45` joined=`2` action=`NO_BUY_AI` sq_ev=`-0.0538`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_1200_1400` sample=`34` joined=`1` action=`NO_BUY_AI` sq_ev=`-0.0985`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1200_1400` sample=`15` joined=`1` action=`NO_BUY_AI` sq_ev=`-0.2467`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_0900_1000` sample=`14` joined=`1` action=`NO_BUY_AI` sq_ev=`-0.2436`
- `score50_64|risk_context_not_available|-|stale_not_available|defensive_limit|below_min_liquidity|overbought_ok|time_1400_close` sample=`12` joined=`3` action=`SKIP_PRE_SUBMIT_SAFETY` sq_ev=`-0.9583`
- `score50_64|weak_strength_momentum|-|stale_high|quote_based|liquidity_high|overbought_normal|time_0900_1000` sample=`12` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`10` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`9` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|neutral_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`8` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`

## Warnings
- `unknown_bucket_source_quality_gap`
