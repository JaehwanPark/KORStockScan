# Lifecycle Decision Matrix - 2026-08-26

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-08-26`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `4778`
- source_rows_total: `4799`
- retained_rows: `4778`
- dropped_rows_by_source: `{'dedupe': 21}`
- joined_rows: `2913`
- policy_pass_count: `5`
- promote_ready_count: `0`
- entry_bucket_actionable_count: `4`
- entry_bucket_runtime_candidate_count: `0`
- holding_bucket_count/workorders: `21` / `5`
- exit_bucket_count/workorders: `38` / `10`
- scale_in_bucket_actionable_count: `0`
- scale_in_bucket_runtime_candidate_count: `0`
- overnight_bucket_actionable_count: `0`
- overnight_bucket_runtime_candidate_count: `0`
- lifecycle_flow_bucket_count: `34`
- lifecycle_flow_complete_count: `11`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `0` / `11` / `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0026`
- incomplete_flow_reason_counts: `{'missing_holding': 4161, 'missing_exit': 3020, 'missing_submit': 4108, 'missing_entry': 4013, 'candidate_id_only': 4012, 'scale_in_noise_only': 2871, 'sim_record_id_only': 2, 'postclose_exit_without_entry': 1142}`
- bucket_directed_sim_probe: `{'observed_row_count': 1193, 'matched_row_count': 0, 'background_row_count': 1193, 'matched_unique_source_bucket_count': 0, 'match_status_counts': {'no_match': 43, 'not_instrumented': 1150}, 'matched_classification_state_counts': {}, 'primary_source': 'matched_bucket_directed_sim_probe_only', 'background_source': 'unmatched_or_policy_missing_sim_observation', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 0, 'route_counts': {'bounded_auxiliary_weight': 1, 'hold_sample': 4}, 'quality_counts': {'observational_only_pending_outcome': 1, 'hold_sample': 4}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 655 | 11 | -0.4514 | 0.0185 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 70 | 15 | -1.221 | 0.3214 | `pass` | `NO_CHANGE` | False |
| `holding` | 20 | 15 | -1.0779 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 2871 | 2852 | -0.9877 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 1162 | 20 | -1.0238 | 0.0344 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 4173, 'complete_flow_count': 11, 'direct_sim_record_complete_flow_count': 0, 'adm_bridge_complete_flow_count': 11, 'fallback_complete_flow_count': 0, 'direct_flow_zero_diagnostic': {'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'direct_sim_record_flow_count': 2, 'direct_sim_record_incomplete_flow_count': 2, 'direct_sim_record_stage_coverage_counts': {}, 'direct_sim_record_incomplete_reason_counts': {'missing_entry': 2, 'missing_submit': 2, 'missing_holding': 2, 'missing_exit': 2, 'sim_record_id_only': 2, 'scale_in_noise_only': 2}, 'runtime_effect': False, 'decision_authority': 'ldm_direct_flow_diagnostic_only'}, 'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'incomplete_flow_count': 4162, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 4778, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0026, 'complete_flow_conversion_denominator': 1153, 'complete_flow_conversion_rate': 0.0095, 'active_priority_incomplete_seed_count': 149, 'scale_in_followup_event_count': 2871, 'scale_in_unique_flow_count': 2164, 'scale_in_noise_flow_count': 2871, 'denominator_exclusion_counts': {'scale_in_noise_flow_excluded': 2871, 'active_priority_incomplete_seed_excluded': 149}, 'conversion_blocker_reason_counts': {'missing_entry': 1142, 'missing_submit': 1142, 'missing_holding': 1142, 'candidate_id_only': 1142, 'postclose_exit_without_entry': 1142}, 'observation_seed_reason_counts': {'missing_holding': 3019, 'missing_exit': 3020, 'missing_submit': 2966, 'missing_entry': 2871, 'candidate_id_only': 2870, 'scale_in_noise_only': 2871, 'sim_record_id_only': 2}, 'join_contract_blocked': False, 'bundle_ev_tuning_state': 'ready_for_bundle_ev_tuning', 'top_incomplete_reason': 'missing_holding', 'stage_identity': {'entry': {'source_row_count': 655, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 654, 'candidate_id': 1}, 'identity_join_rate': 1.0}, 'submit': {'source_row_count': 70, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 70}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 20, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 20}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 2871, 'identity_missing_count': 0, 'identity_quality_counts': {'candidate_id': 2869, 'exact_sim_record_id': 2}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 1162, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 20, 'candidate_id': 1142}, 'identity_join_rate': 1.0}}, 'required_stage_source_counts': {'entry': 655, 'submit': 70, 'holding': 20, 'exit': 1162}, 'incomplete_flow_reason_counts': {'missing_holding': 4161, 'missing_exit': 3020, 'missing_submit': 4108, 'missing_entry': 4013, 'candidate_id_only': 4012, 'scale_in_noise_only': 2871, 'sim_record_id_only': 2, 'postclose_exit_without_entry': 1142}, 'bucket_count': 34, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:f58154b780` | 1 | 1 | -1.31 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:05c0ca21ce` | 1 | 1 | 0.045 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:7ee2fdca81` | 1 | 1 | 0.0318 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:0cb91a7ba6` | 1 | 1 | -0.8 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:c4090b7214` | 1 | 1 | -1.2917 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:e0bfa00978` | 1 | 1 | -2.3584 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:9f5b0bdb1f` | 1 | 1 | -0.285 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:7bce7f4a3a` | 1 | 1 | -2.3081 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:fd77333652` | 1 | 1 | -2.8037 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:e2542c8a2a` | 1 | 1 | 0.1838 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:aeaa204df4` | 1 | 1 | -1.9575 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 2793 | 2774 | -1.0254 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 78 | 78 | 0.3555 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:f9f18a2ca7` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:d61d009728` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:542cd2bc91` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:c50d2ff605` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:f2f2f3d14e` | 2 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:de60314e2b` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:7b1e064efb` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 655, 'bucket_count': 167, 'actionable_bucket_count': 4, 'source_quality_blocked_bucket_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 4}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `NO_BUY_AI` | 300 | 11 | -0.4514 | -1.3836 | 0.3636 | `candidate_tighten_or_exclude` |
| `chosen_action` | `ALLOW_LEVEL1_RISK_OFF_ENTRY` | 1 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `BUY_DEFENSIVE` | 55 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 30 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_SOURCE_QUALITY` | 3 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_STALE` | 3 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `WAIT_REQUOTE` | 263 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 3 | 2 | -0.0088 | -0.715 | 0.5 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_1000_1200` | 2 | 2 | 0.3473 | -1.515 | 0.5 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_1200_1400` | 4 | 2 | 0.4923 | -1.4 | 0.5 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_1200_1400` | 1 | 1 | -0.2958 | -2.61 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_chase_risk|time=time_1000_1200` | 1 | 1 | -2.4083 | -3.16 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 1 | 1 | 0.2019 | -1.6 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 13 | 1 | -3.4427 | 1.0 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_watch|time=time_1000_1200` | 4 | 1 | -0.6821 | -1.59 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_1000_1200` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_ok|time=time_1400_close` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 1 | 0 | None | None | None | `hold_sample` |
| `liquidity_bucket` | `liquidity_high` | 246 | 11 | -0.4514 | -1.3836 | 0.3636 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 557 | 11 | -0.4514 | -1.3836 | 0.3636 | `candidate_tighten_or_exclude` |
| `stale_bucket` | `fresh` | 331 | 10 | -0.4283 | -1.363 | 0.4 | `candidate_tighten_or_exclude` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- `entry_bucket_source_quality_1`: `chosen_action` / `NO_BUY_AI` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_2`: `liquidity_bucket` / `liquidity_high` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_3`: `source_stage` / `scalp_entry_action_decision_snapshot` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_4`: `stale_bucket` / `fresh` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`

## Submit Bucket Attribution

- decision_authority: `adm_ldm_submit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'submit_rows': 70, 'bucket_count': 78, 'contract_gap_count': 0, 'workorder_count': 0, 'runtime_candidate_count': 0, 'quote_freshness_attribution_present': True, 'row_quote_freshness_attribution_present': True, 'sentinel_quote_freshness_attribution_present': True, 'sentinel_quote_freshness_attribution': {'source_report_type': 'buy_funnel_sentinel', 'decision_authority': 'submit_drought_quote_freshness_attribution_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'forbidden_uses': ['broker_order_submit', 'adm_ldm_training_input', 'general_threshold_ev_input', 'live_auto_promotion'], 'refresh_attempted_count': 93, 'refresh_applied_count': 79, 'still_latency_blocked_after_refresh_count': 50, 'latency_pass_recovered_count': 26, 'order_bundle_submitted_after_refresh_count': 0, 'refresh_subreason_counts': {'observer_quote_refresh_failed_invalid': 1, 'observer_quote_refresh_failed_stale': 10, 'ws_snapshot_refresh_failed_input_snapshot_fresh': 194, 'ws_snapshot_refresh_failed_invalid': 1, 'ws_snapshot_refresh_failed_stale': 16}, 'refresh_block_subreason_counts': {'observer_quote_refresh_failed_invalid': 1, 'observer_quote_refresh_failed_stale': 10, 'ws_snapshot_refresh_failed_input_snapshot_fresh': 194, 'ws_snapshot_refresh_failed_invalid': 1, 'ws_snapshot_refresh_failed_stale': 16}, 'latency_pass_recovered_downstream_counts': {'entry_ai_authority_revalidation': 26}, 'post_restart_window_policy': 'event_provenance_only'}, 'quote_freshness_resolution_counts': {'refresh_attempted_unresolved': 15, 'refresh_failed_quote_stale': 3, 'refresh_not_attempted_or_not_instrumented': 1, 'refresh_resolved_quote_freshness': 34, 'sim_submit_path_not_applicable': 17}, 'pre_submit_refresh_applied_counts': {'refresh_attempted_not_applied': 18, 'refresh_not_attempted_or_not_instrumented': 1, 'sim_submit_path_not_applicable': 17, 'ws_snapshot_refresh_applied': 34}, 'real_submitted_row_count': 0, 'missing_broker_order_key_count': 0, 'bot_history_broker_order_key_backfill_candidate_count': 0, 'bot_history_broker_order_key_backfill_full_coverage': False, 'bot_history_broker_order_key_exact_mapping_count': 0, 'bot_history_broker_order_key_exact_mapping_full_coverage': False, 'post_submit_provenance_join_resolution': 'no_gap_broker_order_key_present_or_no_missing_rows', 'bot_history_broker_order_key_backfill_candidates': [], 'missing_broker_order_key_rate': 0.0, 'post_submit_provenance_join_gap_raw': False, 'post_submit_provenance_join_gap': False}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 70 | 15 | -1.221 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 70 | 15 | -1.221 | `keep_collecting` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_resolved_quote_freshness|fill=false|submitted=false` | 34 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_attempted_unresolved|fill=false|submitted=false` | 15 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 7 | 7 | -0.6575 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 6 | 4 | -0.0907 | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_failed_quote_stale|fill=false|submitted=false` | 3 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 3 | 3 | -2.0106 | `source_quality_workorder` |
| `combo_submit_quality` | `source=entry_submit_revalidation_block|revalidation=warning_observed_mark_gap_unresolved|quote_age=quote_age_3_10s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=latency_unknown|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_overbought_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=pullback_or_rebreak_not_confirmed|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | -7.3174 | `source_quality_workorder` |
| `latency_reason` | `spread_above_caution_below_guard_cap` | 25 | 0 | None | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 17 | 15 | -1.221 | `keep_collecting` |
| `latency_reason` | `spread_too_wide` | 13 | 0 | None | `keep_collecting` |
| `latency_reason` | `ws_age_too_high` | 10 | 0 | None | `keep_collecting` |
| `latency_reason` | `ws_age_too_high,spread_too_wide` | 3 | 0 | None | `keep_collecting` |
| `latency_reason` | `latency_reason_unknown` | 1 | 0 | None | `source_quality_workorder` |
| `latency_reason` | `quote_stale,ws_age_too_high,spread_too_wide` | 1 | 0 | None | `keep_collecting` |
| `latency_state` | `danger` | 52 | 0 | None | `keep_collecting` |
| `latency_state` | `simulated` | 17 | 15 | -1.221 | `keep_collecting` |
| `latency_state` | `latency_unknown` | 1 | 0 | None | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_not_available` | 53 | 0 | None | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 14 | 12 | -1.0236 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 3 | 3 | -2.0106 | `keep_collecting` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 53 | 0 | None | `source_quality_workorder` |
| `liquidity_guard_action` | `would_pass` | 14 | 12 | -1.0236 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 3 | 3 | -2.0106 | `keep_collecting` |
| `overbought_bucket` | `overbought_not_available` | 53 | 0 | None | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 16 | 14 | -0.7855 | `keep_collecting` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 1 | 1 | -7.3174 | `keep_collecting` |
| `overbought_guard_action` | `overbought_guard_unknown` | 53 | 0 | None | `source_quality_workorder` |
| `overbought_guard_action` | `would_pass` | 16 | 14 | -0.7855 | `keep_collecting` |
| `overbought_guard_action` | `would_block` | 1 | 1 | -7.3174 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `refresh_age_lt1s` | 34 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 17 | 15 | -1.221 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `refresh_age_not_instrumented` | 16 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `refresh_age_1_3s` | 3 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_applied` | `ws_snapshot_refresh_applied` | 34 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_applied` | `refresh_attempted_not_applied` | 18 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 17 | 15 | -1.221 | `keep_collecting` |
| `pre_submit_refresh_applied` | `refresh_not_attempted_or_not_instrumented` | 1 | 0 | None | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 20, 'source_row_count': 20, 'bucket_count': 21, 'joined_sample': 75, 'source_quality_adjusted_ev_pct': -1.0779, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 5, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 8 | 8 | -1.4718 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 3 | 3 | 0.1319 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | -0.63 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 1 | 1 | -1.2217 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 1 | 1 | -2.3081 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_not_applicable_at_start` | 17 | 15 | -1.0779 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s_plus` | 3 | 0 | None | `hold_sample` |
| `holding_action` | `WAIT` | 17 | 15 | -1.0779 | `candidate_tighten_or_exclude` |
| `holding_action` | `SELL_TODAY` | 3 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 17 | 15 | -1.0779 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 3 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 9 | 8 | -1.4718 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 4 | 3 | 0.1319 | `hold_no_edge` |
| `profit_band` | `profit_pos080_pos150` | 2 | 2 | -0.63 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 2 | 1 | -1.2217 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 1 | 1 | -2.3081 | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 2 | 0 | None | `hold_sample` |

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
- summary: `{'exit_rows': 1162, 'source_row_count': 1162, 'bucket_count': 38, 'joined_sample': 100, 'source_quality_adjusted_ev_pct': -1.0238, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 2 | 2 | -1.055 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 2 | 2 | -0.6487 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 2 | 2 | -1.3451 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 2 | 2 | -0.63 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 2 | 2 | 0.2726 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_lt_neg070` | 1 | 1 | -1.9575 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg010_pos080` | 1 | 1 | 0.045 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 1 | 1 | -0.285 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 1 | 1 | -2.3584 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | -1.1463 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 1 | 1 | -1.4784 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 1 | 1 | -0.1496 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=NEUTRAL|profit=profit_neg070_neg010` | 1 | 1 | -1.2217 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 1 | 1 | -2.8037 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 1 | 1 | -2.3081 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=scalp_sim_panic_context_warning_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 1142 | 0 | None | `hold_sample` |
| `exit_outcome` | `GOOD_EXIT` | 7 | 7 | -1.4797 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 5 | 5 | -0.3948 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `COMPLETED` | 3 | 3 | -0.7325 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 3 | 3 | -1.2789 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 2 | 2 | -1.055 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 1142 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 6 | 6 | -0.8412 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 5 | 5 | -0.6046 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 4 | 4 | -1.2005 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 3 | 3 | -1.8313 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 2 | 2 | -1.055 | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_context_warning_not_applicable` | 1142 | 0 | None | `hold_sample` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 15 | 15 | -1.0779 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 3 | 3 | -0.7325 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 2 | 2 | -1.055 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 1142 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 11 | 11 | -1.4402 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 4 | 4 | 0.1101 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 2 | 2 | -0.7533 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 2 | 2 | -0.63 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 1 | 1 | -2.3081 | `hold_sample` |
| `profit_band` | `profit_not_applicable_context_noop` | 1142 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- `exit_bucket_source_quality_1`: `exit_outcome` / `GOOD_EXIT` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_2`: `exit_outcome` / `NEUTRAL` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_3`: `exit_outcome` / `COMPLETED` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_4`: `exit_outcome` / `MISSED_UPSIDE` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_5`: `exit_rule` / `scalp_sim_overnight_sell_today` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_6`: `exit_rule` / `scalp_trailing_take_profit` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_7`: `exit_rule` / `scalp_preset_hard_stop_pct` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_8`: `exit_rule` / `scalp_soft_stop_pct` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_9`: `exit_source_stage` / `sim_post_sell_evaluation` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_10`: `exit_source_stage` / `scalp_sim_overnight_sell_today` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `incremental_notional_ev_pct`
- summary: `{'scale_in_rows': 2871, 'bucket_count': 208, 'edge_bucket_count': 0, 'actionable_bucket_count': 0, 'runtime_authority_blocked_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'arm_counts': {'AVG_DOWN': 2793, 'PYRAMID': 78}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 2851 | 2851 | None | -1.0801 | 0.0228 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 1 | 1 | None | 1.26 | 1.0 | `hold_sample` |
| `ai_score_band` | `score_unknown` | 19 | 0 | None | None | None | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 1756 | 1756 | None | -1.0631 | 0.0251 | `hold_sample` |
| `ai_score_source` | `live` | 483 | 483 | None | -1.0901 | 0.0166 | `hold_sample` |
| `ai_score_source` | `holding_ai_not_called` | 295 | 295 | None | -1.2351 | 0.0068 | `hold_sample` |
| `ai_score_source` | `not_evaluated_no_ai_score_source` | 175 | 175 | None | -0.795 | 0.0229 | `hold_sample` |
| `ai_score_source` | `prior_valid` | 141 | 141 | None | -1.2724 | 0.0567 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 2 | 2 | None | -0.935 | 0.0 | `hold_sample` |
| `ai_score_source` | `stage_rule_backfilled` | 19 | 0 | None | None | None | `hold_sample` |
| `arm` | `AVG_DOWN` | 2793 | 2774 | None | -1.1188 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 78 | 78 | None | 0.3254 | 0.8462 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 2775 | 2756 | None | -1.1056 | 0.0 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 78 | 78 | None | 0.3254 | 0.8462 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 18 | 18 | None | -3.1428 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.23)` | 190 | 190 | None | -0.23 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.34)` | 134 | 134 | None | -0.34 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.46)` | 96 | 96 | None | -0.46 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.66)` | 96 | 96 | None | -0.66 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.57)` | 92 | 92 | None | -0.57 | 0.0 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `adm_ldm_overnight_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'observation_state': 'observed', 'observation_reason': 'overnight_pipeline_rows_available', 'source_artifact_present': True, 'overnight_rows': 6, 'bucket_count': 22, 'actionable_bucket_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'status_counts': {'HOLD_OVERNIGHT': 3, 'SELL_TODAY': 3}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 1 | 1 | -1.9575 | -2.61 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 1 | 1 | 0.045 | 0.06 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 1 | 1 | -0.285 | -0.38 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_lt_neg070` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg010_pos080` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 1 | 0 | None | None | None | `hold_sample` |
| `confidence_band` | `confidence_070p` | 6 | 3 | -0.7325 | -0.9767 | 0.3333 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 6 | 3 | -0.7325 | -0.9767 | 0.3333 | `hold_sample` |
| `overnight_action` | `SELL_TODAY` | 6 | 3 | -0.7325 | -0.9767 | 0.3333 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 3 | 3 | -0.7325 | -0.9767 | 0.3333 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 3 | 0 | None | None | None | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 4 | 2 | -1.1213 | -1.495 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 2 | 1 | 0.045 | 0.06 | 1.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 6 | 3 | -0.7325 | -0.9767 | 0.3333 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 2 | 1 | -1.9575 | -2.61 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 2 | 1 | 0.045 | 0.06 | 1.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 2 | 1 | -0.285 | -0.38 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 6 | 3 | -0.7325 | -0.9767 | 0.3333 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 3 | 3 | -0.7325 | -0.9767 | 0.3333 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_decision` | 3 | 0 | None | None | None | `hold_sample` |

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
