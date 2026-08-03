# Lifecycle Decision Matrix - 2026-08-03

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-08-03`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `1535`
- source_rows_total: `2774`
- retained_rows: `1535`
- dropped_rows_by_source: `{'dedupe': 1239}`
- joined_rows: `131`
- policy_pass_count: `2`
- promote_ready_count: `1`
- entry_bucket_actionable_count: `14`
- entry_bucket_runtime_candidate_count: `10`
- holding_bucket_count/workorders: `9` / `0`
- exit_bucket_count/workorders: `20` / `1`
- scale_in_bucket_actionable_count: `0`
- scale_in_bucket_runtime_candidate_count: `0`
- overnight_bucket_actionable_count: `0`
- overnight_bucket_runtime_candidate_count: `0`
- lifecycle_flow_bucket_count: `46`
- lifecycle_flow_complete_count: `3`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `0` / `3` / `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0041`
- incomplete_flow_reason_counts: `{'missing_holding': 728, 'missing_exit': 565, 'missing_submit': 662, 'candidate_id_only': 424, 'missing_entry': 221, 'scale_in_noise_only': 58, 'postclose_exit_without_entry': 163, 'sim_record_id_only': 3}`
- bucket_directed_sim_probe: `{'observed_row_count': 456, 'matched_row_count': 0, 'background_row_count': 456, 'matched_unique_source_bucket_count': 0, 'match_status_counts': {'not_instrumented': 304, 'policy_missing': 152}, 'matched_classification_state_counts': {}, 'primary_source': 'matched_bucket_directed_sim_probe_only', 'background_source': 'unmatched_or_policy_missing_sim_observation', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 1, 'route_counts': {'bounded_auxiliary_weight': 1, 'hold_sample': 4}, 'quality_counts': {'observational_only_pending_outcome': 1, 'hold_sample': 4}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 1238 | 65 | 3.3648 | 0.3413 | `pass` | `BUY_DEFENSIVE` | True |
| `submit` | 69 | 2 | 1.2247 | 0.0058 | `hold_sample` | `ALLOW_SUBMIT` | False |
| `holding` | 3 | 2 | 0.4752 | 0.1333 | `hold_sample` | `HOLD` | False |
| `scale_in` | 58 | 58 | -0.8649 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 167 | 4 | -0.2299 | 0.0096 | `hold_sample` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 731, 'complete_flow_count': 3, 'direct_sim_record_complete_flow_count': 0, 'adm_bridge_complete_flow_count': 3, 'fallback_complete_flow_count': 0, 'direct_flow_zero_diagnostic': {'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'direct_sim_record_flow_count': 3, 'direct_sim_record_incomplete_flow_count': 3, 'direct_sim_record_stage_coverage_counts': {}, 'direct_sim_record_incomplete_reason_counts': {'missing_entry': 3, 'missing_submit': 3, 'missing_holding': 3, 'missing_exit': 3, 'sim_record_id_only': 3, 'scale_in_noise_only': 3}, 'runtime_effect': False, 'decision_authority': 'ldm_direct_flow_diagnostic_only'}, 'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'incomplete_flow_count': 728, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 1535, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0041, 'complete_flow_conversion_denominator': 166, 'complete_flow_conversion_rate': 0.0181, 'active_priority_incomplete_seed_count': 507, 'scale_in_followup_event_count': 58, 'scale_in_unique_flow_count': 48, 'scale_in_noise_flow_count': 58, 'denominator_exclusion_counts': {'scale_in_noise_flow_excluded': 58, 'active_priority_incomplete_seed_excluded': 507}, 'conversion_blocker_reason_counts': {'missing_entry': 163, 'missing_submit': 163, 'missing_holding': 163, 'candidate_id_only': 163, 'postclose_exit_without_entry': 163}, 'observation_seed_reason_counts': {'missing_holding': 565, 'missing_exit': 565, 'missing_submit': 499, 'candidate_id_only': 261, 'missing_entry': 58, 'scale_in_noise_only': 58, 'sim_record_id_only': 3}, 'join_contract_blocked': False, 'bundle_ev_tuning_state': 'ready_for_bundle_ev_tuning', 'top_incomplete_reason': 'missing_holding', 'stage_identity': {'entry': {'source_row_count': 1238, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 1032, 'candidate_id': 206}, 'identity_join_rate': 1.0}, 'submit': {'source_row_count': 69, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 69}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 3, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 3}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 58, 'identity_missing_count': 0, 'identity_quality_counts': {'candidate_id': 55, 'exact_sim_record_id': 3}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 167, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 4, 'candidate_id': 163}, 'identity_join_rate': 1.0}}, 'required_stage_source_counts': {'entry': 1238, 'submit': 69, 'holding': 3, 'exit': 167}, 'incomplete_flow_reason_counts': {'missing_holding': 728, 'missing_exit': 565, 'missing_submit': 662, 'candidate_id_only': 424, 'missing_entry': 221, 'scale_in_noise_only': 58, 'postclose_exit_without_entry': 163, 'sim_record_id_only': 3}, 'bucket_count': 46, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:99013dc4f3` | 1 | 1 | 1.2012 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:d0233209ef` | 1 | 1 | -0.83 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:a5ddbd8b87` | 1 | 1 | -1.04 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 58 | 58 | 3.4417 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 53 | 53 | -1.0143 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 5 | 5 | 0.718 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 4 | 4 | 3.1589 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:2a245e5d4f` | 1 | 1 | 4.0086 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:db8bbc6230` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:01a26e930a` | 3 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_ai:c18e731ca8` | 13 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_ai:9a372901ee` | 3 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_bl:cf6cca51c3` | 4 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:b90a5c668a` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:6d88d558c7` | 7 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:1c4ab1bc7c` | 18 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:542cd2bc91` | 109 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_ai:0370c0d68d` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_bl:98023dd644` | 2 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_sc:ccaec8e263` | 4 | 0 | None | `hold_sample` | `join_contract_blocked` |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 1238, 'bucket_count': 218, 'actionable_bucket_count': 14, 'source_quality_blocked_bucket_count': 10, 'runtime_candidate_count': 10, 'workorder_count': 20}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `WAIT_REQUOTE` | 389 | 63 | 3.4327 | 5.2779 | 0.746 | `candidate_recovery_or_relax` |
| `chosen_action` | `NO_BUY_AI` | 519 | 1 | 1.3075 | 1.11 | 1.0 | `hold_sample` |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 143 | 1 | 1.1418 | -1.6 | 0.0 | `source_quality_workorder` |
| `chosen_action` | `ALLOW_BOTTOMING_ENTRY` | 21 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `ALLOW_LEVEL1_RISK_OFF_ENTRY` | 122 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `BUY_DEFENSIVE` | 36 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_STALE` | 8 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_1000_1200` | 24 | 24 | 2.7518 | 3.8641 | 0.6667 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 15 | 15 | 2.187 | 3.0597 | 0.7333 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_ok|time=time_1000_1200` | 9 | 9 | 7.6585 | 13.6406 | 0.8889 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 5 | 5 | 1.4503 | 1.4482 | 0.8 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_chase_risk|time=time_1000_1200` | 3 | 3 | 7.5937 | 12.2302 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_ok|time=time_1400_close` | 1 | 1 | 1.3075 | 1.11 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_0900_1000` | 19 | 1 | 1.1418 | -1.6 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_chase_risk|time=time_0900_1000` | 1 | 1 | 3.2929 | 4.1737 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_ok|time=time_0900_1000` | 1 | 1 | -1.4818 | -1.7564 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_mid|overbought=overbought_watch|time=time_1000_1200` | 1 | 1 | 4.0086 | 5.8844 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_chase_risk|time=time_0900_1000` | 1 | 1 | 5.1904 | 8.0924 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 1 | 1 | 2.5647 | 3.1356 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 1 | 1 | -0.5234 | -0.934 | 0.0 | `hold_sample` |
| `liquidity_bucket` | `liquidity_high` | 390 | 63 | 3.3899 | 5.2021 | 0.746 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_watch` | 350 | 42 | 2.5652 | 3.623 | 0.6905 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_ok` | 81 | 11 | 6.2502 | 11.1017 | 0.8182 | `candidate_recovery_or_relax` |
| `score_band` | `score_63_65` | 349 | 61 | 3.3783 | 5.1335 | 0.7377 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 63 | 63 | 3.4327 | 5.2779 | 0.746 | `candidate_recovery_or_relax` |

### Entry Bucket Runtime Approval Candidates

- `entry_bucket_2`: `combo_entry_spot` / `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_1000_1200` -> `candidate_recovery_or_relax`
- `entry_bucket_4`: `liquidity_bucket` / `liquidity_high` -> `candidate_recovery_or_relax`
- `entry_bucket_5`: `overbought_bucket` / `overbought_watch` -> `candidate_recovery_or_relax`
- `entry_bucket_7`: `score_band` / `score_63_65` -> `candidate_recovery_or_relax`
- `entry_bucket_8`: `source_stage` / `wait6579_ev_cohort` -> `candidate_recovery_or_relax`
- `entry_bucket_9`: `stale_bucket` / `fresh_or_unflagged` -> `candidate_recovery_or_relax`
- `entry_bucket_10`: `strength_bucket` / `neutral_strength_momentum` -> `candidate_recovery_or_relax`
- `entry_bucket_11`: `strength_bucket` / `weak_strength_momentum` -> `candidate_recovery_or_relax`
- `entry_bucket_13`: `time_bucket` / `time_1000_1200` -> `candidate_recovery_or_relax`
- `entry_bucket_14`: `time_bucket` / `time_0900_1000` -> `candidate_recovery_or_relax`

### Entry Bucket Workorders

- `entry_bucket_unknown_source_quality_1`: `chosen_action` / `SKIP_PRE_SUBMIT_SAFETY` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_2`: `combo_entry_spot` / `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1400_close` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_3`: `exit_rule` / `exit_unknown` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_4`: `liquidity_bucket` / `liquidity_not_available` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_5`: `overbought_bucket` / `overbought_not_available` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_6`: `score_band` / `score_lt60` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_7`: `source_stage` / `scalp_entry_action_decision_snapshot` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_8`: `stale_bucket` / `stale_not_available` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_9`: `strength_bucket` / `risk_unknown` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_10`: `time_bucket` / `time_1400_close` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_source_quality_1`: `chosen_action` / `WAIT_REQUOTE` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_2`: `combo_entry_spot` / `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_1000_1200` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_3`: `combo_entry_spot` / `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_4`: `liquidity_bucket` / `liquidity_high` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_5`: `overbought_bucket` / `overbought_watch` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_6`: `overbought_bucket` / `overbought_ok` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_7`: `score_band` / `score_63_65` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_8`: `source_stage` / `wait6579_ev_cohort` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_9`: `stale_bucket` / `fresh_or_unflagged` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_10`: `strength_bucket` / `neutral_strength_momentum` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`

## Submit Bucket Attribution

- decision_authority: `adm_ldm_submit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'submit_rows': 69, 'bucket_count': 84, 'contract_gap_count': 0, 'workorder_count': 0, 'runtime_candidate_count': 0, 'quote_freshness_attribution_present': True, 'row_quote_freshness_attribution_present': True, 'sentinel_quote_freshness_attribution_present': True, 'sentinel_quote_freshness_attribution': {'source_report_type': 'buy_funnel_sentinel', 'decision_authority': 'submit_drought_quote_freshness_attribution_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'forbidden_uses': ['broker_order_submit', 'adm_ldm_training_input', 'general_threshold_ev_input', 'live_auto_promotion'], 'refresh_attempted_count': 116, 'refresh_applied_count': 47, 'still_latency_blocked_after_refresh_count': 101, 'latency_pass_recovered_count': 3, 'order_bundle_submitted_after_refresh_count': 2, 'refresh_subreason_counts': {'observer_quote_refresh_failed_invalid': 1, 'observer_quote_refresh_failed_stale': 12, 'ws_snapshot_refresh_failed_input_snapshot_fresh': 272, 'ws_snapshot_refresh_failed_invalid': 1, 'ws_snapshot_refresh_failed_missing': 1, 'ws_snapshot_refresh_failed_stale': 27}, 'refresh_block_subreason_counts': {'observer_quote_refresh_failed_invalid': 1, 'observer_quote_refresh_failed_stale': 12, 'ws_snapshot_refresh_failed_input_snapshot_fresh': 272, 'ws_snapshot_refresh_failed_invalid': 1, 'ws_snapshot_refresh_failed_missing': 1, 'ws_snapshot_refresh_failed_stale': 27}, 'latency_pass_recovered_downstream_counts': {'order_bundle_submitted': 2, 'price_guard_or_revalidation': 1}, 'post_restart_window_policy': 'event_provenance_only'}, 'quote_freshness_resolution_counts': {'refresh_attempted_unresolved': 33, 'refresh_failed_quote_stale': 10, 'refresh_not_attempted_or_not_instrumented': 14, 'refresh_resolved_quote_freshness': 9, 'sim_submit_path_not_applicable': 3}, 'pre_submit_refresh_applied_counts': {'refresh_attempted_not_applied': 43, 'refresh_not_attempted_or_not_instrumented': 14, 'sim_submit_path_not_applicable': 3, 'ws_snapshot_refresh_applied': 9}, 'real_submitted_row_count': 14, 'missing_broker_order_key_count': 0, 'bot_history_broker_order_key_backfill_candidate_count': 0, 'bot_history_broker_order_key_backfill_full_coverage': False, 'bot_history_broker_order_key_exact_mapping_count': 0, 'bot_history_broker_order_key_exact_mapping_full_coverage': False, 'post_submit_provenance_join_resolution': 'no_gap_broker_order_key_present_or_no_missing_rows', 'bot_history_broker_order_key_backfill_candidates': [], 'missing_broker_order_key_rate': 0.0, 'post_submit_provenance_join_gap_raw': False, 'post_submit_provenance_join_gap': False}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 55 | 2 | 1.2247 | `keep_collecting` |
| `actual_order_submitted` | `true` | 14 | 0 | None | `keep_collecting` |
| `broker_order_forbidden` | `true` | 55 | 2 | 1.2247 | `keep_collecting` |
| `broker_order_forbidden` | `false` | 14 | 0 | None | `keep_collecting` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_attempted_unresolved|fill=false|submitted=false` | 33 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_failed_quote_stale|fill=false|submitted=false` | 10 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_resolved_quote_freshness|fill=false|submitted=false` | 9 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=caution|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 7 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_lt1s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=caution|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 3 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=safe|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=safe|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_lt1s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_lt1s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=safe|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 1 | 1 | 1.3075 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | 1.1418 | `source_quality_workorder` |
| `latency_reason` | `spread_above_caution_below_guard_cap` | 20 | 0 | None | `keep_collecting` |
| `latency_reason` | `spread_too_wide` | 11 | 0 | None | `keep_collecting` |
| `latency_reason` | `ws_age_too_high` | 11 | 0 | None | `keep_collecting` |
| `latency_reason` | `caution_normal_entry_allowed` | 10 | 0 | None | `keep_collecting` |
| `latency_reason` | `ws_age_too_high,spread_too_wide` | 7 | 0 | None | `keep_collecting` |
| `latency_reason` | `safe_normal_entry_allowed` | 3 | 0 | None | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 3 | 2 | 1.2247 | `keep_collecting` |
| `latency_reason` | `quote_stale,ws_age_too_high,spread_too_wide` | 2 | 0 | None | `keep_collecting` |
| `latency_reason` | `latency_true_ofi_false_negative_direct_canary_normal_override` | 1 | 0 | None | `keep_collecting` |
| `latency_reason` | `quote_stale,ws_age_too_high` | 1 | 0 | None | `keep_collecting` |
| `latency_state` | `danger` | 53 | 0 | None | `keep_collecting` |
| `latency_state` | `caution` | 10 | 0 | None | `keep_collecting` |
| `latency_state` | `safe` | 3 | 0 | None | `keep_collecting` |
| `latency_state` | `simulated` | 3 | 2 | 1.2247 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_not_available` | 66 | 0 | None | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 2 | 1 | 1.3075 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 1 | 1 | 1.1418 | `keep_collecting` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 66 | 0 | None | `source_quality_workorder` |
| `liquidity_guard_action` | `would_pass` | 2 | 1 | 1.3075 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 1 | 1 | 1.1418 | `keep_collecting` |
| `overbought_bucket` | `overbought_not_available` | 66 | 0 | None | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 2 | 1 | 1.3075 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 1 | 1 | 1.1418 | `keep_collecting` |
| `overbought_guard_action` | `overbought_guard_unknown` | 66 | 0 | None | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 3, 'source_row_count': 3, 'bucket_count': 9, 'joined_sample': 10, 'source_quality_adjusted_ev_pct': 0.4752, 'source_quality_gate': 'hold_sample', 'unknown_reason_counts': {}, 'workorder_count': 0, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1 | 1 | -0.2509 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | 1.2012 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_not_applicable_at_start` | 3 | 2 | 0.4752 | `hold_sample` |
| `holding_action` | `WAIT` | 3 | 2 | 0.4752 | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 3 | 2 | 0.4752 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 1 | 1 | -0.2509 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 1 | 1 | 1.2012 | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `adm_ldm_exit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'exit_rows': 167, 'source_row_count': 167, 'bucket_count': 20, 'joined_sample': 20, 'source_quality_adjusted_ev_pct': -0.2299, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 1, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 2 | 2 | -0.935 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | -0.2509 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 1 | 1 | 1.2012 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_euphoria_context_noop|rule=scalp_sim_euphoria_context_noop_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 141 | 0 | None | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=scalp_sim_panic_context_warning_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 22 | 0 | None | `hold_sample` |
| `exit_outcome` | `MISSED_UPSIDE` | 2 | 2 | 0.4752 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 2 | 2 | -0.935 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 163 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 2 | 2 | -0.935 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 1 | 1 | -0.2509 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 1 | 1 | 1.2012 | `hold_sample` |
| `exit_rule` | `scalp_sim_euphoria_context_noop_not_applicable` | 141 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_context_warning_not_applicable` | 22 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 2 | 2 | -0.935 | `hold_sample` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 2 | 2 | 0.4752 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_euphoria_context_noop` | 141 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 22 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 3 | 3 | -0.707 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 1 | 1 | 1.2012 | `hold_sample` |
| `profit_band` | `profit_not_applicable_context_noop` | 163 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- `exit_bucket_source_quality_1`: `profit_band` / `profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `incremental_notional_ev_pct`
- summary: `{'scale_in_rows': 58, 'bucket_count': 54, 'edge_bucket_count': 0, 'actionable_bucket_count': 0, 'runtime_authority_blocked_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'arm_counts': {'AVG_DOWN': 53, 'PYRAMID': 5}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 58 | 58 | None | -0.9517 | 0.0862 | `hold_sample` |
| `ai_score_source` | `live` | 29 | 29 | None | -1.09 | 0.1034 | `hold_sample` |
| `ai_score_source` | `not_evaluated_no_ai_score_source` | 25 | 25 | None | -0.8272 | 0.04 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 3 | 3 | None | -0.5633 | 0.3333 | `hold_sample` |
| `ai_score_source` | `prior_valid` | 1 | 1 | None | -1.22 | 0.0 | `hold_sample` |
| `arm` | `AVG_DOWN` | 53 | 53 | None | -1.1092 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 5 | 5 | None | 0.718 | 1.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 53 | 53 | None | -1.1092 | 0.0 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 5 | 5 | None | 0.718 | 1.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.37)` | 6 | 6 | None | -1.37 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.21)` | 4 | 4 | None | -1.21 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.53)` | 4 | 4 | None | -1.53 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-2.18)` | 4 | 4 | None | -2.18 | 0.0 | `hold_sample` |
| `blocker_reason` | `entry_split_probe_scale_in_forbidden` | 3 | 3 | None | -1.2167 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.23)` | 3 | 3 | None | -0.23 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.32)` | 3 | 3 | None | -0.32 | 0.0 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 3 | 3 | None | 0.7267 | 1.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 3 | 3 | None | -0.5633 | 0.3333 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.14)` | 2 | 2 | None | -0.14 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.49)` | 2 | 2 | None | -0.49 | 0.0 | `hold_sample` |

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
