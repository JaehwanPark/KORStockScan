# Lifecycle Decision Matrix - 2026-09-02

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-09-02_rolling5d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `6549`
- source_rows_total: `9063`
- retained_rows: `6549`
- dropped_rows_by_source: `{}`
- joined_rows: `3232`
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
- lifecycle_flow_bucket_count: `66`
- lifecycle_flow_complete_count: `30`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0063`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 1960 | 9 | 0.0266 | 0.0014 | `pass` | `NO_CHANGE` | False |
| `submit` | 214 | 32 | -1.0377 | 0.162 | `pass` | `NO_CHANGE` | False |
| `holding` | 40 | 32 | -1.0239 | 0.8546 | `pass` | `EXIT` | False |
| `scale_in` | 3097 | 3090 | -0.8877 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 1238 | 69 | -0.9847 | 0.1402 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 66, 'complete_flow_count': 30, 'incomplete_flow_count': 4763, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 2748 | 2742 | -1.073 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 349 | 348 | 0.5718 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:5ee2a7cfd7` | 4 | 4 | -1.1375 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:0cb91a7ba6` | 3 | 3 | -0.91 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:8de6b2fa46` | 2 | 2 | -1.035 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:f4d0891804` | 1 | 1 | -0.88 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_bl:44fb83e208` | 1 | 1 | -0.79 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_ai_c:4bb9b08477` | 1 | 1 | -0.45 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:a6af469504` | 1 | 1 | -0.46 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:d7ad29dfc9` | 1 | 1 | -0.44 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:61bcc9f24b` | 1 | 1 | -0.79 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:b0bc92a886` | 1 | 1 | -0.98 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:e6cc63e69d` | 1 | 1 | -1.45 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:e629891351` | 1 | 1 | -1.11 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:b0018089a8` | 1 | 1 | -3.5005 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:b31cc048c8` | 1 | 1 | -0.49 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:a74ce3066d` | 1 | 1 | -0.83 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:04a7285e92` | 1 | 1 | -0.95 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:d89fc00551` | 1 | 1 | -0.1275 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:36904223da` | 1 | 1 | -0.79 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 210, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `NO_BUY_AI` | 751 | 6 | 0.1239 | -1.3134 | 0.3333 | `hold_sample` |
| `stale_bucket` | `fresh` | 907 | 6 | 0.1239 | -1.3134 | 0.3333 | `hold_sample` |
| `liquidity_bucket` | `liquidity_high` | 636 | 6 | 0.1239 | -1.3134 | 0.3333 | `hold_sample` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 1635 | 6 | 0.1239 | -1.3134 | 0.3333 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 552 | 5 | -0.2395 | -1.59 | 0.2 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 662 | 5 | -0.0215 | -1.674 | 0.2 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 4 | 4 | 0.2791 | 0.4 | 1.0 | `hold_sample` |
| `score_band` | `score_70p` | 111 | 4 | -0.0394 | -1.1875 | 0.5 | `hold_sample` |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 125 | 3 | -0.1679 | -0.1967 | 0.6667 | `hold_sample` |
| `liquidity_bucket` | `liquidity_not_available` | 1250 | 3 | -0.1679 | -0.1967 | 0.6667 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 156 | 3 | 0.1494 | -0.9333 | 0.3333 | `hold_sample` |
| `overbought_bucket` | `overbought_not_available` | 1164 | 3 | -0.1679 | -0.1967 | 0.6667 | `hold_sample` |
| `overbought_bucket` | `overbought_watch` | 388 | 3 | 0.0984 | -1.6933 | 0.3333 | `hold_sample` |
| `strength_bucket` | `risk_context_not_available` | 128 | 3 | -0.1679 | -0.1967 | 0.6667 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 3 | 3 | -0.107 | -1.5 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_entry_ai_price_skip_order` | 19 | 3 | -0.1679 | -0.1967 | 0.6667 | `hold_sample` |
| `score_band` | `score_63_65` | 29 | 3 | 0.1817 | -0.22 | 0.6667 | `hold_sample` |
| `stale_bucket` | `stale_not_available` | 821 | 3 | -0.1679 | -0.1967 | 0.6667 | `hold_sample` |
| `time_bucket` | `time_0900_1000` | 313 | 2 | 0.7238 | 0.375 | 1.0 | `hold_sample` |
| `time_bucket` | `time_1200_1400` | 484 | 2 | -0.0052 | -0.635 | 0.5 | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 101, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 205 | 32 | -1.0377 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 209 | 32 | -1.0377 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 37 | 32 | -1.0377 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 37 | 32 | -1.0377 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 37 | 32 | -1.0377 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 37 | 32 | -1.0377 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 37 | 32 | -1.0377 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 37 | 32 | -1.0377 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 37 | 32 | -1.0377 | `keep_collecting` |
| `latency_state` | `simulated` | 37 | 32 | -1.0377 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 205 | 32 | -1.0377 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 36 | 31 | -1.0661 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 32 | 27 | -1.411 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 25 | 24 | -1.4125 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 25 | 24 | -1.4125 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 24 | 24 | -1.4125 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 25 | 24 | -1.4125 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 25 | 24 | -1.4125 | `source_quality_workorder` |
| `price_below_bid_bucket` | `not_below_bid` | 27 | 22 | -1.3549 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 28 | 20 | -1.8533 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 18 | 18 | -2.0152 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_ok` | 12 | 8 | 0.0865 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 12 | 8 | 0.0865 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 176 | 8 | 0.0865 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 12 | 8 | 0.0865 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 12 | 8 | 0.0865 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 7 | 7 | -0.4942 | `keep_collecting` |
| `would_limit_fill` | `false` | 188 | 7 | 0.0779 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 10 | 6 | -0.0509 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_context_missing` | 4 | 4 | 1.2618 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_10s_plus` | 8 | 4 | 0.7917 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 3 | 3 | 0.0196 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 2 | 2 | -0.8318 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 2 | 2 | -0.3961 | `source_quality_workorder` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 1 | 1 | -0.1581 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 1 | 1 | 0.851 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 1 | 1 | 0.1467 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | 4.9886 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=pullback_or_rebreak_not_confirmed|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | -0.1581 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 1 | 1 | 0.1467 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 25, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 36 | 32 | -1.0239 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 36 | 32 | -1.0239 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 32 | 28 | -1.3665 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 19 | 16 | -2.0105 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 16 | 16 | -2.0105 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 9 | 9 | -0.0756 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 6 | 6 | -0.233 | `hold_no_edge` |
| `holding_action` | `holding_action_not_applicable_at_start` | 4 | 4 | 1.3739 | `hold_no_edge` |
| `profit_band` | `profit_pos080_pos150` | 3 | 3 | -1.3821 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 3 | 3 | -1.3821 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 3 | 3 | 0.2391 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 3 | 2 | 0.4003 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 2 | 2 | 0.4003 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 1 | 1 | -1.35 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 1 | 1 | 4.7784 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 1 | 1 | -1.35 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 4.7784 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 4 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 3 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 4 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 45, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 46 | 46 | -1.4191 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 34 | 34 | -0.9979 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 31 | 31 | -0.9626 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 31 | 31 | -0.9626 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 31 | 31 | -0.9626 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 26 | 26 | -1.0577 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 17 | 17 | -0.0473 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 14 | 14 | -1.7755 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 12 | 12 | -0.8765 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 10 | 10 | -0.0283 | `hold_no_edge` |
| `exit_rule` | `scalp_soft_stop_pct` | 10 | 10 | -2.7555 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 8 | 8 | 0.1809 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 8 | 8 | -0.2084 | `hold_no_edge` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 8 | 8 | -0.9149 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 7 | 7 | -2.7334 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 5 | 5 | -0.468 | `hold_sample` |
| `exit_outcome` | `COMPLETED` | 4 | 4 | -1.0444 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 4 | 4 | -1.0444 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 4 | 4 | -0.284 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 3 | 3 | -1.3821 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 3 | 3 | -0.809 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_lt_neg070` | 3 | 3 | -1.35 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 3 | 3 | -0.809 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 3 | 3 | 0.1583 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 3 | 3 | 0.1263 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 2 | 2 | -1.9473 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 2 | 2 | -1.705 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 1 | 1 | -1.35 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 1 | 1 | 4.7784 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 1 | 1 | -0.1275 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 1 | 1 | -2.6672 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | -0.4217 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=MISSED_UPSIDE|profit=profit_neg070_neg010` | 1 | 1 | 0.9211 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=NEUTRAL|profit=profit_lt_neg070` | 1 | 1 | -0.9741 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | -4.527 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg070_neg010` | 1 | 1 | -0.1205 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | 0.3171 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 1 | 1 | 4.7784 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 1 | 1 | -0.7361 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300` | 1 | 1 | -1.35 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 279, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `price_guard_reason` | `price_guard_none` | 3097 | 3090 | None | -0.9822 | 0.1104 | `hold_sample` |
| `qty_reason` | `qty_none` | 3090 | 3090 | None | -0.9822 | 0.1104 | `hold_sample` |
| `time_bucket` | `time_unknown` | 3097 | 3090 | None | -0.9822 | 0.1104 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 3090 | 3089 | None | -0.9825 | 0.1104 | `hold_sample` |
| `arm` | `AVG_DOWN` | 2748 | 2742 | None | -1.177 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 2712 | 2706 | None | -1.1495 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 1890 | 1890 | None | -1.5262 | 0.0 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 1700 | 1700 | None | -0.991 | 0.1341 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 1707 | 1700 | None | -0.8252 | 0.2006 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 1478 | 1478 | None | -1.1424 | 0.1394 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 1398 | 1391 | None | -1.1734 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 850 | 850 | None | -1.2536 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 836 | 836 | None | -0.9193 | 0.0825 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 803 | 803 | None | -0.4233 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 746 | 746 | None | -0.6035 | 0.319 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_1` | 709 | 709 | None | -1.268 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 577 | 577 | None | -1.0819 | 0.1161 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 490 | 490 | None | -0.7353 | 0.1041 | `hold_sample` |
| `ai_score_source` | `holding_ai_not_called` | 354 | 354 | None | -0.8328 | 0.0621 | `hold_sample` |
| `arm` | `PYRAMID` | 349 | 348 | None | 0.5531 | 0.9799 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 19, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 8 | 4 | -1.0444 | -1.3925 | 0.0 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 4 | 4 | -1.0444 | -1.3925 | 0.0 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 8 | 4 | -1.0444 | -1.3925 | 0.0 | `hold_sample` |
| `stage` | `exit` | 4 | 4 | -1.0444 | -1.3925 | 0.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 8 | 4 | -1.0444 | -1.3925 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 8 | 4 | -1.0444 | -1.3925 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 8 | 4 | -1.0444 | -1.3925 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 4 | 4 | -1.0444 | -1.3925 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 3 | 3 | -1.35 | -1.8 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 6 | 3 | -1.35 | -1.8 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 6 | 3 | -1.35 | -1.8 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 1 | 1 | -0.1275 | -0.17 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 2 | 1 | -0.1275 | -0.17 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 2 | 1 | -0.1275 | -0.17 | 0.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 4 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_lt_neg070` | 3 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 1 | 0 | None | None | None | `hold_sample` |
| `stage` | `holding` | 4 | 0 | None | None | None | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_decision` | 4 | 0 | None | None | None | `hold_sample` |

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
