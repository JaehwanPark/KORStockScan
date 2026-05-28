# Lifecycle Decision Matrix - 2026-05-27

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-05-27`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `41172`
- source_rows_total: `41172`
- retained_rows: `41172`
- dropped_rows_by_source: `{}`
- joined_rows: `39464`
- policy_pass_count: `5`
- promote_ready_count: `1`
- entry_bucket_actionable_count: `17`
- entry_bucket_runtime_candidate_count: `4`
- holding_bucket_count/workorders: `30` / `10`
- exit_bucket_count/workorders: `54` / `10`
- scale_in_bucket_actionable_count: `381`
- scale_in_bucket_runtime_candidate_count: `10`
- overnight_bucket_actionable_count: `0`
- overnight_bucket_runtime_candidate_count: `0`
- lifecycle_flow_bucket_count: `82`
- lifecycle_flow_complete_count: `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0`
- incomplete_flow_reason_counts: `{'missing_entry': 20976, 'missing_holding': 21539, 'missing_exit': 21248, 'missing_submit': 21505}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 1, 'route_counts': {'bounded_auxiliary_weight': 1, 'hold_sample': 4}, 'quality_counts': {'observational_only_pending_outcome': 1, 'hold_sample': 4}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 985 | 148 | 1.8842 | 1.0 | `pass` | `BUY_DEFENSIVE` | True |
| `submit` | 424 | 183 | -0.8487 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 390 | 183 | -1.1027 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 38083 | 38041 | -0.4229 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 1290 | 909 | -0.7019 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 21929, 'complete_flow_count': 0, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 41172, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0, 'stage_identity': {'entry': {'source_row_count': 985, 'identity_missing_count': 0, 'identity_quality_counts': {'candidate_id': 984, 'exact_sim_record_id': 1}, 'identity_join_rate': 1.0}, 'submit': {'source_row_count': 424, 'identity_missing_count': 0, 'identity_quality_counts': {'candidate_id': 35, 'exact_sim_record_id': 389}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 390, 'identity_missing_count': 0, 'identity_quality_counts': {'exact_sim_record_id': 390}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 38083, 'identity_missing_count': 0, 'identity_quality_counts': {'candidate_id': 21754, 'exact_sim_record_id': 16329}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 1290, 'identity_missing_count': 0, 'identity_quality_counts': {'exact_sim_record_id': 909, 'candidate_id': 381}, 'identity_join_rate': 1.0}}, 'incomplete_flow_reason_counts': {'missing_entry': 20976, 'missing_holding': 21539, 'missing_exit': 21248, 'missing_submit': 21505}, 'bucket_count': 82, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 16352 | 16339 | -0.6081 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 3818 | 3818 | 0.5364 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:5f8bb8e981` | 168 | 168 | -0.4147 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:9f284741cf` | 76 | 76 | 2.6587 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:0dbddcc72e` | 49 | 49 | 1.5253 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:63acce4470` | 41 | 41 | -0.1394 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:bf81e4fab9` | 33 | 33 | -0.5406 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:e81b5f597d` | 30 | 30 | -0.5137 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b3f591e69a` | 12 | 12 | -0.765 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b75dcb4fef` | 12 | 12 | -0.4425 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:bfc859574f` | 201 | 9 | -0.6757 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:f87fa0c80c` | 7 | 7 | -0.6829 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:34cc4a9d10` | 6 | 6 | -0.046 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:f8ff028ae0` | 5 | 5 | 3.3856 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:ab1924a1fc` | 35 | 5 | -0.6351 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:22134ec0b0` | 4 | 4 | -2.0392 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:70e9d883f8` | 4 | 4 | -0.4887 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:a1371ed802` | 4 | 4 | -0.9049 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:f865a9a3b6` | 4 | 4 | -0.56 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:7ed5a2f0f0` | 3 | 3 | -0.2272 | `hold_sample` | `hold_sample_or_incomplete_flow` |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 985, 'bucket_count': 153, 'actionable_bucket_count': 17, 'runtime_candidate_count': 4, 'workorder_count': 10}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `action_unknown` | 521 | 130 | 2.2594 | 3.6585 | 0.6231 | `candidate_recovery_or_relax` |
| `chosen_action` | `NO_BUY_AI` | 447 | 13 | -0.8994 | -0.9623 | 0.3846 | `candidate_tighten_or_exclude` |
| `chosen_action` | `BUY_NOW` | 13 | 5 | -0.6351 | -2.312 | 0.0 | `hold_sample` |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 1 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_SOURCE_QUALITY` | 3 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_unknown` | 76 | 76 | 2.6587 | 4.3494 | 0.6316 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_unknown` | 49 | 49 | 1.5253 | 2.4068 | 0.6122 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1000_1200` | 77 | 7 | -0.8453 | -0.65 | 0.4286 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_unknown` | 5 | 5 | 3.3856 | 5.4231 | 0.6 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1200_1400` | 25 | 2 | -0.0821 | -1.19 | 0.5 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1000_1200` | 7 | 2 | -3.0661 | -2.225 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1000_1200` | 11 | 2 | -2.628 | -2.215 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_ok|time=time_1000_1200` | 4 | 1 | 1.5007 | -2.51 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_ok|time=time_1200_1400` | 3 | 1 | 0.4976 | -2.18 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1200_1400` | 5 | 1 | 0.0821 | -2.44 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_ok|time=time_1200_1400` | 1 | 1 | 1.1856 | -2.31 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_0900_1000` | 12 | 1 | -0.6643 | 1.18 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=blocked_ai_score|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_chase_risk|time=time_1000_1200` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=blocked_ai_score|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_chase_risk|time=time_1200_1400` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=blocked_ai_score|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_normal|time=time_0900_1000` | 15 | 0 | None | None | None | `hold_sample` |
| `exit_rule` | `exit_unknown` | 967 | 130 | 2.2594 | 3.6585 | 0.6231 | `candidate_recovery_or_relax` |
| `liquidity_bucket` | `liquidity_unknown` | 985 | 148 | 1.8842 | 3.0509 | 0.5811 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_unknown` | 818 | 145 | 1.9012 | 3.1623 | 0.5931 | `candidate_recovery_or_relax` |
| `score_band` | `score_70p` | 235 | 81 | 2.4554 | 3.9382 | 0.5926 | `candidate_recovery_or_relax` |
| `score_band` | `score_66_69` | 82 | 49 | 1.5253 | 2.4068 | 0.6122 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 130 | 130 | 2.2594 | 3.6585 | 0.6231 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 347 | 18 | -0.826 | -1.3372 | 0.2778 | `candidate_tighten_or_exclude` |
| `stale_bucket` | `fresh_or_unflagged` | 521 | 130 | 2.2594 | 3.6585 | 0.6231 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh` | 366 | 18 | -0.826 | -1.3372 | 0.2778 | `candidate_tighten_or_exclude` |
| `strength_bucket` | `strength_unknown` | 521 | 130 | 2.2594 | 3.6585 | 0.6231 | `candidate_recovery_or_relax` |
| `strength_bucket` | `risk_unknown` | 348 | 18 | -0.826 | -1.3372 | 0.2778 | `candidate_tighten_or_exclude` |
| `time_bucket` | `time_unknown` | 521 | 130 | 2.2594 | 3.6585 | 0.6231 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_1000_1200` | 191 | 12 | -1.317 | -1.3283 | 0.25 | `candidate_tighten_or_exclude` |

### Entry Bucket Runtime Approval Candidates

- `entry_bucket_8`: `score_band` / `score_70p` -> `candidate_recovery_or_relax`
- `entry_bucket_9`: `score_band` / `score_66_69` -> `candidate_recovery_or_relax`
- `entry_bucket_10`: `source_stage` / `wait6579_ev_cohort` -> `candidate_recovery_or_relax`
- `entry_bucket_12`: `stale_bucket` / `fresh_or_unflagged` -> `candidate_recovery_or_relax`

### Entry Bucket Workorders

- `entry_bucket_source_quality_1`: `chosen_action` / `action_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_2`: `chosen_action` / `NO_BUY_AI` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_3`: `combo_entry_spot` / `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_4`: `combo_entry_spot` / `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_5`: `exit_rule` / `exit_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_6`: `liquidity_bucket` / `liquidity_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_7`: `overbought_bucket` / `overbought_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_8`: `score_band` / `score_70p` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_9`: `score_band` / `score_66_69` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_10`: `source_stage` / `wait6579_ev_cohort` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`

## Submit Bucket Attribution

- decision_authority: `adm_ldm_submit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'submit_rows': 424, 'bucket_count': 62, 'contract_gap_count': 0, 'workorder_count': 0, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 413 | 183 | -0.8487 | `keep_collecting` |
| `actual_order_submitted` | `true` | 11 | 0 | None | `keep_collecting` |
| `broker_order_forbidden` | `true` | 412 | 183 | -0.8487 | `keep_collecting` |
| `broker_order_forbidden` | `false` | 12 | 0 | None | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 225 | 102 | -0.8577 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 88 | 42 | -0.6648 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 26 | 13 | -1.1385 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 20 | 13 | -1.0221 | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=block_False|quote_age=quote_age_unknown|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_normal|latency=latency_unknown|fill=false|submitted=false` | 18 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 11 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=block_False|quote_age=quote_age_unknown|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_unknown|latency=latency_unknown|fill=false|submitted=true` | 10 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=pre_submit_liquidity_guard_block|revalidation=block_False|quote_age=quote_age_unknown|liquidity=below_min_liquidity|liquidity_guard=liquidity_guard_unknown|overbought=overbought_unknown|latency=latency_unknown|fill=false|submitted=false` | 5 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_unknown|latency=simulated|fill=false|submitted=false` | 5 | 2 | -0.4428 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 5 | 3 | -2.1829 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 5 | 4 | -0.5305 | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_pass|revalidation=block_False|quote_age=quote_age_unknown|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_normal|latency=latency_unknown|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=block_False|quote_age=quote_age_unknown|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_ok|latency=latency_unknown|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=false|submitted=false` | 1 | 1 | -1.6635 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | 1.5007 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | -3.3701 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | 1.2767 | `source_quality_workorder` |
| `latency_reason` | `scalp_live_simulator` | 389 | 183 | -0.8487 | `keep_collecting` |
| `latency_reason` | `latency_reason_unknown` | 35 | 0 | None | `source_quality_workorder` |
| `latency_state` | `simulated` | 389 | 183 | -0.8487 | `keep_collecting` |
| `latency_state` | `latency_unknown` | 35 | 0 | None | `source_quality_workorder` |
| `liquidity_bucket` | `below_min_liquidity` | 357 | 159 | -0.8321 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 37 | 24 | -0.9586 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_unknown` | 30 | 0 | None | `source_quality_workorder` |
| `liquidity_guard_action` | `would_block` | 352 | 159 | -0.8321 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 37 | 24 | -0.9586 | `keep_collecting` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 35 | 0 | None | `source_quality_workorder` |
| `overbought_bucket` | `overbought_unknown` | 395 | 175 | -0.8624 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_normal` | 19 | 0 | None | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 10 | 8 | -0.5473 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 389 | 183 | -0.8487 | `keep_collecting` |
| `overbought_guard_action` | `overbought_guard_unknown` | 35 | 0 | None | `source_quality_workorder` |
| `price_below_bid_bucket` | `not_below_bid` | 307 | 131 | -0.8927 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 70 | 43 | -0.7205 | `keep_collecting` |
| `price_below_bid_bucket` | `price_below_bid_unknown` | 35 | 0 | None | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 12 | 9 | -0.82 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 390, 'source_row_count': 390, 'bucket_count': 30, 'joined_sample': 915, 'source_quality_adjusted_ev_pct': -1.1027, 'source_quality_gate': 'pass', 'unknown_reason_counts': {'not_applicable': 17, 'join_gap': 9, 'missing_source_field': 2}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_unknown` | 87 | 87 | -1.6093 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_lt_neg070|held=held_unknown` | 39 | 39 | -1.5133 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_unknown` | 13 | 13 | -0.0104 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_unknown` | 11 | 11 | -0.0846 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_unknown` | 7 | 7 | -1.9558 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_unknown` | 7 | 7 | -0.0537 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_neg010_pos080|held=held_unknown` | 5 | 5 | -0.4945 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_pos080_pos150|held=held_unknown` | 5 | 5 | 0.6145 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_unknown` | 4 | 4 | 2.4172 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_unknown` | 2 | 2 | 0.9238 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_pos150_pos300|held=held_unknown` | 2 | 2 | -0.087 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_pos150_pos300_plus|held=held_unknown` | 1 | 1 | 0.4144 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_unknown|held=held_unknown` | 11 | 0 | None | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_unknown|held=held_unknown` | 163 | 0 | None | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_unknown|held=held_unknown` | 32 | 0 | None | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=holding_action_unknown|profit=profit_neg070_neg010|held=held_020_180s` | 1 | 0 | None | `source_quality_workorder` |
| `held_bucket` | `held_unknown` | 389 | 183 | -1.1027 | `source_quality_workorder` |
| `held_bucket` | `held_020_180s` | 1 | 0 | None | `hold_sample` |
| `holding_action` | `WAIT` | 285 | 122 | -1.0802 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_unknown` | 85 | 52 | -1.1188 | `source_quality_workorder` |
| `holding_action` | `BUY` | 20 | 9 | -1.3159 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 389 | 183 | -1.1027 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 1 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 133 | 133 | -1.5994 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 18 | 18 | 0.1631 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 16 | 16 | -0.2127 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 9 | 9 | -0.0611 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300_plus` | 7 | 7 | 1.7044 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 1 | 0 | None | `hold_sample` |
| `profit_band` | `profit_unknown` | 206 | 0 | None | `source_quality_workorder` |

### Holding Bucket Attribution Workorders

- `holding_bucket_source_quality_1`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_2`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_lt_neg070|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_3`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_4`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_5`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_6`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_7`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_neg010_pos080|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_8`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_pos080_pos150|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_9`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_10`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Exit Bucket Attribution

- decision_authority: `adm_ldm_exit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'exit_rows': 1290, 'source_row_count': 1290, 'bucket_count': 54, 'joined_sample': 4545, 'source_quality_adjusted_ev_pct': -0.7019, 'source_quality_gate': 'pass', 'unknown_reason_counts': {'not_applicable': 8, 'join_gap': 8, 'missing_source_field': 1}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_neg070_neg010` | 344 | 344 | -0.4828 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_lt_neg070` | 303 | 303 | -1.1974 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_neg010_pos080` | 60 | 60 | 0.2383 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 37 | 37 | -2.4919 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 22 | 22 | -1.0219 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 19 | 19 | -0.8657 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 19 | 19 | -1.0117 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 17 | 17 | -1.9229 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_pos150_pos300` | 16 | 16 | 2.0663 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_pos080_pos150` | 14 | 14 | 1.1271 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 9 | 9 | -1.3594 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 9 | 9 | -0.3416 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 6 | 6 | -0.3173 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 5 | 5 | -0.822 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 5 | 5 | 1.3017 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 5 | 5 | -0.0011 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_pos150_pos300_plus` | 4 | 4 | 3.9307 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 3 | 3 | 2.3963 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 2 | 2 | -1.2625 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 2 | 2 | 0.2763 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 2 | 2 | 0.584 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300` | 2 | 2 | 1.1319 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 1 | 1 | -0.1725 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_sell_order_assumed_filled|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 1 | 1 | -0.1725 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_ai_momentum_decay|outcome=NEUTRAL|profit=profit_neg010_pos080` | 1 | 1 | 0.2395 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_preset_tp_touch|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 1 | 1 | 1.3174 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_euphoria_context_noop|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown` | 380 | 0 | None | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown` | 1 | 0 | None | `source_quality_workorder` |
| `exit_outcome` | `outcome_unknown` | 1124 | 743 | -0.6062 | `source_quality_workorder` |
| `exit_outcome` | `GOOD_EXIT` | 78 | 78 | -1.743 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 52 | 52 | -0.4374 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 36 | 36 | -0.8044 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 741 | 741 | -0.6074 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 68 | 68 | -1.8664 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 55 | 55 | -1.2429 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 39 | 39 | 0.2202 | `hold_no_edge` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 2 | 2 | -1.2625 | `hold_sample` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 2 | 2 | -0.1725 | `hold_sample` |
| `exit_rule` | `scalp_ai_momentum_decay` | 1 | 1 | 0.2395 | `hold_sample` |
| `exit_rule` | `scalp_sim_preset_tp_touch` | 1 | 1 | 1.3174 | `hold_sample` |

### Exit Bucket Attribution Workorders

- `exit_bucket_source_quality_1`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_neg070_neg010` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_2`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_3`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_neg010_pos080` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_4`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_5`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_6`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_7`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_8`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_9`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_pos150_pos300` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_10`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_pos080_pos150` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'scale_in_rows': 38083, 'bucket_count': 3084, 'actionable_bucket_count': 381, 'runtime_candidate_count': 10, 'workorder_count': 10, 'arm_counts': {'AVG_DOWN': 17847, 'PYRAMID': 3907, 'arm_unknown': 16329}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_70p` | 28678 | 28678 | -0.4042 | -0.4409 | 0.2069 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_60_62` | 3639 | 3639 | -0.2537 | -0.2729 | 0.1849 | `hold_no_edge` |
| `ai_score_band` | `score_66_69` | 3544 | 3544 | -0.2495 | -0.2743 | 0.2128 | `hold_no_edge` |
| `ai_score_band` | `score_lt60` | 1217 | 1217 | -1.8393 | -2.2437 | 0.189 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_63_65` | 963 | 963 | -0.4679 | -0.503 | 0.1568 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_unknown` | 42 | 0 | None | None | None | `hold_sample` |
| `ai_score_source` | `ai_source_unknown` | 38083 | 38041 | -0.4229 | -0.4686 | 0.2035 | `candidate_tighten_or_exclude` |
| `arm` | `AVG_DOWN` | 17847 | 17834 | -0.6507 | -0.7269 | 0.0 | `candidate_tighten_or_exclude` |
| `arm` | `arm_unknown` | 16329 | 16329 | -0.3504 | -0.3463 | 0.2396 | `candidate_tighten_or_exclude` |
| `arm` | `PYRAMID` | 3907 | 3878 | 0.3193 | 0.2047 | 0.9874 | `candidate_recovery_or_relax` |
| `blocker_namespace` | `blocker_namespace_unknown` | 16329 | 16329 | -0.3504 | -0.3463 | 0.2396 | `candidate_tighten_or_exclude` |
| `blocker_namespace` | `AVG_DOWN` | 11415 | 11402 | -0.8103 | -0.8939 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 6432 | 6432 | -0.3678 | -0.431 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_namespace` | `PYRAMID` | 3907 | 3878 | 0.3193 | 0.2047 | 0.9874 | `candidate_recovery_or_relax` |
| `blocker_reason` | `blocker_reason_unknown` | 16329 | 16329 | -0.3504 | -0.3463 | 0.2396 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `add_judgment_locked` | 3659 | 3659 | -0.3291 | -0.3436 | 0.1588 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `profit_not_enough` | 3118 | 3118 | 0.5044 | 0.4432 | 0.9945 | `candidate_recovery_or_relax` |
| `blocker_reason` | `low_broken` | 918 | 918 | -0.3522 | -0.3745 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `scalping_cutoff` | 273 | 273 | -0.3883 | -0.4036 | 0.0806 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.08)` | 204 | 204 | -0.0501 | -0.08 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.81)` | 182 | 182 | -0.7626 | -0.81 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.76)` | 173 | 173 | -0.6691 | -0.76 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.09)` | 151 | 151 | -0.0476 | -0.09 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.74)` | 148 | 148 | -0.6752 | -0.74 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.96)` | 138 | 138 | -0.8896 | -0.96 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.77)` | 132 | 132 | -0.6973 | -0.77 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.10)` | 130 | 130 | -1.0539 | -1.1 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.16)` | 129 | 129 | -1.0769 | -1.16 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.99)` | 126 | 126 | -0.8935 | -0.99 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.79)` | 123 | 123 | -0.7145 | -0.79 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.08)` | 119 | 119 | -0.9805 | -1.08 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `trend_not_strong` | 118 | 118 | 2.6781 | 2.6679 | 1.0 | `candidate_recovery_or_relax` |
| `blocker_reason` | `pnl_out_of_range(-0.83)` | 116 | 116 | -0.7397 | -0.83 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.09)` | 116 | 116 | -0.9625 | -1.09 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.85)` | 111 | 111 | -0.7623 | -0.85 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.92)` | 106 | 106 | -0.834 | -0.92 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.03)` | 103 | 103 | -0.9726 | -1.03 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.23)` | 103 | 103 | -1.13 | -1.23 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.90)` | 99 | 99 | -0.8508 | -0.9 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.05)` | 95 | 95 | -0.0264 | -0.05 | 0.0 | `hold_no_edge` |

### Scale-In Bucket Runtime Approval Candidates

- `scale_in_bucket_1`: `ai_score_band` / `score_70p` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_2`: `ai_score_band` / `score_lt60` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_3`: `ai_score_band` / `score_63_65` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_5`: `arm` / `AVG_DOWN` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_7`: `arm` / `PYRAMID` -> `candidate_recovery_or_relax`
- `scale_in_bucket_9`: `blocker_namespace` / `AVG_DOWN` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_10`: `blocker_namespace` / `AVG_DOWN_ONLY` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_11`: `blocker_namespace` / `PYRAMID` -> `candidate_recovery_or_relax`
- `scale_in_bucket_13`: `blocker_reason` / `add_judgment_locked` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_14`: `blocker_reason` / `profit_not_enough` -> `candidate_recovery_or_relax`

### Scale-In Bucket Workorders

- `scale_in_bucket_source_quality_1`: `ai_score_band` / `score_70p` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_2`: `ai_score_band` / `score_lt60` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_3`: `ai_score_band` / `score_63_65` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_4`: `ai_score_source` / `ai_source_unknown` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_5`: `arm` / `AVG_DOWN` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_6`: `arm` / `arm_unknown` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_7`: `arm` / `PYRAMID` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_8`: `blocker_namespace` / `blocker_namespace_unknown` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_9`: `blocker_namespace` / `AVG_DOWN` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_10`: `blocker_namespace` / `AVG_DOWN_ONLY` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`

## Overnight Bucket Attribution

- decision_authority: `adm_ldm_overnight_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'overnight_rows': 3, 'bucket_count': 21, 'actionable_bucket_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'status_counts': {'HOLD_OVERNIGHT': 1, 'SELL_TODAY': 2}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 1 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=action_unknown|status=SELL_TODAY|confidence=confidence_unknown|profit=profit_neg070_neg010` | 1 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 1 | 0 | None | None | None | `hold_sample` |
| `confidence_band` | `confidence_070p` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `confidence_band` | `confidence_unknown` | 1 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_unknown` | 1 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `overnight_action` | `SELL_TODAY` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `overnight_action` | `action_unknown` | 1 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 2 | 2 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 1 | 0 | None | None | None | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 1 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 3 | 2 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 3 | 2 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 3 | 2 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 1 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_sell_order_assumed_filled` | 1 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_decision` | 1 | 0 | None | None | None | `hold_sample` |
| `stage` | `exit` | 2 | 2 | -0.1725 | -0.23 | 0.0 | `hold_sample` |

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
