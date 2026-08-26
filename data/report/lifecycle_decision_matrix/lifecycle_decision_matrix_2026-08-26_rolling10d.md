# Lifecycle Decision Matrix - 2026-08-26

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-08-26_rolling10d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `18019`
- source_rows_total: `22860`
- retained_rows: `18019`
- dropped_rows_by_source: `{}`
- joined_rows: `8861`
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
- lifecycle_flow_bucket_count: `150`
- lifecycle_flow_complete_count: `100`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0073`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 4735 | 57 | -0.4617 | 0.0149 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 584 | 117 | -0.7859 | 0.4393 | `pass` | `NO_CHANGE` | False |
| `holding` | 147 | 115 | -0.9419 | 0.9576 | `pass` | `EXIT` | False |
| `scale_in` | 8425 | 8373 | -0.9068 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 4128 | 199 | -0.9124 | 0.3744 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 150, 'complete_flow_count': 100, 'incomplete_flow_count': 13548, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 7790 | 7738 | -1.0098 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 634 | 634 | 0.3503 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:0cb91a7ba6` | 5 | 5 | -1.034 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:a6af469504` | 4 | 4 | -0.9775 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:03eec49aed` | 4 | 4 | -0.9565 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:f658be39ac` | 3 | 3 | -1.26 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_ai_c:a101f93752` | 2 | 2 | -0.845 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:5c4d0773e1` | 2 | 2 | -1.0275 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:b0bc92a886` | 2 | 2 | -1.365 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:27b40f1c54` | 2 | 2 | -0.755 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:77c2d7d131` | 2 | 2 | -1.195 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:2ee314bc27` | 2 | 2 | -0.995 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:b31cc048c8` | 2 | 2 | -2.265 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:bbe961df76` | 2 | 2 | -0.985 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:6669d1917b` | 2 | 2 | -1.3 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:bf44bd3042` | 1 | 1 | -0.53 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:92f69621e6` | 1 | 1 | -1.21 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_bl:e2e349e4ea` | 1 | 1 | -1.2 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:53097ae10f` | 1 | 1 | -0.2008 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:f58154b780` | 1 | 1 | -1.31 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 314, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 3887 | 55 | -0.3921 | -1.1435 | 0.3454 | `source_quality_workorder` |
| `chosen_action` | `NO_BUY_AI` | 2156 | 53 | -0.4204 | -1.2036 | 0.3207 | `candidate_tighten_or_exclude` |
| `liquidity_bucket` | `liquidity_high` | 1856 | 53 | -0.4204 | -1.2036 | 0.3207 | `candidate_tighten_or_exclude` |
| `stale_bucket` | `fresh` | 2555 | 52 | -0.4154 | -1.1962 | 0.3269 | `candidate_tighten_or_exclude` |
| `strength_bucket` | `weak_strength_momentum` | 1848 | 38 | -0.5874 | -1.3271 | 0.2632 | `candidate_tighten_or_exclude` |
| `time_bucket` | `time_1000_1200` | 1352 | 30 | -0.4145 | -1.266 | 0.2666 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_normal` | 584 | 27 | -0.0828 | -1.0678 | 0.2222 | `hold_sample` |
| `score_band` | `score_70p` | 371 | 27 | -0.4963 | -1.2326 | 0.2592 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 26 | 26 | -0.223 | -1.5211 | 0.0 | `hold_sample` |
| `overbought_bucket` | `overbought_watch` | 1077 | 20 | -0.5499 | -1.75 | 0.3 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 20 | 20 | -0.7616 | 0.4145 | 0.9 | `hold_sample` |
| `score_band` | `score_63_65` | 110 | 18 | -0.5374 | -0.9144 | 0.4444 | `hold_sample` |
| `time_bucket` | `time_1200_1400` | 981 | 12 | -0.1969 | -1.4658 | 0.3333 | `source_quality_workorder` |
| `strength_bucket` | `neutral_strength_momentum` | 2134 | 10 | 0.092 | -0.345 | 0.7 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 9 | 9 | -0.5173 | -3.4122 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 24 | 9 | -0.0178 | -0.9266 | 0.3333 | `hold_sample` |
| `score_band` | `score_lt60` | 4236 | 8 | -0.3441 | -1.2312 | 0.375 | `source_quality_workorder` |
| `time_bucket` | `time_0900_1000` | 1001 | 8 | -0.7051 | -1.0513 | 0.125 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 8 | 7 | -0.2378 | -0.9743 | 0.2857 | `hold_sample` |
| `strength_bucket` | `strong_strength_momentum` | 490 | 7 | -0.0231 | -1.2871 | 0.2857 | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 122, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 512 | 117 | -0.7859 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 144 | 117 | -0.7859 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 144 | 117 | -0.7859 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 144 | 117 | -0.7859 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 144 | 117 | -0.7859 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 144 | 117 | -0.7859 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 144 | 117 | -0.7859 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 144 | 117 | -0.7859 | `keep_collecting` |
| `latency_state` | `simulated` | 144 | 117 | -0.7859 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 512 | 117 | -0.7859 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 562 | 115 | -0.8042 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 136 | 109 | -0.7519 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 99 | 78 | -0.7882 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 90 | 68 | -0.4591 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 90 | 68 | -0.4591 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 77 | 60 | -0.6455 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 78 | 60 | -0.4398 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 428 | 60 | -0.4398 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 78 | 60 | -0.4398 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 66 | 57 | -1.1502 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 66 | 57 | -1.1502 | `source_quality_workorder` |
| `liquidity_bucket` | `below_min_liquidity` | 58 | 49 | -1.2394 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 53 | 49 | -1.2394 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 54 | 49 | -1.2394 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 110 | 48 | -1.1707 | `keep_collecting` |
| `would_limit_fill` | `false` | 493 | 42 | -0.4866 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 41 | 35 | -0.7005 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 39 | 33 | -0.4989 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_context_missing` | 37 | 31 | -0.6605 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 23 | 21 | -1.6777 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 24 | 20 | -1.3031 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 20 | 19 | -1.0651 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 25 | 18 | -0.3305 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 25 | 18 | -0.3305 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_10s_plus` | 17 | 9 | -1.0407 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 14 | 9 | -0.4415 | `source_quality_workorder` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 8 | 8 | -1.2491 | `keep_collecting` |
| `overbought_guard_action` | `would_block` | 8 | 8 | -1.2491 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_overbought_guard_would_block` | 6 | 6 | -0.8952 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 6 | 5 | -0.8046 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 38, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 137 | 115 | -0.9419 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 137 | 115 | -0.9419 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 88 | 74 | -1.0165 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 68 | 62 | -1.4474 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 45 | 45 | -1.2837 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 48 | 40 | -0.8223 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 31 | 30 | -0.4035 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 17 | 17 | -0.3767 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 17 | 17 | -1.8806 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 12 | 12 | -0.4584 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 12 | 9 | -0.8482 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 8 | 8 | 0.2443 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 5 | 5 | -0.2161 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 5 | 5 | -1.4322 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 5 | 5 | -0.6689 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 4 | 4 | -0.1182 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 3 | 3 | 1.7663 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 3 | 3 | -0.179 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 2 | 2 | -0.2718 | `hold_sample` |
| `holding_action` | `BUY` | 1 | 1 | -0.2008 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 1 | 1 | 0.2903 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | -0.2008 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 0.2903 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 10 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 4 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 4 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 22 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 10 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 14 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 8 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_020_180s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_180_600s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 51, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 112 | 112 | -1.3003 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 110 | 110 | -0.9183 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 79 | 79 | -0.9068 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 79 | 79 | -0.9068 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 79 | 79 | -0.9068 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 49 | 49 | -0.3335 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 48 | 48 | -1.141 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 42 | 42 | -0.5962 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 40 | 40 | -0.778 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 37 | 37 | -1.5211 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 33 | 33 | -0.4126 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 31 | 31 | -0.389 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 31 | 31 | -0.5442 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 28 | 28 | -0.9468 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 28 | 28 | -1.9464 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 18 | 18 | -0.8602 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 15 | 15 | -0.8386 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 15 | 15 | -1.432 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 12 | 12 | -1.257 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `COMPLETED` | 10 | 10 | -0.8918 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 10 | 10 | -0.8918 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 10 | 10 | -0.0899 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 8 | 8 | 0.2443 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 7 | 7 | -3.0391 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 7 | 7 | 0.5754 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_lt_neg070` | 6 | 6 | -1.3075 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 6 | 6 | -1.3825 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 6 | 6 | -1.9577 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 5 | 5 | -0.2161 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 4 | 4 | -0.6829 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 4 | 4 | -0.7113 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 3 | 3 | -0.3725 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 3 | 3 | -1.0385 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg070_neg010` | 3 | 3 | 0.3314 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 3 | 3 | 1.2699 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=NEUTRAL|profit=profit_neg070_neg010` | 2 | 2 | -0.7522 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg070_neg010` | 2 | 2 | -2.1641 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 2 | 2 | 0.6301 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 1 | 1 | 0.2903 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg010_pos080` | 1 | 1 | 0.045 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 371, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 8361 | 8361 | None | -0.9962 | 0.0713 | `hold_sample` |
| `arm` | `AVG_DOWN` | 7791 | 7739 | None | -1.102 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 7698 | 7646 | None | -1.077 | 0.0 | `hold_sample` |
| `price_guard_reason` | `price_guard_none` | 6925 | 6886 | None | -0.903 | 0.0793 | `hold_sample` |
| `qty_reason` | `qty_none` | 6886 | 6886 | None | -0.903 | 0.0793 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 4453 | 4453 | None | -0.9942 | 0.077 | `hold_sample` |
| `time_bucket` | `time_unknown` | 4054 | 4034 | None | -0.7784 | 0.119 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 3983 | 3983 | None | -0.8568 | 0.1162 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 3771 | 3771 | None | -1.397 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 3265 | 3226 | None | -0.9997 | 0.0003 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 2795 | 2795 | None | -1.0599 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 2450 | 2450 | None | -0.4534 | 0.0 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 2256 | 2236 | None | -0.6698 | 0.2147 | `hold_sample` |
| `ai_score_source` | `live` | 2031 | 2031 | None | -0.9676 | 0.097 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 1544 | 1544 | None | -1.0797 | 0.0214 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 893 | 893 | None | -0.8667 | 0.0448 | `hold_sample` |
| `ai_score_source` | `not_evaluated_no_ai_score_source` | 848 | 848 | None | -0.8259 | 0.0224 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 833 | 833 | None | -0.0725 | 0.6183 | `hold_sample` |
| `ai_score_source` | `holding_ai_not_called` | 663 | 663 | None | -1.1507 | 0.0362 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_1` | 643 | 643 | None | -1.0611 | 0.0 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 25, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 20 | 10 | -0.8918 | -1.189 | 0.1 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 10 | 10 | -0.8918 | -1.189 | 0.1 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 20 | 10 | -0.8918 | -1.189 | 0.1 | `hold_sample` |
| `stage` | `exit` | 10 | 10 | -0.8918 | -1.189 | 0.1 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 20 | 10 | -0.8918 | -1.189 | 0.1 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 20 | 10 | -0.8918 | -1.189 | 0.1 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 10 | 10 | -0.8918 | -1.189 | 0.1 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 18 | 9 | -0.9958 | -1.3278 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 6 | 6 | -1.3075 | -1.7434 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 12 | 6 | -1.3075 | -1.7434 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 8 | 4 | -1.26 | -1.68 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 8 | 4 | -0.6581 | -0.8775 | 0.25 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 3 | 3 | -0.3725 | -0.4967 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 6 | 3 | -0.3725 | -0.4967 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 1 | 1 | 0.045 | 0.06 | 1.0 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 2 | 1 | -0.8475 | -1.13 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 2 | 1 | -0.3975 | -0.53 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 2 | 1 | 0.045 | 0.06 | 1.0 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 2 | 1 | 0.045 | 0.06 | 1.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 10 | 0 | None | None | None | `hold_sample` |

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
