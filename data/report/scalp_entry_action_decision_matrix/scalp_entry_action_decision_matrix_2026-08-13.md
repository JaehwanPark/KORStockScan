# Scalp Entry Action Decision Matrix - 2026-08-13

## Contract
- status: `warning`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `560`
- joined_sample/sample_floor: `11` / `20`
- prompt_applied_count: `273`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 560}`
- forced_action_counts: `{'-': 560}`
- action_counts: `{'WAIT_REQUOTE': 168, 'NO_BUY_AI': 311, 'SKIP_PRE_SUBMIT_SAFETY': 31, 'BUY_DEFENSIVE': 48, 'SKIP_STALE': 2}`
- missing_actions: `[]`
- zero_sample_actions: `['BUY_NOW', 'SKIP_SOURCE_QUALITY']`
- unknown_bucket_affected_rows: `4`
- unknown_dimension_occurrence_count: `7`
- unknown_bucket_not_available_rows: `287`
- not_available_dimension_occurrence_count: `916`
- unknown_bucket_dimension_counts: `{'score_bucket': 1, 'risk_context_bucket': 3, 'price_resolution_bucket': 3}`
- unknown_bucket_not_available_dimension_counts: `{'liquidity_bucket': 277, 'overbought_bucket': 240, 'stale_bucket': 181, 'price_resolution_bucket': 184, 'risk_context_bucket': 31, 'score_bucket': 3}`
- score_source_missing_count: `1`
- score_source_missing_provenance: `{'gap': 'score_bucket_source_score_missing', 'expected_source_fields': ['ai_score', 'ai_score_after_bonus', 'current_ai_score', 'ai_score_raw', 'entry_score', 'score', 'scalp_sim_candidate_window_original_score', 'swing_entry_recovery_gate_score'], 'recommended_resolution': 'join_or_emit_entry_score_before_adm_bucket_decision', 'decision_authority': 'source_quality_gap_discovery', 'runtime_effect': False, 'allowed_runtime_apply': False}`
- adm_source_bucket_used_count: `273`
- recomputed_unknown_count: `2272`
- entry_price_skip_followup_cumulative_status: `collecting_mature_followups`
- entry_price_skip_followup_90s_sample/floor: `0` / `20`
- entry_price_skip_followup_sample_floor_met: `False`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 0 | 0 | None | None | 0 | 0 |
| `WAIT_REQUOTE` | 168 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 2 | 0 | 0.0 | None | 0 | 0 |
| `BUY_DEFENSIVE` | 48 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 311 | 5 | -0.0268 | -1.67 | 2 | 3 |
| `SKIP_SOURCE_QUALITY` | 0 | 0 | None | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 31 | 6 | 0.0093 | 0.0483 | 2 | 2 |

## Top Buckets
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1200_1400` sample=`41` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`41` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_1400_close` sample=`39` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_0900_1000` sample=`24` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1000_1200` sample=`21` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_ok|time_1400_close` sample=`21` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_1000_1200` sample=`20` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_ok|time_1200_1400` sample=`15` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1400_close` sample=`14` joined=`1` action=`NO_BUY_AI` sq_ev=`0.0086`
- `score_lt50|strong_strength_momentum|-|fresh|defensive_limit|liquidity_not_available|overbought_not_available|time_1200_1400` sample=`14` joined=`0` action=`BUY_DEFENSIVE` sq_ev=`0.0`

## Warnings
- `joined_sample_below_sample_floor`
- `sim_post_sell_outcome_source_below_sample_floor`
- `unknown_bucket_source_quality_gap`
