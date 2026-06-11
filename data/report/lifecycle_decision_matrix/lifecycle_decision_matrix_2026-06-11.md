# Lifecycle Decision Matrix - 2026-06-11

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-11`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `16418`
- source_rows_total: `24739`
- retained_rows: `16418`
- dropped_rows_by_source: `{'dedupe': 8321}`
- joined_rows: `14853`
- policy_pass_count: `5`
- promote_ready_count: `0`
- entry_bucket_actionable_count: `26`
- entry_bucket_runtime_candidate_count: `10`
- holding_bucket_count/workorders: `41` / `10`
- exit_bucket_count/workorders: `54` / `10`
- scale_in_bucket_actionable_count: `232`
- scale_in_bucket_runtime_candidate_count: `10`
- overnight_bucket_actionable_count: `5`
- overnight_bucket_runtime_candidate_count: `3`
- lifecycle_flow_bucket_count: `150`
- lifecycle_flow_complete_count: `108`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `0` / `108` / `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0075`
- incomplete_flow_reason_counts: `{'missing_entry': 13855, 'missing_holding': 14298, 'missing_exit': 13341, 'missing_submit': 14305, 'postclose_exit_without_entry': 1008, 'candidate_id_only': 13842, 'scale_in_noise_only': 12816, 'sim_record_id_only': 432}`
- bucket_directed_sim_probe: `{'observed_row_count': 2748, 'matched_row_count': 1264, 'background_row_count': 1484, 'matched_unique_source_bucket_count': 4, 'match_status_counts': {'matched': 1264, 'no_match': 408, 'not_instrumented': 1076}, 'matched_classification_state_counts': {'lifecycle_flow_sim_probe_candidate': 1264}, 'primary_source': 'matched_bucket_directed_sim_probe_only', 'background_source': 'unmatched_or_policy_missing_sim_observation', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 0, 'route_counts': {'bounded_auxiliary_weight': 1, 'hold_sample': 4}, 'quality_counts': {'observational_only_pending_outcome': 1, 'hold_sample': 4}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 925 | 179 | -0.1736 | 1.0 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 494 | 387 | -0.8277 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 475 | 387 | -0.7377 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 13188 | 13187 | -0.3151 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 1336 | 713 | -0.8561 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 14457, 'complete_flow_count': 108, 'direct_sim_record_complete_flow_count': 0, 'adm_bridge_complete_flow_count': 108, 'fallback_complete_flow_count': 0, 'incomplete_flow_count': 14349, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 16418, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0075, 'complete_flow_conversion_denominator': 1147, 'complete_flow_conversion_rate': 0.0942, 'active_priority_incomplete_seed_count': 494, 'scale_in_followup_event_count': 13188, 'scale_in_unique_flow_count': 12094, 'scale_in_noise_flow_count': 12816, 'denominator_exclusion_counts': {'scale_in_noise_flow_excluded': 12816, 'active_priority_incomplete_seed_excluded': 494}, 'conversion_blocker_reason_counts': {'missing_entry': 1039, 'missing_holding': 998, 'missing_exit': 31, 'postclose_exit_without_entry': 1008, 'missing_submit': 1006, 'sim_record_id_only': 383, 'candidate_id_only': 623}, 'observation_seed_reason_counts': {'missing_submit': 13299, 'missing_holding': 13300, 'missing_exit': 13310, 'candidate_id_only': 13219, 'missing_entry': 12816, 'scale_in_noise_only': 12816, 'sim_record_id_only': 49}, 'join_contract_blocked': False, 'bundle_ev_tuning_state': 'ready_for_bundle_ev_tuning', 'top_incomplete_reason': 'missing_submit', 'stage_identity': {'entry': {'source_row_count': 925, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 473, 'candidate_id': 452}, 'identity_join_rate': 1.0}, 'submit': {'source_row_count': 494, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 494}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 475, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 436, 'exact_sim_record_id': 39}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 13188, 'identity_missing_count': 0, 'identity_quality_counts': {'candidate_id': 12767, 'exact_sim_record_id': 421}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 1336, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 299, 'exact_sim_record_id': 414, 'candidate_id': 623}, 'identity_join_rate': 1.0}}, 'required_stage_source_counts': {'entry': 925, 'submit': 494, 'holding': 475, 'exit': 1336}, 'incomplete_flow_reason_counts': {'missing_entry': 13855, 'missing_holding': 14298, 'missing_exit': 13341, 'missing_submit': 14305, 'postclose_exit_without_entry': 1008, 'candidate_id_only': 13842, 'scale_in_noise_only': 12816, 'sim_record_id_only': 432}, 'bucket_count': 150, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9d8cac316e` | 3 | 3 | -0.1989 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:f7df4238eb` | 3 | 3 | 0.9512 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:be2863195a` | 2 | 2 | -0.2021 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:84b7dde4a3` | 2 | 2 | -1.311 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9c99306a62` | 2 | 2 | -2.3639 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:3cbb81cd02` | 2 | 2 | -1.0778 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:a2a88f9390` | 2 | 2 | -2.0692 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:545378fef0` | 2 | 2 | -1.7107 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:bdf988029a` | 2 | 2 | 2.1971 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:7d18e006c3` | 2 | 2 | 4.6411 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:21510b4932` | 2 | 2 | 0.2805 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:0b047ad72e` | 1 | 1 | 0.4452 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:00f1a930ff` | 1 | 1 | -1.4926 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:f20e597db1` | 1 | 1 | -0.6075 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:7f4b207c82` | 1 | 1 | 1.0981 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:f1c1fcc930` | 1 | 1 | -0.9733 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:77748d3150` | 1 | 1 | -0.8868 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:d4987d75cf` | 1 | 1 | -1.5394 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:717323c912` | 1 | 1 | -0.6898 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:ce5051d3e3` | 1 | 1 | 0.6609 | `candidate_recovery_or_relax` | `pass` |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 925, 'bucket_count': 190, 'actionable_bucket_count': 26, 'source_quality_blocked_bucket_count': 0, 'runtime_candidate_count': 10, 'workorder_count': 10}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `NO_BUY_AI` | 463 | 103 | -0.8781 | -0.8827 | 0.3786 | `candidate_tighten_or_exclude` |
| `chosen_action` | `WAIT_REQUOTE` | 73 | 73 | 0.8699 | 1.6613 | 0.6712 | `candidate_recovery_or_relax` |
| `chosen_action` | `BUY_NOW` | 6 | 3 | -1.3813 | 1.4967 | 0.6667 | `hold_sample` |
| `chosen_action` | `ALLOW_BOTTOMING_ENTRY` | 32 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `ALLOW_LEVEL1_RISK_OFF_ENTRY` | 347 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_SOURCE_QUALITY` | 4 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 18 | 18 | 1.1815 | 2.0139 | 0.7778 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 59 | 13 | -0.4934 | -1.3069 | 0.2308 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 36 | 13 | -0.7221 | -0.0208 | 0.5385 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 33 | 10 | 0.6663 | -0.414 | 0.5 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 8 | 8 | 1.9006 | 2.7043 | 0.875 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 8 | 8 | 2.604 | 3.8751 | 0.875 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_ok|time=time_1200_1400` | 13 | 7 | -4.0162 | 0.0414 | 0.5714 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1400_close` | 19 | 6 | -0.4432 | -0.72 | 0.3333 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_ok|time=time_1400_close` | 14 | 6 | -3.7162 | -1.565 | 0.3333 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 6 | 6 | 1.9658 | 3.5685 | 0.8333 | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 6 | 6 | -0.5673 | -0.9519 | 0.5 | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_ok|time=time_1000_1200` | 6 | 6 | 1.0141 | 2.6804 | 0.5 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 19 | 6 | -0.5487 | -0.875 | 0.5 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_ok|time=time_1000_1200` | 16 | 5 | -0.9907 | -2.312 | 0.0 | `hold_sample` |
| `exit_rule` | `exit_unknown` | 819 | 73 | 0.8699 | 1.6613 | 0.6712 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_trailing_take_profit` | 41 | 41 | -1.4043 | 1.7795 | 1.0 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 36 | 36 | -0.7445 | -2.0522 | 0.0 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 29 | 29 | -0.352 | -2.9486 | 0.0 | `candidate_tighten_or_exclude` |
| `liquidity_bucket` | `liquidity_high` | 471 | 179 | -0.1736 | 0.1947 | 0.5028 | `hold_no_edge` |
| `overbought_bucket` | `overbought_normal` | 332 | 104 | 0.2718 | 0.3579 | 0.5481 | `hold_no_edge` |
| `overbought_bucket` | `overbought_ok` | 91 | 40 | -2.0965 | -0.6077 | 0.375 | `candidate_tighten_or_exclude` |
| `overbought_bucket` | `overbought_watch` | 109 | 33 | 0.6265 | 0.5316 | 0.5152 | `candidate_recovery_or_relax` |
| `score_band` | `score_60_62` | 544 | 66 | -1.0049 | -0.6715 | 0.3939 | `candidate_tighten_or_exclude` |
| `score_band` | `score_66_69` | 61 | 39 | 0.2927 | 0.6062 | 0.5641 | `hold_no_edge` |
| `score_band` | `score_70p` | 86 | 35 | 0.9416 | 1.9617 | 0.6571 | `candidate_recovery_or_relax` |
| `score_band` | `score_63_65` | 87 | 23 | -0.1442 | 0.0969 | 0.5217 | `hold_no_edge` |
| `score_band` | `score_lt60` | 147 | 16 | -0.3634 | -0.96 | 0.4375 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 348 | 106 | -0.8923 | -0.8154 | 0.3868 | `candidate_tighten_or_exclude` |
| `source_stage` | `wait6579_ev_cohort` | 73 | 73 | 0.8699 | 1.6613 | 0.6712 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh` | 421 | 106 | -0.8923 | -0.8154 | 0.3868 | `candidate_tighten_or_exclude` |
| `stale_bucket` | `fresh_or_unflagged` | 452 | 73 | 0.8699 | 1.6613 | 0.6712 | `candidate_recovery_or_relax` |
| `strength_bucket` | `weak_strength_momentum` | 385 | 93 | -0.7027 | -0.8405 | 0.3871 | `candidate_tighten_or_exclude` |
| `strength_bucket` | `strong_strength_momentum` | 117 | 75 | 0.6228 | 1.3137 | 0.6267 | `candidate_recovery_or_relax` |
| `strength_bucket` | `neutral_strength_momentum` | 44 | 11 | -1.1306 | 1.317 | 0.6364 | `candidate_tighten_or_exclude` |

### Entry Bucket Runtime Approval Candidates

- `entry_bucket_11`: `overbought_bucket` / `overbought_ok` -> `candidate_tighten_or_exclude`
- `entry_bucket_12`: `overbought_bucket` / `overbought_watch` -> `candidate_recovery_or_relax`
- `entry_bucket_13`: `score_band` / `score_60_62` -> `candidate_tighten_or_exclude`
- `entry_bucket_14`: `score_band` / `score_70p` -> `candidate_recovery_or_relax`
- `entry_bucket_16`: `source_stage` / `scalp_entry_action_decision_snapshot` -> `candidate_tighten_or_exclude`
- `entry_bucket_17`: `source_stage` / `wait6579_ev_cohort` -> `candidate_recovery_or_relax`
- `entry_bucket_18`: `stale_bucket` / `fresh` -> `candidate_tighten_or_exclude`
- `entry_bucket_19`: `stale_bucket` / `fresh_or_unflagged` -> `candidate_recovery_or_relax`
- `entry_bucket_20`: `strength_bucket` / `weak_strength_momentum` -> `candidate_tighten_or_exclude`
- `entry_bucket_21`: `strength_bucket` / `strong_strength_momentum` -> `candidate_recovery_or_relax`

### Entry Bucket Workorders

- `entry_bucket_source_quality_1`: `chosen_action` / `NO_BUY_AI` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_2`: `chosen_action` / `WAIT_REQUOTE` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_3`: `combo_entry_spot` / `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_4`: `combo_entry_spot` / `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_5`: `combo_entry_spot` / `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_6`: `combo_entry_spot` / `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_7`: `exit_rule` / `exit_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_8`: `exit_rule` / `scalp_trailing_take_profit` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_9`: `exit_rule` / `scalp_soft_stop_pct` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_10`: `exit_rule` / `scalp_hard_stop_pct` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`

## Submit Bucket Attribution

- decision_authority: `adm_ldm_submit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'submit_rows': 494, 'bucket_count': 68, 'contract_gap_count': 1, 'workorder_count': 1, 'runtime_candidate_count': 0, 'real_submitted_row_count': 17, 'missing_broker_order_key_count': 17, 'bot_history_broker_order_key_backfill_candidate_count': 17, 'bot_history_broker_order_key_backfill_full_coverage': True, 'bot_history_broker_order_key_backfill_candidates': [{'stock_code': '011070', 'event_time': '2026-06-11T10:03:24.667092', 'candidate_count': 2, 'best_candidate': {'broker_order_no': '0029982', 'bot_history_event_time': '2026-06-11 10:03:19', 'status': '접수', 'delta_sec': 5}, 'match_policy': 'same_stock_within_180s_bot_history_ws_buy_order'}, {'stock_code': '222800', 'event_time': '2026-06-11T10:58:43.483563', 'candidate_count': 3, 'best_candidate': {'broker_order_no': '0039477', 'bot_history_event_time': '2026-06-11 10:58:37', 'status': '접수', 'delta_sec': 6}, 'match_policy': 'same_stock_within_180s_bot_history_ws_buy_order'}, {'stock_code': '240810', 'event_time': '2026-06-11T11:01:50.254829', 'candidate_count': 2, 'best_candidate': {'broker_order_no': '0039885', 'bot_history_event_time': '2026-06-11 11:01:45', 'status': '접수', 'delta_sec': 5}, 'match_policy': 'same_stock_within_180s_bot_history_ws_buy_order'}, {'stock_code': '009150', 'event_time': '2026-06-11T11:05:34.240301', 'candidate_count': 2, 'best_candidate': {'broker_order_no': '0040256', 'bot_history_event_time': '2026-06-11 11:05:30', 'status': '접수', 'delta_sec': 4}, 'match_policy': 'same_stock_within_180s_bot_history_ws_buy_order'}, {'stock_code': '095610', 'event_time': '2026-06-11T11:40:33.617551', 'candidate_count': 2, 'best_candidate': {'broker_order_no': '0044567', 'bot_history_event_time': '2026-06-11 11:40:29', 'status': '접수', 'delta_sec': 4}, 'match_policy': 'same_stock_within_180s_bot_history_ws_buy_order'}, {'stock_code': '001820', 'event_time': '2026-06-11T11:42:06.269320', 'candidate_count': 2, 'best_candidate': {'broker_order_no': '0044725', 'bot_history_event_time': '2026-06-11 11:42:02', 'status': '접수', 'delta_sec': 4}, 'match_policy': 'same_stock_within_180s_bot_history_ws_buy_order'}, {'stock_code': '086520', 'event_time': '2026-06-11T11:43:00.887617', 'candidate_count': 2, 'best_candidate': {'broker_order_no': '0044827', 'bot_history_event_time': '2026-06-11 11:42:56', 'status': '접수', 'delta_sec': 4}, 'match_policy': 'same_stock_within_180s_bot_history_ws_buy_order'}, {'stock_code': '084370', 'event_time': '2026-06-11T11:44:52.169348', 'candidate_count': 2, 'best_candidate': {'broker_order_no': '0045014', 'bot_history_event_time': '2026-06-11 11:44:48', 'status': '접수', 'delta_sec': 4}, 'match_policy': 'same_stock_within_180s_bot_history_ws_buy_order'}, {'stock_code': '007660', 'event_time': '2026-06-11T11:48:25.329305', 'candidate_count': 2, 'best_candidate': {'broker_order_no': '0045364', 'bot_history_event_time': '2026-06-11 11:48:21', 'status': '접수', 'delta_sec': 4}, 'match_policy': 'same_stock_within_180s_bot_history_ws_buy_order'}, {'stock_code': '000660', 'event_time': '2026-06-11T12:06:03.869069', 'candidate_count': 2, 'best_candidate': {'broker_order_no': '0047102', 'bot_history_event_time': '2026-06-11 12:05:59', 'status': '접수', 'delta_sec': 4}, 'match_policy': 'same_stock_within_180s_bot_history_ws_buy_order'}, {'stock_code': '402340', 'event_time': '2026-06-11T12:08:01.854923', 'candidate_count': 2, 'best_candidate': {'broker_order_no': '0047324', 'bot_history_event_time': '2026-06-11 12:07:57', 'status': '접수', 'delta_sec': 4}, 'match_policy': 'same_stock_within_180s_bot_history_ws_buy_order'}, {'stock_code': '007810', 'event_time': '2026-06-11T12:23:47.266539', 'candidate_count': 2, 'best_candidate': {'broker_order_no': '0048868', 'bot_history_event_time': '2026-06-11 12:23:43', 'status': '접수', 'delta_sec': 4}, 'match_policy': 'same_stock_within_180s_bot_history_ws_buy_order'}, {'stock_code': '125490', 'event_time': '2026-06-11T12:30:33.145429', 'candidate_count': 2, 'best_candidate': {'broker_order_no': '0049507', 'bot_history_event_time': '2026-06-11 12:30:37', 'status': '체결', 'delta_sec': 3}, 'match_policy': 'same_stock_within_180s_bot_history_ws_buy_order'}, {'stock_code': '131970', 'event_time': '2026-06-11T12:35:00.465200', 'candidate_count': 2, 'best_candidate': {'broker_order_no': '0049916', 'bot_history_event_time': '2026-06-11 12:34:55', 'status': '접수', 'delta_sec': 5}, 'match_policy': 'same_stock_within_180s_bot_history_ws_buy_order'}, {'stock_code': '222800', 'event_time': '2026-06-11T12:44:05.556730', 'candidate_count': 2, 'best_candidate': {'broker_order_no': '0050687', 'bot_history_event_time': '2026-06-11 12:44:01', 'status': '접수', 'delta_sec': 4}, 'match_policy': 'same_stock_within_180s_bot_history_ws_buy_order'}, {'stock_code': '093370', 'event_time': '2026-06-11T12:45:25.453824', 'candidate_count': 2, 'best_candidate': {'broker_order_no': '0050835', 'bot_history_event_time': '2026-06-11 12:45:21', 'status': '접수', 'delta_sec': 4}, 'match_policy': 'same_stock_within_180s_bot_history_ws_buy_order'}, {'stock_code': '222800', 'event_time': '2026-06-11T13:29:17.652123', 'candidate_count': 2, 'best_candidate': {'broker_order_no': '0055115', 'bot_history_event_time': '2026-06-11 13:29:12', 'status': '접수', 'delta_sec': 5}, 'match_policy': 'same_stock_within_180s_bot_history_ws_buy_order'}], 'missing_broker_order_key_rate': 1.0, 'post_submit_provenance_join_gap': True}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 477 | 387 | -0.8277 | `keep_collecting` |
| `actual_order_submitted` | `true` | 17 | 0 | None | `keep_collecting` |
| `broker_order_forbidden` | `true` | 477 | 387 | -0.8277 | `keep_collecting` |
| `broker_order_forbidden` | `false` | 17 | 0 | None | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 150 | 138 | -0.8426 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 134 | 119 | -0.9234 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=false|submitted=false` | 34 | 28 | -0.3164 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 33 | 25 | -0.638 | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=block_False|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=latency_unknown|fill=false|submitted=false` | 31 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 29 | 25 | -0.7004 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 20 | 19 | -0.4661 | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=block_False|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=latency_unknown|fill=false|submitted=true` | 12 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=pre_submit_liquidity_guard_block|revalidation=block_False|quote_age=quote_age_unknown|liquidity=below_min_liquidity|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=latency_unknown|fill=false|submitted=false` | 7 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=false|submitted=false` | 7 | 7 | -2.6337 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 6 | 6 | -0.11 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_overbought_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=pullback_or_rebreak_not_confirmed|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 6 | 6 | -2.5079 | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=block_False|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_ok|latency=latency_unknown|fill=false|submitted=true` | 5 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 5 | 5 | -1.4108 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 4 | 3 | -0.8403 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=pullback_or_rebreak_not_confirmed|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 4 | 3 | 1.1737 | `source_quality_workorder` |
| `combo_submit_quality` | `source=pre_submit_liquidity_guard_block|revalidation=block_False|quote_age=quote_age_unknown|liquidity=below_min_liquidity|liquidity_guard=liquidity_guard_unknown|overbought=pullback_required|latency=latency_unknown|fill=false|submitted=false` | 2 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 2 | 1 | 0.518 | `source_quality_workorder` |
| `combo_submit_quality` | `source=pre_submit_liquidity_guard_block|revalidation=block_False|quote_age=quote_age_unknown|liquidity=below_min_liquidity|liquidity_guard=liquidity_guard_unknown|overbought=overbought_ok|latency=latency_unknown|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_lt1s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | -0.74 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_overbought_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=pullback_or_rebreak_not_confirmed|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | -2.5614 | `source_quality_workorder` |
| `latency_reason` | `scalp_live_simulator` | 436 | 387 | -0.8277 | `keep_collecting` |
| `latency_reason` | `latency_reason_unknown` | 58 | 0 | None | `source_quality_workorder` |
| `latency_state` | `simulated` | 436 | 387 | -0.8277 | `keep_collecting` |
| `latency_state` | `latency_unknown` | 58 | 0 | None | `source_quality_workorder` |
| `liquidity_bucket` | `below_min_liquidity` | 233 | 200 | -0.7427 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 213 | 187 | -0.9186 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_not_available` | 48 | 0 | None | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 223 | 200 | -0.7427 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 213 | 187 | -0.9186 | `keep_collecting` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 58 | 0 | None | `source_quality_workorder` |
| `overbought_bucket` | `overbought_ok` | 364 | 319 | -0.8938 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 67 | 58 | -0.3641 | `keep_collecting` |
| `overbought_bucket` | `overbought_not_available` | 50 | 0 | None | `keep_collecting` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 11 | 10 | -1.4088 | `keep_collecting` |
| `overbought_bucket` | `pullback_required` | 2 | 0 | None | `keep_collecting` |

### Submit Bucket Workorders

- `order_entry_post_submit_provenance_join_gap`: `post_submit_provenance_join_gap` / `submitted_exists_broker_order_key_missing` -> `submitted_exists_broker_order_key_missing`

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 475, 'source_row_count': 475, 'bucket_count': 41, 'joined_sample': 1935, 'source_quality_adjusted_ev_pct': -0.7377, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 171 | 171 | -1.6064 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 49 | 49 | -1.3379 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 35 | 35 | -0.254 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 29 | 29 | -0.3036 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 23 | 23 | 0.8203 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 19 | 19 | -0.0374 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 17 | 17 | 0.3484 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 12 | 12 | 2.5074 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 12 | 12 | 1.5569 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 8 | 8 | -0.395 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 6 | 6 | 0.0871 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 3 | 3 | 0.7116 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1 | 1 | -1.3626 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | -0.2245 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 1.7039 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 7 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 42 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 12 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 8 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 9 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos080_pos150|held=held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos150_pos300_plus|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos150_pos300|held=held_600_1800s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_not_applicable_at_start` | 436 | 387 | -0.7377 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s` | 7 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 32 | 0 | None | `hold_sample` |
| `holding_action` | `holding_action_not_applicable_at_start` | 316 | 274 | -1.013 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 114 | 107 | -0.0949 | `hold_no_edge` |
| `holding_action` | `BUY` | 6 | 6 | 0.3753 | `candidate_recovery_or_relax` |
| `holding_action` | `SELL_TODAY` | 39 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 436 | 387 | -0.7377 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 39 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 236 | 221 | -1.5457 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 55 | 53 | -0.0602 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 47 | 45 | 0.4509 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg010_pos080` | 45 | 35 | -0.2366 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300_plus` | 26 | 25 | 2.019 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 17 | 8 | -0.395 | `candidate_tighten_or_exclude` |

### Holding Bucket Attribution Workorders

- `holding_bucket_source_quality_1`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_2`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_3`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_4`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_5`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_6`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_7`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_8`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_9`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_10`: `held_bucket` / `held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Exit Bucket Attribution

- decision_authority: `adm_ldm_exit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'exit_rows': 1336, 'source_row_count': 1336, 'bucket_count': 54, 'joined_sample': 3565, 'source_quality_adjusted_ev_pct': -0.8561, 'source_quality_gate': 'pass', 'unknown_reason_counts': {'not_applicable': 6, 'join_gap': 8, 'missing_source_field': 1}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 274 | 274 | -1.205 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 86 | 86 | -0.5243 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 43 | 43 | -1.821 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 39 | 39 | -1.4536 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 37 | 37 | -1.4453 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 31 | 31 | -1.0554 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 24 | 24 | -2.2471 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 18 | 18 | 0.1477 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 15 | 15 | -0.9525 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 14 | 14 | 1.0145 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 13 | 13 | -0.7204 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 13 | 13 | 0.017 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 12 | 12 | -1.8847 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 11 | 11 | -0.8983 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 10 | 10 | 0.2602 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 10 | 10 | 0.3647 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 9 | 9 | -0.3192 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 9 | 9 | 0.27 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 9 | 9 | 1.3713 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 9 | 9 | 1.9031 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 7 | 7 | 0.0431 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 5 | 5 | -0.2962 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos150_pos300` | 3 | 3 | 2.2567 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos150_pos300_plus` | 3 | 3 | 4.8672 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos080_pos150` | 2 | 2 | 1.0312 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos150_pos300` | 2 | 2 | 1.2675 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300` | 2 | 2 | 0.4415 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300_plus` | 2 | 2 | 4.6411 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos150_pos300_plus` | 1 | 1 | 8.79 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_euphoria_context_noop|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown` | 412 | 0 | None | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown` | 211 | 0 | None | `source_quality_workorder` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 375 | 375 | -0.9372 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 118 | 118 | -1.1566 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 110 | 110 | -0.4921 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 71 | 71 | -0.9463 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 662 | 39 | -0.03 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 375 | 375 | -0.9372 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 113 | 113 | 0.3534 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_soft_stop_pct` | 111 | 111 | -1.482 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 75 | 75 | -1.7765 | `candidate_tighten_or_exclude` |

### Exit Bucket Attribution Workorders

- `exit_bucket_source_quality_1`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_2`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_3`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_4`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_5`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_6`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_7`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_8`: `combo_exit_result` / `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_9`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_10`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'scale_in_rows': 13188, 'bucket_count': 1530, 'actionable_bucket_count': 232, 'runtime_candidate_count': 10, 'workorder_count': 10, 'arm_counts': {'AVG_DOWN': 9323, 'PYRAMID': 3865}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_70p` | 6060 | 6060 | -0.2812 | -0.3679 | 0.2972 | `hold_no_edge` |
| `ai_score_band` | `score_60_62` | 3014 | 3014 | -0.3297 | -0.3762 | 0.2595 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_66_69` | 2567 | 2567 | -0.3548 | -0.4277 | 0.2941 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_63_65` | 956 | 956 | -0.3577 | -0.4164 | 0.2678 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_lt60` | 590 | 590 | -0.3473 | -0.424 | 0.2458 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_unknown` | 1 | 0 | None | None | None | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 13187 | 13187 | -0.3151 | -0.3875 | 0.2835 | `candidate_tighten_or_exclude` |
| `ai_score_source` | `stage_rule_backfilled` | 1 | 0 | None | None | None | `hold_sample` |
| `arm` | `AVG_DOWN` | 9323 | 9322 | -0.7005 | -0.7846 | 0.0 | `candidate_tighten_or_exclude` |
| `arm` | `PYRAMID` | 3865 | 3865 | 0.6144 | 0.5703 | 0.9674 | `candidate_recovery_or_relax` |
| `blocker_namespace` | `AVG_DOWN` | 5861 | 5860 | -0.9135 | -1.0138 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_namespace` | `PYRAMID` | 3865 | 3865 | 0.6144 | 0.5703 | 0.9674 | `candidate_recovery_or_relax` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 3462 | 3462 | -0.3399 | -0.3965 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `profit_not_enough` | 3671 | 3671 | 0.5422 | 0.4939 | 0.967 | `candidate_recovery_or_relax` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 421 | 421 | -0.7485 | -0.7476 | 0.1164 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `low_broken` | 271 | 271 | -0.3915 | -0.412 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `ok` | 177 | 177 | -1.935 | -2.3914 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `trend_not_strong` | 121 | 121 | 2.8232 | 2.8821 | 1.0 | `candidate_recovery_or_relax` |
| `blocker_reason` | `pnl_out_of_range(-0.04)` | 115 | 115 | -0.0083 | -0.04 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.90)` | 113 | 113 | -0.8135 | -0.9 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `add_judgment_locked` | 109 | 109 | -0.315 | -0.3318 | 0.1376 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.91)` | 109 | 109 | -0.8376 | -0.91 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.81)` | 108 | 108 | -0.735 | -0.81 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.73)` | 101 | 101 | -0.653 | -0.73 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.14)` | 91 | 91 | -1.0452 | -1.14 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.97)` | 88 | 88 | -0.8884 | -0.97 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.24)` | 85 | 85 | -1.1311 | -1.24 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.96)` | 83 | 83 | -0.8571 | -0.96 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.05)` | 82 | 82 | -0.9227 | -1.05 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.83)` | 81 | 81 | -0.7421 | -0.83 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.76)` | 77 | 77 | -0.6956 | -0.76 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.89)` | 76 | 76 | -0.8073 | -0.89 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.74)` | 72 | 72 | -0.6859 | -0.74 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.03)` | 72 | 72 | -0.9177 | -1.03 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.06)` | 71 | 71 | -0.0275 | -0.06 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.80)` | 70 | 70 | -0.6733 | -0.8 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.03)` | 68 | 68 | 0.0051 | -0.03 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.79)` | 68 | 68 | -0.7198 | -0.79 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.71)` | 65 | 65 | -0.6054 | -0.71 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.04)` | 63 | 63 | -0.9185 | -1.04 | 0.0 | `candidate_tighten_or_exclude` |

### Scale-In Bucket Runtime Approval Candidates

- `scale_in_bucket_1`: `ai_score_band` / `score_60_62` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_2`: `ai_score_band` / `score_66_69` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_3`: `ai_score_band` / `score_63_65` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_4`: `ai_score_band` / `score_lt60` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_5`: `ai_score_source` / `score_field_backfilled` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_6`: `arm` / `AVG_DOWN` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_7`: `arm` / `PYRAMID` -> `candidate_recovery_or_relax`
- `scale_in_bucket_8`: `blocker_namespace` / `AVG_DOWN` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_9`: `blocker_namespace` / `PYRAMID` -> `candidate_recovery_or_relax`
- `scale_in_bucket_10`: `blocker_namespace` / `AVG_DOWN_ONLY` -> `candidate_tighten_or_exclude`

### Scale-In Bucket Workorders

- `scale_in_bucket_source_quality_1`: `ai_score_band` / `score_60_62` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_2`: `ai_score_band` / `score_66_69` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
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
- summary: `{'overnight_rows': 78, 'bucket_count': 35, 'actionable_bucket_count': 5, 'runtime_candidate_count': 3, 'workorder_count': 5, 'status_counts': {'HOLD_OVERNIGHT': 39, 'SELL_TODAY': 39}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 15 | 15 | -0.9525 | -1.27 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 10 | 10 | 0.2602 | 0.347 | 0.9 | `hold_no_edge` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 9 | 9 | -0.3192 | -0.4256 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 2 | 2 | 1.0312 | 1.375 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos150_pos300` | 2 | 2 | 1.2675 | 1.69 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos150_pos300_plus` | 1 | 1 | 8.79 | 11.72 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_lt_neg070` | 15 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg010_pos080` | 10 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 9 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_pos080_pos150` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_pos150_pos300` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_pos150_pos300_plus` | 1 | 0 | None | None | None | `hold_sample` |
| `confidence_band` | `confidence_070p` | 78 | 39 | -0.03 | -0.04 | 0.359 | `hold_no_edge` |
| `held_bucket` | `held_600_1800s_plus` | 64 | 32 | -0.0087 | -0.0116 | 0.3438 | `hold_no_edge` |
| `held_bucket` | `held_600_1800s` | 14 | 7 | -0.1275 | -0.17 | 0.4286 | `hold_no_edge` |
| `overnight_action` | `SELL_TODAY` | 78 | 39 | -0.03 | -0.04 | 0.359 | `hold_no_edge` |
| `overnight_status` | `SELL_TODAY` | 39 | 39 | -0.03 | -0.04 | 0.359 | `hold_no_edge` |
| `overnight_status` | `HOLD_OVERNIGHT` | 39 | 0 | None | None | None | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 50 | 25 | -0.6879 | -0.9172 | 0.0 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_zero_pos080` | 18 | 9 | 0.2933 | 0.3911 | 1.0 | `hold_no_edge` |
| `price_source` | `holding_price_samples_last` | 78 | 39 | -0.03 | -0.04 | 0.359 | `hold_no_edge` |
| `profit_band` | `profit_lt_neg070` | 30 | 15 | -0.9525 | -1.27 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 20 | 10 | 0.2602 | 0.347 | 0.9 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 18 | 9 | -0.3192 | -0.4256 | 0.0 | `candidate_tighten_or_exclude` |
| `source_quality_gate` | `overnight_decision_coverage` | 78 | 39 | -0.03 | -0.04 | 0.359 | `hold_no_edge` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 39 | 39 | -0.03 | -0.04 | 0.359 | `hold_no_edge` |
| `stage` | `exit` | 39 | 39 | -0.03 | -0.04 | 0.359 | `hold_no_edge` |

### Overnight Bucket Runtime Approval Candidates

- `overnight_bucket_1`: `combo_overnight_decision` / `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` -> `candidate_tighten_or_exclude`
- `overnight_bucket_3`: `peak_profit_band` / `peak_lt_zero` -> `candidate_tighten_or_exclude`
- `overnight_bucket_4`: `profit_band` / `profit_lt_neg070` -> `candidate_tighten_or_exclude`

### Overnight Bucket Workorders

- `overnight_bucket_source_quality_1`: `combo_overnight_decision` / `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_2`: `combo_overnight_decision` / `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_3`: `peak_profit_band` / `peak_lt_zero` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_4`: `profit_band` / `profit_lt_neg070` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_5`: `profit_band` / `profit_neg070_neg010` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`

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
