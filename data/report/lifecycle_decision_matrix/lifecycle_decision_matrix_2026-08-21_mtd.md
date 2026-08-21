# Lifecycle Decision Matrix - 2026-08-21

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-08-21_mtd`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `25640`
- source_rows_total: `33500`
- retained_rows: `25640`
- dropped_rows_by_source: `{}`
- joined_rows: `10031`
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
- lifecycle_flow_bucket_count: `187`
- lifecycle_flow_complete_count: `102`
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
| `entry` | 10191 | 136 | 1.4398 | 0.1693 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 820 | 117 | -0.672 | 0.3218 | `pass` | `NO_CHANGE` | False |
| `holding` | 163 | 115 | -0.8944 | 0.746 | `pass` | `EXIT` | False |
| `scale_in` | 9566 | 9487 | -0.8033 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 4900 | 176 | -0.8162 | 0.2156 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 187, 'complete_flow_count': 102, 'incomplete_flow_count': 17329, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 8689 | 8612 | -0.9223 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 877 | 875 | 0.368 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
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
- summary: `{'bucket_count': 433, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 4769 | 103 | 1.9119 | 2.8058 | 0.6213 | `candidate_recovery_or_relax` |
| `score_band` | `score_63_65` | 1105 | 96 | 1.9998 | 2.9935 | 0.625 | `candidate_recovery_or_relax` |
| `chosen_action` | `WAIT_REQUOTE` | 2757 | 65 | 3.3381 | 5.1293 | 0.7538 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 10118 | 63 | 3.4327 | 5.2779 | 0.746 | `source_quality_workorder` |
| `source_stage` | `wait6579_ev_cohort` | 63 | 63 | 3.4327 | 5.2779 | 0.746 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_watch` | 2995 | 55 | 1.8372 | 2.3921 | 0.6182 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 7272 | 43 | -0.3398 | -0.8542 | 0.4651 | `source_quality_workorder` |
| `chosen_action` | `NO_BUY_AI` | 5923 | 41 | -0.3739 | -0.9178 | 0.439 | `hold_sample` |
| `stale_bucket` | `fresh` | 5310 | 40 | -0.4159 | -0.9685 | 0.425 | `hold_sample` |
| `liquidity_bucket` | `liquidity_not_available` | 4734 | 32 | -0.1602 | -1.1597 | 0.3438 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_not_available` | 3828 | 32 | -0.1602 | -1.1597 | 0.3438 | `source_quality_workorder` |
| `stale_bucket` | `stale_not_available` | 2867 | 31 | -0.2022 | -1.1455 | 0.3548 | `source_quality_workorder` |
| `time_bucket` | `time_1000_1200` | 2217 | 31 | -0.3436 | -1.1277 | 0.3226 | `hold_sample` |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 635 | 30 | -0.1948 | -1.267 | 0.3 | `source_quality_workorder` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 30 | 30 | 0.0949 | -1.4857 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_entry_ai_price_skip_order` | 563 | 30 | -0.1948 | -1.267 | 0.3 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 30 | 30 | -0.5485 | 0.5047 | 0.9667 | `hold_sample` |
| `strength_bucket` | `risk_context_not_available` | 424 | 29 | -0.2409 | -1.2555 | 0.3104 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 3950 | 28 | -0.439 | -1.0739 | 0.3929 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 1799 | 27 | 0.2386 | -0.2753 | 0.4444 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_1000_1200` | 24 | 24 | 2.7518 | 3.8641 | 0.6667 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_ok` | 986 | 16 | 3.8991 | 7.5649 | 0.8125 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 15 | 15 | 2.187 | 3.0597 | 0.7333 | `candidate_recovery_or_relax` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 128, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 732 | 117 | -0.672 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 162 | 117 | -0.672 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 162 | 117 | -0.672 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 162 | 117 | -0.672 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 162 | 117 | -0.672 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 162 | 117 | -0.672 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 162 | 117 | -0.672 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 162 | 117 | -0.672 | `keep_collecting` |
| `latency_state` | `simulated` | 162 | 117 | -0.672 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 732 | 117 | -0.672 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 799 | 115 | -0.6884 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 160 | 115 | -0.6676 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 110 | 80 | -0.5357 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 105 | 70 | -0.2109 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 105 | 70 | -0.2109 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 98 | 67 | -0.2445 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 651 | 67 | -0.2445 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 98 | 67 | -0.2445 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 101 | 64 | -1.0028 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 62 | 51 | -0.2469 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 64 | 50 | -1.2449 | `source_quality_workorder` |
| `price_resolution_bucket` | `defensive_order_price` | 62 | 49 | -1.2232 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 62 | 47 | -1.3589 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 55 | 47 | -1.3589 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 57 | 47 | -1.3589 | `keep_collecting` |
| `would_limit_fill` | `false` | 727 | 46 | -0.3212 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 118 | 44 | -1.1989 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 36 | 26 | -0.7132 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 40 | 24 | -0.4175 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 29 | 22 | -0.2161 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 27 | 22 | -1.8582 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 29 | 21 | -0.0764 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 19 | 18 | -0.5859 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 22 | 14 | -0.3379 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 15 | 10 | -1.7001 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 7 | 7 | 0.4465 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_10s_plus` | 10 | 4 | -1.7409 | `keep_collecting` |
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
| `held_bucket` | `held_not_applicable_at_start` | 154 | 115 | -0.8944 | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 154 | 115 | -0.8944 | `hold_sample` |
| `holding_action` | `WAIT` | 114 | 86 | -0.86 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 64 | 61 | -1.3892 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 49 | 49 | -1.2296 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 36 | 36 | -0.4575 | `hold_no_edge` |
| `holding_action` | `holding_action_not_applicable_at_start` | 39 | 28 | -1.025 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 23 | 23 | -0.402 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 12 | 12 | -2.0408 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 12 | 12 | -0.5853 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 9 | 9 | 0.2536 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 13 | 7 | -0.86 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 7 | 7 | -0.86 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 6 | 6 | -0.0337 | `hold_sample` |
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
| `profit_band` | `profit_not_applicable_at_start` | 39 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 9 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 28 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 11 | 0 | None | `hold_sample` |
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
| `exit_source_stage` | `sim_post_sell_evaluation` | 111 | 111 | -0.7766 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 95 | 95 | -1.2723 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 56 | 56 | -0.9047 | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 56 | 56 | -0.9047 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 56 | 56 | -0.9047 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 52 | 52 | -0.1618 | `hold_sample` |
| `exit_outcome` | `NEUTRAL` | 48 | 48 | -0.579 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 36 | 36 | -0.4575 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 34 | 34 | -1.1144 | `hold_sample` |
| `exit_outcome` | `GOOD_EXIT` | 33 | 33 | -1.4169 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 32 | 32 | -0.5896 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 32 | 32 | -0.6923 | `hold_sample` |
| `exit_outcome` | `MISSED_UPSIDE` | 30 | 30 | -0.3885 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 26 | 26 | -2.1353 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 22 | 22 | -0.5805 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 19 | 19 | -0.8347 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 16 | 16 | -0.9805 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 16 | 16 | -0.1401 | `hold_no_edge` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 10 | 10 | -0.691 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 10 | 10 | -0.2895 | `hold_sample` |
| `exit_outcome` | `COMPLETED` | 9 | 9 | -0.755 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 9 | 9 | 0.2536 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 9 | 9 | -0.755 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 9 | 9 | -1.6107 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 9 | 9 | -1.9588 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 8 | 8 | -2.9242 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 6 | 6 | -0.2487 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 5 | 5 | 0.6804 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 4 | 4 | -0.2797 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 4 | 4 | 0.365 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_lt_neg070` | 3 | 3 | -1.7675 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 3 | 3 | -1.1332 | `hold_sample` |
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
- summary: `{'bucket_count': 360, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 9447 | 9445 | None | -0.8892 | 0.0811 | `hold_sample` |
| `arm` | `AVG_DOWN` | 8689 | 8612 | None | -1.0069 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 8617 | 8540 | None | -0.9886 | 0.0 | `hold_sample` |
| `price_guard_reason` | `price_guard_none` | 8066 | 8000 | None | -0.7834 | 0.0931 | `hold_sample` |
| `qty_reason` | `qty_none` | 8000 | 8000 | None | -0.7834 | 0.0931 | `hold_sample` |
| `time_bucket` | `time_unknown` | 8066 | 8000 | None | -0.7834 | 0.0931 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 4597 | 4597 | None | -0.8861 | 0.0907 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 4376 | 4376 | None | -0.7224 | 0.1257 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 4433 | 4367 | None | -0.687 | 0.1706 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 4352 | 4352 | None | -1.2036 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 3705 | 3639 | None | -0.8977 | 0.0014 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 3086 | 3086 | None | -0.9433 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 2688 | 2688 | None | -0.477 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 2662 | 2662 | None | -0.8523 | 0.1165 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 1835 | 1835 | None | -0.8682 | 0.0589 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 1208 | 1208 | None | -0.1175 | 0.5596 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_1` | 1167 | 1167 | None | -1.0254 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 1106 | 1106 | None | -0.9024 | 0.0507 | `hold_sample` |
| `ai_score_source` | `not_evaluated_no_ai_score_source` | 955 | 955 | None | -0.7601 | 0.0283 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_2` | 926 | 926 | None | -0.8449 | 0.0 | `hold_sample` |

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
