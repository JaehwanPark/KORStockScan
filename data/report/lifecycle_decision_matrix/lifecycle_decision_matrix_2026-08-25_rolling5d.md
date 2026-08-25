# Lifecycle Decision Matrix - 2026-08-25

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-08-25_rolling5d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `6557`
- source_rows_total: `9947`
- retained_rows: `6557`
- dropped_rows_by_source: `{}`
- joined_rows: `2507`
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
- lifecycle_flow_bucket_count: `91`
- lifecycle_flow_complete_count: `50`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0107`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 2005 | 22 | -0.3662 | 0.0095 | `pass` | `NO_CHANGE` | False |
| `submit` | 258 | 52 | -0.54 | 0.4639 | `pass` | `NO_CHANGE` | False |
| `holding` | 69 | 52 | -0.7257 | 0.9451 | `pass` | `EXIT` | False |
| `scale_in` | 2279 | 2273 | -0.8418 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 1946 | 108 | -0.7791 | 0.5209 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 91, 'complete_flow_count': 50, 'incomplete_flow_count': 4624, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 2081 | 2075 | -0.9485 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 197 | 197 | 0.2819 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:a6af469504` | 4 | 4 | -0.9775 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:b0bc92a886` | 2 | 2 | -1.365 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:0cb91a7ba6` | 2 | 2 | -1.07 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:27b40f1c54` | 2 | 2 | -0.755 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:bbe961df76` | 2 | 2 | -0.985 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:f658be39ac` | 2 | 2 | -1.0987 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_ai_c:bde1a44f4a` | 1 | 1 | -0.97 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_ai_c:e766b2429d` | 1 | 1 | -0.64 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_ai_c:a101f93752` | 1 | 1 | -0.52 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_bloc:ce21fab319` | 1 | 1 | -0.51 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:555dee5f6c` | 1 | 1 | -0.65 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:3b618795a8` | 1 | 1 | -0.79 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:9d042ec94c` | 1 | 1 | -1.01 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:0c9b051cda` | 1 | 1 | -0.81 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:55248db096` | 1 | 1 | -0.48 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:3fde12b654` | 1 | 1 | -0.6 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:827611b511` | 1 | 1 | -1.05 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:beb61a6072` | 1 | 1 | -0.52 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 215, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 1632 | 21 | -0.1846 | -1.1876 | 0.3333 | `source_quality_workorder` |
| `chosen_action` | `NO_BUY_AI` | 834 | 20 | -0.2551 | -1.2635 | 0.3 | `hold_sample` |
| `stale_bucket` | `fresh` | 1022 | 20 | -0.2551 | -1.2635 | 0.3 | `hold_sample` |
| `liquidity_bucket` | `liquidity_high` | 718 | 20 | -0.2551 | -1.2635 | 0.3 | `hold_sample` |
| `score_band` | `score_70p` | 249 | 17 | -0.5132 | -1.2041 | 0.2353 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 763 | 14 | -0.3785 | -1.6743 | 0.1429 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 181 | 12 | -0.0183 | -1.125 | 0.1667 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 10 | 10 | -0.3269 | -1.567 | 0.0 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 549 | 10 | -0.5921 | -1.468 | 0.1 | `source_quality_workorder` |
| `exit_rule` | `scalp_trailing_take_profit` | 9 | 9 | -0.0848 | 0.1822 | 0.7778 | `hold_sample` |
| `overbought_bucket` | `overbought_watch` | 469 | 6 | -0.7701 | -2.0667 | 0.3333 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 6 | 6 | -0.0405 | -1.2183 | 0.1666 | `hold_sample` |
| `strength_bucket` | `neutral_strength_momentum` | 899 | 5 | 0.2691 | 0.324 | 1.0 | `hold_sample` |
| `time_bucket` | `time_1200_1400` | 427 | 5 | -0.3466 | -1.688 | 0.4 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_1200_1400` | 15 | 4 | -0.4464 | -1.76 | 0.5 | `hold_sample` |
| `time_bucket` | `time_1400_close` | 618 | 4 | 0.1802 | 0.34 | 1.0 | `source_quality_workorder` |
| `exit_rule` | `scalp_soft_stop_pct` | 3 | 3 | -1.3418 | -3.7133 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 5 | 3 | -0.3747 | -1.1367 | 0.0 | `hold_sample` |
| `score_band` | `score_lt60` | 1743 | 3 | 0.4667 | -1.7433 | 0.3333 | `source_quality_workorder` |
| `time_bucket` | `time_0900_1000` | 411 | 3 | -0.3747 | -1.1367 | 0.0 | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 114, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 214 | 52 | -0.54 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 248 | 52 | -0.54 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 67 | 52 | -0.54 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 67 | 52 | -0.54 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 67 | 52 | -0.54 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 67 | 52 | -0.54 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 67 | 52 | -0.54 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 67 | 52 | -0.54 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 67 | 52 | -0.54 | `keep_collecting` |
| `latency_state` | `simulated` | 67 | 52 | -0.54 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 214 | 52 | -0.54 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 62 | 47 | -0.5801 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 37 | 30 | -0.7735 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 37 | 30 | -0.7735 | `source_quality_workorder` |
| `liquidity_bucket` | `below_min_liquidity` | 34 | 26 | -0.9258 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 36 | 26 | -0.1543 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 37 | 26 | -0.1126 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 65 | 26 | -1.0815 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 30 | 26 | -0.9258 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 31 | 26 | -0.9258 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 36 | 26 | -0.1543 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 30 | 22 | -0.2216 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 168 | 22 | -0.2216 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 30 | 22 | -0.2216 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 25 | 21 | -0.9022 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 25 | 21 | -1.159 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 28 | 19 | -0.0045 | `keep_collecting` |
| `would_limit_fill` | `false` | 216 | 18 | -0.3113 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 15 | 14 | -1.5718 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 14 | 12 | -0.7541 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 16 | 12 | -0.1378 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 10 | 8 | -0.8387 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 9 | 6 | -0.6584 | `source_quality_workorder` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 5 | 5 | -0.1629 | `keep_collecting` |
| `overbought_guard_action` | `would_block` | 5 | 5 | -0.1629 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_10s_plus` | 10 | 4 | 1.2287 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_overbought_guard_would_block` | 4 | 4 | 0.2164 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 5 | 4 | 0.182 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 5 | 4 | 0.182 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_overbought_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=pullback_or_rebreak_not_confirmed|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 3 | 3 | 0.7587 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 31, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 64 | 52 | -0.7257 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 64 | 52 | -0.7257 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 34 | 29 | -0.7881 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 29 | 25 | -1.4511 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 30 | 23 | -0.647 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 14 | 14 | -0.0646 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 14 | 14 | -0.9284 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 11 | 11 | -2.1163 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 9 | 9 | -0.2429 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 7 | 6 | -0.3911 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 5 | 5 | 0.2565 | `hold_no_edge` |
| `profit_band` | `profit_pos080_pos150` | 4 | 4 | 0.5921 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 4 | 4 | -0.1182 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 2 | 2 | -0.433 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 2 | 2 | -0.9368 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | -0.6452 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 1.8295 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 2 | 2 | -0.433 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 1 | 1 | 0.2903 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 0.2903 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 5 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 3 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 12 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 5 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 7 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 5 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_020_180s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_180_600s` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 46, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 56 | 56 | -1.2372 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 54 | 54 | -0.8576 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 54 | 54 | -0.8576 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 54 | 54 | -0.8576 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 49 | 49 | -0.6761 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 31 | 31 | -0.5079 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 30 | 30 | -1.1103 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 26 | 26 | -0.0452 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 24 | 24 | -0.5417 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 17 | 17 | -0.1607 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 16 | 16 | -1.4424 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 16 | 16 | -0.4573 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 14 | 14 | -0.0646 | `hold_no_edge` |
| `exit_rule` | `scalp_soft_stop_pct` | 11 | 11 | -1.9534 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 10 | 10 | -0.9651 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 7 | 7 | -0.7878 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 7 | 7 | -1.379 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 6 | 6 | -0.9248 | `hold_sample` |
| `exit_outcome` | `COMPLETED` | 5 | 5 | -0.9405 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 5 | 5 | -0.9405 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 5 | 5 | 0.6368 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 5 | 5 | 0.0 | `hold_no_edge` |
| `profit_band` | `profit_pos080_pos150` | 4 | 4 | 0.5921 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_lt_neg070` | 4 | 4 | -1.0763 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 4 | 4 | -2.9588 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 4 | 4 | -1.0221 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 3 | 3 | -1.2939 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg070_neg010` | 3 | 3 | 0.3314 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300` | 2 | 2 | -0.433 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 2 | 2 | -0.433 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 2 | 2 | 0.6301 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 1 | 1 | 0.2903 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 1 | 1 | -0.3975 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | -0.2206 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=NEUTRAL|profit=profit_lt_neg070` | 1 | 1 | -0.5293 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=NEUTRAL|profit=profit_neg070_neg010` | 1 | 1 | -0.2828 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg070_neg010` | 1 | 1 | -0.8423 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 1 | 1 | -1.8555 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 1 | 1 | 0.2903 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 1 | 1 | 2.9638 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 221, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `price_guard_reason` | `price_guard_none` | 2279 | 2273 | None | -0.9157 | 0.0805 | `hold_sample` |
| `qty_reason` | `qty_none` | 2273 | 2273 | None | -0.9157 | 0.0805 | `hold_sample` |
| `time_bucket` | `time_unknown` | 2279 | 2273 | None | -0.9157 | 0.0805 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 2265 | 2265 | None | -0.9217 | 0.0772 | `hold_sample` |
| `arm` | `AVG_DOWN` | 2082 | 2076 | None | -1.0272 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 2069 | 2063 | None | -1.0138 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 1258 | 1258 | None | -1.4222 | 0.0 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 1233 | 1227 | None | -0.827 | 0.1491 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 1052 | 1046 | None | -1.0197 | 0.0 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 1015 | 1015 | None | -0.9814 | 0.0433 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 1010 | 1010 | None | -0.7374 | 0.1376 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 935 | 935 | None | -1.085 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 796 | 796 | None | -0.7476 | 0.1633 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 763 | 763 | None | -0.4461 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 638 | 638 | None | -1.1836 | 0.0439 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_1` | 420 | 420 | None | -1.1862 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 393 | 393 | None | -1.0104 | 0.0305 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 278 | 278 | None | -0.0359 | 0.6151 | `hold_sample` |
| `ai_score_source` | `not_evaluated_no_ai_score_source` | 254 | 254 | None | -0.8045 | 0.0118 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_0` | 252 | 252 | None | -0.9585 | 0.0 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 20, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 10 | 5 | -0.9405 | -1.254 | 0.0 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 5 | 5 | -0.9405 | -1.254 | 0.0 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 10 | 5 | -0.9405 | -1.254 | 0.0 | `hold_sample` |
| `stage` | `exit` | 5 | 5 | -0.9405 | -1.254 | 0.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 10 | 5 | -0.9405 | -1.254 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 10 | 5 | -0.9405 | -1.254 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 10 | 5 | -0.9405 | -1.254 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 5 | 5 | -0.9405 | -1.254 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 4 | 4 | -1.0763 | -1.435 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 8 | 4 | -1.0763 | -1.435 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 6 | 3 | -1.1525 | -1.5367 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 1 | 1 | -0.3975 | -0.53 | 0.0 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 2 | 1 | -0.8475 | -1.13 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 2 | 1 | -0.3975 | -0.53 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 2 | 1 | -0.3975 | -0.53 | 0.0 | `hold_sample` |
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
