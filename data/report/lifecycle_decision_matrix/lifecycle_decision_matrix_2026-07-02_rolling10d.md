# Lifecycle Decision Matrix - 2026-07-02

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-02_rolling10d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `54622`
- source_rows_total: `86060`
- retained_rows: `54622`
- dropped_rows_by_source: `{}`
- joined_rows: `31007`
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
- lifecycle_flow_bucket_count: `336`
- lifecycle_flow_complete_count: `206`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0042`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 4127 | 473 | 0.7862 | 0.7836 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 1010 | 456 | -0.6753 | 0.9312 | `pass` | `NO_CHANGE` | False |
| `holding` | 836 | 456 | -1.1079 | 0.9541 | `pass` | `EXIT` | False |
| `scale_in` | 29100 | 28637 | -0.5569 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 19549 | 985 | -0.9748 | 0.7314 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 336, 'complete_flow_count': 206, 'incomplete_flow_count': 49379, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 22671 | 22512 | -0.88 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 5910 | 5606 | 0.7636 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 440 | 440 | -0.9962 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 147 | 147 | 1.0421 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 103 | 103 | 1.9652 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 47 | 47 | -0.1659 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 33 | 33 | 2.9796 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 17 | 17 | -0.8809 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 8 | 8 | -0.8012 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:05b084aa57` | 7 | 7 | -0.923 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:f708d0f2a2` | 6 | 6 | 2.881 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:89e49a11bc` | 5 | 5 | -1.3548 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:c1801bf4e3` | 5 | 5 | -1.9774 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:8050d08a3f` | 4 | 4 | -1.8461 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 4 | 4 | -0.7775 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:3cbb81cd02` | 3 | 3 | -1.5619 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:67138f9e63` | 3 | 3 | -1.0287 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:2a4bfd22da` | 3 | 3 | -1.3519 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:7248608969` | 3 | 3 | -0.8576 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:c86da1173b` | 3 | 3 | -0.5224 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 437, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 2977 | 468 | 0.803 | 1.0341 | 0.4316 | `hold_no_edge` |
| `overbought_bucket` | `overbought_normal` | 2527 | 348 | 0.6956 | 0.6426 | 0.4224 | `candidate_recovery_or_relax` |
| `chosen_action` | `WAIT_REQUOTE` | 364 | 287 | 1.5839 | 2.5936 | 0.5714 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 3937 | 283 | 1.604 | 2.6273 | 0.5689 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 211 | 211 | 1.8255 | 2.9599 | 0.5877 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 1949 | 175 | -0.4945 | -1.4635 | 0.2114 | `candidate_tighten_or_exclude` |
| `chosen_action` | `NO_BUY_AI` | 2962 | 169 | -0.4565 | -1.3393 | 0.2308 | `candidate_tighten_or_exclude` |
| `stale_bucket` | `fresh_or_unflagged` | 623 | 134 | 1.9231 | 3.1301 | 0.597 | `candidate_recovery_or_relax` |
| `strength_bucket` | `strong_strength_momentum` | 431 | 134 | 1.263 | 1.967 | 0.5074 | `candidate_recovery_or_relax` |
| `score_band` | `score_70p` | 539 | 127 | 0.6682 | 0.8741 | 0.441 | `candidate_recovery_or_relax` |
| `strength_bucket` | `weak_strength_momentum` | 1320 | 117 | 0.1193 | -0.6522 | 0.2735 | `hold_no_edge` |
| `score_band` | `score_60_62` | 1745 | 108 | -0.4903 | -1.5213 | 0.1852 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 95 | 95 | -0.2355 | -2.1756 | 0.0 | `candidate_tighten_or_exclude` |
| `time_bucket` | `time_0900_1000` | 817 | 94 | 0.0912 | -0.9158 | 0.2447 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_1000_1200` | 681 | 85 | 1.0589 | 1.2822 | 0.4471 | `candidate_recovery_or_relax` |
| `score_band` | `score_66_69` | 199 | 84 | 2.0932 | 3.5451 | 0.6309 | `hold_sample` |
| `overbought_bucket` | `overbought_watch` | 636 | 82 | 0.2986 | 0.6425 | 0.4146 | `hold_no_edge` |
| `stale_bucket` | `stale_high` | 1074 | 76 | -0.698 | -1.372 | 0.2368 | `candidate_tighten_or_exclude` |
| `time_bucket` | `time_1200_1400` | 562 | 72 | 0.8428 | 2.1805 | 0.5417 | `hold_sample` |
| `stale_bucket` | `fresh` | 612 | 64 | -0.3002 | -1.9585 | 0.125 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 44 | 44 | -0.4285 | -3.5002 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 27 | 27 | 0.7171 | 0.7784 | 0.5926 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1400_close` | 18 | 18 | 1.4469 | 2.3012 | 0.6667 | `candidate_recovery_or_relax` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 144, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 844 | 456 | -0.6753 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 802 | 456 | -0.6753 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 802 | 456 | -0.6753 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 802 | 456 | -0.6753 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 802 | 456 | -0.6753 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 802 | 456 | -0.6753 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 802 | 456 | -0.6753 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 802 | 456 | -0.6753 | `keep_collecting` |
| `latency_state` | `simulated` | 802 | 456 | -0.6753 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 844 | 456 | -0.6753 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 798 | 455 | -0.6666 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 735 | 421 | -0.7171 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 599 | 383 | -0.7474 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_ok` | 651 | 367 | -0.7553 | `keep_collecting` |
| `revalidation_state` | `warning_stale_context_or_quote` | 523 | 356 | -0.6913 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 463 | 327 | -0.7021 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 443 | 290 | -0.7651 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 486 | 260 | -0.492 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 486 | 260 | -0.492 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 328 | 195 | -0.9206 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 315 | 195 | -0.9206 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 315 | 195 | -0.9206 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 280 | 186 | -0.5466 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 197 | 131 | -0.3926 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 158 | 121 | -1.0041 | `source_quality_workorder` |
| `revalidation_state` | `ok_or_unflagged` | 481 | 99 | -0.5894 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 153 | 88 | -0.2967 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_unknown` | 221 | 74 | -0.2989 | `source_quality_workorder` |
| `price_resolution_bucket` | `price_resolution_unknown` | 203 | 73 | -0.2967 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 203 | 73 | -0.2967 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_10s_plus` | 112 | 63 | -0.7993 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 134 | 56 | -1.0118 | `keep_collecting` |
| `would_limit_fill` | `true` | 98 | 40 | -0.107 | `keep_collecting` |
| `would_limit_fill` | `false` | 313 | 33 | -0.5265 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 59 | 28 | -0.4274 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 206 | 28 | -0.5529 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 33 | 23 | -1.2639 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 44 | 22 | 0.081 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 83 | 20 | -0.7245 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 54 | 18 | -0.3369 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 46, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 802 | 456 | -1.1079 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 802 | 456 | -1.1079 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 726 | 409 | -1.1167 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 348 | 331 | -1.6581 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 296 | 296 | -1.6389 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 64 | 38 | -1.0513 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 38 | 38 | 0.7785 | `hold_no_edge` |
| `profit_band` | `profit_pos080_pos150` | 40 | 37 | -0.1378 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 35 | 35 | -0.1782 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 34 | 34 | 0.6483 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 28 | 28 | -1.7324 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300_plus` | 23 | 22 | 1.6716 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 31 | 20 | -0.6095 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 18 | 18 | -0.63 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 18 | 18 | 1.6311 | `candidate_recovery_or_relax` |
| `holding_action` | `BUY` | 12 | 9 | -0.9468 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 10 | 8 | -0.682 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 8 | 8 | -0.682 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 7 | 7 | -2.1729 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 4 | 4 | 1.8856 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 2 | 2 | 3.3445 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 2 | 2 | -0.425 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 0.57 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 2 | 2 | 0.3637 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 34 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 3 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 5 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 8 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 18 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 346 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 34 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 317 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 26 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_020_180s` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_180_600s` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 6 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 6 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 65, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 710 | 710 | -1.3816 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 528 | 528 | -0.9088 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 528 | 528 | -0.9088 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 528 | 528 | -0.9088 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 423 | 423 | -1.108 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 376 | 376 | -1.1712 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 190 | 190 | -1.3833 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 185 | 185 | -1.7047 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 141 | 141 | -0.5303 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 138 | 138 | -0.4369 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 128 | 128 | -2.0399 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 121 | 121 | -0.5259 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 100 | 100 | -0.9302 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 89 | 89 | -1.8731 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 82 | 82 | 0.7677 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 56 | 56 | -0.8435 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 51 | 51 | -2.7769 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 51 | 51 | -1.4355 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 44 | 44 | -1.1109 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 42 | 42 | 0.1378 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 39 | 39 | 0.9111 | `candidate_recovery_or_relax` |
| `exit_outcome` | `outcome_unknown` | 18598 | 34 | -0.3426 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 34 | 34 | -0.3426 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 34 | 34 | -0.3426 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300_plus` | 27 | 27 | 2.0874 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg010_pos080` | 26 | 26 | -0.0834 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 26 | 26 | -1.7801 | `candidate_tighten_or_exclude` |
| `exit_rule` | `daily_limit_up_immediate_exit` | 19 | 19 | -0.4778 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 18 | 18 | 0.1928 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 17 | 17 | -0.9776 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 16 | 16 | 1.8384 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 15 | 15 | -0.9742 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 13 | 13 | -0.0553 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 12 | 12 | 0.7168 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 11 | 11 | -0.2618 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` | 9 | 9 | 1.0444 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=daily_limit_up_immediate_exit|outcome=NEUTRAL|profit=profit_neg070_neg010` | 9 | 9 | -0.9177 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 7 | 7 | 0.9653 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 7 | 7 | 3.4245 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 5 | 5 | 0.357 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 686, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_source` | `score_field_backfilled` | 28624 | 28624 | None | -0.6196 | 0.1897 | `hold_sample` |
| `arm` | `AVG_DOWN` | 23141 | 22982 | None | -0.9458 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 19933 | 19774 | None | -1.0144 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_70p` | 14933 | 14933 | None | -0.5826 | 0.225 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 6618 | 6618 | None | -0.6639 | 0.1568 | `hold_sample` |
| `arm` | `PYRAMID` | 5959 | 5655 | None | 0.7093 | 0.9617 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 5959 | 5655 | None | 0.7093 | 0.9617 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 4828 | 4828 | None | 0.5049 | 0.9756 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 3222 | 3222 | None | -0.6768 | 0.135 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 3208 | 3208 | None | -0.523 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2313 | 2313 | None | -1.0278 | 0.0826 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 2203 | 2203 | None | -0.6386 | 0.143 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 1648 | 1648 | None | -0.6393 | 0.1705 | `hold_sample` |
| `blocker_reason` | `add_judgment_locked` | 930 | 930 | None | -0.5799 | 0.0656 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 913 | 913 | None | -1.0165 | 0.057 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 583 | 583 | None | -0.8527 | 0.0926 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 443 | 443 | None | -0.8561 | 0.1422 | `hold_sample` |
| `blocker_reason` | `low_broken` | 439 | 439 | None | -0.4976 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.54)` | 396 | 396 | None | -0.54 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.23)` | 394 | 394 | None | -0.23 | 0.0 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 34, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 68 | 34 | -0.3426 | -0.4568 | 0.1765 | `candidate_tighten_or_exclude` |
| `overnight_status` | `SELL_TODAY` | 34 | 34 | -0.3426 | -0.4568 | 0.1765 | `candidate_tighten_or_exclude` |
| `confidence_band` | `confidence_070p` | 68 | 34 | -0.3426 | -0.4568 | 0.1765 | `candidate_tighten_or_exclude` |
| `stage` | `exit` | 34 | 34 | -0.3426 | -0.4568 | 0.1765 | `candidate_tighten_or_exclude` |
| `source_quality_gate` | `overnight_decision_coverage` | 68 | 34 | -0.3426 | -0.4568 | 0.1765 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 34 | 34 | -0.3426 | -0.4568 | 0.1765 | `candidate_tighten_or_exclude` |
| `price_source` | `holding_price_samples_last` | 62 | 31 | -0.359 | -0.4787 | 0.1935 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_lt_zero` | 56 | 28 | -0.6964 | -0.9286 | 0.0 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s_plus` | 36 | 18 | 0.0233 | 0.0311 | 0.2778 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 17 | 17 | -0.9776 | -1.3035 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 34 | 17 | -0.9776 | -1.3035 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 11 | 11 | -0.2618 | -0.3491 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 22 | 11 | -0.2618 | -0.3491 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 16 | 8 | -0.9694 | -1.2925 | 0.125 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 10 | 5 | -0.525 | -0.7 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 3 | 3 | 0.82 | 1.0933 | 1.0 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 6 | 3 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 6 | 3 | -0.5625 | -0.75 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 6 | 3 | 0.82 | 1.0933 | 1.0 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 6 | 3 | 0.82 | 1.0933 | 1.0 | `hold_sample` |

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
