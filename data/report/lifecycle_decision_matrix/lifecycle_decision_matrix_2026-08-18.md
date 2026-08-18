# Lifecycle Decision Matrix - 2026-08-18

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-08-18`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `3145`
- source_rows_total: `3964`
- retained_rows: `3145`
- dropped_rows_by_source: `{'dedupe': 819}`
- joined_rows: `1586`
- policy_pass_count: `5`
- promote_ready_count: `0`
- entry_bucket_actionable_count: `4`
- entry_bucket_runtime_candidate_count: `0`
- holding_bucket_count/workorders: `19` / `7`
- exit_bucket_count/workorders: `32` / `10`
- scale_in_bucket_actionable_count: `0`
- scale_in_bucket_runtime_candidate_count: `0`
- overnight_bucket_actionable_count: `0`
- overnight_bucket_runtime_candidate_count: `0`
- lifecycle_flow_bucket_count: `40`
- lifecycle_flow_complete_count: `19`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `0` / `19` / `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0078`
- incomplete_flow_reason_counts: `{'missing_submit': 2369, 'missing_holding': 2429, 'missing_exit': 1673, 'missing_entry': 2259, 'candidate_id_only': 2261, 'scale_in_noise_only': 1500, 'sim_record_id_only': 13, 'postclose_exit_without_entry': 758}`
- bucket_directed_sim_probe: `{'observed_row_count': 859, 'matched_row_count': 0, 'background_row_count': 859, 'matched_unique_source_bucket_count': 0, 'match_status_counts': {'no_match': 82, 'not_instrumented': 777}, 'matched_classification_state_counts': {}, 'primary_source': 'matched_bucket_directed_sim_probe_only', 'background_source': 'unmatched_or_policy_missing_sim_observation', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 1, 'route_counts': {'bounded_auxiliary_weight': 1, 'hold_sample': 4}, 'quality_counts': {'observational_only_pending_outcome': 1, 'hold_sample': 4}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 736 | 13 | -0.6238 | 0.023 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 88 | 25 | -1.175 | 0.7102 | `pass` | `NO_CHANGE` | False |
| `holding` | 26 | 24 | -1.3104 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 1500 | 1487 | -1.2748 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 795 | 37 | -1.2543 | 0.1722 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 2450, 'complete_flow_count': 19, 'direct_sim_record_complete_flow_count': 0, 'adm_bridge_complete_flow_count': 19, 'fallback_complete_flow_count': 0, 'direct_flow_zero_diagnostic': {'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'direct_sim_record_flow_count': 13, 'direct_sim_record_incomplete_flow_count': 13, 'direct_sim_record_stage_coverage_counts': {}, 'direct_sim_record_incomplete_reason_counts': {'missing_entry': 13, 'missing_submit': 13, 'missing_holding': 13, 'missing_exit': 13, 'sim_record_id_only': 13, 'scale_in_noise_only': 13}, 'runtime_effect': False, 'decision_authority': 'ldm_direct_flow_diagnostic_only'}, 'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'incomplete_flow_count': 2431, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 3145, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0078, 'complete_flow_conversion_denominator': 778, 'complete_flow_conversion_rate': 0.0244, 'active_priority_incomplete_seed_count': 172, 'scale_in_followup_event_count': 1500, 'scale_in_unique_flow_count': 1093, 'scale_in_noise_flow_count': 1500, 'denominator_exclusion_counts': {'scale_in_noise_flow_excluded': 1500, 'active_priority_incomplete_seed_excluded': 172}, 'conversion_blocker_reason_counts': {'missing_entry': 759, 'missing_holding': 759, 'missing_exit': 1, 'missing_submit': 758, 'candidate_id_only': 758, 'postclose_exit_without_entry': 758}, 'observation_seed_reason_counts': {'missing_submit': 1611, 'missing_holding': 1670, 'missing_exit': 1672, 'missing_entry': 1500, 'candidate_id_only': 1503, 'scale_in_noise_only': 1500, 'sim_record_id_only': 13}, 'join_contract_blocked': False, 'bundle_ev_tuning_state': 'ready_for_bundle_ev_tuning', 'top_incomplete_reason': 'missing_holding', 'stage_identity': {'entry': {'source_row_count': 736, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 720, 'candidate_id': 16}, 'identity_join_rate': 1.0}, 'submit': {'source_row_count': 88, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 88}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 26, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 26}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 1500, 'identity_missing_count': 0, 'identity_quality_counts': {'candidate_id': 1487, 'exact_sim_record_id': 13}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 795, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 37, 'candidate_id': 758}, 'identity_join_rate': 1.0}}, 'required_stage_source_counts': {'entry': 736, 'submit': 88, 'holding': 26, 'exit': 795}, 'incomplete_flow_reason_counts': {'missing_submit': 2369, 'missing_holding': 2429, 'missing_exit': 1673, 'missing_entry': 2259, 'candidate_id_only': 2261, 'scale_in_noise_only': 1500, 'sim_record_id_only': 13, 'postclose_exit_without_entry': 758}, 'bucket_count': 40, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:0cb91a7ba6` | 2 | 2 | -1.115 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:03eec49aed` | 2 | 2 | -1.1106 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:bf44bd3042` | 1 | 1 | -0.53 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:92f69621e6` | 1 | 1 | -1.21 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_bl:e2e349e4ea` | 1 | 1 | -1.2 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:53097ae10f` | 1 | 1 | -0.2008 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:e629891351` | 1 | 1 | -0.84 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:a6d949bab9` | 1 | 1 | -1.56 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:4db4bab026` | 1 | 1 | -0.6724 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:b31cc048c8` | 1 | 1 | -2.55 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:63a0b8330e` | 1 | 1 | -2.6687 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:a74ce3066d` | 1 | 1 | -0.54 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:92f1223ea8` | 1 | 1 | -0.5 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:36904223da` | 1 | 1 | -0.9 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:82e718d20d` | 1 | 1 | -1.5701 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:4a9f25e5c6` | 1 | 1 | -3.4858 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:a0caef179f` | 1 | 1 | 1.7646 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 1438 | 1425 | -1.3616 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 62 | 62 | 0.7207 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:01a26e930a` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 736, 'bucket_count': 166, 'actionable_bucket_count': 4, 'source_quality_blocked_bucket_count': 14, 'runtime_candidate_count': 0, 'workorder_count': 14}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `NO_BUY_AI` | 340 | 12 | -0.6281 | -0.8742 | 0.3333 | `candidate_tighten_or_exclude` |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 9 | 1 | -0.572 | -1.4 | 0.0 | `source_quality_workorder` |
| `chosen_action` | `ALLOW_BOTTOMING_ENTRY` | 2 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `ALLOW_LEVEL1_RISK_OFF_ENTRY` | 14 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `BUY_DEFENSIVE` | 59 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_SOURCE_QUALITY` | 1 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_STALE` | 3 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `WAIT_REQUOTE` | 308 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 5 | 5 | -0.3294 | -1.078 | 0.2 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 2 | 2 | 0.0037 | -1.535 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_chase_risk|time=time_1000_1200` | 1 | 1 | -0.2032 | 0.75 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_ok|time=time_1000_1200` | 1 | 1 | -2.827 | 1.31 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_ok|time=time_1400_close` | 2 | 1 | -3.3495 | 0.51 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1200_1400` | 3 | 1 | -0.572 | -1.4 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 5 | 1 | 0.4773 | -1.47 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_1400_close` | 24 | 1 | 0.0046 | -3.13 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=blocked_ai_score|stale=fresh|liquidity=liquidity_not_available|overbought=overbought_normal|time=time_1000_1200` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_sim_panic_level1_entry_observed|stale=fresh_or_unflagged|liquidity=liquidity_state_normal|overbought=panic_entry_overbought_not_applicable|time=time_1000_1200` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 2 | 0 | None | None | None | `hold_sample` |
| `liquidity_bucket` | `liquidity_high` | 296 | 12 | -0.6281 | -0.8742 | 0.3333 | `candidate_tighten_or_exclude` |
| `stale_bucket` | `fresh` | 414 | 12 | -0.6281 | -0.8742 | 0.3333 | `candidate_tighten_or_exclude` |
| `strength_bucket` | `weak_strength_momentum` | 287 | 10 | -0.6136 | -0.75 | 0.4 | `candidate_tighten_or_exclude` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- `entry_bucket_unknown_source_quality_1`: `chosen_action` / `SKIP_PRE_SUBMIT_SAFETY` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_2`: `combo_entry_spot` / `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1000_1200` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_3`: `combo_entry_spot` / `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1200_1400` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_4`: `combo_entry_spot` / `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1400_close` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_5`: `exit_rule` / `exit_unknown` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_6`: `liquidity_bucket` / `liquidity_not_available` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_7`: `overbought_bucket` / `overbought_not_available` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_8`: `score_band` / `score_lt60` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_9`: `source_stage` / `scalp_entry_action_decision_snapshot` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_10`: `stale_bucket` / `stale_not_available` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_source_quality_1`: `chosen_action` / `NO_BUY_AI` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_2`: `liquidity_bucket` / `liquidity_high` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_3`: `stale_bucket` / `fresh` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_4`: `strength_bucket` / `weak_strength_momentum` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`

## Submit Bucket Attribution

- decision_authority: `adm_ldm_submit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'submit_rows': 88, 'bucket_count': 96, 'contract_gap_count': 0, 'workorder_count': 0, 'runtime_candidate_count': 0, 'quote_freshness_attribution_present': True, 'row_quote_freshness_attribution_present': True, 'sentinel_quote_freshness_attribution_present': True, 'sentinel_quote_freshness_attribution': {'source_report_type': 'buy_funnel_sentinel', 'decision_authority': 'submit_drought_quote_freshness_attribution_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'forbidden_uses': ['broker_order_submit', 'adm_ldm_training_input', 'general_threshold_ev_input', 'live_auto_promotion'], 'refresh_attempted_count': 120, 'refresh_applied_count': 62, 'still_latency_blocked_after_refresh_count': 85, 'latency_pass_recovered_count': 19, 'order_bundle_submitted_after_refresh_count': 2, 'refresh_subreason_counts': {'observer_quote_refresh_failed_invalid': 1, 'observer_quote_refresh_failed_stale': 10, 'ws_snapshot_refresh_failed_input_snapshot_fresh': 311, 'ws_snapshot_refresh_failed_invalid': 1, 'ws_snapshot_refresh_failed_stale': 25}, 'refresh_block_subreason_counts': {'observer_quote_refresh_failed_invalid': 1, 'observer_quote_refresh_failed_stale': 10, 'ws_snapshot_refresh_failed_input_snapshot_fresh': 311, 'ws_snapshot_refresh_failed_invalid': 1, 'ws_snapshot_refresh_failed_stale': 25}, 'latency_pass_recovered_downstream_counts': {'budget_pass_no_submit_event': 1, 'entry_ai_authority_revalidation': 16, 'order_bundle_submitted': 2}, 'post_restart_window_policy': 'event_provenance_only'}, 'quote_freshness_resolution_counts': {'refresh_attempted_unresolved': 40, 'refresh_failed_quote_stale': 2, 'refresh_not_attempted_or_not_instrumented': 5, 'refresh_resolved_quote_freshness': 14, 'sim_submit_path_not_applicable': 27}, 'pre_submit_refresh_applied_counts': {'refresh_attempted_not_applied': 42, 'refresh_not_attempted_or_not_instrumented': 5, 'sim_submit_path_not_applicable': 27, 'ws_snapshot_refresh_applied': 14}, 'real_submitted_row_count': 2, 'missing_broker_order_key_count': 0, 'bot_history_broker_order_key_backfill_candidate_count': 0, 'bot_history_broker_order_key_backfill_full_coverage': False, 'bot_history_broker_order_key_exact_mapping_count': 0, 'bot_history_broker_order_key_exact_mapping_full_coverage': False, 'post_submit_provenance_join_resolution': 'no_gap_broker_order_key_present_or_no_missing_rows', 'bot_history_broker_order_key_backfill_candidates': [], 'missing_broker_order_key_rate': 0.0, 'post_submit_provenance_join_gap_raw': False, 'post_submit_provenance_join_gap': False}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 86 | 25 | -1.175 | `keep_collecting` |
| `actual_order_submitted` | `true` | 2 | 0 | None | `keep_collecting` |
| `broker_order_forbidden` | `true` | 86 | 25 | -1.175 | `keep_collecting` |
| `broker_order_forbidden` | `false` | 2 | 0 | None | `keep_collecting` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_attempted_unresolved|fill=false|submitted=false` | 40 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_resolved_quote_freshness|fill=false|submitted=false` | 14 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 9 | 9 | -0.5205 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 6 | 5 | -0.7974 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 6 | 6 | -2.3092 | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_failed_quote_stale|fill=false|submitted=false` | 2 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 2 | 2 | -2.5877 | `source_quality_workorder` |
| `combo_submit_quality` | `source=entry_submit_revalidation_block|revalidation=warning_observed_mark_gap_unresolved|quote_age=quote_age_1_3s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=latency_unknown|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=entry_submit_revalidation_block|revalidation=warning_observed_mark_gap_unresolved|quote_age=quote_age_3_10s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=latency_unknown|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=entry_submit_revalidation_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=latency_unknown|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=caution|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_lt1s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=caution|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_block|revalidation=warning_stale_context_or_quote|quote_consistency_stale|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | 0.1881 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=pullback_or_rebreak_not_confirmed|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | -2.9417 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_overbought_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=pullback_or_rebreak_not_confirmed|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | 1.081 | `source_quality_workorder` |
| `latency_reason` | `scalp_live_simulator` | 27 | 25 | -1.175 | `keep_collecting` |
| `latency_reason` | `ws_age_too_high` | 20 | 0 | None | `keep_collecting` |
| `latency_reason` | `spread_above_caution_below_guard_cap` | 17 | 0 | None | `keep_collecting` |
| `latency_reason` | `ws_age_too_high,spread_too_wide` | 10 | 0 | None | `keep_collecting` |
| `latency_reason` | `spread_too_wide` | 9 | 0 | None | `keep_collecting` |
| `latency_reason` | `latency_reason_unknown` | 3 | 0 | None | `source_quality_workorder` |
| `latency_reason` | `caution_normal_entry_allowed` | 2 | 0 | None | `keep_collecting` |
| `latency_state` | `danger` | 56 | 0 | None | `keep_collecting` |
| `latency_state` | `simulated` | 27 | 25 | -1.175 | `keep_collecting` |
| `latency_state` | `latency_unknown` | 3 | 0 | None | `source_quality_workorder` |
| `latency_state` | `caution` | 2 | 0 | None | `keep_collecting` |
| `liquidity_bucket` | `liquidity_not_available` | 61 | 0 | None | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 18 | 16 | -0.4627 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 9 | 9 | -2.4414 | `keep_collecting` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 61 | 0 | None | `source_quality_workorder` |
| `liquidity_guard_action` | `would_pass` | 18 | 16 | -0.4627 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 9 | 9 | -2.4414 | `keep_collecting` |
| `overbought_bucket` | `overbought_not_available` | 61 | 0 | None | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 24 | 23 | -1.1963 | `keep_collecting` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 2 | 2 | -0.9304 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 26, 'source_row_count': 26, 'bucket_count': 19, 'joined_sample': 120, 'source_quality_adjusted_ev_pct': -1.3104, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 7, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 16 | 16 | -1.5334 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 4 | 4 | -1.0498 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | -0.2008 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 1 | 1 | -3.4858 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | -0.794 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 1 | 1 | 1.7646 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_not_applicable_at_start` | 26 | 24 | -1.3104 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 24 | 23 | -1.3587 | `candidate_tighten_or_exclude` |
| `holding_action` | `BUY` | 1 | 1 | -0.2008 | `hold_sample` |
| `holding_action` | `holding_action_not_applicable_at_start` | 1 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 26 | 24 | -1.3104 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 16 | 16 | -1.5334 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 5 | 5 | -0.88 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 1 | 1 | -3.4858 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 1 | 1 | -0.794 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 1 | 1 | 1.7646 | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 2 | 0 | None | `hold_sample` |

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
- summary: `{'exit_rows': 795, 'source_row_count': 795, 'bucket_count': 32, 'joined_sample': 185, 'source_quality_adjusted_ev_pct': -1.2543, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 10 | 10 | -1.339 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 8 | 8 | -0.8792 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 3 | 3 | -0.5233 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 3 | 3 | -1.9135 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 3 | 3 | -1.748 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 2 | 2 | -3.3174 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 2 | 2 | -2.3081 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 2 | 2 | 0.4219 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | -0.5099 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg070_neg010` | 1 | 1 | -3.4858 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 1 | 1 | -0.794 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 1 | 1 | 1.7646 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=scalp_sim_panic_context_warning_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 758 | 0 | None | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 13 | 13 | -1.1508 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 10 | 10 | -1.165 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 8 | 8 | -0.5545 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 6 | 6 | -2.5607 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 758 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 13 | 13 | -1.1508 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 9 | 9 | -0.8382 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 8 | 8 | -0.8644 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 7 | 7 | -2.4273 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_context_warning_not_applicable` | 758 | 0 | None | `hold_sample` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 24 | 24 | -1.3104 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 13 | 13 | -1.1508 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 758 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 26 | 26 | -1.4586 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 5 | 5 | -0.88 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 4 | 4 | -1.2639 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 1 | 1 | -0.794 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 1 | 1 | 1.7646 | `hold_sample` |
| `profit_band` | `profit_not_applicable_context_noop` | 758 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- `exit_bucket_source_quality_1`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_2`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_3`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_4`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_5`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_6`: `exit_outcome` / `outcome_not_applicable_partial_exit` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_7`: `exit_outcome` / `NEUTRAL` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_8`: `exit_outcome` / `MISSED_UPSIDE` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_9`: `exit_outcome` / `GOOD_EXIT` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_10`: `exit_rule` / `scalp_sim_panic_lifecycle_partial_exit` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `incremental_notional_ev_pct`
- summary: `{'scale_in_rows': 1500, 'bucket_count': 256, 'edge_bucket_count': 0, 'actionable_bucket_count': 0, 'runtime_authority_blocked_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'arm_counts': {'AVG_DOWN': 1438, 'PYRAMID': 62}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 1485 | 1485 | None | -1.4163 | 0.0404 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 2 | 2 | None | 1.31 | 1.0 | `hold_sample` |
| `ai_score_band` | `score_unknown` | 13 | 0 | None | None | None | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 618 | 618 | None | -1.6053 | 0.0291 | `hold_sample` |
| `ai_score_source` | `live` | 420 | 420 | None | -1.4099 | 0.0667 | `hold_sample` |
| `ai_score_source` | `not_evaluated_no_ai_score_source` | 216 | 216 | None | -1.0048 | 0.0324 | `hold_sample` |
| `ai_score_source` | `holding_ai_not_called` | 132 | 132 | None | -1.1561 | 0.0379 | `hold_sample` |
| `ai_score_source` | `prior_valid` | 88 | 88 | None | -1.5032 | 0.0455 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 13 | 13 | None | -1.1138 | 0.0 | `hold_sample` |
| `ai_score_source` | `stage_rule_backfilled` | 13 | 0 | None | None | None | `hold_sample` |
| `arm` | `AVG_DOWN` | 1438 | 1425 | None | -1.5046 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 62 | 62 | None | 0.7006 | 1.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 1376 | 1363 | None | -1.429 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 62 | 62 | None | -3.1663 | 0.0 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 62 | 62 | None | 0.7006 | 1.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.33)` | 48 | 48 | None | -0.33 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.23)` | 40 | 40 | None | -0.23 | 0.0 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 39 | 39 | None | 0.5433 | 1.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.42)` | 34 | 34 | None | -0.42 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.62)` | 29 | 29 | None | -0.62 | 0.0 | `hold_sample` |

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
