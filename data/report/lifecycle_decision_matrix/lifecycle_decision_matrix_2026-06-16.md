# Lifecycle Decision Matrix - 2026-06-16

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-16`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `22185`
- source_rows_total: `27085`
- retained_rows: `22185`
- dropped_rows_by_source: `{'dedupe': 4900}`
- joined_rows: `20266`
- policy_pass_count: `5`
- promote_ready_count: `1`
- entry_bucket_actionable_count: `23`
- entry_bucket_runtime_candidate_count: `10`
- holding_bucket_count/workorders: `35` / `10`
- exit_bucket_count/workorders: `51` / `10`
- scale_in_bucket_actionable_count: `0`
- scale_in_bucket_runtime_candidate_count: `0`
- overnight_bucket_actionable_count: `6`
- overnight_bucket_runtime_candidate_count: `1`
- lifecycle_flow_bucket_count: `140`
- lifecycle_flow_complete_count: `102`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `0` / `102` / `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.005`
- incomplete_flow_reason_counts: `{'missing_submit': 20426, 'missing_holding': 20427, 'missing_exit': 20076, 'missing_entry': 20117, 'postclose_exit_without_entry': 394, 'candidate_id_only': 20161, 'sim_record_id_only': 145, 'scale_in_noise_only': 19701}`
- bucket_directed_sim_probe: `{'observed_row_count': 1176, 'matched_row_count': 42, 'background_row_count': 1134, 'matched_unique_source_bucket_count': 2, 'match_status_counts': {'matched': 42, 'no_match': 704, 'not_instrumented': 430}, 'matched_classification_state_counts': {'lifecycle_flow_sim_probe_candidate': 42}, 'primary_source': 'matched_bucket_directed_sim_probe_only', 'background_source': 'unmatched_or_policy_missing_sim_observation', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 1, 'route_counts': {'bounded_auxiliary_weight': 1, 'hold_sample': 4}, 'quality_counts': {'observational_only_pending_outcome': 1, 'hold_sample': 4}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 1213 | 217 | 1.2732 | 1.0 | `pass` | `BUY_DEFENSIVE` | True |
| `submit` | 293 | 190 | -0.5406 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 278 | 190 | -0.985 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 19832 | 19366 | -0.4216 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 569 | 303 | -0.9698 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 20572, 'complete_flow_count': 102, 'direct_sim_record_complete_flow_count': 0, 'adm_bridge_complete_flow_count': 102, 'fallback_complete_flow_count': 0, 'direct_flow_zero_diagnostic': {'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_sim_record_flow_count': 145, 'direct_sim_record_incomplete_flow_count': 145, 'direct_sim_record_stage_coverage_counts': {'exit': 126, 'holding': 20}, 'direct_sim_record_incomplete_reason_counts': {'missing_entry': 145, 'missing_submit': 145, 'missing_holding': 125, 'missing_exit': 19, 'sim_record_id_only': 145, 'scale_in_noise_only': 19, 'postclose_exit_without_entry': 126}, 'runtime_effect': False, 'decision_authority': 'ldm_direct_flow_diagnostic_only'}, 'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'incomplete_flow_count': 20470, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 22185, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.005, 'complete_flow_conversion_denominator': 518, 'complete_flow_conversion_rate': 0.1969, 'active_priority_incomplete_seed_count': 353, 'scale_in_followup_event_count': 19832, 'scale_in_unique_flow_count': 15416, 'scale_in_noise_flow_count': 19701, 'denominator_exclusion_counts': {'scale_in_noise_flow_excluded': 19701, 'active_priority_incomplete_seed_excluded': 353}, 'conversion_blocker_reason_counts': {'missing_entry': 416, 'missing_holding': 393, 'missing_exit': 22, 'postclose_exit_without_entry': 394, 'missing_submit': 392, 'sim_record_id_only': 126, 'candidate_id_only': 266}, 'observation_seed_reason_counts': {'missing_submit': 20034, 'missing_holding': 20034, 'missing_exit': 20054, 'candidate_id_only': 19895, 'missing_entry': 19701, 'sim_record_id_only': 19, 'scale_in_noise_only': 19701}, 'join_contract_blocked': False, 'bundle_ev_tuning_state': 'ready_for_bundle_ev_tuning', 'top_incomplete_reason': 'missing_holding', 'stage_identity': {'entry': {'source_row_count': 1213, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 1000, 'candidate_id': 213}, 'identity_join_rate': 1.0}, 'submit': {'source_row_count': 293, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 293}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 278, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 258, 'exact_sim_record_id': 20}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 19832, 'identity_missing_count': 0, 'identity_quality_counts': {'exact_sim_record_id': 150, 'candidate_id': 19682}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 569, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 159, 'exact_sim_record_id': 144, 'candidate_id': 266}, 'identity_join_rate': 1.0}}, 'required_stage_source_counts': {'entry': 1213, 'submit': 293, 'holding': 278, 'exit': 569}, 'incomplete_flow_reason_counts': {'missing_submit': 20426, 'missing_holding': 20427, 'missing_exit': 20076, 'missing_entry': 20117, 'postclose_exit_without_entry': 394, 'candidate_id_only': 20161, 'sim_record_id_only': 145, 'scale_in_noise_only': 19701}, 'bucket_count': 140, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9b100ebd9b` | 5 | 5 | -1.448 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:8050d08a3f` | 3 | 3 | -2.4793 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:89e49a11bc` | 3 | 3 | -1.5592 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9d8cac316e` | 3 | 3 | -0.6791 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:67138f9e63` | 2 | 2 | -0.8293 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:d8b4aa95dd` | 2 | 2 | -1.2595 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:8804394aa4` | 2 | 2 | 0.6028 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:f7df4238eb` | 2 | 2 | 0.66 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:917af9e5d4` | 2 | 2 | -0.9532 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:441959da5f` | 2 | 2 | -1.4608 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:7f4b207c82` | 1 | 1 | 2.6014 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:d4987d75cf` | 1 | 1 | -1.8202 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:73f53a9171` | 1 | 1 | -0.6697 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:63c5889354` | 1 | 1 | -1.6031 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:5898181be2` | 1 | 1 | -1.5637 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:a61bbddbb3` | 1 | 1 | -0.6737 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:92c2eeaf3e` | 1 | 1 | -1.5585 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:bb1a5dec46` | 1 | 1 | -3.8472 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:d43dbcd7d2` | 1 | 1 | -1.8817 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:54dd5256bc` | 1 | 1 | -0.8488 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 1213, 'bucket_count': 225, 'actionable_bucket_count': 23, 'source_quality_blocked_bucket_count': 0, 'runtime_candidate_count': 10, 'workorder_count': 10}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `WAIT_REQUOTE` | 133 | 133 | 2.1966 | 3.3093 | 0.7143 | `candidate_recovery_or_relax` |
| `chosen_action` | `NO_BUY_AI` | 960 | 74 | -0.0745 | -1.0832 | 0.2838 | `hold_no_edge` |
| `chosen_action` | `BUY_NOW` | 19 | 10 | -1.0354 | -0.351 | 0.2 | `candidate_tighten_or_exclude` |
| `chosen_action` | `ALLOW_BOTTOMING_ENTRY` | 4 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `ALLOW_LEVEL1_RISK_OFF_ENTRY` | 76 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_SOURCE_QUALITY` | 21 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 27 | 27 | 1.3544 | 1.749 | 0.7037 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 26 | 26 | 1.3342 | 1.764 | 0.5769 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 23 | 23 | 1.3968 | 1.9066 | 0.8261 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 53 | 22 | 0.3982 | -0.8045 | 0.2727 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 124 | 20 | -0.2634 | -0.315 | 0.45 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 10 | 10 | 0.5453 | 0.5856 | 0.6 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 9 | 9 | 1.0653 | 1.5251 | 0.5556 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 7 | 7 | 6.213 | 9.7616 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 20 | 6 | 0.9672 | -2.6817 | 0.1667 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 8 | 6 | -1.8589 | 0.6483 | 0.3333 | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 5 | 5 | 3.9584 | 5.8216 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 15 | 5 | -0.0702 | -1.91 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 5 | 5 | 2.1453 | 3.6408 | 0.6 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 4 | 4 | 2.8805 | 4.0857 | 0.75 | `hold_sample` |
| `exit_rule` | `exit_unknown` | 1129 | 133 | 2.1966 | 3.3093 | 0.7143 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_soft_stop_pct` | 42 | 42 | -0.0109 | -1.9864 | 0.0 | `hold_no_edge` |
| `exit_rule` | `scalp_trailing_take_profit` | 23 | 23 | -0.2589 | 2.3639 | 1.0 | `hold_no_edge` |
| `exit_rule` | `scalp_hard_stop_pct` | 16 | 16 | -0.6449 | -3.26 | 0.0 | `candidate_tighten_or_exclude` |
| `liquidity_bucket` | `liquidity_high` | 930 | 217 | 1.2732 | 1.6427 | 0.5438 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 933 | 172 | 0.7258 | 0.7044 | 0.5116 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_watch` | 112 | 24 | 3.2053 | 4.0214 | 0.6667 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_ok` | 65 | 15 | 3.6472 | 6.8165 | 0.6667 | `candidate_recovery_or_relax` |
| `score_band` | `score_70p` | 152 | 57 | 0.9564 | 1.6956 | 0.614 | `candidate_recovery_or_relax` |

### Entry Bucket Runtime Approval Candidates

- `entry_bucket_3`: `combo_entry_spot` / `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` -> `candidate_recovery_or_relax`
- `entry_bucket_4`: `combo_entry_spot` / `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` -> `candidate_recovery_or_relax`
- `entry_bucket_5`: `combo_entry_spot` / `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` -> `candidate_recovery_or_relax`
- `entry_bucket_6`: `combo_entry_spot` / `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` -> `candidate_recovery_or_relax`
- `entry_bucket_10`: `liquidity_bucket` / `liquidity_high` -> `candidate_recovery_or_relax`
- `entry_bucket_11`: `overbought_bucket` / `overbought_normal` -> `candidate_recovery_or_relax`
- `entry_bucket_12`: `overbought_bucket` / `overbought_watch` -> `candidate_recovery_or_relax`
- `entry_bucket_14`: `score_band` / `score_70p` -> `candidate_recovery_or_relax`
- `entry_bucket_15`: `score_band` / `score_66_69` -> `candidate_recovery_or_relax`
- `entry_bucket_16`: `score_band` / `score_63_65` -> `candidate_recovery_or_relax`

### Entry Bucket Workorders

- `entry_bucket_source_quality_1`: `chosen_action` / `WAIT_REQUOTE` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_2`: `chosen_action` / `BUY_NOW` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_3`: `combo_entry_spot` / `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_4`: `combo_entry_spot` / `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_5`: `combo_entry_spot` / `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_6`: `combo_entry_spot` / `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_7`: `combo_entry_spot` / `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_8`: `exit_rule` / `exit_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_9`: `exit_rule` / `scalp_hard_stop_pct` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_10`: `liquidity_bucket` / `liquidity_high` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`

## Submit Bucket Attribution

- decision_authority: `adm_ldm_submit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'submit_rows': 293, 'bucket_count': 66, 'contract_gap_count': 0, 'workorder_count': 0, 'runtime_candidate_count': 0, 'real_submitted_row_count': 3, 'missing_broker_order_key_count': 0, 'bot_history_broker_order_key_backfill_candidate_count': 0, 'bot_history_broker_order_key_backfill_full_coverage': False, 'bot_history_broker_order_key_exact_mapping_count': 0, 'bot_history_broker_order_key_exact_mapping_full_coverage': False, 'post_submit_provenance_join_resolution': 'no_gap_broker_order_key_present_or_no_missing_rows', 'bot_history_broker_order_key_backfill_candidates': [], 'missing_broker_order_key_rate': 0.0, 'post_submit_provenance_join_gap_raw': False, 'post_submit_provenance_join_gap': False}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 290 | 190 | -0.5406 | `keep_collecting` |
| `actual_order_submitted` | `true` | 3 | 0 | None | `keep_collecting` |
| `broker_order_forbidden` | `true` | 289 | 190 | -0.5406 | `keep_collecting` |
| `broker_order_forbidden` | `false` | 4 | 0 | None | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 86 | 58 | -0.009 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 59 | 45 | -1.0826 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 40 | 27 | -0.298 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=false|submitted=false` | 21 | 17 | -0.6466 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 21 | 18 | -0.7727 | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=block_False|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=latency_unknown|fill=false|submitted=false` | 20 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 16 | 13 | -0.7278 | `source_quality_workorder` |
| `combo_submit_quality` | `source=pre_submit_liquidity_guard_block|revalidation=block_False|quote_age=quote_age_unknown|liquidity=below_min_liquidity|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=latency_unknown|fill=false|submitted=false` | 11 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 4 | 3 | 0.5627 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 4 | 3 | -0.6679 | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=block_False|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=latency_unknown|fill=false|submitted=true` | 3 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 2 | 2 | -0.4774 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_overbought_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=pullback_or_rebreak_not_confirmed|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 2 | 2 | -2.74 | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_pass|revalidation=block_False|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=latency_unknown|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | -2.161 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | -2.161 | `source_quality_workorder` |
| `latency_reason` | `scalp_live_simulator` | 258 | 190 | -0.5406 | `keep_collecting` |
| `latency_reason` | `latency_reason_unknown` | 35 | 0 | None | `source_quality_workorder` |
| `latency_state` | `simulated` | 258 | 190 | -0.5406 | `keep_collecting` |
| `latency_state` | `latency_unknown` | 35 | 0 | None | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_ok` | 156 | 109 | -0.223 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 113 | 81 | -0.9681 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_not_available` | 24 | 0 | None | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 156 | 109 | -0.223 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 102 | 81 | -0.9681 | `keep_collecting` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 35 | 0 | None | `source_quality_workorder` |
| `overbought_bucket` | `overbought_ok` | 208 | 150 | -0.481 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 48 | 38 | -0.6603 | `keep_collecting` |
| `overbought_bucket` | `overbought_not_available` | 35 | 0 | None | `keep_collecting` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 2 | 2 | -2.74 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 256 | 188 | -0.5172 | `keep_collecting` |
| `overbought_guard_action` | `overbought_guard_unknown` | 35 | 0 | None | `source_quality_workorder` |
| `overbought_guard_action` | `would_block` | 2 | 2 | -2.74 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 183 | 134 | -0.3978 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 66 | 51 | -0.9387 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 278, 'source_row_count': 278, 'bucket_count': 35, 'joined_sample': 950, 'source_quality_adjusted_ev_pct': -0.985, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 92 | 92 | -1.4144 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 47 | 47 | -1.5397 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 12 | 12 | 0.1621 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 9 | 9 | -1.0907 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 8 | 8 | 0.5744 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 4 | 4 | -0.2875 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 4 | 4 | 0.4425 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 3 | 3 | 0.44 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 3 | 3 | 2.8445 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 3 | 3 | 0.308 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 0.4103 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 4.2814 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 1 | 1 | -0.12 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 1 | 1 | 2.2355 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 47 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 19 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 8 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 7 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 5 | 0 | None | `hold_sample` |
| `held_bucket` | `held_not_applicable_at_start` | 258 | 190 | -0.985 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s_plus` | 20 | 0 | None | `hold_sample` |
| `holding_action` | `WAIT` | 169 | 122 | -0.9416 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 77 | 58 | -1.1506 | `candidate_tighten_or_exclude` |
| `holding_action` | `BUY` | 12 | 10 | -0.5535 | `candidate_tighten_or_exclude` |
| `holding_action` | `SELL_TODAY` | 20 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 258 | 190 | -0.985 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 20 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 156 | 148 | -1.4345 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 14 | 14 | 0.1976 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 9 | 9 | 0.759 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg010_pos080` | 14 | 7 | 0.4414 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300_plus` | 7 | 7 | 1.9627 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 10 | 5 | -0.254 | `hold_no_edge` |
| `profit_band` | `profit_not_applicable_at_start` | 68 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- `holding_bucket_source_quality_1`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_2`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_3`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_4`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_5`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_6`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_7`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_8`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_9`: `held_bucket` / `held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_10`: `holding_action` / `WAIT` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Exit Bucket Attribution

- decision_authority: `adm_ldm_exit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'exit_rows': 569, 'source_row_count': 569, 'bucket_count': 51, 'joined_sample': 1515, 'source_quality_adjusted_ev_pct': -0.9698, 'source_quality_gate': 'pass', 'unknown_reason_counts': {'not_applicable': 3, 'join_gap': 8, 'missing_source_field': 1}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 93 | 93 | -1.1985 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 30 | 30 | -1.0755 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 25 | 25 | -0.4972 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 25 | 25 | -1.6096 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 25 | 25 | -1.0059 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 22 | 22 | -2.6134 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 16 | 16 | -1.3696 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 9 | 9 | -1.7752 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 8 | 8 | -0.7087 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 7 | 7 | 0.3311 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 6 | 6 | -0.0685 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 6 | 6 | 0.6231 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 5 | 5 | -0.1905 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 5 | 5 | 0.145 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 4 | 4 | 0.3575 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 4 | 4 | 2.7837 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 3 | 3 | 1.6775 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` | 2 | 2 | 0.95 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 2 | 2 | -0.8387 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 1 | 1 | -0.6116 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | 0.0961 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 1 | 1 | -0.3145 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 1 | 1 | 0.9965 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300` | 1 | 1 | 1.0734 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300_plus` | 1 | 1 | 4.2814 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_euphoria_context_noop|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown` | 247 | 0 | None | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown` | 19 | 0 | None | `source_quality_workorder` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 124 | 124 | -0.9723 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 61 | 61 | -1.6346 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 50 | 50 | -0.596 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 48 | 48 | -0.8221 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 286 | 20 | -0.2152 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 124 | 124 | -0.9723 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 80 | 80 | -1.2207 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 47 | 47 | -2.0295 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 29 | 29 | 0.8584 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 20 | 20 | -0.2152 | `hold_no_edge` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 3 | 3 | -0.2767 | `hold_no_edge` |
| `exit_rule` | `exit_rule_unknown` | 266 | 0 | None | `source_quality_workorder` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 159 | 159 | -1.0627 | `candidate_tighten_or_exclude` |

### Exit Bucket Attribution Workorders

- `exit_bucket_source_quality_1`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_2`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_3`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_4`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_5`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_6`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_7`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_8`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_9`: `combo_exit_result` / `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_10`: `combo_exit_result` / `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `incremental_notional_ev_pct`
- summary: `{'scale_in_rows': 19832, 'bucket_count': 2883, 'edge_bucket_count': 0, 'actionable_bucket_count': 0, 'runtime_authority_blocked_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'arm_counts': {'PYRAMID': 4007, 'AVG_DOWN': 15825}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_70p` | 12823 | 12823 | None | -0.4805 | 0.1855 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 3173 | 3173 | None | -0.4944 | 0.1768 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 1496 | 1496 | None | -0.4454 | 0.1832 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 1056 | 1056 | None | -0.4241 | 0.2339 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 808 | 808 | None | -0.5239 | 0.1757 | `hold_sample` |
| `ai_score_band` | `score_unknown` | 476 | 10 | None | 0.4088 | 0.625 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 19356 | 19356 | None | -0.4788 | 0.1861 | `hold_sample` |
| `ai_score_source` | `sim_scale_in_source_not_scored` | 10 | 10 | None | 0.4088 | 0.625 | `hold_sample` |
| `ai_score_source` | `stage_rule_backfilled` | 466 | 0 | None | None | None | `hold_sample` |
| `arm` | `AVG_DOWN` | 15825 | 15698 | None | -0.7666 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 4007 | 3668 | None | 0.7553 | 0.9842 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 10807 | 10680 | None | -0.9224 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 5018 | 5018 | None | -0.4348 | 0.0 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 4007 | 3668 | None | 0.7553 | 0.9842 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 2756 | 2756 | None | 0.5043 | 0.9877 | `hold_sample` |
| `blocker_reason` | `add_judgment_locked` | 2595 | 2595 | None | -0.3322 | 0.1561 | `hold_sample` |
| `blocker_reason` | `low_broken` | 350 | 350 | None | -0.4577 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalping_pyramid_ok` | 305 | 305 | None | 3.5856 | 1.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.93)` | 282 | 282 | None | -0.93 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_scale_in_window_expansion` | 238 | 238 | None | -0.3497 | 0.3613 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `adm_ldm_overnight_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'overnight_rows': 40, 'bucket_count': 22, 'actionable_bucket_count': 6, 'runtime_candidate_count': 1, 'workorder_count': 6, 'status_counts': {'HOLD_OVERNIGHT': 20, 'SELL_TODAY': 20}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 8 | 8 | -0.7087 | -0.945 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 7 | 7 | 0.3311 | 0.4414 | 1.0 | `candidate_recovery_or_relax` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 5 | 5 | -0.1905 | -0.254 | 0.0 | `hold_no_edge` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_lt_neg070` | 8 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg010_pos080` | 7 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 5 | 0 | None | None | None | `hold_sample` |
| `confidence_band` | `confidence_070p` | 40 | 20 | -0.2152 | -0.287 | 0.35 | `hold_no_edge` |
| `held_bucket` | `held_600_1800s_plus` | 40 | 20 | -0.2152 | -0.287 | 0.35 | `hold_no_edge` |
| `overnight_action` | `SELL_TODAY` | 40 | 20 | -0.2152 | -0.287 | 0.35 | `hold_no_edge` |
| `overnight_status` | `SELL_TODAY` | 20 | 20 | -0.2152 | -0.287 | 0.35 | `hold_no_edge` |
| `overnight_status` | `HOLD_OVERNIGHT` | 20 | 0 | None | None | None | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 26 | 13 | -0.5094 | -0.6792 | 0.0 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_zero_pos080` | 14 | 7 | 0.3311 | 0.4414 | 1.0 | `candidate_recovery_or_relax` |
| `price_source` | `holding_price_samples_last` | 40 | 20 | -0.2152 | -0.287 | 0.35 | `hold_no_edge` |
| `profit_band` | `profit_lt_neg070` | 16 | 8 | -0.7087 | -0.945 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 14 | 7 | 0.3311 | 0.4414 | 1.0 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 10 | 5 | -0.1905 | -0.254 | 0.0 | `hold_no_edge` |
| `source_quality_gate` | `overnight_decision_coverage` | 40 | 20 | -0.2152 | -0.287 | 0.35 | `hold_no_edge` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 20 | 20 | -0.2152 | -0.287 | 0.35 | `hold_no_edge` |
| `source_stage` | `scalp_sim_overnight_decision` | 20 | 0 | None | None | None | `hold_sample` |
| `stage` | `exit` | 20 | 20 | -0.2152 | -0.287 | 0.35 | `hold_no_edge` |

### Overnight Bucket Runtime Approval Candidates

- `overnight_bucket_3`: `peak_profit_band` / `peak_lt_zero` -> `candidate_tighten_or_exclude`

### Overnight Bucket Workorders

- `overnight_bucket_source_quality_1`: `combo_overnight_decision` / `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_2`: `combo_overnight_decision` / `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_3`: `peak_profit_band` / `peak_lt_zero` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_4`: `peak_profit_band` / `peak_zero_pos080` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_5`: `profit_band` / `profit_lt_neg070` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_6`: `profit_band` / `profit_neg010_pos080` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`

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
