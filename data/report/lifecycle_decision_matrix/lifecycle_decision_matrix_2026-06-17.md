# Lifecycle Decision Matrix - 2026-06-17

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-17`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `23836`
- source_rows_total: `24104`
- retained_rows: `23836`
- dropped_rows_by_source: `{'dedupe': 268}`
- joined_rows: `21601`
- policy_pass_count: `5`
- promote_ready_count: `1`
- entry_bucket_actionable_count: `17`
- entry_bucket_runtime_candidate_count: `10`
- holding_bucket_count/workorders: `34` / `10`
- exit_bucket_count/workorders: `46` / `10`
- scale_in_bucket_actionable_count: `0`
- scale_in_bucket_runtime_candidate_count: `0`
- overnight_bucket_actionable_count: `9`
- overnight_bucket_runtime_candidate_count: `9`
- lifecycle_flow_bucket_count: `155`
- lifecycle_flow_complete_count: `129`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `0` / `129` / `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0058`
- incomplete_flow_reason_counts: `{'missing_entry': 21657, 'missing_holding': 21947, 'missing_exit': 21764, 'missing_submit': 21947, 'candidate_id_only': 21678, 'sim_record_id_only': 45, 'scale_in_noise_only': 21430, 'postclose_exit_without_entry': 210}`
- bucket_directed_sim_probe: `{'observed_row_count': 629, 'matched_row_count': 26, 'background_row_count': 603, 'matched_unique_source_bucket_count': 3, 'match_status_counts': {'matched': 26, 'no_match': 376, 'not_instrumented': 227}, 'matched_classification_state_counts': {'lifecycle_flow_sim_probe_candidate': 26}, 'primary_source': 'matched_bucket_directed_sim_probe_only', 'background_source': 'unmatched_or_policy_missing_sim_observation', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 1, 'route_counts': {'bounded_auxiliary_weight': 1, 'hold_sample': 4}, 'quality_counts': {'observational_only_pending_outcome': 1, 'hold_sample': 4}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 1594 | 140 | 0.922 | 1.0 | `pass` | `BUY_DEFENSIVE` | True |
| `submit` | 213 | 181 | -0.3372 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 197 | 181 | -0.7509 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 21452 | 20894 | -0.3612 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 380 | 205 | -0.7896 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 22104, 'complete_flow_count': 129, 'direct_sim_record_complete_flow_count': 0, 'adm_bridge_complete_flow_count': 129, 'fallback_complete_flow_count': 0, 'direct_flow_zero_diagnostic': {'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'direct_sim_record_flow_count': 45, 'direct_sim_record_incomplete_flow_count': 45, 'direct_sim_record_stage_coverage_counts': {'exit': 35, 'holding': 16}, 'direct_sim_record_incomplete_reason_counts': {'missing_entry': 45, 'missing_submit': 45, 'missing_holding': 29, 'missing_exit': 10, 'sim_record_id_only': 45, 'scale_in_noise_only': 10, 'postclose_exit_without_entry': 35}, 'runtime_effect': False, 'decision_authority': 'ldm_direct_flow_diagnostic_only'}, 'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'incomplete_flow_count': 21975, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 23836, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0058, 'complete_flow_conversion_denominator': 356, 'complete_flow_conversion_rate': 0.3624, 'active_priority_incomplete_seed_count': 318, 'scale_in_followup_event_count': 21452, 'scale_in_unique_flow_count': 15813, 'scale_in_noise_flow_count': 21430, 'denominator_exclusion_counts': {'scale_in_noise_flow_excluded': 21430, 'active_priority_incomplete_seed_excluded': 318}, 'conversion_blocker_reason_counts': {'missing_entry': 227, 'missing_holding': 210, 'missing_exit': 17, 'missing_submit': 210, 'sim_record_id_only': 35, 'postclose_exit_without_entry': 210, 'candidate_id_only': 175}, 'observation_seed_reason_counts': {'missing_submit': 21737, 'missing_holding': 21737, 'missing_exit': 21747, 'candidate_id_only': 21503, 'missing_entry': 21430, 'sim_record_id_only': 10, 'scale_in_noise_only': 21430}, 'join_contract_blocked': False, 'bundle_ev_tuning_state': 'ready_for_bundle_ev_tuning', 'top_incomplete_reason': 'missing_submit', 'stage_identity': {'entry': {'source_row_count': 1594, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 1511, 'candidate_id': 83}, 'identity_join_rate': 1.0}, 'submit': {'source_row_count': 213, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 213}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 197, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 181, 'exact_sim_record_id': 16}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 21452, 'identity_missing_count': 0, 'identity_quality_counts': {'exact_sim_record_id': 32, 'candidate_id': 21420}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 380, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 169, 'exact_sim_record_id': 36, 'candidate_id': 175}, 'identity_join_rate': 1.0}}, 'required_stage_source_counts': {'entry': 1594, 'submit': 213, 'holding': 197, 'exit': 380}, 'incomplete_flow_reason_counts': {'missing_entry': 21657, 'missing_holding': 21947, 'missing_exit': 21764, 'missing_submit': 21947, 'candidate_id_only': 21678, 'sim_record_id_only': 45, 'scale_in_noise_only': 21430, 'postclose_exit_without_entry': 210}, 'bucket_count': 155, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:8050d08a3f` | 5 | 5 | -2.0613 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:1b4e4b3128` | 4 | 4 | -2.8474 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:67138f9e63` | 4 | 4 | -1.0349 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:81b7841fa7` | 3 | 3 | -1.4627 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:528fdd1edb` | 2 | 2 | 0.5214 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:06a029c7a2` | 2 | 2 | -1.207 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:f68b1eee89` | 2 | 2 | -0.597 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:a62f71d09a` | 2 | 2 | 0.4872 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:b30924d33a` | 2 | 2 | 0.8507 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:3cbb81cd02` | 2 | 2 | -0.4065 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9d8cac316e` | 2 | 2 | -0.5655 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:ec7a1ee648` | 2 | 2 | -0.7903 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:917af9e5d4` | 2 | 2 | -1.1714 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:6db490b9d4` | 2 | 2 | -1.3644 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9b100ebd9b` | 2 | 2 | -1.162 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:18f09004f7` | 2 | 2 | -0.86 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:d4c6deacea` | 2 | 2 | 0.8117 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:a5f3e518ef` | 2 | 2 | -2.6524 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:e7d65a7c45` | 1 | 1 | -0.7991 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:f97841f1ce` | 1 | 1 | -1.3271 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 1594, 'bucket_count': 205, 'actionable_bucket_count': 17, 'source_quality_blocked_bucket_count': 0, 'runtime_candidate_count': 10, 'workorder_count': 10}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `WAIT_REQUOTE` | 75 | 75 | 1.8511 | 2.8002 | 0.6933 | `candidate_recovery_or_relax` |
| `chosen_action` | `NO_BUY_AI` | 1470 | 56 | -0.167 | -1.1962 | 0.25 | `hold_no_edge` |
| `chosen_action` | `BUY_NOW` | 10 | 9 | -0.0443 | 0.7567 | 0.5556 | `hold_sample` |
| `chosen_action` | `ALLOW_BOTTOMING_ENTRY` | 1 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `ALLOW_LEVEL1_RISK_OFF_ENTRY` | 7 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_SOURCE_QUALITY` | 31 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 23 | 23 | 2.0801 | 2.924 | 0.7391 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 16 | 16 | 2.6681 | 4.4076 | 0.875 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 114 | 14 | 0.4995 | -1.9707 | 0.1429 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 13 | 13 | 1.6894 | 2.2893 | 0.6154 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 34 | 8 | -0.3155 | -1.0488 | 0.375 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 265 | 7 | -0.1604 | -1.6686 | 0.1429 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 217 | 6 | -0.7392 | -1.5667 | 0.1667 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 6 | 6 | 0.6224 | 0.5504 | 0.8333 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 21 | 5 | -0.725 | 0.484 | 0.6 | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 4 | 4 | 0.4969 | 0.8346 | 0.5 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 12 | 4 | 0.4478 | 2.165 | 0.75 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 34 | 3 | 0.1295 | -1.9433 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 3 | 3 | 0.1815 | 0.0479 | 0.3333 | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_mid|overbought=overbought_normal|time=time_0900_1000` | 3 | 3 | 0.1828 | -0.0175 | 0.3333 | `hold_sample` |
| `exit_rule` | `exit_unknown` | 1529 | 75 | 1.8511 | 2.8002 | 0.6933 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_soft_stop_pct` | 28 | 28 | -0.1615 | -1.9214 | 0.0 | `hold_no_edge` |
| `exit_rule` | `scalp_trailing_take_profit` | 19 | 19 | -0.2874 | 2.3816 | 1.0 | `hold_no_edge` |
| `exit_rule` | `scalp_hard_stop_pct` | 18 | 18 | 0.0127 | -2.8683 | 0.0 | `hold_no_edge` |
| `liquidity_bucket` | `liquidity_high` | 1250 | 136 | 0.9511 | 1.1101 | 0.5147 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 1412 | 129 | 0.8991 | 0.8185 | 0.4961 | `candidate_recovery_or_relax` |
| `score_band` | `score_66_69` | 87 | 37 | 1.8157 | 2.6048 | 0.6216 | `candidate_recovery_or_relax` |
| `score_band` | `score_70p` | 64 | 35 | 1.2913 | 2.3396 | 0.7429 | `candidate_recovery_or_relax` |
| `score_band` | `score_60_62` | 993 | 30 | 0.0182 | -1.7507 | 0.1667 | `hold_no_edge` |
| `score_band` | `score_63_65` | 172 | 28 | 0.7037 | 1.3281 | 0.5 | `candidate_recovery_or_relax` |
| `score_band` | `score_lt60` | 278 | 10 | -0.354 | -1.31 | 0.3 | `candidate_tighten_or_exclude` |
| `source_stage` | `wait6579_ev_cohort` | 75 | 75 | 1.8511 | 2.8002 | 0.6933 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 1162 | 65 | -0.1501 | -0.9258 | 0.2923 | `hold_no_edge` |
| `stale_bucket` | `fresh_or_unflagged` | 83 | 75 | 1.8511 | 2.8002 | 0.6933 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh` | 1353 | 65 | -0.1501 | -0.9258 | 0.2923 | `hold_no_edge` |
| `strength_bucket` | `weak_strength_momentum` | 1282 | 72 | 0.1271 | -0.3683 | 0.3333 | `hold_no_edge` |
| `strength_bucket` | `strong_strength_momentum` | 200 | 66 | 1.6437 | 2.469 | 0.697 | `candidate_recovery_or_relax` |

### Entry Bucket Runtime Approval Candidates

- `entry_bucket_2`: `combo_entry_spot` / `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` -> `candidate_recovery_or_relax`
- `entry_bucket_7`: `liquidity_bucket` / `liquidity_high` -> `candidate_recovery_or_relax`
- `entry_bucket_8`: `overbought_bucket` / `overbought_normal` -> `candidate_recovery_or_relax`
- `entry_bucket_9`: `score_band` / `score_66_69` -> `candidate_recovery_or_relax`
- `entry_bucket_10`: `score_band` / `score_70p` -> `candidate_recovery_or_relax`
- `entry_bucket_11`: `score_band` / `score_63_65` -> `candidate_recovery_or_relax`
- `entry_bucket_13`: `source_stage` / `wait6579_ev_cohort` -> `candidate_recovery_or_relax`
- `entry_bucket_14`: `stale_bucket` / `fresh_or_unflagged` -> `candidate_recovery_or_relax`
- `entry_bucket_15`: `strength_bucket` / `strong_strength_momentum` -> `candidate_recovery_or_relax`
- `entry_bucket_16`: `time_bucket` / `time_1000_1200` -> `candidate_recovery_or_relax`

### Entry Bucket Workorders

- `entry_bucket_source_quality_1`: `chosen_action` / `WAIT_REQUOTE` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_2`: `combo_entry_spot` / `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_3`: `combo_entry_spot` / `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_4`: `combo_entry_spot` / `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_5`: `combo_entry_spot` / `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_6`: `exit_rule` / `exit_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_7`: `liquidity_bucket` / `liquidity_high` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_8`: `overbought_bucket` / `overbought_normal` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_9`: `score_band` / `score_66_69` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_10`: `score_band` / `score_70p` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`

## Submit Bucket Attribution

- decision_authority: `adm_ldm_submit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'submit_rows': 213, 'bucket_count': 94, 'contract_gap_count': 0, 'workorder_count': 0, 'runtime_candidate_count': 0, 'quote_freshness_attribution_present': True, 'quote_freshness_resolution_counts': {'refresh_attempted_unresolved': 16, 'refresh_not_attempted_or_not_instrumented': 16, 'sim_submit_path_not_applicable': 181}, 'pre_submit_refresh_applied_counts': {'refresh_attempted_not_applied': 16, 'refresh_not_attempted_or_not_instrumented': 16, 'sim_submit_path_not_applicable': 181}, 'real_submitted_row_count': 5, 'missing_broker_order_key_count': 0, 'bot_history_broker_order_key_backfill_candidate_count': 0, 'bot_history_broker_order_key_backfill_full_coverage': False, 'bot_history_broker_order_key_exact_mapping_count': 0, 'bot_history_broker_order_key_exact_mapping_full_coverage': False, 'post_submit_provenance_join_resolution': 'no_gap_broker_order_key_present_or_no_missing_rows', 'bot_history_broker_order_key_backfill_candidates': [], 'missing_broker_order_key_rate': 0.0, 'post_submit_provenance_join_gap_raw': False, 'post_submit_provenance_join_gap': False}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 208 | 181 | -0.3372 | `keep_collecting` |
| `actual_order_submitted` | `true` | 5 | 0 | None | `keep_collecting` |
| `broker_order_forbidden` | `true` | 207 | 181 | -0.3372 | `keep_collecting` |
| `broker_order_forbidden` | `false` | 6 | 0 | None | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 57 | 57 | -0.5425 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 42 | 42 | -0.1886 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 23 | 23 | -0.0931 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 18 | 18 | -0.6084 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 17 | 17 | -0.1437 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 16 | 16 | -0.462 | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_attempted_unresolved|fill=false|submitted=false` | 15 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=pre_submit_liquidity_guard_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=latency_unknown|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=false` | 8 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 4 | 4 | 0.3745 | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=safe|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 2 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=pre_submit_liquidity_guard_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=latency_unknown|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=false` | 2 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_pass|revalidation=ok_or_unflagged|quote_age=quote_age_lt1s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=caution|refresh=refresh_attempted_unresolved|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=caution|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=safe|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=safe|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=pre_submit_liquidity_guard_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=latency_unknown|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | -0.5707 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | -0.4574 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | 1.1096 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=pullback_or_rebreak_not_confirmed|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | -0.8483 | `source_quality_workorder` |
| `latency_reason` | `scalp_live_simulator` | 181 | 181 | -0.3372 | `keep_collecting` |
| `latency_reason` | `latency_reason_unknown` | 11 | 0 | None | `source_quality_workorder` |
| `latency_reason` | `quote_stale,ws_age_too_high` | 7 | 0 | None | `keep_collecting` |
| `latency_reason` | `quote_stale,ws_age_too_high,spread_too_wide` | 5 | 0 | None | `keep_collecting` |
| `latency_reason` | `safe_normal_entry_allowed` | 4 | 0 | None | `keep_collecting` |
| `latency_reason` | `other_danger` | 3 | 0 | None | `keep_collecting` |
| `latency_reason` | `caution_normal_entry_allowed` | 1 | 0 | None | `keep_collecting` |
| `latency_reason` | `spread_too_wide` | 1 | 0 | None | `keep_collecting` |
| `latency_state` | `simulated` | 181 | 181 | -0.3372 | `keep_collecting` |
| `latency_state` | `danger` | 15 | 0 | None | `keep_collecting` |
| `latency_state` | `latency_unknown` | 11 | 0 | None | `source_quality_workorder` |
| `latency_state` | `safe` | 4 | 0 | None | `keep_collecting` |
| `latency_state` | `caution` | 2 | 0 | None | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 115 | 104 | -0.4063 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 77 | 77 | -0.2439 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_not_available` | 21 | 0 | None | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 197, 'source_row_count': 197, 'bucket_count': 34, 'joined_sample': 905, 'source_quality_adjusted_ev_pct': -0.7509, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 88 | 88 | -1.3561 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 40 | 40 | -1.2095 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 8 | 8 | 0.6799 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 8 | 8 | 0.8035 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 7 | 7 | 0.5455 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 7 | 7 | 0.4109 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 6 | 6 | 1.8846 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 4 | 4 | -0.4075 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 4 | 4 | -0.3475 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 3 | 3 | 2.7396 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 2 | 2 | -2.1721 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 2 | 2 | 0.14 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 1 | 1 | 0.7014 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 0.1 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 6 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos080_pos150|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_not_applicable_at_start` | 181 | 181 | -0.7509 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 14 | 0 | None | `hold_sample` |
| `holding_action` | `WAIT` | 114 | 114 | -0.8798 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 64 | 64 | -0.4995 | `candidate_tighten_or_exclude` |
| `holding_action` | `BUY` | 3 | 3 | -1.2142 | `candidate_tighten_or_exclude` |
| `holding_action` | `SELL_TODAY` | 16 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 181 | 181 | -0.7509 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 16 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 134 | 130 | -1.3235 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 16 | 16 | 0.6842 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos080_pos150` | 16 | 15 | 0.5544 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300_plus` | 9 | 9 | 2.1696 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 16 | 8 | -0.3775 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 6 | 3 | 0.1267 | `hold_no_edge` |

### Holding Bucket Attribution Workorders

- `holding_bucket_source_quality_1`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_2`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_3`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_4`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_5`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_6`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_7`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_8`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_9`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_10`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Exit Bucket Attribution

- decision_authority: `adm_ldm_exit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'exit_rows': 380, 'source_row_count': 380, 'bucket_count': 46, 'joined_sample': 1025, 'source_quality_adjusted_ev_pct': -0.7896, 'source_quality_gate': 'pass', 'unknown_reason_counts': {'not_applicable': 4, 'join_gap': 8, 'missing_source_field': 1}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 39 | 39 | -1.0632 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 24 | 24 | -2.4232 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 21 | 21 | -0.8282 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 20 | 20 | -1.544 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 20 | 20 | -0.8194 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 15 | 15 | -1.4827 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 9 | 9 | 0.4393 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 8 | 8 | -0.2831 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 6 | 6 | 0.9 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 5 | 5 | -1.2101 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 5 | 5 | 0.2458 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 5 | 5 | 1.4663 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 4 | 4 | -1.0312 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 4 | 4 | -0.565 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 4 | 4 | 1.1799 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 4 | 4 | 3.0488 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 4 | 4 | 0.0249 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 3 | 3 | 0.095 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300` | 3 | 3 | 0.7582 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos080_pos150` | 1 | 1 | 0.8925 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` | 1 | 1 | 0.97 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_euphoria_context_noop|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown` | 171 | 0 | None | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown` | 4 | 0 | None | `source_quality_workorder` |
| `exit_outcome` | `GOOD_EXIT` | 63 | 63 | -1.2146 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 55 | 55 | -0.2085 | `hold_no_edge` |
| `exit_outcome` | `NEUTRAL` | 51 | 51 | -0.8851 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 20 | 20 | -1.1765 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 191 | 16 | -0.3258 | `source_quality_workorder` |
| `exit_rule` | `scalp_soft_stop_pct` | 79 | 79 | -1.1232 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 50 | 50 | -1.632 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 40 | 40 | 0.9301 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 20 | 20 | -1.1765 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 16 | 16 | -0.3258 | `candidate_tighten_or_exclude` |
| `exit_rule` | `exit_rule_unknown` | 175 | 0 | None | `source_quality_workorder` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 169 | 169 | -0.7878 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 20 | 20 | -1.1765 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 16 | 16 | -0.3258 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_euphoria_context_noop` | 171 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 4 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 148 | 148 | -1.329 | `candidate_tighten_or_exclude` |

### Exit Bucket Attribution Workorders

- `exit_bucket_source_quality_1`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_2`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_3`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_4`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_5`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_6`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_7`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_8`: `combo_exit_result` / `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_9`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_10`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `incremental_notional_ev_pct`
- summary: `{'scale_in_rows': 21452, 'bucket_count': 4003, 'edge_bucket_count': 0, 'actionable_bucket_count': 0, 'runtime_authority_blocked_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'arm_counts': {'PYRAMID': 4880, 'AVG_DOWN': 16572}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_70p` | 16410 | 16410 | None | -0.4274 | 0.2122 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 2743 | 2743 | None | -0.3844 | 0.2122 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 850 | 850 | None | -0.5131 | 0.14 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 592 | 592 | None | -0.478 | 0.1875 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 288 | 288 | None | -0.3288 | 0.1389 | `hold_sample` |
| `ai_score_band` | `score_unknown` | 569 | 11 | None | 1.7527 | 0.9091 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 20883 | 20883 | None | -0.4253 | 0.2075 | `hold_sample` |
| `ai_score_source` | `sim_scale_in_source_not_scored` | 11 | 11 | None | 1.7527 | 0.9091 | `hold_sample` |
| `ai_score_source` | `stage_rule_backfilled` | 558 | 0 | None | None | None | `hold_sample` |
| `arm` | `AVG_DOWN` | 16572 | 16463 | None | -0.726 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 4880 | 4431 | None | 0.6974 | 0.9804 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 11012 | 10903 | None | -0.8867 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 5560 | 5560 | None | -0.4108 | 0.0 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 4880 | 4431 | None | 0.6974 | 0.9804 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 3460 | 3460 | None | 0.4579 | 0.989 | `hold_sample` |
| `blocker_reason` | `add_judgment_locked` | 3320 | 3320 | None | -0.3571 | 0.1018 | `hold_sample` |
| `blocker_reason` | `scalping_pyramid_ok` | 435 | 435 | None | 2.851 | 1.0 | `hold_sample` |
| `blocker_reason` | `low_broken` | 332 | 332 | None | -0.4652 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_scale_in_window_expansion` | 195 | 195 | None | -0.3816 | 0.3744 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.06)` | 187 | 187 | None | -0.06 | 0.0 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `adm_ldm_overnight_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'overnight_rows': 32, 'bucket_count': 27, 'actionable_bucket_count': 9, 'runtime_candidate_count': 9, 'workorder_count': 9, 'status_counts': {'HOLD_OVERNIGHT': 16, 'SELL_TODAY': 16}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 8 | 8 | -0.2831 | -0.3775 | 0.0 | `hold_no_edge` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 4 | 4 | -1.0312 | -1.375 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 3 | 3 | 0.095 | 0.1267 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 1 | 1 | 0.8925 | 1.19 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_lt_neg070` | 4 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg010_pos080` | 3 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 8 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_pos080_pos150` | 1 | 0 | None | None | None | `hold_sample` |
| `confidence_band` | `confidence_070p` | 32 | 16 | -0.3258 | -0.4344 | 0.25 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s_plus` | 28 | 14 | -0.3112 | -0.415 | 0.2857 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s` | 4 | 2 | -0.4275 | -0.57 | 0.0 | `hold_sample` |
| `overnight_action` | `SELL_TODAY` | 32 | 16 | -0.3258 | -0.4344 | 0.25 | `candidate_tighten_or_exclude` |
| `overnight_status` | `SELL_TODAY` | 16 | 16 | -0.3258 | -0.4344 | 0.25 | `candidate_tighten_or_exclude` |
| `overnight_status` | `HOLD_OVERNIGHT` | 16 | 0 | None | None | None | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 24 | 12 | -0.5325 | -0.71 | 0.0 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_zero_pos080` | 6 | 3 | 0.095 | 0.1267 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 2 | 1 | 0.8925 | 1.19 | 1.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 32 | 16 | -0.3258 | -0.4344 | 0.25 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 16 | 8 | -0.2831 | -0.3775 | 0.0 | `hold_no_edge` |
| `profit_band` | `profit_lt_neg070` | 8 | 4 | -1.0312 | -1.375 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 32 | 16 | -0.3258 | -0.4344 | 0.25 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 16 | 16 | -0.3258 | -0.4344 | 0.25 | `candidate_tighten_or_exclude` |
| `stage` | `exit` | 16 | 16 | -0.3258 | -0.4344 | 0.25 | `candidate_tighten_or_exclude` |

### Overnight Bucket Runtime Approval Candidates

- `overnight_bucket_1`: `confidence_band` / `confidence_070p` -> `candidate_tighten_or_exclude`
- `overnight_bucket_2`: `held_bucket` / `held_600_1800s_plus` -> `candidate_tighten_or_exclude`
- `overnight_bucket_3`: `overnight_action` / `SELL_TODAY` -> `candidate_tighten_or_exclude`
- `overnight_bucket_4`: `overnight_status` / `SELL_TODAY` -> `candidate_tighten_or_exclude`
- `overnight_bucket_5`: `peak_profit_band` / `peak_lt_zero` -> `candidate_tighten_or_exclude`
- `overnight_bucket_6`: `price_source` / `holding_price_samples_last` -> `candidate_tighten_or_exclude`
- `overnight_bucket_7`: `source_quality_gate` / `overnight_decision_coverage` -> `candidate_tighten_or_exclude`
- `overnight_bucket_8`: `source_stage` / `scalp_sim_overnight_sell_today` -> `candidate_tighten_or_exclude`
- `overnight_bucket_9`: `stage` / `exit` -> `candidate_tighten_or_exclude`

### Overnight Bucket Workorders

- `overnight_bucket_source_quality_1`: `confidence_band` / `confidence_070p` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_2`: `held_bucket` / `held_600_1800s_plus` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_3`: `overnight_action` / `SELL_TODAY` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_4`: `overnight_status` / `SELL_TODAY` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_5`: `peak_profit_band` / `peak_lt_zero` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_6`: `price_source` / `holding_price_samples_last` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_7`: `source_quality_gate` / `overnight_decision_coverage` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_8`: `source_stage` / `scalp_sim_overnight_sell_today` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_9`: `stage` / `exit` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`

## Fixed Threshold Roles

- `hard_safety`: broker_submit_guard, stale_quote_submit_block, price_freshness_guard, hard_stop, protect_stop, emergency_stop, account_order_cooldown_qty_guard
- `baseline_prior`: BUY_SCORE_THRESHOLD, VPW_MIN_SCORE, strength_momentum_cutoff, entry_score_cutoff
- `bounded_tunable`: SCALP_ENTRY_LATENCY_MAX_WS_AGE_MS_FOR_CAUTION, SCALP_ENTRY_LATENCY_MAX_WS_JITTER_MS_FOR_CAUTION, SCALP_ENTRY_LATENCY_MAX_SPREAD_RATIO_FOR_CAUTION, score65_74_recovery_probe, soft_stop_whipsaw_confirmation, holding_flow_override, scale_in_price_guard
- `legacy_archive`: fallback_scout_main, fallback_single, latency_fallback_split_entry, legacy_latency_composite, closed_shadow_axes

## Forbidden Uses

- `hard_safety_override`
- `real_execution_quality_from_sim_only`
- `intraday_threshold_mutation`
- `runtime_feature_future_label_leakage`
