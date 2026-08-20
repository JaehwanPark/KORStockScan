# Lifecycle Decision Matrix - 2026-08-19

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-08-19_mtd`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `20348`
- source_rows_total: `26800`
- retained_rows: `20348`
- dropped_rows_by_source: `{}`
- joined_rows: `7649`
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
- lifecycle_flow_bucket_count: `160`
- lifecycle_flow_complete_count: `79`
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
| `entry` | 8750 | 121 | 1.6818 | 0.189 | `pass` | `NO_CHANGE` | False |
| `submit` | 625 | 93 | -0.5944 | 0.3642 | `pass` | `NO_CHANGE` | False |
| `holding` | 129 | 92 | -0.8502 | 0.7354 | `pass` | `EXIT` | False |
| `scale_in` | 7263 | 7200 | -0.8724 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 3581 | 143 | -0.7767 | 0.2485 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 160, 'complete_flow_count': 79, 'incomplete_flow_count': 13371, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 6794 | 6733 | -0.9614 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 469 | 467 | 0.4102 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 58 | 58 | 3.4417 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:4e1fc29475` | 4 | 4 | -0.842 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:d0233209ef` | 4 | 4 | -0.6925 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 4 | 4 | 3.1589 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:5159f83a5b` | 3 | 3 | -0.1136 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:0cb91a7ba6` | 3 | 3 | -0.9233 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:cb6ed22b69` | 3 | 3 | -1.0067 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:305d9e5c71` | 3 | 3 | -0.2375 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:62b3401904` | 3 | 3 | -0.26 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:b75bf201fa` | 2 | 2 | -0.745 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:397dbf1728` | 2 | 2 | -0.84 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:f548b6989d` | 2 | 2 | -0.54 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:03eec49aed` | 2 | 2 | -1.1106 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:77c2d7d131` | 2 | 2 | -1.195 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:f658be39ac` | 2 | 2 | -1.86 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:5603187fa1` | 2 | 2 | 4.0844 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:bf44bd3042` | 1 | 1 | -0.53 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:92f69621e6` | 1 | 1 | -1.21 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 421, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `score_band` | `score_63_65` | 1086 | 94 | 2.0501 | 3.0515 | 0.617 | `candidate_recovery_or_relax` |
| `liquidity_bucket` | `liquidity_high` | 4182 | 90 | 2.2815 | 3.3901 | 0.6555 | `candidate_recovery_or_relax` |
| `chosen_action` | `WAIT_REQUOTE` | 2138 | 63 | 3.4327 | 5.2779 | 0.746 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 8692 | 63 | 3.4327 | 5.2779 | 0.746 | `source_quality_workorder` |
| `source_stage` | `wait6579_ev_cohort` | 63 | 63 | 3.4327 | 5.2779 | 0.746 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_watch` | 2666 | 49 | 2.2017 | 2.9438 | 0.6735 | `candidate_recovery_or_relax` |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 609 | 30 | -0.1948 | -1.267 | 0.3 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_not_available` | 3929 | 30 | -0.1948 | -1.267 | 0.3 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_not_available` | 3089 | 30 | -0.1948 | -1.267 | 0.3 | `source_quality_workorder` |
| `source_stage` | `scalp_sim_entry_ai_price_skip_order` | 546 | 30 | -0.1948 | -1.267 | 0.3 | `hold_sample` |
| `strength_bucket` | `risk_context_not_available` | 407 | 29 | -0.2409 | -1.2555 | 0.3104 | `hold_sample` |
| `stale_bucket` | `stale_not_available` | 2281 | 29 | -0.2409 | -1.2555 | 0.3104 | `source_quality_workorder` |
| `chosen_action` | `NO_BUY_AI` | 5247 | 28 | -0.2473 | -0.7682 | 0.4643 | `hold_sample` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 6059 | 28 | -0.2473 | -0.7682 | 0.4643 | `source_quality_workorder` |
| `stale_bucket` | `fresh` | 4532 | 27 | -0.3048 | -0.8378 | 0.4444 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 1798 | 27 | -0.4106 | -1.1404 | 0.2963 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 25 | 25 | 0.1771 | -1.4908 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_1000_1200` | 24 | 24 | 2.7518 | 3.8641 | 0.6667 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_trailing_take_profit` | 23 | 23 | -0.5589 | 0.5461 | 0.9565 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 1574 | 21 | 0.3582 | -0.1839 | 0.4286 | `hold_sample` |
| `overbought_bucket` | `overbought_ok` | 870 | 15 | 4.1917 | 8.0606 | 0.8 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 15 | 15 | 2.187 | 3.0597 | 0.7333 | `candidate_recovery_or_relax` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 121, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 569 | 93 | -0.5944 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 124 | 93 | -0.5944 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 124 | 93 | -0.5944 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 124 | 93 | -0.5944 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 124 | 93 | -0.5944 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 124 | 93 | -0.5944 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 124 | 93 | -0.5944 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 124 | 93 | -0.5944 | `keep_collecting` |
| `latency_state` | `simulated` | 124 | 93 | -0.5944 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 569 | 93 | -0.5944 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 614 | 92 | -0.6029 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 122 | 91 | -0.587 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 90 | 69 | -0.5192 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 76 | 53 | -0.1002 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 76 | 53 | -0.1002 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 73 | 51 | -0.129 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 506 | 51 | -0.129 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 73 | 51 | -0.129 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 76 | 49 | -1.018 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 49 | 42 | -0.0842 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 51 | 42 | -1.1595 | `source_quality_workorder` |
| `price_resolution_bucket` | `defensive_order_price` | 49 | 41 | -1.1314 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 52 | 40 | -1.2492 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 47 | 40 | -1.2492 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 48 | 40 | -1.2492 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 84 | 36 | -1.089 | `keep_collecting` |
| `would_limit_fill` | `false` | 554 | 35 | -0.1991 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 24 | 19 | -1.7562 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 22 | 18 | -0.0964 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 31 | 17 | -0.3078 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 20 | 16 | 0.0242 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 22 | 15 | -0.2977 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 14 | 14 | -0.2973 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 13 | 9 | -0.3043 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 11 | 8 | -1.8453 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 7 | 7 | 0.4465 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_10s_plus` | 8 | 4 | -1.7409 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 3 | 3 | -2.9104 | `source_quality_workorder` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 2 | 2 | -0.9304 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 9 | 2 | -1.2667 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 31, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 121 | 92 | -0.8502 | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 121 | 92 | -0.8502 | `hold_sample` |
| `holding_action` | `WAIT` | 94 | 72 | -0.8974 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 51 | 49 | -1.2884 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 43 | 43 | -1.2471 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 27 | 27 | -0.5543 | `hold_no_edge` |
| `holding_action` | `holding_action_not_applicable_at_start` | 26 | 19 | -0.7053 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 16 | 16 | -0.5239 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 10 | 10 | -0.6381 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 8 | 8 | 0.5173 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 13 | 7 | -0.86 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 7 | 7 | -0.86 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 6 | 6 | -1.5841 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 5 | 5 | 0.3306 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 3 | 3 | 0.8284 | `hold_sample` |
| `holding_action` | `BUY` | 1 | 1 | -0.2008 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 1 | 1 | 1.7646 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | -0.2008 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 1 | 1 | 1.7646 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 8 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 3 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 3 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 29 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 8 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 22 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 7 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_020_180s` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 48, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `exit_source_stage` | `sim_post_sell_evaluation` | 89 | 89 | -0.7154 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 77 | 77 | -1.2163 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 46 | 46 | -0.9172 | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 46 | 46 | -0.9172 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 46 | 46 | -0.9172 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 41 | 41 | -0.1313 | `hold_sample` |
| `exit_outcome` | `NEUTRAL` | 39 | 39 | -0.5605 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 28 | 28 | -0.5902 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 28 | 28 | -1.1343 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 27 | 27 | -0.5543 | `hold_no_edge` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 27 | 27 | -0.6533 | `hold_sample` |
| `exit_outcome` | `MISSED_UPSIDE` | 26 | 26 | -0.2859 | `hold_sample` |
| `exit_outcome` | `GOOD_EXIT` | 24 | 24 | -1.4324 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 20 | 20 | -2.0266 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 18 | 18 | -0.5794 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 17 | 17 | -0.8385 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 13 | 13 | -1.091 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 11 | 11 | -0.1369 | `hold_no_edge` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 9 | 9 | -0.5919 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 9 | 9 | -0.2267 | `hold_sample` |
| `exit_outcome` | `COMPLETED` | 8 | 8 | -0.6516 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 8 | 8 | 0.5173 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 8 | 8 | -0.6516 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 7 | 7 | -1.4848 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 7 | 7 | -2.0053 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 6 | 6 | -0.2487 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 6 | 6 | -2.6836 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 5 | 5 | 0.6804 | `hold_sample` |
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
- summary: `{'bucket_count': 350, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 7169 | 7167 | None | -0.9663 | 0.0529 | `hold_sample` |
| `arm` | `AVG_DOWN` | 6794 | 6733 | None | -1.0518 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 6722 | 6661 | None | -1.0288 | 0.0 | `hold_sample` |
| `price_guard_reason` | `price_guard_none` | 5763 | 5713 | None | -0.8403 | 0.0611 | `hold_sample` |
| `qty_reason` | `qty_none` | 5713 | 5713 | None | -0.8403 | 0.0611 | `hold_sample` |
| `time_bucket` | `time_unknown` | 5763 | 5713 | None | -0.8403 | 0.0611 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 3356 | 3356 | None | -0.981 | 0.0516 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 3258 | 3258 | None | -1.2304 | 0.0 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 3095 | 3045 | None | -0.7682 | 0.1146 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2976 | 2976 | None | -0.8293 | 0.0571 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 2723 | 2673 | None | -0.9208 | 0.0015 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 2211 | 2211 | None | -0.9752 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 2020 | 2020 | None | -0.9356 | 0.0916 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 1923 | 1923 | None | -0.4798 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 1354 | 1354 | None | -0.843 | 0.0783 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_1` | 886 | 886 | None | -1.0563 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 849 | 849 | None | -0.9302 | 0.0542 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 777 | 777 | None | -0.2873 | 0.3809 | `hold_sample` |
| `ai_score_source` | `not_evaluated_no_ai_score_source` | 751 | 751 | None | -0.7747 | 0.032 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_2` | 681 | 681 | None | -0.8563 | 0.0 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 16 | 8 | -0.6516 | -0.8688 | 0.0 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 8 | 8 | -0.6516 | -0.8688 | 0.0 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 16 | 8 | -0.6516 | -0.8688 | 0.0 | `hold_sample` |
| `stage` | `exit` | 8 | 8 | -0.6516 | -0.8688 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 16 | 8 | -0.6516 | -0.8688 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 16 | 8 | -0.6516 | -0.8688 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 8 | 8 | -0.6516 | -0.8688 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 6 | 6 | -0.2487 | -0.3317 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 12 | 6 | -0.2487 | -0.3317 | 0.0 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 8 | 4 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 8 | 4 | -1.1306 | -1.5075 | 0.0 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 6 | 3 | -0.2375 | -0.3167 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 6 | 3 | -1.2975 | -1.73 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 2 | 2 | -1.86 | -2.48 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 4 | 2 | -0.3037 | -0.405 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 4 | 2 | -1.86 | -2.48 | 0.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 8 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_lt_neg070` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 6 | 0 | None | None | None | `hold_sample` |
| `stage` | `holding` | 8 | 0 | None | None | None | `hold_sample` |

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
