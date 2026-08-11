# Lifecycle Decision Matrix - 2026-08-11

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-08-11`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `525`
- source_rows_total: `526`
- retained_rows: `525`
- dropped_rows_by_source: `{'dedupe': 1}`
- joined_rows: `28`
- policy_pass_count: `0`
- promote_ready_count: `0`
- entry_bucket_actionable_count: `0`
- entry_bucket_runtime_candidate_count: `0`
- holding_bucket_count/workorders: `7` / `3`
- exit_bucket_count/workorders: `16` / `1`
- scale_in_bucket_actionable_count: `0`
- scale_in_bucket_runtime_candidate_count: `0`
- overnight_bucket_actionable_count: `0`
- overnight_bucket_runtime_candidate_count: `0`
- lifecycle_flow_bucket_count: `21`
- lifecycle_flow_complete_count: `3`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `0` / `3` / `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0205`
- incomplete_flow_reason_counts: `{'missing_submit': 117, 'missing_holding': 143, 'missing_exit': 141, 'missing_entry': 21, 'candidate_id_only': 21, 'scale_in_noise_only': 19, 'postclose_exit_without_entry': 2}`
- bucket_directed_sim_probe: `{'observed_row_count': 39, 'matched_row_count': 0, 'background_row_count': 39, 'matched_unique_source_bucket_count': 0, 'match_status_counts': {'no_match': 6, 'not_instrumented': 33}, 'matched_classification_state_counts': {}, 'primary_source': 'matched_bucket_directed_sim_probe_only', 'background_source': 'unmatched_or_policy_missing_sim_observation', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 1, 'route_counts': {'bounded_auxiliary_weight': 1, 'hold_sample': 4}, 'quality_counts': {'observational_only_pending_outcome': 1, 'hold_sample': 4}}`
- warnings: `['all_stage_policy_entries_below_sample_floor']`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 469 | 3 | -0.2664 | 0.0019 | `hold_sample` | `WAIT_REQUOTE` | False |
| `submit` | 29 | 3 | -0.2664 | 0.031 | `hold_sample` | `NO_CHANGE` | False |
| `holding` | 3 | 3 | -0.4555 | 0.3 | `hold_sample` | `EXIT` | False |
| `scale_in` | 19 | 16 | -0.6096 | 1.0 | `hold_sample` | `NO_CHANGE` | False |
| `exit` | 5 | 3 | -0.4555 | 0.18 | `hold_sample` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 146, 'complete_flow_count': 3, 'direct_sim_record_complete_flow_count': 0, 'adm_bridge_complete_flow_count': 3, 'fallback_complete_flow_count': 0, 'direct_flow_zero_diagnostic': {'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'direct_sim_record_flow_count': 0, 'direct_sim_record_incomplete_flow_count': 0, 'direct_sim_record_stage_coverage_counts': {}, 'direct_sim_record_incomplete_reason_counts': {}, 'runtime_effect': False, 'decision_authority': 'ldm_direct_flow_diagnostic_only'}, 'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'incomplete_flow_count': 143, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 525, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0205, 'complete_flow_conversion_denominator': 5, 'complete_flow_conversion_rate': 0.6, 'active_priority_incomplete_seed_count': 122, 'scale_in_followup_event_count': 19, 'scale_in_unique_flow_count': 17, 'scale_in_noise_flow_count': 19, 'denominator_exclusion_counts': {'scale_in_noise_flow_excluded': 19, 'active_priority_incomplete_seed_excluded': 122}, 'conversion_blocker_reason_counts': {'missing_entry': 2, 'missing_submit': 2, 'missing_holding': 2, 'candidate_id_only': 2, 'postclose_exit_without_entry': 2}, 'observation_seed_reason_counts': {'missing_submit': 115, 'missing_holding': 141, 'missing_exit': 141, 'missing_entry': 19, 'candidate_id_only': 19, 'scale_in_noise_only': 19}, 'join_contract_blocked': False, 'bundle_ev_tuning_state': 'ready_for_bundle_ev_tuning', 'top_incomplete_reason': 'missing_holding', 'stage_identity': {'entry': {'source_row_count': 469, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 469}, 'identity_join_rate': 1.0}, 'submit': {'source_row_count': 29, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 29}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 3, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 3}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 19, 'identity_missing_count': 0, 'identity_quality_counts': {'candidate_id': 19}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 5, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 3, 'candidate_id': 2}, 'identity_join_rate': 1.0}}, 'required_stage_source_counts': {'entry': 469, 'submit': 29, 'holding': 3, 'exit': 5}, 'incomplete_flow_reason_counts': {'missing_submit': 117, 'missing_holding': 143, 'missing_exit': 141, 'missing_entry': 21, 'candidate_id_only': 21, 'scale_in_noise_only': 19, 'postclose_exit_without_entry': 2}, 'bucket_count': 21, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:5ad377bcf7` | 1 | 1 | -0.4211 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:4e1fc29475` | 1 | 1 | -0.904 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:1230ecd40d` | 1 | 1 | -0.0415 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 17 | 14 | -0.6996 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 2 | 2 | 0.02 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:f36cc32176` | 2 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_ai:c18e731ca8` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:6d88d558c7` | 3 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:c50d2ff605` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:07390fbd3e` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:f2f2f3d14e` | 6 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:111f0ede63` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:70a865069d` | 17 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:6f0786a34b` | 44 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:6a7b928aa6` | 5 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:92dad7616b` | 2 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:5566b1f38e` | 4 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:c69a7be5bd` | 25 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:b528e0c876` | 9 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:43870ece59` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 469, 'bucket_count': 141, 'actionable_bucket_count': 0, 'source_quality_blocked_bucket_count': 10, 'runtime_candidate_count': 0, 'workorder_count': 10}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 34 | 3 | -0.2664 | -0.6133 | 0.3333 | `source_quality_workorder` |
| `chosen_action` | `BUY_DEFENSIVE` | 5 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `NO_BUY_AI` | 360 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_SOURCE_QUALITY` | 1 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `WAIT_REQUOTE` | 69 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_0900_1000` | 2 | 1 | 0.5661 | -1.4 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_0900_1000` | 4 | 1 | -1.0132 | 1.01 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1000_1200` | 12 | 1 | -0.352 | -1.45 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=blocked_ai_score|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=blocked_ai_score|stale=fresh|liquidity=liquidity_not_available|overbought=overbought_normal|time=time_0900_1000` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_1400_close` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1000_1200` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1400_close` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1400_close` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=blocked_ai_score|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_1200_1400` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=blocked_ai_score|stale=fresh|liquidity=liquidity_not_available|overbought=overbought_normal|time=time_1000_1200` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=blocked_ai_score|stale=fresh|liquidity=liquidity_not_available|overbought=overbought_watch|time=time_0900_1000` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_chase_risk|time=time_1400_close` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1400_close` | 6 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_ok|time=time_1000_1200` | 2 | 0 | None | None | None | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- `entry_bucket_unknown_source_quality_1`: `chosen_action` / `SKIP_PRE_SUBMIT_SAFETY` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_2`: `combo_entry_spot` / `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_0900_1000` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_3`: `exit_rule` / `exit_unknown` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_4`: `liquidity_bucket` / `liquidity_not_available` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_5`: `overbought_bucket` / `overbought_not_available` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_6`: `score_band` / `score_lt60` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_7`: `source_stage` / `scalp_entry_action_decision_snapshot` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_8`: `stale_bucket` / `stale_not_available` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_9`: `strength_bucket` / `risk_unknown` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_10`: `time_bucket` / `time_0900_1000` -> `unknown_bucket_source_quality_blocker`

## Submit Bucket Attribution

- decision_authority: `adm_ldm_submit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'submit_rows': 29, 'bucket_count': 58, 'contract_gap_count': 0, 'workorder_count': 0, 'runtime_candidate_count': 0, 'quote_freshness_attribution_present': True, 'row_quote_freshness_attribution_present': True, 'sentinel_quote_freshness_attribution_present': True, 'sentinel_quote_freshness_attribution': {'source_report_type': 'buy_funnel_sentinel', 'decision_authority': 'submit_drought_quote_freshness_attribution_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'forbidden_uses': ['broker_order_submit', 'adm_ldm_training_input', 'general_threshold_ev_input', 'live_auto_promotion'], 'refresh_attempted_count': 45, 'refresh_applied_count': 25, 'still_latency_blocked_after_refresh_count': 36, 'latency_pass_recovered_count': 1, 'order_bundle_submitted_after_refresh_count': 0, 'refresh_subreason_counts': {'ws_snapshot_refresh_failed_input_snapshot_fresh': 60, 'ws_snapshot_refresh_failed_stale': 10}, 'refresh_block_subreason_counts': {'ws_snapshot_refresh_failed_input_snapshot_fresh': 60, 'ws_snapshot_refresh_failed_stale': 10}, 'latency_pass_recovered_downstream_counts': {'entry_ai_authority_revalidation': 1}, 'post_restart_window_policy': 'event_provenance_only'}, 'quote_freshness_resolution_counts': {'refresh_attempted_unresolved': 14, 'refresh_failed_quote_stale': 4, 'refresh_resolved_quote_freshness': 8, 'sim_submit_path_not_applicable': 3}, 'pre_submit_refresh_applied_counts': {'refresh_attempted_not_applied': 18, 'sim_submit_path_not_applicable': 3, 'ws_snapshot_refresh_applied': 8}, 'real_submitted_row_count': 0, 'missing_broker_order_key_count': 0, 'bot_history_broker_order_key_backfill_candidate_count': 0, 'bot_history_broker_order_key_backfill_full_coverage': False, 'bot_history_broker_order_key_exact_mapping_count': 0, 'bot_history_broker_order_key_exact_mapping_full_coverage': False, 'post_submit_provenance_join_resolution': 'no_gap_broker_order_key_present_or_no_missing_rows', 'bot_history_broker_order_key_backfill_candidates': [], 'missing_broker_order_key_rate': 0.0, 'post_submit_provenance_join_gap_raw': False, 'post_submit_provenance_join_gap': False}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 29 | 3 | -0.2664 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 29 | 3 | -0.2664 | `keep_collecting` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_attempted_unresolved|fill=false|submitted=false` | 14 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_resolved_quote_freshness|fill=false|submitted=false` | 8 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_failed_quote_stale|fill=false|submitted=false` | 4 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 2 | 2 | 0.1071 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | -1.0132 | `source_quality_workorder` |
| `latency_reason` | `spread_above_caution_below_guard_cap` | 11 | 0 | None | `keep_collecting` |
| `latency_reason` | `spread_too_wide` | 6 | 0 | None | `keep_collecting` |
| `latency_reason` | `ws_age_too_high` | 6 | 0 | None | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 3 | 3 | -0.2664 | `keep_collecting` |
| `latency_reason` | `ws_age_too_high,spread_too_wide` | 3 | 0 | None | `keep_collecting` |
| `latency_state` | `danger` | 26 | 0 | None | `keep_collecting` |
| `latency_state` | `simulated` | 3 | 3 | -0.2664 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_not_available` | 26 | 0 | None | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 2 | 2 | 0.1071 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 1 | 1 | -1.0132 | `keep_collecting` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 26 | 0 | None | `source_quality_workorder` |
| `liquidity_guard_action` | `would_pass` | 2 | 2 | 0.1071 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 1 | 1 | -1.0132 | `keep_collecting` |
| `overbought_bucket` | `overbought_not_available` | 26 | 0 | None | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 3 | 3 | -0.2664 | `keep_collecting` |
| `overbought_guard_action` | `overbought_guard_unknown` | 26 | 0 | None | `source_quality_workorder` |
| `overbought_guard_action` | `would_pass` | 3 | 3 | -0.2664 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `refresh_age_not_instrumented` | 14 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `refresh_age_lt1s` | 10 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 3 | 3 | -0.2664 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `refresh_age_1_3s` | 1 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `refresh_age_3_10s` | 1 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_applied` | `refresh_attempted_not_applied` | 18 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_applied` | `ws_snapshot_refresh_applied` | 8 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 3 | 3 | -0.2664 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `refresh_attempted` | 26 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 3 | 3 | -0.2664 | `keep_collecting` |
| `pre_submit_refresh_reason` | `ws_snapshot:input_snapshot_fresh` | 14 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_reason` | `ws_snapshot:latest_ws_snapshot_fresh` | 8 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_reason` | `ws_snapshot:latest_snapshot_stale` | 4 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 3 | 3 | -0.2664 | `keep_collecting` |
| `pre_submit_refresh_source` | `ws_manager_latest_data` | 26 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 3 | 3 | -0.2664 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 3, 'source_row_count': 3, 'bucket_count': 7, 'joined_sample': 15, 'source_quality_adjusted_ev_pct': -0.4555, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 3, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 2 | 2 | -0.6625 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | -0.0415 | `hold_sample` |
| `held_bucket` | `held_not_applicable_at_start` | 3 | 3 | -0.4555 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 3 | 3 | -0.4555 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 3 | 3 | -0.4555 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 2 | 2 | -0.6625 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 1 | 1 | -0.0415 | `hold_sample` |

### Holding Bucket Attribution Workorders

- `holding_bucket_source_quality_1`: `held_bucket` / `held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_2`: `holding_action` / `WAIT` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_3`: `holding_source_stage` / `scalp_sim_holding_started` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Exit Bucket Attribution

- decision_authority: `adm_ldm_exit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'exit_rows': 5, 'source_row_count': 5, 'bucket_count': 16, 'joined_sample': 15, 'source_quality_adjusted_ev_pct': -0.4555, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 1, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | -0.4211 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 1 | 1 | -0.904 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 1 | 1 | -0.0415 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=scalp_sim_panic_context_warning_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 2 | 0 | None | `hold_sample` |
| `exit_outcome` | `GOOD_EXIT` | 1 | 1 | -0.0415 | `hold_sample` |
| `exit_outcome` | `MISSED_UPSIDE` | 1 | 1 | -0.4211 | `hold_sample` |
| `exit_outcome` | `NEUTRAL` | 1 | 1 | -0.904 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 2 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 2 | 2 | -0.6625 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 1 | 1 | -0.0415 | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_context_warning_not_applicable` | 2 | 0 | None | `hold_sample` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 3 | 3 | -0.4555 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 2 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 2 | 2 | -0.6625 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 1 | 1 | -0.0415 | `hold_sample` |
| `profit_band` | `profit_not_applicable_context_noop` | 2 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- `exit_bucket_source_quality_1`: `exit_source_stage` / `sim_post_sell_evaluation` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `incremental_notional_ev_pct`
- summary: `{'scale_in_rows': 19, 'bucket_count': 38, 'edge_bucket_count': 0, 'actionable_bucket_count': 0, 'runtime_authority_blocked_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'arm_counts': {'AVG_DOWN': 17, 'PYRAMID': 2}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 16 | 16 | None | -0.6681 | 0.125 | `hold_sample` |
| `ai_score_band` | `score_unknown` | 3 | 0 | None | None | None | `hold_sample` |
| `ai_score_source` | `not_evaluated_no_ai_score_source` | 12 | 12 | None | -0.7008 | 0.1667 | `hold_sample` |
| `ai_score_source` | `live` | 4 | 4 | None | -0.57 | 0.0 | `hold_sample` |
| `ai_score_source` | `stage_rule_backfilled` | 3 | 0 | None | None | None | `hold_sample` |
| `arm` | `AVG_DOWN` | 17 | 14 | None | -0.7664 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 2 | 2 | None | 0.02 | 1.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 17 | 14 | None | -0.7664 | 0.0 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 2 | 2 | None | 0.02 | 1.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_scale_in_window_expansion` | 4 | 4 | None | -0.6125 | 0.25 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.23)` | 2 | 2 | None | -0.23 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.73)` | 2 | 2 | None | -0.73 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.91)` | 2 | 2 | None | -0.91 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.20)` | 2 | 2 | None | -1.2 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.48)` | 1 | 1 | None | -0.48 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.56)` | 1 | 1 | None | -0.56 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.08)` | 1 | 1 | None | -1.08 | 0.0 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 1 | 1 | None | 0.02 | 1.0 | `hold_sample` |
| `blocker_reason` | `reversal_probe_missing` | 3 | 0 | None | None | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 9 | 9 | None | -0.66 | 0.2222 | `hold_sample` |

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
