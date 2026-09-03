# Lifecycle Decision Matrix - 2026-09-03

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-09-03_rolling10d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `20320`
- source_rows_total: `25341`
- retained_rows: `20320`
- dropped_rows_by_source: `{}`
- joined_rows: `11074`
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
- lifecycle_flow_bucket_count: `133`
- lifecycle_flow_complete_count: `91`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0058`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 5148 | 49 | -0.2288 | 0.0104 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 562 | 103 | -0.8709 | 0.3011 | `pass` | `NO_CHANGE` | False |
| `holding` | 131 | 103 | -0.9669 | 0.8903 | `pass` | `EXIT` | False |
| `scale_in` | 10708 | 10640 | -0.8463 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 3771 | 179 | -0.9351 | 0.251 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 133, 'complete_flow_count': 91, 'incomplete_flow_count': 15547, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 9795 | 9730 | -0.97 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 913 | 910 | 0.4768 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:0cb91a7ba6` | 8 | 8 | -0.8838 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:5ee2a7cfd7` | 5 | 5 | -1.216 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:a6af469504` | 4 | 4 | -0.76 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:b31cc048c8` | 3 | 3 | -1.2133 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:f58154b780` | 2 | 2 | -1.12 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:7a29eed6f7` | 2 | 2 | -1.1552 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:42bc391d5b` | 2 | 2 | -0.7738 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:8de6b2fa46` | 2 | 2 | -1.035 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:36904223da` | 2 | 2 | -0.715 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:1793c3951c` | 1 | 1 | -0.6466 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:05c0ca21ce` | 1 | 1 | 0.045 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:f4d0891804` | 1 | 1 | -0.88 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:a9d1313d5d` | 1 | 1 | 0.1763 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:7ee2fdca81` | 1 | 1 | 0.0318 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_bl:44fb83e208` | 1 | 1 | -0.79 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_ai_c:4bb9b08477` | 1 | 1 | -0.45 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_bloc:ce21fab319` | 1 | 1 | -0.51 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:441959da5f` | 1 | 1 | -1.677 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 310, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `NO_BUY_AI` | 2261 | 46 | -0.2328 | -1.2948 | 0.2826 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_high` | 1921 | 46 | -0.2328 | -1.2948 | 0.2826 | `hold_sample` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 4275 | 46 | -0.2328 | -1.2948 | 0.2826 | `source_quality_workorder` |
| `stale_bucket` | `fresh` | 2611 | 45 | -0.2228 | -1.2882 | 0.2889 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 1421 | 29 | -0.1686 | -1.5283 | 0.2069 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 1944 | 29 | -0.1989 | -1.4672 | 0.2069 | `hold_sample` |
| `score_band` | `score_63_65` | 129 | 26 | -0.0904 | -1.1134 | 0.3077 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 606 | 24 | 0.0198 | -1.2404 | 0.1667 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 23 | 23 | -0.068 | -1.5269 | 0.0 | `hold_sample` |
| `overbought_bucket` | `overbought_watch` | 1119 | 17 | -0.1503 | -1.6653 | 0.3529 | `hold_sample` |
| `score_band` | `score_70p` | 284 | 15 | -0.3642 | -1.2987 | 0.3333 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 14 | 14 | -0.3881 | 0.515 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 15 | 11 | -0.1952 | -1.1655 | 0.1818 | `hold_sample` |
| `time_bucket` | `time_1200_1400` | 1252 | 11 | -0.3164 | -1.2964 | 0.3636 | `source_quality_workorder` |
| `strength_bucket` | `strong_strength_momentum` | 574 | 9 | 0.1346 | -1.6622 | 0.2222 | `hold_sample` |
| `strength_bucket` | `neutral_strength_momentum` | 2238 | 8 | -0.7691 | -0.2563 | 0.625 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 8 | 8 | -0.2984 | -3.3587 | 0.0 | `hold_sample` |
| `score_band` | `score_lt60` | 4718 | 6 | -0.468 | -1.2617 | 0.3333 | `source_quality_workorder` |
| `time_bucket` | `time_0900_1000` | 876 | 6 | -0.2106 | -0.5317 | 0.5 | `hold_sample` |
| `overbought_bucket` | `overbought_ok` | 483 | 4 | -1.5551 | 0.42 | 0.75 | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 120, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 524 | 103 | -0.8709 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 543 | 103 | -0.8709 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 123 | 103 | -0.8709 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 123 | 103 | -0.8709 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 123 | 103 | -0.8709 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 123 | 103 | -0.8709 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 123 | 103 | -0.8709 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 123 | 103 | -0.8709 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 123 | 103 | -0.8709 | `keep_collecting` |
| `latency_state` | `simulated` | 123 | 103 | -0.8709 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 524 | 103 | -0.8709 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 118 | 98 | -0.8313 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 102 | 83 | -0.9047 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 86 | 68 | -0.7062 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 73 | 54 | -0.394 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 73 | 54 | -0.394 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 56 | 53 | -1.4435 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 56 | 53 | -1.4435 | `source_quality_workorder` |
| `price_resolution_bucket` | `price_resolution_unknown` | 67 | 50 | -0.264 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 452 | 50 | -0.264 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 67 | 50 | -0.264 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 52 | 49 | -1.3965 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 49 | 49 | -1.3965 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 50 | 49 | -1.3965 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 76 | 41 | -1.752 | `keep_collecting` |
| `would_limit_fill` | `false` | 484 | 32 | -0.303 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 31 | 31 | -1.9743 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 41 | 28 | -0.3493 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 22 | 20 | -0.822 | `keep_collecting` |
| `would_limit_fill` | `true` | 22 | 18 | -0.1946 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 19 | 16 | -0.2083 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_context_missing` | 16 | 15 | -0.4254 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 14 | 14 | -1.6312 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_10s_plus` | 24 | 12 | -0.3893 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 8 | 8 | -0.0969 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 8 | 8 | -1.4105 | `source_quality_workorder` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 5 | 5 | -1.6467 | `keep_collecting` |
| `overbought_guard_action` | `would_block` | 5 | 5 | -1.6467 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_overbought_guard_would_block` | 4 | 4 | -2.0188 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 4 | 4 | 0.021 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 35, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 120 | 103 | -0.9669 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 120 | 103 | -0.9669 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 101 | 84 | -1.0733 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 66 | 59 | -1.4534 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 54 | 54 | -1.4166 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 25 | 24 | -0.3737 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 19 | 19 | -0.4963 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 16 | 16 | -0.3571 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 8 | 8 | -0.407 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 7 | 7 | -0.5075 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 6 | 6 | -0.8069 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 6 | 6 | -0.8069 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 8 | 5 | -0.3092 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 5 | 5 | -0.5373 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 5 | 5 | -1.8504 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 3 | 3 | -0.1404 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 2 | 2 | 2.5344 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 2 | 2 | -0.5625 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 2 | 2 | 2.5344 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 2 | 2 | -0.433 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 11 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 7 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 17 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 11 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 17 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_020_180s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_180_600s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 5 | 0 | None | `hold_sample` |
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
- summary: `{'bucket_count': 53, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 112 | 112 | -1.2875 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 104 | 104 | -0.9419 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 64 | 64 | -0.9208 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 64 | 64 | -0.9208 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 64 | 64 | -0.9208 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 46 | 46 | -1.0861 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 43 | 43 | -1.4093 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 42 | 42 | -0.2951 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 36 | 36 | -0.7517 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 26 | 26 | -0.328 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 26 | 26 | -0.4356 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 26 | 26 | -0.8527 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 26 | 26 | -2.1351 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 25 | 25 | -0.412 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 21 | 21 | -0.8746 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 18 | 18 | -0.4983 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 13 | 13 | -0.7391 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 12 | 12 | -2.5678 | `hold_sample` |
| `exit_outcome` | `COMPLETED` | 11 | 11 | -0.9532 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 11 | 11 | -0.9532 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 11 | 11 | -0.3 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 9 | 9 | -1.6752 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 8 | 8 | -0.7847 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 7 | 7 | -0.5075 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_lt_neg070` | 7 | 7 | -1.3886 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 7 | 7 | -1.2916 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 6 | 6 | -0.8069 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 6 | 6 | -0.587 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 5 | 5 | -1.9245 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 5 | 5 | -0.7503 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 5 | 5 | 0.2312 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 4 | 4 | -1.1675 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 3 | 3 | -0.27 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 3 | 3 | -1.7414 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 2 | 2 | 2.5344 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=NEUTRAL|profit=profit_lt_neg070` | 2 | 2 | -0.7517 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=NEUTRAL|profit=profit_neg070_neg010` | 2 | 2 | -0.7522 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg070_neg010` | 2 | 2 | -0.4814 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 2 | 2 | -0.0856 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg010_pos080` | 1 | 1 | 0.045 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 400, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `price_guard_reason` | `price_guard_none` | 10705 | 10640 | None | -0.9303 | 0.0834 | `hold_sample` |
| `qty_reason` | `qty_none` | 10643 | 10640 | None | -0.9303 | 0.0834 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 10628 | 10626 | None | -0.933 | 0.0824 | `hold_sample` |
| `arm` | `AVG_DOWN` | 9795 | 9730 | None | -1.059 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 9709 | 9644 | None | -1.04 | 0.0 | `hold_sample` |
| `time_bucket` | `time_unknown` | 7837 | 7788 | None | -0.8757 | 0.1055 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 6175 | 6175 | None | -0.9341 | 0.0918 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 5949 | 5949 | None | -1.4704 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 5615 | 5615 | None | -0.9852 | 0.0997 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 5061 | 4993 | None | -1.0502 | 0.0004 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 4276 | 4227 | None | -0.7466 | 0.1944 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 3568 | 3568 | None | -1.1162 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 3509 | 3509 | None | -0.4386 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 2798 | 2798 | None | -0.9624 | 0.0579 | `hold_sample` |
| `ai_score_source` | `live` | 2101 | 2101 | None | -0.9006 | 0.1066 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 1878 | 1878 | None | -0.4819 | 0.3647 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_1` | 1689 | 1689 | None | -1.1469 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 1452 | 1452 | None | -0.7467 | 0.0923 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 1007 | 1007 | None | 0.1714 | 0.7091 | `hold_sample` |
| `ai_score_source` | `holding_ai_not_called` | 966 | 966 | None | -1.0407 | 0.0362 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 22 | 11 | -0.9532 | -1.2709 | 0.0909 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 11 | 11 | -0.9532 | -1.2709 | 0.0909 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 22 | 11 | -0.9532 | -1.2709 | 0.0909 | `hold_sample` |
| `stage` | `exit` | 11 | 11 | -0.9532 | -1.2709 | 0.0909 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 22 | 11 | -0.9532 | -1.2709 | 0.0909 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 22 | 11 | -0.9532 | -1.2709 | 0.0909 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 11 | 11 | -0.9532 | -1.2709 | 0.0909 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 20 | 10 | -1.053 | -1.404 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 7 | 7 | -1.3886 | -1.8514 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 14 | 7 | -1.1914 | -1.5886 | 0.1428 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 14 | 7 | -1.3886 | -1.8514 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 3 | 3 | -0.27 | -0.36 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 6 | 3 | -0.27 | -0.36 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 4 | 2 | -0.585 | -0.78 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 1 | 1 | 0.045 | 0.06 | 1.0 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 2 | 1 | -0.8475 | -1.13 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 2 | 1 | -0.1275 | -0.17 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 2 | 1 | 0.045 | 0.06 | 1.0 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 2 | 1 | 0.045 | 0.06 | 1.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 11 | 0 | None | None | None | `hold_sample` |

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
