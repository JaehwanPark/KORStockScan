# Lifecycle Decision Matrix - 2026-08-04

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-08-04`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `2046`
- source_rows_total: `4649`
- retained_rows: `2046`
- dropped_rows_by_source: `{'dedupe': 2603}`
- joined_rows: `1000`
- policy_pass_count: `2`
- promote_ready_count: `0`
- entry_bucket_actionable_count: `0`
- entry_bucket_runtime_candidate_count: `0`
- holding_bucket_count/workorders: `11` / `0`
- exit_bucket_count/workorders: `24` / `7`
- scale_in_bucket_actionable_count: `0`
- scale_in_bucket_runtime_candidate_count: `0`
- overnight_bucket_actionable_count: `0`
- overnight_bucket_runtime_candidate_count: `0`
- lifecycle_flow_bucket_count: `52`
- lifecycle_flow_complete_count: `9`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `0` / `9` / `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0064`
- incomplete_flow_reason_counts: `{'missing_holding': 1394, 'missing_exit': 1314, 'missing_submit': 1349, 'missing_entry': 1054, 'candidate_id_only': 1123, 'scale_in_noise_only': 973, 'postclose_exit_without_entry': 80, 'sim_record_id_only': 9}`
- bucket_directed_sim_probe: `{'observed_row_count': 271, 'matched_row_count': 0, 'background_row_count': 271, 'matched_unique_source_bucket_count': 0, 'match_status_counts': {'no_match': 106, 'not_instrumented': 165}, 'matched_classification_state_counts': {}, 'primary_source': 'matched_bucket_directed_sim_probe_only', 'background_source': 'unmatched_or_policy_missing_sim_observation', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 1, 'route_counts': {'bounded_auxiliary_weight': 1, 'hold_sample': 4}, 'quality_counts': {'observational_only_pending_outcome': 1, 'hold_sample': 4}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 916 | 4 | 0.3529 | 0.0017 | `hold_sample` | `BUY_DEFENSIVE` | False |
| `submit` | 54 | 5 | 0.2304 | 0.0463 | `hold_sample` | `NO_CHANGE` | False |
| `holding` | 9 | 5 | 0.0269 | 0.2778 | `hold_sample` | `NO_CHANGE` | False |
| `scale_in` | 973 | 972 | -0.4579 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 94 | 14 | -0.5411 | 0.2085 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 1403, 'complete_flow_count': 9, 'direct_sim_record_complete_flow_count': 0, 'adm_bridge_complete_flow_count': 9, 'fallback_complete_flow_count': 0, 'direct_flow_zero_diagnostic': {'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'direct_sim_record_flow_count': 9, 'direct_sim_record_incomplete_flow_count': 9, 'direct_sim_record_stage_coverage_counts': {}, 'direct_sim_record_incomplete_reason_counts': {'missing_entry': 9, 'missing_submit': 9, 'missing_holding': 9, 'missing_exit': 9, 'sim_record_id_only': 9, 'scale_in_noise_only': 9}, 'runtime_effect': False, 'decision_authority': 'ldm_direct_flow_diagnostic_only'}, 'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'incomplete_flow_count': 1394, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 2046, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0064, 'complete_flow_conversion_denominator': 90, 'complete_flow_conversion_rate': 0.1, 'active_priority_incomplete_seed_count': 340, 'scale_in_followup_event_count': 973, 'scale_in_unique_flow_count': 721, 'scale_in_noise_flow_count': 973, 'denominator_exclusion_counts': {'scale_in_noise_flow_excluded': 973, 'active_priority_incomplete_seed_excluded': 340}, 'conversion_blocker_reason_counts': {'missing_entry': 81, 'missing_holding': 81, 'missing_exit': 1, 'missing_submit': 80, 'candidate_id_only': 80, 'postclose_exit_without_entry': 80}, 'observation_seed_reason_counts': {'missing_holding': 1313, 'missing_exit': 1313, 'missing_submit': 1269, 'missing_entry': 973, 'candidate_id_only': 1043, 'scale_in_noise_only': 973, 'sim_record_id_only': 9}, 'join_contract_blocked': False, 'bundle_ev_tuning_state': 'ready_for_bundle_ev_tuning', 'top_incomplete_reason': 'missing_holding', 'stage_identity': {'entry': {'source_row_count': 916, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 837, 'candidate_id': 79}, 'identity_join_rate': 1.0}, 'submit': {'source_row_count': 54, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 54}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 9, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 9}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 973, 'identity_missing_count': 0, 'identity_quality_counts': {'candidate_id': 964, 'exact_sim_record_id': 9}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 94, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 14, 'candidate_id': 80}, 'identity_join_rate': 1.0}}, 'required_stage_source_counts': {'entry': 916, 'submit': 54, 'holding': 9, 'exit': 94}, 'incomplete_flow_reason_counts': {'missing_holding': 1394, 'missing_exit': 1314, 'missing_submit': 1349, 'missing_entry': 1054, 'candidate_id_only': 1123, 'scale_in_noise_only': 973, 'postclose_exit_without_entry': 80, 'sim_record_id_only': 9}, 'bucket_count': 52, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:397dbf1728` | 2 | 2 | -0.84 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:cb6ed22b69` | 2 | 2 | -0.83 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_bl:36dfb94c33` | 1 | 1 | -0.54 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:9e4edc4bd2` | 1 | 1 | -0.99 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:d0233209ef` | 1 | 1 | -0.69 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:75c7602241` | 1 | 1 | -1.55 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:0e6c01c6bb` | 1 | 1 | -0.6 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 870 | 870 | -0.5571 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 103 | 102 | 0.3877 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:01a26e930a` | 2 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_ai:c18e731ca8` | 34 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_ai:9a372901ee` | 2 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_bl:cf6cca51c3` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:f9f18a2ca7` | 9 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:9eb10536a2` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:6d88d558c7` | 7 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:1c4ab1bc7c` | 6 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:542cd2bc91` | 60 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_ai:0370c0d68d` | 2 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_bl:98023dd644` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 916, 'bucket_count': 205, 'actionable_bucket_count': 0, 'source_quality_blocked_bucket_count': 13, 'runtime_candidate_count': 0, 'workorder_count': 10}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 86 | 4 | 0.3529 | -0.305 | 0.5 | `source_quality_workorder` |
| `chosen_action` | `ALLOW_BOTTOMING_ENTRY` | 6 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `ALLOW_LEVEL1_RISK_OFF_ENTRY` | 73 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `BUY_DEFENSIVE` | 25 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `NO_BUY_AI` | 559 | 0 | None | None | None | `source_quality_workorder` |
| `chosen_action` | `SKIP_SOURCE_QUALITY` | 1 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `WAIT_REQUOTE` | 166 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1000_1200` | 33 | 3 | 0.1625 | 0.08 | 0.6667 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1200_1400` | 12 | 1 | 0.9241 | -1.46 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_1200_1400` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1000_1200` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1400_close` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_sim_panic_level1_entry_observed|stale=fresh_or_unflagged|liquidity=liquidity_state_normal|overbought=panic_entry_overbought_not_applicable|time=time_1000_1200` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_chase_risk|time=time_0900_1000` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 6 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 7 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 9 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 5 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_1000_1200` | 7 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_1200_1400` | 2 | 0 | None | None | None | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- `entry_bucket_unknown_source_quality_1`: `chosen_action` / `SKIP_PRE_SUBMIT_SAFETY` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_2`: `chosen_action` / `NO_BUY_AI` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_3`: `combo_entry_spot` / `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_0900_1000` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_4`: `combo_entry_spot` / `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1000_1200` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_5`: `exit_rule` / `exit_unknown` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_6`: `liquidity_bucket` / `liquidity_not_available` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_7`: `overbought_bucket` / `overbought_not_available` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_8`: `score_band` / `score_lt60` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_9`: `source_stage` / `scalp_entry_action_decision_snapshot` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_10`: `stale_bucket` / `stale_not_available` -> `unknown_bucket_source_quality_blocker`

## Submit Bucket Attribution

- decision_authority: `adm_ldm_submit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'submit_rows': 54, 'bucket_count': 82, 'contract_gap_count': 0, 'workorder_count': 0, 'runtime_candidate_count': 0, 'quote_freshness_attribution_present': True, 'row_quote_freshness_attribution_present': True, 'sentinel_quote_freshness_attribution_present': True, 'sentinel_quote_freshness_attribution': {'source_report_type': 'buy_funnel_sentinel', 'decision_authority': 'submit_drought_quote_freshness_attribution_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'forbidden_uses': ['broker_order_submit', 'adm_ldm_training_input', 'general_threshold_ev_input', 'live_auto_promotion'], 'refresh_attempted_count': 91, 'refresh_applied_count': 41, 'still_latency_blocked_after_refresh_count': 68, 'latency_pass_recovered_count': 6, 'order_bundle_submitted_after_refresh_count': 1, 'refresh_subreason_counts': {'ws_snapshot_refresh_failed_input_snapshot_fresh': 186, 'ws_snapshot_refresh_failed_stale': 18}, 'refresh_block_subreason_counts': {'ws_snapshot_refresh_failed_input_snapshot_fresh': 186, 'ws_snapshot_refresh_failed_stale': 18}, 'latency_pass_recovered_downstream_counts': {'budget_pass_no_submit_event': 1, 'order_bundle_submitted': 1, 'price_guard_or_revalidation': 4}, 'post_restart_window_policy': 'event_provenance_only'}, 'quote_freshness_resolution_counts': {'refresh_attempted_unresolved': 15, 'refresh_failed_quote_stale': 4, 'refresh_not_attempted_or_not_instrumented': 13, 'refresh_resolved_quote_freshness': 13, 'sim_submit_path_not_applicable': 9}, 'pre_submit_refresh_applied_counts': {'refresh_attempted_not_applied': 19, 'refresh_not_attempted_or_not_instrumented': 13, 'sim_submit_path_not_applicable': 9, 'ws_snapshot_refresh_applied': 13}, 'real_submitted_row_count': 13, 'missing_broker_order_key_count': 0, 'bot_history_broker_order_key_backfill_candidate_count': 0, 'bot_history_broker_order_key_backfill_full_coverage': False, 'bot_history_broker_order_key_exact_mapping_count': 0, 'bot_history_broker_order_key_exact_mapping_full_coverage': False, 'post_submit_provenance_join_resolution': 'no_gap_broker_order_key_present_or_no_missing_rows', 'bot_history_broker_order_key_backfill_candidates': [], 'missing_broker_order_key_rate': 0.0, 'post_submit_provenance_join_gap_raw': False, 'post_submit_provenance_join_gap': False}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 41 | 5 | 0.2304 | `keep_collecting` |
| `actual_order_submitted` | `true` | 13 | 0 | None | `keep_collecting` |
| `broker_order_forbidden` | `true` | 41 | 5 | 0.2304 | `keep_collecting` |
| `broker_order_forbidden` | `false` | 13 | 0 | None | `keep_collecting` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_attempted_unresolved|fill=false|submitted=false` | 15 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_resolved_quote_freshness|fill=false|submitted=false` | 13 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=caution|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 8 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_failed_quote_stale|fill=false|submitted=false` | 4 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 4 | 3 | 0.1625 | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_lt1s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=caution|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 2 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 2 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 2 | 1 | -0.2596 | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=safe|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_lt1s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_lt1s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=safe|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | 0.9241 | `source_quality_workorder` |
| `latency_reason` | `spread_above_caution_below_guard_cap` | 17 | 0 | None | `keep_collecting` |
| `latency_reason` | `caution_normal_entry_allowed` | 10 | 0 | None | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 9 | 5 | 0.2304 | `keep_collecting` |
| `latency_reason` | `spread_too_wide` | 9 | 0 | None | `keep_collecting` |
| `latency_reason` | `ws_age_too_high,spread_too_wide` | 4 | 0 | None | `keep_collecting` |
| `latency_reason` | `safe_normal_entry_allowed` | 2 | 0 | None | `keep_collecting` |
| `latency_reason` | `ws_age_too_high` | 2 | 0 | None | `keep_collecting` |
| `latency_reason` | `latency_true_ofi_false_negative_direct_canary_normal_override` | 1 | 0 | None | `keep_collecting` |
| `latency_state` | `danger` | 33 | 0 | None | `keep_collecting` |
| `latency_state` | `caution` | 10 | 0 | None | `keep_collecting` |
| `latency_state` | `simulated` | 9 | 5 | 0.2304 | `keep_collecting` |
| `latency_state` | `safe` | 2 | 0 | None | `keep_collecting` |
| `liquidity_bucket` | `liquidity_not_available` | 45 | 0 | None | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 5 | 2 | 0.3323 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 4 | 3 | 0.1625 | `keep_collecting` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 45 | 0 | None | `source_quality_workorder` |
| `liquidity_guard_action` | `would_block` | 5 | 2 | 0.3323 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 4 | 3 | 0.1625 | `keep_collecting` |
| `overbought_bucket` | `overbought_not_available` | 45 | 0 | None | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 7 | 4 | 0.3529 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 2 | 1 | -0.2596 | `keep_collecting` |
| `overbought_guard_action` | `overbought_guard_unknown` | 45 | 0 | None | `source_quality_workorder` |
| `overbought_guard_action` | `would_pass` | 9 | 5 | 0.2304 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `refresh_age_not_instrumented` | 28 | 0 | None | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 9, 'source_row_count': 9, 'bucket_count': 11, 'joined_sample': 25, 'source_quality_adjusted_ev_pct': 0.0269, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 0, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 3 | 3 | 0.1744 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1 | 1 | -0.2758 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 1 | 1 | -0.1128 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 4 | 0 | None | `hold_sample` |
| `held_bucket` | `held_not_applicable_at_start` | 9 | 5 | 0.0269 | `hold_no_edge` |
| `holding_action` | `WAIT` | 9 | 5 | 0.0269 | `hold_no_edge` |
| `holding_source_stage` | `scalp_sim_holding_started` | 9 | 5 | 0.0269 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 3 | 3 | 0.1744 | `hold_no_edge` |
| `profit_band` | `profit_lt_neg070` | 1 | 1 | -0.2758 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 1 | 1 | -0.1128 | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 4 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `adm_ldm_exit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'exit_rows': 94, 'source_row_count': 94, 'bucket_count': 24, 'joined_sample': 70, 'source_quality_adjusted_ev_pct': -0.5411, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 7, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 5 | 5 | -0.63 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 4 | 4 | -1.14 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 3 | 3 | 0.1744 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | -0.2758 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg070_neg010` | 1 | 1 | -0.1128 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_euphoria_context_noop|rule=scalp_sim_euphoria_context_noop_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 78 | 0 | None | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=scalp_sim_panic_context_warning_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 2 | 0 | None | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 9 | 9 | -0.8567 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 4 | 4 | 0.1026 | `hold_no_edge` |
| `exit_outcome` | `MISSED_UPSIDE` | 1 | 1 | -0.2758 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 80 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 9 | 9 | -0.8567 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 4 | 4 | 0.1026 | `hold_no_edge` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 1 | 1 | -0.2758 | `hold_sample` |
| `exit_rule` | `scalp_sim_euphoria_context_noop_not_applicable` | 78 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_context_warning_not_applicable` | 2 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 9 | 9 | -0.8567 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 5 | 5 | 0.0269 | `hold_no_edge` |
| `exit_source_stage` | `scalp_sim_euphoria_context_noop` | 78 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 2 | 0 | None | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 6 | 6 | -0.5438 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 5 | 5 | -0.9672 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 3 | 3 | 0.1744 | `hold_no_edge` |
| `profit_band` | `profit_not_applicable_context_noop` | 80 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- `exit_bucket_source_quality_1`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_2`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_3`: `exit_outcome` / `outcome_not_applicable_partial_exit` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_4`: `exit_rule` / `scalp_sim_panic_lifecycle_partial_exit` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_5`: `exit_source_stage` / `scalp_sim_partial_sell_order_assumed_filled` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_6`: `profit_band` / `profit_neg070_neg010` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_7`: `profit_band` / `profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `incremental_notional_ev_pct`
- summary: `{'scale_in_rows': 973, 'bucket_count': 104, 'edge_bucket_count': 0, 'actionable_bucket_count': 0, 'runtime_authority_blocked_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'arm_counts': {'AVG_DOWN': 870, 'PYRAMID': 103}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 963 | 962 | None | -0.5158 | 0.0551 | `hold_sample` |
| `ai_score_band` | `score_70p` | 4 | 4 | None | 0.81 | 1.0 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 2 | 2 | None | 0.81 | 1.0 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 2 | 2 | None | 1.16 | 1.0 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 2 | 2 | None | 0.81 | 1.0 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 427 | 427 | None | -0.483 | 0.0492 | `hold_sample` |
| `ai_score_source` | `live` | 331 | 331 | None | -0.4686 | 0.1118 | `hold_sample` |
| `ai_score_source` | `prior_valid` | 85 | 85 | None | -0.3976 | 0.0235 | `hold_sample` |
| `ai_score_source` | `not_evaluated_no_ai_score_source` | 78 | 78 | None | -0.675 | 0.0385 | `hold_sample` |
| `ai_score_source` | `holding_ai_not_called` | 42 | 42 | None | -0.7757 | 0.0 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 10 | 9 | None | -0.7778 | 0.0 | `hold_sample` |
| `arm` | `AVG_DOWN` | 870 | 870 | None | -0.6026 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 103 | 102 | None | 0.3609 | 0.6176 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 868 | 868 | None | -0.597 | 0.0 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 103 | 102 | None | 0.3609 | 0.6176 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 2 | 2 | None | -3.0 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.42)` | 104 | 104 | None | -0.42 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.23)` | 98 | 98 | None | -0.23 | 0.0 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 98 | 98 | None | 0.346 | 0.602 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.60)` | 79 | 79 | None | -0.6 | 0.0 | `hold_sample` |

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
