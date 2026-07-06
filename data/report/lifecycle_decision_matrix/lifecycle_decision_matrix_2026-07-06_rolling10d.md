# Lifecycle Decision Matrix - 2026-07-06

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-06_rolling10d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `35739`
- source_rows_total: `65294`
- retained_rows: `35739`
- dropped_rows_by_source: `{}`
- joined_rows: `18727`
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
- lifecycle_flow_complete_count: `69`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0021`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 2079 | 196 | 1.1738 | 0.5511 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 659 | 148 | -0.5489 | 0.6377 | `pass` | `NO_CHANGE` | False |
| `holding` | 441 | 148 | -0.8875 | 0.7825 | `pass` | `EXIT` | False |
| `scale_in` | 18020 | 17874 | -0.7385 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 14540 | 361 | -0.917 | 0.165 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 227, 'complete_flow_count': 69, 'incomplete_flow_count': 33302, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 15109 | 14995 | -0.9738 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 2682 | 2650 | 0.5995 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 199 | 199 | -1.036 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 91 | 91 | 1.0905 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 39 | 39 | 2.2821 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 16 | 16 | 2.4863 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 15 | 15 | -0.0097 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 9 | 9 | -1.1211 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b4078edac9` | 4 | 4 | -2.8316 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:4874ec99fd` | 3 | 3 | -2.057 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:224eb1ba18` | 3 | 3 | -2.1539 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 3 | 3 | -0.8333 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:2e5e6a8919` | 3 | 3 | -1.3825 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 3 | 3 | -0.8367 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:a4de6797c9` | 11 | 2 | 0.415 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:df02034b40` | 12 | 2 | -1.24 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:7d1a415bd0` | 2 | 2 | 0.8157 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:aee8bb0d09` | 2 | 2 | -0.795 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:15c17a2405` | 1 | 1 | -2.4958 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:c7dbb66715` | 2 | 1 | -1.54 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 381, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 1394 | 191 | 1.2252 | 1.8393 | 0.5497 | `candidate_recovery_or_relax` |
| `chosen_action` | `WAIT_REQUOTE` | 263 | 150 | 1.5245 | 2.5596 | 0.5733 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 2029 | 146 | 1.5618 | 2.624 | 0.5685 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 1146 | 144 | 0.8462 | 1.1306 | 0.5556 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh_or_unflagged` | 338 | 74 | 2.1525 | 3.5689 | 0.6216 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 74 | 74 | 2.1525 | 3.5689 | 0.6216 | `candidate_recovery_or_relax` |
| `strength_bucket` | `strong_strength_momentum` | 156 | 59 | 1.9573 | 3.3126 | 0.6271 | `hold_no_edge` |
| `score_band` | `score_70p` | 338 | 55 | 0.9016 | 1.2758 | 0.5273 | `source_quality_workorder` |
| `chosen_action` | `NO_BUY_AI` | 1379 | 42 | 0.1457 | -0.7526 | 0.4762 | `hold_no_edge` |
| `time_bucket` | `time_1200_1400` | 358 | 40 | 1.4226 | 3.2735 | 0.65 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_1000_1200` | 349 | 39 | 1.3392 | 1.8295 | 0.5385 | `hold_sample` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 651 | 35 | -0.0689 | -0.8091 | 0.5143 | `source_quality_workorder` |
| `strength_bucket` | `weak_strength_momentum` | 575 | 34 | 0.3047 | -0.15 | 0.4706 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 29 | 29 | 0.5767 | 0.8949 | 0.4483 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_trailing_take_profit` | 25 | 25 | -0.4273 | 2.1236 | 1.0 | `hold_sample` |
| `overbought_bucket` | `overbought_ok` | 159 | 23 | 3.579 | 6.6107 | 0.6957 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 21 | 21 | 0.7008 | 0.9448 | 0.4286 | `hold_sample` |
| `stale_bucket` | `fresh` | 228 | 19 | 0.2489 | -1.7358 | 0.3684 | `hold_sample` |
| `score_band` | `score_63_65` | 98 | 19 | 2.203 | 3.0966 | 0.6842 | `hold_sample` |
| `score_band` | `score_66_69` | 50 | 17 | 3.5676 | 7.1021 | 0.8235 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 12 | 12 | 0.6964 | 0.8433 | 0.6667 | `candidate_recovery_or_relax` |

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
| `actual_order_submitted` | `false` | 455 | 148 | -0.5489 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 423 | 148 | -0.5489 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 423 | 148 | -0.5489 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 423 | 148 | -0.5489 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 423 | 148 | -0.5489 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 423 | 148 | -0.5489 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 423 | 148 | -0.5489 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 423 | 148 | -0.5489 | `keep_collecting` |
| `latency_state` | `simulated` | 423 | 148 | -0.5489 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 455 | 148 | -0.5489 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 423 | 148 | -0.5489 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 382 | 132 | -0.5806 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 622 | 131 | -0.6353 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 318 | 100 | -0.6526 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 282 | 98 | -0.2209 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 282 | 98 | -0.2209 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 263 | 88 | -0.2714 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 280 | 88 | -0.2714 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 263 | 88 | -0.2714 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 160 | 60 | -0.956 | `source_quality_workorder` |
| `liquidity_bucket` | `below_min_liquidity` | 145 | 50 | -1.1919 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 141 | 50 | -1.1919 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 141 | 50 | -1.1919 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 108 | 48 | -0.3329 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 112 | 48 | -0.9337 | `keep_collecting` |
| `would_limit_fill` | `true` | 128 | 48 | -0.1624 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 139 | 45 | -1.4654 | `keep_collecting` |
| `would_limit_fill` | `false` | 371 | 40 | -0.4021 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 111 | 28 | -0.5059 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 68 | 27 | -1.6952 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 81 | 25 | -0.3181 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 47 | 23 | 0.0069 | `source_quality_workorder` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 21 | 15 | 0.5721 | `keep_collecting` |
| `revalidation_state` | `warning_stale_context_or_quote` | 30 | 15 | 0.3634 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 37 | 13 | -0.5183 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 24 | 12 | -0.16 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 19 | 10 | 0.2234 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_10s_plus` | 38 | 7 | -0.5149 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 11 | 7 | 0.8833 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 22 | 6 | -0.7502 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 40, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 423 | 148 | -0.8875 | `hold_no_edge` |
| `holding_source_stage` | `scalp_sim_holding_started` | 423 | 148 | -0.8875 | `hold_no_edge` |
| `holding_action` | `WAIT` | 395 | 135 | -0.9839 | `hold_no_edge` |
| `profit_band` | `profit_lt_neg070` | 84 | 76 | -2.092 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 71 | 71 | -2.1076 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 29 | 26 | 0.0672 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300` | 24 | 24 | 0.8333 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 23 | 23 | -0.028 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 21 | 21 | 0.7234 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 18 | 12 | -0.2275 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 12 | 12 | -0.2275 | `hold_no_edge` |
| `holding_action` | `holding_action_not_applicable_at_start` | 23 | 11 | 0.4351 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 8 | 8 | 1.0443 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 6 | 6 | 0.7891 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 3 | 3 | -2.011 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 3 | 3 | 0.7968 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 3 | 3 | 1.6029 | `candidate_recovery_or_relax` |
| `holding_action` | `BUY` | 5 | 2 | -1.6583 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 3 | 2 | 0.13 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 2 | 2 | -1.6583 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 2 | 2 | 0.13 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 2 | 2 | 1.8099 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 18 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 4 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 11 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 275 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 18 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 260 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 12 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_020_180s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_180_600s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_020_180s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 5 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos080_pos150|held=held_600_1800s_plus` | 3 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 61, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 234 | 234 | -0.9578 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 234 | 234 | -0.9578 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 234 | 234 | -0.9578 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 223 | 223 | -1.4763 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 159 | 159 | -1.255 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 109 | 109 | -0.9088 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 77 | 77 | -0.4647 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 65 | 65 | -0.5162 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 43 | 43 | -1.3479 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 42 | 42 | 0.5403 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_soft_stop_pct` | 40 | 40 | -1.9587 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 38 | 38 | -0.6391 | `candidate_recovery_or_relax` |
| `exit_outcome` | `NEUTRAL` | 28 | 28 | -0.6006 | `hold_no_edge` |
| `profit_band` | `profit_pos080_pos150` | 27 | 27 | 0.32 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300` | 19 | 19 | 0.643 | `candidate_recovery_or_relax` |
| `exit_outcome` | `outcome_unknown` | 14197 | 18 | -0.4358 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 18 | 18 | -0.4358 | `hold_no_edge` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 18 | 18 | -0.4358 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 18 | 18 | -1.6066 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 14 | 14 | -2.5802 | `hold_sample` |
| `exit_rule` | `scalp_hard_stop_pct` | 11 | 11 | -3.1296 | `candidate_tighten_or_exclude` |
| `exit_rule` | `daily_limit_up_immediate_exit` | 10 | 10 | -0.5304 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 10 | 10 | -0.7102 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 9 | 9 | 1.4094 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 8 | 8 | -1.1409 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 8 | 8 | -1.6636 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 6 | 6 | 0.0729 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 6 | 6 | -0.2037 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=daily_limit_up_immediate_exit|outcome=NEUTRAL|profit=profit_neg070_neg010` | 6 | 6 | -0.1683 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 6 | 6 | -2.7374 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 6 | 6 | 0.2502 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 6 | 6 | 1.1608 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` | 5 | 5 | 1.084 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 5 | 5 | 0.6224 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 5 | 5 | 1.8062 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300` | 5 | 5 | 0.5878 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 4 | 4 | -0.7436 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 4 | 4 | 0.045 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos080_pos150` | 3 | 3 | 0.8325 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 3 | 3 | -3.9978 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 399, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_source` | `score_field_backfilled` | 16705 | 16702 | None | -0.8166 | 0.1459 | `hold_sample` |
| `arm` | `AVG_DOWN` | 15321 | 15207 | None | -1.0548 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 15148 | 15034 | None | -1.0286 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_70p` | 8060 | 8060 | None | -0.8415 | 0.1613 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 4205 | 4205 | None | -0.7945 | 0.1424 | `hold_sample` |
| `arm` | `PYRAMID` | 2699 | 2667 | None | 0.5515 | 0.9793 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 2699 | 2667 | None | 0.5515 | 0.9793 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 2445 | 2445 | None | 0.4696 | 0.9775 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2313 | 2313 | None | -1.0278 | 0.0826 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 2134 | 2133 | None | -0.898 | 0.1037 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 1914 | 1912 | None | -0.7467 | 0.1391 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 1557 | 1557 | None | -0.7116 | 0.14 | `hold_sample` |
| `ai_score_source` | `live` | 924 | 924 | None | -0.7833 | 0.1504 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 913 | 913 | None | -1.0165 | 0.057 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.23)` | 544 | 544 | None | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 443 | 443 | None | -0.8561 | 0.1422 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.54)` | 408 | 408 | None | -0.54 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 247 | 247 | None | -0.7797 | 0.0729 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 229 | 229 | None | -0.9303 | 0.1048 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.89)` | 227 | 227 | None | -0.89 | 0.0 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 30, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 36 | 18 | -0.4358 | -0.5811 | 0.2222 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 18 | 18 | -0.4358 | -0.5811 | 0.2222 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 36 | 18 | -0.4358 | -0.5811 | 0.2222 | `hold_sample` |
| `stage` | `exit` | 18 | 18 | -0.4358 | -0.5811 | 0.2222 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 36 | 18 | -0.4358 | -0.5811 | 0.2222 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 18 | 18 | -0.4358 | -0.5811 | 0.2222 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 32 | 16 | -0.4688 | -0.625 | 0.25 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 28 | 14 | -0.7393 | -0.9857 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 22 | 11 | -0.0777 | -0.1036 | 0.3636 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 8 | 8 | -1.1409 | -1.5213 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 16 | 8 | -1.1409 | -1.5213 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 6 | 6 | -0.2037 | -0.2717 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 12 | 6 | -0.2037 | -0.2717 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 8 | 4 | -1.3519 | -1.8025 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 3 | 3 | 0.8325 | 1.11 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 6 | 3 | 0.8325 | 1.11 | 1.0 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 6 | 3 | 0.8325 | 1.11 | 1.0 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 4 | 2 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 4 | 2 | -0.3975 | -0.53 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 1 | 1 | 0.0075 | 0.01 | 1.0 | `hold_sample` |

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
