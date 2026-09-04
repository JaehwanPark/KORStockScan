# Lifecycle Decision Matrix - 2026-09-04

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-09-04_mtd`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `8609`
- source_rows_total: `11982`
- retained_rows: `8609`
- dropped_rows_by_source: `{}`
- joined_rows: `4547`
- policy_pass_count: `5`
- promote_ready_count: `0`
- entry_bucket_actionable_count: `None`
- entry_bucket_runtime_candidate_count: `None`
- holding_bucket_count/workorders: `None` / `None`
- exit_bucket_count/workorders: `None` / `None`
- scale_in_bucket_actionable_count: `None`
- scale_in_bucket_runtime_candidate_count: `None`
- overnight_bucket_actionable_count: `None`
- overnight_bucket_runtime_candidate_count: `None`
- lifecycle_flow_bucket_count: `82`
- lifecycle_flow_complete_count: `38`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0058`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 2359 | 25 | 1.239 | 0.013 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 254 | 37 | -0.685 | 0.1968 | `pass` | `NO_CHANGE` | False |
| `holding` | 48 | 37 | -1.0296 | 0.8636 | `pass` | `EXIT` | False |
| `scale_in` | 4383 | 4370 | -0.847 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 1565 | 78 | -0.9606 | 0.2186 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 82, 'complete_flow_count': 38, 'incomplete_flow_count': 6474, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 4024 | 4012 | -0.9739 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 359 | 358 | 0.575 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 7 | 7 | 3.9599 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:5ee2a7cfd7` | 4 | 4 | -1.1925 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:42bc391d5b` | 2 | 2 | -0.7738 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:a6af469504` | 2 | 2 | -0.56 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:0cb91a7ba6` | 2 | 2 | -0.68 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:36904223da` | 2 | 2 | -0.715 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:bf44bd3042` | 1 | 1 | -0.65 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:f58154b780` | 1 | 1 | -0.75 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:7a29eed6f7` | 1 | 1 | -1.0614 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:f4d0891804` | 1 | 1 | -0.88 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:8880885eab` | 1 | 1 | -1.05 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 1 | 1 | 2.5732 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_bl:44fb83e208` | 1 | 1 | -0.79 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_ai_c:4bb9b08477` | 1 | 1 | -0.45 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:441959da5f` | 1 | 1 | -1.677 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:e95b96a4e9` | 1 | 1 | -1.38 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:b0bc92a886` | 1 | 1 | -0.98 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:e6cc63e69d` | 1 | 1 | -1.45 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 251, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 968 | 23 | 1.3739 | 1.1862 | 0.3478 | `hold_sample` |
| `chosen_action` | `NO_BUY_AI` | 1107 | 15 | 0.0872 | -1.5107 | 0.1333 | `hold_sample` |
| `stale_bucket` | `fresh` | 1032 | 15 | 0.0872 | -1.5107 | 0.1333 | `hold_sample` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 1945 | 15 | 0.0872 | -1.5107 | 0.1333 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 331 | 12 | 0.2503 | -1.0022 | 0.1667 | `hold_sample` |
| `score_band` | `score_70p` | 133 | 12 | 2.3452 | 3.3033 | 0.5833 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 947 | 12 | 0.1091 | -1.1226 | 0.1666 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 11 | 11 | -0.0308 | -1.5045 | 0.0 | `hold_sample` |
| `score_band` | `score_63_65` | 47 | 11 | 0.2028 | -0.9315 | 0.1818 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 627 | 11 | 0.1041 | -0.9352 | 0.1818 | `hold_sample` |
| `chosen_action` | `WAIT_REQUOTE` | 883 | 8 | 3.7866 | 6.2428 | 0.75 | `hold_sample` |
| `exit_rule` | `exit_unknown` | 2342 | 8 | 3.7866 | 6.2428 | 0.75 | `hold_sample` |
| `stale_bucket` | `fresh_or_unflagged` | 58 | 8 | 3.7866 | 6.2428 | 0.75 | `hold_sample` |
| `overbought_bucket` | `overbought_watch` | 541 | 8 | 1.5721 | 1.8753 | 0.375 | `hold_sample` |
| `time_bucket` | `time_1200_1400` | 640 | 8 | 1.4233 | 1.8045 | 0.375 | `hold_sample` |
| `source_stage` | `wait6579_ev_cohort` | 8 | 8 | 3.7866 | 6.2428 | 0.75 | `hold_sample` |
| `strength_bucket` | `neutral_strength_momentum` | 1019 | 6 | 3.8573 | 6.4752 | 0.8333 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 6 | 5 | -0.2081 | -1.446 | 0.0 | `hold_sample` |
| `strength_bucket` | `strong_strength_momentum` | 218 | 5 | 1.4293 | 0.3803 | 0.2 | `hold_sample` |
| `time_bucket` | `time_0900_1000` | 376 | 4 | 0.6012 | -0.6425 | 0.5 | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 104, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 242 | 37 | -0.685 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 244 | 37 | -0.685 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 43 | 37 | -0.685 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 43 | 37 | -0.685 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 43 | 37 | -0.685 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 43 | 37 | -0.685 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 43 | 37 | -0.685 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 43 | 37 | -0.685 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 43 | 37 | -0.685 | `keep_collecting` |
| `latency_state` | `simulated` | 43 | 37 | -0.685 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 242 | 37 | -0.685 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 42 | 37 | -0.685 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 34 | 29 | -1.0236 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 33 | 28 | -0.8584 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 20 | 19 | -1.2652 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 20 | 19 | -1.2652 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 19 | 19 | -1.2652 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 19 | 19 | -1.2652 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 20 | 19 | -1.2652 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_ok` | 24 | 18 | -0.0725 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 23 | 18 | -0.0725 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 211 | 18 | -0.0725 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 23 | 18 | -0.0725 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 24 | 18 | -0.0725 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 27 | 15 | -1.9293 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 12 | 12 | -2.3051 | `source_quality_workorder` |
| `would_limit_fill` | `false` | 226 | 11 | 0.0984 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 13 | 9 | 0.0314 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_context_missing` | 8 | 8 | 0.5424 | `keep_collecting` |
| `would_limit_fill` | `true` | 8 | 7 | -0.341 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 6 | 5 | -0.3293 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 6 | 5 | -0.4434 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 4 | 4 | 0.0844 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_10s_plus` | 14 | 4 | 1.225 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 3 | 3 | -0.0296 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 3 | 3 | -0.4262 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 2 | 2 | 0.3994 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 2 | 2 | -0.0849 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | 4.9886 | `source_quality_workorder` |
| `latency_state` | `caution` | 7 | 0 | None | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 26, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 43 | 37 | -1.0296 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 43 | 37 | -1.0296 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 36 | 31 | -1.3521 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 30 | 26 | -1.5022 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 25 | 25 | -1.4952 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 7 | 7 | -0.0655 | `hold_no_edge` |
| `holding_action` | `holding_action_not_applicable_at_start` | 7 | 6 | 0.6362 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 4 | 4 | 0.1789 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 3 | 3 | -0.3914 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 2 | 1 | -0.1205 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 1 | 1 | -1.8886 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 1 | 1 | -1.35 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 1 | 1 | 4.7784 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 1 | 1 | -0.1205 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | -1.8886 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 1 | 1 | -1.35 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1 | 1 | -1.677 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 4.7784 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 5 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 5 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 6 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 5 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 5 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 46, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 56 | 56 | -1.2795 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 39 | 39 | -0.9381 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 34 | 34 | -0.942 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 34 | 34 | -0.942 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 34 | 34 | -0.942 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 26 | 26 | -1.0646 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 16 | 16 | -1.4133 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 15 | 15 | -0.9157 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 13 | 13 | 0.129 | `hold_no_edge` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 12 | 12 | -0.767 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 11 | 11 | -0.4326 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 10 | 10 | -2.4877 | `hold_sample` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 9 | 9 | -1.1659 | `hold_sample` |
| `exit_outcome` | `MISSED_UPSIDE` | 8 | 8 | -0.0292 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 8 | 8 | -0.0075 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 8 | 8 | -0.5437 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 8 | 8 | -0.7127 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 6 | 6 | -2.5838 | `hold_sample` |
| `exit_outcome` | `COMPLETED` | 5 | 5 | -1.263 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 5 | 5 | -1.263 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_lt_neg070` | 4 | 4 | -1.5356 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 4 | 4 | 0.1183 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 3 | 3 | -0.9692 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 2 | 2 | -2.6854 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 2 | 2 | -2.0019 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 2 | 2 | 0.5293 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 2 | 2 | -0.7961 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 1 | 1 | -1.8886 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 1 | 1 | -1.35 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 1 | 1 | 4.7784 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 1 | 1 | -0.1725 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | -0.5956 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 1 | 1 | -2.6672 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | -0.4217 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=NEUTRAL|profit=profit_lt_neg070` | 1 | 1 | -0.9741 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=NEUTRAL|profit=profit_neg070_neg010` | 1 | 1 | -0.115 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg070_neg010` | 1 | 1 | -0.1205 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 1 | 1 | -1.8886 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | 0.3171 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 1 | 1 | 4.7784 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 283, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `price_guard_reason` | `price_guard_none` | 4382 | 4370 | None | -0.9312 | 0.0806 | `hold_sample` |
| `qty_reason` | `qty_none` | 4371 | 4370 | None | -0.9312 | 0.0806 | `hold_sample` |
| `time_bucket` | `time_unknown` | 4383 | 4370 | None | -0.9312 | 0.0806 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 4369 | 4368 | None | -0.932 | 0.0802 | `hold_sample` |
| `arm` | `AVG_DOWN` | 4024 | 4012 | None | -1.0638 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 3992 | 3980 | None | -1.0463 | 0.0 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 2849 | 2849 | None | -0.9456 | 0.0909 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 2597 | 2597 | None | -1.3976 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2477 | 2477 | None | -1.0154 | 0.1066 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 2304 | 2291 | None | -0.818 | 0.1536 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 2092 | 2079 | None | -1.056 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 1342 | 1342 | None | -0.4724 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 1333 | 1333 | None | -1.0855 | 0.0 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_1` | 1203 | 1203 | None | -1.0719 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 1064 | 1064 | None | -0.9165 | 0.0254 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 827 | 827 | None | -0.6743 | 0.2672 | `hold_sample` |
| `ai_score_source` | `live` | 663 | 663 | None | -0.9467 | 0.0769 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 536 | 536 | None | -0.6608 | 0.1007 | `hold_sample` |
| `ai_score_source` | `holding_ai_not_called` | 387 | 387 | None | -0.8267 | 0.0569 | `hold_sample` |
| `arm` | `PYRAMID` | 359 | 358 | None | 0.5539 | 0.9833 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 19, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 10 | 5 | -1.263 | -1.684 | 0.0 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 5 | 5 | -1.263 | -1.684 | 0.0 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 10 | 5 | -1.263 | -1.684 | 0.0 | `hold_sample` |
| `stage` | `exit` | 5 | 5 | -1.263 | -1.684 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 10 | 5 | -1.263 | -1.684 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 10 | 5 | -1.263 | -1.684 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 10 | 5 | -1.263 | -1.684 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 5 | 5 | -1.263 | -1.684 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 4 | 4 | -1.5356 | -2.0475 | 0.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 8 | 4 | -1.5356 | -2.0475 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 8 | 4 | -1.5356 | -2.0475 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 1 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 5 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_lt_neg070` | 4 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 1 | 0 | None | None | None | `hold_sample` |
| `stage` | `holding` | 5 | 0 | None | None | None | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_decision` | 5 | 0 | None | None | None | `hold_sample` |

### Overnight Bucket Runtime Approval Candidates

- none

### Overnight Bucket Workorders

- none

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
