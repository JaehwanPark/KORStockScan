# Lifecycle Decision Matrix - 2026-08-25

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-08-25`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `2815`
- source_rows_total: `3910`
- retained_rows: `2815`
- dropped_rows_by_source: `{'dedupe': 1095}`
- joined_rows: `1433`
- policy_pass_count: `4`
- promote_ready_count: `0`
- entry_bucket_actionable_count: `0`
- entry_bucket_runtime_candidate_count: `0`
- holding_bucket_count/workorders: `26` / `9`
- exit_bucket_count/workorders: `42` / `10`
- scale_in_bucket_actionable_count: `0`
- scale_in_bucket_runtime_candidate_count: `0`
- overnight_bucket_actionable_count: `0`
- overnight_bucket_runtime_candidate_count: `0`
- lifecycle_flow_bucket_count: `48`
- lifecycle_flow_complete_count: `20`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `0` / `20` / `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0092`
- incomplete_flow_reason_counts: `{'missing_holding': 2159, 'missing_exit': 1494, 'missing_submit': 2105, 'missing_entry': 2000, 'candidate_id_only': 2016, 'scale_in_noise_only': 1334, 'postclose_exit_without_entry': 665, 'sim_record_id_only': 11}`
- bucket_directed_sim_probe: `{'observed_row_count': 789, 'matched_row_count': 0, 'background_row_count': 789, 'matched_unique_source_bucket_count': 0, 'match_status_counts': {'not_instrumented': 694, 'policy_disabled': 95}, 'matched_classification_state_counts': {}, 'primary_source': 'matched_bucket_directed_sim_probe_only', 'background_source': 'unmatched_or_policy_missing_sim_observation', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 1, 'route_counts': {'bounded_auxiliary_weight': 1, 'hold_sample': 4}, 'quality_counts': {'observational_only_pending_outcome': 1, 'hold_sample': 4}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 657 | 9 | 0.0461 | 0.0123 | `hold_sample` | `NO_CHANGE` | False |
| `submit` | 84 | 23 | -0.3971 | 0.6298 | `pass` | `NO_CHANGE` | False |
| `holding` | 28 | 23 | -0.7273 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 1334 | 1331 | -0.8796 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 712 | 47 | -0.7835 | 0.3103 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 2179, 'complete_flow_count': 20, 'direct_sim_record_complete_flow_count': 0, 'adm_bridge_complete_flow_count': 20, 'fallback_complete_flow_count': 0, 'direct_flow_zero_diagnostic': {'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'direct_sim_record_flow_count': 11, 'direct_sim_record_incomplete_flow_count': 11, 'direct_sim_record_stage_coverage_counts': {}, 'direct_sim_record_incomplete_reason_counts': {'missing_entry': 11, 'missing_submit': 11, 'missing_holding': 11, 'missing_exit': 11, 'sim_record_id_only': 11, 'scale_in_noise_only': 11}, 'runtime_effect': False, 'decision_authority': 'ldm_direct_flow_diagnostic_only'}, 'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'incomplete_flow_count': 2159, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 2815, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0092, 'complete_flow_conversion_denominator': 686, 'complete_flow_conversion_rate': 0.0292, 'active_priority_incomplete_seed_count': 159, 'scale_in_followup_event_count': 1334, 'scale_in_unique_flow_count': 980, 'scale_in_noise_flow_count': 1334, 'denominator_exclusion_counts': {'scale_in_noise_flow_excluded': 1334, 'active_priority_incomplete_seed_excluded': 159}, 'conversion_blocker_reason_counts': {'missing_entry': 666, 'missing_holding': 666, 'missing_exit': 1, 'missing_submit': 665, 'candidate_id_only': 665, 'postclose_exit_without_entry': 665}, 'observation_seed_reason_counts': {'missing_holding': 1493, 'missing_exit': 1493, 'missing_submit': 1440, 'missing_entry': 1334, 'candidate_id_only': 1351, 'scale_in_noise_only': 1334, 'sim_record_id_only': 11}, 'join_contract_blocked': False, 'bundle_ev_tuning_state': 'ready_for_bundle_ev_tuning', 'top_incomplete_reason': 'missing_holding', 'stage_identity': {'entry': {'source_row_count': 657, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 629, 'candidate_id': 28}, 'identity_join_rate': 1.0}, 'submit': {'source_row_count': 84, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 84}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 28, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 28}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 1334, 'identity_missing_count': 0, 'identity_quality_counts': {'candidate_id': 1323, 'exact_sim_record_id': 11}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 712, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 47, 'candidate_id': 665}, 'identity_join_rate': 1.0}}, 'required_stage_source_counts': {'entry': 657, 'submit': 84, 'holding': 28, 'exit': 712}, 'incomplete_flow_reason_counts': {'missing_holding': 2159, 'missing_exit': 1494, 'missing_submit': 2105, 'missing_entry': 2000, 'candidate_id_only': 2016, 'scale_in_noise_only': 1334, 'postclose_exit_without_entry': 665, 'sim_record_id_only': 11}, 'bucket_count': 48, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:a6af469504` | 2 | 2 | -0.96 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:0cb91a7ba6` | 2 | 2 | -1.07 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_bloc:ce21fab319` | 1 | 1 | -0.51 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:3b618795a8` | 1 | 1 | -0.79 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:55248db096` | 1 | 1 | -0.48 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:beb61a6072` | 1 | 1 | -0.52 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:27b40f1c54` | 1 | 1 | -0.94 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:7946d42f06` | 1 | 1 | -0.8423 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:2ee314bc27` | 1 | 1 | -1.36 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:b31cc048c8` | 1 | 1 | -1.98 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:f7970ec848` | 1 | 1 | 0.565 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:a9aa050472` | 1 | 1 | -0.97 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:69b67411f9` | 1 | 1 | -0.51 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:2e5cbd28f0` | 1 | 1 | -1.0 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:bbe961df76` | 1 | 1 | -0.88 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:388c2a1d9b` | 1 | 1 | -0.44 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:eb9f273723` | 1 | 1 | -0.61 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:2a955db258` | 1 | 1 | -0.5 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 1279 | 1276 | -0.9238 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 55 | 55 | 0.1465 | `hold_sample` | `join_contract_blocked` |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 657, 'bucket_count': 161, 'actionable_bucket_count': 0, 'source_quality_blocked_bucket_count': 10, 'runtime_candidate_count': 0, 'workorder_count': 10}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `NO_BUY_AI` | 275 | 9 | 0.0461 | -1.4233 | 0.2222 | `source_quality_workorder` |
| `chosen_action` | `ALLOW_BOTTOMING_ENTRY` | 7 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `ALLOW_LEVEL1_RISK_OFF_ENTRY` | 21 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `BUY_DEFENSIVE` | 74 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 34 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_SOURCE_QUALITY` | 4 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_STALE` | 1 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `WAIT_REQUOTE` | 241 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 3 | 3 | -0.1713 | -1.5633 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 3 | 1 | 0.0252 | -1.72 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 1 | 1 | 0.0525 | -1.4 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_ok|time=time_1400_close` | 3 | 1 | 0.2275 | 0.5 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_1200_1400` | 3 | 1 | 0.4501 | 0.06 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 8 | 1 | 1.3388 | -1.78 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_1000_1200` | 28 | 1 | -1.1651 | -3.78 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_1400_close` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_ok|time=time_1400_close` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_ok|time=time_1400_close` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1400_close` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 1 | 0 | None | None | None | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- `entry_bucket_unknown_source_quality_1`: `chosen_action` / `NO_BUY_AI` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_2`: `combo_entry_spot` / `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1200_1400` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_3`: `exit_rule` / `exit_unknown` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_4`: `liquidity_bucket` / `liquidity_not_available` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_5`: `overbought_bucket` / `overbought_not_available` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_6`: `score_band` / `score_lt60` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_7`: `source_stage` / `scalp_entry_action_decision_snapshot` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_8`: `stale_bucket` / `stale_not_available` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_9`: `strength_bucket` / `risk_unknown` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_10`: `time_bucket` / `time_1200_1400` -> `unknown_bucket_source_quality_blocker`

## Submit Bucket Attribution

- decision_authority: `adm_ldm_submit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'submit_rows': 84, 'bucket_count': 95, 'contract_gap_count': 0, 'workorder_count': 0, 'runtime_candidate_count': 0, 'quote_freshness_attribution_present': True, 'row_quote_freshness_attribution_present': True, 'sentinel_quote_freshness_attribution_present': True, 'sentinel_quote_freshness_attribution': {'source_report_type': 'buy_funnel_sentinel', 'decision_authority': 'submit_drought_quote_freshness_attribution_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'forbidden_uses': ['broker_order_submit', 'adm_ldm_training_input', 'general_threshold_ev_input', 'live_auto_promotion'], 'refresh_attempted_count': 89, 'refresh_applied_count': 72, 'still_latency_blocked_after_refresh_count': 44, 'latency_pass_recovered_count': 32, 'order_bundle_submitted_after_refresh_count': 3, 'refresh_subreason_counts': {'observer_quote_refresh_failed_invalid': 1, 'ws_snapshot_refresh_failed_input_snapshot_fresh': 207, 'ws_snapshot_refresh_failed_invalid': 1, 'ws_snapshot_refresh_failed_stale': 2}, 'refresh_block_subreason_counts': {'observer_quote_refresh_failed_invalid': 1, 'ws_snapshot_refresh_failed_input_snapshot_fresh': 207, 'ws_snapshot_refresh_failed_invalid': 1, 'ws_snapshot_refresh_failed_stale': 2}, 'latency_pass_recovered_downstream_counts': {'budget_pass_no_submit_event': 6, 'entry_ai_authority_revalidation': 22, 'order_bundle_submitted': 3, 'upstream_block_after_latency_recovery': 1}, 'post_restart_window_policy': 'event_provenance_only'}, 'quote_freshness_resolution_counts': {'refresh_attempted_unresolved': 20, 'refresh_failed_quote_stale': 2, 'refresh_not_attempted_or_not_instrumented': 18, 'refresh_resolved_quote_freshness': 18, 'sim_submit_path_not_applicable': 26}, 'pre_submit_refresh_applied_counts': {'refresh_attempted_not_applied': 22, 'refresh_not_attempted_or_not_instrumented': 18, 'sim_submit_path_not_applicable': 26, 'ws_snapshot_refresh_applied': 18}, 'real_submitted_row_count': 15, 'missing_broker_order_key_count': 0, 'bot_history_broker_order_key_backfill_candidate_count': 0, 'bot_history_broker_order_key_backfill_full_coverage': False, 'bot_history_broker_order_key_exact_mapping_count': 0, 'bot_history_broker_order_key_exact_mapping_full_coverage': False, 'post_submit_provenance_join_resolution': 'no_gap_broker_order_key_present_or_no_missing_rows', 'bot_history_broker_order_key_backfill_candidates': [], 'missing_broker_order_key_rate': 0.0, 'post_submit_provenance_join_gap_raw': False, 'post_submit_provenance_join_gap': False}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 69 | 23 | -0.3971 | `keep_collecting` |
| `actual_order_submitted` | `true` | 15 | 0 | None | `keep_collecting` |
| `broker_order_forbidden` | `true` | 69 | 23 | -0.3971 | `keep_collecting` |
| `broker_order_forbidden` | `false` | 15 | 0 | None | `keep_collecting` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_attempted_unresolved|fill=false|submitted=false` | 18 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_resolved_quote_freshness|fill=false|submitted=false` | 18 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=caution|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 12 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 8 | 5 | 0.17 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 5 | 5 | -2.0011 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 4 | 4 | -0.8732 | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_lt1s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=caution|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 3 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=entry_submit_revalidation_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=latency_unknown|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=false` | 2 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_normal|latency=danger|refresh=refresh_attempted_unresolved|fill=false|submitted=false` | 2 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_failed_quote_stale|fill=false|submitted=false` | 2 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 2 | 2 | -0.3575 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 2 | 2 | 0.14 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 2 | 2 | 2.3542 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_overbought_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=pullback_or_rebreak_not_confirmed|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 2 | 2 | 0.3264 | `source_quality_workorder` |
| `combo_submit_quality` | `source=pre_submit_liquidity_guard_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=latency_unknown|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_overbought_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=pullback_or_rebreak_not_confirmed|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | -1.4104 | `source_quality_workorder` |
| `latency_reason` | `scalp_live_simulator` | 26 | 23 | -0.3971 | `keep_collecting` |
| `latency_reason` | `caution_normal_entry_allowed` | 15 | 0 | None | `keep_collecting` |
| `latency_reason` | `spread_above_caution_below_guard_cap` | 14 | 0 | None | `keep_collecting` |
| `latency_reason` | `ws_age_too_high` | 12 | 0 | None | `keep_collecting` |
| `latency_reason` | `spread_too_wide` | 8 | 0 | None | `keep_collecting` |
| `latency_reason` | `ws_age_too_high,spread_too_wide` | 5 | 0 | None | `keep_collecting` |
| `latency_reason` | `latency_reason_unknown` | 3 | 0 | None | `source_quality_workorder` |
| `latency_reason` | `quote_stale,ws_age_too_high` | 1 | 0 | None | `keep_collecting` |
| `latency_state` | `danger` | 40 | 0 | None | `keep_collecting` |
| `latency_state` | `simulated` | 26 | 23 | -0.3971 | `keep_collecting` |
| `latency_state` | `caution` | 15 | 0 | None | `keep_collecting` |
| `latency_state` | `latency_unknown` | 3 | 0 | None | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_not_available` | 57 | 0 | None | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 15 | 12 | -0.0286 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 12 | 11 | -0.7991 | `keep_collecting` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 58 | 0 | None | `source_quality_workorder` |
| `liquidity_guard_action` | `would_pass` | 15 | 12 | -0.0286 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 11 | 11 | -0.7991 | `keep_collecting` |
| `overbought_bucket` | `overbought_not_available` | 56 | 0 | None | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 16 | 13 | 0.1804 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 28, 'source_row_count': 28, 'bucket_count': 26, 'joined_sample': 115, 'source_quality_adjusted_ev_pct': -0.7273, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 9, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 9 | 9 | -0.6744 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 4 | 4 | -1.8937 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 3 | 3 | -0.7595 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 2 | 2 | -0.5625 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 2 | 2 | -0.433 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 0.3319 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | 0.565 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 0.2903 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_020_180s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_180_600s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_not_applicable_at_start` | 26 | 23 | -0.7273 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_020_180s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 1 | 0 | None | `hold_sample` |
| `holding_action` | `holding_action_not_applicable_at_start` | 12 | 12 | -0.9628 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 14 | 11 | -0.4703 | `candidate_tighten_or_exclude` |
| `holding_action` | `SELL_TODAY` | 2 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 26 | 23 | -0.7273 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 2 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 14 | 13 | -1.0496 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 4 | 4 | -0.4867 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 3 | 2 | -0.5625 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 2 | 2 | -0.433 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 1 | 1 | 0.565 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 1 | 1 | 0.2903 | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 3 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- `holding_bucket_source_quality_1`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_2`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_3`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_4`: `held_bucket` / `held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_5`: `holding_action` / `holding_action_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_6`: `holding_action` / `WAIT` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_7`: `holding_source_stage` / `scalp_sim_holding_started` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_8`: `profit_band` / `profit_lt_neg070` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_9`: `profit_band` / `profit_neg010_pos080` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Exit Bucket Attribution

- decision_authority: `adm_ldm_exit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'exit_rows': 712, 'source_row_count': 712, 'bucket_count': 42, 'joined_sample': 235, 'source_quality_adjusted_ev_pct': -0.7834, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 13 | 13 | -1.1169 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 9 | 9 | -0.4811 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 4 | 4 | -0.774 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 4 | 4 | -1.0423 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 2 | 2 | -2.2718 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 2 | 2 | -1.2632 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 2 | 2 | -0.433 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_lt_neg070` | 1 | 1 | -0.8475 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 1 | 1 | -0.3975 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 1 | 1 | -1.086 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | -0.2206 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=NEUTRAL|profit=profit_lt_neg070` | 1 | 1 | -0.5293 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=NEUTRAL|profit=profit_neg070_neg010` | 1 | 1 | -0.2828 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg070_neg010` | 1 | 1 | -0.8423 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 1 | 1 | 0.2903 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 1 | 1 | 0.2478 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 1 | 1 | 0.3319 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 1 | 1 | 0.565 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=scalp_sim_panic_context_warning_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 665 | 0 | None | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 22 | 22 | -0.8568 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 9 | 9 | -1.0638 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 8 | 8 | -0.3764 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 6 | 6 | -0.6904 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `COMPLETED` | 2 | 2 | -0.6225 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 665 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 22 | 22 | -0.8568 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 9 | 9 | -0.3111 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 6 | 6 | -0.7338 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 6 | 6 | -1.4521 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 4 | 4 | -0.5143 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_context_warning_not_applicable` | 665 | 0 | None | `hold_sample` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 23 | 23 | -0.7273 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 22 | 22 | -0.8568 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 2 | 2 | -0.6225 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 665 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 27 | 27 | -1.0745 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 12 | 12 | -0.4877 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 4 | 4 | -0.4867 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 2 | 2 | -0.433 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 1 | 1 | 0.565 | `hold_sample` |

### Exit Bucket Attribution Workorders

- `exit_bucket_source_quality_1`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_2`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_3`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_4`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_5`: `exit_outcome` / `outcome_not_applicable_partial_exit` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_6`: `exit_outcome` / `GOOD_EXIT` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_7`: `exit_outcome` / `NEUTRAL` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_8`: `exit_outcome` / `MISSED_UPSIDE` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_9`: `exit_rule` / `scalp_sim_panic_lifecycle_partial_exit` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_10`: `exit_rule` / `scalp_trailing_take_profit` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `incremental_notional_ev_pct`
- summary: `{'scale_in_rows': 1334, 'bucket_count': 162, 'edge_bucket_count': 0, 'actionable_bucket_count': 0, 'runtime_authority_blocked_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'arm_counts': {'AVG_DOWN': 1279, 'PYRAMID': 55}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 1331 | 1331 | None | -0.952 | 0.0398 | `hold_sample` |
| `ai_score_band` | `score_unknown` | 3 | 0 | None | None | None | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 674 | 674 | None | -0.8881 | 0.0356 | `hold_sample` |
| `ai_score_source` | `live` | 400 | 400 | None | -0.9498 | 0.0625 | `hold_sample` |
| `ai_score_source` | `not_evaluated_no_ai_score_source` | 127 | 127 | None | -0.8727 | 0.0 | `hold_sample` |
| `ai_score_source` | `holding_ai_not_called` | 72 | 72 | None | -1.606 | 0.0556 | `hold_sample` |
| `ai_score_source` | `prior_valid` | 47 | 47 | None | -1.1306 | 0.0 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 11 | 11 | None | -0.8173 | 0.0 | `hold_sample` |
| `ai_score_source` | `stage_rule_backfilled` | 3 | 0 | None | None | None | `hold_sample` |
| `arm` | `AVG_DOWN` | 1279 | 1276 | None | -0.9983 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 55 | 55 | None | 0.1236 | 0.9636 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 1266 | 1263 | None | -0.9761 | 0.0 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 55 | 55 | None | 0.1236 | 0.9636 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 13 | 13 | None | -3.1615 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.64)` | 73 | 73 | None | -0.64 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.23)` | 64 | 64 | None | -0.23 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.51)` | 62 | 62 | None | -0.51 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.37)` | 61 | 61 | None | -0.37 | 0.0 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 53 | 53 | None | 0.123 | 0.9623 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.78)` | 48 | 48 | None | -0.78 | 0.0 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `adm_ldm_overnight_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'observation_state': 'observed', 'observation_reason': 'overnight_pipeline_rows_available', 'source_artifact_present': True, 'overnight_rows': 4, 'bucket_count': 19, 'actionable_bucket_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'status_counts': {'HOLD_OVERNIGHT': 2, 'SELL_TODAY': 2}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 1 | 1 | -0.8475 | -1.13 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 1 | 1 | -0.3975 | -0.53 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_lt_neg070` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 1 | 0 | None | None | None | `hold_sample` |
| `confidence_band` | `confidence_070p` | 4 | 2 | -0.6225 | -0.83 | 0.0 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 2 | 1 | -0.8475 | -1.13 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 2 | 1 | -0.3975 | -0.53 | 0.0 | `hold_sample` |
| `overnight_action` | `SELL_TODAY` | 4 | 2 | -0.6225 | -0.83 | 0.0 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 2 | 2 | -0.6225 | -0.83 | 0.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 2 | 0 | None | None | None | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 4 | 2 | -0.6225 | -0.83 | 0.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 4 | 2 | -0.6225 | -0.83 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 2 | 1 | -0.8475 | -1.13 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 2 | 1 | -0.3975 | -0.53 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 4 | 2 | -0.6225 | -0.83 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 2 | 2 | -0.6225 | -0.83 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_decision` | 2 | 0 | None | None | None | `hold_sample` |
| `stage` | `exit` | 2 | 2 | -0.6225 | -0.83 | 0.0 | `hold_sample` |
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
