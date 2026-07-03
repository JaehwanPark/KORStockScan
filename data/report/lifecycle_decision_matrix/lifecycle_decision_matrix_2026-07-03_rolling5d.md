# Lifecycle Decision Matrix - 2026-07-03

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-03_rolling5d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `32685`
- source_rows_total: `61005`
- retained_rows: `32685`
- dropped_rows_by_source: `{}`
- joined_rows: `17563`
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
- lifecycle_flow_bucket_count: `207`
- lifecycle_flow_complete_count: `56`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0018`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 1834 | 182 | 1.2061 | 0.5873 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 556 | 129 | -0.4888 | 0.68 | `pass` | `NO_CHANGE` | False |
| `holding` | 367 | 129 | -0.821 | 0.8259 | `pass` | `EXIT` | False |
| `scale_in` | 16949 | 16818 | -0.745 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 12979 | 305 | -0.8705 | 0.1585 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 207, 'complete_flow_count': 56, 'incomplete_flow_count': 30588, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 14245 | 14144 | -0.9797 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 2509 | 2479 | 0.5973 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 166 | 166 | -1.0178 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 84 | 84 | 1.1875 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 38 | 38 | 2.1431 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 16 | 16 | 2.4863 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 14 | 14 | 0.0453 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 6 | 6 | -1.2167 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:4874ec99fd` | 3 | 3 | -2.057 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:224eb1ba18` | 3 | 3 | -2.1539 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 3 | 3 | -0.8333 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:2e5e6a8919` | 3 | 3 | -1.3825 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 3 | 3 | -0.8367 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:a4de6797c9` | 11 | 2 | 0.415 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:df02034b40` | 11 | 2 | -1.24 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b4078edac9` | 2 | 2 | -2.7691 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:7d1a415bd0` | 2 | 2 | 0.8157 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:aee8bb0d09` | 2 | 2 | -0.795 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:c7dbb66715` | 2 | 1 | -1.54 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:dfd7c31acb` | 1 | 1 | -1.5916 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 364, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 1248 | 177 | 1.2626 | 1.9565 | 0.5649 | `candidate_recovery_or_relax` |
| `chosen_action` | `WAIT_REQUOTE` | 237 | 142 | 1.5607 | 2.6309 | 0.5845 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 1790 | 138 | 1.6012 | 2.7011 | 0.5797 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 1028 | 131 | 0.8443 | 1.1944 | 0.5725 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh_or_unflagged` | 279 | 66 | 2.3066 | 3.8446 | 0.6515 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 66 | 66 | 2.3066 | 3.8446 | 0.6515 | `candidate_recovery_or_relax` |
| `strength_bucket` | `strong_strength_momentum` | 148 | 58 | 1.9942 | 3.3722 | 0.6379 | `hold_no_edge` |
| `score_band` | `score_70p` | 285 | 46 | 1.0087 | 1.6267 | 0.5652 | `source_quality_workorder` |
| `time_bucket` | `time_1200_1400` | 281 | 38 | 1.4655 | 3.416 | 0.6579 | `candidate_recovery_or_relax` |
| `chosen_action` | `NO_BUY_AI` | 1230 | 36 | 0.073 | -0.7292 | 0.5 | `hold_no_edge` |
| `time_bucket` | `time_1000_1200` | 300 | 33 | 1.378 | 1.8934 | 0.5758 | `hold_sample` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 523 | 29 | -0.2036 | -0.7917 | 0.5517 | `source_quality_workorder` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 28 | 28 | 0.6185 | 0.9549 | 0.4643 | `candidate_recovery_or_relax` |
| `strength_bucket` | `weak_strength_momentum` | 445 | 26 | 0.4275 | -0.0489 | 0.5385 | `hold_sample` |
| `overbought_bucket` | `overbought_ok` | 143 | 23 | 3.579 | 6.6107 | 0.6957 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_trailing_take_profit` | 23 | 23 | -0.4564 | 2.0587 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 19 | 19 | 0.7105 | 0.9848 | 0.421 | `hold_sample` |
| `score_band` | `score_63_65` | 94 | 18 | 2.3291 | 3.462 | 0.7222 | `hold_sample` |
| `score_band` | `score_66_69` | 49 | 16 | 3.3179 | 6.7845 | 0.8125 | `hold_sample` |
| `stale_bucket` | `fresh` | 194 | 15 | 0.158 | -2.0653 | 0.3333 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 10 | 10 | 0.9273 | 1.1505 | 0.8 | `candidate_recovery_or_relax` |

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
| `actual_order_submitted` | `false` | 377 | 129 | -0.4888 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 350 | 129 | -0.4888 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 350 | 129 | -0.4888 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 350 | 129 | -0.4888 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 350 | 129 | -0.4888 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 350 | 129 | -0.4888 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 350 | 129 | -0.4888 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 350 | 129 | -0.4888 | `keep_collecting` |
| `latency_state` | `simulated` | 350 | 129 | -0.4888 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 377 | 129 | -0.4888 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 350 | 129 | -0.4888 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 317 | 116 | -0.5183 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 519 | 112 | -0.5807 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 246 | 91 | -0.274 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 246 | 91 | -0.274 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 258 | 86 | -0.6037 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 227 | 81 | -0.3354 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 240 | 81 | -0.3354 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 227 | 81 | -0.3354 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 123 | 48 | -0.7475 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 110 | 45 | -0.1968 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 94 | 43 | -0.2589 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 94 | 41 | -0.6737 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 107 | 38 | -1.0031 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 104 | 38 | -1.0031 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 104 | 38 | -1.0031 | `keep_collecting` |
| `would_limit_fill` | `false` | 323 | 36 | -0.5086 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 103 | 33 | -1.3474 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 96 | 26 | -0.6375 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 45 | 23 | 0.0069 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 65 | 22 | -0.4099 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 57 | 21 | -1.4311 | `source_quality_workorder` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 20 | 15 | 0.5721 | `keep_collecting` |
| `revalidation_state` | `warning_stale_context_or_quote` | 30 | 15 | 0.3634 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 30 | 10 | -0.507 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 19 | 10 | 0.2234 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 21 | 10 | -0.1734 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 11 | 7 | 0.8833 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 6 | 6 | 0.0094 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 16 | 5 | -0.604 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 39, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 350 | 129 | -0.821 | `hold_no_edge` |
| `holding_source_stage` | `scalp_sim_holding_started` | 350 | 129 | -0.821 | `hold_no_edge` |
| `holding_action` | `WAIT` | 330 | 119 | -0.9031 | `hold_no_edge` |
| `profit_band` | `profit_lt_neg070` | 70 | 62 | -2.1343 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 58 | 58 | -2.17 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 27 | 24 | 0.0075 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300` | 22 | 22 | 0.9952 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 22 | 22 | -0.0436 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 19 | 19 | 0.8993 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 17 | 12 | -0.2275 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 12 | 12 | -0.2275 | `hold_no_edge` |
| `holding_action` | `holding_action_not_applicable_at_start` | 17 | 8 | 0.6087 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 7 | 7 | 0.9718 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 6 | 6 | 0.7891 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 3 | 3 | 1.6029 | `candidate_recovery_or_relax` |
| `holding_action` | `BUY` | 3 | 2 | -1.6583 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 3 | 2 | 0.13 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 2 | 2 | -1.6583 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 2 | 2 | 0.13 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 2 | 2 | -1.5735 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 0.57 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 2.0684 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 17 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 4 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 11 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 221 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 17 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 211 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 9 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_020_180s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_180_600s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 5 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos080_pos150|held=held_600_1800s_plus` | 3 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 55, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 197 | 197 | -0.9306 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 197 | 197 | -0.9306 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 197 | 197 | -0.9306 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 182 | 182 | -1.4667 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 131 | 131 | -1.2446 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 91 | 91 | -0.8186 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 67 | 67 | -0.4674 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 56 | 56 | -0.5225 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 38 | 38 | 0.5503 | `candidate_recovery_or_relax` |
| `exit_outcome` | `GOOD_EXIT` | 34 | 34 | -1.146 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 34 | 34 | -0.7574 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_soft_stop_pct` | 33 | 33 | -1.9159 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 25 | 25 | 0.2829 | `candidate_recovery_or_relax` |
| `exit_outcome` | `NEUTRAL` | 23 | 23 | -0.4254 | `hold_no_edge` |
| `exit_outcome` | `outcome_unknown` | 12691 | 17 | -0.4513 | `source_quality_workorder` |
| `profit_band` | `profit_pos150_pos300` | 17 | 17 | 0.8301 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 17 | 17 | -0.4513 | `hold_no_edge` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 17 | 17 | -0.4513 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 17 | 17 | -1.6548 | `hold_sample` |
| `exit_rule` | `scalp_hard_stop_pct` | 10 | 10 | -3.1539 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 9 | 9 | -2.6075 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 9 | 9 | -0.8242 | `hold_sample` |
| `exit_rule` | `daily_limit_up_immediate_exit` | 8 | 8 | 0.0065 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300_plus` | 8 | 8 | 1.3917 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 8 | 8 | -1.1409 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 7 | 7 | -1.6609 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 6 | 6 | 0.0729 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=daily_limit_up_immediate_exit|outcome=NEUTRAL|profit=profit_neg070_neg010` | 6 | 6 | -0.1683 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 6 | 6 | -2.7374 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 6 | 6 | 0.2502 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 5 | 5 | -0.21 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` | 5 | 5 | 1.084 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 5 | 5 | 0.6224 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 5 | 5 | 1.1429 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 5 | 5 | 1.8062 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 4 | 4 | 0.045 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300` | 4 | 4 | 1.0693 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos080_pos150` | 3 | 3 | 0.8325 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 3 | 3 | -3.9978 | `hold_sample` |
| `exit_rule` | `scalp_ai_momentum_decay` | 2 | 2 | -0.3491 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 377, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_source` | `score_field_backfilled` | 16511 | 16510 | None | -0.8154 | 0.147 | `hold_sample` |
| `arm` | `AVG_DOWN` | 14424 | 14323 | None | -1.0552 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 14259 | 14158 | None | -1.0287 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_70p` | 8060 | 8060 | None | -0.8415 | 0.1613 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 4201 | 4201 | None | -0.7957 | 0.1419 | `hold_sample` |
| `arm` | `PYRAMID` | 2525 | 2495 | None | 0.548 | 0.9787 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 2525 | 2495 | None | 0.548 | 0.9787 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 2318 | 2318 | None | 0.4728 | 0.9771 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2313 | 2313 | None | -1.0278 | 0.0826 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 1786 | 1786 | None | -0.8222 | 0.0957 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 1551 | 1551 | None | -0.7121 | 0.1386 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 1215 | 1214 | None | -0.8668 | 0.1269 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 913 | 913 | None | -1.0165 | 0.057 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.23)` | 506 | 506 | None | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 443 | 443 | None | -0.8561 | 0.1422 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.54)` | 398 | 398 | None | -0.54 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 302 | 302 | None | -0.9531 | 0.0331 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.68)` | 218 | 218 | None | -0.68 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 212 | 212 | None | -0.7519 | 0.0802 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.43)` | 206 | 206 | None | -0.43 | 0.0 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 34 | 17 | -0.4513 | -0.6018 | 0.2353 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 17 | 17 | -0.4513 | -0.6018 | 0.2353 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 34 | 17 | -0.4513 | -0.6018 | 0.2353 | `hold_sample` |
| `stage` | `exit` | 17 | 17 | -0.4513 | -0.6018 | 0.2353 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 34 | 17 | -0.4513 | -0.6018 | 0.2353 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 17 | 17 | -0.4513 | -0.6018 | 0.2353 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 32 | 16 | -0.4688 | -0.625 | 0.25 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 26 | 13 | -0.7829 | -1.0439 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 22 | 11 | -0.0777 | -0.1036 | 0.3636 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 8 | 8 | -1.1409 | -1.5213 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 16 | 8 | -1.1409 | -1.5213 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 5 | 5 | -0.21 | -0.28 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 10 | 5 | -0.21 | -0.28 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 8 | 4 | -1.3519 | -1.8025 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 3 | 3 | 0.8325 | 1.11 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 6 | 3 | 0.8325 | 1.11 | 1.0 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 6 | 3 | 0.8325 | 1.11 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 1 | 1 | 0.0075 | 0.01 | 1.0 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 2 | 1 | -0.6225 | -0.83 | 0.0 | `hold_sample` |

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
