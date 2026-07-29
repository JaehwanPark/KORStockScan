# Lifecycle Decision Matrix - 2026-07-29

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-29`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `196`
- source_rows_total: `432`
- retained_rows: `196`
- dropped_rows_by_source: `{'dedupe': 236}`
- joined_rows: `94`
- policy_pass_count: `1`
- promote_ready_count: `0`
- entry_bucket_actionable_count: `0`
- entry_bucket_runtime_candidate_count: `0`
- holding_bucket_count/workorders: `12` / `3`
- exit_bucket_count/workorders: `25` / `5`
- scale_in_bucket_actionable_count: `0`
- scale_in_bucket_runtime_candidate_count: `0`
- overnight_bucket_actionable_count: `0`
- overnight_bucket_runtime_candidate_count: `0`
- lifecycle_flow_bucket_count: `21`
- lifecycle_flow_complete_count: `3`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `0` / `3` / `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0224`
- incomplete_flow_reason_counts: `{'missing_holding': 130, 'missing_exit': 120, 'missing_submit': 114, 'missing_entry': 90, 'candidate_id_only': 95, 'scale_in_noise_only': 79, 'sim_record_id_only': 4, 'postclose_exit_without_entry': 11}`
- bucket_directed_sim_probe: `{'observed_row_count': 43, 'matched_row_count': 0, 'background_row_count': 43, 'matched_unique_source_bucket_count': 0, 'match_status_counts': {'no_match': 18, 'not_instrumented': 23, 'policy_disabled': 2}, 'matched_classification_state_counts': {}, 'primary_source': 'matched_bucket_directed_sim_probe_only', 'background_source': 'unmatched_or_policy_missing_sim_observation', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 0, 'route_counts': {'bounded_auxiliary_weight': 1, 'hold_sample': 4}, 'quality_counts': {'observational_only_pending_outcome': 1, 'hold_sample': 4}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 76 | 3 | -0.8198 | 0.0118 | `hold_sample` | `WAIT_REQUOTE` | False |
| `submit` | 20 | 3 | -0.8198 | 0.045 | `hold_sample` | `NO_CHANGE` | False |
| `holding` | 4 | 3 | -0.8757 | 0.225 | `hold_sample` | `EXIT` | False |
| `scale_in` | 79 | 78 | -0.0975 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 17 | 7 | -0.7185 | 0.2882 | `hold_sample` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 134, 'complete_flow_count': 3, 'direct_sim_record_complete_flow_count': 0, 'adm_bridge_complete_flow_count': 3, 'fallback_complete_flow_count': 0, 'direct_flow_zero_diagnostic': {'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'direct_sim_record_flow_count': 4, 'direct_sim_record_incomplete_flow_count': 4, 'direct_sim_record_stage_coverage_counts': {'holding': 1, 'exit': 1}, 'direct_sim_record_incomplete_reason_counts': {'missing_entry': 4, 'missing_submit': 4, 'sim_record_id_only': 4, 'postclose_exit_without_entry': 1, 'missing_holding': 3, 'missing_exit': 3, 'scale_in_noise_only': 3}, 'runtime_effect': False, 'decision_authority': 'ldm_direct_flow_diagnostic_only'}, 'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'incomplete_flow_count': 131, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 196, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0224, 'complete_flow_conversion_denominator': 14, 'complete_flow_conversion_rate': 0.2143, 'active_priority_incomplete_seed_count': 41, 'scale_in_followup_event_count': 79, 'scale_in_unique_flow_count': 62, 'scale_in_noise_flow_count': 79, 'denominator_exclusion_counts': {'scale_in_noise_flow_excluded': 79, 'active_priority_incomplete_seed_excluded': 41}, 'conversion_blocker_reason_counts': {'missing_entry': 11, 'missing_submit': 11, 'sim_record_id_only': 1, 'postclose_exit_without_entry': 11, 'missing_holding': 10, 'candidate_id_only': 10}, 'observation_seed_reason_counts': {'missing_holding': 120, 'missing_exit': 120, 'missing_submit': 103, 'missing_entry': 79, 'candidate_id_only': 85, 'scale_in_noise_only': 79, 'sim_record_id_only': 3}, 'join_contract_blocked': False, 'bundle_ev_tuning_state': 'ready_for_bundle_ev_tuning', 'top_incomplete_reason': 'missing_holding', 'stage_identity': {'entry': {'source_row_count': 76, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 67, 'candidate_id': 9}, 'identity_join_rate': 1.0}, 'submit': {'source_row_count': 20, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 20}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 4, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 3, 'exact_sim_record_id': 1}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 79, 'identity_missing_count': 0, 'identity_quality_counts': {'candidate_id': 76, 'exact_sim_record_id': 3}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 17, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 6, 'exact_sim_record_id': 1, 'candidate_id': 10}, 'identity_join_rate': 1.0}}, 'required_stage_source_counts': {'entry': 76, 'submit': 20, 'holding': 4, 'exit': 17}, 'incomplete_flow_reason_counts': {'missing_holding': 130, 'missing_exit': 120, 'missing_submit': 114, 'missing_entry': 90, 'candidate_id_only': 95, 'scale_in_noise_only': 79, 'sim_record_id_only': 4, 'postclose_exit_without_entry': 11}, 'bucket_count': 21, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:f44ea1e4fd` | 2 | 2 | -1.28 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:cb6ed22b69` | 1 | 1 | 0.33 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 41 | 41 | 0.413 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 38 | 37 | -0.6631 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:62b3401904` | 1 | 1 | -0.1725 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:661dd5007a` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:306834dafc` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:01a26e930a` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:8a9ce220d7` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:81a1a398fd` | 4 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:07390fbd3e` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:6f0786a34b` | 5 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:07acd7bc08` | 2 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:33cafb7fc7` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:43870ece59` | 4 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:5fc5abcf3e` | 2 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:2ee469a4fb` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:53da8da968` | 8 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:5721087451` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:be414ae5c3` | 8 | 0 | None | `hold_sample` | `join_contract_blocked` |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 76, 'bucket_count': 67, 'actionable_bucket_count': 0, 'source_quality_blocked_bucket_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 11 | 3 | -0.8198 | -0.89 | 0.3333 | `hold_sample` |
| `chosen_action` | `ALLOW_LEVEL1_RISK_OFF_ENTRY` | 9 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `BUY_DEFENSIVE` | 8 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `BUY_NOW` | 1 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `NO_BUY_AI` | 24 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_STALE` | 1 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `WAIT_REQUOTE` | 22 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1000_1200` | 8 | 2 | -0.6883 | -1.42 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_0900_1000` | 1 | 1 | -1.083 | 0.17 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_watch|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_0900_1000` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1000_1200` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_sim_panic_level1_entry_observed|stale=fresh_or_unflagged|liquidity=liquidity_state_normal|overbought=panic_entry_overbought_not_applicable|time=time_1000_1200` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=stale_watch|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1400_close` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=scalp_entry_action_decision_snapshot|stale=stale_watch|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1400_close` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1400_close` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=stale_watch|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_0900_1000` | 3 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=stale_watch|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1400_close` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=blocked_ai_score|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=blocked_ai_score|stale=fresh|liquidity=liquidity_not_available|overbought=overbought_normal|time=time_0900_1000` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=blocked_ai_score|stale=fresh|liquidity=liquidity_not_available|overbought=overbought_normal|time=time_1000_1200` | 4 | 0 | None | None | None | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `adm_ldm_submit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'submit_rows': 20, 'bucket_count': 73, 'contract_gap_count': 0, 'workorder_count': 0, 'runtime_candidate_count': 0, 'quote_freshness_attribution_present': True, 'row_quote_freshness_attribution_present': True, 'sentinel_quote_freshness_attribution_present': True, 'sentinel_quote_freshness_attribution': {'source_report_type': 'buy_funnel_sentinel', 'decision_authority': 'submit_drought_quote_freshness_attribution_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'forbidden_uses': ['broker_order_submit', 'adm_ldm_training_input', 'general_threshold_ev_input', 'live_auto_promotion'], 'refresh_attempted_count': 5, 'refresh_applied_count': 1, 'still_latency_blocked_after_refresh_count': 3, 'latency_pass_recovered_count': 1, 'order_bundle_submitted_after_refresh_count': 0, 'refresh_subreason_counts': {'ws_snapshot_refresh_failed_input_snapshot_fresh': 3}, 'refresh_block_subreason_counts': {'ws_snapshot_refresh_failed_input_snapshot_fresh': 3}, 'latency_pass_recovered_downstream_counts': {'no_downstream_event': 1}, 'post_restart_window_policy': 'event_provenance_only'}, 'quote_freshness_resolution_counts': {'refresh_attempted_unresolved': 4, 'refresh_not_attempted_or_not_instrumented': 11, 'refresh_resolved_quote_freshness': 2, 'sim_submit_path_not_applicable': 3}, 'pre_submit_refresh_applied_counts': {'refresh_attempted_not_applied': 4, 'refresh_not_attempted_or_not_instrumented': 11, 'sim_submit_path_not_applicable': 3, 'ws_snapshot_refresh_applied': 2}, 'real_submitted_row_count': 10, 'missing_broker_order_key_count': 0, 'bot_history_broker_order_key_backfill_candidate_count': 0, 'bot_history_broker_order_key_backfill_full_coverage': False, 'bot_history_broker_order_key_exact_mapping_count': 0, 'bot_history_broker_order_key_exact_mapping_full_coverage': False, 'post_submit_provenance_join_resolution': 'no_gap_broker_order_key_present_or_no_missing_rows', 'bot_history_broker_order_key_backfill_candidates': [], 'missing_broker_order_key_rate': 0.0, 'post_submit_provenance_join_gap_raw': False, 'post_submit_provenance_join_gap': False}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 10 | 3 | -0.8198 | `keep_collecting` |
| `actual_order_submitted` | `true` | 10 | 0 | None | `keep_collecting` |
| `broker_order_forbidden` | `false` | 10 | 0 | None | `keep_collecting` |
| `broker_order_forbidden` | `true` | 10 | 3 | -0.8198 | `keep_collecting` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=caution|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 5 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_attempted_unresolved|fill=false|submitted=false` | 4 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 3 | 3 | -0.8198 | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_resolved_quote_freshness|fill=false|submitted=false` | 2 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_lt1s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=caution|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 2 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=entry_submit_revalidation_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=latency_unknown|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=safe|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_lt1s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `latency_reason` | `caution_normal_entry_allowed` | 7 | 0 | None | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 3 | 3 | -0.8198 | `keep_collecting` |
| `latency_reason` | `spread_above_caution_below_guard_cap` | 3 | 0 | None | `keep_collecting` |
| `latency_reason` | `ws_age_too_high` | 2 | 0 | None | `keep_collecting` |
| `latency_reason` | `latency_reason_unknown` | 1 | 0 | None | `source_quality_workorder` |
| `latency_reason` | `latency_spread_relief_normal_override` | 1 | 0 | None | `keep_collecting` |
| `latency_reason` | `latency_true_ofi_false_negative_direct_canary_normal_override` | 1 | 0 | None | `keep_collecting` |
| `latency_reason` | `safe_normal_entry_allowed` | 1 | 0 | None | `keep_collecting` |
| `latency_reason` | `spread_too_wide` | 1 | 0 | None | `keep_collecting` |
| `latency_state` | `danger` | 8 | 0 | None | `keep_collecting` |
| `latency_state` | `caution` | 7 | 0 | None | `keep_collecting` |
| `latency_state` | `simulated` | 3 | 3 | -0.8198 | `keep_collecting` |
| `latency_state` | `latency_unknown` | 1 | 0 | None | `source_quality_workorder` |
| `latency_state` | `safe` | 1 | 0 | None | `keep_collecting` |
| `liquidity_bucket` | `liquidity_not_available` | 17 | 0 | None | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 3 | 3 | -0.8198 | `keep_collecting` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 17 | 0 | None | `source_quality_workorder` |
| `liquidity_guard_action` | `would_pass` | 3 | 3 | -0.8198 | `keep_collecting` |
| `overbought_bucket` | `overbought_not_available` | 17 | 0 | None | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 3 | 3 | -0.8198 | `keep_collecting` |
| `overbought_guard_action` | `overbought_guard_unknown` | 17 | 0 | None | `source_quality_workorder` |
| `overbought_guard_action` | `would_pass` | 3 | 3 | -0.8198 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `refresh_age_not_instrumented` | 15 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 3 | 3 | -0.8198 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `refresh_age_lt1s` | 2 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_applied` | `refresh_not_attempted_or_not_instrumented` | 11 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_applied` | `refresh_attempted_not_applied` | 4 | 0 | None | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 4, 'source_row_count': 4, 'bucket_count': 12, 'joined_sample': 15, 'source_quality_adjusted_ev_pct': -0.8757, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 3, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 2 | 2 | -1.0724 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | -0.4823 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_not_applicable_at_start` | 3 | 3 | -0.8757 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `holding_action` | `WAIT` | 3 | 3 | -0.8757 | `candidate_tighten_or_exclude` |
| `holding_action` | `SELL_TODAY` | 1 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 3 | 3 | -0.8757 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 1 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 2 | 2 | -1.0724 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 1 | 1 | -0.4823 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- `holding_bucket_source_quality_1`: `held_bucket` / `held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_2`: `holding_action` / `WAIT` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_3`: `holding_source_stage` / `scalp_sim_holding_started` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Exit Bucket Attribution

- decision_authority: `adm_ldm_exit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'exit_rows': 17, 'source_row_count': 17, 'bucket_count': 25, 'joined_sample': 35, 'source_quality_adjusted_ev_pct': -0.7185, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 5, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 2 | 2 | -1.28 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 1 | 1 | -0.1725 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 1 | 1 | 0.33 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 1 | 1 | -1.4093 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 1 | 1 | -0.7356 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 1 | 1 | -0.4823 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_euphoria_context_noop|rule=scalp_sim_euphoria_context_noop_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 10 | 0 | None | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 3 | 3 | -0.7433 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 2 | 2 | -0.9458 | `hold_sample` |
| `exit_outcome` | `COMPLETED` | 1 | 1 | -0.1725 | `hold_sample` |
| `exit_outcome` | `NEUTRAL` | 1 | 1 | -0.7356 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 10 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 3 | 3 | -0.7433 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 2 | 2 | -1.0724 | `hold_sample` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 1 | 1 | -0.1725 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 1 | 1 | -0.4823 | `hold_sample` |
| `exit_rule` | `scalp_sim_euphoria_context_noop_not_applicable` | 10 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 3 | 3 | -0.7433 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 3 | 3 | -0.8757 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 1 | 1 | -0.1725 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_euphoria_context_noop` | 10 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 4 | 4 | -1.1762 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 2 | 2 | -0.0761 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 1 | 1 | -0.1725 | `hold_sample` |
| `profit_band` | `profit_not_applicable_context_noop` | 10 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- `exit_bucket_source_quality_1`: `exit_outcome` / `outcome_not_applicable_partial_exit` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_2`: `exit_rule` / `scalp_sim_panic_lifecycle_partial_exit` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_3`: `exit_source_stage` / `scalp_sim_partial_sell_order_assumed_filled` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_4`: `exit_source_stage` / `sim_post_sell_evaluation` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_5`: `profit_band` / `profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `incremental_notional_ev_pct`
- summary: `{'scale_in_rows': 79, 'bucket_count': 49, 'edge_bucket_count': 0, 'actionable_bucket_count': 0, 'runtime_authority_blocked_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'arm_counts': {'AVG_DOWN': 38, 'PYRAMID': 41}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 78 | 78 | None | -0.1468 | 0.5256 | `hold_sample` |
| `ai_score_band` | `score_unknown` | 1 | 0 | None | None | None | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 49 | 49 | None | 0.1986 | 0.7959 | `hold_sample` |
| `ai_score_source` | `not_evaluated_no_ai_score_source` | 23 | 23 | None | -0.7717 | 0.0435 | `hold_sample` |
| `ai_score_source` | `live` | 3 | 3 | None | -0.5433 | 0.0 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 3 | 3 | None | -0.6 | 0.3333 | `hold_sample` |
| `ai_score_source` | `stage_rule_backfilled` | 1 | 0 | None | None | None | `hold_sample` |
| `arm` | `PYRAMID` | 41 | 41 | None | 0.37 | 1.0 | `hold_sample` |
| `arm` | `AVG_DOWN` | 38 | 37 | None | -0.7195 | 0.0 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 41 | 41 | None | 0.37 | 1.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 38 | 37 | None | -0.7195 | 0.0 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 39 | 39 | None | 0.3679 | 1.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.23)` | 7 | 7 | None | -0.23 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.97)` | 6 | 6 | None | -0.97 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.39)` | 4 | 4 | None | -0.39 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.16)` | 4 | 4 | None | -1.16 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 3 | 3 | None | -0.6 | 0.3333 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.15)` | 2 | 2 | None | -0.15 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.55)` | 2 | 2 | None | -0.55 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.79)` | 2 | 2 | None | -0.79 | 0.0 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `adm_ldm_overnight_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'overnight_rows': 2, 'bucket_count': 15, 'actionable_bucket_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'status_counts': {'HOLD_OVERNIGHT': 1, 'SELL_TODAY': 1}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 1 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 1 | 0 | None | None | None | `hold_sample` |
| `confidence_band` | `confidence_070p` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `overnight_action` | `SELL_TODAY` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 1 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 1 | 0 | None | None | None | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 1 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_decision` | 1 | 0 | None | None | None | `hold_sample` |
| `stage` | `exit` | 1 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `stage` | `holding` | 1 | 0 | None | None | None | `hold_sample` |

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
