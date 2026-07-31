# Lifecycle Decision Matrix - 2026-07-31

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-31_mtd`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `17411`
- source_rows_total: `30838`
- retained_rows: `17411`
- dropped_rows_by_source: `{}`
- joined_rows: `7147`
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
- lifecycle_flow_bucket_count: `265`
- lifecycle_flow_complete_count: `128`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0094`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 4027 | 71 | -0.2927 | 0.0436 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 879 | 111 | -0.4114 | 0.4551 | `pass` | `NO_CHANGE` | False |
| `holding` | 321 | 111 | -1.1387 | 0.6629 | `pass` | `EXIT` | False |
| `scale_in` | 6698 | 6582 | -0.8401 | 0.9991 | `pass` | `NO_CHANGE` | False |
| `exit` | 5486 | 272 | -0.9477 | 0.3841 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 265, 'complete_flow_count': 128, 'incomplete_flow_count': 13511, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 5894 | 5799 | -1.0318 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 732 | 711 | 0.732 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 55 | 55 | -1.0052 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:ac760bc3a4` | 16 | 16 | -0.8625 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 9 | 9 | -0.1104 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:62b3401904` | 8 | 8 | -0.1725 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 6 | 6 | 0.341 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:8858a17062` | 5 | 5 | -1.04 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 5 | 5 | -0.672 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:35ce26a91c` | 4 | 4 | -1.14 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 4 | 4 | -1.3575 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 3 | 3 | -1.6518 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:964bbee510` | 3 | 3 | -0.8233 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 3 | 3 | -0.6967 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:19270f18a8` | 3 | 3 | -0.1725 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:15c17a2405` | 2 | 2 | -2.7967 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:73753e9274` | 2 | 2 | -1.265 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:ad0146c320` | 2 | 2 | -1.8569 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:d65aac5eca` | 2 | 2 | -0.62 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:a5ddbd8b87` | 2 | 2 | -0.835 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 377, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 1618 | 54 | -0.1126 | -1.3142 | 0.3333 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 2983 | 51 | -0.1885 | -1.4006 | 0.3725 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 1466 | 48 | 0.0088 | -1.3159 | 0.3333 | `hold_sample` |
| `chosen_action` | `NO_BUY_AI` | 2179 | 42 | -0.0031 | -1.4891 | 0.3095 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 1302 | 32 | 0.1902 | -1.5147 | 0.2813 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 1260 | 29 | -0.4133 | -0.9609 | 0.3793 | `hold_sample` |
| `stale_bucket` | `stale_high` | 1026 | 28 | -0.0966 | -1.1354 | 0.3929 | `hold_sample` |
| `time_bucket` | `time_0900_1000` | 820 | 25 | 0.1852 | -1.0241 | 0.32 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 24 | 24 | -0.0893 | -3.5713 | 0.0 | `hold_sample` |
| `score_band` | `score_60_62` | 655 | 24 | -0.1985 | -1.5513 | 0.2917 | `hold_sample` |
| `strength_bucket` | `neutral_strength_momentum` | 1855 | 23 | -0.8205 | -0.9558 | 0.4783 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 21 | 21 | -0.491 | 1.5448 | 0.9524 | `hold_sample` |
| `score_band` | `score_70p` | 365 | 17 | -0.5397 | -0.7379 | 0.5882 | `hold_sample` |
| `score_band` | `score_lt60` | 2831 | 17 | 0.1986 | -0.6606 | 0.4706 | `hold_sample` |
| `chosen_action` | `WAIT_REQUOTE` | 1337 | 16 | -0.7111 | -0.5559 | 0.5 | `hold_sample` |
| `stale_bucket` | `fresh` | 861 | 16 | -0.1897 | -2.3013 | 0.1875 | `hold_sample` |
| `liquidity_bucket` | `liquidity_not_available` | 2179 | 16 | -0.8924 | -1.1581 | 0.4375 | `hold_sample` |
| `overbought_bucket` | `overbought_not_available` | 1926 | 16 | -0.8924 | -1.1581 | 0.4375 | `hold_sample` |
| `exit_rule` | `exit_unknown` | 3969 | 13 | -0.49 | -0.7333 | 0.3846 | `hold_sample` |
| `stale_bucket` | `fresh_or_unflagged` | 185 | 13 | -0.49 | -0.7333 | 0.3846 | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 140, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 686 | 111 | -0.4114 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 830 | 111 | -0.4114 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 297 | 111 | -0.4114 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 297 | 111 | -0.4114 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 297 | 111 | -0.4114 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 297 | 111 | -0.4114 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 297 | 111 | -0.4114 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 297 | 111 | -0.4114 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 297 | 111 | -0.4114 | `keep_collecting` |
| `latency_state` | `simulated` | 297 | 111 | -0.4114 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 686 | 111 | -0.4114 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 294 | 108 | -0.3147 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 287 | 106 | -0.4498 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 254 | 83 | -0.3011 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 196 | 67 | -0.1925 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 195 | 67 | -0.1925 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 573 | 67 | -0.1925 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 195 | 67 | -0.1925 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 196 | 67 | -0.1925 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 101 | 44 | -0.7449 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 101 | 44 | -0.7449 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 101 | 44 | -0.7449 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 101 | 44 | -0.7449 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 102 | 44 | -0.7449 | `source_quality_workorder` |
| `would_limit_fill` | `false` | 687 | 37 | -0.069 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 95 | 30 | 0.0387 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 90 | 30 | -0.3448 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 40 | 25 | -0.36 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 94 | 22 | -1.0785 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_10s_plus` | 63 | 20 | -0.7674 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 74 | 20 | -0.1211 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 34 | 17 | -0.7627 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 50 | 16 | -0.6729 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 16 | 10 | -0.7922 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 10 | 7 | -0.5307 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 9 | 4 | 0.3807 | `keep_collecting` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 3 | 3 | -3.8922 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 5 | 3 | -0.7689 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 7 | 3 | -0.4527 | `source_quality_workorder` |
| `overbought_guard_action` | `would_block` | 3 | 3 | -3.8922 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 38, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 297 | 111 | -1.1387 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 297 | 111 | -1.1387 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 287 | 106 | -1.1712 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 77 | 72 | -1.891 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 70 | 70 | -1.9095 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 15 | 13 | -0.0365 | `hold_no_edge` |
| `profit_band` | `profit_pos080_pos150` | 12 | 11 | -0.0685 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 11 | 11 | -0.1033 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 10 | 10 | -0.0327 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 7 | 7 | 0.5147 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 7 | 7 | 0.5147 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 5 | 5 | 1.7127 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 5 | 5 | 1.7127 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 19 | 3 | -0.395 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 3 | 3 | -0.395 | `hold_sample` |
| `holding_action` | `BUY` | 2 | 2 | -0.1101 | `hold_sample` |
| `holding_action` | `holding_action_not_applicable_at_start` | 5 | 2 | -1.2424 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 2 | 2 | -1.2424 | `hold_sample` |
| `holding_action` | `DROP` | 3 | 1 | 0.4555 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 0.2066 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | -0.4267 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=DROP|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 0.4555 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 24 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 7 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 15 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 186 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 24 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=DROP|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 181 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_180_600s` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 6 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 8 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos080_pos150|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 64, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 176 | 176 | -1.4394 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 150 | 150 | -0.8889 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 150 | 150 | -0.8889 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 150 | 150 | -0.8889 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 106 | 106 | -1.1471 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 98 | 98 | -1.2046 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 53 | 53 | -0.4541 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 47 | 47 | -1.8818 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 41 | 41 | -0.8749 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 37 | 37 | -0.5619 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 35 | 35 | -1.5795 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 32 | 32 | 0.3704 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 24 | 24 | -0.2666 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 24 | 24 | -0.2666 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 22 | 22 | -1.2226 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 18 | 18 | 0.0389 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 18 | 18 | -2.3488 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 17 | 17 | -1.4442 | `hold_sample` |
| `exit_outcome` | `outcome_unknown` | 3986 | 15 | -0.323 | `source_quality_workorder` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 12 | 12 | -0.8619 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 12 | 12 | -1.8014 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 11 | 11 | -0.0976 | `hold_no_edge` |
| `exit_outcome` | `COMPLETED` | 9 | 9 | -0.1725 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 9 | 9 | -0.1725 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 8 | 8 | -0.8621 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 7 | 7 | 0.5147 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 7 | 7 | 2.3404 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_hard_stop_pct` | 6 | 6 | -4.6866 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 6 | 6 | -0.19 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 6 | 6 | -0.2929 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 5 | 5 | -0.966 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 5 | 5 | 0.246 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 5 | 5 | 0.1896 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 4 | 4 | 1.302 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 4 | 4 | 1.0808 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 3 | 3 | 0.055 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 3 | 3 | -4.0827 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 3 | 3 | -0.6788 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 3 | 3 | -0.3234 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 3 | 3 | -0.2673 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 443, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 6237 | 6220 | None | -1.0226 | 0.0867 | `hold_sample` |
| `arm` | `AVG_DOWN` | 5960 | 5865 | None | -1.191 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 5882 | 5787 | None | -1.1634 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 3533 | 3533 | None | -1.0728 | 0.1002 | `hold_sample` |
| `price_guard_reason` | `price_guard_none` | 3553 | 3506 | None | -0.8645 | 0.1022 | `hold_sample` |
| `qty_reason` | `qty_none` | 3509 | 3506 | None | -0.8645 | 0.1022 | `hold_sample` |
| `time_bucket` | `time_unknown` | 3556 | 3506 | None | -0.8645 | 0.1022 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 3292 | 3242 | None | -0.8503 | 0.1105 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 2865 | 2865 | None | -1.1012 | 0.0 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 2171 | 2171 | None | -0.9024 | 0.1156 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 2017 | 2017 | None | -1.3714 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 1599 | 1599 | None | -1.0156 | 0.0982 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 1249 | 1249 | None | -0.9547 | 0.1033 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 1071 | 1071 | None | -0.4239 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 738 | 717 | None | 0.7113 | 0.9902 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 738 | 717 | None | 0.7113 | 0.9902 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 705 | 705 | None | -0.4541 | 0.4184 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 700 | 700 | None | -0.8168 | 0.1114 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 682 | 663 | None | -0.8657 | 0.0997 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 448 | 448 | None | 0.372 | 0.9911 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 32, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 48 | 24 | -0.2666 | -0.3554 | 0.125 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 24 | 24 | -0.2666 | -0.3554 | 0.125 | `hold_sample` |
| `stage` | `exit` | 24 | 24 | -0.2666 | -0.3554 | 0.125 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 48 | 24 | -0.2666 | -0.3554 | 0.125 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 24 | 24 | -0.2666 | -0.3554 | 0.125 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 46 | 23 | -0.2283 | -0.3043 | 0.1304 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 42 | 21 | -0.3618 | -0.4824 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 16 | 16 | -0.173 | -0.2306 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 32 | 16 | -0.173 | -0.2306 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 30 | 15 | -0.264 | -0.352 | 0.2 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 26 | 13 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 22 | 11 | -0.3778 | -0.5036 | 0.2727 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 14 | 7 | -0.2989 | -0.3986 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 10 | 5 | -0.966 | -1.288 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 4 | 4 | -0.9206 | -1.2275 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 2 | 2 | 0.12 | 0.16 | 1.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 4 | 2 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 4 | 2 | 0.12 | 0.16 | 1.0 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 4 | 2 | 0.12 | 0.16 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 1 | 1 | 0.96 | 1.28 | 1.0 | `hold_sample` |

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
