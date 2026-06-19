# Lifecycle Decision Matrix - 2026-06-19

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-19`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `3115`
- source_rows_total: `4095`
- retained_rows: `3115`
- dropped_rows_by_source: `{'dedupe': 980}`
- joined_rows: `2116`
- policy_pass_count: `5`
- promote_ready_count: `1`
- entry_bucket_actionable_count: `20`
- entry_bucket_runtime_candidate_count: `10`
- holding_bucket_count/workorders: `32` / `10`
- exit_bucket_count/workorders: `46` / `10`
- scale_in_bucket_actionable_count: `0`
- scale_in_bucket_runtime_candidate_count: `0`
- overnight_bucket_actionable_count: `11`
- overnight_bucket_runtime_candidate_count: `9`
- lifecycle_flow_bucket_count: `113`
- lifecycle_flow_complete_count: `57`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `0` / `57` / `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0251`
- incomplete_flow_reason_counts: `{'missing_entry': 1974, 'missing_holding': 2166, 'missing_exit': 1939, 'missing_submit': 2166, 'postclose_exit_without_entry': 273, 'candidate_id_only': 1978, 'scale_in_noise_only': 1681, 'sim_record_id_only': 101}`
- bucket_directed_sim_probe: `{'observed_row_count': 698, 'matched_row_count': 64, 'background_row_count': 634, 'matched_unique_source_bucket_count': 2, 'match_status_counts': {'matched': 64, 'no_match': 329, 'not_instrumented': 305}, 'matched_classification_state_counts': {'lifecycle_flow_sim_probe_candidate': 64}, 'primary_source': 'matched_bucket_directed_sim_probe_only', 'background_source': 'unmatched_or_policy_missing_sim_observation', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 1, 'route_counts': {'bounded_auxiliary_weight': 1, 'hold_sample': 4}, 'quality_counts': {'observational_only_pending_outcome': 1, 'hold_sample': 4}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 763 | 82 | 1.062 | 0.8813 | `pass` | `BUY_DEFENSIVE` | True |
| `submit` | 131 | 86 | 0.2986 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 130 | 86 | -0.7244 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 1739 | 1720 | -0.4709 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 352 | 142 | -0.7578 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 2269, 'complete_flow_count': 57, 'direct_sim_record_complete_flow_count': 0, 'adm_bridge_complete_flow_count': 57, 'fallback_complete_flow_count': 0, 'direct_flow_zero_diagnostic': {'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'direct_sim_record_flow_count': 101, 'direct_sim_record_incomplete_flow_count': 101, 'direct_sim_record_stage_coverage_counts': {'holding': 20, 'exit': 62}, 'direct_sim_record_incomplete_reason_counts': {'missing_entry': 101, 'missing_submit': 101, 'sim_record_id_only': 101, 'postclose_exit_without_entry': 62, 'missing_holding': 81, 'missing_exit': 39, 'scale_in_noise_only': 39}, 'runtime_effect': False, 'decision_authority': 'ldm_direct_flow_diagnostic_only'}, 'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'incomplete_flow_count': 2212, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 3115, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0251, 'complete_flow_conversion_denominator': 350, 'complete_flow_conversion_rate': 0.1629, 'active_priority_incomplete_seed_count': 238, 'scale_in_followup_event_count': 1739, 'scale_in_unique_flow_count': 1722, 'scale_in_noise_flow_count': 1681, 'denominator_exclusion_counts': {'scale_in_noise_flow_excluded': 1681, 'active_priority_incomplete_seed_excluded': 238}, 'conversion_blocker_reason_counts': {'missing_entry': 293, 'missing_holding': 272, 'missing_exit': 20, 'postclose_exit_without_entry': 273, 'missing_submit': 272, 'sim_record_id_only': 62, 'candidate_id_only': 210}, 'observation_seed_reason_counts': {'missing_exit': 1919, 'missing_submit': 1894, 'missing_holding': 1894, 'candidate_id_only': 1768, 'missing_entry': 1681, 'scale_in_noise_only': 1681, 'sim_record_id_only': 39}, 'join_contract_blocked': False, 'bundle_ev_tuning_state': 'ready_for_bundle_ev_tuning', 'top_incomplete_reason': 'missing_submit', 'stage_identity': {'entry': {'source_row_count': 763, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 637, 'candidate_id': 126}, 'identity_join_rate': 1.0}, 'submit': {'source_row_count': 131, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 131}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 130, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 110, 'exact_sim_record_id': 20}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 1739, 'identity_missing_count': 0, 'identity_quality_counts': {'candidate_id': 1642, 'exact_sim_record_id': 97}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 352, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 67, 'exact_sim_record_id': 75, 'candidate_id': 210}, 'identity_join_rate': 1.0}}, 'required_stage_source_counts': {'entry': 763, 'submit': 131, 'holding': 130, 'exit': 352}, 'incomplete_flow_reason_counts': {'missing_entry': 1974, 'missing_holding': 2166, 'missing_exit': 1939, 'missing_submit': 2166, 'postclose_exit_without_entry': 273, 'candidate_id_only': 1978, 'scale_in_noise_only': 1681, 'sim_record_id_only': 101}, 'bucket_count': 113, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:23495871ee` | 3 | 3 | -1.9545 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:2b39f2b635` | 3 | 3 | -1.2435 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:02eec4d554` | 2 | 2 | -1.8412 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:3cbb81cd02` | 2 | 2 | 0.0453 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:f7df4238eb` | 2 | 2 | 0.889 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:4ff19246fa` | 2 | 2 | -2.1966 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:be3bcb1776` | 2 | 2 | -1.5908 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:8adb1bf0c3` | 1 | 1 | -3.0672 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:5557fe98a5` | 1 | 1 | -0.93 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:ae8509fc72` | 1 | 1 | -1.6583 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:c982e1d321` | 1 | 1 | -2.1528 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:9c03f3dde5` | 1 | 1 | -1.245 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:f1c1fcc930` | 1 | 1 | -0.7621 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:84b7dde4a3` | 1 | 1 | -1.0997 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:92c2eeaf3e` | 1 | 1 | 0.3386 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:da3af63f79` | 1 | 1 | -1.6601 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:bf337f9918` | 1 | 1 | -2.3489 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:cd8682b0ec` | 1 | 1 | -0.7129 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:8050d08a3f` | 1 | 1 | -1.3355 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9d8cac316e` | 1 | 1 | 0.033 | `hold_no_edge` | `pass` |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 763, 'bucket_count': 191, 'actionable_bucket_count': 20, 'source_quality_blocked_bucket_count': 0, 'runtime_candidate_count': 10, 'workorder_count': 10}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `WAIT_REQUOTE` | 50 | 50 | 1.4993 | 2.342 | 0.52 | `candidate_recovery_or_relax` |
| `chosen_action` | `NO_BUY_AI` | 611 | 29 | 0.3999 | -1.97 | 0.1379 | `candidate_recovery_or_relax` |
| `chosen_action` | `BUY_NOW` | 24 | 3 | 0.1743 | -2.46 | 0.0 | `hold_sample` |
| `chosen_action` | `ALLOW_BOTTOMING_ENTRY` | 8 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `ALLOW_LEVEL1_RISK_OFF_ENTRY` | 68 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_SOURCE_QUALITY` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 15 | 15 | 0.7851 | 0.7647 | 0.5333 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 13 | 13 | 0.4515 | 0.3458 | 0.3846 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 57 | 12 | 0.611 | -1.7525 | 0.25 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 7 | 7 | 0.547 | 0.4765 | 0.4286 | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 5 | 5 | 1.137 | 1.5239 | 0.4 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 15 | 5 | -0.0547 | -2.486 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 34 | 3 | 0.6201 | -0.9133 | 0.3333 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 64 | 3 | 0.0918 | -2.17 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 93 | 2 | -0.4544 | -2.275 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 15 | 2 | 0.1534 | -2.625 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_ok|time=time_0900_1000` | 2 | 2 | 16.629 | 30.4238 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 2 | 2 | 0.2601 | -0.0064 | 0.5 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 2 | 1 | 1.4647 | -2.85 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_1400_close` | 35 | 1 | 1.4048 | -2.74 | 0.0 | `hold_sample` |
| `exit_rule` | `exit_unknown` | 731 | 50 | 1.4993 | 2.342 | 0.52 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_hard_stop_pct` | 15 | 15 | 0.745 | -3.1493 | 0.0 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_soft_stop_pct` | 13 | 13 | 0.2156 | -2.0623 | 0.0 | `hold_no_edge` |
| `liquidity_bucket` | `liquidity_high` | 632 | 82 | 1.062 | 0.6413 | 0.3659 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 585 | 74 | 0.5568 | -0.4891 | 0.3243 | `candidate_recovery_or_relax` |
| `score_band` | `score_70p` | 111 | 41 | 1.4425 | 1.7562 | 0.439 | `candidate_recovery_or_relax` |
| `score_band` | `score_60_62` | 476 | 22 | 0.5195 | -1.8373 | 0.1818 | `candidate_recovery_or_relax` |
| `score_band` | `score_66_69` | 35 | 15 | 0.3549 | 0.2892 | 0.3333 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 50 | 50 | 1.4993 | 2.342 | 0.52 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 468 | 32 | 0.3787 | -2.0159 | 0.125 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh_or_unflagged` | 126 | 50 | 1.4993 | 2.342 | 0.52 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh` | 195 | 20 | 0.482 | -2.0285 | 0.15 | `candidate_recovery_or_relax` |
| `stale_bucket` | `stale_high` | 399 | 12 | 0.2065 | -1.995 | 0.0833 | `hold_no_edge` |
| `strength_bucket` | `strong_strength_momentum` | 119 | 46 | 1.1947 | 1.4083 | 0.413 | `candidate_recovery_or_relax` |
| `strength_bucket` | `weak_strength_momentum` | 511 | 33 | 1.0139 | -0.3285 | 0.303 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_0900_1000` | 308 | 52 | 1.2647 | 0.9931 | 0.4038 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_1000_1200` | 231 | 24 | 0.7206 | 0.5349 | 0.3333 | `candidate_recovery_or_relax` |

### Entry Bucket Runtime Approval Candidates

- `entry_bucket_8`: `liquidity_bucket` / `liquidity_high` -> `candidate_recovery_or_relax`
- `entry_bucket_9`: `overbought_bucket` / `overbought_normal` -> `candidate_recovery_or_relax`
- `entry_bucket_10`: `score_band` / `score_70p` -> `candidate_recovery_or_relax`
- `entry_bucket_11`: `score_band` / `score_60_62` -> `candidate_recovery_or_relax`
- `entry_bucket_13`: `source_stage` / `wait6579_ev_cohort` -> `candidate_recovery_or_relax`
- `entry_bucket_14`: `source_stage` / `scalp_entry_action_decision_snapshot` -> `candidate_recovery_or_relax`
- `entry_bucket_15`: `stale_bucket` / `fresh_or_unflagged` -> `candidate_recovery_or_relax`
- `entry_bucket_16`: `stale_bucket` / `fresh` -> `candidate_recovery_or_relax`
- `entry_bucket_17`: `strength_bucket` / `strong_strength_momentum` -> `candidate_recovery_or_relax`
- `entry_bucket_18`: `strength_bucket` / `weak_strength_momentum` -> `candidate_recovery_or_relax`

### Entry Bucket Workorders

- `entry_bucket_source_quality_1`: `chosen_action` / `WAIT_REQUOTE` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_2`: `chosen_action` / `NO_BUY_AI` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_3`: `combo_entry_spot` / `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_4`: `combo_entry_spot` / `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_5`: `combo_entry_spot` / `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_6`: `exit_rule` / `exit_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_7`: `exit_rule` / `scalp_hard_stop_pct` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_8`: `liquidity_bucket` / `liquidity_high` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_9`: `overbought_bucket` / `overbought_normal` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_10`: `score_band` / `score_70p` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`

## Submit Bucket Attribution

- decision_authority: `adm_ldm_submit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'submit_rows': 131, 'bucket_count': 86, 'contract_gap_count': 0, 'workorder_count': 0, 'runtime_candidate_count': 0, 'quote_freshness_attribution_present': True, 'quote_freshness_resolution_counts': {'refresh_failed_quote_stale': 5, 'refresh_not_attempted_or_not_instrumented': 1, 'refresh_resolved_quote_freshness': 15, 'sim_submit_path_not_applicable': 110}, 'pre_submit_refresh_applied_counts': {'observer_quote_refresh_applied': 1, 'refresh_attempted_not_applied': 5, 'refresh_not_attempted_or_not_instrumented': 1, 'sim_submit_path_not_applicable': 110, 'ws_snapshot_refresh_applied': 14}, 'real_submitted_row_count': 0, 'missing_broker_order_key_count': 0, 'bot_history_broker_order_key_backfill_candidate_count': 0, 'bot_history_broker_order_key_backfill_full_coverage': False, 'bot_history_broker_order_key_exact_mapping_count': 0, 'bot_history_broker_order_key_exact_mapping_full_coverage': False, 'post_submit_provenance_join_resolution': 'no_gap_broker_order_key_present_or_no_missing_rows', 'bot_history_broker_order_key_backfill_candidates': [], 'missing_broker_order_key_rate': 0.0, 'post_submit_provenance_join_gap_raw': False, 'post_submit_provenance_join_gap': False}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 131 | 86 | 0.2986 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 128 | 86 | 0.2986 | `keep_collecting` |
| `broker_order_forbidden` | `false` | 3 | 0 | None | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 43 | 30 | 0.3755 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 28 | 25 | -0.0799 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 20 | 17 | 0.9791 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 16 | 12 | -0.2716 | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_resolved_quote_freshness|fill=false|submitted=false` | 13 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_failed_quote_stale|fill=false|submitted=false` | 4 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_pass|revalidation=ok_or_unflagged|quote_age=quote_age_lt1s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=caution|refresh=refresh_failed_quote_stale|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_pass|revalidation=ok_or_unflagged|quote_age=quote_age_lt1s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=caution|refresh=refresh_resolved_quote_freshness|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_pass|revalidation=ok_or_unflagged|quote_age=quote_age_lt1s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=safe|refresh=refresh_resolved_quote_freshness|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=pre_submit_liquidity_guard_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=latency_unknown|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | 0.5334 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | 2.491 | `source_quality_workorder` |
| `latency_reason` | `scalp_live_simulator` | 110 | 86 | 0.2986 | `keep_collecting` |
| `latency_reason` | `other_danger` | 12 | 0 | None | `keep_collecting` |
| `latency_reason` | `spread_too_wide` | 4 | 0 | None | `keep_collecting` |
| `latency_reason` | `quote_stale,ws_age_too_high,spread_too_wide` | 3 | 0 | None | `keep_collecting` |
| `latency_reason` | `latency_reason_unknown` | 1 | 0 | None | `source_quality_workorder` |
| `latency_reason` | `quote_stale,ws_age_too_high` | 1 | 0 | None | `keep_collecting` |
| `latency_state` | `simulated` | 110 | 86 | 0.2986 | `keep_collecting` |
| `latency_state` | `danger` | 17 | 0 | None | `keep_collecting` |
| `latency_state` | `caution` | 2 | 0 | None | `keep_collecting` |
| `latency_state` | `latency_unknown` | 1 | 0 | None | `source_quality_workorder` |
| `latency_state` | `safe` | 1 | 0 | None | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 60 | 43 | 0.1986 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 51 | 43 | 0.3986 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_not_available` | 20 | 0 | None | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 60 | 43 | 0.1986 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 50 | 43 | 0.3986 | `keep_collecting` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 21 | 0 | None | `source_quality_workorder` |
| `overbought_bucket` | `overbought_ok` | 108 | 85 | 0.2728 | `keep_collecting` |
| `overbought_bucket` | `overbought_not_available` | 21 | 0 | None | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 2 | 1 | 2.491 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 110 | 86 | 0.2986 | `keep_collecting` |
| `overbought_guard_action` | `overbought_guard_unknown` | 21 | 0 | None | `source_quality_workorder` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 110 | 86 | 0.2986 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `refresh_age_lt1s` | 15 | 0 | None | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 130, 'source_row_count': 130, 'bucket_count': 32, 'joined_sample': 430, 'source_quality_adjusted_ev_pct': -0.7244, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 56 | 56 | -1.3748 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 8 | 8 | -1.3396 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 5 | 5 | -0.336 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 5 | 5 | 4.3865 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 5 | 5 | 1.4116 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 3 | 3 | -0.9654 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 2 | 2 | 0.1 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 0.3971 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 22 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 8 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos150_pos300_plus|held=held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos150_pos300|held=held_600_1800s_plus` | 3 | 0 | None | `hold_sample` |
| `held_bucket` | `held_not_applicable_at_start` | 110 | 86 | -0.7244 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 18 | 0 | None | `hold_sample` |
| `holding_action` | `WAIT` | 97 | 75 | -0.6491 | `candidate_tighten_or_exclude` |
| `holding_action` | `BUY` | 8 | 8 | -1.3396 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 5 | 3 | -0.9654 | `candidate_tighten_or_exclude` |
| `holding_action` | `SELL_TODAY` | 20 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 110 | 86 | -0.7244 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 20 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 75 | 67 | -1.3523 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 10 | 5 | -0.336 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 8 | 5 | 1.4116 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300_plus` | 7 | 5 | 4.3865 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg010_pos080` | 4 | 2 | 0.1 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 2 | 2 | 0.3971 | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 24 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- `holding_bucket_source_quality_1`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_2`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_3`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_4`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_5`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_6`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_7`: `held_bucket` / `held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_8`: `holding_action` / `WAIT` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_9`: `holding_action` / `BUY` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_10`: `holding_action` / `holding_action_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Exit Bucket Attribution

- decision_authority: `adm_ldm_exit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'exit_rows': 352, 'source_row_count': 352, 'bucket_count': 46, 'joined_sample': 710, 'source_quality_adjusted_ev_pct': -0.7578, 'source_quality_gate': 'pass', 'unknown_reason_counts': {'not_applicable': 5, 'join_gap': 8, 'missing_source_field': 1}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 38 | 38 | -1.2797 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 16 | 16 | -1.1129 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 13 | 13 | -2.456 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 11 | 11 | -0.5645 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 11 | 11 | -0.9496 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 9 | 9 | -1.2974 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 8 | 8 | -0.8484 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 8 | 8 | -1.2407 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 5 | 5 | -0.252 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos150_pos300` | 3 | 3 | 1.32 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 3 | 3 | -0.2867 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 3 | 3 | 1.0694 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 2 | 2 | 0.075 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos150_pos300_plus` | 2 | 2 | 7.8637 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` | 2 | 2 | 1.11 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos150_pos300` | 2 | 2 | 1.785 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 2 | 2 | 0.889 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 1 | 1 | 0.45 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos150_pos300_plus` | 1 | 1 | 6.0685 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 1 | 1 | 0.3386 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 1 | 1 | 0.4556 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_euphoria_context_noop|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown` | 104 | 0 | None | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown` | 106 | 0 | None | `source_quality_workorder` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 55 | 55 | -0.7733 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 28 | 28 | -1.3671 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 20 | 20 | -0.9958 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 230 | 20 | 0.5895 | `source_quality_workorder` |
| `exit_outcome` | `MISSED_UPSIDE` | 19 | 19 | -0.9825 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 55 | 55 | -0.7733 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 37 | 37 | -1.6124 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 23 | 23 | -0.9992 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 20 | 20 | 0.5895 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_trailing_take_profit` | 7 | 7 | 0.8258 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_rule_unknown` | 210 | 0 | None | `source_quality_workorder` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 67 | 67 | -1.1472 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 55 | 55 | -0.7733 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 20 | 20 | 0.5895 | `candidate_recovery_or_relax` |
| `exit_source_stage` | `scalp_sim_euphoria_context_noop` | 104 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 106 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 106 | 106 | -1.3024 | `candidate_tighten_or_exclude` |

### Exit Bucket Attribution Workorders

- `exit_bucket_source_quality_1`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_2`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_3`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_4`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_5`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_6`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_7`: `combo_exit_result` / `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_8`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_9`: `combo_exit_result` / `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_10`: `combo_exit_result` / `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos150_pos300` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `incremental_notional_ev_pct`
- summary: `{'scale_in_rows': 1739, 'bucket_count': 349, 'edge_bucket_count': 0, 'actionable_bucket_count': 0, 'runtime_authority_blocked_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'arm_counts': {'PYRAMID': 567, 'AVG_DOWN': 1172}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_70p` | 990 | 990 | None | -0.6006 | 0.2808 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 322 | 322 | None | -0.5085 | 0.3292 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 212 | 212 | None | -0.1394 | 0.5047 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 124 | 124 | None | -0.4256 | 0.2339 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 72 | 72 | None | -0.3828 | 0.4444 | `hold_sample` |
| `ai_score_band` | `score_unknown` | 19 | 0 | None | None | None | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 1720 | 1720 | None | -0.5048 | 0.3209 | `hold_sample` |
| `ai_score_source` | `stage_rule_backfilled` | 19 | 0 | None | None | None | `hold_sample` |
| `arm` | `AVG_DOWN` | 1172 | 1159 | None | -1.0456 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 567 | 561 | None | 0.6124 | 0.984 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 823 | 810 | None | -1.3198 | 0.0 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 567 | 561 | None | 0.6124 | 0.984 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 349 | 349 | None | -0.4092 | 0.0 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 523 | 523 | None | 0.5576 | 0.9847 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 97 | 97 | None | -0.8648 | 0.2268 | `hold_sample` |
| `blocker_reason` | `ok` | 59 | 59 | None | -2.8346 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_scale_in_window_expansion` | 17 | 17 | None | 0.1018 | 0.3529 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.32)` | 16 | 16 | None | -1.32 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.43)` | 16 | 16 | None | -1.43 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.70)` | 16 | 16 | None | -1.7 | 0.0 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `adm_ldm_overnight_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'overnight_rows': 40, 'bucket_count': 32, 'actionable_bucket_count': 11, 'runtime_candidate_count': 9, 'workorder_count': 10, 'status_counts': {'HOLD_OVERNIGHT': 20, 'SELL_TODAY': 20}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 8 | 8 | -0.8484 | -1.1313 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 5 | 5 | -0.252 | -0.336 | 0.0 | `hold_no_edge` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos150_pos300` | 3 | 3 | 1.32 | 1.76 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 2 | 2 | 0.075 | 0.1 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos150_pos300_plus` | 2 | 2 | 7.8637 | 10.485 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_lt_neg070` | 8 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg010_pos080` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 5 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_pos150_pos300` | 3 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_pos150_pos300_plus` | 2 | 0 | None | None | None | `hold_sample` |
| `confidence_band` | `confidence_070p` | 40 | 20 | 0.5895 | 0.786 | 0.35 | `candidate_recovery_or_relax` |
| `held_bucket` | `held_600_1800s_plus` | 36 | 18 | 0.6742 | 0.8989 | 0.3889 | `candidate_recovery_or_relax` |
| `held_bucket` | `held_600_1800s` | 4 | 2 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `overnight_action` | `SELL_TODAY` | 40 | 20 | 0.5895 | 0.786 | 0.35 | `candidate_recovery_or_relax` |
| `overnight_status` | `SELL_TODAY` | 20 | 20 | 0.5895 | 0.786 | 0.35 | `candidate_recovery_or_relax` |
| `overnight_status` | `HOLD_OVERNIGHT` | 20 | 0 | None | None | None | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 26 | 13 | -0.619 | -0.8254 | 0.0 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_pos150_pos300` | 6 | 3 | 1.32 | 1.76 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos150_pos300_plus` | 4 | 2 | 7.8637 | 10.485 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 4 | 2 | 0.075 | 0.1 | 1.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 36 | 18 | 0.6742 | 0.8989 | 0.3889 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_lt_neg070` | 16 | 8 | -0.8484 | -1.1313 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 10 | 5 | -0.252 | -0.336 | 0.0 | `hold_no_edge` |
| `source_quality_gate` | `overnight_decision_coverage` | 40 | 20 | 0.5895 | 0.786 | 0.35 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 20 | 20 | 0.5895 | 0.786 | 0.35 | `candidate_recovery_or_relax` |
| `stage` | `exit` | 20 | 20 | 0.5895 | 0.786 | 0.35 | `candidate_recovery_or_relax` |

### Overnight Bucket Runtime Approval Candidates

- `overnight_bucket_2`: `confidence_band` / `confidence_070p` -> `candidate_recovery_or_relax`
- `overnight_bucket_3`: `held_bucket` / `held_600_1800s_plus` -> `candidate_recovery_or_relax`
- `overnight_bucket_4`: `overnight_action` / `SELL_TODAY` -> `candidate_recovery_or_relax`
- `overnight_bucket_5`: `overnight_status` / `SELL_TODAY` -> `candidate_recovery_or_relax`
- `overnight_bucket_6`: `peak_profit_band` / `peak_lt_zero` -> `candidate_tighten_or_exclude`
- `overnight_bucket_7`: `price_source` / `holding_price_samples_last` -> `candidate_recovery_or_relax`
- `overnight_bucket_9`: `source_quality_gate` / `overnight_decision_coverage` -> `candidate_recovery_or_relax`
- `overnight_bucket_10`: `source_stage` / `scalp_sim_overnight_sell_today` -> `candidate_recovery_or_relax`
- `overnight_bucket_11`: `stage` / `exit` -> `candidate_recovery_or_relax`

### Overnight Bucket Workorders

- `overnight_bucket_source_quality_1`: `combo_overnight_decision` / `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_2`: `confidence_band` / `confidence_070p` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_3`: `held_bucket` / `held_600_1800s_plus` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_4`: `overnight_action` / `SELL_TODAY` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_5`: `overnight_status` / `SELL_TODAY` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_6`: `peak_profit_band` / `peak_lt_zero` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_7`: `price_source` / `holding_price_samples_last` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_8`: `profit_band` / `profit_lt_neg070` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_9`: `source_quality_gate` / `overnight_decision_coverage` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_10`: `source_stage` / `scalp_sim_overnight_sell_today` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`

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
