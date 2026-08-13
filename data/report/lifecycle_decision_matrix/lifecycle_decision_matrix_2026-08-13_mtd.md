# Lifecycle Decision Matrix - 2026-08-13

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-08-13_mtd`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `13366`
- source_rows_total: `18379`
- retained_rows: `13366`
- dropped_rows_by_source: `{}`
- joined_rows: `4786`
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
- lifecycle_flow_bucket_count: `116`
- lifecycle_flow_complete_count: `46`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0056`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 6779 | 100 | 2.1438 | 0.2251 | `pass` | `NO_CHANGE` | False |
| `submit` | 366 | 48 | -0.2288 | 0.2797 | `pass` | `NO_CHANGE` | False |
| `holding` | 65 | 48 | -0.5306 | 0.622 | `pass` | `EXIT` | False |
| `scale_in` | 4555 | 4520 | -0.7538 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 1601 | 70 | -0.5953 | 0.2772 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 116, 'complete_flow_count': 46, 'incomplete_flow_count': 8214, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 4156 | 4123 | -0.8615 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 399 | 397 | 0.3642 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 58 | 58 | 3.4417 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:4e1fc29475` | 4 | 4 | -0.842 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:d0233209ef` | 4 | 4 | -0.6925 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 4 | 4 | 3.1589 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:5159f83a5b` | 3 | 3 | -0.1136 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:cb6ed22b69` | 3 | 3 | -1.0067 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:305d9e5c71` | 3 | 3 | -0.2375 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:b75bf201fa` | 2 | 2 | -0.745 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:397dbf1728` | 2 | 2 | -0.84 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:62b3401904` | 2 | 2 | -0.1725 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:5ad377bcf7` | 1 | 1 | -0.4211 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:7dd76f2392` | 1 | 1 | -2.1224 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_bl:36dfb94c33` | 1 | 1 | -0.54 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:8b2aea4c29` | 1 | 1 | -0.86 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:1729d68718` | 1 | 1 | -0.7 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:31a116e56b` | 1 | 1 | -0.7246 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:7664e5a914` | 1 | 1 | -0.1193 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:1fbcba9334` | 1 | 1 | 0.0719 | `hold_no_edge` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 396, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `score_band` | `score_63_65` | 1022 | 86 | 2.3384 | 3.3932 | 0.6395 | `candidate_recovery_or_relax` |
| `liquidity_bucket` | `liquidity_high` | 3384 | 71 | 3.0126 | 4.5347 | 0.7324 | `candidate_recovery_or_relax` |
| `chosen_action` | `WAIT_REQUOTE` | 1354 | 63 | 3.4327 | 5.2779 | 0.746 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 6742 | 63 | 3.4327 | 5.2779 | 0.746 | `source_quality_workorder` |
| `source_stage` | `wait6579_ev_cohort` | 63 | 63 | 3.4327 | 5.2779 | 0.746 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_watch` | 2201 | 46 | 2.3639 | 3.2669 | 0.6957 | `candidate_recovery_or_relax` |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 564 | 28 | -0.1258 | -1.1996 | 0.3214 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_not_available` | 2817 | 28 | -0.1258 | -1.1996 | 0.3214 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_not_available` | 2066 | 28 | -0.1258 | -1.1996 | 0.3214 | `source_quality_workorder` |
| `source_stage` | `scalp_sim_entry_ai_price_skip_order` | 514 | 28 | -0.1258 | -1.1996 | 0.3214 | `hold_sample` |
| `strength_bucket` | `risk_context_not_available` | 375 | 27 | -0.1727 | -1.1848 | 0.3333 | `hold_sample` |
| `stale_bucket` | `stale_not_available` | 1561 | 27 | -0.1727 | -1.1848 | 0.3333 | `source_quality_workorder` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_1000_1200` | 24 | 24 | 2.7518 | 3.8641 | 0.6667 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_trailing_take_profit` | 16 | 16 | -0.2479 | 0.49 | 0.9375 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1000_1200` | 186 | 15 | -0.3392 | -1.1287 | 0.3333 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 15 | 15 | 2.187 | 3.0597 | 0.7333 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 14 | 14 | 0.3435 | -1.4964 | 0.0 | `hold_sample` |
| `overbought_bucket` | `overbought_ok` | 661 | 12 | 5.7694 | 9.8524 | 0.75 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_1000_1200` | 1241 | 12 | -0.4646 | -1.4308 | 0.25 | `hold_sample` |
| `chosen_action` | `NO_BUY_AI` | 4331 | 9 | 0.1817 | -0.5178 | 0.6667 | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 105, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 334 | 48 | -0.2288 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 360 | 48 | -0.2288 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 62 | 48 | -0.2288 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 62 | 48 | -0.2288 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 62 | 48 | -0.2288 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 62 | 48 | -0.2288 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 62 | 48 | -0.2288 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 62 | 48 | -0.2288 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 62 | 48 | -0.2288 | `keep_collecting` |
| `latency_state` | `simulated` | 62 | 48 | -0.2288 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 334 | 48 | -0.2288 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 62 | 48 | -0.2288 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 50 | 41 | -0.1078 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 39 | 34 | -0.1799 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 39 | 29 | 0.1273 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 38 | 29 | 0.1273 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 304 | 29 | 0.1273 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 38 | 29 | 0.1273 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 39 | 29 | 0.1273 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 25 | 19 | -0.7722 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 24 | 19 | -0.7722 | `keep_collecting` |
| `would_limit_fill` | `false` | 329 | 19 | -0.0664 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 22 | 19 | -0.7722 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 23 | 19 | -0.7722 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 24 | 19 | -0.7722 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_3_10s` | 42 | 17 | -0.714 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 17 | 15 | -0.0325 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_ok` | 24 | 14 | -0.3474 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 10 | 10 | -0.622 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 13 | 10 | 0.4954 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 7 | 7 | 0.4465 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 8 | 7 | -0.8454 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 10 | 6 | -1.0513 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 8 | 4 | -0.1938 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 6 | 3 | 0.6095 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_1_3s` | 6 | 2 | -1.2667 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 4 | 2 | -1.2667 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 2 | 1 | -0.2518 | `keep_collecting` |
| `latency_state` | `caution` | 25 | 0 | None | `keep_collecting` |
| `latency_reason` | `caution_normal_entry_allowed` | 25 | 0 | None | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 26, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 60 | 48 | -0.5306 | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 60 | 48 | -0.5306 | `hold_sample` |
| `holding_action` | `WAIT` | 52 | 41 | -0.5256 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 22 | 22 | -1.0108 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 21 | 21 | -0.9753 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 16 | 16 | -0.2654 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 11 | 11 | -0.1419 | `hold_no_edge` |
| `holding_action` | `holding_action_not_applicable_at_start` | 8 | 7 | -0.5595 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 10 | 5 | -0.3908 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 5 | 5 | 0.5942 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 5 | 5 | -0.3908 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 5 | 5 | -0.5371 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 4 | 4 | 0.6118 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1 | 1 | -1.7547 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | 0.5237 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 5 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 3 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 12 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 5 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 11 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_020_180s` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 42, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `exit_source_stage` | `sim_post_sell_evaluation` | 46 | 46 | -0.5355 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 32 | 32 | -1.0168 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 23 | 23 | -0.0991 | `hold_sample` |
| `exit_outcome` | `NEUTRAL` | 21 | 21 | -0.5386 | `hold_no_edge` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 19 | 19 | -0.8411 | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 19 | 19 | -0.8411 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 19 | 19 | -0.8411 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 17 | 17 | -0.4621 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 16 | 16 | -0.2654 | `hold_no_edge` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 15 | 15 | -0.5368 | `hold_sample` |
| `exit_outcome` | `MISSED_UPSIDE` | 14 | 14 | -0.0887 | `hold_sample` |
| `exit_outcome` | `GOOD_EXIT` | 11 | 11 | -1.0982 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 10 | 10 | -1.03 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 10 | 10 | -0.0023 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 9 | 9 | -0.6311 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 8 | 8 | -0.1913 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 7 | 7 | -2.0265 | `hold_sample` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 6 | 6 | -0.1954 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 6 | 6 | -0.8628 | `hold_sample` |
| `exit_outcome` | `COMPLETED` | 5 | 5 | -0.2115 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 5 | 5 | 0.5942 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 5 | 5 | -0.2115 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 5 | 5 | -0.2115 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 5 | 5 | -0.8208 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 3 | 3 | -2.3487 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 3 | 3 | -1.9609 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 3 | 3 | 0.852 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 2 | 2 | 0.2074 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 1 | 1 | -1.3447 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=NEUTRAL|profit=profit_neg070_neg010` | 1 | 1 | -0.115 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | -1.2568 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 1 | 1 | -0.1193 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg070_neg010` | 1 | 1 | -0.8911 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg070_neg010` | 1 | 1 | -0.1128 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 1531 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_context_noop` | 1531 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_euphoria_context_noop` | 338 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_euphoria_context_noop_not_applicable` | 338 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 1193 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_context_warning_not_applicable` | 1193 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 266, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `price_guard_reason` | `price_guard_none` | 4555 | 4520 | None | -0.8259 | 0.0756 | `hold_sample` |
| `qty_reason` | `qty_none` | 4520 | 4520 | None | -0.8259 | 0.0756 | `hold_sample` |
| `time_bucket` | `time_unknown` | 4555 | 4520 | None | -0.8259 | 0.0756 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 4492 | 4490 | None | -0.8365 | 0.0695 | `hold_sample` |
| `arm` | `AVG_DOWN` | 4156 | 4123 | None | -0.9382 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 4146 | 4113 | None | -0.9326 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2511 | 2511 | None | -0.8051 | 0.0669 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 2494 | 2494 | None | -1.268 | 0.0 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 2481 | 2446 | None | -0.7348 | 0.1398 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 2100 | 2100 | None | -0.8042 | 0.0738 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 2113 | 2078 | None | -0.931 | 0.0019 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 1687 | 1687 | None | -0.9888 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 1514 | 1514 | None | -0.4628 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 1420 | 1420 | None | -0.7979 | 0.1085 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 1005 | 1005 | None | -0.8317 | 0.1045 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_1` | 723 | 723 | None | -1.082 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 704 | 704 | None | -0.2405 | 0.4119 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 602 | 602 | None | -0.9486 | 0.0748 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_2` | 516 | 516 | None | -0.8512 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 482 | 482 | None | 0.2089 | 0.6473 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 18, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 10 | 5 | -0.2115 | -0.282 | 0.0 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 5 | 5 | -0.2115 | -0.282 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 5 | 5 | -0.2115 | -0.282 | 0.0 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 10 | 5 | -0.2115 | -0.282 | 0.0 | `hold_sample` |
| `stage` | `exit` | 5 | 5 | -0.2115 | -0.282 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 10 | 5 | -0.2115 | -0.282 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 10 | 5 | -0.2115 | -0.282 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 10 | 5 | -0.2115 | -0.282 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 5 | 5 | -0.2115 | -0.282 | 0.0 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 8 | 4 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 6 | 3 | -0.2375 | -0.3167 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 2 | 1 | -0.3675 | -0.49 | 0.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 5 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 5 | 0 | None | None | None | `hold_sample` |
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
