# Lifecycle Decision Matrix - 2026-07-30

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-30_rolling10d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `2265`
- source_rows_total: `6092`
- retained_rows: `2265`
- dropped_rows_by_source: `{}`
- joined_rows: `745`
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
- lifecycle_flow_bucket_count: `83`
- lifecycle_flow_complete_count: `23`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0185`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 1172 | 11 | 0.0723 | 0.0122 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 286 | 12 | 0.1515 | 0.059 | `pass` | `ALLOW_SUBMIT` | False |
| `holding` | 43 | 12 | -0.6168 | 0.241 | `pass` | `EXIT` | False |
| `scale_in` | 665 | 664 | -0.4961 | 0.9907 | `pass` | `NO_CHANGE` | False |
| `exit` | 99 | 46 | -0.6667 | 0.5624 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 83, 'complete_flow_count': 23, 'incomplete_flow_count': 1222, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 569 | 568 | -0.6516 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 96 | 96 | 0.4239 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:ac760bc3a4` | 9 | 9 | -0.84 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:62b3401904` | 7 | 7 | -0.1725 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:f44ea1e4fd` | 2 | 2 | -1.28 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:ddd55828ec` | 1 | 1 | -0.55 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:d65aac5eca` | 1 | 1 | -0.35 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:f58154b780` | 1 | 1 | -1.11 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:b75bf201fa` | 1 | 1 | -1.3 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_ai:5f3f5e5611` | 1 | 1 | -1.02 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:a6f85bdcc6` | 1 | 1 | -0.422 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:57aa592422` | 1 | 1 | -0.96 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:eb99aaba9b` | 1 | 1 | -0.47 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:0b436f64c2` | 1 | 1 | -0.96 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:cb6ed22b69` | 1 | 1 | 0.33 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:a5ddbd8b87` | 1 | 1 | -0.5 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:a1f0075e93` | 1 | 1 | -1.02 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:0b7151ca7a` | 1 | 1 | -0.83 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:e48ea83ea5` | 1 | 1 | -0.1725 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:661dd5007a` | 6 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 179, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 8 | 8 | 0.2441 | -1.4663 | 0.0 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 240 | 7 | 0.355 | -1.2034 | 0.1429 | `hold_sample` |
| `score_band` | `score_lt60` | 1015 | 7 | -0.0674 | -1.0057 | 0.2857 | `source_quality_workorder` |
| `chosen_action` | `NO_BUY_AI` | 414 | 6 | 0.4845 | -1.22 | 0.1667 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_high` | 264 | 6 | 0.4845 | -1.22 | 0.1667 | `hold_sample` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 990 | 6 | 0.4845 | -1.22 | 0.1667 | `source_quality_workorder` |
| `time_bucket` | `time_0900_1000` | 241 | 6 | 0.0324 | -0.8807 | 0.3333 | `source_quality_workorder` |
| `time_bucket` | `time_1000_1200` | 362 | 5 | 0.1202 | -1.458 | 0.0 | `source_quality_workorder` |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 54 | 4 | -0.4224 | -1.0375 | 0.25 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_not_available` | 857 | 4 | -0.4224 | -1.0375 | 0.25 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_not_available` | 825 | 4 | -0.4224 | -1.0375 | 0.25 | `source_quality_workorder` |
| `strength_bucket` | `risk_context_not_available` | 14 | 4 | -0.4224 | -1.0375 | 0.25 | `hold_sample` |
| `source_stage` | `scalp_sim_entry_ai_price_skip_order` | 14 | 4 | -0.4224 | -1.0375 | 0.25 | `hold_sample` |
| `stale_bucket` | `stale_high` | 156 | 4 | 0.5305 | -1.4875 | 0.0 | `hold_sample` |
| `stale_bucket` | `stale_not_available` | 538 | 4 | -0.4224 | -1.0375 | 0.25 | `source_quality_workorder` |
| `strength_bucket` | `weak_strength_momentum` | 164 | 4 | 0.4107 | -1.0925 | 0.25 | `hold_sample` |
| `stale_bucket` | `fresh` | 198 | 2 | 0.3924 | -0.685 | 0.5 | `hold_sample` |
| `strength_bucket` | `neutral_strength_momentum` | 686 | 2 | 0.6321 | -1.475 | 0.0 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 2 | 2 | -0.3678 | 0.13 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 42 | 2 | 0.6038 | -1.485 | 0.0 | `hold_sample` |

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
| `actual_order_submitted` | `false` | 218 | 12 | 0.1515 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 34 | 12 | 0.1515 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 260 | 12 | 0.1515 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 35 | 12 | 0.1515 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 35 | 12 | 0.1515 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 35 | 12 | 0.1515 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 35 | 12 | 0.1515 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 35 | 12 | 0.1515 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 35 | 12 | 0.1515 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 35 | 12 | 0.1515 | `keep_collecting` |
| `latency_state` | `simulated` | 35 | 12 | 0.1515 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 218 | 12 | 0.1515 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 35 | 12 | 0.1515 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 33 | 11 | 0.1505 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 33 | 11 | 0.1505 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 208 | 11 | 0.1505 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 33 | 11 | 0.1505 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 33 | 11 | 0.1505 | `keep_collecting` |
| `would_limit_fill` | `false` | 272 | 7 | -0.123 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 9 | 6 | -0.1814 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 26 | 6 | 0.4845 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 17 | 4 | 0.3995 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 12 | 4 | 0.629 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 4 | 3 | -0.8198 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 4 | 2 | 0.6037 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 8 | 2 | 0.6543 | `source_quality_workorder` |
| `liquidity_bucket` | `below_min_liquidity` | 2 | 1 | 0.1637 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 2 | 1 | 0.1637 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_10s_plus` | 5 | 1 | 0.1637 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 2 | 1 | 0.1637 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | 0.1637 | `source_quality_workorder` |
| `liquidity_guard_action` | `would_block` | 2 | 1 | 0.1637 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 2 | 1 | 0.1637 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 1 | 0 | None | `keep_collecting` |
| `latency_state` | `caution` | 38 | 0 | None | `keep_collecting` |
| `latency_reason` | `caution_normal_entry_allowed` | 38 | 0 | None | `keep_collecting` |
| `latency_state` | `danger` | 187 | 0 | None | `keep_collecting` |
| `price_resolution_bucket` | `defensive_limit` | 57 | 0 | None | `keep_collecting` |
| `submit_source_stage` | `entry_submit_revalidation_block` | 8 | 0 | None | `keep_collecting` |
| `broker_order_forbidden` | `false` | 68 | 0 | None | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 23, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 35 | 12 | -0.6168 | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 35 | 12 | -0.6168 | `hold_sample` |
| `holding_action` | `WAIT` | 32 | 10 | -0.5979 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 10 | 10 | -0.7126 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 9 | 9 | -0.6108 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 2 | 2 | -0.1379 | `hold_sample` |
| `holding_action` | `BUY` | 1 | 1 | 0.2066 | `hold_sample` |
| `holding_action` | `holding_action_not_applicable_at_start` | 2 | 1 | -1.6295 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 0.2066 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | -0.4823 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1 | 1 | -1.6295 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 8 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 5 | 0 | None | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 8 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 23 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 8 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 22 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_180_600s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 5 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 34, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 29 | 29 | -0.9015 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 27 | 27 | -0.83 | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 27 | 27 | -0.83 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 27 | 27 | -0.83 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 20 | 20 | -0.977 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 14 | 14 | -0.3271 | `hold_sample` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 11 | 11 | -0.6252 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `COMPLETED` | 8 | 8 | -0.1725 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 8 | 8 | -0.6215 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 8 | 8 | -0.1725 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 8 | 8 | -0.1725 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 8 | 8 | -0.1725 | `hold_sample` |
| `exit_outcome` | `MISSED_UPSIDE` | 6 | 6 | -0.3452 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 6 | 6 | -0.5333 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 5 | 5 | -0.4555 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 3 | 3 | -0.9716 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 3 | 3 | 0.0181 | `hold_sample` |
| `exit_outcome` | `GOOD_EXIT` | 2 | 2 | -0.9458 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 2 | 2 | -0.1379 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 2 | 2 | -0.6426 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 1 | 1 | -1.6295 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 1 | 1 | 0.33 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 1 | 1 | -1.4093 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 1 | 1 | -1.6295 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 1 | 1 | -0.4823 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 1 | 1 | 0.2066 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 53 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_context_noop` | 53 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_euphoria_context_noop` | 43 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_euphoria_context_noop_not_applicable` | 43 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 10 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_context_warning_not_applicable` | 10 | 0 | None | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_euphoria_context_noop|rule=scalp_sim_euphoria_context_noop_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 43 | 0 | None | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=scalp_sim_panic_context_warning_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 10 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 152, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `price_guard_reason` | `price_guard_none` | 665 | 664 | None | -0.5735 | 0.1446 | `hold_sample` |
| `qty_reason` | `qty_none` | 664 | 664 | None | -0.5735 | 0.1446 | `hold_sample` |
| `time_bucket` | `time_unknown` | 665 | 664 | None | -0.5735 | 0.1446 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 661 | 661 | None | -0.5705 | 0.1452 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 598 | 597 | None | -0.5636 | 0.1608 | `hold_sample` |
| `arm` | `AVG_DOWN` | 569 | 568 | None | -0.7359 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 566 | 565 | None | -0.722 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 455 | 455 | None | -0.7596 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 288 | 288 | None | -0.4388 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 271 | 271 | None | -1.0747 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 268 | 268 | None | -0.6077 | 0.0821 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 243 | 243 | None | -0.4701 | 0.2716 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 206 | 206 | None | -0.6261 | 0.1262 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 163 | 163 | None | -0.4806 | 0.2086 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 147 | 147 | None | -0.4948 | 0.2109 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 135 | 135 | None | 0.0098 | 0.6741 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 123 | 123 | None | -0.6716 | 0.0406 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 100 | 100 | None | 0.2891 | 0.91 | `hold_sample` |
| `arm` | `PYRAMID` | 96 | 96 | None | 0.3872 | 1.0 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 96 | 96 | None | 0.3872 | 1.0 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 16 | 8 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 8 | 8 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 8 | 8 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 16 | 8 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 16 | 8 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `stage` | `exit` | 8 | 8 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 16 | 8 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 16 | 8 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 16 | 8 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 8 | 8 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 10 | 5 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 4 | 2 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 8 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 8 | 0 | None | None | None | `hold_sample` |
| `stage` | `holding` | 8 | 0 | None | None | None | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_decision` | 8 | 0 | None | None | None | `hold_sample` |

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
