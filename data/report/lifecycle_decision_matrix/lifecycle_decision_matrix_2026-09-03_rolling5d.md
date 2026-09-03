# Lifecycle Decision Matrix - 2026-09-03

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-09-03_rolling5d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `9471`
- source_rows_total: `12957`
- retained_rows: `9471`
- dropped_rows_by_source: `{}`
- joined_rows: `4861`
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
- lifecycle_flow_bucket_count: `78`
- lifecycle_flow_complete_count: `42`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0059`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 2582 | 18 | -0.0175 | 0.0072 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 290 | 46 | -0.8035 | 0.1912 | `pass` | `NO_CHANGE` | False |
| `holding` | 55 | 46 | -1.0556 | 0.8989 | `pass` | `EXIT` | False |
| `scale_in` | 4680 | 4662 | -0.8609 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 1864 | 89 | -0.9915 | 0.1231 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 78, 'complete_flow_count': 42, 'incomplete_flow_count': 7123, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 4237 | 4221 | -1.011 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 443 | 441 | 0.5757 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:5ee2a7cfd7` | 5 | 5 | -1.216 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:0cb91a7ba6` | 4 | 4 | -0.8275 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:42bc391d5b` | 2 | 2 | -0.7738 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:a6af469504` | 2 | 2 | -0.56 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:8de6b2fa46` | 2 | 2 | -1.035 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:36904223da` | 2 | 2 | -0.715 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:7a29eed6f7` | 1 | 1 | -1.0614 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:f4d0891804` | 1 | 1 | -0.88 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_bl:44fb83e208` | 1 | 1 | -0.79 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_ai_c:4bb9b08477` | 1 | 1 | -0.45 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:441959da5f` | 1 | 1 | -1.677 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:d7ad29dfc9` | 1 | 1 | -0.44 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:e95b96a4e9` | 1 | 1 | -1.38 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:61bcc9f24b` | 1 | 1 | -0.79 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:b0bc92a886` | 1 | 1 | -0.98 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:e6cc63e69d` | 1 | 1 | -1.45 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:e629891351` | 1 | 1 | -1.11 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:b0018089a8` | 1 | 1 | -3.5005 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 238, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `NO_BUY_AI` | 1077 | 15 | 0.0125 | -1.6533 | 0.1333 | `hold_sample` |
| `stale_bucket` | `fresh` | 1234 | 15 | 0.0125 | -1.6533 | 0.1333 | `hold_sample` |
| `liquidity_bucket` | `liquidity_high` | 916 | 15 | 0.0125 | -1.6533 | 0.1333 | `hold_sample` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 2133 | 15 | 0.0125 | -1.6533 | 0.1333 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 945 | 11 | -0.0293 | -1.5773 | 0.0909 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 266 | 10 | -0.0264 | -1.321 | 0.1 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 10 | 10 | -0.1034 | -1.491 | 0.0 | `hold_sample` |
| `score_band` | `score_63_65` | 54 | 10 | -0.0167 | -1.107 | 0.2 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 717 | 10 | -0.2237 | -1.695 | 0.1 | `hold_sample` |
| `score_band` | `score_70p` | 156 | 6 | -0.0001 | -1.8767 | 0.3333 | `hold_sample` |
| `overbought_bucket` | `overbought_watch` | 550 | 5 | 0.0904 | -2.318 | 0.2 | `hold_sample` |
| `time_bucket` | `time_1200_1400` | 655 | 5 | -0.0061 | -1.514 | 0.2 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 4 | 4 | 0.2791 | 0.4 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 4 | 4 | -0.2469 | -1.4375 | 0.0 | `hold_sample` |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 153 | 3 | -0.1679 | -0.1967 | 0.6667 | `hold_sample` |
| `liquidity_bucket` | `liquidity_not_available` | 1568 | 3 | -0.1679 | -0.1967 | 0.6667 | `hold_sample` |
| `overbought_bucket` | `overbought_not_available` | 1442 | 3 | -0.1679 | -0.1967 | 0.6667 | `hold_sample` |
| `strength_bucket` | `risk_context_not_available` | 156 | 3 | -0.1679 | -0.1967 | 0.6667 | `hold_sample` |
| `source_stage` | `scalp_sim_entry_ai_price_skip_order` | 28 | 3 | -0.1679 | -0.1967 | 0.6667 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 3 | 3 | -0.0891 | -3.43 | 0.0 | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 107, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 278 | 46 | -0.8035 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 281 | 46 | -0.8035 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 51 | 46 | -0.8035 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 51 | 46 | -0.8035 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 51 | 46 | -0.8035 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 51 | 46 | -0.8035 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 51 | 46 | -0.8035 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 51 | 46 | -0.8035 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 51 | 46 | -0.8035 | `keep_collecting` |
| `latency_state` | `simulated` | 51 | 46 | -0.8035 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 278 | 46 | -0.8035 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 50 | 45 | -0.8179 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 42 | 37 | -1.112 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 38 | 33 | -1.0091 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 29 | 27 | -1.2837 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 28 | 27 | -1.2837 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 27 | 27 | -1.2837 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 28 | 27 | -1.2837 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 28 | 27 | -1.2837 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_3_10s` | 33 | 21 | -1.7882 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 23 | 19 | -0.1212 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 23 | 19 | -0.1212 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 241 | 19 | -0.1212 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 23 | 19 | -0.1212 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 23 | 19 | -0.1212 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 18 | 18 | -2.0152 | `source_quality_workorder` |
| `would_limit_fill` | `false` | 256 | 13 | 0.0414 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 15 | 11 | -0.0238 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 9 | 9 | -0.4442 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 8 | 8 | 0.5424 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_10s_plus` | 13 | 6 | 0.4821 | `keep_collecting` |
| `would_limit_fill` | `true` | 6 | 6 | -0.4733 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 4 | 4 | 0.0844 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 4 | 4 | -0.6675 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 4 | 4 | -0.4845 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 3 | 3 | -0.4262 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 2 | 2 | 0.3994 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 2 | 2 | -0.0849 | `source_quality_workorder` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 1 | 1 | -0.1581 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | 4.9886 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 26, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 50 | 46 | -1.0556 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 50 | 46 | -1.0556 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 44 | 40 | -1.3094 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 33 | 29 | -1.6538 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 28 | 28 | -1.6529 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 10 | 10 | -0.0682 | `hold_no_edge` |
| `holding_action` | `holding_action_not_applicable_at_start` | 6 | 6 | 0.6362 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 6 | 6 | -0.233 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 4 | 4 | 0.1789 | `hold_no_edge` |
| `profit_band` | `profit_pos080_pos150` | 3 | 3 | -1.3821 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 3 | 3 | -1.3821 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 3 | 2 | 0.4003 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 2 | 2 | 0.4003 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 1 | 1 | -1.35 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 1 | 1 | 4.7784 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 1 | 1 | -1.35 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1 | 1 | -1.677 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 4.7784 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 5 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 4 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 4 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 5 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 47, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 61 | 61 | -1.3653 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 47 | 47 | -0.9985 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 37 | 37 | -0.9473 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 37 | 37 | -0.9473 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 37 | 37 | -0.9473 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 28 | 28 | -1.0861 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 20 | 20 | -1.6049 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 18 | 18 | -0.0447 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 17 | 17 | -0.8728 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 14 | 14 | -2.4475 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 12 | 12 | -0.3306 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 11 | 11 | -0.0258 | `hold_no_edge` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 11 | 11 | -0.7925 | `hold_sample` |
| `exit_outcome` | `MISSED_UPSIDE` | 10 | 10 | 0.0008 | `hold_sample` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 9 | 9 | -1.0458 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 9 | 9 | -0.5156 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 9 | 9 | -2.6074 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 7 | 7 | -0.7449 | `hold_sample` |
| `exit_outcome` | `COMPLETED` | 5 | 5 | -1.254 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 5 | 5 | -1.254 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_lt_neg070` | 4 | 4 | -1.5356 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 4 | 4 | 0.1183 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 4 | 4 | -0.284 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 3 | 3 | -1.3821 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 3 | 3 | -0.9692 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 3 | 3 | -1.8092 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 3 | 3 | 0.1263 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 2 | 2 | -2.6854 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 2 | 2 | -1.705 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 1 | 1 | -1.35 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 1 | 1 | 4.7784 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 1 | 1 | -0.1275 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | -0.5956 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 1 | 1 | -2.6672 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | -0.4217 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=MISSED_UPSIDE|profit=profit_neg070_neg010` | 1 | 1 | 0.9211 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=NEUTRAL|profit=profit_lt_neg070` | 1 | 1 | -0.9741 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg070_neg010` | 1 | 1 | -0.1205 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | 0.3171 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 1 | 1 | 4.7784 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 320, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `price_guard_reason` | `price_guard_none` | 4679 | 4662 | None | -0.9498 | 0.0931 | `hold_sample` |
| `qty_reason` | `qty_none` | 4663 | 4662 | None | -0.9498 | 0.0931 | `hold_sample` |
| `time_bucket` | `time_unknown` | 4680 | 4662 | None | -0.9498 | 0.0931 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 4661 | 4659 | None | -0.9508 | 0.0927 | `hold_sample` |
| `arm` | `AVG_DOWN` | 4237 | 4221 | None | -1.107 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 4191 | 4175 | None | -1.0839 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 2806 | 2806 | None | -1.4462 | 0.0 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 2739 | 2739 | None | -0.9672 | 0.1044 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 2513 | 2495 | None | -0.8186 | 0.1739 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2358 | 2358 | None | -1.0786 | 0.112 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 2186 | 2168 | None | -1.1005 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 1337 | 1337 | None | -0.4565 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 1330 | 1330 | None | -1.1263 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 1248 | 1248 | None | -0.8825 | 0.0721 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_1` | 1137 | 1137 | None | -1.1722 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 1016 | 1016 | None | -0.6865 | 0.2815 | `hold_sample` |
| `ai_score_source` | `live` | 821 | 821 | None | -0.9899 | 0.1145 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 677 | 677 | None | -0.7219 | 0.0945 | `hold_sample` |
| `ai_score_source` | `holding_ai_not_called` | 487 | 487 | None | -0.813 | 0.0472 | `hold_sample` |
| `arm` | `PYRAMID` | 443 | 441 | None | 0.5548 | 0.9842 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 10 | 5 | -1.254 | -1.672 | 0.0 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 5 | 5 | -1.254 | -1.672 | 0.0 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 10 | 5 | -1.254 | -1.672 | 0.0 | `hold_sample` |
| `stage` | `exit` | 5 | 5 | -1.254 | -1.672 | 0.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 10 | 5 | -1.254 | -1.672 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 10 | 5 | -1.254 | -1.672 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 10 | 5 | -1.254 | -1.672 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 5 | 5 | -1.254 | -1.672 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 4 | 4 | -1.5356 | -2.0475 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 8 | 4 | -1.5356 | -2.0475 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 8 | 4 | -1.5356 | -2.0475 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 1 | 1 | -0.1275 | -0.17 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 2 | 1 | -0.1275 | -0.17 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 2 | 1 | -0.1275 | -0.17 | 0.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 5 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_lt_neg070` | 4 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 1 | 0 | None | None | None | `hold_sample` |
| `stage` | `holding` | 5 | 0 | None | None | None | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_decision` | 5 | 0 | None | None | None | `hold_sample` |

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
