# Lifecycle Decision Matrix - 2026-06-26

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-26`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `6798`
- source_rows_total: `8676`
- retained_rows: `6798`
- dropped_rows_by_source: `{'dedupe': 1878}`
- joined_rows: `4093`
- policy_pass_count: `5`
- promote_ready_count: `1`
- entry_bucket_actionable_count: `16`
- entry_bucket_runtime_candidate_count: `10`
- holding_bucket_count/workorders: `26` / `10`
- exit_bucket_count/workorders: `46` / `10`
- scale_in_bucket_actionable_count: `0`
- scale_in_bucket_runtime_candidate_count: `0`
- overnight_bucket_actionable_count: `0`
- overnight_bucket_runtime_candidate_count: `0`
- lifecycle_flow_bucket_count: `72`
- lifecycle_flow_complete_count: `39`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `0` / `39` / `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0064`
- incomplete_flow_reason_counts: `{'missing_submit': 6051, 'missing_holding': 6048, 'missing_exit': 4014, 'candidate_id_only': 5918, 'missing_entry': 5862, 'sim_record_id_only': 70, 'scale_in_noise_only': 3821, 'postclose_exit_without_entry': 2041}`
- bucket_directed_sim_probe: `{'observed_row_count': 2352, 'matched_row_count': 0, 'background_row_count': 2352, 'matched_unique_source_bucket_count': 0, 'match_status_counts': {'no_match': 303, 'not_instrumented': 2049}, 'matched_classification_state_counts': {}, 'primary_source': 'matched_bucket_directed_sim_probe_only', 'background_source': 'unmatched_or_policy_missing_sim_observation', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 1, 'route_counts': {'bounded_auxiliary_weight': 1, 'hold_sample': 4}, 'quality_counts': {'observational_only_pending_outcome': 1, 'hold_sample': 4}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 623 | 98 | 0.8835 | 1.0 | `pass` | `BUY_DEFENSIVE` | True |
| `submit` | 93 | 70 | -0.5037 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 86 | 70 | -0.9629 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 3886 | 3723 | -0.1058 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 2110 | 132 | -0.9603 | 0.8258 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 6094, 'complete_flow_count': 39, 'direct_sim_record_complete_flow_count': 0, 'adm_bridge_complete_flow_count': 39, 'fallback_complete_flow_count': 0, 'direct_flow_zero_diagnostic': {'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'direct_sim_record_flow_count': 70, 'direct_sim_record_incomplete_flow_count': 70, 'direct_sim_record_stage_coverage_counts': {'exit': 63, 'holding': 4}, 'direct_sim_record_incomplete_reason_counts': {'missing_entry': 70, 'missing_submit': 70, 'missing_holding': 66, 'missing_exit': 7, 'sim_record_id_only': 70, 'scale_in_noise_only': 7, 'postclose_exit_without_entry': 63}, 'runtime_effect': False, 'decision_authority': 'ldm_direct_flow_diagnostic_only'}, 'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'incomplete_flow_count': 6055, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 6798, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0064, 'complete_flow_conversion_denominator': 2080, 'complete_flow_conversion_rate': 0.0187, 'active_priority_incomplete_seed_count': 193, 'scale_in_followup_event_count': 3886, 'scale_in_unique_flow_count': 3221, 'scale_in_noise_flow_count': 3821, 'denominator_exclusion_counts': {'scale_in_noise_flow_excluded': 3821, 'active_priority_incomplete_seed_excluded': 193}, 'conversion_blocker_reason_counts': {'missing_entry': 2041, 'missing_submit': 2041, 'missing_holding': 2037, 'sim_record_id_only': 63, 'postclose_exit_without_entry': 2041, 'candidate_id_only': 1978}, 'observation_seed_reason_counts': {'missing_submit': 4010, 'missing_holding': 4011, 'missing_exit': 4014, 'candidate_id_only': 3940, 'missing_entry': 3821, 'sim_record_id_only': 7, 'scale_in_noise_only': 3821}, 'join_contract_blocked': False, 'bundle_ev_tuning_state': 'ready_for_bundle_ev_tuning', 'top_incomplete_reason': 'missing_submit', 'stage_identity': {'entry': {'source_row_count': 623, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 497, 'candidate_id': 126}, 'identity_join_rate': 1.0}, 'submit': {'source_row_count': 93, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 93}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 86, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 82, 'exact_sim_record_id': 4}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 3886, 'identity_missing_count': 0, 'identity_quality_counts': {'exact_sim_record_id': 72, 'candidate_id': 3814}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 2110, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 65, 'exact_sim_record_id': 67, 'candidate_id': 1978}, 'identity_join_rate': 1.0}}, 'required_stage_source_counts': {'entry': 623, 'submit': 93, 'holding': 86, 'exit': 2110}, 'incomplete_flow_reason_counts': {'missing_submit': 6051, 'missing_holding': 6048, 'missing_exit': 4014, 'candidate_id_only': 5918, 'missing_entry': 5862, 'sim_record_id_only': 70, 'scale_in_noise_only': 3821, 'postclose_exit_without_entry': 2041}, 'bucket_count': 72, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:c1801bf4e3` | 3 | 3 | -2.3956 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:89e49a11bc` | 2 | 2 | -0.9762 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:f1afdbf31e` | 2 | 2 | -2.3266 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:4badedabe9` | 2 | 2 | -0.7389 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:acadf41d1b` | 1 | 1 | -1.1508 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:89550e9954` | 1 | 1 | -2.0794 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:3cbb81cd02` | 1 | 1 | -2.0077 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9d8cac316e` | 1 | 1 | -0.6766 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:18efae3686` | 1 | 1 | 0.8299 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:d5a4652d44` | 1 | 1 | 2.2912 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:4ff19246fa` | 1 | 1 | -2.557 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:6bf0a1f84a` | 1 | 1 | -2.2211 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:d0c0691471` | 1 | 1 | 4.3977 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:0df4cac793` | 1 | 1 | -1.3695 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:7248608969` | 1 | 1 | -0.9133 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:584d40b511` | 1 | 1 | 0.9455 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:c86da1173b` | 1 | 1 | -1.8237 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:2f4c990412` | 1 | 1 | -1.5975 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:04bb093e59` | 1 | 1 | -0.78 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:5d90359dac` | 1 | 1 | -2.0389 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 623, 'bucket_count': 189, 'actionable_bucket_count': 16, 'source_quality_blocked_bucket_count': 0, 'runtime_candidate_count': 10, 'workorder_count': 10}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `WAIT_REQUOTE` | 59 | 59 | 1.759 | 2.7409 | 0.6271 | `candidate_recovery_or_relax` |
| `chosen_action` | `NO_BUY_AI` | 482 | 36 | -0.4827 | -1.4028 | 0.1944 | `candidate_tighten_or_exclude` |
| `chosen_action` | `BUY_NOW` | 14 | 3 | 0.0588 | -2.4367 | 0.0 | `hold_sample` |
| `chosen_action` | `ALLOW_BOTTOMING_ENTRY` | 9 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `ALLOW_LEVEL1_RISK_OFF_ENTRY` | 58 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_SOURCE_QUALITY` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 9 | 9 | 3.2118 | 5.2572 | 0.8889 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 8 | 8 | 0.4554 | 0.2381 | 0.5 | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 6 | 6 | 3.3435 | 5.1423 | 0.8333 | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1400_close` | 6 | 6 | 0.2821 | 0.0661 | 0.5 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 33 | 5 | 0.301 | -2.552 | 0.2 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 30 | 5 | -0.9196 | -1.274 | 0.4 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 5 | 5 | 5.6938 | 9.7879 | 0.8 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 11 | 4 | -0.88 | -0.445 | 0.25 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 31 | 4 | -0.4735 | -2.4125 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 4 | 4 | 3.2535 | 4.9861 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 3 | 3 | 1.4512 | 1.9049 | 0.6667 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 3 | 3 | -1.0174 | -1.465 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1400_close` | 3 | 3 | -0.2092 | -0.8179 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 12 | 3 | -0.0287 | -2.1833 | 0.0 | `hold_sample` |
| `exit_rule` | `exit_unknown` | 584 | 59 | 1.759 | 2.7409 | 0.6271 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_soft_stop_pct` | 20 | 20 | -0.2712 | -1.9285 | 0.0 | `hold_no_edge` |
| `exit_rule` | `scalp_hard_stop_pct` | 12 | 12 | -0.1074 | -3.4092 | 0.0 | `hold_no_edge` |
| `liquidity_bucket` | `liquidity_high` | 499 | 98 | 0.8835 | 1.0603 | 0.449 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 430 | 75 | 1.1832 | 1.1824 | 0.4533 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_watch` | 118 | 22 | -0.1323 | 0.8519 | 0.4545 | `hold_no_edge` |
| `score_band` | `score_60_62` | 347 | 28 | -0.6607 | -1.1314 | 0.25 | `candidate_tighten_or_exclude` |
| `score_band` | `score_66_69` | 51 | 28 | 2.2276 | 3.5079 | 0.7143 | `candidate_recovery_or_relax` |
| `score_band` | `score_70p` | 59 | 27 | 0.389 | 0.1737 | 0.4074 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 59 | 59 | 1.759 | 2.7409 | 0.6271 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 402 | 39 | -0.4411 | -1.4823 | 0.1795 | `candidate_tighten_or_exclude` |
| `stale_bucket` | `fresh_or_unflagged` | 126 | 59 | 1.759 | 2.7409 | 0.6271 | `candidate_recovery_or_relax` |
| `stale_bucket` | `stale_high` | 316 | 23 | -0.6234 | -1.3422 | 0.1739 | `candidate_tighten_or_exclude` |
| `stale_bucket` | `fresh` | 135 | 16 | -0.1789 | -1.6838 | 0.1875 | `hold_no_edge` |
| `strength_bucket` | `strong_strength_momentum` | 121 | 52 | 1.2835 | 2.1804 | 0.5769 | `candidate_recovery_or_relax` |
| `strength_bucket` | `weak_strength_momentum` | 344 | 39 | 0.5083 | 0.1314 | 0.3333 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_1000_1200` | 163 | 35 | 1.691 | 2.242 | 0.5429 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_0900_1000` | 215 | 28 | -0.2458 | -0.8817 | 0.2143 | `hold_no_edge` |
| `time_bucket` | `time_1200_1400` | 107 | 21 | 1.4648 | 2.5314 | 0.6667 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_1400_close` | 138 | 14 | 0.2513 | -0.217 | 0.3571 | `hold_no_edge` |

### Entry Bucket Runtime Approval Candidates

- `entry_bucket_4`: `liquidity_bucket` / `liquidity_high` -> `candidate_recovery_or_relax`
- `entry_bucket_5`: `overbought_bucket` / `overbought_normal` -> `candidate_recovery_or_relax`
- `entry_bucket_6`: `score_band` / `score_60_62` -> `candidate_tighten_or_exclude`
- `entry_bucket_7`: `score_band` / `score_66_69` -> `candidate_recovery_or_relax`
- `entry_bucket_8`: `score_band` / `score_70p` -> `candidate_recovery_or_relax`
- `entry_bucket_9`: `source_stage` / `wait6579_ev_cohort` -> `candidate_recovery_or_relax`
- `entry_bucket_10`: `source_stage` / `scalp_entry_action_decision_snapshot` -> `candidate_tighten_or_exclude`
- `entry_bucket_11`: `stale_bucket` / `fresh_or_unflagged` -> `candidate_recovery_or_relax`
- `entry_bucket_12`: `stale_bucket` / `stale_high` -> `candidate_tighten_or_exclude`
- `entry_bucket_13`: `strength_bucket` / `strong_strength_momentum` -> `candidate_recovery_or_relax`

### Entry Bucket Workorders

- `entry_bucket_source_quality_1`: `chosen_action` / `WAIT_REQUOTE` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_2`: `chosen_action` / `NO_BUY_AI` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_3`: `exit_rule` / `exit_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_4`: `liquidity_bucket` / `liquidity_high` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_5`: `overbought_bucket` / `overbought_normal` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_6`: `score_band` / `score_60_62` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_7`: `score_band` / `score_66_69` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_8`: `score_band` / `score_70p` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_9`: `source_stage` / `wait6579_ev_cohort` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_10`: `source_stage` / `scalp_entry_action_decision_snapshot` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`

## Submit Bucket Attribution

- decision_authority: `adm_ldm_submit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'submit_rows': 93, 'bucket_count': 76, 'contract_gap_count': 0, 'workorder_count': 0, 'runtime_candidate_count': 0, 'quote_freshness_attribution_present': True, 'row_quote_freshness_attribution_present': False, 'sentinel_quote_freshness_attribution_present': True, 'sentinel_quote_freshness_attribution': {'source_report_type': 'buy_funnel_sentinel', 'decision_authority': 'submit_drought_quote_freshness_attribution_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'forbidden_uses': ['broker_order_submit', 'adm_ldm_training_input', 'general_threshold_ev_input', 'live_auto_promotion'], 'refresh_attempted_count': 22, 'refresh_applied_count': 20, 'still_latency_blocked_after_refresh_count': 4, 'latency_pass_recovered_count': 10, 'order_bundle_submitted_after_refresh_count': 6, 'refresh_subreason_counts': {'observer_quote_refresh_failed_stale': 3, 'ws_snapshot_refresh_failed_stale': 2, 'ws_snapshot_refresh_failed_missing': 1}, 'refresh_block_subreason_counts': {'observer_quote_refresh_failed_stale': 3, 'ws_snapshot_refresh_failed_stale': 2, 'ws_snapshot_refresh_failed_missing': 1}, 'latency_pass_recovered_downstream_counts': {'armed_expired_before_submit': 2, 'no_downstream_event': 1, 'order_bundle_submitted': 6, 'upstream_block_after_latency_recovery': 1}, 'post_restart_window_policy': 'event_provenance_only'}, 'quote_freshness_resolution_counts': {'refresh_not_attempted_or_not_instrumented': 11, 'sim_submit_path_not_applicable': 82}, 'pre_submit_refresh_applied_counts': {'refresh_not_attempted_or_not_instrumented': 11, 'sim_submit_path_not_applicable': 82}, 'real_submitted_row_count': 9, 'missing_broker_order_key_count': 0, 'bot_history_broker_order_key_backfill_candidate_count': 0, 'bot_history_broker_order_key_backfill_full_coverage': False, 'bot_history_broker_order_key_exact_mapping_count': 0, 'bot_history_broker_order_key_exact_mapping_full_coverage': False, 'post_submit_provenance_join_resolution': 'no_gap_broker_order_key_present_or_no_missing_rows', 'bot_history_broker_order_key_backfill_candidates': [], 'missing_broker_order_key_rate': 0.0, 'post_submit_provenance_join_gap_raw': False, 'post_submit_provenance_join_gap': False}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 84 | 70 | -0.5037 | `keep_collecting` |
| `actual_order_submitted` | `true` | 9 | 0 | None | `keep_collecting` |
| `broker_order_forbidden` | `true` | 84 | 70 | -0.5037 | `keep_collecting` |
| `broker_order_forbidden` | `false` | 9 | 0 | None | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 38 | 33 | -0.3751 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 20 | 16 | -0.7808 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 10 | 9 | -0.5582 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 7 | 7 | -0.7944 | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=caution|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 5 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 3 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 2 | 2 | 0.276 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 2 | 2 | 0.0093 | `source_quality_workorder` |
| `combo_submit_quality` | `source=entry_submit_revalidation_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=latency_unknown|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_lt1s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=safe|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=pre_submit_liquidity_guard_block|revalidation=ok_or_unflagged|quote_age=quote_age_lt1s|liquidity=below_min_liquidity|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=latency_unknown|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 1 | 1 | -0.3755 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `latency_reason` | `scalp_live_simulator` | 82 | 70 | -0.5037 | `keep_collecting` |
| `latency_reason` | `caution_normal_entry_allowed` | 5 | 0 | None | `keep_collecting` |
| `latency_reason` | `latency_reason_unknown` | 2 | 0 | None | `source_quality_workorder` |
| `latency_reason` | `latency_other_danger_relief_normal_override` | 1 | 0 | None | `keep_collecting` |
| `latency_reason` | `latency_quote_fresh_composite_normal_override` | 1 | 0 | None | `keep_collecting` |
| `latency_reason` | `latency_spread_relief_normal_override` | 1 | 0 | None | `keep_collecting` |
| `latency_reason` | `safe_normal_entry_allowed` | 1 | 0 | None | `keep_collecting` |
| `latency_state` | `simulated` | 82 | 70 | -0.5037 | `keep_collecting` |
| `latency_state` | `caution` | 5 | 0 | None | `keep_collecting` |
| `latency_state` | `danger` | 3 | 0 | None | `keep_collecting` |
| `latency_state` | `latency_unknown` | 2 | 0 | None | `source_quality_workorder` |
| `latency_state` | `safe` | 1 | 0 | None | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 51 | 45 | -0.3943 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 32 | 25 | -0.7007 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_not_available` | 10 | 0 | None | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 51 | 45 | -0.3943 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 31 | 25 | -0.7007 | `keep_collecting` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 11 | 0 | None | `source_quality_workorder` |
| `overbought_bucket` | `overbought_ok` | 77 | 67 | -0.5289 | `keep_collecting` |
| `overbought_bucket` | `overbought_not_available` | 11 | 0 | None | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 5 | 3 | 0.0588 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 82 | 70 | -0.5037 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 86, 'source_row_count': 86, 'bucket_count': 26, 'joined_sample': 350, 'source_quality_adjusted_ev_pct': -0.9629, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 53 | 53 | -1.4914 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 6 | 6 | 0.162 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 3 | 3 | 2.103 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 3 | 3 | -1.2115 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 2 | 2 | 3.3445 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 2 | 2 | 1.1375 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1 | 1 | -0.9691 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 12 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos080_pos150|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos150_pos300_plus|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_not_applicable_at_start` | 82 | 70 | -0.9629 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 3 | 0 | None | `hold_sample` |
| `holding_action` | `WAIT` | 76 | 64 | -1.0857 | `candidate_tighten_or_exclude` |
| `holding_action` | `BUY` | 3 | 3 | 1.9066 | `candidate_recovery_or_relax` |
| `holding_action` | `holding_action_not_applicable_at_start` | 3 | 3 | -1.2115 | `candidate_tighten_or_exclude` |
| `holding_action` | `SELL_TODAY` | 4 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 82 | 70 | -0.9629 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 4 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 59 | 57 | -1.4675 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 7 | 6 | 0.162 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300_plus` | 6 | 5 | 2.5996 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300` | 2 | 2 | 1.1375 | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 12 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- `holding_bucket_source_quality_1`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_2`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_3`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_4`: `held_bucket` / `held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_5`: `holding_action` / `WAIT` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_6`: `holding_action` / `BUY` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_7`: `holding_action` / `holding_action_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_8`: `holding_source_stage` / `scalp_sim_holding_started` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_9`: `profit_band` / `profit_lt_neg070` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_10`: `profit_band` / `profit_pos150_pos300_plus` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Exit Bucket Attribution

- decision_authority: `adm_ldm_exit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'exit_rows': 2110, 'source_row_count': 2110, 'bucket_count': 46, 'joined_sample': 660, 'source_quality_adjusted_ev_pct': -0.9602, 'source_quality_gate': 'pass', 'unknown_reason_counts': {'not_applicable': 3, 'join_gap': 8, 'missing_source_field': 1}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 47 | 47 | -1.0823 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 16 | 16 | -0.5381 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 16 | 16 | -1.6925 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 11 | 11 | -2.4288 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 9 | 9 | -0.8048 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 7 | 7 | -0.5521 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 6 | 6 | -1.4692 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 5 | 5 | -1.3825 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 2 | 2 | -0.7688 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 2 | 2 | 2.4508 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 2 | 2 | 0.6168 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos080_pos150` | 1 | 1 | 0.7575 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos150_pos300_plus` | 1 | 1 | 4.845 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=daily_limit_up_immediate_exit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 1 | 1 | 2.2912 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=daily_limit_up_immediate_exit|outcome=NEUTRAL|profit=profit_pos150_pos300_plus` | 1 | 1 | -0.1359 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_ai_momentum_decay|outcome=NEUTRAL|profit=profit_pos080_pos150` | 1 | 1 | 0.9455 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 1 | 1 | -2.6628 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 1 | 1 | 0.9755 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 1 | 1 | 1.2995 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 1 | 1 | 0.4455 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_euphoria_context_noop|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown` | 67 | 0 | None | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown` | 1911 | 0 | None | `source_quality_workorder` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 63 | 63 | -0.9441 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 32 | 32 | -1.5091 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 17 | 17 | -0.7589 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 16 | 16 | -0.6342 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 1982 | 4 | 1.0162 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 63 | 63 | -0.9441 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 32 | 32 | -1.1934 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 22 | 22 | -1.9293 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 8 | 8 | 0.7741 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 4 | 4 | 1.0162 | `candidate_recovery_or_relax` |
| `exit_rule` | `daily_limit_up_immediate_exit` | 2 | 2 | 1.0776 | `hold_sample` |
| `exit_rule` | `scalp_ai_momentum_decay` | 1 | 1 | 0.9455 | `hold_sample` |
| `exit_rule` | `exit_rule_unknown` | 1978 | 0 | None | `source_quality_workorder` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 65 | 65 | -1.0975 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 63 | 63 | -0.9441 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 4 | 4 | 1.0162 | `candidate_recovery_or_relax` |
| `exit_source_stage` | `scalp_sim_euphoria_context_noop` | 67 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 1911 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- `exit_bucket_source_quality_1`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_2`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_3`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_4`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_5`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_6`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_7`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_8`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_9`: `combo_exit_result` / `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_10`: `combo_exit_result` / `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos080_pos150` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `incremental_notional_ev_pct`
- summary: `{'scale_in_rows': 3886, 'bucket_count': 485, 'edge_bucket_count': 0, 'actionable_bucket_count': 0, 'runtime_authority_blocked_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'arm_counts': {'AVG_DOWN': 2363, 'PYRAMID': 1523}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_70p` | 2209 | 2209 | None | -0.0549 | 0.4138 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 724 | 724 | None | -0.4131 | 0.2597 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 377 | 377 | None | -0.3661 | 0.2255 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 246 | 246 | None | -0.3391 | 0.252 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 163 | 163 | None | -0.2578 | 0.2945 | `hold_sample` |
| `ai_score_band` | `score_unknown` | 167 | 4 | None | -1.58 | 0.0 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 3719 | 3719 | None | -0.1838 | 0.3487 | `hold_sample` |
| `ai_score_source` | `sim_scale_in_source_not_scored` | 4 | 4 | None | -1.58 | 0.0 | `hold_sample` |
| `ai_score_source` | `stage_rule_backfilled` | 163 | 0 | None | None | None | `hold_sample` |
| `arm` | `AVG_DOWN` | 2363 | 2350 | None | -0.8493 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 1523 | 1373 | None | 0.9567 | 0.9467 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 1900 | 1887 | None | -0.9581 | 0.0 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 1523 | 1373 | None | 0.9567 | 0.9467 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 463 | 463 | None | -0.4062 | 0.0 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 1024 | 1024 | None | 0.6259 | 0.9922 | `hold_sample` |
| `blocker_reason` | `scalping_pyramid_ok` | 171 | 171 | None | 2.5317 | 1.0 | `hold_sample` |
| `blocker_reason` | `add_judgment_locked` | 150 | 150 | None | -0.4847 | 0.04 | `hold_sample` |
| `blocker_reason` | `scalping_buy_window_blocked` | 143 | 143 | None | -0.1988 | 0.042 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.97)` | 133 | 133 | None | -0.97 | 0.0 | `hold_sample` |
| `blocker_reason` | `low_broken` | 107 | 107 | None | -0.4076 | 0.0 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `adm_ldm_overnight_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'overnight_rows': 8, 'bucket_count': 24, 'actionable_bucket_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'status_counts': {'HOLD_OVERNIGHT': 4, 'SELL_TODAY': 4}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 2 | 2 | -0.7688 | -1.025 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 1 | 1 | 0.7575 | 1.01 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos150_pos300_plus` | 1 | 1 | 4.845 | 6.46 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_lt_neg070` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_pos080_pos150` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_pos150_pos300_plus` | 1 | 0 | None | None | None | `hold_sample` |
| `confidence_band` | `confidence_070p` | 8 | 4 | 1.0162 | 1.355 | 0.5 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 6 | 3 | 1.5425 | 2.0567 | 0.6667 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 2 | 1 | -0.5625 | -0.75 | 0.0 | `hold_sample` |
| `overnight_action` | `SELL_TODAY` | 8 | 4 | 1.0162 | 1.355 | 0.5 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 4 | 4 | 1.0162 | 1.355 | 0.5 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 4 | 0 | None | None | None | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 4 | 2 | -0.7688 | -1.025 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 2 | 1 | 0.7575 | 1.01 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos150_pos300_plus` | 2 | 1 | 4.845 | 6.46 | 1.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 8 | 4 | 1.0162 | 1.355 | 0.5 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 4 | 2 | -0.7688 | -1.025 | 0.0 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 2 | 1 | 0.7575 | 1.01 | 1.0 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 2 | 1 | 4.845 | 6.46 | 1.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 8 | 4 | 1.0162 | 1.355 | 0.5 | `hold_sample` |

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
