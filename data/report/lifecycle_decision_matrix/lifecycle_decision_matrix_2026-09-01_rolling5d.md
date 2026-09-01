# Lifecycle Decision Matrix - 2026-09-01

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-09-01_rolling5d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `5843`
- source_rows_total: `7450`
- retained_rows: `5843`
- dropped_rows_by_source: `{}`
- joined_rows: `2943`
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
- lifecycle_flow_bucket_count: `69`
- lifecycle_flow_complete_count: `28`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0067`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 1850 | 13 | -0.5552 | 0.0051 | `pass` | `NO_CHANGE` | False |
| `submit` | 203 | 30 | -1.0227 | 0.1499 | `pass` | `NO_CHANGE` | False |
| `holding` | 40 | 30 | -1.0129 | 0.7683 | `pass` | `EXIT` | False |
| `scale_in` | 2831 | 2813 | -0.6625 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 919 | 57 | -1.0068 | 0.2915 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 69, 'complete_flow_count': 28, 'incomplete_flow_count': 4159, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 2396 | 2379 | -0.8725 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 435 | 434 | 0.4883 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:0cb91a7ba6` | 4 | 4 | -0.8875 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:8de6b2fa46` | 2 | 2 | -1.035 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:5ee2a7cfd7` | 2 | 2 | -1.145 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:f58154b780` | 1 | 1 | -0.93 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:7a29eed6f7` | 1 | 1 | -1.249 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:1793c3951c` | 1 | 1 | -0.6466 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:a9d1313d5d` | 1 | 1 | 0.1763 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_bl:44fb83e208` | 1 | 1 | -0.79 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_ai_c:4bb9b08477` | 1 | 1 | -0.45 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:d7ad29dfc9` | 1 | 1 | -0.44 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:61bcc9f24b` | 1 | 1 | -0.79 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:2a1b39688d` | 1 | 1 | -2.3901 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:b0bc92a886` | 1 | 1 | -0.98 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:b31cc048c8` | 1 | 1 | -1.17 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:2f0e6b68fc` | 1 | 1 | -2.7606 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:a74ce3066d` | 1 | 1 | -0.83 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:04a7285e92` | 1 | 1 | -0.95 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:d89fc00551` | 1 | 1 | -0.1275 | `hold_no_edge` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 210, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `NO_BUY_AI` | 821 | 10 | -0.6714 | -1.144 | 0.3 | `hold_sample` |
| `stale_bucket` | `fresh` | 929 | 10 | -0.6714 | -1.144 | 0.3 | `hold_sample` |
| `liquidity_bucket` | `liquidity_high` | 704 | 10 | -0.6714 | -1.144 | 0.3 | `hold_sample` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 1525 | 10 | -0.6714 | -1.144 | 0.3 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 544 | 9 | -0.2763 | -1.3411 | 0.2222 | `hold_sample` |
| `score_band` | `score_63_65` | 39 | 7 | -0.1705 | -0.9371 | 0.2857 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 242 | 6 | -0.2396 | -1.1967 | 0.1667 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 6 | 6 | -0.2902 | -1.4867 | 0.0 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 5 | 5 | -0.7981 | 0.34 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 6 | 5 | -0.2285 | -1.128 | 0.2 | `hold_sample` |
| `score_band` | `score_70p` | 107 | 5 | -1.1459 | -0.786 | 0.6 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 716 | 5 | -0.1587 | -1.604 | 0.2 | `hold_sample` |
| `strength_bucket` | `neutral_strength_momentum` | 811 | 4 | -1.5467 | -0.4825 | 0.5 | `hold_sample` |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 122 | 3 | -0.1679 | -0.1967 | 0.6667 | `hold_sample` |
| `liquidity_bucket` | `liquidity_not_available` | 1081 | 3 | -0.1679 | -0.1967 | 0.6667 | `hold_sample` |
| `overbought_bucket` | `overbought_not_available` | 995 | 3 | -0.1679 | -0.1967 | 0.6667 | `hold_sample` |
| `strength_bucket` | `risk_context_not_available` | 124 | 3 | -0.1679 | -0.1967 | 0.6667 | `hold_sample` |
| `source_stage` | `scalp_sim_entry_ai_price_skip_order` | 27 | 3 | -0.1679 | -0.1967 | 0.6667 | `hold_sample` |
| `stale_bucket` | `stale_not_available` | 711 | 3 | -0.1679 | -0.1967 | 0.6667 | `hold_sample` |
| `overbought_bucket` | `overbought_ok` | 167 | 2 | -2.8519 | -0.485 | 0.5 | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 106, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 189 | 30 | -1.0227 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 193 | 30 | -1.0227 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 40 | 30 | -1.0227 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 40 | 30 | -1.0227 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 40 | 30 | -1.0227 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 40 | 30 | -1.0227 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 40 | 30 | -1.0227 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 40 | 30 | -1.0227 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 40 | 30 | -1.0227 | `keep_collecting` |
| `latency_state` | `simulated` | 40 | 30 | -1.0227 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 189 | 30 | -1.0227 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 39 | 29 | -1.0525 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 35 | 26 | -1.1762 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 30 | 21 | -1.1282 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 19 | 18 | -1.3287 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 21 | 18 | -1.3287 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 18 | 18 | -1.3287 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 19 | 18 | -1.3287 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 21 | 18 | -1.3287 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_3_10s` | 27 | 15 | -1.4841 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 13 | 13 | -1.6515 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_ok` | 21 | 12 | -0.5638 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 19 | 12 | -0.5638 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 163 | 12 | -0.5638 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 19 | 12 | -0.5638 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 21 | 12 | -0.5638 | `keep_collecting` |
| `would_limit_fill` | `false` | 177 | 8 | -0.8454 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 13 | 7 | -1.0878 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 7 | 6 | -1.1747 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 4 | 4 | -0.0006 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 5 | 4 | -0.0006 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 3 | 3 | 0.0196 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 4 | 3 | 0.0196 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_10s_plus` | 9 | 3 | -0.5513 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 2 | 2 | -0.748 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 2 | 2 | -0.3961 | `source_quality_workorder` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 1 | 1 | -0.1581 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 1 | 1 | 0.851 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=pullback_or_rebreak_not_confirmed|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | -0.1581 | `source_quality_workorder` |
| `overbought_guard_action` | `would_block` | 1 | 1 | -0.1581 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 23, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 37 | 30 | -1.0129 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 37 | 30 | -1.0129 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 34 | 27 | -1.152 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 18 | 16 | -1.5695 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 16 | 16 | -1.5695 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 9 | 9 | -0.2143 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 6 | 6 | -0.441 | `hold_sample` |
| `holding_action` | `holding_action_not_applicable_at_start` | 3 | 3 | 0.2391 | `hold_no_edge` |
| `profit_band` | `profit_pos080_pos150` | 3 | 3 | -1.3821 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 3 | 3 | -1.3821 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 3 | 3 | 0.2391 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 3 | 2 | 0.4003 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 2 | 2 | 0.4003 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 3 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 7 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 7 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_180_600s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 40, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 39 | 39 | -1.2974 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 31 | 31 | -1.0305 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 23 | 23 | -0.9826 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 23 | 23 | -0.9826 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 23 | 23 | -0.9826 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 20 | 20 | -1.0605 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 15 | 15 | -1.6904 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 14 | 14 | -0.4199 | `hold_sample` |
| `exit_outcome` | `NEUTRAL` | 9 | 9 | -0.6921 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 9 | 9 | -0.2143 | `hold_sample` |
| `exit_outcome` | `MISSED_UPSIDE` | 7 | 7 | -0.0515 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 7 | 7 | -0.8545 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 7 | 7 | -2.466 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 6 | 6 | -0.1195 | `hold_no_edge` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 6 | 6 | -0.9445 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 5 | 5 | -2.6155 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 4 | 4 | 0.1059 | `hold_sample` |
| `exit_outcome` | `COMPLETED` | 3 | 3 | -0.9475 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 3 | 3 | -1.3821 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 3 | 3 | -0.9475 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 3 | 3 | -0.4633 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 3 | 3 | -0.5199 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 3 | 3 | -0.771 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_lt_neg070` | 2 | 2 | -1.3575 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 2 | 2 | -1.3447 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 2 | 2 | -0.8661 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 2 | 2 | -1.8728 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 2 | 2 | -2.0922 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 2 | 2 | -1.705 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 2 | 2 | -0.0196 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 1 | 1 | -0.1275 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=MISSED_UPSIDE|profit=profit_neg070_neg010` | 1 | 1 | 0.9211 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg070_neg010` | 1 | 1 | -0.1205 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | 0.3171 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 1 | 1 | -0.7361 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 862 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_context_noop` | 862 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 862 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_context_warning_not_applicable` | 862 | 0 | None | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=scalp_sim_panic_context_warning_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 862 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 258, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `price_guard_reason` | `price_guard_none` | 2830 | 2813 | None | -0.7348 | 0.1515 | `hold_sample` |
| `qty_reason` | `qty_none` | 2814 | 2813 | None | -0.7348 | 0.1515 | `hold_sample` |
| `time_bucket` | `time_unknown` | 2831 | 2813 | None | -0.7348 | 0.1515 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 2812 | 2811 | None | -0.735 | 0.1515 | `hold_sample` |
| `arm` | `AVG_DOWN` | 2396 | 2379 | None | -0.9541 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 2370 | 2353 | None | -0.9293 | 0.0 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 1625 | 1607 | None | -0.5737 | 0.2652 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 1494 | 1494 | None | -0.6482 | 0.1968 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 1306 | 1306 | None | -0.7697 | 0.2129 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 1273 | 1273 | None | -1.4755 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 1226 | 1208 | None | -0.9485 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 998 | 998 | None | -0.3851 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 808 | 808 | None | -0.402 | 0.4047 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 794 | 794 | None | -0.7089 | 0.1008 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 698 | 698 | None | -1.0073 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 592 | 592 | None | -0.8209 | 0.147 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_1` | 531 | 531 | None | -1.1117 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 454 | 454 | None | 0.2164 | 0.7467 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 447 | 447 | None | -0.675 | 0.1118 | `hold_sample` |
| `arm` | `PYRAMID` | 435 | 434 | None | 0.4695 | 0.9839 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 6 | 3 | -0.9475 | -1.2633 | 0.0 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 3 | 3 | -0.9475 | -1.2633 | 0.0 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 6 | 3 | -0.9475 | -1.2633 | 0.0 | `hold_sample` |
| `stage` | `exit` | 3 | 3 | -0.9475 | -1.2633 | 0.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 6 | 3 | -0.9475 | -1.2633 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 6 | 3 | -0.9475 | -1.2633 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 6 | 3 | -0.9475 | -1.2633 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 3 | 3 | -0.9475 | -1.2633 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 2 | 2 | -1.3575 | -1.81 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 4 | 2 | -1.3575 | -1.81 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 1 | 1 | -0.1275 | -0.17 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 2 | 1 | -0.7725 | -1.03 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 2 | 1 | -0.1275 | -0.17 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2 | 1 | -1.9425 | -2.59 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 2 | 1 | -0.1275 | -0.17 | 0.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 3 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_lt_neg070` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 1 | 0 | None | None | None | `hold_sample` |
| `stage` | `holding` | 3 | 0 | None | None | None | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_decision` | 3 | 0 | None | None | None | `hold_sample` |

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
