# Lifecycle Decision Matrix - 2026-05-19

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-05-19`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `13886`
- source_rows_total: `13886`
- retained_rows: `13886`
- dropped_rows_by_source: `{}`
- joined_rows: `13393`
- policy_pass_count: `4`
- promote_ready_count: `0`
- entry_bucket_actionable_count: `0`
- entry_bucket_runtime_candidate_count: `0`
- holding_bucket_count/workorders: `28` / `10`
- exit_bucket_count/workorders: `41` / `10`
- scale_in_bucket_actionable_count: `162`
- scale_in_bucket_runtime_candidate_count: `10`
- overnight_bucket_actionable_count: `3`
- overnight_bucket_runtime_candidate_count: `0`
- lifecycle_flow_bucket_count: `35`
- lifecycle_flow_complete_count: `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0`
- incomplete_flow_reason_counts: `{'missing_submit': 13552, 'missing_holding': 13552, 'missing_exit': 13552, 'missing_entry': 13602}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 0, 'route_counts': {'hold_sample': 5}, 'quality_counts': {'hold_sample': 5}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 50 | 0 | None | 0.0 | `hold_sample` | `NO_CHANGE` | False |
| `submit` | 100 | 100 | -0.6895 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 113 | 100 | -0.4847 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 13510 | 13080 | -0.1662 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 113 | 113 | -0.4446 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 13652, 'complete_flow_count': 0, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 13886, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0, 'stage_identity': {'entry': {'source_row_count': 50, 'identity_missing_count': 0, 'identity_quality_counts': {'candidate_id': 50}, 'identity_join_rate': 1.0}, 'submit': {'source_row_count': 100, 'identity_missing_count': 0, 'identity_quality_counts': {'exact_sim_record_id': 100}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 113, 'identity_missing_count': 0, 'identity_quality_counts': {'exact_sim_record_id': 113}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 13510, 'identity_missing_count': 0, 'identity_quality_counts': {'exact_sim_record_id': 8, 'candidate_id': 13502}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 113, 'identity_missing_count': 0, 'identity_quality_counts': {'exact_sim_record_id': 113}, 'identity_join_rate': 1.0}}, 'incomplete_flow_reason_counts': {'missing_submit': 13552, 'missing_holding': 13552, 'missing_exit': 13552, 'missing_entry': 13602}, 'bucket_count': 35, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 12934 | 12784 | -0.2239 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 568 | 288 | 2.35 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:3e8349fb28` | 13 | 13 | -0.8559 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:926cbbe021` | 13 | 13 | 0.6593 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:be58d571f4` | 12 | 12 | -0.1913 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:c260e8fed9` | 9 | 9 | 0.0691 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:033a0b4f01` | 8 | 8 | -0.9984 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:6e9c6552da` | 7 | 7 | 0.0446 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:cdf5e9e566` | 5 | 5 | -0.1034 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:1f8c274bdd` | 4 | 4 | -2.1431 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:e29be7371d` | 4 | 4 | -1.6743 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:3bd95ff845` | 3 | 3 | 0.1597 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:db291b2ff1` | 3 | 3 | -2.2191 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b62d8cb522` | 2 | 2 | 0.4882 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:f453f7b6dd` | 2 | 2 | -1.1136 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:9c678203e4` | 2 | 2 | 0.1871 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:cce5439e04` | 1 | 1 | -2.7213 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:74988cec73` | 1 | 1 | -2.6564 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:4bd5cc7a3c` | 1 | 1 | 0.565 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:3417ce4d3a` | 1 | 1 | -0.6592 | `hold_sample` | `hold_sample_or_incomplete_flow` |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 50, 'bucket_count': 26, 'actionable_bucket_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `NO_BUY_AI` | 50 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=blocked_ai_score|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_normal|time=time_0900_1000` | 6 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=blocked_ai_score|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_watch|time=time_0900_1000` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_0900_1000` | 10 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=blocked_ai_score|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_normal|time=time_0900_1000` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_0900_1000` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=blocked_ai_score|stale=stale_unknown|liquidity=liquidity_unknown|overbought=overbought_normal|time=time_0900_1000` | 19 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=blocked_ai_score|stale=stale_unknown|liquidity=liquidity_unknown|overbought=overbought_watch|time=time_0900_1000` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_unknown|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_0900_1000` | 9 | 0 | None | None | None | `hold_sample` |
| `exit_rule` | `exit_unknown` | 50 | 0 | None | None | None | `hold_sample` |
| `liquidity_bucket` | `liquidity_unknown` | 50 | 0 | None | None | None | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 27 | 0 | None | None | None | `hold_sample` |
| `overbought_bucket` | `overbought_unknown` | 21 | 0 | None | None | None | `hold_sample` |
| `overbought_bucket` | `overbought_watch` | 2 | 0 | None | None | None | `hold_sample` |
| `score_band` | `score_60_62` | 17 | 0 | None | None | None | `hold_sample` |
| `score_band` | `score_63_65` | 4 | 0 | None | None | None | `hold_sample` |
| `score_band` | `score_lt60` | 29 | 0 | None | None | None | `hold_sample` |
| `source_stage` | `blocked_ai_score` | 29 | 0 | None | None | None | `hold_sample` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 21 | 0 | None | None | None | `hold_sample` |
| `stale_bucket` | `fresh` | 21 | 0 | None | None | None | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `adm_ldm_submit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'submit_rows': 100, 'bucket_count': 30, 'contract_gap_count': 1, 'workorder_count': 1, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 100 | 100 | -0.6895 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 95 | 95 | -0.6492 | `keep_collecting` |
| `broker_order_forbidden` | `broker_order_forbidden_unknown` | 5 | 5 | -1.4548 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_unknown|latency=latency_unknown|fill=would_limit_fill_unknown|submitted=false` | 70 | 70 | -0.5693 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_unknown|latency=latency_unknown|fill=would_limit_fill_unknown|submitted=false` | 21 | 21 | -1.0141 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_unknown|latency=latency_unknown|fill=false|submitted=false` | 8 | 8 | -0.9042 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_unknown|latency=latency_unknown|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | -0.5693 | `source_quality_workorder` |
| `latency_reason` | `latency_reason_unknown` | 100 | 100 | -0.6895 | `source_quality_workorder` |
| `latency_state` | `latency_unknown` | 100 | 100 | -0.6895 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_unknown` | 100 | 100 | -0.6895 | `source_quality_workorder` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 100 | 100 | -0.6895 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_unknown` | 100 | 100 | -0.6895 | `source_quality_workorder` |
| `overbought_guard_action` | `overbought_guard_unknown` | 100 | 100 | -0.6895 | `source_quality_workorder` |
| `price_below_bid_bucket` | `not_below_bid` | 86 | 86 | -0.6544 | `keep_collecting` |
| `price_below_bid_bucket` | `price_below_bid_unknown` | 8 | 8 | -0.9042 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 5 | 5 | -0.4204 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 1 | 1 | -3.3384 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 85 | 85 | -0.6783 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 8 | 8 | -0.9042 | `source_quality_workorder` |
| `price_resolution_bucket` | `defensive_order_price` | 7 | 7 | -0.5799 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 70 | 70 | -0.5693 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 21 | 21 | -1.0141 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_unknown` | 8 | 8 | -0.9042 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_10s_plus` | 1 | 1 | -0.5693 | `keep_collecting` |
| `revalidation_state` | `warning_stale_context_or_quote` | 92 | 92 | -0.6708 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 8 | 8 | -0.9042 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 92 | 92 | -0.6708 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 8 | 8 | -0.9042 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 92 | 92 | -0.6708 | `source_quality_workorder` |
| `would_limit_fill` | `false` | 8 | 8 | -0.9042 | `keep_collecting` |

### Submit Bucket Workorders

- `order_entry_sim_submit_path_bucket_instrumentation`: `sim_pre_submit_guard_contract_gap` / `sim_pre_submit_guard_bucket_fields_missing` -> `sim_pre_submit_guard_bucket_fields_missing`

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 113, 'source_row_count': 113, 'bucket_count': 28, 'joined_sample': 500, 'source_quality_adjusted_ev_pct': -0.4847, 'source_quality_gate': 'pass', 'unknown_reason_counts': {'not_applicable': 15, 'join_gap': 4, 'missing_source_field': 2}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_unknown` | 39 | 39 | -1.2401 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_unknown` | 20 | 20 | 0.2239 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_unknown` | 16 | 16 | 0.2484 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_unknown` | 7 | 7 | 0.4725 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_lt_neg070|held=held_unknown` | 7 | 7 | -1.8646 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_unknown` | 5 | 5 | 0.6653 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_unknown` | 2 | 2 | -0.47 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300|held=held_unknown` | 1 | 1 | -2.1536 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_neg070_neg010|held=held_unknown` | 1 | 1 | -0.47 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_pos150_pos300_plus|held=held_unknown` | 1 | 1 | 0.565 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_pos150_pos300|held=held_unknown` | 1 | 1 | 0.8536 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=holding_action_unknown|profit=profit_lt_neg070|held=held_600_1800s_plus` | 4 | 0 | None | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=holding_action_unknown|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 5 | 0 | None | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=holding_action_unknown|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 3 | 0 | None | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=holding_action_unknown|profit=profit_pos080_pos150|held=held_600_1800s_plus` | 1 | 0 | None | `source_quality_workorder` |
| `held_bucket` | `held_unknown` | 100 | 100 | -0.4847 | `source_quality_workorder` |
| `held_bucket` | `held_600_1800s_plus` | 13 | 0 | None | `hold_sample` |
| `holding_action` | `WAIT` | 89 | 89 | -0.3845 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_unknown` | 23 | 10 | -1.2103 | `source_quality_workorder` |
| `holding_action` | `BUY` | 1 | 1 | -2.1536 | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 100 | 100 | -0.4847 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 13 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 50 | 46 | -1.3351 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 21 | 20 | 0.2239 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 21 | 16 | 0.2484 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 9 | 9 | 0.2231 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300_plus` | 6 | 6 | 0.6486 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 6 | 3 | -0.47 | `candidate_tighten_or_exclude` |

### Holding Bucket Attribution Workorders

- `holding_bucket_source_quality_1`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_2`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_3`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_4`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_5`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_lt_neg070|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_6`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_7`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_8`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_9`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_neg070_neg010|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_10`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_pos150_pos300_plus|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Exit Bucket Attribution

- decision_authority: `adm_ldm_exit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'exit_rows': 113, 'source_row_count': 113, 'bucket_count': 41, 'joined_sample': 565, 'source_quality_adjusted_ev_pct': -0.4446, 'source_quality_gate': 'pass', 'unknown_reason_counts': {'not_applicable': 8, 'missing_source_field': 1}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 15 | 15 | -0.8886 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 11 | 11 | -0.9995 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 8 | 8 | 0.5665 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 6 | 6 | -2.0437 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 6 | 6 | 0.6486 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 6 | 6 | -0.0445 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 5 | 5 | 0.2625 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_sell_order_assumed_filled|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 5 | 5 | 0.2625 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 5 | 5 | -0.1214 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 5 | 5 | 0.5604 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 5 | 5 | -0.1034 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 4 | 4 | -0.8794 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_sell_order_assumed_filled|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 4 | 4 | -0.8794 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 4 | 4 | -2.1431 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 4 | 4 | -1.9132 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 4 | 4 | -0.2898 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 3 | 3 | -0.3525 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_sell_order_assumed_filled|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 3 | 3 | -0.3525 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300` | 3 | 3 | 0.3179 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 2 | 2 | -1.9579 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 2 | 2 | 1.1065 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos080_pos150` | 1 | 1 | 0.615 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_sell_order_assumed_filled|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos080_pos150` | 1 | 1 | 0.615 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 1 | 1 | -0.0596 | `hold_sample` |
| `exit_outcome` | `MISSED_UPSIDE` | 34 | 34 | -0.3363 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 27 | 27 | -0.546 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 26 | 26 | -0.7219 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 26 | 26 | -0.2037 | `source_quality_workorder` |
| `exit_rule` | `scalp_trailing_take_profit` | 45 | 45 | 0.2618 | `hold_no_edge` |
| `exit_rule` | `scalp_soft_stop_pct` | 32 | 32 | -1.1433 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 26 | 26 | -0.2037 | `hold_no_edge` |
| `exit_rule` | `scalp_hard_stop_pct` | 10 | 10 | -2.0141 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 87 | 87 | -0.5166 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 13 | 13 | -0.2037 | `hold_no_edge` |
| `exit_source_stage` | `scalp_sim_sell_order_assumed_filled` | 13 | 13 | -0.2037 | `hold_no_edge` |
| `profit_band` | `profit_lt_neg070` | 50 | 50 | -1.2752 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 21 | 21 | 0.231 | `hold_no_edge` |
| `profit_band` | `profit_pos080_pos150` | 21 | 21 | 0.2328 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 9 | 9 | 0.2231 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 6 | 6 | -0.3525 | `candidate_tighten_or_exclude` |

### Exit Bucket Attribution Workorders

- `exit_bucket_source_quality_1`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_2`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_3`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_4`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_5`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_6`: `combo_exit_result` / `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_7`: `combo_exit_result` / `source=scalp_sim_sell_order_assumed_filled|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_8`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_9`: `combo_exit_result` / `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_10`: `combo_exit_result` / `source=scalp_sim_sell_order_assumed_filled|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'scale_in_rows': 13510, 'bucket_count': 1483, 'actionable_bucket_count': 162, 'runtime_candidate_count': 10, 'workorder_count': 10, 'arm_counts': {'PYRAMID': 576, 'AVG_DOWN': 12934}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_70p` | 4377 | 4377 | -0.1007 | -0.1618 | 0.3875 | `hold_no_edge` |
| `ai_score_band` | `score_lt60` | 3343 | 3343 | -0.1921 | -0.2381 | 0.2677 | `hold_no_edge` |
| `ai_score_band` | `score_66_69` | 2440 | 2440 | -0.2275 | -0.283 | 0.1824 | `hold_no_edge` |
| `ai_score_band` | `score_60_62` | 1572 | 1572 | -0.2156 | -0.262 | 0.2551 | `hold_no_edge` |
| `ai_score_band` | `score_63_65` | 1340 | 1340 | -0.1559 | -0.2059 | 0.2567 | `hold_no_edge` |
| `ai_score_band` | `score_unknown` | 438 | 8 | 1.5325 | 1.5088 | 1.0 | `candidate_recovery_or_relax` |
| `ai_score_source` | `ai_source_unknown` | 13510 | 13080 | -0.1662 | -0.2194 | 0.2897 | `hold_no_edge` |
| `arm` | `AVG_DOWN` | 12934 | 12784 | -0.2239 | -0.2792 | 0.2732 | `hold_no_edge` |
| `arm` | `PYRAMID` | 576 | 296 | 2.328 | 2.3606 | 1.0 | `candidate_recovery_or_relax` |
| `blocker_namespace` | `AVG_DOWN` | 11410 | 11410 | -0.2039 | -0.2658 | 0.3061 | `hold_no_edge` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 1374 | 1374 | -0.3904 | -0.3904 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_namespace` | `PYRAMID` | 288 | 288 | 2.35 | 2.3842 | 1.0 | `candidate_recovery_or_relax` |
| `blocker_namespace` | `blocker_namespace_unknown` | 8 | 8 | 1.5325 | 1.5088 | 1.0 | `candidate_recovery_or_relax` |
| `blocker_namespace` | `PRICE_GUARD` | 185 | 0 | None | None | None | `hold_sample` |
| `blocker_namespace` | `QTY_GUARD` | 245 | 0 | None | None | None | `hold_sample` |
| `blocker_reason` | `scale_in_probe_blocked` | 2610 | 2610 | -0.2077 | -0.3443 | 0.3375 | `hold_no_edge` |
| `blocker_reason` | `scale_in_gate_blocked` | 2508 | 2508 | -0.0787 | -0.2069 | 0.2588 | `hold_no_edge` |
| `blocker_reason` | `add_judgment_locked` | 2342 | 2342 | -0.3229 | -0.3229 | 0.105 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `near_market_close` | 780 | 780 | 0.0372 | 0.0372 | 0.5872 | `hold_no_edge` |
| `blocker_reason` | `scalping_cutoff` | 310 | 310 | -0.3115 | -0.3115 | 0.1419 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `scalping_pyramid_ok` | 274 | 274 | 2.3951 | 2.43 | 1.0 | `candidate_recovery_or_relax` |
| `blocker_reason` | `holding_exit_matrix_avg_down_bias` | 150 | 150 | -0.3939 | -0.4652 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `low_broken` | 80 | 80 | -0.3831 | -0.3831 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(0.05)` | 53 | 53 | 0.05 | 0.05 | 1.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(0.47)` | 41 | 41 | 0.47 | 0.47 | 1.0 | `candidate_recovery_or_relax` |
| `blocker_reason` | `pnl_out_of_range(0.34)` | 40 | 40 | 0.34 | 0.34 | 1.0 | `candidate_recovery_or_relax` |
| `blocker_reason` | `pnl_out_of_range(-1.21)` | 39 | 39 | -1.21 | -1.21 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.75)` | 37 | 37 | -0.75 | -0.75 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.88)` | 36 | 36 | -0.88 | -0.88 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.06)` | 35 | 35 | -0.06 | -0.06 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.05)` | 32 | 32 | -0.05 | -0.05 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(0.29)` | 32 | 32 | 0.29 | 0.29 | 1.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.80)` | 31 | 31 | -0.8 | -0.8 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.04)` | 29 | 29 | -0.04 | -0.04 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-1.27)` | 28 | 28 | -1.27 | -1.27 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.08)` | 27 | 27 | -0.08 | -0.08 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.09)` | 27 | 27 | -0.09 | -0.09 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(0.43)` | 27 | 27 | 0.43 | 0.43 | 1.0 | `candidate_recovery_or_relax` |
| `blocker_reason` | `pnl_out_of_range(-1.17)` | 26 | 26 | -1.17 | -1.17 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.38)` | 26 | 26 | -1.38 | -1.38 | 0.0 | `candidate_tighten_or_exclude` |

### Scale-In Bucket Runtime Approval Candidates

- `scale_in_bucket_2`: `arm` / `PYRAMID` -> `candidate_recovery_or_relax`
- `scale_in_bucket_3`: `blocker_namespace` / `AVG_DOWN_ONLY` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_4`: `blocker_namespace` / `PYRAMID` -> `candidate_recovery_or_relax`
- `scale_in_bucket_6`: `blocker_reason` / `add_judgment_locked` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_7`: `blocker_reason` / `scalping_cutoff` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_8`: `blocker_reason` / `scalping_pyramid_ok` -> `candidate_recovery_or_relax`
- `scale_in_bucket_9`: `blocker_reason` / `holding_exit_matrix_avg_down_bias` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_10`: `blocker_reason` / `low_broken` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_11`: `blocker_reason` / `pnl_out_of_range(0.47)` -> `candidate_recovery_or_relax`
- `scale_in_bucket_12`: `blocker_reason` / `pnl_out_of_range(0.34)` -> `candidate_recovery_or_relax`

### Scale-In Bucket Workorders

- `scale_in_bucket_source_quality_1`: `ai_score_band` / `score_unknown` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_2`: `arm` / `PYRAMID` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_3`: `blocker_namespace` / `AVG_DOWN_ONLY` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_4`: `blocker_namespace` / `PYRAMID` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_5`: `blocker_namespace` / `blocker_namespace_unknown` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_6`: `blocker_reason` / `add_judgment_locked` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_7`: `blocker_reason` / `scalping_cutoff` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_8`: `blocker_reason` / `scalping_pyramid_ok` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_9`: `blocker_reason` / `holding_exit_matrix_avg_down_bias` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_10`: `blocker_reason` / `low_broken` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`

## Overnight Bucket Attribution

- decision_authority: `adm_ldm_overnight_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'overnight_rows': 39, 'bucket_count': 35, 'actionable_bucket_count': 3, 'runtime_candidate_count': 0, 'workorder_count': 3, 'status_counts': {'HOLD_OVERNIGHT': 13, 'SELL_TODAY': 26}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_lt040|profit=profit_neg010_pos080` | 5 | 5 | 0.2625 | 0.35 | 0.8 | `hold_no_edge` |
| `combo_overnight_decision` | `action=action_unknown|status=SELL_TODAY|confidence=confidence_unknown|profit=profit_neg010_pos080` | 5 | 5 | 0.2625 | 0.35 | 0.8 | `hold_no_edge` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_lt040|profit=profit_lt_neg070` | 4 | 4 | -0.8794 | -1.1725 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=action_unknown|status=SELL_TODAY|confidence=confidence_unknown|profit=profit_lt_neg070` | 4 | 4 | -0.8794 | -1.1725 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_lt040|profit=profit_neg070_neg010` | 3 | 3 | -0.3525 | -0.47 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=action_unknown|status=SELL_TODAY|confidence=confidence_unknown|profit=profit_neg070_neg010` | 3 | 3 | -0.3525 | -0.47 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_lt040|profit=profit_pos080_pos150` | 1 | 1 | 0.615 | 0.82 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=action_unknown|status=SELL_TODAY|confidence=confidence_unknown|profit=profit_pos080_pos150` | 1 | 1 | 0.615 | 0.82 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_lt040|profit=profit_lt_neg070` | 4 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_lt040|profit=profit_neg010_pos080` | 5 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_lt040|profit=profit_neg070_neg010` | 3 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_lt040|profit=profit_pos080_pos150` | 1 | 0 | None | None | None | `hold_sample` |
| `confidence_band` | `confidence_lt040` | 26 | 13 | -0.2037 | -0.2715 | 0.3846 | `hold_no_edge` |
| `confidence_band` | `confidence_unknown` | 13 | 13 | -0.2037 | -0.2715 | 0.3846 | `hold_no_edge` |
| `held_bucket` | `held_600_1800s_plus` | 26 | 13 | -0.2037 | -0.2715 | 0.3846 | `hold_no_edge` |
| `held_bucket` | `held_unknown` | 13 | 13 | -0.2037 | -0.2715 | 0.3846 | `hold_no_edge` |
| `overnight_action` | `SELL_TODAY` | 26 | 13 | -0.2037 | -0.2715 | 0.3846 | `hold_no_edge` |
| `overnight_action` | `action_unknown` | 13 | 13 | -0.2037 | -0.2715 | 0.3846 | `hold_no_edge` |
| `overnight_status` | `SELL_TODAY` | 26 | 26 | -0.2037 | -0.2715 | 0.3846 | `hold_no_edge` |
| `overnight_status` | `HOLD_OVERNIGHT` | 13 | 0 | None | None | None | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 13 | 13 | -0.2037 | -0.2715 | 0.3846 | `hold_no_edge` |
| `peak_profit_band` | `peak_lt_zero` | 16 | 8 | -0.5747 | -0.7662 | 0.0 | `candidate_tighten_or_exclude` |
| `price_source` | `holding_price_samples_last` | 39 | 26 | -0.2037 | -0.2715 | 0.3846 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 15 | 10 | 0.2625 | 0.35 | 0.8 | `hold_no_edge` |
| `profit_band` | `profit_lt_neg070` | 12 | 8 | -0.8794 | -1.1725 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 9 | 6 | -0.3525 | -0.47 | 0.0 | `candidate_tighten_or_exclude` |
| `source_quality_gate` | `source_quality_unknown` | 39 | 26 | -0.2037 | -0.2715 | 0.3846 | `hold_no_edge` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 13 | 13 | -0.2037 | -0.2715 | 0.3846 | `hold_no_edge` |
| `source_stage` | `scalp_sim_sell_order_assumed_filled` | 13 | 13 | -0.2037 | -0.2715 | 0.3846 | `hold_no_edge` |
| `stage` | `exit` | 26 | 26 | -0.2037 | -0.2715 | 0.3846 | `hold_no_edge` |

### Overnight Bucket Runtime Approval Candidates

- none

### Overnight Bucket Workorders

- `overnight_bucket_source_quality_1`: `peak_profit_band` / `peak_lt_zero` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_2`: `profit_band` / `profit_lt_neg070` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_3`: `profit_band` / `profit_neg070_neg010` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`

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
