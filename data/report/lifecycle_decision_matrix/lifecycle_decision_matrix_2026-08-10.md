# Lifecycle Decision Matrix - 2026-08-10

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-08-10`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `1791`
- source_rows_total: `1798`
- retained_rows: `1791`
- dropped_rows_by_source: `{'dedupe': 7}`
- joined_rows: `1146`
- policy_pass_count: `3`
- promote_ready_count: `0`
- entry_bucket_actionable_count: `0`
- entry_bucket_runtime_candidate_count: `0`
- holding_bucket_count/workorders: `14` / `7`
- exit_bucket_count/workorders: `29` / `8`
- scale_in_bucket_actionable_count: `0`
- scale_in_bucket_runtime_candidate_count: `0`
- overnight_bucket_actionable_count: `0`
- overnight_bucket_runtime_candidate_count: `0`
- lifecycle_flow_bucket_count: `32`
- lifecycle_flow_complete_count: `12`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `0` / `12` / `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0093`
- incomplete_flow_reason_counts: `{'missing_submit': 1260, 'missing_holding': 1273, 'missing_exit': 1272, 'missing_entry': 1110, 'sim_record_id_only': 3, 'postclose_exit_without_entry': 2, 'scale_in_noise_only': 1108, 'candidate_id_only': 1107}`
- bucket_directed_sim_probe: `{'observed_row_count': 121, 'matched_row_count': 0, 'background_row_count': 121, 'matched_unique_source_bucket_count': 0, 'match_status_counts': {'no_match': 27, 'not_instrumented': 92, 'policy_disabled': 2}, 'matched_classification_state_counts': {}, 'primary_source': 'matched_bucket_directed_sim_probe_only', 'background_source': 'unmatched_or_policy_missing_sim_observation', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 1, 'route_counts': {'bounded_auxiliary_weight': 1, 'hold_sample': 4}, 'quality_counts': {'observational_only_pending_outcome': 1, 'hold_sample': 4}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 629 | 12 | -0.156 | 0.0229 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 26 | 12 | -0.156 | 0.5538 | `pass` | `NO_CHANGE` | False |
| `holding` | 13 | 12 | -0.7377 | 1.0 | `hold_sample` | `EXIT` | False |
| `scale_in` | 1108 | 1096 | -0.9381 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 15 | 14 | -0.6528 | 1.0 | `hold_sample` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 1286, 'complete_flow_count': 12, 'direct_sim_record_complete_flow_count': 0, 'adm_bridge_complete_flow_count': 12, 'fallback_complete_flow_count': 0, 'direct_flow_zero_diagnostic': {'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'direct_sim_record_flow_count': 3, 'direct_sim_record_incomplete_flow_count': 3, 'direct_sim_record_stage_coverage_counts': {'holding': 1, 'exit': 1}, 'direct_sim_record_incomplete_reason_counts': {'missing_entry': 3, 'missing_submit': 3, 'sim_record_id_only': 3, 'postclose_exit_without_entry': 1, 'missing_holding': 2, 'missing_exit': 2, 'scale_in_noise_only': 2}, 'runtime_effect': False, 'decision_authority': 'ldm_direct_flow_diagnostic_only'}, 'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'incomplete_flow_count': 1274, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 1791, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0093, 'complete_flow_conversion_denominator': 14, 'complete_flow_conversion_rate': 0.8571, 'active_priority_incomplete_seed_count': 164, 'scale_in_followup_event_count': 1108, 'scale_in_unique_flow_count': 811, 'scale_in_noise_flow_count': 1108, 'denominator_exclusion_counts': {'scale_in_noise_flow_excluded': 1108, 'active_priority_incomplete_seed_excluded': 164}, 'conversion_blocker_reason_counts': {'missing_entry': 2, 'missing_submit': 2, 'sim_record_id_only': 1, 'postclose_exit_without_entry': 2, 'missing_holding': 1, 'candidate_id_only': 1}, 'observation_seed_reason_counts': {'missing_submit': 1258, 'missing_holding': 1272, 'missing_exit': 1272, 'missing_entry': 1108, 'sim_record_id_only': 2, 'scale_in_noise_only': 1108, 'candidate_id_only': 1106}, 'join_contract_blocked': False, 'bundle_ev_tuning_state': 'ready_for_bundle_ev_tuning', 'top_incomplete_reason': 'missing_holding', 'stage_identity': {'entry': {'source_row_count': 629, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 629}, 'identity_join_rate': 1.0}, 'submit': {'source_row_count': 26, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 26}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 13, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 12, 'exact_sim_record_id': 1}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 1108, 'identity_missing_count': 0, 'identity_quality_counts': {'exact_sim_record_id': 2, 'candidate_id': 1106}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 15, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 12, 'exact_sim_record_id': 2, 'candidate_id': 1}, 'identity_join_rate': 1.0}}, 'required_stage_source_counts': {'entry': 629, 'submit': 26, 'holding': 13, 'exit': 15}, 'incomplete_flow_reason_counts': {'missing_submit': 1260, 'missing_holding': 1273, 'missing_exit': 1272, 'missing_entry': 1110, 'sim_record_id_only': 3, 'postclose_exit_without_entry': 2, 'scale_in_noise_only': 1108, 'candidate_id_only': 1107}, 'bucket_count': 32, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:5159f83a5b` | 3 | 3 | -0.1136 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:7dd76f2392` | 1 | 1 | -2.1224 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:31a116e56b` | 1 | 1 | -0.7246 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:7664e5a914` | 1 | 1 | -0.1193 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:1fbcba9334` | 1 | 1 | 0.0719 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:f3f2837f26` | 1 | 1 | -1.6262 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:7e17ca9764` | 1 | 1 | -2.1951 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:ce05b30c9f` | 1 | 1 | -0.9949 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:db2aa0a4af` | 1 | 1 | -1.632 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:46ace3ddee` | 1 | 1 | 0.8311 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 1015 | 1004 | -1.067 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 93 | 92 | 0.4685 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:62b3401904` | 1 | 1 | -0.1725 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:075ce13c92` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:f36cc32176` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_ai:c18e731ca8` | 9 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_ai:9a372901ee` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:f9f18a2ca7` | 4 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:6d88d558c7` | 10 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:c50d2ff605` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 629, 'bucket_count': 170, 'actionable_bucket_count': 0, 'source_quality_blocked_bucket_count': 12, 'runtime_candidate_count': 0, 'workorder_count': 10}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 94 | 12 | -0.156 | -1.2583 | 0.4167 | `source_quality_workorder` |
| `chosen_action` | `BUY_DEFENSIVE` | 4 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `NO_BUY_AI` | 479 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_SOURCE_QUALITY` | 7 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_STALE` | 1 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `WAIT_REQUOTE` | 44 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1000_1200` | 44 | 5 | -0.3517 | -0.63 | 0.6 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_0900_1000` | 13 | 4 | 1.0184 | -1.1275 | 0.25 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_0900_1000` | 3 | 1 | -0.0674 | -4.11 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1200_1400` | 2 | 1 | -0.5819 | -3.8 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1200_1400` | 14 | 1 | -3.5375 | 0.47 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=blocked_ai_score|stale=stale_watch|liquidity=liquidity_not_available|overbought=overbought_watch|time=time_0900_1000` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_ok|time=time_1000_1200` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_1000_1200` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1000_1200` | 3 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1400_close` | 3 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_chase_risk|time=time_1400_close` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 1 | 0 | None | None | None | `hold_sample` |
| `score_band` | `score_63_65` | 112 | 10 | -0.1222 | -0.719 | 0.5 | `hold_no_edge` |
| `source_stage` | `scalp_sim_entry_ai_price_skip_order` | 91 | 12 | -0.156 | -1.2583 | 0.4167 | `hold_no_edge` |
| `strength_bucket` | `risk_context_not_available` | 91 | 12 | -0.156 | -1.2583 | 0.4167 | `hold_no_edge` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- `entry_bucket_unknown_source_quality_1`: `chosen_action` / `SKIP_PRE_SUBMIT_SAFETY` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_2`: `combo_entry_spot` / `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_0900_1000` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_3`: `combo_entry_spot` / `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1200_1400` -> `unknown_bucket_source_quality_blocker`
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
- summary: `{'submit_rows': 26, 'bucket_count': 64, 'contract_gap_count': 0, 'workorder_count': 0, 'runtime_candidate_count': 0, 'quote_freshness_attribution_present': True, 'row_quote_freshness_attribution_present': True, 'sentinel_quote_freshness_attribution_present': True, 'sentinel_quote_freshness_attribution': {'source_report_type': 'buy_funnel_sentinel', 'decision_authority': 'submit_drought_quote_freshness_attribution_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'forbidden_uses': ['broker_order_submit', 'adm_ldm_training_input', 'general_threshold_ev_input', 'live_auto_promotion'], 'refresh_attempted_count': 25, 'refresh_applied_count': 12, 'still_latency_blocked_after_refresh_count': 16, 'latency_pass_recovered_count': 1, 'order_bundle_submitted_after_refresh_count': 0, 'refresh_subreason_counts': {'observer_quote_refresh_failed_spread': 1, 'ws_snapshot_refresh_failed_input_snapshot_fresh': 30, 'ws_snapshot_refresh_failed_stale': 4}, 'refresh_block_subreason_counts': {'observer_quote_refresh_failed_spread': 1, 'ws_snapshot_refresh_failed_input_snapshot_fresh': 30, 'ws_snapshot_refresh_failed_stale': 4}, 'latency_pass_recovered_downstream_counts': {'entry_ai_authority_revalidation': 1}, 'post_restart_window_policy': 'event_provenance_only'}, 'quote_freshness_resolution_counts': {'refresh_attempted_unresolved': 6, 'refresh_failed_quote_stale': 3, 'refresh_resolved_quote_freshness': 4, 'sim_submit_path_not_applicable': 13}, 'pre_submit_refresh_applied_counts': {'refresh_attempted_not_applied': 9, 'sim_submit_path_not_applicable': 13, 'ws_snapshot_refresh_applied': 4}, 'real_submitted_row_count': 0, 'missing_broker_order_key_count': 0, 'bot_history_broker_order_key_backfill_candidate_count': 0, 'bot_history_broker_order_key_backfill_full_coverage': False, 'bot_history_broker_order_key_exact_mapping_count': 0, 'bot_history_broker_order_key_exact_mapping_full_coverage': False, 'post_submit_provenance_join_resolution': 'no_gap_broker_order_key_present_or_no_missing_rows', 'bot_history_broker_order_key_backfill_candidates': [], 'missing_broker_order_key_rate': 0.0, 'post_submit_provenance_join_gap_raw': False, 'post_submit_provenance_join_gap': False}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 26 | 12 | -0.156 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 26 | 12 | -0.156 | `keep_collecting` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_attempted_unresolved|fill=false|submitted=false` | 6 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 5 | 5 | -0.1421 | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_resolved_quote_freshness|fill=false|submitted=false` | 4 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_failed_quote_stale|fill=false|submitted=false` | 3 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 3 | 3 | 0.7563 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 3 | 3 | -1.3005 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_block|revalidation=warning_stale_context_or_quote|quote_consistency_stale|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | 0.4716 | `source_quality_workorder` |
| `latency_reason` | `scalp_live_simulator` | 13 | 12 | -0.156 | `keep_collecting` |
| `latency_reason` | `spread_above_caution_below_guard_cap` | 4 | 0 | None | `keep_collecting` |
| `latency_reason` | `spread_too_wide` | 4 | 0 | None | `keep_collecting` |
| `latency_reason` | `ws_age_too_high,spread_too_wide` | 3 | 0 | None | `keep_collecting` |
| `latency_reason` | `quote_stale,ws_age_too_high,spread_too_wide` | 1 | 0 | None | `keep_collecting` |
| `latency_reason` | `ws_age_too_high` | 1 | 0 | None | `keep_collecting` |
| `latency_state` | `danger` | 13 | 0 | None | `keep_collecting` |
| `latency_state` | `simulated` | 13 | 12 | -0.156 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_not_available` | 13 | 0 | None | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 9 | 8 | 0.1948 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 4 | 4 | -0.8575 | `keep_collecting` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 13 | 0 | None | `source_quality_workorder` |
| `liquidity_guard_action` | `would_pass` | 9 | 8 | 0.1948 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 4 | 4 | -0.8575 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 13 | 12 | -0.156 | `keep_collecting` |
| `overbought_bucket` | `overbought_not_available` | 13 | 0 | None | `keep_collecting` |
| `overbought_guard_action` | `overbought_guard_unknown` | 13 | 0 | None | `source_quality_workorder` |
| `overbought_guard_action` | `would_pass` | 13 | 12 | -0.156 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 13 | 12 | -0.156 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `refresh_age_not_instrumented` | 6 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `refresh_age_lt1s` | 5 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `refresh_age_1_3s` | 2 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 13 | 12 | -0.156 | `keep_collecting` |
| `pre_submit_refresh_applied` | `refresh_attempted_not_applied` | 9 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_applied` | `ws_snapshot_refresh_applied` | 4 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_attempted` | `refresh_attempted` | 13 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 13 | 12 | -0.156 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 13 | 12 | -0.156 | `keep_collecting` |
| `pre_submit_refresh_reason` | `ws_snapshot:input_snapshot_fresh` | 6 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_reason` | `ws_snapshot:latest_ws_snapshot_fresh` | 4 | 0 | None | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 13, 'source_row_count': 13, 'bucket_count': 14, 'joined_sample': 60, 'source_quality_adjusted_ev_pct': -0.7377, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 7, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 7 | 7 | -1.0399 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 4 | 4 | -0.601 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | 0.8311 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_not_applicable_at_start` | 12 | 12 | -0.7377 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `holding_action` | `WAIT` | 12 | 12 | -0.7377 | `candidate_tighten_or_exclude` |
| `holding_action` | `SELL_TODAY` | 1 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 12 | 12 | -0.7377 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 1 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 7 | 7 | -1.0399 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 4 | 4 | -0.601 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 1 | 1 | 0.8311 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- `holding_bucket_source_quality_1`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_2`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_3`: `held_bucket` / `held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_4`: `holding_action` / `WAIT` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_5`: `holding_source_stage` / `scalp_sim_holding_started` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_6`: `profit_band` / `profit_lt_neg070` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_7`: `profit_band` / `profit_neg010_pos080` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Exit Bucket Attribution

- decision_authority: `adm_ldm_exit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'exit_rows': 15, 'source_row_count': 15, 'bucket_count': 29, 'joined_sample': 70, 'source_quality_adjusted_ev_pct': -0.6528, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 8, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 3 | 3 | -0.1136 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 2 | 2 | -1.8743 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 2 | 2 | -1.1783 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 1 | 1 | -0.1725 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 1 | 1 | -0.9949 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=NEUTRAL|profit=profit_neg070_neg010` | 1 | 1 | -0.115 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 1 | 1 | -2.1951 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 1 | 1 | -0.1193 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 1 | 1 | 0.8311 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 1 | 1 | 0.0719 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=scalp_sim_panic_context_warning_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 1 | 0 | None | `hold_sample` |
| `exit_outcome` | `MISSED_UPSIDE` | 5 | 5 | 0.0742 | `hold_no_edge` |
| `exit_outcome` | `GOOD_EXIT` | 4 | 4 | -1.5263 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 4 | 4 | -0.8083 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `COMPLETED` | 1 | 1 | -0.1725 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 1 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 5 | 5 | -0.3146 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 4 | 4 | -0.3339 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 3 | 3 | -1.9812 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 2 | 2 | -0.1437 | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_context_warning_not_applicable` | 1 | 0 | None | `hold_sample` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 13 | 13 | -0.6898 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 1 | 1 | -0.1725 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 1 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 7 | 7 | -1.0399 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 4 | 4 | -0.601 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 2 | 2 | -0.1437 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 1 | 1 | 0.8311 | `hold_sample` |
| `profit_band` | `profit_not_applicable_context_noop` | 1 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- `exit_bucket_source_quality_1`: `exit_outcome` / `GOOD_EXIT` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_2`: `exit_outcome` / `NEUTRAL` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_3`: `exit_rule` / `scalp_trailing_take_profit` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_4`: `exit_rule` / `scalp_preset_hard_stop_pct` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_5`: `exit_rule` / `scalp_soft_stop_pct` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_6`: `exit_source_stage` / `sim_post_sell_evaluation` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_7`: `profit_band` / `profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_8`: `profit_band` / `profit_neg010_pos080` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `incremental_notional_ev_pct`
- summary: `{'scale_in_rows': 1108, 'bucket_count': 131, 'edge_bucket_count': 0, 'actionable_bucket_count': 0, 'runtime_authority_blocked_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'arm_counts': {'PYRAMID': 93, 'AVG_DOWN': 1015}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 1095 | 1094 | None | -1.0147 | 0.0823 | `hold_sample` |
| `ai_score_band` | `score_unknown` | 13 | 2 | None | 0.25 | 1.0 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 619 | 619 | None | -0.9948 | 0.0792 | `hold_sample` |
| `ai_score_source` | `holding_ai_not_called` | 185 | 185 | None | -1.2204 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 181 | 181 | None | -0.8694 | 0.1989 | `hold_sample` |
| `ai_score_source` | `not_evaluated_no_ai_score_source` | 73 | 73 | None | -0.6453 | 0.0685 | `hold_sample` |
| `ai_score_source` | `prior_valid` | 36 | 36 | None | -1.7783 | 0.0 | `hold_sample` |
| `ai_score_source` | `sim_scale_in_source_not_scored` | 2 | 2 | None | 0.25 | 1.0 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 1 | 0 | None | None | None | `hold_sample` |
| `ai_score_source` | `stage_rule_backfilled` | 11 | 0 | None | None | None | `hold_sample` |
| `arm` | `AVG_DOWN` | 1015 | 1004 | None | -1.1456 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 93 | 92 | None | 0.442 | 1.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 1013 | 1002 | None | -1.1415 | 0.0 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 93 | 92 | None | 0.442 | 1.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 2 | 2 | None | -3.18 | 0.0 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 83 | 83 | None | 0.4583 | 1.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.79)` | 72 | 72 | None | -0.79 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.22)` | 60 | 60 | None | -1.22 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.98)` | 59 | 59 | None | -0.98 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.08)` | 46 | 46 | None | -1.08 | 0.0 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `adm_ldm_overnight_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'observation_state': 'observed', 'observation_reason': 'overnight_pipeline_rows_available', 'source_artifact_present': True, 'overnight_rows': 2, 'bucket_count': 15, 'actionable_bucket_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'status_counts': {'HOLD_OVERNIGHT': 1, 'SELL_TODAY': 1}}`

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
