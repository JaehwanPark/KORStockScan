# Lifecycle Decision Matrix - 2026-05-24

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-05-24`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `45`
- source_rows_total: `45`
- retained_rows: `45`
- dropped_rows_by_source: `{}`
- joined_rows: `15`
- policy_pass_count: `1`
- promote_ready_count: `0`
- entry_bucket_actionable_count: `0`
- entry_bucket_runtime_candidate_count: `0`
- holding_bucket_count/workorders: `5` / `4`
- exit_bucket_count/workorders: `5` / `4`
- scale_in_bucket_actionable_count: `16`
- scale_in_bucket_runtime_candidate_count: `8`
- overnight_bucket_actionable_count: `0`
- overnight_bucket_runtime_candidate_count: `0`
- lifecycle_flow_bucket_count: `4`
- lifecycle_flow_complete_count: `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0`
- incomplete_flow_reason_counts: `{'missing_entry': 16, 'missing_exit': 11, 'missing_submit': 11, 'missing_holding': 11}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 0, 'route_counts': {'hold_sample': 5}, 'quality_counts': {'hold_sample': 5}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 0 | 0 | None | 0.0 | `hold_sample` | `NO_CHANGE` | False |
| `submit` | 5 | 0 | None | 0.0 | `hold_sample` | `NO_CHANGE` | False |
| `holding` | 5 | 0 | None | 0.0 | `hold_sample` | `NO_CHANGE` | False |
| `scale_in` | 30 | 15 | -55.622 | 0.75 | `pass` | `NO_CHANGE` | False |
| `exit` | 5 | 0 | None | 0.0 | `hold_sample` | `NO_CHANGE` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 16, 'complete_flow_count': 0, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 45, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0, 'stage_identity': {'entry': {'source_row_count': 0, 'identity_missing_count': 0, 'identity_quality_counts': {}, 'identity_join_rate': 0.0}, 'submit': {'source_row_count': 5, 'identity_missing_count': 0, 'identity_quality_counts': {'exact_sim_record_id': 5}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 5, 'identity_missing_count': 0, 'identity_quality_counts': {'exact_sim_record_id': 5}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 30, 'identity_missing_count': 0, 'identity_quality_counts': {'candidate_id': 30}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 5, 'identity_missing_count': 0, 'identity_quality_counts': {'candidate_id': 5}, 'identity_join_rate': 1.0}}, 'incomplete_flow_reason_counts': {'missing_entry': 16, 'missing_exit': 11, 'missing_submit': 11, 'missing_holding': 11}, 'bucket_count': 4, 'runtime_candidate_count': 0, 'workorder_count': 16}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 1 | 1 | -55.622 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:bbed60de0b` | 5 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 5 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:116ea07d4d` | 5 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |

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
- summary: `{'submit_rows': 5, 'bucket_count': 15, 'contract_gap_count': 2, 'workorder_count': 2, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 5 | 0 | None | `keep_collecting` |
| `broker_order_forbidden` | `true` | 5 | 0 | None | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_unknown|latency=latency_unknown|fill=true|submitted=false` | 5 | 0 | None | `source_quality_workorder` |
| `latency_reason` | `latency_reason_unknown` | 5 | 0 | None | `source_quality_workorder` |
| `latency_state` | `latency_unknown` | 5 | 0 | None | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_unknown` | 5 | 0 | None | `source_quality_workorder` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 5 | 0 | None | `source_quality_workorder` |
| `overbought_bucket` | `overbought_unknown` | 5 | 0 | None | `source_quality_workorder` |
| `overbought_guard_action` | `overbought_guard_unknown` | 5 | 0 | None | `source_quality_workorder` |
| `price_below_bid_bucket` | `price_below_bid_unknown` | 5 | 0 | None | `source_quality_workorder` |
| `price_resolution_bucket` | `price_resolution_unknown` | 5 | 0 | None | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 5 | 0 | None | `source_quality_workorder` |
| `revalidation_state` | `ok_or_unflagged` | 5 | 0 | None | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 5 | 0 | None | `keep_collecting` |
| `would_limit_fill` | `true` | 5 | 0 | None | `keep_collecting` |

### Submit Bucket Workorders

- `order_entry_post_submit_contract_gap_review`: `post_submit_contract_gap` / `price_revalidation_or_submit_state_missing` -> `price_revalidation_or_submit_state_missing`
- `order_entry_sim_submit_path_bucket_instrumentation`: `sim_pre_submit_guard_contract_gap` / `sim_pre_submit_guard_bucket_fields_missing` -> `sim_pre_submit_guard_bucket_fields_missing`

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 5, 'source_row_count': 5, 'bucket_count': 5, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': None, 'source_quality_gate': 'hold_sample', 'unknown_reason_counts': {'join_gap': 6}, 'workorder_count': 4, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_unknown|held=held_unknown` | 5 | 0 | None | `source_quality_workorder` |
| `held_bucket` | `held_unknown` | 5 | 0 | None | `source_quality_workorder` |
| `holding_action` | `holding_action_unknown` | 5 | 0 | None | `source_quality_workorder` |
| `holding_source_stage` | `scalp_sim_holding_started` | 5 | 0 | None | `hold_sample` |
| `profit_band` | `profit_unknown` | 5 | 0 | None | `source_quality_workorder` |

### Holding Bucket Attribution Workorders

- `holding_bucket_source_quality_1`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_unknown|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_2`: `held_bucket` / `held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_3`: `holding_action` / `holding_action_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_4`: `profit_band` / `profit_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Exit Bucket Attribution

- decision_authority: `adm_ldm_exit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'exit_rows': 5, 'source_row_count': 5, 'bucket_count': 5, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': None, 'source_quality_gate': 'hold_sample', 'unknown_reason_counts': {'join_gap': 6}, 'workorder_count': 4, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown` | 5 | 0 | None | `source_quality_workorder` |
| `exit_outcome` | `outcome_unknown` | 5 | 0 | None | `source_quality_workorder` |
| `exit_rule` | `exit_rule_unknown` | 5 | 0 | None | `source_quality_workorder` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 5 | 0 | None | `hold_sample` |
| `profit_band` | `profit_unknown` | 5 | 0 | None | `source_quality_workorder` |

### Exit Bucket Attribution Workorders

- `exit_bucket_source_quality_1`: `combo_exit_result` / `source=scalp_sim_panic_context_warning|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_2`: `exit_outcome` / `outcome_unknown` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_3`: `exit_rule` / `exit_rule_unknown` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_4`: `profit_band` / `profit_unknown` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'scale_in_rows': 30, 'bucket_count': 26, 'actionable_bucket_count': 16, 'runtime_candidate_count': 8, 'workorder_count': 10, 'arm_counts': {'AVG_DOWN': 15, 'PYRAMID': 15}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 15 | 15 | -55.622 | -69.47 | 0.0 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_unknown` | 15 | 0 | None | None | None | `hold_sample` |
| `ai_score_source` | `ai_source_unknown` | 30 | 15 | -55.622 | -69.47 | 0.0 | `candidate_tighten_or_exclude` |
| `arm` | `AVG_DOWN` | 15 | 10 | -43.77 | -54.655 | 0.0 | `candidate_tighten_or_exclude` |
| `arm` | `PYRAMID` | 15 | 5 | -79.326 | -99.1 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_namespace` | `AVG_DOWN` | 15 | 10 | -43.77 | -54.655 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_namespace` | `PYRAMID` | 15 | 5 | -79.326 | -99.1 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `buy_side_paused` | 5 | 5 | -8.214 | -10.21 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `forced` | 5 | 5 | -79.326 | -99.1 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `ok` | 5 | 5 | -79.326 | -99.1 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `invalid_quote` | 5 | 0 | None | None | None | `hold_sample` |
| `blocker_reason` | `pyramid_evidence_insufficient:buy_pressure_ok,tick_accel_ok` | 5 | 0 | None | None | None | `hold_sample` |
| `blocker_reason` | `spread_bps>80.0` | 5 | 0 | None | None | None | `hold_sample` |
| `held_bucket` | `held_lt020s` | 15 | 15 | -55.622 | -69.47 | 0.0 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_unknown` | 15 | 0 | None | None | None | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 15 | 15 | -55.622 | -69.47 | 0.0 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_unknown` | 15 | 0 | None | None | None | `hold_sample` |
| `price_guard_reason` | `price_guard_none` | 20 | 15 | -55.622 | -69.47 | 0.0 | `candidate_tighten_or_exclude` |
| `price_guard_reason` | `invalid_quote` | 5 | 0 | None | None | None | `hold_sample` |
| `price_guard_reason` | `spread_bps>80.0` | 5 | 0 | None | None | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 15 | 15 | -55.622 | -69.47 | 0.0 | `candidate_tighten_or_exclude` |
| `qty_reason` | `qty_none` | 25 | 15 | -55.622 | -69.47 | 0.0 | `candidate_tighten_or_exclude` |
| `supply_pass_bucket` | `supply_pass_unknown` | 30 | 15 | -55.622 | -69.47 | 0.0 | `candidate_tighten_or_exclude` |
| `time_bucket` | `time_unknown` | 30 | 15 | -55.622 | -69.47 | 0.0 | `candidate_tighten_or_exclude` |

### Scale-In Bucket Runtime Approval Candidates

- `scale_in_bucket_1`: `ai_score_band` / `score_lt60` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_3`: `arm` / `AVG_DOWN` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_5`: `blocker_namespace` / `AVG_DOWN` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_10`: `held_bucket` / `held_lt020s` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_11`: `peak_profit_band` / `peak_lt_zero` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_12`: `price_guard_reason` / `price_guard_none` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_13`: `profit_band` / `profit_lt_neg070` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_14`: `qty_reason` / `qty_none` -> `candidate_tighten_or_exclude`

### Scale-In Bucket Workorders

- `scale_in_bucket_source_quality_1`: `ai_score_band` / `score_lt60` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_2`: `ai_score_source` / `ai_source_unknown` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_3`: `arm` / `AVG_DOWN` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_4`: `arm` / `PYRAMID` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_5`: `blocker_namespace` / `AVG_DOWN` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_6`: `blocker_namespace` / `PYRAMID` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_7`: `blocker_reason` / `buy_side_paused` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_8`: `blocker_reason` / `forced` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_9`: `blocker_reason` / `ok` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_10`: `held_bucket` / `held_lt020s` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`

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
