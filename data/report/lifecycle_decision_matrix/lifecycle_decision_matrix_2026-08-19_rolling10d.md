# Lifecycle Decision Matrix - 2026-08-19

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-08-19_rolling10d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `13718`
- source_rows_total: `16024`
- retained_rows: `13718`
- dropped_rows_by_source: `{}`
- joined_rows: `5971`
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
- lifecycle_flow_bucket_count: `122`
- lifecycle_flow_complete_count: `59`
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
| `entry` | 4291 | 44 | -0.3001 | 0.0151 | `pass` | `NO_CHANGE` | False |
| `submit` | 428 | 78 | -0.711 | 0.4096 | `pass` | `NO_CHANGE` | False |
| `holding` | 108 | 77 | -0.9621 | 0.8278 | `pass` | `EXIT` | False |
| `scale_in` | 5725 | 5664 | -0.9351 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 3166 | 108 | -0.8406 | 0.2908 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 122, 'complete_flow_count': 59, 'incomplete_flow_count': 9916, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 5406 | 5346 | -1.0146 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 319 | 318 | 0.4008 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:4e1fc29475` | 4 | 4 | -0.842 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:5159f83a5b` | 3 | 3 | -0.1136 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:0cb91a7ba6` | 3 | 3 | -0.9233 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:305d9e5c71` | 3 | 3 | -0.2375 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:03eec49aed` | 2 | 2 | -1.1106 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:77c2d7d131` | 2 | 2 | -1.195 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:f658be39ac` | 2 | 2 | -1.86 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:62b3401904` | 2 | 2 | -0.3037 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:5603187fa1` | 2 | 2 | 4.0844 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:bf44bd3042` | 1 | 1 | -0.53 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:92f69621e6` | 1 | 1 | -1.21 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:5ad377bcf7` | 1 | 1 | -0.4211 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:7dd76f2392` | 1 | 1 | -2.1224 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_bl:e2e349e4ea` | 1 | 1 | -1.2 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:53097ae10f` | 1 | 1 | -0.2008 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:31a116e56b` | 1 | 1 | -0.7246 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:7664e5a914` | 1 | 1 | -0.1193 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:1fbcba9334` | 1 | 1 | 0.0719 | `hold_no_edge` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 325, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `NO_BUY_AI` | 2443 | 24 | -0.3236 | -1.05 | 0.375 | `hold_sample` |
| `stale_bucket` | `fresh` | 2567 | 24 | -0.3236 | -1.05 | 0.375 | `hold_sample` |
| `liquidity_bucket` | `liquidity_high` | 2061 | 24 | -0.3236 | -1.05 | 0.375 | `hold_sample` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 3283 | 24 | -0.3236 | -1.05 | 0.375 | `source_quality_workorder` |
| `time_bucket` | `time_1000_1200` | 1144 | 24 | -0.3361 | -0.9442 | 0.3333 | `hold_sample` |
| `score_band` | `score_63_65` | 286 | 23 | -0.4968 | -0.7409 | 0.3913 | `hold_no_edge` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 21 | 21 | 0.0907 | -1.4924 | 0.0 | `hold_sample` |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 240 | 20 | -0.2719 | -1.29 | 0.3 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_not_available` | 2105 | 20 | -0.2719 | -1.29 | 0.3 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_not_available` | 1804 | 20 | -0.2719 | -1.29 | 0.3 | `source_quality_workorder` |
| `strength_bucket` | `risk_context_not_available` | 216 | 20 | -0.2719 | -1.29 | 0.3 | `hold_no_edge` |
| `source_stage` | `scalp_sim_entry_ai_price_skip_order` | 216 | 20 | -0.2719 | -1.29 | 0.3 | `hold_no_edge` |
| `stale_bucket` | `stale_not_available` | 1397 | 20 | -0.2719 | -1.29 | 0.3 | `source_quality_workorder` |
| `strength_bucket` | `weak_strength_momentum` | 1995 | 19 | -0.2454 | -0.92 | 0.4211 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 15 | 15 | -0.9639 | 0.5653 | 1.0 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 648 | 14 | -0.136 | -1.1135 | 0.2143 | `hold_sample` |
| `score_band` | `score_70p` | 178 | 11 | -0.2211 | -1.4855 | 0.3636 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1000_1200` | 74 | 9 | -0.2838 | -1.0044 | 0.3333 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 8 | 8 | -0.0811 | -3.5175 | 0.0 | `hold_sample` |
| `time_bucket` | `time_0900_1000` | 841 | 8 | 0.2262 | -1.5037 | 0.25 | `source_quality_workorder` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 117, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 399 | 78 | -0.711 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 104 | 78 | -0.711 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 104 | 78 | -0.711 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 104 | 78 | -0.711 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 104 | 78 | -0.711 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 104 | 78 | -0.711 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 104 | 78 | -0.711 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 104 | 78 | -0.711 | `keep_collecting` |
| `latency_state` | `simulated` | 104 | 78 | -0.711 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 399 | 78 | -0.711 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 419 | 77 | -0.7227 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 102 | 76 | -0.7052 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 73 | 55 | -0.6591 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 71 | 46 | -1.0987 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 64 | 43 | -0.1715 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 64 | 43 | -0.1715 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 61 | 41 | -0.2108 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 346 | 41 | -0.2108 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 61 | 41 | -0.2108 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 43 | 37 | -1.2652 | `source_quality_workorder` |
| `price_resolution_bucket` | `defensive_order_price` | 41 | 36 | -1.2362 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 44 | 35 | -1.3738 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 39 | 35 | -1.3738 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 40 | 35 | -1.3738 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 63 | 32 | -1.2601 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 34 | 30 | -0.1019 | `keep_collecting` |
| `would_limit_fill` | `false` | 368 | 28 | -0.2658 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 22 | 18 | -1.8393 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 30 | 17 | -0.3078 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 20 | 15 | -0.2977 | `keep_collecting` |
| `would_limit_fill` | `true` | 17 | 13 | -0.0923 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 14 | 11 | -0.2007 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 11 | 11 | -0.5038 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 10 | 7 | -2.073 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 11 | 7 | -0.5222 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 6 | 6 | 0.4092 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_10s_plus` | 6 | 4 | -1.7409 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 3 | 3 | -2.9104 | `source_quality_workorder` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 2 | 2 | -0.9304 | `keep_collecting` |
| `overbought_guard_action` | `would_block` | 2 | 2 | -0.9304 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 30, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 101 | 77 | -0.9621 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 101 | 77 | -0.9621 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 75 | 58 | -1.0389 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 45 | 43 | -1.3059 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 37 | 37 | -1.2608 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 21 | 21 | -0.7745 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 25 | 18 | -0.757 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 11 | 11 | -0.8598 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 9 | 9 | -0.734 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 11 | 6 | -0.9845 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 6 | 6 | 0.4135 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 6 | 6 | -0.9845 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 6 | 6 | -1.5841 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 3 | 3 | -0.0015 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 3 | 3 | 0.8284 | `hold_sample` |
| `holding_action` | `BUY` | 1 | 1 | -0.2008 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 1 | 1 | 1.7646 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | -0.2008 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 1 | 1 | 1.7646 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 7 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 3 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 24 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 7 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 17 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 7 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_020_180s` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 44, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `exit_source_stage` | `sim_post_sell_evaluation` | 74 | 74 | -0.8046 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 61 | 61 | -1.252 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 32 | 32 | -0.2571 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 31 | 31 | -0.6475 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 27 | 27 | -0.9708 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 27 | 27 | -0.9708 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 27 | 27 | -0.9708 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 23 | 23 | -0.691 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 22 | 22 | -0.3501 | `hold_no_edge` |
| `exit_outcome` | `GOOD_EXIT` | 21 | 21 | -1.5125 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 21 | 21 | -0.7745 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 18 | 18 | -1.9612 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 18 | 18 | -1.1922 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 17 | 17 | -0.6213 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 16 | 16 | -0.8401 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 12 | 12 | -1.2007 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 9 | 9 | -0.5278 | `hold_sample` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 8 | 8 | -0.6444 | `hold_sample` |
| `exit_outcome` | `COMPLETED` | 7 | 7 | -0.72 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 7 | 7 | -0.72 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 7 | 7 | -1.4848 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 6 | 6 | 0.4135 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 6 | 6 | -0.1847 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 6 | 6 | -2.0174 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 6 | 6 | -0.4302 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 5 | 5 | -0.264 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 5 | 5 | -2.5609 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 4 | 4 | 0.5501 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 3 | 3 | 0.2415 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 2 | 2 | 4.0844 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_lt_neg070` | 2 | 2 | -1.86 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 2 | 2 | 0.1401 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300_plus` | 2 | 2 | 4.0844 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 1 | 1 | 1.7646 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 1 | 1 | -1.3447 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=NEUTRAL|profit=profit_neg070_neg010` | 1 | 1 | -0.115 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg070_neg010` | 1 | 1 | -3.4858 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg070_neg010` | 1 | 1 | -0.8911 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 1 | 1 | 1.7646 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 3058 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 321, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 5656 | 5655 | None | -1.0285 | 0.0518 | `hold_sample` |
| `arm` | `AVG_DOWN` | 5406 | 5346 | None | -1.1095 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 5338 | 5278 | None | -1.0828 | 0.0 | `hold_sample` |
| `price_guard_reason` | `price_guard_none` | 4225 | 4177 | None | -0.8884 | 0.0572 | `hold_sample` |
| `qty_reason` | `qty_none` | 4177 | 4177 | None | -0.8884 | 0.0572 | `hold_sample` |
| `time_bucket` | `time_unknown` | 4225 | 4177 | None | -0.8884 | 0.0572 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 2766 | 2766 | None | -1.0549 | 0.0535 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 2710 | 2710 | None | -1.1905 | 0.0 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 2256 | 2208 | None | -0.8265 | 0.1082 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2119 | 2119 | None | -0.9834 | 0.042 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 2022 | 1974 | None | -0.9554 | 0.002 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 1661 | 1661 | None | -1.001 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 1487 | 1487 | None | -1.0267 | 0.0753 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 1123 | 1123 | None | -0.496 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 1092 | 1092 | None | -0.7934 | 0.0943 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 621 | 621 | None | -0.8063 | 0.0483 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_1` | 619 | 619 | None | -1.0988 | 0.0 | `hold_sample` |
| `ai_score_source` | `not_evaluated_no_ai_score_source` | 599 | 599 | None | -0.7847 | 0.0317 | `hold_sample` |
| `ai_score_source` | `holding_ai_not_called` | 571 | 571 | None | -1.0451 | 0.014 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 529 | 529 | None | -0.3249 | 0.4215 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 14 | 7 | -0.72 | -0.96 | 0.0 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 7 | 7 | -0.72 | -0.96 | 0.0 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 14 | 7 | -0.72 | -0.96 | 0.0 | `hold_sample` |
| `stage` | `exit` | 7 | 7 | -0.72 | -0.96 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 14 | 7 | -0.72 | -0.96 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 14 | 7 | -0.72 | -0.96 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 7 | 7 | -0.72 | -0.96 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 5 | 5 | -0.264 | -0.352 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 10 | 5 | -0.264 | -0.352 | 0.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 8 | 4 | -1.1306 | -1.5075 | 0.0 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 6 | 3 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 6 | 3 | -0.2375 | -0.3167 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 2 | 2 | -1.86 | -2.48 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 4 | 2 | -1.86 | -2.48 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 4 | 2 | -0.3037 | -0.405 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 4 | 2 | -1.86 | -2.48 | 0.0 | `hold_sample` |
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
