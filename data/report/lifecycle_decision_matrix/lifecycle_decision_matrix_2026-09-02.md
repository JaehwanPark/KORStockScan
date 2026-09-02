# Lifecycle Decision Matrix - 2026-09-02

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-09-02`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `2316`
- source_rows_total: `3424`
- retained_rows: `2316`
- dropped_rows_by_source: `{'dedupe': 1108}`
- joined_rows: `1229`
- policy_pass_count: `3`
- promote_ready_count: `0`
- entry_bucket_actionable_count: `0`
- entry_bucket_runtime_candidate_count: `0`
- holding_bucket_count/workorders: `18` / `5`
- exit_bucket_count/workorders: `37` / `10`
- scale_in_bucket_actionable_count: `0`
- scale_in_bucket_runtime_candidate_count: `0`
- overnight_bucket_actionable_count: `0`
- overnight_bucket_runtime_candidate_count: `0`
- lifecycle_flow_bucket_count: `37`
- lifecycle_flow_complete_count: `11`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `0` / `11` / `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0066`
- incomplete_flow_reason_counts: `{'missing_holding': 1650, 'missing_exit': 1336, 'missing_submit': 1595, 'missing_entry': 1494, 'postclose_exit_without_entry': 314, 'candidate_id_only': 1495, 'scale_in_noise_only': 1180, 'sim_record_id_only': 10}`
- bucket_directed_sim_probe: `{'observed_row_count': 375, 'matched_row_count': 0, 'background_row_count': 375, 'matched_unique_source_bucket_count': 0, 'match_status_counts': {'not_instrumented': 325, 'policy_disabled': 50}, 'matched_classification_state_counts': {}, 'primary_source': 'matched_bucket_directed_sim_probe_only', 'background_source': 'unmatched_or_policy_missing_sim_observation', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 0, 'route_counts': {'bounded_auxiliary_weight': 1, 'hold_sample': 4}, 'quality_counts': {'observational_only_pending_outcome': 1, 'hold_sample': 4}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 717 | 3 | 0.2038 | 0.0013 | `hold_sample` | `NO_CHANGE` | False |
| `submit` | 67 | 11 | -1.0131 | 0.1806 | `pass` | `NO_CHANGE` | False |
| `holding` | 14 | 11 | -1.1528 | 0.8643 | `hold_sample` | `EXIT` | False |
| `scale_in` | 1180 | 1179 | -1.2016 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 338 | 25 | -0.982 | 0.1849 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 1661, 'complete_flow_count': 11, 'direct_sim_record_complete_flow_count': 0, 'adm_bridge_complete_flow_count': 11, 'fallback_complete_flow_count': 0, 'direct_flow_zero_diagnostic': {'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'direct_sim_record_flow_count': 10, 'direct_sim_record_incomplete_flow_count': 10, 'direct_sim_record_stage_coverage_counts': {}, 'direct_sim_record_incomplete_reason_counts': {'missing_entry': 10, 'missing_submit': 10, 'missing_holding': 10, 'missing_exit': 10, 'sim_record_id_only': 10, 'scale_in_noise_only': 10}, 'runtime_effect': False, 'decision_authority': 'ldm_direct_flow_diagnostic_only'}, 'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'incomplete_flow_count': 1650, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 2316, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0066, 'complete_flow_conversion_denominator': 325, 'complete_flow_conversion_rate': 0.0338, 'active_priority_incomplete_seed_count': 156, 'scale_in_followup_event_count': 1180, 'scale_in_unique_flow_count': 913, 'scale_in_noise_flow_count': 1180, 'denominator_exclusion_counts': {'scale_in_noise_flow_excluded': 1180, 'active_priority_incomplete_seed_excluded': 156}, 'conversion_blocker_reason_counts': {'missing_entry': 314, 'missing_submit': 314, 'missing_holding': 314, 'postclose_exit_without_entry': 314, 'candidate_id_only': 313}, 'observation_seed_reason_counts': {'missing_holding': 1336, 'missing_exit': 1336, 'missing_submit': 1281, 'missing_entry': 1180, 'candidate_id_only': 1182, 'scale_in_noise_only': 1180, 'sim_record_id_only': 10}, 'join_contract_blocked': False, 'bundle_ev_tuning_state': 'ready_for_bundle_ev_tuning', 'top_incomplete_reason': 'missing_holding', 'stage_identity': {'entry': {'source_row_count': 717, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 705, 'candidate_id': 12}, 'identity_join_rate': 1.0}, 'submit': {'source_row_count': 67, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 67}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 14, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 14}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 1180, 'identity_missing_count': 0, 'identity_quality_counts': {'candidate_id': 1170, 'exact_sim_record_id': 10}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 338, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 25, 'candidate_id': 313}, 'identity_join_rate': 1.0}}, 'required_stage_source_counts': {'entry': 717, 'submit': 67, 'holding': 14, 'exit': 338}, 'incomplete_flow_reason_counts': {'missing_holding': 1650, 'missing_exit': 1336, 'missing_submit': 1595, 'missing_entry': 1494, 'postclose_exit_without_entry': 314, 'candidate_id_only': 1495, 'scale_in_noise_only': 1180, 'sim_record_id_only': 10}, 'bucket_count': 37, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:5ee2a7cfd7` | 2 | 2 | -1.13 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:f4d0891804` | 1 | 1 | -0.88 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:a6af469504` | 1 | 1 | -0.46 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:e6cc63e69d` | 1 | 1 | -1.45 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:e629891351` | 1 | 1 | -1.11 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:b0018089a8` | 1 | 1 | -3.5005 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:b31cc048c8` | 1 | 1 | -0.49 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:520515b37c` | 1 | 1 | -1.03 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:0e6c01c6bb` | 1 | 1 | -0.74 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:0e426f49f2` | 1 | 1 | -0.71 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 1149 | 1148 | -1.2524 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 31 | 31 | 0.6793 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:ab869676ad` | 1 | 1 | 0.3978 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:542cd2bc91` | 2 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_ai_c:acdcdf0d59` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_ai_c:2315da1c23` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:b846e1412a` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:c3e248a0f4` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:b52ee96ab3` | 3 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:18c5a6106d` | 7 | 0 | None | `hold_sample` | `join_contract_blocked` |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 717, 'bucket_count': 147, 'actionable_bucket_count': 0, 'source_quality_blocked_bucket_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `NO_BUY_AI` | 248 | 3 | 0.2038 | -1.0167 | 0.3333 | `hold_sample` |
| `chosen_action` | `ALLOW_BOTTOMING_ENTRY` | 3 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `ALLOW_LEVEL1_RISK_OFF_ENTRY` | 9 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `BUY_DEFENSIVE` | 72 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 45 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_SOURCE_QUALITY` | 2 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_STALE` | 3 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `WAIT_REQUOTE` | 335 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 1 | 1 | 0.5965 | 0.26 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_1200_1400` | 4 | 1 | -0.1318 | -1.79 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 1 | 1 | 0.1467 | -1.52 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1400_close` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_1400_close` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=blocked_ai_score|stale=stale_watch|liquidity=liquidity_not_available|overbought=overbought_normal|time=time_0900_1000` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_ok|time=time_1400_close` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_sim_panic_level1_entry_observed|stale=fresh_or_unflagged|liquidity=liquidity_state_normal|overbought=panic_entry_overbought_not_applicable|time=time_0900_1000` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_sim_panic_level1_entry_observed|stale=fresh_or_unflagged|liquidity=liquidity_state_normal|overbought=panic_entry_overbought_not_applicable|time=time_1000_1200` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1400_close` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_ok|time=time_1000_1200` | 1 | 0 | None | None | None | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `adm_ldm_submit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'submit_rows': 67, 'bucket_count': 80, 'contract_gap_count': 0, 'workorder_count': 0, 'runtime_candidate_count': 0, 'quote_freshness_attribution_present': True, 'row_quote_freshness_attribution_present': True, 'sentinel_quote_freshness_attribution_present': True, 'sentinel_quote_freshness_attribution': {'source_report_type': 'buy_funnel_sentinel', 'decision_authority': 'submit_drought_quote_freshness_attribution_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'forbidden_uses': ['broker_order_submit', 'adm_ldm_training_input', 'general_threshold_ev_input', 'live_auto_promotion'], 'refresh_attempted_count': 10, 'refresh_applied_count': 4, 'still_latency_blocked_after_refresh_count': 7, 'latency_pass_recovered_count': 1, 'order_bundle_submitted_after_refresh_count': 0, 'refresh_subreason_counts': {'ws_snapshot_refresh_failed_input_snapshot_fresh': 27, 'ws_snapshot_refresh_failed_stale': 1}, 'refresh_block_subreason_counts': {'ws_snapshot_refresh_failed_input_snapshot_fresh': 27, 'ws_snapshot_refresh_failed_stale': 1}, 'latency_pass_recovered_downstream_counts': {'entry_ai_authority_revalidation': 1}, 'post_restart_window_policy': 'event_provenance_only'}, 'quote_freshness_resolution_counts': {'refresh_attempted_unresolved': 12, 'refresh_failed_quote_stale': 11, 'refresh_not_attempted_or_not_instrumented': 2, 'refresh_resolved_quote_freshness': 30, 'sim_submit_path_not_applicable': 12}, 'pre_submit_refresh_applied_counts': {'refresh_attempted_not_applied': 23, 'refresh_not_attempted_or_not_instrumented': 2, 'sim_submit_path_not_applicable': 12, 'ws_snapshot_refresh_applied': 30}, 'real_submitted_row_count': 2, 'missing_broker_order_key_count': 0, 'bot_history_broker_order_key_backfill_candidate_count': 0, 'bot_history_broker_order_key_backfill_full_coverage': False, 'bot_history_broker_order_key_exact_mapping_count': 0, 'bot_history_broker_order_key_exact_mapping_full_coverage': False, 'post_submit_provenance_join_resolution': 'no_gap_broker_order_key_present_or_no_missing_rows', 'bot_history_broker_order_key_backfill_candidates': [], 'missing_broker_order_key_rate': 0.0, 'post_submit_provenance_join_gap_raw': False, 'post_submit_provenance_join_gap': False}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 65 | 11 | -1.0131 | `keep_collecting` |
| `actual_order_submitted` | `true` | 2 | 0 | None | `keep_collecting` |
| `broker_order_forbidden` | `true` | 65 | 11 | -1.0131 | `keep_collecting` |
| `broker_order_forbidden` | `false` | 2 | 0 | None | `keep_collecting` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_resolved_quote_freshness|fill=false|submitted=false` | 30 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_attempted_unresolved|fill=false|submitted=false` | 12 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_failed_quote_stale|fill=false|submitted=false` | 11 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 6 | 6 | -2.8216 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 3 | 2 | 0.2324 | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=caution|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=safe|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 1 | 1 | 0.1467 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | 4.9886 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | 0.1855 | `source_quality_workorder` |
| `latency_reason` | `spread_above_caution_below_guard_cap` | 22 | 0 | None | `keep_collecting` |
| `latency_reason` | `spread_too_wide` | 14 | 0 | None | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 12 | 11 | -1.0131 | `keep_collecting` |
| `latency_reason` | `ws_age_too_high,spread_too_wide` | 8 | 0 | None | `keep_collecting` |
| `latency_reason` | `ws_age_too_high` | 7 | 0 | None | `keep_collecting` |
| `latency_reason` | `quote_stale,ws_age_too_high,spread_too_wide` | 2 | 0 | None | `keep_collecting` |
| `latency_reason` | `caution_normal_entry_allowed` | 1 | 0 | None | `keep_collecting` |
| `latency_reason` | `safe_normal_entry_allowed` | 1 | 0 | None | `keep_collecting` |
| `latency_state` | `danger` | 53 | 0 | None | `keep_collecting` |
| `latency_state` | `simulated` | 12 | 11 | -1.0131 | `keep_collecting` |
| `latency_state` | `caution` | 1 | 0 | None | `keep_collecting` |
| `latency_state` | `safe` | 1 | 0 | None | `keep_collecting` |
| `liquidity_bucket` | `liquidity_not_available` | 55 | 0 | None | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 8 | 8 | -1.4694 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 4 | 3 | 0.2038 | `keep_collecting` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 55 | 0 | None | `source_quality_workorder` |
| `liquidity_guard_action` | `would_block` | 8 | 8 | -1.4694 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 4 | 3 | 0.2038 | `keep_collecting` |
| `overbought_bucket` | `overbought_not_available` | 55 | 0 | None | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 11 | 10 | -1.6133 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 1 | 1 | 4.9886 | `keep_collecting` |
| `overbought_guard_action` | `overbought_guard_unknown` | 55 | 0 | None | `source_quality_workorder` |
| `overbought_guard_action` | `would_pass` | 12 | 11 | -1.0131 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `refresh_age_lt1s` | 36 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `refresh_age_not_instrumented` | 14 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 12 | 11 | -1.0131 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 14, 'source_row_count': 14, 'bucket_count': 18, 'joined_sample': 55, 'source_quality_adjusted_ev_pct': -1.1528, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 5, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 7 | 7 | -2.1635 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 2 | 2 | -0.4827 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 1 | 1 | -1.35 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 4.7784 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_not_applicable_at_start` | 12 | 11 | -1.1528 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |
| `holding_action` | `WAIT` | 11 | 10 | -1.746 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 1 | 1 | 4.7784 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 2 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 12 | 11 | -1.1528 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 2 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 9 | 7 | -2.1635 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 2 | 2 | -0.4827 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 1 | 1 | -1.35 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 1 | 1 | 4.7784 | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- `holding_bucket_source_quality_1`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_2`: `held_bucket` / `held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_3`: `holding_action` / `WAIT` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_4`: `holding_source_stage` / `scalp_sim_holding_started` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_5`: `profit_band` / `profit_lt_neg070` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Exit Bucket Attribution

- decision_authority: `adm_ldm_exit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'exit_rows': 338, 'source_row_count': 338, 'bucket_count': 37, 'joined_sample': 125, 'source_quality_adjusted_ev_pct': -0.982, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 9 | 9 | -1.0233 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_lt_neg070` | 2 | 2 | -1.0537 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 2 | 2 | -0.475 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 2 | 2 | -3.028 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 1 | 1 | -0.6948 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | -0.4217 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=NEUTRAL|profit=profit_lt_neg070` | 1 | 1 | -0.9741 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | -4.527 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 1 | 1 | -2.4707 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 1 | 1 | 0.3978 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 1 | 1 | 0.4181 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 1 | 1 | 4.7784 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 1 | 1 | -1.3835 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300` | 1 | 1 | -1.35 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=scalp_sim_panic_context_warning_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 313 | 0 | None | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 11 | 11 | -0.9236 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 5 | 5 | -1.3746 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 4 | 4 | 0.062 | `hold_no_edge` |
| `exit_outcome` | `GOOD_EXIT` | 3 | 3 | -1.886 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `COMPLETED` | 2 | 2 | -1.0537 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 313 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 11 | 11 | -0.9236 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 5 | 5 | 0.5722 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 4 | 4 | -0.8758 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 4 | 4 | -3.2634 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 1 | 1 | -0.6948 | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_context_warning_not_applicable` | 313 | 0 | None | `hold_sample` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 12 | 12 | -1.0236 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 11 | 11 | -0.9236 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 2 | 2 | -1.0537 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 313 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 18 | 18 | -1.4701 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 3 | 3 | -0.1892 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 2 | 2 | -0.475 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 1 | 1 | -1.35 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 1 | 1 | 4.7784 | `hold_sample` |
| `profit_band` | `profit_not_applicable_context_noop` | 313 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- `exit_bucket_source_quality_1`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_2`: `exit_outcome` / `outcome_not_applicable_partial_exit` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_3`: `exit_outcome` / `NEUTRAL` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_4`: `exit_outcome` / `GOOD_EXIT` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_5`: `exit_rule` / `scalp_sim_panic_lifecycle_partial_exit` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_6`: `exit_rule` / `scalp_trailing_take_profit` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_7`: `exit_rule` / `scalp_sim_overnight_sell_today` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_8`: `exit_rule` / `scalp_soft_stop_pct` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_9`: `exit_source_stage` / `sim_post_sell_evaluation` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_10`: `exit_source_stage` / `scalp_sim_partial_sell_order_assumed_filled` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `incremental_notional_ev_pct`
- summary: `{'scale_in_rows': 1180, 'bucket_count': 165, 'edge_bucket_count': 0, 'actionable_bucket_count': 0, 'runtime_authority_blocked_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'arm_counts': {'AVG_DOWN': 1149, 'PYRAMID': 31}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 1179 | 1179 | None | -1.3224 | 0.0263 | `hold_sample` |
| `ai_score_band` | `score_unknown` | 1 | 0 | None | None | None | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 751 | 751 | None | -1.3568 | 0.0306 | `hold_sample` |
| `ai_score_source` | `live` | 204 | 204 | None | -1.3831 | 0.0294 | `hold_sample` |
| `ai_score_source` | `not_evaluated_no_ai_score_source` | 97 | 97 | None | -0.7953 | 0.0 | `hold_sample` |
| `ai_score_source` | `holding_ai_not_called` | 63 | 63 | None | -1.41 | 0.0 | `hold_sample` |
| `ai_score_source` | `prior_valid` | 54 | 54 | None | -1.5596 | 0.037 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 10 | 10 | None | -0.776 | 0.0 | `hold_sample` |
| `ai_score_source` | `stage_rule_backfilled` | 1 | 0 | None | None | None | `hold_sample` |
| `arm` | `AVG_DOWN` | 1149 | 1148 | None | -1.3759 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 31 | 31 | None | 0.659 | 1.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 1135 | 1134 | None | -1.3518 | 0.0 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 31 | 31 | None | 0.659 | 1.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 14 | 14 | None | -3.3229 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.42)` | 44 | 44 | None | -1.42 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.25)` | 40 | 40 | None | -1.25 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.08)` | 39 | 39 | None | -1.08 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.39)` | 33 | 33 | None | -0.39 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.74)` | 31 | 31 | None | -0.74 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.91)` | 28 | 28 | None | -0.91 | 0.0 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `adm_ldm_overnight_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'observation_state': 'observed', 'observation_reason': 'overnight_pipeline_rows_available', 'source_artifact_present': True, 'overnight_rows': 4, 'bucket_count': 15, 'actionable_bucket_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'status_counts': {'HOLD_OVERNIGHT': 2, 'SELL_TODAY': 2}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 2 | 2 | -1.0537 | -1.405 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_lt_neg070` | 2 | 0 | None | None | None | `hold_sample` |
| `confidence_band` | `confidence_070p` | 4 | 2 | -1.0537 | -1.405 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 4 | 2 | -1.0537 | -1.405 | 0.0 | `hold_sample` |
| `overnight_action` | `SELL_TODAY` | 4 | 2 | -1.0537 | -1.405 | 0.0 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 2 | 2 | -1.0537 | -1.405 | 0.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 2 | 0 | None | None | None | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 4 | 2 | -1.0537 | -1.405 | 0.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 4 | 2 | -1.0537 | -1.405 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 4 | 2 | -1.0537 | -1.405 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 4 | 2 | -1.0537 | -1.405 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 2 | 2 | -1.0537 | -1.405 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_decision` | 2 | 0 | None | None | None | `hold_sample` |
| `stage` | `exit` | 2 | 2 | -1.0537 | -1.405 | 0.0 | `hold_sample` |
| `stage` | `holding` | 2 | 0 | None | None | None | `hold_sample` |

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
