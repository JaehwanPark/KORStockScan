# Lifecycle Decision Matrix - 2026-08-25

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-08-25_mtd`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `29571`
- source_rows_total: `39960`
- retained_rows: `29571`
- dropped_rows_by_source: `{}`
- joined_rows: `11875`
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
- lifecycle_flow_bucket_count: `216`
- lifecycle_flow_complete_count: `141`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.007`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 11491 | 153 | 1.2426 | 0.1517 | `pass` | `NO_CHANGE` | False |
| `submit` | 984 | 159 | -0.5817 | 0.3818 | `pass` | `NO_CHANGE` | False |
| `holding` | 218 | 157 | -0.8095 | 0.8139 | `pass` | `EXIT` | False |
| `scale_in` | 11224 | 11142 | -0.8144 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 5654 | 264 | -0.7797 | 0.3543 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 216, 'complete_flow_count': 141, 'incomplete_flow_count': 19977, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 10264 | 10184 | -0.9244 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 959 | 957 | 0.3557 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 58 | 58 | 3.4417 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:a6af469504` | 5 | 5 | -0.974 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:0cb91a7ba6` | 5 | 5 | -0.982 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:f658be39ac` | 5 | 5 | -1.5 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:4e1fc29475` | 4 | 4 | -0.842 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:d0233209ef` | 4 | 4 | -0.6925 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 4 | 4 | 3.1589 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:03eec49aed` | 4 | 4 | -0.9565 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:5159f83a5b` | 3 | 3 | -0.1136 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:cb6ed22b69` | 3 | 3 | -1.0067 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:305d9e5c71` | 3 | 3 | -0.2375 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:62b3401904` | 3 | 3 | -0.26 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:b75bf201fa` | 2 | 2 | -0.745 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:397dbf1728` | 2 | 2 | -0.84 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_ai_c:a101f93752` | 2 | 2 | -0.845 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:f548b6989d` | 2 | 2 | -0.54 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:5c4d0773e1` | 2 | 2 | -1.0275 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:b0bc92a886` | 2 | 2 | -1.365 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 446, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 5251 | 119 | 1.6422 | 2.2736 | 0.5714 | `candidate_recovery_or_relax` |
| `score_band` | `score_63_65` | 1109 | 96 | 1.9998 | 2.9935 | 0.625 | `candidate_recovery_or_relax` |
| `chosen_action` | `WAIT_REQUOTE` | 3242 | 65 | 3.3381 | 5.1293 | 0.7538 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 11401 | 63 | 3.4327 | 5.2779 | 0.746 | `source_quality_workorder` |
| `source_stage` | `wait6579_ev_cohort` | 63 | 63 | 3.4327 | 5.2779 | 0.746 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_watch` | 3296 | 59 | 1.6828 | 2.1445 | 0.6102 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 8311 | 59 | -0.2732 | -0.9351 | 0.4068 | `source_quality_workorder` |
| `chosen_action` | `NO_BUY_AI` | 6481 | 57 | -0.2954 | -0.9837 | 0.3859 | `hold_sample` |
| `stale_bucket` | `fresh` | 5984 | 56 | -0.324 | -1.0211 | 0.375 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 2587 | 41 | -0.4042 | -1.2107 | 0.2683 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 40 | 40 | -0.0105 | -1.506 | 0.0 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 4461 | 40 | -0.3683 | -1.1538 | 0.325 | `hold_sample` |
| `score_band` | `score_70p` | 554 | 39 | -0.4113 | -1.1505 | 0.3333 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 1930 | 38 | 0.1702 | -0.5614 | 0.3421 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 36 | 36 | -0.492 | 0.4422 | 0.9167 | `hold_sample` |
| `liquidity_bucket` | `liquidity_not_available` | 5458 | 33 | -0.2821 | -1.1315 | 0.3333 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_not_available` | 4494 | 33 | -0.2821 | -1.1315 | 0.3333 | `source_quality_workorder` |
| `stale_bucket` | `stale_not_available` | 3329 | 32 | -0.3266 | -1.1169 | 0.3438 | `source_quality_workorder` |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 696 | 31 | -0.3234 | -1.2335 | 0.2903 | `source_quality_workorder` |
| `source_stage` | `scalp_sim_entry_ai_price_skip_order` | 588 | 31 | -0.3234 | -1.2335 | 0.2903 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_1000_1200` | 24 | 24 | 2.7518 | 3.8641 | 0.6667 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_ok` | 1098 | 17 | 3.6832 | 7.1493 | 0.8235 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 15 | 15 | 2.187 | 3.0597 | 0.7333 | `candidate_recovery_or_relax` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 131, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 870 | 159 | -0.5817 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 213 | 159 | -0.5817 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 213 | 159 | -0.5817 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 213 | 159 | -0.5817 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 213 | 159 | -0.5817 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 213 | 159 | -0.5817 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 213 | 159 | -0.5817 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 213 | 159 | -0.5817 | `keep_collecting` |
| `latency_state` | `simulated` | 213 | 159 | -0.5817 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 870 | 159 | -0.5817 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 957 | 157 | -0.5925 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 206 | 152 | -0.5908 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 132 | 97 | -0.4452 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 132 | 91 | -0.1803 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 132 | 91 | -0.1803 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 129 | 84 | -0.7153 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 120 | 84 | -0.2249 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 752 | 84 | -0.2249 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 120 | 84 | -0.2249 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 93 | 75 | -0.9812 | `source_quality_workorder` |
| `price_resolution_bucket` | `defensive_order_price` | 91 | 74 | -0.9633 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 89 | 68 | -1.1188 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 80 | 68 | -0.4371 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 79 | 68 | -1.1188 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 81 | 68 | -1.1188 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 164 | 65 | -1.0617 | `keep_collecting` |
| `would_limit_fill` | `false` | 859 | 60 | -0.3042 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 54 | 41 | -0.6161 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 54 | 34 | -0.365 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 31 | 30 | -0.9402 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 34 | 27 | -1.4843 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 34 | 26 | -0.2248 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 32 | 24 | -0.0264 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 26 | 20 | -1.1906 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 25 | 17 | -0.2211 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_10s_plus` | 19 | 8 | -0.2561 | `keep_collecting` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 7 | 7 | -0.3822 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 7 | 7 | 0.4465 | `source_quality_workorder` |
| `overbought_guard_action` | `would_block` | 7 | 7 | -0.3822 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_overbought_guard_would_block` | 5 | 5 | 0.3893 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 38, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 204 | 157 | -0.8095 | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 204 | 157 | -0.8095 | `hold_sample` |
| `holding_action` | `WAIT` | 138 | 105 | -0.8322 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 89 | 82 | -1.3369 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 63 | 63 | -1.1627 | `hold_sample` |
| `holding_action` | `holding_action_not_applicable_at_start` | 65 | 51 | -0.7749 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 45 | 45 | -0.3806 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 25 | 25 | -0.3344 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 19 | 19 | -1.9145 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 19 | 19 | -0.4509 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 20 | 13 | -0.6436 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 12 | 12 | 0.5422 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 9 | 9 | -0.877 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 7 | 7 | 0.0518 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 5 | 5 | 1.2288 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 4 | 4 | 0.3069 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 4 | 4 | -0.1182 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 3 | 3 | -0.179 | `hold_sample` |
| `holding_action` | `BUY` | 1 | 1 | -0.2008 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 1 | 1 | 0.2903 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | -0.2008 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 1 | 1 | 1.7646 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 0.2903 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 14 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 4 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 7 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 47 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 14 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 33 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 14 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_020_180s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 6 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_020_180s` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_180_600s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 52, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `exit_source_stage` | `sim_post_sell_evaluation` | 150 | 150 | -0.7056 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 141 | 141 | -1.2243 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 100 | 100 | -0.885 | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 100 | 100 | -0.885 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 100 | 100 | -0.885 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 72 | 72 | -0.104 | `hold_sample` |
| `exit_outcome` | `NEUTRAL` | 61 | 61 | -0.5628 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 59 | 59 | -0.547 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 58 | 58 | -1.1219 | `hold_sample` |
| `exit_outcome` | `GOOD_EXIT` | 45 | 45 | -1.344 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 45 | 45 | -0.3806 | `hold_no_edge` |
| `exit_outcome` | `MISSED_UPSIDE` | 44 | 44 | -0.2505 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 42 | 42 | -0.7573 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 42 | 42 | -0.5579 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 33 | 33 | -1.9882 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 25 | 25 | -0.8563 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 19 | 19 | -1.03 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 18 | 18 | -0.0815 | `hold_no_edge` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 17 | 17 | -0.7309 | `hold_sample` |
| `exit_outcome` | `COMPLETED` | 14 | 14 | -0.8213 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 14 | 14 | -0.8213 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 14 | 14 | -1.4319 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 12 | 12 | 0.5422 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 11 | 11 | -0.2832 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 10 | 10 | -2.7937 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 9 | 9 | -1.9588 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 8 | 8 | 0.4885 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_lt_neg070` | 7 | 7 | -1.3725 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 7 | 7 | -0.27 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 6 | 6 | -1.2136 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 6 | 6 | 1.0609 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 4 | 4 | 0.3069 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 4 | 4 | -0.2797 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg070_neg010` | 4 | 4 | 0.0258 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 3 | 3 | 2.8197 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 3 | 3 | -0.179 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=NEUTRAL|profit=profit_neg070_neg010` | 2 | 2 | -0.1989 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg070_neg010` | 2 | 2 | -2.1641 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg070_neg010` | 2 | 2 | -1.1643 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 2 | 2 | 0.6301 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 379, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 11102 | 11100 | None | -0.8984 | 0.0762 | `hold_sample` |
| `arm` | `AVG_DOWN` | 10265 | 10185 | None | -1.0076 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 10180 | 10100 | None | -0.9893 | 0.0 | `hold_sample` |
| `price_guard_reason` | `price_guard_none` | 9724 | 9655 | None | -0.8121 | 0.0854 | `hold_sample` |
| `qty_reason` | `qty_none` | 9655 | 9655 | None | -0.8121 | 0.0854 | `hold_sample` |
| `time_bucket` | `time_unknown` | 9724 | 9655 | None | -0.8121 | 0.0854 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 5406 | 5406 | None | -0.8928 | 0.084 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 5315 | 5315 | None | -1.2375 | 0.0 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 5298 | 5229 | None | -0.7219 | 0.1578 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 5063 | 5063 | None | -0.7393 | 0.1165 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 4501 | 4432 | None | -0.9173 | 0.0011 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 3777 | 3777 | None | -0.9687 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 3253 | 3253 | None | -0.4706 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 3141 | 3141 | None | -0.8633 | 0.1102 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 2296 | 2296 | None | -0.9254 | 0.0588 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_1` | 1517 | 1517 | None | -1.0548 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 1428 | 1428 | None | -0.9168 | 0.0476 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 1375 | 1375 | None | -0.1242 | 0.5484 | `hold_sample` |
| `ai_score_source` | `not_evaluated_no_ai_score_source` | 1156 | 1156 | None | -0.7728 | 0.0242 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_2` | 1113 | 1113 | None | -0.8492 | 0.0 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 22, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 28 | 14 | -0.8213 | -1.095 | 0.0 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 14 | 14 | -0.8213 | -1.095 | 0.0 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 28 | 14 | -0.8213 | -1.095 | 0.0 | `hold_sample` |
| `stage` | `exit` | 14 | 14 | -0.8213 | -1.095 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 28 | 14 | -0.8213 | -1.095 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 28 | 14 | -0.8213 | -1.095 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 14 | 14 | -0.8213 | -1.095 | 0.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 20 | 10 | -1.0808 | -1.441 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 7 | 7 | -1.3725 | -1.83 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 7 | 7 | -0.27 | -0.36 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 14 | 7 | -1.2761 | -1.7014 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 14 | 7 | -1.3725 | -1.83 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 14 | 7 | -0.27 | -0.36 | 0.0 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 8 | 4 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 8 | 4 | -0.39 | -0.52 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 4 | 2 | -0.3037 | -0.405 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 2 | 1 | -0.3975 | -0.53 | 0.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 14 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_lt_neg070` | 7 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 7 | 0 | None | None | None | `hold_sample` |

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
