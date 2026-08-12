# Lifecycle Decision Matrix - 2026-08-12

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-08-12_rolling5d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `3876`
- source_rows_total: `3885`
- retained_rows: `3876`
- dropped_rows_by_source: `{}`
- joined_rows: `1962`
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
- lifecycle_flow_bucket_count: `45`
- lifecycle_flow_complete_count: `19`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0079`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 1809 | 18 | -0.1731 | 0.0158 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 110 | 19 | -0.3886 | 0.3608 | `pass` | `NO_CHANGE` | False |
| `holding` | 20 | 19 | -0.7761 | 0.7632 | `pass` | `EXIT` | False |
| `scale_in` | 1904 | 1885 | -0.8984 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 33 | 21 | -0.7159 | 0.7158 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 45, 'complete_flow_count': 19, 'incomplete_flow_count': 2371, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 1803 | 1785 | -0.9736 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 101 | 100 | 0.4445 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:4e1fc29475` | 4 | 4 | -0.842 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:5159f83a5b` | 3 | 3 | -0.1136 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:5ad377bcf7` | 1 | 1 | -0.4211 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:7dd76f2392` | 1 | 1 | -2.1224 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:31a116e56b` | 1 | 1 | -0.7246 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:7664e5a914` | 1 | 1 | -0.1193 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:1fbcba9334` | 1 | 1 | 0.0719 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:f3f2837f26` | 1 | 1 | -1.6262 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:7e17ca9764` | 1 | 1 | -2.1951 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:1230ecd40d` | 1 | 1 | -0.0415 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:ce05b30c9f` | 1 | 1 | -0.9949 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:7946d42f06` | 1 | 1 | -2.063 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:db2aa0a4af` | 1 | 1 | -1.632 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:46ace3ddee` | 1 | 1 | 0.8311 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:62b3401904` | 1 | 1 | -0.1725 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:075ce13c92` | 1 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:f36cc32176` | 3 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_ai:c18e731ca8` | 12 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 232, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 174 | 18 | -0.1731 | -1.1878 | 0.3334 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_not_available` | 755 | 18 | -0.1731 | -1.1878 | 0.3334 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_not_available` | 581 | 18 | -0.1731 | -1.1878 | 0.3334 | `source_quality_workorder` |
| `strength_bucket` | `risk_context_not_available` | 163 | 18 | -0.1731 | -1.1878 | 0.3334 | `hold_no_edge` |
| `source_stage` | `scalp_sim_entry_ai_price_skip_order` | 163 | 18 | -0.1731 | -1.1878 | 0.3334 | `hold_no_edge` |
| `stale_bucket` | `stale_not_available` | 539 | 18 | -0.1731 | -1.1878 | 0.3334 | `source_quality_workorder` |
| `score_band` | `score_63_65` | 214 | 15 | -0.2021 | -0.8047 | 0.4 | `hold_no_edge` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 9 | 9 | 0.3854 | -1.5067 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1000_1200` | 73 | 9 | -0.2838 | -1.0044 | 0.3333 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 482 | 9 | -0.2838 | -1.0044 | 0.3333 | `hold_sample` |
| `time_bucket` | `time_0900_1000` | 349 | 7 | 0.5085 | -1.2871 | 0.2857 | `source_quality_workorder` |
| `exit_rule` | `scalp_trailing_take_profit` | 6 | 6 | -1.0254 | 0.5583 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_0900_1000` | 17 | 5 | 0.6121 | -0.7 | 0.4 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 3 | 3 | -0.1438 | -3.7233 | 0.0 | `hold_sample` |
| `score_band` | `score_60_62` | 25 | 3 | -0.0277 | -3.1033 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_0900_1000` | 5 | 2 | 0.2494 | -2.755 | 0.0 | `hold_sample` |
| `time_bucket` | `time_1200_1400` | 346 | 2 | -2.0597 | -1.665 | 0.5 | `source_quality_workorder` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1200_1400` | 2 | 1 | -0.5819 | -3.8 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1200_1400` | 28 | 1 | -3.5375 | 0.47 | 1.0 | `hold_sample` |
| `chosen_action` | `BUY_DEFENSIVE` | 49 | 0 | None | None | None | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 83, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 110 | 19 | -0.3886 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 108 | 19 | -0.3886 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 20 | 19 | -0.3886 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 20 | 19 | -0.3886 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 20 | 19 | -0.3886 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 20 | 19 | -0.3886 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 20 | 19 | -0.3886 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 20 | 19 | -0.3886 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 20 | 19 | -0.3886 | `keep_collecting` |
| `latency_state` | `simulated` | 20 | 19 | -0.3886 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 110 | 19 | -0.3886 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 20 | 19 | -0.3886 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 19 | 18 | -0.1731 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 19 | 18 | -0.1731 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 14 | 13 | 0.1022 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 13 | 13 | 0.1022 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 101 | 13 | 0.1022 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 13 | 13 | 0.1022 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 14 | 13 | 0.1022 | `keep_collecting` |
| `would_limit_fill` | `false` | 97 | 7 | -0.1609 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 7 | 7 | -0.1609 | `source_quality_workorder` |
| `liquidity_bucket` | `below_min_liquidity` | 7 | 6 | -1.452 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 7 | 6 | -1.452 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 6 | 6 | -1.452 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 6 | 6 | 0.4092 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 6 | 6 | 0.4092 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 6 | 6 | -1.452 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 7 | 6 | -1.452 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_3_10s` | 6 | 5 | -1.8367 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 4 | 4 | -1.2287 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 1 | 1 | -4.2687 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 2 | 1 | -4.2687 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 1 | 1 | 0.4716 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | 0.4716 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | -4.2687 | `source_quality_workorder` |
| `latency_state` | `danger` | 88 | 0 | None | `keep_collecting` |
| `price_resolution_bucket` | `defensive_limit` | 2 | 0 | None | `keep_collecting` |
| `submit_source_stage` | `entry_submit_revalidation_block` | 1 | 0 | None | `keep_collecting` |
| `submit_source_stage` | `latency_block` | 88 | 0 | None | `keep_collecting` |
| `latency_reason` | `latency_reason_unknown` | 2 | 0 | None | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 16, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 19 | 19 | -0.7761 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 19 | 19 | -0.7761 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 18 | 18 | -0.7046 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 12 | 12 | -0.9224 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 12 | 12 | -0.9224 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 5 | 5 | -0.8934 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 4 | 4 | -0.601 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 2 | 2 | 0.3948 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 0.3948 | `hold_sample` |
| `holding_action` | `holding_action_not_applicable_at_start` | 1 | 1 | -2.063 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | -2.063 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 1 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 30, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `exit_source_stage` | `sim_post_sell_evaluation` | 20 | 20 | -0.7431 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 12 | 12 | -0.9224 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 9 | 9 | -0.5694 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 8 | 8 | -0.8252 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 7 | 7 | -0.5254 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 6 | 6 | -1.3683 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 6 | 6 | -0.0083 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 5 | 5 | -0.8934 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 5 | 5 | -0.8726 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 4 | 4 | -0.1905 | `hold_no_edge` |
| `exit_rule` | `scalp_soft_stop_pct` | 3 | 3 | -1.9812 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 3 | 3 | -1.4732 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 2 | 2 | -0.1437 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 2 | 2 | 0.3948 | `hold_sample` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 2 | 2 | -0.1437 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 2 | 2 | -1.8743 | `hold_sample` |
| `exit_outcome` | `COMPLETED` | 1 | 1 | -0.1725 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 1 | 1 | -0.1725 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 1 | 1 | -0.1725 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=NEUTRAL|profit=profit_neg070_neg010` | 1 | 1 | -0.115 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 1 | 1 | -2.1951 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 1 | 1 | -0.0415 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 1 | 1 | -0.1193 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 1 | 1 | 0.8311 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 1 | 1 | 0.0719 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 12 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_context_noop` | 12 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 12 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_context_warning_not_applicable` | 12 | 0 | None | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=scalp_sim_panic_context_warning_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 12 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 167, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `price_guard_reason` | `price_guard_none` | 1904 | 1885 | None | -0.9714 | 0.052 | `hold_sample` |
| `qty_reason` | `qty_none` | 1885 | 1885 | None | -0.9714 | 0.052 | `hold_sample` |
| `time_bucket` | `time_unknown` | 1904 | 1885 | None | -0.9714 | 0.052 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 1883 | 1882 | None | -0.9734 | 0.0505 | `hold_sample` |
| `arm` | `AVG_DOWN` | 1803 | 1785 | None | -1.0492 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 1799 | 1781 | None | -1.0444 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 1392 | 1392 | None | -1.2157 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 1095 | 1095 | None | -1.0525 | 0.0137 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 1003 | 1003 | None | -0.9762 | 0.0489 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 1005 | 986 | None | -0.9047 | 0.0994 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 921 | 902 | None | -1.0402 | 0.0033 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 846 | 846 | None | -1.0833 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 453 | 453 | None | -0.8604 | 0.0861 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 426 | 426 | None | -0.8358 | 0.1503 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 365 | 365 | None | -0.493 | 0.0 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_1` | 326 | 326 | None | -1.196 | 0.0 | `hold_sample` |
| `ai_score_source` | `holding_ai_not_called` | 231 | 231 | None | -1.1775 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 227 | 227 | None | -0.9071 | 0.0309 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_2` | 224 | 224 | None | -1.0612 | 0.0 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_3` | 162 | 162 | None | -0.8431 | 0.0 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 15, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 1 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 1 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `stage` | `exit` | 1 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 1 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 1 | 0 | None | None | None | `hold_sample` |
| `stage` | `holding` | 1 | 0 | None | None | None | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_decision` | 1 | 0 | None | None | None | `hold_sample` |

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
