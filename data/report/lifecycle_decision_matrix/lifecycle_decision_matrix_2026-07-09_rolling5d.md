# Lifecycle Decision Matrix - 2026-07-09

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-09_rolling5d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `11970`
- source_rows_total: `16564`
- retained_rows: `11970`
- dropped_rows_by_source: `{}`
- joined_rows: `4535`
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
- lifecycle_flow_bucket_count: `159`
- lifecycle_flow_complete_count: `57`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0053`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 1001 | 49 | -0.0558 | 0.0754 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 334 | 85 | -0.6022 | 0.6187 | `pass` | `NO_CHANGE` | False |
| `holding` | 230 | 85 | -1.3573 | 0.8347 | `pass` | `EXIT` | False |
| `scale_in` | 4213 | 4132 | -0.8673 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 6192 | 184 | -1.1174 | 0.1525 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 159, 'complete_flow_count': 57, 'incomplete_flow_count': 10682, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 3583 | 3518 | -1.1168 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 538 | 522 | 0.8226 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 75 | 75 | -1.0572 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 14 | 14 | -0.1542 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 8 | 8 | -0.7688 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 7 | 7 | 0.1809 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 4 | 4 | 0.652 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 4 | 4 | -1.3575 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:15c17a2405` | 3 | 3 | -2.6964 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b4078edac9` | 3 | 3 | -2.6887 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 3 | 3 | -0.6967 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:10cd1f01cf` | 2 | 2 | -2.2218 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:4874ec99fd` | 2 | 2 | -1.1385 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:0e963d335b` | 2 | 2 | -1.07 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:9cad8b8252` | 1 | 1 | -2.0092 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:9b3d586d84` | 1 | 1 | -1.2667 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:50ebb4b990` | 1 | 1 | -1.45 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:3ecc9eeb81` | 1 | 1 | 0.9467 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:ad0146c320` | 1 | 1 | -1.8985 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:d284f9c76b` | 1 | 1 | -0.7822 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 243, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 667 | 47 | 0.0099 | -0.9704 | 0.2979 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 591 | 40 | 0.1861 | -1.0093 | 0.3 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 609 | 31 | -0.1027 | -1.6761 | 0.2903 | `hold_sample` |
| `chosen_action` | `NO_BUY_AI` | 717 | 29 | 0.0005 | -1.6141 | 0.2759 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 583 | 26 | 0.1704 | -1.1252 | 0.2692 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 19 | 19 | -0.0261 | -3.5879 | 0.0 | `hold_sample` |
| `chosen_action` | `WAIT_REQUOTE` | 109 | 18 | 0.1173 | 0.2557 | 0.3889 | `hold_sample` |
| `exit_rule` | `exit_unknown` | 970 | 18 | 0.025 | 0.0668 | 0.3333 | `hold_sample` |
| `stale_bucket` | `fresh_or_unflagged` | 137 | 18 | 0.025 | 0.0668 | 0.3333 | `hold_sample` |
| `strength_bucket` | `neutral_strength_momentum` | 252 | 18 | -0.1653 | -1.0319 | 0.3333 | `hold_sample` |
| `score_band` | `score_70p` | 140 | 18 | -0.092 | -0.717 | 0.3889 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 289 | 18 | -0.1847 | -0.8319 | 0.2222 | `hold_sample` |
| `source_stage` | `wait6579_ev_cohort` | 18 | 18 | 0.025 | 0.0668 | 0.3333 | `hold_sample` |
| `score_band` | `score_60_62` | 392 | 17 | -0.2662 | -1.6488 | 0.2353 | `hold_sample` |
| `stale_bucket` | `fresh` | 200 | 15 | -0.1696 | -2.2753 | 0.2 | `hold_sample` |
| `stale_bucket` | `stale_high` | 464 | 15 | -0.0479 | -1.2567 | 0.3333 | `hold_sample` |
| `time_bucket` | `time_0900_1000` | 182 | 15 | 0.4763 | -0.3559 | 0.4 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 9 | 9 | -0.0606 | 2.86 | 1.0 | `hold_sample` |
| `time_bucket` | `time_1200_1400` | 239 | 8 | -0.5619 | -2.9563 | 0.125 | `hold_sample` |
| `time_bucket` | `time_1400_close` | 291 | 8 | -0.2573 | -0.8491 | 0.5 | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 102, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 242 | 85 | -0.6022 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 334 | 85 | -0.6022 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 219 | 85 | -0.6022 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 219 | 85 | -0.6022 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 219 | 85 | -0.6022 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 219 | 85 | -0.6022 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 219 | 85 | -0.6022 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 219 | 85 | -0.6022 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 219 | 85 | -0.6022 | `keep_collecting` |
| `latency_state` | `simulated` | 219 | 85 | -0.6022 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 242 | 85 | -0.6022 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 216 | 82 | -0.4818 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 207 | 80 | -0.6223 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 189 | 68 | -0.483 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 94 | 44 | -1.0867 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 92 | 44 | -1.0867 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 93 | 44 | -1.0867 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 93 | 44 | -1.0867 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 93 | 44 | -1.0867 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_ok` | 126 | 41 | -0.0823 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 126 | 41 | -0.0823 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 148 | 41 | -0.0823 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 126 | 41 | -0.0823 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 126 | 41 | -0.0823 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 63 | 24 | -1.4588 | `keep_collecting` |
| `would_limit_fill` | `true` | 68 | 22 | -0.2512 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 37 | 20 | -1.2554 | `source_quality_workorder` |
| `would_limit_fill` | `false` | 173 | 19 | 0.1133 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_10s_plus` | 45 | 18 | -0.6676 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 58 | 17 | -0.1217 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 54 | 16 | 0.2551 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 39 | 15 | -0.6501 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_context_missing` | 28 | 14 | -0.4762 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 11 | 5 | -0.2806 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 10 | 5 | -0.6915 | `source_quality_workorder` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 3 | 3 | -3.8922 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 4 | 3 | -0.6432 | `source_quality_workorder` |
| `overbought_guard_action` | `would_block` | 3 | 3 | -3.8922 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 77 | 2 | -0.3933 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 3 | 2 | 0.0045 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 38, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 219 | 85 | -1.3573 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 219 | 85 | -1.3573 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 207 | 81 | -1.4181 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 63 | 59 | -2.1403 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 58 | 58 | -2.1274 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 9 | 8 | 0.2698 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 8 | 8 | 0.0575 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 8 | 8 | 0.0575 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 6 | 6 | 0.2224 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 5 | 5 | 1.7333 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 4 | 4 | 1.7787 | `hold_sample` |
| `holding_action` | `holding_action_not_applicable_at_start` | 7 | 3 | -0.0281 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 5 | 3 | 0.0733 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 3 | 3 | 0.0733 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 6 | 2 | -0.3 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 2 | 2 | -0.3 | `hold_sample` |
| `holding_action` | `BUY` | 3 | 1 | -0.4267 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | -0.4267 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1 | 1 | -2.886 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | 1.2504 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 1.5514 | `hold_sample` |
| `holding_action` | `DROP` | 2 | 0 | None | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 11 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 8 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 134 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 11 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=DROP|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 126 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_020_180s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos080_pos150|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 54, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 128 | 128 | -1.6593 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 100 | 100 | -0.9428 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 100 | 100 | -0.9428 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 100 | 100 | -0.9428 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 73 | 73 | -1.4787 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 71 | 71 | -1.2755 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 42 | 42 | -1.9713 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 32 | 32 | -2.0789 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 27 | 27 | -0.479 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 26 | 26 | -0.6767 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 24 | 24 | -0.5129 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 20 | 20 | -2.455 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 18 | 18 | 0.7534 | `candidate_recovery_or_relax` |
| `exit_outcome` | `NEUTRAL` | 15 | 15 | -1.5885 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 14 | 14 | -1.3178 | `hold_sample` |
| `exit_outcome` | `outcome_unknown` | 6019 | 11 | -0.3069 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 11 | 11 | -0.3069 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 11 | 11 | -0.3069 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 8 | 8 | 0.2298 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 8 | 8 | 0.0575 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 8 | 8 | -1.9054 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 7 | 7 | 2.3551 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 6 | 6 | 0.1558 | `hold_sample` |
| `exit_rule` | `scalp_hard_stop_pct` | 6 | 6 | -4.5643 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 4 | 4 | -0.7436 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 4 | 4 | -0.9694 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 4 | 4 | 1.0808 | `hold_sample` |
| `exit_rule` | `daily_limit_up_immediate_exit` | 3 | 3 | -2.7856 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 3 | 3 | 0.055 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 3 | 3 | -0.2075 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 3 | 3 | 0.2567 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 3 | 3 | -0.1496 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 3 | 3 | 1.2531 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 3 | 3 | 0.2672 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos150_pos300_plus` | 2 | 2 | 3.9095 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 2 | 2 | -5.5389 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 2 | 2 | -4.3141 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 2 | 2 | -3.8397 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 2 | 2 | -0.9288 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 2 | 2 | 2.4535 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 372, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 3730 | 3719 | None | -1.121 | 0.0837 | `hold_sample` |
| `arm` | `AVG_DOWN` | 3668 | 3603 | None | -1.301 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 3603 | 3538 | None | -1.2652 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 2384 | 2384 | None | -1.0867 | 0.1338 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 1193 | 1193 | None | -1.0067 | 0.1098 | `hold_sample` |
| `arm` | `PYRAMID` | 545 | 529 | None | 0.7939 | 0.9847 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 545 | 529 | None | 0.7939 | 0.9847 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 502 | 487 | None | -0.9426 | 0.0722 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 345 | 345 | None | -1.586 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 326 | 323 | None | -0.0685 | 0.5494 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 313 | 313 | None | 0.3971 | 0.9809 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 193 | 193 | None | -1.7726 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 168 | 168 | None | -1.295 | 0.1071 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 105 | 105 | None | -0.9402 | 0.0762 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.23)` | 101 | 101 | None | -0.23 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_scale_in_window_expansion` | 101 | 101 | None | -0.4917 | 0.297 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 86 | 86 | None | -0.8823 | 0.186 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 68 | 68 | None | -0.8884 | 0.2647 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 65 | 65 | None | -3.2461 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.08)` | 61 | 61 | None | -1.08 | 0.0 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 32, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 22 | 11 | -0.3069 | -0.4091 | 0.2727 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 11 | 11 | -0.3069 | -0.4091 | 0.2727 | `hold_sample` |
| `stage` | `exit` | 11 | 11 | -0.3069 | -0.4091 | 0.2727 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 22 | 11 | -0.3069 | -0.4091 | 0.2727 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 11 | 11 | -0.3069 | -0.4091 | 0.2727 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 20 | 10 | -0.2228 | -0.297 | 0.3 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 20 | 10 | -0.3203 | -0.427 | 0.3 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 16 | 8 | -0.3441 | -0.4587 | 0.375 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 16 | 8 | -0.5719 | -0.7625 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 4 | 4 | -0.1744 | -0.2325 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 8 | 4 | -0.9694 | -1.2925 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 8 | 4 | -0.1744 | -0.2325 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 3 | 3 | -0.91 | -1.2133 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 2 | 2 | 0.12 | 0.16 | 1.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 4 | 2 | -0.225 | -0.3 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 4 | 2 | 0.12 | 0.16 | 1.0 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 4 | 2 | 0.12 | 0.16 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 1 | 1 | 0.96 | 1.28 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_lt040|profit=profit_lt_neg070` | 1 | 1 | -1.1475 | -1.53 | 0.0 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |

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
