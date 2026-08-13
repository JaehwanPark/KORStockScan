# Lifecycle Decision Matrix - 2026-08-13

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-08-13_rolling5d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `6736`
- source_rows_total: `7603`
- retained_rows: `6736`
- dropped_rows_by_source: `{}`
- joined_rows: `3108`
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
- lifecycle_flow_bucket_count: `64`
- lifecycle_flow_complete_count: `26`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0054`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 2320 | 23 | -0.101 | 0.0134 | `pass` | `NO_CHANGE` | False |
| `submit` | 169 | 33 | -0.3381 | 0.3487 | `pass` | `NO_CHANGE` | False |
| `holding` | 44 | 33 | -0.6465 | 0.7859 | `pass` | `EXIT` | False |
| `scale_in` | 3017 | 2984 | -0.8118 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 1186 | 35 | -0.611 | 0.4363 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 64, 'complete_flow_count': 26, 'incomplete_flow_count': 4759, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 2768 | 2736 | -0.9148 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 249 | 248 | 0.3245 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:4e1fc29475` | 4 | 4 | -0.842 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:5159f83a5b` | 3 | 3 | -0.1136 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:305d9e5c71` | 3 | 3 | -0.2375 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:5ad377bcf7` | 1 | 1 | -0.4211 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:7dd76f2392` | 1 | 1 | -2.1224 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:31a116e56b` | 1 | 1 | -0.7246 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:7664e5a914` | 1 | 1 | -0.1193 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:1fbcba9334` | 1 | 1 | 0.0719 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:f3f2837f26` | 1 | 1 | -1.6262 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:7e17ca9764` | 1 | 1 | -2.1951 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:1230ecd40d` | 1 | 1 | -0.0415 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_bloc:f2f4676367` | 1 | 1 | 0.1639 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:f15e79e2f2` | 1 | 1 | -1.3447 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:ce05b30c9f` | 1 | 1 | -0.9949 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:d3cb9791fb` | 1 | 1 | -1.7547 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:d95dd39f2f` | 1 | 1 | 0.2263 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:7946d42f06` | 1 | 1 | -2.063 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:88970cb1c3` | 1 | 1 | 0.5237 | `candidate_recovery_or_relax` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 262, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 195 | 18 | -0.1731 | -1.1878 | 0.3334 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_not_available` | 993 | 18 | -0.1731 | -1.1878 | 0.3334 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_not_available` | 781 | 18 | -0.1731 | -1.1878 | 0.3334 | `source_quality_workorder` |
| `strength_bucket` | `risk_context_not_available` | 184 | 18 | -0.1731 | -1.1878 | 0.3334 | `hold_no_edge` |
| `source_stage` | `scalp_sim_entry_ai_price_skip_order` | 184 | 18 | -0.1731 | -1.1878 | 0.3334 | `hold_no_edge` |
| `stale_bucket` | `stale_not_available` | 677 | 18 | -0.1731 | -1.1878 | 0.3334 | `source_quality_workorder` |
| `score_band` | `score_63_65` | 222 | 15 | -0.2021 | -0.8047 | 0.4 | `hold_no_edge` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 10 | 10 | 0.2287 | -1.502 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1000_1200` | 73 | 9 | -0.2838 | -1.0044 | 0.3333 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 587 | 9 | -0.2838 | -1.0044 | 0.3333 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 8 | 8 | -0.6963 | 0.47 | 1.0 | `hold_sample` |
| `time_bucket` | `time_0900_1000` | 423 | 7 | 0.5085 | -1.2871 | 0.2857 | `source_quality_workorder` |
| `time_bucket` | `time_1200_1400` | 483 | 6 | -0.6238 | -1.9667 | 0.3333 | `source_quality_workorder` |
| `chosen_action` | `NO_BUY_AI` | 1527 | 5 | 0.1585 | -1.67 | 0.4 | `hold_sample` |
| `stale_bucket` | `fresh` | 1453 | 5 | 0.1585 | -1.67 | 0.4 | `hold_sample` |
| `liquidity_bucket` | `liquidity_high` | 1263 | 5 | 0.1585 | -1.67 | 0.4 | `hold_sample` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 1676 | 5 | 0.1585 | -1.67 | 0.4 | `source_quality_workorder` |
| `exit_rule` | `scalp_soft_stop_pct` | 5 | 5 | 0.1921 | -3.694 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_0900_1000` | 17 | 5 | 0.6121 | -0.7 | 0.4 | `hold_sample` |
| `score_band` | `score_60_62` | 26 | 4 | 0.0832 | -2.2975 | 0.25 | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 96, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 164 | 33 | -0.3381 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 165 | 33 | -0.3381 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 42 | 33 | -0.3381 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 42 | 33 | -0.3381 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 42 | 33 | -0.3381 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 42 | 33 | -0.3381 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 42 | 33 | -0.3381 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 42 | 33 | -0.3381 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 42 | 33 | -0.3381 | `keep_collecting` |
| `latency_state` | `simulated` | 42 | 33 | -0.3381 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 164 | 33 | -0.3381 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 42 | 33 | -0.3381 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 33 | 27 | -0.1796 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 24 | 22 | -0.2561 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 27 | 19 | 0.0858 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 26 | 19 | 0.0858 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 144 | 19 | 0.0858 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 26 | 19 | 0.0858 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 27 | 19 | 0.0858 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 17 | 14 | -0.9134 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 16 | 14 | -0.9134 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 14 | 14 | -0.9134 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 15 | 14 | -0.9134 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 16 | 14 | -0.9134 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_3_10s` | 21 | 13 | -1.0199 | `keep_collecting` |
| `would_limit_fill` | `false` | 143 | 12 | -0.1446 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 19 | 11 | -0.502 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 9 | 8 | -0.1201 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 7 | 7 | -1.0857 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 10 | 7 | 0.481 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 8 | 6 | -1.0513 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 6 | 6 | 0.4092 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 6 | 6 | -0.943 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 7 | 4 | -0.1938 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_1_3s` | 1 | 1 | 0.4716 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 4 | 1 | 0.9116 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | 0.4716 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 1 | 0 | None | `keep_collecting` |
| `latency_state` | `caution` | 5 | 0 | None | `keep_collecting` |
| `latency_reason` | `caution_normal_entry_allowed` | 5 | 0 | None | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 24, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 40 | 33 | -0.6465 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 40 | 33 | -0.6465 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 33 | 27 | -0.6368 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 16 | 16 | -0.9538 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 15 | 15 | -0.9004 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 10 | 10 | -0.5547 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 7 | 6 | -0.6903 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 6 | 6 | -0.4393 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 8 | 4 | -0.4603 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 4 | 4 | -0.4603 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 4 | 4 | -0.7278 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 3 | 3 | 0.4378 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 0.3948 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1 | 1 | -1.7547 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | 0.5237 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 4 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 3 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 7 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 6 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_020_180s` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 33, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `exit_source_stage` | `sim_post_sell_evaluation` | 31 | 31 | -0.6613 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 16 | 16 | -0.9538 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 14 | 14 | -0.3661 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 13 | 13 | -0.7328 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 11 | 11 | -0.5732 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 10 | 10 | -0.151 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 10 | 10 | -0.5547 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 8 | 8 | -1.1831 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 6 | 6 | -0.3152 | `hold_sample` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 5 | 5 | -0.2 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 5 | 5 | -1.791 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 5 | 5 | -0.1196 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 5 | 5 | -0.8726 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 5 | 5 | -0.2196 | `hold_sample` |
| `exit_outcome` | `COMPLETED` | 4 | 4 | -0.2212 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 4 | 4 | -0.2212 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 4 | 4 | -0.2212 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 4 | 4 | -1.0824 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 3 | 3 | 0.4378 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 2 | 2 | -1.8743 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 2 | 2 | -1.9749 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 2 | 2 | 0.6774 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 1 | 1 | -1.3447 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=NEUTRAL|profit=profit_neg070_neg010` | 1 | 1 | -0.115 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | -1.2568 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 1 | 1 | -0.0415 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 1 | 1 | -0.1193 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg070_neg010` | 1 | 1 | -0.8911 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 1151 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_context_noop` | 1151 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 1151 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_context_warning_not_applicable` | 1151 | 0 | None | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=scalp_sim_panic_context_warning_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 1151 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 215, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `price_guard_reason` | `price_guard_none` | 3017 | 2984 | None | -0.8858 | 0.0777 | `hold_sample` |
| `qty_reason` | `qty_none` | 2984 | 2984 | None | -0.8858 | 0.0777 | `hold_sample` |
| `time_bucket` | `time_unknown` | 3017 | 2984 | None | -0.8858 | 0.0777 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 2979 | 2978 | None | -0.8886 | 0.0759 | `hold_sample` |
| `arm` | `AVG_DOWN` | 2768 | 2736 | None | -0.9936 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 2762 | 2730 | None | -0.9883 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 1946 | 1946 | None | -1.2229 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 1654 | 1654 | None | -0.99 | 0.0526 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 1642 | 1609 | None | -0.7974 | 0.1442 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 1510 | 1510 | None | -0.8705 | 0.0861 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 1412 | 1379 | None | -0.9857 | 0.0029 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 1137 | 1137 | None | -1.0332 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 887 | 887 | None | -0.8679 | 0.0913 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 743 | 743 | None | -0.7548 | 0.1373 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 714 | 714 | None | -0.4693 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 456 | 456 | None | -0.2587 | 0.4759 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_1` | 456 | 456 | None | -1.1548 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 374 | 374 | None | -0.7542 | 0.0776 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_2` | 329 | 329 | None | -1.0005 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 319 | 319 | None | 0.2092 | 0.7116 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 17, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 8 | 4 | -0.2212 | -0.295 | 0.0 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 4 | 4 | -0.2212 | -0.295 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 4 | 4 | -0.2212 | -0.295 | 0.0 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 8 | 4 | -0.2212 | -0.295 | 0.0 | `hold_sample` |
| `stage` | `exit` | 4 | 4 | -0.2212 | -0.295 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 8 | 4 | -0.2212 | -0.295 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 8 | 4 | -0.2212 | -0.295 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 8 | 4 | -0.2212 | -0.295 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 4 | 4 | -0.2212 | -0.295 | 0.0 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 6 | 3 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 6 | 3 | -0.2375 | -0.3167 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 2 | 1 | -0.3675 | -0.49 | 0.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 4 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 4 | 0 | None | None | None | `hold_sample` |
| `stage` | `holding` | 4 | 0 | None | None | None | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_decision` | 4 | 0 | None | None | None | `hold_sample` |

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
