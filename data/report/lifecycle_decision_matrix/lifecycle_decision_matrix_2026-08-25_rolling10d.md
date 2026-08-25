# Lifecycle Decision Matrix - 2026-08-25

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-08-25_rolling10d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `13241`
- source_rows_total: `18061`
- retained_rows: `13241`
- dropped_rows_by_source: `{}`
- joined_rows: `5948`
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
- lifecycle_flow_bucket_count: `138`
- lifecycle_flow_complete_count: `89`
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
| `entry` | 4080 | 46 | -0.4642 | 0.014 | `pass` | `NO_CHANGE` | False |
| `submit` | 514 | 102 | -0.7219 | 0.4567 | `pass` | `NO_CHANGE` | False |
| `holding` | 127 | 100 | -0.9215 | 0.9513 | `pass` | `EXIT` | False |
| `scale_in` | 5554 | 5521 | -0.865 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 2966 | 179 | -0.9 | 0.4123 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 138, 'complete_flow_count': 89, 'incomplete_flow_count': 9386, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 4997 | 4964 | -1.0011 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 556 | 556 | 0.3496 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:a6af469504` | 4 | 4 | -0.9775 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:0cb91a7ba6` | 4 | 4 | -1.0925 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:03eec49aed` | 4 | 4 | -0.9565 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:f658be39ac` | 3 | 3 | -1.26 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_ai_c:a101f93752` | 2 | 2 | -0.845 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:5c4d0773e1` | 2 | 2 | -1.0275 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:b0bc92a886` | 2 | 2 | -1.365 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:27b40f1c54` | 2 | 2 | -0.755 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:77c2d7d131` | 2 | 2 | -1.195 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:2ee314bc27` | 2 | 2 | -0.995 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:b31cc048c8` | 2 | 2 | -2.265 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:bbe961df76` | 2 | 2 | -0.985 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:6669d1917b` | 2 | 2 | -1.3 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:bf44bd3042` | 1 | 1 | -0.53 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:92f69621e6` | 1 | 1 | -1.21 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_bl:e2e349e4ea` | 1 | 1 | -1.2 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:53097ae10f` | 1 | 1 | -0.2008 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_ai_c:bde1a44f4a` | 1 | 1 | -0.97 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 288, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 3330 | 44 | -0.3772 | -1.0834 | 0.3409 | `source_quality_workorder` |
| `chosen_action` | `NO_BUY_AI` | 1856 | 42 | -0.4123 | -1.1564 | 0.3095 | `candidate_tighten_or_exclude` |
| `stale_bucket` | `fresh` | 2224 | 42 | -0.4123 | -1.1564 | 0.3095 | `candidate_tighten_or_exclude` |
| `liquidity_bucket` | `liquidity_high` | 1610 | 42 | -0.4123 | -1.1564 | 0.3095 | `candidate_tighten_or_exclude` |
| `strength_bucket` | `weak_strength_momentum` | 1635 | 31 | -0.5057 | -1.3239 | 0.2581 | `candidate_tighten_or_exclude` |
| `score_band` | `score_70p` | 367 | 27 | -0.4963 | -1.2326 | 0.2592 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 507 | 25 | -0.0887 | -1.096 | 0.2 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 1184 | 24 | -0.4176 | -1.1987 | 0.25 | `source_quality_workorder` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 23 | 23 | -0.2451 | -1.5161 | 0.0 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 17 | 17 | -0.7165 | 0.3824 | 0.8824 | `hold_sample` |
| `overbought_bucket` | `overbought_watch` | 942 | 12 | -0.7048 | -2.0308 | 0.25 | `hold_sample` |
| `score_band` | `score_63_65` | 75 | 10 | -0.9128 | -0.444 | 0.5 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 24 | 9 | -0.0178 | -0.9266 | 0.3333 | `hold_sample` |
| `time_bucket` | `time_1200_1400` | 831 | 9 | -0.3391 | -1.3533 | 0.3333 | `source_quality_workorder` |
| `strength_bucket` | `neutral_strength_momentum` | 1811 | 8 | 0.0462 | -0.085 | 0.75 | `hold_sample` |
| `time_bucket` | `time_1400_close` | 1192 | 7 | -0.8398 | -0.0771 | 0.8571 | `source_quality_workorder` |
| `exit_rule` | `scalp_soft_stop_pct` | 6 | 6 | -0.589 | -3.4883 | 0.0 | `hold_sample` |
| `score_band` | `score_lt60` | 3625 | 6 | 0.2287 | -1.5433 | 0.3333 | `source_quality_workorder` |
| `time_bucket` | `time_0900_1000` | 873 | 6 | -0.4 | -1.3017 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 5 | 5 | -0.3294 | -1.078 | 0.2 | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 122, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 442 | 102 | -0.7219 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 127 | 102 | -0.7219 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 127 | 102 | -0.7219 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 127 | 102 | -0.7219 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 127 | 102 | -0.7219 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 127 | 102 | -0.7219 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 127 | 102 | -0.7219 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 127 | 102 | -0.7219 | `keep_collecting` |
| `latency_state` | `simulated` | 127 | 102 | -0.7219 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 442 | 102 | -0.7219 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 493 | 100 | -0.7417 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 120 | 95 | -0.7469 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 83 | 64 | -0.7888 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 76 | 56 | -0.3382 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 76 | 56 | -0.3382 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 62 | 53 | -0.9851 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 62 | 53 | -0.9851 | `source_quality_workorder` |
| `price_below_bid_bucket` | `not_below_bid` | 65 | 50 | -0.6641 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 65 | 49 | -0.4372 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 363 | 49 | -0.4372 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 65 | 49 | -0.4372 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 55 | 46 | -1.1891 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 50 | 46 | -1.1891 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 51 | 46 | -1.1891 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 106 | 45 | -1.1147 | `keep_collecting` |
| `would_limit_fill` | `false` | 433 | 35 | -0.4524 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 40 | 34 | -0.5059 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 37 | 31 | -0.6605 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 32 | 26 | -0.4562 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 20 | 19 | -1.0651 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 20 | 18 | -1.6222 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 21 | 17 | -1.3528 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 19 | 14 | -0.3991 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 19 | 14 | -0.3991 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 14 | 9 | -0.4415 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_10s_plus` | 16 | 8 | -0.2561 | `keep_collecting` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 7 | 7 | -0.3822 | `keep_collecting` |
| `overbought_guard_action` | `would_block` | 7 | 7 | -0.3822 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_overbought_guard_would_block` | 5 | 5 | 0.3893 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 6 | 5 | -0.8046 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 36, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 120 | 100 | -0.9215 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 120 | 100 | -0.9215 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 71 | 59 | -1.0009 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 59 | 54 | -1.4438 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 48 | 40 | -0.8223 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 37 | 37 | -1.243 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 27 | 27 | -0.463 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 17 | 17 | -1.8806 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 14 | 14 | -0.4856 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 12 | 12 | -0.4584 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 10 | 8 | -0.8015 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 6 | 6 | 0.5357 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 4 | 4 | 0.3069 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 4 | 4 | -1.4848 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 4 | 4 | -0.1182 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 3 | 3 | -0.6948 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 3 | 3 | 1.7663 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 3 | 3 | -0.179 | `hold_sample` |
| `holding_action` | `BUY` | 1 | 1 | -0.2008 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 1 | 1 | 0.2903 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | -0.2008 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 1 | 1 | 1.7646 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 0.2903 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 7 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 4 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 20 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 7 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 12 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 8 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_020_180s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_180_600s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 48, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 101 | 101 | -1.285 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 95 | 95 | -0.8931 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 77 | 77 | -0.903 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 77 | 77 | -0.903 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 77 | 77 | -0.903 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 46 | 46 | -1.1448 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 44 | 44 | -0.3027 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 40 | 40 | -0.5883 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 35 | 35 | -0.8327 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 31 | 31 | -0.5442 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 30 | 30 | -1.5307 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 30 | 30 | -0.326 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 27 | 27 | -0.463 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 25 | 25 | -1.9602 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 24 | 24 | -0.9046 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 16 | 16 | -0.8867 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 13 | 13 | -1.4454 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 12 | 12 | -1.257 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 9 | 9 | -0.8369 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 8 | 8 | -0.1806 | `hold_sample` |
| `exit_outcome` | `COMPLETED` | 7 | 7 | -0.96 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 7 | 7 | -0.96 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 7 | 7 | 0.5754 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 6 | 6 | 0.5357 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 6 | 6 | -3.0783 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 6 | 6 | -1.9577 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_lt_neg070` | 5 | 5 | -1.1775 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 5 | 5 | -1.1874 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 4 | 4 | 0.3069 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 3 | 3 | -0.5285 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 3 | 3 | -0.179 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg070_neg010` | 3 | 3 | 0.3314 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 3 | 3 | 1.2699 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 2 | 2 | -0.4163 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg070_neg010` | 2 | 2 | -2.1641 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 2 | 2 | 0.6301 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 1 | 1 | 0.2903 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=NEUTRAL|profit=profit_lt_neg070` | 1 | 1 | -0.5293 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=NEUTRAL|profit=profit_neg070_neg010` | 1 | 1 | -0.2828 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 1 | 1 | -1.8555 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 328, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 5510 | 5510 | None | -0.9527 | 0.0964 | `hold_sample` |
| `arm` | `AVG_DOWN` | 4998 | 4965 | None | -1.0927 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 4923 | 4890 | None | -1.0609 | 0.0 | `hold_sample` |
| `price_guard_reason` | `price_guard_none` | 4054 | 4034 | None | -0.7784 | 0.119 | `hold_sample` |
| `qty_reason` | `qty_none` | 4034 | 4034 | None | -0.7784 | 0.119 | `hold_sample` |
| `time_bucket` | `time_unknown` | 4054 | 4034 | None | -0.7784 | 0.119 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 2697 | 2697 | None | -0.9494 | 0.1109 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 2256 | 2236 | None | -0.6698 | 0.2147 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 2114 | 2114 | None | -1.2565 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2089 | 2089 | None | -0.6141 | 0.2011 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 1819 | 1799 | None | -0.9128 | 0.0006 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 1598 | 1598 | None | -0.9724 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 1548 | 1548 | None | -0.9294 | 0.1221 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 1361 | 1361 | None | -0.4563 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 959 | 959 | None | -1.0362 | 0.0313 | `hold_sample` |
| `ai_score_source` | `not_evaluated_no_ai_score_source` | 673 | 673 | None | -0.8339 | 0.0223 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_1` | 643 | 643 | None | -1.0611 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 630 | 630 | None | -0.9259 | 0.0365 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 618 | 618 | None | 0.0678 | 0.7476 | `hold_sample` |
| `arm` | `PYRAMID` | 556 | 556 | None | 0.3316 | 0.9748 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 14 | 7 | -0.96 | -1.28 | 0.0 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 7 | 7 | -0.96 | -1.28 | 0.0 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 14 | 7 | -0.96 | -1.28 | 0.0 | `hold_sample` |
| `stage` | `exit` | 7 | 7 | -0.96 | -1.28 | 0.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 14 | 7 | -0.96 | -1.28 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 14 | 7 | -0.96 | -1.28 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 14 | 7 | -0.96 | -1.28 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 7 | 7 | -0.96 | -1.28 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 5 | 5 | -1.1775 | -1.57 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 10 | 5 | -1.1775 | -1.57 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 8 | 4 | -1.26 | -1.68 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 2 | 2 | -0.4163 | -0.555 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 4 | 2 | -0.4163 | -0.555 | 0.0 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 2 | 1 | -0.8475 | -1.13 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 2 | 1 | -0.3975 | -0.53 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2 | 1 | -0.435 | -0.58 | 0.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 7 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_lt_neg070` | 5 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 2 | 0 | None | None | None | `hold_sample` |
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
