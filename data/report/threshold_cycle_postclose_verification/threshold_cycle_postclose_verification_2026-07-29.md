# Threshold Cycle Postclose Verification - 2026-07-29

- status: `warning`
- latest_start_marker: `[START] threshold-cycle postclose target_date=2026-07-29 max_iterations=80 started_at=2026-07-29T22:04:45+0900`
- latest_done_marker: `[DONE] threshold-cycle postclose target_date=2026-07-29 ai_correction_provider=openai panic_sell_defense=true panic_buying=false market_panic_breadth=true scalp_sim_ai_deferred_review=true pipeline_event_verbosity=true quote_consistency_report=true intraday_ws_freshness_monitor=true observation_source_quality_audit=true ai_watching_score_smoothing_diagnostic=true codebase_performance_workorder=true pattern_lab_currentness_audit=true pattern_lab_ai_review=true time_window_regime_counterfactual=true producer_gap_discovery=true stage_hook_workorder_discovery=true stage_hook_runtime_scaffold=true pattern_lab_propagation_audit=true scalp_sim_overnight=true scalp_entry_adm=true entry_split_order_plan=true scale_in_split_order_plan=true entry_ai_gate_backtest=true tight_stop_entry_companion_report=true ai_score_optimization_backtest=true rising_missed_intraday_feedback_postclose=true rising_missed_scout_workorder=true rising_missed_normal_buy_bridge_candidate_discovery=true rising_missed_first_touch_calibration=true scalping_pyramid_intraday_feedback_postclose=true scalping_pyramid_quality_calibration=true scalping_avg_down_recovery_calibration=true rising_missed_classifier_prior=true one_share_threshold_opportunity=true one_share_threshold_opportunity_ai_provider=openai institutional_flow_context=true microstructure_reaction_context=true lifecycle_decision_matrix=true lifecycle_ai_context=true ldm_hypothesis_parent_refinement=true lifecycle_bucket_discovery=true lifecycle_bucket_windows=true lifecycle_bucket_window_list=rolling5d,rolling10d,mtd lifecycle_bucket_promotion_window=mtd force_lifecycle_bucket_windows=false force_deep_audits=false force_workorder_branch=false runtime_apply_bridge=true scalp_sim_auto_approval_control_tower=true latency_classifier_recommendation=true tuning_performance_control_tower=true swing_lifecycle=false swing_strategy_discovery=false swing_lifecycle_matrix=false swing_lifecycle_bucket_discovery=false swing_ai_review_provider=openai swing_lifecycle_bucket_discovery_ai_provider=openai pattern_lab_ai_review_provider=openai producer_gap_discovery_ai_provider=openai stage_hook_workorder_discovery_ai_provider=openai pattern_labs=true deepseek_swing_lab=false code_improvement_workorder=true daily_ev=true runtime_approval_summary=true runtime_apply_gap_audit=true key_lineage_ledger=true conversion_lane=true next_stage2_checklist=true finished_at=2026-07-29T22:35:00+0900`
- predecessor_status: `pass`
- predecessor_wait_count: `0`
- predecessor_timeout_count: `0`
- log_issues: `[]`

## Execution Profile
- profile_status: `recovered_partial_profile`
- disabled_stage_flags: `['swing_lifecycle', 'swing_strategy_discovery', 'swing_lifecycle_matrix', 'swing_lifecycle_bucket_discovery', 'deepseek_swing_lab']`
- missing_required_flags: `[]`
- interpretation: `latest DONE marker was produced by a recovery run with selected heavy stages disabled; same-date artifacts are still validated separately`
- missing_required_artifacts: `[]`
- missing_downstream_links: `[]`
- stale_downstream_links: `[]`
- runtime_apply_gap_issues: `[]`

## Warning Follow-Up Summary
- status: `warning`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- P1 `submit_drought` 판정: `pass_no_submit_drought_critical`
  - 근거: `{'status': 'not_applicable', 'handoff_status': 'not_applicable', 'root_cause_closure_status': 'not_applicable', 'root_cause_open_reasons': [], 'artifact_regeneration_required': False, 'critical': False, 'primary': 'LATENCY_DROUGHT', 'matches': ['LATENCY_DROUGHT'], 'missing': [], 'quote_freshness_attribution_inconsistent': False, 'submit_drought_refresh_attempted_count': 5, 'submit_drought_refresh_applied_count': 1, 'submit_drought_latency_pass_recovered_count': 1, 'submit_drought_unknown_latency_reason_count': 0, 'ldm_submit_real_submitted_row_count': 10, 'ldm_submit_missing_broker_order_key_count': 0, 'ldm_submit_missing_broker_order_key_rate': 0.0, 'ldm_submit_post_submit_provenance_join_gap': False, 'ldm_submit_post_submit_provenance_join_gap_raw': False, 'ldm_submit_bot_history_backfill_candidate_count': 0, 'ldm_submit_bot_history_backfill_full_coverage': False, 'ldm_submit_bot_history_exact_mapping_count': 0, 'ldm_submit_bot_history_exact_mapping_full_coverage': False, 'ldm_submit_post_submit_provenance_join_resolution': 'no_gap_broker_order_key_present_or_no_missing_rows'}`
  - 다음 액션: `No submit drought critical condition was active in this verification context.`
- P2 `scalp_entry_adm_unknown_bucket_source_quality_gap` 판정: `source_quality_followup_required`
  - 근거: `{'status': 'warning', 'warnings': ['joined_sample_below_sample_floor', 'unknown_bucket_source_quality_gap'], 'affected_rows': 2, 'affected_rate': 0.0235, 'dimension_counts': {'score_bucket': 1, 'risk_context_bucket': 1, 'price_resolution_bucket': 1}, 'unknown_root_cause_counts': {'score_bucket:source_score_missing': 1, 'risk_context_bucket:post_submit_or_exit_not_required': 1, 'price_resolution_bucket:post_submit_or_exit_not_required': 1}, 'stage_counts': {'latency_block': 6, 'scalp_entry_action_decision_snapshot': 35, 'order_bundle_submitted': 10, 'blocked_ai_score': 7, 'scalp_sim_entry_ai_price_skip_order': 10, 'entry_submit_revalidation_block': 1, 'scalp_sim_sell_order_assumed_filled': 1}, 'recommended_route': 'source_quality_workorder', 'not_available_route': 'field_legitimately_unavailable_no_workorder', 'lookup_status_counts': {'matched_prior_bucket': 25, 'new_or_unseen_token_vs_prior_adm': 60}}`
  - 다음 액션: `Prioritize source score emission for score_bucket unknown rows, then risk_context/price_resolution source fields; keep not_available buckets as explicit non-workorder context unless they become required source fields.`
- P3 `pattern_lab_warning` 판정: `warning_review_required`
  - 근거: `{'currentness_status': 'pass', 'currentness_fail_count': 0, 'ai_review_status': 'warning', 'ai_review_workorder_count': 1, 'ai_review_warnings': []}`
  - 다음 액션: `No new pattern-lab implement_now item; keep pattern lab warning as source-only monitoring unless fresh currentness or AI review emits a concrete workorder.`
- P4 `live_auto_ready_zero_breakdown` 판정: `warning_explained_no_live_auto_ready`
  - 근거: `{'live_auto_apply_ready_count': 0, 'state_counts': {'source_only_keep_collecting': 194, 'lifecycle_flow_sim_probe_candidate': 1, 'sim_auto_approved': 1, 'new_bucket_candidate': 10}, 'source_bucket_kind_counts': {'taxonomy_provenance_gap': 26, 'source_only_observation': 178, 'lifecycle_flow_sim_probe_policy': 1, 'sim_auto_policy': 1}, 'runtime_gap_categories': {'runtime_blocked_contract_gap': 11, 'sim_auto_approved': 1, 'source_only_explicit_exclusion': 2, 'source_quality_blocker': 12}, 'source_contract_status': 'warning', 'source_contract_change_count': 12, 'ai_two_pass_review_status': 'parsed', 'positive_edge_source_quality_pass_count': 0, 'bridge_blocker_ledger_count': 26, 'runtime_uptake_rate_pct': 0.0, 'handoff_warnings': ['lifecycle_bucket_discovery_source_contract_warning', 'source_contract_drift_warning']}`
  - 다음 액션: `Keep complete lifecycle promotion as the owner; close source-contract drift, source-quality blockers, and runtime_blocked_contract_gap buckets before expecting live-auto candidates.`

## Runtime Apply Gap Audit
- status: `pass`
- retry_queue_count: `0`
- codex_directive_count: `2`
- summary: `{'actionable_unknown_gap_count': 3, 'ai_review_retry_pending': False, 'ai_review_status': 'parsed', 'bridge_blocker_ledger_count': 26, 'candidate_count': 26, 'codex_directive_count': 2, 'conversion_blocker_rank_count': 25, 'critical_failure_count': 0, 'derived_review_category_counts': {'runtime_blocked_contract_gap': 11, 'sim_auto_approved': 1, 'source_only_explicit_exclusion': 2, 'source_quality_blocker': 12}, 'positive_edge_source_quality_pass_count': 0, 'quiet_gap_codex_directive_count': 0, 'quiet_gap_count': 143, 'quiet_gap_rollup_count': 143, 'retry_queue_count': 0, 'runtime_uptake_rate_pct': 0.0, 'source_dimension_gap_count': 24, 'status': 'pass'}`

## BUY Funnel Submit Drought Handoff
- status: `not_applicable`
- critical: `False`
- missing: `[]`

## Submit Bucket Handoff
- status: `pass`
- attribution_present: `True`
- missing: `[]`

## Holding Bucket Handoff
- status: `pass`
- attribution_present: `True`
- source_present: `True`
- runtime_candidate_count: `0`
- bucket_count ev/runtime/expected: `12` / `12` / `12`
- workorder_count ev/runtime/expected: `3` / `3` / `3`
- missing: `[]`

## Exit Bucket Handoff
- status: `pass`
- attribution_present: `True`
- source_present: `True`
- runtime_candidate_count: `0`
- bucket_count ev/runtime/expected: `25` / `25` / `25`
- workorder_count ev/runtime/expected: `5` / `5` / `5`
- missing: `[]`

## Lifecycle Flow Bucket Handoff
- status: `pass`
- attribution_present: `True`
- flow_count: `134`
- complete_flow_count: `3`
- direct_sim_record_complete_flow_count: `0`
- adm_bridge_complete_flow_count: `3`
- fallback_complete_flow_count: `0`
- incomplete_flow_count: `131`
- complete_flow_rate: `0.0224`
- join_contract_blocked: `False`
- bundle_ev_tuning_state: `ready_for_bundle_ev_tuning`
- top_incomplete_reason: `missing_holding`
- missing: `[]`

## AI Correction
- status: `pass`
- ai_status: `parsed`
- provider_status: `{'provider': 'openai', 'status': 'reused_valid_artifact', 'new_provider_call': False, 'key_name': 'OPENAI_API_KEY', 'attempt_index': 1, 'model_index': 1, 'configured_key_count': 2, 'attempted_key_count': 1, 'attempted_keys': 1, 'attempted_key_names': ['OPENAI_API_KEY'], 'configured_model_count': 3, 'attempted_model_count': 1, 'attempted_models': ['gpt-5.5'], 'configured_models': ['gpt-5.5', 'gpt-5.4', 'gpt-5.4-mini'], 'model': 'gpt-5.5', 'schema_name': 'threshold_ai_correction_v1', 'reasoning_effort': 'high', 'prompt_chars': 111678, 'input_context_chars': 110358, 'input_context_hash': '94d4d03654144985cdbcb5b4e3ed72fea9547b8e6c29b44f9b4d5f2a036bfbc1', 'elapsed_ms': 92928, 'output_chars': 12232, 'input_tokens': 31984, 'output_tokens': 7412, 'total_tokens': 39396, 'estimated_cost': None, 'estimated_cost_usd': None, 'cost_estimate_status': 'missing_price_contract', 'reuse_source_path': '/home/ubuntu/KORStockScan/data/report/threshold_cycle_ai_review/threshold_cycle_ai_review_2026-07-29_postclose.json', 'reused_at': '2026-07-29 22:24:35', 'estimated_incremental_cost': 0.0, 'estimated_incremental_cost_usd': 0.0, 'incremental_cost_status': 'reused_no_new_provider_call'}`
- blocking_runtime_candidate_families: `['bad_entry_refined_canary', 'entry_split_order_plan', 'holding_exit_decision_matrix_advisory', 'lifecycle_decision_matrix_runtime', 'protect_trailing_smoothing', 'scale_in_split_order_plan', 'soft_stop_whipsaw_confirmation']`
- parse_warnings: `[]`
- interpretation: `AI correction parsed successfully`

## Scalp Sim Overnight
- status: `pass`
- decision_target: `1`
- active_undecided_count: `0`
- decision_coverage_rate: `1.0`
- source_quality_status: `pass`
- source_quality_warnings: `[]`
- interpretation: `scalp sim overnight preclose decisions covered active sim positions`

## Entry Bucket Handoff
- status: `pass`
- expected_candidate_ids: `[]`
- missing_ev_candidate_ids: `[]`
- missing_runtime_summary_candidate_ids: `[]`
- missing_workorder_order_ids: `[]`
- interpretation: `LDM entry bucket candidates and workorders propagated to threshold EV, runtime summary, and code workorder.`

## Scale-In Bucket Handoff
- attribution_present: `True`
- source_present: `True`
- status: `pass`
- expected_candidate_ids: `[]`
- missing_ev_candidate_ids: `[]`
- missing_runtime_summary_candidate_ids: `[]`
- missing_workorder_order_ids: `[]`
- interpretation: `LDM scale-in bucket candidates and workorders propagated to threshold EV, runtime summary, and code workorder.`
- policy_contract_status: `pass`
- policy_contract_missing: `[]`
- policy_contract_interpretation: `Scale-in policy contract closed as source-only; runtime remains disabled and reopen trigger is preserved.`

## Overnight Bucket Handoff
- attribution_present: `True`
- source_present: `True`
- status: `pass`
- expected_candidate_ids: `[]`
- missing_ev_candidate_ids: `[]`
- missing_runtime_summary_candidate_ids: `[]`
- missing_workorder_order_ids: `[]`
- interpretation: `LDM overnight bucket candidates and workorders propagated to threshold EV, runtime summary, and code workorder.`

## Lifecycle Bucket Discovery Handoff
- status: `pass`
- source_contract_status: `warning`
- ai_two_pass_review_status: `parsed`
- expected_candidate_ids: `['lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_sim_panic_level1_entry_observed_stal', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_s', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_s', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_sim_entry_ai_price_skip_order_stale_s', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_sim_entry_ai_price_skip_order_stale_s', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_sim_panic_level1_entry_observed_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_combo_holding_flow_source_scalp_sim_ov', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_pyramid_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_none_exit_ex', 'scale_in:stage_policy:scale_in_weighted_adm_v1', 'source_contract:source_added:lifecycle_ai_context_attribution:source_key_lifecycle_ai_context_attribution', 'source_contract:source_added:scale_in_attribution:source_key_scale_in_attribution', 'source_contract:source_added:scale_in_counterfactual_enrichment:source_key_scale_in_counterfactual_enrichment', 'source_contract:source_added:scalp_sim_holding:source_key_scalp_sim_holding', 'source_contract:source_added:scalp_sim_overnight:source_key_scalp_sim_overnight', 'source_contract:source_added:scalp_sim_panic:source_key_scalp_sim_panic', 'source_contract:source_added:scalp_sim_scale_in:source_key_scalp_sim_scale_in', 'source_contract:source_added:scalp_sim_submit:source_key_scalp_sim_submit', 'source_contract:source_added:sim_post_sell:source_key_sim_post_sell', 'source_contract:source_added:wait6579:source_key_wait6579']`
- live_auto_apply_families: `[]`
- missing_bridge_families: `[]`
- missing_runtime_summary_candidate_ids: `[]`
- workorder_needed_bucket_ids: `['source_contract:source_added:lifecycle_ai_context_attribution:source_key_lifecycle_ai_context_attribution', 'source_contract:source_added:scale_in_attribution:source_key_scale_in_attribution', 'source_contract:source_added:scale_in_counterfactual_enrichment:source_key_scale_in_counterfactual_enrichment', 'source_contract:source_added:scalp_sim_holding:source_key_scalp_sim_holding', 'source_contract:source_added:scalp_sim_overnight:source_key_scalp_sim_overnight', 'source_contract:source_added:scalp_sim_panic:source_key_scalp_sim_panic', 'source_contract:source_added:scalp_sim_scale_in:source_key_scalp_sim_scale_in', 'source_contract:source_added:scalp_sim_submit:source_key_scalp_sim_submit', 'source_contract:source_added:sim_post_sell:source_key_sim_post_sell', 'source_contract:source_added:wait6579:source_key_wait6579']`
- ai_post_apply_followup_bucket_ids: `[]`
- warnings: `['lifecycle_bucket_discovery_source_contract_warning', 'source_contract_drift_warning']`
- interpretation: `lifecycle bucket discovery candidates propagated to bridge/runtime summary/workorder`

## LDM Hypothesis Parent Refinement
- status: `pass`
- input/consumed: `2` / `2`
- derived input/consumed: `0` / `0`
- derived_contract_drift_recompute_consumed: `False`
- closure_counts: `{'new_parent_candidate_created': 2}`
- missing: `[]`
- warnings: `[]`
- contract_drift: `{'candidate_feature_event_count': 61, 'recomputable_match_count': 61, 'recomputable_hypothesis_ids': ['ldm_hypothesis_00d0b765311ad7aa', 'ldm_hypothesis_e04e4d815fd8d0f9'], 'runtime_matched_event_count': 61}`
- diagnosis_missing_warning_input_ids: `[]`
- diagnosis_missing_fail_input_ids: `[]`
- diagnosed_repeated_input_ids: `['ldm_refinement_c6380c8c3ca9d081', 'ldm_refinement_51f4e5e2d0f1a36d']`
- runtime_authority_violation_input_ids: `[]`

## Active Sim Priority Handoff
- status: `pass`
- active_seed_ids: `[]`
- observed_seed_ids: `[]`
- missing: `[]`
- warnings: `[]`
- match_absence_diagnosis: `not_applicable`
- match_absence_reason: `active_priority_observed_or_no_active_priority`
- candidate_prefix_count: `61`
- top_candidate_prefixes: `[('{"entry_score_parent": "score_watch_recovery", "entry_source_parent": "entry_source_blocked_ai_score"}', 48), ('{"entry_score_parent": "score_watch_recovery", "entry_source_parent": "entry_source_wait6579"}', 13)]`

## Lifecycle Bucket Windows
- status: `warning`
- checked: `True`
- windows: `{'rolling5d': {'available': True, 'source_contract_status': 'pass', 'parent_granularity_status': 'too_broad', 'parent_bucket_count': 17, 'window_role': 'rolling_confirmation'}, 'rolling10d': {'available': True, 'source_contract_status': 'pass', 'parent_granularity_status': 'target_pass', 'parent_bucket_count': 30, 'window_role': 'rolling_confirmation'}, 'mtd': {'available': True, 'source_contract_status': 'pass', 'parent_granularity_status': 'target_pass', 'parent_bucket_count': 38, 'window_role': 'promotion_confirmation'}}`
- missing: `[]`
- warnings: `['lifecycle_bucket_discovery_rolling5d_parent_granularity_not_target']`

## Swing Lifecycle Handoff
- status: `disabled`
- expected_candidate_ids: `[]`
- missing_ev_candidate_ids: `[]`
- missing_runtime_summary_candidate_ids: `[]`
- missing_workorder_order_ids: `[]`
- daily_simulation_consumed: `None`
- ai_two_pass_review_status: `-`
- warnings: `[]`
- interpretation: `-`

## Producer Gap Discovery Handoff
- status: `pass`
- ai_two_pass_review_status: `parsed`
- audit_status: `pass`
- expected_workorder_order_ids: `[]`
- missing_workorder_order_ids: `[]`
- missing: `[]`
- interpretation: `producer gap high-priority orders propagated to code improvement workorder with parsed AI review`

## Stage Hook Workorder Handoff
- status: `pass`
- ai_two_pass_review_status: `parsed`
- audit_status: `pass`
- expected_workorder_order_ids: `['order_stage_hook_workorder_discovery_stage_hook_holding_flow_runner_debounce_guard', 'order_stage_hook_workorder_discovery_stage_hook_plateau_breakdown_exit_arbitration_probe']`
- missing_workorder_order_ids: `[]`
- unconsumed_hook_candidate_ids: `[]`
- missing: `[]`
- interpretation: `stage hook implementation-ready orders propagated to code improvement workorder`

## Bottom Rebound Sim Handoff
- status: `not_applicable`
- included: `False`
- source_rows: `0`
- selected_candidate_count: `0`
- arm_count: `0`
- persisted_candidate_count: `0`
- persisted_arm_count: `0`
- missing: `[]`
- interpretation: `bottom_rebound source was absent or blocked; safe-pool-only swing sim path applies`

## Runtime Gap Provenance
- active_gap_count: `0`
- raw_preserved: `None`
- gap_affected_handoff_count: `0`

## Workorder Snapshot
- generation_id: `2026-07-29-b59da43d5b3f`
- source_hash: `b59da43d5b3f5a9bbd0d66e6d7efce9077f70e682675372c7ef231db50a53896`
- snapshot_status: `source_changed_with_lineage`
- previous_generation_id: `2026-07-29-72601dca64a3`
- previous_source_hash: `72601dca64a3f134c9099f1d145ac144d9b9d1a5fd239ded400296b527327c7b`
- new_order_ids: `['order_ai_threshold_miss_ev_recovery', 'order_latency_guard_miss_ev_recovery', 'order_panic_sell_defense_lifecycle_transition_pack', 'order_partial_only_표류_전용_timeout_report_only', 'order_perf_buy_funnel_json_scan', 'order_perf_daily_report_bulk_history', 'order_perf_daily_report_engine_singleton', 'order_perf_final_ensemble_records', 'order_perf_monitor_snapshot_stream_tail', 'order_perf_sentinel_event_cache_incremental_review', 'order_rising_missed_classifier_prior_bridge', 'order_rising_missed_classifier_prior_feedback_bridge', 'order_rising_missed_scout_loss_filter', 'order_rising_missed_scout_post_sell_bridge', 'order_rising_missed_scout_scale_in_qty_evidence_split', 'order_split_entry_rebase_수량_정합성_report_only_감사', 'order_동일_종목_split_entry_soft_stop_재진입_cooldown_report_only']`
- removed_order_ids: `['order_lifecycle_bucket_discovery_source_contract_source_contract_source_added_entry_6d966faa56', 'order_lifecycle_bucket_discovery_source_contract_source_contract_source_added_institutional_flow_context_5ffac855c5', 'order_lifecycle_entry_bucket_chosen_action_skip_pre_submit_safety', 'order_lifecycle_entry_bucket_combo_entry_spot_score_score_unknown_source_scalp_sim_entry_ai_price_skip_order_stale_stale_not_a', 'order_lifecycle_entry_bucket_exit_rule_exit_unknown', 'order_lifecycle_entry_bucket_exit_rule_scalp_preset_hard_stop_pct', 'order_lifecycle_entry_bucket_exit_rule_scalp_trailing_take_profit', 'order_lifecycle_entry_bucket_liquidity_bucket_liquidity_not_available', 'order_lifecycle_entry_bucket_overbought_bucket_overbought_not_available', 'order_lifecycle_entry_bucket_score_band_score_unknown', 'order_lifecycle_entry_bucket_source_stage_scalp_sim_entry_ai_price_skip_order', 'order_lifecycle_source_dimension_gap_entry_combo_entry_spot_entry_combo_entry_spot_score_score_unknown_source_scalp_sim_entry_ai_pr_3694e586', 'order_lifecycle_source_dimension_gap_entry_score_band_entry_score_band_score_unknown_2083bdb1d0', 'order_observation_source_quality_unknown_token_provenance_gap']`
- decision_changed_order_ids: `[]`
