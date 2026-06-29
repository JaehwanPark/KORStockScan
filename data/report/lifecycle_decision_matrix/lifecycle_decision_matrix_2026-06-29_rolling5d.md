# Lifecycle Decision Matrix - 2026-06-29

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-29_rolling5d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `20825`
- source_rows_total: `26469`
- retained_rows: `20825`
- dropped_rows_by_source: `{}`
- joined_rows: `11994`
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
- lifecycle_flow_bucket_count: `152`
- lifecycle_flow_complete_count: `88`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0047`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 1999 | 221 | 0.5891 | 0.8525 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 246 | 168 | -0.6001 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 225 | 168 | -0.9654 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 11383 | 11133 | -0.5134 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 6972 | 304 | -0.9218 | 0.6828 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 152, 'complete_flow_count': 88, 'incomplete_flow_count': 18665, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 8668 | 8614 | -0.9027 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 2578 | 2382 | 0.9104 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 110 | 110 | -0.9926 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 71 | 71 | 0.8489 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 51 | 51 | 1.6985 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 12 | 12 | -0.4583 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 9 | 9 | 2.8458 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 5 | 5 | -0.738 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:c1801bf4e3` | 4 | 4 | -2.1825 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:89e49a11bc` | 3 | 3 | -1.2664 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:67138f9e63` | 3 | 3 | -1.0287 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 3 | 3 | -0.8433 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9d8cac316e` | 2 | 2 | -0.9575 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:f1afdbf31e` | 2 | 2 | -2.3266 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:4badedabe9` | 2 | 2 | -0.7389 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:2089125172` | 2 | 2 | -1.0394 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:aee8bb0d09` | 2 | 2 | -0.875 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:05b084aa57` | 2 | 2 | -0.5084 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:f68b1eee89` | 1 | 1 | -0.0802 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:acadf41d1b` | 1 | 1 | -1.1508 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 309, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 1658 | 221 | 0.5891 | 0.7147 | 0.4163 | `candidate_tighten_or_exclude` |
| `overbought_bucket` | `overbought_normal` | 1382 | 162 | 0.7738 | 0.8115 | 0.4321 | `candidate_tighten_or_exclude` |
| `chosen_action` | `WAIT_REQUOTE` | 131 | 131 | 1.3169 | 2.1429 | 0.5649 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 1909 | 131 | 1.3169 | 2.1429 | 0.5649 | `hold_sample` |
| `chosen_action` | `NO_BUY_AI` | 1648 | 85 | -0.5099 | -1.3206 | 0.2117 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 826 | 75 | -0.6238 | -1.6235 | 0.1333 | `candidate_tighten_or_exclude` |
| `strength_bucket` | `weak_strength_momentum` | 675 | 63 | 0.1528 | -0.7033 | 0.2381 | `candidate_tighten_or_exclude` |
| `stale_bucket` | `fresh_or_unflagged` | 186 | 59 | 1.759 | 2.7409 | 0.6271 | `hold_sample` |
| `strength_bucket` | `strong_strength_momentum` | 226 | 59 | 1.0574 | 1.6937 | 0.5085 | `hold_sample` |
| `source_stage` | `wait6579_ev_cohort` | 59 | 59 | 1.759 | 2.7409 | 0.6271 | `candidate_recovery_or_relax` |
| `score_band` | `score_60_62` | 716 | 53 | -0.7092 | -1.4807 | 0.1698 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 48 | 48 | -0.3514 | -2.0842 | 0.0 | `candidate_tighten_or_exclude` |
| `time_bucket` | `time_0900_1000` | 413 | 45 | -0.2484 | -1.3908 | 0.1556 | `hold_no_edge` |
| `stale_bucket` | `stale_high` | 598 | 41 | -0.7369 | -1.3978 | 0.1707 | `candidate_tighten_or_exclude` |
| `overbought_bucket` | `overbought_watch` | 343 | 40 | -0.3056 | -0.2913 | 0.35 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 254 | 40 | 1.4155 | 1.8545 | 0.5 | `hold_sample` |
| `stale_bucket` | `fresh` | 326 | 34 | -0.4874 | -1.8956 | 0.0882 | `candidate_tighten_or_exclude` |
| `score_band` | `score_70p` | 113 | 31 | 0.2478 | -0.1019 | 0.3548 | `hold_sample` |
| `time_bucket` | `time_1200_1400` | 236 | 31 | 0.4526 | 1.2742 | 0.4839 | `candidate_tighten_or_exclude` |
| `score_band` | `score_66_69` | 75 | 29 | 2.1641 | 3.2987 | 0.6897 | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 95, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 230 | 168 | -0.6001 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 213 | 168 | -0.6001 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 213 | 168 | -0.6001 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 213 | 168 | -0.6001 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 213 | 168 | -0.6001 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 213 | 168 | -0.6001 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 213 | 168 | -0.6001 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 213 | 168 | -0.6001 | `keep_collecting` |
| `latency_state` | `simulated` | 213 | 168 | -0.6001 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 230 | 168 | -0.6001 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 212 | 167 | -0.5762 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 204 | 161 | -0.5946 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 195 | 151 | -0.5659 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 184 | 149 | -0.6268 | `source_quality_workorder` |
| `revalidation_state` | `warning_stale_context_or_quote` | 189 | 147 | -0.6557 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 170 | 140 | -0.6315 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 140 | 111 | -0.5482 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 140 | 111 | -0.5482 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 131 | 109 | -0.5992 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 110 | 91 | -0.5366 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 78 | 65 | -0.4692 | `source_quality_workorder` |
| `liquidity_bucket` | `below_min_liquidity` | 79 | 57 | -0.7012 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 73 | 57 | -0.7012 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 73 | 57 | -0.7012 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 42 | 37 | -0.82 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_10s_plus` | 40 | 30 | -0.6638 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 57 | 21 | -0.211 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 29 | 19 | -0.391 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 29 | 19 | -0.391 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 29 | 19 | -0.391 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 20 | 16 | -0.6731 | `keep_collecting` |
| `would_limit_fill` | `false` | 56 | 14 | -0.5306 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 18 | 13 | -0.6398 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 13 | 12 | -0.6344 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_1_3s` | 37 | 10 | -0.8167 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 19 | 10 | -0.3415 | `source_quality_workorder` |
| `price_resolution_bucket` | `defensive_order_price` | 13 | 9 | -0.5533 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 8 | 6 | -0.9054 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 7 | 5 | -1.1916 | `keep_collecting` |
| `would_limit_fill` | `true` | 6 | 5 | 0.0 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 35, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 213 | 168 | -0.9654 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 213 | 168 | -0.9654 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 198 | 155 | -0.9937 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 123 | 118 | -1.5492 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 108 | 108 | -1.5359 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 18 | 14 | -0.6872 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 14 | 14 | -0.6872 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 14 | 12 | 0.023 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 12 | 12 | 0.7262 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 12 | 12 | 0.023 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 12 | 12 | 0.7262 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300_plus` | 11 | 10 | 2.0994 | `hold_sample` |
| `holding_action` | `holding_action_not_applicable_at_start` | 10 | 8 | -1.1491 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 7 | 7 | 1.748 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 7 | 7 | -1.6088 | `candidate_tighten_or_exclude` |
| `holding_action` | `BUY` | 5 | 5 | 0.2057 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 3 | 3 | -1.8869 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 2 | 2 | 0.1258 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 2 | 2 | 3.3445 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 2 | 2 | 0.1258 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 2.0684 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 12 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 10 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 45 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 12 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 43 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_180_600s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos080_pos150|held=held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos150_pos300_plus|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 58, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 215 | 215 | -1.3392 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 157 | 157 | -1.0105 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 135 | 135 | -0.9124 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 135 | 135 | -0.9124 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 135 | 135 | -0.9124 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 96 | 96 | -1.1088 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 73 | 73 | -1.2868 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 70 | 70 | -1.5133 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 51 | 51 | -0.7391 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 48 | 48 | -0.5937 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 42 | 42 | -1.9869 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 36 | 36 | -0.4171 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 35 | 35 | -0.556 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 33 | 33 | -1.7957 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 26 | 26 | 0.9751 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 22 | 22 | -1.071 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 21 | 21 | -2.6231 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 17 | 17 | -0.6539 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 15 | 15 | 0.1694 | `candidate_tighten_or_exclude` |
| `exit_rule` | `daily_limit_up_immediate_exit` | 14 | 14 | -0.4858 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 6680 | 12 | 0.1331 | `source_quality_workorder` |
| `profit_band` | `profit_pos150_pos300` | 12 | 12 | 0.7262 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 12 | 12 | 0.1331 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 12 | 12 | 0.1331 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 12 | 12 | -1.2035 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300_plus` | 11 | 11 | 2.2534 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=daily_limit_up_immediate_exit|outcome=NEUTRAL|profit=profit_neg070_neg010` | 9 | 9 | -0.9177 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 9 | 9 | -1.5469 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 6 | 6 | 0.6932 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 6 | 6 | 1.473 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 5 | 5 | -0.8205 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 4 | 4 | -0.195 | `source_quality_workorder` |
| `profit_band` | `profit_neg010_pos080` | 3 | 3 | 0.0605 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` | 3 | 3 | 0.9367 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 3 | 3 | 1.0305 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300` | 3 | 3 | 0.6398 | `hold_sample` |
| `exit_rule` | `scalp_ai_momentum_decay` | 2 | 2 | 0.0958 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos080_pos150` | 2 | 2 | 0.8175 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=daily_limit_up_immediate_exit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 2 | 2 | -0.4736 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 2 | 2 | -3.061 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 432, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_source` | `score_field_backfilled` | 11126 | 11126 | None | -0.5654 | 0.2076 | `hold_sample` |
| `arm` | `AVG_DOWN` | 8791 | 8737 | None | -0.953 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 7461 | 7407 | None | -1.04 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_70p` | 6732 | 6732 | None | -0.5199 | 0.2366 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 2619 | 2619 | None | -0.6886 | 0.1615 | `hold_sample` |
| `arm` | `PYRAMID` | 2592 | 2396 | None | 0.8507 | 0.9661 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 2592 | 2396 | None | 0.8507 | 0.9661 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2313 | 2313 | None | -1.0278 | 0.0826 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 1968 | 1968 | None | 0.5682 | 0.9939 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 1330 | 1330 | None | -0.4688 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 913 | 913 | None | -1.0165 | 0.057 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 847 | 847 | None | -0.6039 | 0.1476 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 540 | 540 | None | -0.645 | 0.1537 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 443 | 443 | None | -0.8561 | 0.1422 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 388 | 388 | None | -0.3276 | 0.2217 | `hold_sample` |
| `blocker_reason` | `add_judgment_locked` | 360 | 360 | None | -0.6426 | 0.0305 | `hold_sample` |
| `blocker_reason` | `scalping_buy_window_blocked` | 238 | 238 | None | -0.3743 | 0.0378 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.97)` | 226 | 226 | None | -0.97 | 0.0 | `hold_sample` |
| `blocker_reason` | `low_broken` | 215 | 215 | None | -0.4036 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalping_pyramid_ok` | 209 | 209 | None | 3.1452 | 1.0 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 29, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 24 | 12 | 0.1331 | 0.1775 | 0.25 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 12 | 12 | 0.1331 | 0.1775 | 0.25 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 24 | 12 | 0.1331 | 0.1775 | 0.25 | `hold_sample` |
| `stage` | `exit` | 12 | 12 | 0.1331 | 0.1775 | 0.25 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 24 | 12 | 0.1331 | 0.1775 | 0.25 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 12 | 12 | 0.1331 | 0.1775 | 0.25 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 22 | 11 | 0.1609 | 0.2146 | 0.2727 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 20 | 10 | 0.24 | 0.32 | 0.3 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 18 | 9 | -0.5425 | -0.7233 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 5 | 5 | -0.8205 | -1.094 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 10 | 5 | -0.8205 | -1.094 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 4 | 4 | -0.195 | -0.26 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 8 | 4 | -0.195 | -0.26 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 2 | 2 | 0.8175 | 1.09 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 4 | 2 | 0.8175 | 1.09 | 1.0 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 4 | 2 | 0.8175 | 1.09 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos150_pos300_plus` | 1 | 1 | 4.845 | 6.46 | 1.0 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 2 | 1 | -0.24 | -0.32 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 2 | 1 | -0.5625 | -0.75 | 0.0 | `hold_sample` |

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
