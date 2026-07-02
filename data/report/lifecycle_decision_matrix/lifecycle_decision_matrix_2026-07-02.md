# Lifecycle Decision Matrix - 2026-07-02

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-02`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `6662`
- source_rows_total: `9912`
- retained_rows: `6662`
- dropped_rows_by_source: `{'dedupe': 3250}`
- joined_rows: `3366`
- policy_pass_count: `5`
- promote_ready_count: `0`
- entry_bucket_actionable_count: `6`
- entry_bucket_runtime_candidate_count: `0`
- holding_bucket_count/workorders: `18` / `7`
- exit_bucket_count/workorders: `38` / `10`
- scale_in_bucket_actionable_count: `0`
- scale_in_bucket_runtime_candidate_count: `0`
- overnight_bucket_actionable_count: `0`
- overnight_bucket_runtime_candidate_count: `0`
- lifecycle_flow_bucket_count: `77`
- lifecycle_flow_complete_count: `9`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `0` / `9` / `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0014`
- incomplete_flow_reason_counts: `{'missing_exit': 3383, 'missing_entry': 6087, 'missing_holding': 6210, 'missing_submit': 6184, 'postclose_exit_without_entry': 2863, 'candidate_id_only': 6083, 'sim_record_id_only': 66, 'scale_in_noise_only': 3208}`
- bucket_directed_sim_probe: `{'observed_row_count': 3193, 'matched_row_count': 21, 'background_row_count': 3172, 'matched_unique_source_bucket_count': 1, 'match_status_counts': {'matched': 21, 'no_match': 315, 'not_instrumented': 2857}, 'matched_classification_state_counts': {'lifecycle_flow_sim_probe_candidate': 21}, 'primary_source': 'matched_bucket_directed_sim_probe_only', 'background_source': 'unmatched_or_policy_missing_sim_observation', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 1, 'route_counts': {'bounded_auxiliary_weight': 1, 'hold_sample': 4}, 'quality_counts': {'observational_only_pending_outcome': 1, 'hold_sample': 4}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 286 | 17 | 1.2343 | 0.101 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 142 | 19 | -0.9002 | 0.2542 | `pass` | `NO_CHANGE` | False |
| `holding` | 101 | 19 | -1.7701 | 0.3574 | `pass` | `EXIT` | False |
| `scale_in` | 3257 | 3238 | -0.7308 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 2876 | 73 | -1.1566 | 0.1853 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 6255, 'complete_flow_count': 9, 'direct_sim_record_complete_flow_count': 0, 'adm_bridge_complete_flow_count': 9, 'fallback_complete_flow_count': 0, 'direct_flow_zero_diagnostic': {'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'direct_sim_record_flow_count': 66, 'direct_sim_record_incomplete_flow_count': 66, 'direct_sim_record_stage_coverage_counts': {'holding': 1, 'exit': 52}, 'direct_sim_record_incomplete_reason_counts': {'missing_entry': 66, 'missing_submit': 66, 'missing_holding': 65, 'missing_exit': 14, 'sim_record_id_only': 66, 'scale_in_noise_only': 14, 'postclose_exit_without_entry': 52}, 'runtime_effect': False, 'decision_authority': 'ldm_direct_flow_diagnostic_only'}, 'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'incomplete_flow_count': 6246, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 6662, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0014, 'complete_flow_conversion_denominator': 2888, 'complete_flow_conversion_rate': 0.0031, 'active_priority_incomplete_seed_count': 159, 'scale_in_followup_event_count': 3257, 'scale_in_unique_flow_count': 2753, 'scale_in_noise_flow_count': 3208, 'denominator_exclusion_counts': {'scale_in_noise_flow_excluded': 3208, 'active_priority_incomplete_seed_excluded': 159}, 'conversion_blocker_reason_counts': {'missing_entry': 2879, 'missing_holding': 2871, 'missing_exit': 16, 'postclose_exit_without_entry': 2863, 'missing_submit': 2858, 'sim_record_id_only': 52, 'candidate_id_only': 2803}, 'observation_seed_reason_counts': {'missing_exit': 3367, 'missing_holding': 3339, 'missing_submit': 3326, 'candidate_id_only': 3280, 'missing_entry': 3208, 'sim_record_id_only': 14, 'scale_in_noise_only': 3208}, 'join_contract_blocked': False, 'bundle_ev_tuning_state': 'ready_for_bundle_ev_tuning', 'top_incomplete_reason': 'missing_holding', 'stage_identity': {'entry': {'source_row_count': 286, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 200, 'candidate_id': 86}, 'identity_join_rate': 1.0}, 'submit': {'source_row_count': 142, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 142}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 101, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 100, 'exact_sim_record_id': 1}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 3257, 'identity_missing_count': 0, 'identity_quality_counts': {'exact_sim_record_id': 63, 'candidate_id': 3194}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 2876, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 20, 'exact_sim_record_id': 53, 'candidate_id': 2803}, 'identity_join_rate': 1.0}}, 'required_stage_source_counts': {'entry': 286, 'submit': 142, 'holding': 101, 'exit': 2876}, 'incomplete_flow_reason_counts': {'missing_exit': 3383, 'missing_entry': 6087, 'missing_holding': 6210, 'missing_submit': 6184, 'postclose_exit_without_entry': 2863, 'candidate_id_only': 6083, 'sim_record_id_only': 66, 'scale_in_noise_only': 3208}, 'bucket_count': 77, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:de45155b3b` | 1 | 1 | -1.654 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:c8b94ea5f8` | 1 | 1 | -1.9776 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:a2fde9fa15` | 1 | 1 | -1.4308 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:b485054732` | 1 | 1 | -1.125 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:9826fdb35b` | 1 | 1 | -1.5266 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:b0018089a8` | 1 | 1 | -2.017 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:92385e7561` | 1 | 1 | -2.2285 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:19a95e3069` | 1 | 1 | -2.7521 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:aab309119e` | 1 | 1 | 0.8991 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 2739 | 2720 | -0.9518 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 469 | 469 | 0.5635 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 46 | 46 | -1.0143 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 11 | 11 | 0.7047 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 3 | 3 | -1.4367 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:4874ec99fd` | 2 | 2 | -2.1328 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:7d1a415bd0` | 2 | 2 | 0.8157 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 2 | 2 | 0.655 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:df02034b40` | 4 | 1 | -0.83 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 1 | 1 | 0.0041 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 1 | 1 | 9.4991 | `hold_sample` | `join_contract_blocked` |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 286, 'bucket_count': 156, 'actionable_bucket_count': 6, 'source_quality_blocked_bucket_count': 10, 'runtime_candidate_count': 0, 'workorder_count': 16}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `WAIT_REQUOTE` | 14 | 13 | 1.3273 | 2.2003 | 0.3077 | `candidate_recovery_or_relax` |
| `chosen_action` | `NO_BUY_AI` | 177 | 4 | 0.9321 | -4.3 | 0.0 | `hold_sample` |
| `chosen_action` | `ALLOW_BOTTOMING_ENTRY` | 6 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `ALLOW_LEVEL1_RISK_OFF_ENTRY` | 67 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `BUY_DEFENSIVE` | 1 | 0 | None | None | None | `source_quality_workorder` |
| `chosen_action` | `BUY_NOW` | 16 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_STALE` | 5 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 7 | 7 | 0.4257 | 0.6126 | 0.2857 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 4 | 4 | 1.193 | 2.0309 | 0.25 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1400_close` | 3 | 1 | 1.06 | -3.31 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 1 | 1 | 0.8643 | -3.72 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 1 | 1 | 0.0041 | 0.0 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_ok|time=time_1400_close` | 1 | 1 | 9.4991 | 16.1922 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 5 | 1 | 1.1557 | -4.08 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 1 | 1 | 0.6482 | -6.09 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 3 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_ok|time=time_1000_1200` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=ai_confirmed|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=ai_confirmed|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 2 | 0 | None | None | None | `hold_sample` |
| `liquidity_bucket` | `liquidity_high` | 184 | 17 | 1.2343 | 0.6708 | 0.2353 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 168 | 15 | 0.7224 | 0.0868 | 0.2 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 13 | 13 | 1.3273 | 2.2003 | 0.3077 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh_or_unflagged` | 86 | 13 | 1.3273 | 2.2003 | 0.3077 | `candidate_recovery_or_relax` |
| `strength_bucket` | `strong_strength_momentum` | 40 | 11 | 1.7483 | 2.3451 | 0.3636 | `candidate_recovery_or_relax` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- `entry_bucket_unknown_source_quality_1`: `chosen_action` / `BUY_DEFENSIVE` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_2`: `combo_entry_spot` / `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1400_close` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_3`: `exit_rule` / `exit_unknown` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_4`: `liquidity_bucket` / `liquidity_not_available` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_5`: `overbought_bucket` / `overbought_not_available` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_6`: `score_band` / `score_70p` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_7`: `source_stage` / `scalp_entry_action_decision_snapshot` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_8`: `stale_bucket` / `stale_not_available` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_9`: `strength_bucket` / `risk_unknown` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_10`: `time_bucket` / `time_1400_close` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_source_quality_1`: `chosen_action` / `WAIT_REQUOTE` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_2`: `liquidity_bucket` / `liquidity_high` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_3`: `overbought_bucket` / `overbought_normal` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_4`: `source_stage` / `wait6579_ev_cohort` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_5`: `stale_bucket` / `fresh_or_unflagged` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_6`: `strength_bucket` / `strong_strength_momentum` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`

## Submit Bucket Attribution

- decision_authority: `adm_ldm_submit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'submit_rows': 142, 'bucket_count': 89, 'contract_gap_count': 0, 'workorder_count': 0, 'runtime_candidate_count': 0, 'quote_freshness_attribution_present': True, 'row_quote_freshness_attribution_present': True, 'sentinel_quote_freshness_attribution_present': True, 'sentinel_quote_freshness_attribution': {'source_report_type': 'buy_funnel_sentinel', 'decision_authority': 'submit_drought_quote_freshness_attribution_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'forbidden_uses': ['broker_order_submit', 'adm_ldm_training_input', 'general_threshold_ev_input', 'live_auto_promotion'], 'refresh_attempted_count': 32, 'refresh_applied_count': 29, 'still_latency_blocked_after_refresh_count': 17, 'latency_pass_recovered_count': 7, 'order_bundle_submitted_after_refresh_count': 4, 'refresh_subreason_counts': {'observer_quote_refresh_failed_stale': 68, 'ws_snapshot_refresh_failed_invalid': 1, 'ws_snapshot_refresh_failed_stale': 34, 'ws_snapshot_refresh_failed_missing': 37}, 'refresh_block_subreason_counts': {'observer_quote_refresh_failed_stale': 68, 'ws_snapshot_refresh_failed_invalid': 1, 'ws_snapshot_refresh_failed_stale': 34, 'ws_snapshot_refresh_failed_missing': 37}, 'latency_pass_recovered_downstream_counts': {'armed_expired_before_submit': 1, 'budget_pass_no_submit_event': 1, 'no_downstream_event': 1, 'order_bundle_submitted': 4}, 'post_restart_window_policy': 'event_provenance_only'}, 'quote_freshness_resolution_counts': {'refresh_not_attempted_or_not_instrumented': 40, 'refresh_resolved_quote_freshness': 2, 'sim_submit_path_not_applicable': 100}, 'pre_submit_refresh_applied_counts': {'refresh_not_attempted_or_not_instrumented': 40, 'sim_submit_path_not_applicable': 100, 'ws_snapshot_refresh_applied': 2}, 'real_submitted_row_count': 39, 'missing_broker_order_key_count': 0, 'bot_history_broker_order_key_backfill_candidate_count': 0, 'bot_history_broker_order_key_backfill_full_coverage': False, 'bot_history_broker_order_key_exact_mapping_count': 0, 'bot_history_broker_order_key_exact_mapping_full_coverage': False, 'post_submit_provenance_join_resolution': 'no_gap_broker_order_key_present_or_no_missing_rows', 'bot_history_broker_order_key_backfill_candidates': [], 'missing_broker_order_key_rate': 0.0, 'post_submit_provenance_join_gap_raw': False, 'post_submit_provenance_join_gap': False}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 103 | 19 | -0.9002 | `keep_collecting` |
| `actual_order_submitted` | `true` | 39 | 0 | None | `keep_collecting` |
| `broker_order_forbidden` | `true` | 103 | 19 | -0.9002 | `keep_collecting` |
| `broker_order_forbidden` | `false` | 39 | 0 | None | `keep_collecting` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=caution|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 28 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 28 | 9 | -1.9535 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 27 | 2 | -0.0909 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 22 | 3 | 0.7546 | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=safe|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 8 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 6 | 1 | 0.3748 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 4 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 3 | 1 | 0.8643 | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_resolved_quote_freshness|fill=false|submitted=false` | 2 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 2 | 2 | 0.3741 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_consistency_stale|quote_age=quote_age_10s_plus|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 2 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 2 | 1 | -3.5919 | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_lt1s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=caution|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_lt1s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_lt1s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=safe|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=pre_submit_liquidity_guard_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=latency_unknown|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_consistency_stale|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_lt1s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `latency_reason` | `scalp_live_simulator` | 100 | 19 | -0.9002 | `keep_collecting` |
| `latency_reason` | `caution_normal_entry_allowed` | 29 | 0 | None | `keep_collecting` |
| `latency_reason` | `safe_normal_entry_allowed` | 9 | 0 | None | `keep_collecting` |
| `latency_reason` | `latency_reason_unknown` | 1 | 0 | None | `source_quality_workorder` |
| `latency_reason` | `latency_spread_relief_normal_override` | 1 | 0 | None | `keep_collecting` |
| `latency_reason` | `other_danger` | 1 | 0 | None | `keep_collecting` |
| `latency_reason` | `spread_too_wide` | 1 | 0 | None | `keep_collecting` |
| `latency_state` | `simulated` | 100 | 19 | -0.9002 | `keep_collecting` |
| `latency_state` | `caution` | 29 | 0 | None | `keep_collecting` |
| `latency_state` | `safe` | 9 | 0 | None | `keep_collecting` |
| `latency_state` | `danger` | 3 | 0 | None | `keep_collecting` |
| `latency_state` | `latency_unknown` | 1 | 0 | None | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_ok` | 57 | 8 | 0.4618 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 44 | 11 | -1.8908 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_not_available` | 41 | 0 | None | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 57 | 8 | 0.4618 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 101, 'source_row_count': 101, 'bucket_count': 18, 'joined_sample': 95, 'source_quality_adjusted_ev_pct': -1.7701, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 7, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 13 | 13 | -2.2291 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 4 | 4 | -0.4242 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1 | 1 | -1.5266 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1 | 1 | -1.4308 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 76 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 5 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_020_180s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_not_applicable_at_start` | 100 | 19 | -1.7701 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_020_180s` | 1 | 0 | None | `hold_sample` |
| `holding_action` | `WAIT` | 93 | 17 | -1.8044 | `candidate_tighten_or_exclude` |
| `holding_action` | `BUY` | 1 | 1 | -1.5266 | `hold_sample` |
| `holding_action` | `holding_action_not_applicable_at_start` | 6 | 1 | -1.4308 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 1 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 100 | 19 | -1.7701 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 1 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 16 | 15 | -2.1291 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 4 | 4 | -0.4242 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_not_applicable_at_start` | 81 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- `holding_bucket_source_quality_1`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_2`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_3`: `held_bucket` / `held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_4`: `holding_action` / `WAIT` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_5`: `holding_source_stage` / `scalp_sim_holding_started` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_6`: `profit_band` / `profit_lt_neg070` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_7`: `profit_band` / `profit_pos080_pos150` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Exit Bucket Attribution

- decision_authority: `adm_ldm_exit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'exit_rows': 2876, 'source_row_count': 2876, 'bucket_count': 38, 'joined_sample': 365, 'source_quality_adjusted_ev_pct': -1.1566, 'source_quality_gate': 'pass', 'unknown_reason_counts': {'not_applicable': 1, 'join_gap': 8, 'missing_source_field': 1}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 38 | 38 | -1.2337 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 11 | 11 | -0.5645 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 8 | 8 | -1.7497 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 3 | 3 | -2.9643 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` | 2 | 2 | 1.115 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 2 | 2 | -2.3885 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 2 | 2 | 0.8157 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 1 | 1 | -0.6225 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 1 | 1 | -0.03 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 1 | 1 | -3.1218 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 1 | 1 | -1.9776 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 1 | 1 | -4.2271 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 1 | 1 | 1.5441 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 1 | 1 | 0.8991 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_euphoria_context_noop|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown` | 88 | 0 | None | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown` | 2715 | 0 | None | `source_quality_workorder` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 52 | 52 | -0.9787 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 12 | 12 | -1.4286 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 5 | 5 | -2.3152 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 3 | 3 | -1.4001 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 2804 | 1 | -0.6225 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 52 | 52 | -0.9787 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 12 | 12 | -2.0723 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 5 | 5 | -0.0305 | `hold_no_edge` |
| `exit_rule` | `scalp_hard_stop_pct` | 3 | 3 | -2.6329 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 1 | 1 | -0.6225 | `hold_sample` |
| `exit_rule` | `exit_rule_unknown` | 2803 | 0 | None | `source_quality_workorder` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 52 | 52 | -0.9787 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 20 | 20 | -1.6459 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 1 | 1 | -0.6225 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_euphoria_context_noop` | 88 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 2715 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 54 | 54 | -1.4865 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 11 | 11 | -0.5645 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 6 | 6 | 0.0889 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 1 | 1 | -0.03 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 1 | 1 | 1.5441 | `hold_sample` |
| `profit_band` | `profit_unknown` | 2803 | 0 | None | `source_quality_workorder` |

### Exit Bucket Attribution Workorders

- `exit_bucket_source_quality_1`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_2`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_3`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_4`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_5`: `combo_exit_result` / `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_6`: `combo_exit_result` / `source=scalp_sim_euphoria_context_noop|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_7`: `combo_exit_result` / `source=scalp_sim_panic_context_warning|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_8`: `exit_outcome` / `outcome_not_applicable_partial_exit` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_9`: `exit_outcome` / `MISSED_UPSIDE` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_10`: `exit_outcome` / `GOOD_EXIT` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `incremental_notional_ev_pct`
- summary: `{'scale_in_rows': 3257, 'bucket_count': 273, 'edge_bucket_count': 0, 'actionable_bucket_count': 0, 'runtime_authority_blocked_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'arm_counts': {'PYRAMID': 471, 'AVG_DOWN': 2786}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_66_69` | 1125 | 1125 | None | -0.7052 | 0.1511 | `hold_sample` |
| `ai_score_band` | `score_70p` | 830 | 830 | None | -1.1348 | 0.1301 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 590 | 590 | None | -0.5851 | 0.1441 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 491 | 491 | None | -0.5512 | 0.1731 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 201 | 201 | None | -1.1315 | 0.1095 | `hold_sample` |
| `ai_score_band` | `score_unknown` | 20 | 1 | None | None | None | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 3237 | 3237 | None | -0.7966 | 0.1452 | `hold_sample` |
| `ai_score_source` | `sim_scale_in_source_not_scored` | 1 | 1 | None | None | None | `hold_sample` |
| `ai_score_source` | `stage_rule_backfilled` | 19 | 0 | None | None | None | `hold_sample` |
| `arm` | `AVG_DOWN` | 2786 | 2767 | None | -1.0221 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 471 | 471 | None | 0.531 | 1.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 2758 | 2739 | None | -0.9995 | 0.0 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 471 | 471 | None | 0.531 | 1.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 28 | 28 | None | -3.2307 | 0.0 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 434 | 434 | None | 0.4719 | 1.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.23)` | 113 | 113 | None | -0.23 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.33)` | 90 | 90 | None | -0.33 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.39)` | 78 | 78 | None | -0.39 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.88)` | 71 | 71 | None | -0.88 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.13)` | 69 | 69 | None | -0.13 | 0.0 | `hold_sample` |

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
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 1 | 1 | -0.6225 | -0.83 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_lt_neg070` | 1 | 0 | None | None | None | `hold_sample` |
| `confidence_band` | `confidence_070p` | 2 | 1 | -0.6225 | -0.83 | 0.0 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 2 | 1 | -0.6225 | -0.83 | 0.0 | `hold_sample` |
| `overnight_action` | `SELL_TODAY` | 2 | 1 | -0.6225 | -0.83 | 0.0 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 1 | 1 | -0.6225 | -0.83 | 0.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 1 | 0 | None | None | None | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 2 | 1 | -0.6225 | -0.83 | 0.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 2 | 1 | -0.6225 | -0.83 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 2 | 1 | -0.6225 | -0.83 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 2 | 1 | -0.6225 | -0.83 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 1 | 1 | -0.6225 | -0.83 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_decision` | 1 | 0 | None | None | None | `hold_sample` |
| `stage` | `exit` | 1 | 1 | -0.6225 | -0.83 | 0.0 | `hold_sample` |
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
