# Lifecycle Decision Matrix - 2026-08-18

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-08-18_mtd`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `19475`
- source_rows_total: `25863`
- retained_rows: `19475`
- dropped_rows_by_source: `{}`
- joined_rows: `7513`
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
- lifecycle_flow_bucket_count: `151`
- lifecycle_flow_complete_count: `71`
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
| `entry` | 8147 | 120 | 1.6947 | 0.1905 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 558 | 82 | -0.5881 | 0.3888 | `pass` | `NO_CHANGE` | False |
| `holding` | 117 | 81 | -0.8198 | 0.6995 | `pass` | `EXIT` | False |
| `scale_in` | 7170 | 7108 | -0.8714 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 3483 | 122 | -0.7471 | 0.2138 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 151, 'complete_flow_count': 71, 'incomplete_flow_count': 13022, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 6705 | 6645 | -0.9608 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 465 | 463 | 0.4119 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 58 | 58 | 3.4417 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:4e1fc29475` | 4 | 4 | -0.842 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:d0233209ef` | 4 | 4 | -0.6925 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 4 | 4 | 3.1589 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:5159f83a5b` | 3 | 3 | -0.1136 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:0cb91a7ba6` | 3 | 3 | -0.9233 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:cb6ed22b69` | 3 | 3 | -1.0067 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:305d9e5c71` | 3 | 3 | -0.2375 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:b75bf201fa` | 2 | 2 | -0.745 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:397dbf1728` | 2 | 2 | -0.84 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:f548b6989d` | 2 | 2 | -0.54 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:03eec49aed` | 2 | 2 | -1.1106 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:f658be39ac` | 2 | 2 | -1.86 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:62b3401904` | 2 | 2 | -0.1725 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:5603187fa1` | 2 | 2 | 4.0844 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:bf44bd3042` | 1 | 1 | -0.53 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:92f69621e6` | 1 | 1 | -1.21 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:5ad377bcf7` | 1 | 1 | -0.4211 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 411, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `score_band` | `score_63_65` | 1080 | 94 | 2.0501 | 3.0515 | 0.617 | `candidate_recovery_or_relax` |
| `liquidity_bucket` | `liquidity_high` | 3937 | 89 | 2.3056 | 3.4678 | 0.6629 | `candidate_recovery_or_relax` |
| `chosen_action` | `WAIT_REQUOTE` | 1913 | 63 | 3.4327 | 5.2779 | 0.746 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 8090 | 63 | 3.4327 | 5.2779 | 0.746 | `source_quality_workorder` |
| `source_stage` | `wait6579_ev_cohort` | 63 | 63 | 3.4327 | 5.2779 | 0.746 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_watch` | 2482 | 48 | 2.2447 | 3.0785 | 0.6875 | `candidate_recovery_or_relax` |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 593 | 30 | -0.1948 | -1.267 | 0.3 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_not_available` | 3601 | 30 | -0.1948 | -1.267 | 0.3 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_not_available` | 2787 | 30 | -0.1948 | -1.267 | 0.3 | `source_quality_workorder` |
| `source_stage` | `scalp_sim_entry_ai_price_skip_order` | 532 | 30 | -0.1948 | -1.267 | 0.3 | `hold_sample` |
| `strength_bucket` | `risk_context_not_available` | 393 | 29 | -0.2409 | -1.2555 | 0.3104 | `hold_sample` |
| `stale_bucket` | `stale_not_available` | 2072 | 29 | -0.2409 | -1.2555 | 0.3104 | `source_quality_workorder` |
| `chosen_action` | `NO_BUY_AI` | 4965 | 27 | -0.2615 | -0.6663 | 0.4815 | `hold_sample` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 5589 | 27 | -0.2615 | -0.6663 | 0.4815 | `source_quality_workorder` |
| `stale_bucket` | `fresh` | 4174 | 26 | -0.3218 | -0.7346 | 0.4615 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 1631 | 26 | -0.4316 | -1.0488 | 0.3077 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 25 | 25 | 0.1771 | -1.4908 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_1000_1200` | 24 | 24 | 2.7518 | 3.8641 | 0.6667 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_trailing_take_profit` | 23 | 23 | -0.5589 | 0.5461 | 0.9565 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 1537 | 21 | 0.3582 | -0.1839 | 0.4286 | `hold_sample` |
| `overbought_bucket` | `overbought_ok` | 814 | 15 | 4.1917 | 8.0606 | 0.8 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 15 | 15 | 2.187 | 3.0597 | 0.7333 | `candidate_recovery_or_relax` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 118, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 514 | 82 | -0.5881 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 113 | 82 | -0.5881 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 113 | 82 | -0.5881 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 113 | 82 | -0.5881 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 113 | 82 | -0.5881 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 113 | 82 | -0.5881 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 113 | 82 | -0.5881 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 113 | 82 | -0.5881 | `keep_collecting` |
| `latency_state` | `simulated` | 113 | 82 | -0.5881 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 514 | 82 | -0.5881 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 548 | 81 | -0.5977 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 111 | 80 | -0.5795 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 87 | 66 | -0.4588 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 74 | 51 | -0.0955 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 74 | 51 | -0.0955 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 71 | 49 | -0.1252 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 461 | 49 | -0.1252 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 71 | 49 | -0.1252 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 70 | 43 | -0.8631 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 44 | 37 | -0.25 | `keep_collecting` |
| `would_limit_fill` | `false` | 497 | 34 | -0.2089 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 42 | 33 | -1.2753 | `source_quality_workorder` |
| `price_resolution_bucket` | `defensive_order_price` | 40 | 32 | -1.243 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 43 | 31 | -1.3985 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 38 | 31 | -1.3985 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 39 | 31 | -1.3985 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 70 | 29 | -1.1854 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 21 | 17 | -0.11 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 31 | 17 | -0.3078 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 20 | 15 | -1.6489 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 19 | 15 | 0.0645 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 11 | 11 | -0.7245 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 16 | 9 | -0.7076 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 12 | 8 | -0.2698 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 7 | 7 | 0.4465 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 9 | 6 | -1.8905 | `keep_collecting` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 2 | 2 | -0.9304 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_10s_plus` | 5 | 2 | -2.5877 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 9 | 2 | -1.2667 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 2 | 2 | -2.5877 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 31, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 110 | 81 | -0.8198 | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 110 | 81 | -0.8198 | `hold_sample` |
| `holding_action` | `WAIT` | 91 | 69 | -0.8634 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 46 | 44 | -1.2772 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 42 | 42 | -1.2331 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 23 | 23 | -0.3925 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 15 | 15 | -0.384 | `hold_no_edge` |
| `holding_action` | `holding_action_not_applicable_at_start` | 18 | 11 | -0.6024 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 7 | 7 | 0.3569 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 7 | 7 | -0.4381 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 11 | 6 | -0.9066 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 6 | 6 | -0.9066 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 5 | 5 | 0.3306 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 2 | 2 | -2.2024 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 0.4227 | `hold_sample` |
| `holding_action` | `BUY` | 1 | 1 | -0.2008 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 1 | 1 | 1.7646 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | -0.2008 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 1 | 1 | 1.7646 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 7 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 3 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 3 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 29 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 7 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 22 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 7 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_020_180s` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 48, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `exit_source_stage` | `sim_post_sell_evaluation` | 79 | 79 | -0.6638 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 66 | 66 | -1.2236 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 36 | 36 | -0.4677 | `hold_no_edge` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 36 | 36 | -0.9425 | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 36 | 36 | -0.9425 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 36 | 36 | -0.9425 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 36 | 36 | -0.0302 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 27 | 27 | -0.6533 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 23 | 23 | -0.3925 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 23 | 23 | -0.5996 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 22 | 22 | -0.2581 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 22 | 22 | -1.1727 | `hold_sample` |
| `exit_outcome` | `GOOD_EXIT` | 21 | 21 | -1.425 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 17 | 17 | -0.8385 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 15 | 15 | -2.2398 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 14 | 14 | -0.5807 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 10 | 10 | -0.9729 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 10 | 10 | -0.0023 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 9 | 9 | -0.2267 | `hold_sample` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 8 | 8 | -0.6116 | `hold_sample` |
| `exit_outcome` | `COMPLETED` | 7 | 7 | -0.6825 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 7 | 7 | 0.3569 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 7 | 7 | -0.6825 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 6 | 6 | -2.6836 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 5 | 5 | -0.2115 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 5 | 5 | -2.0998 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 4 | 4 | -1.7493 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 4 | 4 | 0.4405 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 3 | 3 | 0.2455 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 3 | 3 | 0.2415 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 2 | 2 | 4.0844 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_lt_neg070` | 2 | 2 | -1.86 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300_plus` | 2 | 2 | 4.0844 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 1 | 1 | 1.7646 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 1 | 1 | -1.3447 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=NEUTRAL|profit=profit_neg070_neg010` | 1 | 1 | -0.115 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg070_neg010` | 1 | 1 | -3.4858 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg070_neg010` | 1 | 1 | -0.8911 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 1 | 1 | 1.7646 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg070_neg010` | 1 | 1 | -0.1128 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 349, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 7077 | 7075 | None | -0.9648 | 0.053 | `hold_sample` |
| `arm` | `AVG_DOWN` | 6705 | 6645 | None | -1.0506 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 6633 | 6573 | None | -1.0273 | 0.0 | `hold_sample` |
| `price_guard_reason` | `price_guard_none` | 5670 | 5621 | None | -0.8363 | 0.0614 | `hold_sample` |
| `qty_reason` | `qty_none` | 5621 | 5621 | None | -0.8363 | 0.0614 | `hold_sample` |
| `time_bucket` | `time_unknown` | 5670 | 5621 | None | -0.8363 | 0.0614 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 3327 | 3327 | None | -0.9793 | 0.052 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 3201 | 3201 | None | -1.2249 | 0.0 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 3042 | 2993 | None | -0.7609 | 0.1153 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2974 | 2974 | None | -0.8272 | 0.0572 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 2682 | 2633 | None | -0.9204 | 0.0015 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 2179 | 2179 | None | -0.9659 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 2013 | 2013 | None | -0.9266 | 0.0919 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 1892 | 1892 | None | -0.4809 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 1337 | 1337 | None | -0.8459 | 0.0785 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_1` | 874 | 874 | None | -1.0502 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 798 | 798 | None | -0.9096 | 0.0564 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 757 | 757 | None | -0.2809 | 0.3857 | `hold_sample` |
| `ai_score_source` | `not_evaluated_no_ai_score_source` | 699 | 699 | None | -0.7857 | 0.0286 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_2` | 677 | 677 | None | -0.8551 | 0.0 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 14 | 7 | -0.6825 | -0.91 | 0.0 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 7 | 7 | -0.6825 | -0.91 | 0.0 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 14 | 7 | -0.6825 | -0.91 | 0.0 | `hold_sample` |
| `stage` | `exit` | 7 | 7 | -0.6825 | -0.91 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 14 | 7 | -0.6825 | -0.91 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 14 | 7 | -0.6825 | -0.91 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 7 | 7 | -0.6825 | -0.91 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 5 | 5 | -0.2115 | -0.282 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 10 | 5 | -0.2115 | -0.282 | 0.0 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 8 | 4 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 6 | 3 | -0.2375 | -0.3167 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 6 | 3 | -1.2975 | -1.73 | 0.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 6 | 3 | -1.3625 | -1.8167 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 2 | 2 | -1.86 | -2.48 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 4 | 2 | -1.86 | -2.48 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 7 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_lt_neg070` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 5 | 0 | None | None | None | `hold_sample` |
| `stage` | `holding` | 7 | 0 | None | None | None | `hold_sample` |

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
