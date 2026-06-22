# Lifecycle Decision Matrix - 2026-06-22

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-22`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `4940`
- source_rows_total: `5842`
- retained_rows: `4940`
- dropped_rows_by_source: `{'dedupe': 902}`
- joined_rows: `3503`
- policy_pass_count: `5`
- promote_ready_count: `1`
- entry_bucket_actionable_count: `14`
- entry_bucket_runtime_candidate_count: `8`
- holding_bucket_count/workorders: `37` / `10`
- exit_bucket_count/workorders: `49` / `10`
- scale_in_bucket_actionable_count: `0`
- scale_in_bucket_runtime_candidate_count: `0`
- overnight_bucket_actionable_count: `9`
- overnight_bucket_runtime_candidate_count: `8`
- lifecycle_flow_bucket_count: `130`
- lifecycle_flow_complete_count: `65`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `0` / `65` / `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0166`
- incomplete_flow_reason_counts: `{'missing_entry': 3566, 'missing_holding': 3790, 'missing_exit': 3350, 'missing_submit': 3803, 'candidate_id_only': 3560, 'sim_record_id_only': 145, 'scale_in_noise_only': 3068, 'postclose_exit_without_entry': 491}`
- bucket_directed_sim_probe: `{'observed_row_count': 1159, 'matched_row_count': 23, 'background_row_count': 1136, 'matched_unique_source_bucket_count': 2, 'match_status_counts': {'matched': 23, 'no_match': 613, 'not_instrumented': 523}, 'matched_classification_state_counts': {'lifecycle_flow_sim_probe_candidate': 23}, 'primary_source': 'matched_bucket_directed_sim_probe_only', 'background_source': 'unmatched_or_policy_missing_sim_observation', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 1, 'route_counts': {'bounded_auxiliary_weight': 1, 'hold_sample': 4}, 'quality_counts': {'observational_only_pending_outcome': 1, 'hold_sample': 4}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 750 | 75 | 0.568 | 0.75 | `pass` | `BUY_DEFENSIVE` | True |
| `submit` | 209 | 113 | -0.0536 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 213 | 113 | -0.8397 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 3169 | 2993 | -0.4236 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 599 | 209 | -0.7225 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 3906, 'complete_flow_count': 65, 'direct_sim_record_complete_flow_count': 0, 'adm_bridge_complete_flow_count': 65, 'fallback_complete_flow_count': 0, 'direct_flow_zero_diagnostic': {'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'direct_sim_record_flow_count': 145, 'direct_sim_record_incomplete_flow_count': 145, 'direct_sim_record_stage_coverage_counts': {'exit': 101, 'holding': 20}, 'direct_sim_record_incomplete_reason_counts': {'missing_entry': 145, 'missing_submit': 145, 'missing_holding': 125, 'missing_exit': 44, 'sim_record_id_only': 145, 'scale_in_noise_only': 44, 'postclose_exit_without_entry': 101}, 'runtime_effect': False, 'decision_authority': 'ldm_direct_flow_diagnostic_only'}, 'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'incomplete_flow_count': 3841, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 4940, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0166, 'complete_flow_conversion_denominator': 563, 'complete_flow_conversion_rate': 0.1155, 'active_priority_incomplete_seed_count': 275, 'scale_in_followup_event_count': 3169, 'scale_in_unique_flow_count': 2962, 'scale_in_noise_flow_count': 3068, 'denominator_exclusion_counts': {'scale_in_noise_flow_excluded': 3068, 'active_priority_incomplete_seed_excluded': 275}, 'conversion_blocker_reason_counts': {'missing_entry': 498, 'missing_holding': 478, 'missing_exit': 7, 'missing_submit': 491, 'sim_record_id_only': 101, 'postclose_exit_without_entry': 491, 'candidate_id_only': 390}, 'observation_seed_reason_counts': {'missing_submit': 3312, 'missing_holding': 3312, 'missing_exit': 3343, 'candidate_id_only': 3170, 'missing_entry': 3068, 'sim_record_id_only': 44, 'scale_in_noise_only': 3068}, 'join_contract_blocked': False, 'bundle_ev_tuning_state': 'ready_for_bundle_ev_tuning', 'top_incomplete_reason': 'missing_submit', 'stage_identity': {'entry': {'source_row_count': 750, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 604, 'candidate_id': 146}, 'identity_join_rate': 1.0}, 'submit': {'source_row_count': 209, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 209}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 213, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 193, 'exact_sim_record_id': 20}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 3169, 'identity_missing_count': 0, 'identity_quality_counts': {'exact_sim_record_id': 145, 'candidate_id': 3024}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 599, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 96, 'exact_sim_record_id': 113, 'candidate_id': 390}, 'identity_join_rate': 1.0}}, 'required_stage_source_counts': {'entry': 750, 'submit': 209, 'holding': 213, 'exit': 599}, 'incomplete_flow_reason_counts': {'missing_entry': 3566, 'missing_holding': 3790, 'missing_exit': 3350, 'missing_submit': 3803, 'candidate_id_only': 3560, 'sim_record_id_only': 145, 'scale_in_noise_only': 3068, 'postclose_exit_without_entry': 491}, 'bucket_count': 130, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:4fa8c887a4` | 2 | 2 | -0.4466 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:89e49a11bc` | 2 | 2 | -1.3344 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:df69d30b89` | 2 | 2 | -0.7517 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:388199cb18` | 2 | 2 | -1.144 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:76e538b0ff` | 2 | 2 | -2.0015 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:14e5424738` | 1 | 1 | -2.5811 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:46c66915b5` | 1 | 1 | -1.4956 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:c982e1d321` | 1 | 1 | -1.3611 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:bc5e32bf5e` | 1 | 1 | -1.1306 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:44bfe8840d` | 1 | 1 | -1.1528 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:84b7dde4a3` | 1 | 1 | -1.1838 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:06a029c7a2` | 1 | 1 | -1.276 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:a1bf60d3a7` | 1 | 1 | 0.1536 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:1e13768d55` | 1 | 1 | -1.0825 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:2b39f2b635` | 1 | 1 | -1.5259 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:67138f9e63` | 1 | 1 | -1.0121 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:d3080a9399` | 1 | 1 | -1.258 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:f7df4238eb` | 1 | 1 | -0.0261 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:84461e0e65` | 1 | 1 | 2.0803 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:67a530f66b` | 1 | 1 | -1.6228 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 750, 'bucket_count': 202, 'actionable_bucket_count': 14, 'source_quality_blocked_bucket_count': 0, 'runtime_candidate_count': 8, 'workorder_count': 10}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `WAIT_REQUOTE` | 42 | 42 | 0.9539 | 1.3667 | 0.619 | `candidate_recovery_or_relax` |
| `chosen_action` | `NO_BUY_AI` | 581 | 25 | 0.1396 | -1.5036 | 0.28 | `hold_no_edge` |
| `chosen_action` | `BUY_NOW` | 22 | 8 | -0.1198 | 0.0 | 0.25 | `hold_sample` |
| `chosen_action` | `ALLOW_BOTTOMING_ENTRY` | 6 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `ALLOW_LEVEL1_RISK_OFF_ENTRY` | 98 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_SOURCE_QUALITY` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 13 | 13 | 1.9047 | 2.7858 | 0.6154 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 11 | 11 | 1.228 | 1.6194 | 0.7273 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 5 | 5 | -2.4165 | -3.0668 | 0.2 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 8 | 5 | 0.1382 | -1.388 | 0.2 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 7 | 5 | -0.1123 | 3.08 | 0.8 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 77 | 4 | -0.6536 | -1.3675 | 0.25 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 51 | 3 | 0.2984 | -0.5133 | 0.3333 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 3 | 3 | -1.4642 | -1.8874 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 13 | 2 | 0.5228 | -2.075 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 43 | 2 | 0.5148 | -3.61 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 2 | 2 | 1.4093 | 1.5275 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 2 | 2 | 1.4829 | 1.4233 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 4 | 2 | 0.3377 | -2.31 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_ok|time=time_0900_1000` | 2 | 2 | 3.5561 | 5.6395 | 1.0 | `hold_sample` |
| `exit_rule` | `exit_unknown` | 717 | 42 | 0.9539 | 1.3667 | 0.619 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_soft_stop_pct` | 13 | 13 | 0.049 | -2.1362 | 0.0 | `hold_no_edge` |
| `exit_rule` | `scalp_hard_stop_pct` | 11 | 11 | 0.3419 | -3.3318 | 0.0 | `candidate_recovery_or_relax` |
| `liquidity_bucket` | `liquidity_high` | 564 | 73 | 0.6173 | 0.3225 | 0.4658 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 521 | 59 | 0.6398 | -0.0428 | 0.4237 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_watch` | 105 | 13 | -0.12 | 1.0245 | 0.6154 | `hold_no_edge` |
| `score_band` | `score_70p` | 111 | 44 | 1.0203 | 1.311 | 0.5455 | `candidate_recovery_or_relax` |
| `score_band` | `score_60_62` | 423 | 14 | -0.2892 | -1.855 | 0.2143 | `hold_no_edge` |
| `score_band` | `score_66_69` | 25 | 10 | -0.8833 | -1.3241 | 0.5 | `candidate_tighten_or_exclude` |
| `source_stage` | `wait6579_ev_cohort` | 42 | 42 | 0.9539 | 1.3667 | 0.619 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 418 | 33 | 0.0768 | -1.1391 | 0.2727 | `hold_no_edge` |
| `stale_bucket` | `fresh_or_unflagged` | 146 | 42 | 0.9539 | 1.3667 | 0.619 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh` | 218 | 18 | 0.1637 | 0.1378 | 0.4444 | `hold_no_edge` |
| `stale_bucket` | `stale_high` | 320 | 15 | -0.0275 | -2.6713 | 0.0667 | `hold_no_edge` |
| `strength_bucket` | `strong_strength_momentum` | 104 | 45 | 0.7829 | 1.053 | 0.6 | `candidate_recovery_or_relax` |
| `strength_bucket` | `weak_strength_momentum` | 498 | 26 | 0.3026 | -0.8667 | 0.2308 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_0900_1000` | 320 | 44 | 0.2147 | 0.2667 | 0.5 | `hold_no_edge` |
| `time_bucket` | `time_1000_1200` | 281 | 26 | 1.3276 | 1.0843 | 0.5 | `candidate_recovery_or_relax` |

### Entry Bucket Runtime Approval Candidates

- `entry_bucket_6`: `liquidity_bucket` / `liquidity_high` -> `candidate_recovery_or_relax`
- `entry_bucket_7`: `overbought_bucket` / `overbought_normal` -> `candidate_recovery_or_relax`
- `entry_bucket_8`: `score_band` / `score_70p` -> `candidate_recovery_or_relax`
- `entry_bucket_10`: `source_stage` / `wait6579_ev_cohort` -> `candidate_recovery_or_relax`
- `entry_bucket_11`: `stale_bucket` / `fresh_or_unflagged` -> `candidate_recovery_or_relax`
- `entry_bucket_12`: `strength_bucket` / `strong_strength_momentum` -> `candidate_recovery_or_relax`
- `entry_bucket_13`: `strength_bucket` / `weak_strength_momentum` -> `candidate_recovery_or_relax`
- `entry_bucket_14`: `time_bucket` / `time_1000_1200` -> `candidate_recovery_or_relax`

### Entry Bucket Workorders

- `entry_bucket_source_quality_1`: `chosen_action` / `WAIT_REQUOTE` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_2`: `combo_entry_spot` / `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_3`: `combo_entry_spot` / `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_4`: `exit_rule` / `exit_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_5`: `exit_rule` / `scalp_hard_stop_pct` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_6`: `liquidity_bucket` / `liquidity_high` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_7`: `overbought_bucket` / `overbought_normal` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_8`: `score_band` / `score_70p` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_9`: `score_band` / `score_66_69` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_10`: `source_stage` / `wait6579_ev_cohort` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`

## Submit Bucket Attribution

- decision_authority: `adm_ldm_submit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'submit_rows': 209, 'bucket_count': 96, 'contract_gap_count': 0, 'workorder_count': 0, 'runtime_candidate_count': 0, 'quote_freshness_attribution_present': True, 'quote_freshness_resolution_counts': {'refresh_attempted_unresolved': 3, 'refresh_failed_quote_stale': 1, 'refresh_not_attempted_or_not_instrumented': 8, 'refresh_resolved_quote_freshness': 3, 'sim_submit_path_not_applicable': 194}, 'pre_submit_refresh_applied_counts': {'refresh_attempted_not_applied': 4, 'refresh_not_attempted_or_not_instrumented': 8, 'sim_submit_path_not_applicable': 194, 'ws_snapshot_refresh_applied': 3}, 'real_submitted_row_count': 1, 'missing_broker_order_key_count': 0, 'bot_history_broker_order_key_backfill_candidate_count': 0, 'bot_history_broker_order_key_backfill_full_coverage': False, 'bot_history_broker_order_key_exact_mapping_count': 0, 'bot_history_broker_order_key_exact_mapping_full_coverage': False, 'post_submit_provenance_join_resolution': 'no_gap_broker_order_key_present_or_no_missing_rows', 'bot_history_broker_order_key_backfill_candidates': [], 'missing_broker_order_key_rate': 0.0, 'post_submit_provenance_join_gap_raw': False, 'post_submit_provenance_join_gap': False}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 208 | 113 | -0.0536 | `keep_collecting` |
| `actual_order_submitted` | `true` | 1 | 0 | None | `keep_collecting` |
| `broker_order_forbidden` | `true` | 208 | 113 | -0.0536 | `keep_collecting` |
| `broker_order_forbidden` | `false` | 1 | 0 | None | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 67 | 27 | 0.238 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 54 | 36 | -0.2845 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 18 | 17 | 0.1025 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 15 | 10 | -0.2611 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 12 | 2 | 0.89 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 9 | 9 | -0.2737 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 6 | 3 | 0.6472 | `source_quality_workorder` |
| `combo_submit_quality` | `source=pre_submit_liquidity_guard_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=latency_unknown|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=false` | 5 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 5 | 3 | -0.9169 | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_attempted_unresolved|fill=false|submitted=false` | 3 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_resolved_quote_freshness|fill=false|submitted=false` | 3 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 2 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_unknown|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=would_unknown|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 2 | 2 | -0.2679 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 2 | 2 | 0.473 | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_failed_quote_stale|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=caution|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=pre_submit_liquidity_guard_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=below_min_liquidity|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=latency_unknown|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=pre_submit_liquidity_guard_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=latency_unknown|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=pullback_or_rebreak_not_confirmed|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | -0.4411 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_overbought_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=pullback_or_rebreak_not_confirmed|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | 0.1497 | `source_quality_workorder` |
| `latency_reason` | `scalp_live_simulator` | 194 | 113 | -0.0536 | `keep_collecting` |
| `latency_reason` | `latency_reason_unknown` | 7 | 0 | None | `source_quality_workorder` |
| `latency_reason` | `other_danger` | 3 | 0 | None | `keep_collecting` |
| `latency_reason` | `spread_too_wide` | 3 | 0 | None | `keep_collecting` |
| `latency_reason` | `caution_normal_entry_allowed` | 1 | 0 | None | `keep_collecting` |
| `latency_reason` | `quote_stale,ws_age_too_high` | 1 | 0 | None | `keep_collecting` |
| `latency_state` | `simulated` | 194 | 113 | -0.0536 | `keep_collecting` |
| `latency_state` | `danger` | 7 | 0 | None | `keep_collecting` |
| `latency_state` | `latency_unknown` | 7 | 0 | None | `source_quality_workorder` |
| `latency_state` | `caution` | 1 | 0 | None | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 102 | 69 | -0.1936 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 97 | 42 | 0.1865 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_not_available` | 10 | 2 | -0.2679 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 97 | 42 | 0.1865 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 95 | 69 | -0.1936 | `keep_collecting` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 15 | 0 | None | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 213, 'source_row_count': 213, 'bucket_count': 37, 'joined_sample': 565, 'source_quality_adjusted_ev_pct': -0.8397, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 54 | 54 | -1.5132 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 27 | 27 | -1.3257 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 7 | 7 | 1.5423 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 6 | 6 | 0.982 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 4 | 4 | -1.3503 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 4 | 4 | 0.1 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 4 | 4 | -0.3825 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 3 | 3 | 2.3429 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 2 | 2 | 2.0801 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 0.53 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 1 | 1 | 0.7506 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 72 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 8 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 5 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos080_pos150|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos080_pos150|held=held_600_1800s_plus` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos150_pos300_plus|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos150_pos300|held=held_600_1800s_plus` | 3 | 0 | None | `hold_sample` |
| `held_bucket` | `held_not_applicable_at_start` | 193 | 113 | -0.8397 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 18 | 0 | None | `hold_sample` |
| `holding_action` | `WAIT` | 149 | 77 | -0.8051 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 40 | 32 | -0.8589 | `candidate_tighten_or_exclude` |
| `holding_action` | `BUY` | 4 | 4 | -1.3503 | `candidate_tighten_or_exclude` |
| `holding_action` | `SELL_TODAY` | 20 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 193 | 113 | -0.8397 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 20 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 88 | 85 | -1.446 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 11 | 8 | 1.4434 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos080_pos150` | 10 | 6 | 0.982 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg010_pos080` | 9 | 5 | 0.186 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300_plus` | 6 | 5 | 2.2378 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 9 | 4 | -0.3825 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_not_applicable_at_start` | 80 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- `holding_bucket_source_quality_1`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_2`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_3`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_4`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_5`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_6`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_7`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_8`: `held_bucket` / `held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_9`: `holding_action` / `WAIT` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_10`: `holding_action` / `holding_action_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Exit Bucket Attribution

- decision_authority: `adm_ldm_exit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'exit_rows': 599, 'source_row_count': 599, 'bucket_count': 49, 'joined_sample': 1045, 'source_quality_adjusted_ev_pct': -0.7225, 'source_quality_gate': 'pass', 'unknown_reason_counts': {'not_applicable': 6, 'join_gap': 8, 'missing_source_field': 1}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 52 | 52 | -1.216 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 27 | 27 | -0.4352 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 22 | 22 | -1.393 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 15 | 15 | -1.319 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 14 | 14 | -1.7871 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 12 | 12 | -0.6904 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 11 | 11 | -2.295 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 10 | 10 | -1.1275 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 8 | 8 | 0.1962 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 5 | 5 | 0.1395 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 4 | 4 | -0.2869 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos080_pos150` | 4 | 4 | 0.7725 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 3 | 3 | -1.195 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos150_pos300` | 3 | 3 | 1.7025 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` | 3 | 3 | 0.9833 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos150_pos300_plus` | 3 | 3 | 4.4337 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 3 | 3 | 0.4327 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 3 | 3 | 2.316 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 2 | 2 | 2.1204 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos150_pos300_plus` | 1 | 1 | 4.5525 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 1 | 1 | 1.7617 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 1 | 1 | 2.2884 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 1 | 1 | 0.0103 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300` | 1 | 1 | 1.1504 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_euphoria_context_noop|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown` | 187 | 0 | None | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown` | 203 | 0 | None | `source_quality_workorder` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 93 | 93 | -0.6146 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 39 | 39 | -0.7162 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 31 | 31 | -1.2739 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 26 | 26 | -1.3513 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 410 | 20 | 0.4357 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 93 | 93 | -0.6146 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 47 | 47 | -1.7215 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 37 | 37 | -1.0634 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 20 | 20 | 0.4357 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_trailing_take_profit` | 12 | 12 | 1.4748 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_rule_unknown` | 390 | 0 | None | `source_quality_workorder` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 96 | 96 | -1.0683 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 93 | 93 | -0.6146 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 20 | 20 | 0.4357 | `candidate_recovery_or_relax` |

### Exit Bucket Attribution Workorders

- `exit_bucket_source_quality_1`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_2`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_3`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_4`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_5`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_6`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_7`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_8`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_9`: `combo_exit_result` / `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_10`: `combo_exit_result` / `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `incremental_notional_ev_pct`
- summary: `{'scale_in_rows': 3169, 'bucket_count': 532, 'edge_bucket_count': 0, 'actionable_bucket_count': 0, 'runtime_authority_blocked_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'arm_counts': {'PYRAMID': 821, 'AVG_DOWN': 2348}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_70p` | 1890 | 1890 | None | -0.5287 | 0.2196 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 503 | 503 | None | -0.4704 | 0.2167 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 322 | 322 | None | -0.4396 | 0.2236 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 156 | 156 | None | -0.1149 | 0.2756 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 116 | 116 | None | -0.1903 | 0.2845 | `hold_sample` |
| `ai_score_band` | `score_unknown` | 182 | 6 | None | -0.822 | 0.4 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 2987 | 2987 | None | -0.4745 | 0.225 | `hold_sample` |
| `ai_score_source` | `sim_scale_in_source_not_scored` | 6 | 6 | None | -0.822 | 0.4 | `hold_sample` |
| `ai_score_source` | `stage_rule_backfilled` | 176 | 0 | None | None | None | `hold_sample` |
| `arm` | `AVG_DOWN` | 2348 | 2307 | None | -0.985 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 821 | 686 | None | 1.2422 | 0.9839 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 1666 | 1625 | None | -1.2231 | 0.0 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 821 | 686 | None | 1.2422 | 0.9839 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 682 | 682 | None | -0.4178 | 0.0 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 451 | 451 | None | 0.5923 | 0.9867 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 139 | 139 | None | -0.7305 | 0.1511 | `hold_sample` |
| `blocker_reason` | `scalping_pyramid_ok` | 130 | 130 | None | 3.1431 | 1.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_scale_in_window_expansion` | 83 | 83 | None | -0.2729 | 0.3494 | `hold_sample` |
| `blocker_reason` | `ok` | 82 | 82 | None | -2.6541 | 0.0 | `hold_sample` |
| `blocker_reason` | `low_broken` | 60 | 60 | None | -0.3682 | 0.0 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `adm_ldm_overnight_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'overnight_rows': 40, 'bucket_count': 35, 'actionable_bucket_count': 9, 'runtime_candidate_count': 8, 'workorder_count': 9, 'status_counts': {'HOLD_OVERNIGHT': 20, 'SELL_TODAY': 20}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 5 | 5 | -0.2445 | -0.326 | 0.0 | `hold_no_edge` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 4 | 4 | 0.1931 | 0.2575 | 0.75 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 4 | 4 | 0.7725 | 1.03 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 3 | 3 | -1.195 | -1.5933 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos150_pos300` | 3 | 3 | 1.7025 | 2.27 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos150_pos300_plus` | 1 | 1 | 4.5525 | 6.07 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_lt_neg070` | 3 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg010_pos080` | 4 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 5 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_pos080_pos150` | 4 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_pos150_pos300` | 3 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_pos150_pos300_plus` | 1 | 0 | None | None | None | `hold_sample` |
| `confidence_band` | `confidence_070p` | 40 | 20 | 0.4357 | 0.581 | 0.55 | `candidate_recovery_or_relax` |
| `held_bucket` | `held_600_1800s_plus` | 36 | 18 | 0.4183 | 0.5578 | 0.5 | `candidate_recovery_or_relax` |
| `held_bucket` | `held_600_1800s` | 4 | 2 | 0.5925 | 0.79 | 1.0 | `hold_sample` |
| `overnight_action` | `SELL_TODAY` | 40 | 20 | 0.4357 | 0.581 | 0.55 | `candidate_recovery_or_relax` |
| `overnight_status` | `SELL_TODAY` | 20 | 20 | 0.4357 | 0.581 | 0.55 | `candidate_recovery_or_relax` |
| `overnight_status` | `HOLD_OVERNIGHT` | 20 | 0 | None | None | None | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 18 | 9 | -0.54 | -0.72 | 0.0 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_pos080_pos150` | 8 | 4 | 0.7725 | 1.03 | 1.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 40 | 20 | 0.4357 | 0.581 | 0.55 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 10 | 5 | -0.2445 | -0.326 | 0.0 | `hold_no_edge` |
| `source_quality_gate` | `overnight_decision_coverage` | 40 | 20 | 0.4357 | 0.581 | 0.55 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 20 | 20 | 0.4357 | 0.581 | 0.55 | `candidate_recovery_or_relax` |
| `stage` | `exit` | 20 | 20 | 0.4357 | 0.581 | 0.55 | `candidate_recovery_or_relax` |

### Overnight Bucket Runtime Approval Candidates

- `overnight_bucket_1`: `confidence_band` / `confidence_070p` -> `candidate_recovery_or_relax`
- `overnight_bucket_2`: `held_bucket` / `held_600_1800s_plus` -> `candidate_recovery_or_relax`
- `overnight_bucket_3`: `overnight_action` / `SELL_TODAY` -> `candidate_recovery_or_relax`
- `overnight_bucket_4`: `overnight_status` / `SELL_TODAY` -> `candidate_recovery_or_relax`
- `overnight_bucket_6`: `price_source` / `holding_price_samples_last` -> `candidate_recovery_or_relax`
- `overnight_bucket_7`: `source_quality_gate` / `overnight_decision_coverage` -> `candidate_recovery_or_relax`
- `overnight_bucket_8`: `source_stage` / `scalp_sim_overnight_sell_today` -> `candidate_recovery_or_relax`
- `overnight_bucket_9`: `stage` / `exit` -> `candidate_recovery_or_relax`

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
