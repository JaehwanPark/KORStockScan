# Lifecycle Decision Matrix - 2026-08-31

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-08-31_rolling10d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `13914`
- source_rows_total: `17456`
- retained_rows: `13914`
- dropped_rows_by_source: `{}`
- joined_rows: `7474`
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
- lifecycle_flow_bucket_count: `126`
- lifecycle_flow_complete_count: `77`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0075`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 3938 | 42 | -0.419 | 0.0111 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 439 | 87 | -0.7895 | 0.3715 | `pass` | `NO_CHANGE` | False |
| `holding` | 117 | 87 | -0.8093 | 0.9064 | `pass` | `EXIT` | False |
| `scale_in` | 7161 | 7106 | -0.8341 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 2259 | 152 | -0.8194 | 0.5129 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 126, 'complete_flow_count': 77, 'incomplete_flow_count': 10199, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 6579 | 6526 | -0.9446 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 581 | 579 | 0.4116 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:0cb91a7ba6` | 6 | 6 | -0.9517 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:a6af469504` | 4 | 4 | -0.9775 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:f58154b780` | 2 | 2 | -1.12 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:b31cc048c8` | 2 | 2 | -1.575 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:5ee2a7cfd7` | 2 | 2 | -1.05 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:f658be39ac` | 2 | 2 | -1.0987 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:7a29eed6f7` | 1 | 1 | -1.249 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:1793c3951c` | 1 | 1 | -0.6466 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:05c0ca21ce` | 1 | 1 | 0.045 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:a9d1313d5d` | 1 | 1 | 0.1763 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:7ee2fdca81` | 1 | 1 | 0.0318 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_ai_c:bde1a44f4a` | 1 | 1 | -0.97 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_ai_c:e766b2429d` | 1 | 1 | -0.64 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_ai_c:a101f93752` | 1 | 1 | -0.52 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_bloc:ce21fab319` | 1 | 1 | -0.51 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:555dee5f6c` | 1 | 1 | -0.65 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:3b618795a8` | 1 | 1 | -0.79 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:0c9b051cda` | 1 | 1 | -0.81 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 290, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `NO_BUY_AI` | 1720 | 40 | -0.3385 | -1.1427 | 0.325 | `hold_sample` |
| `liquidity_bucket` | `liquidity_high` | 1459 | 40 | -0.3385 | -1.1427 | 0.325 | `hold_sample` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 3256 | 40 | -0.3385 | -1.1427 | 0.325 | `source_quality_workorder` |
| `stale_bucket` | `fresh` | 2030 | 39 | -0.3297 | -1.1313 | 0.3333 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 1102 | 26 | -0.3443 | -1.4277 | 0.2308 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 1483 | 26 | -0.3351 | -1.4004 | 0.2308 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 467 | 20 | -0.0217 | -1.1205 | 0.2 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 18 | 18 | -0.2777 | -1.5461 | 0.0 | `hold_sample` |
| `score_band` | `score_70p` | 275 | 18 | -0.6662 | -0.9922 | 0.2778 | `hold_sample` |
| `score_band` | `score_63_65` | 91 | 17 | -0.1213 | -1.0212 | 0.4118 | `hold_sample` |
| `overbought_bucket` | `overbought_watch` | 857 | 15 | -0.2985 | -1.4547 | 0.4 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 15 | 15 | -0.5574 | 0.4233 | 0.8667 | `hold_sample` |
| `strength_bucket` | `neutral_strength_momentum` | 1686 | 8 | -0.7974 | -0.285 | 0.625 | `hold_sample` |
| `time_bucket` | `time_1200_1400` | 884 | 8 | -0.3379 | -0.7387 | 0.625 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 11 | 7 | -0.1657 | -1.01 | 0.2857 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 6 | 6 | -0.4241 | -3.3933 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 8 | 6 | -0.0405 | -1.2183 | 0.1666 | `hold_sample` |
| `strength_bucket` | `strong_strength_momentum` | 452 | 6 | 0.2589 | -1.17 | 0.3333 | `hold_sample` |
| `score_band` | `score_lt60` | 3557 | 5 | -0.5909 | -1.21 | 0.4 | `source_quality_workorder` |
| `time_bucket` | `time_0900_1000` | 684 | 5 | -0.873 | -0.802 | 0.2 | `hold_sample` |

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
| `actual_order_submitted` | `false` | 399 | 87 | -0.7895 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 420 | 87 | -0.7895 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 111 | 87 | -0.7895 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 111 | 87 | -0.7895 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 111 | 87 | -0.7895 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 111 | 87 | -0.7895 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 111 | 87 | -0.7895 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 111 | 87 | -0.7895 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 111 | 87 | -0.7895 | `keep_collecting` |
| `latency_state` | `simulated` | 111 | 87 | -0.7895 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 399 | 87 | -0.7895 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 104 | 80 | -0.7549 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 85 | 63 | -0.6866 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 69 | 50 | -0.595 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 67 | 47 | -0.4441 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 67 | 47 | -0.4441 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 52 | 45 | -1.2059 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 52 | 45 | -1.2059 | `source_quality_workorder` |
| `price_resolution_bucket` | `price_resolution_unknown` | 59 | 42 | -0.3433 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 331 | 42 | -0.3433 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 59 | 42 | -0.3433 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 47 | 40 | -1.1953 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 43 | 40 | -1.1953 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 44 | 40 | -1.1953 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 75 | 36 | -1.2863 | `keep_collecting` |
| `would_limit_fill` | `false` | 370 | 29 | -0.4982 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 37 | 25 | -0.5342 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 22 | 20 | -1.4622 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 21 | 19 | -1.0017 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 20 | 17 | -1.029 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 19 | 17 | -1.0079 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 16 | 13 | 0.0022 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 17 | 13 | 0.0022 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 12 | 12 | -1.4717 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_10s_plus` | 21 | 9 | -0.8839 | `keep_collecting` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 7 | 7 | -1.1843 | `keep_collecting` |
| `overbought_guard_action` | `would_block` | 7 | 7 | -1.1843 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_overbought_guard_would_block` | 5 | 5 | -1.2904 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 6 | 5 | -0.1372 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 5 | 4 | -0.2725 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 38, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 107 | 87 | -0.8093 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 107 | 87 | -0.8093 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 80 | 63 | -0.919 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 49 | 43 | -1.3798 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 36 | 36 | -1.318 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 27 | 24 | -0.5213 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 23 | 22 | -0.3283 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 14 | 14 | -0.2847 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 11 | 8 | -0.3309 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 8 | 8 | -0.4046 | `hold_no_edge` |
| `profit_band` | `profit_pos080_pos150` | 7 | 7 | 0.1009 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 7 | 7 | -1.698 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 6 | 6 | -0.3671 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 5 | 5 | -0.5905 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 4 | 4 | -0.5435 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 4 | 4 | -0.3341 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 4 | 4 | -0.1182 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 1.8295 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 2 | 2 | -0.433 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 1 | 1 | 0.2903 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 0.2903 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 10 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 4 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 3 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 20 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 10 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 17 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_020_180s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_180_600s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_180_600s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 52, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `exit_source_stage` | `sim_post_sell_evaluation` | 84 | 84 | -0.7833 | `hold_no_edge` |
| `profit_band` | `profit_lt_neg070` | 82 | 82 | -1.233 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 58 | 58 | -0.8784 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 58 | 58 | -0.8784 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 58 | 58 | -0.8784 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 40 | 40 | -0.2586 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 36 | 36 | -1.093 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 33 | 33 | -0.4563 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 30 | 30 | -1.4046 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 29 | 29 | -0.6336 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 25 | 25 | -0.2115 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg010_pos080` | 23 | 23 | -0.3121 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 22 | 22 | -0.5273 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 20 | 20 | -0.981 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 17 | 17 | -0.6835 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 17 | 17 | -1.8834 | `hold_sample` |
| `exit_outcome` | `COMPLETED` | 10 | 10 | -0.78 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 10 | 10 | -0.78 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 10 | 10 | -0.1265 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 9 | 9 | -0.8626 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 8 | 8 | -1.3859 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 7 | 7 | 0.1009 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 6 | 6 | -0.3671 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_lt_neg070` | 6 | 6 | -1.1725 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 6 | 6 | -1.4883 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 6 | 6 | -2.5518 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 6 | 6 | 0.3829 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 5 | 5 | -0.5853 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 5 | 5 | -1.6212 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 5 | 5 | -0.7503 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 3 | 3 | -0.27 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 3 | 3 | -1.873 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 3 | 3 | -0.9272 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg070_neg010` | 3 | 3 | 0.3314 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 3 | 3 | 0.1747 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 2 | 2 | -1.2784 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=NEUTRAL|profit=profit_neg070_neg010` | 2 | 2 | -0.7522 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 1 | 1 | 0.2903 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg010_pos080` | 1 | 1 | 0.045 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 1 | 1 | -0.1496 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 357, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `price_guard_reason` | `price_guard_none` | 7159 | 7106 | None | -0.9145 | 0.0791 | `hold_sample` |
| `qty_reason` | `qty_none` | 7108 | 7106 | None | -0.9145 | 0.0791 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 7095 | 7094 | None | -0.9181 | 0.0779 | `hold_sample` |
| `arm` | `AVG_DOWN` | 6580 | 6527 | None | -1.029 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 6526 | 6473 | None | -1.0112 | 0.0 | `hold_sample` |
| `time_bucket` | `time_unknown` | 4290 | 4254 | None | -0.8041 | 0.1167 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 3839 | 3839 | None | -1.47 | 0.0 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 3827 | 3827 | None | -0.9098 | 0.0839 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 3448 | 3448 | None | -0.942 | 0.0859 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 3394 | 3339 | None | -1.0204 | 0.0006 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 2605 | 2605 | None | -1.093 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 2481 | 2481 | None | -0.4269 | 0.0 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 2383 | 2347 | None | -0.6787 | 0.2116 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 1963 | 1963 | None | -0.9788 | 0.0784 | `hold_sample` |
| `ai_score_source` | `live` | 1549 | 1549 | None | -0.8684 | 0.1188 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 1103 | 1103 | None | -0.7972 | 0.0789 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 1089 | 1089 | None | -0.3201 | 0.449 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_1` | 796 | 796 | None | -1.1321 | 0.0 | `hold_sample` |
| `ai_score_source` | `not_evaluated_no_ai_score_source` | 773 | 773 | None | -0.7662 | 0.0285 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 723 | 723 | None | 0.1432 | 0.693 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 25, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 20 | 10 | -0.78 | -1.04 | 0.1 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 10 | 10 | -0.78 | -1.04 | 0.1 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 20 | 10 | -0.78 | -1.04 | 0.1 | `hold_sample` |
| `stage` | `exit` | 10 | 10 | -0.78 | -1.04 | 0.1 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 20 | 10 | -0.78 | -1.04 | 0.1 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 20 | 10 | -0.78 | -1.04 | 0.1 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 10 | 10 | -0.78 | -1.04 | 0.1 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 18 | 9 | -0.8717 | -1.1622 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 6 | 6 | -1.1725 | -1.5633 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 12 | 6 | -1.1725 | -1.5633 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 8 | 4 | -0.8963 | -1.195 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 3 | 3 | -0.27 | -0.36 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 6 | 3 | -0.7325 | -0.9767 | 0.3333 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 6 | 3 | -0.27 | -0.36 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 4 | 2 | -0.585 | -0.78 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 1 | 1 | 0.045 | 0.06 | 1.0 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 2 | 1 | -0.8475 | -1.13 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 2 | 1 | 0.045 | 0.06 | 1.0 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 2 | 1 | 0.045 | 0.06 | 1.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 10 | 0 | None | None | None | `hold_sample` |

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
