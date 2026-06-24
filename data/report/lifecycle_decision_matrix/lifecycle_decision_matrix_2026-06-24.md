# Lifecycle Decision Matrix - 2026-06-24

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-24`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `6192`
- source_rows_total: `8087`
- retained_rows: `6192`
- dropped_rows_by_source: `{'dedupe': 1895}`
- joined_rows: `3923`
- policy_pass_count: `5`
- promote_ready_count: `1`
- entry_bucket_actionable_count: `20`
- entry_bucket_runtime_candidate_count: `10`
- holding_bucket_count/workorders: `30` / `10`
- exit_bucket_count/workorders: `51` / `10`
- scale_in_bucket_actionable_count: `0`
- scale_in_bucket_runtime_candidate_count: `0`
- overnight_bucket_actionable_count: `0`
- overnight_bucket_runtime_candidate_count: `0`
- lifecycle_flow_bucket_count: `82`
- lifecycle_flow_complete_count: `32`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `0` / `32` / `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0059`
- incomplete_flow_reason_counts: `{'missing_holding': 5334, 'missing_exit': 3766, 'missing_submit': 5335, 'missing_entry': 5102, 'postclose_exit_without_entry': 1589, 'candidate_id_only': 5168, 'sim_record_id_only': 97, 'scale_in_noise_only': 3513}`
- bucket_directed_sim_probe: `{'observed_row_count': 2025, 'matched_row_count': 8, 'background_row_count': 2017, 'matched_unique_source_bucket_count': 1, 'match_status_counts': {'matched': 8, 'no_match': 424, 'not_instrumented': 1593}, 'matched_classification_state_counts': {'lifecycle_flow_sim_probe_candidate': 8}, 'primary_source': 'matched_bucket_directed_sim_probe_only', 'background_source': 'unmatched_or_policy_missing_sim_observation', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 0, 'route_counts': {'bounded_auxiliary_weight': 1, 'hold_sample': 4}, 'quality_counts': {'observational_only_pending_outcome': 1, 'hold_sample': 4}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 671 | 107 | 1.0952 | 1.0 | `pass` | `BUY_DEFENSIVE` | True |
| `submit` | 136 | 69 | -0.629 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 128 | 69 | -1.185 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 3600 | 3516 | -0.4747 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 1657 | 162 | -0.9513 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 5387, 'complete_flow_count': 32, 'direct_sim_record_complete_flow_count': 0, 'adm_bridge_complete_flow_count': 32, 'fallback_complete_flow_count': 0, 'direct_flow_zero_diagnostic': {'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'direct_sim_record_flow_count': 97, 'direct_sim_record_incomplete_flow_count': 97, 'direct_sim_record_stage_coverage_counts': {'holding': 4, 'exit': 90}, 'direct_sim_record_incomplete_reason_counts': {'missing_entry': 97, 'missing_submit': 97, 'missing_holding': 93, 'missing_exit': 7, 'sim_record_id_only': 97, 'scale_in_noise_only': 7, 'postclose_exit_without_entry': 90}, 'runtime_effect': False, 'decision_authority': 'ldm_direct_flow_diagnostic_only'}, 'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'incomplete_flow_count': 5355, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 6192, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0059, 'complete_flow_conversion_denominator': 1621, 'complete_flow_conversion_rate': 0.0197, 'active_priority_incomplete_seed_count': 253, 'scale_in_followup_event_count': 3600, 'scale_in_unique_flow_count': 2958, 'scale_in_noise_flow_count': 3513, 'denominator_exclusion_counts': {'scale_in_noise_flow_excluded': 3513, 'active_priority_incomplete_seed_excluded': 253}, 'conversion_blocker_reason_counts': {'missing_entry': 1589, 'missing_submit': 1589, 'missing_holding': 1585, 'postclose_exit_without_entry': 1589, 'sim_record_id_only': 90, 'candidate_id_only': 1495}, 'observation_seed_reason_counts': {'missing_holding': 3749, 'missing_exit': 3766, 'missing_submit': 3746, 'candidate_id_only': 3673, 'missing_entry': 3513, 'sim_record_id_only': 7, 'scale_in_noise_only': 3513}, 'join_contract_blocked': False, 'bundle_ev_tuning_state': 'ready_for_bundle_ev_tuning', 'top_incomplete_reason': 'missing_submit', 'stage_identity': {'entry': {'source_row_count': 671, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 504, 'candidate_id': 167}, 'identity_join_rate': 1.0}, 'submit': {'source_row_count': 136, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 136}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 128, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 124, 'exact_sim_record_id': 4}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 3600, 'identity_missing_count': 0, 'identity_quality_counts': {'exact_sim_record_id': 94, 'candidate_id': 3506}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 1657, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 68, 'exact_sim_record_id': 94, 'candidate_id': 1495}, 'identity_join_rate': 1.0}}, 'required_stage_source_counts': {'entry': 671, 'submit': 136, 'holding': 128, 'exit': 1657}, 'incomplete_flow_reason_counts': {'missing_holding': 5334, 'missing_exit': 3766, 'missing_submit': 5335, 'missing_entry': 5102, 'postclose_exit_without_entry': 1589, 'candidate_id_only': 5168, 'sim_record_id_only': 97, 'scale_in_noise_only': 3513}, 'bucket_count': 82, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:84461e0e65` | 2 | 2 | 3.097 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:2a4bfd22da` | 2 | 2 | -1.6246 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:b24470d667` | 1 | 1 | -1.5684 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:f1c1fcc930` | 1 | 1 | -2.4303 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:0d1ad9d351` | 1 | 1 | -1.2361 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:fdcf3965a4` | 1 | 1 | -0.4533 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:c3a750aefc` | 1 | 1 | -1.1304 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:8050d08a3f` | 1 | 1 | -1.9237 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:3cbb81cd02` | 1 | 1 | -1.6289 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:d8b4aa95dd` | 1 | 1 | -1.5637 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:8fb049af92` | 1 | 1 | 0.8299 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:5a2fc3c833` | 1 | 1 | -1.102 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:c86da1173b` | 1 | 1 | -0.063 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_bl:c4c0159799` | 1 | 1 | -1.2035 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:18f09004f7` | 1 | 1 | -1.1465 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:d11ef6d7dd` | 1 | 1 | -0.2501 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:b063da6501` | 1 | 1 | -0.7288 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:0ebf5532de` | 1 | 1 | -1.6084 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_sc:3f78c749f3` | 1 | 1 | -1.9731 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_sc:ad2470e217` | 1 | 1 | -0.4607 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 671, 'bucket_count': 215, 'actionable_bucket_count': 20, 'source_quality_blocked_bucket_count': 0, 'runtime_candidate_count': 10, 'workorder_count': 10}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `WAIT_REQUOTE` | 77 | 77 | 1.6558 | 2.6637 | 0.5714 | `candidate_recovery_or_relax` |
| `chosen_action` | `NO_BUY_AI` | 475 | 29 | -0.3656 | -0.9134 | 0.2414 | `candidate_tighten_or_exclude` |
| `chosen_action` | `BUY_NOW` | 25 | 1 | 0.2905 | -2.5 | 0.0 | `hold_sample` |
| `chosen_action` | `ALLOW_BOTTOMING_ENTRY` | 8 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `ALLOW_LEVEL1_RISK_OFF_ENTRY` | 82 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_SOURCE_QUALITY` | 4 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1400_close` | 12 | 12 | 2.0293 | 3.4187 | 0.75 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 8 | 8 | -0.0504 | -0.2316 | 0.375 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 8 | 8 | 0.7878 | 0.9157 | 0.625 | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 6 | 6 | 0.0274 | -0.2605 | 0.3333 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 28 | 5 | -2.0229 | -2.09 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 5 | 5 | -0.2247 | -0.3395 | 0.4 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 5 | 5 | 0.9411 | 0.9094 | 0.6 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 27 | 4 | 1.3856 | -1.225 | 0.25 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 19 | 4 | -1.0366 | -1.925 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1400_close` | 4 | 4 | 4.0769 | 6.4095 | 0.75 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 4 | 4 | 1.8054 | 2.3599 | 0.75 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 3 | 3 | 1.196 | 1.4698 | 0.6667 | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 3 | 3 | 2.6909 | 4.3564 | 0.6667 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1400_close` | 3 | 3 | 2.6538 | 4.6006 | 0.3333 | `hold_sample` |
| `exit_rule` | `exit_unknown` | 641 | 77 | 1.6558 | 2.6637 | 0.5714 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_soft_stop_pct` | 14 | 14 | -0.2054 | -1.91 | 0.0 | `hold_no_edge` |
| `liquidity_bucket` | `liquidity_high` | 518 | 107 | 1.0952 | 1.6459 | 0.4766 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 446 | 83 | 0.737 | 0.9506 | 0.4458 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_watch` | 113 | 17 | 1.4087 | 2.296 | 0.6471 | `candidate_recovery_or_relax` |
| `score_band` | `score_66_69` | 76 | 39 | 2.2422 | 3.6771 | 0.5897 | `candidate_recovery_or_relax` |
| `score_band` | `score_70p` | 86 | 31 | 0.5547 | 0.5718 | 0.4839 | `candidate_recovery_or_relax` |
| `score_band` | `score_60_62` | 359 | 19 | -0.5191 | -1.4111 | 0.1579 | `candidate_tighten_or_exclude` |
| `score_band` | `score_63_65` | 80 | 17 | 1.2556 | 2.3324 | 0.5294 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 77 | 77 | 1.6558 | 2.6637 | 0.5714 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 398 | 30 | -0.3438 | -0.9663 | 0.2333 | `candidate_tighten_or_exclude` |

### Entry Bucket Runtime Approval Candidates

- `entry_bucket_5`: `liquidity_bucket` / `liquidity_high` -> `candidate_recovery_or_relax`
- `entry_bucket_6`: `overbought_bucket` / `overbought_normal` -> `candidate_recovery_or_relax`
- `entry_bucket_8`: `score_band` / `score_66_69` -> `candidate_recovery_or_relax`
- `entry_bucket_9`: `score_band` / `score_70p` -> `candidate_recovery_or_relax`
- `entry_bucket_12`: `source_stage` / `wait6579_ev_cohort` -> `candidate_recovery_or_relax`
- `entry_bucket_13`: `source_stage` / `scalp_entry_action_decision_snapshot` -> `candidate_tighten_or_exclude`
- `entry_bucket_14`: `stale_bucket` / `fresh_or_unflagged` -> `candidate_recovery_or_relax`
- `entry_bucket_16`: `strength_bucket` / `strong_strength_momentum` -> `candidate_recovery_or_relax`
- `entry_bucket_17`: `time_bucket` / `time_1000_1200` -> `candidate_recovery_or_relax`
- `entry_bucket_18`: `time_bucket` / `time_0900_1000` -> `candidate_recovery_or_relax`

### Entry Bucket Workorders

- `entry_bucket_source_quality_1`: `chosen_action` / `WAIT_REQUOTE` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_2`: `chosen_action` / `NO_BUY_AI` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_3`: `combo_entry_spot` / `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1400_close` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_4`: `exit_rule` / `exit_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_5`: `liquidity_bucket` / `liquidity_high` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_6`: `overbought_bucket` / `overbought_normal` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_7`: `overbought_bucket` / `overbought_watch` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_8`: `score_band` / `score_66_69` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_9`: `score_band` / `score_70p` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_10`: `score_band` / `score_60_62` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`

## Submit Bucket Attribution

- decision_authority: `adm_ldm_submit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'submit_rows': 136, 'bucket_count': 84, 'contract_gap_count': 0, 'workorder_count': 0, 'runtime_candidate_count': 0, 'quote_freshness_attribution_present': False, 'quote_freshness_resolution_counts': {'refresh_not_attempted_or_not_instrumented': 12, 'sim_submit_path_not_applicable': 124}, 'pre_submit_refresh_applied_counts': {'refresh_not_attempted_or_not_instrumented': 12, 'sim_submit_path_not_applicable': 124}, 'real_submitted_row_count': 8, 'missing_broker_order_key_count': 0, 'bot_history_broker_order_key_backfill_candidate_count': 0, 'bot_history_broker_order_key_backfill_full_coverage': False, 'bot_history_broker_order_key_exact_mapping_count': 0, 'bot_history_broker_order_key_exact_mapping_full_coverage': False, 'post_submit_provenance_join_resolution': 'no_gap_broker_order_key_present_or_no_missing_rows', 'bot_history_broker_order_key_backfill_candidates': [], 'missing_broker_order_key_rate': 0.0, 'post_submit_provenance_join_gap_raw': False, 'post_submit_provenance_join_gap': False}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 128 | 69 | -0.629 | `keep_collecting` |
| `actual_order_submitted` | `true` | 8 | 0 | None | `keep_collecting` |
| `broker_order_forbidden` | `true` | 128 | 69 | -0.629 | `keep_collecting` |
| `broker_order_forbidden` | `false` | 8 | 0 | None | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 47 | 25 | -0.1681 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 39 | 23 | -1.3429 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 10 | 3 | -1.6385 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 8 | 5 | -0.5028 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 4 | 3 | 1.3917 | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_lt1s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=caution|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 3 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 2 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 2 | 1 | -0.7527 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 2 | 2 | -0.5869 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 2 | 1 | 0.9695 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 2 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 2 | 2 | 1.1039 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 2 | 2 | -3.0055 | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=caution|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_lt1s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_ok|latency=danger|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_ok|latency=caution|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=pre_submit_liquidity_guard_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=latency_unknown|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=pre_submit_liquidity_guard_block|revalidation=ok_or_unflagged|quote_age=quote_age_lt1s|liquidity=below_min_liquidity|liquidity_guard=liquidity_guard_unknown|overbought=overbought_ok|latency=latency_unknown|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=pre_submit_liquidity_guard_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=below_min_liquidity|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=latency_unknown|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=pre_submit_overbought_pullback_guard_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=pullback_required|latency=latency_unknown|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | -2.2334 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_lt1s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | 1.9387 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=pullback_or_rebreak_not_confirmed|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_overbought_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=pullback_or_rebreak_not_confirmed|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `latency_reason` | `scalp_live_simulator` | 124 | 69 | -0.629 | `keep_collecting` |
| `latency_reason` | `caution_normal_entry_allowed` | 5 | 0 | None | `keep_collecting` |
| `latency_reason` | `latency_reason_unknown` | 4 | 0 | None | `source_quality_workorder` |
| `latency_reason` | `latency_quote_fresh_composite_normal_override` | 2 | 0 | None | `keep_collecting` |
| `latency_reason` | `latency_other_danger_relief_normal_override` | 1 | 0 | None | `keep_collecting` |
| `latency_state` | `simulated` | 124 | 69 | -0.629 | `keep_collecting` |
| `latency_state` | `caution` | 5 | 0 | None | `keep_collecting` |
| `latency_state` | `latency_unknown` | 4 | 0 | None | `source_quality_workorder` |
| `latency_state` | `danger` | 3 | 0 | None | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 71 | 37 | -0.4268 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 56 | 32 | -0.8627 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_not_available` | 9 | 0 | None | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 128, 'source_row_count': 128, 'bucket_count': 30, 'joined_sample': 345, 'source_quality_adjusted_ev_pct': -1.185, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 52 | 52 | -1.5598 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 4 | 4 | 2.6386 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 4 | 4 | 0.3133 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 3 | 3 | -1.8141 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 2 | 2 | -2.0681 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 2 | 2 | -1.501 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 1 | 1 | -0.49 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | 0.6096 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 50 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_020_180s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_180_600s` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_020_180s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_not_applicable_at_start` | 124 | 69 | -1.185 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_020_180s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 2 | 0 | None | `hold_sample` |
| `holding_action` | `WAIT` | 115 | 65 | -1.1481 | `candidate_tighten_or_exclude` |
| `holding_action` | `BUY` | 3 | 2 | -2.0681 | `hold_sample` |
| `holding_action` | `holding_action_not_applicable_at_start` | 6 | 2 | -1.501 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 4 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 124 | 69 | -1.185 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 4 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 59 | 56 | -1.5759 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 4 | 4 | 0.3133 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300_plus` | 4 | 4 | 2.6386 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg010_pos080` | 3 | 3 | -1.8141 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 2 | 1 | -0.49 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 1 | 1 | 0.6096 | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 55 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- `holding_bucket_source_quality_1`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_2`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_3`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_4`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_5`: `held_bucket` / `held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_6`: `holding_action` / `WAIT` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_7`: `holding_source_stage` / `scalp_sim_holding_started` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_8`: `profit_band` / `profit_lt_neg070` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_9`: `profit_band` / `profit_pos150_pos300` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_10`: `profit_band` / `profit_pos150_pos300_plus` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Exit Bucket Attribution

- decision_authority: `adm_ldm_exit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'exit_rows': 1657, 'source_row_count': 1657, 'bucket_count': 51, 'joined_sample': 810, 'source_quality_adjusted_ev_pct': -0.9513, 'source_quality_gate': 'pass', 'unknown_reason_counts': {'not_applicable': 2, 'join_gap': 8, 'missing_source_field': 1}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 70 | 70 | -1.1099 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 17 | 17 | -1.7744 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 15 | 15 | -0.5713 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 12 | 12 | -1.3046 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 10 | 10 | -0.6428 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 7 | 7 | -3.2862 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 4 | 4 | -1.7315 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 4 | 4 | -0.8844 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 3 | 3 | -0.7075 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 3 | 3 | 2.4305 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 2 | 2 | 0.355 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=daily_limit_up_immediate_exit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 2 | 2 | -2.1195 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 2 | 2 | 3.097 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 1 | 1 | -0.3675 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` | 1 | 1 | 0.85 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos150_pos300` | 1 | 1 | 1.97 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos150_pos300_plus` | 1 | 1 | 4.105 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=daily_limit_up_immediate_exit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 1 | 1 | -1.2035 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=daily_limit_up_immediate_exit|outcome=NEUTRAL|profit=profit_pos150_pos300` | 1 | 1 | -0.6637 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=daily_limit_up_immediate_exit|outcome=NEUTRAL|profit=profit_pos150_pos300_plus` | 1 | 1 | 3.8292 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_ai_momentum_decay|outcome=NEUTRAL|profit=profit_pos150_pos300` | 1 | 1 | 0.8299 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 1 | 1 | -0.4533 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 1 | 1 | 0.5311 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 1 | 1 | 0.6096 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_euphoria_context_noop|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown` | 112 | 0 | None | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown` | 1383 | 0 | None | `source_quality_workorder` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 90 | 90 | -0.8736 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 27 | 27 | -2.0109 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 27 | 27 | -0.3184 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 14 | 14 | -0.7212 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 1499 | 4 | -0.6225 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 90 | 90 | -0.8736 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 31 | 31 | -1.2945 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 23 | 23 | -1.9819 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 8 | 8 | 1.7716 | `candidate_recovery_or_relax` |
| `exit_rule` | `daily_limit_up_immediate_exit` | 5 | 5 | -0.4554 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 4 | 4 | -0.6225 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_ai_momentum_decay` | 1 | 1 | 0.8299 | `hold_sample` |
| `exit_rule` | `exit_rule_unknown` | 1495 | 0 | None | `source_quality_workorder` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 90 | 90 | -0.8736 | `candidate_tighten_or_exclude` |

### Exit Bucket Attribution Workorders

- `exit_bucket_source_quality_1`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_2`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_3`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_4`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_5`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_6`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_7`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_8`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_9`: `combo_exit_result` / `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_10`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `incremental_notional_ev_pct`
- summary: `{'scale_in_rows': 3600, 'bucket_count': 659, 'edge_bucket_count': 0, 'actionable_bucket_count': 0, 'runtime_authority_blocked_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'arm_counts': {'PYRAMID': 772, 'AVG_DOWN': 2828}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_70p` | 1620 | 1620 | None | -0.3374 | 0.2278 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 927 | 927 | None | -0.599 | 0.1478 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 541 | 541 | None | -0.6659 | 0.1257 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 218 | 218 | None | -0.8458 | 0.0872 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 209 | 209 | None | -0.7033 | 0.1627 | `hold_sample` |
| `ai_score_band` | `score_unknown` | 85 | 1 | None | 7.86 | 1.0 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 3515 | 3515 | None | -0.5102 | 0.1784 | `hold_sample` |
| `ai_score_source` | `sim_scale_in_source_not_scored` | 1 | 1 | None | 7.86 | 1.0 | `hold_sample` |
| `ai_score_source` | `stage_rule_backfilled` | 84 | 0 | None | None | None | `hold_sample` |
| `arm` | `AVG_DOWN` | 2828 | 2803 | None | -0.8069 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 772 | 713 | None | 0.6678 | 0.8808 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 1954 | 1929 | None | -0.9911 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 874 | 874 | None | -0.4004 | 0.0 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 772 | 713 | None | 0.6678 | 0.8808 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 578 | 578 | None | 0.394 | 0.9014 | `hold_sample` |
| `blocker_reason` | `add_judgment_locked` | 272 | 272 | None | -0.3532 | 0.0478 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.07)` | 244 | 244 | None | -1.07 | 0.0 | `hold_sample` |
| `blocker_reason` | `low_broken` | 108 | 108 | None | -0.472 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 93 | 93 | None | -0.93 | 0.0323 | `hold_sample` |
| `blocker_reason` | `scalping_pyramid_ok` | 61 | 61 | None | 2.9005 | 1.0 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `adm_ldm_overnight_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'overnight_rows': 8, 'bucket_count': 19, 'actionable_bucket_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'status_counts': {'HOLD_OVERNIGHT': 4, 'SELL_TODAY': 4}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 3 | 3 | -0.7075 | -0.9433 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 1 | 1 | -0.3675 | -0.49 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_lt_neg070` | 3 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 1 | 0 | None | None | None | `hold_sample` |
| `confidence_band` | `confidence_070p` | 8 | 4 | -0.6225 | -0.83 | 0.0 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 4 | 2 | -0.5325 | -0.71 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 4 | 2 | -0.7125 | -0.95 | 0.0 | `hold_sample` |
| `overnight_action` | `SELL_TODAY` | 8 | 4 | -0.6225 | -0.83 | 0.0 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 4 | 4 | -0.6225 | -0.83 | 0.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 4 | 0 | None | None | None | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 8 | 4 | -0.6225 | -0.83 | 0.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 8 | 4 | -0.6225 | -0.83 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 6 | 3 | -0.7075 | -0.9433 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 2 | 1 | -0.3675 | -0.49 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 8 | 4 | -0.6225 | -0.83 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 4 | 4 | -0.6225 | -0.83 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_decision` | 4 | 0 | None | None | None | `hold_sample` |
| `stage` | `exit` | 4 | 4 | -0.6225 | -0.83 | 0.0 | `hold_sample` |
| `stage` | `holding` | 4 | 0 | None | None | None | `hold_sample` |

### Overnight Bucket Runtime Approval Candidates

- none

### Overnight Bucket Workorders

- none

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
