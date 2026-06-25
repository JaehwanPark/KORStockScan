# Lifecycle Decision Matrix - 2026-06-25

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-25`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `6235`
- source_rows_total: `7648`
- retained_rows: `6235`
- dropped_rows_by_source: `{'dedupe': 1413}`
- joined_rows: `3836`
- policy_pass_count: `5`
- promote_ready_count: `0`
- entry_bucket_actionable_count: `10`
- entry_bucket_runtime_candidate_count: `5`
- holding_bucket_count/workorders: `29` / `10`
- exit_bucket_count/workorders: `48` / `10`
- scale_in_bucket_actionable_count: `0`
- scale_in_bucket_runtime_candidate_count: `0`
- overnight_bucket_actionable_count: `0`
- overnight_bucket_runtime_candidate_count: `0`
- lifecycle_flow_bucket_count: `68`
- lifecycle_flow_complete_count: `30`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `0` / `30` / `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0054`
- incomplete_flow_reason_counts: `{'missing_submit': 5490, 'missing_holding': 5487, 'missing_exit': 3680, 'missing_entry': 5367, 'postclose_exit_without_entry': 1817, 'sim_record_id_only': 61, 'scale_in_noise_only': 3550, 'candidate_id_only': 5363}`
- bucket_directed_sim_probe: `{'observed_row_count': 2104, 'matched_row_count': 22, 'background_row_count': 2082, 'matched_unique_source_bucket_count': 1, 'match_status_counts': {'matched': 22, 'no_match': 261, 'not_instrumented': 1821}, 'matched_classification_state_counts': {'lifecycle_flow_sim_probe_candidate': 22}, 'primary_source': 'matched_bucket_directed_sim_probe_only', 'background_source': 'unmatched_or_policy_missing_sim_observation', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 1, 'route_counts': {'bounded_auxiliary_weight': 1, 'hold_sample': 4}, 'quality_counts': {'observational_only_pending_outcome': 1, 'hold_sample': 4}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 576 | 36 | -0.8218 | 0.225 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 90 | 66 | -1.0696 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 86 | 66 | -1.3207 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 3601 | 3547 | -0.4738 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 1882 | 121 | -1.0616 | 0.7779 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 5527, 'complete_flow_count': 30, 'direct_sim_record_complete_flow_count': 0, 'adm_bridge_complete_flow_count': 30, 'fallback_complete_flow_count': 0, 'direct_flow_zero_diagnostic': {'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'direct_sim_record_flow_count': 61, 'direct_sim_record_incomplete_flow_count': 61, 'direct_sim_record_stage_coverage_counts': {'holding': 4, 'exit': 53}, 'direct_sim_record_incomplete_reason_counts': {'missing_entry': 61, 'missing_submit': 61, 'missing_holding': 57, 'missing_exit': 8, 'sim_record_id_only': 61, 'scale_in_noise_only': 8, 'postclose_exit_without_entry': 53}, 'runtime_effect': False, 'decision_authority': 'ldm_direct_flow_diagnostic_only'}, 'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'incomplete_flow_count': 5497, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 6235, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0054, 'complete_flow_conversion_denominator': 1847, 'complete_flow_conversion_rate': 0.0162, 'active_priority_incomplete_seed_count': 130, 'scale_in_followup_event_count': 3601, 'scale_in_unique_flow_count': 3058, 'scale_in_noise_flow_count': 3550, 'denominator_exclusion_counts': {'scale_in_noise_flow_excluded': 3550, 'active_priority_incomplete_seed_excluded': 130}, 'conversion_blocker_reason_counts': {'missing_entry': 1817, 'missing_submit': 1817, 'missing_holding': 1813, 'postclose_exit_without_entry': 1817, 'sim_record_id_only': 53, 'candidate_id_only': 1761}, 'observation_seed_reason_counts': {'missing_submit': 3673, 'missing_holding': 3674, 'missing_exit': 3680, 'missing_entry': 3550, 'sim_record_id_only': 8, 'scale_in_noise_only': 3550, 'candidate_id_only': 3602}, 'join_contract_blocked': False, 'bundle_ev_tuning_state': 'ready_for_bundle_ev_tuning', 'top_incomplete_reason': 'missing_submit', 'stage_identity': {'entry': {'source_row_count': 576, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 516, 'candidate_id': 60}, 'identity_join_rate': 1.0}, 'submit': {'source_row_count': 90, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 90}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 86, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 82, 'exact_sim_record_id': 4}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 3601, 'identity_missing_count': 0, 'identity_quality_counts': {'exact_sim_record_id': 59, 'candidate_id': 3542}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 1882, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 65, 'exact_sim_record_id': 56, 'candidate_id': 1761}, 'identity_join_rate': 1.0}}, 'required_stage_source_counts': {'entry': 576, 'submit': 90, 'holding': 86, 'exit': 1882}, 'incomplete_flow_reason_counts': {'missing_submit': 5490, 'missing_holding': 5487, 'missing_exit': 3680, 'missing_entry': 5367, 'postclose_exit_without_entry': 1817, 'sim_record_id_only': 61, 'scale_in_noise_only': 3550, 'candidate_id_only': 5363}, 'bucket_count': 68, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:67138f9e63` | 3 | 3 | -1.0287 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:f68b1eee89` | 1 | 1 | -0.0802 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:3ba076b12f` | 1 | 1 | -0.5916 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:f3928c3e95` | 1 | 1 | -0.5748 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:8050d08a3f` | 1 | 1 | -1.7254 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:89e49a11bc` | 1 | 1 | -1.8467 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9d8cac316e` | 1 | 1 | -1.2385 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:544644011b` | 1 | 1 | 0.8636 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:947b09ea47` | 1 | 1 | -1.5196 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:545378fef0` | 1 | 1 | -1.0541 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:24e8afe254` | 1 | 1 | 0.0015 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:2a4bfd22da` | 1 | 1 | -0.8065 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:5a2fc3c833` | 1 | 1 | -2.9077 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:5a8c68df46` | 1 | 1 | -0.506 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:c64b7a41ca` | 1 | 1 | 0.6824 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:52b742f847` | 1 | 1 | -3.4591 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:2bd37cbd07` | 1 | 1 | -2.9015 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:f85a279901` | 1 | 1 | 0.8935 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_sc:569a7bc45c` | 1 | 1 | -1.0898 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:dd99a5f791` | 1 | 1 | -0.6208 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 576, 'bucket_count': 172, 'actionable_bucket_count': 10, 'source_quality_blocked_bucket_count': 0, 'runtime_candidate_count': 5, 'workorder_count': 10}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `NO_BUY_AI` | 495 | 34 | -0.8945 | -1.7868 | 0.0882 | `candidate_tighten_or_exclude` |
| `chosen_action` | `BUY_NOW` | 20 | 2 | 0.4146 | -1.6 | 0.0 | `hold_sample` |
| `chosen_action` | `ALLOW_BOTTOMING_ENTRY` | 4 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `ALLOW_LEVEL1_RISK_OFF_ENTRY` | 56 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_SOURCE_QUALITY` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 18 | 5 | -0.6903 | -2.078 | 0.2 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 41 | 4 | 0.2452 | -1.865 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 27 | 3 | -1.2115 | -0.3367 | 0.3333 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 34 | 3 | -2.0993 | -1.26 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 13 | 2 | -0.3769 | -2.815 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_1400_close` | 74 | 2 | -1.1771 | -2.135 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 2 | 2 | -3.16 | -1.075 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_watch|time=time_1200_1400` | 4 | 2 | -0.5378 | -0.04 | 0.5 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 14 | 1 | 0.555 | -1.53 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 19 | 1 | 0.5192 | -1.82 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1400_close` | 20 | 1 | -1.9791 | -1.87 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_1200_1400` | 3 | 1 | -3.2967 | -3.58 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_ok|time=time_0900_1000` | 2 | 1 | 1.1896 | -2.8 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 8 | 1 | -0.5674 | -2.66 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 3 | 1 | 0.9954 | -2.55 | 0.0 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 25 | 25 | -0.5816 | -1.988 | 0.0 | `candidate_tighten_or_exclude` |
| `liquidity_bucket` | `liquidity_high` | 461 | 36 | -0.8218 | -1.7764 | 0.0833 | `candidate_tighten_or_exclude` |
| `overbought_bucket` | `overbought_normal` | 409 | 26 | -0.8365 | -1.6577 | 0.0769 | `candidate_tighten_or_exclude` |
| `score_band` | `score_60_62` | 369 | 25 | -0.7636 | -1.872 | 0.08 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 424 | 36 | -0.8218 | -1.7764 | 0.0833 | `candidate_tighten_or_exclude` |
| `stale_bucket` | `fresh` | 191 | 18 | -0.7617 | -2.0839 | 0.0 | `candidate_tighten_or_exclude` |
| `stale_bucket` | `stale_high` | 282 | 18 | -0.882 | -1.4689 | 0.1667 | `candidate_tighten_or_exclude` |
| `strength_bucket` | `weak_strength_momentum` | 331 | 24 | -0.4249 | -2.0596 | 0.0833 | `candidate_tighten_or_exclude` |
| `time_bucket` | `time_0900_1000` | 198 | 17 | -0.2526 | -2.2294 | 0.0588 | `hold_no_edge` |
| `time_bucket` | `time_1200_1400` | 129 | 10 | -1.673 | -1.366 | 0.1 | `candidate_tighten_or_exclude` |

### Entry Bucket Runtime Approval Candidates

- `entry_bucket_3`: `liquidity_bucket` / `liquidity_high` -> `candidate_tighten_or_exclude`
- `entry_bucket_4`: `overbought_bucket` / `overbought_normal` -> `candidate_tighten_or_exclude`
- `entry_bucket_5`: `score_band` / `score_60_62` -> `candidate_tighten_or_exclude`
- `entry_bucket_6`: `source_stage` / `scalp_entry_action_decision_snapshot` -> `candidate_tighten_or_exclude`
- `entry_bucket_9`: `strength_bucket` / `weak_strength_momentum` -> `candidate_tighten_or_exclude`

### Entry Bucket Workorders

- `entry_bucket_source_quality_1`: `chosen_action` / `NO_BUY_AI` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_2`: `exit_rule` / `scalp_soft_stop_pct` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_3`: `liquidity_bucket` / `liquidity_high` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_4`: `overbought_bucket` / `overbought_normal` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_5`: `score_band` / `score_60_62` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_6`: `source_stage` / `scalp_entry_action_decision_snapshot` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_7`: `stale_bucket` / `fresh` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_8`: `stale_bucket` / `stale_high` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_9`: `strength_bucket` / `weak_strength_momentum` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_10`: `time_bucket` / `time_1200_1400` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`

## Submit Bucket Attribution

- decision_authority: `adm_ldm_submit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'submit_rows': 90, 'bucket_count': 81, 'contract_gap_count': 0, 'workorder_count': 0, 'runtime_candidate_count': 0, 'quote_freshness_attribution_present': True, 'row_quote_freshness_attribution_present': False, 'sentinel_quote_freshness_attribution_present': True, 'sentinel_quote_freshness_attribution': {'source_report_type': 'buy_funnel_sentinel', 'decision_authority': 'submit_drought_quote_freshness_attribution_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'forbidden_uses': ['broker_order_submit', 'adm_ldm_training_input', 'general_threshold_ev_input', 'live_auto_promotion'], 'refresh_attempted_count': 20, 'refresh_applied_count': 16, 'still_latency_blocked_after_refresh_count': 9, 'latency_pass_recovered_count': 10, 'order_bundle_submitted_after_refresh_count': 3, 'refresh_subreason_counts': {'observer_quote_refresh_failed_invalid': 1, 'observer_quote_refresh_failed_stale': 12, 'ws_snapshot_refresh_failed_invalid': 1, 'ws_snapshot_refresh_failed_stale': 5, 'ws_snapshot_refresh_failed_missing': 7}, 'refresh_block_subreason_counts': {'observer_quote_refresh_failed_invalid': 1, 'observer_quote_refresh_failed_stale': 12, 'ws_snapshot_refresh_failed_invalid': 1, 'ws_snapshot_refresh_failed_stale': 5, 'ws_snapshot_refresh_failed_missing': 7}, 'latency_pass_recovered_downstream_counts': {'armed_expired_before_submit': 4, 'order_bundle_submitted': 3, 'upstream_block_after_latency_recovery': 3}, 'post_restart_window_policy': 'event_provenance_only'}, 'quote_freshness_resolution_counts': {'refresh_not_attempted_or_not_instrumented': 8, 'sim_submit_path_not_applicable': 82}, 'pre_submit_refresh_applied_counts': {'refresh_not_attempted_or_not_instrumented': 8, 'sim_submit_path_not_applicable': 82}, 'real_submitted_row_count': 5, 'missing_broker_order_key_count': 0, 'bot_history_broker_order_key_backfill_candidate_count': 0, 'bot_history_broker_order_key_backfill_full_coverage': False, 'bot_history_broker_order_key_exact_mapping_count': 0, 'bot_history_broker_order_key_exact_mapping_full_coverage': False, 'post_submit_provenance_join_resolution': 'no_gap_broker_order_key_present_or_no_missing_rows', 'bot_history_broker_order_key_backfill_candidates': [], 'missing_broker_order_key_rate': 0.0, 'post_submit_provenance_join_gap_raw': False, 'post_submit_provenance_join_gap': False}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 85 | 66 | -1.0696 | `keep_collecting` |
| `actual_order_submitted` | `true` | 5 | 0 | None | `keep_collecting` |
| `broker_order_forbidden` | `true` | 85 | 66 | -1.0696 | `keep_collecting` |
| `broker_order_forbidden` | `false` | 5 | 0 | None | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 29 | 25 | -0.9721 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 16 | 15 | -1.1935 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 8 | 4 | -0.8233 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 6 | 5 | -0.4104 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 6 | 4 | -1.3628 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 3 | 3 | -1.2125 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 3 | 1 | -4.5872 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 3 | 2 | -1.4185 | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_lt1s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=caution|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 2 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=pre_submit_liquidity_guard_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=latency_unknown|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=false` | 2 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 2 | 2 | 0.0512 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 2 | 2 | -0.4319 | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=caution|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_ok|latency=caution|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=pre_submit_liquidity_guard_block|revalidation=ok_or_unflagged|quote_age=quote_age_lt1s|liquidity=below_min_liquidity|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=latency_unknown|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | -1.1175 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | -0.0554 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_overbought_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=pullback_or_rebreak_not_confirmed|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | -4.5946 | `source_quality_workorder` |
| `latency_reason` | `scalp_live_simulator` | 82 | 66 | -1.0696 | `keep_collecting` |
| `latency_reason` | `caution_normal_entry_allowed` | 4 | 0 | None | `keep_collecting` |
| `latency_reason` | `latency_reason_unknown` | 3 | 0 | None | `source_quality_workorder` |
| `latency_reason` | `latency_other_danger_relief_normal_override` | 1 | 0 | None | `keep_collecting` |
| `latency_state` | `simulated` | 82 | 66 | -1.0696 | `keep_collecting` |
| `latency_state` | `caution` | 4 | 0 | None | `keep_collecting` |
| `latency_state` | `latency_unknown` | 3 | 0 | None | `source_quality_workorder` |
| `latency_state` | `danger` | 1 | 0 | None | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 53 | 43 | -1.0555 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 32 | 23 | -1.0959 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_not_available` | 5 | 0 | None | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 53 | 43 | -1.0555 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 29 | 23 | -1.0959 | `keep_collecting` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 8 | 0 | None | `source_quality_workorder` |
| `overbought_bucket` | `overbought_ok` | 70 | 55 | -1.0153 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 12 | 10 | -1.0159 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 86, 'source_row_count': 86, 'bucket_count': 29, 'joined_sample': 330, 'source_quality_adjusted_ev_pct': -1.3207, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 46 | 46 | -1.4868 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 5 | 5 | -1.536 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 4 | 4 | 0.8033 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 4 | 4 | -1.9067 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 3 | 3 | -1.5119 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 2 | 2 | 0.3776 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1 | 1 | -2.9015 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 0.0015 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 14 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_180_600s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_not_applicable_at_start` | 82 | 66 | -1.3207 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_180_600s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 3 | 0 | None | `hold_sample` |
| `holding_action` | `WAIT` | 75 | 61 | -1.2564 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 6 | 4 | -1.9067 | `candidate_tighten_or_exclude` |
| `holding_action` | `BUY` | 1 | 1 | -2.9015 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 4 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 82 | 66 | -1.3207 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 4 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 53 | 51 | -1.5475 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 7 | 5 | -1.536 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 4 | 4 | 0.8033 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos080_pos150` | 3 | 3 | -1.5119 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300_plus` | 2 | 2 | 0.3776 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 1 | 1 | 0.0015 | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 16 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- `holding_bucket_source_quality_1`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_2`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_3`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_4`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_5`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_6`: `held_bucket` / `held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_7`: `holding_action` / `WAIT` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_8`: `holding_action` / `holding_action_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_9`: `holding_source_stage` / `scalp_sim_holding_started` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_10`: `profit_band` / `profit_lt_neg070` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Exit Bucket Attribution

- decision_authority: `adm_ldm_exit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'exit_rows': 1882, 'source_row_count': 1882, 'bucket_count': 48, 'joined_sample': 605, 'source_quality_adjusted_ev_pct': -1.0616, 'source_quality_gate': 'pass', 'unknown_reason_counts': {'not_applicable': 2, 'join_gap': 8, 'missing_source_field': 1}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 36 | 36 | -1.0708 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 15 | 15 | -1.7879 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 14 | 14 | -0.5664 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 11 | 11 | -1.2063 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 8 | 8 | -2.6711 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 8 | 8 | -0.8075 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 5 | 5 | -0.6764 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 4 | 4 | -1.7525 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=daily_limit_up_immediate_exit|outcome=NEUTRAL|profit=profit_neg070_neg010` | 3 | 3 | -2.4166 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 2 | 2 | -0.6113 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 2 | 2 | -0.1613 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 2 | 2 | 0.5819 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 2 | 2 | 0.3776 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 1 | 1 | -0.07 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` | 1 | 1 | 0.88 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=daily_limit_up_immediate_exit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 1 | 1 | -1.759 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 1 | 1 | 0.0015 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 1 | 1 | -3.4591 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 1 | 1 | 2.0907 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 1 | 1 | 0.6824 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300` | 1 | 1 | -0.0413 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300_plus` | 1 | 1 | 4.8895 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_euphoria_context_noop|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown` | 67 | 0 | None | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown` | 1694 | 0 | None | `source_quality_workorder` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 52 | 52 | -0.8783 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 28 | 28 | -1.776 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 22 | 22 | -1.0799 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 15 | 15 | -0.5166 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 1765 | 4 | -0.3862 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 52 | 52 | -0.8783 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 35 | 35 | -1.3299 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 17 | 17 | -1.8683 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 9 | 9 | 0.6757 | `candidate_recovery_or_relax` |
| `exit_rule` | `daily_limit_up_immediate_exit` | 4 | 4 | -2.2522 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 4 | 4 | -0.3862 | `candidate_tighten_or_exclude` |
| `exit_rule` | `exit_rule_unknown` | 1761 | 0 | None | `source_quality_workorder` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 65 | 65 | -1.2498 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 52 | 52 | -0.8783 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 4 | 4 | -0.3862 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_euphoria_context_noop` | 67 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- `exit_bucket_source_quality_1`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_2`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_3`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_4`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_5`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_6`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_7`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_8`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_9`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=daily_limit_up_immediate_exit|outcome=NEUTRAL|profit=profit_neg070_neg010` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_10`: `combo_exit_result` / `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `incremental_notional_ev_pct`
- summary: `{'scale_in_rows': 3601, 'bucket_count': 687, 'edge_bucket_count': 0, 'actionable_bucket_count': 0, 'runtime_authority_blocked_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'arm_counts': {'AVG_DOWN': 2881, 'PYRAMID': 720}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_70p` | 2289 | 2289 | None | -0.4873 | 0.2018 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 809 | 809 | None | -0.5313 | 0.2052 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 248 | 248 | None | -0.809 | 0.0565 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 119 | 119 | None | -0.7841 | 0.0924 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 81 | 81 | None | 0.599 | 0.2963 | `hold_sample` |
| `ai_score_band` | `score_unknown` | 55 | 1 | None | None | None | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 3546 | 3546 | None | -0.505 | 0.1909 | `hold_sample` |
| `ai_score_source` | `sim_scale_in_source_not_scored` | 1 | 1 | None | None | None | `hold_sample` |
| `ai_score_source` | `stage_rule_backfilled` | 54 | 0 | None | None | None | `hold_sample` |
| `arm` | `AVG_DOWN` | 2881 | 2862 | None | -0.799 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 720 | 685 | None | 0.7229 | 0.9883 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 2040 | 2021 | None | -0.9601 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 841 | 841 | None | -0.4121 | 0.0 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 720 | 685 | None | 0.7229 | 0.9883 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 631 | 631 | None | 0.438 | 0.9937 | `hold_sample` |
| `blocker_reason` | `add_judgment_locked` | 185 | 185 | None | -0.4872 | 0.027 | `hold_sample` |
| `blocker_reason` | `low_broken` | 108 | 108 | None | -0.3997 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalping_buy_window_blocked` | 94 | 94 | None | -0.6128 | 0.0319 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.43)` | 93 | 93 | None | -1.43 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.48)` | 91 | 91 | None | -1.48 | 0.0 | `hold_sample` |

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
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 2 | 2 | -0.6113 | -0.815 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 2 | 2 | -0.1613 | -0.215 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_lt_neg070` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 2 | 0 | None | None | None | `hold_sample` |
| `confidence_band` | `confidence_070p` | 8 | 4 | -0.3862 | -0.515 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 6 | 3 | -0.435 | -0.58 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 2 | 1 | -0.24 | -0.32 | 0.0 | `hold_sample` |
| `overnight_action` | `SELL_TODAY` | 8 | 4 | -0.3862 | -0.515 | 0.0 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 4 | 4 | -0.3862 | -0.515 | 0.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 4 | 0 | None | None | None | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 8 | 4 | -0.3862 | -0.515 | 0.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 8 | 4 | -0.3862 | -0.515 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 4 | 2 | -0.6113 | -0.815 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 4 | 2 | -0.1613 | -0.215 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 8 | 4 | -0.3862 | -0.515 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 4 | 4 | -0.3862 | -0.515 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_decision` | 4 | 0 | None | None | None | `hold_sample` |
| `stage` | `exit` | 4 | 4 | -0.3862 | -0.515 | 0.0 | `hold_sample` |
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
