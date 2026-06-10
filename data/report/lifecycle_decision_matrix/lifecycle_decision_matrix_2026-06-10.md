# Lifecycle Decision Matrix - 2026-06-10

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-10`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `25704`
- source_rows_total: `40072`
- retained_rows: `25704`
- dropped_rows_by_source: `{'dedupe': 14368}`
- joined_rows: `24185`
- policy_pass_count: `5`
- promote_ready_count: `0`
- entry_bucket_actionable_count: `9`
- entry_bucket_runtime_candidate_count: `6`
- holding_bucket_count/workorders: `40` / `10`
- exit_bucket_count/workorders: `60` / `10`
- scale_in_bucket_actionable_count: `307`
- scale_in_bucket_runtime_candidate_count: `10`
- overnight_bucket_actionable_count: `7`
- overnight_bucket_runtime_candidate_count: `2`
- lifecycle_flow_bucket_count: `145`
- lifecycle_flow_complete_count: `101`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `0` / `101` / `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0042`
- incomplete_flow_reason_counts: `{'missing_entry': 23271, 'missing_holding': 23634, 'missing_exit': 22872, 'missing_submit': 23633, 'postclose_exit_without_entry': 806, 'candidate_id_only': 23279, 'sim_record_id_only': 332, 'scale_in_noise_only': 22439}`
- bucket_directed_sim_probe: `{'observed_row_count': 2398, 'matched_row_count': 0, 'background_row_count': 2398, 'matched_unique_source_bucket_count': 0, 'match_status_counts': {'not_instrumented': 842, 'policy_disabled': 1556}, 'matched_classification_state_counts': {}, 'primary_source': 'matched_bucket_directed_sim_probe_only', 'background_source': 'unmatched_or_policy_missing_sim_observation', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 1, 'route_counts': {'bounded_auxiliary_weight': 1, 'hold_sample': 4}, 'quality_counts': {'observational_only_pending_outcome': 1, 'hold_sample': 4}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 725 | 190 | 0.09 | 1.0 | `pass` | `NO_CHANGE` | False |
| `submit` | 538 | 451 | -0.3873 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 491 | 451 | -1.0027 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 22726 | 22380 | -0.5608 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 1224 | 713 | -1.0044 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 23779, 'complete_flow_count': 101, 'direct_sim_record_complete_flow_count': 0, 'adm_bridge_complete_flow_count': 101, 'fallback_complete_flow_count': 0, 'incomplete_flow_count': 23678, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 25704, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0042, 'complete_flow_conversion_denominator': 933, 'complete_flow_conversion_rate': 0.1083, 'active_priority_incomplete_seed_count': 407, 'scale_in_followup_event_count': 22726, 'scale_in_unique_flow_count': 18288, 'scale_in_noise_flow_count': 22439, 'denominator_exclusion_counts': {'scale_in_noise_flow_excluded': 22439, 'active_priority_incomplete_seed_excluded': 407}, 'conversion_blocker_reason_counts': {'missing_entry': 832, 'missing_holding': 797, 'missing_exit': 26, 'postclose_exit_without_entry': 806, 'missing_submit': 796, 'sim_record_id_only': 285, 'candidate_id_only': 511}, 'observation_seed_reason_counts': {'missing_submit': 22837, 'missing_holding': 22837, 'missing_exit': 22846, 'candidate_id_only': 22768, 'missing_entry': 22439, 'scale_in_noise_only': 22439, 'sim_record_id_only': 47}, 'join_contract_blocked': False, 'bundle_ev_tuning_state': 'ready_for_bundle_ev_tuning', 'top_incomplete_reason': 'missing_holding', 'stage_identity': {'entry': {'source_row_count': 725, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 349, 'candidate_id': 376}, 'identity_join_rate': 1.0}, 'submit': {'source_row_count': 538, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 538}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 491, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 466, 'exact_sim_record_id': 25}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 22726, 'identity_missing_count': 0, 'identity_quality_counts': {'exact_sim_record_id': 334, 'candidate_id': 22392}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 1224, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 407, 'exact_sim_record_id': 306, 'candidate_id': 511}, 'identity_join_rate': 1.0}}, 'required_stage_source_counts': {'entry': 725, 'submit': 538, 'holding': 491, 'exit': 1224}, 'incomplete_flow_reason_counts': {'missing_entry': 23271, 'missing_holding': 23634, 'missing_exit': 22872, 'missing_submit': 23633, 'postclose_exit_without_entry': 806, 'candidate_id_only': 23279, 'sim_record_id_only': 332, 'scale_in_noise_only': 22439}, 'bucket_count': 145, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:6564dad233` | 3 | 3 | -0.9132 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:ec33ba7790` | 3 | 3 | -1.6944 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:00f1a930ff` | 2 | 2 | 0.0097 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9c99306a62` | 2 | 2 | -1.6342 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:a2a88f9390` | 2 | 2 | -1.3424 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:388199cb18` | 2 | 2 | -1.4154 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:bbc4a80a0b` | 2 | 2 | -1.5209 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:db99ed9342` | 2 | 2 | -0.3382 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:44682ae7f6` | 1 | 1 | -0.7658 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:318057d8fb` | 1 | 1 | -1.5336 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:f72d5bee4a` | 1 | 1 | -1.298 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:7a21687583` | 1 | 1 | -2.3712 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:2d47627f4e` | 1 | 1 | -2.4478 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:58f184c302` | 1 | 1 | -0.8273 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:fa53949948` | 1 | 1 | -2.6217 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:e7d65a7c45` | 1 | 1 | -0.9546 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:2d14fc030f` | 1 | 1 | -2.6937 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:af7d5c8fc1` | 1 | 1 | -1.5043 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:1826709612` | 1 | 1 | -1.2065 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:dbbccb3993` | 1 | 1 | 0.6063 | `candidate_recovery_or_relax` | `pass` |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 725, 'bucket_count': 165, 'actionable_bucket_count': 9, 'source_quality_blocked_bucket_count': 0, 'runtime_candidate_count': 6, 'workorder_count': 9}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `NO_BUY_AI` | 330 | 101 | -0.1678 | -1.7038 | 0.1485 | `hold_no_edge` |
| `chosen_action` | `WAIT_REQUOTE` | 86 | 86 | 0.4052 | 1.0245 | 0.4651 | `candidate_recovery_or_relax` |
| `chosen_action` | `BUY_NOW` | 6 | 3 | -0.2698 | -1.9467 | 0.3333 | `hold_sample` |
| `chosen_action` | `ALLOW_BOTTOMING_ENTRY` | 36 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `ALLOW_LEVEL1_RISK_OFF_ENTRY` | 254 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_SOURCE_QUALITY` | 13 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 35 | 22 | -0.0025 | -1.4968 | 0.2273 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 69 | 22 | -0.0489 | -1.9418 | 0.0455 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 18 | 18 | 0.1903 | 0.4281 | 0.3889 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 33 | 16 | -0.2278 | -1.8738 | 0.0625 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 15 | 15 | -0.3875 | -0.4747 | 0.4 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 9 | 9 | 1.2751 | 1.7878 | 0.6667 | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 8 | 8 | 0.4442 | 0.8882 | 0.5 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 30 | 7 | 0.1217 | -0.92 | 0.2857 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 5 | 5 | 0.0005 | 0.0152 | 0.4 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 5 | 5 | 2.1273 | 4.1053 | 0.4 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 13 | 5 | 0.0463 | -1.398 | 0.2 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 4 | 4 | -0.4305 | -2.27 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 4 | 4 | 1.6333 | 2.0215 | 0.75 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_ok|time=time_1000_1200` | 4 | 4 | 1.5042 | 5.4704 | 1.0 | `hold_sample` |
| `exit_rule` | `exit_unknown` | 621 | 86 | 0.4052 | 1.0245 | 0.4651 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_soft_stop_pct` | 62 | 62 | -0.1215 | -1.9206 | 0.0 | `hold_no_edge` |
| `exit_rule` | `scalp_hard_stop_pct` | 25 | 25 | -0.282 | -2.9468 | 0.0 | `hold_no_edge` |
| `exit_rule` | `scalp_trailing_take_profit` | 15 | 15 | -0.1295 | 0.9847 | 1.0 | `hold_no_edge` |
| `liquidity_bucket` | `liquidity_high` | 381 | 190 | 0.09 | -0.4727 | 0.2947 | `hold_no_edge` |
| `overbought_bucket` | `overbought_normal` | 355 | 150 | 0.0767 | -0.797 | 0.2733 | `hold_no_edge` |
| `overbought_bucket` | `overbought_watch` | 56 | 25 | 0.6363 | 0.7238 | 0.32 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_ok` | 19 | 12 | -0.1246 | 1.408 | 0.5833 | `hold_no_edge` |
| `score_band` | `score_60_62` | 409 | 66 | -0.1318 | -1.7771 | 0.1212 | `hold_no_edge` |
| `score_band` | `score_70p` | 77 | 42 | 0.173 | 0.3908 | 0.4524 | `hold_no_edge` |
| `score_band` | `score_63_65` | 78 | 41 | 0.1532 | 0.2413 | 0.3171 | `hold_no_edge` |
| `score_band` | `score_66_69` | 34 | 22 | 0.6407 | 0.8889 | 0.4545 | `candidate_recovery_or_relax` |
| `score_band` | `score_lt60` | 127 | 19 | -0.0974 | -0.9674 | 0.3158 | `hold_no_edge` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 253 | 104 | -0.1707 | -1.7108 | 0.1538 | `hold_no_edge` |
| `source_stage` | `wait6579_ev_cohort` | 86 | 86 | 0.4052 | 1.0245 | 0.4651 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh` | 298 | 104 | -0.1707 | -1.7108 | 0.1538 | `hold_no_edge` |
| `stale_bucket` | `fresh_or_unflagged` | 376 | 86 | 0.4052 | 1.0245 | 0.4651 | `candidate_recovery_or_relax` |
| `strength_bucket` | `weak_strength_momentum` | 294 | 103 | -0.2159 | -1.5106 | 0.1748 | `hold_no_edge` |
| `strength_bucket` | `strong_strength_momentum` | 101 | 77 | 0.5383 | 0.9381 | 0.4416 | `candidate_recovery_or_relax` |
| `strength_bucket` | `neutral_strength_momentum` | 40 | 10 | -0.2123 | -0.6452 | 0.4 | `hold_no_edge` |

### Entry Bucket Runtime Approval Candidates

- `entry_bucket_4`: `overbought_bucket` / `overbought_watch` -> `candidate_recovery_or_relax`
- `entry_bucket_5`: `score_band` / `score_66_69` -> `candidate_recovery_or_relax`
- `entry_bucket_6`: `source_stage` / `wait6579_ev_cohort` -> `candidate_recovery_or_relax`
- `entry_bucket_7`: `stale_bucket` / `fresh_or_unflagged` -> `candidate_recovery_or_relax`
- `entry_bucket_8`: `strength_bucket` / `strong_strength_momentum` -> `candidate_recovery_or_relax`
- `entry_bucket_9`: `time_bucket` / `time_0900_1000` -> `candidate_recovery_or_relax`

### Entry Bucket Workorders

- `entry_bucket_source_quality_1`: `chosen_action` / `WAIT_REQUOTE` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_2`: `combo_entry_spot` / `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_3`: `exit_rule` / `exit_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_4`: `overbought_bucket` / `overbought_watch` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_5`: `score_band` / `score_66_69` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_6`: `source_stage` / `wait6579_ev_cohort` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_7`: `stale_bucket` / `fresh_or_unflagged` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_8`: `strength_bucket` / `strong_strength_momentum` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_9`: `time_bucket` / `time_0900_1000` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`

## Submit Bucket Attribution

- decision_authority: `adm_ldm_submit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'submit_rows': 538, 'bucket_count': 70, 'contract_gap_count': 0, 'workorder_count': 0, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 512 | 451 | -0.3873 | `keep_collecting` |
| `actual_order_submitted` | `true` | 26 | 0 | None | `keep_collecting` |
| `broker_order_forbidden` | `true` | 510 | 451 | -0.3873 | `keep_collecting` |
| `broker_order_forbidden` | `false` | 28 | 0 | None | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 163 | 156 | -0.6155 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 101 | 94 | -0.0396 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 55 | 55 | -0.486 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 49 | 49 | -0.1572 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=false|submitted=false` | 39 | 39 | 0.0111 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 32 | 31 | -0.6031 | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=block_False|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=latency_unknown|fill=false|submitted=true` | 23 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=block_False|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_normal|latency=latency_unknown|fill=false|submitted=false` | 22 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=pre_submit_liquidity_guard_block|revalidation=block_False|quote_age=quote_age_unknown|liquidity=below_min_liquidity|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=latency_unknown|fill=false|submitted=false` | 21 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 6 | 6 | -1.7223 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 6 | 6 | -0.5878 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 6 | 6 | -0.7385 | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=block_False|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_ok|latency=latency_unknown|fill=false|submitted=true` | 3 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=false|submitted=false` | 3 | 3 | -1.2812 | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_pass|revalidation=block_False|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_normal|latency=latency_unknown|fill=false|submitted=false` | 2 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 2 | 2 | -0.8136 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=pullback_or_rebreak_not_confirmed|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 2 | 2 | 0.7862 | `source_quality_workorder` |
| `combo_submit_quality` | `source=pre_submit_liquidity_guard_block|revalidation=block_False|quote_age=quote_age_unknown|liquidity=below_min_liquidity|liquidity_guard=liquidity_guard_unknown|overbought=overbought_ok|latency=latency_unknown|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_overbought_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=pullback_or_rebreak_not_confirmed|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | 1.57 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_overbought_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=pullback_or_rebreak_not_confirmed|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | -1.5922 | `source_quality_workorder` |
| `latency_reason` | `scalp_live_simulator` | 466 | 451 | -0.3873 | `keep_collecting` |
| `latency_reason` | `latency_reason_unknown` | 72 | 0 | None | `source_quality_workorder` |
| `latency_state` | `simulated` | 466 | 451 | -0.3873 | `keep_collecting` |
| `latency_state` | `latency_unknown` | 72 | 0 | None | `source_quality_workorder` |
| `liquidity_bucket` | `below_min_liquidity` | 309 | 280 | -0.5256 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 179 | 171 | -0.1607 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_not_available` | 50 | 0 | None | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 287 | 280 | -0.5256 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 179 | 171 | -0.1607 | `keep_collecting` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 72 | 0 | None | `source_quality_workorder` |
| `overbought_bucket` | `overbought_ok` | 364 | 345 | -0.4619 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 102 | 102 | -0.1653 | `keep_collecting` |
| `overbought_bucket` | `overbought_not_available` | 44 | 0 | None | `keep_collecting` |
| `overbought_bucket` | `overbought_normal` | 24 | 0 | None | `keep_collecting` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 4 | 4 | 0.3876 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 462 | 447 | -0.3942 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 491, 'source_row_count': 491, 'bucket_count': 40, 'joined_sample': 2255, 'source_quality_adjusted_ev_pct': -1.0027, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 317 | 317 | -1.3519 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 32 | 32 | -1.4426 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 22 | 22 | -1.2168 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 22 | 22 | 0.5043 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 18 | 18 | 0.0927 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 17 | 17 | 0.732 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 10 | 10 | 1.6544 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 3 | 3 | 0.0674 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 3 | 3 | 0.407 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 3 | 3 | 1.2832 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 2 | 2 | -0.2291 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 1.122 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 1.5762 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 8 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s` | 5 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 5 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos080_pos150|held=held_600_1800s_plus` | 6 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos150_pos300|held=held_600_1800s` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos150_pos300|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_not_applicable_at_start` | 466 | 451 | -1.0027 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s` | 10 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 15 | 0 | None | `hold_sample` |
| `holding_action` | `holding_action_not_applicable_at_start` | 387 | 384 | -1.0073 | `candidate_tighten_or_exclude` |
| `holding_action` | `BUY` | 43 | 35 | -1.3 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 36 | 32 | -0.6225 | `candidate_tighten_or_exclude` |
| `holding_action` | `SELL_TODAY` | 25 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 466 | 451 | -1.0027 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 25 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 375 | 371 | -1.3517 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 31 | 25 | 0.4926 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300` | 25 | 22 | 0.7198 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg010_pos080` | 31 | 21 | 0.0891 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300_plus` | 12 | 12 | 1.6035 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 2 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 15 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- `holding_bucket_source_quality_1`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_2`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_3`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_4`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_5`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_6`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_7`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_8`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_9`: `held_bucket` / `held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_10`: `holding_action` / `holding_action_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Exit Bucket Attribution

- decision_authority: `adm_ldm_exit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'exit_rows': 1224, 'source_row_count': 1224, 'bucket_count': 60, 'joined_sample': 3565, 'source_quality_adjusted_ev_pct': -1.0045, 'source_quality_gate': 'pass', 'unknown_reason_counts': {'not_applicable': 5, 'join_gap': 8, 'missing_source_field': 1}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 222 | 222 | -1.2151 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 91 | 91 | -1.5009 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 70 | 70 | -1.1002 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 57 | 57 | -0.5437 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 56 | 56 | -0.7997 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 49 | 49 | -2.1206 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 33 | 33 | -1.2554 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 22 | 22 | -1.6523 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 10 | 10 | 0.3075 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 9 | 9 | -0.4502 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 8 | 8 | -0.3346 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 8 | 8 | 0.779 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 7 | 7 | -0.8569 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 7 | 7 | 0.3427 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 7 | 7 | 0.9652 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 7 | 7 | 1.7979 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos080_pos150` | 6 | 6 | 0.7762 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 6 | 6 | -0.2773 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 5 | 5 | -0.0122 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 5 | 5 | 0.2605 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 4 | 4 | -3.0206 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 4 | 4 | 0.1709 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 4 | 4 | 0.4322 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos150_pos300` | 3 | 3 | 1.6325 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 3 | 3 | 0.5495 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300` | 3 | 3 | 1.1099 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 2 | 2 | -0.4313 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 1 | 1 | -0.09 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` | 1 | 1 | 0.82 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_ai_review_exit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 1 | 1 | 0.3249 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_protect_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 1 | 1 | -0.3141 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300_plus` | 1 | 1 | 2.0042 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_euphoria_context_noop|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown` | 443 | 0 | None | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown` | 68 | 0 | None | `source_quality_workorder` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 281 | 281 | -1.0677 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 172 | 172 | -1.4366 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 120 | 120 | -0.5001 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 115 | 115 | -0.9455 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 536 | 25 | -0.0126 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 281 | 281 | -1.0677 | `candidate_tighten_or_exclude` |

### Exit Bucket Attribution Workorders

- `exit_bucket_source_quality_1`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_2`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_3`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_4`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_5`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_6`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_7`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_8`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_9`: `combo_exit_result` / `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_10`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'scale_in_rows': 22726, 'bucket_count': 2269, 'actionable_bucket_count': 307, 'runtime_candidate_count': 10, 'workorder_count': 10, 'arm_counts': {'PYRAMID': 4222, 'AVG_DOWN': 18504}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_70p` | 11877 | 11877 | -0.6014 | -0.6791 | 0.172 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_60_62` | 4459 | 4459 | -0.5155 | -0.5769 | 0.172 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_66_69` | 3502 | 3502 | -0.4697 | -0.5388 | 0.1939 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_63_65` | 1420 | 1420 | -0.6414 | -0.7221 | 0.1556 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_lt60` | 1117 | 1117 | -0.4981 | -0.5811 | 0.205 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_unknown` | 351 | 5 | 0.4106 | 0.096 | 0.6 | `candidate_recovery_or_relax` |
| `ai_score_source` | `score_field_backfilled` | 22375 | 22375 | -0.561 | -0.6346 | 0.176 | `candidate_tighten_or_exclude` |
| `ai_score_source` | `sim_scale_in_source_not_scored` | 5 | 5 | 0.4106 | 0.096 | 0.6 | `candidate_recovery_or_relax` |
| `ai_score_source` | `stage_rule_backfilled` | 346 | 0 | None | None | None | `hold_sample` |
| `arm` | `AVG_DOWN` | 18504 | 18379 | -0.8239 | -0.9011 | 0.0 | `candidate_tighten_or_exclude` |
| `arm` | `PYRAMID` | 4222 | 4001 | 0.6479 | 0.5905 | 0.9853 | `candidate_recovery_or_relax` |
| `blocker_namespace` | `AVG_DOWN` | 14140 | 14015 | -0.9648 | -1.046 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 4364 | 4364 | -0.3715 | -0.436 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_namespace` | `PYRAMID` | 4222 | 4001 | 0.6479 | 0.5905 | 0.9853 | `candidate_recovery_or_relax` |
| `blocker_reason` | `profit_not_enough` | 3113 | 3113 | 0.5226 | 0.4571 | 0.9823 | `candidate_recovery_or_relax` |
| `blocker_reason` | `add_judgment_locked` | 1825 | 1825 | -0.273 | -0.2983 | 0.2499 | `hold_no_edge` |
| `blocker_reason` | `low_broken` | 606 | 606 | -0.4361 | -0.4619 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 329 | 329 | -0.9005 | -0.8999 | 0.0486 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `ok` | 286 | 286 | -1.9013 | -2.2703 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.88)` | 246 | 246 | -0.8097 | -0.88 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.20)` | 220 | 220 | -1.1172 | -1.2 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.05)` | 213 | 213 | -0.9819 | -1.05 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.23)` | 200 | 200 | -1.1482 | -1.23 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.81)` | 183 | 183 | -0.7627 | -0.81 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `scalp_sim_scale_in_window_expansion` | 181 | 181 | -0.457 | -0.4896 | 0.2983 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.96)` | 180 | 180 | -0.8844 | -0.96 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `scalping_pyramid_ok` | 173 | 173 | 2.7417 | 2.8155 | 1.0 | `candidate_recovery_or_relax` |
| `blocker_reason` | `scalping_cutoff` | 170 | 170 | 0.1459 | 0.1098 | 0.5824 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-1.32)` | 163 | 163 | -1.2195 | -1.32 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.46)` | 163 | 163 | -1.3619 | -1.46 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.91)` | 159 | 159 | -0.8404 | -0.91 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.74)` | 158 | 158 | -0.6668 | -0.74 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.78)` | 153 | 153 | -0.7201 | -0.78 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.10)` | 150 | 150 | -0.9903 | -1.1 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.18)` | 150 | 150 | -1.0787 | -1.18 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.94)` | 149 | 149 | -0.8696 | -0.94 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.33)` | 149 | 149 | -1.2421 | -1.33 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.95)` | 147 | 147 | -0.8842 | -0.95 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.01)` | 147 | 147 | -0.9606 | -1.01 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.22)` | 146 | 146 | -1.1335 | -1.22 | 0.0 | `candidate_tighten_or_exclude` |

### Scale-In Bucket Runtime Approval Candidates

- `scale_in_bucket_1`: `ai_score_band` / `score_70p` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_2`: `ai_score_band` / `score_60_62` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_3`: `ai_score_band` / `score_66_69` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_4`: `ai_score_band` / `score_63_65` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_5`: `ai_score_band` / `score_lt60` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_7`: `ai_score_source` / `score_field_backfilled` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_9`: `arm` / `AVG_DOWN` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_10`: `arm` / `PYRAMID` -> `candidate_recovery_or_relax`
- `scale_in_bucket_11`: `blocker_namespace` / `AVG_DOWN` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_12`: `blocker_namespace` / `AVG_DOWN_ONLY` -> `candidate_tighten_or_exclude`

### Scale-In Bucket Workorders

- `scale_in_bucket_source_quality_1`: `ai_score_band` / `score_70p` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_2`: `ai_score_band` / `score_60_62` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_3`: `ai_score_band` / `score_66_69` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_4`: `ai_score_band` / `score_63_65` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_5`: `ai_score_band` / `score_lt60` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_6`: `ai_score_band` / `score_unknown` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_7`: `ai_score_source` / `score_field_backfilled` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_8`: `ai_score_source` / `sim_scale_in_source_not_scored` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_9`: `arm` / `AVG_DOWN` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_10`: `arm` / `PYRAMID` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`

## Overnight Bucket Attribution

- decision_authority: `adm_ldm_overnight_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'overnight_rows': 50, 'bucket_count': 31, 'actionable_bucket_count': 7, 'runtime_candidate_count': 2, 'workorder_count': 7, 'status_counts': {'HOLD_OVERNIGHT': 25, 'SELL_TODAY': 25}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 10 | 10 | 0.3075 | 0.41 | 0.9 | `candidate_recovery_or_relax` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 6 | 6 | 0.7762 | 1.035 | 1.0 | `candidate_recovery_or_relax` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 4 | 4 | -3.0206 | -4.0275 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos150_pos300` | 3 | 3 | 1.6325 | 2.1767 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 2 | 2 | -0.4313 | -0.575 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_lt_neg070` | 4 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg010_pos080` | 10 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_pos080_pos150` | 6 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_pos150_pos300` | 3 | 0 | None | None | None | `hold_sample` |
| `confidence_band` | `confidence_070p` | 50 | 25 | -0.0126 | -0.0168 | 0.72 | `hold_no_edge` |
| `held_bucket` | `held_600_1800s_plus` | 30 | 15 | -0.217 | -0.2893 | 0.8 | `hold_no_edge` |
| `held_bucket` | `held_600_1800s` | 20 | 10 | 0.294 | 0.392 | 0.6 | `hold_no_edge` |
| `overnight_action` | `SELL_TODAY` | 50 | 25 | -0.0126 | -0.0168 | 0.72 | `hold_no_edge` |
| `overnight_status` | `SELL_TODAY` | 25 | 25 | -0.0126 | -0.0168 | 0.72 | `hold_no_edge` |
| `overnight_status` | `HOLD_OVERNIGHT` | 25 | 0 | None | None | None | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 18 | 9 | 0.345 | 0.46 | 1.0 | `candidate_recovery_or_relax` |
| `peak_profit_band` | `peak_lt_zero` | 14 | 7 | -1.8536 | -2.4714 | 0.0 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_pos080_pos150` | 12 | 6 | 0.7762 | 1.035 | 1.0 | `candidate_recovery_or_relax` |
| `peak_profit_band` | `peak_pos150_pos300` | 6 | 3 | 1.6325 | 2.1767 | 1.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 50 | 25 | -0.0126 | -0.0168 | 0.72 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 20 | 10 | 0.3075 | 0.41 | 0.9 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos080_pos150` | 12 | 6 | 0.7762 | 1.035 | 1.0 | `candidate_recovery_or_relax` |
| `source_quality_gate` | `overnight_decision_coverage` | 50 | 25 | -0.0126 | -0.0168 | 0.72 | `hold_no_edge` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 25 | 25 | -0.0126 | -0.0168 | 0.72 | `hold_no_edge` |
| `stage` | `exit` | 25 | 25 | -0.0126 | -0.0168 | 0.72 | `hold_no_edge` |

### Overnight Bucket Runtime Approval Candidates

- `overnight_bucket_1`: `combo_overnight_decision` / `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` -> `candidate_recovery_or_relax`
- `overnight_bucket_6`: `profit_band` / `profit_neg010_pos080` -> `candidate_recovery_or_relax`

### Overnight Bucket Workorders

- `overnight_bucket_source_quality_1`: `combo_overnight_decision` / `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_2`: `combo_overnight_decision` / `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_3`: `peak_profit_band` / `peak_zero_pos080` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_4`: `peak_profit_band` / `peak_lt_zero` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_5`: `peak_profit_band` / `peak_pos080_pos150` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_6`: `profit_band` / `profit_neg010_pos080` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_7`: `profit_band` / `profit_pos080_pos150` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`

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
