# Threshold Cycle Daily EV Report - 2026-06-24

## Summary
- status: `warning`
- warning_count: `9`
- source_quality: status=`pass` allowed=`True`
- samples real/sim: `4` / `629`
- live_auto_ready_count: `0`
- primary_verdict: `sim_evidence_present_no_live_bucket`

## Runtime Apply
- status: `auto_bounded_live_ready`
- runtime_change: `True`
- selected_families: `soft_stop_whipsaw_confirmation, score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, profit_stagnation_exit_runtime, latency_spread_relief_real_operator_override, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, ai_watching_score_smoothing_report_only, lifecycle_decision_matrix_runtime, weak_pullback_entry_block_runtime, early_accel_recheck_runtime, real_pyramid_scale_in_quality_guard_runtime, sell_side_open_time_block_runtime, pre_submit_liquidity_relief_runtime, weak_context_late_entry_guard_runtime, swing_market_regime_sensitivity`

## Daily EV
- completed: `4` / open: `0`
- win/loss: `1` / `3` (`25.0`%)
- avg_profit_rate: `-1.18`%
- realized_pnl_krw: `-82831`
- full_fill_completed_avg_profit_rate: `-2.785`%

## Entry Funnel
- budget_pass_to_submitted: `8` / `99` (`8.08`%)
- latency pass/block: `19` / `80`
- latency submit routing: `latency_classifier_runtime_semantics_gap`
- latency recommended action: `reject` (`recovery_count=0 below floor=10`)
- latency profile generation: `{'mode': 'grid_quantile_search', 'profile_count': 540, 'age_cap_ms': 1500, 'jitter_cap_ms': 1500, 'spread_cap_ratio': 0.012, 'counterfactual_sample_floor': 3, 'recovery_event_floor_ratio': 0.1}`
- safe/caution_normal/recovery: `0` / `0` / `0`
- recovery attempts/cf sample/cf ev: `0` / `0` / `None`%
- recovered/lost labels: `0` / `0`
- stale/broker override excluded: `0` / `0`
- full/partial fill: `3` / `2`

## Holding Exit
- holding_reviews: `609`
- exit_signals: `69`
- holding_review_ms_p95: `2613.0`

## Scalp Simulator
- authority: `equal_weight` / fill_policy: `signal_inclusive_best_ask_v1`
- armed/filled/sold: `124` / `124` / `72`
- expired/unpriced/duplicate: `0` / `0` / `30`
- entry_ai_price applied/skip: `3` / `0`
- submit_revalidation warning/block: `123` / `0`
- scale_in filled/unfilled: `0` / `3`
- overnight decision/sell/hold/carry_restored: `4` / `4` / `0` / `0`
- completed_profit_summary: `{'sample': 72, 'win_count': 13, 'loss_count': 59, 'avg_profit_rate': -1.5994, 'median_profit_rate': -1.93, 'downside_p10_profit_rate': -3.99, 'upside_p90_profit_rate': 2.07, 'win_rate': 0.1806, 'loss_rate': 0.8194, 'stddev_profit_rate': 2.5572}`
- post_sell_join: joined=`71` / pending=`1`
- post_sell_mfe_mae_10m: mfe=`2.5683`% / mae=`-5.7687`% / close=`0.2969`%

## Missed Probe Counterfactual
- book: `scalp_score65_74_probe_counterfactual` / role: `missed_buy_probe_counterfactual`
- total/score65_74: `77` / `12`
- avg_expected_ev: `2.6637`% / score65_74_avg_expected_ev: `0.2674`%
- actual_order_submitted: `False` / broker_order_forbidden: `True`
- authority: `missed_probe_ev_only_not_broker_execution`

## Scalp Entry ADM
- artifact: `/home/ubuntu/KORStockScan/data/report/scalp_entry_action_decision_matrix/scalp_entry_action_decision_matrix_2026-06-24.json`
- status: `warning` / authority: `entry_advisory_prompt_context_only`
- total/joined/floor: `571` / `61` / `20`
- prompt_applied_count: `442`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 571}`
- forced_action_counts: `{'-': 571}`
- missing_actions: `[]`
- zero_sample_actions: `['WAIT_REQUOTE', 'SKIP_STALE']`
- top_actions: `[{'action': 'BUY_NOW', 'sample_count': 25, 'joined_sample': 1, 'source_quality_adjusted_ev_pct': -0.1}, {'action': 'BUY_DEFENSIVE', 'sample_count': 8, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'NO_BUY_AI', 'sample_count': 470, 'joined_sample': 33, 'source_quality_adjusted_ev_pct': -0.0614}, {'action': 'SKIP_SOURCE_QUALITY', 'sample_count': 4, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'SKIP_PRE_SUBMIT_SAFETY', 'sample_count': 51, 'joined_sample': 27, 'source_quality_adjusted_ev_pct': -1.2086}]`

## Lifecycle Decision Matrix
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-06-24.json`
- status: `pass` / version: `lifecycle_decision_matrix_v1_2026-06-24`
- total/joined: `6192` / `3923`
- policy_pass/promote_ready: `5` / `1`
- lifecycle_flow buckets/complete/runtime/workorders: `82` / `32` / `0` / `20`
- holding/exit buckets: `30` / `51`
- holding/exit workorders: `10` / `10`
- lifecycle identity missing/join_rate: `0` / `1.0`
- lifecycle complete_flow_rate: `0.0059`
- incomplete_flow_reason_counts: `{'missing_holding': 5334, 'missing_exit': 3766, 'missing_submit': 5335, 'missing_entry': 5102, 'postclose_exit_without_entry': 1589, 'candidate_id_only': 5168, 'sim_record_id_only': 97, 'scale_in_noise_only': 3513}`
- fixed_threshold_roles: `{'hard_safety': ['broker_submit_guard', 'stale_quote_submit_block', 'price_freshness_guard', 'hard_stop', 'protect_stop', 'emergency_stop', 'account_order_cooldown_qty_guard'], 'baseline_prior': ['BUY_SCORE_THRESHOLD', 'VPW_MIN_SCORE', 'strength_momentum_cutoff', 'entry_score_cutoff'], 'bounded_tunable': ['SCALP_ENTRY_LATENCY_MAX_WS_AGE_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_WS_JITTER_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_SPREAD_RATIO_FOR_CAUTION', 'score65_74_recovery_probe', 'soft_stop_whipsaw_confirmation', 'holding_flow_override', 'scale_in_price_guard'], 'legacy_archive': ['fallback_scout_main', 'fallback_single', 'latency_fallback_split_entry', 'legacy_latency_composite', 'closed_shadow_axes']}`
- policy_entries: `[{'stage': 'entry', 'sample': 671, 'joined_sample': 107, 'stage_ev_composite_pct': 1.0952, 'confidence': 1.0, 'selected_action': 'BUY_DEFENSIVE', 'source_quality_gate': 'pass', 'promote_ready': True}, {'stage': 'submit', 'sample': 136, 'joined_sample': 69, 'stage_ev_composite_pct': -0.629, 'confidence': 1.0, 'selected_action': 'NO_CHANGE', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'holding', 'sample': 128, 'joined_sample': 69, 'stage_ev_composite_pct': -1.185, 'confidence': 1.0, 'selected_action': 'EXIT', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'scale_in', 'sample': 3600, 'joined_sample': 3516, 'stage_ev_composite_pct': -0.4747, 'confidence': 1.0, 'selected_action': 'NO_CHANGE', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'exit', 'sample': 1657, 'joined_sample': 162, 'stage_ev_composite_pct': -0.9513, 'confidence': 1.0, 'selected_action': 'EXIT', 'source_quality_gate': 'pass', 'promote_ready': False}]`

## Lifecycle Bucket Discovery
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-06-24.json`
- status: `pass` / human_intervention_required: `False`
- candidates/surfaced: `500` / `94`
- sim_auto/live_auto/new_bucket: `5` / `0` / `0`
- role/window: `new_pattern_detection` / `same_day_source_bundle_plus_rolling_threshold_cycle_consumer`
- parent_count/granularity/conflict: `40` / `target_pass` / `2`
- state_counts: `{'source_only_keep_collecting': 486, 'lifecycle_flow_sim_probe_candidate': 2, 'sim_auto_approved': 5, 'entry_only_sim_auto_approved': 6, 'entry_only_source_candidate': 1}`
- top_surfaced: `[{'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 2, 'source_quality_adjusted_ev_pct': 3.097}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': 1.5402}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 2719, 'source_quality_adjusted_ev_pct': -0.7642}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_pyramid_', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 710, 'source_quality_adjusted_ev_pct': 0.6796}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 80, 'source_quality_adjusted_ev_pct': -0.9334}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wait6579_ev_cohort_stale_fresh_or_unflagge', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 38, 'source_quality_adjusted_ev_pct': 2.2786}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait6579_ev_cohort_stale_fresh_or_unflagged_', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 28, 'source_quality_adjusted_ev_pct': 0.5371}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wait6579_ev_cohort_stale_fresh_or_unflagge', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 11, 'source_quality_adjusted_ev_pct': 2.3521}]`

## Lifecycle Bucket Windows
- promotion_window: `mtd`
- confirmation_windows: `['rolling5d', 'rolling10d']`
- windows: `{'rolling5d': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-06-24_rolling5d.json', 'window_role': 'rolling_confirmation', 'window_policy': 'rolling5d', 'status': 'pass', 'parent_bucket_count': 26, 'selected_parent_level': 'L1_broad', 'parent_granularity_status': 'too_broad', 'absorbed_child_count': 225, 'absorbed_sample_count': 16054, 'child_conflict_warning_count': 11, 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'parsed'}, 'rolling10d': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-06-24_rolling10d.json', 'window_role': 'rolling_confirmation', 'window_policy': 'rolling10d', 'status': 'pass', 'parent_bucket_count': 43, 'selected_parent_level': 'L1_broad', 'parent_granularity_status': 'target_pass', 'absorbed_child_count': 500, 'absorbed_sample_count': 90927, 'child_conflict_warning_count': 20, 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'parsed'}, 'mtd': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-06-24_mtd.json', 'window_role': 'promotion_confirmation', 'window_policy': 'mtd', 'status': 'pass', 'parent_bucket_count': 39, 'selected_parent_level': 'L1_broad', 'parent_granularity_status': 'target_pass', 'absorbed_child_count': 500, 'absorbed_sample_count': 197941, 'child_conflict_warning_count': 17, 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'parsed'}}`

## Lifecycle AI Context
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_ai_context/lifecycle_ai_context_2026-06-24.json`
- context_version: `lifecycle_ai_context_v1_2026-06-24` / authority: `ai_advisory_prompt_context_only`
- prompt_stage_count: `3` / runtime_effect: `False`
- stage_contexts: `[{'stage': 'entry', 'prompt_injection_allowed': True, 'policy_key': 'entry:weighted_adm_v1', 'alignment_hint': 'BUY_DEFENSIVE', 'context_contribution_score': 0.0, 'attribution_quality_status': 'observational_only_pending_outcome'}, {'stage': 'submit', 'prompt_injection_allowed': False, 'policy_key': 'submit:weighted_adm_v1', 'alignment_hint': 'NO_CHANGE', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'holding', 'prompt_injection_allowed': True, 'policy_key': 'holding:weighted_adm_v1', 'alignment_hint': 'EXIT', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'scale_in', 'prompt_injection_allowed': False, 'policy_key': 'scale_in:weighted_adm_v1', 'alignment_hint': 'NO_CHANGE', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'exit', 'prompt_injection_allowed': True, 'policy_key': 'exit:weighted_adm_v1', 'alignment_hint': 'EXIT', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}]`

## Lifecycle AI Context Attribution
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_ai_context_attribution/lifecycle_ai_context_attribution_2026-06-24.json`
- eligible/applied/skipped: `1020` / `1020` / `0`
- replay_budget: `30`
- implementation_status: `implemented`
- stage_attribution: `{'entry': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'observational_only_pending_outcome', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'submit': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'holding': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'scale_in': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'exit': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}}`

## Institutional Flow Context
- artifact: `/home/ubuntu/KORStockScan/data/report/institutional_flow_context/institutional_flow_context_2026-06-24.json`
- status: `pass` / authority: `source_only_lifecycle_feature`
- rows ok/partial/missing/token_error: `120` / `0` / `0` / `0`
- join_rate_pct: `100.0`
- source_mix: `{'ka10059+ka10061': 120}`
- top_net_buy: `[{'stock_code': '005930', 'smart_money_net': 2883413, 'foreign_net_roll5': 0, 'inst_net_roll5': 0, 'regime': 'UNKNOWN'}, {'stock_code': '006800', 'smart_money_net': 826927, 'foreign_net_roll5': 5373437, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}, {'stock_code': '003490', 'smart_money_net': 813480, 'foreign_net_roll5': 1841900, 'inst_net_roll5': 368037, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '047040', 'smart_money_net': 742846, 'foreign_net_roll5': 0, 'inst_net_roll5': 0, 'regime': 'UNKNOWN'}, {'stock_code': '015760', 'smart_money_net': 365462, 'foreign_net_roll5': 0, 'inst_net_roll5': 0, 'regime': 'UNKNOWN'}, {'stock_code': '196170', 'smart_money_net': 296498, 'foreign_net_roll5': 106837, 'inst_net_roll5': 348682, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '028300', 'smart_money_net': 268079, 'foreign_net_roll5': 0, 'inst_net_roll5': 218302, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '046890', 'smart_money_net': 206595, 'foreign_net_roll5': 254268, 'inst_net_roll5': 266444, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '028050', 'smart_money_net': 199304, 'foreign_net_roll5': 0, 'inst_net_roll5': 0, 'regime': 'UNKNOWN'}, {'stock_code': '336570', 'smart_money_net': 196160, 'foreign_net_roll5': 0, 'inst_net_roll5': 0, 'regime': 'UNKNOWN'}]`

## Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-06-24.json`
- fresh: gemini=`False` claude=`True`
- consensus/orders/family_candidates: `0` / `10` / `0`

## Swing Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_2026-06-24.json`
- deepseek_lab_available: `True`
- findings/orders: `5` / `3`
- data_quality_warnings: `0`
- top_level_data_quality_warnings: `0`
- resolved_data_quality_warnings: `0`
- ofi_qi_stale_missing_unique_records: `0`
- ofi_qi_stale_missing_reasons: `{'micro_missing': 0, 'micro_stale': 0, 'observer_unhealthy': 0, 'micro_not_ready': 0, 'state_insufficient': 0}`
- ofi_qi_stale_missing_reason_combinations: `{}`
- ofi_qi_stale_missing_reason_combination_unique_records: `{}`
- ofi_qi_observer_unhealthy_overlap: `{'observer_unhealthy_total': 0, 'observer_unhealthy_with_other_reason': 0, 'observer_unhealthy_only': 0}`
- source_quality_blocked_families: `[]`
- carryover_warnings: `0`
- population_split_available: `True`

## Swing Strategy Discovery Sim
- artifact: `/home/ubuntu/KORStockScan/data/report/swing_strategy_discovery_ev/swing_strategy_discovery_ev_2026-06-24.json`
- authority: `swing_sim_exploration_only` / source_only: `True`
- candidate/arm/policy_exit_rows: `1238` / `7875` / `7875`
- labeled/pending_future_quotes: `1209` / `4072`
- implementation_status: `implemented`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- surviving/avoid_bucket_count: `1` / `20`
- runtime_effect: `False`

## Pipeline Event Verbosity
- artifact: `/home/ubuntu/KORStockScan/data/report/pipeline_event_verbosity/pipeline_event_verbosity_2026-06-24.json`
- state: `v2_shadow_pending_flush`
- recommended_workorder_state: `observe_pending_next_flush`
- high_volume_line_count: `7368`
- high_volume_byte_share_pct: `3.84`
- parity_ok: `False`
- suppress_eligibility: `False`

## Codebase Performance Workorder Source
- artifact: `/home/ubuntu/KORStockScan/data/report/codebase_performance_workorder/codebase_performance_workorder_2026-06-24.json`
- authority: `ops_performance_workorder_source`
- accepted/deferred/rejected: `7` / `2` / `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`

## Pattern Lab Audits
- currentness: status=`pass` fail=`0` orders=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-06-24.json`
- ai_review: status=`pass` orders=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_ai_review/pattern_lab_ai_review_2026-06-24.json`
- time_window_regime_counterfactual: status=`pass` artifact=`/home/ubuntu/KORStockScan/data/report/time_window_regime_counterfactual/time_window_regime_counterfactual_2026-06-24.json`
- producer_gap_discovery: status=`pass` orders=`0` artifact=`/home/ubuntu/KORStockScan/data/report/producer_gap_discovery/producer_gap_discovery_2026-06-24.json`
- stage_hook_workorder_discovery: status=`warning` orders=`2` artifact=`/home/ubuntu/KORStockScan/data/report/stage_hook_workorder_discovery/stage_hook_workorder_discovery_2026-06-24.json`
- propagation: status=`warning` fail=`0` warnings=`2` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_2026-06-24.json`

## Swing Runtime Approval
- request_report: `/home/ubuntu/KORStockScan/data/report/swing_runtime_approval/swing_runtime_approval_2026-06-23.json`
- approval_artifact: `-`
- requested/approved/live_dry_run: `2` / `2` / `1`
- dry_run_forced: `True`
- legacy_phase0_real_canary_ignored: `False`
- blocked: `[]`

## Code Improvement Workorder
- artifact: `/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-06-24.json`
- markdown: `/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-06-24.md`
- selected_order_count: `110`
- decision_counts: `{'implement_now': 1, 'attach_existing_family': 132, 'design_family_candidate': 5, 'defer_evidence': 3, 'reject': 3}`

## Approval Requests
- none

## Swing Approval Requests
- `swing_model_floor` approval_id=`swing_runtime_approval:2026-06-23:swing_model_floor` score=`0.7812` target_env_keys=`['SWING_FLOOR_BULL', 'SWING_FLOOR_BEAR']`
- `swing_market_regime_sensitivity` approval_id=`swing_runtime_approval:2026-06-23:swing_market_regime_sensitivity` score=`0.7812` target_env_keys=`['SWING_MARKET_REGIME_SENSITIVITY']`

## Calibration Decisions
## Code Improvement Top Orders
- `order_entry_submit_drought_auto_resolution` decision=`implement_now` subsystem=`runtime_instrumentation`
- `order_entry_broker_receipt_contract_gap_review` decision=`attach_existing_family` subsystem=`runtime_instrumentation`
- `order_entry_fill_quality_contract_gap_review` decision=`attach_existing_family` subsystem=`runtime_instrumentation`

- `soft_stop_whipsaw_confirmation`: `adjust_up` sample=`7249/10`
- `holding_flow_ofi_smoothing`: `hold` sample=`72/20`
- `protect_trailing_smoothing`: `adjust_down` sample=`36/20`
- `trailing_continuation`: `freeze` sample=`276/20`
- `market_regime_continuous_thresholds`: `hold_sample` sample=`8/10`
- `pre_submit_price_guard`: `hold` sample=`0/1`
- `dynamic_entry_price_resolver`: `hold_sample` sample=`374/20`
- `entry_price_execution_quality`: `hold` sample=`46/5`
- `score65_74_recovery_probe`: `adjust_up` sample=`180/20`
- `strength_momentum_soft_gate_p1`: `hold` sample=`4870/20`
- `overbought_pullback_guard_p1`: `hold` sample=`895/20`
- `liquidity_pre_submit_guard_p1`: `hold` sample=`1156/20`
- `bad_entry_refined_canary`: `adjust_up` sample=`71244/10`
- `holding_exit_decision_matrix_advisory`: `hold_no_edge` sample=`0/1`
- `lifecycle_decision_matrix_runtime`: `adjust_up` sample=`6192/20`
- `scale_in_price_guard`: `hold` sample=`850/20`
- `position_sizing_dynamic_formula`: `hold_sample` sample=`16/30`

## Warnings
- `scalp_entry_adm:ai_numeric_consistency_rows_excluded_from_aggregates`
- `lifecycle_bucket_discovery:source_contract_drift_warning`
- `lifecycle_bucket_discovery:source_contract_drift_warning`
- `swing_strategy_discovery:pending_future_quotes`
- `swing_strategy_discovery:clean_tuning_baseline_swing_discovery_lookback_filtered`
- `swing_lifecycle_decision_matrix:swing_intraday_live_equiv_probe_missing`
- `swing_lifecycle_decision_matrix:pending_future_quotes`
- `swing_lifecycle_decision_matrix:clean_tuning_baseline_swing_discovery_lookback_filtered`
- `pattern_lab_propagation_audit_warning`
