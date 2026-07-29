# Lifecycle Decision Matrix - 2026-07-28

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-28_mtd`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `15921`
- source_rows_total: `27721`
- retained_rows: `15921`
- dropped_rows_by_source: `{}`
- joined_rows: `6549`
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
- lifecycle_flow_bucket_count: `240`
- lifecycle_flow_complete_count: `119`
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
| `entry` | 3313 | 63 | -0.2592 | 0.0482 | `pass` | `NO_CHANGE` | False |
| `submit` | 808 | 103 | -0.4002 | 0.4873 | `pass` | `NO_CHANGE` | False |
| `holding` | 308 | 103 | -1.158 | 0.7007 | `pass` | `NO_CHANGE` | False |
| `scale_in` | 6134 | 6024 | -0.8454 | 0.999 | `pass` | `NO_CHANGE` | False |
| `exit` | 5358 | 256 | -0.9584 | 0.3925 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 240, 'complete_flow_count': 119, 'incomplete_flow_count': 12556, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 5417 | 5328 | -1.0346 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 645 | 624 | 0.7792 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 55 | 55 | -1.0052 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:ac760bc3a4` | 16 | 16 | -0.8625 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 9 | 9 | -0.1104 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:62b3401904` | 6 | 6 | -0.1725 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
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
- summary: `{'bucket_count': 319, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 1364 | 53 | -0.1213 | -1.3407 | 0.3208 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 2565 | 50 | -0.1992 | -1.4304 | 0.36 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 1313 | 47 | 0.0016 | -1.3458 | 0.3191 | `hold_sample` |
| `chosen_action` | `NO_BUY_AI` | 1778 | 41 | -0.0117 | -1.5276 | 0.2927 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 1038 | 31 | 0.1852 | -1.5665 | 0.2581 | `hold_sample` |
| `stale_bucket` | `stale_high` | 1007 | 28 | -0.0966 | -1.1354 | 0.3929 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 1049 | 25 | -0.4244 | -0.8842 | 0.44 | `hold_sample` |
| `score_band` | `score_60_62` | 649 | 24 | -0.1985 | -1.5513 | 0.2917 | `hold_sample` |
| `strength_bucket` | `neutral_strength_momentum` | 1594 | 23 | -0.8205 | -0.9558 | 0.4783 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 23 | 23 | -0.0459 | -3.5504 | 0.0 | `hold_sample` |
| `time_bucket` | `time_0900_1000` | 595 | 22 | 0.3007 | -1.1756 | 0.2727 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 18 | 18 | -0.4625 | 1.7878 | 1.0 | `hold_sample` |
| `score_band` | `score_70p` | 346 | 17 | -0.5397 | -0.7379 | 0.5882 | `hold_sample` |
| `chosen_action` | `WAIT_REQUOTE` | 1167 | 16 | -0.7111 | -0.5559 | 0.5 | `hold_sample` |
| `stale_bucket` | `fresh` | 540 | 15 | -0.2255 | -2.4607 | 0.1333 | `hold_sample` |
| `exit_rule` | `exit_unknown` | 3263 | 13 | -0.49 | -0.7333 | 0.3846 | `hold_sample` |
| `stale_bucket` | `fresh_or_unflagged` | 171 | 13 | -0.49 | -0.7333 | 0.3846 | `hold_sample` |
| `score_band` | `score_lt60` | 2243 | 13 | 0.4221 | -0.6654 | 0.4616 | `hold_sample` |
| `source_stage` | `wait6579_ev_cohort` | 13 | 13 | -0.49 | -0.7333 | 0.3846 | `hold_sample` |
| `time_bucket` | `time_1200_1400` | 732 | 10 | -1.0499 | -2.708 | 0.3 | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 132, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 632 | 103 | -0.4002 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 761 | 103 | -0.4002 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 286 | 103 | -0.4002 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 286 | 103 | -0.4002 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 286 | 103 | -0.4002 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 286 | 103 | -0.4002 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 286 | 103 | -0.4002 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 286 | 103 | -0.4002 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 286 | 103 | -0.4002 | `keep_collecting` |
| `latency_state` | `simulated` | 286 | 103 | -0.4002 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 632 | 103 | -0.4002 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 283 | 100 | -0.2954 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 277 | 98 | -0.4411 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 253 | 82 | -0.309 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 187 | 61 | -0.1768 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 186 | 61 | -0.1768 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 522 | 61 | -0.1768 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 186 | 61 | -0.1768 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 187 | 61 | -0.1768 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 99 | 42 | -0.7247 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 99 | 42 | -0.7247 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 99 | 42 | -0.7247 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 99 | 42 | -0.7247 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 100 | 42 | -0.7247 | `source_quality_workorder` |
| `would_limit_fill` | `false` | 620 | 32 | 0.0103 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 94 | 29 | 0.0281 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 88 | 29 | -0.3832 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_10s_plus` | 62 | 20 | -0.7674 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 90 | 20 | -1.0695 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 74 | 20 | -0.1211 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_context_missing` | 30 | 18 | -0.2335 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 34 | 17 | -0.7627 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 50 | 16 | -0.6729 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 14 | 9 | -0.9657 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 8 | 4 | 0.3807 | `keep_collecting` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 3 | 3 | -3.8922 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 4 | 3 | -0.1616 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 5 | 3 | -0.7689 | `source_quality_workorder` |
| `overbought_guard_action` | `would_block` | 3 | 3 | -3.8922 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 129 | 2 | 3.1505 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 37, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 286 | 103 | -1.158 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 286 | 103 | -1.158 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 278 | 99 | -1.18 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 72 | 67 | -1.9393 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 65 | 65 | -1.9608 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 12 | 11 | -0.0685 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 12 | 10 | 0.0429 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 10 | 10 | -0.0327 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 9 | 9 | -0.0029 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 7 | 7 | 0.5147 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 7 | 7 | 0.5147 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 5 | 5 | 1.7127 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 5 | 5 | 1.7127 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 17 | 3 | -0.395 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 3 | 3 | -0.395 | `hold_sample` |
| `holding_action` | `holding_action_not_applicable_at_start` | 4 | 2 | -1.2424 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 2 | 2 | -1.2424 | `hold_sample` |
| `holding_action` | `BUY` | 1 | 1 | -0.4267 | `hold_sample` |
| `holding_action` | `DROP` | 3 | 1 | 0.4555 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | -0.4267 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=DROP|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 0.4555 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 22 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 6 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 14 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 183 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 22 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=DROP|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 179 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_180_600s` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 5 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 7 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos080_pos150|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 63, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 167 | 167 | -1.4509 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 144 | 144 | -0.8915 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 144 | 144 | -0.8915 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 144 | 144 | -0.8915 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 102 | 102 | -1.1448 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 90 | 90 | -1.2326 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 50 | 50 | -0.4651 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 46 | 46 | -1.8667 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 36 | 36 | -0.8717 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 36 | 36 | -0.5644 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 33 | 33 | -1.6179 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 29 | 29 | 0.4399 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 22 | 22 | -0.2751 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 22 | 22 | -0.2751 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 21 | 21 | -1.2458 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 18 | 18 | -2.3488 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 16 | 16 | -1.3734 | `hold_sample` |
| `exit_outcome` | `outcome_unknown` | 3986 | 15 | -0.323 | `source_quality_workorder` |
| `profit_band` | `profit_neg010_pos080` | 14 | 14 | 0.091 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 12 | 12 | -1.8014 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 11 | 11 | -0.0976 | `hold_no_edge` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 8 | 8 | -0.8383 | `hold_sample` |
| `exit_outcome` | `COMPLETED` | 7 | 7 | -0.1725 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 7 | 7 | 0.5147 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 7 | 7 | 2.3404 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 7 | 7 | -0.1725 | `hold_sample` |
| `exit_rule` | `scalp_hard_stop_pct` | 6 | 6 | -4.6866 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 6 | 6 | -0.19 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 6 | 6 | -0.9009 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 6 | 6 | -0.2929 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 5 | 5 | -0.966 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 4 | 4 | 0.225 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 4 | 4 | 1.302 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 4 | 4 | 1.0808 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 3 | 3 | 0.055 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 3 | 3 | -4.0827 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 3 | 3 | 0.4565 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 3 | 3 | -0.2673 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos150_pos300_plus` | 2 | 2 | 3.9095 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 2 | 2 | -5.5389 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 436, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 5679 | 5662 | None | -1.0368 | 0.0798 | `hold_sample` |
| `arm` | `AVG_DOWN` | 5483 | 5394 | None | -1.1983 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 5409 | 5320 | None | -1.1701 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 3252 | 3252 | None | -1.0683 | 0.1039 | `hold_sample` |
| `price_guard_reason` | `price_guard_none` | 2990 | 2948 | None | -0.8619 | 0.092 | `hold_sample` |
| `qty_reason` | `qty_none` | 2950 | 2948 | None | -0.8619 | 0.092 | `hold_sample` |
| `time_bucket` | `time_unknown` | 2992 | 2948 | None | -0.8619 | 0.092 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 2969 | 2925 | None | -0.8643 | 0.0927 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 2723 | 2723 | None | -1.0994 | 0.0 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 1991 | 1991 | None | -0.9395 | 0.0914 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 1678 | 1678 | None | -1.3692 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 1453 | 1453 | None | -0.9596 | 0.108 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 1058 | 1058 | None | -1.0018 | 0.0775 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 953 | 953 | None | -0.4222 | 0.0 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 676 | 657 | None | -0.8672 | 0.0991 | `hold_sample` |
| `arm` | `PYRAMID` | 651 | 630 | None | 0.7598 | 0.9888 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 651 | 630 | None | 0.7598 | 0.9888 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 575 | 575 | None | -0.9016 | 0.0678 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 530 | 530 | None | -0.4768 | 0.3925 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 367 | 367 | None | 0.372 | 0.9891 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 44 | 22 | -0.2751 | -0.3668 | 0.1364 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 22 | 22 | -0.2751 | -0.3668 | 0.1364 | `hold_sample` |
| `stage` | `exit` | 22 | 22 | -0.2751 | -0.3668 | 0.1364 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 44 | 22 | -0.2751 | -0.3668 | 0.1364 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 22 | 22 | -0.2751 | -0.3668 | 0.1364 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 42 | 21 | -0.2336 | -0.3114 | 0.1429 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 38 | 19 | -0.3817 | -0.5089 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 14 | 14 | -0.173 | -0.2307 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 28 | 14 | -0.2706 | -0.3607 | 0.2143 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 28 | 14 | -0.173 | -0.2307 | 0.0 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 22 | 11 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 22 | 11 | -0.3778 | -0.5036 | 0.2727 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 12 | 6 | -0.32 | -0.4267 | 0.0 | `hold_sample` |
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
