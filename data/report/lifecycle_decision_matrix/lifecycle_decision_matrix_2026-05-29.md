# Lifecycle Decision Matrix - 2026-05-29

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-05-29`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `22977`
- source_rows_total: `22977`
- retained_rows: `22977`
- dropped_rows_by_source: `{}`
- joined_rows: `22200`
- policy_pass_count: `5`
- promote_ready_count: `1`
- entry_bucket_actionable_count: `21`
- entry_bucket_runtime_candidate_count: `10`
- holding_bucket_count/workorders: `34` / `10`
- exit_bucket_count/workorders: `70` / `10`
- scale_in_bucket_actionable_count: `176`
- scale_in_bucket_runtime_candidate_count: `10`
- overnight_bucket_actionable_count: `16`
- overnight_bucket_runtime_candidate_count: `9`
- lifecycle_flow_bucket_count: `102`
- lifecycle_flow_complete_count: `81`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.007`
- incomplete_flow_reason_counts: `{'missing_entry': 11141, 'missing_holding': 11417, 'missing_exit': 11070, 'missing_submit': 11420, 'postclose_exit_without_entry': 367, 'candidate_id_only': 11203, 'sim_record_id_only': 190}`
- bucket_directed_sim_probe: `{'observed_row_count': 11540, 'matched_row_count': 0, 'background_row_count': 11540, 'matched_unique_source_bucket_count': 0, 'match_status_counts': {'candidate_context_only': 660, 'not_instrumented': 10880}, 'matched_classification_state_counts': {}, 'primary_source': 'matched_bucket_directed_sim_probe_only', 'background_source': 'unmatched_or_policy_missing_sim_observation', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 1, 'route_counts': {'bounded_auxiliary_weight': 1, 'hold_sample': 4}, 'quality_counts': {'observational_only_pending_outcome': 1, 'hold_sample': 4}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 628 | 102 | 1.4025 | 1.0 | `pass` | `BUY_DEFENSIVE` | True |
| `submit` | 217 | 192 | -0.5838 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 207 | 192 | -0.4373 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 21057 | 21047 | 0.0949 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 868 | 667 | -0.4226 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 11518, 'complete_flow_count': 81, 'incomplete_flow_count': 11437, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 22977, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.007, 'join_contract_blocked': False, 'bundle_ev_tuning_state': 'ready_for_bundle_ev_tuning', 'top_incomplete_reason': 'missing_submit', 'stage_identity': {'entry': {'source_row_count': 628, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 360, 'candidate_id': 268}, 'identity_join_rate': 1.0}, 'submit': {'source_row_count': 217, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 217}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 207, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 192, 'exact_sim_record_id': 15}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 21057, 'identity_missing_count': 0, 'identity_quality_counts': {'candidate_id': 10794, 'exact_sim_record_id': 10263}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 868, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 177, 'exact_sim_record_id': 490, 'candidate_id': 201}, 'identity_join_rate': 1.0}}, 'required_stage_source_counts': {'entry': 628, 'submit': 217, 'holding': 207, 'exit': 868}, 'incomplete_flow_reason_counts': {'missing_entry': 11141, 'missing_holding': 11417, 'missing_exit': 11070, 'missing_submit': 11420, 'postclose_exit_without_entry': 367, 'candidate_id_only': 11203, 'sim_record_id_only': 190}, 'bucket_count': 102, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:b85b2fccd5` | 4 | 4 | 2.7842 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:88611b572d` | 3 | 3 | -3.5096 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:4ce5e1021f` | 3 | 3 | -1.3861 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:e9528bc1e5` | 3 | 3 | -1.2149 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:ae57efd74f` | 2 | 2 | -1.717 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:b3c74de049` | 2 | 2 | -0.7787 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:42075e2cfd` | 2 | 2 | -0.7548 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:d2c943bee6` | 2 | 2 | 1.2894 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:ae09808f9f` | 2 | 2 | -1.0358 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:15951f1a81` | 2 | 2 | -0.1823 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:0a0afd5bcf` | 1 | 1 | 0.0681 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:a48e9bb93a` | 1 | 1 | -0.9598 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:1b13378bbb` | 1 | 1 | -0.5405 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:a552b1a5cd` | 1 | 1 | -0.4299 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:10c09c0c5c` | 1 | 1 | -1.3718 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:0400855ce2` | 1 | 1 | 2.4291 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:bf5db47340` | 1 | 1 | -0.9728 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:7a9deca452` | 1 | 1 | -0.6955 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:f14c0fc7a7` | 1 | 1 | -1.2909 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:82ba8c3b0d` | 1 | 1 | -0.5915 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 628, 'bucket_count': 176, 'actionable_bucket_count': 21, 'runtime_candidate_count': 10, 'workorder_count': 10}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `WAIT_REQUOTE` | 81 | 81 | 1.9704 | 3.0981 | 0.5679 | `candidate_recovery_or_relax` |
| `chosen_action` | `NO_BUY_AI` | 350 | 14 | -0.7413 | -0.3079 | 0.5 | `candidate_tighten_or_exclude` |
| `chosen_action` | `BUY_NOW` | 8 | 7 | -0.8813 | 0.0457 | 0.7143 | `hold_sample` |
| `chosen_action` | `ALLOW_BOTTOMING_ENTRY` | 37 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `ALLOW_LEVEL1_RISK_OFF_ENTRY` | 150 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_SOURCE_QUALITY` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_normal|time=time_1200_1400` | 11 | 11 | -0.0268 | -0.1244 | 0.2727 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_watch|time=time_1000_1200` | 10 | 10 | 2.794 | 4.1544 | 0.9 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_normal|time=time_1000_1200` | 6 | 6 | 0.5633 | 0.5001 | 0.5 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1000_1200` | 13 | 6 | -0.7064 | -0.1333 | 0.6667 | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_normal|time=time_0900_1000` | 5 | 5 | 1.7974 | 2.3637 | 0.6 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_chase_risk|time=time_0900_1000` | 5 | 5 | -0.5352 | -1.2438 | 0.2 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_normal|time=time_1000_1200` | 5 | 5 | 1.5618 | 2.3313 | 0.8 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_watch|time=time_0900_1000` | 5 | 5 | 1.2433 | 1.395 | 0.6 | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_normal|time=time_1400_close` | 4 | 4 | 6.1969 | 10.5465 | 0.75 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_normal|time=time_1200_1400` | 4 | 4 | 0.8824 | 0.9534 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_0900_1000` | 15 | 3 | -1.0527 | -0.2467 | 0.6667 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1000_1200` | 53 | 3 | -1.4651 | -1.19 | 0.3333 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_normal|time=time_0900_1000` | 3 | 3 | 1.0877 | 2.1632 | 0.3333 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_normal|time=time_0900_1000` | 2 | 2 | -0.015 | -0.6215 | 0.5 | `hold_sample` |
| `exit_rule` | `exit_unknown` | 607 | 81 | 1.9704 | 3.0981 | 0.5679 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_trailing_take_profit` | 12 | 12 | -0.7219 | 1.3875 | 1.0 | `candidate_tighten_or_exclude` |
| `liquidity_bucket` | `liquidity_high` | 81 | 81 | 1.9704 | 3.0981 | 0.5679 | `candidate_recovery_or_relax` |
| `liquidity_bucket` | `liquidity_unknown` | 360 | 21 | -0.788 | -0.19 | 0.5714 | `candidate_tighten_or_exclude` |
| `overbought_bucket` | `overbought_proxy_normal` | 47 | 47 | 1.4616 | 2.2013 | 0.5532 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_proxy_watch` | 21 | 21 | 2.2663 | 3.4519 | 0.7143 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_unknown` | 235 | 19 | -0.8954 | -0.3547 | 0.5263 | `candidate_tighten_or_exclude` |
| `overbought_bucket` | `overbought_proxy_chase_risk` | 10 | 10 | 1.4611 | 2.456 | 0.3 | `candidate_recovery_or_relax` |
| `score_band` | `score_70p` | 131 | 48 | 1.9148 | 3.1819 | 0.6667 | `candidate_recovery_or_relax` |
| `score_band` | `score_66_69` | 49 | 34 | 1.5423 | 2.4359 | 0.4412 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 81 | 81 | 1.9704 | 3.0981 | 0.5679 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 260 | 21 | -0.788 | -0.19 | 0.5714 | `candidate_tighten_or_exclude` |
| `stale_bucket` | `fresh_or_unflagged` | 268 | 81 | 1.9704 | 3.0981 | 0.5679 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh` | 270 | 20 | -0.8091 | -0.071 | 0.6 | `candidate_tighten_or_exclude` |
| `strength_bucket` | `strong_strength_momentum` | 97 | 71 | 2.0934 | 3.3267 | 0.5493 | `candidate_recovery_or_relax` |
| `strength_bucket` | `risk_unknown` | 260 | 21 | -0.788 | -0.19 | 0.5714 | `candidate_tighten_or_exclude` |
| `time_bucket` | `time_1000_1200` | 225 | 38 | 1.711 | 2.8584 | 0.6842 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_0900_1000` | 197 | 33 | 0.0537 | 0.1545 | 0.4242 | `hold_no_edge` |
| `time_bucket` | `time_1200_1400` | 170 | 22 | 0.8914 | 1.6601 | 0.5 | `candidate_recovery_or_relax` |

### Entry Bucket Runtime Approval Candidates

- `entry_bucket_6`: `liquidity_bucket` / `liquidity_high` -> `candidate_recovery_or_relax`
- `entry_bucket_8`: `overbought_bucket` / `overbought_proxy_normal` -> `candidate_recovery_or_relax`
- `entry_bucket_9`: `overbought_bucket` / `overbought_proxy_watch` -> `candidate_recovery_or_relax`
- `entry_bucket_12`: `score_band` / `score_70p` -> `candidate_recovery_or_relax`
- `entry_bucket_13`: `score_band` / `score_66_69` -> `candidate_recovery_or_relax`
- `entry_bucket_14`: `source_stage` / `wait6579_ev_cohort` -> `candidate_recovery_or_relax`
- `entry_bucket_15`: `source_stage` / `scalp_entry_action_decision_snapshot` -> `candidate_tighten_or_exclude`
- `entry_bucket_16`: `stale_bucket` / `fresh_or_unflagged` -> `candidate_recovery_or_relax`
- `entry_bucket_17`: `stale_bucket` / `fresh` -> `candidate_tighten_or_exclude`
- `entry_bucket_18`: `strength_bucket` / `strong_strength_momentum` -> `candidate_recovery_or_relax`

### Entry Bucket Workorders

- `entry_bucket_source_quality_1`: `chosen_action` / `WAIT_REQUOTE` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_2`: `chosen_action` / `NO_BUY_AI` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_3`: `combo_entry_spot` / `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_watch|time=time_1000_1200` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_4`: `exit_rule` / `exit_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_5`: `exit_rule` / `scalp_trailing_take_profit` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_6`: `liquidity_bucket` / `liquidity_high` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_7`: `liquidity_bucket` / `liquidity_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_8`: `overbought_bucket` / `overbought_proxy_normal` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_9`: `overbought_bucket` / `overbought_proxy_watch` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_10`: `overbought_bucket` / `overbought_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`

## Submit Bucket Attribution

- decision_authority: `adm_ldm_submit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'submit_rows': 217, 'bucket_count': 62, 'contract_gap_count': 0, 'workorder_count': 0, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 211 | 192 | -0.5838 | `keep_collecting` |
| `actual_order_submitted` | `true` | 6 | 0 | None | `keep_collecting` |
| `broker_order_forbidden` | `true` | 210 | 192 | -0.5838 | `keep_collecting` |
| `broker_order_forbidden` | `false` | 7 | 0 | None | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 107 | 107 | -0.299 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 31 | 31 | -0.6619 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 17 | 17 | -0.9841 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 16 | 16 | -0.444 | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=block_False|quote_age=quote_age_unknown|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_normal|latency=latency_unknown|fill=false|submitted=false` | 11 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 5 | 5 | -2.2565 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 5 | 5 | -1.2916 | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=block_False|quote_age=quote_age_unknown|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_unknown|latency=latency_unknown|fill=false|submitted=true` | 4 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=pre_submit_liquidity_guard_block|revalidation=block_False|quote_age=quote_age_unknown|liquidity=below_min_liquidity|liquidity_guard=liquidity_guard_unknown|overbought=overbought_unknown|latency=latency_unknown|fill=false|submitted=false` | 4 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 4 | 4 | -3.7351 | `source_quality_workorder` |
| `combo_submit_quality` | `source=pre_submit_liquidity_guard_block|revalidation=block_False|quote_age=quote_age_unknown|liquidity=below_min_liquidity|liquidity_guard=liquidity_guard_unknown|overbought=overbought_ok|latency=latency_unknown|fill=false|submitted=false` | 3 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_unknown|latency=simulated|fill=false|submitted=false` | 3 | 3 | 0.2328 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 3 | 3 | -0.0885 | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=block_False|quote_age=quote_age_unknown|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_ok|latency=latency_unknown|fill=false|submitted=true` | 2 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_pass|revalidation=block_False|quote_age=quote_age_unknown|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_normal|latency=latency_unknown|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | -3.4886 | `source_quality_workorder` |
| `latency_reason` | `scalp_live_simulator` | 192 | 192 | -0.5838 | `keep_collecting` |
| `latency_reason` | `latency_reason_unknown` | 25 | 0 | None | `source_quality_workorder` |
| `latency_state` | `simulated` | 192 | 192 | -0.5838 | `keep_collecting` |
| `latency_state` | `latency_unknown` | 25 | 0 | None | `source_quality_workorder` |
| `liquidity_bucket` | `below_min_liquidity` | 172 | 165 | -0.5705 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 27 | 27 | -0.6649 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_unknown` | 18 | 0 | None | `source_quality_workorder` |
| `liquidity_guard_action` | `would_block` | 165 | 165 | -0.5705 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 27 | 27 | -0.6649 | `keep_collecting` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 25 | 0 | None | `source_quality_workorder` |
| `overbought_bucket` | `overbought_unknown` | 188 | 180 | -0.5023 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_ok` | 17 | 12 | -1.8053 | `keep_collecting` |
| `overbought_bucket` | `overbought_normal` | 12 | 0 | None | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 192 | 192 | -0.5838 | `keep_collecting` |
| `overbought_guard_action` | `overbought_guard_unknown` | 25 | 0 | None | `source_quality_workorder` |
| `price_below_bid_bucket` | `not_below_bid` | 136 | 136 | -0.4295 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 53 | 53 | -0.9486 | `keep_collecting` |
| `price_below_bid_bucket` | `price_below_bid_unknown` | 25 | 0 | None | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 3 | 3 | -1.13 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 127 | 127 | -0.4188 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 207, 'source_row_count': 207, 'bucket_count': 34, 'joined_sample': 960, 'source_quality_adjusted_ev_pct': -0.4373, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 65 | 65 | -1.4198 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 28 | 28 | -1.9447 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 21 | 21 | 1.0602 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 18 | 18 | -0.046 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 13 | 13 | 0.4278 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 12 | 12 | 1.6666 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 10 | 10 | -0.0514 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 9 | 9 | 2.0223 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 4 | 4 | -1.1886 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 4 | 4 | -0.3684 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 4 | 4 | 1.0149 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 2 | 2 | -0.265 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | 1.0295 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 1 | 1 | -0.23 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos080_pos150|held=held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos150_pos300_plus|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos150_pos300|held=held_600_1800s_plus` | 3 | 0 | None | `hold_sample` |
| `held_bucket` | `held_not_applicable_at_start` | 192 | 192 | -0.4373 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s_plus` | 15 | 0 | None | `hold_sample` |
| `holding_action` | `WAIT` | 131 | 131 | -0.3498 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 56 | 56 | -0.6144 | `candidate_tighten_or_exclude` |
| `holding_action` | `BUY` | 5 | 5 | -0.745 | `candidate_tighten_or_exclude` |
| `holding_action` | `SELL_TODAY` | 15 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 192 | 192 | -0.4373 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 15 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 101 | 97 | -1.5618 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 28 | 25 | 1.0529 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos080_pos150` | 26 | 24 | 0.2532 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 24 | 22 | -0.1046 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300_plus` | 22 | 21 | 1.8191 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 6 | 3 | -0.2533 | `hold_no_edge` |

### Holding Bucket Attribution Workorders

- `holding_bucket_source_quality_1`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_2`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_3`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_4`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_5`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_6`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_7`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_8`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_9`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_10`: `held_bucket` / `held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Exit Bucket Attribution

- decision_authority: `adm_ldm_exit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'exit_rows': 868, 'source_row_count': 868, 'bucket_count': 70, 'joined_sample': 3335, 'source_quality_adjusted_ev_pct': -0.4226, 'source_quality_gate': 'pass', 'unknown_reason_counts': {'not_applicable': 12, 'join_gap': 8, 'missing_source_field': 1}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 189 | 189 | -0.4453 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 180 | 180 | -1.1999 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 55 | 55 | 0.3115 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 26 | 26 | -2.4693 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 18 | 18 | -1.6628 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos150_pos300` | 16 | 16 | 2.3638 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 15 | 15 | -1.0446 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` | 14 | 14 | 1.1979 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 13 | 13 | -0.9616 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 12 | 12 | -1.0642 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 9 | 9 | 1.3506 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 9 | 9 | 2.4637 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 8 | 8 | -1.6455 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 8 | 8 | 0.3987 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 8 | 8 | 0.3608 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 8 | 8 | 0.915 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 7 | 7 | -0.5566 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 7 | 7 | -0.5726 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 7 | 7 | 0.9341 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 7 | 7 | 0.1036 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos150_pos300_plus` | 6 | 6 | 4.0838 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 5 | 5 | -0.3204 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 4 | 4 | -0.7612 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_sell_order_assumed_filled|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 4 | 4 | -0.7612 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 3 | 3 | -0.19 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos150_pos300` | 3 | 3 | 1.7825 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_sell_order_assumed_filled|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 3 | 3 | -0.19 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_sell_order_assumed_filled|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos150_pos300` | 3 | 3 | 1.7825 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300` | 3 | 3 | 0.7587 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 2 | 2 | 0.1163 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos080_pos150` | 2 | 2 | 0.765 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_sell_order_assumed_filled|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 2 | 2 | 0.1163 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_sell_order_assumed_filled|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos080_pos150` | 2 | 2 | 0.765 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300_plus` | 2 | 2 | 2.3592 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos150_pos300_plus` | 1 | 1 | 4.7325 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_sell_order_assumed_filled|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos150_pos300_plus` | 1 | 1 | 4.7325 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_ai_momentum_decay|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 1 | 1 | 0.0681 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_ai_momentum_decay|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 1 | 1 | -0.9728 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | 0.7997 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_preset_tp_touch|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 1 | 1 | 1.5033 | `hold_sample` |

### Exit Bucket Attribution Workorders

- `exit_bucket_source_quality_1`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_2`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_3`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_4`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_5`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_6`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos150_pos300` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_7`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_8`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_9`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_10`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'scale_in_rows': 21057, 'bucket_count': 1436, 'actionable_bucket_count': 176, 'runtime_candidate_count': 10, 'workorder_count': 10, 'arm_counts': {'AVG_DOWN': 12243, 'PYRAMID': 8814}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_70p` | 14453 | 14453 | 0.2036 | 0.1919 | 0.461 | `hold_no_edge` |
| `ai_score_band` | `score_66_69` | 2559 | 2559 | -0.1012 | -0.1167 | 0.3603 | `hold_no_edge` |
| `ai_score_band` | `score_60_62` | 2494 | 2494 | -0.1813 | -0.1986 | 0.233 | `hold_no_edge` |
| `ai_score_band` | `score_63_65` | 838 | 838 | -0.0557 | -0.0781 | 0.3795 | `hold_no_edge` |
| `ai_score_band` | `score_lt60` | 703 | 703 | -0.2667 | -0.2889 | 0.3101 | `hold_no_edge` |
| `ai_score_band` | `score_unknown` | 10 | 0 | None | None | None | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 21047 | 21047 | 0.0949 | 0.0813 | 0.4135 | `hold_no_edge` |
| `ai_score_source` | `stage_rule_backfilled` | 10 | 0 | None | None | None | `hold_sample` |
| `arm` | `AVG_DOWN` | 12243 | 12240 | -0.6934 | -0.7294 | 0.0 | `candidate_tighten_or_exclude` |
| `arm` | `PYRAMID` | 8814 | 8807 | 1.1904 | 1.208 | 0.9881 | `candidate_recovery_or_relax` |
| `blocker_namespace` | `AVG_DOWN` | 10014 | 10011 | -0.774 | -0.8057 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_namespace` | `PYRAMID` | 8814 | 8807 | 1.1904 | 1.208 | 0.9881 | `candidate_recovery_or_relax` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 2229 | 2229 | -0.3314 | -0.3866 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 10263 | 10263 | 0.3343 | 0.3664 | 0.4756 | `candidate_recovery_or_relax` |
| `blocker_reason` | `profit_not_enough` | 3165 | 3165 | 0.6796 | 0.6324 | 0.9912 | `candidate_recovery_or_relax` |
| `blocker_reason` | `add_judgment_locked` | 1548 | 1548 | -0.1455 | -0.1675 | 0.2965 | `hold_no_edge` |
| `blocker_reason` | `low_broken` | 535 | 535 | -0.3412 | -0.3659 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `trend_not_strong` | 216 | 216 | 2.607 | 2.5822 | 1.0 | `candidate_recovery_or_relax` |
| `blocker_reason` | `pnl_out_of_range(-0.05)` | 138 | 138 | -0.028 | -0.05 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.79)` | 122 | 122 | -0.7489 | -0.79 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.27)` | 107 | 107 | -1.2379 | -1.27 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.15)` | 89 | 89 | -1.1417 | -1.15 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.85)` | 67 | 67 | -0.7759 | -0.85 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.01)` | 62 | 62 | 0.015 | -0.01 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `ok` | 59 | 59 | -1.9748 | -2.4195 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.09)` | 57 | 57 | -0.0625 | -0.09 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.77)` | 51 | 51 | -0.7009 | -0.77 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.06)` | 50 | 50 | -0.9838 | -1.06 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.16)` | 49 | 49 | -1.0717 | -1.16 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.78)` | 46 | 46 | -0.7048 | -0.78 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.06)` | 45 | 45 | -0.0344 | -0.06 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.02)` | 40 | 40 | 0.0006 | -0.02 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-1.18)` | 39 | 39 | -1.0876 | -1.18 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.07)` | 38 | 38 | -0.0475 | -0.07 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.73)` | 36 | 36 | -0.7015 | -0.73 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.95)` | 36 | 36 | -0.8327 | -0.95 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.03)` | 35 | 35 | -0.9198 | -1.03 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.81)` | 34 | 34 | -0.7129 | -0.81 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.88)` | 33 | 33 | -0.8213 | -0.88 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.49)` | 33 | 33 | -1.3432 | -1.49 | 0.0 | `candidate_tighten_or_exclude` |

### Scale-In Bucket Runtime Approval Candidates

- `scale_in_bucket_1`: `arm` / `AVG_DOWN` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_2`: `arm` / `PYRAMID` -> `candidate_recovery_or_relax`
- `scale_in_bucket_3`: `blocker_namespace` / `AVG_DOWN` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_4`: `blocker_namespace` / `PYRAMID` -> `candidate_recovery_or_relax`
- `scale_in_bucket_5`: `blocker_namespace` / `AVG_DOWN_ONLY` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_6`: `blocker_reason` / `scalp_sim_panic_scale_in_blocked` -> `candidate_recovery_or_relax`
- `scale_in_bucket_7`: `blocker_reason` / `profit_not_enough` -> `candidate_recovery_or_relax`
- `scale_in_bucket_8`: `blocker_reason` / `low_broken` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_9`: `blocker_reason` / `trend_not_strong` -> `candidate_recovery_or_relax`
- `scale_in_bucket_10`: `blocker_reason` / `pnl_out_of_range(-0.79)` -> `candidate_tighten_or_exclude`

### Scale-In Bucket Workorders

- `scale_in_bucket_source_quality_1`: `arm` / `AVG_DOWN` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_2`: `arm` / `PYRAMID` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_3`: `blocker_namespace` / `AVG_DOWN` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_4`: `blocker_namespace` / `PYRAMID` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_5`: `blocker_namespace` / `AVG_DOWN_ONLY` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_6`: `blocker_reason` / `scalp_sim_panic_scale_in_blocked` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_7`: `blocker_reason` / `profit_not_enough` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_8`: `blocker_reason` / `low_broken` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_9`: `blocker_reason` / `trend_not_strong` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_10`: `blocker_reason` / `pnl_out_of_range(-0.79)` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`

## Overnight Bucket Attribution

- decision_authority: `adm_ldm_overnight_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'overnight_rows': 45, 'bucket_count': 45, 'actionable_bucket_count': 16, 'runtime_candidate_count': 9, 'workorder_count': 10, 'status_counts': {'HOLD_OVERNIGHT': 15, 'SELL_TODAY': 30}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 4 | 4 | -0.7612 | -1.015 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=action_unknown|status=SELL_TODAY|confidence=confidence_unknown|profit=profit_lt_neg070` | 4 | 4 | -0.7612 | -1.015 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 3 | 3 | -0.19 | -0.2533 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos150_pos300` | 3 | 3 | 1.7825 | 2.3767 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=action_unknown|status=SELL_TODAY|confidence=confidence_unknown|profit=profit_neg070_neg010` | 3 | 3 | -0.19 | -0.2533 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=action_unknown|status=SELL_TODAY|confidence=confidence_unknown|profit=profit_pos150_pos300` | 3 | 3 | 1.7825 | 2.3767 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 2 | 2 | 0.1163 | 0.155 | 0.5 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 2 | 2 | 0.765 | 1.02 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=action_unknown|status=SELL_TODAY|confidence=confidence_unknown|profit=profit_neg010_pos080` | 2 | 2 | 0.1163 | 0.155 | 0.5 | `hold_sample` |
| `combo_overnight_decision` | `action=action_unknown|status=SELL_TODAY|confidence=confidence_unknown|profit=profit_pos080_pos150` | 2 | 2 | 0.765 | 1.02 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos150_pos300_plus` | 1 | 1 | 4.7325 | 6.31 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=action_unknown|status=SELL_TODAY|confidence=confidence_unknown|profit=profit_pos150_pos300_plus` | 1 | 1 | 4.7325 | 6.31 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_lt_neg070` | 4 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg010_pos080` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 3 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_pos080_pos150` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_pos150_pos300` | 3 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_pos150_pos300_plus` | 1 | 0 | None | None | None | `hold_sample` |
| `confidence_band` | `confidence_070p` | 30 | 15 | 0.5485 | 0.7313 | 0.4667 | `candidate_recovery_or_relax` |
| `confidence_band` | `confidence_unknown` | 15 | 15 | 0.5485 | 0.7313 | 0.4667 | `candidate_recovery_or_relax` |
| `held_bucket` | `held_600_1800s_plus` | 30 | 15 | 0.5485 | 0.7313 | 0.4667 | `candidate_recovery_or_relax` |
| `held_bucket` | `held_unknown` | 15 | 15 | 0.5485 | 0.7313 | 0.4667 | `candidate_recovery_or_relax` |
| `overnight_action` | `SELL_TODAY` | 30 | 15 | 0.5485 | 0.7313 | 0.4667 | `candidate_recovery_or_relax` |
| `overnight_action` | `action_unknown` | 15 | 15 | 0.5485 | 0.7313 | 0.4667 | `candidate_recovery_or_relax` |
| `overnight_status` | `SELL_TODAY` | 30 | 30 | 0.5485 | 0.7313 | 0.4667 | `candidate_recovery_or_relax` |
| `peak_profit_band` | `peak_unknown` | 15 | 15 | 0.5485 | 0.7313 | 0.4667 | `candidate_recovery_or_relax` |
| `peak_profit_band` | `peak_lt_zero` | 16 | 8 | -0.4575 | -0.61 | 0.0 | `candidate_tighten_or_exclude` |
| `price_source` | `holding_price_samples_last` | 45 | 30 | 0.5485 | 0.7313 | 0.4667 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_lt_neg070` | 12 | 8 | -0.7612 | -1.015 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 9 | 6 | -0.19 | -0.2533 | 0.0 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 9 | 6 | 1.7825 | 2.3767 | 1.0 | `candidate_recovery_or_relax` |
| `source_quality_gate` | `overnight_decision_coverage` | 45 | 30 | 0.5485 | 0.7313 | 0.4667 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 15 | 15 | 0.5485 | 0.7313 | 0.4667 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_sim_sell_order_assumed_filled` | 15 | 15 | 0.5485 | 0.7313 | 0.4667 | `candidate_recovery_or_relax` |
| `stage` | `exit` | 30 | 30 | 0.5485 | 0.7313 | 0.4667 | `candidate_recovery_or_relax` |

### Overnight Bucket Runtime Approval Candidates

- `overnight_bucket_1`: `confidence_band` / `confidence_070p` -> `candidate_recovery_or_relax`
- `overnight_bucket_3`: `held_bucket` / `held_600_1800s_plus` -> `candidate_recovery_or_relax`
- `overnight_bucket_5`: `overnight_action` / `SELL_TODAY` -> `candidate_recovery_or_relax`
- `overnight_bucket_7`: `overnight_status` / `SELL_TODAY` -> `candidate_recovery_or_relax`
- `overnight_bucket_10`: `price_source` / `holding_price_samples_last` -> `candidate_recovery_or_relax`
- `overnight_bucket_13`: `source_quality_gate` / `overnight_decision_coverage` -> `candidate_recovery_or_relax`
- `overnight_bucket_14`: `source_stage` / `scalp_sim_overnight_sell_today` -> `candidate_recovery_or_relax`
- `overnight_bucket_15`: `source_stage` / `scalp_sim_sell_order_assumed_filled` -> `candidate_recovery_or_relax`
- `overnight_bucket_16`: `stage` / `exit` -> `candidate_recovery_or_relax`

### Overnight Bucket Workorders

- `overnight_bucket_source_quality_1`: `confidence_band` / `confidence_070p` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_2`: `confidence_band` / `confidence_unknown` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_3`: `held_bucket` / `held_600_1800s_plus` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_4`: `held_bucket` / `held_unknown` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_5`: `overnight_action` / `SELL_TODAY` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_6`: `overnight_action` / `action_unknown` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_7`: `overnight_status` / `SELL_TODAY` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_8`: `peak_profit_band` / `peak_unknown` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_9`: `peak_profit_band` / `peak_lt_zero` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_10`: `price_source` / `holding_price_samples_last` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`

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
