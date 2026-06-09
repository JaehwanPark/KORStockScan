# Lifecycle Decision Matrix - 2026-06-08

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-08`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `25034`
- source_rows_total: `44511`
- retained_rows: `25034`
- dropped_rows_by_source: `{'dedupe': 19477}`
- joined_rows: `24122`
- policy_pass_count: `5`
- promote_ready_count: `1`
- entry_bucket_actionable_count: `14`
- entry_bucket_runtime_candidate_count: `10`
- holding_bucket_count/workorders: `35` / `10`
- exit_bucket_count/workorders: `52` / `10`
- scale_in_bucket_actionable_count: `231`
- scale_in_bucket_runtime_candidate_count: `10`
- overnight_bucket_actionable_count: `8`
- overnight_bucket_runtime_candidate_count: `7`
- lifecycle_flow_bucket_count: `107`
- lifecycle_flow_complete_count: `79`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `0` / `79` / `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0034`
- incomplete_flow_reason_counts: `{'missing_entry': 22936, 'missing_holding': 23389, 'missing_exit': 22692, 'postclose_exit_without_entry': 719, 'missing_submit': 23373, 'candidate_id_only': 22981, 'scale_in_noise_only': 22191, 'sim_record_id_only': 376}`
- bucket_directed_sim_probe: `{'observed_row_count': 2197, 'matched_row_count': 999, 'background_row_count': 1198, 'matched_unique_source_bucket_count': 2, 'match_status_counts': {'matched': 999, 'no_match': 473, 'not_instrumented': 725}, 'matched_classification_state_counts': {'lifecycle_flow_sim_probe_candidate': 999}, 'primary_source': 'matched_bucket_directed_sim_probe_only', 'background_source': 'unmatched_or_policy_missing_sim_observation', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 1, 'route_counts': {'bounded_auxiliary_weight': 1, 'hold_sample': 4}, 'quality_counts': {'observational_only_pending_outcome': 1, 'hold_sample': 4}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 622 | 166 | 0.3266 | 1.0 | `pass` | `BUY_DEFENSIVE` | True |
| `submit` | 434 | 376 | -0.3636 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 386 | 376 | -0.9469 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 22511 | 22510 | -0.3299 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 1081 | 694 | -1.0085 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 23490, 'complete_flow_count': 79, 'direct_sim_record_complete_flow_count': 0, 'adm_bridge_complete_flow_count': 79, 'fallback_complete_flow_count': 0, 'incomplete_flow_count': 23411, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 25034, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0034, 'complete_flow_conversion_denominator': 824, 'complete_flow_conversion_rate': 0.0959, 'active_priority_incomplete_seed_count': 475, 'scale_in_followup_event_count': 22511, 'scale_in_unique_flow_count': 18262, 'scale_in_noise_flow_count': 22191, 'denominator_exclusion_counts': {'scale_in_noise_flow_excluded': 22191, 'active_priority_incomplete_seed_excluded': 475}, 'conversion_blocker_reason_counts': {'missing_entry': 745, 'missing_holding': 724, 'missing_exit': 26, 'postclose_exit_without_entry': 719, 'missing_submit': 708, 'sim_record_id_only': 321, 'candidate_id_only': 387}, 'observation_seed_reason_counts': {'missing_submit': 22665, 'missing_holding': 22665, 'missing_exit': 22666, 'candidate_id_only': 22594, 'missing_entry': 22191, 'scale_in_noise_only': 22191, 'sim_record_id_only': 55}, 'join_contract_blocked': False, 'bundle_ev_tuning_state': 'ready_for_bundle_ev_tuning', 'top_incomplete_reason': 'missing_holding', 'stage_identity': {'entry': {'source_row_count': 622, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 164, 'candidate_id': 458}, 'identity_join_rate': 1.0}, 'submit': {'source_row_count': 434, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 434}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 386, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 376, 'exact_sim_record_id': 10}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 22511, 'identity_missing_count': 0, 'identity_quality_counts': {'candidate_id': 22136, 'exact_sim_record_id': 375}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 1081, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 366, 'exact_sim_record_id': 328, 'candidate_id': 387}, 'identity_join_rate': 1.0}}, 'required_stage_source_counts': {'entry': 622, 'submit': 434, 'holding': 386, 'exit': 1081}, 'incomplete_flow_reason_counts': {'missing_entry': 22936, 'missing_holding': 23389, 'missing_exit': 22692, 'postclose_exit_without_entry': 719, 'missing_submit': 23373, 'candidate_id_only': 22981, 'scale_in_noise_only': 22191, 'sim_record_id_only': 376}, 'bucket_count': 107, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:ec33ba7790` | 3 | 3 | -2.1459 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:bdd3af3121` | 3 | 3 | 0.9552 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:5035e8a5e2` | 3 | 3 | -0.9556 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:af7d5c8fc1` | 2 | 2 | -1.8192 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9c99306a62` | 2 | 2 | -1.3372 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:f3928c3e95` | 2 | 2 | -0.7964 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:2f79e0a458` | 2 | 2 | -2.649 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:0925bb0755` | 2 | 2 | -0.2597 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:a0da04849a` | 2 | 2 | -0.8785 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:bbc4a80a0b` | 2 | 2 | -1.7694 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:ce63fe0afc` | 2 | 2 | -0.3346 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:eea5fd0867` | 1 | 1 | -0.9219 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:e397a3cc31` | 1 | 1 | -0.7784 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:3428f86331` | 1 | 1 | -1.6188 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:e7d65a7c45` | 1 | 1 | -2.7806 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:6513e82ce9` | 1 | 1 | 0.0593 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:3036de4e2e` | 1 | 1 | -0.1287 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:86108067b2` | 1 | 1 | -4.1326 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:77e4bf5bad` | 1 | 1 | -1.7712 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:1b4e4b3128` | 1 | 1 | -1.0941 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 622, 'bucket_count': 180, 'actionable_bucket_count': 14, 'source_quality_blocked_bucket_count': 0, 'runtime_candidate_count': 10, 'workorder_count': 10}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `WAIT_REQUOTE` | 113 | 113 | 0.4274 | 0.7753 | 0.6372 | `candidate_recovery_or_relax` |
| `chosen_action` | `NO_BUY_AI` | 150 | 53 | 0.1117 | -0.8726 | 0.3019 | `hold_no_edge` |
| `chosen_action` | `ALLOW_BOTTOMING_ENTRY` | 73 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `ALLOW_LEVEL1_RISK_OFF_ENTRY` | 272 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `BUY_NOW` | 2 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_SOURCE_QUALITY` | 12 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 15 | 9 | -0.0554 | 0.3122 | 0.4444 | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 9 | 9 | 0.5518 | 0.0144 | 0.8889 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 9 | 9 | -0.2127 | -0.8454 | 0.6667 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 8 | 8 | 0.435 | 0.8975 | 0.5 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 8 | 8 | 0.49 | -0.6527 | 0.875 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 7 | 6 | 0.2291 | -1.0933 | 0.3333 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 7 | 6 | 0.2863 | -2.2017 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 6 | 6 | 1.9045 | 3.0702 | 0.5 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 6 | 6 | 1.2053 | 2.2553 | 0.8333 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_ok|time=time_1000_1200` | 6 | 6 | 0.9961 | 3.1119 | 0.8333 | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 5 | 5 | 0.7745 | 0.5288 | 0.8 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_ok|time=time_1200_1400` | 5 | 5 | -0.2604 | 0.8837 | 0.8 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_ok|time=time_1200_1400` | 5 | 4 | -0.035 | -2.5225 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1400_close` | 4 | 4 | -1.0251 | -1.5808 | 0.25 | `hold_sample` |
| `exit_rule` | `exit_unknown` | 569 | 113 | 0.4274 | 0.7753 | 0.6372 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_soft_stop_pct` | 27 | 27 | 0.009 | -1.9285 | 0.0 | `hold_no_edge` |
| `exit_rule` | `scalp_trailing_take_profit` | 16 | 16 | 0.5474 | 2.1394 | 1.0 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_hard_stop_pct` | 10 | 10 | -0.308 | -2.841 | 0.0 | `candidate_tighten_or_exclude` |
| `liquidity_bucket` | `liquidity_high` | 232 | 166 | 0.3266 | 0.2492 | 0.5301 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 123 | 80 | 0.1725 | -0.5015 | 0.525 | `hold_no_edge` |
| `overbought_bucket` | `overbought_watch` | 95 | 41 | 0.6116 | 0.6631 | 0.4878 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_ok` | 49 | 36 | 0.3415 | 1.1413 | 0.6111 | `candidate_recovery_or_relax` |
| `score_band` | `score_70p` | 86 | 48 | 0.058 | 0.621 | 0.5625 | `hold_no_edge` |
| `score_band` | `score_66_69` | 55 | 40 | 0.8819 | 1.073 | 0.7 | `candidate_recovery_or_relax` |
| `score_band` | `score_60_62` | 341 | 39 | 0.054 | -0.6179 | 0.3333 | `hold_no_edge` |
| `score_band` | `score_63_65` | 66 | 31 | 0.2996 | -0.0067 | 0.5484 | `hold_no_edge` |
| `source_stage` | `wait6579_ev_cohort` | 113 | 113 | 0.4274 | 0.7753 | 0.6372 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 89 | 53 | 0.1117 | -0.8726 | 0.3019 | `hold_no_edge` |
| `stale_bucket` | `fresh_or_unflagged` | 458 | 113 | 0.4274 | 0.7753 | 0.6372 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh` | 115 | 52 | 0.1217 | -0.9096 | 0.2885 | `hold_no_edge` |
| `strength_bucket` | `strong_strength_momentum` | 111 | 90 | 0.5549 | 0.9835 | 0.6556 | `candidate_recovery_or_relax` |
| `strength_bucket` | `weak_strength_momentum` | 142 | 69 | 0.0642 | -0.6264 | 0.3768 | `hold_no_edge` |
| `time_bucket` | `time_1000_1200` | 187 | 62 | 0.4787 | 0.5476 | 0.6935 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_0900_1000` | 198 | 42 | 0.4019 | 0.7813 | 0.4762 | `candidate_recovery_or_relax` |

### Entry Bucket Runtime Approval Candidates

- `entry_bucket_5`: `liquidity_bucket` / `liquidity_high` -> `candidate_recovery_or_relax`
- `entry_bucket_6`: `overbought_bucket` / `overbought_watch` -> `candidate_recovery_or_relax`
- `entry_bucket_7`: `overbought_bucket` / `overbought_ok` -> `candidate_recovery_or_relax`
- `entry_bucket_8`: `score_band` / `score_66_69` -> `candidate_recovery_or_relax`
- `entry_bucket_9`: `source_stage` / `wait6579_ev_cohort` -> `candidate_recovery_or_relax`
- `entry_bucket_10`: `stale_bucket` / `fresh_or_unflagged` -> `candidate_recovery_or_relax`
- `entry_bucket_11`: `strength_bucket` / `strong_strength_momentum` -> `candidate_recovery_or_relax`
- `entry_bucket_12`: `time_bucket` / `time_1000_1200` -> `candidate_recovery_or_relax`
- `entry_bucket_13`: `time_bucket` / `time_0900_1000` -> `candidate_recovery_or_relax`
- `entry_bucket_14`: `time_bucket` / `time_1200_1400` -> `candidate_recovery_or_relax`

### Entry Bucket Workorders

- `entry_bucket_source_quality_1`: `chosen_action` / `WAIT_REQUOTE` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_2`: `exit_rule` / `exit_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_3`: `exit_rule` / `scalp_trailing_take_profit` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_4`: `exit_rule` / `scalp_hard_stop_pct` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_5`: `liquidity_bucket` / `liquidity_high` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_6`: `overbought_bucket` / `overbought_watch` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_7`: `overbought_bucket` / `overbought_ok` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_8`: `score_band` / `score_66_69` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_9`: `source_stage` / `wait6579_ev_cohort` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_10`: `stale_bucket` / `fresh_or_unflagged` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`

## Submit Bucket Attribution

- decision_authority: `adm_ldm_submit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'submit_rows': 434, 'bucket_count': 72, 'contract_gap_count': 0, 'workorder_count': 0, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 406 | 376 | -0.3636 | `keep_collecting` |
| `actual_order_submitted` | `true` | 28 | 0 | None | `keep_collecting` |
| `broker_order_forbidden` | `true` | 406 | 376 | -0.3636 | `keep_collecting` |
| `broker_order_forbidden` | `false` | 28 | 0 | None | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 96 | 96 | -0.252 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 78 | 78 | -0.3519 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 48 | 48 | -0.0213 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 48 | 48 | -0.277 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 41 | 41 | -0.0838 | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=block_False|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=latency_unknown|fill=false|submitted=true` | 24 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 21 | 21 | -2.6509 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=false|submitted=false` | 20 | 20 | 0.0996 | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=block_False|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_normal|latency=latency_unknown|fill=false|submitted=false` | 15 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=pre_submit_liquidity_guard_block|revalidation=block_False|quote_age=quote_age_unknown|liquidity=below_min_liquidity|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=latency_unknown|fill=false|submitted=false` | 11 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=block_False|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_ok|latency=latency_unknown|fill=false|submitted=true` | 4 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=false|submitted=false` | 4 | 4 | -0.2428 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 4 | 4 | 0.6241 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 4 | 4 | -0.3518 | `source_quality_workorder` |
| `combo_submit_quality` | `source=pre_submit_liquidity_guard_block|revalidation=block_False|quote_age=quote_age_unknown|liquidity=below_min_liquidity|liquidity_guard=liquidity_guard_unknown|overbought=overbought_ok|latency=latency_unknown|fill=false|submitted=false` | 3 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 3 | 3 | -0.0727 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=pullback_or_rebreak_not_confirmed|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 2 | 2 | -1.1608 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 2 | 2 | 0.1318 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=pullback_or_rebreak_not_confirmed|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 2 | 2 | -1.5734 | `source_quality_workorder` |
| `combo_submit_quality` | `source=pre_submit_liquidity_guard_block|revalidation=block_False|quote_age=quote_age_unknown|liquidity=below_min_liquidity|liquidity_guard=liquidity_guard_unknown|overbought=pullback_required|latency=latency_unknown|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=pullback_or_rebreak_not_confirmed|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | 0.1039 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_overbought_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=pullback_or_rebreak_not_confirmed|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | -7.0043 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_overbought_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=pullback_or_rebreak_not_confirmed|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | -1.4374 | `source_quality_workorder` |
| `latency_reason` | `scalp_live_simulator` | 376 | 376 | -0.3636 | `keep_collecting` |
| `latency_reason` | `latency_reason_unknown` | 58 | 0 | None | `source_quality_workorder` |
| `latency_state` | `simulated` | 376 | 376 | -0.3636 | `keep_collecting` |
| `latency_state` | `latency_unknown` | 58 | 0 | None | `source_quality_workorder` |
| `liquidity_bucket` | `below_min_liquidity` | 269 | 254 | -0.5004 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 122 | 122 | -0.0787 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_not_available` | 43 | 0 | None | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 254 | 254 | -0.5004 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 122 | 122 | -0.0787 | `keep_collecting` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 58 | 0 | None | `source_quality_workorder` |
| `overbought_bucket` | `overbought_ok` | 298 | 291 | -0.3882 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 78 | 78 | -0.1276 | `keep_collecting` |
| `overbought_bucket` | `overbought_not_available` | 35 | 0 | None | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 386, 'source_row_count': 386, 'bucket_count': 35, 'joined_sample': 1880, 'source_quality_adjusted_ev_pct': -0.9469, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 224 | 224 | -1.6413 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 37 | 37 | -1.1401 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 26 | 26 | -0.0395 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 20 | 20 | 0.4358 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 20 | 20 | 0.5283 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 19 | 19 | -1.2718 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 11 | 11 | 3.473 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 6 | 6 | 1.1601 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 5 | 5 | 1.2501 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 3 | 3 | 0.4414 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 2 | 2 | 1.7376 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | 1.8776 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 1.8388 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 1 | 1 | -0.23 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos150_pos300_plus|held=held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_not_applicable_at_start` | 376 | 376 | -0.9469 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s` | 6 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 4 | 0 | None | `hold_sample` |
| `holding_action` | `holding_action_not_applicable_at_start` | 302 | 302 | -1.0312 | `candidate_tighten_or_exclude` |
| `holding_action` | `BUY` | 45 | 45 | -0.6795 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 29 | 29 | -0.4842 | `candidate_tighten_or_exclude` |
| `holding_action` | `SELL_TODAY` | 10 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 376 | 376 | -0.9469 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 10 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 283 | 280 | -1.55 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 33 | 33 | 0.2367 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 25 | 25 | 0.6727 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg010_pos080` | 25 | 23 | 0.4365 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300_plus` | 16 | 14 | 3.1084 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 4 | 1 | -0.23 | `hold_sample` |

### Holding Bucket Attribution Workorders

- `holding_bucket_source_quality_1`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_2`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_3`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_4`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_5`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_6`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_7`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_8`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_9`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_10`: `held_bucket` / `held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Exit Bucket Attribution

- decision_authority: `adm_ldm_exit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'exit_rows': 1081, 'source_row_count': 1081, 'bucket_count': 52, 'joined_sample': 3470, 'source_quality_adjusted_ev_pct': -1.0085, 'source_quality_gate': 'pass', 'unknown_reason_counts': {'not_applicable': 4, 'join_gap': 8, 'missing_source_field': 1}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 254 | 254 | -1.2733 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 63 | 63 | -2.7396 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 63 | 63 | -1.2097 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 58 | 58 | -0.5333 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 49 | 49 | -0.7286 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 48 | 48 | -1.5995 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 32 | 32 | -0.9715 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 18 | 18 | -1.8134 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 15 | 15 | -0.4452 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 11 | 11 | 1.4213 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 10 | 10 | 0.9582 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 9 | 9 | 1.0468 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 9 | 9 | 0.1923 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 9 | 9 | 0.563 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 8 | 8 | -0.7724 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 6 | 6 | 3.3514 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300` | 6 | 6 | 1.2269 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 5 | 5 | 1.6803 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 4 | 4 | 0.255 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 4 | 4 | -0.3183 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 3 | 3 | -0.9775 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 3 | 3 | -0.235 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 2 | 2 | 0.3412 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos150_pos300_plus` | 2 | 2 | 3.1763 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos150_pos300` | 1 | 1 | 1.82 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos150_pos300_plus` | 1 | 1 | 3.17 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300_plus` | 1 | 1 | 6.9078 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_euphoria_context_noop|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown` | 360 | 0 | None | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown` | 27 | 0 | None | `source_quality_workorder` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 318 | 318 | -1.0954 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 148 | 148 | -0.3863 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 143 | 143 | -1.7839 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 75 | 75 | -0.5688 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 397 | 10 | 0.3397 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 318 | 318 | -1.0954 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 144 | 144 | -1.9545 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 129 | 129 | -1.1129 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 93 | 93 | 0.7536 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 10 | 10 | 0.3397 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_rule_unknown` | 387 | 0 | None | `source_quality_workorder` |

### Exit Bucket Attribution Workorders

- `exit_bucket_source_quality_1`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_2`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_3`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_4`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_5`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_6`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_7`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_8`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_9`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_10`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'scale_in_rows': 22511, 'bucket_count': 2232, 'actionable_bucket_count': 231, 'runtime_candidate_count': 10, 'workorder_count': 10, 'arm_counts': {'AVG_DOWN': 15936, 'PYRAMID': 6575}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_70p` | 11886 | 11886 | -0.3507 | -0.4686 | 0.2497 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_66_69` | 4840 | 4840 | -0.2023 | -0.306 | 0.3585 | `hold_no_edge` |
| `ai_score_band` | `score_60_62` | 3977 | 3977 | -0.4015 | -0.4674 | 0.3327 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_63_65` | 1193 | 1193 | -0.3603 | -0.4612 | 0.2816 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_lt60` | 614 | 614 | -0.4117 | -0.5414 | 0.2313 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_unknown` | 1 | 0 | None | None | None | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 22510 | 22510 | -0.3299 | -0.435 | 0.2889 | `candidate_tighten_or_exclude` |
| `ai_score_source` | `stage_rule_backfilled` | 1 | 0 | None | None | None | `hold_sample` |
| `arm` | `AVG_DOWN` | 15936 | 15935 | -0.7709 | -0.8758 | 0.0 | `candidate_tighten_or_exclude` |
| `arm` | `PYRAMID` | 6575 | 6575 | 0.7389 | 0.6332 | 0.9892 | `candidate_recovery_or_relax` |
| `blocker_namespace` | `AVG_DOWN` | 11449 | 11448 | -0.9459 | -1.0574 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_namespace` | `PYRAMID` | 6575 | 6575 | 0.7389 | 0.6332 | 0.9892 | `candidate_recovery_or_relax` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 4487 | 4487 | -0.3244 | -0.4123 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `profit_not_enough` | 6278 | 6278 | 0.7047 | 0.5933 | 0.989 | `candidate_recovery_or_relax` |
| `blocker_reason` | `add_judgment_locked` | 780 | 780 | -0.2664 | -0.2891 | 0.1821 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.96)` | 584 | 584 | -0.8449 | -0.96 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.20)` | 550 | 550 | -1.022 | -1.2 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.37)` | 547 | 547 | -1.2563 | -1.37 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.43)` | 500 | 500 | -1.2541 | -1.43 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.78)` | 496 | 496 | -0.728 | -0.78 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.82)` | 491 | 491 | -0.6262 | -0.82 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.10)` | 462 | 462 | -1.0204 | -1.1 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.00)` | 444 | 444 | -0.9288 | -1.0 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 375 | 375 | -0.9753 | -0.9753 | 0.1173 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `low_broken` | 337 | 337 | -0.3962 | -0.4212 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `ok` | 242 | 242 | -2.0241 | -2.5382 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.14)` | 173 | 173 | -1.0095 | -1.14 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.86)` | 154 | 154 | -0.7877 | -0.86 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.18)` | 142 | 142 | -1.0821 | -1.18 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.01)` | 133 | 133 | -0.9088 | -1.01 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.05)` | 121 | 121 | -0.9697 | -1.05 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.04)` | 113 | 113 | -0.908 | -1.04 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.34)` | 110 | 110 | -1.2168 | -1.34 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `scalping_cutoff` | 108 | 108 | -0.406 | -0.5008 | 0.25 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.71)` | 107 | 107 | -0.6256 | -0.71 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.73)` | 107 | 107 | -0.6267 | -0.73 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.93)` | 102 | 102 | -0.8225 | -0.93 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.07)` | 101 | 101 | -0.0369 | -0.07 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.80)` | 101 | 101 | -0.7253 | -0.8 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.02)` | 95 | 95 | -0.9343 | -1.02 | 0.0 | `candidate_tighten_or_exclude` |

### Scale-In Bucket Runtime Approval Candidates

- `scale_in_bucket_1`: `ai_score_band` / `score_70p` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_2`: `ai_score_band` / `score_60_62` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_3`: `ai_score_band` / `score_63_65` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_4`: `ai_score_band` / `score_lt60` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_5`: `ai_score_source` / `score_field_backfilled` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_6`: `arm` / `AVG_DOWN` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_7`: `arm` / `PYRAMID` -> `candidate_recovery_or_relax`
- `scale_in_bucket_8`: `blocker_namespace` / `AVG_DOWN` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_9`: `blocker_namespace` / `PYRAMID` -> `candidate_recovery_or_relax`
- `scale_in_bucket_10`: `blocker_namespace` / `AVG_DOWN_ONLY` -> `candidate_tighten_or_exclude`

### Scale-In Bucket Workorders

- `scale_in_bucket_source_quality_1`: `ai_score_band` / `score_70p` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_2`: `ai_score_band` / `score_60_62` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_3`: `ai_score_band` / `score_63_65` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_4`: `ai_score_band` / `score_lt60` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_5`: `ai_score_source` / `score_field_backfilled` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_6`: `arm` / `AVG_DOWN` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_7`: `arm` / `PYRAMID` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_8`: `blocker_namespace` / `AVG_DOWN` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_9`: `blocker_namespace` / `PYRAMID` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_10`: `blocker_namespace` / `AVG_DOWN_ONLY` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`

## Overnight Bucket Attribution

- decision_authority: `adm_ldm_overnight_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'overnight_rows': 20, 'bucket_count': 27, 'actionable_bucket_count': 8, 'runtime_candidate_count': 7, 'workorder_count': 8, 'status_counts': {'HOLD_OVERNIGHT': 10, 'SELL_TODAY': 10}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 3 | 3 | -0.9775 | -1.3033 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 3 | 3 | -0.235 | -0.3133 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 2 | 2 | 0.3412 | 0.455 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos150_pos300_plus` | 2 | 2 | 3.1763 | 4.235 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_lt_neg070` | 3 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg010_pos080` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 3 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_pos150_pos300_plus` | 2 | 0 | None | None | None | `hold_sample` |
| `confidence_band` | `confidence_070p` | 20 | 10 | 0.3397 | 0.453 | 0.4 | `candidate_recovery_or_relax` |
| `held_bucket` | `held_600_1800s` | 12 | 6 | -0.2687 | -0.3583 | 0.3333 | `hold_no_edge` |
| `held_bucket` | `held_600_1800s_plus` | 8 | 4 | 1.2525 | 1.67 | 0.5 | `hold_sample` |
| `overnight_action` | `SELL_TODAY` | 20 | 10 | 0.3397 | 0.453 | 0.4 | `candidate_recovery_or_relax` |
| `overnight_status` | `SELL_TODAY` | 10 | 10 | 0.3397 | 0.453 | 0.4 | `candidate_recovery_or_relax` |
| `overnight_status` | `HOLD_OVERNIGHT` | 10 | 0 | None | None | None | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 12 | 6 | -0.6063 | -0.8083 | 0.0 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_pos150_pos300_plus` | 4 | 2 | 3.1763 | 4.235 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 4 | 2 | 0.3412 | 0.455 | 1.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 20 | 10 | 0.3397 | 0.453 | 0.4 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_lt_neg070` | 6 | 3 | -0.9775 | -1.3033 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 6 | 3 | -0.235 | -0.3133 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 20 | 10 | 0.3397 | 0.453 | 0.4 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 10 | 10 | 0.3397 | 0.453 | 0.4 | `candidate_recovery_or_relax` |
| `stage` | `exit` | 10 | 10 | 0.3397 | 0.453 | 0.4 | `candidate_recovery_or_relax` |

### Overnight Bucket Runtime Approval Candidates

- `overnight_bucket_1`: `confidence_band` / `confidence_070p` -> `candidate_recovery_or_relax`
- `overnight_bucket_2`: `overnight_action` / `SELL_TODAY` -> `candidate_recovery_or_relax`
- `overnight_bucket_3`: `overnight_status` / `SELL_TODAY` -> `candidate_recovery_or_relax`
- `overnight_bucket_5`: `price_source` / `holding_price_samples_last` -> `candidate_recovery_or_relax`
- `overnight_bucket_6`: `source_quality_gate` / `overnight_decision_coverage` -> `candidate_recovery_or_relax`
- `overnight_bucket_7`: `source_stage` / `scalp_sim_overnight_sell_today` -> `candidate_recovery_or_relax`
- `overnight_bucket_8`: `stage` / `exit` -> `candidate_recovery_or_relax`

### Overnight Bucket Workorders

- `overnight_bucket_source_quality_1`: `confidence_band` / `confidence_070p` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_2`: `overnight_action` / `SELL_TODAY` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_3`: `overnight_status` / `SELL_TODAY` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_4`: `peak_profit_band` / `peak_lt_zero` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_5`: `price_source` / `holding_price_samples_last` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_6`: `source_quality_gate` / `overnight_decision_coverage` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_7`: `source_stage` / `scalp_sim_overnight_sell_today` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_8`: `stage` / `exit` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`

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
