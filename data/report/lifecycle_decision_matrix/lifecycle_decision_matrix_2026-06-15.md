# Lifecycle Decision Matrix - 2026-06-15

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-15`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `19534`
- source_rows_total: `32459`
- retained_rows: `19534`
- dropped_rows_by_source: `{'dedupe': 12925}`
- joined_rows: `17684`
- policy_pass_count: `5`
- promote_ready_count: `1`
- entry_bucket_actionable_count: `16`
- entry_bucket_runtime_candidate_count: `10`
- holding_bucket_count/workorders: `36` / `10`
- exit_bucket_count/workorders: `54` / `10`
- scale_in_bucket_actionable_count: `0`
- scale_in_bucket_runtime_candidate_count: `0`
- overnight_bucket_actionable_count: `13`
- overnight_bucket_runtime_candidate_count: `9`
- lifecycle_flow_bucket_count: `120`
- lifecycle_flow_complete_count: `79`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `0` / `79` / `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0044`
- incomplete_flow_reason_counts: `{'missing_entry': 17351, 'missing_holding': 17663, 'missing_exit': 17206, 'missing_submit': 17660, 'postclose_exit_without_entry': 511, 'candidate_id_only': 17362, 'sim_record_id_only': 234, 'scale_in_noise_only': 16819}`
- bucket_directed_sim_probe: `{'observed_row_count': 1535, 'matched_row_count': 72, 'background_row_count': 1463, 'matched_unique_source_bucket_count': 2, 'match_status_counts': {'matched': 72, 'no_match': 246, 'not_instrumented': 535, 'policy_disabled': 682}, 'matched_classification_state_counts': {'lifecycle_flow_sim_probe_candidate': 72}, 'primary_source': 'matched_bucket_directed_sim_probe_only', 'background_source': 'unmatched_or_policy_missing_sim_observation', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 1, 'route_counts': {'bounded_auxiliary_weight': 1, 'hold_sample': 4}, 'quality_counts': {'observational_only_pending_outcome': 1, 'hold_sample': 4}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 1280 | 111 | 0.6496 | 0.9626 | `pass` | `BUY_DEFENSIVE` | True |
| `submit` | 314 | 141 | -0.2235 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 288 | 141 | -0.6796 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 17025 | 16964 | -0.6036 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 627 | 327 | -0.7974 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 17796, 'complete_flow_count': 79, 'direct_sim_record_complete_flow_count': 0, 'adm_bridge_complete_flow_count': 79, 'fallback_complete_flow_count': 0, 'incomplete_flow_count': 17717, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 19534, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0044, 'complete_flow_conversion_denominator': 611, 'complete_flow_conversion_rate': 0.1293, 'active_priority_incomplete_seed_count': 366, 'scale_in_followup_event_count': 17025, 'scale_in_unique_flow_count': 13478, 'scale_in_noise_flow_count': 16819, 'denominator_exclusion_counts': {'scale_in_noise_flow_excluded': 16819, 'active_priority_incomplete_seed_excluded': 366}, 'conversion_blocker_reason_counts': {'missing_entry': 532, 'missing_holding': 511, 'missing_exit': 21, 'postclose_exit_without_entry': 511, 'missing_submit': 508, 'sim_record_id_only': 208, 'candidate_id_only': 300}, 'observation_seed_reason_counts': {'missing_submit': 17152, 'missing_holding': 17152, 'missing_exit': 17185, 'candidate_id_only': 17062, 'missing_entry': 16819, 'sim_record_id_only': 26, 'scale_in_noise_only': 16819}, 'join_contract_blocked': False, 'bundle_ev_tuning_state': 'ready_for_bundle_ev_tuning', 'top_incomplete_reason': 'missing_holding', 'stage_identity': {'entry': {'source_row_count': 1280, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 1011, 'candidate_id': 269}, 'identity_join_rate': 1.0}, 'submit': {'source_row_count': 314, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 314}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 288, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 273, 'exact_sim_record_id': 15}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 17025, 'identity_missing_count': 0, 'identity_quality_counts': {'exact_sim_record_id': 232, 'candidate_id': 16793}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 627, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 107, 'exact_sim_record_id': 220, 'candidate_id': 300}, 'identity_join_rate': 1.0}}, 'required_stage_source_counts': {'entry': 1280, 'submit': 314, 'holding': 288, 'exit': 627}, 'incomplete_flow_reason_counts': {'missing_entry': 17351, 'missing_holding': 17663, 'missing_exit': 17206, 'missing_submit': 17660, 'postclose_exit_without_entry': 511, 'candidate_id_only': 17362, 'sim_record_id_only': 234, 'scale_in_noise_only': 16819}, 'bucket_count': 120, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:3cbb81cd02` | 3 | 3 | -0.5904 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:89e49a11bc` | 3 | 3 | -1.4776 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:67138f9e63` | 3 | 3 | -0.7057 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:f7df4238eb` | 3 | 3 | 0.9802 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:8050d08a3f` | 2 | 2 | -2.1179 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:b705884db4` | 2 | 2 | -0.3949 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:a6f1cf48c2` | 2 | 2 | -2.6105 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:81b7841fa7` | 2 | 2 | -1.2872 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:9842d687d5` | 2 | 2 | -0.3557 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:6d56b1e4d8` | 2 | 2 | -1.068 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:b9576c8a52` | 2 | 2 | -0.7984 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:88bef343e5` | 1 | 1 | -0.8237 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:b33b664d62` | 1 | 1 | -0.784 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:4fad8db7ce` | 1 | 1 | -0.8067 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:ee62c5b5e1` | 1 | 1 | 1.2181 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:0ea7ad009c` | 1 | 1 | -1.5909 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:1b4e4b3128` | 1 | 1 | -1.5795 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:84b7dde4a3` | 1 | 1 | -0.7538 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:06a029c7a2` | 1 | 1 | -1.4484 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:a7ad859ad1` | 1 | 1 | -3.0748 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 1280, 'bucket_count': 181, 'actionable_bucket_count': 16, 'source_quality_blocked_bucket_count': 0, 'runtime_candidate_count': 10, 'workorder_count': 10}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `NO_BUY_AI` | 989 | 61 | 0.0942 | -1.0628 | 0.2131 | `hold_no_edge` |
| `chosen_action` | `WAIT_REQUOTE` | 47 | 47 | 1.47 | 2.1299 | 0.617 | `candidate_recovery_or_relax` |
| `chosen_action` | `BUY_NOW` | 10 | 3 | -0.9108 | -2.33 | 0.0 | `hold_sample` |
| `chosen_action` | `ALLOW_BOTTOMING_ENTRY` | 4 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `ALLOW_LEVEL1_RISK_OFF_ENTRY` | 218 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_SOURCE_QUALITY` | 12 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 132 | 13 | 0.1197 | -1.4431 | 0.1538 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 84 | 12 | 0.7228 | -1.1917 | 0.25 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 11 | 11 | 1.08 | 1.1747 | 0.4545 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 11 | 11 | 2.2375 | 3.0322 | 0.9091 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 188 | 10 | 0.1348 | -1.406 | 0.1 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 7 | 7 | -0.0051 | -0.1618 | 0.4286 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 6 | 6 | 1.3155 | 1.8716 | 0.6667 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 35 | 5 | 0.5743 | 1.826 | 0.8 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 88 | 4 | -0.2343 | -1.615 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 75 | 4 | 0.0078 | -1.55 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 20 | 3 | -1.0617 | 0.28 | 0.6667 | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 3 | 3 | -0.3453 | -0.4341 | 0.3333 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 13 | 2 | 0.3328 | -1.02 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 2 | 2 | -0.779 | -1.012 | 0.0 | `hold_sample` |
| `exit_rule` | `exit_unknown` | 1216 | 47 | 1.47 | 2.1299 | 0.617 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_soft_stop_pct` | 35 | 35 | 0.1821 | -1.9063 | 0.0 | `hold_no_edge` |
| `exit_rule` | `scalp_trailing_take_profit` | 12 | 12 | -0.2159 | 2.1675 | 1.0 | `hold_no_edge` |
| `exit_rule` | `scalp_hard_stop_pct` | 10 | 10 | -0.3652 | -2.718 | 0.0 | `candidate_tighten_or_exclude` |
| `liquidity_bucket` | `liquidity_high` | 941 | 111 | 0.6496 | 0.2548 | 0.3784 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 936 | 94 | 0.6127 | -0.0432 | 0.3617 | `candidate_recovery_or_relax` |
| `score_band` | `score_60_62` | 680 | 41 | 0.0476 | -1.3273 | 0.1951 | `hold_no_edge` |
| `score_band` | `score_66_69` | 61 | 25 | 0.8184 | 0.9404 | 0.44 | `candidate_recovery_or_relax` |
| `score_band` | `score_70p` | 97 | 24 | 1.5223 | 2.3272 | 0.7083 | `candidate_recovery_or_relax` |
| `score_band` | `score_lt60` | 343 | 13 | 0.1512 | -0.2715 | 0.3077 | `hold_no_edge` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 852 | 64 | 0.0471 | -1.1222 | 0.2031 | `hold_no_edge` |
| `source_stage` | `wait6579_ev_cohort` | 47 | 47 | 1.47 | 2.1299 | 0.617 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh` | 939 | 64 | 0.0471 | -1.1222 | 0.2031 | `hold_no_edge` |
| `stale_bucket` | `fresh_or_unflagged` | 269 | 47 | 1.47 | 2.1299 | 0.617 | `candidate_recovery_or_relax` |
| `strength_bucket` | `weak_strength_momentum` | 829 | 58 | 0.3459 | -0.6806 | 0.2759 | `candidate_recovery_or_relax` |
| `strength_bucket` | `strong_strength_momentum` | 155 | 48 | 1.1177 | 1.556 | 0.5208 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_0900_1000` | 316 | 45 | 0.9235 | 0.9506 | 0.4667 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_1000_1200` | 476 | 43 | 0.7742 | 0.4902 | 0.4186 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_1200_1400` | 415 | 22 | -0.0626 | -1.4936 | 0.1364 | `hold_no_edge` |

### Entry Bucket Runtime Approval Candidates

- `entry_bucket_7`: `liquidity_bucket` / `liquidity_high` -> `candidate_recovery_or_relax`
- `entry_bucket_8`: `overbought_bucket` / `overbought_normal` -> `candidate_recovery_or_relax`
- `entry_bucket_9`: `score_band` / `score_66_69` -> `candidate_recovery_or_relax`
- `entry_bucket_10`: `score_band` / `score_70p` -> `candidate_recovery_or_relax`
- `entry_bucket_11`: `source_stage` / `wait6579_ev_cohort` -> `candidate_recovery_or_relax`
- `entry_bucket_12`: `stale_bucket` / `fresh_or_unflagged` -> `candidate_recovery_or_relax`
- `entry_bucket_13`: `strength_bucket` / `weak_strength_momentum` -> `candidate_recovery_or_relax`
- `entry_bucket_14`: `strength_bucket` / `strong_strength_momentum` -> `candidate_recovery_or_relax`
- `entry_bucket_15`: `time_bucket` / `time_0900_1000` -> `candidate_recovery_or_relax`
- `entry_bucket_16`: `time_bucket` / `time_1000_1200` -> `candidate_recovery_or_relax`

### Entry Bucket Workorders

- `entry_bucket_source_quality_1`: `chosen_action` / `WAIT_REQUOTE` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_2`: `combo_entry_spot` / `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_3`: `combo_entry_spot` / `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_4`: `combo_entry_spot` / `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_5`: `exit_rule` / `exit_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_6`: `exit_rule` / `scalp_hard_stop_pct` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_7`: `liquidity_bucket` / `liquidity_high` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_8`: `overbought_bucket` / `overbought_normal` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_9`: `score_band` / `score_66_69` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_10`: `score_band` / `score_70p` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`

## Submit Bucket Attribution

- decision_authority: `adm_ldm_submit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'submit_rows': 314, 'bucket_count': 59, 'contract_gap_count': 0, 'workorder_count': 0, 'runtime_candidate_count': 0, 'real_submitted_row_count': 9, 'missing_broker_order_key_count': 0, 'bot_history_broker_order_key_backfill_candidate_count': 0, 'bot_history_broker_order_key_backfill_full_coverage': False, 'bot_history_broker_order_key_exact_mapping_count': 0, 'bot_history_broker_order_key_exact_mapping_full_coverage': False, 'post_submit_provenance_join_resolution': 'no_gap_broker_order_key_present_or_no_missing_rows', 'bot_history_broker_order_key_backfill_candidates': [], 'missing_broker_order_key_rate': 0.0, 'post_submit_provenance_join_gap_raw': False, 'post_submit_provenance_join_gap': False}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 305 | 141 | -0.2235 | `keep_collecting` |
| `actual_order_submitted` | `true` | 9 | 0 | None | `keep_collecting` |
| `broker_order_forbidden` | `true` | 305 | 141 | -0.2235 | `keep_collecting` |
| `broker_order_forbidden` | `false` | 9 | 0 | None | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 93 | 46 | 0.1091 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 60 | 31 | -0.3451 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 57 | 30 | -0.7322 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=false|submitted=false` | 27 | 13 | 0.3252 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 21 | 14 | -0.1065 | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=block_False|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=latency_unknown|fill=false|submitted=false` | 18 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=pre_submit_liquidity_guard_block|revalidation=block_False|quote_age=quote_age_unknown|liquidity=below_min_liquidity|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=latency_unknown|fill=false|submitted=false` | 12 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=block_False|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=latency_unknown|fill=false|submitted=true` | 8 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 5 | 3 | -0.9937 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 4 | 2 | -0.0331 | `source_quality_workorder` |
| `combo_submit_quality` | `source=pre_submit_liquidity_guard_block|revalidation=block_False|quote_age=quote_age_unknown|liquidity=below_min_liquidity|liquidity_guard=liquidity_guard_unknown|overbought=overbought_ok|latency=latency_unknown|fill=false|submitted=false` | 2 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 2 | 1 | -0.575 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 2 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=block_False|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_ok|latency=latency_unknown|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=false|submitted=false` | 1 | 1 | -2.9869 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `latency_reason` | `scalp_live_simulator` | 273 | 141 | -0.2235 | `keep_collecting` |
| `latency_reason` | `latency_reason_unknown` | 41 | 0 | None | `source_quality_workorder` |
| `latency_state` | `simulated` | 273 | 141 | -0.2235 | `keep_collecting` |
| `latency_state` | `latency_unknown` | 41 | 0 | None | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_ok` | 185 | 93 | -0.0484 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 102 | 48 | -0.5627 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_not_available` | 27 | 0 | None | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 185 | 93 | -0.0484 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 88 | 48 | -0.5627 | `keep_collecting` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 41 | 0 | None | `source_quality_workorder` |
| `overbought_bucket` | `overbought_ok` | 236 | 122 | -0.2633 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 40 | 19 | 0.0318 | `keep_collecting` |
| `overbought_bucket` | `overbought_not_available` | 38 | 0 | None | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 273 | 141 | -0.2235 | `keep_collecting` |
| `overbought_guard_action` | `overbought_guard_unknown` | 41 | 0 | None | `source_quality_workorder` |
| `price_below_bid_bucket` | `not_below_bid` | 206 | 112 | -0.1011 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 49 | 25 | -0.7588 | `keep_collecting` |
| `price_below_bid_bucket` | `price_below_bid_unknown` | 41 | 0 | None | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 18 | 4 | -0.3042 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 177 | 96 | -0.0352 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 288, 'source_row_count': 288, 'bucket_count': 36, 'joined_sample': 705, 'source_quality_adjusted_ev_pct': -0.6796, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 85 | 85 | -0.9838 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 21 | 21 | -1.3612 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 8 | 8 | 0.3694 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 6 | 6 | 1.8908 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 5 | 5 | -0.472 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 5 | 5 | 0.9349 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 3 | 3 | -0.2779 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 3 | 3 | -0.142 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 2 | 2 | 0.045 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 1 | 1 | -0.19 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | 0.4265 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 0.6983 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 91 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 40 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 5 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 4 | 0 | None | `hold_sample` |
| `held_bucket` | `held_not_applicable_at_start` | 273 | 141 | -0.6796 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s` | 3 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 12 | 0 | None | `hold_sample` |
| `holding_action` | `WAIT` | 203 | 112 | -0.6057 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 69 | 29 | -0.965 | `candidate_tighten_or_exclude` |
| `holding_action` | `BUY` | 1 | 0 | None | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 15 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 273 | 141 | -0.6796 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 15 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 112 | 106 | -1.0586 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 9 | 9 | 0.3758 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300` | 8 | 8 | 0.5311 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300_plus` | 7 | 7 | 1.7204 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 12 | 6 | -0.425 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 8 | 5 | -0.1488 | `hold_no_edge` |
| `profit_band` | `profit_not_applicable_at_start` | 132 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- `holding_bucket_source_quality_1`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_2`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_3`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_4`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_5`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_6`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_7`: `held_bucket` / `held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_8`: `holding_action` / `WAIT` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_9`: `holding_action` / `holding_action_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_10`: `holding_source_stage` / `scalp_sim_holding_started` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Exit Bucket Attribution

- decision_authority: `adm_ldm_exit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'exit_rows': 627, 'source_row_count': 627, 'bucket_count': 54, 'joined_sample': 1635, 'source_quality_adjusted_ev_pct': -0.7974, 'source_quality_gate': 'pass', 'unknown_reason_counts': {'not_applicable': 3, 'join_gap': 8, 'missing_source_field': 1}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 158 | 158 | -1.0649 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 42 | 42 | -0.585 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 26 | 26 | -0.9641 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 18 | 18 | -0.6668 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 14 | 14 | -1.4778 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 10 | 10 | -1.0809 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 9 | 9 | -2.1314 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 6 | 6 | -0.7325 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 6 | 6 | -0.3188 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 6 | 6 | -0.3721 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 5 | 5 | 0.3808 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 4 | 4 | 2.3538 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 3 | 3 | 0.215 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 3 | 3 | 0.1768 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` | 2 | 2 | 1.0 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos150_pos300_plus` | 2 | 2 | 4.3727 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 2 | 2 | -1.3098 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 2 | 2 | 0.6577 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos150_pos300` | 1 | 1 | 2.39 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | -0.4042 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_preset_tp_touch|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 1 | 1 | 1.6373 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 1 | 1 | 0.6983 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 1 | 1 | 1.2181 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 1 | 1 | 0.6105 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 1 | 1 | -0.8019 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300` | 1 | 1 | 0.0966 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300_plus` | 1 | 1 | 0.9647 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_euphoria_context_noop|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown` | 253 | 0 | None | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown` | 47 | 0 | None | `source_quality_workorder` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 205 | 205 | -0.8765 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 39 | 39 | -0.7268 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 36 | 36 | -0.2871 | `hold_no_edge` |
| `exit_outcome` | `GOOD_EXIT` | 32 | 32 | -1.1481 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 315 | 15 | -0.3775 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 205 | 205 | -0.8765 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 58 | 58 | -0.9958 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 21 | 21 | -1.5529 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 20 | 20 | 0.7976 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 15 | 15 | -0.3775 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 7 | 7 | -0.3767 | `candidate_tighten_or_exclude` |

### Exit Bucket Attribution Workorders

- `exit_bucket_source_quality_1`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_2`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_3`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_4`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_5`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_6`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_7`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_8`: `combo_exit_result` / `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_9`: `combo_exit_result` / `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_10`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `incremental_notional_ev_pct`
- summary: `{'scale_in_rows': 17025, 'bucket_count': 2208, 'edge_bucket_count': 0, 'actionable_bucket_count': 0, 'runtime_authority_blocked_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'arm_counts': {'PYRAMID': 1957, 'AVG_DOWN': 15068}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_70p` | 9361 | 9361 | None | -0.663 | 0.1036 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 2979 | 2979 | None | -0.6709 | 0.1101 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 1885 | 1885 | None | -0.6682 | 0.1013 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 1604 | 1604 | None | -0.6199 | 0.1608 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 1134 | 1134 | None | -0.5598 | 0.1226 | `hold_sample` |
| `ai_score_band` | `score_unknown` | 62 | 1 | None | 1.02 | 1.0 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 16963 | 16963 | None | -0.654 | 0.1112 | `hold_sample` |
| `ai_score_source` | `sim_scale_in_source_not_scored` | 1 | 1 | None | 1.02 | 1.0 | `hold_sample` |
| `ai_score_source` | `stage_rule_backfilled` | 61 | 0 | None | None | None | `hold_sample` |
| `arm` | `AVG_DOWN` | 15068 | 15033 | None | -0.8057 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 1957 | 1931 | None | 0.5282 | 0.9772 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 10906 | 10871 | None | -0.9406 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 4162 | 4162 | None | -0.4534 | 0.0 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 1957 | 1931 | None | 0.5282 | 0.9772 | `hold_sample` |
| `blocker_reason` | `add_judgment_locked` | 1940 | 1940 | None | -0.3867 | 0.1077 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 1592 | 1592 | None | 0.5081 | 0.9805 | `hold_sample` |
| `blocker_reason` | `low_broken` | 395 | 395 | None | -0.5131 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.98)` | 338 | 338 | None | -0.98 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 231 | 231 | None | -0.7184 | 0.039 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.73)` | 223 | 223 | None | -0.73 | 0.0 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `adm_ldm_overnight_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'overnight_rows': 30, 'bucket_count': 23, 'actionable_bucket_count': 13, 'runtime_candidate_count': 9, 'workorder_count': 10, 'status_counts': {'HOLD_OVERNIGHT': 15, 'SELL_TODAY': 15}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 6 | 6 | -0.7325 | -0.9767 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 6 | 6 | -0.3188 | -0.425 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 3 | 3 | 0.215 | 0.2867 | 0.6667 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_lt_neg070` | 6 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg010_pos080` | 3 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 6 | 0 | None | None | None | `hold_sample` |
| `confidence_band` | `confidence_070p` | 30 | 15 | -0.3775 | -0.5033 | 0.1333 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s_plus` | 24 | 12 | -0.3662 | -0.4883 | 0.1667 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s` | 6 | 3 | -0.4225 | -0.5633 | 0.0 | `hold_sample` |
| `overnight_action` | `SELL_TODAY` | 30 | 15 | -0.3775 | -0.5033 | 0.1333 | `candidate_tighten_or_exclude` |
| `overnight_status` | `SELL_TODAY` | 15 | 15 | -0.3775 | -0.5033 | 0.1333 | `candidate_tighten_or_exclude` |
| `overnight_status` | `HOLD_OVERNIGHT` | 15 | 0 | None | None | None | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 26 | 13 | -0.4863 | -0.6485 | 0.0 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_zero_pos080` | 4 | 2 | 0.33 | 0.44 | 1.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 30 | 15 | -0.3775 | -0.5033 | 0.1333 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 12 | 6 | -0.7325 | -0.9767 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 12 | 6 | -0.3188 | -0.425 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 6 | 3 | 0.215 | 0.2867 | 0.6667 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 30 | 15 | -0.3775 | -0.5033 | 0.1333 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 15 | 15 | -0.3775 | -0.5033 | 0.1333 | `candidate_tighten_or_exclude` |
| `stage` | `exit` | 15 | 15 | -0.3775 | -0.5033 | 0.1333 | `candidate_tighten_or_exclude` |

### Overnight Bucket Runtime Approval Candidates

- `overnight_bucket_3`: `confidence_band` / `confidence_070p` -> `candidate_tighten_or_exclude`
- `overnight_bucket_4`: `held_bucket` / `held_600_1800s_plus` -> `candidate_tighten_or_exclude`
- `overnight_bucket_5`: `overnight_action` / `SELL_TODAY` -> `candidate_tighten_or_exclude`
- `overnight_bucket_6`: `overnight_status` / `SELL_TODAY` -> `candidate_tighten_or_exclude`
- `overnight_bucket_7`: `peak_profit_band` / `peak_lt_zero` -> `candidate_tighten_or_exclude`
- `overnight_bucket_8`: `price_source` / `holding_price_samples_last` -> `candidate_tighten_or_exclude`
- `overnight_bucket_11`: `source_quality_gate` / `overnight_decision_coverage` -> `candidate_tighten_or_exclude`
- `overnight_bucket_12`: `source_stage` / `scalp_sim_overnight_sell_today` -> `candidate_tighten_or_exclude`
- `overnight_bucket_13`: `stage` / `exit` -> `candidate_tighten_or_exclude`

### Overnight Bucket Workorders

- `overnight_bucket_source_quality_1`: `combo_overnight_decision` / `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_2`: `combo_overnight_decision` / `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_3`: `confidence_band` / `confidence_070p` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_4`: `held_bucket` / `held_600_1800s_plus` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_5`: `overnight_action` / `SELL_TODAY` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_6`: `overnight_status` / `SELL_TODAY` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_7`: `peak_profit_band` / `peak_lt_zero` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_8`: `price_source` / `holding_price_samples_last` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_9`: `profit_band` / `profit_lt_neg070` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_10`: `profit_band` / `profit_neg070_neg010` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`

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
