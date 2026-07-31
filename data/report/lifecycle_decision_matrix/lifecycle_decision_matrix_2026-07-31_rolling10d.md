# Lifecycle Decision Matrix - 2026-07-31

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-31_rolling10d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `3062`
- source_rows_total: `7159`
- retained_rows: `3062`
- dropped_rows_by_source: `{}`
- joined_rows: `1118`
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
- lifecycle_flow_bucket_count: `98`
- lifecycle_flow_complete_count: `25`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0137`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 1533 | 14 | -0.1651 | 0.0099 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 257 | 15 | -0.0859 | 0.0512 | `pass` | `NO_CHANGE` | False |
| `holding` | 46 | 15 | -0.782 | 0.2288 | `pass` | `EXIT` | False |
| `scale_in` | 1033 | 1027 | -0.6951 | 0.994 | `pass` | `NO_CHANGE` | False |
| `exit` | 193 | 47 | -0.7233 | 0.5481 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 98, 'complete_flow_count': 25, 'incomplete_flow_count': 1798, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 918 | 912 | -0.828 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 115 | 115 | 0.3585 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:ac760bc3a4` | 9 | 9 | -0.84 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:62b3401904` | 6 | 6 | -0.1725 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:f44ea1e4fd` | 2 | 2 | -1.28 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:ddd55828ec` | 1 | 1 | -0.55 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:d65aac5eca` | 1 | 1 | -0.35 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:f58154b780` | 1 | 1 | -1.11 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:b75bf201fa` | 1 | 1 | -1.3 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:5159f83a5b` | 1 | 1 | -1.1229 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:38511f6f01` | 1 | 1 | -0.6279 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_ai:5f3f5e5611` | 1 | 1 | -1.02 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:a6f85bdcc6` | 1 | 1 | -0.422 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:57aa592422` | 1 | 1 | -0.96 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:eb99aaba9b` | 1 | 1 | -0.47 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:0b436f64c2` | 1 | 1 | -0.96 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:cb6ed22b69` | 1 | 1 | 0.33 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:a5ddbd8b87` | 1 | 1 | -0.5 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:63a0b8330e` | 1 | 1 | -2.5775 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:a1f0075e93` | 1 | 1 | -1.02 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 240, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 9 | 9 | 0.1314 | -1.4633 | 0.0 | `hold_sample` |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 130 | 7 | -0.6853 | -1.3771 | 0.1428 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_not_available` | 982 | 7 | -0.6853 | -1.3771 | 0.1428 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_normal` | 346 | 7 | 0.355 | -1.2034 | 0.1429 | `hold_sample` |
| `overbought_bucket` | `overbought_not_available` | 845 | 7 | -0.6853 | -1.3771 | 0.1428 | `source_quality_workorder` |
| `strength_bucket` | `risk_context_not_available` | 89 | 7 | -0.6853 | -1.3771 | 0.1428 | `hold_sample` |
| `source_stage` | `scalp_sim_entry_ai_price_skip_order` | 89 | 7 | -0.6853 | -1.3771 | 0.1428 | `hold_sample` |
| `score_band` | `score_lt60` | 1289 | 7 | -0.0674 | -1.0057 | 0.2857 | `source_quality_workorder` |
| `stale_bucket` | `stale_not_available` | 622 | 7 | -0.6853 | -1.3771 | 0.1428 | `source_quality_workorder` |
| `time_bucket` | `time_0900_1000` | 388 | 7 | -0.1508 | -0.7549 | 0.2857 | `source_quality_workorder` |
| `chosen_action` | `NO_BUY_AI` | 713 | 6 | 0.4845 | -1.22 | 0.1667 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_high` | 480 | 6 | 0.4845 | -1.22 | 0.1667 | `hold_sample` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 1107 | 6 | 0.4845 | -1.22 | 0.1667 | `source_quality_workorder` |
| `time_bucket` | `time_1000_1200` | 407 | 6 | -0.0283 | -1.455 | 0.0 | `source_quality_workorder` |
| `score_band` | `score_63_65` | 94 | 4 | -0.2033 | -1.095 | 0.0 | `hold_sample` |
| `stale_bucket` | `stale_high` | 156 | 4 | 0.5305 | -1.4875 | 0.0 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 388 | 4 | 0.4107 | -1.0925 | 0.25 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 3 | 3 | -0.6619 | 0.0867 | 0.6667 | `hold_sample` |
| `stale_bucket` | `fresh` | 467 | 2 | 0.3924 | -0.685 | 0.5 | `hold_sample` |
| `strength_bucket` | `neutral_strength_momentum` | 755 | 2 | 0.6321 | -1.475 | 0.0 | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 112, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 191 | 15 | -0.0859 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 38 | 15 | -0.0859 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 236 | 15 | -0.0859 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 39 | 15 | -0.0859 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 39 | 15 | -0.0859 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 39 | 15 | -0.0859 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 39 | 15 | -0.0859 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 39 | 15 | -0.0859 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 39 | 15 | -0.0859 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 39 | 15 | -0.0859 | `keep_collecting` |
| `latency_state` | `simulated` | 39 | 15 | -0.0859 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 191 | 15 | -0.0859 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 39 | 15 | -0.0859 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 35 | 12 | 0.0737 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 35 | 12 | 0.0737 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 181 | 12 | 0.0737 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 35 | 12 | 0.0737 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 35 | 12 | 0.0737 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 13 | 9 | -0.4662 | `keep_collecting` |
| `would_limit_fill` | `false` | 241 | 8 | -0.204 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 26 | 6 | 0.4845 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 6 | 4 | -0.8075 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 17 | 4 | 0.3995 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 12 | 4 | 0.629 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 4 | 3 | -0.7244 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 4 | 3 | -0.7244 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 4 | 3 | -0.7244 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 4 | 3 | -0.7244 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 4 | 3 | -0.7244 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_3_10s` | 15 | 2 | -1.1685 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 4 | 2 | 0.6037 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 8 | 2 | 0.6543 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 2 | 2 | -1.1685 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_10s_plus` | 5 | 1 | 0.1637 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | 0.1637 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 1 | 0 | None | `keep_collecting` |
| `latency_state` | `caution` | 41 | 0 | None | `keep_collecting` |
| `latency_reason` | `caution_normal_entry_allowed` | 41 | 0 | None | `keep_collecting` |
| `latency_state` | `danger` | 154 | 0 | None | `keep_collecting` |
| `price_resolution_bucket` | `defensive_limit` | 53 | 0 | None | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 23, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 39 | 15 | -0.782 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 39 | 15 | -0.782 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 36 | 13 | -0.7929 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 12 | 12 | -0.9022 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 11 | 11 | -0.8361 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 3 | 3 | -0.3012 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 2 | 2 | -0.5551 | `hold_sample` |
| `holding_action` | `BUY` | 1 | 1 | 0.2066 | `hold_sample` |
| `holding_action` | `holding_action_not_applicable_at_start` | 2 | 1 | -1.6295 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 0.2066 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1 | 1 | -1.6295 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 7 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 5 | 0 | None | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 7 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 24 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 7 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 23 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_180_600s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 5 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 35, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 30 | 30 | -0.9671 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 26 | 26 | -0.83 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 26 | 26 | -0.83 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 26 | 26 | -0.83 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 19 | 19 | -0.9847 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 14 | 14 | -0.8004 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 13 | 13 | -0.339 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 9 | 9 | -0.711 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 9 | 9 | -0.6772 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `COMPLETED` | 7 | 7 | -0.1725 | `hold_sample` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 7 | 7 | -0.1725 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 7 | 7 | -0.1725 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 7 | 7 | -0.1725 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 6 | 6 | -0.5333 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 6 | 6 | -0.5668 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 4 | 4 | -0.1434 | `hold_sample` |
| `exit_outcome` | `NEUTRAL` | 3 | 3 | -0.9716 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 3 | 3 | -0.3012 | `hold_sample` |
| `exit_outcome` | `GOOD_EXIT` | 2 | 2 | -0.9458 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 2 | 2 | -2.1035 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 2 | 2 | -0.6426 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 2 | 2 | -0.2107 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 1 | 1 | 0.33 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 1 | 1 | -1.4093 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | -2.5775 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 1 | 1 | -1.6295 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 1 | 1 | -0.4823 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 146 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_context_noop` | 146 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_euphoria_context_noop` | 117 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_euphoria_context_noop_not_applicable` | 117 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 29 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_context_warning_not_applicable` | 29 | 0 | None | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_euphoria_context_noop|rule=scalp_sim_euphoria_context_noop_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 117 | 0 | None | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=scalp_sim_panic_context_warning_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 29 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 173, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `price_guard_reason` | `price_guard_none` | 1032 | 1027 | None | -0.7851 | 0.112 | `hold_sample` |
| `qty_reason` | `qty_none` | 1028 | 1027 | None | -0.7851 | 0.112 | `hold_sample` |
| `time_bucket` | `time_unknown` | 1033 | 1027 | None | -0.7851 | 0.112 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 1024 | 1024 | None | -0.7838 | 0.1123 | `hold_sample` |
| `arm` | `AVG_DOWN` | 918 | 912 | None | -0.9248 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 911 | 905 | None | -0.9059 | 0.0 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 769 | 763 | None | -0.6974 | 0.1507 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 536 | 536 | None | -1.2778 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 527 | 527 | None | -0.8566 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 510 | 510 | None | -0.8967 | 0.0706 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 353 | 353 | None | -0.4448 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 337 | 337 | None | -1.0231 | 0.0742 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 329 | 329 | None | -0.6245 | 0.2219 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 303 | 303 | None | -0.7103 | 0.1584 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 270 | 264 | None | -1.039 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 234 | 234 | None | -0.3443 | 0.4914 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 211 | 211 | None | -0.5552 | 0.1896 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 143 | 143 | None | -0.739 | 0.014 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 138 | 138 | None | 0.2578 | 0.8333 | `hold_sample` |
| `arm` | `PYRAMID` | 115 | 115 | None | 0.3222 | 1.0 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 17, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 14 | 7 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 7 | 7 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 7 | 7 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 14 | 7 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 14 | 7 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `stage` | `exit` | 7 | 7 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 14 | 7 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 14 | 7 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 14 | 7 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 7 | 7 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 10 | 5 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 7 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 7 | 0 | None | None | None | `hold_sample` |
| `stage` | `holding` | 7 | 0 | None | None | None | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_decision` | 7 | 0 | None | None | None | `hold_sample` |

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
