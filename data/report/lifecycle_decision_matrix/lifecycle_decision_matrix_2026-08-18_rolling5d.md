# Lifecycle Decision Matrix - 2026-08-18

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-08-18_rolling5d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `6109`
- source_rows_total: `7484`
- retained_rows: `6109`
- dropped_rows_by_source: `{}`
- joined_rows: `2727`
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
- lifecycle_flow_bucket_count: `68`
- lifecycle_flow_complete_count: `25`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0052`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 1368 | 20 | -0.5508 | 0.0177 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 192 | 34 | -1.0954 | 0.5428 | `pass` | `NO_CHANGE` | False |
| `holding` | 52 | 33 | -1.2404 | 0.8122 | `pass` | `EXIT` | False |
| `scale_in` | 2615 | 2588 | -1.0768 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 1882 | 52 | -0.9514 | 0.1285 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 68, 'complete_flow_count': 25, 'incomplete_flow_count': 4808, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 2549 | 2522 | -1.1232 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 66 | 66 | 0.699 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:0cb91a7ba6` | 3 | 3 | -0.9233 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:03eec49aed` | 2 | 2 | -1.1106 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:f658be39ac` | 2 | 2 | -1.86 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:5603187fa1` | 2 | 2 | 4.0844 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:bf44bd3042` | 1 | 1 | -0.53 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:92f69621e6` | 1 | 1 | -1.21 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_bl:e2e349e4ea` | 1 | 1 | -1.2 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:53097ae10f` | 1 | 1 | -0.2008 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:f548b6989d` | 1 | 1 | -0.34 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:927a4c8e9e` | 1 | 1 | -0.2151 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:a6af469504` | 1 | 1 | -0.96 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:e629891351` | 1 | 1 | -0.84 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:9d1a12917f` | 1 | 1 | -2.31 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:a6d949bab9` | 1 | 1 | -1.56 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:4db4bab026` | 1 | 1 | -0.6724 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:b31cc048c8` | 1 | 1 | -2.55 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:77f502e017` | 1 | 1 | -2.4209 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:63a0b8330e` | 1 | 1 | -2.6687 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 213, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `NO_BUY_AI` | 634 | 18 | -0.483 | -0.7406 | 0.3889 | `source_quality_workorder` |
| `stale_bucket` | `fresh` | 756 | 18 | -0.483 | -0.7406 | 0.3889 | `hold_sample` |
| `liquidity_bucket` | `liquidity_high` | 553 | 18 | -0.483 | -0.7406 | 0.3889 | `hold_sample` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 1137 | 18 | -0.483 | -0.7406 | 0.3889 | `source_quality_workorder` |
| `strength_bucket` | `weak_strength_momentum` | 531 | 15 | -0.4195 | -0.7307 | 0.4 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 390 | 14 | -0.4034 | -0.7214 | 0.3571 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_normal` | 177 | 12 | -0.0948 | -1.1875 | 0.1667 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 11 | 11 | -0.0348 | -1.4836 | 0.0 | `hold_sample` |
| `score_band` | `score_63_65` | 58 | 8 | -1.0494 | -0.6212 | 0.375 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 7 | 7 | -1.2698 | 0.6743 | 1.0 | `hold_sample` |
| `score_band` | `score_70p` | 64 | 6 | -0.4908 | -0.725 | 0.5 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 5 | 5 | -0.3294 | -1.078 | 0.2 | `hold_sample` |
| `overbought_bucket` | `overbought_ok` | 153 | 3 | -2.119 | 0.8933 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 6 | 3 | -0.0044 | -0.9367 | 0.3333 | `hold_sample` |
| `score_band` | `score_60_62` | 7 | 3 | -0.0653 | -0.7733 | 0.3333 | `hold_sample` |
| `score_band` | `score_lt60` | 1239 | 3 | 0.1731 | -2.0367 | 0.0 | `source_quality_workorder` |
| `time_bucket` | `time_1400_close` | 382 | 3 | -1.1751 | -0.5867 | 0.6667 | `source_quality_workorder` |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 29 | 2 | -1.1609 | -2.21 | 0.0 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_not_available` | 784 | 2 | -1.1609 | -2.21 | 0.0 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_not_available` | 721 | 2 | -1.1609 | -2.21 | 0.0 | `source_quality_workorder` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 107, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 180 | 34 | -1.0954 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 51 | 34 | -1.0954 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 51 | 34 | -1.0954 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 51 | 34 | -1.0954 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 51 | 34 | -1.0954 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 51 | 34 | -1.0954 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 51 | 34 | -1.0954 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 51 | 34 | -1.0954 | `keep_collecting` |
| `latency_state` | `simulated` | 51 | 34 | -1.0954 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 180 | 34 | -1.0954 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 188 | 33 | -1.1342 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 49 | 32 | -1.1057 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 46 | 29 | -1.112 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 37 | 25 | -1.0344 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 35 | 22 | -0.3891 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 35 | 22 | -0.3891 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 33 | 20 | -0.4915 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 157 | 20 | -0.4915 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 33 | 20 | -0.4915 | `keep_collecting` |
| `would_limit_fill` | `false` | 168 | 15 | -0.3895 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 18 | 14 | -1.9581 | `source_quality_workorder` |
| `price_resolution_bucket` | `defensive_order_price` | 16 | 13 | -1.931 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 23 | 13 | -0.3429 | `source_quality_workorder` |
| `liquidity_bucket` | `below_min_liquidity` | 18 | 12 | -2.3902 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 28 | 12 | -1.8531 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 16 | 12 | -2.3902 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 16 | 12 | -2.3902 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 12 | 8 | -2.3519 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 7 | 5 | -2.2182 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 6 | 5 | -0.7974 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 6 | 5 | -0.7974 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 6 | 3 | -0.0203 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 5 | 3 | -1.0445 | `keep_collecting` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 2 | 2 | -0.9304 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_10s_plus` | 2 | 2 | -2.5877 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 4 | 2 | -0.6918 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 2 | 2 | -2.5877 | `source_quality_workorder` |
| `overbought_guard_action` | `would_block` | 2 | 2 | -0.9304 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_0_5bps` | 1 | 1 | -0.2298 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_block` | 1 | 1 | 0.1881 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 26, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 50 | 33 | -1.2404 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 50 | 33 | -1.2404 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 39 | 28 | -1.3581 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 24 | 22 | -1.5436 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 21 | 21 | -1.4909 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 7 | 7 | -0.683 | `hold_sample` |
| `holding_action` | `holding_action_not_applicable_at_start` | 10 | 4 | -0.6774 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 4 | 4 | -1.0498 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 2 | 2 | -0.2362 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 2 | 2 | -0.1906 | `hold_sample` |
| `holding_action` | `BUY` | 1 | 1 | -0.2008 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 1 | 1 | -3.4858 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 1 | 1 | 1.7646 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | -0.2008 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 1 | 1 | -3.4858 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | -0.794 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 1 | 1 | 1.7646 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1 | 1 | -2.65 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | 0.3217 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 2 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 17 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 11 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 6 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 2 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 39, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 34 | 34 | -1.4182 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 33 | 33 | -0.8426 | `candidate_recovery_or_relax` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 17 | 17 | -1.0559 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 17 | 17 | -1.0559 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 17 | 17 | -1.0559 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 15 | 15 | -0.3684 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_trailing_take_profit` | 13 | 13 | 0.0919 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 12 | 12 | -0.799 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 12 | 12 | -1.2917 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 11 | 11 | -0.8253 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 10 | 10 | -1.7845 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 8 | 8 | -0.5545 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 8 | 8 | -2.4265 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 7 | 7 | -0.683 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 6 | 6 | -0.9893 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 5 | 5 | -0.49 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 5 | 5 | -1.125 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 3 | 3 | -3.0186 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 3 | 3 | -1.9135 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `COMPLETED` | 2 | 2 | -1.86 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 2 | 2 | -0.2362 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 2 | 2 | 4.0844 | `hold_sample` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 2 | 2 | -1.86 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 2 | 2 | -1.86 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_lt_neg070` | 2 | 2 | -1.86 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 2 | 2 | -2.3081 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 2 | 2 | 0.4219 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300_plus` | 2 | 2 | 4.0844 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 1 | 1 | 1.7646 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | -0.5099 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg070_neg010` | 1 | 1 | -3.4858 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 1 | 1 | 0.3217 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 1 | 1 | -0.794 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 1 | 1 | 1.7646 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 1830 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_context_noop` | 1830 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 1830 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_context_warning_not_applicable` | 1830 | 0 | None | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=scalp_sim_panic_context_warning_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 1830 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 252, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 2585 | 2585 | None | -1.1877 | 0.0244 | `hold_sample` |
| `arm` | `AVG_DOWN` | 2549 | 2522 | None | -1.2342 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 2487 | 2460 | None | -1.1855 | 0.0 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 1227 | 1227 | None | -1.2789 | 0.0147 | `hold_sample` |
| `price_guard_reason` | `price_guard_none` | 1115 | 1101 | None | -0.8791 | 0.0027 | `hold_sample` |
| `qty_reason` | `qty_none` | 1101 | 1101 | None | -0.8791 | 0.0027 | `hold_sample` |
| `time_bucket` | `time_unknown` | 1115 | 1101 | None | -0.8791 | 0.0027 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 707 | 707 | None | -1.0732 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 593 | 593 | None | -1.2345 | 0.0523 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 569 | 555 | None | -0.8809 | 0.0 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 561 | 547 | None | -0.8772 | 0.0055 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 492 | 492 | None | -0.8873 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 463 | 463 | None | -0.9468 | 0.0043 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 378 | 378 | None | -0.5537 | 0.0 | `hold_sample` |
| `ai_score_source` | `not_evaluated_no_ai_score_source` | 357 | 357 | None | -0.8726 | 0.0196 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 332 | 332 | None | -0.8889 | 0.0 | `hold_sample` |
| `ai_score_source` | `holding_ai_not_called` | 286 | 286 | None | -0.9927 | 0.0175 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 196 | 196 | None | -0.7896 | 0.0 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_2` | 161 | 161 | None | -0.8674 | 0.0 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_1` | 151 | 151 | None | -0.8981 | 0.0 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 15, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 4 | 2 | -1.86 | -2.48 | 0.0 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 2 | 2 | -1.86 | -2.48 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 2 | 2 | -1.86 | -2.48 | 0.0 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 4 | 2 | -1.86 | -2.48 | 0.0 | `hold_sample` |
| `stage` | `exit` | 2 | 2 | -1.86 | -2.48 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 4 | 2 | -1.86 | -2.48 | 0.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 4 | 2 | -1.86 | -2.48 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 4 | 2 | -1.86 | -2.48 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 4 | 2 | -1.86 | -2.48 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 4 | 2 | -1.86 | -2.48 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 2 | 2 | -1.86 | -2.48 | 0.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_lt_neg070` | 2 | 0 | None | None | None | `hold_sample` |
| `stage` | `holding` | 2 | 0 | None | None | None | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_decision` | 2 | 0 | None | None | None | `hold_sample` |

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
