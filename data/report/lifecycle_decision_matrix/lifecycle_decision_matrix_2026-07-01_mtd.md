# Lifecycle Decision Matrix - 2026-07-01

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-01_mtd`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `7312`
- source_rows_total: `13954`
- retained_rows: `7312`
- dropped_rows_by_source: `{'dedupe': 6642}`
- joined_rows: `3738`
- policy_pass_count: `5`
- promote_ready_count: `1`
- entry_bucket_actionable_count: `6`
- entry_bucket_runtime_candidate_count: `1`
- holding_bucket_count/workorders: `24` / `6`
- exit_bucket_count/workorders: `34` / `10`
- scale_in_bucket_actionable_count: `0`
- scale_in_bucket_runtime_candidate_count: `0`
- overnight_bucket_actionable_count: `0`
- overnight_bucket_runtime_candidate_count: `0`
- lifecycle_flow_bucket_count: `73`
- lifecycle_flow_complete_count: `11`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `0` / `11` / `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0016`
- incomplete_flow_reason_counts: `{'missing_exit': 3758, 'missing_holding': 6908, 'missing_submit': 6882, 'candidate_id_only': 6802, 'missing_entry': 6781, 'sim_record_id_only': 51, 'scale_in_noise_only': 3599, 'postclose_exit_without_entry': 3182}`
- bucket_directed_sim_probe: `{'observed_row_count': 3413, 'matched_row_count': 0, 'background_row_count': 3413, 'matched_unique_source_bucket_count': 0, 'match_status_counts': {'no_match': 227, 'not_instrumented': 3186}, 'matched_classification_state_counts': {}, 'primary_source': 'matched_bucket_directed_sim_probe_only', 'background_source': 'unmatched_or_policy_missing_sim_observation', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 1, 'route_counts': {'bounded_auxiliary_weight': 1, 'hold_sample': 4}, 'quality_counts': {'observational_only_pending_outcome': 1, 'hold_sample': 4}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 287 | 26 | 1.9634 | 0.2355 | `pass` | `BUY_DEFENSIVE` | True |
| `submit` | 117 | 20 | -0.5277 | 0.3419 | `pass` | `NO_CHANGE` | False |
| `holding` | 71 | 20 | -0.0056 | 0.5634 | `pass` | `EXIT` | False |
| `scale_in` | 3642 | 3612 | -0.5501 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 3195 | 60 | -0.6539 | 0.1127 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 6951, 'complete_flow_count': 11, 'direct_sim_record_complete_flow_count': 0, 'adm_bridge_complete_flow_count': 11, 'fallback_complete_flow_count': 0, 'direct_flow_zero_diagnostic': {'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'direct_sim_record_flow_count': 51, 'direct_sim_record_incomplete_flow_count': 51, 'direct_sim_record_stage_coverage_counts': {'holding': 4, 'exit': 47}, 'direct_sim_record_incomplete_reason_counts': {'missing_entry': 51, 'missing_submit': 51, 'missing_holding': 47, 'missing_exit': 4, 'sim_record_id_only': 51, 'scale_in_noise_only': 4, 'postclose_exit_without_entry': 47}, 'runtime_effect': False, 'decision_authority': 'ldm_direct_flow_diagnostic_only'}, 'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'incomplete_flow_count': 6940, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 7312, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0016, 'complete_flow_conversion_denominator': 3193, 'complete_flow_conversion_rate': 0.0034, 'active_priority_incomplete_seed_count': 159, 'scale_in_followup_event_count': 3642, 'scale_in_unique_flow_count': 3013, 'scale_in_noise_flow_count': 3599, 'denominator_exclusion_counts': {'scale_in_noise_flow_excluded': 3599, 'active_priority_incomplete_seed_excluded': 159}, 'conversion_blocker_reason_counts': {'missing_entry': 3182, 'missing_submit': 3182, 'sim_record_id_only': 47, 'postclose_exit_without_entry': 3182, 'missing_holding': 3178, 'candidate_id_only': 3135}, 'observation_seed_reason_counts': {'missing_exit': 3758, 'missing_holding': 3730, 'missing_submit': 3700, 'candidate_id_only': 3667, 'missing_entry': 3599, 'sim_record_id_only': 4, 'scale_in_noise_only': 3599}, 'join_contract_blocked': False, 'bundle_ev_tuning_state': 'ready_for_bundle_ev_tuning', 'top_incomplete_reason': 'missing_holding', 'stage_identity': {'entry': {'source_row_count': 287, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 215, 'candidate_id': 72}, 'identity_join_rate': 1.0}, 'submit': {'source_row_count': 117, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 117}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 71, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 67, 'exact_sim_record_id': 4}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 3642, 'identity_missing_count': 0, 'identity_quality_counts': {'exact_sim_record_id': 47, 'candidate_id': 3595}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 3195, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 13, 'exact_sim_record_id': 47, 'candidate_id': 3135}, 'identity_join_rate': 1.0}}, 'required_stage_source_counts': {'entry': 287, 'submit': 117, 'holding': 71, 'exit': 3195}, 'incomplete_flow_reason_counts': {'missing_exit': 3758, 'missing_holding': 6908, 'missing_submit': 6882, 'candidate_id_only': 6802, 'missing_entry': 6781, 'sim_record_id_only': 51, 'scale_in_noise_only': 3599, 'postclose_exit_without_entry': 3182}, 'bucket_count': 73, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:b17339bebb` | 1 | 1 | 2.9613 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:b620fd9627` | 1 | 1 | -1.396 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:e8b25163c1` | 1 | 1 | 0.4047 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:441959da5f` | 1 | 1 | -1.7162 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:20905a436c` | 1 | 1 | 0.1443 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:abbedf07de` | 1 | 1 | -0.1943 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:a715976d90` | 1 | 1 | -1.265 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:c37b5ba29e` | 1 | 1 | -1.4977 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:8de8567ae2` | 1 | 1 | 1.35 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:dc3474d040` | 1 | 1 | 0.3232 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:ef6857b3cc` | 1 | 1 | 1.7031 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 2972 | 2953 | -0.7924 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 627 | 616 | 0.6298 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 39 | 39 | -0.9841 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 9 | 9 | 2.7826 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 4 | 4 | 5.0573 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 4 | 4 | 0.18 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:2e5e6a8919` | 3 | 3 | -1.3825 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 2 | 2 | 5.7424 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:c7dbb66715` | 1 | 1 | -1.54 | `hold_sample` | `join_contract_blocked` |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 287, 'bucket_count': 176, 'actionable_bucket_count': 6, 'source_quality_blocked_bucket_count': 22, 'runtime_candidate_count': 1, 'workorder_count': 16}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `WAIT_REQUOTE` | 76 | 19 | 3.0218 | 5.2238 | 0.7368 | `candidate_recovery_or_relax` |
| `chosen_action` | `NO_BUY_AI` | 126 | 4 | -0.0729 | 2.0075 | 1.0 | `hold_sample` |
| `chosen_action` | `BUY_NOW` | 4 | 2 | -0.7302 | -0.8 | 0.5 | `source_quality_workorder` |
| `chosen_action` | `BUY_DEFENSIVE` | 12 | 1 | -4.6124 | 1.64 | 1.0 | `source_quality_workorder` |
| `chosen_action` | `ALLOW_BOTTOMING_ENTRY` | 5 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `ALLOW_LEVEL1_RISK_OFF_ENTRY` | 41 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_SOURCE_QUALITY` | 2 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_STALE` | 21 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_0900_1000` | 25 | 3 | 0.1586 | -0.14 | 0.6667 | `source_quality_workorder` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 3 | 3 | 0.1515 | 0.0894 | 0.3333 | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_ok|time=time_1200_1400` | 2 | 2 | 5.9184 | 9.86 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 2 | 2 | 0.8352 | 0.7558 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 5 | 1 | 3.6054 | 2.18 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 4 | 1 | -0.6409 | 1.51 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_ok|time=time_1200_1400` | 3 | 1 | 0.8449 | 2.93 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 1 | 1 | 0.5406 | 0.5129 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_ok|time=time_1200_1400` | 1 | 1 | 10.9442 | 18.9616 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_chase_risk|time=time_1200_1400` | 1 | 1 | -4.101 | 1.41 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_chase_risk|time=time_1200_1400` | 1 | 1 | 10.6654 | 18.6176 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 1 | 1 | -2.2732 | -1.2189 | 0.0 | `hold_sample` |
| `liquidity_bucket` | `liquidity_high` | 124 | 21 | 2.6193 | 4.9925 | 0.7619 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 92 | 12 | 0.3826 | 0.5455 | 0.6667 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 15 | 15 | 3.7838 | 6.5608 | 0.7333 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh_or_unflagged` | 61 | 15 | 3.7838 | 6.5608 | 0.7333 | `candidate_recovery_or_relax` |
| `strength_bucket` | `strong_strength_momentum` | 33 | 17 | 3.2616 | 5.7876 | 0.7059 | `candidate_recovery_or_relax` |

### Entry Bucket Runtime Approval Candidates

- `entry_bucket_2`: `liquidity_bucket` / `liquidity_high` -> `candidate_recovery_or_relax`

### Entry Bucket Workorders

- `entry_bucket_unknown_source_quality_1`: `chosen_action` / `BUY_NOW` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_2`: `chosen_action` / `BUY_DEFENSIVE` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_3`: `combo_entry_spot` / `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_0900_1000` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_4`: `combo_entry_spot` / `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1200_1400` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_5`: `combo_entry_spot` / `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1000_1200` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_6`: `combo_entry_spot` / `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1400_close` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_7`: `combo_entry_spot` / `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_0900_1000` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_8`: `combo_entry_spot` / `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1200_1400` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_9`: `combo_entry_spot` / `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1400_close` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_10`: `exit_rule` / `exit_unknown` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_source_quality_1`: `chosen_action` / `WAIT_REQUOTE` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_2`: `liquidity_bucket` / `liquidity_high` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_3`: `overbought_bucket` / `overbought_normal` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_4`: `source_stage` / `wait6579_ev_cohort` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_5`: `stale_bucket` / `fresh_or_unflagged` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_6`: `strength_bucket` / `strong_strength_momentum` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`

## Submit Bucket Attribution

- decision_authority: `adm_ldm_submit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'submit_rows': 117, 'bucket_count': 79, 'contract_gap_count': 0, 'workorder_count': 0, 'runtime_candidate_count': 0, 'quote_freshness_attribution_present': True, 'row_quote_freshness_attribution_present': True, 'sentinel_quote_freshness_attribution_present': True, 'sentinel_quote_freshness_attribution': {'source_report_type': 'buy_funnel_sentinel', 'decision_authority': 'submit_drought_quote_freshness_attribution_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'forbidden_uses': ['broker_order_submit', 'adm_ldm_training_input', 'general_threshold_ev_input', 'live_auto_promotion'], 'refresh_attempted_count': 34, 'refresh_applied_count': 33, 'still_latency_blocked_after_refresh_count': 24, 'latency_pass_recovered_count': 9, 'order_bundle_submitted_after_refresh_count': 8, 'refresh_subreason_counts': {'observer_quote_refresh_failed_invalid': 12, 'observer_quote_refresh_failed_stale': 140, 'ws_snapshot_refresh_failed_invalid': 67, 'ws_snapshot_refresh_failed_stale': 31, 'ws_snapshot_refresh_failed_missing': 56}, 'refresh_block_subreason_counts': {'observer_quote_refresh_failed_invalid': 12, 'observer_quote_refresh_failed_stale': 140, 'ws_snapshot_refresh_failed_invalid': 67, 'ws_snapshot_refresh_failed_stale': 31, 'ws_snapshot_refresh_failed_missing': 56}, 'latency_pass_recovered_downstream_counts': {'order_bundle_submitted': 8, 'upstream_block_after_latency_recovery': 1}, 'post_restart_window_policy': 'event_provenance_only'}, 'quote_freshness_resolution_counts': {'refresh_failed_quote_stale': 5, 'refresh_not_attempted_or_not_instrumented': 45, 'sim_submit_path_not_applicable': 67}, 'pre_submit_refresh_applied_counts': {'refresh_attempted_not_applied': 5, 'refresh_not_attempted_or_not_instrumented': 45, 'sim_submit_path_not_applicable': 67}, 'real_submitted_row_count': 45, 'missing_broker_order_key_count': 0, 'bot_history_broker_order_key_backfill_candidate_count': 0, 'bot_history_broker_order_key_backfill_full_coverage': False, 'bot_history_broker_order_key_exact_mapping_count': 0, 'bot_history_broker_order_key_exact_mapping_full_coverage': False, 'post_submit_provenance_join_resolution': 'no_gap_broker_order_key_present_or_no_missing_rows', 'bot_history_broker_order_key_backfill_candidates': [], 'missing_broker_order_key_rate': 0.0, 'post_submit_provenance_join_gap_raw': False, 'post_submit_provenance_join_gap': False}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 72 | 20 | -0.5277 | `keep_collecting` |
| `actual_order_submitted` | `true` | 45 | 0 | None | `keep_collecting` |
| `broker_order_forbidden` | `true` | 72 | 20 | -0.5277 | `keep_collecting` |
| `broker_order_forbidden` | `false` | 45 | 0 | None | `keep_collecting` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=caution|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 31 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 22 | 3 | -2.267 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 15 | 5 | -0.5818 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 11 | 5 | -0.5469 | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=safe|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 10 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 8 | 5 | 0.411 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 6 | 1 | -1.54 | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_failed_quote_stale|fill=false|submitted=false` | 5 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_lt1s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=caution|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 4 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 3 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 2 | 1 | 1.3744 | `source_quality_workorder` |
| `latency_reason` | `scalp_live_simulator` | 67 | 20 | -0.5277 | `keep_collecting` |
| `latency_reason` | `caution_normal_entry_allowed` | 35 | 0 | None | `keep_collecting` |
| `latency_reason` | `safe_normal_entry_allowed` | 10 | 0 | None | `keep_collecting` |
| `latency_reason` | `quote_stale,ws_age_too_high` | 4 | 0 | None | `keep_collecting` |
| `latency_reason` | `quote_stale,ws_age_too_high,spread_too_wide` | 1 | 0 | None | `keep_collecting` |
| `latency_state` | `simulated` | 67 | 20 | -0.5277 | `keep_collecting` |
| `latency_state` | `caution` | 35 | 0 | None | `keep_collecting` |
| `latency_state` | `safe` | 10 | 0 | None | `keep_collecting` |
| `latency_state` | `danger` | 5 | 0 | None | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 56 | 18 | -0.5772 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_not_available` | 50 | 0 | None | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 11 | 2 | -0.0828 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 56 | 18 | -0.5772 | `keep_collecting` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 50 | 0 | None | `source_quality_workorder` |
| `liquidity_guard_action` | `would_block` | 11 | 2 | -0.0828 | `keep_collecting` |
| `overbought_bucket` | `overbought_not_available` | 50 | 0 | None | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 46 | 9 | -1.25 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 21 | 11 | 0.0632 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 67 | 20 | -0.5277 | `keep_collecting` |
| `overbought_guard_action` | `overbought_guard_unknown` | 50 | 0 | None | `source_quality_workorder` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 67 | 20 | -0.5277 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `refresh_age_not_instrumented` | 45 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `refresh_age_10s_plus` | 3 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `refresh_age_1_3s` | 1 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `refresh_age_lt1s` | 1 | 0 | None | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 71, 'source_row_count': 71, 'bucket_count': 24, 'joined_sample': 100, 'source_quality_adjusted_ev_pct': -0.0056, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 6, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 7 | 7 | 0.7493 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 5 | 5 | -1.569 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 3 | 3 | -0.1365 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 3 | 3 | 1.6029 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1 | 1 | -1.7162 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | -0.1943 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 45 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_180_600s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 3 | 0 | None | `hold_sample` |
| `held_bucket` | `held_not_applicable_at_start` | 67 | 20 | -0.0056 | `hold_no_edge` |
| `held_bucket` | `held_180_600s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 3 | 0 | None | `hold_sample` |
| `holding_action` | `WAIT` | 60 | 15 | -0.2006 | `hold_no_edge` |
| `holding_action` | `holding_action_not_applicable_at_start` | 6 | 5 | 0.5796 | `candidate_recovery_or_relax` |
| `holding_action` | `BUY` | 1 | 0 | None | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 4 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 67 | 20 | -0.0056 | `hold_no_edge` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 4 | 0 | None | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 10 | 10 | 1.0054 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_lt_neg070` | 10 | 6 | -1.5935 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 4 | 4 | -0.1509 | `hold_no_edge` |
| `profit_band` | `profit_not_applicable_at_start` | 47 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- `holding_bucket_source_quality_1`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_2`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_3`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_4`: `holding_action` / `holding_action_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_5`: `profit_band` / `profit_pos150_pos300` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_6`: `profit_band` / `profit_lt_neg070` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Exit Bucket Attribution

- decision_authority: `adm_ldm_exit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'exit_rows': 3195, 'source_row_count': 3195, 'bucket_count': 34, 'joined_sample': 300, 'source_quality_adjusted_ev_pct': -0.6538, 'source_quality_gate': 'pass', 'unknown_reason_counts': {'not_applicable': 1, 'join_gap': 8, 'missing_source_field': 1}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 30 | 30 | -1.1173 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 11 | 11 | -0.4991 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 4 | 4 | -1.2337 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 4 | 4 | -0.1509 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 4 | 4 | 1.673 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 2 | 2 | -0.5465 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 1 | 1 | 0.09 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` | 1 | 1 | 1.26 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 1 | 1 | -1.7162 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | -1.265 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300` | 1 | 1 | 1.35 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_euphoria_context_noop|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown` | 61 | 0 | None | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown` | 3074 | 0 | None | `source_quality_workorder` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 43 | 43 | -0.8758 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 7 | 7 | -0.4876 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 5 | 5 | 1.0854 | `candidate_recovery_or_relax` |
| `exit_outcome` | `outcome_unknown` | 3139 | 4 | -1.2337 | `source_quality_workorder` |
| `exit_outcome` | `NEUTRAL` | 1 | 1 | 1.35 | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 43 | 43 | -0.8758 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 11 | 11 | 0.5768 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 4 | 4 | -1.2337 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 2 | 2 | -1.4906 | `hold_sample` |
| `exit_rule` | `exit_rule_unknown` | 3135 | 0 | None | `source_quality_workorder` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 43 | 43 | -0.8758 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 13 | 13 | 0.2588 | `hold_no_edge` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 4 | 4 | -1.2337 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_euphoria_context_noop` | 61 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 3074 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 36 | 36 | -1.151 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 11 | 11 | -0.4991 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 7 | 7 | 0.9927 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos080_pos150` | 5 | 5 | 0.1313 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 1 | 1 | 0.09 | `hold_sample` |
| `profit_band` | `profit_unknown` | 3135 | 0 | None | `source_quality_workorder` |

### Exit Bucket Attribution Workorders

- `exit_bucket_source_quality_1`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_2`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_3`: `combo_exit_result` / `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_4`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_5`: `combo_exit_result` / `source=scalp_sim_euphoria_context_noop|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_6`: `combo_exit_result` / `source=scalp_sim_panic_context_warning|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_7`: `exit_outcome` / `outcome_not_applicable_partial_exit` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_8`: `exit_outcome` / `GOOD_EXIT` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_9`: `exit_outcome` / `MISSED_UPSIDE` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_10`: `exit_outcome` / `outcome_unknown` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `incremental_notional_ev_pct`
- summary: `{'scale_in_rows': 3642, 'bucket_count': 263, 'edge_bucket_count': 0, 'actionable_bucket_count': 0, 'runtime_authority_blocked_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'arm_counts': {'PYRAMID': 631, 'AVG_DOWN': 3011}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_70p` | 1575 | 1575 | None | -0.5635 | 0.2051 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 764 | 764 | None | -0.604 | 0.1322 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 440 | 440 | None | -1.0007 | 0.025 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 440 | 440 | None | -0.5442 | 0.2364 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 391 | 391 | None | -0.7317 | 0.1381 | `hold_sample` |
| `ai_score_band` | `score_unknown` | 32 | 2 | None | None | None | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 3610 | 3610 | None | -0.6412 | 0.1643 | `hold_sample` |
| `ai_score_source` | `sim_scale_in_source_not_scored` | 2 | 2 | None | None | None | `hold_sample` |
| `ai_score_source` | `stage_rule_backfilled` | 30 | 0 | None | None | None | `hold_sample` |
| `arm` | `AVG_DOWN` | 3011 | 2992 | None | -0.888 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 631 | 620 | None | 0.5536 | 0.9595 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 2994 | 2975 | None | -0.8745 | 0.0 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 631 | 620 | None | 0.5536 | 0.9595 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 17 | 17 | None | -3.2518 | 0.0 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 574 | 574 | None | 0.4473 | 0.9564 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.54)` | 308 | 308 | None | -0.54 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.68)` | 143 | 143 | None | -0.68 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.43)` | 132 | 132 | None | -0.43 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.23)` | 125 | 125 | None | -0.23 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.46)` | 78 | 78 | None | -0.46 | 0.0 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `adm_ldm_overnight_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'overnight_rows': 8, 'bucket_count': 16, 'actionable_bucket_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'status_counts': {'HOLD_OVERNIGHT': 4, 'SELL_TODAY': 4}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 4 | 4 | -1.2337 | -1.645 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_lt_neg070` | 4 | 0 | None | None | None | `hold_sample` |
| `confidence_band` | `confidence_070p` | 8 | 4 | -1.2337 | -1.645 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 6 | 3 | -1.3825 | -1.8433 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 2 | 1 | -0.7875 | -1.05 | 0.0 | `hold_sample` |
| `overnight_action` | `SELL_TODAY` | 8 | 4 | -1.2337 | -1.645 | 0.0 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 4 | 4 | -1.2337 | -1.645 | 0.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 4 | 0 | None | None | None | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 8 | 4 | -1.2337 | -1.645 | 0.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 8 | 4 | -1.2337 | -1.645 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 8 | 4 | -1.2337 | -1.645 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 8 | 4 | -1.2337 | -1.645 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 4 | 4 | -1.2337 | -1.645 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_decision` | 4 | 0 | None | None | None | `hold_sample` |
| `stage` | `exit` | 4 | 4 | -1.2337 | -1.645 | 0.0 | `hold_sample` |
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
