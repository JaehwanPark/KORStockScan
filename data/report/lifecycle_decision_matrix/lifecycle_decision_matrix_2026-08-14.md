# Lifecycle Decision Matrix - 2026-08-14

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-08-14`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `2964`
- source_rows_total: `3520`
- retained_rows: `2964`
- dropped_rows_by_source: `{'dedupe': 556}`
- joined_rows: `1141`
- policy_pass_count: `2`
- promote_ready_count: `0`
- entry_bucket_actionable_count: `0`
- entry_bucket_runtime_candidate_count: `0`
- holding_bucket_count/workorders: `18` / `6`
- exit_bucket_count/workorders: `30` / `10`
- scale_in_bucket_actionable_count: `0`
- scale_in_bucket_runtime_candidate_count: `0`
- overnight_bucket_actionable_count: `0`
- overnight_bucket_runtime_candidate_count: `0`
- lifecycle_flow_bucket_count: `43`
- lifecycle_flow_complete_count: `6`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `0` / `6` / `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0025`
- incomplete_flow_reason_counts: `{'missing_submit': 2290, 'missing_holding': 2366, 'missing_exit': 1301, 'missing_entry': 2191, 'postclose_exit_without_entry': 1076, 'sim_record_id_only': 6, 'scale_in_noise_only': 1115, 'candidate_id_only': 2186}`
- bucket_directed_sim_probe: `{'observed_row_count': 1147, 'matched_row_count': 33, 'background_row_count': 1114, 'matched_unique_source_bucket_count': 1, 'match_status_counts': {'matched': 33, 'no_match': 26, 'not_instrumented': 1088}, 'matched_classification_state_counts': {'lifecycle_flow_sim_probe_candidate': 33}, 'primary_source': 'matched_bucket_directed_sim_probe_only', 'background_source': 'unmatched_or_policy_missing_sim_observation', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 0, 'route_counts': {'bounded_auxiliary_weight': 1, 'hold_sample': 4}, 'quality_counts': {'observational_only_pending_outcome': 1, 'hold_sample': 4}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 632 | 7 | -0.4153 | 0.0078 | `hold_sample` | `WAIT_REQUOTE` | False |
| `submit` | 104 | 9 | -0.8741 | 0.0779 | `hold_sample` | `NO_CHANGE` | False |
| `holding` | 26 | 9 | -1.0539 | 0.3115 | `hold_sample` | `EXIT` | False |
| `scale_in` | 1115 | 1101 | -0.8093 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 1087 | 15 | -0.2044 | 0.0207 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 2383, 'complete_flow_count': 6, 'direct_sim_record_complete_flow_count': 0, 'adm_bridge_complete_flow_count': 6, 'fallback_complete_flow_count': 0, 'direct_flow_zero_diagnostic': {'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'direct_sim_record_flow_count': 6, 'direct_sim_record_incomplete_flow_count': 6, 'direct_sim_record_stage_coverage_counts': {'holding': 2, 'exit': 2}, 'direct_sim_record_incomplete_reason_counts': {'missing_entry': 6, 'missing_submit': 6, 'missing_holding': 4, 'missing_exit': 4, 'sim_record_id_only': 6, 'scale_in_noise_only': 4, 'postclose_exit_without_entry': 2}, 'runtime_effect': False, 'decision_authority': 'ldm_direct_flow_diagnostic_only'}, 'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'incomplete_flow_count': 2377, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 2964, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0025, 'complete_flow_conversion_denominator': 1082, 'complete_flow_conversion_rate': 0.0055, 'active_priority_incomplete_seed_count': 186, 'scale_in_followup_event_count': 1115, 'scale_in_unique_flow_count': 806, 'scale_in_noise_flow_count': 1115, 'denominator_exclusion_counts': {'scale_in_noise_flow_excluded': 1115, 'active_priority_incomplete_seed_excluded': 186}, 'conversion_blocker_reason_counts': {'missing_entry': 1076, 'missing_submit': 1076, 'missing_holding': 1074, 'postclose_exit_without_entry': 1076, 'sim_record_id_only': 2, 'candidate_id_only': 1072}, 'observation_seed_reason_counts': {'missing_submit': 1214, 'missing_holding': 1292, 'missing_exit': 1301, 'missing_entry': 1115, 'sim_record_id_only': 4, 'scale_in_noise_only': 1115, 'candidate_id_only': 1114}, 'join_contract_blocked': False, 'bundle_ev_tuning_state': 'ready_for_bundle_ev_tuning', 'top_incomplete_reason': 'missing_holding', 'stage_identity': {'entry': {'source_row_count': 632, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 629, 'candidate_id': 3}, 'identity_join_rate': 1.0}, 'submit': {'source_row_count': 104, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 104}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 26, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 24, 'exact_sim_record_id': 2}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 1115, 'identity_missing_count': 0, 'identity_quality_counts': {'exact_sim_record_id': 4, 'candidate_id': 1111}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 1087, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 13, 'exact_sim_record_id': 2, 'candidate_id': 1072}, 'identity_join_rate': 1.0}}, 'required_stage_source_counts': {'entry': 632, 'submit': 104, 'holding': 26, 'exit': 1087}, 'incomplete_flow_reason_counts': {'missing_submit': 2290, 'missing_holding': 2366, 'missing_exit': 1301, 'missing_entry': 2191, 'postclose_exit_without_entry': 1076, 'sim_record_id_only': 6, 'scale_in_noise_only': 1115, 'candidate_id_only': 2186}, 'bucket_count': 43, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:f548b6989d` | 1 | 1 | -0.34 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:927a4c8e9e` | 1 | 1 | -0.2151 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:a6af469504` | 1 | 1 | -0.96 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:0cb91a7ba6` | 1 | 1 | -0.54 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:77f502e017` | 1 | 1 | -2.4209 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:0df2a3d41d` | 1 | 1 | 0.3217 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 1111 | 1097 | -0.8135 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 4 | 4 | 0.362 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:f658be39ac` | 2 | 2 | -1.86 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:5603187fa1` | 2 | 2 | 4.0844 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:9d1a12917f` | 1 | 1 | -2.31 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:7de5848ca3` | 2 | 1 | -2.65 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_ai_c:2315da1c23` | 2 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:24aeb192e4` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:28d2f4d6f7` | 2 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:b846e1412a` | 2 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:3149875e3b` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:c3e248a0f4` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:90c7bf43c5` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:425fb814b4` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 632, 'bucket_count': 149, 'actionable_bucket_count': 0, 'source_quality_blocked_bucket_count': 17, 'runtime_candidate_count': 0, 'workorder_count': 10}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `NO_BUY_AI` | 294 | 6 | -0.1929 | -0.4733 | 0.5 | `source_quality_workorder` |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 20 | 1 | -1.7499 | -3.02 | 0.0 | `source_quality_workorder` |
| `chosen_action` | `ALLOW_BOTTOMING_ENTRY` | 1 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `ALLOW_LEVEL1_RISK_OFF_ENTRY` | 2 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `BUY_DEFENSIVE` | 60 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `BUY_NOW` | 2 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_STALE` | 2 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `WAIT_REQUOTE` | 251 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 6 | 3 | -0.0044 | -0.9367 | 0.3333 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_ok|time=time_1400_close` | 4 | 1 | -0.1805 | 0.86 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_1000_1200` | 5 | 1 | -1.0012 | 0.62 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_0900_1000` | 1 | 1 | -1.7499 | -3.02 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 11 | 1 | 0.0376 | -1.51 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_1400_close` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_1400_close` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=blocked_ai_score|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1400_close` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=blocked_ai_score|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_1400_close` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1400_close` | 4 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_1400_close` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1400_close` | 4 | 0 | None | None | None | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- `entry_bucket_unknown_source_quality_1`: `chosen_action` / `NO_BUY_AI` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_2`: `chosen_action` / `SKIP_PRE_SUBMIT_SAFETY` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_3`: `combo_entry_spot` / `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_0900_1000` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_4`: `combo_entry_spot` / `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1000_1200` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_5`: `combo_entry_spot` / `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1200_1400` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_6`: `combo_entry_spot` / `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1400_close` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_7`: `exit_rule` / `exit_unknown` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_8`: `liquidity_bucket` / `liquidity_not_available` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_9`: `overbought_bucket` / `overbought_not_available` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_10`: `score_band` / `score_lt60` -> `unknown_bucket_source_quality_blocker`

## Submit Bucket Attribution

- decision_authority: `adm_ldm_submit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'submit_rows': 104, 'bucket_count': 87, 'contract_gap_count': 0, 'workorder_count': 0, 'runtime_candidate_count': 0, 'quote_freshness_attribution_present': True, 'row_quote_freshness_attribution_present': True, 'sentinel_quote_freshness_attribution_present': True, 'sentinel_quote_freshness_attribution': {'source_report_type': 'buy_funnel_sentinel', 'decision_authority': 'submit_drought_quote_freshness_attribution_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'forbidden_uses': ['broker_order_submit', 'adm_ldm_training_input', 'general_threshold_ev_input', 'live_auto_promotion'], 'refresh_attempted_count': 115, 'refresh_applied_count': 49, 'still_latency_blocked_after_refresh_count': 92, 'latency_pass_recovered_count': 14, 'order_bundle_submitted_after_refresh_count': 0, 'refresh_subreason_counts': {'observer_quote_refresh_failed_stale': 2, 'ws_snapshot_refresh_failed_input_snapshot_fresh': 197, 'ws_snapshot_refresh_failed_stale': 13}, 'refresh_block_subreason_counts': {'observer_quote_refresh_failed_stale': 2, 'ws_snapshot_refresh_failed_input_snapshot_fresh': 197, 'ws_snapshot_refresh_failed_stale': 13}, 'latency_pass_recovered_downstream_counts': {'armed_expired_before_submit': 2, 'entry_ai_authority_revalidation': 12}, 'post_restart_window_policy': 'event_provenance_only'}, 'quote_freshness_resolution_counts': {'refresh_attempted_unresolved': 47, 'refresh_failed_quote_stale': 6, 'refresh_not_attempted_or_not_instrumented': 12, 'refresh_resolved_quote_freshness': 15, 'sim_submit_path_not_applicable': 24}, 'pre_submit_refresh_applied_counts': {'refresh_attempted_not_applied': 53, 'refresh_not_attempted_or_not_instrumented': 12, 'sim_submit_path_not_applicable': 24, 'ws_snapshot_refresh_applied': 15}, 'real_submitted_row_count': 10, 'missing_broker_order_key_count': 0, 'bot_history_broker_order_key_backfill_candidate_count': 0, 'bot_history_broker_order_key_backfill_full_coverage': False, 'bot_history_broker_order_key_exact_mapping_count': 0, 'bot_history_broker_order_key_exact_mapping_full_coverage': False, 'post_submit_provenance_join_resolution': 'no_gap_broker_order_key_present_or_no_missing_rows', 'bot_history_broker_order_key_backfill_candidates': [], 'missing_broker_order_key_rate': 0.0, 'post_submit_provenance_join_gap_raw': False, 'post_submit_provenance_join_gap': False}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 94 | 9 | -0.8741 | `keep_collecting` |
| `actual_order_submitted` | `true` | 10 | 0 | None | `keep_collecting` |
| `broker_order_forbidden` | `true` | 94 | 9 | -0.8741 | `keep_collecting` |
| `broker_order_forbidden` | `false` | 10 | 0 | None | `keep_collecting` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_attempted_unresolved|fill=false|submitted=false` | 47 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_resolved_quote_freshness|fill=false|submitted=false` | 15 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 14 | 4 | 0.0566 | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=caution|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 8 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_failed_quote_stale|fill=false|submitted=false` | 6 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 6 | 2 | -2.48 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 3 | 2 | -0.6918 | `source_quality_workorder` |
| `combo_submit_quality` | `source=pre_submit_liquidity_guard_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=liquidity_guard_unknown|overbought=overbought_ok|latency=latency_unknown|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=false` | 2 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=safe|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_lt1s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=safe|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | -1.7499 | `source_quality_workorder` |
| `latency_reason` | `scalp_live_simulator` | 24 | 9 | -0.8741 | `keep_collecting` |
| `latency_reason` | `spread_above_caution_below_guard_cap` | 23 | 0 | None | `keep_collecting` |
| `latency_reason` | `ws_age_too_high` | 18 | 0 | None | `keep_collecting` |
| `latency_reason` | `spread_too_wide` | 15 | 0 | None | `keep_collecting` |
| `latency_reason` | `ws_age_too_high,spread_too_wide` | 11 | 0 | None | `keep_collecting` |
| `latency_reason` | `caution_normal_entry_allowed` | 8 | 0 | None | `keep_collecting` |
| `latency_reason` | `latency_reason_unknown` | 2 | 0 | None | `source_quality_workorder` |
| `latency_reason` | `safe_normal_entry_allowed` | 2 | 0 | None | `keep_collecting` |
| `latency_reason` | `quote_stale,ws_age_too_high,spread_too_wide` | 1 | 0 | None | `keep_collecting` |
| `latency_state` | `danger` | 68 | 0 | None | `keep_collecting` |
| `latency_state` | `simulated` | 24 | 9 | -0.8741 | `keep_collecting` |
| `latency_state` | `caution` | 8 | 0 | None | `keep_collecting` |
| `latency_state` | `latency_unknown` | 2 | 0 | None | `source_quality_workorder` |
| `latency_state` | `safe` | 2 | 0 | None | `keep_collecting` |
| `liquidity_bucket` | `liquidity_not_available` | 78 | 0 | None | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 17 | 6 | -0.1929 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 9 | 3 | -2.2366 | `keep_collecting` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 80 | 0 | None | `source_quality_workorder` |
| `liquidity_guard_action` | `would_pass` | 17 | 6 | -0.1929 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 7 | 3 | -2.2366 | `keep_collecting` |
| `overbought_bucket` | `overbought_not_available` | 78 | 0 | None | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 22 | 6 | -0.789 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 4 | 3 | -1.0445 | `keep_collecting` |
| `overbought_guard_action` | `overbought_guard_unknown` | 80 | 0 | None | `source_quality_workorder` |
| `overbought_guard_action` | `would_pass` | 24 | 9 | -0.8741 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 26, 'source_row_count': 26, 'bucket_count': 18, 'joined_sample': 45, 'source_quality_adjusted_ev_pct': -1.0539, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 6, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 5 | 5 | -1.3551 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 2 | 2 | -0.1906 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1 | 1 | -2.65 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | 0.3217 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 10 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 5 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_not_applicable_at_start` | 24 | 9 | -1.0539 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s` | 2 | 0 | None | `hold_sample` |
| `holding_action` | `WAIT` | 15 | 5 | -1.3551 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 9 | 4 | -0.6774 | `candidate_tighten_or_exclude` |
| `holding_action` | `SELL_TODAY` | 2 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 24 | 9 | -1.0539 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 2 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 8 | 6 | -1.5709 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 2 | 2 | -0.1906 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 1 | 1 | 0.3217 | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 15 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- `holding_bucket_source_quality_1`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_2`: `held_bucket` / `held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_3`: `holding_action` / `WAIT` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_4`: `holding_action` / `holding_action_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_5`: `holding_source_stage` / `scalp_sim_holding_started` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_6`: `profit_band` / `profit_lt_neg070` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Exit Bucket Attribution

- decision_authority: `adm_ldm_exit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'exit_rows': 1087, 'source_row_count': 1087, 'bucket_count': 30, 'joined_sample': 75, 'source_quality_adjusted_ev_pct': -0.2044, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 3 | 3 | -0.6815 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_lt_neg070` | 2 | 2 | -1.86 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 2 | 2 | -1.055 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 2 | 2 | -0.44 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 2 | 2 | -0.1906 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300_plus` | 2 | 2 | 4.0844 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 1 | 1 | -2.4209 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 1 | 1 | 0.3217 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=scalp_sim_panic_context_warning_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 1072 | 0 | None | `hold_sample` |
| `exit_outcome` | `NEUTRAL` | 5 | 5 | 1.2249 | `candidate_recovery_or_relax` |
| `exit_outcome` | `GOOD_EXIT` | 4 | 4 | -0.6201 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 4 | 4 | -0.7475 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `COMPLETED` | 2 | 2 | -1.86 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 1072 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 5 | 5 | 1.6219 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 4 | 4 | -0.7475 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 3 | 3 | -0.6815 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 2 | 2 | -1.86 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 1 | 1 | -2.4209 | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_context_warning_not_applicable` | 1072 | 0 | None | `hold_sample` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 9 | 9 | 0.4049 | `candidate_recovery_or_relax` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 4 | 4 | -0.7475 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 2 | 2 | -1.86 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 1072 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 8 | 8 | -1.2869 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 2 | 2 | -0.1906 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 2 | 2 | -0.44 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 2 | 2 | 4.0844 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 1 | 1 | 0.3217 | `hold_sample` |
| `profit_band` | `profit_not_applicable_context_noop` | 1072 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- `exit_bucket_source_quality_1`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_2`: `exit_outcome` / `NEUTRAL` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_3`: `exit_outcome` / `GOOD_EXIT` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_4`: `exit_outcome` / `outcome_not_applicable_partial_exit` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_5`: `exit_rule` / `scalp_trailing_take_profit` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_6`: `exit_rule` / `scalp_sim_panic_lifecycle_partial_exit` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_7`: `exit_rule` / `scalp_preset_hard_stop_pct` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_8`: `exit_source_stage` / `sim_post_sell_evaluation` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_9`: `exit_source_stage` / `scalp_sim_partial_sell_order_assumed_filled` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_10`: `profit_band` / `profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `incremental_notional_ev_pct`
- summary: `{'scale_in_rows': 1115, 'bucket_count': 105, 'edge_bucket_count': 0, 'actionable_bucket_count': 0, 'runtime_authority_blocked_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'arm_counts': {'PYRAMID': 4, 'AVG_DOWN': 1111}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 1100 | 1100 | None | -0.8791 | 0.0027 | `hold_sample` |
| `ai_score_band` | `score_unknown` | 15 | 1 | None | None | None | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 609 | 609 | None | -0.9477 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 173 | 173 | None | -0.8088 | 0.0173 | `hold_sample` |
| `ai_score_source` | `holding_ai_not_called` | 154 | 154 | None | -0.8527 | 0.0 | `hold_sample` |
| `ai_score_source` | `not_evaluated_no_ai_score_source` | 141 | 141 | None | -0.67 | 0.0 | `hold_sample` |
| `ai_score_source` | `prior_valid` | 20 | 20 | None | -1.071 | 0.0 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 3 | 3 | None | -0.9033 | 0.0 | `hold_sample` |
| `ai_score_source` | `sim_scale_in_source_not_scored` | 1 | 1 | None | None | None | `hold_sample` |
| `ai_score_source` | `stage_rule_backfilled` | 14 | 0 | None | None | None | `hold_sample` |
| `arm` | `AVG_DOWN` | 1111 | 1097 | None | -0.883 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 4 | 4 | None | 0.5367 | 1.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 1111 | 1097 | None | -0.883 | 0.0 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 4 | 4 | None | 0.5367 | 1.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.99)` | 103 | 103 | None | -0.99 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.67)` | 89 | 89 | None | -0.67 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.78)` | 86 | 86 | None | -0.78 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.84)` | 84 | 84 | None | -0.84 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.14)` | 76 | 76 | None | -1.14 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.60)` | 44 | 44 | None | -0.6 | 0.0 | `hold_sample` |

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
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 2 | 2 | -1.86 | -2.48 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_lt_neg070` | 2 | 0 | None | None | None | `hold_sample` |
| `confidence_band` | `confidence_070p` | 4 | 2 | -1.86 | -2.48 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 4 | 2 | -1.86 | -2.48 | 0.0 | `hold_sample` |
| `overnight_action` | `SELL_TODAY` | 4 | 2 | -1.86 | -2.48 | 0.0 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 2 | 2 | -1.86 | -2.48 | 0.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 2 | 0 | None | None | None | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 4 | 2 | -1.86 | -2.48 | 0.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 4 | 2 | -1.86 | -2.48 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 4 | 2 | -1.86 | -2.48 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 4 | 2 | -1.86 | -2.48 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 2 | 2 | -1.86 | -2.48 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_decision` | 2 | 0 | None | None | None | `hold_sample` |
| `stage` | `exit` | 2 | 2 | -1.86 | -2.48 | 0.0 | `hold_sample` |
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
