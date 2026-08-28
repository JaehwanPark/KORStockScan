# Lifecycle Decision Matrix - 2026-08-28

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-08-28_rolling5d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `11965`
- source_rows_total: `14934`
- retained_rows: `11965`
- dropped_rows_by_source: `{}`
- joined_rows: `6624`
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
- lifecycle_flow_bucket_count: `116`
- lifecycle_flow_complete_count: `68`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0076`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 3209 | 39 | -0.4359 | 0.0118 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 352 | 76 | -0.7561 | 0.4052 | `pass` | `NO_CHANGE` | False |
| `holding` | 103 | 76 | -0.7703 | 0.9125 | `pass` | `EXIT` | False |
| `scale_in` | 6352 | 6302 | -0.8368 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 1949 | 131 | -0.7975 | 0.5724 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 116, 'complete_flow_count': 68, 'incomplete_flow_count': 8913, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 5854 | 5805 | -0.9411 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 497 | 496 | 0.3837 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:a6af469504` | 4 | 4 | -0.9775 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:0cb91a7ba6` | 4 | 4 | -0.94 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:f58154b780` | 2 | 2 | -1.12 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:b31cc048c8` | 2 | 2 | -1.575 | `candidate_tighten_or_exclude` | `pass` |
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
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:55248db096` | 1 | 1 | -0.48 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 278, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `NO_BUY_AI` | 1467 | 38 | -0.3374 | -1.0629 | 0.3421 | `hold_sample` |
| `liquidity_bucket` | `liquidity_high` | 1249 | 38 | -0.3374 | -1.0629 | 0.3421 | `hold_sample` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 2643 | 38 | -0.3374 | -1.0629 | 0.3421 | `source_quality_workorder` |
| `stale_bucket` | `fresh` | 1695 | 37 | -0.328 | -1.0486 | 0.3513 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 888 | 24 | -0.343 | -1.325 | 0.25 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 1253 | 24 | -0.3331 | -1.2954 | 0.25 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 418 | 19 | -0.0073 | -1.0984 | 0.2105 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 17 | 17 | -0.2766 | -1.5465 | 0.0 | `hold_sample` |
| `score_band` | `score_70p` | 234 | 17 | -0.6804 | -0.8282 | 0.2941 | `hold_sample` |
| `score_band` | `score_63_65` | 77 | 16 | -0.1365 | -1.1175 | 0.375 | `hold_sample` |
| `overbought_bucket` | `overbought_watch` | 714 | 14 | -0.2895 | -1.2886 | 0.4286 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 14 | 14 | -0.6059 | 0.4164 | 0.8571 | `hold_sample` |
| `strength_bucket` | `neutral_strength_momentum` | 1322 | 8 | -0.7974 | -0.285 | 0.625 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 11 | 7 | -0.1657 | -1.01 | 0.2857 | `hold_sample` |
| `time_bucket` | `time_1200_1400` | 733 | 7 | -0.4036 | -0.9186 | 0.5714 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 8 | 6 | -0.0405 | -1.2183 | 0.1666 | `hold_sample` |
| `strength_bucket` | `strong_strength_momentum` | 390 | 6 | 0.2589 | -1.17 | 0.3333 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 5 | 5 | -0.424 | -3.316 | 0.0 | `hold_sample` |
| `score_band` | `score_lt60` | 2886 | 5 | -0.5909 | -1.21 | 0.4 | `source_quality_workorder` |
| `time_bucket` | `time_0900_1000` | 583 | 5 | -0.873 | -0.802 | 0.2 | `hold_sample` |

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
| `actual_order_submitted` | `false` | 315 | 76 | -0.7561 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 338 | 76 | -0.7561 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 97 | 76 | -0.7561 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 97 | 76 | -0.7561 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 97 | 76 | -0.7561 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 97 | 76 | -0.7561 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 97 | 76 | -0.7561 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 97 | 76 | -0.7561 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 97 | 76 | -0.7561 | `keep_collecting` |
| `latency_state` | `simulated` | 97 | 76 | -0.7561 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 315 | 76 | -0.7561 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 91 | 70 | -0.7047 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 72 | 53 | -0.6075 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 62 | 44 | -0.4607 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 62 | 44 | -0.4607 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 59 | 43 | -0.4856 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 54 | 39 | -0.3544 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 260 | 39 | -0.3544 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 54 | 39 | -0.3544 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 43 | 37 | -1.1796 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 43 | 37 | -1.1796 | `source_quality_workorder` |
| `liquidity_bucket` | `below_min_liquidity` | 38 | 32 | -1.1623 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 35 | 32 | -1.1623 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 35 | 32 | -1.1623 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 66 | 30 | -1.2565 | `keep_collecting` |
| `would_limit_fill` | `false` | 292 | 26 | -0.5326 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 32 | 22 | -0.5799 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 20 | 17 | -1.029 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 19 | 17 | -1.0079 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 17 | 15 | -1.1121 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 16 | 14 | -1.4737 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 16 | 13 | 0.0022 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 17 | 13 | 0.0022 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 12 | 12 | -1.4717 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_10s_plus` | 15 | 7 | -0.8497 | `keep_collecting` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 6 | 6 | -1.3553 | `keep_collecting` |
| `overbought_guard_action` | `would_block` | 6 | 6 | -1.3553 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_overbought_guard_would_block` | 5 | 5 | -1.2904 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 5 | 4 | -0.2725 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 5 | 4 | 0.2908 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 37, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 94 | 76 | -0.7703 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 94 | 76 | -0.7703 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 67 | 52 | -0.8852 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 44 | 38 | -1.2902 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 31 | 31 | -1.1981 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 27 | 24 | -0.5213 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 20 | 19 | -0.3684 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 11 | 11 | -0.342 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 8 | 8 | -0.4046 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 9 | 7 | -0.5098 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 7 | 7 | -1.698 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 6 | 6 | -0.3671 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 5 | 5 | 0.5928 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 4 | 4 | -0.3341 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 4 | 4 | -0.1182 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 3 | 3 | -1.0318 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 3 | 3 | -0.2317 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 1.8295 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 2 | 2 | -0.433 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 1 | 1 | 0.2903 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 0.2903 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 9 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 3 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 3 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 18 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 9 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 15 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_020_180s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_180_600s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_180_600s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 51, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `exit_source_stage` | `sim_post_sell_evaluation` | 73 | 73 | -0.7388 | `hold_no_edge` |
| `profit_band` | `profit_lt_neg070` | 70 | 70 | -1.1952 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 49 | 49 | -0.8749 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 49 | 49 | -0.8749 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 49 | 49 | -0.8749 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 35 | 35 | -0.2246 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 29 | 29 | -0.5141 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 29 | 29 | -1.1107 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 26 | 26 | -1.2559 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 24 | 24 | -0.6563 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 23 | 23 | -0.2404 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg010_pos080` | 20 | 20 | -0.3477 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 20 | 20 | -0.533 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 19 | 19 | -0.9843 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 15 | 15 | -0.8275 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 13 | 13 | -1.7407 | `hold_sample` |
| `exit_outcome` | `COMPLETED` | 9 | 9 | -0.8525 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 9 | 9 | -0.8525 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 8 | 8 | -0.8558 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 8 | 8 | -1.3859 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 8 | 8 | -0.2152 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 6 | 6 | -0.3671 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_lt_neg070` | 6 | 6 | -1.1725 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 6 | 6 | -1.4883 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 5 | 5 | 0.5928 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 5 | 5 | -0.5853 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 5 | 5 | -1.6212 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 5 | 5 | -0.7503 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 5 | 5 | 0.5955 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 3 | 3 | -2.4491 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg070_neg010` | 3 | 3 | 0.3314 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 2 | 2 | -0.3412 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 2 | 2 | -1.2784 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=NEUTRAL|profit=profit_neg070_neg010` | 2 | 2 | -0.7522 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 2 | 2 | -2.0976 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 2 | 2 | -0.63 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 2 | 2 | 0.6301 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 1 | 1 | 0.2903 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg010_pos080` | 1 | 1 | 0.045 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 1 | 1 | -0.1496 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 329, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `price_guard_reason` | `price_guard_none` | 6350 | 6302 | None | -0.9166 | 0.0762 | `hold_sample` |
| `qty_reason` | `qty_none` | 6304 | 6302 | None | -0.9166 | 0.0762 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 6291 | 6291 | None | -0.9205 | 0.0749 | `hold_sample` |
| `arm` | `AVG_DOWN` | 5855 | 5806 | None | -1.0244 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 5815 | 5766 | None | -1.0096 | 0.0 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 3571 | 3571 | None | -0.9167 | 0.0824 | `hold_sample` |
| `time_bucket` | `time_unknown` | 3481 | 3450 | None | -0.7821 | 0.1201 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 3357 | 3357 | None | -1.4813 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 3267 | 3267 | None | -0.9226 | 0.0906 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 3026 | 2976 | None | -1.0153 | 0.0007 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 2370 | 2370 | None | -1.1087 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 2247 | 2247 | None | -0.4279 | 0.0 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 1936 | 1905 | None | -0.6594 | 0.2177 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 1671 | 1671 | None | -1.0257 | 0.0544 | `hold_sample` |
| `ai_score_source` | `live` | 1359 | 1359 | None | -0.8406 | 0.1038 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 900 | 900 | None | -0.2319 | 0.4711 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 893 | 893 | None | -0.7777 | 0.0862 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 646 | 646 | None | 0.118 | 0.6656 | `hold_sample` |
| `ai_score_source` | `not_evaluated_no_ai_score_source` | 622 | 622 | None | -0.7436 | 0.0225 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_1` | 619 | 619 | None | -1.1093 | 0.0 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 18 | 9 | -0.8525 | -1.1367 | 0.1111 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 9 | 9 | -0.8525 | -1.1367 | 0.1111 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 18 | 9 | -0.8525 | -1.1367 | 0.1111 | `hold_sample` |
| `stage` | `exit` | 9 | 9 | -0.8525 | -1.1367 | 0.1111 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 18 | 9 | -0.8525 | -1.1367 | 0.1111 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 18 | 9 | -0.8525 | -1.1367 | 0.1111 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 9 | 9 | -0.8525 | -1.1367 | 0.1111 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 16 | 8 | -0.9647 | -1.2863 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 6 | 6 | -1.1725 | -1.5633 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 12 | 6 | -1.1725 | -1.5633 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 6 | 3 | -1.1525 | -1.5367 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 6 | 3 | -0.7325 | -0.9767 | 0.3333 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 2 | 2 | -0.3412 | -0.455 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 4 | 2 | -0.585 | -0.78 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 4 | 2 | -0.3412 | -0.455 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 1 | 1 | 0.045 | 0.06 | 1.0 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 2 | 1 | -0.8475 | -1.13 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 2 | 1 | 0.045 | 0.06 | 1.0 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 2 | 1 | 0.045 | 0.06 | 1.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 9 | 0 | None | None | None | `hold_sample` |

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
