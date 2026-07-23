# Lifecycle Decision Matrix - 2026-07-23

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-23`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `353`
- source_rows_total: `1290`
- retained_rows: `353`
- dropped_rows_by_source: `{'dedupe': 937}`
- joined_rows: `106`
- policy_pass_count: `1`
- promote_ready_count: `0`
- entry_bucket_actionable_count: `0`
- entry_bucket_runtime_candidate_count: `0`
- holding_bucket_count/workorders: `10` / `0`
- exit_bucket_count/workorders: `19` / `5`
- scale_in_bucket_actionable_count: `0`
- scale_in_bucket_runtime_candidate_count: `0`
- overnight_bucket_actionable_count: `0`
- overnight_bucket_runtime_candidate_count: `0`
- lifecycle_flow_bucket_count: `30`
- lifecycle_flow_complete_count: `7`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `0` / `7` / `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0345`
- incomplete_flow_reason_counts: `{'missing_holding': 193, 'missing_exit': 179, 'missing_submit': 159, 'missing_entry': 118, 'candidate_id_only': 115, 'scale_in_noise_only': 97, 'sim_record_id_only': 9, 'postclose_exit_without_entry': 17}`
- bucket_directed_sim_probe: `{'observed_row_count': 68, 'matched_row_count': 0, 'background_row_count': 68, 'matched_unique_source_bucket_count': 0, 'match_status_counts': {'no_match': 42, 'not_instrumented': 24, 'policy_disabled': 2}, 'matched_classification_state_counts': {}, 'primary_source': 'matched_bucket_directed_sim_probe_only', 'background_source': 'unmatched_or_policy_missing_sim_observation', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 1, 'route_counts': {'bounded_auxiliary_weight': 1, 'hold_sample': 4}, 'quality_counts': {'observational_only_pending_outcome': 1, 'hold_sample': 4}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 171 | 0 | None | 0.0 | `hold_sample` | `NO_CHANGE` | False |
| `submit` | 47 | 0 | None | 0.0 | `hold_sample` | `NO_CHANGE` | False |
| `holding` | 13 | 0 | None | 0.0 | `hold_sample` | `NO_CHANGE` | False |
| `scale_in` | 97 | 97 | -0.5735 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 25 | 9 | -0.8136 | 0.324 | `hold_sample` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 203, 'complete_flow_count': 7, 'direct_sim_record_complete_flow_count': 0, 'adm_bridge_complete_flow_count': 7, 'fallback_complete_flow_count': 0, 'direct_flow_zero_diagnostic': {'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'direct_sim_record_flow_count': 9, 'direct_sim_record_incomplete_flow_count': 9, 'direct_sim_record_stage_coverage_counts': {'holding': 1, 'exit': 1}, 'direct_sim_record_incomplete_reason_counts': {'missing_entry': 9, 'missing_submit': 9, 'sim_record_id_only': 9, 'postclose_exit_without_entry': 1, 'missing_holding': 8, 'missing_exit': 8, 'scale_in_noise_only': 8}, 'runtime_effect': False, 'decision_authority': 'ldm_direct_flow_diagnostic_only'}, 'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'incomplete_flow_count': 196, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 353, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0345, 'complete_flow_conversion_denominator': 28, 'complete_flow_conversion_rate': 0.25, 'active_priority_incomplete_seed_count': 78, 'scale_in_followup_event_count': 97, 'scale_in_unique_flow_count': 90, 'scale_in_noise_flow_count': 97, 'denominator_exclusion_counts': {'scale_in_noise_flow_excluded': 97, 'active_priority_incomplete_seed_excluded': 78}, 'conversion_blocker_reason_counts': {'missing_entry': 21, 'missing_holding': 20, 'missing_exit': 4, 'missing_submit': 17, 'sim_record_id_only': 1, 'postclose_exit_without_entry': 17, 'candidate_id_only': 16}, 'observation_seed_reason_counts': {'missing_holding': 173, 'missing_exit': 175, 'missing_submit': 142, 'missing_entry': 97, 'candidate_id_only': 99, 'scale_in_noise_only': 97, 'sim_record_id_only': 8}, 'join_contract_blocked': False, 'bundle_ev_tuning_state': 'ready_for_bundle_ev_tuning', 'top_incomplete_reason': 'missing_holding', 'stage_identity': {'entry': {'source_row_count': 171, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 161, 'candidate_id': 10}, 'identity_join_rate': 1.0}, 'submit': {'source_row_count': 47, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 47}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 13, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 12, 'exact_sim_record_id': 1}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 97, 'identity_missing_count': 0, 'identity_quality_counts': {'candidate_id': 89, 'exact_sim_record_id': 8}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 25, 'identity_missing_count': 0, 'identity_quality_counts': {'exact_sim_record_id': 1, 'candidate_id': 16, 'entry_adm_bridge_key': 8}, 'identity_join_rate': 1.0}}, 'required_stage_source_counts': {'entry': 171, 'submit': 47, 'holding': 13, 'exit': 25}, 'incomplete_flow_reason_counts': {'missing_holding': 193, 'missing_exit': 179, 'missing_submit': 159, 'missing_entry': 118, 'candidate_id_only': 115, 'scale_in_noise_only': 97, 'sim_record_id_only': 9, 'postclose_exit_without_entry': 17}, 'bucket_count': 30, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:ac760bc3a4` | 6 | 6 | -0.8717 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:57aa592422` | 1 | 1 | -0.96 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 96 | 96 | -0.5823 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:62b3401904` | 1 | 1 | -0.1725 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 1 | 1 | 0.27 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:f2ff621987` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:54101985e8` | 2 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:81a1a398fd` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:07390fbd3e` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:6ce17fe9aa` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:8ebf65e20e` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:7b1e064efb` | 5 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:162c1ba90b` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:70a865069d` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:ab9f8a4c2e` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:34865a272b` | 2 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:7b79da9187` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:d7f4f26201` | 2 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:5566b1f38e` | 7 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:c69a7be5bd` | 12 | 0 | None | `hold_sample` | `join_contract_blocked` |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 171, 'bucket_count': 69, 'actionable_bucket_count': 0, 'source_quality_blocked_bucket_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `ALLOW_LEVEL1_RISK_OFF_ENTRY` | 10 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `BUY_DEFENSIVE` | 8 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `NO_BUY_AI` | 75 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 1 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_SOURCE_QUALITY` | 2 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `WAIT_REQUOTE` | 75 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1000_1200` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1400_close` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=stale_watch|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1000_1200` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=stale_watch|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1200_1400` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=stale_watch|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1400_close` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1400_close` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=ai_confirmed|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=ai_confirmed|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 5 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=ai_confirmed|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=ai_confirmed|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_1400_close` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=ai_confirmed|stale=stale_high|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=blocked_ai_score|stale=stale_block|liquidity=liquidity_not_available|overbought=overbought_normal|time=time_0900_1000` | 2 | 0 | None | None | None | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `adm_ldm_submit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'submit_rows': 47, 'bucket_count': 84, 'contract_gap_count': 0, 'workorder_count': 0, 'runtime_candidate_count': 0, 'quote_freshness_attribution_present': True, 'row_quote_freshness_attribution_present': True, 'sentinel_quote_freshness_attribution_present': True, 'sentinel_quote_freshness_attribution': {'source_report_type': 'buy_funnel_sentinel', 'decision_authority': 'submit_drought_quote_freshness_attribution_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'forbidden_uses': ['broker_order_submit', 'adm_ldm_training_input', 'general_threshold_ev_input', 'live_auto_promotion'], 'refresh_attempted_count': 23, 'refresh_applied_count': 22, 'still_latency_blocked_after_refresh_count': 1, 'latency_pass_recovered_count': 4, 'order_bundle_submitted_after_refresh_count': 2, 'refresh_subreason_counts': {'ws_snapshot_refresh_failed_stale': 1}, 'refresh_block_subreason_counts': {'ws_snapshot_refresh_failed_stale': 1}, 'latency_pass_recovered_downstream_counts': {'budget_pass_no_submit_event': 1, 'order_bundle_submitted': 2, 'price_guard_or_revalidation': 1}, 'post_restart_window_policy': 'event_provenance_only'}, 'quote_freshness_resolution_counts': {'refresh_failed_quote_stale': 1, 'refresh_not_attempted_or_not_instrumented': 14, 'refresh_resolved_quote_freshness': 20, 'sim_submit_path_not_applicable': 12}, 'pre_submit_refresh_applied_counts': {'refresh_attempted_not_applied': 1, 'refresh_not_attempted_or_not_instrumented': 14, 'sim_submit_path_not_applicable': 12, 'ws_snapshot_refresh_applied': 20}, 'real_submitted_row_count': 12, 'missing_broker_order_key_count': 0, 'bot_history_broker_order_key_backfill_candidate_count': 0, 'bot_history_broker_order_key_backfill_full_coverage': False, 'bot_history_broker_order_key_exact_mapping_count': 0, 'bot_history_broker_order_key_exact_mapping_full_coverage': False, 'post_submit_provenance_join_resolution': 'no_gap_broker_order_key_present_or_no_missing_rows', 'bot_history_broker_order_key_backfill_candidates': [], 'missing_broker_order_key_rate': 0.0, 'post_submit_provenance_join_gap_raw': False, 'post_submit_provenance_join_gap': False}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 35 | 0 | None | `keep_collecting` |
| `actual_order_submitted` | `true` | 12 | 0 | None | `keep_collecting` |
| `broker_order_forbidden` | `true` | 35 | 0 | None | `keep_collecting` |
| `broker_order_forbidden` | `false` | 12 | 0 | None | `keep_collecting` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_resolved_quote_freshness|fill=false|submitted=false` | 20 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 9 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=caution|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 5 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=safe|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 3 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=warning_observed_mark_gap_allowed|quote_age=quote_age_3_10s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=caution|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 2 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=entry_submit_revalidation_block|revalidation=warning_observed_mark_gap_unresolved|quote_age=quote_age_1_3s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=latency_unknown|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=entry_submit_revalidation_block|revalidation=warning_observed_mark_gap_unresolved|quote_age=quote_age_3_10s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=latency_unknown|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_failed_quote_stale|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=caution|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=safe|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `latency_reason` | `spread_above_caution_below_guard_cap` | 13 | 0 | None | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 12 | 0 | None | `keep_collecting` |
| `latency_reason` | `caution_normal_entry_allowed` | 8 | 0 | None | `keep_collecting` |
| `latency_reason` | `safe_normal_entry_allowed` | 4 | 0 | None | `keep_collecting` |
| `latency_reason` | `spread_too_wide` | 4 | 0 | None | `keep_collecting` |
| `latency_reason` | `latency_reason_unknown` | 2 | 0 | None | `source_quality_workorder` |
| `latency_reason` | `ws_age_too_high` | 2 | 0 | None | `keep_collecting` |
| `latency_reason` | `ws_age_too_high,spread_too_wide` | 2 | 0 | None | `keep_collecting` |
| `latency_state` | `danger` | 21 | 0 | None | `keep_collecting` |
| `latency_state` | `simulated` | 12 | 0 | None | `keep_collecting` |
| `latency_state` | `caution` | 8 | 0 | None | `keep_collecting` |
| `latency_state` | `safe` | 4 | 0 | None | `keep_collecting` |
| `latency_state` | `latency_unknown` | 2 | 0 | None | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_not_available` | 35 | 0 | None | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 11 | 0 | None | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 1 | 0 | None | `keep_collecting` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 35 | 0 | None | `source_quality_workorder` |
| `liquidity_guard_action` | `would_pass` | 11 | 0 | None | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 1 | 0 | None | `keep_collecting` |
| `overbought_bucket` | `overbought_not_available` | 35 | 0 | None | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 11 | 0 | None | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 1 | 0 | None | `keep_collecting` |
| `overbought_guard_action` | `overbought_guard_unknown` | 35 | 0 | None | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 13, 'source_row_count': 13, 'bucket_count': 10, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': None, 'source_quality_gate': 'hold_sample', 'unknown_reason_counts': {}, 'workorder_count': 0, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 12 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_not_applicable_at_start` | 12 | 0 | None | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 1 | 0 | None | `hold_sample` |
| `holding_action` | `WAIT` | 12 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 12 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 1 | 0 | None | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 1 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 12 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `adm_ldm_exit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'exit_rows': 25, 'source_row_count': 25, 'bucket_count': 19, 'joined_sample': 45, 'source_quality_adjusted_ev_pct': -0.8136, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 5, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 7 | 7 | -0.9214 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 1 | 1 | -0.1725 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 1 | 1 | -0.7 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_euphoria_context_noop|rule=scalp_sim_euphoria_context_noop_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 12 | 0 | None | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=scalp_sim_panic_context_warning_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 4 | 0 | None | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 8 | 8 | -0.8938 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `COMPLETED` | 1 | 1 | -0.1725 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 16 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 8 | 8 | -0.8938 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 1 | 1 | -0.1725 | `hold_sample` |
| `exit_rule` | `scalp_sim_euphoria_context_noop_not_applicable` | 12 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_context_warning_not_applicable` | 4 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 8 | 8 | -0.8938 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 1 | 1 | -0.1725 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_euphoria_context_noop` | 12 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 4 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 7 | 7 | -0.9214 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 2 | 2 | -0.4362 | `hold_sample` |
| `profit_band` | `profit_not_applicable_context_noop` | 16 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- `exit_bucket_source_quality_1`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_2`: `exit_outcome` / `outcome_not_applicable_partial_exit` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_3`: `exit_rule` / `scalp_sim_panic_lifecycle_partial_exit` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_4`: `exit_source_stage` / `scalp_sim_partial_sell_order_assumed_filled` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_5`: `profit_band` / `profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `incremental_notional_ev_pct`
- summary: `{'scale_in_rows': 97, 'bucket_count': 60, 'edge_bucket_count': 0, 'actionable_bucket_count': 0, 'runtime_authority_blocked_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'arm_counts': {'AVG_DOWN': 96, 'PYRAMID': 1}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 97 | 97 | None | -0.6396 | 0.0103 | `hold_sample` |
| `ai_score_source` | `live` | 49 | 49 | None | -0.6569 | 0.0 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 21 | 21 | None | -0.8271 | 0.0 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 19 | 19 | None | -0.4926 | 0.0 | `hold_sample` |
| `ai_score_source` | `not_evaluated_no_ai_score_source` | 6 | 6 | None | -0.4733 | 0.1667 | `hold_sample` |
| `ai_score_source` | `holding_ai_not_called` | 2 | 2 | None | -0.14 | 0.0 | `hold_sample` |
| `arm` | `AVG_DOWN` | 96 | 96 | None | -0.6491 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 1 | 1 | None | 0.27 | 1.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 96 | 96 | None | -0.6491 | 0.0 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 1 | 1 | None | 0.27 | 1.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.35)` | 8 | 8 | None | -0.35 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 8 | 8 | None | -0.8237 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.23)` | 7 | 7 | None | -0.23 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.46)` | 7 | 7 | None | -0.46 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.69)` | 7 | 7 | None | -0.69 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.64)` | 6 | 6 | None | -0.64 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.58)` | 5 | 5 | None | -0.58 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.77)` | 5 | 5 | None | -0.77 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.91)` | 5 | 5 | None | -0.91 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.37)` | 4 | 4 | None | -0.37 | 0.0 | `hold_sample` |

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
| `held_bucket` | `held_600_1800s_plus` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
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
