# Lifecycle Decision Matrix - 2026-07-29

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-29_mtd`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `16117`
- source_rows_total: `28153`
- retained_rows: `16117`
- dropped_rows_by_source: `{}`
- joined_rows: `6643`
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
- lifecycle_flow_bucket_count: `246`
- lifecycle_flow_complete_count: `122`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0095`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 3389 | 66 | -0.2847 | 0.0465 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 828 | 106 | -0.4121 | 0.4748 | `pass` | `NO_CHANGE` | False |
| `holding` | 312 | 106 | -1.15 | 0.6872 | `pass` | `EXIT` | False |
| `scale_in` | 6213 | 6102 | -0.8358 | 0.999 | `pass` | `NO_CHANGE` | False |
| `exit` | 5375 | 263 | -0.9521 | 0.3897 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 246, 'complete_flow_count': 122, 'incomplete_flow_count': 12687, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 5455 | 5365 | -1.032 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 686 | 665 | 0.7566 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 55 | 55 | -1.0052 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:ac760bc3a4` | 16 | 16 | -0.8625 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 9 | 9 | -0.1104 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:62b3401904` | 7 | 7 | -0.1725 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
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
- summary: `{'bucket_count': 329, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 1379 | 53 | -0.1213 | -1.3407 | 0.3208 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 2613 | 50 | -0.1992 | -1.4304 | 0.36 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 1335 | 47 | 0.0016 | -1.3458 | 0.3191 | `hold_sample` |
| `chosen_action` | `NO_BUY_AI` | 1802 | 41 | -0.0117 | -1.5276 | 0.2927 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 1059 | 31 | 0.1852 | -1.5665 | 0.2581 | `hold_sample` |
| `stale_bucket` | `stale_high` | 1008 | 28 | -0.0966 | -1.1354 | 0.3929 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 1082 | 27 | -0.4439 | -0.9239 | 0.4074 | `hold_sample` |
| `score_band` | `score_60_62` | 653 | 24 | -0.1985 | -1.5513 | 0.2917 | `hold_sample` |
| `strength_bucket` | `neutral_strength_momentum` | 1604 | 23 | -0.8205 | -0.9558 | 0.4783 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 23 | 23 | -0.0459 | -3.5504 | 0.0 | `hold_sample` |
| `time_bucket` | `time_0900_1000` | 624 | 23 | 0.2406 | -1.1171 | 0.3043 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 19 | 19 | -0.4951 | 1.7026 | 1.0 | `hold_sample` |
| `score_band` | `score_70p` | 352 | 17 | -0.5397 | -0.7379 | 0.5882 | `hold_sample` |
| `chosen_action` | `WAIT_REQUOTE` | 1189 | 16 | -0.7111 | -0.5559 | 0.5 | `hold_sample` |
| `score_band` | `score_lt60` | 2307 | 16 | 0.1892 | -0.7075 | 0.4375 | `hold_sample` |
| `stale_bucket` | `fresh` | 564 | 15 | -0.2255 | -2.4607 | 0.1333 | `hold_sample` |
| `exit_rule` | `exit_unknown` | 3336 | 13 | -0.49 | -0.7333 | 0.3846 | `hold_sample` |
| `stale_bucket` | `fresh_or_unflagged` | 180 | 13 | -0.49 | -0.7333 | 0.3846 | `hold_sample` |
| `source_stage` | `wait6579_ev_cohort` | 13 | 13 | -0.49 | -0.7333 | 0.3846 | `hold_sample` |
| `liquidity_bucket` | `liquidity_not_available` | 1806 | 12 | -0.9951 | -0.9633 | 0.5833 | `hold_sample` |

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
| `actual_order_submitted` | `false` | 642 | 106 | -0.4121 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 780 | 106 | -0.4121 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 289 | 106 | -0.4121 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 289 | 106 | -0.4121 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 289 | 106 | -0.4121 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 289 | 106 | -0.4121 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 289 | 106 | -0.4121 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 289 | 106 | -0.4121 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 289 | 106 | -0.4121 | `keep_collecting` |
| `latency_state` | `simulated` | 289 | 106 | -0.4121 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 642 | 106 | -0.4121 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 286 | 103 | -0.3107 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 280 | 101 | -0.4524 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 253 | 82 | -0.309 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 190 | 64 | -0.2069 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 189 | 64 | -0.2069 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 531 | 64 | -0.2069 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 189 | 64 | -0.2069 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 190 | 64 | -0.2069 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 99 | 42 | -0.7247 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 99 | 42 | -0.7247 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 99 | 42 | -0.7247 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 99 | 42 | -0.7247 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 100 | 42 | -0.7247 | `source_quality_workorder` |
| `would_limit_fill` | `false` | 640 | 35 | -0.0609 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 94 | 29 | 0.0281 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 88 | 29 | -0.3832 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 33 | 21 | -0.3173 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_10s_plus` | 63 | 20 | -0.7674 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 90 | 20 | -1.0695 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 74 | 20 | -0.1211 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 34 | 17 | -0.7627 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 50 | 16 | -0.6729 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 14 | 9 | -0.9657 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 7 | 6 | -0.4907 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 8 | 4 | 0.3807 | `keep_collecting` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 3 | 3 | -3.8922 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 5 | 3 | -0.7689 | `source_quality_workorder` |
| `overbought_guard_action` | `would_block` | 3 | 3 | -3.8922 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 136 | 2 | 3.1505 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 37, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 289 | 106 | -1.15 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 289 | 106 | -1.15 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 281 | 102 | -1.1711 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 74 | 69 | -1.9142 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 67 | 67 | -1.9343 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 13 | 11 | -0.0048 | `hold_no_edge` |
| `profit_band` | `profit_pos080_pos150` | 12 | 11 | -0.0685 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 10 | 10 | -0.0509 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 10 | 10 | -0.0327 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 7 | 7 | 0.5147 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 7 | 7 | 0.5147 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 5 | 5 | 1.7127 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 5 | 5 | 1.7127 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 18 | 3 | -0.395 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 3 | 3 | -0.395 | `hold_sample` |
| `holding_action` | `holding_action_not_applicable_at_start` | 4 | 2 | -1.2424 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 2 | 2 | -1.2424 | `hold_sample` |
| `holding_action` | `BUY` | 1 | 1 | -0.4267 | `hold_sample` |
| `holding_action` | `DROP` | 3 | 1 | 0.4555 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | -0.4267 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=DROP|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 0.4555 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 23 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 7 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 14 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 183 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 23 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=DROP|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 179 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_180_600s` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 6 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 7 | 0 | None | `hold_sample` |
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
| `profit_band` | `profit_lt_neg070` | 171 | 171 | -1.4444 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 147 | 147 | -0.8885 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 147 | 147 | -0.8885 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 147 | 147 | -0.8885 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 104 | 104 | -1.1474 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 93 | 93 | -1.2211 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 51 | 51 | -0.4593 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 46 | 46 | -1.8667 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 36 | 36 | -0.8717 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 36 | 36 | -0.5644 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 35 | 35 | -1.5795 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 30 | 30 | 0.4092 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 23 | 23 | -0.2707 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 23 | 23 | -0.2707 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 22 | 22 | -1.2226 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 18 | 18 | -2.3488 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 16 | 16 | 0.0701 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 16 | 16 | -1.3734 | `hold_sample` |
| `exit_outcome` | `outcome_unknown` | 3986 | 15 | -0.323 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 12 | 12 | -1.8014 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 11 | 11 | -0.0976 | `hold_no_edge` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 10 | 10 | -0.8851 | `hold_sample` |
| `exit_outcome` | `COMPLETED` | 8 | 8 | -0.1725 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 8 | 8 | -0.1725 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 7 | 7 | 0.5147 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 7 | 7 | 2.3404 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_hard_stop_pct` | 6 | 6 | -4.6866 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 6 | 6 | -0.19 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 6 | 6 | -0.9009 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 6 | 6 | -0.2929 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 5 | 5 | -0.966 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 5 | 5 | 0.246 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 4 | 4 | 1.302 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 4 | 4 | 1.0808 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 3 | 3 | 0.055 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 3 | 3 | -4.0827 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 3 | 3 | -0.6788 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 3 | 3 | -0.3234 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 3 | 3 | 0.4565 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 3 | 3 | -0.2673 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 439, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 5757 | 5740 | None | -1.0247 | 0.0859 | `hold_sample` |
| `arm` | `AVG_DOWN` | 5521 | 5431 | None | -1.1951 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 5447 | 5357 | None | -1.167 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 3255 | 3255 | None | -1.0678 | 0.1038 | `hold_sample` |
| `price_guard_reason` | `price_guard_none` | 3069 | 3026 | None | -0.8435 | 0.1032 | `hold_sample` |
| `qty_reason` | `qty_none` | 3028 | 3026 | None | -0.8435 | 0.1032 | `hold_sample` |
| `time_bucket` | `time_unknown` | 3071 | 3026 | None | -0.8435 | 0.1032 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 3028 | 2983 | None | -0.8468 | 0.1047 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 2736 | 2736 | None | -1.0985 | 0.0 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 2040 | 2040 | None | -0.9121 | 0.1083 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 1699 | 1699 | None | -1.3648 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 1453 | 1453 | None | -0.9596 | 0.108 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 1087 | 1087 | None | -0.9678 | 0.0984 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 969 | 969 | None | -0.4206 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 692 | 671 | None | 0.736 | 0.9895 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 692 | 671 | None | 0.736 | 0.9895 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 679 | 660 | None | -0.8659 | 0.1001 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 596 | 596 | None | -0.8662 | 0.0906 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 575 | 575 | None | -0.4152 | 0.433 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 406 | 406 | None | 0.3716 | 0.9902 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 46 | 23 | -0.2707 | -0.3609 | 0.1304 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 23 | 23 | -0.2707 | -0.3609 | 0.1304 | `hold_sample` |
| `stage` | `exit` | 23 | 23 | -0.2707 | -0.3609 | 0.1304 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 46 | 23 | -0.2707 | -0.3609 | 0.1304 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 23 | 23 | -0.2707 | -0.3609 | 0.1304 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 44 | 22 | -0.2308 | -0.3077 | 0.1364 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 40 | 20 | -0.3713 | -0.495 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 15 | 15 | -0.173 | -0.2307 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 30 | 15 | -0.173 | -0.2307 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 28 | 14 | -0.2706 | -0.3607 | 0.2143 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 24 | 12 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
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
