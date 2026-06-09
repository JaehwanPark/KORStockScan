# Lifecycle Decision Matrix - 2026-06-09

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-09`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `20862`
- source_rows_total: `36345`
- retained_rows: `20862`
- dropped_rows_by_source: `{'dedupe': 15483}`
- joined_rows: `19325`
- policy_pass_count: `5`
- promote_ready_count: `1`
- entry_bucket_actionable_count: `30`
- entry_bucket_runtime_candidate_count: `10`
- holding_bucket_count/workorders: `35` / `10`
- exit_bucket_count/workorders: `62` / `10`
- scale_in_bucket_actionable_count: `207`
- scale_in_bucket_runtime_candidate_count: `10`
- overnight_bucket_actionable_count: `11`
- overnight_bucket_runtime_candidate_count: `8`
- lifecycle_flow_bucket_count: `153`
- lifecycle_flow_complete_count: `137`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `0` / `137` / `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0072`
- incomplete_flow_reason_counts: `{'missing_submit': 18795, 'missing_holding': 18786, 'missing_exit': 18307, 'missing_entry': 18334, 'postclose_exit_without_entry': 500, 'candidate_id_only': 18459, 'scale_in_noise_only': 17827, 'sim_record_id_only': 246}`
- bucket_directed_sim_probe: `{'observed_row_count': 1603, 'matched_row_count': 0, 'background_row_count': 1603, 'matched_unique_source_bucket_count': 0, 'match_status_counts': {'no_match': 1072, 'not_instrumented': 531}, 'matched_classification_state_counts': {}, 'primary_source': 'matched_bucket_directed_sim_probe_only', 'background_source': 'unmatched_or_policy_missing_sim_observation', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 1, 'route_counts': {'bounded_auxiliary_weight': 1, 'hold_sample': 4}, 'quality_counts': {'observational_only_pending_outcome': 1, 'hold_sample': 4}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 1429 | 201 | 1.3021 | 1.0 | `pass` | `BUY_DEFENSIVE` | True |
| `submit` | 302 | 281 | -0.4741 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 297 | 281 | -0.8262 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 18054 | 18053 | -0.3088 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 780 | 509 | -0.9208 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 18944, 'complete_flow_count': 137, 'direct_sim_record_complete_flow_count': 0, 'adm_bridge_complete_flow_count': 137, 'fallback_complete_flow_count': 0, 'incomplete_flow_count': 18807, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 20862, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0072, 'complete_flow_conversion_denominator': 644, 'complete_flow_conversion_rate': 0.2127, 'active_priority_incomplete_seed_count': 473, 'scale_in_followup_event_count': 18054, 'scale_in_unique_flow_count': 13882, 'scale_in_noise_flow_count': 17827, 'denominator_exclusion_counts': {'scale_in_noise_flow_excluded': 17827, 'active_priority_incomplete_seed_excluded': 473}, 'conversion_blocker_reason_counts': {'missing_entry': 507, 'missing_holding': 490, 'missing_exit': 7, 'postclose_exit_without_entry': 500, 'missing_submit': 499, 'sim_record_id_only': 228, 'candidate_id_only': 271}, 'observation_seed_reason_counts': {'missing_submit': 18296, 'missing_holding': 18296, 'missing_exit': 18300, 'candidate_id_only': 18188, 'missing_entry': 17827, 'scale_in_noise_only': 17827, 'sim_record_id_only': 18}, 'join_contract_blocked': False, 'bundle_ev_tuning_state': 'ready_for_bundle_ev_tuning', 'top_incomplete_reason': 'missing_submit', 'stage_identity': {'entry': {'source_row_count': 1429, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 1050, 'candidate_id': 379}, 'identity_join_rate': 1.0}, 'submit': {'source_row_count': 302, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 302}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 297, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 281, 'exact_sim_record_id': 16}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 18054, 'identity_missing_count': 0, 'identity_quality_counts': {'candidate_id': 17809, 'exact_sim_record_id': 245}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 780, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 265, 'exact_sim_record_id': 244, 'candidate_id': 271}, 'identity_join_rate': 1.0}}, 'required_stage_source_counts': {'entry': 1429, 'submit': 302, 'holding': 297, 'exit': 780}, 'incomplete_flow_reason_counts': {'missing_submit': 18795, 'missing_holding': 18786, 'missing_exit': 18307, 'missing_entry': 18334, 'postclose_exit_without_entry': 500, 'candidate_id_only': 18459, 'scale_in_noise_only': 17827, 'sim_record_id_only': 246}, 'bucket_count': 153, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:8050d08a3f` | 6 | 6 | -1.771 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:fddb29efa4` | 3 | 3 | -1.0195 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:8b8602048c` | 3 | 3 | -0.7941 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:3cbb81cd02` | 3 | 3 | -1.3164 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:b705884db4` | 3 | 3 | -0.4437 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9d8cac316e` | 3 | 3 | -0.549 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:84b7dde4a3` | 2 | 2 | -1.8026 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:05807447b7` | 2 | 2 | -0.8057 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:8e26d387af` | 2 | 2 | -1.1486 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:f3928c3e95` | 2 | 2 | -1.1929 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:67138f9e63` | 2 | 2 | -0.9801 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:84461e0e65` | 2 | 2 | 2.6813 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:f0874e9a2a` | 2 | 2 | -1.9472 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:81b7841fa7` | 2 | 2 | -1.0663 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:6d56b1e4d8` | 2 | 2 | -1.2845 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:c6e869aefc` | 2 | 2 | -1.0232 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:2de07aaa23` | 1 | 1 | -0.8732 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:022c6f8c95` | 1 | 1 | -0.7642 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:7f4b207c82` | 1 | 1 | 0.9154 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:6bd655acf4` | 1 | 1 | 0.0409 | `hold_no_edge` | `pass` |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 1429, 'bucket_count': 228, 'actionable_bucket_count': 30, 'source_quality_blocked_bucket_count': 0, 'runtime_candidate_count': 10, 'workorder_count': 10}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `WAIT_REQUOTE` | 114 | 114 | 2.6003 | 4.2172 | 0.7193 | `candidate_recovery_or_relax` |
| `chosen_action` | `NO_BUY_AI` | 1005 | 71 | -0.3604 | -1.0637 | 0.2535 | `candidate_tighten_or_exclude` |
| `chosen_action` | `BUY_NOW` | 20 | 16 | -0.5696 | -0.0838 | 0.5625 | `candidate_tighten_or_exclude` |
| `chosen_action` | `ALLOW_BOTTOMING_ENTRY` | 33 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `ALLOW_LEVEL1_RISK_OFF_ENTRY` | 232 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_SOURCE_QUALITY` | 25 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 35 | 35 | 2.0245 | 3.1219 | 0.6571 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 142 | 17 | -0.1899 | -0.4106 | 0.4118 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 17 | 17 | 1.2487 | 1.7551 | 0.7059 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 41 | 13 | 0.4188 | -2.0792 | 0.0 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 13 | 13 | 1.9824 | 3.3218 | 0.6923 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 13 | 13 | 1.4406 | 2.3363 | 0.6154 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 25 | 10 | -0.558 | -1.009 | 0.3 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 25 | 8 | -0.9984 | 0.4675 | 0.625 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_ok|time=time_1000_1200` | 8 | 8 | 6.0773 | 11.3038 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 5 | 5 | 4.4594 | 6.9518 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 27 | 5 | 0.0487 | -0.672 | 0.4 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 172 | 4 | -1.7768 | -1.32 | 0.25 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 4 | 4 | 2.3085 | 3.0264 | 0.75 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 10 | 4 | -0.1194 | -2.25 | 0.0 | `hold_sample` |
| `exit_rule` | `exit_unknown` | 1342 | 114 | 2.6003 | 4.2172 | 0.7193 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_soft_stop_pct` | 33 | 33 | -0.4719 | -2.0527 | 0.0 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 26 | 26 | -0.6419 | 1.8554 | 1.0 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 18 | 18 | -0.1253 | -2.7856 | 0.0 | `hold_no_edge` |
| `liquidity_bucket` | `liquidity_high` | 983 | 201 | 1.3021 | 2.0095 | 0.5423 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 888 | 146 | 1.062 | 1.3947 | 0.5274 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_ok` | 127 | 27 | 1.9605 | 4.6538 | 0.6667 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_watch` | 131 | 24 | 1.0523 | 0.7465 | 0.4167 | `candidate_recovery_or_relax` |

### Entry Bucket Runtime Approval Candidates

- `entry_bucket_4`: `combo_entry_spot` / `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` -> `candidate_recovery_or_relax`
- `entry_bucket_13`: `liquidity_bucket` / `liquidity_high` -> `candidate_recovery_or_relax`
- `entry_bucket_14`: `overbought_bucket` / `overbought_normal` -> `candidate_recovery_or_relax`
- `entry_bucket_15`: `overbought_bucket` / `overbought_ok` -> `candidate_recovery_or_relax`
- `entry_bucket_16`: `overbought_bucket` / `overbought_watch` -> `candidate_recovery_or_relax`
- `entry_bucket_17`: `score_band` / `score_70p` -> `candidate_recovery_or_relax`
- `entry_bucket_18`: `score_band` / `score_60_62` -> `candidate_tighten_or_exclude`
- `entry_bucket_19`: `score_band` / `score_66_69` -> `candidate_recovery_or_relax`
- `entry_bucket_20`: `score_band` / `score_63_65` -> `candidate_recovery_or_relax`
- `entry_bucket_22`: `source_stage` / `wait6579_ev_cohort` -> `candidate_recovery_or_relax`

### Entry Bucket Workorders

- `entry_bucket_source_quality_1`: `chosen_action` / `WAIT_REQUOTE` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_2`: `chosen_action` / `NO_BUY_AI` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_3`: `chosen_action` / `BUY_NOW` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_4`: `combo_entry_spot` / `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_5`: `combo_entry_spot` / `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_6`: `combo_entry_spot` / `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_7`: `combo_entry_spot` / `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_8`: `combo_entry_spot` / `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_9`: `combo_entry_spot` / `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_10`: `exit_rule` / `exit_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`

## Submit Bucket Attribution

- decision_authority: `adm_ldm_submit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'submit_rows': 302, 'bucket_count': 68, 'contract_gap_count': 0, 'workorder_count': 0, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 296 | 281 | -0.4741 | `keep_collecting` |
| `actual_order_submitted` | `true` | 6 | 0 | None | `keep_collecting` |
| `broker_order_forbidden` | `true` | 296 | 281 | -0.4741 | `keep_collecting` |
| `broker_order_forbidden` | `false` | 6 | 0 | None | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 116 | 116 | -0.4937 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 65 | 65 | -0.2067 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 31 | 31 | -0.6189 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 29 | 29 | -0.9121 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 17 | 17 | -0.2773 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=false|submitted=false` | 8 | 8 | 0.2485 | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=block_False|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_normal|latency=latency_unknown|fill=false|submitted=false` | 7 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=pre_submit_liquidity_guard_block|revalidation=block_False|quote_age=quote_age_unknown|liquidity=below_min_liquidity|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=latency_unknown|fill=false|submitted=false` | 6 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=block_False|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=latency_unknown|fill=false|submitted=true` | 5 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 5 | 5 | -1.3499 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 3 | 3 | -1.1255 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 2 | 2 | -0.123 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 2 | 2 | 0.9453 | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=block_False|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_ok|latency=latency_unknown|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=pre_submit_liquidity_guard_block|revalidation=block_False|quote_age=quote_age_unknown|liquidity=below_min_liquidity|liquidity_guard=liquidity_guard_unknown|overbought=overbought_ok|latency=latency_unknown|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=pre_submit_liquidity_guard_block|revalidation=block_False|quote_age=quote_age_unknown|liquidity=below_min_liquidity|liquidity_guard=liquidity_guard_unknown|overbought=pullback_required|latency=latency_unknown|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=pullback_or_rebreak_not_confirmed|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | -0.0198 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=pullback_or_rebreak_not_confirmed|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | -1.8155 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_overbought_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=pullback_or_rebreak_not_confirmed|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | -3.8312 | `source_quality_workorder` |
| `latency_reason` | `scalp_live_simulator` | 281 | 281 | -0.4741 | `keep_collecting` |
| `latency_reason` | `latency_reason_unknown` | 21 | 0 | None | `source_quality_workorder` |
| `latency_state` | `simulated` | 281 | 281 | -0.4741 | `keep_collecting` |
| `latency_state` | `latency_unknown` | 21 | 0 | None | `source_quality_workorder` |
| `liquidity_bucket` | `below_min_liquidity` | 182 | 174 | -0.5661 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 107 | 107 | -0.3244 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_not_available` | 13 | 0 | None | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 174 | 174 | -0.5661 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 107 | 107 | -0.3244 | `keep_collecting` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 21 | 0 | None | `source_quality_workorder` |
| `overbought_bucket` | `overbought_ok` | 246 | 244 | -0.4907 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 34 | 34 | -0.2303 | `keep_collecting` |
| `overbought_bucket` | `overbought_not_available` | 11 | 0 | None | `keep_collecting` |
| `overbought_bucket` | `overbought_normal` | 7 | 0 | None | `keep_collecting` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 3 | 3 | -1.8888 | `keep_collecting` |
| `overbought_bucket` | `pullback_required` | 1 | 0 | None | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 278 | 278 | -0.4588 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 297, 'source_row_count': 297, 'bucket_count': 35, 'joined_sample': 1405, 'source_quality_adjusted_ev_pct': -0.8262, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 128 | 128 | -1.1834 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 65 | 65 | -1.401 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 17 | 17 | 0.2332 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 13 | 13 | 0.1211 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 10 | 10 | 0.0405 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 10 | 10 | -0.2433 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 8 | 8 | -1.5485 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 7 | 7 | 1.5901 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 7 | 7 | 0.4808 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 6 | 6 | 0.2007 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 4 | 4 | -0.2943 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 3 | 3 | -0.207 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 3 | 3 | 1.7803 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 6 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos080_pos150|held=held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos150_pos300|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_not_applicable_at_start` | 281 | 281 | -0.8262 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s` | 6 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 10 | 0 | None | `hold_sample` |
| `holding_action` | `WAIT` | 172 | 172 | -0.7904 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 101 | 101 | -0.8301 | `candidate_tighten_or_exclude` |
| `holding_action` | `BUY` | 8 | 8 | -1.5485 | `candidate_tighten_or_exclude` |
| `holding_action` | `SELL_TODAY` | 16 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 281 | 281 | -0.8262 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 16 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 209 | 201 | -1.2683 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 32 | 30 | 0.1846 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 22 | 20 | -0.1014 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 14 | 13 | 0.3515 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300_plus` | 10 | 10 | 1.6472 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 10 | 7 | -0.2569 | `hold_no_edge` |

### Holding Bucket Attribution Workorders

- `holding_bucket_source_quality_1`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_2`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_3`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_4`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_5`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_6`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_7`: `held_bucket` / `held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_8`: `holding_action` / `WAIT` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_9`: `holding_action` / `holding_action_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_10`: `holding_action` / `BUY` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Exit Bucket Attribution

- decision_authority: `adm_ldm_exit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'exit_rows': 780, 'source_row_count': 780, 'bucket_count': 62, 'joined_sample': 2545, 'source_quality_adjusted_ev_pct': -0.9208, 'source_quality_gate': 'pass', 'unknown_reason_counts': {'not_applicable': 5, 'join_gap': 8, 'missing_source_field': 1}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 179 | 179 | -1.2298 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 43 | 43 | -0.5586 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 36 | 36 | -0.9282 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 34 | 34 | -1.15 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 28 | 28 | -2.0151 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 28 | 28 | -1.4734 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 26 | 26 | -1.7831 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 14 | 14 | -0.4952 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 10 | 10 | -1.5712 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 10 | 10 | -0.7609 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 10 | 10 | -0.3289 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 9 | 9 | 0.5754 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 8 | 8 | -0.8559 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 8 | 8 | 0.134 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 8 | 8 | 0.2584 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 7 | 7 | 0.1443 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 6 | 6 | -0.2316 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 5 | 5 | 2.3209 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 4 | 4 | 0.3525 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 4 | 4 | -0.4827 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 4 | 4 | 0.0007 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 4 | 4 | 0.7389 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 4 | 4 | 0.5794 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300` | 4 | 4 | 0.1824 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 3 | 3 | -0.27 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 2 | 2 | 0.0825 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos080_pos150` | 2 | 2 | 0.7725 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_neg070_neg010` | 2 | 2 | 0.0601 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos150_pos300` | 1 | 1 | 1.14 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` | 1 | 1 | 1.05 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos150_pos300_plus` | 1 | 1 | 3.5695 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_ai_momentum_decay|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 1 | 1 | -0.4789 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_neg070_neg010` | 1 | 1 | -0.5911 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_neg070_neg010` | 1 | 1 | -0.2471 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300_plus` | 1 | 1 | 1.9121 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_euphoria_context_noop|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown` | 263 | 0 | None | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown` | 8 | 0 | None | `source_quality_workorder` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 228 | 228 | -1.0444 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 106 | 106 | -0.4877 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 87 | 87 | -1.3017 | `candidate_tighten_or_exclude` |

### Exit Bucket Attribution Workorders

- `exit_bucket_source_quality_1`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_2`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_3`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_4`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_5`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_6`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_7`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_8`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_9`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_10`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'scale_in_rows': 18054, 'bucket_count': 2265, 'actionable_bucket_count': 207, 'runtime_candidate_count': 10, 'workorder_count': 10, 'arm_counts': {'AVG_DOWN': 12793, 'PYRAMID': 5261}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_70p` | 10663 | 10663 | -0.2879 | -0.3516 | 0.3029 | `hold_no_edge` |
| `ai_score_band` | `score_66_69` | 2554 | 2554 | -0.2905 | -0.3587 | 0.2807 | `hold_no_edge` |
| `ai_score_band` | `score_lt60` | 2107 | 2107 | -0.3662 | -0.4391 | 0.2354 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_60_62` | 1514 | 1514 | -0.4458 | -0.5086 | 0.2061 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_63_65` | 1215 | 1215 | -0.2611 | -0.3273 | 0.2864 | `hold_no_edge` |
| `ai_score_band` | `score_unknown` | 1 | 0 | None | None | None | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 18053 | 18053 | -0.3088 | -0.3743 | 0.2827 | `candidate_tighten_or_exclude` |
| `ai_score_source` | `stage_rule_backfilled` | 1 | 0 | None | None | None | `hold_sample` |
| `arm` | `AVG_DOWN` | 12793 | 12792 | -0.7 | -0.7706 | 0.0 | `candidate_tighten_or_exclude` |
| `arm` | `PYRAMID` | 5261 | 5261 | 0.6423 | 0.5891 | 0.97 | `candidate_recovery_or_relax` |
| `blocker_namespace` | `AVG_DOWN` | 9061 | 9060 | -0.8416 | -0.9162 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_namespace` | `PYRAMID` | 5261 | 5261 | 0.6423 | 0.5891 | 0.97 | `candidate_recovery_or_relax` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 3732 | 3732 | -0.356 | -0.417 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `profit_not_enough` | 4531 | 4531 | 0.6344 | 0.5802 | 0.9793 | `candidate_recovery_or_relax` |
| `blocker_reason` | `add_judgment_locked` | 2390 | 2390 | -0.2442 | -0.264 | 0.2268 | `hold_no_edge` |
| `blocker_reason` | `low_broken` | 352 | 352 | -0.4619 | -0.4887 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 245 | 245 | -0.9298 | -0.9297 | 0.049 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.94)` | 240 | 240 | -0.8708 | -0.94 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.18)` | 198 | 198 | -1.1106 | -1.18 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.71)` | 149 | 149 | -0.6704 | -0.71 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.30)` | 147 | 147 | -1.178 | -1.3 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.04)` | 146 | 146 | -0.9464 | -1.04 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.85)` | 136 | 136 | -0.7834 | -0.85 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `ok` | 135 | 135 | -1.8699 | -2.3419 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.07)` | 132 | 132 | -0.0529 | -0.07 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.93)` | 129 | 129 | -0.8608 | -0.93 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.42)` | 123 | 123 | -1.3293 | -1.42 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.00)` | 115 | 115 | -0.9118 | -1.0 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.01)` | 115 | 115 | -0.9315 | -1.01 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.72)` | 108 | 108 | -0.6515 | -0.72 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `trend_not_strong` | 108 | 108 | 2.6757 | 2.694 | 1.0 | `candidate_recovery_or_relax` |
| `blocker_reason` | `pnl_out_of_range(-1.13)` | 106 | 106 | -1.0253 | -1.13 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.75)` | 100 | 100 | -0.6658 | -0.75 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.77)` | 99 | 99 | -0.6746 | -0.77 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.89)` | 99 | 99 | -0.8039 | -0.89 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.06)` | 95 | 95 | 0.0221 | -0.06 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.86)` | 95 | 95 | -0.7882 | -0.86 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.81)` | 93 | 93 | -0.7425 | -0.81 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.92)` | 93 | 93 | -0.8629 | -0.92 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.95)` | 93 | 93 | -0.8652 | -0.95 | 0.0 | `candidate_tighten_or_exclude` |

### Scale-In Bucket Runtime Approval Candidates

- `scale_in_bucket_1`: `ai_score_band` / `score_lt60` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_2`: `ai_score_band` / `score_60_62` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_3`: `ai_score_source` / `score_field_backfilled` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_4`: `arm` / `AVG_DOWN` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_5`: `arm` / `PYRAMID` -> `candidate_recovery_or_relax`
- `scale_in_bucket_6`: `blocker_namespace` / `AVG_DOWN` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_7`: `blocker_namespace` / `PYRAMID` -> `candidate_recovery_or_relax`
- `scale_in_bucket_8`: `blocker_namespace` / `AVG_DOWN_ONLY` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_9`: `blocker_reason` / `profit_not_enough` -> `candidate_recovery_or_relax`
- `scale_in_bucket_10`: `blocker_reason` / `low_broken` -> `candidate_tighten_or_exclude`

### Scale-In Bucket Workorders

- `scale_in_bucket_source_quality_1`: `ai_score_band` / `score_lt60` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_2`: `ai_score_band` / `score_60_62` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_3`: `ai_score_source` / `score_field_backfilled` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_4`: `arm` / `AVG_DOWN` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_5`: `arm` / `PYRAMID` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_6`: `blocker_namespace` / `AVG_DOWN` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_7`: `blocker_namespace` / `PYRAMID` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_8`: `blocker_namespace` / `AVG_DOWN_ONLY` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_9`: `blocker_reason` / `profit_not_enough` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_10`: `blocker_reason` / `low_broken` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`

## Overnight Bucket Attribution

- decision_authority: `adm_ldm_overnight_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'overnight_rows': 32, 'bucket_count': 31, 'actionable_bucket_count': 11, 'runtime_candidate_count': 8, 'workorder_count': 10, 'status_counts': {'HOLD_OVERNIGHT': 16, 'SELL_TODAY': 16}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 8 | 8 | -0.8559 | -1.1413 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 3 | 3 | -0.27 | -0.36 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 2 | 2 | 0.0825 | 0.11 | 0.5 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 2 | 2 | 0.7725 | 1.03 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos150_pos300` | 1 | 1 | 1.14 | 1.52 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_lt_neg070` | 8 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg010_pos080` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 3 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_pos080_pos150` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_pos150_pos300` | 1 | 0 | None | None | None | `hold_sample` |
| `confidence_band` | `confidence_070p` | 32 | 16 | -0.3005 | -0.4006 | 0.25 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s_plus` | 20 | 10 | -0.2527 | -0.337 | 0.3 | `hold_no_edge` |
| `held_bucket` | `held_600_1800s` | 12 | 6 | -0.38 | -0.5067 | 0.1667 | `candidate_tighten_or_exclude` |
| `overnight_action` | `SELL_TODAY` | 32 | 16 | -0.3005 | -0.4006 | 0.25 | `candidate_tighten_or_exclude` |
| `overnight_status` | `SELL_TODAY` | 16 | 16 | -0.3005 | -0.4006 | 0.25 | `candidate_tighten_or_exclude` |
| `overnight_status` | `HOLD_OVERNIGHT` | 16 | 0 | None | None | None | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 24 | 12 | -0.6444 | -0.8592 | 0.0 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_pos080_pos150` | 4 | 2 | 0.7725 | 1.03 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos150_pos300` | 2 | 1 | 1.14 | 1.52 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 2 | 1 | 0.24 | 0.32 | 1.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 32 | 16 | -0.3005 | -0.4006 | 0.25 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 16 | 8 | -0.8559 | -1.1413 | 0.0 | `candidate_tighten_or_exclude` |
| `source_quality_gate` | `overnight_decision_coverage` | 32 | 16 | -0.3005 | -0.4006 | 0.25 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 16 | 16 | -0.3005 | -0.4006 | 0.25 | `candidate_tighten_or_exclude` |
| `stage` | `exit` | 16 | 16 | -0.3005 | -0.4006 | 0.25 | `candidate_tighten_or_exclude` |

### Overnight Bucket Runtime Approval Candidates

- `overnight_bucket_2`: `confidence_band` / `confidence_070p` -> `candidate_tighten_or_exclude`
- `overnight_bucket_4`: `overnight_action` / `SELL_TODAY` -> `candidate_tighten_or_exclude`
- `overnight_bucket_5`: `overnight_status` / `SELL_TODAY` -> `candidate_tighten_or_exclude`
- `overnight_bucket_6`: `peak_profit_band` / `peak_lt_zero` -> `candidate_tighten_or_exclude`
- `overnight_bucket_7`: `price_source` / `holding_price_samples_last` -> `candidate_tighten_or_exclude`
- `overnight_bucket_9`: `source_quality_gate` / `overnight_decision_coverage` -> `candidate_tighten_or_exclude`
- `overnight_bucket_10`: `source_stage` / `scalp_sim_overnight_sell_today` -> `candidate_tighten_or_exclude`
- `overnight_bucket_11`: `stage` / `exit` -> `candidate_tighten_or_exclude`

### Overnight Bucket Workorders

- `overnight_bucket_source_quality_1`: `combo_overnight_decision` / `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_2`: `confidence_band` / `confidence_070p` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_3`: `held_bucket` / `held_600_1800s` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_4`: `overnight_action` / `SELL_TODAY` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_5`: `overnight_status` / `SELL_TODAY` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_6`: `peak_profit_band` / `peak_lt_zero` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_7`: `price_source` / `holding_price_samples_last` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_8`: `profit_band` / `profit_lt_neg070` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_9`: `source_quality_gate` / `overnight_decision_coverage` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_10`: `source_stage` / `scalp_sim_overnight_sell_today` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`

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
