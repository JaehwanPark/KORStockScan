# Lifecycle Decision Matrix - 2026-09-04

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-09-04_rolling10d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `18592`
- source_rows_total: `22978`
- retained_rows: `18592`
- dropped_rows_by_source: `{}`
- joined_rows: `10177`
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
- lifecycle_flow_bucket_count: `124`
- lifecycle_flow_complete_count: `76`
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
| `entry` | 4997 | 50 | 0.3813 | 0.012 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 529 | 82 | -0.9777 | 0.2018 | `pass` | `NO_CHANGE` | False |
| `holding` | 110 | 82 | -1.0276 | 0.8392 | `pass` | `EXIT` | False |
| `scale_in` | 9886 | 9821 | -0.8324 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 3070 | 142 | -0.9669 | 0.2777 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 124, 'complete_flow_count': 76, 'incomplete_flow_count': 14025, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 9028 | 8966 | -0.9593 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 858 | 855 | 0.498 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 7 | 7 | 3.9599 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:0cb91a7ba6` | 6 | 6 | -0.8217 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:5ee2a7cfd7` | 5 | 5 | -1.216 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:f58154b780` | 3 | 3 | -0.9967 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:7a29eed6f7` | 2 | 2 | -1.1552 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:42bc391d5b` | 2 | 2 | -0.7738 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:a6af469504` | 2 | 2 | -0.56 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:b31cc048c8` | 2 | 2 | -0.83 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:8de6b2fa46` | 2 | 2 | -1.035 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:36904223da` | 2 | 2 | -0.715 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:bf44bd3042` | 1 | 1 | -0.65 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:1793c3951c` | 1 | 1 | -0.6466 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:05c0ca21ce` | 1 | 1 | 0.045 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:f4d0891804` | 1 | 1 | -0.88 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:a9d1313d5d` | 1 | 1 | 0.1763 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:8880885eab` | 1 | 1 | -1.05 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:7ee2fdca81` | 1 | 1 | 0.0318 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 1 | 1 | 2.5732 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 318, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 1945 | 47 | 0.4164 | 0.0003 | 0.3617 | `candidate_tighten_or_exclude` |
| `chosen_action` | `NO_BUY_AI` | 2269 | 39 | -0.275 | -1.2803 | 0.282 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 4162 | 39 | -0.275 | -1.2803 | 0.282 | `candidate_tighten_or_exclude` |
| `stale_bucket` | `fresh` | 2388 | 38 | -0.2642 | -1.2721 | 0.2895 | `candidate_tighten_or_exclude` |
| `score_band` | `score_63_65` | 134 | 28 | 0.006 | -0.9859 | 0.3214 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 1359 | 27 | -0.0698 | -1.2121 | 0.2593 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 1919 | 26 | -0.191 | -1.3 | 0.2308 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 667 | 21 | 0.1212 | -0.9779 | 0.2381 | `hold_sample` |
| `overbought_bucket` | `overbought_watch` | 1097 | 19 | 0.519 | -0.0936 | 0.3684 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 19 | 19 | -0.1088 | -1.511 | 0.0 | `hold_sample` |
| `score_band` | `score_70p` | 221 | 15 | 1.4677 | 2.3259 | 0.5333 | `hold_sample` |
| `time_bucket` | `time_1200_1400` | 1231 | 13 | 0.5812 | 0.7389 | 0.4615 | `hold_sample` |
| `strength_bucket` | `neutral_strength_momentum` | 2177 | 12 | 1.326 | 2.9842 | 0.6667 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 12 | 12 | -0.5092 | 0.5542 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 17 | 12 | -0.1834 | -1.1917 | 0.1667 | `hold_sample` |
| `strength_bucket` | `strong_strength_momentum` | 538 | 9 | 0.958 | -0.2221 | 0.3333 | `hold_sample` |
| `chosen_action` | `WAIT_REQUOTE` | 1910 | 8 | 3.7866 | 6.2428 | 0.75 | `hold_sample` |
| `exit_rule` | `exit_unknown` | 4955 | 8 | 3.7866 | 6.2428 | 0.75 | `hold_sample` |
| `stale_bucket` | `fresh_or_unflagged` | 76 | 8 | 3.7866 | 6.2428 | 0.75 | `hold_sample` |
| `source_stage` | `wait6579_ev_cohort` | 8 | 8 | 3.7866 | 6.2428 | 0.75 | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 119, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 503 | 82 | -0.9777 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 506 | 82 | -0.9777 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 103 | 82 | -0.9777 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 103 | 82 | -0.9777 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 103 | 82 | -0.9777 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 103 | 82 | -0.9777 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 103 | 82 | -0.9777 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 103 | 82 | -0.9777 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 103 | 82 | -0.9777 | `keep_collecting` |
| `latency_state` | `simulated` | 103 | 82 | -0.9777 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 503 | 82 | -0.9777 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 100 | 80 | -0.9087 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 91 | 72 | -1.0699 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 80 | 61 | -0.8763 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 64 | 44 | -0.4666 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 64 | 44 | -0.4666 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 60 | 43 | -0.3073 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 441 | 43 | -0.3073 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 60 | 43 | -0.3073 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 43 | 39 | -1.7169 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 43 | 39 | -1.7169 | `source_quality_workorder` |
| `liquidity_bucket` | `below_min_liquidity` | 40 | 38 | -1.5695 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 38 | 38 | -1.5695 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 39 | 38 | -1.5695 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 56 | 30 | -1.9663 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 27 | 27 | -2.1374 | `source_quality_workorder` |
| `would_limit_fill` | `false` | 464 | 26 | -0.3801 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 36 | 24 | -0.4451 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 22 | 17 | -0.1959 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 19 | 15 | -0.2107 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 16 | 14 | -0.9905 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_10s_plus` | 26 | 9 | -0.8856 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 9 | 8 | 0.5424 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 6 | 6 | -1.74 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 6 | 6 | -0.9139 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 3 | 3 | -0.4262 | `source_quality_workorder` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 3 | 2 | -3.7378 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 2 | 2 | 0.3994 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 3 | 2 | -0.0849 | `source_quality_workorder` |
| `overbought_guard_action` | `would_block` | 3 | 2 | -3.7378 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 31, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 100 | 82 | -1.0276 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 100 | 82 | -1.0276 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 92 | 75 | -1.1519 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 54 | 48 | -1.5314 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 47 | 47 | -1.5283 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 21 | 20 | -0.3511 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 15 | 15 | -0.403 | `hold_no_edge` |
| `holding_action` | `holding_action_not_applicable_at_start` | 8 | 7 | 0.3034 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 5 | 5 | -1.0812 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 5 | 5 | -0.5373 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 5 | 5 | -1.0812 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 5 | 5 | -0.5373 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 5 | 5 | -0.1955 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 6 | 3 | -0.1404 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 3 | 3 | -0.1404 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 1 | 1 | 4.7784 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1 | 1 | -1.677 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 4.7784 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 10 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 8 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 18 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 10 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 17 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_180_600s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 5 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 52, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 92 | 92 | -1.3152 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 84 | 84 | -0.9851 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 48 | 48 | -0.9404 | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 48 | 48 | -0.9404 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 48 | 48 | -0.9404 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 38 | 38 | -1.0487 | `hold_sample` |
| `exit_outcome` | `GOOD_EXIT` | 34 | 34 | -1.5008 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 33 | 33 | -0.2907 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 31 | 31 | -0.8248 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 22 | 22 | -0.2991 | `hold_no_edge` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 22 | 22 | -0.8715 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 20 | 20 | -2.34 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 19 | 19 | -0.3241 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 19 | 19 | -0.8736 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 17 | 17 | -0.3771 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 11 | 11 | -0.7197 | `hold_sample` |
| `exit_outcome` | `COMPLETED` | 10 | 10 | -0.9412 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 10 | 10 | -0.9412 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 10 | 10 | -0.529 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 10 | 10 | -2.627 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 10 | 10 | -0.3632 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_lt_neg070` | 6 | 6 | -1.4787 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 6 | 6 | -1.3259 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 6 | 6 | -0.6252 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 5 | 5 | -1.0812 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 5 | 5 | -0.5373 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 5 | 5 | -0.6603 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 5 | 5 | -2.1816 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 5 | 5 | -1.9245 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 4 | 4 | -1.1675 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 4 | 4 | 0.227 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 3 | 3 | -0.195 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 3 | 3 | -1.7414 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 3 | 3 | -0.9618 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=NEUTRAL|profit=profit_neg070_neg010` | 2 | 2 | -0.6683 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 1 | 1 | 4.7784 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg010_pos080` | 1 | 1 | 0.045 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 1 | 1 | -0.1496 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | -0.4217 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=MISSED_UPSIDE|profit=profit_neg070_neg010` | 1 | 1 | 0.9211 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 386, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `price_guard_reason` | `price_guard_none` | 9883 | 9821 | None | -0.9158 | 0.085 | `hold_sample` |
| `qty_reason` | `qty_none` | 9824 | 9821 | None | -0.9158 | 0.085 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 9809 | 9807 | None | -0.9188 | 0.0839 | `hold_sample` |
| `arm` | `AVG_DOWN` | 9028 | 8966 | None | -1.0477 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 8955 | 8893 | None | -1.0301 | 0.0 | `hold_sample` |
| `time_bucket` | `time_unknown` | 7015 | 6969 | None | -0.8489 | 0.1103 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 5867 | 5867 | None | -0.9243 | 0.0926 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 5473 | 5473 | None | -1.4495 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 5238 | 5238 | None | -0.9893 | 0.0993 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 4690 | 4625 | None | -1.0387 | 0.0004 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 3822 | 3776 | None | -0.713 | 0.2036 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 3258 | 3258 | None | -0.4434 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 3247 | 3247 | None | -1.0923 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 2566 | 2566 | None | -0.9217 | 0.06 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 1749 | 1749 | None | -0.5017 | 0.3613 | `hold_sample` |
| `ai_score_source` | `live` | 1733 | 1733 | None | -0.8828 | 0.1148 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_1` | 1649 | 1649 | None | -1.0838 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 1317 | 1317 | None | -0.7003 | 0.0979 | `hold_sample` |
| `ai_score_source` | `holding_ai_not_called` | 966 | 966 | None | -0.9853 | 0.0321 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 915 | 915 | None | 0.1832 | 0.7224 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 20 | 10 | -0.9412 | -1.255 | 0.1 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 10 | 10 | -0.9412 | -1.255 | 0.1 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 20 | 10 | -0.9412 | -1.255 | 0.1 | `hold_sample` |
| `stage` | `exit` | 10 | 10 | -0.9412 | -1.255 | 0.1 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 20 | 10 | -0.9412 | -1.255 | 0.1 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 10 | 10 | -0.9412 | -1.255 | 0.1 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 18 | 9 | -1.0267 | -1.3689 | 0.1111 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 18 | 9 | -1.0508 | -1.4011 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 16 | 8 | -1.064 | -1.4188 | 0.125 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 6 | 6 | -1.4787 | -1.9717 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 12 | 6 | -1.4787 | -1.9717 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 3 | 3 | -0.195 | -0.26 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 6 | 3 | -0.195 | -0.26 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 1 | 1 | 0.045 | 0.06 | 1.0 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 2 | 1 | -0.7725 | -1.03 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 2 | 1 | -0.1275 | -0.17 | 0.0 | `hold_sample` |
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
