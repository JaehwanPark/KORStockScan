# Lifecycle Decision Matrix - 2026-08-27

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-08-27_rolling5d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `10355`
- source_rows_total: `13123`
- retained_rows: `10355`
- dropped_rows_by_source: `{}`
- joined_rows: `5684`
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
- lifecycle_flow_bucket_count: `106`
- lifecycle_flow_complete_count: `59`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0074`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 2602 | 32 | -0.3174 | 0.0126 | `pass` | `NO_CHANGE` | False |
| `submit` | 296 | 67 | -0.7291 | 0.4402 | `pass` | `NO_CHANGE` | False |
| `holding` | 89 | 67 | -0.72 | 0.9574 | `pass` | `EXIT` | False |
| `scale_in` | 5438 | 5400 | -0.8771 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 1930 | 118 | -0.7668 | 0.5374 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 106, 'complete_flow_count': 59, 'incomplete_flow_count': 7867, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 5057 | 5020 | -0.9744 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 380 | 379 | 0.4125 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:a6af469504` | 4 | 4 | -0.9775 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:0cb91a7ba6` | 3 | 3 | -0.98 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:f658be39ac` | 2 | 2 | -1.0987 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:f58154b780` | 1 | 1 | -1.31 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:05c0ca21ce` | 1 | 1 | 0.045 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:7ee2fdca81` | 1 | 1 | 0.0318 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_ai_c:bde1a44f4a` | 1 | 1 | -0.97 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_ai_c:e766b2429d` | 1 | 1 | -0.64 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_ai_c:a101f93752` | 1 | 1 | -0.52 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_bloc:ce21fab319` | 1 | 1 | -0.51 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:555dee5f6c` | 1 | 1 | -0.65 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:3b618795a8` | 1 | 1 | -0.79 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:0c9b051cda` | 1 | 1 | -0.81 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:55248db096` | 1 | 1 | -0.48 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:beb61a6072` | 1 | 1 | -0.52 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:b0bc92a886` | 1 | 1 | -1.93 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:c918fe4c6d` | 1 | 1 | -1.693 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:45a0798af4` | 1 | 1 | -0.4 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 261, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `NO_BUY_AI` | 1149 | 31 | -0.1927 | -1.0897 | 0.3548 | `hold_sample` |
| `liquidity_bucket` | `liquidity_high` | 964 | 31 | -0.1927 | -1.0897 | 0.3548 | `hold_sample` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 2136 | 31 | -0.1927 | -1.0897 | 0.3548 | `source_quality_workorder` |
| `stale_bucket` | `fresh` | 1360 | 30 | -0.1764 | -1.073 | 0.3667 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 984 | 21 | -0.3771 | -1.3519 | 0.2381 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 706 | 19 | -0.3732 | -1.3768 | 0.2632 | `hold_sample` |
| `score_band` | `score_70p` | 203 | 15 | -0.3909 | -0.874 | 0.2667 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 293 | 14 | 0.0717 | -1.0878 | 0.2143 | `hold_sample` |
| `overbought_bucket` | `overbought_watch` | 582 | 14 | -0.2895 | -1.2886 | 0.4286 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 13 | 13 | -0.2638 | -1.5654 | 0.0 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 12 | 12 | -0.3311 | 0.4559 | 0.8333 | `hold_sample` |
| `score_band` | `score_63_65` | 60 | 11 | -0.0947 | -1.1127 | 0.4546 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 8 | 6 | -0.0405 | -1.2183 | 0.1666 | `hold_sample` |
| `time_bucket` | `time_1200_1400` | 588 | 6 | 0.3027 | -1.0817 | 0.5 | `hold_sample` |
| `strength_bucket` | `neutral_strength_momentum` | 1094 | 5 | 0.1317 | 0.028 | 0.8 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 5 | 5 | -0.424 | -3.316 | 0.0 | `hold_sample` |
| `score_band` | `score_lt60` | 2329 | 5 | -0.5909 | -1.21 | 0.4 | `source_quality_workorder` |
| `strength_bucket` | `strong_strength_momentum` | 323 | 5 | 0.2576 | -1.106 | 0.4 | `hold_sample` |
| `time_bucket` | `time_0900_1000` | 523 | 5 | -0.873 | -0.802 | 0.2 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_1000_1200` | 4 | 4 | 0.2355 | -1.35 | 0.5 | `hold_sample` |

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
| `actual_order_submitted` | `false` | 266 | 67 | -0.7291 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 287 | 67 | -0.7291 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 82 | 67 | -0.7291 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 82 | 67 | -0.7291 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 82 | 67 | -0.7291 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 82 | 67 | -0.7291 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 82 | 67 | -0.7291 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 82 | 67 | -0.7291 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 82 | 67 | -0.7291 | `keep_collecting` |
| `latency_state` | `simulated` | 82 | 67 | -0.7291 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 266 | 67 | -0.7291 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 76 | 61 | -0.6674 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 58 | 44 | -0.5359 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 49 | 37 | -0.3629 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 49 | 37 | -0.3629 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 39 | 35 | -1.1964 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 46 | 35 | -0.483 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 39 | 35 | -1.1964 | `source_quality_workorder` |
| `price_resolution_bucket` | `price_resolution_unknown` | 43 | 32 | -0.2179 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 216 | 32 | -0.2179 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 43 | 32 | -0.2179 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 36 | 30 | -1.1807 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 33 | 30 | -1.1807 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 33 | 30 | -1.1807 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 59 | 29 | -1.2266 | `keep_collecting` |
| `would_limit_fill` | `false` | 245 | 23 | -0.3046 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 26 | 19 | -0.3113 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 20 | 17 | -1.029 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 18 | 17 | -1.0079 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 15 | 14 | -0.86 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 15 | 13 | -1.4235 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 12 | 12 | -1.4717 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 12 | 9 | 0.0035 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 12 | 9 | 0.0035 | `keep_collecting` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 6 | 6 | -1.3553 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_10s_plus` | 12 | 6 | -1.0502 | `keep_collecting` |
| `overbought_guard_action` | `would_block` | 6 | 6 | -1.3553 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_overbought_guard_would_block` | 5 | 5 | -1.2904 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 5 | 4 | -0.2725 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 4 | 3 | 0.2699 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 36, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 81 | 67 | -0.72 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 81 | 67 | -0.72 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 54 | 43 | -0.8309 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 36 | 31 | -1.3206 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 27 | 24 | -0.5213 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 24 | 24 | -1.2106 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 18 | 17 | -0.2815 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 9 | 9 | -0.172 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 8 | 8 | -0.4046 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 9 | 7 | -0.5098 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 7 | 7 | -1.698 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 6 | 6 | -0.3671 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 5 | 5 | 0.5928 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 4 | 4 | -0.3341 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 4 | 4 | -0.1182 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 3 | 3 | -1.0318 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 3 | 3 | -0.2317 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 1.8295 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 2 | 2 | -0.433 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 1 | 1 | 0.2903 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 0.2903 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 8 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 3 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 3 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 14 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 8 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 11 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_020_180s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_180_600s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 51, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `exit_source_stage` | `sim_post_sell_evaluation` | 64 | 64 | -0.6818 | `hold_no_edge` |
| `profit_band` | `profit_lt_neg070` | 59 | 59 | -1.2183 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 46 | 46 | -0.8685 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 46 | 46 | -0.8685 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 46 | 46 | -0.8685 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 33 | 33 | -0.1712 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 29 | 29 | -0.5141 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 26 | 26 | -1.1265 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 22 | 22 | -1.2043 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 22 | 22 | -0.5985 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 20 | 20 | -0.1985 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 20 | 20 | -0.533 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 18 | 18 | -0.2634 | `hold_no_edge` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 14 | 14 | -1.0324 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 13 | 13 | -0.8125 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 12 | 12 | -1.6558 | `hold_sample` |
| `exit_outcome` | `COMPLETED` | 8 | 8 | -0.8625 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 8 | 8 | -0.8625 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 8 | 8 | -0.8558 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 8 | 8 | -1.3859 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 7 | 7 | -0.2711 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 6 | 6 | -0.3671 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 5 | 5 | 0.5928 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_lt_neg070` | 5 | 5 | -1.2525 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 5 | 5 | -0.7503 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 5 | 5 | 0.5955 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 4 | 4 | -1.56 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 4 | 4 | -1.4289 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 3 | 3 | -2.4491 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg070_neg010` | 3 | 3 | 0.3314 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 2 | 2 | -0.3412 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 2 | 2 | -0.6835 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=NEUTRAL|profit=profit_neg070_neg010` | 2 | 2 | -0.7522 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 2 | 2 | -0.63 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 2 | 2 | 0.6301 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 1 | 1 | 0.2903 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg010_pos080` | 1 | 1 | 0.045 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 1 | 1 | -1.4784 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 1 | 1 | -0.1496 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=NEUTRAL|profit=profit_lt_neg070` | 1 | 1 | -0.5293 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 310, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `price_guard_reason` | `price_guard_none` | 5437 | 5400 | None | -0.9603 | 0.0674 | `hold_sample` |
| `qty_reason` | `qty_none` | 5401 | 5400 | None | -0.9603 | 0.0674 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 5390 | 5390 | None | -0.9649 | 0.0659 | `hold_sample` |
| `arm` | `AVG_DOWN` | 5058 | 5021 | None | -1.0607 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 5022 | 4985 | None | -1.0456 | 0.0 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 3026 | 3026 | None | -0.9817 | 0.0678 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 3015 | 3015 | None | -1.4867 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2862 | 2862 | None | -0.978 | 0.0783 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 2608 | 2570 | None | -1.0516 | 0.0008 | `hold_sample` |
| `time_bucket` | `time_unknown` | 2567 | 2548 | None | -0.827 | 0.117 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 2104 | 2104 | None | -1.1461 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 1885 | 1885 | None | -0.4431 | 0.0 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 1427 | 1408 | None | -0.6985 | 0.2119 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 1391 | 1391 | None | -1.0725 | 0.0532 | `hold_sample` |
| `ai_score_source` | `live` | 1140 | 1140 | None | -0.8758 | 0.1009 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 753 | 753 | None | -0.7963 | 0.0704 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 672 | 672 | None | -0.225 | 0.4613 | `hold_sample` |
| `ai_score_source` | `not_evaluated_no_ai_score_source` | 549 | 549 | None | -0.7372 | 0.0255 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_1` | 462 | 462 | None | -1.1541 | 0.0 | `hold_sample` |
| `ai_score_source` | `holding_ai_not_called` | 453 | 453 | None | -1.2595 | 0.0243 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 16 | 8 | -0.8625 | -1.15 | 0.125 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 8 | 8 | -0.8625 | -1.15 | 0.125 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 16 | 8 | -0.8625 | -1.15 | 0.125 | `hold_sample` |
| `stage` | `exit` | 8 | 8 | -0.8625 | -1.15 | 0.125 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 16 | 8 | -0.8625 | -1.15 | 0.125 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 16 | 8 | -0.8625 | -1.15 | 0.125 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 8 | 8 | -0.8625 | -1.15 | 0.125 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 14 | 7 | -0.9922 | -1.3229 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 5 | 5 | -1.2525 | -1.67 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 10 | 5 | -1.2525 | -1.67 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 6 | 3 | -1.1525 | -1.5367 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 6 | 3 | -0.7325 | -0.9767 | 0.3333 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 2 | 2 | -0.3412 | -0.455 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 4 | 2 | -0.3412 | -0.455 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 1 | 1 | 0.045 | 0.06 | 1.0 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 2 | 1 | -0.8475 | -1.13 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 2 | 1 | -0.3975 | -0.53 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 2 | 1 | 0.045 | 0.06 | 1.0 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 2 | 1 | 0.045 | 0.06 | 1.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 8 | 0 | None | None | None | `hold_sample` |

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
