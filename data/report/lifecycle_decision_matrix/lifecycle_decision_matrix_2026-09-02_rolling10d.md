# Lifecycle Decision Matrix - 2026-09-02

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-09-02_rolling10d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `18514`
- source_rows_total: `23997`
- retained_rows: `18514`
- dropped_rows_by_source: `{}`
- joined_rows: `9856`
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
- lifecycle_flow_bucket_count: `143`
- lifecycle_flow_complete_count: `98`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0071`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 5169 | 48 | -0.3492 | 0.0099 | `pass` | `NO_CHANGE` | False |
| `submit` | 566 | 108 | -0.8396 | 0.3331 | `pass` | `NO_CHANGE` | False |
| `holding` | 143 | 108 | -0.8455 | 0.8954 | `pass` | `EXIT` | False |
| `scale_in` | 9449 | 9392 | -0.8536 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 3187 | 200 | -0.8621 | 0.4233 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 143, 'complete_flow_count': 98, 'incomplete_flow_count': 13676, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 8602 | 8547 | -0.9834 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 846 | 844 | 0.4613 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:0cb91a7ba6` | 7 | 7 | -0.9271 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:a6af469504` | 5 | 5 | -0.874 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:5ee2a7cfd7` | 5 | 5 | -1.068 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:b31cc048c8` | 3 | 3 | -1.2133 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:f58154b780` | 2 | 2 | -1.12 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:b0bc92a886` | 2 | 2 | -1.455 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:e6cc63e69d` | 2 | 2 | -1.15 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:8de6b2fa46` | 2 | 2 | -1.035 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:c876ed88d1` | 2 | 2 | -1.175 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:f658be39ac` | 2 | 2 | -1.0987 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:7a29eed6f7` | 1 | 1 | -1.249 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:1793c3951c` | 1 | 1 | -0.6466 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:05c0ca21ce` | 1 | 1 | 0.045 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:f4d0891804` | 1 | 1 | -0.88 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:a9d1313d5d` | 1 | 1 | 0.1763 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:7ee2fdca81` | 1 | 1 | 0.0318 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_bl:44fb83e208` | 1 | 1 | -0.79 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_ai_c:bde1a44f4a` | 1 | 1 | -0.97 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 306, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `NO_BUY_AI` | 2218 | 44 | -0.2745 | -1.097 | 0.3409 | `hold_sample` |
| `liquidity_bucket` | `liquidity_high` | 1885 | 44 | -0.2745 | -1.097 | 0.3409 | `hold_sample` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 4278 | 44 | -0.2745 | -1.097 | 0.3409 | `source_quality_workorder` |
| `stale_bucket` | `fresh` | 2602 | 43 | -0.265 | -1.0856 | 0.3488 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 1440 | 29 | -0.3252 | -1.3707 | 0.2414 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 1915 | 29 | -0.2794 | -1.3607 | 0.2414 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 574 | 22 | 0.0141 | -1.0759 | 0.2273 | `hold_sample` |
| `score_band` | `score_70p` | 345 | 21 | -0.5583 | -0.8967 | 0.3333 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 20 | 20 | -0.2512 | -1.5395 | 0.0 | `hold_sample` |
| `score_band` | `score_63_65` | 106 | 19 | -0.0862 | -0.9758 | 0.4211 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 18 | 18 | -0.4093 | 0.4128 | 0.8889 | `hold_sample` |
| `overbought_bucket` | `overbought_watch` | 1102 | 17 | -0.221 | -1.36 | 0.4118 | `hold_sample` |
| `strength_bucket` | `neutral_strength_momentum` | 2278 | 9 | -0.6143 | -0.1989 | 0.6667 | `hold_sample` |
| `time_bucket` | `time_1200_1400` | 1217 | 9 | -0.315 | -0.8555 | 0.5555 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 11 | 7 | -0.1657 | -1.01 | 0.2857 | `hold_sample` |
| `time_bucket` | `time_0900_1000` | 896 | 7 | -0.4168 | -0.4657 | 0.4286 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 6 | 6 | -0.4241 | -3.3933 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 8 | 6 | -0.0405 | -1.2183 | 0.1666 | `hold_sample` |
| `score_band` | `score_lt60` | 4701 | 6 | -0.468 | -1.2617 | 0.3333 | `source_quality_workorder` |
| `strength_bucket` | `strong_strength_momentum` | 560 | 6 | 0.2589 | -1.17 | 0.3333 | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 121, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 520 | 108 | -0.8396 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 547 | 108 | -0.8396 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 134 | 108 | -0.8396 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 134 | 108 | -0.8396 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 134 | 108 | -0.8396 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 134 | 108 | -0.8396 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 134 | 108 | -0.8396 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 134 | 108 | -0.8396 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 134 | 108 | -0.8396 | `keep_collecting` |
| `latency_state` | `simulated` | 134 | 108 | -0.8396 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 520 | 108 | -0.8396 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 127 | 101 | -0.8156 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 104 | 80 | -0.8787 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 86 | 65 | -0.7798 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 68 | 61 | -1.2712 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 68 | 61 | -1.2712 | `source_quality_workorder` |
| `liquidity_bucket` | `below_min_liquidity` | 63 | 56 | -1.2695 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 59 | 56 | -1.2695 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 60 | 56 | -1.2695 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 74 | 52 | -0.3766 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 74 | 52 | -0.3766 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 94 | 50 | -1.4952 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 66 | 47 | -0.2793 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 436 | 47 | -0.2793 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 66 | 47 | -0.2793 | `keep_collecting` |
| `would_limit_fill` | `false` | 480 | 33 | -0.4031 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 34 | 32 | -1.7783 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 42 | 28 | -0.4666 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 24 | 22 | -0.9155 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 23 | 21 | -0.5755 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 23 | 20 | -0.8717 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 17 | 14 | 0.0125 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 14 | 14 | -1.318 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 18 | 14 | 0.0125 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_10s_plus` | 23 | 11 | -0.2528 | `keep_collecting` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 7 | 7 | -1.1843 | `keep_collecting` |
| `overbought_guard_action` | `would_block` | 7 | 7 | -1.1843 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 7 | 6 | -0.0834 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_pre_submit_overbought_guard_would_block` | 5 | 5 | -1.2904 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 6 | 5 | -0.0478 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 38, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 130 | 108 | -0.8455 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 130 | 108 | -0.8455 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 99 | 80 | -1.0537 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 63 | 54 | -1.5036 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 47 | 47 | -1.4747 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 31 | 28 | -0.2506 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 29 | 28 | -0.2743 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 17 | 17 | -0.3035 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 11 | 11 | -0.2291 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 12 | 9 | -0.3075 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 8 | 8 | -0.1478 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 7 | 7 | -0.5075 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 7 | 7 | -1.698 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 6 | 6 | -0.8069 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 5 | 5 | -0.4589 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 5 | 5 | -0.5373 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 4 | 4 | -0.1182 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 2 | 2 | 2.5344 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 1.8295 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 2 | 2 | 2.5344 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 2 | 2 | -0.433 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 13 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 4 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 6 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 22 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 13 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 19 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_020_180s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_180_600s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 4 | 0 | None | `hold_sample` |
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
- summary: `{'bucket_count': 56, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 116 | 116 | -1.284 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 107 | 107 | -0.8211 | `hold_no_edge` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 80 | 80 | -0.9089 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 80 | 80 | -0.9089 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 80 | 80 | -0.9089 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 55 | 55 | -1.0856 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 52 | 52 | -0.1666 | `candidate_recovery_or_relax` |
| `exit_outcome` | `GOOD_EXIT` | 40 | 40 | -1.4377 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 37 | 37 | -0.448 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 36 | 36 | -0.7297 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 31 | 31 | -0.1317 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg010_pos080` | 30 | 30 | -0.2412 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 25 | 25 | -0.52 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 23 | 23 | -0.8579 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 23 | 23 | -2.1819 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 22 | 22 | -0.9604 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `COMPLETED` | 13 | 13 | -0.9115 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 13 | 13 | -0.9115 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 12 | 12 | -0.2381 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 11 | 11 | -0.843 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 10 | 10 | -2.6481 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_lt_neg070` | 9 | 9 | -1.2317 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 9 | 9 | -1.7349 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 8 | 8 | -0.1478 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 8 | 8 | -0.9539 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 8 | 8 | 0.4195 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300` | 7 | 7 | -0.5075 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 6 | 6 | -1.4883 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 5 | 5 | -0.5853 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 5 | 5 | -0.7503 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 4 | 4 | -2.0224 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 4 | 4 | -1.1675 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 3 | 3 | -0.27 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 3 | 3 | -1.7414 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg070_neg010` | 3 | 3 | 0.3314 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 3 | 3 | 0.1747 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 2 | 2 | 2.5344 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=NEUTRAL|profit=profit_lt_neg070` | 2 | 2 | -0.7517 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=NEUTRAL|profit=profit_neg070_neg010` | 2 | 2 | -0.7522 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg070_neg010` | 2 | 2 | -0.4814 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 388, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `price_guard_reason` | `price_guard_none` | 9447 | 9392 | None | -0.9382 | 0.0874 | `hold_sample` |
| `qty_reason` | `qty_none` | 9394 | 9392 | None | -0.9382 | 0.0874 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 9381 | 9380 | None | -0.9409 | 0.0866 | `hold_sample` |
| `arm` | `AVG_DOWN` | 8603 | 8548 | None | -1.0733 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 8527 | 8472 | None | -1.0543 | 0.0 | `hold_sample` |
| `time_bucket` | `time_unknown` | 6578 | 6540 | None | -0.8766 | 0.1155 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 5271 | 5271 | None | -0.9406 | 0.0991 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 5247 | 5247 | None | -1.4974 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 4745 | 4745 | None | -0.9911 | 0.1058 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 4424 | 4367 | None | -1.0657 | 0.0005 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 3643 | 3605 | None | -0.7376 | 0.2096 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 3220 | 3220 | None | -1.147 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 3050 | 3050 | None | -0.4267 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 2507 | 2507 | None | -0.9902 | 0.0638 | `hold_sample` |
| `ai_score_source` | `live` | 1936 | 1936 | None | -0.9125 | 0.1074 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 1646 | 1646 | None | -0.4004 | 0.4022 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 1383 | 1383 | None | -0.7627 | 0.0925 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_1` | 1328 | 1328 | None | -1.194 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 952 | 952 | None | 0.1693 | 0.7143 | `hold_sample` |
| `ai_score_source` | `not_evaluated_no_ai_score_source` | 935 | 935 | None | -0.756 | 0.03 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 26 | 13 | -0.9115 | -1.2154 | 0.0769 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 13 | 13 | -0.9115 | -1.2154 | 0.0769 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 26 | 13 | -0.9115 | -1.2154 | 0.0769 | `hold_sample` |
| `stage` | `exit` | 13 | 13 | -0.9115 | -1.2154 | 0.0769 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 26 | 13 | -0.9115 | -1.2154 | 0.0769 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 26 | 13 | -0.9115 | -1.2154 | 0.0769 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 13 | 13 | -0.9115 | -1.2154 | 0.0769 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 24 | 12 | -0.9913 | -1.3217 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 9 | 9 | -1.2317 | -1.6422 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 18 | 9 | -1.2317 | -1.6422 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 12 | 6 | -1.0412 | -1.3883 | 0.1666 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 8 | 4 | -0.8963 | -1.195 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 3 | 3 | -0.27 | -0.36 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 6 | 3 | -0.27 | -0.36 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 4 | 2 | -0.585 | -0.78 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 1 | 1 | 0.045 | 0.06 | 1.0 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 2 | 1 | -0.8475 | -1.13 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 2 | 1 | 0.045 | 0.06 | 1.0 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 2 | 1 | 0.045 | 0.06 | 1.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 13 | 0 | None | None | None | `hold_sample` |

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
