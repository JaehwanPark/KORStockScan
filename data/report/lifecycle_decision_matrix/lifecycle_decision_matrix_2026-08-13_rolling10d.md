# Lifecycle Decision Matrix - 2026-08-13

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-08-13_rolling10d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `11831`
- source_rows_total: `15605`
- retained_rows: `11831`
- dropped_rows_by_source: `{}`
- joined_rows: `4655`
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
- lifecycle_flow_bucket_count: `108`
- lifecycle_flow_complete_count: `43`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0057`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 5541 | 35 | -0.1239 | 0.0094 | `pass` | `NO_CHANGE` | False |
| `submit` | 297 | 46 | -0.292 | 0.2916 | `pass` | `NO_CHANGE` | False |
| `holding` | 62 | 46 | -0.5743 | 0.6432 | `pass` | `EXIT` | False |
| `scale_in` | 4497 | 4462 | -0.7524 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 1434 | 66 | -0.6174 | 0.2934 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 108, 'complete_flow_count': 43, 'incomplete_flow_count': 7486, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 4103 | 4070 | -0.8595 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 394 | 392 | 0.3597 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:4e1fc29475` | 4 | 4 | -0.842 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:5159f83a5b` | 3 | 3 | -0.1136 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:d0233209ef` | 3 | 3 | -0.6467 | `candidate_tighten_or_exclude` | `pass` |
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
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:9e4edc4bd2` | 1 | 1 | -0.99 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:f3f2837f26` | 1 | 1 | -1.6262 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 354, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 421 | 27 | -0.1727 | -1.1848 | 0.3333 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_not_available` | 2163 | 27 | -0.1727 | -1.1848 | 0.3333 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_not_available` | 1550 | 27 | -0.1727 | -1.1848 | 0.3333 | `source_quality_workorder` |
| `strength_bucket` | `risk_context_not_available` | 375 | 27 | -0.1727 | -1.1848 | 0.3333 | `hold_sample` |
| `source_stage` | `scalp_sim_entry_ai_price_skip_order` | 375 | 27 | -0.1727 | -1.1848 | 0.3333 | `hold_sample` |
| `stale_bucket` | `stale_not_available` | 1561 | 27 | -0.1727 | -1.1848 | 0.3333 | `source_quality_workorder` |
| `score_band` | `score_63_65` | 673 | 25 | -0.1988 | -0.8532 | 0.4 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 15 | 15 | -0.3516 | 0.4487 | 0.9333 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1000_1200` | 139 | 15 | -0.3392 | -1.1287 | 0.3333 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 13 | 13 | 0.2821 | -1.4885 | 0.0 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 1241 | 12 | -0.4646 | -1.4308 | 0.25 | `hold_sample` |
| `time_bucket` | `time_0900_1000` | 941 | 9 | 0.3283 | -1.0078 | 0.3333 | `hold_sample` |
| `chosen_action` | `NO_BUY_AI` | 3812 | 8 | 0.041 | -0.7212 | 0.625 | `source_quality_workorder` |
| `stale_bucket` | `fresh` | 3418 | 8 | 0.041 | -0.7212 | 0.625 | `hold_sample` |
| `liquidity_bucket` | `liquidity_high` | 2994 | 8 | 0.041 | -0.7212 | 0.625 | `hold_sample` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 3785 | 8 | 0.041 | -0.7212 | 0.625 | `source_quality_workorder` |
| `time_bucket` | `time_1200_1400` | 999 | 8 | -0.4114 | -1.3913 | 0.5 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 7 | 7 | -0.3901 | -3.5914 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_0900_1000` | 49 | 6 | 0.4744 | -0.8183 | 0.3333 | `hold_sample` |
| `score_band` | `score_70p` | 126 | 6 | 0.0504 | -1.2067 | 0.5 | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 103, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 279 | 46 | -0.292 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 291 | 46 | -0.292 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 59 | 46 | -0.292 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 59 | 46 | -0.292 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 59 | 46 | -0.292 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 59 | 46 | -0.292 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 59 | 46 | -0.292 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 59 | 46 | -0.292 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 59 | 46 | -0.292 | `keep_collecting` |
| `latency_state` | `simulated` | 59 | 46 | -0.292 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 279 | 46 | -0.292 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 59 | 46 | -0.292 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 47 | 39 | -0.1762 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 38 | 33 | -0.2199 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 37 | 28 | 0.0852 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 36 | 28 | 0.0852 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 250 | 28 | 0.0852 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 36 | 28 | 0.0852 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 37 | 28 | 0.0852 | `keep_collecting` |
| `would_limit_fill` | `false` | 262 | 19 | -0.0664 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 24 | 18 | -0.8785 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 23 | 18 | -0.8785 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 21 | 18 | -0.8785 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 22 | 18 | -0.8785 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 23 | 18 | -0.8785 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_3_10s` | 33 | 16 | -0.83 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 17 | 15 | -0.0325 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_ok` | 22 | 13 | -0.4748 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 9 | 9 | -0.818 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 12 | 9 | 0.4051 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 7 | 7 | 0.4465 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 8 | 7 | -0.8454 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 10 | 6 | -1.0513 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 7 | 4 | -0.1938 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_1_3s` | 5 | 2 | -1.2667 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 5 | 2 | 0.2605 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 4 | 2 | -1.2667 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 2 | 1 | -0.2518 | `keep_collecting` |
| `latency_state` | `caution` | 15 | 0 | None | `keep_collecting` |
| `latency_reason` | `caution_normal_entry_allowed` | 15 | 0 | None | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 26, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 57 | 46 | -0.5743 | `hold_no_edge` |
| `holding_source_stage` | `scalp_sim_holding_started` | 57 | 46 | -0.5743 | `hold_no_edge` |
| `holding_action` | `WAIT` | 49 | 39 | -0.577 | `hold_no_edge` |
| `profit_band` | `profit_lt_neg070` | 21 | 21 | -1.047 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 20 | 20 | -1.0116 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 16 | 16 | -0.2654 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 11 | 11 | -0.1419 | `hold_no_edge` |
| `holding_action` | `holding_action_not_applicable_at_start` | 8 | 7 | -0.5595 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 10 | 5 | -0.3908 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 5 | 5 | -0.3908 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 5 | 5 | -0.5371 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 4 | 4 | 0.4424 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 3 | 3 | 0.4153 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1 | 1 | -1.7547 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | 0.5237 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 5 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 3 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 11 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 5 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 10 | 0 | None | `hold_sample` |
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
| `exit_source_stage` | `sim_post_sell_evaluation` | 44 | 44 | -0.5814 | `hold_no_edge` |
| `profit_band` | `profit_lt_neg070` | 29 | 29 | -1.0488 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 22 | 22 | -0.1582 | `hold_no_edge` |
| `exit_outcome` | `NEUTRAL` | 21 | 21 | -0.5386 | `hold_no_edge` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 17 | 17 | -0.83 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 17 | 17 | -0.4621 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 17 | 17 | -0.83 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 17 | 17 | -0.83 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 16 | 16 | -0.2654 | `hold_no_edge` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 14 | 14 | -0.5572 | `hold_sample` |
| `exit_outcome` | `MISSED_UPSIDE` | 12 | 12 | -0.1826 | `hold_sample` |
| `exit_outcome` | `GOOD_EXIT` | 11 | 11 | -1.0982 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 10 | 10 | -0.0023 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 9 | 9 | -0.6311 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 8 | 8 | -1.0537 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 7 | 7 | -2.0265 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 7 | 7 | -0.1827 | `hold_sample` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 6 | 6 | -0.1954 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 6 | 6 | -0.8628 | `hold_sample` |
| `exit_outcome` | `COMPLETED` | 5 | 5 | -0.2115 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 5 | 5 | -0.2115 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 5 | 5 | -0.2115 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 5 | 5 | -0.8208 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 4 | 4 | 0.4424 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 3 | 3 | -2.3487 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 3 | 3 | -1.9609 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 2 | 2 | 0.2074 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 2 | 2 | 0.6774 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 1 | 1 | -1.3447 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=NEUTRAL|profit=profit_neg070_neg010` | 1 | 1 | -0.115 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | -1.2568 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 1 | 1 | -0.1193 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg070_neg010` | 1 | 1 | -0.8911 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg070_neg010` | 1 | 1 | -0.1128 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 1368 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_context_noop` | 1368 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_euphoria_context_noop` | 197 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_euphoria_context_noop_not_applicable` | 197 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 1171 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_context_warning_not_applicable` | 1171 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 258, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `price_guard_reason` | `price_guard_none` | 4497 | 4462 | None | -0.8243 | 0.0755 | `hold_sample` |
| `qty_reason` | `qty_none` | 4462 | 4462 | None | -0.8243 | 0.0755 | `hold_sample` |
| `time_bucket` | `time_unknown` | 4497 | 4462 | None | -0.8243 | 0.0755 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 4434 | 4432 | None | -0.8349 | 0.0693 | `hold_sample` |
| `arm` | `AVG_DOWN` | 4103 | 4070 | None | -0.936 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 4093 | 4060 | None | -0.9303 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2510 | 2510 | None | -0.805 | 0.0669 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 2460 | 2460 | None | -1.2642 | 0.0 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 2452 | 2417 | None | -0.7339 | 0.1394 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 2100 | 2100 | None | -0.8042 | 0.0738 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 2084 | 2049 | None | -0.9287 | 0.0019 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 1674 | 1674 | None | -0.9872 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 1495 | 1495 | None | -0.4643 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 1391 | 1391 | None | -0.7919 | 0.1086 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 1005 | 1005 | None | -0.8317 | 0.1045 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_1` | 715 | 715 | None | -1.0833 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 692 | 692 | None | -0.2292 | 0.4162 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 578 | 578 | None | -0.9335 | 0.0779 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_2` | 510 | 510 | None | -0.8524 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 480 | 480 | None | 0.209 | 0.6458 | `hold_sample` |

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
