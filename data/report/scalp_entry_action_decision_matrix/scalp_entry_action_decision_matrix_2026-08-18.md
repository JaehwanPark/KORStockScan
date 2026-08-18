# Scalp Entry Action Decision Matrix - 2026-08-18

## Contract
- status: `warning`
- runtime_effect: `False`
- decision_authority: `entry_advisory_prompt_context_only`
- application_mode: `operator_override_advisory_prompt`
- primary_decision_metric: `source_quality_adjusted_ev_pct`

## Summary
- total_candidates: `791`
- joined_sample/sample_floor: `23` / `20`
- prompt_applied_count: `305`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 791}`
- forced_action_counts: `{'-': 791}`
- action_counts: `{'WAIT_REQUOTE': 364, 'NO_BUY_AI': 340, 'BUY_DEFENSIVE': 61, 'SKIP_PRE_SUBMIT_SAFETY': 19, 'SKIP_SOURCE_QUALITY': 1, 'SKIP_STALE': 6}`
- missing_actions: `[]`
- zero_sample_actions: `['BUY_NOW']`
- unknown_bucket_affected_rows: `6`
- unknown_dimension_occurrence_count: `6`
- unknown_bucket_not_available_rows: `486`
- not_available_dimension_occurrence_count: `1624`
- unknown_bucket_dimension_counts: `{'score_bucket': 3, 'risk_context_bucket': 3}`
- unknown_bucket_not_available_dimension_counts: `{'stale_bucket': 345, 'price_resolution_bucket': 346, 'liquidity_bucket': 476, 'overbought_bucket': 438, 'risk_context_bucket': 19}`
- score_source_missing_count: `3`
- score_source_missing_provenance: `{'gap': 'score_bucket_source_score_missing', 'expected_source_fields': ['ai_score', 'ai_score_after_bonus', 'current_ai_score', 'ai_score_raw', 'entry_score', 'score', 'scalp_sim_candidate_window_original_score', 'swing_entry_recovery_gate_score'], 'recommended_resolution': 'join_or_emit_entry_score_before_adm_bucket_decision', 'decision_authority': 'source_quality_gap_discovery', 'runtime_effect': False, 'allowed_runtime_apply': False}`
- adm_source_bucket_used_count: `305`
- recomputed_unknown_count: `3705`
- entry_price_skip_followup_cumulative_status: `collecting_mature_followups`
- entry_price_skip_followup_90s_sample/floor: `0` / `20`
- entry_price_skip_followup_sample_floor_met: `False`

## Action Summary
| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BUY_NOW` | 0 | 0 | None | None | 0 | 0 |
| `WAIT_REQUOTE` | 364 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_STALE` | 6 | 0 | 0.0 | None | 0 | 0 |
| `BUY_DEFENSIVE` | 61 | 0 | 0.0 | None | 0 | 0 |
| `NO_BUY_AI` | 340 | 12 | -0.0309 | -0.8742 | 2 | 8 |
| `SKIP_SOURCE_QUALITY` | 1 | 0 | 0.0 | None | 0 | 0 |
| `SKIP_PRE_SUBMIT_SAFETY` | 19 | 11 | -1.0447 | -1.8045 | 5 | 8 |

## Top Buckets
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1000_1200` sample=`79` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_0900_1000` sample=`59` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1400_close` sample=`52` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score_lt50|neutral_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_1200_1400` sample=`47` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1400_close` sample=`35` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_1400_close` sample=`27` joined=`1` action=`NO_BUY_AI` sq_ev=`-0.1159`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_ok|time_1200_1400` sample=`24` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_ok|time_1000_1200` sample=`23` joined=`1` action=`NO_BUY_AI` sq_ev=`0.057`
- `score50_64|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_watch|time_1000_1200` sample=`21` joined=`0` action=`NO_BUY_AI` sq_ev=`0.0`
- `score_lt50|weak_strength_momentum|-|stale_not_available|price_not_available_pre_submit|liquidity_not_available|overbought_not_available|time_0900_1000` sample=`21` joined=`0` action=`WAIT_REQUOTE` sq_ev=`0.0`

## Warnings
- `sim_post_sell_outcome_join_contract_gap`
- `unknown_bucket_source_quality_gap`
