# Lifecycle Decision Matrix - 2026-07-27

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-27`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `168`
- source_rows_total: `207`
- retained_rows: `168`
- dropped_rows_by_source: `{'dedupe': 39}`
- joined_rows: `3`
- policy_pass_count: `0`
- promote_ready_count: `0`
- entry_bucket_actionable_count: `0`
- entry_bucket_runtime_candidate_count: `0`
- holding_bucket_count/workorders: `5` / `0`
- exit_bucket_count/workorders: `5` / `0`
- scale_in_bucket_actionable_count: `0`
- scale_in_bucket_runtime_candidate_count: `0`
- overnight_bucket_actionable_count: `0`
- overnight_bucket_runtime_candidate_count: `0`
- lifecycle_flow_bucket_count: `21`
- lifecycle_flow_complete_count: `0`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `0` / `0` / `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0`
- incomplete_flow_reason_counts: `{'missing_submit': 47, 'missing_holding': 63, 'missing_exit': 63, 'missing_entry': 3, 'candidate_id_only': 2, 'scale_in_noise_only': 2, 'sim_record_id_only': 1, 'postclose_exit_without_entry': 1, 'identity_namespace_mismatch': 1, 'join_contract_blocked': 1}`
- bucket_directed_sim_probe: `{'observed_row_count': 2, 'matched_row_count': 0, 'background_row_count': 2, 'matched_unique_source_bucket_count': 0, 'match_status_counts': {'policy_disabled': 2}, 'matched_classification_state_counts': {}, 'primary_source': 'matched_bucket_directed_sim_probe_only', 'background_source': 'unmatched_or_policy_missing_sim_observation', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 0, 'route_counts': {'bounded_auxiliary_weight': 1, 'hold_sample': 4}, 'quality_counts': {'observational_only_pending_outcome': 1, 'hold_sample': 4}}`
- warnings: `['all_stage_policy_entries_below_sample_floor']`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 147 | 0 | None | 0.0 | `hold_sample` | `NO_CHANGE` | False |
| `submit` | 17 | 0 | None | 0.0 | `hold_sample` | `NO_CHANGE` | False |
| `holding` | 1 | 0 | None | 0.0 | `hold_sample` | `NO_CHANGE` | False |
| `scale_in` | 2 | 2 | -1.443 | 0.2 | `hold_sample` | `NO_CHANGE` | False |
| `exit` | 1 | 1 | -0.1725 | 0.1 | `hold_sample` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 64, 'complete_flow_count': 0, 'direct_sim_record_complete_flow_count': 0, 'adm_bridge_complete_flow_count': 0, 'fallback_complete_flow_count': 0, 'direct_flow_zero_diagnostic': {'direct_flow_zero_reason': 'producer_missing_sim_record_on_required_stage', 'direct_flow_zero_closure_status': 'producer_followup_required', 'direct_flow_zero_followup_required': True, 'direct_sim_record_flow_count': 1, 'direct_sim_record_incomplete_flow_count': 1, 'direct_sim_record_stage_coverage_counts': {'holding': 1, 'exit': 1}, 'direct_sim_record_incomplete_reason_counts': {'missing_entry': 1, 'missing_submit': 1, 'sim_record_id_only': 1, 'postclose_exit_without_entry': 1}, 'runtime_effect': False, 'decision_authority': 'ldm_direct_flow_diagnostic_only'}, 'direct_flow_zero_reason': 'producer_missing_sim_record_on_required_stage', 'direct_flow_zero_closure_status': 'producer_followup_required', 'direct_flow_zero_followup_required': True, 'incomplete_flow_count': 64, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 168, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0, 'complete_flow_conversion_denominator': 1, 'complete_flow_conversion_rate': 0.0, 'active_priority_incomplete_seed_count': 61, 'scale_in_followup_event_count': 2, 'scale_in_unique_flow_count': 2, 'scale_in_noise_flow_count': 2, 'denominator_exclusion_counts': {'scale_in_noise_flow_excluded': 2, 'active_priority_incomplete_seed_excluded': 61}, 'conversion_blocker_reason_counts': {'missing_entry': 1, 'missing_submit': 1, 'sim_record_id_only': 1, 'postclose_exit_without_entry': 1, 'identity_namespace_mismatch': 1, 'join_contract_blocked': 1}, 'observation_seed_reason_counts': {'missing_submit': 46, 'missing_holding': 63, 'missing_exit': 63, 'missing_entry': 2, 'candidate_id_only': 2, 'scale_in_noise_only': 2}, 'join_contract_blocked': True, 'bundle_ev_tuning_state': 'blocked_join_gap', 'top_incomplete_reason': 'missing_holding', 'stage_identity': {'entry': {'source_row_count': 147, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 147}, 'identity_join_rate': 1.0}, 'submit': {'source_row_count': 17, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 17}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 1, 'identity_missing_count': 0, 'identity_quality_counts': {'exact_sim_record_id': 1}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 2, 'identity_missing_count': 0, 'identity_quality_counts': {'candidate_id': 2}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 1, 'identity_missing_count': 0, 'identity_quality_counts': {'exact_sim_record_id': 1}, 'identity_join_rate': 1.0}}, 'required_stage_source_counts': {'entry': 147, 'submit': 17, 'holding': 1, 'exit': 1}, 'incomplete_flow_reason_counts': {'missing_submit': 47, 'missing_holding': 63, 'missing_exit': 63, 'missing_entry': 3, 'candidate_id_only': 2, 'scale_in_noise_only': 2, 'sim_record_id_only': 1, 'postclose_exit_without_entry': 1, 'identity_namespace_mismatch': 1, 'join_contract_blocked': 1}, 'bucket_count': 21, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:62b3401904` | 1 | 1 | -0.1725 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 1 | 1 | -3.006 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 1 | 1 | 0.12 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_ai_c:6376c75255` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_ai_c:2315da1c23` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:425fb814b4` | 3 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:54101985e8` | 4 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:81a1a398fd` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:07390fbd3e` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:f2f2f3d14e` | 14 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:f51f5dbd6a` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:de60314e2b` | 2 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:70a865069d` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:31f7c4caf3` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:34865a272b` | 5 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:5566b1f38e` | 2 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:c69a7be5bd` | 9 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:b528e0c876` | 9 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:43870ece59` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:5fc5abcf3e` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 147, 'bucket_count': 83, 'actionable_bucket_count': 0, 'source_quality_blocked_bucket_count': 16, 'runtime_candidate_count': 0, 'workorder_count': 10}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `BUY_DEFENSIVE` | 7 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `BUY_NOW` | 5 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `NO_BUY_AI` | 91 | 0 | None | None | None | `source_quality_workorder` |
| `chosen_action` | `SKIP_STALE` | 1 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `WAIT_REQUOTE` | 43 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1400_close` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_1200_1400` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1400_close` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1400_close` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_1200_1400` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=stale_block|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1400_close` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1200_1400` | 3 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_0900_1000` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1000_1200` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1400_close` | 3 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=stale_watch|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1200_1400` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=stale_watch|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1400_close` | 5 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_chase_risk|time=time_0900_1000` | 1 | 0 | None | None | None | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- `entry_bucket_unknown_source_quality_1`: `chosen_action` / `NO_BUY_AI` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_2`: `combo_entry_spot` / `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_0900_1000` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_3`: `combo_entry_spot` / `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1000_1200` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_4`: `combo_entry_spot` / `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1200_1400` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_5`: `combo_entry_spot` / `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1400_close` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_6`: `exit_rule` / `exit_unknown` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_7`: `liquidity_bucket` / `liquidity_not_available` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_8`: `overbought_bucket` / `overbought_not_available` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_9`: `score_band` / `score_lt60` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_10`: `source_stage` / `scalp_entry_action_decision_snapshot` -> `unknown_bucket_source_quality_blocker`

## Submit Bucket Attribution

- decision_authority: `adm_ldm_submit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'submit_rows': 17, 'bucket_count': 40, 'contract_gap_count': 0, 'workorder_count': 0, 'runtime_candidate_count': 0, 'quote_freshness_attribution_present': True, 'row_quote_freshness_attribution_present': True, 'sentinel_quote_freshness_attribution_present': True, 'sentinel_quote_freshness_attribution': {'source_report_type': 'buy_funnel_sentinel', 'decision_authority': 'submit_drought_quote_freshness_attribution_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'forbidden_uses': ['broker_order_submit', 'adm_ldm_training_input', 'general_threshold_ev_input', 'live_auto_promotion'], 'refresh_attempted_count': 27, 'refresh_applied_count': 19, 'still_latency_blocked_after_refresh_count': 6, 'latency_pass_recovered_count': 3, 'order_bundle_submitted_after_refresh_count': 1, 'refresh_subreason_counts': {'observer_quote_refresh_failed_stale': 1, 'ws_snapshot_refresh_failed_stale': 6}, 'refresh_block_subreason_counts': {'observer_quote_refresh_failed_stale': 1, 'ws_snapshot_refresh_failed_stale': 6}, 'latency_pass_recovered_downstream_counts': {'order_bundle_submitted': 1, 'price_guard_or_revalidation': 2}, 'post_restart_window_policy': 'event_provenance_only'}, 'quote_freshness_resolution_counts': {'refresh_failed_quote_stale': 1, 'refresh_not_attempted_or_not_instrumented': 2, 'refresh_resolved_quote_freshness': 14}, 'pre_submit_refresh_applied_counts': {'refresh_attempted_not_applied': 1, 'refresh_not_attempted_or_not_instrumented': 2, 'ws_snapshot_refresh_applied': 14}, 'real_submitted_row_count': 2, 'missing_broker_order_key_count': 0, 'bot_history_broker_order_key_backfill_candidate_count': 0, 'bot_history_broker_order_key_backfill_full_coverage': False, 'bot_history_broker_order_key_exact_mapping_count': 0, 'bot_history_broker_order_key_exact_mapping_full_coverage': False, 'post_submit_provenance_join_resolution': 'no_gap_broker_order_key_present_or_no_missing_rows', 'bot_history_broker_order_key_backfill_candidates': [], 'missing_broker_order_key_rate': 0.0, 'post_submit_provenance_join_gap_raw': False, 'post_submit_provenance_join_gap': False}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 15 | 0 | None | `keep_collecting` |
| `actual_order_submitted` | `true` | 2 | 0 | None | `keep_collecting` |
| `broker_order_forbidden` | `true` | 15 | 0 | None | `keep_collecting` |
| `broker_order_forbidden` | `false` | 2 | 0 | None | `keep_collecting` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_resolved_quote_freshness|fill=false|submitted=false` | 14 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=caution|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 2 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_failed_quote_stale|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `latency_reason` | `spread_too_wide` | 12 | 0 | None | `keep_collecting` |
| `latency_reason` | `ws_age_too_high,spread_too_wide` | 3 | 0 | None | `keep_collecting` |
| `latency_reason` | `caution_normal_entry_allowed` | 2 | 0 | None | `keep_collecting` |
| `latency_state` | `danger` | 15 | 0 | None | `keep_collecting` |
| `latency_state` | `caution` | 2 | 0 | None | `keep_collecting` |
| `liquidity_bucket` | `liquidity_not_available` | 17 | 0 | None | `keep_collecting` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 17 | 0 | None | `source_quality_workorder` |
| `overbought_bucket` | `overbought_not_available` | 17 | 0 | None | `keep_collecting` |
| `overbought_guard_action` | `overbought_guard_unknown` | 17 | 0 | None | `source_quality_workorder` |
| `pre_submit_refresh_age_bucket` | `refresh_age_lt1s` | 15 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `refresh_age_not_instrumented` | 2 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_applied` | `ws_snapshot_refresh_applied` | 14 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_applied` | `refresh_not_attempted_or_not_instrumented` | 2 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_applied` | `refresh_attempted_not_applied` | 1 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_attempted` | `refresh_attempted` | 15 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_attempted` | `refresh_not_attempted_or_not_instrumented` | 2 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_reason` | `ws_snapshot:latest_ws_snapshot_fresh` | 14 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_reason` | `refresh_reason_not_instrumented` | 2 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_reason` | `ws_snapshot:latest_snapshot_stale` | 1 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_source` | `ws_manager_latest_data` | 15 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_source` | `refresh_source_not_instrumented` | 2 | 0 | None | `keep_collecting` |
| `price_below_bid_bucket` | `price_below_bid_unknown` | 17 | 0 | None | `source_quality_workorder` |
| `price_resolution_bucket` | `price_not_available_pre_submit` | 15 | 0 | None | `keep_collecting` |
| `price_resolution_bucket` | `resolved_price` | 2 | 0 | None | `keep_collecting` |
| `quote_age_bucket` | `quote_age_unknown` | 15 | 0 | None | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_1_3s` | 2 | 0 | None | `keep_collecting` |
| `quote_freshness_resolution_state` | `refresh_resolved_quote_freshness` | 14 | 0 | None | `keep_collecting` |
| `quote_freshness_resolution_state` | `refresh_not_attempted_or_not_instrumented` | 2 | 0 | None | `keep_collecting` |
| `quote_freshness_resolution_state` | `refresh_failed_quote_stale` | 1 | 0 | None | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 17 | 0 | None | `keep_collecting` |
| `submit_source_stage` | `latency_block` | 15 | 0 | None | `keep_collecting` |
| `submit_source_stage` | `order_bundle_submitted` | 2 | 0 | None | `keep_collecting` |
| `would_limit_fill` | `false` | 17 | 0 | None | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 1, 'source_row_count': 1, 'bucket_count': 5, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': None, 'source_quality_gate': 'hold_sample', 'unknown_reason_counts': {}, 'workorder_count': 0, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 1 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 1 | 0 | None | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `adm_ldm_exit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'exit_rows': 1, 'source_row_count': 1, 'bucket_count': 5, 'joined_sample': 5, 'source_quality_adjusted_ev_pct': -0.1725, 'source_quality_gate': 'hold_sample', 'unknown_reason_counts': {}, 'workorder_count': 0, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 1 | 1 | -0.1725 | `hold_sample` |
| `exit_outcome` | `COMPLETED` | 1 | 1 | -0.1725 | `hold_sample` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 1 | 1 | -0.1725 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 1 | 1 | -0.1725 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 1 | 1 | -0.1725 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `incremental_notional_ev_pct`
- summary: `{'scale_in_rows': 2, 'bucket_count': 17, 'edge_bucket_count': 0, 'actionable_bucket_count': 0, 'runtime_authority_blocked_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'arm_counts': {'PYRAMID': 1, 'AVG_DOWN': 1}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 2 | 2 | None | -1.885 | 0.5 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 2 | 2 | None | -1.885 | 0.5 | `hold_sample` |
| `arm` | `AVG_DOWN` | 1 | 1 | None | -3.84 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 1 | 1 | None | 0.07 | 1.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 1 | 1 | None | -3.84 | 0.0 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 1 | 1 | None | 0.07 | 1.0 | `hold_sample` |
| `blocker_reason` | `probe_expand_forbidden` | 1 | 1 | None | -3.84 | 0.0 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 1 | 1 | None | 0.07 | 1.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 1 | 1 | None | -3.84 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 1 | 1 | None | 0.07 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 2 | 2 | None | -1.885 | 0.5 | `hold_sample` |
| `price_guard_reason` | `price_guard_none` | 2 | 2 | None | -1.885 | 0.5 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 1 | 1 | None | -3.84 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 1 | 1 | None | 0.07 | 1.0 | `hold_sample` |
| `qty_reason` | `qty_none` | 2 | 2 | None | -1.885 | 0.5 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 2 | 2 | None | -1.885 | 0.5 | `hold_sample` |
| `time_bucket` | `time_unknown` | 2 | 2 | None | -1.885 | 0.5 | `hold_sample` |

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
