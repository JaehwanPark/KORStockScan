# Lifecycle Decision Matrix - 2026-07-15

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-15_rolling10d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `14743`
- source_rows_total: `21353`
- retained_rows: `14743`
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
- lifecycle_flow_bucket_count: `211`
- lifecycle_flow_complete_count: `88`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0069`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 1785 | 63 | -0.1124 | 0.0626 | `pass` | `NO_CHANGE` | False |
| `submit` | 496 | 102 | -0.6094 | 0.5366 | `pass` | `NO_CHANGE` | False |
| `holding` | 308 | 102 | -1.3116 | 0.749 | `pass` | `EXIT` | False |
| `scale_in` | 5570 | 5447 | -0.8439 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 6584 | 234 | -1.0955 | 0.2648 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 211, 'complete_flow_count': 88, 'incomplete_flow_count': 12672, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 4797 | 4697 | -1.0619 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 667 | 644 | 0.7611 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 88 | 88 | -1.0511 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 16 | 16 | -0.0942 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 8 | 8 | -0.7688 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 7 | 7 | 0.1809 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 4 | 4 | 0.652 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 4 | 4 | -1.3575 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:15c17a2405` | 3 | 3 | -2.6964 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:35ce26a91c` | 3 | 3 | -1.2733 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:ac760bc3a4` | 3 | 3 | -1.06 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:964bbee510` | 3 | 3 | -0.8233 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b4078edac9` | 3 | 3 | -2.6887 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 3 | 3 | -0.6967 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:ad0146c320` | 2 | 2 | -1.8569 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:bb8a19e627` | 2 | 2 | -0.5731 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:8858a17062` | 2 | 2 | -1.09 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:10cd1f01cf` | 2 | 2 | -2.2218 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:4874ec99fd` | 2 | 2 | -1.1385 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:0e963d335b` | 2 | 2 | -1.07 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 296, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 1028 | 55 | 0.0085 | -0.9446 | 0.3273 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 964 | 47 | 0.1725 | -0.8872 | 0.3404 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 1196 | 43 | -0.1903 | -1.4891 | 0.3488 | `hold_sample` |
| `chosen_action` | `NO_BUY_AI` | 1186 | 35 | -0.0181 | -1.5394 | 0.2857 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 826 | 31 | 0.0933 | -1.5581 | 0.1936 | `hold_sample` |
| `strength_bucket` | `neutral_strength_momentum` | 638 | 25 | -0.2691 | -0.4531 | 0.52 | `hold_sample` |
| `score_band` | `score_70p` | 238 | 25 | -0.1623 | -0.7386 | 0.48 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 536 | 25 | -0.0879 | -0.611 | 0.36 | `hold_sample` |
| `chosen_action` | `WAIT_REQUOTE` | 364 | 22 | -0.0898 | 0.0593 | 0.4545 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 22 | 22 | -0.0617 | -3.5482 | 0.0 | `hold_sample` |
| `score_band` | `score_60_62` | 594 | 22 | -0.241 | -1.4559 | 0.2727 | `hold_sample` |
| `stale_bucket` | `stale_high` | 722 | 21 | -0.1109 | -1.441 | 0.3333 | `hold_sample` |
| `exit_rule` | `exit_unknown` | 1742 | 20 | 0.055 | 0.0963 | 0.4 | `hold_sample` |
| `stale_bucket` | `fresh_or_unflagged` | 172 | 20 | 0.055 | 0.0963 | 0.4 | `hold_sample` |
| `source_stage` | `wait6579_ev_cohort` | 20 | 20 | 0.055 | 0.0963 | 0.4 | `hold_sample` |
| `time_bucket` | `time_0900_1000` | 338 | 19 | 0.296 | -0.6945 | 0.3684 | `hold_sample` |
| `stale_bucket` | `fresh` | 371 | 16 | -0.2444 | -1.8556 | 0.25 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 15 | 15 | -0.3211 | 2.1347 | 1.0 | `hold_sample` |
| `time_bucket` | `time_1200_1400` | 403 | 11 | -0.7682 | -2.44 | 0.2727 | `hold_sample` |
| `liquidity_bucket` | `liquidity_not_available` | 581 | 8 | -0.9438 | -1.2688 | 0.625 | `hold_sample` |

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
| `actual_order_submitted` | `false` | 380 | 102 | -0.6094 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 483 | 102 | -0.6094 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 294 | 102 | -0.6094 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 294 | 102 | -0.6094 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 294 | 102 | -0.6094 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 294 | 102 | -0.6094 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 294 | 102 | -0.6094 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 294 | 102 | -0.6094 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 294 | 102 | -0.6094 | `keep_collecting` |
| `latency_state` | `simulated` | 294 | 102 | -0.6094 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 380 | 102 | -0.6094 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 291 | 99 | -0.5099 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 279 | 95 | -0.631 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 258 | 81 | -0.4455 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 176 | 54 | -0.1786 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 175 | 54 | -0.1786 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 258 | 54 | -0.1786 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 175 | 54 | -0.1786 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 176 | 54 | -0.1786 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 119 | 48 | -1.0941 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 117 | 48 | -1.0941 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 118 | 48 | -1.0941 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 118 | 48 | -1.0941 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 119 | 48 | -1.0941 | `source_quality_workorder` |
| `would_limit_fill` | `false` | 291 | 28 | -0.0206 | `keep_collecting` |
| `would_limit_fill` | `true` | 86 | 26 | -0.3487 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 74 | 25 | -1.3856 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 84 | 24 | 0.1105 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_10s_plus` | 68 | 21 | -0.8137 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 40 | 21 | -1.178 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 74 | 19 | -0.0983 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_context_missing` | 34 | 18 | -0.7999 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 58 | 17 | -0.7135 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 12 | 7 | -1.0282 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 13 | 6 | -0.4506 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 5 | 4 | -0.8075 | `source_quality_workorder` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 3 | 3 | -3.8922 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 5 | 3 | -0.8942 | `source_quality_workorder` |
| `overbought_guard_action` | `would_block` | 3 | 3 | -3.8922 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 94 | 2 | -0.3933 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 42, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 294 | 102 | -1.3116 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 294 | 102 | -1.3116 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 281 | 97 | -1.3787 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 74 | 69 | -2.0912 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 68 | 68 | -2.0796 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 10 | 9 | 0.2346 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 10 | 8 | -0.1975 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 8 | 8 | 0.0575 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 8 | 8 | 0.0575 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 7 | 7 | -0.2908 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 7 | 7 | 0.1839 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 6 | 6 | 1.6858 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 5 | 5 | 1.7127 | `hold_sample` |
| `holding_action` | `holding_action_not_applicable_at_start` | 7 | 3 | -0.0281 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 8 | 2 | -0.3 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 2 | 2 | -0.3 | `hold_sample` |
| `holding_action` | `BUY` | 3 | 1 | -0.4267 | `hold_sample` |
| `holding_action` | `DROP` | 3 | 1 | 0.4555 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | -0.4267 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=DROP|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 0.4555 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1 | 1 | -2.886 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | 1.2504 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 1.5514 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 14 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 3 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 9 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 192 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 14 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=DROP|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 184 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_020_180s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_180_600s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 2 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 63, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 160 | 160 | -1.6049 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 131 | 131 | -0.9663 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 131 | 131 | -0.9663 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 131 | 131 | -0.9663 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 93 | 93 | -1.2609 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 89 | 89 | -1.4055 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 47 | 47 | -1.9505 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 38 | 38 | -1.8705 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 38 | 38 | -0.4968 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 33 | 33 | -0.5427 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 31 | 31 | -0.8294 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_trailing_take_profit` | 25 | 25 | 0.5265 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 23 | 23 | -2.3884 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 20 | 20 | -1.415 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 5490 | 14 | -0.3338 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 14 | 14 | -0.3338 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 14 | 14 | -0.3338 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 14 | 14 | -1.3178 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 11 | 11 | -0.0786 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 10 | 10 | -1.8292 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 9 | 9 | 0.199 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 8 | 8 | 0.0575 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 8 | 8 | 2.2418 | `hold_sample` |
| `exit_rule` | `scalp_hard_stop_pct` | 7 | 7 | -4.4293 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 7 | 7 | -1.0317 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 5 | 5 | -0.966 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 5 | 5 | -0.1935 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 4 | 4 | -0.1241 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 4 | 4 | 1.302 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 4 | 4 | 1.0808 | `hold_sample` |
| `exit_rule` | `daily_limit_up_immediate_exit` | 3 | 3 | -2.7856 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 3 | 3 | 0.055 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 3 | 3 | 0.2567 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 3 | 3 | -4.0827 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 3 | 3 | -1.3481 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 3 | 3 | 0.2672 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos150_pos300_plus` | 2 | 2 | 3.9095 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 2 | 2 | -5.5389 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 2 | 2 | -3.8397 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 2 | 2 | -0.9288 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 416, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 5005 | 4988 | None | -1.0801 | 0.0798 | `hold_sample` |
| `arm` | `AVG_DOWN` | 4896 | 4796 | None | -1.2417 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 4822 | 4722 | None | -1.2105 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 2987 | 2987 | None | -1.0736 | 0.1232 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 1666 | 1666 | None | -0.9411 | 0.1056 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 1407 | 1407 | None | -1.1724 | 0.0 | `hold_sample` |
| `price_guard_reason` | `price_guard_none` | 1355 | 1315 | None | -0.9189 | 0.0914 | `hold_sample` |
| `qty_reason` | `qty_none` | 1317 | 1315 | None | -0.9189 | 0.0914 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 1357 | 1315 | None | -0.9189 | 0.0914 | `hold_sample` |
| `time_bucket` | `time_unknown` | 1357 | 1315 | None | -0.9189 | 0.0914 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 745 | 745 | None | -1.4605 | 0.0 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 726 | 705 | None | -0.9445 | 0.0839 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 681 | 681 | None | -1.0623 | 0.1101 | `hold_sample` |
| `arm` | `PYRAMID` | 674 | 651 | None | 0.7379 | 0.9861 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 674 | 651 | None | 0.7379 | 0.9861 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 592 | 592 | None | -1.1283 | 0.0743 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 433 | 433 | None | -0.4132 | 0.0 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 394 | 394 | None | 0.4019 | 0.9848 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 355 | 355 | None | -0.9542 | 0.0817 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 357 | 354 | None | -0.0489 | 0.5578 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 33, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 28 | 14 | -0.3338 | -0.445 | 0.2143 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 14 | 14 | -0.3338 | -0.445 | 0.2143 | `hold_sample` |
| `stage` | `exit` | 14 | 14 | -0.3338 | -0.445 | 0.2143 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 28 | 14 | -0.3338 | -0.445 | 0.2143 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 14 | 14 | -0.3338 | -0.445 | 0.2143 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 26 | 13 | -0.2712 | -0.3615 | 0.2308 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 22 | 11 | -0.3778 | -0.5036 | 0.2727 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 22 | 11 | -0.5339 | -0.7118 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 18 | 9 | -0.325 | -0.4333 | 0.3333 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 6 | 6 | -0.1737 | -0.2317 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 12 | 6 | -0.1737 | -0.2317 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 10 | 5 | -0.966 | -1.288 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 4 | 4 | -0.9206 | -1.2275 | 0.0 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 6 | 3 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 6 | 3 | -0.4675 | -0.6233 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 2 | 2 | 0.12 | 0.16 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 4 | 2 | 0.12 | 0.16 | 1.0 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 4 | 2 | 0.12 | 0.16 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 1 | 1 | 0.96 | 1.28 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_lt040|profit=profit_lt_neg070` | 1 | 1 | -1.1475 | -1.53 | 0.0 | `hold_sample` |

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
