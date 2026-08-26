# Lifecycle Decision Matrix - 2026-08-26

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-08-26_mtd`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `34349`
- source_rows_total: `44759`
- retained_rows: `34349`
- dropped_rows_by_source: `{}`
- joined_rows: `14788`
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
- lifecycle_flow_bucket_count: `227`
- lifecycle_flow_complete_count: `152`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0063`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 12146 | 164 | 1.129 | 0.1428 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 1054 | 174 | -0.6368 | 0.3766 | `pass` | `NO_CHANGE` | False |
| `holding` | 238 | 172 | -0.8329 | 0.8302 | `pass` | `EXIT` | False |
| `scale_in` | 14095 | 13994 | -0.8497 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 6816 | 284 | -0.7969 | 0.3317 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 227, 'complete_flow_count': 152, 'incomplete_flow_count': 24139, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 13057 | 12958 | -0.946 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 1037 | 1035 | 0.3557 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 58 | 58 | 3.4417 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:0cb91a7ba6` | 6 | 6 | -0.9517 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:a6af469504` | 5 | 5 | -0.974 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:f658be39ac` | 5 | 5 | -1.5 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:4e1fc29475` | 4 | 4 | -0.842 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:d0233209ef` | 4 | 4 | -0.6925 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 4 | 4 | 3.1589 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:03eec49aed` | 4 | 4 | -0.9565 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:5159f83a5b` | 3 | 3 | -0.1136 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:cb6ed22b69` | 3 | 3 | -1.0067 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:305d9e5c71` | 3 | 3 | -0.2375 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:62b3401904` | 3 | 3 | -0.26 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:b75bf201fa` | 2 | 2 | -0.745 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:397dbf1728` | 2 | 2 | -0.84 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_ai_c:a101f93752` | 2 | 2 | -0.845 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:f548b6989d` | 2 | 2 | -0.54 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:5c4d0773e1` | 2 | 2 | -1.0275 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:b0bc92a886` | 2 | 2 | -1.365 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 453, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 5497 | 130 | 1.465 | 1.9641 | 0.5538 | `candidate_recovery_or_relax` |
| `score_band` | `score_63_65` | 1144 | 104 | 1.8407 | 2.6476 | 0.6058 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 8868 | 70 | -0.3012 | -1.0056 | 0.4 | `source_quality_workorder` |
| `chosen_action` | `NO_BUY_AI` | 6781 | 68 | -0.3206 | -1.0484 | 0.3823 | `hold_sample` |
| `overbought_bucket` | `overbought_watch` | 3431 | 67 | 1.4439 | 1.7298 | 0.5821 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh` | 6315 | 66 | -0.3398 | -1.0729 | 0.3788 | `hold_sample` |
| `chosen_action` | `WAIT_REQUOTE` | 3505 | 65 | 3.3381 | 5.1293 | 0.7538 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 12045 | 63 | 3.4327 | 5.2779 | 0.746 | `source_quality_workorder` |
| `source_stage` | `wait6579_ev_cohort` | 63 | 63 | 3.4327 | 5.2779 | 0.746 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_1000_1200` | 2755 | 47 | -0.404 | -1.2521 | 0.2766 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 4674 | 47 | -0.4548 | -1.1817 | 0.3192 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 43 | 43 | -0.0135 | -1.5098 | 0.0 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 2007 | 40 | 0.1613 | -0.5691 | 0.35 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 39 | 39 | -0.5323 | 0.4541 | 0.9231 | `hold_sample` |
| `score_band` | `score_70p` | 558 | 39 | -0.4113 | -1.1505 | 0.3333 | `hold_sample` |
| `liquidity_bucket` | `liquidity_not_available` | 5851 | 33 | -0.2821 | -1.1315 | 0.3333 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_not_available` | 4847 | 33 | -0.2821 | -1.1315 | 0.3333 | `source_quality_workorder` |
| `stale_bucket` | `stale_not_available` | 3581 | 32 | -0.3266 | -1.1169 | 0.3438 | `source_quality_workorder` |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 726 | 31 | -0.3234 | -1.2335 | 0.2903 | `source_quality_workorder` |
| `source_stage` | `scalp_sim_entry_ai_price_skip_order` | 594 | 31 | -0.3234 | -1.2335 | 0.2903 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_1000_1200` | 24 | 24 | 2.7518 | 3.8641 | 0.6667 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_ok` | 1165 | 17 | 3.6832 | 7.1493 | 0.8235 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 15 | 15 | 2.187 | 3.0597 | 0.7333 | `candidate_recovery_or_relax` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 131, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 940 | 174 | -0.6368 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 230 | 174 | -0.6368 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 230 | 174 | -0.6368 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 230 | 174 | -0.6368 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 230 | 174 | -0.6368 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 230 | 174 | -0.6368 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 230 | 174 | -0.6368 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 230 | 174 | -0.6368 | `keep_collecting` |
| `latency_state` | `simulated` | 230 | 174 | -0.6368 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 940 | 174 | -0.6368 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 1026 | 172 | -0.6473 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 222 | 166 | -0.6073 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 144 | 107 | -0.4552 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 146 | 103 | -0.2785 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 146 | 103 | -0.2785 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 145 | 98 | -0.7253 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 133 | 95 | -0.2511 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 817 | 95 | -0.2511 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 133 | 95 | -0.2511 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 97 | 79 | -1.1005 | `source_quality_workorder` |
| `price_resolution_bucket` | `defensive_order_price` | 95 | 78 | -1.085 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 92 | 71 | -1.1565 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 82 | 71 | -1.1565 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 84 | 71 | -1.1565 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 80 | 68 | -0.4371 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 168 | 68 | -1.1036 | `keep_collecting` |
| `would_limit_fill` | `false` | 919 | 67 | -0.3412 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 55 | 42 | -0.7756 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 61 | 41 | -0.415 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 31 | 30 | -0.9402 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 37 | 30 | -1.537 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 38 | 28 | -0.0356 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 34 | 26 | -0.2248 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 29 | 23 | -1.1686 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 31 | 21 | -0.1962 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_10s_plus` | 20 | 9 | -1.0407 | `keep_collecting` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 8 | 8 | -1.2491 | `keep_collecting` |
| `overbought_guard_action` | `would_block` | 8 | 8 | -1.2491 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 7 | 7 | 0.4465 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_pre_submit_overbought_guard_would_block` | 6 | 6 | -0.8952 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 40, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 221 | 172 | -0.8329 | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 221 | 172 | -0.8329 | `hold_sample` |
| `holding_action` | `WAIT` | 155 | 120 | -0.8629 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 98 | 90 | -1.3489 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 71 | 71 | -1.1975 | `hold_sample` |
| `holding_action` | `holding_action_not_applicable_at_start` | 65 | 51 | -0.7749 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 49 | 48 | -0.3486 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 28 | 28 | -0.2844 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 19 | 19 | -1.9145 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 19 | 19 | -0.4509 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 22 | 14 | -0.6849 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 14 | 14 | 0.3748 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 10 | 10 | -0.9115 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 9 | 9 | -0.0997 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 5 | 5 | -0.2161 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 5 | 5 | 1.2288 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 4 | 4 | -0.1182 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 3 | 3 | -0.179 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 2 | 2 | -0.2718 | `hold_sample` |
| `holding_action` | `BUY` | 1 | 1 | -0.2008 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 1 | 1 | 0.2903 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | -0.2008 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 0.2903 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 17 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 4 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 7 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 5 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 49 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 17 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 35 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 14 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_020_180s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 6 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_020_180s` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_180_600s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 3 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 55, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `exit_source_stage` | `sim_post_sell_evaluation` | 165 | 165 | -0.7394 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 152 | 152 | -1.2399 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 102 | 102 | -0.8883 | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 102 | 102 | -0.8883 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 102 | 102 | -0.8883 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 77 | 77 | -0.1365 | `hold_sample` |
| `exit_outcome` | `NEUTRAL` | 66 | 66 | -0.5501 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 61 | 61 | -0.5537 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 60 | 60 | -1.1197 | `hold_sample` |
| `exit_outcome` | `GOOD_EXIT` | 52 | 52 | -1.3623 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 49 | 49 | -0.3406 | `hold_no_edge` |
| `exit_outcome` | `MISSED_UPSIDE` | 47 | 47 | -0.3161 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 46 | 46 | -0.7958 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 42 | 42 | -0.5579 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 36 | 36 | -1.9752 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 27 | 27 | -0.8409 | `hold_sample` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 23 | 23 | -0.7596 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 20 | 20 | -0.0461 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 19 | 19 | -1.03 | `hold_sample` |
| `exit_outcome` | `COMPLETED` | 17 | 17 | -0.8056 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 17 | 17 | -0.8056 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 16 | 16 | -1.421 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 14 | 14 | 0.3748 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 12 | 12 | -0.3551 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 11 | 11 | -2.7946 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 9 | 9 | -1.9588 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_lt_neg070` | 8 | 8 | -1.4456 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 8 | 8 | -0.2719 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 8 | 8 | 0.4885 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 7 | 7 | -1.3771 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 6 | 6 | -0.3965 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 6 | 6 | 1.0609 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 5 | 5 | -0.2161 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 4 | 4 | -0.7113 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg070_neg010` | 4 | 4 | 0.0258 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 3 | 3 | 2.8197 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=NEUTRAL|profit=profit_neg070_neg010` | 3 | 3 | -0.5398 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg070_neg010` | 2 | 2 | -2.1641 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg070_neg010` | 2 | 2 | -1.1643 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 2 | 2 | 0.6301 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 405, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 13953 | 13951 | None | -0.9355 | 0.0653 | `hold_sample` |
| `arm` | `AVG_DOWN` | 13058 | 12959 | None | -1.0314 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 12955 | 12856 | None | -1.0143 | 0.0 | `hold_sample` |
| `price_guard_reason` | `price_guard_none` | 12595 | 12507 | None | -0.8731 | 0.0712 | `hold_sample` |
| `qty_reason` | `qty_none` | 12507 | 12507 | None | -0.8731 | 0.0712 | `hold_sample` |
| `time_bucket` | `time_unknown` | 9724 | 9655 | None | -0.8121 | 0.0854 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 7162 | 7162 | None | -0.9346 | 0.0696 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 6972 | 6972 | None | -1.318 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 6957 | 6957 | None | -0.8441 | 0.091 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 5947 | 5859 | None | -0.9641 | 0.0009 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 5298 | 5229 | None | -0.7219 | 0.1578 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 4974 | 4974 | None | -1.0187 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 4342 | 4342 | None | -0.4654 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 3624 | 3624 | None | -0.8935 | 0.0977 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 2881 | 2881 | None | -0.9712 | 0.0479 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 1691 | 1691 | None | -0.8869 | 0.0503 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 1590 | 1590 | None | -0.1717 | 0.5075 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_1` | 1517 | 1517 | None | -1.0548 | 0.0 | `hold_sample` |
| `ai_score_source` | `not_evaluated_no_ai_score_source` | 1331 | 1331 | None | -0.7757 | 0.024 | `hold_sample` |
| `ai_score_source` | `holding_ai_not_called` | 1198 | 1198 | None | -1.0812 | 0.0226 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 34 | 17 | -0.8056 | -1.0741 | 0.0588 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 17 | 17 | -0.8056 | -1.0741 | 0.0588 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 34 | 17 | -0.8056 | -1.0741 | 0.0588 | `hold_sample` |
| `stage` | `exit` | 17 | 17 | -0.8056 | -1.0741 | 0.0588 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 34 | 17 | -0.8056 | -1.0741 | 0.0588 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 17 | 17 | -0.8056 | -1.0741 | 0.0588 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 32 | 16 | -0.8588 | -1.145 | 0.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 26 | 13 | -1.0004 | -1.3339 | 0.0769 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 8 | 8 | -1.4456 | -1.9275 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 8 | 8 | -0.2719 | -0.3625 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 16 | 8 | -1.4456 | -1.9275 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 16 | 8 | -0.2719 | -0.3625 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 14 | 7 | -1.2761 | -1.7014 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 10 | 5 | -0.561 | -0.748 | 0.2 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 8 | 4 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 8 | 4 | -0.39 | -0.52 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 1 | 1 | 0.045 | 0.06 | 1.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 2 | 1 | -0.3975 | -0.53 | 0.0 | `hold_sample` |
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
