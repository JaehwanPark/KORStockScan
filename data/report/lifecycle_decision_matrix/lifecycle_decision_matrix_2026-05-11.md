# Lifecycle Decision Matrix - 2026-05-11

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-05-11`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `1133`
- source_rows_total: `1133`
- retained_rows: `1133`
- dropped_rows_by_source: `{}`
- joined_rows: `1031`
- policy_pass_count: `1`
- promote_ready_count: `0`
- entry_bucket_actionable_count: `0`
- entry_bucket_runtime_candidate_count: `0`
- holding_bucket_count/workorders: `13` / `10`
- exit_bucket_count/workorders: `0` / `0`
- scale_in_bucket_actionable_count: `40`
- scale_in_bucket_runtime_candidate_count: `10`
- overnight_bucket_actionable_count: `0`
- overnight_bucket_runtime_candidate_count: `0`
- lifecycle_flow_bucket_count: `4`
- lifecycle_flow_complete_count: `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0`
- incomplete_flow_reason_counts: `{'missing_entry': 1058, 'missing_exit': 1058, 'missing_holding': 1033, 'missing_submit': 1025}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 0, 'route_counts': {'hold_sample': 5}, 'quality_counts': {'hold_sample': 5}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 0 | 0 | None | 0.0 | `hold_sample` | `NO_CHANGE` | False |
| `submit` | 33 | 9 | 0.3133 | 0.2455 | `hold_sample` | `ALLOW_SUBMIT` | False |
| `holding` | 25 | 9 | 0.3133 | 0.324 | `hold_sample` | `HOLD` | False |
| `scale_in` | 1075 | 1013 | -0.0985 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 0 | 0 | None | 0.0 | `hold_sample` | `NO_CHANGE` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 1058, 'complete_flow_count': 0, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 1133, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0, 'stage_identity': {'entry': {'source_row_count': 0, 'identity_missing_count': 0, 'identity_quality_counts': {}, 'identity_join_rate': 0.0}, 'submit': {'source_row_count': 33, 'identity_missing_count': 0, 'identity_quality_counts': {'exact_sim_record_id': 33}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 25, 'identity_missing_count': 0, 'identity_quality_counts': {'exact_sim_record_id': 25}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 1075, 'identity_missing_count': 0, 'identity_quality_counts': {'exact_sim_record_id': 7, 'candidate_id': 1068}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 0, 'identity_missing_count': 0, 'identity_quality_counts': {}, 'identity_join_rate': 0.0}}, 'incomplete_flow_reason_counts': {'missing_entry': 1058, 'missing_exit': 1058, 'missing_holding': 1033, 'missing_submit': 1025}, 'bucket_count': 4, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 946 | 937 | 0.5156 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 79 | 44 | 15.5431 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:bbed60de0b` | 25 | 9 | 0.3133 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:fbae46ee02` | 8 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 0, 'bucket_count': 0, 'actionable_bucket_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `adm_ldm_submit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'submit_rows': 33, 'bucket_count': 21, 'contract_gap_count': 2, 'workorder_count': 2, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 33 | 9 | 0.3133 | `keep_collecting` |
| `broker_order_forbidden` | `broker_order_forbidden_unknown` | 33 | 9 | 0.3133 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_unknown|latency=latency_unknown|fill=true|submitted=false` | 14 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_unknown|latency=latency_unknown|fill=would_limit_fill_unknown|submitted=false` | 8 | 8 | 0.675 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_virtual_pending|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_unknown|latency=latency_unknown|fill=would_limit_fill_unknown|submitted=false` | 8 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_unknown|latency=latency_unknown|fill=false|submitted=false` | 3 | 1 | -2.58 | `source_quality_workorder` |
| `latency_reason` | `latency_reason_unknown` | 33 | 9 | 0.3133 | `source_quality_workorder` |
| `latency_state` | `latency_unknown` | 33 | 9 | 0.3133 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_unknown` | 33 | 9 | 0.3133 | `source_quality_workorder` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 33 | 9 | 0.3133 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_unknown` | 33 | 9 | 0.3133 | `source_quality_workorder` |
| `overbought_guard_action` | `overbought_guard_unknown` | 33 | 9 | 0.3133 | `source_quality_workorder` |
| `price_below_bid_bucket` | `price_below_bid_unknown` | 33 | 9 | 0.3133 | `source_quality_workorder` |
| `price_resolution_bucket` | `price_resolution_unknown` | 33 | 9 | 0.3133 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 33 | 9 | 0.3133 | `source_quality_workorder` |
| `revalidation_state` | `ok_or_unflagged` | 33 | 9 | 0.3133 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 25 | 9 | 0.3133 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_buy_order_virtual_pending` | 8 | 0 | None | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 16 | 8 | 0.675 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 14 | 0 | None | `keep_collecting` |
| `would_limit_fill` | `false` | 3 | 1 | -2.58 | `keep_collecting` |

### Submit Bucket Workorders

- `order_entry_post_submit_contract_gap_review`: `post_submit_contract_gap` / `price_revalidation_or_submit_state_missing` -> `price_revalidation_or_submit_state_missing`
- `order_entry_sim_submit_path_bucket_instrumentation`: `sim_pre_submit_guard_contract_gap` / `sim_pre_submit_guard_bucket_fields_missing` -> `sim_pre_submit_guard_bucket_fields_missing`

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 25, 'source_row_count': 25, 'bucket_count': 13, 'joined_sample': 45, 'source_quality_adjusted_ev_pct': 0.3133, 'source_quality_gate': 'pass', 'unknown_reason_counts': {'not_applicable': 8, 'join_gap': 4, 'missing_source_field': 2}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_neg010_pos080|held=held_unknown` | 3 | 3 | 0.39 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_lt_neg070|held=held_unknown` | 2 | 2 | -2.295 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_pos080_pos150|held=held_unknown` | 2 | 2 | 1.1 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_pos150_pos300|held=held_unknown` | 2 | 2 | 2.02 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_unknown|held=held_unknown` | 16 | 0 | None | `source_quality_workorder` |
| `held_bucket` | `held_unknown` | 25 | 9 | 0.3133 | `source_quality_workorder` |
| `holding_action` | `holding_action_unknown` | 25 | 9 | 0.3133 | `source_quality_workorder` |
| `holding_source_stage` | `scalp_sim_holding_started` | 25 | 9 | 0.3133 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg010_pos080` | 3 | 3 | 0.39 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_lt_neg070` | 2 | 2 | -2.295 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 2 | 2 | 1.1 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 2 | 2 | 2.02 | `hold_sample` |
| `profit_band` | `profit_unknown` | 16 | 0 | None | `source_quality_workorder` |

### Holding Bucket Attribution Workorders

- `holding_bucket_source_quality_1`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_neg010_pos080|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_2`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_lt_neg070|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_3`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_pos080_pos150|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_4`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_pos150_pos300|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_5`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_unknown|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_6`: `held_bucket` / `held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_7`: `holding_action` / `holding_action_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_8`: `holding_source_stage` / `scalp_sim_holding_started` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_9`: `profit_band` / `profit_neg010_pos080` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_10`: `profit_band` / `profit_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Exit Bucket Attribution

- decision_authority: `adm_ldm_exit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'exit_rows': 0, 'source_row_count': 0, 'bucket_count': 0, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': None, 'source_quality_gate': 'hold_sample', 'unknown_reason_counts': {}, 'workorder_count': 0, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'scale_in_rows': 1075, 'bucket_count': 311, 'actionable_bucket_count': 40, 'runtime_candidate_count': 10, 'workorder_count': 10, 'arm_counts': {'PYRAMID': 111, 'AVG_DOWN': 964}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_70p` | 766 | 766 | 0.9313 | 1.1607 | 0.1567 | `candidate_recovery_or_relax` |
| `ai_score_band` | `score_66_69` | 105 | 105 | 3.8281 | 4.6518 | 0.4762 | `candidate_recovery_or_relax` |
| `ai_score_band` | `score_lt60` | 75 | 75 | -20.1809 | -25.2243 | 0.1733 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_63_65` | 34 | 34 | 1.8452 | 2.2191 | 0.4118 | `candidate_recovery_or_relax` |
| `ai_score_band` | `score_60_62` | 26 | 26 | 1.0172 | 1.2158 | 0.2692 | `candidate_recovery_or_relax` |
| `ai_score_band` | `score_unknown` | 69 | 7 | 29.896 | 36.62 | 1.0 | `candidate_recovery_or_relax` |
| `ai_score_source` | `ai_source_unknown` | 1075 | 1013 | -0.0985 | -0.1489 | 0.2083 | `hold_no_edge` |
| `arm` | `AVG_DOWN` | 964 | 955 | -0.3191 | -0.3933 | 0.1696 | `candidate_tighten_or_exclude` |
| `arm` | `PYRAMID` | 111 | 58 | 3.5338 | 3.8757 | 0.8448 | `candidate_recovery_or_relax` |
| `blocker_namespace` | `AVG_DOWN` | 777 | 777 | -0.312 | -0.4032 | 0.2085 | `candidate_tighten_or_exclude` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 178 | 178 | -0.3503 | -0.3503 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_namespace` | `PYRAMID` | 51 | 51 | -0.0845 | -0.6186 | 0.8235 | `hold_no_edge` |
| `blocker_namespace` | `blocker_namespace_unknown` | 7 | 7 | 29.896 | 36.62 | 1.0 | `candidate_recovery_or_relax` |
| `blocker_namespace` | `PRICE_GUARD` | 31 | 0 | None | None | None | `hold_sample` |
| `blocker_namespace` | `QTY_GUARD` | 31 | 0 | None | None | None | `hold_sample` |
| `blocker_reason` | `add_judgment_locked` | 272 | 272 | -0.3182 | -0.3182 | 0.0441 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `scale_in_gate_blocked` | 207 | 207 | -0.2622 | -0.3211 | 0.0435 | `hold_no_edge` |
| `blocker_reason` | `scale_in_probe_blocked` | 135 | 135 | 0.5122 | 0.5268 | 0.4 | `candidate_recovery_or_relax` |
| `blocker_reason` | `scalping_pyramid_ok` | 42 | 42 | 16.8958 | 20.4845 | 1.0 | `candidate_recovery_or_relax` |
| `blocker_reason` | `🛑 하드스탑 도달 (-2.5%) [AI: 50]` | 25 | 25 | -53.7257 | -67.0996 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(37.21)` | 13 | 13 | 30.368 | 37.21 | 1.0 | `candidate_recovery_or_relax` |
| `blocker_reason` | `pnl_out_of_range(-0.03)` | 11 | 11 | -0.03 | -0.03 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `ai_not_recovering` | 8 | 8 | -0.32 | -0.32 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `blocker_reason_unknown` | 7 | 7 | 29.896 | 36.62 | 1.0 | `candidate_recovery_or_relax` |
| `blocker_reason` | `pnl_out_of_range(36.82)` | 7 | 7 | 30.056 | 36.82 | 1.0 | `candidate_recovery_or_relax` |
| `blocker_reason` | `pnl_out_of_range(-0.08)` | 6 | 6 | -0.08 | -0.08 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.81)` | 6 | 6 | -0.81 | -0.81 | 0.0 | `candidate_tighten_or_exclude` |

### Scale-In Bucket Runtime Approval Candidates

- `scale_in_bucket_1`: `ai_score_band` / `score_70p` -> `candidate_recovery_or_relax`
- `scale_in_bucket_2`: `ai_score_band` / `score_66_69` -> `candidate_recovery_or_relax`
- `scale_in_bucket_3`: `ai_score_band` / `score_lt60` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_4`: `ai_score_band` / `score_63_65` -> `candidate_recovery_or_relax`
- `scale_in_bucket_5`: `ai_score_band` / `score_60_62` -> `candidate_recovery_or_relax`
- `scale_in_bucket_7`: `arm` / `AVG_DOWN` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_8`: `arm` / `PYRAMID` -> `candidate_recovery_or_relax`
- `scale_in_bucket_9`: `blocker_namespace` / `AVG_DOWN` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_10`: `blocker_namespace` / `AVG_DOWN_ONLY` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_12`: `blocker_reason` / `add_judgment_locked` -> `candidate_tighten_or_exclude`

### Scale-In Bucket Workorders

- `scale_in_bucket_source_quality_1`: `ai_score_band` / `score_70p` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_2`: `ai_score_band` / `score_66_69` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_3`: `ai_score_band` / `score_lt60` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_4`: `ai_score_band` / `score_63_65` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_5`: `ai_score_band` / `score_60_62` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_6`: `ai_score_band` / `score_unknown` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_7`: `arm` / `AVG_DOWN` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_8`: `arm` / `PYRAMID` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_9`: `blocker_namespace` / `AVG_DOWN` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_10`: `blocker_namespace` / `AVG_DOWN_ONLY` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`

## Overnight Bucket Attribution

- decision_authority: `adm_ldm_overnight_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'overnight_rows': 0, 'bucket_count': 0, 'actionable_bucket_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'status_counts': {}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |

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
