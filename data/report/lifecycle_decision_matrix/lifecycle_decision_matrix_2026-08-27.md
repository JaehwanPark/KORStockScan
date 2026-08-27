# Lifecycle Decision Matrix - 2026-08-27

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-08-27`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `1646`
- source_rows_total: `1864`
- retained_rows: `1646`
- dropped_rows_by_source: `{'dedupe': 218}`
- joined_rows: `927`
- policy_pass_count: `2`
- promote_ready_count: `0`
- entry_bucket_actionable_count: `0`
- entry_bucket_runtime_candidate_count: `0`
- holding_bucket_count/workorders: `13` / `7`
- exit_bucket_count/workorders: `21` / `7`
- scale_in_bucket_actionable_count: `0`
- scale_in_bucket_runtime_candidate_count: `0`
- overnight_bucket_actionable_count: `0`
- overnight_bucket_runtime_candidate_count: `0`
- lifecycle_flow_bucket_count: `36`
- lifecycle_flow_complete_count: `9`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `0` / `9` / `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0084`
- incomplete_flow_reason_counts: `{'missing_submit': 1005, 'missing_holding': 1053, 'missing_exit': 1053, 'missing_entry': 913, 'sim_record_id_only': 3, 'scale_in_noise_only': 909, 'candidate_id_only': 910, 'postclose_exit_without_entry': 4}`
- bucket_directed_sim_probe: `{'observed_row_count': 44, 'matched_row_count': 0, 'background_row_count': 44, 'matched_unique_source_bucket_count': 0, 'match_status_counts': {'no_match': 31, 'not_instrumented': 13}, 'matched_classification_state_counts': {}, 'primary_source': 'matched_bucket_directed_sim_probe_only', 'background_source': 'unmatched_or_policy_missing_sim_observation', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 1, 'route_counts': {'bounded_auxiliary_weight': 1, 'hold_sample': 4}, 'quality_counts': {'observational_only_pending_outcome': 1, 'hold_sample': 4}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 647 | 4 | 0.125 | 0.0025 | `hold_sample` | `NO_CHANGE` | False |
| `submit` | 62 | 10 | -1.6677 | 0.1613 | `pass` | `NO_CHANGE` | False |
| `holding` | 14 | 10 | -0.7832 | 0.7143 | `hold_sample` | `EXIT` | False |
| `scale_in` | 909 | 893 | -0.522 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 14 | 10 | -0.7832 | 0.7143 | `hold_sample` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 1066, 'complete_flow_count': 9, 'direct_sim_record_complete_flow_count': 0, 'adm_bridge_complete_flow_count': 9, 'fallback_complete_flow_count': 0, 'direct_flow_zero_diagnostic': {'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'direct_sim_record_flow_count': 3, 'direct_sim_record_incomplete_flow_count': 3, 'direct_sim_record_stage_coverage_counts': {}, 'direct_sim_record_incomplete_reason_counts': {'missing_entry': 3, 'missing_submit': 3, 'missing_holding': 3, 'missing_exit': 3, 'sim_record_id_only': 3, 'scale_in_noise_only': 3}, 'runtime_effect': False, 'decision_authority': 'ldm_direct_flow_diagnostic_only'}, 'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'incomplete_flow_count': 1057, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 1646, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0084, 'complete_flow_conversion_denominator': 13, 'complete_flow_conversion_rate': 0.6923, 'active_priority_incomplete_seed_count': 144, 'scale_in_followup_event_count': 909, 'scale_in_unique_flow_count': 676, 'scale_in_noise_flow_count': 909, 'denominator_exclusion_counts': {'scale_in_noise_flow_excluded': 909, 'active_priority_incomplete_seed_excluded': 144}, 'conversion_blocker_reason_counts': {'missing_entry': 4, 'missing_submit': 4, 'missing_holding': 4, 'candidate_id_only': 4, 'postclose_exit_without_entry': 4}, 'observation_seed_reason_counts': {'missing_submit': 1001, 'missing_holding': 1049, 'missing_exit': 1053, 'missing_entry': 909, 'sim_record_id_only': 3, 'scale_in_noise_only': 909, 'candidate_id_only': 906}, 'join_contract_blocked': False, 'bundle_ev_tuning_state': 'ready_for_bundle_ev_tuning', 'top_incomplete_reason': 'missing_holding', 'stage_identity': {'entry': {'source_row_count': 647, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 647}, 'identity_join_rate': 1.0}, 'submit': {'source_row_count': 62, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 62}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 14, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 14}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 909, 'identity_missing_count': 0, 'identity_quality_counts': {'exact_sim_record_id': 3, 'candidate_id': 906}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 14, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 10, 'candidate_id': 4}, 'identity_join_rate': 1.0}}, 'required_stage_source_counts': {'entry': 647, 'submit': 62, 'holding': 14, 'exit': 14}, 'incomplete_flow_reason_counts': {'missing_submit': 1005, 'missing_holding': 1053, 'missing_exit': 1053, 'missing_entry': 913, 'sim_record_id_only': 3, 'scale_in_noise_only': 909, 'candidate_id_only': 910, 'postclose_exit_without_entry': 4}, 'bucket_count': 36, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:c918fe4c6d` | 1 | 1 | -1.693 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:0953a2ca90` | 1 | 1 | -1.4345 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:5f1ed96255` | 1 | 1 | 0.529 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:d8bc4e1490` | 1 | 1 | 0.3563 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:57240f2428` | 1 | 1 | -1.8805 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:ffc82782b8` | 1 | 1 | 1.5492 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:54e4c3fdb0` | 1 | 1 | -1.8344 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:3fcedc0cd2` | 1 | 1 | 0.6331 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:ab7190eb7e` | 1 | 1 | -1.2106 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 689 | 674 | -0.8551 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 220 | 219 | 0.5033 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:672652b010` | 2 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:f9f18a2ca7` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_bloc:9844731079` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:28d2f4d6f7` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:c3e248a0f4` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:f2f2f3d14e` | 3 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:7b1e064efb` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:63006383a0` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:70a865069d` | 6 | 0 | None | `hold_sample` | `join_contract_blocked` |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 647, 'bucket_count': 151, 'actionable_bucket_count': 0, 'source_quality_blocked_bucket_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `NO_BUY_AI` | 291 | 4 | 0.125 | -0.03 | 0.75 | `hold_sample` |
| `chosen_action` | `BUY_DEFENSIVE` | 58 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 41 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_SOURCE_QUALITY` | 4 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_STALE` | 2 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `WAIT_REQUOTE` | 251 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_1000_1200` | 2 | 2 | 0.1237 | -1.185 | 0.5 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_ok|time=time_1400_close` | 1 | 1 | -0.7441 | 2.15 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 2 | 1 | 0.9967 | 0.1 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_1200_1400` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1200_1400` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1400_close` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_1200_1400` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_1400_close` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=blocked_ai_score|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1400_close` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=blocked_ai_score|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_1200_1400` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=blocked_ai_score|stale=fresh|liquidity=liquidity_not_available|overbought=overbought_normal|time=time_1000_1200` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=blocked_ai_score|stale=stale_watch|liquidity=liquidity_not_available|overbought=overbought_normal|time=time_1000_1200` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 2 | 0 | None | None | None | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `adm_ldm_submit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'submit_rows': 62, 'bucket_count': 88, 'contract_gap_count': 0, 'workorder_count': 0, 'runtime_candidate_count': 0, 'quote_freshness_attribution_present': True, 'row_quote_freshness_attribution_present': True, 'sentinel_quote_freshness_attribution_present': True, 'sentinel_quote_freshness_attribution': {'source_report_type': 'buy_funnel_sentinel', 'decision_authority': 'submit_drought_quote_freshness_attribution_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'forbidden_uses': ['broker_order_submit', 'adm_ldm_training_input', 'general_threshold_ev_input', 'live_auto_promotion'], 'refresh_attempted_count': 106, 'refresh_applied_count': 77, 'still_latency_blocked_after_refresh_count': 66, 'latency_pass_recovered_count': 27, 'order_bundle_submitted_after_refresh_count': 0, 'refresh_subreason_counts': {'observer_quote_refresh_failed_stale': 3, 'ws_snapshot_refresh_failed_input_snapshot_fresh': 284, 'ws_snapshot_refresh_failed_stale': 17}, 'refresh_block_subreason_counts': {'observer_quote_refresh_failed_stale': 3, 'ws_snapshot_refresh_failed_input_snapshot_fresh': 284, 'ws_snapshot_refresh_failed_stale': 17}, 'latency_pass_recovered_downstream_counts': {'entry_ai_authority_revalidation': 27}, 'post_restart_window_policy': 'event_provenance_only'}, 'quote_freshness_resolution_counts': {'refresh_attempted_unresolved': 17, 'refresh_failed_quote_stale': 5, 'refresh_not_attempted_or_not_instrumented': 6, 'refresh_resolved_quote_freshness': 20, 'sim_submit_path_not_applicable': 14}, 'pre_submit_refresh_applied_counts': {'refresh_attempted_not_applied': 22, 'refresh_not_attempted_or_not_instrumented': 6, 'sim_submit_path_not_applicable': 14, 'ws_snapshot_refresh_applied': 20}, 'real_submitted_row_count': 4, 'missing_broker_order_key_count': 0, 'bot_history_broker_order_key_backfill_candidate_count': 0, 'bot_history_broker_order_key_backfill_full_coverage': False, 'bot_history_broker_order_key_exact_mapping_count': 0, 'bot_history_broker_order_key_exact_mapping_full_coverage': False, 'post_submit_provenance_join_resolution': 'no_gap_broker_order_key_present_or_no_missing_rows', 'bot_history_broker_order_key_backfill_candidates': [], 'missing_broker_order_key_rate': 0.0, 'post_submit_provenance_join_gap_raw': False, 'post_submit_provenance_join_gap': False}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 58 | 10 | -1.6677 | `keep_collecting` |
| `actual_order_submitted` | `true` | 4 | 0 | None | `keep_collecting` |
| `broker_order_forbidden` | `true` | 58 | 10 | -1.6677 | `keep_collecting` |
| `broker_order_forbidden` | `false` | 4 | 0 | None | `keep_collecting` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_resolved_quote_freshness|fill=false|submitted=false` | 20 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_attempted_unresolved|fill=false|submitted=false` | 17 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_failed_quote_stale|fill=false|submitted=false` | 5 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 5 | 2 | 0.539 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 5 | 5 | -2.6556 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 3 | 2 | -0.2889 | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=caution|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 2 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=entry_submit_revalidation_block|revalidation=warning_observed_mark_gap_unresolved|quote_age=quote_age_3_10s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=latency_unknown|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=entry_submit_revalidation_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=latency_unknown|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=caution|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=safe|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | -3.8986 | `source_quality_workorder` |
| `latency_reason` | `spread_above_caution_below_guard_cap` | 15 | 0 | None | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 14 | 10 | -1.6677 | `keep_collecting` |
| `latency_reason` | `ws_age_too_high` | 14 | 0 | None | `keep_collecting` |
| `latency_reason` | `spread_too_wide` | 10 | 0 | None | `keep_collecting` |
| `latency_reason` | `caution_normal_entry_allowed` | 3 | 0 | None | `keep_collecting` |
| `latency_reason` | `ws_age_too_high,spread_too_wide` | 3 | 0 | None | `keep_collecting` |
| `latency_reason` | `latency_reason_unknown` | 2 | 0 | None | `source_quality_workorder` |
| `latency_reason` | `safe_normal_entry_allowed` | 1 | 0 | None | `keep_collecting` |
| `latency_state` | `danger` | 42 | 0 | None | `keep_collecting` |
| `latency_state` | `simulated` | 14 | 10 | -1.6677 | `keep_collecting` |
| `latency_state` | `caution` | 3 | 0 | None | `keep_collecting` |
| `latency_state` | `latency_unknown` | 2 | 0 | None | `source_quality_workorder` |
| `latency_state` | `safe` | 1 | 0 | None | `keep_collecting` |
| `liquidity_bucket` | `liquidity_not_available` | 48 | 0 | None | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 8 | 4 | 0.125 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 6 | 6 | -2.8628 | `keep_collecting` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 48 | 0 | None | `source_quality_workorder` |
| `liquidity_guard_action` | `would_pass` | 8 | 4 | 0.125 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 6 | 6 | -2.8628 | `keep_collecting` |
| `overbought_bucket` | `overbought_not_available` | 48 | 0 | None | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 14 | 10 | -1.6677 | `keep_collecting` |
| `overbought_guard_action` | `overbought_guard_unknown` | 48 | 0 | None | `source_quality_workorder` |
| `overbought_guard_action` | `would_pass` | 14 | 10 | -1.6677 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `refresh_age_not_instrumented` | 23 | 0 | None | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 14, 'source_row_count': 14, 'bucket_count': 13, 'joined_sample': 50, 'source_quality_adjusted_ev_pct': -0.7832, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 7, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 4 | 4 | -0.7074 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 3 | 3 | 0.3239 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 2 | 2 | -2.1407 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | -1.693 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 4 | 0 | None | `hold_sample` |
| `held_bucket` | `held_not_applicable_at_start` | 14 | 10 | -0.7832 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 13 | 9 | -0.6821 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 1 | 1 | -1.693 | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 14 | 10 | -0.7832 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 5 | 5 | -0.9045 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 3 | 3 | 0.3239 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_lt_neg070` | 2 | 2 | -2.1407 | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 4 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- `holding_bucket_source_quality_1`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_2`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_3`: `held_bucket` / `held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_4`: `holding_action` / `WAIT` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_5`: `holding_source_stage` / `scalp_sim_holding_started` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_6`: `profit_band` / `profit_neg010_pos080` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_7`: `profit_band` / `profit_pos150_pos300` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Exit Bucket Attribution

- decision_authority: `adm_ldm_exit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'exit_rows': 14, 'source_row_count': 14, 'bucket_count': 21, 'joined_sample': 50, 'source_quality_adjusted_ev_pct': -0.7832, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 7, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 3 | 3 | -1.0724 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 2 | 2 | -0.2887 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | -2.8469 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 1 | 1 | -1.4345 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 1 | 1 | -1.8344 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 1 | 1 | 0.529 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 1 | 1 | 1.5492 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=scalp_sim_panic_context_warning_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 4 | 0 | None | `hold_sample` |
| `exit_outcome` | `NEUTRAL` | 4 | 4 | -1.1629 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 3 | 3 | -0.804 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 3 | 3 | -0.2562 | `hold_no_edge` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 4 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 8 | 8 | -0.4439 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 2 | 2 | -2.1407 | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_context_warning_not_applicable` | 4 | 0 | None | `hold_sample` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 10 | 10 | -0.7832 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 4 | 0 | None | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 5 | 5 | -0.9045 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 3 | 3 | 0.3239 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_lt_neg070` | 2 | 2 | -2.1407 | `hold_sample` |
| `profit_band` | `profit_not_applicable_context_noop` | 4 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- `exit_bucket_source_quality_1`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_2`: `exit_outcome` / `NEUTRAL` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_3`: `exit_outcome` / `GOOD_EXIT` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_4`: `exit_rule` / `scalp_trailing_take_profit` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_5`: `exit_source_stage` / `sim_post_sell_evaluation` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_6`: `profit_band` / `profit_neg010_pos080` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_7`: `profit_band` / `profit_pos150_pos300` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `incremental_notional_ev_pct`
- summary: `{'scale_in_rows': 909, 'bucket_count': 129, 'edge_bucket_count': 0, 'actionable_bucket_count': 0, 'runtime_authority_blocked_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'arm_counts': {'PYRAMID': 220, 'AVG_DOWN': 689}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 884 | 884 | None | -0.6192 | 0.2376 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 4 | 4 | None | 1.995 | 1.0 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 2 | 2 | None | 1.81 | 1.0 | `hold_sample` |
| `ai_score_band` | `score_unknown` | 18 | 2 | None | 2.15 | 1.0 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 1 | 1 | None | 0.78 | 1.0 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 461 | 461 | None | -0.7611 | 0.269 | `hold_sample` |
| `ai_score_source` | `live` | 178 | 178 | None | -0.1634 | 0.3989 | `hold_sample` |
| `ai_score_source` | `not_evaluated_no_ai_score_source` | 173 | 173 | None | -0.5673 | 0.052 | `hold_sample` |
| `ai_score_source` | `holding_ai_not_called` | 63 | 63 | None | -1.0741 | 0.0794 | `hold_sample` |
| `ai_score_source` | `prior_valid` | 15 | 15 | None | 0.5553 | 0.4667 | `hold_sample` |
| `ai_score_source` | `sim_scale_in_source_not_scored` | 2 | 2 | None | 2.15 | 1.0 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 1 | 1 | None | 2.45 | 1.0 | `hold_sample` |
| `ai_score_source` | `stage_rule_backfilled` | 16 | 0 | None | None | None | `hold_sample` |
| `arm` | `AVG_DOWN` | 689 | 674 | None | -0.9373 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 220 | 219 | None | 0.4537 | 1.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 684 | 669 | None | -0.9203 | 0.0 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 220 | 219 | None | 0.4537 | 1.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 5 | 5 | None | -3.208 | 0.0 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 179 | 179 | None | 0.2092 | 1.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.84)` | 53 | 53 | None | -0.84 | 0.0 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `adm_ldm_overnight_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'observation_state': 'no_natural_sample', 'observation_reason': 'pipeline_artifact_present_without_overnight_activity', 'source_artifact_present': True, 'overnight_rows': 0, 'bucket_count': 0, 'actionable_bucket_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'status_counts': {}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |

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
