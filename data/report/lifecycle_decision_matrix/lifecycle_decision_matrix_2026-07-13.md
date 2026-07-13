# Lifecycle Decision Matrix - 2026-07-13

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-13`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `603`
- source_rows_total: `1173`
- retained_rows: `603`
- dropped_rows_by_source: `{'dedupe': 570}`
- joined_rows: `349`
- policy_pass_count: `2`
- promote_ready_count: `0`
- entry_bucket_actionable_count: `0`
- entry_bucket_runtime_candidate_count: `0`
- holding_bucket_count/workorders: `16` / `5`
- exit_bucket_count/workorders: `34` / `10`
- scale_in_bucket_actionable_count: `0`
- scale_in_bucket_runtime_candidate_count: `0`
- overnight_bucket_actionable_count: `0`
- overnight_bucket_runtime_candidate_count: `0`
- lifecycle_flow_bucket_count: `39`
- lifecycle_flow_complete_count: `9`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `0` / `9` / `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0213`
- incomplete_flow_reason_counts: `{'missing_submit': 386, 'missing_holding': 409, 'missing_exit': 363, 'missing_entry': 340, 'candidate_id_only': 340, 'scale_in_noise_only': 289, 'sim_record_id_only': 14, 'postclose_exit_without_entry': 51}`
- bucket_directed_sim_probe: `{'observed_row_count': 109, 'matched_row_count': 0, 'background_row_count': 109, 'matched_unique_source_bucket_count': 0, 'match_status_counts': {'not_instrumented': 50, 'policy_disabled': 2, 'policy_missing': 57}, 'matched_classification_state_counts': {}, 'primary_source': 'matched_bucket_directed_sim_probe_only', 'background_source': 'unmatched_or_policy_missing_sim_observation', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 0, 'route_counts': {'bounded_auxiliary_weight': 1, 'hold_sample': 4}, 'quality_counts': {'observational_only_pending_outcome': 1, 'hold_sample': 4}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 182 | 7 | -0.6835 | 0.0269 | `hold_sample` | `WAIT_REQUOTE` | False |
| `submit` | 43 | 9 | -0.5489 | 0.1884 | `hold_sample` | `NO_CHANGE` | False |
| `holding` | 16 | 9 | -1.5228 | 0.5062 | `hold_sample` | `EXIT` | False |
| `scale_in` | 302 | 301 | -1.0384 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 60 | 23 | -1.1777 | 0.8817 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 423, 'complete_flow_count': 9, 'direct_sim_record_complete_flow_count': 0, 'adm_bridge_complete_flow_count': 9, 'fallback_complete_flow_count': 0, 'direct_flow_zero_diagnostic': {'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'direct_sim_record_flow_count': 14, 'direct_sim_record_incomplete_flow_count': 14, 'direct_sim_record_stage_coverage_counts': {'holding': 1, 'exit': 14}, 'direct_sim_record_incomplete_reason_counts': {'missing_entry': 14, 'missing_submit': 14, 'sim_record_id_only': 14, 'postclose_exit_without_entry': 14, 'missing_holding': 13}, 'runtime_effect': False, 'decision_authority': 'ldm_direct_flow_diagnostic_only'}, 'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'incomplete_flow_count': 414, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 603, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0213, 'complete_flow_conversion_denominator': 60, 'complete_flow_conversion_rate': 0.15, 'active_priority_incomplete_seed_count': 74, 'scale_in_followup_event_count': 302, 'scale_in_unique_flow_count': 264, 'scale_in_noise_flow_count': 289, 'denominator_exclusion_counts': {'scale_in_noise_flow_excluded': 289, 'active_priority_incomplete_seed_excluded': 74}, 'conversion_blocker_reason_counts': {'missing_entry': 51, 'missing_submit': 51, 'sim_record_id_only': 14, 'postclose_exit_without_entry': 51, 'missing_holding': 50, 'candidate_id_only': 37}, 'observation_seed_reason_counts': {'missing_submit': 335, 'missing_holding': 359, 'missing_exit': 363, 'missing_entry': 289, 'candidate_id_only': 303, 'scale_in_noise_only': 289}, 'join_contract_blocked': False, 'bundle_ev_tuning_state': 'ready_for_bundle_ev_tuning', 'top_incomplete_reason': 'missing_holding', 'stage_identity': {'entry': {'source_row_count': 182, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 168, 'candidate_id': 14}, 'identity_join_rate': 1.0}, 'submit': {'source_row_count': 43, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 43}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 16, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 15, 'exact_sim_record_id': 1}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 302, 'identity_missing_count': 0, 'identity_quality_counts': {'candidate_id': 289, 'exact_sim_record_id': 13}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 60, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 9, 'exact_sim_record_id': 14, 'candidate_id': 37}, 'identity_join_rate': 1.0}}, 'required_stage_source_counts': {'entry': 182, 'submit': 43, 'holding': 16, 'exit': 60}, 'incomplete_flow_reason_counts': {'missing_submit': 386, 'missing_holding': 409, 'missing_exit': 363, 'missing_entry': 340, 'candidate_id_only': 340, 'scale_in_noise_only': 289, 'sim_record_id_only': 14, 'postclose_exit_without_entry': 51}, 'bucket_count': 39, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:8058890631` | 1 | 1 | -0.7511 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:ad0146c320` | 1 | 1 | -1.8153 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:48ff71b3f6` | 1 | 1 | -1.1279 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:cd91d32ec0` | 1 | 1 | -1.5739 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:452add0e70` | 1 | 1 | -2.4233 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:4605369e6e` | 1 | 1 | -1.5939 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:43a09edbd6` | 1 | 1 | -1.4744 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:7f6445a63b` | 1 | 1 | -2.8982 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:b5897179f3` | 1 | 1 | -0.0474 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 281 | 280 | -1.0838 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 13 | 13 | -1.0162 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 8 | 8 | 0.69 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:19270f18a8` | 1 | 1 | -0.1725 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:0e304b8817` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:01a26e930a` | 4 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:542cd2bc91` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:c3e248a0f4` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:3e4df63664` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:425fb814b4` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:54101985e8` | 6 | 0 | None | `hold_sample` | `join_contract_blocked` |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 182, 'bucket_count': 89, 'actionable_bucket_count': 0, 'source_quality_blocked_bucket_count': 12, 'runtime_candidate_count': 0, 'workorder_count': 10}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `NO_BUY_AI` | 81 | 3 | -0.0535 | -3.31 | 0.0 | `source_quality_workorder` |
| `chosen_action` | `BUY_DEFENSIVE` | 3 | 2 | -0.4418 | -1.12 | 0.5 | `hold_sample` |
| `chosen_action` | `WAIT_REQUOTE` | 83 | 2 | -1.87 | -1.6 | 0.5 | `hold_sample` |
| `chosen_action` | `ALLOW_LEVEL1_RISK_OFF_ENTRY` | 14 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_STALE` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 1 | 1 | 0.3681 | -1.84 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 1 | 1 | -0.6599 | -5.02 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1200_1400` | 3 | 1 | -2.3311 | 0.1 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=stale_watch|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1000_1200` | 1 | 1 | 0.4167 | -3.52 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=stale_watch|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1200_1400` | 3 | 1 | -1.4089 | -3.3 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 18 | 1 | 0.1313 | -3.07 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_watch|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_0900_1000` | 5 | 1 | -1.3004 | 1.28 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=ai_confirmed|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=ai_confirmed|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 3 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_sim_panic_level1_entry_observed|stale=fresh_or_unflagged|liquidity=liquidity_state_normal|overbought=panic_entry_overbought_not_applicable|time=time_0900_1000` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_sim_panic_level1_entry_observed|stale=fresh_or_unflagged|liquidity=liquidity_state_normal|overbought=panic_entry_overbought_not_applicable|time=time_1000_1200` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_sim_panic_level1_entry_observed|stale=fresh_or_unflagged|liquidity=liquidity_state_normal|overbought=panic_entry_overbought_not_applicable|time=time_1200_1400` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_sim_panic_level1_entry_observed|stale=fresh_or_unflagged|liquidity=liquidity_state_normal|overbought=panic_entry_overbought_not_applicable|time=time_1200_1400` | 1 | 0 | None | None | None | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- `entry_bucket_unknown_source_quality_1`: `chosen_action` / `NO_BUY_AI` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_2`: `combo_entry_spot` / `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1200_1400` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_3`: `combo_entry_spot` / `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1400_close` -> `unknown_bucket_source_quality_blocker`
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
- summary: `{'submit_rows': 43, 'bucket_count': 83, 'contract_gap_count': 0, 'workorder_count': 0, 'runtime_candidate_count': 0, 'quote_freshness_attribution_present': True, 'row_quote_freshness_attribution_present': True, 'sentinel_quote_freshness_attribution_present': True, 'sentinel_quote_freshness_attribution': {'source_report_type': 'buy_funnel_sentinel', 'decision_authority': 'submit_drought_quote_freshness_attribution_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'forbidden_uses': ['broker_order_submit', 'adm_ldm_training_input', 'general_threshold_ev_input', 'live_auto_promotion'], 'refresh_attempted_count': 22, 'refresh_applied_count': 15, 'still_latency_blocked_after_refresh_count': 8, 'latency_pass_recovered_count': 1, 'order_bundle_submitted_after_refresh_count': 0, 'refresh_subreason_counts': {'observer_quote_refresh_failed_stale': 2, 'ws_snapshot_refresh_failed_stale': 12}, 'refresh_block_subreason_counts': {'observer_quote_refresh_failed_stale': 2, 'ws_snapshot_refresh_failed_stale': 12}, 'latency_pass_recovered_downstream_counts': {'price_guard_or_revalidation': 1}, 'post_restart_window_policy': 'event_provenance_only'}, 'quote_freshness_resolution_counts': {'refresh_failed_quote_stale': 7, 'refresh_not_attempted_or_not_instrumented': 4, 'refresh_resolved_quote_freshness': 17, 'sim_submit_path_not_applicable': 15}, 'pre_submit_refresh_applied_counts': {'refresh_attempted_not_applied': 7, 'refresh_not_attempted_or_not_instrumented': 4, 'sim_submit_path_not_applicable': 15, 'ws_snapshot_refresh_applied': 17}, 'real_submitted_row_count': 4, 'missing_broker_order_key_count': 0, 'bot_history_broker_order_key_backfill_candidate_count': 0, 'bot_history_broker_order_key_backfill_full_coverage': False, 'bot_history_broker_order_key_exact_mapping_count': 0, 'bot_history_broker_order_key_exact_mapping_full_coverage': False, 'post_submit_provenance_join_resolution': 'no_gap_broker_order_key_present_or_no_missing_rows', 'bot_history_broker_order_key_backfill_candidates': [], 'missing_broker_order_key_rate': 0.0, 'post_submit_provenance_join_gap_raw': False, 'post_submit_provenance_join_gap': False}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 39 | 9 | -0.5489 | `keep_collecting` |
| `actual_order_submitted` | `true` | 4 | 0 | None | `keep_collecting` |
| `broker_order_forbidden` | `true` | 39 | 9 | -0.5489 | `keep_collecting` |
| `broker_order_forbidden` | `false` | 4 | 0 | None | `keep_collecting` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_resolved_quote_freshness|fill=false|submitted=false` | 17 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_failed_quote_stale|fill=false|submitted=false` | 7 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 6 | 3 | -0.0535 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 4 | 1 | -0.5262 | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=caution|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 2 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 2 | 2 | -1.87 | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=warning_observed_mark_gap_allowed|quote_age=quote_age_1_3s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=safe|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=warning_observed_mark_gap_allowed|quote_age=quote_age_3_10s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=caution|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 1 | 1 | -1.3004 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 1 | 1 | 0.4167 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | 0.3699 | `source_quality_workorder` |
| `latency_reason` | `scalp_live_simulator` | 15 | 9 | -0.5489 | `keep_collecting` |
| `latency_reason` | `spread_above_caution_below_guard_cap` | 15 | 0 | None | `keep_collecting` |
| `latency_reason` | `spread_too_wide` | 4 | 0 | None | `keep_collecting` |
| `latency_reason` | `caution_normal_entry_allowed` | 3 | 0 | None | `keep_collecting` |
| `latency_reason` | `ws_age_too_high` | 2 | 0 | None | `keep_collecting` |
| `latency_reason` | `ws_age_too_high,spread_too_wide` | 2 | 0 | None | `keep_collecting` |
| `latency_reason` | `quote_stale,ws_age_too_high` | 1 | 0 | None | `keep_collecting` |
| `latency_reason` | `safe_normal_entry_allowed` | 1 | 0 | None | `keep_collecting` |
| `latency_state` | `danger` | 24 | 0 | None | `keep_collecting` |
| `latency_state` | `simulated` | 15 | 9 | -0.5489 | `keep_collecting` |
| `latency_state` | `caution` | 3 | 0 | None | `keep_collecting` |
| `latency_state` | `safe` | 1 | 0 | None | `keep_collecting` |
| `liquidity_bucket` | `liquidity_not_available` | 28 | 0 | None | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 10 | 7 | -0.6835 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 5 | 2 | -0.0781 | `keep_collecting` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 28 | 0 | None | `source_quality_workorder` |
| `liquidity_guard_action` | `would_pass` | 10 | 7 | -0.6835 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 5 | 2 | -0.0781 | `keep_collecting` |
| `overbought_bucket` | `overbought_not_available` | 28 | 0 | None | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 12 | 6 | 0.0166 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 3 | 3 | -1.6801 | `keep_collecting` |
| `overbought_guard_action` | `overbought_guard_unknown` | 28 | 0 | None | `source_quality_workorder` |
| `overbought_guard_action` | `would_pass` | 15 | 9 | -0.5489 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `refresh_age_lt1s` | 17 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 15 | 9 | -0.5489 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 16, 'source_row_count': 16, 'bucket_count': 16, 'joined_sample': 45, 'source_quality_adjusted_ev_pct': -1.5228, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 5, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 7 | 7 | -1.79 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | -1.1279 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | -0.0474 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 6 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_not_applicable_at_start` | 15 | 9 | -1.5228 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `holding_action` | `WAIT` | 15 | 9 | -1.5228 | `candidate_tighten_or_exclude` |
| `holding_action` | `SELL_TODAY` | 1 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 15 | 9 | -1.5228 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 1 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 7 | 7 | -1.79 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 1 | 1 | -1.1279 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 1 | 1 | -0.0474 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 1 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 6 | 0 | None | `hold_sample` |

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
- summary: `{'exit_rows': 60, 'source_row_count': 60, 'bucket_count': 34, 'joined_sample': 115, 'source_quality_adjusted_ev_pct': -1.1777, 'source_quality_gate': 'pass', 'unknown_reason_counts': {'not_applicable': 1, 'missing_source_field': 1}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 8 | 8 | -1.245 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 5 | 5 | -0.65 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 3 | 3 | -1.9442 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 2 | 2 | -1.5242 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 1 | 1 | -0.1725 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | -2.8982 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 1 | 1 | -0.7511 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 1 | 1 | -0.0474 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 1 | 1 | -1.1279 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_euphoria_context_noop|rule=scalp_sim_euphoria_context_noop_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 14 | 0 | None | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=scalp_sim_panic_context_warning_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 23 | 0 | None | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 13 | 13 | -1.0162 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 4 | 4 | -1.47 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 4 | 4 | -1.2318 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 1 | 1 | -2.8982 | `hold_sample` |
| `exit_outcome` | `outcome_unknown` | 1 | 1 | -0.1725 | `source_quality_workorder` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 37 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 13 | 13 | -1.0162 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 5 | 5 | -1.7762 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 2 | 2 | -1.8247 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 2 | 2 | -0.5877 | `hold_sample` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 1 | 1 | -0.1725 | `hold_sample` |
| `exit_rule` | `scalp_sim_euphoria_context_noop_not_applicable` | 14 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_context_warning_not_applicable` | 23 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 13 | 13 | -1.0162 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 9 | 9 | -1.5228 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 1 | 1 | -0.1725 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_euphoria_context_noop` | 14 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 23 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 15 | 15 | -1.4993 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 6 | 6 | -0.5704 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 1 | 1 | -1.1279 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 1 | 1 | -0.0474 | `hold_sample` |
| `profit_band` | `profit_not_applicable_context_noop` | 37 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- `exit_bucket_source_quality_1`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_2`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_3`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_4`: `combo_exit_result` / `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_5`: `exit_outcome` / `outcome_not_applicable_partial_exit` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_6`: `exit_outcome` / `GOOD_EXIT` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_7`: `exit_outcome` / `NEUTRAL` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_8`: `exit_outcome` / `outcome_unknown` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_9`: `exit_rule` / `scalp_sim_panic_lifecycle_partial_exit` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_10`: `exit_rule` / `scalp_soft_stop_pct` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `incremental_notional_ev_pct`
- summary: `{'scale_in_rows': 302, 'bucket_count': 137, 'edge_bucket_count': 0, 'actionable_bucket_count': 0, 'runtime_authority_blocked_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'arm_counts': {'PYRAMID': 8, 'AVG_DOWN': 294}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 297 | 297 | None | -1.2727 | 0.0202 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 2 | 2 | None | -0.175 | 0.5 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 1 | 1 | None | -1.23 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_70p` | 1 | 1 | None | 1.93 | 1.0 | `hold_sample` |
| `ai_score_band` | `score_unknown` | 1 | 0 | None | None | None | `hold_sample` |
| `ai_score_source` | `live` | 172 | 172 | None | -1.402 | 0.0174 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 72 | 72 | None | -1.0936 | 0.0 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 55 | 55 | None | -0.9973 | 0.0909 | `hold_sample` |
| `ai_score_source` | `prior_valid` | 2 | 2 | None | -1.45 | 0.0 | `hold_sample` |
| `ai_score_source` | `stage_rule_backfilled` | 1 | 0 | None | None | None | `hold_sample` |
| `arm` | `AVG_DOWN` | 294 | 293 | None | -1.3076 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 8 | 8 | None | 0.6875 | 1.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 287 | 286 | None | -1.2623 | 0.0 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 8 | 8 | None | 0.6875 | 1.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 7 | 7 | None | -3.16 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.48)` | 18 | 18 | None | -0.48 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.61)` | 14 | 14 | None | -1.61 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 13 | 13 | None | -1.1246 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.61)` | 11 | 11 | None | -0.61 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.48)` | 10 | 10 | None | -1.48 | 0.0 | `hold_sample` |

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
