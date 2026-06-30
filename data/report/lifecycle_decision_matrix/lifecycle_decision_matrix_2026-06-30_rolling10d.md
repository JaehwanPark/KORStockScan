# Lifecycle Decision Matrix - 2026-06-30

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-30_rolling10d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `45588`
- source_rows_total: `68036`
- retained_rows: `45588`
- dropped_rows_by_source: `{}`
- joined_rows: `27406`
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
- lifecycle_flow_bucket_count: `349`
- lifecycle_flow_complete_count: `251`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0062`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 4304 | 505 | 0.6781 | 0.8298 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 960 | 530 | -0.5402 | 0.9924 | `pass` | `NO_CHANGE` | False |
| `holding` | 877 | 530 | -1.0686 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 25370 | 24780 | -0.5191 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 14077 | 1061 | -0.9308 | 0.8569 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 349, 'complete_flow_count': 251, 'incomplete_flow_count': 40034, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 19224 | 19062 | -0.8887 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 5618 | 5190 | 0.8628 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 424 | 424 | -0.9827 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 156 | 156 | 1.0345 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 107 | 107 | 1.555 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 51 | 51 | -0.0215 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 32 | 32 | 2.9586 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 16 | 16 | -0.8497 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 9 | 9 | -0.9944 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 8 | 8 | -0.625 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:89e49a11bc` | 7 | 7 | -1.349 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:c1801bf4e3` | 6 | 6 | -1.8851 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:05b084aa57` | 6 | 6 | -0.7393 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:f708d0f2a2` | 6 | 6 | 2.881 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:76e538b0ff` | 5 | 5 | -1.5047 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:8050d08a3f` | 4 | 4 | -1.8461 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:67138f9e63` | 4 | 4 | -1.0246 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:0e963d335b` | 4 | 4 | -0.475 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:3cbb81cd02` | 3 | 3 | -1.5619 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:84461e0e65` | 3 | 3 | 2.7581 | `candidate_recovery_or_relax` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 415, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 3233 | 503 | 0.6857 | 0.7778 | 0.4294 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 2788 | 380 | 0.6957 | 0.5612 | 0.4237 | `candidate_recovery_or_relax` |
| `chosen_action` | `WAIT_REQUOTE` | 316 | 297 | 1.4141 | 2.2691 | 0.5791 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 4096 | 297 | 1.4141 | 2.2691 | 0.5791 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 225 | 225 | 1.5611 | 2.4663 | 0.6 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 2061 | 193 | -0.4249 | -1.4789 | 0.1917 | `hold_no_edge` |
| `chosen_action` | `NO_BUY_AI` | 3240 | 186 | -0.4145 | -1.3697 | 0.2258 | `hold_no_edge` |
| `strength_bucket` | `strong_strength_momentum` | 462 | 151 | 0.8595 | 1.2369 | 0.5232 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh_or_unflagged` | 622 | 148 | 1.5118 | 2.3636 | 0.6148 | `candidate_recovery_or_relax` |
| `score_band` | `score_70p` | 502 | 144 | 0.7042 | 0.8258 | 0.4653 | `candidate_recovery_or_relax` |
| `strength_bucket` | `weak_strength_momentum` | 1564 | 134 | 0.1522 | -0.6805 | 0.2537 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_0900_1000` | 1040 | 133 | 0.1206 | -0.4821 | 0.3233 | `hold_no_edge` |
| `score_band` | `score_60_62` | 1925 | 118 | -0.5243 | -1.6405 | 0.1695 | `hold_no_edge` |
| `exit_rule` | `scalp_soft_stop_pct` | 103 | 103 | -0.2543 | -2.0984 | 0.0 | `hold_no_edge` |
| `time_bucket` | `time_1000_1200` | 784 | 97 | 1.2003 | 1.3549 | 0.4639 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_watch` | 708 | 94 | 0.237 | 0.7669 | 0.4468 | `hold_no_edge` |
| `score_band` | `score_66_69` | 207 | 88 | 1.6065 | 2.6117 | 0.6023 | `candidate_tighten_or_exclude` |
| `stale_bucket` | `stale_high` | 1214 | 87 | -0.556 | -1.7436 | 0.1724 | `hold_no_edge` |
| `stale_bucket` | `fresh` | 723 | 76 | -0.3069 | -1.3782 | 0.1973 | `hold_no_edge` |
| `exit_rule` | `scalp_hard_stop_pct` | 54 | 54 | -0.2915 | -3.418 | 0.0 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 48 | 48 | 1.0757 | 1.5618 | 0.5417 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 38 | 38 | 0.865 | 1.0218 | 0.6316 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1400_close` | 18 | 18 | 1.4469 | 2.3012 | 0.6667 | `candidate_recovery_or_relax` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 138, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 877 | 530 | -0.5402 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 829 | 530 | -0.5402 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 829 | 530 | -0.5402 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 829 | 530 | -0.5402 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 829 | 530 | -0.5402 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 829 | 530 | -0.5402 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 829 | 530 | -0.5402 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 829 | 530 | -0.5402 | `keep_collecting` |
| `latency_state` | `simulated` | 829 | 530 | -0.5402 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 877 | 530 | -0.5402 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 823 | 527 | -0.534 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 736 | 483 | -0.5618 | `source_quality_workorder` |
| `price_below_bid_bucket` | `not_below_bid` | 750 | 477 | -0.5722 | `keep_collecting` |
| `revalidation_state` | `warning_stale_context_or_quote` | 716 | 467 | -0.5388 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 676 | 424 | -0.5949 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 617 | 408 | -0.5643 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 550 | 369 | -0.5674 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 470 | 276 | -0.4109 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 470 | 276 | -0.4109 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 375 | 251 | -0.6849 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 356 | 251 | -0.6849 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 356 | 251 | -0.6849 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 373 | 227 | -0.4141 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 264 | 158 | -0.2848 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 212 | 157 | -0.8391 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_context_missing` | 153 | 103 | -0.2836 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_10s_plus` | 137 | 78 | -0.6915 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 116 | 74 | -0.563 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 241 | 62 | -0.5036 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_unknown` | 114 | 50 | -0.3192 | `source_quality_workorder` |
| `price_resolution_bucket` | `price_resolution_unknown` | 93 | 47 | -0.3183 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 93 | 47 | -0.3183 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 69 | 45 | -0.2962 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 48 | 33 | -0.96 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_1_3s` | 139 | 32 | -0.2813 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 29 | 25 | -0.1862 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 48 | 25 | -0.066 | `keep_collecting` |
| `would_limit_fill` | `false` | 176 | 22 | -0.605 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 40 | 20 | -0.7836 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 22 | 19 | -0.4655 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 49, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 828 | 530 | -1.0686 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 828 | 530 | -1.0686 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 722 | 454 | -1.0684 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 410 | 395 | -1.5956 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 332 | 332 | -1.5964 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 92 | 64 | -1.0766 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 53 | 53 | -1.5312 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 39 | 36 | 0.8633 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos080_pos150` | 42 | 35 | 0.0884 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 34 | 34 | 0.0518 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 34 | 34 | 0.8115 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300_plus` | 29 | 27 | 1.7765 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 40 | 24 | -0.5717 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 22 | 22 | -0.585 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 20 | 20 | 1.676 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 19 | 13 | -0.3482 | `hold_no_edge` |
| `holding_action` | `BUY` | 14 | 12 | -1.033 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 12 | 12 | -0.4214 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 10 | 10 | -1.9085 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 5 | 5 | 1.5512 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 2 | 2 | 3.3445 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 2 | 2 | -0.425 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 2 | 2 | 1.7422 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 0.53 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | 1.3343 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 49 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 4 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 7 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 36 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 298 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 49 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 268 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 28 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_020_180s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_180_600s` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 9 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s` | 2 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 66, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 759 | 759 | -1.3785 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 526 | 526 | -0.8526 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 526 | 526 | -0.8526 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 526 | 526 | -0.8526 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 486 | 486 | -1.1146 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 360 | 360 | -1.1756 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 213 | 213 | -1.2879 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 204 | 204 | -1.666 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 172 | 172 | -1.9426 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 160 | 160 | -0.4782 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 150 | 150 | -0.5064 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 126 | 126 | -0.5054 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 122 | 122 | -1.0271 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 100 | 100 | -1.7588 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 78 | 78 | 0.9545 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 71 | 71 | -1.3955 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 62 | 62 | -2.6914 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 59 | 59 | -0.6823 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 53 | 53 | -1.0977 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 13065 | 49 | 0.0535 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 49 | 49 | 0.0535 | `candidate_recovery_or_relax` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 49 | 49 | 0.0535 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos080_pos150` | 40 | 40 | 0.3102 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300` | 40 | 40 | 0.9607 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 39 | 39 | -1.7482 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 37 | 37 | 0.001 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300_plus` | 35 | 35 | 2.3959 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 24 | 24 | 0.2075 | `hold_no_edge` |
| `exit_rule` | `daily_limit_up_immediate_exit` | 19 | 19 | -0.4778 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 15 | 15 | -0.9765 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 15 | 15 | -0.2685 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 14 | 14 | 0.1194 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 13 | 13 | 0.8691 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 13 | 13 | 1.9239 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 10 | 10 | -0.9783 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 10 | 10 | 3.0919 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` | 9 | 9 | 0.9844 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=daily_limit_up_immediate_exit|outcome=NEUTRAL|profit=profit_neg070_neg010` | 9 | 9 | -0.9177 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 7 | 7 | 0.1778 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos080_pos150` | 7 | 7 | 0.7929 | `source_quality_workorder` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 680, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_source` | `score_field_backfilled` | 24764 | 24764 | None | -0.5758 | 0.2034 | `hold_sample` |
| `arm` | `AVG_DOWN` | 19692 | 19530 | None | -0.9485 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 15847 | 15685 | None | -1.0652 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_70p` | 14418 | 14418 | None | -0.5459 | 0.2319 | `hold_sample` |
| `arm` | `PYRAMID` | 5678 | 5250 | None | 0.8133 | 0.9615 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 5678 | 5250 | None | 0.8133 | 0.9615 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 5232 | 5232 | None | -0.6452 | 0.1674 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 4271 | 4271 | None | 0.5252 | 0.9768 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 3845 | 3845 | None | -0.4726 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 2613 | 2613 | None | -0.6166 | 0.1573 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2313 | 2313 | None | -1.0278 | 0.0826 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 1378 | 1378 | None | -0.5758 | 0.1589 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 1123 | 1123 | None | -0.5421 | 0.1674 | `hold_sample` |
| `blocker_reason` | `add_judgment_locked` | 916 | 916 | None | -0.5574 | 0.0633 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 913 | 913 | None | -1.0165 | 0.057 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 616 | 616 | None | -0.8418 | 0.1088 | `hold_sample` |
| `blocker_reason` | `low_broken` | 491 | 491 | None | -0.4385 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 443 | 443 | None | -0.8561 | 0.1422 | `hold_sample` |
| `blocker_reason` | `scalping_pyramid_ok` | 438 | 438 | None | 3.1459 | 1.0 | `hold_sample` |
| `blocker_reason` | `scalping_buy_window_blocked` | 367 | 367 | None | -0.4359 | 0.0845 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 38, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 98 | 49 | 0.0535 | 0.0714 | 0.3469 | `candidate_recovery_or_relax` |
| `overnight_status` | `SELL_TODAY` | 49 | 49 | 0.0535 | 0.0714 | 0.3469 | `candidate_recovery_or_relax` |
| `confidence_band` | `confidence_070p` | 98 | 49 | 0.0535 | 0.0714 | 0.3469 | `candidate_recovery_or_relax` |
| `stage` | `exit` | 49 | 49 | 0.0535 | 0.0714 | 0.3469 | `candidate_recovery_or_relax` |
| `source_quality_gate` | `overnight_decision_coverage` | 98 | 49 | 0.0535 | 0.0714 | 0.3469 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 49 | 49 | 0.0535 | 0.0714 | 0.3469 | `candidate_recovery_or_relax` |
| `price_source` | `holding_price_samples_last` | 92 | 46 | 0.0683 | 0.0911 | 0.3696 | `candidate_recovery_or_relax` |
| `held_bucket` | `held_600_1800s_plus` | 72 | 36 | 0.2208 | 0.2945 | 0.3889 | `candidate_recovery_or_relax` |
| `peak_profit_band` | `peak_lt_zero` | 64 | 32 | -0.5876 | -0.7834 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 16 | 16 | -0.2564 | -0.3419 | 0.0 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 32 | 16 | -0.2564 | -0.3419 | 0.0 | `hold_no_edge` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 15 | 15 | -0.9765 | -1.302 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 30 | 15 | -0.9765 | -1.302 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 7 | 7 | 0.7929 | 1.0571 | 1.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 14 | 7 | -0.3461 | -0.4614 | 0.4286 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 14 | 7 | 0.7929 | 1.0571 | 1.0 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 14 | 7 | 0.7929 | 1.0571 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 6 | 6 | 0.22 | 0.2933 | 0.8333 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 12 | 6 | 0.22 | 0.2933 | 0.8333 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 10 | 5 | 0.2745 | 0.366 | 1.0 | `hold_sample` |

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
