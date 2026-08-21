# Scalp Entry Action Decision Matrix - 2026-08-21

## Contract
- status: `warning`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `772`
- joined_sample/sample_floor: `10` / `20`
- prompt_applied_count: `254`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 772}`
- forced_action_counts: `{'-': 772}`
- action_counts: `{'WAIT_REQUOTE': 392, 'BUY_DEFENSIVE': 81, 'NO_BUY_AI': 276, 'BUY_NOW': 2, 'SKIP_SOURCE_QUALITY': 2, 'SKIP_PRE_SUBMIT_SAFETY': 16, 'SKIP_STALE': 3}`
- missing_actions: `[]`
- zero_sample_actions: `[]`
- unknown_bucket_affected_rows: `5`
- unknown_dimension_occurrence_count: `5`
- unknown_bucket_not_available_rows: `518`
- not_available_dimension_occurrence_count: `1750`
- unknown_bucket_dimension_counts: `{'risk_context_bucket': 4, 'score_bucket': 1}`
- unknown_bucket_not_available_dimension_counts: `{'liquidity_bucket': 512, 'overbought_bucket': 487, 'stale_bucket': 369, 'price_resolution_bucket': 367, 'risk_context_bucket': 15}`
- score_source_missing_count: `1`
- score_source_missing_provenance: `{'gap': 'score_bucket_source_score_missing', 'expected_source_fields': ['ai_score', 'ai_score_after_bonus', 'current_ai_score', 'ai_score_raw', 'entry_score', 'score', 'scalp_sim_candidate_window_original_score', 'swing_entry_recovery_gate_score'], 'recommended_resolution': 'join_or_emit_entry_score_before_adm_bucket_decision', 'decision_authority': 'source_quality_gap_discovery', 'runtime_effect': False, 'allowed_runtime_apply': False}`
- adm_source_bucket_used_count: `254`
- recomputed_unknown_count: `3859`
- entry_price_skip_followup_cumulative_status: `collecting_mature_followups`
- entry_price_skip_followup_90s_sample/floor: `0` / `20`
- entry_price_skip_followup_sample_floor_met: `False`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 2 | 0 | 0.0 | None | 0 | 0 |
| `WAIT_REQUOTE` | 392 | 1 | 0.0008 | 0.33 | 0 | 0 |
| `SKIP_STALE` | 3 | 0 | 0.0 | None | 0 | 0 |
| `BUY_DEFENSIVE` | 81 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 276 | 4 | -0.0247 | -1.7075 | 2 | 2 |
| `SKIP_SOURCE_QUALITY` | 2 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 16 | 5 | -0.34 | -1.088 | 2 | 2 |

## Top Buckets
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`93` joined=`1` action=`WAIT_REQUOTE` sq_ev=`0.0035`
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1000_1200` sample=`66` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1200_1400` sample=`55` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_0900_1000` sample=`49` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_1000_1200` sample=`33` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_1200_1400` sample=`24` joined=`2` action=`NO_BUY_AI` sq_ev=`-0.3067`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_1400_close` sample=`24` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1400_close` sample=`23` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_0900_1000` sample=`23` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_lt50|weak_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`22` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`

## Warnings
- `joined_sample_below_sample_floor`
- `sim_post_sell_outcome_source_below_sample_floor`
- `unknown_bucket_source_quality_gap`
