# Lifecycle Decision Matrix - 2026-08-31

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-08-31_mtd`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `39554`
- source_rows_total: `50956`
- retained_rows: `39554`
- dropped_rows_by_source: `{}`
- joined_rows: `17505`
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
- lifecycle_flow_bucket_count: `252`
- lifecycle_flow_complete_count: `179`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0065`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 14129 | 178 | 1.0012 | 0.1319 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 1259 | 204 | -0.7221 | 0.343 | `pass` | `NO_CHANGE` | False |
| `holding` | 280 | 202 | -0.8578 | 0.8151 | `pass` | `EXIT` | False |
| `scale_in` | 16727 | 16593 | -0.8165 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 7159 | 328 | -0.8177 | 0.3534 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 252, 'complete_flow_count': 179, 'incomplete_flow_count': 27528, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 15268 | 15138 | -0.9319 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 1458 | 1454 | 0.3854 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 58 | 58 | 3.4417 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:0cb91a7ba6` | 9 | 9 | -0.9422 | `candidate_tighten_or_exclude` | `pass` |
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
- summary: `{'bucket_count': 470, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 6228 | 143 | 1.2824 | 1.7013 | 0.5384 | `candidate_recovery_or_relax` |
| `score_band` | `score_63_65` | 1196 | 113 | 1.6807 | 2.3895 | 0.5929 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 10528 | 83 | -0.3392 | -0.9932 | 0.3976 | `source_quality_workorder` |
| `chosen_action` | `NO_BUY_AI` | 7643 | 81 | -0.3564 | -1.0289 | 0.3827 | `hold_sample` |
| `stale_bucket` | `fresh` | 7340 | 79 | -0.3733 | -1.0489 | 0.3797 | `hold_sample` |
| `overbought_bucket` | `overbought_watch` | 3852 | 70 | 1.3795 | 1.5678 | 0.5714 | `candidate_recovery_or_relax` |
| `chosen_action` | `WAIT_REQUOTE` | 4269 | 65 | 3.3381 | 5.1293 | 0.7538 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 14014 | 63 | 3.4327 | 5.2779 | 0.746 | `source_quality_workorder` |
| `source_stage` | `wait6579_ev_cohort` | 63 | 63 | 3.4327 | 5.2779 | 0.746 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_1000_1200` | 3319 | 57 | -0.3439 | -1.2646 | 0.2807 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 5433 | 54 | -0.389 | -1.2311 | 0.3148 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 48 | 48 | -0.0448 | -1.5083 | 0.0 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 2266 | 47 | 0.1279 | -0.6349 | 0.3404 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 45 | 45 | -0.5515 | 0.4776 | 0.9333 | `hold_sample` |
| `score_band` | `score_70p` | 642 | 42 | -0.5279 | -1.1814 | 0.3333 | `hold_sample` |
| `liquidity_bucket` | `liquidity_not_available` | 7038 | 34 | -0.2702 | -1.0829 | 0.3529 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_not_available` | 5940 | 34 | -0.2702 | -1.0829 | 0.3529 | `source_quality_workorder` |
| `stale_bucket` | `stale_not_available` | 4325 | 33 | -0.313 | -1.0673 | 0.3636 | `source_quality_workorder` |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 864 | 32 | -0.3095 | -1.1787 | 0.3125 | `source_quality_workorder` |
| `source_stage` | `scalp_sim_entry_ai_price_skip_order` | 622 | 32 | -0.3095 | -1.1787 | 0.3125 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_1000_1200` | 24 | 24 | 2.7518 | 3.8641 | 0.6667 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_ok` | 1340 | 20 | 2.8083 | 6.1359 | 0.8 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 15 | 15 | 2.187 | 3.0597 | 0.7333 | `candidate_recovery_or_relax` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 136, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 1131 | 204 | -0.7221 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 273 | 204 | -0.7221 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 273 | 204 | -0.7221 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 273 | 204 | -0.7221 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 273 | 204 | -0.7221 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 273 | 204 | -0.7221 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 273 | 204 | -0.7221 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 273 | 204 | -0.7221 | `keep_collecting` |
| `latency_state` | `simulated` | 273 | 204 | -0.7221 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 1131 | 204 | -0.7221 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 1219 | 202 | -0.7319 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 264 | 195 | -0.7034 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 179 | 130 | -0.5585 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 186 | 127 | -0.8459 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 172 | 117 | -0.3045 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 172 | 117 | -0.3045 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 157 | 109 | -0.2825 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 982 | 109 | -0.2825 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 157 | 109 | -0.2825 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 116 | 95 | -1.2264 | `source_quality_workorder` |
| `price_resolution_bucket` | `defensive_order_price` | 114 | 94 | -1.2149 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 109 | 87 | -1.2837 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 98 | 87 | -1.2837 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 101 | 87 | -1.2837 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 193 | 80 | -1.2382 | `keep_collecting` |
| `would_limit_fill` | `false` | 1097 | 75 | -0.3896 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 81 | 68 | -0.4371 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 77 | 49 | -0.4771 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 56 | 43 | -0.8381 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 49 | 42 | -1.6696 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 46 | 34 | -0.0464 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 31 | 30 | -0.9402 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 36 | 29 | -1.2425 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 38 | 27 | -0.1741 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 34 | 26 | -0.2248 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_10s_plus` | 31 | 13 | -1.1476 | `keep_collecting` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 9 | 9 | -1.1279 | `keep_collecting` |
| `overbought_guard_action` | `would_block` | 9 | 9 | -1.1279 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 9 | 8 | -1.1772 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 8 | 7 | 0.4465 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 41, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 261 | 202 | -0.8578 | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 261 | 202 | -0.8578 | `hold_sample` |
| `holding_action` | `WAIT` | 194 | 149 | -0.8849 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 113 | 104 | -1.3853 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 85 | 85 | -1.2671 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 59 | 58 | -0.4085 | `hold_no_edge` |
| `holding_action` | `holding_action_not_applicable_at_start` | 66 | 52 | -0.7925 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 37 | 37 | -0.3576 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 20 | 20 | -0.513 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 19 | 19 | -1.9145 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 16 | 16 | 0.1868 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 24 | 15 | -0.5778 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 11 | 11 | -0.7449 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 11 | 11 | -0.2868 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 8 | 8 | -0.0136 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 5 | 5 | 0.0856 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 5 | 5 | 1.2288 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 4 | 4 | -0.1182 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 3 | 3 | -0.179 | `hold_sample` |
| `holding_action` | `BUY` | 1 | 1 | -0.2008 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 1 | 1 | 0.2903 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | -0.2008 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 0.2903 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 19 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 4 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 8 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 5 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 59 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 19 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 45 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 14 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_020_180s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_180_600s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 6 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_020_180s` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_180_600s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 2 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 56, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `exit_source_stage` | `sim_post_sell_evaluation` | 195 | 195 | -0.7795 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 177 | 177 | -1.2541 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 114 | 114 | -0.8913 | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 114 | 114 | -0.8913 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 114 | 114 | -0.8913 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 92 | 92 | -0.2039 | `hold_sample` |
| `exit_outcome` | `NEUTRAL` | 77 | 77 | -0.5995 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 70 | 70 | -1.1034 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 65 | 65 | -0.5219 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 63 | 63 | -1.411 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 59 | 59 | -0.4008 | `hold_no_edge` |
| `exit_outcome` | `MISSED_UPSIDE` | 55 | 55 | -0.3081 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 52 | 52 | -0.8033 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 44 | 44 | -0.5539 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 43 | 43 | -2.0357 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 28 | 28 | -0.8437 | `hold_sample` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 27 | 27 | -0.6863 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 26 | 26 | -0.1349 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 21 | 21 | -1.1331 | `hold_sample` |
| `exit_outcome` | `COMPLETED` | 19 | 19 | -0.7682 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 19 | 19 | -0.7682 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 17 | 17 | -1.5049 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 16 | 16 | 0.1868 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 15 | 15 | -0.3881 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 14 | 14 | -2.7646 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 12 | 12 | -1.9373 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 10 | 10 | 0.3758 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_lt_neg070` | 9 | 9 | -1.3708 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 9 | 9 | -0.2558 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 9 | 9 | -1.3699 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 8 | 8 | -0.0136 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 7 | 7 | -0.5572 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 6 | 6 | -0.5704 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 6 | 6 | 1.0609 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg070_neg010` | 4 | 4 | 0.0258 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 3 | 3 | 2.8197 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=NEUTRAL|profit=profit_neg070_neg010` | 3 | 3 | -0.5398 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 3 | 3 | 0.1747 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 2 | 2 | -1.2784 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg070_neg010` | 2 | 2 | -2.1641 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 438, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 16542 | 16539 | None | -0.9016 | 0.0797 | `hold_sample` |
| `arm` | `AVG_DOWN` | 15269 | 15139 | None | -1.0164 | 0.0 | `hold_sample` |
| `price_guard_reason` | `price_guard_none` | 15225 | 15106 | None | -0.8451 | 0.0865 | `hold_sample` |
| `qty_reason` | `qty_none` | 15108 | 15106 | None | -0.8451 | 0.0865 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 15143 | 15013 | None | -0.9984 | 0.0 | `hold_sample` |
| `time_bucket` | `time_unknown` | 12356 | 12254 | None | -0.7906 | 0.1013 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 8424 | 8424 | None | -0.8969 | 0.0876 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 8191 | 8191 | None | -1.3284 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 7824 | 7824 | None | -0.8192 | 0.1081 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 7099 | 6978 | None | -0.9564 | 0.001 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 6816 | 6714 | None | -0.6841 | 0.1849 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 5691 | 5691 | None | -1.0118 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 5169 | 5169 | None | -0.453 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 4211 | 4211 | None | -0.8582 | 0.1173 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 3798 | 3798 | None | -0.9253 | 0.069 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 2297 | 2297 | None | -0.2136 | 0.5072 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 2209 | 2209 | None | -0.8498 | 0.0647 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_1` | 1963 | 1963 | None | -1.0687 | 0.0 | `hold_sample` |
| `ai_score_source` | `not_evaluated_no_ai_score_source` | 1728 | 1728 | None | -0.7629 | 0.0284 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 1643 | 1643 | None | 0.1945 | 0.7346 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 38 | 19 | -0.7682 | -1.0242 | 0.0526 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 19 | 19 | -0.7682 | -1.0242 | 0.0526 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 38 | 19 | -0.7682 | -1.0242 | 0.0526 | `hold_sample` |
| `stage` | `exit` | 19 | 19 | -0.7682 | -1.0242 | 0.0526 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 38 | 19 | -0.7682 | -1.0242 | 0.0526 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 19 | 19 | -0.7682 | -1.0242 | 0.0526 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 36 | 18 | -0.8133 | -1.0845 | 0.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 30 | 15 | -0.927 | -1.236 | 0.0667 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 9 | 9 | -1.3708 | -1.8278 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 9 | 9 | -0.2558 | -0.3411 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 18 | 9 | -1.3708 | -1.8278 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 18 | 9 | -0.2558 | -0.3411 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 16 | 8 | -1.1325 | -1.51 | 0.0 | `hold_sample` |
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
