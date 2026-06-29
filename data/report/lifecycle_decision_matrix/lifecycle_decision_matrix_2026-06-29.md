# Lifecycle Decision Matrix - 2026-06-29

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-29`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `7792`
- source_rows_total: `10145`
- retained_rows: `7792`
- dropped_rows_by_source: `{'dedupe': 2353}`
- joined_rows: `4065`
- policy_pass_count: `5`
- promote_ready_count: `1`
- entry_bucket_actionable_count: `16`
- entry_bucket_runtime_candidate_count: `10`
- holding_bucket_count/workorders: `27` / `7`
- exit_bucket_count/workorders: `47` / `10`
- scale_in_bucket_actionable_count: `0`
- scale_in_bucket_runtime_candidate_count: `0`
- overnight_bucket_actionable_count: `0`
- overnight_bucket_runtime_candidate_count: `0`
- lifecycle_flow_bucket_count: `71`
- lifecycle_flow_complete_count: `19`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `0` / `19` / `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0027`
- incomplete_flow_reason_counts: `{'missing_exit': 4163, 'missing_submit': 7093, 'missing_holding': 7100, 'candidate_id_only': 6891, 'missing_entry': 6825, 'sim_record_id_only': 24, 'scale_in_noise_only': 3875, 'postclose_exit_without_entry': 2950}`
- bucket_directed_sim_probe: `{'observed_row_count': 3097, 'matched_row_count': 0, 'background_row_count': 3097, 'matched_unique_source_bucket_count': 0, 'match_status_counts': {'not_instrumented': 2957, 'policy_missing': 140}, 'matched_classification_state_counts': {}, 'primary_source': 'matched_bucket_directed_sim_probe_only', 'background_source': 'unmatched_or_policy_missing_sim_observation', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 1, 'route_counts': {'bounded_auxiliary_weight': 1, 'hold_sample': 4}, 'quality_counts': {'observational_only_pending_outcome': 1, 'hold_sample': 4}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 800 | 87 | 0.8412 | 0.9461 | `pass` | `BUY_DEFENSIVE` | True |
| `submit` | 63 | 32 | 0.1573 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 53 | 32 | -0.238 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 3896 | 3863 | -0.9426 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 2980 | 51 | -0.4904 | 0.0873 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 7132, 'complete_flow_count': 19, 'direct_sim_record_complete_flow_count': 0, 'adm_bridge_complete_flow_count': 19, 'fallback_complete_flow_count': 0, 'direct_flow_zero_diagnostic': {'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'direct_sim_record_flow_count': 24, 'direct_sim_record_incomplete_flow_count': 24, 'direct_sim_record_stage_coverage_counts': {'exit': 21, 'holding': 4}, 'direct_sim_record_incomplete_reason_counts': {'missing_entry': 24, 'missing_submit': 24, 'missing_holding': 20, 'missing_exit': 3, 'sim_record_id_only': 24, 'scale_in_noise_only': 3, 'postclose_exit_without_entry': 21}, 'runtime_effect': False, 'decision_authority': 'ldm_direct_flow_diagnostic_only'}, 'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'incomplete_flow_count': 7113, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 7792, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0027, 'complete_flow_conversion_denominator': 2969, 'complete_flow_conversion_rate': 0.0064, 'active_priority_incomplete_seed_count': 288, 'scale_in_followup_event_count': 3896, 'scale_in_unique_flow_count': 3223, 'scale_in_noise_flow_count': 3875, 'denominator_exclusion_counts': {'scale_in_noise_flow_excluded': 3875, 'active_priority_incomplete_seed_excluded': 288}, 'conversion_blocker_reason_counts': {'missing_entry': 2950, 'missing_submit': 2950, 'missing_holding': 2946, 'sim_record_id_only': 21, 'postclose_exit_without_entry': 2950, 'candidate_id_only': 2929}, 'observation_seed_reason_counts': {'missing_exit': 4163, 'missing_submit': 4143, 'missing_holding': 4154, 'candidate_id_only': 3962, 'missing_entry': 3875, 'sim_record_id_only': 3, 'scale_in_noise_only': 3875}, 'join_contract_blocked': False, 'bundle_ev_tuning_state': 'ready_for_bundle_ev_tuning', 'top_incomplete_reason': 'missing_holding', 'stage_identity': {'entry': {'source_row_count': 800, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 710, 'candidate_id': 90}, 'identity_join_rate': 1.0}, 'submit': {'source_row_count': 63, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 63}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 53, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 49, 'exact_sim_record_id': 4}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 3896, 'identity_missing_count': 0, 'identity_quality_counts': {'exact_sim_record_id': 24, 'candidate_id': 3872}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 2980, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 27, 'exact_sim_record_id': 24, 'candidate_id': 2929}, 'identity_join_rate': 1.0}}, 'required_stage_source_counts': {'entry': 800, 'submit': 63, 'holding': 53, 'exit': 2980}, 'incomplete_flow_reason_counts': {'missing_exit': 4163, 'missing_submit': 7093, 'missing_holding': 7100, 'candidate_id_only': 6891, 'missing_entry': 6825, 'sim_record_id_only': 24, 'scale_in_noise_only': 3875, 'postclose_exit_without_entry': 2950}, 'bucket_count': 71, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:65ec45aaab` | 1 | 1 | -1.6151 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:a5aac23c60` | 1 | 1 | -0.115 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:f7df4238eb` | 1 | 1 | 0.4396 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9ab6415792` | 1 | 1 | 1.113 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:d21da7ef52` | 1 | 1 | 0.25 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:119abec365` | 1 | 1 | 1.3996 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:ec55547898` | 1 | 1 | 1.8578 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:df6c99e573` | 1 | 1 | 0.1059 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_sc:9d376f2701` | 1 | 1 | 0.7507 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:4df7d22a1f` | 1 | 1 | 0.8294 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:8d05153b8b` | 1 | 1 | -0.754 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:b82e6a20cb` | 1 | 1 | -2.8338 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:6a1637e34a` | 1 | 1 | 0.5612 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:bcfffe7083` | 1 | 1 | 2.0684 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:b1ff7e4553` | 1 | 1 | -3.3141 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:2089125172` | 1 | 1 | -1.4344 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:fd59fc5941` | 1 | 1 | 0.8118 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:e5de472b13` | 1 | 1 | 4.059 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:ddafca51c9` | 1 | 1 | -2.2449 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 3530 | 3508 | -1.0995 | `hold_sample` | `join_contract_blocked` |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 800, 'bucket_count': 225, 'actionable_bucket_count': 16, 'source_quality_blocked_bucket_count': 0, 'runtime_candidate_count': 10, 'workorder_count': 10}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `WAIT_REQUOTE` | 72 | 72 | 0.9546 | 1.6528 | 0.5139 | `candidate_recovery_or_relax` |
| `chosen_action` | `NO_BUY_AI` | 671 | 15 | 0.2967 | -0.0667 | 0.5333 | `hold_no_edge` |
| `chosen_action` | `ALLOW_LEVEL1_RISK_OFF_ENTRY` | 18 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `BUY_NOW` | 38 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_SOURCE_QUALITY` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 15 | 15 | 0.8177 | 1.3777 | 0.4 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 10 | 10 | 0.9273 | 1.1505 | 0.8 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 7 | 7 | 2.0312 | 3.0314 | 0.5714 | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 6 | 6 | 0.1652 | 0.3266 | 0.5 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 6 | 6 | 0.1611 | 0.0108 | 0.5 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_ok|time=time_1200_1400` | 5 | 5 | 1.3439 | 2.8708 | 0.6 | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 4 | 4 | 1.3948 | 2.3204 | 0.25 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1400_close` | 4 | 4 | 3.3799 | 5.3973 | 0.75 | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_ok|time=time_1200_1400` | 3 | 3 | 0.3124 | 1.4046 | 0.3333 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 3 | 3 | -0.4249 | -0.9147 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 31 | 2 | -0.713 | 2.46 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 32 | 2 | -0.1232 | 2.16 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 2 | 2 | 1.1307 | 1.3538 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_chase_risk|time=time_1400_close` | 4 | 1 | 0.0 | -0.23 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 13 | 1 | -0.5173 | 2.25 | 1.0 | `hold_sample` |
| `exit_rule` | `exit_unknown` | 785 | 72 | 0.9546 | 1.6528 | 0.5139 | `candidate_recovery_or_relax` |
| `liquidity_bucket` | `liquidity_high` | 698 | 87 | 0.8412 | 1.3563 | 0.5172 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 543 | 61 | 0.9568 | 1.4079 | 0.5574 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_ok` | 79 | 13 | 1.4844 | 3.4506 | 0.5385 | `candidate_recovery_or_relax` |

### Entry Bucket Runtime Approval Candidates

- `entry_bucket_5`: `liquidity_bucket` / `liquidity_high` -> `candidate_recovery_or_relax`
- `entry_bucket_6`: `overbought_bucket` / `overbought_normal` -> `candidate_recovery_or_relax`
- `entry_bucket_8`: `score_band` / `score_70p` -> `candidate_recovery_or_relax`
- `entry_bucket_9`: `score_band` / `score_66_69` -> `candidate_recovery_or_relax`
- `entry_bucket_10`: `source_stage` / `wait6579_ev_cohort` -> `candidate_recovery_or_relax`
- `entry_bucket_11`: `stale_bucket` / `fresh_or_unflagged` -> `candidate_recovery_or_relax`
- `entry_bucket_12`: `strength_bucket` / `strong_strength_momentum` -> `candidate_recovery_or_relax`
- `entry_bucket_13`: `time_bucket` / `time_0900_1000` -> `candidate_recovery_or_relax`
- `entry_bucket_14`: `time_bucket` / `time_1000_1200` -> `candidate_recovery_or_relax`
- `entry_bucket_15`: `time_bucket` / `time_1200_1400` -> `candidate_recovery_or_relax`

### Entry Bucket Workorders

- `entry_bucket_source_quality_1`: `chosen_action` / `WAIT_REQUOTE` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_2`: `combo_entry_spot` / `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_3`: `combo_entry_spot` / `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_4`: `exit_rule` / `exit_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_5`: `liquidity_bucket` / `liquidity_high` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_6`: `overbought_bucket` / `overbought_normal` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_7`: `overbought_bucket` / `overbought_ok` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_8`: `score_band` / `score_70p` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_9`: `score_band` / `score_66_69` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_10`: `source_stage` / `wait6579_ev_cohort` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`

## Submit Bucket Attribution

- decision_authority: `adm_ldm_submit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'submit_rows': 63, 'bucket_count': 73, 'contract_gap_count': 0, 'workorder_count': 0, 'runtime_candidate_count': 0, 'quote_freshness_attribution_present': True, 'row_quote_freshness_attribution_present': False, 'sentinel_quote_freshness_attribution_present': True, 'sentinel_quote_freshness_attribution': {'source_report_type': 'buy_funnel_sentinel', 'decision_authority': 'submit_drought_quote_freshness_attribution_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'forbidden_uses': ['broker_order_submit', 'adm_ldm_training_input', 'general_threshold_ev_input', 'live_auto_promotion'], 'refresh_attempted_count': 31, 'refresh_applied_count': 23, 'still_latency_blocked_after_refresh_count': 8, 'latency_pass_recovered_count': 10, 'order_bundle_submitted_after_refresh_count': 1, 'refresh_subreason_counts': {'observer_quote_refresh_failed_invalid': 1, 'observer_quote_refresh_failed_stale': 6, 'ws_snapshot_refresh_failed_invalid': 1, 'ws_snapshot_refresh_failed_stale': 4, 'ws_snapshot_refresh_failed_missing': 2}, 'refresh_block_subreason_counts': {'observer_quote_refresh_failed_invalid': 1, 'observer_quote_refresh_failed_stale': 6, 'ws_snapshot_refresh_failed_invalid': 1, 'ws_snapshot_refresh_failed_stale': 4, 'ws_snapshot_refresh_failed_missing': 2}, 'latency_pass_recovered_downstream_counts': {'armed_expired_before_submit': 3, 'budget_pass_no_submit_event': 1, 'no_downstream_event': 1, 'order_bundle_submitted': 1, 'other:first_ai_wait': 1, 'upstream_block_after_latency_recovery': 3}, 'post_restart_window_policy': 'event_provenance_only'}, 'quote_freshness_resolution_counts': {'refresh_not_attempted_or_not_instrumented': 14, 'sim_submit_path_not_applicable': 49}, 'pre_submit_refresh_applied_counts': {'refresh_not_attempted_or_not_instrumented': 14, 'sim_submit_path_not_applicable': 49}, 'real_submitted_row_count': 2, 'missing_broker_order_key_count': 0, 'bot_history_broker_order_key_backfill_candidate_count': 0, 'bot_history_broker_order_key_backfill_full_coverage': False, 'bot_history_broker_order_key_exact_mapping_count': 0, 'bot_history_broker_order_key_exact_mapping_full_coverage': False, 'post_submit_provenance_join_resolution': 'no_gap_broker_order_key_present_or_no_missing_rows', 'bot_history_broker_order_key_backfill_candidates': [], 'missing_broker_order_key_rate': 0.0, 'post_submit_provenance_join_gap_raw': False, 'post_submit_provenance_join_gap': False}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 61 | 32 | 0.1573 | `keep_collecting` |
| `actual_order_submitted` | `true` | 2 | 0 | None | `keep_collecting` |
| `broker_order_forbidden` | `true` | 61 | 32 | 0.1573 | `keep_collecting` |
| `broker_order_forbidden` | `false` | 2 | 0 | None | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 18 | 10 | -0.3415 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 11 | 7 | 0.8833 | `source_quality_workorder` |
| `combo_submit_quality` | `source=entry_submit_revalidation_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=latency_unknown|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=false` | 8 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 6 | 6 | 0.0094 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 5 | 4 | 0.0 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 3 | 1 | 1.17 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 3 | 1 | 1.8266 | `source_quality_workorder` |
| `combo_submit_quality` | `source=entry_submit_revalidation_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_lt1s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=latency_unknown|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=false` | 2 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_ok|latency=caution|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_lt1s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_ok|latency=danger|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=pre_submit_liquidity_guard_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=latency_unknown|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=pre_submit_liquidity_guard_block|revalidation=ok_or_unflagged|quote_age=quote_age_lt1s|liquidity=below_min_liquidity|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=latency_unknown|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 1 | 1 | 0.0 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | -0.4875 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | -0.2999 | `source_quality_workorder` |
| `latency_reason` | `scalp_live_simulator` | 49 | 32 | 0.1573 | `keep_collecting` |
| `latency_reason` | `latency_reason_unknown` | 12 | 0 | None | `source_quality_workorder` |
| `latency_reason` | `caution_normal_entry_allowed` | 1 | 0 | None | `keep_collecting` |
| `latency_reason` | `latency_quote_fresh_composite_normal_override` | 1 | 0 | None | `keep_collecting` |
| `latency_state` | `simulated` | 49 | 32 | 0.1573 | `keep_collecting` |
| `latency_state` | `latency_unknown` | 12 | 0 | None | `source_quality_workorder` |
| `latency_state` | `caution` | 1 | 0 | None | `keep_collecting` |
| `latency_state` | `danger` | 1 | 0 | None | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 36 | 23 | 0.0991 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 15 | 9 | 0.3059 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_not_available` | 12 | 0 | None | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 36 | 23 | 0.0991 | `keep_collecting` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 14 | 0 | None | `source_quality_workorder` |
| `liquidity_guard_action` | `would_block` | 13 | 9 | 0.3059 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 48 | 29 | 0.2007 | `keep_collecting` |
| `overbought_bucket` | `overbought_not_available` | 12 | 0 | None | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 3 | 3 | -0.2625 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 49 | 32 | 0.1573 | `keep_collecting` |
| `overbought_guard_action` | `overbought_guard_unknown` | 14 | 0 | None | `source_quality_workorder` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 49 | 32 | 0.1573 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `refresh_age_not_instrumented` | 14 | 0 | None | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 53, 'source_row_count': 53, 'bucket_count': 27, 'joined_sample': 160, 'source_quality_adjusted_ev_pct': -0.238, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 7, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 9 | 9 | -2.0492 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 9 | 9 | -0.2156 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 6 | 6 | 0.5378 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 3 | 3 | 1.2799 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 2 | 2 | 2.586 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1 | 1 | -1.79 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 0.25 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 2.0684 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 17 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos080_pos150|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_not_applicable_at_start` | 49 | 32 | -0.238 | `hold_no_edge` |
| `held_bucket` | `held_600_1800s_plus` | 4 | 0 | None | `hold_sample` |
| `holding_action` | `WAIT` | 47 | 30 | -0.2632 | `hold_no_edge` |
| `holding_action` | `BUY` | 1 | 1 | -1.79 | `hold_sample` |
| `holding_action` | `holding_action_not_applicable_at_start` | 1 | 1 | 2.0684 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 4 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 49 | 32 | -0.238 | `hold_no_edge` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 4 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 11 | 10 | -2.0233 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 11 | 9 | -0.2156 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 6 | 6 | 0.5378 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos080_pos150` | 4 | 3 | 1.2799 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300_plus` | 3 | 3 | 2.4135 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg010_pos080` | 1 | 1 | 0.25 | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 17 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- `holding_bucket_source_quality_1`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_2`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_3`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_4`: `profit_band` / `profit_lt_neg070` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_5`: `profit_band` / `profit_pos150_pos300` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_6`: `profit_band` / `profit_pos080_pos150` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_7`: `profit_band` / `profit_pos150_pos300_plus` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Exit Bucket Attribution

- decision_authority: `adm_ldm_exit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'exit_rows': 2980, 'source_row_count': 2980, 'bucket_count': 47, 'joined_sample': 255, 'source_quality_adjusted_ev_pct': -0.4904, 'source_quality_gate': 'pass', 'unknown_reason_counts': {'not_applicable': 3, 'join_gap': 8, 'missing_source_field': 1}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 13 | 13 | -1.31 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=daily_limit_up_immediate_exit|outcome=NEUTRAL|profit=profit_neg070_neg010` | 6 | 6 | -0.1683 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 5 | 5 | -0.584 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 3 | 3 | 0.6732 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 2 | 2 | -0.2287 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` | 2 | 2 | 0.965 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 2 | 2 | -3.4997 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 2 | 2 | -2.6791 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 2 | 2 | -0.3955 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 2 | 2 | -1.5248 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 2 | 2 | 1.5907 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300` | 2 | 2 | 0.9804 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 1 | 1 | -1.3425 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos080_pos150` | 1 | 1 | 0.8775 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=daily_limit_up_immediate_exit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 1 | 1 | 0.25 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=daily_limit_up_immediate_exit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 1 | 1 | 0.8118 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_ai_momentum_decay|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 1 | 1 | -0.754 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | -2.2449 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 1 | 1 | 1.8578 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 1 | 1 | 4.059 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_euphoria_context_noop|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown` | 32 | 0 | None | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown` | 2897 | 0 | None | `source_quality_workorder` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 20 | 20 | -0.901 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 12 | 12 | -0.0864 | `hold_no_edge` |
| `exit_outcome` | `GOOD_EXIT` | 10 | 10 | -0.791 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 5 | 5 | 0.5762 | `candidate_recovery_or_relax` |
| `exit_outcome` | `outcome_unknown` | 2933 | 4 | -0.2306 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 20 | 20 | -0.901 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 9 | 9 | 1.4532 | `candidate_recovery_or_relax` |
| `exit_rule` | `daily_limit_up_immediate_exit` | 8 | 8 | 0.0065 | `hold_no_edge` |
| `exit_rule` | `scalp_soft_stop_pct` | 6 | 6 | -1.5331 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 4 | 4 | -0.2306 | `hold_no_edge` |
| `exit_rule` | `scalp_hard_stop_pct` | 3 | 3 | -3.0814 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_ai_momentum_decay` | 1 | 1 | -0.754 | `hold_sample` |
| `exit_rule` | `exit_rule_unknown` | 2929 | 0 | None | `source_quality_workorder` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 27 | 27 | -0.2247 | `hold_no_edge` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 20 | 20 | -0.901 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 4 | 4 | -0.2306 | `hold_no_edge` |
| `exit_source_stage` | `scalp_sim_euphoria_context_noop` | 32 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 2897 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- `exit_bucket_source_quality_1`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_2`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_3`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_4`: `combo_exit_result` / `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_5`: `combo_exit_result` / `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_6`: `combo_exit_result` / `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos080_pos150` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_7`: `combo_exit_result` / `source=scalp_sim_euphoria_context_noop|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_8`: `combo_exit_result` / `source=scalp_sim_panic_context_warning|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_9`: `exit_outcome` / `outcome_not_applicable_partial_exit` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_10`: `exit_outcome` / `GOOD_EXIT` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `incremental_notional_ev_pct`
- summary: `{'scale_in_rows': 3896, 'bucket_count': 230, 'edge_bucket_count': 0, 'actionable_bucket_count': 0, 'runtime_authority_blocked_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'arm_counts': {'PYRAMID': 349, 'AVG_DOWN': 3547}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_70p` | 2234 | 2234 | None | -1.0131 | 0.0971 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 1086 | 1086 | None | -0.9894 | 0.0635 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 222 | 222 | None | -0.7786 | 0.1171 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 175 | 175 | None | -0.9803 | 0.0571 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 144 | 144 | None | -0.9277 | 0.0972 | `hold_sample` |
| `ai_score_band` | `score_unknown` | 35 | 2 | None | None | None | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 3861 | 3861 | None | -0.9883 | 0.087 | `hold_sample` |
| `ai_score_source` | `sim_scale_in_source_not_scored` | 2 | 2 | None | None | None | `hold_sample` |
| `ai_score_source` | `stage_rule_backfilled` | 33 | 0 | None | None | None | `hold_sample` |
| `arm` | `AVG_DOWN` | 3547 | 3525 | None | -1.1472 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 349 | 338 | None | 0.6792 | 1.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 3521 | 3499 | None | -1.1304 | 0.0 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 349 | 338 | None | 0.6792 | 1.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 26 | 26 | None | -3.4162 | 0.0 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 313 | 313 | None | 0.6421 | 1.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.46)` | 186 | 186 | None | -1.46 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.89)` | 177 | 177 | None | -0.89 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.68)` | 163 | 163 | None | -1.68 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.81)` | 138 | 138 | None | -0.81 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.79)` | 113 | 113 | None | -1.79 | 0.0 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `adm_ldm_overnight_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'overnight_rows': 8, 'bucket_count': 23, 'actionable_bucket_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'status_counts': {'HOLD_OVERNIGHT': 4, 'SELL_TODAY': 4}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 2 | 2 | -0.2287 | -0.305 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 1 | 1 | -1.3425 | -1.79 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 1 | 1 | 0.8775 | 1.17 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_lt_neg070` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_pos080_pos150` | 1 | 0 | None | None | None | `hold_sample` |
| `confidence_band` | `confidence_070p` | 8 | 4 | -0.2306 | -0.3075 | 0.25 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 8 | 4 | -0.2306 | -0.3075 | 0.25 | `hold_sample` |
| `overnight_action` | `SELL_TODAY` | 8 | 4 | -0.2306 | -0.3075 | 0.25 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 4 | 4 | -0.2306 | -0.3075 | 0.25 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 4 | 0 | None | None | None | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 6 | 3 | -0.6 | -0.8 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 2 | 1 | 0.8775 | 1.17 | 1.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 6 | 3 | -0.25 | -0.3333 | 0.3333 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 4 | 2 | -0.2287 | -0.305 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 2 | 1 | -1.3425 | -1.79 | 0.0 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 2 | 1 | 0.8775 | 1.17 | 1.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 8 | 4 | -0.2306 | -0.3075 | 0.25 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 4 | 4 | -0.2306 | -0.3075 | 0.25 | `hold_sample` |

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
