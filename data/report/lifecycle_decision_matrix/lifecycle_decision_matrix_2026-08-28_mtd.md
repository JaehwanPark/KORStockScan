# Lifecycle Decision Matrix - 2026-08-28

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-08-28_mtd`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `37605`
- source_rows_total: `48434`
- retained_rows: `37605`
- dropped_rows_by_source: `{}`
- joined_rows: `16655`
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
- lifecycle_flow_bucket_count: `245`
- lifecycle_flow_complete_count: `170`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0064`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 13400 | 175 | 1.0217 | 0.1342 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 1172 | 193 | -0.7051 | 0.3546 | `pass` | `NO_CHANGE` | False |
| `holding` | 266 | 191 | -0.845 | 0.8122 | `pass` | `EXIT` | False |
| `scale_in` | 15918 | 15789 | -0.8167 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 6849 | 307 | -0.8083 | 0.3678 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 245, 'complete_flow_count': 170, 'incomplete_flow_count': 26242, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 14543 | 14417 | -0.9299 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 1374 | 1371 | 0.3737 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 58 | 58 | 3.4417 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:0cb91a7ba6` | 7 | 7 | -0.9329 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:a6af469504` | 5 | 5 | -0.974 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:f658be39ac` | 5 | 5 | -1.5 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:4e1fc29475` | 4 | 4 | -0.842 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:d0233209ef` | 4 | 4 | -0.6925 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 4 | 4 | 3.1589 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:03eec49aed` | 4 | 4 | -0.9565 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:5159f83a5b` | 3 | 3 | -0.1136 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:cb6ed22b69` | 3 | 3 | -1.0067 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:b31cc048c8` | 3 | 3 | -1.9 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:305d9e5c71` | 3 | 3 | -0.2375 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:62b3401904` | 3 | 3 | -0.26 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:f58154b780` | 2 | 2 | -1.12 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:b75bf201fa` | 2 | 2 | -0.745 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:397dbf1728` | 2 | 2 | -0.84 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_ai_c:a101f93752` | 2 | 2 | -0.845 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:f548b6989d` | 2 | 2 | -0.54 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 466, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 6018 | 141 | 1.3057 | 1.7631 | 0.5461 | `candidate_recovery_or_relax` |
| `score_band` | `score_63_65` | 1182 | 112 | 1.6946 | 2.4062 | 0.5893 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 9915 | 81 | -0.3387 | -0.9521 | 0.4074 | `source_quality_workorder` |
| `chosen_action` | `NO_BUY_AI` | 7390 | 79 | -0.3563 | -0.9876 | 0.3924 | `hold_sample` |
| `stale_bucket` | `fresh` | 7005 | 77 | -0.3737 | -1.007 | 0.3896 | `hold_sample` |
| `overbought_bucket` | `overbought_watch` | 3709 | 69 | 1.4057 | 1.6453 | 0.5797 | `candidate_recovery_or_relax` |
| `chosen_action` | `WAIT_REQUOTE` | 3942 | 65 | 3.3381 | 5.1293 | 0.7538 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 13288 | 63 | 3.4327 | 5.2779 | 0.746 | `source_quality_workorder` |
| `source_stage` | `wait6579_ev_cohort` | 63 | 63 | 3.4327 | 5.2779 | 0.746 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_1000_1200` | 3105 | 55 | -0.3434 | -1.2138 | 0.2909 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 5203 | 52 | -0.3901 | -1.1762 | 0.3269 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 47 | 47 | -0.0395 | -1.5077 | 0.0 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 2217 | 46 | 0.1371 | -0.6153 | 0.3478 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 44 | 44 | -0.5668 | 0.4766 | 0.9318 | `hold_sample` |
| `score_band` | `score_70p` | 601 | 41 | -0.5304 | -1.118 | 0.3415 | `hold_sample` |
| `liquidity_bucket` | `liquidity_not_available` | 6554 | 33 | -0.2821 | -1.1315 | 0.3333 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_not_available` | 5480 | 33 | -0.2821 | -1.1315 | 0.3333 | `source_quality_workorder` |
| `stale_bucket` | `stale_not_available` | 4006 | 32 | -0.3266 | -1.1169 | 0.3438 | `source_quality_workorder` |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 809 | 31 | -0.3234 | -1.2335 | 0.2903 | `source_quality_workorder` |
| `source_stage` | `scalp_sim_entry_ai_price_skip_order` | 612 | 31 | -0.3234 | -1.2335 | 0.2903 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_1000_1200` | 24 | 24 | 2.7518 | 3.8641 | 0.6667 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_ok` | 1281 | 20 | 2.8083 | 6.1359 | 0.8 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 15 | 15 | 2.187 | 3.0597 | 0.7333 | `candidate_recovery_or_relax` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 133, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 1047 | 193 | -0.7051 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 259 | 193 | -0.7051 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 259 | 193 | -0.7051 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 259 | 193 | -0.7051 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 259 | 193 | -0.7051 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 259 | 193 | -0.7051 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 259 | 193 | -0.7051 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 259 | 193 | -0.7051 | `keep_collecting` |
| `latency_state` | `simulated` | 259 | 193 | -0.7051 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 1047 | 193 | -0.7051 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 1137 | 191 | -0.7153 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 251 | 185 | -0.6816 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 169 | 123 | -0.5182 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 173 | 117 | -0.8237 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 167 | 114 | -0.3073 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 167 | 114 | -0.3073 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 152 | 106 | -0.2849 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 911 | 106 | -0.2849 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 152 | 106 | -0.2849 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 107 | 87 | -1.2171 | `source_quality_workorder` |
| `price_resolution_bucket` | `defensive_order_price` | 105 | 86 | -1.2044 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 100 | 79 | -1.2792 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 90 | 79 | -1.2792 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 92 | 79 | -1.2792 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 184 | 74 | -1.2222 | `keep_collecting` |
| `would_limit_fill` | `false` | 1019 | 72 | -0.3975 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 81 | 68 | -0.4371 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 72 | 46 | -0.4952 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 56 | 43 | -0.8381 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 43 | 36 | -1.7087 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 46 | 34 | -0.0464 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 31 | 30 | -0.9402 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 38 | 27 | -0.1741 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 34 | 26 | -0.2248 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 32 | 25 | -1.3473 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_10s_plus` | 25 | 11 | -1.1738 | `keep_collecting` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 8 | 8 | -1.2491 | `keep_collecting` |
| `overbought_guard_action` | `would_block` | 8 | 8 | -1.2491 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 8 | 7 | 0.4465 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 8 | 7 | -1.0812 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 41, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 248 | 191 | -0.845 | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 248 | 191 | -0.845 | `hold_sample` |
| `holding_action` | `WAIT` | 181 | 138 | -0.8695 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 108 | 99 | -1.3512 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 80 | 80 | -1.2174 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 56 | 55 | -0.4267 | `hold_no_edge` |
| `holding_action` | `holding_action_not_applicable_at_start` | 66 | 52 | -0.7925 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 34 | 34 | -0.3826 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 20 | 20 | -0.513 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 19 | 19 | -1.9145 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 22 | 14 | -0.6849 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 14 | 14 | 0.3748 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 10 | 10 | -0.9115 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 9 | 9 | -0.0997 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 8 | 8 | -0.0136 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 5 | 5 | 0.0856 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 5 | 5 | 1.2288 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 4 | 4 | -0.1182 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 3 | 3 | -0.179 | `hold_sample` |
| `holding_action` | `BUY` | 1 | 1 | -0.2008 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 1 | 1 | 0.2903 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | -0.2008 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 0.2903 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 18 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 4 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 7 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 5 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 57 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 18 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 43 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 14 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_020_180s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_180_600s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 6 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_020_180s` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_180_600s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 55, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `exit_source_stage` | `sim_post_sell_evaluation` | 184 | 184 | -0.7616 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 165 | 165 | -1.2396 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 105 | 105 | -0.8908 | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 105 | 105 | -0.8908 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 105 | 105 | -0.8908 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 87 | 87 | -0.1871 | `hold_sample` |
| `exit_outcome` | `NEUTRAL` | 72 | 72 | -0.6047 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 63 | 63 | -1.1127 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 61 | 61 | -0.5537 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 59 | 59 | -1.3459 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 56 | 56 | -0.4183 | `hold_no_edge` |
| `exit_outcome` | `MISSED_UPSIDE` | 53 | 53 | -0.3242 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 51 | 51 | -0.8011 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 42 | 42 | -0.5579 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 39 | 39 | -2.0038 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 27 | 27 | -0.8409 | `hold_sample` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 25 | 25 | -0.7729 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 24 | 24 | -0.1651 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 21 | 21 | -1.1331 | `hold_sample` |
| `exit_outcome` | `COMPLETED` | 18 | 18 | -0.8038 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 18 | 18 | -0.8038 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 17 | 17 | -1.5049 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 15 | 15 | -0.3881 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 14 | 14 | 0.3748 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 11 | 11 | -2.7946 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 11 | 11 | -1.984 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_lt_neg070` | 9 | 9 | -1.3708 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 9 | 9 | -1.3699 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 9 | 9 | 0.493 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 8 | 8 | -0.0136 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 8 | 8 | -0.2719 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 6 | 6 | -0.3965 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 6 | 6 | -0.5704 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 6 | 6 | 1.0609 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg070_neg010` | 4 | 4 | 0.0258 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 3 | 3 | 2.8197 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=NEUTRAL|profit=profit_neg070_neg010` | 3 | 3 | -0.5398 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 2 | 2 | -1.2784 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg070_neg010` | 2 | 2 | -2.1641 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 2 | 2 | 1.6569 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 426, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 15738 | 15736 | None | -0.9017 | 0.0786 | `hold_sample` |
| `arm` | `AVG_DOWN` | 14544 | 14418 | None | -1.0139 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 14432 | 14306 | None | -0.9971 | 0.0 | `hold_sample` |
| `price_guard_reason` | `price_guard_none` | 14416 | 14302 | None | -0.8421 | 0.0857 | `hold_sample` |
| `qty_reason` | `qty_none` | 14304 | 14302 | None | -0.8421 | 0.0857 | `hold_sample` |
| `time_bucket` | `time_unknown` | 11547 | 11450 | None | -0.783 | 0.1012 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 8168 | 8168 | None | -0.8995 | 0.0871 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 7709 | 7709 | None | -1.3245 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 7643 | 7643 | None | -0.808 | 0.1107 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 6731 | 6615 | None | -0.9506 | 0.0011 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 6369 | 6272 | None | -0.6786 | 0.1849 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 5456 | 5456 | None | -1.0152 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 4935 | 4935 | None | -0.4547 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 4021 | 4021 | None | -0.8483 | 0.1122 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 3506 | 3506 | None | -0.9432 | 0.0568 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 2108 | 2108 | None | -0.1664 | 0.5218 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 1999 | 1999 | None | -0.8467 | 0.0665 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_1` | 1786 | 1786 | None | -1.0545 | 0.0 | `hold_sample` |
| `ai_score_source` | `not_evaluated_no_ai_score_source` | 1577 | 1577 | None | -0.7536 | 0.026 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 1566 | 1566 | None | 0.1867 | 0.7254 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 26, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 36 | 18 | -0.8038 | -1.0717 | 0.0556 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 18 | 18 | -0.8038 | -1.0717 | 0.0556 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 36 | 18 | -0.8038 | -1.0717 | 0.0556 | `hold_sample` |
| `stage` | `exit` | 18 | 18 | -0.8038 | -1.0717 | 0.0556 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 36 | 18 | -0.8038 | -1.0717 | 0.0556 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 18 | 18 | -0.8038 | -1.0717 | 0.0556 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 34 | 17 | -0.8537 | -1.1382 | 0.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 28 | 14 | -0.9841 | -1.3122 | 0.0714 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 9 | 9 | -1.3708 | -1.8278 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 18 | 9 | -1.3708 | -1.8278 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 8 | 8 | -0.2719 | -0.3625 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 16 | 8 | -0.2719 | -0.3625 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 14 | 7 | -1.2761 | -1.7014 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 10 | 5 | -0.561 | -0.748 | 0.2 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 8 | 4 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 8 | 4 | -0.39 | -0.52 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 4 | 2 | -0.585 | -0.78 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 1 | 1 | 0.045 | 0.06 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 2 | 1 | 0.045 | 0.06 | 1.0 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 2 | 1 | 0.045 | 0.06 | 1.0 | `hold_sample` |

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
