# Lifecycle Decision Matrix - 2026-06-05

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-05_rolling5d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `15722`
- source_rows_total: `27307`
- retained_rows: `15722`
- dropped_rows_by_source: `{}`
- joined_rows: `14917`
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
- lifecycle_flow_bucket_count: `134`
- lifecycle_flow_complete_count: `60`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0041`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 679 | 95 | 1.0748 | 0.9586 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 188 | 162 | -0.6647 | 0.965 | `pass` | `NO_CHANGE` | False |
| `holding` | 194 | 162 | -1.0088 | 0.9604 | `pass` | `EXIT` | False |
| `scale_in` | 13976 | 13975 | -0.5159 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 685 | 523 | -0.9681 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 134, 'complete_flow_count': 60, 'incomplete_flow_count': 14537, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 12014 | 12013 | -0.6676 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 1803 | 1803 | 0.5252 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 123 | 123 | -1.075 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 33 | 33 | 2.1037 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:c7f35b773f` | 12 | 12 | -1.9011 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 11 | 11 | 1.32 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 11 | 11 | -0.95 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 10 | 10 | 2.0779 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:727c304d19` | 10 | 10 | -2.0274 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 9 | 9 | -0.7111 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:05b084aa57` | 9 | 9 | -0.8524 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:53bb9c05e0` | 9 | 9 | -0.7924 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7092a0ecba` | 7 | 7 | -1.0192 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:23320ac43e` | 5 | 5 | -0.1805 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:ffa670224b` | 5 | 5 | 1.0715 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:f708d0f2a2` | 5 | 5 | 2.2264 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:0562f02c36` | 4 | 4 | -0.8877 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:50092e1a75` | 4 | 4 | -0.8943 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:1222f9a339` | 4 | 4 | -1.1569 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 4 | 4 | -0.2125 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 194, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `WAIT_REQUOTE` | 54 | 54 | 1.9392 | 3.1961 | 0.6851 | `hold_sample` |
| `exit_rule` | `exit_unknown` | 638 | 54 | 1.9392 | 3.1961 | 0.6851 | `source_quality_workorder` |
| `stale_bucket` | `fresh_or_unflagged` | 215 | 54 | 1.9392 | 3.1961 | 0.6851 | `hold_sample` |
| `liquidity_bucket` | `liquidity_high` | 54 | 54 | 1.9392 | 3.1961 | 0.6851 | `hold_sample` |
| `source_stage` | `wait6579_ev_cohort` | 54 | 54 | 1.9392 | 3.1961 | 0.6851 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 132 | 42 | 0.8232 | 0.9729 | 0.619 | `source_quality_workorder` |
| `strength_bucket` | `risk_unknown` | 307 | 41 | -0.0637 | -1.2307 | 0.2439 | `source_quality_workorder` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 307 | 41 | -0.0637 | -1.2307 | 0.2439 | `source_quality_workorder` |
| `chosen_action` | `NO_BUY_AI` | 460 | 40 | -0.1152 | -1.209 | 0.25 | `source_quality_workorder` |
| `stale_bucket` | `fresh` | 336 | 39 | -0.0758 | -1.1654 | 0.2564 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_not_available` | 375 | 39 | -0.0273 | -1.1933 | 0.2564 | `source_quality_workorder` |
| `time_bucket` | `time_1000_1200` | 212 | 39 | 0.8831 | 1.0544 | 0.5385 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_not_available` | 255 | 36 | 0.0855 | -1.0961 | 0.2778 | `source_quality_workorder` |
| `strength_bucket` | `strong_strength_momentum` | 63 | 36 | 1.6641 | 2.8836 | 0.6389 | `source_quality_workorder` |
| `score_band` | `score_63_65` | 64 | 35 | 1.9384 | 3.1117 | 0.6857 | `source_quality_workorder` |
| `time_bucket` | `time_1200_1400` | 130 | 29 | 2.1417 | 2.9709 | 0.5517 | `source_quality_workorder` |
| `exit_rule` | `scalp_soft_stop_pct` | 25 | 25 | -0.1013 | -1.9364 | 0.0 | `source_quality_workorder` |
| `score_band` | `score_60_62` | 281 | 22 | -0.0814 | -1.2168 | 0.2273 | `source_quality_workorder` |
| `score_band` | `score_lt60` | 277 | 16 | -0.0773 | -1.3913 | 0.25 | `source_quality_workorder` |
| `time_bucket` | `time_1400_close` | 178 | 16 | 0.5884 | 0.0121 | 0.375 | `source_quality_workorder` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 14 | 14 | 0.1238 | -0.1149 | 0.6429 | `hold_no_edge` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 61, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `liquidity_guard_action` | `would_pass` | 227 | 227 | -0.5391 | `keep_collecting` |
| `actual_order_submitted` | `false` | 229 | 171 | -0.6687 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 162 | 162 | -0.6647 | `keep_collecting` |
| `latency_state` | `simulated` | 162 | 162 | -0.6647 | `keep_collecting` |
| `actual_order_submitted` | `true` | 182 | 162 | -0.6647 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 153 | 153 | -0.6602 | `source_quality_workorder` |
| `revalidation_state` | `warning_stale_context_or_quote` | 145 | 145 | -0.6342 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 144 | 144 | -0.7265 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 137 | 137 | -0.603 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 131 | 131 | -0.7125 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 102 | 97 | -0.9587 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 97 | 97 | -0.9587 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 97 | 97 | -0.9587 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 92 | 92 | -0.7817 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 65 | 65 | -0.2261 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 61 | 61 | -0.4771 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 56 | 56 | -0.1434 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 56 | 56 | -1.0587 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 33 | 33 | -0.1748 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 26 | 26 | -0.6118 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_context_missing` | 25 | 25 | -1.003 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 22 | 22 | -0.0749 | `source_quality_workorder` |
| `price_resolution_bucket` | `defensive_order_price` | 21 | 21 | -0.3931 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 17 | 17 | -0.1991 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 17 | 17 | -0.925 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 9 | 9 | -0.7409 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 35 | 9 | -0.7409 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 9 | 9 | -0.7409 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=false|submitted=false` | 9 | 9 | -0.7409 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 8 | 8 | -1.1322 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 4 | 4 | -0.4703 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 3 | 3 | -2.2849 | `source_quality_workorder` |
| `price_resolution_bucket` | `ai_tier2_use_defensive` | 1 | 1 | 0.574 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 1 | 1 | 0.3022 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | -0.6128 | `source_quality_workorder` |
| `revalidation_state` | `block_False` | 26 | 0 | None | `keep_collecting` |
| `price_resolution_bucket` | `defensive_limit` | 7 | 0 | None | `keep_collecting` |
| `submit_source_stage` | `latency_block` | 13 | 0 | None | `keep_collecting` |
| `submit_source_stage` | `latency_pass` | 6 | 0 | None | `keep_collecting` |
| `latency_reason` | `latency_reason_unknown` | 26 | 0 | None | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 35, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 162 | 162 | -1.0088 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 162 | 162 | -1.0088 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 142 | 142 | -1.0235 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 139 | 123 | -1.37 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 107 | 107 | -1.4052 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 18 | 18 | -0.9238 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 15 | 15 | -1.1624 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 13 | 11 | -0.0143 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 11 | 10 | 0.1615 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 10 | 10 | 0.0344 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 9 | 9 | 0.1734 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 8 | 8 | 0.478 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 8 | 8 | 0.478 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 17 | 5 | -0.386 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 6 | 5 | 0.3482 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 5 | 5 | -0.386 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 3 | 3 | 0.4102 | `candidate_recovery_or_relax` |
| `holding_action` | `BUY` | 2 | 2 | -0.7284 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1 | 1 | -0.7105 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | -0.7462 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | -0.5008 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | 0.0536 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 1.2566 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 32 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 10 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 22 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 32 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 6 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 10 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 9 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos080_pos150|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos150_pos300_plus|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 55, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 386 | 386 | -1.3227 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 342 | 342 | -0.9984 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 178 | 178 | -1.3595 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 149 | 149 | -1.0157 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 149 | 149 | -1.0157 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 149 | 149 | -1.0157 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 132 | 132 | -0.5471 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 127 | 127 | -1.4524 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 112 | 112 | -1.1795 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 84 | 84 | 0.2798 | `candidate_recovery_or_relax` |
| `exit_outcome` | `NEUTRAL` | 83 | 83 | -1.0214 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 76 | 76 | -1.5805 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 64 | 64 | -0.4223 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 64 | 64 | -0.9493 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 57 | 57 | -1.9239 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 57 | 57 | -1.2558 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 47 | 47 | -0.5014 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 39 | 39 | -1.0718 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 35 | 35 | -0.5657 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 33 | 33 | 0.1409 | `hold_no_edge` |
| `exit_outcome` | `outcome_unknown` | 194 | 32 | -0.4223 | `source_quality_workorder` |
| `profit_band` | `profit_neg010_pos080` | 27 | 27 | -0.1089 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 26 | 26 | -2.3705 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 20 | 20 | 0.581 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 18 | 18 | -0.3744 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 16 | 16 | -0.8447 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 12 | 12 | -0.3138 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 12 | 12 | -0.4708 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 11 | 11 | -1.517 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300_plus` | 10 | 10 | 1.4502 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 10 | 10 | 0.8953 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 8 | 8 | 0.1598 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 8 | 8 | 0.4946 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 7 | 7 | 0.475 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 6 | 6 | 1.0649 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 5 | 5 | 2.3325 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 4 | 4 | 0.1211 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 4 | 4 | -0.3855 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 3 | 3 | -0.6451 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 2 | 2 | 0.1837 | `source_quality_workorder` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 309, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `arm` | `AVG_DOWN` | 20584 | 20582 | -0.7217 | -0.7858 | 0.0 | `candidate_tighten_or_exclude` |
| `ai_score_source` | `score_field_backfilled` | 13975 | 13975 | -0.5159 | -0.5795 | 0.1268 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_70p` | 5936 | 5936 | -0.5253 | -0.5861 | 0.1186 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_66_69` | 4398 | 4398 | -0.4994 | -0.5713 | 0.1512 | `candidate_tighten_or_exclude` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 3750 | 3750 | -0.3909 | -0.449 | 0.0 | `candidate_tighten_or_exclude` |
| `arm` | `PYRAMID` | 3618 | 3618 | 0.5251 | 0.459 | 0.9801 | `candidate_recovery_or_relax` |
| `blocker_reason` | `add_judgment_locked` | 2346 | 2346 | -0.321 | -0.3367 | 0.1543 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_63_65` | 1661 | 1661 | -0.4446 | -0.5039 | 0.115 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `profit_not_enough` | 1391 | 1391 | 0.5178 | 0.4507 | 0.9864 | `candidate_recovery_or_relax` |
| `ai_score_band` | `score_60_62` | 1336 | 1336 | -0.5666 | -0.6242 | 0.1227 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_lt60` | 644 | 644 | -0.621 | -0.6767 | 0.0761 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `low_broken` | 354 | 354 | -0.4256 | -0.4513 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `scalping_cutoff` | 255 | 255 | -0.4568 | -0.4678 | 0.0431 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 182 | 182 | -0.8528 | -0.8528 | 0.0385 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.75)` | 163 | 163 | -0.6924 | -0.75 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.79)` | 150 | 150 | -0.7293 | -0.79 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.96)` | 135 | 135 | -0.8883 | -0.96 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.77)` | 121 | 121 | -0.7016 | -0.77 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.92)` | 121 | 121 | -0.8486 | -0.92 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.15)` | 118 | 118 | -1.0416 | -1.15 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.88)` | 115 | 115 | -0.8037 | -0.88 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.02)` | 115 | 115 | -0.9349 | -1.02 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.86)` | 114 | 114 | -0.7955 | -0.86 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.94)` | 111 | 111 | -0.8684 | -0.94 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.06)` | 111 | 111 | -0.963 | -1.06 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.71)` | 107 | 107 | -0.6554 | -0.71 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.80)` | 107 | 107 | -0.733 | -0.8 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.93)` | 104 | 104 | -0.866 | -0.93 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.17)` | 98 | 98 | -1.0669 | -1.17 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.09)` | 95 | 95 | -0.0487 | -0.09 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.82)` | 94 | 94 | -0.7497 | -0.82 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.07)` | 91 | 91 | -0.9806 | -1.07 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `ok` | 83 | 83 | -1.7299 | -2.1277 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.91)` | 82 | 82 | -0.8342 | -0.91 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.97)` | 82 | 82 | -0.8708 | -0.97 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.38)` | 79 | 79 | -1.2637 | -1.38 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.95)` | 78 | 78 | -0.8791 | -0.95 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.04)` | 78 | 78 | -0.9551 | -1.04 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.09)` | 71 | 71 | -1.0145 | -1.09 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.87)` | 68 | 68 | -0.7953 | -0.87 | 0.0 | `candidate_tighten_or_exclude` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 30, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 96 | 64 | -0.4223 | -0.5631 | 0.125 | `candidate_tighten_or_exclude` |
| `confidence_band` | `confidence_070p` | 64 | 32 | -0.4223 | -0.5631 | 0.125 | `candidate_tighten_or_exclude` |
| `stage` | `exit` | 32 | 32 | -0.4223 | -0.5631 | 0.125 | `candidate_tighten_or_exclude` |
| `price_source` | `holding_price_samples_last` | 64 | 32 | -0.4223 | -0.5631 | 0.125 | `candidate_tighten_or_exclude` |
| `source_quality_gate` | `overnight_decision_coverage` | 64 | 32 | -0.4223 | -0.5631 | 0.125 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 32 | 32 | -0.4223 | -0.5631 | 0.125 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_lt_zero` | 56 | 28 | -0.6171 | -0.8229 | 0.0 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s_plus` | 44 | 22 | -0.3546 | -0.4727 | 0.1363 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 16 | 16 | -0.8447 | -1.1262 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 32 | 16 | -0.8447 | -1.1262 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 12 | 12 | -0.3138 | -0.4183 | 0.0 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 24 | 12 | -0.3138 | -0.4183 | 0.0 | `hold_no_edge` |
| `held_bucket` | `held_600_1800s` | 20 | 10 | -0.5715 | -0.762 | 0.1 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 2 | 2 | 0.1837 | 0.245 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 4 | 2 | 0.1837 | 0.245 | 1.0 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 4 | 2 | 0.1837 | 0.245 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 1 | 1 | 1.0425 | 1.39 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos150_pos300_plus` | 1 | 1 | 2.355 | 3.14 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 2 | 1 | 1.0425 | 1.39 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos150_pos300_plus` | 2 | 1 | 2.355 | 3.14 | 1.0 | `hold_sample` |

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
