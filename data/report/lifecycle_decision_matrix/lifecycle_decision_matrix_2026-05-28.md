# Lifecycle Decision Matrix - 2026-05-28

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-05-28`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `24484`
- source_rows_total: `24484`
- retained_rows: `24484`
- dropped_rows_by_source: `{}`
- joined_rows: `23761`
- policy_pass_count: `5`
- promote_ready_count: `0`
- entry_bucket_actionable_count: `12`
- entry_bucket_runtime_candidate_count: `5`
- holding_bucket_count/workorders: `34` / `10`
- exit_bucket_count/workorders: `68` / `10`
- scale_in_bucket_actionable_count: `206`
- scale_in_bucket_runtime_candidate_count: `10`
- overnight_bucket_actionable_count: `18`
- overnight_bucket_runtime_candidate_count: `10`
- lifecycle_flow_bucket_count: `97`
- lifecycle_flow_complete_count: `84`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0066`
- incomplete_flow_reason_counts: `{'missing_entry': 12410, 'missing_holding': 12694, 'missing_exit': 12349, 'missing_submit': 12697, 'sim_record_id_only': 195, 'postclose_exit_without_entry': 364, 'candidate_id_only': 12472}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 1, 'route_counts': {'bounded_auxiliary_weight': 1, 'hold_sample': 4}, 'quality_counts': {'observational_only_pending_outcome': 1, 'hold_sample': 4}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 569 | 112 | -0.0567 | 1.0 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 217 | 199 | -0.6071 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 216 | 199 | -0.7334 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 22529 | 22492 | -0.4456 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 953 | 759 | -0.5616 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 12797, 'complete_flow_count': 84, 'incomplete_flow_count': 12713, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 24484, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0066, 'join_contract_blocked': False, 'bundle_ev_tuning_state': 'ready_for_bundle_ev_tuning', 'top_incomplete_reason': 'missing_submit', 'stage_identity': {'entry': {'source_row_count': 569, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 298, 'candidate_id': 271}, 'identity_join_rate': 1.0}, 'submit': {'source_row_count': 217, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 217}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 216, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 200, 'exact_sim_record_id': 16}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 22529, 'identity_missing_count': 0, 'identity_quality_counts': {'exact_sim_record_id': 9881, 'candidate_id': 12648}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 953, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 184, 'exact_sim_record_id': 575, 'candidate_id': 194}, 'identity_join_rate': 1.0}}, 'required_stage_source_counts': {'entry': 569, 'submit': 217, 'holding': 216, 'exit': 953}, 'incomplete_flow_reason_counts': {'missing_entry': 12410, 'missing_holding': 12694, 'missing_exit': 12349, 'missing_submit': 12697, 'sim_record_id_only': 195, 'postclose_exit_without_entry': 364, 'candidate_id_only': 12472}, 'bucket_count': 97, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:fd9360c39d` | 7 | 7 | 0.1575 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:88611b572d` | 6 | 6 | -2.1094 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:42075e2cfd` | 5 | 5 | -1.3347 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:7a9deca452` | 3 | 3 | -2.3308 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:4ce5e1021f` | 3 | 3 | -1.3163 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:3b5c514b26` | 3 | 3 | -0.8716 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:7e707fb21d` | 2 | 2 | -1.0617 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:29cdec5d47` | 2 | 2 | -5.0191 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_bloc:5e3a527242` | 2 | 2 | 0.7773 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:a9642d164b` | 2 | 2 | 0.6803 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:6392ad5e98` | 1 | 1 | -1.0715 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:2946036d32` | 1 | 1 | -0.6405 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:4475254a35` | 1 | 1 | -0.5129 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:2e7ea992ad` | 1 | 1 | 0.8064 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:762a966831` | 1 | 1 | 0.4179 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:b85b2fccd5` | 1 | 1 | 0.5166 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:076eaa9b2a` | 1 | 1 | 0.4617 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:844411976d` | 1 | 1 | 0.55 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:a37c497346` | 1 | 1 | -1.699 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:9d952699d4` | 1 | 1 | -0.8489 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 569, 'bucket_count': 165, 'actionable_bucket_count': 12, 'runtime_candidate_count': 5, 'workorder_count': 10}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `WAIT_REQUOTE` | 96 | 96 | -0.026 | 0.2808 | 0.4062 | `hold_no_edge` |
| `chosen_action` | `NO_BUY_AI` | 288 | 11 | -0.4374 | -0.9345 | 0.3636 | `candidate_tighten_or_exclude` |
| `chosen_action` | `BUY_NOW` | 6 | 5 | 0.1916 | -0.71 | 0.4 | `hold_sample` |
| `chosen_action` | `ALLOW_BOTTOMING_ENTRY` | 22 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `ALLOW_LEVEL1_RISK_OFF_ENTRY` | 153 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_SOURCE_QUALITY` | 4 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_normal|time=time_1000_1200` | 12 | 12 | -0.639 | -0.9728 | 0.25 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_chase_risk|time=time_0900_1000` | 11 | 11 | -3.0814 | -4.0545 | 0.2727 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_watch|time=time_1000_1200` | 10 | 10 | -0.6702 | -0.6929 | 0.2 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_watch|time=time_0900_1000` | 8 | 8 | -1.1315 | -1.3987 | 0.25 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_chase_risk|time=time_1000_1200` | 7 | 7 | -0.4497 | 0.2175 | 0.5714 | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_normal|time=time_1200_1400` | 6 | 6 | 1.488 | 2.299 | 0.5 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_normal|time=time_1000_1200` | 6 | 6 | -0.3529 | -0.3774 | 0.5 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1000_1200` | 35 | 5 | -0.0511 | -1.472 | 0.2 | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_watch|time=time_1000_1200` | 5 | 5 | -0.5528 | -0.6995 | 0.2 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_normal|time=time_0900_1000` | 4 | 4 | 1.7915 | 2.8041 | 0.5 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_normal|time=time_1200_1400` | 4 | 4 | -0.3401 | -0.012 | 0.25 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_0900_1000` | 26 | 3 | -0.4214 | 0.4933 | 0.6667 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_normal|time=time_1000_1200` | 3 | 3 | 5.1399 | 9.4685 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_normal|time=time_0900_1000` | 3 | 3 | 1.0365 | 1.0995 | 1.0 | `hold_sample` |
| `exit_rule` | `exit_unknown` | 553 | 96 | -0.026 | 0.2808 | 0.4062 | `hold_no_edge` |
| `liquidity_bucket` | `liquidity_high` | 96 | 96 | -0.026 | 0.2808 | 0.4062 | `hold_no_edge` |
| `liquidity_bucket` | `liquidity_unknown` | 298 | 16 | -0.2409 | -0.8644 | 0.375 | `hold_no_edge` |
| `overbought_bucket` | `overbought_proxy_normal` | 41 | 41 | 0.5132 | 0.9712 | 0.4634 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_proxy_watch` | 29 | 29 | 0.1344 | 0.5125 | 0.3448 | `hold_no_edge` |
| `overbought_bucket` | `overbought_proxy_chase_risk` | 20 | 20 | -1.8933 | -2.2892 | 0.35 | `candidate_tighten_or_exclude` |
| `overbought_bucket` | `overbought_unknown` | 169 | 15 | -0.3546 | -0.9893 | 0.3333 | `candidate_tighten_or_exclude` |
| `score_band` | `score_70p` | 170 | 64 | -0.5206 | -0.4786 | 0.375 | `candidate_tighten_or_exclude` |
| `score_band` | `score_66_69` | 37 | 30 | 0.3064 | 0.4805 | 0.4 | `candidate_recovery_or_relax` |
| `score_band` | `score_60_62` | 267 | 10 | -0.107 | -0.759 | 0.4 | `hold_no_edge` |
| `source_stage` | `wait6579_ev_cohort` | 96 | 96 | -0.026 | 0.2808 | 0.4062 | `hold_no_edge` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 185 | 16 | -0.2409 | -0.8644 | 0.375 | `hold_no_edge` |
| `stale_bucket` | `fresh_or_unflagged` | 271 | 96 | -0.026 | 0.2808 | 0.4062 | `hold_no_edge` |
| `stale_bucket` | `fresh` | 219 | 15 | -0.1893 | -0.7407 | 0.4 | `hold_no_edge` |
| `strength_bucket` | `strong_strength_momentum` | 109 | 81 | -0.099 | 0.1921 | 0.4074 | `hold_no_edge` |
| `strength_bucket` | `risk_unknown` | 185 | 16 | -0.2409 | -0.8644 | 0.375 | `hold_no_edge` |
| `strength_bucket` | `weak_strength_momentum` | 60 | 10 | -0.7482 | -0.8675 | 0.3 | `candidate_tighten_or_exclude` |
| `time_bucket` | `time_1000_1200` | 212 | 54 | -0.1471 | -0.1712 | 0.3333 | `hold_no_edge` |
| `time_bucket` | `time_0900_1000` | 215 | 38 | -1.0589 | -1.2153 | 0.4211 | `candidate_tighten_or_exclude` |
| `time_bucket` | `time_1200_1400` | 114 | 17 | 1.9691 | 3.2365 | 0.4706 | `candidate_recovery_or_relax` |

### Entry Bucket Runtime Approval Candidates

- `entry_bucket_5`: `overbought_bucket` / `overbought_proxy_normal` -> `candidate_recovery_or_relax`
- `entry_bucket_6`: `overbought_bucket` / `overbought_proxy_chase_risk` -> `candidate_tighten_or_exclude`
- `entry_bucket_8`: `score_band` / `score_70p` -> `candidate_tighten_or_exclude`
- `entry_bucket_9`: `score_band` / `score_66_69` -> `candidate_recovery_or_relax`
- `entry_bucket_11`: `time_bucket` / `time_0900_1000` -> `candidate_tighten_or_exclude`

### Entry Bucket Workorders

- `entry_bucket_source_quality_1`: `chosen_action` / `NO_BUY_AI` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_2`: `combo_entry_spot` / `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_normal|time=time_1000_1200` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_3`: `combo_entry_spot` / `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_chase_risk|time=time_0900_1000` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_4`: `combo_entry_spot` / `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_watch|time=time_1000_1200` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_5`: `overbought_bucket` / `overbought_proxy_normal` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_6`: `overbought_bucket` / `overbought_proxy_chase_risk` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_7`: `overbought_bucket` / `overbought_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_8`: `score_band` / `score_70p` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_9`: `score_band` / `score_66_69` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_10`: `strength_bucket` / `weak_strength_momentum` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`

## Submit Bucket Attribution

- decision_authority: `adm_ldm_submit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'submit_rows': 217, 'bucket_count': 59, 'contract_gap_count': 0, 'workorder_count': 0, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 215 | 199 | -0.6071 | `keep_collecting` |
| `actual_order_submitted` | `true` | 2 | 0 | None | `keep_collecting` |
| `broker_order_forbidden` | `true` | 213 | 199 | -0.6071 | `keep_collecting` |
| `broker_order_forbidden` | `false` | 4 | 0 | None | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 112 | 112 | -0.463 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 43 | 43 | -0.8261 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 18 | 18 | -0.4137 | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=block_False|quote_age=quote_age_unknown|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_normal|latency=latency_unknown|fill=false|submitted=false` | 12 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 12 | 12 | -1.2635 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 5 | 5 | -2.0092 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_unknown|latency=simulated|fill=false|submitted=false` | 3 | 3 | 0.1009 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 3 | 3 | -0.7455 | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_pass|revalidation=block_False|quote_age=quote_age_unknown|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_normal|latency=latency_unknown|fill=false|submitted=false` | 2 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=block_False|quote_age=quote_age_unknown|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_unknown|latency=latency_unknown|fill=false|submitted=true` | 2 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 2 | 2 | 0.6658 | `source_quality_workorder` |
| `combo_submit_quality` | `source=pre_submit_liquidity_guard_block|revalidation=block_False|quote_age=quote_age_unknown|liquidity=below_min_liquidity|liquidity_guard=liquidity_guard_unknown|overbought=overbought_unknown|latency=latency_unknown|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | -0.1792 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `latency_reason` | `scalp_live_simulator` | 200 | 199 | -0.6071 | `keep_collecting` |
| `latency_reason` | `latency_reason_unknown` | 17 | 0 | None | `source_quality_workorder` |
| `latency_state` | `simulated` | 200 | 199 | -0.6071 | `keep_collecting` |
| `latency_state` | `latency_unknown` | 17 | 0 | None | `source_quality_workorder` |
| `liquidity_bucket` | `below_min_liquidity` | 177 | 175 | -0.6562 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 24 | 24 | -0.2497 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_unknown` | 16 | 0 | None | `source_quality_workorder` |
| `liquidity_guard_action` | `would_block` | 176 | 175 | -0.6562 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 24 | 24 | -0.2497 | `keep_collecting` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 17 | 0 | None | `source_quality_workorder` |
| `overbought_bucket` | `overbought_unknown` | 196 | 192 | -0.5839 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_normal` | 14 | 0 | None | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 7 | 7 | -1.2449 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 200 | 199 | -0.6071 | `keep_collecting` |
| `overbought_guard_action` | `overbought_guard_unknown` | 17 | 0 | None | `source_quality_workorder` |
| `price_below_bid_bucket` | `not_below_bid` | 135 | 134 | -0.5419 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 55 | 55 | -0.8194 | `keep_collecting` |
| `price_below_bid_bucket` | `price_below_bid_unknown` | 17 | 0 | None | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 10 | 10 | -0.3143 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 123 | 123 | -0.4957 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 74 | 73 | -0.824 | `keep_collecting` |
| `price_resolution_bucket` | `price_unknown` | 12 | 0 | None | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 216, 'source_row_count': 216, 'bucket_count': 34, 'joined_sample': 995, 'source_quality_adjusted_ev_pct': -0.7334, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 80 | 80 | -1.6773 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 38 | 38 | -1.4253 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 19 | 19 | 0.3452 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 14 | 14 | 0.5753 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 11 | 11 | 0.4734 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 9 | 9 | 0.5918 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 8 | 8 | 0.1573 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 7 | 7 | 2.2342 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 6 | 6 | -0.4498 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 4 | 4 | 1.276 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 2 | 2 | 0.1671 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 1 | 1 | -2.3877 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos080_pos150|held=held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos150_pos300_plus|held=held_600_1800s_plus` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos150_pos300|held=held_600_1800s_plus` | 7 | 0 | None | `hold_sample` |
| `held_bucket` | `held_not_applicable_at_start` | 200 | 199 | -0.7334 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s_plus` | 16 | 0 | None | `hold_sample` |
| `holding_action` | `WAIT` | 129 | 129 | -0.8145 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 69 | 68 | -0.6062 | `candidate_tighten_or_exclude` |
| `holding_action` | `BUY` | 2 | 2 | 0.1671 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 16 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 200 | 199 | -0.7334 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 16 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 121 | 120 | -1.5668 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 37 | 30 | 0.3922 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos080_pos150` | 25 | 23 | 0.5818 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg010_pos080` | 15 | 14 | -0.1029 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300_plus` | 14 | 11 | 1.8857 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 3 | 1 | -2.3877 | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- `holding_bucket_source_quality_1`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_2`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_3`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_4`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_5`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_6`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_7`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_8`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_9`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_10`: `held_bucket` / `held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Exit Bucket Attribution

- decision_authority: `adm_ldm_exit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'exit_rows': 953, 'source_row_count': 953, 'bucket_count': 68, 'joined_sample': 3795, 'source_quality_adjusted_ev_pct': -0.5616, 'source_quality_gate': 'pass', 'unknown_reason_counts': {'not_applicable': 12, 'join_gap': 8, 'missing_source_field': 1}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 234 | 234 | -1.2014 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 212 | 212 | -0.4879 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 55 | 55 | 0.2545 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 36 | 36 | -1.1792 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 24 | 24 | -2.7239 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 19 | 19 | -1.7072 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 16 | 16 | -1.1015 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 16 | 16 | -0.0734 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 15 | 15 | -1.6447 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` | 12 | 12 | 1.0608 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos150_pos300` | 10 | 10 | 2.188 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 10 | 10 | 1.1658 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 9 | 9 | -0.5766 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos150_pos300` | 7 | 7 | 1.6318 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_sell_order_assumed_filled|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos150_pos300` | 7 | 7 | 1.6318 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 7 | 7 | -0.1142 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 6 | 6 | 0.9149 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 6 | 6 | 1.0989 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 5 | 5 | 0.5744 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos150_pos300_plus` | 4 | 4 | 3.3549 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 4 | 4 | -0.7126 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 4 | 4 | 1.21 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 4 | 4 | -0.3166 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 4 | 4 | 0.6538 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos150_pos300_plus` | 3 | 3 | 3.0525 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_sell_order_assumed_filled|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos150_pos300_plus` | 3 | 3 | 3.0525 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 3 | 3 | 1.9451 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300` | 3 | 3 | 0.3242 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 2 | 2 | -0.1725 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos080_pos150` | 2 | 2 | 0.7875 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_sell_order_assumed_filled|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 2 | 2 | -0.1725 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_sell_order_assumed_filled|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos080_pos150` | 2 | 2 | 0.7875 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 2 | 2 | -0.0463 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=NEUTRAL|profit=profit_neg070_neg010` | 2 | 2 | -1.2514 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 2 | 2 | 4.1574 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 1 | 1 | -0.5925 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 1 | 1 | -0.0675 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_sell_order_assumed_filled|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 1 | 1 | -0.5925 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_sell_order_assumed_filled|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 1 | 1 | -0.0675 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 1 | 1 | 1.6373 | `hold_sample` |

### Exit Bucket Attribution Workorders

- `exit_bucket_source_quality_1`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_2`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_3`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_4`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_5`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_6`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_7`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_8`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_9`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos150_pos300` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_10`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'scale_in_rows': 22529, 'bucket_count': 1912, 'actionable_bucket_count': 206, 'runtime_candidate_count': 10, 'workorder_count': 10, 'arm_counts': {'PYRAMID': 4707, 'AVG_DOWN': 17822}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_70p` | 16243 | 16243 | -0.4845 | -0.539 | 0.1961 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_66_69` | 2601 | 2601 | -0.401 | -0.4475 | 0.2092 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_60_62` | 2269 | 2269 | -0.1452 | -0.1655 | 0.2503 | `hold_no_edge` |
| `ai_score_band` | `score_63_65` | 711 | 711 | -0.3903 | -0.4397 | 0.225 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_lt60` | 667 | 667 | -0.7565 | -0.8643 | 0.2144 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_unknown` | 38 | 1 | 0.935 | 0.71 | 1.0 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 22491 | 22491 | -0.4457 | -0.4973 | 0.2045 | `candidate_tighten_or_exclude` |
| `ai_score_source` | `sim_scale_in_source_not_scored` | 1 | 1 | 0.935 | 0.71 | 1.0 | `hold_sample` |
| `ai_score_source` | `stage_rule_backfilled` | 37 | 0 | None | None | None | `hold_sample` |
| `arm` | `AVG_DOWN` | 17822 | 17798 | -0.7642 | -0.8211 | 0.0 | `candidate_tighten_or_exclude` |
| `arm` | `PYRAMID` | 4707 | 4694 | 0.7624 | 0.7308 | 0.9802 | `candidate_recovery_or_relax` |
| `blocker_namespace` | `AVG_DOWN` | 14796 | 14772 | -0.8499 | -0.9039 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_namespace` | `PYRAMID` | 4707 | 4694 | 0.7624 | 0.7308 | 0.9802 | `candidate_recovery_or_relax` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 3026 | 3026 | -0.3462 | -0.417 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 9880 | 9880 | -0.4107 | -0.4072 | 0.2344 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `add_judgment_locked` | 2049 | 2049 | -0.436 | -0.5117 | 0.1786 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `profit_not_enough` | 1858 | 1858 | 0.5982 | 0.524 | 0.9828 | `candidate_recovery_or_relax` |
| `blocker_reason` | `low_broken` | 551 | 551 | -0.3679 | -0.3889 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `ok` | 161 | 161 | -2.2482 | -2.8068 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.09)` | 126 | 126 | -0.9852 | -1.09 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.95)` | 118 | 118 | -0.8531 | -0.95 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.80)` | 112 | 112 | -0.7035 | -0.8 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.73)` | 109 | 109 | -0.6465 | -0.73 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.85)` | 101 | 101 | -0.7647 | -0.85 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.05)` | 101 | 101 | -0.9515 | -1.05 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.89)` | 96 | 96 | -0.7814 | -0.89 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.09)` | 91 | 91 | -0.0234 | -0.09 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.98)` | 91 | 91 | -0.878 | -0.98 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.86)` | 86 | 86 | -0.7492 | -0.86 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.93)` | 74 | 74 | -0.8413 | -0.93 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `trend_not_strong` | 74 | 74 | 2.7926 | 2.8414 | 1.0 | `candidate_recovery_or_relax` |
| `blocker_reason` | `pnl_out_of_range(-1.23)` | 69 | 69 | -1.125 | -1.23 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.05)` | 67 | 67 | -0.0111 | -0.05 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-1.00)` | 64 | 64 | -0.9123 | -1.0 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.21)` | 64 | 64 | -1.0884 | -1.21 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.38)` | 64 | 64 | -1.2159 | -1.38 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.08)` | 63 | 63 | -0.9553 | -1.08 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.29)` | 63 | 63 | -1.1141 | -1.29 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.75)` | 62 | 62 | -0.6889 | -0.75 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.76)` | 62 | 62 | -0.6458 | -0.76 | 0.0 | `candidate_tighten_or_exclude` |

### Scale-In Bucket Runtime Approval Candidates

- `scale_in_bucket_1`: `ai_score_band` / `score_70p` -> `candidate_tighten_or_exclude`
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

- `scale_in_bucket_source_quality_1`: `ai_score_band` / `score_70p` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
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
- summary: `{'overnight_rows': 48, 'bucket_count': 45, 'actionable_bucket_count': 18, 'runtime_candidate_count': 10, 'workorder_count': 10, 'status_counts': {'HOLD_OVERNIGHT': 16, 'SELL_TODAY': 32}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos150_pos300` | 7 | 7 | 1.6318 | 2.1757 | 1.0 | `candidate_recovery_or_relax` |
| `combo_overnight_decision` | `action=action_unknown|status=SELL_TODAY|confidence=confidence_unknown|profit=profit_pos150_pos300` | 7 | 7 | 1.6318 | 2.1757 | 1.0 | `candidate_recovery_or_relax` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos150_pos300_plus` | 3 | 3 | 3.0525 | 4.07 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=action_unknown|status=SELL_TODAY|confidence=confidence_unknown|profit=profit_pos150_pos300_plus` | 3 | 3 | 3.0525 | 4.07 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 2 | 2 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 2 | 2 | 0.7875 | 1.05 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=action_unknown|status=SELL_TODAY|confidence=confidence_unknown|profit=profit_neg070_neg010` | 2 | 2 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=action_unknown|status=SELL_TODAY|confidence=confidence_unknown|profit=profit_pos080_pos150` | 2 | 2 | 0.7875 | 1.05 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 1 | 1 | -0.5925 | -0.79 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 1 | 1 | -0.0675 | -0.09 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=action_unknown|status=SELL_TODAY|confidence=confidence_unknown|profit=profit_lt_neg070` | 1 | 1 | -0.5925 | -0.79 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=action_unknown|status=SELL_TODAY|confidence=confidence_unknown|profit=profit_neg010_pos080` | 1 | 1 | -0.0675 | -0.09 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_lt_neg070` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg010_pos080` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_pos080_pos150` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_pos150_pos300` | 7 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_pos150_pos300_plus` | 3 | 0 | None | None | None | `hold_sample` |
| `confidence_band` | `confidence_070p` | 32 | 16 | 1.3219 | 1.7625 | 0.75 | `candidate_recovery_or_relax` |
| `confidence_band` | `confidence_unknown` | 16 | 16 | 1.3219 | 1.7625 | 0.75 | `candidate_recovery_or_relax` |
| `held_bucket` | `held_600_1800s_plus` | 32 | 16 | 1.3219 | 1.7625 | 0.75 | `candidate_recovery_or_relax` |
| `held_bucket` | `held_unknown` | 16 | 16 | 1.3219 | 1.7625 | 0.75 | `candidate_recovery_or_relax` |
| `overnight_action` | `SELL_TODAY` | 32 | 16 | 1.3219 | 1.7625 | 0.75 | `candidate_recovery_or_relax` |
| `overnight_action` | `action_unknown` | 16 | 16 | 1.3219 | 1.7625 | 0.75 | `candidate_recovery_or_relax` |
| `overnight_status` | `SELL_TODAY` | 32 | 32 | 1.3219 | 1.7625 | 0.75 | `candidate_recovery_or_relax` |
| `peak_profit_band` | `peak_unknown` | 16 | 16 | 1.3219 | 1.7625 | 0.75 | `candidate_recovery_or_relax` |
| `peak_profit_band` | `peak_pos150_pos300` | 14 | 7 | 1.6318 | 2.1757 | 1.0 | `candidate_recovery_or_relax` |
| `price_source` | `holding_price_samples_last` | 45 | 30 | 1.4215 | 1.8953 | 0.8 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300` | 21 | 14 | 1.6318 | 2.1757 | 1.0 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300_plus` | 9 | 6 | 3.0525 | 4.07 | 1.0 | `candidate_recovery_or_relax` |
| `source_quality_gate` | `overnight_decision_coverage` | 48 | 32 | 1.3219 | 1.7625 | 0.75 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 16 | 16 | 1.3219 | 1.7625 | 0.75 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_sim_sell_order_assumed_filled` | 16 | 16 | 1.3219 | 1.7625 | 0.75 | `candidate_recovery_or_relax` |
| `stage` | `exit` | 32 | 32 | 1.3219 | 1.7625 | 0.75 | `candidate_recovery_or_relax` |

### Overnight Bucket Runtime Approval Candidates

- `overnight_bucket_3`: `confidence_band` / `confidence_070p` -> `candidate_recovery_or_relax`
- `overnight_bucket_5`: `held_bucket` / `held_600_1800s_plus` -> `candidate_recovery_or_relax`
- `overnight_bucket_7`: `overnight_action` / `SELL_TODAY` -> `candidate_recovery_or_relax`
- `overnight_bucket_9`: `overnight_status` / `SELL_TODAY` -> `candidate_recovery_or_relax`
- `overnight_bucket_12`: `price_source` / `holding_price_samples_last` -> `candidate_recovery_or_relax`
- `overnight_bucket_13`: `profit_band` / `profit_pos150_pos300` -> `candidate_recovery_or_relax`
- `overnight_bucket_15`: `source_quality_gate` / `overnight_decision_coverage` -> `candidate_recovery_or_relax`
- `overnight_bucket_16`: `source_stage` / `scalp_sim_overnight_sell_today` -> `candidate_recovery_or_relax`
- `overnight_bucket_17`: `source_stage` / `scalp_sim_sell_order_assumed_filled` -> `candidate_recovery_or_relax`
- `overnight_bucket_18`: `stage` / `exit` -> `candidate_recovery_or_relax`

### Overnight Bucket Workorders

- `overnight_bucket_source_quality_1`: `combo_overnight_decision` / `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos150_pos300` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_2`: `combo_overnight_decision` / `action=action_unknown|status=SELL_TODAY|confidence=confidence_unknown|profit=profit_pos150_pos300` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_3`: `confidence_band` / `confidence_070p` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_4`: `confidence_band` / `confidence_unknown` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_5`: `held_bucket` / `held_600_1800s_plus` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_6`: `held_bucket` / `held_unknown` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_7`: `overnight_action` / `SELL_TODAY` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_8`: `overnight_action` / `action_unknown` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_9`: `overnight_status` / `SELL_TODAY` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_10`: `peak_profit_band` / `peak_unknown` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`

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
