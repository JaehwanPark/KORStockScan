# Lifecycle Decision Matrix - 2026-08-26

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-08-26_rolling5d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `8709`
- source_rows_total: `11259`
- retained_rows: `8709`
- dropped_rows_by_source: `{}`
- joined_rows: `4757`
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
- lifecycle_flow_bucket_count: `93`
- lifecycle_flow_complete_count: `50`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0073`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 1955 | 28 | -0.3805 | 0.0141 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 234 | 57 | -0.5644 | 0.4891 | `pass` | `NO_CHANGE` | False |
| `holding` | 75 | 57 | -0.709 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 4529 | 4507 | -0.9474 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 1916 | 108 | -0.7653 | 0.521 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 93, 'complete_flow_count': 50, 'incomplete_flow_count': 6810, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 4368 | 4346 | -0.9929 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 160 | 160 | 0.2881 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
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
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:45a0798af4` | 1 | 1 | -0.4 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:e6cc63e69d` | 1 | 1 | -0.85 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 244, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `NO_BUY_AI` | 858 | 27 | -0.2398 | -1.2466 | 0.2963 | `hold_sample` |
| `liquidity_bucket` | `liquidity_high` | 728 | 27 | -0.2398 | -1.2466 | 0.2963 | `hold_sample` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 1596 | 27 | -0.2398 | -1.2466 | 0.2963 | `source_quality_workorder` |
| `stale_bucket` | `fresh` | 1005 | 26 | -0.2228 | -1.2335 | 0.3077 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 724 | 19 | -0.478 | -1.3405 | 0.2105 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 538 | 16 | -0.5209 | -1.4931 | 0.1875 | `hold_sample` |
| `score_band` | `score_70p` | 191 | 15 | -0.3909 | -0.874 | 0.2667 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 208 | 13 | 0.0005 | -1.1792 | 0.1538 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 13 | 13 | -0.2638 | -1.5654 | 0.0 | `hold_sample` |
| `overbought_bucket` | `overbought_watch` | 436 | 12 | -0.3584 | -1.3059 | 0.4167 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 9 | 9 | -0.4785 | 0.2856 | 0.7778 | `hold_sample` |
| `score_band` | `score_63_65` | 39 | 8 | -0.0681 | -1.5025 | 0.375 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 6 | 6 | -0.0405 | -1.2183 | 0.1666 | `hold_sample` |
| `time_bucket` | `time_1200_1400` | 443 | 6 | 0.3027 | -1.0817 | 0.5 | `hold_sample` |
| `time_bucket` | `time_0900_1000` | 391 | 5 | -0.873 | -0.802 | 0.2 | `hold_sample` |
| `strength_bucket` | `neutral_strength_momentum` | 851 | 4 | 0.3506 | -0.5025 | 0.75 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 4 | 4 | -0.5716 | -3.39 | 0.0 | `hold_sample` |
| `score_band` | `score_lt60` | 1718 | 4 | -0.9878 | -1.5375 | 0.25 | `source_quality_workorder` |
| `strength_bucket` | `strong_strength_momentum` | 220 | 4 | 0.3016 | -1.545 | 0.25 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 5 | 3 | -0.3747 | -1.1367 | 0.0 | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 109, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 208 | 57 | -0.5644 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 227 | 57 | -0.5644 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 68 | 57 | -0.5644 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 68 | 57 | -0.5644 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 68 | 57 | -0.5644 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 68 | 57 | -0.5644 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 68 | 57 | -0.5644 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 68 | 57 | -0.5644 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 68 | 57 | -0.5644 | `keep_collecting` |
| `latency_state` | `simulated` | 68 | 57 | -0.5644 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 208 | 57 | -0.5644 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 62 | 51 | -0.4713 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 44 | 34 | -0.203 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 41 | 33 | -0.422 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 41 | 33 | -0.422 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 33 | 29 | -0.8516 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 33 | 29 | -0.8516 | `source_quality_workorder` |
| `price_resolution_bucket` | `price_resolution_unknown` | 35 | 28 | -0.2669 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 166 | 28 | -0.2669 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 35 | 28 | -0.2669 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 34 | 27 | -0.2168 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 30 | 24 | -0.7602 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 50 | 24 | -0.9289 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 27 | 24 | -0.7602 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 27 | 24 | -0.7602 | `keep_collecting` |
| `would_limit_fill` | `false` | 192 | 21 | -0.3849 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 18 | 17 | -1.0079 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 21 | 17 | -0.4113 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 19 | 16 | -0.8771 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 14 | 13 | -0.7597 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 12 | 12 | -1.4717 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 10 | 8 | -0.6535 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 9 | 7 | 0.087 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 9 | 7 | 0.087 | `keep_collecting` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 6 | 6 | -1.3553 | `keep_collecting` |
| `overbought_guard_action` | `would_block` | 6 | 6 | -1.3553 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_10s_plus` | 10 | 5 | -0.4805 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_overbought_guard_would_block` | 5 | 5 | -1.2904 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 5 | 4 | -0.2725 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_overbought_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=pullback_or_rebreak_not_confirmed|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 3 | 3 | 0.7587 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 36, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 67 | 57 | -0.709 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 67 | 57 | -0.709 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 41 | 34 | -0.8703 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 34 | 29 | -1.2641 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 26 | 23 | -0.4704 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 22 | 22 | -1.126 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 13 | 12 | -0.0219 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 9 | 7 | -0.5098 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 7 | 7 | -1.698 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 7 | 7 | -0.2206 | `hold_no_edge` |
| `profit_band` | `profit_pos080_pos150` | 5 | 5 | 0.5928 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 5 | 5 | 0.2563 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 4 | 4 | -0.1182 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 3 | 3 | -1.058 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 3 | 3 | -1.0318 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 3 | 3 | -0.2317 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 1.8295 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 2 | 2 | -0.433 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 1 | 1 | 0.2903 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 1 | 1 | -2.3081 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 0.2903 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 8 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 3 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 3 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 10 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 8 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 7 | 0 | None | `hold_sample` |
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
- summary: `{'bucket_count': 49, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 57 | 57 | -1.186 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 54 | 54 | -0.663 | `hold_no_edge` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 46 | 46 | -0.8685 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 46 | 46 | -0.8685 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 46 | 46 | -0.8685 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 29 | 29 | -0.5141 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 26 | 26 | -1.1265 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 25 | 25 | -0.0839 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 20 | 20 | -0.533 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 19 | 19 | -1.2675 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 18 | 18 | -0.4731 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 17 | 17 | -0.1883 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 14 | 14 | -1.0324 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 13 | 13 | -0.0168 | `hold_no_edge` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 13 | 13 | -0.8125 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 10 | 10 | -1.5588 | `hold_sample` |
| `exit_outcome` | `COMPLETED` | 8 | 8 | -0.8625 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 8 | 8 | -0.8625 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 8 | 8 | -0.8558 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 7 | 7 | -1.1772 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 5 | 5 | 0.5928 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_lt_neg070` | 5 | 5 | -1.2525 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 4 | 4 | -1.56 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 4 | 4 | 0.6121 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 4 | 4 | 0.3299 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 3 | 3 | -1.058 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 3 | 3 | -2.4491 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 3 | 3 | -1.2938 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 3 | 3 | -1.058 | `hold_sample` |
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
- summary: `{'bucket_count': 280, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `price_guard_reason` | `price_guard_none` | 4529 | 4507 | None | -1.0322 | 0.0324 | `hold_sample` |
| `qty_reason` | `qty_none` | 4507 | 4507 | None | -1.0322 | 0.0324 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 4506 | 4506 | None | -1.0327 | 0.0322 | `hold_sample` |
| `arm` | `AVG_DOWN` | 4369 | 4347 | None | -1.0798 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 4338 | 4316 | None | -1.065 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 2620 | 2620 | None | -1.5081 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2581 | 2581 | None | -1.0505 | 0.0322 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 2565 | 2565 | None | -1.0214 | 0.0316 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 2242 | 2220 | None | -1.0728 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 1888 | 1888 | None | -1.1419 | 0.0 | `hold_sample` |
| `time_bucket` | `time_unknown` | 1658 | 1655 | None | -0.9509 | 0.0483 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 1654 | 1654 | None | -0.4465 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 1046 | 1046 | None | -1.1519 | 0.0287 | `hold_sample` |
| `ai_score_source` | `live` | 962 | 962 | None | -1.0077 | 0.0458 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 865 | 862 | None | -0.8989 | 0.0928 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 585 | 585 | None | -0.8578 | 0.0495 | `hold_sample` |
| `ai_score_source` | `holding_ai_not_called` | 390 | 390 | None | -1.2895 | 0.0154 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 382 | 382 | None | -0.343 | 0.3429 | `hold_sample` |
| `ai_score_source` | `not_evaluated_no_ai_score_source` | 376 | 376 | None | -0.8154 | 0.0133 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_1` | 350 | 350 | None | -1.1528 | 0.0 | `hold_sample` |

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
