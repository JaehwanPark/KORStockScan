# Lifecycle Decision Matrix - 2026-06-23

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-23`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `7800`
- source_rows_total: `9632`
- retained_rows: `7800`
- dropped_rows_by_source: `{'dedupe': 1832}`
- joined_rows: `4753`
- policy_pass_count: `5`
- promote_ready_count: `0`
- entry_bucket_actionable_count: `17`
- entry_bucket_runtime_candidate_count: `10`
- holding_bucket_count/workorders: `38` / `10`
- exit_bucket_count/workorders: `48` / `10`
- scale_in_bucket_actionable_count: `0`
- scale_in_bucket_runtime_candidate_count: `0`
- overnight_bucket_actionable_count: `9`
- overnight_bucket_runtime_candidate_count: `0`
- lifecycle_flow_bucket_count: `101`
- lifecycle_flow_complete_count: `56`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `0` / `56` / `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0083`
- incomplete_flow_reason_counts: `{'missing_submit': 6693, 'missing_holding': 6690, 'missing_exit': 4251, 'missing_entry': 6439, 'postclose_exit_without_entry': 2454, 'candidate_id_only': 6431, 'sim_record_id_only': 193, 'scale_in_noise_only': 3979}`
- bucket_directed_sim_probe: `{'observed_row_count': 3247, 'matched_row_count': 125, 'background_row_count': 3122, 'matched_unique_source_bucket_count': 1, 'match_status_counts': {'matched': 125, 'no_match': 666, 'not_instrumented': 2456}, 'matched_classification_state_counts': {'lifecycle_flow_sim_probe_candidate': 125}, 'primary_source': 'matched_bucket_directed_sim_probe_only', 'background_source': 'unmatched_or_policy_missing_sim_observation', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 1, 'route_counts': {'bounded_auxiliary_weight': 1, 'hold_sample': 4}, 'quality_counts': {'observational_only_pending_outcome': 1, 'hold_sample': 4}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 629 | 70 | 0.2837 | 0.779 | `pass` | `NO_CHANGE` | False |
| `submit` | 223 | 144 | -0.7527 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 221 | 144 | -1.3353 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 4132 | 4081 | -0.4826 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 2595 | 314 | -1.0604 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 6761, 'complete_flow_count': 56, 'direct_sim_record_complete_flow_count': 0, 'adm_bridge_complete_flow_count': 56, 'fallback_complete_flow_count': 0, 'direct_flow_zero_diagnostic': {'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'direct_sim_record_flow_count': 193, 'direct_sim_record_incomplete_flow_count': 193, 'direct_sim_record_stage_coverage_counts': {'exit': 160, 'holding': 9}, 'direct_sim_record_incomplete_reason_counts': {'missing_entry': 193, 'missing_submit': 193, 'missing_holding': 184, 'sim_record_id_only': 193, 'postclose_exit_without_entry': 160, 'missing_exit': 33, 'scale_in_noise_only': 33}, 'runtime_effect': False, 'decision_authority': 'ldm_direct_flow_diagnostic_only'}, 'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'incomplete_flow_count': 6705, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 7800, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0083, 'complete_flow_conversion_denominator': 2516, 'complete_flow_conversion_rate': 0.0223, 'active_priority_incomplete_seed_count': 266, 'scale_in_followup_event_count': 4132, 'scale_in_unique_flow_count': 3535, 'scale_in_noise_flow_count': 3979, 'denominator_exclusion_counts': {'scale_in_noise_flow_excluded': 3979, 'active_priority_incomplete_seed_excluded': 266}, 'conversion_blocker_reason_counts': {'missing_entry': 2460, 'missing_holding': 2451, 'missing_exit': 6, 'missing_submit': 2454, 'postclose_exit_without_entry': 2454, 'sim_record_id_only': 160, 'candidate_id_only': 2281}, 'observation_seed_reason_counts': {'missing_submit': 4239, 'missing_holding': 4239, 'missing_exit': 4245, 'candidate_id_only': 4150, 'missing_entry': 3979, 'sim_record_id_only': 33, 'scale_in_noise_only': 3979}, 'join_contract_blocked': False, 'bundle_ev_tuning_state': 'ready_for_bundle_ev_tuning', 'top_incomplete_reason': 'missing_submit', 'stage_identity': {'entry': {'source_row_count': 629, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 425, 'candidate_id': 204}, 'identity_join_rate': 1.0}, 'submit': {'source_row_count': 223, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 223}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 221, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 212, 'exact_sim_record_id': 9}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 4132, 'identity_missing_count': 0, 'identity_quality_counts': {'exact_sim_record_id': 186, 'candidate_id': 3946}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 2595, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 148, 'exact_sim_record_id': 166, 'candidate_id': 2281}, 'identity_join_rate': 1.0}}, 'required_stage_source_counts': {'entry': 629, 'submit': 223, 'holding': 221, 'exit': 2595}, 'incomplete_flow_reason_counts': {'missing_submit': 6693, 'missing_holding': 6690, 'missing_exit': 4251, 'missing_entry': 6439, 'postclose_exit_without_entry': 2454, 'candidate_id_only': 6431, 'sim_record_id_only': 193, 'scale_in_noise_only': 3979}, 'bucket_count': 101, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:8050d08a3f` | 2 | 2 | -1.8677 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:89e49a11bc` | 2 | 2 | -1.4874 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:7248608969` | 2 | 2 | -0.8297 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:5b44354174` | 2 | 2 | -2.5139 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:f52ada862f` | 2 | 2 | -3.9129 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:76e538b0ff` | 2 | 2 | -1.687 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:ee117bc3cd` | 2 | 2 | -2.6799 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:b24470d667` | 1 | 1 | -1.2615 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:3f112defcf` | 1 | 1 | -1.2706 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:9c03f3dde5` | 1 | 1 | -2.0109 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:32a948478c` | 1 | 1 | -1.661 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:efc883da1c` | 1 | 1 | -1.4431 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:c3a750aefc` | 1 | 1 | -1.4009 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:3cbb81cd02` | 1 | 1 | -1.049 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9a00ffe360` | 1 | 1 | -0.4452 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9b100ebd9b` | 1 | 1 | -0.4319 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:7fe2be4de7` | 1 | 1 | -0.7822 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:0df4cac793` | 1 | 1 | -2.4059 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:5a8c68df46` | 1 | 1 | -0.3589 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:b425903d93` | 1 | 1 | -1.1798 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 629, 'bucket_count': 187, 'actionable_bucket_count': 17, 'source_quality_blocked_bucket_count': 0, 'runtime_candidate_count': 10, 'workorder_count': 10}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `NO_BUY_AI` | 405 | 40 | -0.5928 | -1.9303 | 0.15 | `candidate_tighten_or_exclude` |
| `chosen_action` | `WAIT_REQUOTE` | 23 | 23 | 1.9871 | 3.1556 | 0.5217 | `candidate_recovery_or_relax` |
| `chosen_action` | `BUY_NOW` | 19 | 7 | -0.3049 | -2.8657 | 0.0 | `hold_sample` |
| `chosen_action` | `ALLOW_BOTTOMING_ENTRY` | 32 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `ALLOW_LEVEL1_RISK_OFF_ENTRY` | 149 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_SOURCE_QUALITY` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 10 | 10 | 0.5919 | 0.4466 | 0.5 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 38 | 6 | 0.5037 | -2.0417 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 30 | 5 | -0.3615 | -2.528 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 33 | 4 | -0.2984 | -1.485 | 0.25 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 11 | 3 | 1.3341 | -2.07 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 3 | 3 | 1.5678 | 2.8895 | 0.6667 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_1000_1200` | 3 | 3 | 6.2864 | 10.9644 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 9 | 2 | -2.5129 | -2.73 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 12 | 2 | 0.2575 | -3.175 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 9 | 2 | -1.9132 | -2.55 | 0.5 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 7 | 2 | -0.2215 | -1.12 | 0.5 | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 2 | 2 | -0.7735 | -1.6736 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 8 | 2 | 0.753 | -2.14 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 4 | 2 | -2.458 | -2.635 | 0.0 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 25 | 25 | -0.3628 | -2.0224 | 0.0 | `candidate_tighten_or_exclude` |
| `exit_rule` | `exit_unknown` | 582 | 23 | 1.9871 | 3.1556 | 0.5217 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_hard_stop_pct` | 16 | 16 | -0.621 | -3.4931 | 0.0 | `candidate_tighten_or_exclude` |
| `liquidity_bucket` | `liquidity_high` | 376 | 70 | 0.2837 | -0.3527 | 0.2571 | `hold_no_edge` |
| `overbought_bucket` | `overbought_normal` | 343 | 50 | 0.4887 | -0.7222 | 0.22 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_watch` | 96 | 20 | -0.229 | 0.5709 | 0.35 | `hold_no_edge` |
| `score_band` | `score_70p` | 96 | 27 | 0.7429 | 1.1359 | 0.4074 | `candidate_recovery_or_relax` |
| `score_band` | `score_60_62` | 343 | 26 | -0.3497 | -2.3135 | 0.0769 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 312 | 47 | -0.55 | -2.0696 | 0.1277 | `candidate_tighten_or_exclude` |
| `source_stage` | `wait6579_ev_cohort` | 23 | 23 | 1.9871 | 3.1556 | 0.5217 | `candidate_recovery_or_relax` |
| `stale_bucket` | `stale_high` | 228 | 26 | -0.7121 | -2.0192 | 0.1538 | `candidate_tighten_or_exclude` |
| `stale_bucket` | `fresh_or_unflagged` | 204 | 23 | 1.9871 | 3.1556 | 0.5217 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh` | 143 | 21 | -0.3492 | -2.1319 | 0.0952 | `candidate_tighten_or_exclude` |
| `strength_bucket` | `weak_strength_momentum` | 301 | 36 | -0.0543 | -1.0684 | 0.1944 | `hold_no_edge` |
| `strength_bucket` | `strong_strength_momentum` | 98 | 29 | 0.9675 | 1.0183 | 0.3793 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_0900_1000` | 278 | 40 | 0.3699 | -0.2605 | 0.3 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_1000_1200` | 184 | 23 | 0.5435 | 0.2956 | 0.2609 | `candidate_recovery_or_relax` |

### Entry Bucket Runtime Approval Candidates

- `entry_bucket_7`: `overbought_bucket` / `overbought_normal` -> `candidate_recovery_or_relax`
- `entry_bucket_8`: `score_band` / `score_70p` -> `candidate_recovery_or_relax`
- `entry_bucket_9`: `score_band` / `score_60_62` -> `candidate_tighten_or_exclude`
- `entry_bucket_10`: `source_stage` / `scalp_entry_action_decision_snapshot` -> `candidate_tighten_or_exclude`
- `entry_bucket_11`: `source_stage` / `wait6579_ev_cohort` -> `candidate_recovery_or_relax`
- `entry_bucket_12`: `stale_bucket` / `stale_high` -> `candidate_tighten_or_exclude`
- `entry_bucket_13`: `stale_bucket` / `fresh_or_unflagged` -> `candidate_recovery_or_relax`
- `entry_bucket_14`: `stale_bucket` / `fresh` -> `candidate_tighten_or_exclude`
- `entry_bucket_15`: `strength_bucket` / `strong_strength_momentum` -> `candidate_recovery_or_relax`
- `entry_bucket_16`: `time_bucket` / `time_0900_1000` -> `candidate_recovery_or_relax`

### Entry Bucket Workorders

- `entry_bucket_source_quality_1`: `chosen_action` / `NO_BUY_AI` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_2`: `chosen_action` / `WAIT_REQUOTE` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_3`: `combo_entry_spot` / `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_4`: `exit_rule` / `scalp_soft_stop_pct` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_5`: `exit_rule` / `exit_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_6`: `exit_rule` / `scalp_hard_stop_pct` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_7`: `overbought_bucket` / `overbought_normal` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_8`: `score_band` / `score_70p` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_9`: `score_band` / `score_60_62` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_10`: `source_stage` / `scalp_entry_action_decision_snapshot` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`

## Submit Bucket Attribution

- decision_authority: `adm_ldm_submit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'submit_rows': 223, 'bucket_count': 89, 'contract_gap_count': 0, 'workorder_count': 0, 'runtime_candidate_count': 0, 'quote_freshness_attribution_present': True, 'quote_freshness_resolution_counts': {'refresh_attempted_unresolved': 4, 'refresh_not_attempted_or_not_instrumented': 5, 'refresh_resolved_quote_freshness': 2, 'sim_submit_path_not_applicable': 212}, 'pre_submit_refresh_applied_counts': {'refresh_attempted_not_applied': 4, 'refresh_not_attempted_or_not_instrumented': 5, 'sim_submit_path_not_applicable': 212, 'ws_snapshot_refresh_applied': 2}, 'real_submitted_row_count': 2, 'missing_broker_order_key_count': 0, 'bot_history_broker_order_key_backfill_candidate_count': 0, 'bot_history_broker_order_key_backfill_full_coverage': False, 'bot_history_broker_order_key_exact_mapping_count': 0, 'bot_history_broker_order_key_exact_mapping_full_coverage': False, 'post_submit_provenance_join_resolution': 'no_gap_broker_order_key_present_or_no_missing_rows', 'bot_history_broker_order_key_backfill_candidates': [], 'missing_broker_order_key_rate': 0.0, 'post_submit_provenance_join_gap_raw': False, 'post_submit_provenance_join_gap': False}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 221 | 144 | -0.7527 | `keep_collecting` |
| `actual_order_submitted` | `true` | 2 | 0 | None | `keep_collecting` |
| `broker_order_forbidden` | `true` | 221 | 144 | -0.7527 | `keep_collecting` |
| `broker_order_forbidden` | `false` | 2 | 0 | None | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 77 | 61 | -0.988 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 72 | 41 | -0.4079 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 15 | 8 | 0.8652 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 13 | 10 | -2.0752 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 8 | 6 | -0.5865 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 7 | 5 | -0.7714 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 6 | 4 | -0.008 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 5 | 3 | -1.6415 | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_attempted_unresolved|fill=false|submitted=false` | 4 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=pre_submit_liquidity_guard_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=latency_unknown|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=false` | 3 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 3 | 1 | 3.3449 | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_resolved_quote_freshness|fill=false|submitted=false` | 2 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=caution|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 2 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 2 | 2 | -2.2818 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 2 | 2 | -1.7746 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_unknown|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=would_unknown|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | -0.4661 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_overbought_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=pullback_or_rebreak_not_confirmed|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `latency_reason` | `scalp_live_simulator` | 212 | 144 | -0.7527 | `keep_collecting` |
| `latency_reason` | `spread_too_wide` | 4 | 0 | None | `keep_collecting` |
| `latency_reason` | `latency_reason_unknown` | 3 | 0 | None | `source_quality_workorder` |
| `latency_reason` | `caution_normal_entry_allowed` | 2 | 0 | None | `keep_collecting` |
| `latency_reason` | `other_danger` | 2 | 0 | None | `keep_collecting` |
| `latency_state` | `simulated` | 212 | 144 | -0.7527 | `keep_collecting` |
| `latency_state` | `danger` | 6 | 0 | None | `keep_collecting` |
| `latency_state` | `latency_unknown` | 3 | 0 | None | `source_quality_workorder` |
| `latency_state` | `caution` | 2 | 0 | None | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 119 | 86 | -0.8643 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 95 | 57 | -0.5892 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_not_available` | 9 | 1 | -0.4661 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 116 | 86 | -0.8643 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 95 | 57 | -0.5892 | `keep_collecting` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 11 | 0 | None | `source_quality_workorder` |
| `liquidity_guard_action` | `would_unknown` | 1 | 1 | -0.4661 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_ok` | 172 | 118 | -0.8804 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 39 | 26 | -0.1731 | `keep_collecting` |
| `overbought_bucket` | `overbought_not_available` | 11 | 0 | None | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 221, 'source_row_count': 221, 'bucket_count': 38, 'joined_sample': 720, 'source_quality_adjusted_ev_pct': -1.3353, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 100 | 100 | -1.6232 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 17 | 17 | -1.8293 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 8 | 8 | -0.0237 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 7 | 7 | -0.1997 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 3 | 3 | -0.0885 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 3 | 3 | 2.3355 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 2 | 2 | -0.425 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1 | 1 | -3.8866 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 1 | 1 | -0.67 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | -1.341 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 1 | 1 | 2.7338 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 54 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 13 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_180_600s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_not_applicable_at_start` | 212 | 144 | -1.3353 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_180_600s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 3 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 5 | 0 | None | `hold_sample` |
| `holding_action` | `WAIT` | 176 | 122 | -1.2938 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 34 | 21 | -1.455 | `candidate_tighten_or_exclude` |
| `holding_action` | `BUY` | 2 | 1 | -3.8866 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 9 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 212 | 144 | -1.3353 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 9 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 121 | 118 | -1.6721 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 9 | 9 | 0.2827 | `hold_no_edge` |
| `profit_band` | `profit_pos080_pos150` | 7 | 7 | -0.1997 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300_plus` | 4 | 4 | 1.4164 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg010_pos080` | 5 | 3 | -0.0885 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 7 | 3 | -0.5067 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_not_applicable_at_start` | 68 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- `holding_bucket_source_quality_1`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_2`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_3`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_4`: `held_bucket` / `held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_5`: `holding_action` / `WAIT` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_6`: `holding_action` / `holding_action_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_7`: `holding_source_stage` / `scalp_sim_holding_started` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_8`: `profit_band` / `profit_lt_neg070` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_9`: `profit_band` / `profit_pos150_pos300_plus` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_10`: `profit_band` / `profit_neg070_neg010` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Exit Bucket Attribution

- decision_authority: `adm_ldm_exit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'exit_rows': 2595, 'source_row_count': 2595, 'bucket_count': 48, 'joined_sample': 1570, 'source_quality_adjusted_ev_pct': -1.0603, 'source_quality_gate': 'pass', 'unknown_reason_counts': {'not_applicable': 3, 'join_gap': 8, 'missing_source_field': 1}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 114 | 114 | -1.1906 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 34 | 34 | -1.8896 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 29 | 29 | -0.4769 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 23 | 23 | -1.4287 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 22 | 22 | -2.6608 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 18 | 18 | -0.5554 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 14 | 14 | -1.0843 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 12 | 12 | -1.8594 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 11 | 11 | 0.2409 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 6 | 6 | -0.3497 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 6 | 6 | 1.6169 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 4 | 4 | -0.3281 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 4 | 4 | -0.8329 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 4 | 4 | 3.4296 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 3 | 3 | -1.1925 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 2 | 2 | 0.2737 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` | 2 | 2 | 1.125 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 2 | 2 | -0.3493 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos150_pos300` | 1 | 1 | 1.83 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_ai_momentum_decay|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 1 | 1 | 0.3545 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 1 | 1 | -0.9955 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 1 | 1 | 0.7002 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_euphoria_context_noop|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown` | 195 | 0 | None | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown` | 2086 | 0 | None | `source_quality_workorder` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 157 | 157 | -0.9097 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 70 | 70 | -1.8507 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 52 | 52 | -0.3603 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 26 | 26 | -1.442 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 2290 | 9 | -0.4825 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 157 | 157 | -0.9097 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 66 | 66 | -1.3549 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 57 | 57 | -1.9949 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 24 | 24 | 0.7082 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 9 | 9 | -0.4825 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_ai_momentum_decay` | 1 | 1 | 0.3545 | `hold_sample` |
| `exit_rule` | `exit_rule_unknown` | 2281 | 0 | None | `source_quality_workorder` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 157 | 157 | -0.9097 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 148 | 148 | -1.2553 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 9 | 9 | -0.4825 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_euphoria_context_noop` | 195 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- `exit_bucket_source_quality_1`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_2`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_3`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_4`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_5`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_6`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_7`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_8`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_9`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_10`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `incremental_notional_ev_pct`
- summary: `{'scale_in_rows': 4132, 'bucket_count': 712, 'edge_bucket_count': 0, 'actionable_bucket_count': 0, 'runtime_authority_blocked_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'arm_counts': {'PYRAMID': 884, 'AVG_DOWN': 3248}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_70p` | 1851 | 1851 | None | -0.5298 | 0.2712 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 770 | 770 | None | -0.5423 | 0.174 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 723 | 723 | None | -0.571 | 0.177 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 370 | 370 | None | -0.6748 | 0.0865 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 365 | 365 | None | -0.4897 | 0.1507 | `hold_sample` |
| `ai_score_band` | `score_unknown` | 53 | 2 | None | -3.07 | 0.0 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 4079 | 4079 | None | -0.549 | 0.2086 | `hold_sample` |
| `ai_score_source` | `sim_scale_in_source_not_scored` | 2 | 2 | None | -3.07 | 0.0 | `hold_sample` |
| `ai_score_source` | `stage_rule_backfilled` | 51 | 0 | None | None | None | `hold_sample` |
| `arm` | `AVG_DOWN` | 3248 | 3228 | None | -0.8763 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 884 | 853 | None | 0.688 | 0.9988 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 2358 | 2338 | None | -1.0702 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 890 | 890 | None | -0.3668 | 0.0 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 884 | 853 | None | 0.688 | 0.9988 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 707 | 707 | None | 0.537 | 1.0 | `hold_sample` |
| `blocker_reason` | `add_judgment_locked` | 257 | 257 | None | -0.4075 | 0.1323 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 184 | 184 | None | -0.9299 | 0.1413 | `hold_sample` |
| `blocker_reason` | `scalping_buy_window_blocked` | 117 | 117 | None | -0.5143 | 0.188 | `hold_sample` |
| `blocker_reason` | `low_broken` | 104 | 104 | None | -0.4132 | 0.0 | `hold_sample` |
| `blocker_reason` | `ok` | 96 | 96 | None | -2.6677 | 0.0 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `adm_ldm_overnight_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'overnight_rows': 18, 'bucket_count': 25, 'actionable_bucket_count': 9, 'runtime_candidate_count': 0, 'workorder_count': 9, 'status_counts': {'HOLD_OVERNIGHT': 9, 'SELL_TODAY': 9}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 4 | 4 | -0.3281 | -0.4375 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 3 | 3 | -1.1925 | -1.59 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 2 | 2 | 0.2737 | 0.365 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_lt_neg070` | 3 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg010_pos080` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 4 | 0 | None | None | None | `hold_sample` |
| `confidence_band` | `confidence_070p` | 18 | 9 | -0.4825 | -0.6433 | 0.2222 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s_plus` | 10 | 5 | -0.477 | -0.636 | 0.2 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s` | 6 | 3 | -0.595 | -0.7933 | 0.3333 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `overnight_action` | `SELL_TODAY` | 18 | 9 | -0.4825 | -0.6433 | 0.2222 | `candidate_tighten_or_exclude` |
| `overnight_status` | `SELL_TODAY` | 9 | 9 | -0.4825 | -0.6433 | 0.2222 | `candidate_tighten_or_exclude` |
| `overnight_status` | `HOLD_OVERNIGHT` | 9 | 0 | None | None | None | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 14 | 7 | -0.6986 | -0.9314 | 0.0 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_zero_pos080` | 4 | 2 | 0.2737 | 0.365 | 1.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 14 | 7 | -0.5711 | -0.7614 | 0.2857 | `candidate_tighten_or_exclude` |
| `price_source` | `buy_price_fallback` | 4 | 2 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 8 | 4 | -0.3281 | -0.4375 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 6 | 3 | -1.1925 | -1.59 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 4 | 2 | 0.2737 | 0.365 | 1.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 18 | 9 | -0.4825 | -0.6433 | 0.2222 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 9 | 9 | -0.4825 | -0.6433 | 0.2222 | `candidate_tighten_or_exclude` |
| `stage` | `exit` | 9 | 9 | -0.4825 | -0.6433 | 0.2222 | `candidate_tighten_or_exclude` |

### Overnight Bucket Runtime Approval Candidates

- none

### Overnight Bucket Workorders

- `overnight_bucket_source_quality_1`: `confidence_band` / `confidence_070p` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_2`: `held_bucket` / `held_600_1800s_plus` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_3`: `overnight_action` / `SELL_TODAY` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_4`: `overnight_status` / `SELL_TODAY` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_5`: `peak_profit_band` / `peak_lt_zero` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_6`: `price_source` / `holding_price_samples_last` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_7`: `source_quality_gate` / `overnight_decision_coverage` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_8`: `source_stage` / `scalp_sim_overnight_sell_today` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_9`: `stage` / `exit` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`

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
