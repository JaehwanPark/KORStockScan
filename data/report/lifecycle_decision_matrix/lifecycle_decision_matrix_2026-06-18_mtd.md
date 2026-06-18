# Lifecycle Decision Matrix - 2026-06-18

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-18_mtd`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `209811`
- source_rows_total: `313773`
- retained_rows: `209811`
- dropped_rows_by_source: `{}`
- joined_rows: `192548`
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
- lifecycle_flow_bucket_count: `807`
- lifecycle_flow_complete_count: `991`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0052`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 10497 | 1497 | 0.7027 | 0.9755 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 3930 | 2624 | -0.5395 | 0.9978 | `pass` | `NO_CHANGE` | False |
| `holding` | 3680 | 2624 | -0.9264 | 0.9976 | `pass` | `EXIT` | False |
| `scale_in` | 183090 | 181125 | -0.432 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 8614 | 4678 | -0.9488 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 807, 'complete_flow_count': 991, 'incomplete_flow_count': 191222, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 142238 | 141631 | -0.722 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 38862 | 37504 | 0.6831 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 1663 | 1663 | -1.0547 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 313 | 313 | 1.5511 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 276 | 276 | 1.7386 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 200 | 200 | 1.4934 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 134 | 134 | -0.2911 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 55 | 55 | -0.9058 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:0e963d335b` | 39 | 39 | -0.8039 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 32 | 32 | -0.9106 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:8050d08a3f` | 19 | 19 | -2.058 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:2e5e6a8919` | 19 | 19 | -1.3559 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 17 | 17 | -1.2023 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9d8cac316e` | 14 | 14 | -0.5883 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:67138f9e63` | 14 | 14 | -0.9141 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:81b7841fa7` | 13 | 13 | -1.2754 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9b100ebd9b` | 12 | 12 | -1.0708 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:c7f35b773f` | 12 | 12 | -1.9011 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:3cbb81cd02` | 11 | 11 | -0.8866 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:92237a65fa` | 11 | 11 | -0.2686 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 456, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 6993 | 1490 | 0.7005 | 0.8164 | 0.4752 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 6818 | 1109 | 0.5821 | 0.3249 | 0.4572 | `source_quality_workorder` |
| `chosen_action` | `WAIT_REQUOTE` | 794 | 794 | 1.6042 | 2.5716 | 0.6688 | `hold_sample` |
| `exit_rule` | `exit_unknown` | 9794 | 794 | 1.6042 | 2.5716 | 0.6688 | `source_quality_workorder` |
| `chosen_action` | `NO_BUY_AI` | 7404 | 648 | -0.3004 | -1.2081 | 0.2469 | `source_quality_workorder` |
| `stale_bucket` | `fresh_or_unflagged` | 2228 | 547 | 1.2526 | 2.0493 | 0.6472 | `hold_sample` |
| `source_stage` | `wait6579_ev_cohort` | 547 | 547 | 1.2526 | 2.0493 | 0.6472 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 4663 | 542 | -0.0666 | -0.761 | 0.3007 | `source_quality_workorder` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 4281 | 532 | -0.3218 | -1.2272 | 0.2425 | `source_quality_workorder` |
| `stale_bucket` | `fresh` | 4892 | 531 | -0.3216 | -1.2314 | 0.241 | `source_quality_workorder` |
| `strength_bucket` | `strong_strength_momentum` | 996 | 490 | 1.1212 | 1.7786 | 0.6123 | `source_quality_workorder` |
| `time_bucket` | `time_1000_1200` | 2192 | 428 | 0.6251 | 0.725 | 0.507 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_soft_stop_pct` | 337 | 337 | -0.2231 | -1.972 | 0.0 | `source_quality_workorder` |
| `score_band` | `score_60_62` | 4305 | 323 | -0.3421 | -1.2932 | 0.2229 | `source_quality_workorder` |
| `score_band` | `score_70p` | 853 | 311 | 0.9423 | 1.6165 | 0.6109 | `source_quality_workorder` |
| `time_bucket` | `time_0900_1000` | 1333 | 222 | 0.4422 | 0.3525 | 0.4324 | `candidate_tighten_or_exclude` |
| `score_band` | `score_66_69` | 409 | 216 | 1.3049 | 1.9289 | 0.6204 | `hold_sample` |
| `score_band` | `score_63_65` | 725 | 190 | 0.61 | 0.8671 | 0.4895 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_watch` | 894 | 178 | 1.1683 | 1.5503 | 0.5113 | `source_quality_workorder` |
| `time_bucket` | `time_1200_1400` | 1375 | 176 | -0.0208 | -0.2569 | 0.3409 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_trailing_take_profit` | 175 | 175 | -0.551 | 1.9525 | 1.0 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 109 | 109 | 1.0404 | 1.3738 | 0.633 | `hold_no_edge` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 168, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 3797 | 2624 | -0.5395 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 3462 | 2624 | -0.5395 | `keep_collecting` |
| `latency_state` | `simulated` | 3462 | 2624 | -0.5395 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 3783 | 2624 | -0.5395 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 3419 | 2592 | -0.5244 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 3176 | 2427 | -0.5624 | `source_quality_workorder` |
| `revalidation_state` | `warning_stale_context_or_quote` | 2845 | 2164 | -0.5528 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 2790 | 2109 | -0.5838 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 2010 | 1534 | -0.5733 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 1954 | 1499 | -0.6935 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 1819 | 1499 | -0.6935 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 1819 | 1499 | -0.6935 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 1925 | 1466 | -0.6812 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 1705 | 1322 | -0.6265 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 1546 | 1167 | -0.419 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 1611 | 1125 | -0.3342 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 1611 | 1125 | -0.3342 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 1232 | 950 | -0.3815 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 1305 | 912 | -0.3095 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 1163 | 881 | -0.552 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 900 | 730 | -0.7803 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 749 | 523 | -0.3211 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_context_missing` | 654 | 483 | -0.2651 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 710 | 460 | -0.4765 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 484 | 382 | -0.4073 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 484 | 382 | -0.4073 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 484 | 382 | -0.4073 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 484 | 382 | -0.4073 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 484 | 382 | -0.4073 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 484 | 382 | -0.4073 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 312 | 264 | -0.5974 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 343 | 232 | -0.3937 | `source_quality_workorder` |
| `price_resolution_bucket` | `price_resolution_unknown` | 286 | 197 | -0.2568 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 724 | 197 | -0.2568 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 286 | 197 | -0.2568 | `keep_collecting` |
| `would_limit_fill` | `false` | 753 | 196 | -0.2584 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 206 | 179 | -0.3483 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=false|submitted=false` | 221 | 151 | -0.1159 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 163 | 140 | -0.5989 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 208 | 133 | -0.7387 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 47, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 3462 | 2624 | -0.9264 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 3462 | 2624 | -0.9264 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 2027 | 1943 | -1.4302 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 1991 | 1491 | -1.0227 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1112 | 1112 | -1.5039 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 1282 | 979 | -0.76 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 701 | 701 | -1.3148 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 233 | 216 | 0.2199 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 178 | 172 | 0.5821 | `candidate_recovery_or_relax` |
| `holding_action` | `BUY` | 189 | 154 | -1.052 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 193 | 141 | 0.0629 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 130 | 130 | -1.4227 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 122 | 122 | 0.1057 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 108 | 104 | 2.0106 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 94 | 94 | 0.0189 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 91 | 91 | 0.4683 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 90 | 90 | 0.3527 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 70 | 70 | 0.6981 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 49 | 49 | 1.9917 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 103 | 48 | -0.366 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 48 | 48 | 2.1227 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 45 | 45 | 0.1168 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 25 | 25 | -0.4043 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 23 | 23 | -0.3244 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 11 | 11 | 0.7844 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 7 | 7 | 1.3744 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 4 | 4 | 0.7123 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 2 | 2 | 0.919 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 218 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 65 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 153 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 838 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 218 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 35 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 303 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 500 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 27 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 57 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s` | 15 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 37 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 74, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 3479 | 3479 | -1.3292 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 2495 | 2495 | -0.9811 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 1965 | 1965 | -0.9908 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 1965 | 1965 | -0.9908 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 1965 | 1965 | -0.9908 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 1481 | 1481 | -1.2012 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 1117 | 1117 | -1.2891 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 951 | 951 | -1.4788 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 890 | 890 | -0.5124 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 714 | 714 | -1.7953 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 654 | 654 | -0.8954 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 570 | 570 | 0.5472 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 495 | 495 | -0.51 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 435 | 435 | -0.5393 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 387 | 387 | -1.7208 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 386 | 386 | -1.1912 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 344 | 344 | -0.9132 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 314 | 314 | -1.2442 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 294 | 294 | -2.4263 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 224 | 224 | 0.2372 | `hold_no_edge` |
| `exit_outcome` | `outcome_unknown` | 4154 | 218 | -0.2006 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 218 | 218 | -0.2006 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 218 | 218 | -0.2006 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 189 | 189 | 0.0751 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 181 | 181 | 0.682 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300_plus` | 110 | 110 | 2.2492 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 106 | 106 | -1.6781 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 87 | 87 | -0.5005 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 84 | 84 | -0.9637 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 84 | 84 | -0.3583 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 77 | 77 | 0.1082 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 67 | 67 | 1.0949 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 58 | 58 | 0.3174 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 55 | 55 | -0.2924 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 55 | 55 | 0.7728 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 52 | 52 | 0.2388 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 47 | 47 | 2.4159 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 42 | 42 | -0.4983 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 40 | 40 | -0.4387 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 40 | 40 | 0.9884 | `hold_no_edge` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 708, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_source` | `score_field_backfilled` | 181092 | 181092 | None | -0.5005 | 0.2031 | `hold_sample` |
| `arm` | `AVG_DOWN` | 144081 | 143474 | None | -0.7944 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_70p` | 103130 | 103130 | None | -0.5025 | 0.1999 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 100525 | 99918 | None | -0.9557 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 43556 | 43556 | None | -0.4242 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 39009 | 37651 | None | 0.6207 | 0.9776 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 39009 | 37651 | None | 0.6207 | 0.9776 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 33515 | 33515 | None | -0.4649 | 0.2155 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 31785 | 31785 | None | 0.5148 | 0.9814 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 23584 | 23584 | None | -0.515 | 0.2068 | `hold_sample` |
| `blocker_reason` | `add_judgment_locked` | 18480 | 18480 | None | -0.3262 | 0.1617 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 11605 | 11605 | None | -0.5098 | 0.1938 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 9258 | 9258 | None | -0.558 | 0.1958 | `hold_sample` |
| `blocker_reason` | `low_broken` | 4030 | 4030 | None | -0.4614 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 2231 | 2231 | None | -0.8337 | 0.078 | `hold_sample` |
| `blocker_reason` | `ok` | 1473 | 1473 | None | -2.3465 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.96)` | 1450 | 1450 | None | -0.96 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.20)` | 1432 | 1432 | None | -1.2 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.10)` | 1303 | 1303 | None | -1.1 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalping_cutoff` | 1279 | 1279 | None | -0.3215 | 0.1798 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 35, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 436 | 218 | -0.2006 | -0.2675 | 0.3303 | `candidate_tighten_or_exclude` |
| `overnight_status` | `SELL_TODAY` | 218 | 218 | -0.2006 | -0.2675 | 0.3303 | `candidate_tighten_or_exclude` |
| `confidence_band` | `confidence_070p` | 436 | 218 | -0.2006 | -0.2675 | 0.3303 | `candidate_tighten_or_exclude` |
| `stage` | `exit` | 218 | 218 | -0.2006 | -0.2675 | 0.3303 | `candidate_tighten_or_exclude` |
| `price_source` | `holding_price_samples_last` | 436 | 218 | -0.2006 | -0.2675 | 0.3303 | `candidate_tighten_or_exclude` |
| `source_quality_gate` | `overnight_decision_coverage` | 436 | 218 | -0.2006 | -0.2675 | 0.3303 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 218 | 218 | -0.2006 | -0.2675 | 0.3303 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s_plus` | 306 | 153 | -0.1629 | -0.2172 | 0.3595 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_lt_zero` | 292 | 146 | -0.6667 | -0.889 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 84 | 84 | -0.9637 | -1.285 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 168 | 84 | -0.9637 | -1.285 | 0.0 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s` | 130 | 65 | -0.2894 | -0.3859 | 0.2615 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 55 | 55 | -0.2924 | -0.3898 | 0.0 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 110 | 55 | -0.2924 | -0.3898 | 0.0 | `hold_no_edge` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 52 | 52 | 0.2388 | 0.3185 | 0.8654 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 104 | 52 | 0.2388 | 0.3185 | 0.8654 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 90 | 45 | 0.2828 | 0.3771 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 17 | 17 | 0.8713 | 1.1618 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 34 | 17 | 0.8713 | 1.1618 | 1.0 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 34 | 17 | 0.8713 | 1.1618 | 1.0 | `hold_sample` |

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
