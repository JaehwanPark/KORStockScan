# Lifecycle Decision Matrix - 2026-06-12

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-12`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `19223`
- source_rows_total: `19751`
- retained_rows: `19223`
- dropped_rows_by_source: `{'dedupe': 528}`
- joined_rows: `16011`
- policy_pass_count: `5`
- promote_ready_count: `0`
- entry_bucket_actionable_count: `16`
- entry_bucket_runtime_candidate_count: `8`
- holding_bucket_count/workorders: `38` / `10`
- exit_bucket_count/workorders: `49` / `10`
- scale_in_bucket_actionable_count: `0`
- scale_in_bucket_runtime_candidate_count: `0`
- overnight_bucket_actionable_count: `12`
- overnight_bucket_runtime_candidate_count: `10`
- lifecycle_flow_bucket_count: `141`
- lifecycle_flow_complete_count: `94`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `0` / `94` / `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0056`
- incomplete_flow_reason_counts: `{'missing_entry': 16689, 'missing_holding': 16726, 'missing_exit': 15863, 'missing_submit': 16719, 'postclose_exit_without_entry': 945, 'sim_record_id_only': 26, 'scale_in_noise_only': 15716, 'candidate_id_only': 16629}`
- bucket_directed_sim_probe: `{'observed_row_count': 2415, 'matched_row_count': 1132, 'background_row_count': 1283, 'matched_unique_source_bucket_count': 5, 'match_status_counts': {'matched': 1132, 'no_match': 263, 'not_instrumented': 958, 'policy_disabled': 62}, 'matched_classification_state_counts': {'lifecycle_flow_sim_probe_candidate': 1132}, 'primary_source': 'matched_bucket_directed_sim_probe_only', 'background_source': 'unmatched_or_policy_missing_sim_observation', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 1, 'route_counts': {'bounded_auxiliary_weight': 1, 'hold_sample': 4}, 'quality_counts': {'observational_only_pending_outcome': 1, 'hold_sample': 4}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 829 | 70 | -0.7137 | 0.5911 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 789 | 254 | -0.9965 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 744 | 254 | -1.3986 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 15716 | 15208 | -0.4517 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 1145 | 225 | -1.4312 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 16902, 'complete_flow_count': 94, 'direct_sim_record_complete_flow_count': 0, 'adm_bridge_complete_flow_count': 94, 'fallback_complete_flow_count': 0, 'incomplete_flow_count': 16808, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 19223, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0056, 'complete_flow_conversion_denominator': 1067, 'complete_flow_conversion_rate': 0.0881, 'active_priority_incomplete_seed_count': 119, 'scale_in_followup_event_count': 15716, 'scale_in_unique_flow_count': 13898, 'scale_in_noise_flow_count': 15716, 'denominator_exclusion_counts': {'scale_in_noise_flow_excluded': 15716, 'active_priority_incomplete_seed_excluded': 119}, 'conversion_blocker_reason_counts': {'missing_entry': 973, 'missing_holding': 946, 'missing_exit': 28, 'postclose_exit_without_entry': 945, 'missing_submit': 939, 'sim_record_id_only': 19, 'candidate_id_only': 920}, 'observation_seed_reason_counts': {'missing_exit': 15835, 'missing_submit': 15780, 'missing_holding': 15780, 'missing_entry': 15716, 'sim_record_id_only': 7, 'scale_in_noise_only': 15716, 'candidate_id_only': 15709}, 'join_contract_blocked': False, 'bundle_ev_tuning_state': 'ready_for_bundle_ev_tuning', 'top_incomplete_reason': 'missing_holding', 'stage_identity': {'entry': {'source_row_count': 829, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 829}, 'identity_join_rate': 1.0}, 'submit': {'source_row_count': 789, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 789}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 744, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 725, 'exact_sim_record_id': 19}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 15716, 'identity_missing_count': 0, 'identity_quality_counts': {'exact_sim_record_id': 7, 'candidate_id': 15709}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 1145, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 206, 'exact_sim_record_id': 19, 'candidate_id': 920}, 'identity_join_rate': 1.0}}, 'required_stage_source_counts': {'entry': 829, 'submit': 789, 'holding': 744, 'exit': 1145}, 'incomplete_flow_reason_counts': {'missing_entry': 16689, 'missing_holding': 16726, 'missing_exit': 15863, 'missing_submit': 16719, 'postclose_exit_without_entry': 945, 'sim_record_id_only': 26, 'scale_in_noise_only': 15716, 'candidate_id_only': 16629}, 'bucket_count': 141, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:d3405d70cf` | 4 | 4 | -0.975 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:be2863195a` | 2 | 2 | -1.5274 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:83010e3f7e` | 2 | 2 | 1.4204 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:a6f1cf48c2` | 2 | 2 | -3.5934 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:df69d30b89` | 2 | 2 | -1.3405 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:a2a88f9390` | 2 | 2 | -3.062 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:f0874e9a2a` | 2 | 2 | -1.4741 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:917af9e5d4` | 2 | 2 | -0.9491 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:2f79e0a458` | 2 | 2 | -1.7631 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:a40c55c1ac` | 2 | 2 | -0.0965 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:44682ae7f6` | 1 | 1 | -1.3527 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:7a21687583` | 1 | 1 | -5.1733 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:3eaab3f552` | 1 | 1 | -1.4184 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:91dfabaab9` | 1 | 1 | -3.3696 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:8a29e387c0` | 1 | 1 | -1.5394 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:5d63647bf9` | 1 | 1 | 0.6168 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:5fab5969e4` | 1 | 1 | -1.2475 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:36e343de0c` | 1 | 1 | -1.1105 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:6564dad233` | 1 | 1 | -0.9334 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:6293131dcd` | 1 | 1 | -2.1925 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 829, 'bucket_count': 146, 'actionable_bucket_count': 16, 'source_quality_blocked_bucket_count': 0, 'runtime_candidate_count': 8, 'workorder_count': 10}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `NO_BUY_AI` | 802 | 70 | -0.7137 | -1.6771 | 0.1286 | `candidate_tighten_or_exclude` |
| `chosen_action` | `SKIP_SOURCE_QUALITY` | 27 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 93 | 12 | -0.9417 | -1.785 | 0.0833 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 85 | 10 | -0.3154 | -1.69 | 0.1 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 135 | 9 | 0.1781 | -2.3822 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1400_close` | 20 | 8 | -0.3766 | -2.6837 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 23 | 6 | -0.25 | 1.6117 | 0.5 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_ok|time=time_1000_1200` | 14 | 4 | -1.6081 | -2.73 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_ok|time=time_1200_1400` | 10 | 4 | -1.6098 | -1.3775 | 0.25 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 29 | 3 | -0.5344 | -0.56 | 0.3333 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 13 | 3 | -0.3955 | 0.0333 | 0.6667 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_chase_risk|time=time_1200_1400` | 7 | 2 | -2.2839 | -3.075 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_ok|time=time_1400_close` | 10 | 1 | -3.9877 | -2.27 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 12 | 1 | 0.0002 | -2.06 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1400_close` | 2 | 1 | 1.0445 | -3.1 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_ok|time=time_1400_close` | 2 | 1 | -3.4093 | -2.56 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 9 | 1 | 0.087 | -1.94 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_1000_1200` | 1 | 1 | -1.8635 | -2.33 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 48 | 1 | 0.0 | -1.75 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_ok|time=time_1000_1200` | 7 | 1 | -3.3088 | -2.7 | 0.0 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 33 | 33 | -0.6941 | -2.1009 | 0.0 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 24 | 24 | -0.7916 | -2.9525 | 0.0 | `candidate_tighten_or_exclude` |
| `liquidity_bucket` | `liquidity_high` | 737 | 70 | -0.7137 | -1.6771 | 0.1286 | `candidate_tighten_or_exclude` |
| `overbought_bucket` | `overbought_normal` | 690 | 54 | -0.3523 | -1.4802 | 0.1481 | `candidate_tighten_or_exclude` |
| `overbought_bucket` | `overbought_ok` | 73 | 11 | -2.1434 | -2.1782 | 0.0909 | `candidate_tighten_or_exclude` |
| `score_band` | `score_60_62` | 404 | 47 | -0.7583 | -1.7355 | 0.1064 | `candidate_tighten_or_exclude` |
| `score_band` | `score_lt60` | 332 | 13 | -0.5682 | -1.8708 | 0.0769 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 646 | 70 | -0.7137 | -1.6771 | 0.1286 | `candidate_tighten_or_exclude` |
| `stale_bucket` | `fresh` | 735 | 70 | -0.7137 | -1.6771 | 0.1286 | `candidate_tighten_or_exclude` |
| `strength_bucket` | `weak_strength_momentum` | 681 | 59 | -0.7367 | -1.671 | 0.1186 | `candidate_tighten_or_exclude` |
| `time_bucket` | `time_1200_1400` | 267 | 31 | -0.8596 | -1.609 | 0.1613 | `candidate_tighten_or_exclude` |
| `time_bucket` | `time_1000_1200` | 302 | 20 | -0.5759 | -2.138 | 0.05 | `candidate_tighten_or_exclude` |
| `time_bucket` | `time_1400_close` | 65 | 11 | -0.8514 | -2.6727 | 0.0 | `candidate_tighten_or_exclude` |

### Entry Bucket Runtime Approval Candidates

- `entry_bucket_6`: `liquidity_bucket` / `liquidity_high` -> `candidate_tighten_or_exclude`
- `entry_bucket_7`: `overbought_bucket` / `overbought_normal` -> `candidate_tighten_or_exclude`
- `entry_bucket_9`: `score_band` / `score_60_62` -> `candidate_tighten_or_exclude`
- `entry_bucket_11`: `source_stage` / `scalp_entry_action_decision_snapshot` -> `candidate_tighten_or_exclude`
- `entry_bucket_12`: `stale_bucket` / `fresh` -> `candidate_tighten_or_exclude`
- `entry_bucket_13`: `strength_bucket` / `weak_strength_momentum` -> `candidate_tighten_or_exclude`
- `entry_bucket_14`: `time_bucket` / `time_1200_1400` -> `candidate_tighten_or_exclude`
- `entry_bucket_15`: `time_bucket` / `time_1000_1200` -> `candidate_tighten_or_exclude`

### Entry Bucket Workorders

- `entry_bucket_source_quality_1`: `chosen_action` / `NO_BUY_AI` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_2`: `combo_entry_spot` / `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_3`: `combo_entry_spot` / `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_4`: `exit_rule` / `scalp_soft_stop_pct` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_5`: `exit_rule` / `scalp_hard_stop_pct` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_6`: `liquidity_bucket` / `liquidity_high` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_7`: `overbought_bucket` / `overbought_normal` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_8`: `overbought_bucket` / `overbought_ok` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_9`: `score_band` / `score_60_62` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_10`: `score_band` / `score_lt60` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`

## Submit Bucket Attribution

- decision_authority: `adm_ldm_submit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'submit_rows': 789, 'bucket_count': 83, 'contract_gap_count': 0, 'workorder_count': 0, 'runtime_candidate_count': 0, 'real_submitted_row_count': 17, 'missing_broker_order_key_count': 0, 'bot_history_broker_order_key_backfill_candidate_count': 0, 'bot_history_broker_order_key_backfill_full_coverage': False, 'bot_history_broker_order_key_exact_mapping_count': 0, 'bot_history_broker_order_key_exact_mapping_full_coverage': False, 'post_submit_provenance_join_resolution': 'no_gap_broker_order_key_present_or_no_missing_rows', 'bot_history_broker_order_key_backfill_candidates': [], 'missing_broker_order_key_rate': 0.0, 'post_submit_provenance_join_gap_raw': False, 'post_submit_provenance_join_gap': False}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 772 | 254 | -0.9965 | `keep_collecting` |
| `actual_order_submitted` | `true` | 17 | 0 | None | `keep_collecting` |
| `broker_order_forbidden` | `true` | 772 | 254 | -0.9965 | `keep_collecting` |
| `broker_order_forbidden` | `false` | 17 | 0 | None | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 203 | 93 | -1.5686 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 189 | 60 | -0.6432 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 88 | 24 | -0.5052 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=false|submitted=false` | 63 | 17 | 0.0221 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 49 | 19 | -1.5705 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 43 | 22 | -0.2855 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_unknown|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=would_unknown|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 31 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=block_False|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=latency_unknown|fill=false|submitted=false` | 27 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=block_False|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=latency_unknown|fill=false|submitted=true` | 16 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=pre_submit_liquidity_guard_block|revalidation=block_False|quote_age=quote_age_unknown|liquidity=below_min_liquidity|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=latency_unknown|fill=false|submitted=false` | 15 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 12 | 5 | -1.6169 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 10 | 4 | -0.9855 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=false|submitted=false` | 6 | 1 | -0.727 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 5 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 5 | 1 | 0.3904 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=pullback_or_rebreak_not_confirmed|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 4 | 2 | -3.7949 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_overbought_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=pullback_or_rebreak_not_confirmed|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 4 | 1 | -4.4414 | `source_quality_workorder` |
| `combo_submit_quality` | `source=pre_submit_liquidity_guard_block|revalidation=block_False|quote_age=quote_age_unknown|liquidity=below_min_liquidity|liquidity_guard=liquidity_guard_unknown|overbought=pullback_required|latency=latency_unknown|fill=false|submitted=false` | 3 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=pullback_or_rebreak_not_confirmed|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 3 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=pre_submit_overbought_pullback_guard_block|revalidation=block_False|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=pullback_required|latency=latency_unknown|fill=false|submitted=false` | 2 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 2 | 1 | 0.0455 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 2 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_overbought_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=pullback_or_rebreak_not_confirmed|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 2 | 1 | -3.2839 | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=block_False|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_ok|latency=latency_unknown|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=true|submitted=false` | 1 | 1 | 0.0555 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | 2.0186 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_lt1s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | 4.8007 | `source_quality_workorder` |
| `latency_reason` | `scalp_live_simulator` | 725 | 254 | -0.9965 | `keep_collecting` |
| `latency_reason` | `latency_reason_unknown` | 64 | 0 | None | `source_quality_workorder` |
| `latency_state` | `simulated` | 725 | 254 | -0.9965 | `keep_collecting` |
| `latency_state` | `latency_unknown` | 64 | 0 | None | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_ok` | 362 | 107 | -0.5297 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 350 | 147 | -1.3362 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_not_available` | 77 | 0 | None | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 362 | 107 | -0.5297 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 744, 'source_row_count': 744, 'bucket_count': 38, 'joined_sample': 1270, 'source_quality_adjusted_ev_pct': -1.3986, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 162 | 162 | -1.6837 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 30 | 30 | -1.7873 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 28 | 28 | -1.815 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 9 | 9 | 0.6912 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 9 | 9 | 0.3256 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 4 | 4 | 2.1673 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 3 | 3 | -0.4633 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 3 | 3 | 1.8371 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 2 | 2 | -0.6854 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 1.2647 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | 1.0318 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 1 | 1 | -1.5394 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 0.64 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 20 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 92 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 359 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 7 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 5 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos080_pos150|held=held_600_1800s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_not_applicable_at_start` | 725 | 254 | -1.3986 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s` | 13 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 6 | 0 | None | `hold_sample` |
| `holding_action` | `holding_action_not_applicable_at_start` | 546 | 187 | -1.3842 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 130 | 38 | -1.2323 | `candidate_tighten_or_exclude` |
| `holding_action` | `BUY` | 49 | 29 | -1.7088 | `candidate_tighten_or_exclude` |
| `holding_action` | `SELL_TODAY` | 19 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 725 | 254 | -1.3986 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 19 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 232 | 220 | -1.7146 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 12 | 10 | 0.7253 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300` | 10 | 10 | 0.1391 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300_plus` | 7 | 7 | 2.0258 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 9 | 5 | -0.5522 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 3 | 2 | 0.9524 | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 471 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- `holding_bucket_source_quality_1`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_2`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_3`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_4`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_5`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_6`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_7`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_8`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_9`: `held_bucket` / `held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_10`: `holding_action` / `holding_action_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Exit Bucket Attribution

- decision_authority: `adm_ldm_exit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'exit_rows': 1145, 'source_row_count': 1145, 'bucket_count': 49, 'joined_sample': 1125, 'source_quality_adjusted_ev_pct': -1.4312, 'source_quality_gate': 'pass', 'unknown_reason_counts': {'not_applicable': 4, 'join_gap': 8, 'missing_source_field': 1}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 40 | 40 | -2.1881 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 37 | 37 | -1.7132 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 29 | 29 | -1.4455 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 27 | 27 | -2.6418 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 24 | 24 | -1.4407 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 12 | 12 | -0.8469 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 9 | 9 | -1.9678 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 9 | 9 | -0.4114 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 6 | 6 | -0.2623 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 4 | 4 | -0.3244 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 4 | 4 | -1.3068 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 4 | 4 | -0.9544 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 3 | 3 | 1.6269 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 3 | 3 | 1.1541 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos080_pos150` | 2 | 2 | 0.96 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 2 | 2 | 1.2186 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 2 | 2 | 1.4689 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 2 | 2 | 0.0081 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 1 | 1 | 0.48 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_neg070_neg010` | 1 | 1 | -1.0308 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_protect_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 1 | 1 | 1.2647 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_preset_tp_touch|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 1 | 1 | 3.9511 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 1 | 1 | 0.3887 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300` | 1 | 1 | -0.4972 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_euphoria_context_noop|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown` | 673 | 0 | None | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown` | 247 | 0 | None | `source_quality_workorder` |
| `exit_outcome` | `GOOD_EXIT` | 82 | 82 | -1.9685 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 74 | 74 | -1.1855 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 50 | 50 | -1.2763 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 939 | 19 | -0.4768 | `source_quality_workorder` |
| `exit_rule` | `scalp_soft_stop_pct` | 93 | 93 | -1.7637 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 73 | 73 | -2.088 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 20 | 20 | 0.6026 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 19 | 19 | -0.4768 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 18 | 18 | -0.7655 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_preset_protect_profit` | 1 | 1 | 1.2647 | `hold_sample` |
| `exit_rule` | `scalp_sim_preset_tp_touch` | 1 | 1 | 3.9511 | `hold_sample` |
| `exit_rule` | `exit_rule_unknown` | 920 | 0 | None | `source_quality_workorder` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 206 | 206 | -1.5192 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 19 | 19 | -0.4768 | `candidate_tighten_or_exclude` |

### Exit Bucket Attribution Workorders

- `exit_bucket_source_quality_1`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_2`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_3`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_4`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_5`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_6`: `combo_exit_result` / `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_7`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_8`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_9`: `combo_exit_result` / `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_10`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `incremental_notional_ev_pct`
- summary: `{'scale_in_rows': 15716, 'bucket_count': 1585, 'actionable_bucket_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'arm_counts': {'PYRAMID': 3043, 'AVG_DOWN': 12673}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_70p` | 6266 | 6266 | None | -0.5112 | 0.1741 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 3369 | 3369 | None | -0.5505 | 0.1677 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 3164 | 3164 | None | -0.3746 | 0.2083 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 1508 | 1508 | None | -0.6093 | 0.1545 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 895 | 895 | None | -0.8314 | 0.1553 | `hold_sample` |
| `ai_score_band` | `score_unknown` | 514 | 6 | None | 1.47 | 1.0 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 15202 | 15202 | None | -0.5201 | 0.1768 | `hold_sample` |
| `ai_score_source` | `sim_scale_in_source_not_scored` | 7 | 6 | None | 1.47 | 1.0 | `hold_sample` |
| `ai_score_source` | `stage_rule_backfilled` | 507 | 0 | None | None | None | `hold_sample` |
| `arm` | `AVG_DOWN` | 12673 | 12487 | None | -0.8217 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 3043 | 2721 | None | 0.8675 | 0.9897 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 8630 | 8444 | None | -1.0149 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 4043 | 4043 | None | -0.4181 | 0.0 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 3043 | 2721 | None | 0.8675 | 0.9897 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 2265 | 2265 | None | 0.4991 | 0.9907 | `hold_sample` |
| `blocker_reason` | `low_broken` | 530 | 530 | None | -0.4681 | 0.0 | `hold_sample` |
| `blocker_reason` | `add_judgment_locked` | 368 | 368 | None | -0.3391 | 0.1467 | `hold_sample` |
| `blocker_reason` | `scalping_pyramid_ok` | 303 | 303 | None | 3.7077 | 1.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.86)` | 211 | 211 | None | -0.86 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_scale_in_window_expansion` | 180 | 180 | None | -0.5163 | 0.1611 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `adm_ldm_overnight_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'overnight_rows': 38, 'bucket_count': 27, 'actionable_bucket_count': 12, 'runtime_candidate_count': 10, 'workorder_count': 10, 'status_counts': {'HOLD_OVERNIGHT': 19, 'SELL_TODAY': 19}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 12 | 12 | -0.8469 | -1.1292 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 4 | 4 | -0.3244 | -0.4325 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 2 | 2 | 0.96 | 1.28 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 1 | 1 | 0.48 | 0.64 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_lt_neg070` | 12 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg010_pos080` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 4 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_pos080_pos150` | 2 | 0 | None | None | None | `hold_sample` |
| `confidence_band` | `confidence_070p` | 38 | 19 | -0.4768 | -0.6358 | 0.1579 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s` | 26 | 13 | -0.3565 | -0.4754 | 0.2308 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s_plus` | 12 | 6 | -0.7375 | -0.9833 | 0.0 | `candidate_tighten_or_exclude` |
| `overnight_action` | `SELL_TODAY` | 38 | 19 | -0.4768 | -0.6358 | 0.1579 | `candidate_tighten_or_exclude` |
| `overnight_status` | `SELL_TODAY` | 19 | 19 | -0.4768 | -0.6358 | 0.1579 | `candidate_tighten_or_exclude` |
| `overnight_status` | `HOLD_OVERNIGHT` | 19 | 0 | None | None | None | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 32 | 16 | -0.7163 | -0.955 | 0.0 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_pos080_pos150` | 4 | 2 | 0.96 | 1.28 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 2 | 1 | 0.48 | 0.64 | 1.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 38 | 19 | -0.4768 | -0.6358 | 0.1579 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 24 | 12 | -0.8469 | -1.1292 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 8 | 4 | -0.3244 | -0.4325 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 38 | 19 | -0.4768 | -0.6358 | 0.1579 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 19 | 19 | -0.4768 | -0.6358 | 0.1579 | `candidate_tighten_or_exclude` |
| `stage` | `exit` | 19 | 19 | -0.4768 | -0.6358 | 0.1579 | `candidate_tighten_or_exclude` |

### Overnight Bucket Runtime Approval Candidates

- `overnight_bucket_1`: `combo_overnight_decision` / `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` -> `candidate_tighten_or_exclude`
- `overnight_bucket_2`: `confidence_band` / `confidence_070p` -> `candidate_tighten_or_exclude`
- `overnight_bucket_3`: `held_bucket` / `held_600_1800s` -> `candidate_tighten_or_exclude`
- `overnight_bucket_5`: `overnight_action` / `SELL_TODAY` -> `candidate_tighten_or_exclude`
- `overnight_bucket_6`: `overnight_status` / `SELL_TODAY` -> `candidate_tighten_or_exclude`
- `overnight_bucket_7`: `peak_profit_band` / `peak_lt_zero` -> `candidate_tighten_or_exclude`
- `overnight_bucket_8`: `price_source` / `holding_price_samples_last` -> `candidate_tighten_or_exclude`
- `overnight_bucket_9`: `profit_band` / `profit_lt_neg070` -> `candidate_tighten_or_exclude`
- `overnight_bucket_10`: `source_quality_gate` / `overnight_decision_coverage` -> `candidate_tighten_or_exclude`
- `overnight_bucket_11`: `source_stage` / `scalp_sim_overnight_sell_today` -> `candidate_tighten_or_exclude`

### Overnight Bucket Workorders

- `overnight_bucket_source_quality_1`: `combo_overnight_decision` / `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_2`: `confidence_band` / `confidence_070p` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_3`: `held_bucket` / `held_600_1800s` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_4`: `held_bucket` / `held_600_1800s_plus` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_5`: `overnight_action` / `SELL_TODAY` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_6`: `overnight_status` / `SELL_TODAY` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_7`: `peak_profit_band` / `peak_lt_zero` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_8`: `price_source` / `holding_price_samples_last` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_9`: `profit_band` / `profit_lt_neg070` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_10`: `source_quality_gate` / `overnight_decision_coverage` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`

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
