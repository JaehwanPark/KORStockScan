# Lifecycle Decision Matrix - 2026-08-20

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-08-20_mtd`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `23014`
- source_rows_total: `30013`
- retained_rows: `23014`
- dropped_rows_by_source: `{}`
- joined_rows: `9368`
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
- lifecycle_flow_bucket_count: `172`
- lifecycle_flow_complete_count: `91`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0059`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 9486 | 131 | 1.5128 | 0.1756 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 726 | 107 | -0.6019 | 0.3419 | `pass` | `NO_CHANGE` | False |
| `holding` | 149 | 105 | -0.851 | 0.749 | `pass` | `EXIT` | False |
| `scale_in` | 8945 | 8869 | -0.8074 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 3708 | 156 | -0.7801 | 0.2389 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 172, 'complete_flow_count': 91, 'incomplete_flow_count': 15353, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 8183 | 8109 | -0.9182 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 762 | 760 | 0.3748 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 58 | 58 | 3.4417 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:4e1fc29475` | 4 | 4 | -0.842 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:d0233209ef` | 4 | 4 | -0.6925 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 4 | 4 | 3.1589 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:03eec49aed` | 4 | 4 | -0.9565 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:5159f83a5b` | 3 | 3 | -0.1136 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:0cb91a7ba6` | 3 | 3 | -0.9233 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:cb6ed22b69` | 3 | 3 | -1.0067 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:f658be39ac` | 3 | 3 | -1.7675 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:305d9e5c71` | 3 | 3 | -0.2375 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:62b3401904` | 3 | 3 | -0.26 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:b75bf201fa` | 2 | 2 | -0.745 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:397dbf1728` | 2 | 2 | -0.84 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:f548b6989d` | 2 | 2 | -0.54 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:5c4d0773e1` | 2 | 2 | -1.0275 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:77c2d7d131` | 2 | 2 | -1.195 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:5603187fa1` | 2 | 2 | 4.0844 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:bf44bd3042` | 1 | 1 | -0.53 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 429, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 4533 | 99 | 2.0255 | 2.9881 | 0.6262 | `candidate_recovery_or_relax` |
| `score_band` | `score_63_65` | 1098 | 94 | 2.0501 | 3.0515 | 0.617 | `candidate_recovery_or_relax` |
| `chosen_action` | `WAIT_REQUOTE` | 2424 | 64 | 3.3711 | 5.2043 | 0.75 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 9418 | 63 | 3.4327 | 5.2779 | 0.746 | `source_quality_workorder` |
| `source_stage` | `wait6579_ev_cohort` | 63 | 63 | 3.4327 | 5.2779 | 0.746 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_watch` | 2827 | 53 | 1.9605 | 2.6212 | 0.6415 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 6679 | 38 | -0.3222 | -0.7955 | 0.4474 | `source_quality_workorder` |
| `chosen_action` | `NO_BUY_AI` | 5647 | 37 | -0.3172 | -0.8324 | 0.4324 | `hold_sample` |
| `stale_bucket` | `fresh` | 4962 | 36 | -0.3623 | -0.8864 | 0.4166 | `hold_sample` |
| `liquidity_bucket` | `liquidity_not_available` | 4300 | 31 | -0.205 | -1.2077 | 0.3226 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_not_available` | 3419 | 31 | -0.205 | -1.2077 | 0.3226 | `source_quality_workorder` |
| `time_bucket` | `time_1000_1200` | 2038 | 31 | -0.3436 | -1.1277 | 0.3226 | `hold_sample` |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 625 | 30 | -0.1948 | -1.267 | 0.3 | `source_quality_workorder` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 30 | 30 | 0.0949 | -1.4857 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_entry_ai_price_skip_order` | 555 | 30 | -0.1948 | -1.267 | 0.3 | `hold_sample` |
| `stale_bucket` | `stale_not_available` | 2563 | 30 | -0.2499 | -1.1946 | 0.3333 | `source_quality_workorder` |
| `strength_bucket` | `risk_context_not_available` | 416 | 29 | -0.2409 | -1.2555 | 0.3104 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 27 | 27 | -0.6277 | 0.5289 | 0.963 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 1749 | 26 | 0.2572 | -0.3013 | 0.4231 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 3698 | 26 | -0.3628 | -0.8735 | 0.4231 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_1000_1200` | 24 | 24 | 2.7518 | 3.8641 | 0.6667 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_ok` | 930 | 15 | 4.1917 | 8.0606 | 0.8 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 15 | 15 | 2.187 | 3.0597 | 0.7333 | `candidate_recovery_or_relax` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 126, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 656 | 107 | -0.6019 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 146 | 107 | -0.6019 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 146 | 107 | -0.6019 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 146 | 107 | -0.6019 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 146 | 107 | -0.6019 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 146 | 107 | -0.6019 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 146 | 107 | -0.6019 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 146 | 107 | -0.6019 | `keep_collecting` |
| `latency_state` | `simulated` | 146 | 107 | -0.6019 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 656 | 107 | -0.6019 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 709 | 105 | -0.6185 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 144 | 105 | -0.5956 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 104 | 78 | -0.5525 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 96 | 65 | -0.1907 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 96 | 65 | -0.1907 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 90 | 62 | -0.226 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 584 | 62 | -0.226 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 90 | 62 | -0.226 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 92 | 58 | -0.9855 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 55 | 47 | -0.1146 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 56 | 45 | -1.1197 | `source_quality_workorder` |
| `price_resolution_bucket` | `defensive_order_price` | 54 | 44 | -1.0927 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 55 | 42 | -1.2383 | `keep_collecting` |
| `would_limit_fill` | `false` | 643 | 42 | -0.3012 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 49 | 42 | -1.2383 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 50 | 42 | -1.2383 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 99 | 39 | -1.0485 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 38 | 22 | -0.489 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 29 | 20 | -0.3157 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 25 | 20 | -0.0947 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 27 | 20 | -0.0681 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 24 | 19 | -1.7562 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 16 | 16 | -0.3876 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 20 | 13 | -0.3451 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 12 | 8 | -1.8453 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 7 | 7 | 0.4465 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_10s_plus` | 9 | 4 | -1.7409 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 3 | 3 | -2.9104 | `source_quality_workorder` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 2 | 2 | -0.9304 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 11 | 2 | -1.2667 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 32, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 140 | 105 | -0.851 | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 140 | 105 | -0.851 | `hold_sample` |
| `holding_action` | `WAIT` | 108 | 82 | -0.8841 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 60 | 57 | -1.2868 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 49 | 49 | -1.2296 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 31 | 31 | -0.5234 | `hold_no_edge` |
| `holding_action` | `holding_action_not_applicable_at_start` | 31 | 22 | -0.7574 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 20 | 20 | -0.4821 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 10 | 10 | -0.6381 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 8 | 8 | 0.5173 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 8 | 8 | -1.637 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 13 | 7 | -0.86 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 7 | 7 | -0.86 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 5 | 5 | 0.3306 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 3 | 3 | 0.8284 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 2 | 2 | 1.0468 | `hold_sample` |
| `holding_action` | `BUY` | 1 | 1 | -0.2008 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | -0.2008 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 1 | 1 | 1.7646 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 1 | 1 | 0.3289 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 9 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 3 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 4 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 35 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 9 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 26 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 9 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_020_180s` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 49, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `exit_source_stage` | `sim_post_sell_evaluation` | 101 | 101 | -0.7199 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 85 | 85 | -1.2158 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 46 | 46 | -0.9172 | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 46 | 46 | -0.9172 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 46 | 46 | -0.9172 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 46 | 46 | -0.1372 | `hold_sample` |
| `exit_outcome` | `NEUTRAL` | 45 | 45 | -0.6003 | `hold_no_edge` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 32 | 32 | -0.6923 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 31 | 31 | -0.5234 | `hold_no_edge` |
| `exit_outcome` | `GOOD_EXIT` | 29 | 29 | -1.2898 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 28 | 28 | -0.5902 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 28 | 28 | -1.1343 | `hold_sample` |
| `exit_outcome` | `MISSED_UPSIDE` | 27 | 27 | -0.307 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 22 | 22 | -2.0056 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 19 | 19 | -0.8347 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 18 | 18 | -0.5794 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 15 | 15 | -1.0321 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 13 | 13 | -0.1129 | `hold_no_edge` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 10 | 10 | -0.691 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 10 | 10 | -0.2895 | `hold_sample` |
| `exit_outcome` | `COMPLETED` | 9 | 9 | -0.755 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 9 | 9 | -0.755 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 9 | 9 | -1.9588 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 8 | 8 | 0.5173 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 7 | 7 | -1.4848 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 6 | 6 | -0.2487 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 6 | 6 | -2.6836 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 5 | 5 | 0.6804 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_lt_neg070` | 3 | 3 | -1.7675 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 3 | 3 | -1.1332 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 3 | 3 | 0.2455 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 3 | 3 | 0.2415 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 2 | 2 | 1.0468 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 2 | 2 | 4.0844 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300_plus` | 2 | 2 | 4.0844 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=NEUTRAL|profit=profit_neg070_neg010` | 1 | 1 | -0.115 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg070_neg010` | 1 | 1 | -3.4858 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 1 | 1 | 0.3289 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg070_neg010` | 1 | 1 | -0.8911 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 1 | 1 | 1.7646 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 354, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 8837 | 8835 | None | -0.8924 | 0.076 | `hold_sample` |
| `arm` | `AVG_DOWN` | 8183 | 8109 | None | -1.0025 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 8111 | 8037 | None | -0.983 | 0.0 | `hold_sample` |
| `price_guard_reason` | `price_guard_none` | 7445 | 7382 | None | -0.7802 | 0.087 | `hold_sample` |
| `qty_reason` | `qty_none` | 7382 | 7382 | None | -0.7802 | 0.087 | `hold_sample` |
| `time_bucket` | `time_unknown` | 7445 | 7382 | None | -0.7802 | 0.087 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 4391 | 4391 | None | -0.8723 | 0.0934 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 4057 | 4057 | None | -1.1802 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 4053 | 4053 | None | -0.7398 | 0.1113 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 4065 | 4002 | None | -0.6897 | 0.1604 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 3449 | 3386 | None | -0.8857 | 0.0015 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 2842 | 2842 | None | -0.9304 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 2490 | 2490 | None | -0.4781 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 2345 | 2345 | None | -0.9026 | 0.0921 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 1658 | 1658 | None | -0.826 | 0.0645 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 1097 | 1097 | None | -0.1466 | 0.5315 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_1` | 1097 | 1097 | None | -1.0045 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 1035 | 1035 | None | -0.8812 | 0.0541 | `hold_sample` |
| `ai_score_source` | `not_evaluated_no_ai_score_source` | 902 | 902 | None | -0.7639 | 0.0277 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_2` | 861 | 861 | None | -0.8268 | 0.0 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 21, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 18 | 9 | -0.755 | -1.0067 | 0.0 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 9 | 9 | -0.755 | -1.0067 | 0.0 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 18 | 9 | -0.755 | -1.0067 | 0.0 | `hold_sample` |
| `stage` | `exit` | 9 | 9 | -0.755 | -1.0067 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 18 | 9 | -0.755 | -1.0067 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 18 | 9 | -0.755 | -1.0067 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 9 | 9 | -0.755 | -1.0067 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 6 | 6 | -0.2487 | -0.3317 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 12 | 6 | -0.2487 | -0.3317 | 0.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 10 | 5 | -1.221 | -1.628 | 0.0 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 8 | 4 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 8 | 4 | -1.3687 | -1.825 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 3 | 3 | -1.7675 | -2.3567 | 0.0 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 6 | 3 | -0.2375 | -0.3167 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 6 | 3 | -1.7675 | -2.3567 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 4 | 2 | -0.3037 | -0.405 | 0.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 9 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_lt_neg070` | 3 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 6 | 0 | None | None | None | `hold_sample` |
| `stage` | `holding` | 9 | 0 | None | None | None | `hold_sample` |

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
