# Lifecycle Decision Matrix - 2026-07-16

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-16_rolling10d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `13567`
- source_rows_total: `21434`
- retained_rows: `13567`
- dropped_rows_by_source: `{}`
- joined_rows: `5915`
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
- lifecycle_flow_bucket_count: `208`
- lifecycle_flow_complete_count: `100`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0087`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 2002 | 57 | -0.324 | 0.0519 | `pass` | `NO_CHANGE` | False |
| `submit` | 467 | 93 | -0.4894 | 0.5346 | `pass` | `NO_CHANGE` | False |
| `holding` | 265 | 93 | -1.2234 | 0.7507 | `pass` | `EXIT` | False |
| `scale_in` | 5566 | 5456 | -0.8758 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 5267 | 216 | -1.0047 | 0.3559 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 208, 'complete_flow_count': 100, 'incomplete_flow_count': 11388, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 4900 | 4811 | -1.0738 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 594 | 573 | 0.7924 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 55 | 55 | -1.0052 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 9 | 9 | -0.1104 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:ac760bc3a4` | 7 | 7 | -0.8914 | `candidate_tighten_or_exclude` | `pass` |
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
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:3c997aea8d` | 2 | 2 | -0.935 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:10cd1f01cf` | 2 | 2 | -2.2218 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:4874ec99fd` | 2 | 2 | -1.1385 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 283, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 1121 | 48 | -0.1872 | -1.326 | 0.3542 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 1409 | 45 | -0.2782 | -1.4247 | 0.4 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 1106 | 41 | -0.0503 | -1.3351 | 0.3658 | `hold_sample` |
| `chosen_action` | `NO_BUY_AI` | 1351 | 36 | -0.0844 | -1.5339 | 0.3333 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 898 | 28 | 0.1587 | -1.575 | 0.2857 | `hold_sample` |
| `stale_bucket` | `stale_high` | 835 | 24 | -0.2011 | -1.0767 | 0.4583 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 23 | 23 | -0.0459 | -3.5504 | 0.0 | `hold_sample` |
| `score_band` | `score_60_62` | 626 | 23 | -0.2281 | -1.5539 | 0.3043 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 649 | 23 | -0.5138 | -0.832 | 0.4783 | `hold_sample` |
| `strength_bucket` | `neutral_strength_momentum` | 741 | 21 | -0.9588 | -0.9064 | 0.5238 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 18 | 18 | -0.4625 | 1.7878 | 1.0 | `hold_sample` |
| `time_bucket` | `time_0900_1000` | 339 | 18 | 0.3159 | -1.1288 | 0.3333 | `hold_sample` |
| `score_band` | `score_70p` | 210 | 17 | -0.5397 | -0.7379 | 0.5882 | `hold_sample` |
| `chosen_action` | `WAIT_REQUOTE` | 441 | 15 | -0.7304 | -0.5193 | 0.5333 | `hold_sample` |
| `stale_bucket` | `fresh` | 374 | 14 | -0.2728 | -2.5321 | 0.1429 | `hold_sample` |
| `exit_rule` | `exit_unknown` | 1957 | 12 | -0.4957 | -0.7024 | 0.4167 | `hold_sample` |
| `stale_bucket` | `fresh_or_unflagged` | 137 | 12 | -0.4957 | -0.7024 | 0.4167 | `hold_sample` |
| `source_stage` | `wait6579_ev_cohort` | 12 | 12 | -0.4957 | -0.7024 | 0.4167 | `hold_sample` |
| `score_band` | `score_lt60` | 1102 | 10 | 0.3847 | -0.419 | 0.6 | `hold_sample` |
| `time_bucket` | `time_1200_1400` | 469 | 10 | -1.0499 | -2.708 | 0.3 | `hold_sample` |

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
| `actual_order_submitted` | `false` | 365 | 93 | -0.4894 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 450 | 93 | -0.4894 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 250 | 93 | -0.4894 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 250 | 93 | -0.4894 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 250 | 93 | -0.4894 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 250 | 93 | -0.4894 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 250 | 93 | -0.4894 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 250 | 93 | -0.4894 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 250 | 93 | -0.4894 | `keep_collecting` |
| `latency_state` | `simulated` | 250 | 93 | -0.4894 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 365 | 93 | -0.4894 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 247 | 90 | -0.376 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 241 | 88 | -0.5401 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 224 | 75 | -0.3322 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 159 | 55 | -0.2506 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 158 | 55 | -0.2506 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 270 | 55 | -0.2506 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 158 | 55 | -0.2506 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 159 | 55 | -0.2506 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 91 | 38 | -0.8351 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 91 | 38 | -0.8351 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 91 | 38 | -0.8351 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 91 | 38 | -0.8351 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 92 | 38 | -0.8351 | `source_quality_workorder` |
| `would_limit_fill` | `false` | 298 | 29 | -0.0318 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 77 | 26 | -0.0168 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 77 | 26 | -0.4946 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 63 | 19 | -0.9123 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_10s_plus` | 57 | 18 | -0.9212 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 66 | 18 | -0.2072 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 32 | 16 | -0.557 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_context_missing` | 23 | 15 | -0.5949 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 48 | 15 | -0.7891 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 11 | 8 | -1.1411 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 8 | 4 | 0.3807 | `keep_collecting` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 3 | 3 | -3.8922 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 4 | 3 | -0.1616 | `source_quality_workorder` |
| `overbought_guard_action` | `would_block` | 3 | 3 | -3.8922 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 4 | 2 | -1.2352 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=pullback_or_rebreak_not_confirmed|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 2 | 2 | -4.7008 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 37, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 250 | 93 | -1.2234 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 250 | 93 | -1.2234 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 243 | 90 | -1.255 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 64 | 59 | -2.0925 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 58 | 58 | -2.1138 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 11 | 10 | 0.0641 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 11 | 9 | -0.216 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 9 | 9 | 0.1186 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 8 | 8 | -0.2999 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 7 | 7 | 0.5147 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 7 | 7 | 0.5147 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 5 | 5 | 1.7127 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 5 | 5 | 1.7127 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 10 | 3 | -0.395 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 3 | 3 | -0.395 | `hold_sample` |
| `holding_action` | `BUY` | 1 | 1 | -0.4267 | `hold_sample` |
| `holding_action` | `DROP` | 3 | 1 | 0.4555 | `hold_sample` |
| `holding_action` | `holding_action_not_applicable_at_start` | 3 | 1 | -0.8553 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | -0.4267 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=DROP|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 0.4555 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1 | 1 | -0.8553 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 15 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 5 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 9 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 157 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 15 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=DROP|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 153 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_180_600s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos080_pos150|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 61, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 141 | 141 | -1.5384 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 120 | 120 | -0.8851 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 120 | 120 | -0.8851 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 120 | 120 | -0.8851 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 83 | 83 | -1.1728 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 81 | 81 | -1.3081 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 44 | 44 | -1.8721 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 38 | 38 | -0.5083 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 32 | 32 | -1.6249 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 31 | 31 | -0.5674 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 30 | 30 | -0.9993 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 27 | 27 | 0.4363 | `candidate_recovery_or_relax` |
| `exit_outcome` | `NEUTRAL` | 19 | 19 | -1.2622 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 18 | 18 | -2.3488 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 3986 | 15 | -0.323 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 15 | 15 | -0.323 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 15 | 15 | -0.323 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 15 | 15 | -1.3406 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 13 | 13 | -0.0845 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 11 | 11 | -1.817 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 10 | 10 | 0.0321 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 7 | 7 | 0.5147 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 7 | 7 | 2.3404 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_hard_stop_pct` | 6 | 6 | -4.6866 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 6 | 6 | -0.19 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 5 | 5 | -0.966 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 5 | 5 | -0.0725 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 4 | 4 | 0.225 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 4 | 4 | 1.302 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 4 | 4 | 1.0808 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 3 | 3 | -1.4157 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 3 | 3 | 0.055 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 3 | 3 | -4.0827 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 3 | 3 | -0.2673 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos150_pos300_plus` | 2 | 2 | 3.9095 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 2 | 2 | -5.5389 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 2 | 2 | -1.748 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 2 | 2 | -0.2439 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 2 | 2 | -0.5016 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 2 | 2 | -0.3362 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 418, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 5115 | 5098 | None | -1.0803 | 0.0789 | `hold_sample` |
| `arm` | `AVG_DOWN` | 4966 | 4877 | None | -1.2442 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 4895 | 4806 | None | -1.2149 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 2960 | 2960 | None | -1.1112 | 0.1057 | `hold_sample` |
| `price_guard_reason` | `price_guard_none` | 2422 | 2380 | None | -0.9141 | 0.0925 | `hold_sample` |
| `qty_reason` | `qty_none` | 2382 | 2380 | None | -0.9141 | 0.0925 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 2424 | 2380 | None | -0.9141 | 0.0925 | `hold_sample` |
| `time_bucket` | `time_unknown` | 2424 | 2380 | None | -0.9141 | 0.0925 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 2269 | 2269 | None | -1.162 | 0.0 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 1828 | 1828 | None | -0.9537 | 0.0952 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 1432 | 1432 | None | -1.4078 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 1248 | 1248 | None | -1.0173 | 0.1049 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 927 | 927 | None | -1.0393 | 0.0874 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 694 | 694 | None | -0.4155 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 600 | 579 | None | 0.7737 | 0.9878 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 600 | 579 | None | 0.7737 | 0.9878 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 595 | 576 | None | -0.9192 | 0.0922 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 462 | 462 | None | -0.9412 | 0.0671 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 456 | 456 | None | -0.5162 | 0.3772 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 337 | 337 | None | 0.3847 | 0.9881 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 30 | 15 | -0.323 | -0.4307 | 0.2 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 15 | 15 | -0.323 | -0.4307 | 0.2 | `hold_sample` |
| `stage` | `exit` | 15 | 15 | -0.323 | -0.4307 | 0.2 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 30 | 15 | -0.323 | -0.4307 | 0.2 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 15 | 15 | -0.323 | -0.4307 | 0.2 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 28 | 14 | -0.2641 | -0.3521 | 0.2143 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 24 | 12 | -0.5038 | -0.6717 | 0.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 22 | 11 | -0.3778 | -0.5036 | 0.2727 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 18 | 9 | -0.325 | -0.4333 | 0.3333 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 7 | 7 | -0.1736 | -0.2314 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 14 | 7 | -0.1736 | -0.2314 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 10 | 5 | -0.3495 | -0.466 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 10 | 5 | -0.966 | -1.288 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 4 | 4 | -0.9206 | -1.2275 | 0.0 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 8 | 4 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
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
