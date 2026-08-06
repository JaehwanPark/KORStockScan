# Lifecycle Decision Matrix - 2026-08-06

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-08-06_mtd`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `5780`
- source_rows_total: `9775`
- retained_rows: `5780`
- dropped_rows_by_source: `{}`
- joined_rows: `1520`
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
- lifecycle_flow_complete_count: `18`
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
| `entry` | 3810 | 75 | 2.8903 | 0.296 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 184 | 13 | 0.0193 | 0.1429 | `pass` | `NO_CHANGE` | False |
| `holding` | 19 | 13 | -0.3616 | 0.2709 | `pass` | `EXIT` | False |
| `scale_in` | 1390 | 1388 | -0.5469 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 377 | 31 | -0.6049 | 0.1279 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 78, 'complete_flow_count': 18, 'incomplete_flow_count': 3087, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 1250 | 1249 | -0.656 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 140 | 139 | 0.4327 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 58 | 58 | 3.4417 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:d0233209ef` | 4 | 4 | -0.6925 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 4 | 4 | 3.1589 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:b75bf201fa` | 2 | 2 | -0.745 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:397dbf1728` | 2 | 2 | -0.84 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:cb6ed22b69` | 2 | 2 | -0.83 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_bl:36dfb94c33` | 1 | 1 | -0.54 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:8b2aea4c29` | 1 | 1 | -0.86 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:1729d68718` | 1 | 1 | -0.7 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:9e4edc4bd2` | 1 | 1 | -0.99 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:99013dc4f3` | 1 | 1 | 1.2012 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:2a245e5d4f` | 1 | 1 | 4.0086 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:75c7602241` | 1 | 1 | -1.55 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:a5ddbd8b87` | 1 | 1 | -1.04 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:0e6c01c6bb` | 1 | 1 | -0.6 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:62b3401904` | 1 | 1 | -0.1725 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:fef5ae20be` | 1 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:075ce13c92` | 2 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 327, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `score_band` | `score_63_65` | 793 | 71 | 2.8752 | 4.28 | 0.6901 | `candidate_recovery_or_relax` |
| `liquidity_bucket` | `liquidity_high` | 1728 | 64 | 3.3308 | 5.1419 | 0.75 | `candidate_recovery_or_relax` |
| `chosen_action` | `WAIT_REQUOTE` | 800 | 63 | 3.4327 | 5.2779 | 0.746 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 3798 | 63 | 3.4327 | 5.2779 | 0.746 | `source_quality_workorder` |
| `source_stage` | `wait6579_ev_cohort` | 63 | 63 | 3.4327 | 5.2779 | 0.746 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_watch` | 1181 | 42 | 2.5652 | 3.623 | 0.6905 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_1000_1200` | 24 | 24 | 2.7518 | 3.8641 | 0.6667 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 15 | 15 | 2.187 | 3.0597 | 0.7333 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_ok` | 300 | 11 | 6.2502 | 11.1017 | 0.8182 | `candidate_recovery_or_relax` |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 338 | 10 | -0.0407 | -1.221 | 0.3 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_not_available` | 1637 | 10 | -0.0407 | -1.221 | 0.3 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_not_available` | 1186 | 10 | -0.0407 | -1.221 | 0.3 | `source_quality_workorder` |
| `source_stage` | `scalp_sim_entry_ai_price_skip_order` | 303 | 10 | -0.0407 | -1.221 | 0.3 | `hold_sample` |
| `strength_bucket` | `risk_context_not_available` | 164 | 9 | -0.1721 | -1.1789 | 0.3333 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_ok|time=time_1000_1200` | 9 | 9 | 7.6585 | 13.6406 | 0.8889 | `hold_sample` |
| `stale_bucket` | `stale_not_available` | 719 | 9 | -0.1721 | -1.1789 | 0.3333 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_normal` | 755 | 7 | 1.3465 | 1.6753 | 0.8571 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 6 | 6 | 0.2798 | 0.475 | 0.8333 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1000_1200` | 113 | 6 | -0.4222 | -1.315 | 0.3333 | `hold_sample` |
| `overbought_bucket` | `overbought_chase_risk` | 111 | 5 | 6.2529 | 9.7913 | 1.0 | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 95, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 157 | 13 | 0.0193 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 16 | 13 | 0.0193 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 183 | 13 | 0.0193 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 18 | 13 | 0.0193 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 18 | 13 | 0.0193 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 18 | 13 | 0.0193 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 18 | 13 | 0.0193 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 18 | 13 | 0.0193 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 18 | 13 | 0.0193 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 18 | 13 | 0.0193 | `keep_collecting` |
| `latency_state` | `simulated` | 18 | 13 | 0.0193 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 157 | 13 | 0.0193 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 18 | 13 | 0.0193 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 13 | 10 | -0.0407 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 10 | 8 | 0.2669 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 10 | 8 | 0.2669 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 148 | 8 | 0.2669 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 10 | 8 | 0.2669 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 10 | 8 | 0.2669 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 8 | 5 | -0.3769 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 8 | 5 | -0.3769 | `keep_collecting` |
| `would_limit_fill` | `false` | 173 | 5 | 0.1096 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 8 | 5 | -0.3769 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 6 | 5 | 0.1096 | `source_quality_workorder` |
| `liquidity_guard_action` | `would_block` | 8 | 5 | -0.3769 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 8 | 5 | -0.3769 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_3_10s` | 21 | 4 | 0.2801 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 5 | 3 | 0.2191 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 3 | 3 | 0.46 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 3 | 3 | 0.529 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 2 | 2 | 0.4585 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_1_3s` | 5 | 1 | -3.0049 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 1 | 1 | 0.6701 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 3 | 1 | -3.0049 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 2 | 1 | -0.2596 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 2 | 0 | None | `keep_collecting` |
| `latency_state` | `caution` | 20 | 0 | None | `keep_collecting` |
| `latency_reason` | `caution_normal_entry_allowed` | 20 | 0 | None | `keep_collecting` |
| `latency_state` | `danger` | 140 | 0 | None | `keep_collecting` |
| `price_resolution_bucket` | `defensive_limit` | 28 | 0 | None | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 17, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `holding_action` | `WAIT` | 18 | 13 | -0.3616 | `hold_sample` |
| `held_bucket` | `held_not_applicable_at_start` | 18 | 13 | -0.3616 | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 18 | 13 | -0.3616 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 6 | 6 | -1.1627 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 6 | 6 | -1.1627 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 4 | 4 | 0.1827 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 4 | 4 | 0.1827 | `hold_no_edge` |
| `profit_band` | `profit_pos080_pos150` | 2 | 2 | 0.8287 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 0.8287 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 2 | 1 | -0.1128 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 1 | 1 | -0.1128 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 5 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 5 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 36, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 17 | 17 | -0.8165 | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 17 | 17 | -0.8165 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 17 | 17 | -0.8165 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 14 | 14 | -1.084 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 13 | 13 | -0.3616 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 11 | 11 | -0.5423 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 9 | 9 | -0.6311 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 8 | 8 | -1.025 | `hold_sample` |
| `exit_outcome` | `NEUTRAL` | 7 | 7 | -0.3041 | `hold_no_edge` |
| `exit_rule` | `scalp_trailing_take_profit` | 7 | 7 | 0.325 | `hold_sample` |
| `exit_outcome` | `MISSED_UPSIDE` | 4 | 4 | 0.0673 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 4 | 4 | 0.1827 | `hold_no_edge` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 4 | 4 | -0.4364 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 4 | 4 | 0.1827 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 3 | 3 | -0.3107 | `hold_sample` |
| `exit_outcome` | `GOOD_EXIT` | 2 | 2 | -1.4206 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 2 | 2 | 0.8287 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 2 | 2 | -2.6153 | `hold_sample` |
| `exit_outcome` | `COMPLETED` | 1 | 1 | -0.1725 | `hold_sample` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 1 | 1 | -0.1725 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 1 | 1 | -0.1725 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 1 | 1 | -0.1725 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 1 | 1 | -0.8137 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 1 | 1 | -3.2975 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 1 | 1 | -1.933 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 1 | 1 | 0.4563 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 1 | 1 | 1.2012 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg070_neg010` | 1 | 1 | -0.1128 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 346 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_context_noop` | 346 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_euphoria_context_noop` | 309 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_euphoria_context_noop_not_applicable` | 309 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 37 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_context_warning_not_applicable` | 37 | 0 | None | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_euphoria_context_noop|rule=scalp_sim_euphoria_context_noop_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 309 | 0 | None | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=scalp_sim_panic_context_warning_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 37 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 157, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `price_guard_reason` | `price_guard_none` | 1390 | 1388 | None | -0.6068 | 0.072 | `hold_sample` |
| `qty_reason` | `qty_none` | 1388 | 1388 | None | -0.6068 | 0.072 | `hold_sample` |
| `time_bucket` | `time_unknown` | 1390 | 1388 | None | -0.6068 | 0.072 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 1365 | 1364 | None | -0.6319 | 0.0557 | `hold_sample` |
| `arm` | `AVG_DOWN` | 1250 | 1249 | None | -0.7195 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 1246 | 1245 | None | -0.712 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 793 | 793 | None | -0.4068 | 0.0896 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 785 | 785 | None | -0.4562 | 0.0 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 761 | 759 | None | -0.5194 | 0.1317 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 631 | 629 | None | -0.7121 | 0.0 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 545 | 545 | None | -0.5467 | 0.0459 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 484 | 484 | None | -0.7646 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 465 | 465 | None | -0.5481 | 0.1441 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 427 | 427 | None | -1.2618 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 238 | 238 | None | -0.222 | 0.2731 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_1` | 220 | 220 | None | -0.7586 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 208 | 208 | None | -1.1704 | 0.0769 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 208 | 208 | None | -0.7252 | 0.0144 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_2` | 176 | 176 | None | -0.5396 | 0.0 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_0` | 155 | 155 | None | -0.9111 | 0.0 | `hold_sample` |

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
| `held_bucket` | `held_600_1800s` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
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
