# Lifecycle Decision Matrix - 2026-08-21

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-08-21`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `2626`
- source_rows_total: `3487`
- retained_rows: `2626`
- dropped_rows_by_source: `{'dedupe': 861}`
- joined_rows: `663`
- policy_pass_count: `3`
- promote_ready_count: `0`
- entry_bucket_actionable_count: `0`
- entry_bucket_runtime_candidate_count: `0`
- holding_bucket_count/workorders: `14` / `6`
- exit_bucket_count/workorders: `26` / `10`
- scale_in_bucket_actionable_count: `0`
- scale_in_bucket_runtime_candidate_count: `0`
- overnight_bucket_actionable_count: `0`
- overnight_bucket_runtime_candidate_count: `0`
- lifecycle_flow_bucket_count: `44`
- lifecycle_flow_complete_count: `11`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `0` / `11` / `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0055`
- incomplete_flow_reason_counts: `{'missing_holding': 1975, 'missing_exit': 804, 'missing_submit': 1897, 'missing_entry': 1794, 'candidate_id_only': 1808, 'scale_in_noise_only': 621, 'sim_record_id_only': 2, 'postclose_exit_without_entry': 1172}`
- bucket_directed_sim_probe: `{'observed_row_count': 1239, 'matched_row_count': 14, 'background_row_count': 1225, 'matched_unique_source_bucket_count': 1, 'match_status_counts': {'matched': 14, 'no_match': 35, 'not_instrumented': 1190}, 'matched_classification_state_counts': {'lifecycle_flow_sim_probe_candidate': 14}, 'primary_source': 'matched_bucket_directed_sim_probe_only', 'background_source': 'unmatched_or_policy_missing_sim_observation', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 1, 'route_counts': {'bounded_auxiliary_weight': 1, 'hold_sample': 4}, 'quality_counts': {'observational_only_pending_outcome': 1, 'hold_sample': 4}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 705 | 5 | -0.4734 | 0.0035 | `hold_sample` | `WAIT_REQUOTE` | False |
| `submit` | 94 | 10 | -1.4226 | 0.1064 | `pass` | `NO_CHANGE` | False |
| `holding` | 14 | 10 | -1.3495 | 0.7143 | `hold_sample` | `EXIT` | False |
| `scale_in` | 621 | 618 | -0.7445 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 1192 | 20 | -1.0983 | 0.0336 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 1987, 'complete_flow_count': 11, 'direct_sim_record_complete_flow_count': 0, 'adm_bridge_complete_flow_count': 11, 'fallback_complete_flow_count': 0, 'direct_flow_zero_diagnostic': {'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'direct_sim_record_flow_count': 2, 'direct_sim_record_incomplete_flow_count': 2, 'direct_sim_record_stage_coverage_counts': {}, 'direct_sim_record_incomplete_reason_counts': {'missing_entry': 2, 'missing_submit': 2, 'missing_holding': 2, 'missing_exit': 2, 'sim_record_id_only': 2, 'scale_in_noise_only': 2}, 'runtime_effect': False, 'decision_authority': 'ldm_direct_flow_diagnostic_only'}, 'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'incomplete_flow_count': 1976, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 2626, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0055, 'complete_flow_conversion_denominator': 1184, 'complete_flow_conversion_rate': 0.0093, 'active_priority_incomplete_seed_count': 182, 'scale_in_followup_event_count': 621, 'scale_in_unique_flow_count': 446, 'scale_in_noise_flow_count': 621, 'denominator_exclusion_counts': {'scale_in_noise_flow_excluded': 621, 'active_priority_incomplete_seed_excluded': 182}, 'conversion_blocker_reason_counts': {'missing_entry': 1173, 'missing_holding': 1173, 'missing_exit': 1, 'missing_submit': 1172, 'candidate_id_only': 1172, 'postclose_exit_without_entry': 1172}, 'observation_seed_reason_counts': {'missing_holding': 802, 'missing_exit': 803, 'missing_submit': 725, 'missing_entry': 621, 'candidate_id_only': 636, 'scale_in_noise_only': 621, 'sim_record_id_only': 2}, 'join_contract_blocked': False, 'bundle_ev_tuning_state': 'ready_for_bundle_ev_tuning', 'top_incomplete_reason': 'missing_holding', 'stage_identity': {'entry': {'source_row_count': 705, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 688, 'candidate_id': 17}, 'identity_join_rate': 1.0}, 'submit': {'source_row_count': 94, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 94}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 14, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 14}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 621, 'identity_missing_count': 0, 'identity_quality_counts': {'candidate_id': 619, 'exact_sim_record_id': 2}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 1192, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 20, 'candidate_id': 1172}, 'identity_join_rate': 1.0}}, 'required_stage_source_counts': {'entry': 705, 'submit': 94, 'holding': 14, 'exit': 1192}, 'incomplete_flow_reason_counts': {'missing_holding': 1975, 'missing_exit': 804, 'missing_submit': 1897, 'missing_entry': 1794, 'candidate_id_only': 1808, 'scale_in_noise_only': 621, 'sim_record_id_only': 2, 'postclose_exit_without_entry': 1172}, 'bucket_count': 44, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:9d042ec94c` | 1 | 1 | -1.01 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:3fde12b654` | 1 | 1 | -0.6 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:827611b511` | 1 | 1 | -1.05 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:b0bc92a886` | 1 | 1 | -0.8 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:8c461a936f` | 1 | 1 | -0.62 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:d8bc4e1490` | 1 | 1 | 0.0754 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:27b40f1c54` | 1 | 1 | -0.57 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:a7c21066aa` | 1 | 1 | -1.36 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:ccc234c442` | 1 | 1 | 0.5283 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:8c7177b0a1` | 1 | 1 | -0.55 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:bbe961df76` | 1 | 1 | -1.09 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 506 | 503 | -0.9886 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 115 | 115 | 0.3231 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:f896d0f991` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:b846e1412a` | 2 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:23195a6385` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:c3e248a0f4` | 2 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:54101985e8` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:c50d2ff605` | 2 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:07390fbd3e` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 705, 'bucket_count': 148, 'actionable_bucket_count': 0, 'source_quality_blocked_bucket_count': 12, 'runtime_candidate_count': 0, 'workorder_count': 10}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `NO_BUY_AI` | 276 | 4 | -0.8984 | -1.7075 | 0.5 | `hold_sample` |
| `chosen_action` | `WAIT_REQUOTE` | 333 | 1 | 1.2264 | 0.33 | 1.0 | `hold_sample` |
| `chosen_action` | `ALLOW_BOTTOMING_ENTRY` | 6 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `ALLOW_LEVEL1_RISK_OFF_ENTRY` | 11 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `BUY_DEFENSIVE` | 64 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `BUY_NOW` | 1 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 10 | 0 | None | None | None | `source_quality_workorder` |
| `chosen_action` | `SKIP_SOURCE_QUALITY` | 2 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_STALE` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_1200_1400` | 6 | 2 | -1.4302 | -3.68 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1400_close` | 1 | 1 | -0.2437 | 0.4 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_ok|time=time_1400_close` | 2 | 1 | -0.4894 | 0.13 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1400_close` | 94 | 1 | 1.2264 | 0.33 | 1.0 | `source_quality_workorder` |
| `combo_entry_spot` | `score=score_63_65|source=blocked_ai_score|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_1400_close` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1400_close` | 3 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_1400_close` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=blocked_ai_score|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=blocked_ai_score|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_1000_1200` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=blocked_ai_score|stale=fresh|liquidity=liquidity_not_available|overbought=overbought_watch|time=time_1000_1200` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 1 | 0 | None | None | None | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- `entry_bucket_unknown_source_quality_1`: `chosen_action` / `SKIP_PRE_SUBMIT_SAFETY` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_2`: `combo_entry_spot` / `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1400_close` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_3`: `combo_entry_spot` / `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1000_1200` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_4`: `exit_rule` / `exit_unknown` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_5`: `liquidity_bucket` / `liquidity_not_available` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_6`: `overbought_bucket` / `overbought_not_available` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_7`: `score_band` / `score_lt60` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_8`: `source_stage` / `scalp_entry_action_decision_snapshot` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_9`: `stale_bucket` / `stale_not_available` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_10`: `strength_bucket` / `risk_unknown` -> `unknown_bucket_source_quality_blocker`

## Submit Bucket Attribution

- decision_authority: `adm_ldm_submit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'submit_rows': 94, 'bucket_count': 92, 'contract_gap_count': 0, 'workorder_count': 0, 'runtime_candidate_count': 0, 'quote_freshness_attribution_present': True, 'row_quote_freshness_attribution_present': True, 'sentinel_quote_freshness_attribution_present': True, 'sentinel_quote_freshness_attribution': {'source_report_type': 'buy_funnel_sentinel', 'decision_authority': 'submit_drought_quote_freshness_attribution_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'forbidden_uses': ['broker_order_submit', 'adm_ldm_training_input', 'general_threshold_ev_input', 'live_auto_promotion'], 'refresh_attempted_count': 122, 'refresh_applied_count': 74, 'still_latency_blocked_after_refresh_count': 88, 'latency_pass_recovered_count': 25, 'order_bundle_submitted_after_refresh_count': 6, 'refresh_subreason_counts': {'observer_quote_refresh_failed_stale': 2, 'ws_snapshot_refresh_failed_input_snapshot_fresh': 394, 'ws_snapshot_refresh_failed_stale': 23}, 'refresh_block_subreason_counts': {'observer_quote_refresh_failed_stale': 2, 'ws_snapshot_refresh_failed_input_snapshot_fresh': 394, 'ws_snapshot_refresh_failed_stale': 23}, 'latency_pass_recovered_downstream_counts': {'budget_pass_no_submit_event': 3, 'entry_ai_authority_revalidation': 16, 'order_bundle_submitted': 6}, 'post_restart_window_policy': 'event_provenance_only'}, 'quote_freshness_resolution_counts': {'refresh_attempted_unresolved': 31, 'refresh_failed_quote_stale': 10, 'refresh_not_attempted_or_not_instrumented': 19, 'refresh_resolved_quote_freshness': 18, 'sim_submit_path_not_applicable': 16}, 'pre_submit_refresh_applied_counts': {'refresh_attempted_not_applied': 41, 'refresh_not_attempted_or_not_instrumented': 19, 'sim_submit_path_not_applicable': 16, 'ws_snapshot_refresh_applied': 18}, 'real_submitted_row_count': 18, 'missing_broker_order_key_count': 0, 'bot_history_broker_order_key_backfill_candidate_count': 0, 'bot_history_broker_order_key_backfill_full_coverage': False, 'bot_history_broker_order_key_exact_mapping_count': 0, 'bot_history_broker_order_key_exact_mapping_full_coverage': False, 'post_submit_provenance_join_resolution': 'no_gap_broker_order_key_present_or_no_missing_rows', 'bot_history_broker_order_key_backfill_candidates': [], 'missing_broker_order_key_rate': 0.0, 'post_submit_provenance_join_gap_raw': False, 'post_submit_provenance_join_gap': False}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 76 | 10 | -1.4226 | `keep_collecting` |
| `actual_order_submitted` | `true` | 18 | 0 | None | `keep_collecting` |
| `broker_order_forbidden` | `true` | 76 | 10 | -1.4226 | `keep_collecting` |
| `broker_order_forbidden` | `false` | 18 | 0 | None | `keep_collecting` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_attempted_unresolved|fill=false|submitted=false` | 31 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_resolved_quote_freshness|fill=false|submitted=false` | 18 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=caution|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 11 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_failed_quote_stale|fill=false|submitted=false` | 10 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_lt1s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=caution|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 6 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 4 | 2 | -1.4302 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 3 | 2 | -2.1725 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 3 | 3 | -2.5046 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 2 | 2 | 0.3685 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 2 | 1 | -0.2437 | `source_quality_workorder` |
| `combo_submit_quality` | `source=entry_submit_revalidation_block|revalidation=warning_observed_mark_gap_unresolved|quote_age=quote_age_3_10s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=latency_unknown|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=warning_observed_mark_gap_allowed|quote_age=quote_age_lt1s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=caution|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_block|revalidation=warning_stale_context_or_quote|quote_consistency_stale|quote_age=quote_age_10s_plus|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_block|revalidation=warning_stale_context_or_quote|quote_consistency_stale|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `latency_reason` | `caution_normal_entry_allowed` | 18 | 0 | None | `keep_collecting` |
| `latency_reason` | `ws_age_too_high` | 18 | 0 | None | `keep_collecting` |
| `latency_reason` | `spread_above_caution_below_guard_cap` | 17 | 0 | None | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 16 | 10 | -1.4226 | `keep_collecting` |
| `latency_reason` | `spread_too_wide` | 15 | 0 | None | `keep_collecting` |
| `latency_reason` | `ws_age_too_high,spread_too_wide` | 8 | 0 | None | `keep_collecting` |
| `latency_reason` | `latency_reason_unknown` | 1 | 0 | None | `source_quality_workorder` |
| `latency_reason` | `quote_stale,ws_age_too_high,spread_too_wide` | 1 | 0 | None | `keep_collecting` |
| `latency_state` | `danger` | 59 | 0 | None | `keep_collecting` |
| `latency_state` | `caution` | 18 | 0 | None | `keep_collecting` |
| `latency_state` | `simulated` | 16 | 10 | -1.4226 | `keep_collecting` |
| `latency_state` | `latency_unknown` | 1 | 0 | None | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_not_available` | 78 | 0 | None | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 9 | 5 | -0.4734 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 7 | 5 | -2.3718 | `keep_collecting` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 78 | 0 | None | `source_quality_workorder` |
| `liquidity_guard_action` | `would_pass` | 9 | 5 | -0.4734 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 7 | 5 | -2.3718 | `keep_collecting` |
| `overbought_bucket` | `overbought_not_available` | 78 | 0 | None | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 9 | 6 | -1.1701 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 7 | 4 | -1.8014 | `keep_collecting` |
| `overbought_guard_action` | `overbought_guard_unknown` | 78 | 0 | None | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 14, 'source_row_count': 14, 'bucket_count': 14, 'joined_sample': 50, 'source_quality_adjusted_ev_pct': -1.3495, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 6, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 4 | 4 | -2.8485 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 3 | 3 | 0.1323 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 2 | 2 | -0.3212 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | -1.8555 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_not_applicable_at_start` | 14 | 10 | -1.3495 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 8 | 6 | -2.0061 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 6 | 4 | -0.3647 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 14 | 10 | -1.3495 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 5 | 5 | -0.0491 | `hold_no_edge` |
| `profit_band` | `profit_lt_neg070` | 4 | 4 | -2.8485 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 1 | 1 | -1.8555 | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 4 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- `holding_bucket_source_quality_1`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_2`: `held_bucket` / `held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_3`: `holding_action` / `holding_action_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_4`: `holding_action` / `WAIT` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_5`: `holding_source_stage` / `scalp_sim_holding_started` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_6`: `profit_band` / `profit_lt_neg070` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Exit Bucket Attribution

- decision_authority: `adm_ldm_exit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'exit_rows': 1192, 'source_row_count': 1192, 'bucket_count': 26, 'joined_sample': 100, 'source_quality_adjusted_ev_pct': -1.0983, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 6 | 6 | -1.0217 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 4 | 4 | -0.585 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 3 | 3 | -0.2581 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 2 | 2 | -3.6458 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 2 | 2 | -2.0513 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 1 | 1 | -0.2069 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 1 | 1 | -1.8555 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 1 | 1 | 0.7356 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=scalp_sim_panic_context_warning_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 1172 | 0 | None | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 10 | 10 | -0.847 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 4 | 4 | -2.3385 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 3 | 3 | -1.1223 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 3 | 3 | -0.2581 | `hold_no_edge` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 1172 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 10 | 10 | -0.847 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 6 | 6 | -0.3502 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 4 | 4 | -2.8485 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_context_warning_not_applicable` | 1172 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 10 | 10 | -0.847 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 10 | 10 | -1.3495 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 1172 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 10 | 10 | -1.7524 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 5 | 5 | -0.0491 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 4 | 4 | -0.585 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 1 | 1 | -1.8555 | `hold_sample` |
| `profit_band` | `profit_not_applicable_context_noop` | 1172 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- `exit_bucket_source_quality_1`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_2`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_3`: `exit_outcome` / `outcome_not_applicable_partial_exit` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_4`: `exit_outcome` / `GOOD_EXIT` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_5`: `exit_outcome` / `MISSED_UPSIDE` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_6`: `exit_rule` / `scalp_sim_panic_lifecycle_partial_exit` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_7`: `exit_rule` / `scalp_trailing_take_profit` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_8`: `exit_rule` / `scalp_soft_stop_pct` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_9`: `exit_source_stage` / `scalp_sim_partial_sell_order_assumed_filled` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_10`: `exit_source_stage` / `sim_post_sell_evaluation` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `incremental_notional_ev_pct`
- summary: `{'scale_in_rows': 621, 'bucket_count': 104, 'edge_bucket_count': 0, 'actionable_bucket_count': 0, 'runtime_authority_blocked_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'arm_counts': {'AVG_DOWN': 506, 'PYRAMID': 115}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 610 | 610 | None | -0.8422 | 0.1557 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 6 | 6 | None | 0.7367 | 1.0 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 2 | 2 | None | 0.86 | 1.0 | `hold_sample` |
| `ai_score_band` | `score_unknown` | 3 | 0 | None | None | None | `hold_sample` |
| `ai_score_source` | `live` | 317 | 317 | None | -0.4802 | 0.2965 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 206 | 206 | None | -1.18 | 0.034 | `hold_sample` |
| `ai_score_source` | `not_evaluated_no_ai_score_source` | 53 | 53 | None | -0.6957 | 0.0377 | `hold_sample` |
| `ai_score_source` | `prior_valid` | 22 | 22 | None | -1.7645 | 0.0 | `hold_sample` |
| `ai_score_source` | `holding_ai_not_called` | 18 | 18 | None | -1.9833 | 0.0 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 2 | 2 | None | -0.46 | 0.0 | `hold_sample` |
| `ai_score_source` | `stage_rule_backfilled` | 3 | 0 | None | None | None | `hold_sample` |
| `arm` | `AVG_DOWN` | 506 | 503 | None | -1.0778 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 115 | 115 | None | 0.3003 | 0.8957 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 506 | 503 | None | -1.0778 | 0.0 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 115 | 115 | None | 0.3003 | 0.8957 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 108 | 108 | None | 0.2963 | 0.8981 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.96)` | 37 | 37 | None | -0.96 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.57)` | 26 | 26 | None | -0.57 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.77)` | 24 | 24 | None | -0.77 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.59)` | 22 | 22 | None | -0.59 | 0.0 | `hold_sample` |

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
