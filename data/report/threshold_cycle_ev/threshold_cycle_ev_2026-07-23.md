# Threshold Cycle Daily EV Report - 2026-07-23

## Summary
- status: `warning`
- warning_count: `12`
- source_quality: status=`pass` allowed=`True`
- samples real/sim: `54` / `13`
- live_auto_ready_count: `0`
- primary_verdict: `real_primary_evidence_present`

## Runtime Apply
- status: `auto_bounded_live_ready`
- runtime_change: `True`
- selected_families: `soft_stop_whipsaw_confirmation, entry_split_order_plan, scale_in_split_order_plan, score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, profit_stagnation_exit_runtime, latency_spread_relief_real_operator_override, quote_consistency_normalization, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, ai_watching_score_smoothing_report_only, weak_pullback_entry_block_runtime, early_accel_recheck_runtime, real_pyramid_scale_in_quality_guard_runtime, sell_side_open_time_block_runtime, pre_submit_liquidity_relief_runtime, entry_opportunity_recheck_runtime, weak_context_late_entry_guard_runtime, rising_missed_normal_buy_bridge, persistent_operator_overrides_2026_06_26`

## Daily EV
- completed: `0` / open: `0`
- win/loss: `0` / `0` (`0.0`%)
- avg_profit_rate: `0.0`%
- realized_pnl_krw: `0`
- full_fill_completed_avg_profit_rate: `0.0`%

## Entry Funnel
- budget_pass_to_submitted: `0` / `0` (`0.0`%)
- latency pass/block: `0` / `0`
- latency submit routing: `latency_classifier_runtime_semantics_gap`
- latency recommended action: `reject` (`recovery_count=0 below floor=10`)
- latency profile generation: `{'mode': 'grid_quantile_search', 'profile_count': 450, 'age_cap_ms': 1500, 'jitter_cap_ms': 1500, 'spread_cap_ratio': 0.012, 'counterfactual_sample_floor': 3, 'recovery_event_floor_ratio': 0.1}`
- safe/caution_normal/recovery: `0` / `0` / `0`
- recovery attempts/cf sample/cf ev: `0` / `0` / `None`%
- recovered/lost labels: `0` / `0`
- stale/broker override excluded: `0` / `0`
- full/partial fill: `0` / `0`
- entry_split_order_plan: status=`pass` candidates=`1` policy=`entry_split_order_plan:2026-07-23:263dab809c`
- scale_in_split_order_plan: status=`pass` candidates=`2` policy=`scale_in_split_order_plan:2026-07-23:0745ee578b1c`

## Holding Exit
- holding_reviews: `0`
- exit_signals: `0`
- holding_review_ms_p95: `0.0`

## Scalp Simulator
- authority: `equal_weight` / fill_policy: `signal_inclusive_best_ask_v1`
- armed/filled/sold: `12` / `12` / `1`
- expired/unpriced/duplicate: `0` / `0` / `2`
- entry_ai_price applied/skip: `12` / `0`
- submit_revalidation warning/block: `0` / `0`
- scale_in filled/unfilled: `0` / `0`
- overnight decision/sell/hold/carry_restored: `1` / `1` / `0` / `0`
- completed_profit_summary: `{'sample': 1, 'win_count': 0, 'loss_count': 1, 'avg_profit_rate': -0.23, 'median_profit_rate': -0.23, 'downside_p10_profit_rate': -0.23, 'upside_p90_profit_rate': -0.23, 'win_rate': 0.0, 'loss_rate': 1.0, 'stddev_profit_rate': None}`
- post_sell_join: joined=`0` / pending=`1`
- post_sell_mfe_mae_10m: mfe=`None`% / mae=`None`% / close=`None`%

## Missed Probe Counterfactual
- book: `-` / role: `-`
- total/score65_74: `None` / `None`
- avg_expected_ev: `None`% / score65_74_avg_expected_ev: `None`%
- actual_order_submitted: `None` / broker_order_forbidden: `None`
- authority: `-`

## Scalp Entry ADM
- artifact: `/home/ubuntu/KORStockScan/data/report/scalp_entry_action_decision_matrix/scalp_entry_action_decision_matrix_2026-07-23.json`
- status: `warning` / authority: `entry_advisory_prompt_context_only`
- total/joined/floor: `198` / `0` / `20`
- prompt_applied_count: `65`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 198}`
- forced_action_counts: `{'-': 198}`
- missing_actions: `[]`
- zero_sample_actions: `['BUY_NOW']`
- outcome_join_diagnostic: `{'status': 'post_sell_evaluation_missing_or_empty', 'zero_join_reason': 'no_post_sell_evaluation_rows_for_target_date', 'candidate_key_count': 216, 'candidate_key_field_counts': {'candidate_id': 198, 'entry_adm_candidate_id': 0, 'sim_record_id': 2, 'record_id': 79}, 'post_sell_evaluation_rows': 0, 'post_sell_evaluation_join_keys': 0, 'candidate_post_sell_key_overlap_count': 0, 'joined_sample': 0, 'joined_sample_all_rows': 0, 'sample_floor': 20, 'sample_floor_met': False, 'decision_authority': 'source_quality_gap_discovery', 'runtime_effect': False, 'allowed_runtime_apply': False}`
- top_actions: `[{'action': 'WAIT_REQUOTE', 'sample_count': 96, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'SKIP_STALE', 'sample_count': 2, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'BUY_DEFENSIVE', 'sample_count': 20, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'NO_BUY_AI', 'sample_count': 76, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'SKIP_SOURCE_QUALITY', 'sample_count': 2, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}]`

## Lifecycle Decision Matrix
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-07-23.json`
- status: `pass` / version: `lifecycle_decision_matrix_v1_2026-07-23`
- total/joined: `353` / `106`
- policy_pass/promote_ready: `1` / `0`
- lifecycle_flow buckets/complete/runtime/workorders: `30` / `7` / `0` / `20`
- holding/exit buckets: `10` / `19`
- holding/exit workorders: `0` / `5`
- lifecycle identity missing/join_rate: `0` / `1.0`
- lifecycle complete_flow_rate: `0.0345`
- incomplete_flow_reason_counts: `{'missing_holding': 193, 'missing_exit': 179, 'missing_submit': 159, 'missing_entry': 118, 'candidate_id_only': 115, 'scale_in_noise_only': 97, 'sim_record_id_only': 9, 'postclose_exit_without_entry': 17}`
- fixed_threshold_roles: `{'hard_safety': ['broker_submit_guard', 'stale_quote_submit_block', 'price_freshness_guard', 'hard_stop', 'protect_stop', 'emergency_stop', 'account_order_cooldown_qty_guard'], 'baseline_prior': ['BUY_SCORE_THRESHOLD', 'VPW_MIN_SCORE', 'strength_momentum_cutoff', 'entry_score_cutoff'], 'bounded_tunable': ['SCALP_ENTRY_LATENCY_MAX_WS_AGE_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_WS_JITTER_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_SPREAD_RATIO_FOR_CAUTION', 'score65_74_recovery_probe', 'soft_stop_whipsaw_confirmation', 'holding_flow_override', 'scale_in_price_guard'], 'legacy_archive': ['fallback_scout_main', 'fallback_single', 'latency_fallback_split_entry', 'legacy_latency_composite', 'closed_shadow_axes']}`
- policy_entries: `[{'stage': 'entry', 'sample': 171, 'joined_sample': 0, 'stage_ev_composite_pct': None, 'confidence': 0.0, 'selected_action': 'NO_CHANGE', 'source_quality_gate': 'hold_sample', 'promote_ready': False}, {'stage': 'submit', 'sample': 47, 'joined_sample': 0, 'stage_ev_composite_pct': None, 'confidence': 0.0, 'selected_action': 'NO_CHANGE', 'source_quality_gate': 'hold_sample', 'promote_ready': False}, {'stage': 'holding', 'sample': 13, 'joined_sample': 0, 'stage_ev_composite_pct': None, 'confidence': 0.0, 'selected_action': 'NO_CHANGE', 'source_quality_gate': 'hold_sample', 'promote_ready': False}, {'stage': 'scale_in', 'sample': 97, 'joined_sample': 97, 'stage_ev_composite_pct': -0.5735, 'confidence': 1.0, 'selected_action': 'NO_CHANGE', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'exit', 'sample': 25, 'joined_sample': 9, 'stage_ev_composite_pct': -0.8136, 'confidence': 0.324, 'selected_action': 'EXIT', 'source_quality_gate': 'hold_sample', 'promote_ready': False}]`

## Lifecycle Bucket Discovery
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-07-23.json`
- status: `pass` / human_intervention_required: `False`
- candidates/surfaced: `220` / `42`
- sim_auto/live_auto/new_bucket: `1` / `0` / `10`
- role/window: `new_pattern_detection` / `same_day_source_bundle_plus_rolling_threshold_cycle_consumer`
- parent_count/granularity/conflict: `17` / `too_broad` / `0`
- positive_parent/sample_ready/conflict: `0` / `0` / `0`
- active_positive_seed/nonpositive_seed: `0` / `0`
- positive_sim_auto/nonpositive_sim_auto: `0` / `1`
- state_counts: `{'source_only_keep_collecting': 208, 'sim_auto_approved': 1, 'runtime_blocked_contract_gap': 1, 'new_bucket_candidate': 10}`
- top_surfaced: `[{'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 96, 'source_quality_adjusted_ev_pct': -0.5823}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'tighten_or_exclude', 'joined_sample': 6, 'source_quality_adjusted_ev_pct': -0.8717}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_confirmed_stale_stale_high_liquidity_liq', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'tighten_or_exclude', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': -0.96}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_combo_holding_flow_source_scalp_sim_ov', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': -0.1725}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_pyramid_', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': 0.27}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_s', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 0, 'source_quality_adjusted_ev_pct': None}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_s', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 0, 'source_quality_adjusted_ev_pct': None}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_s', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 0, 'source_quality_adjusted_ev_pct': None}]`
- top_sample_ready_positive_parent_buckets: `[]`
- top_active_positive_seeds: `[]`
- top_positive_sim_auto_approved: `[]`
- top_nonpositive_sim_auto_approved: `[{'bucket_id': 'scale_in:stage_policy:scale_in_weighted_adm_v1', 'classification_state': 'sim_auto_approved', 'stage': 'scale_in', 'bucket_type': 'stage_policy', 'source_quality_adjusted_ev_pct': -0.5735, 'joined_sample': 97, 'sample': 97}]`

## Lifecycle Bucket Windows
- promotion_window: `mtd`
- confirmation_windows: `['rolling5d', 'rolling10d']`
- windows: `{'rolling5d': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-07-23_rolling5d.json', 'window_role': 'rolling_confirmation', 'window_policy': 'rolling5d', 'status': 'pass', 'parent_bucket_count': 26, 'selected_parent_level': 'L2_default', 'parent_granularity_status': 'too_broad', 'absorbed_child_count': 69, 'absorbed_sample_count': 1025, 'child_conflict_warning_count': 0, 'positive_parent_count': 1, 'positive_parent_sample_ready_count': 0, 'positive_parent_conflict_count': 0, 'top_sample_ready_positive_parent_buckets': [], 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'parsed'}, 'rolling10d': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-07-23_rolling10d.json', 'window_role': 'rolling_confirmation', 'window_policy': 'rolling10d', 'status': 'pass', 'parent_bucket_count': 41, 'selected_parent_level': 'L2_default', 'parent_granularity_status': 'target_pass', 'absorbed_child_count': 105, 'absorbed_sample_count': 2901, 'child_conflict_warning_count': 1, 'positive_parent_count': 2, 'positive_parent_sample_ready_count': 0, 'positive_parent_conflict_count': 1, 'top_sample_ready_positive_parent_buckets': [], 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'parsed'}, 'mtd': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-07-23_mtd.json', 'window_role': 'promotion_confirmation', 'window_policy': 'mtd', 'status': 'pass', 'parent_bucket_count': 44, 'selected_parent_level': 'L1_broad', 'parent_granularity_status': 'target_pass', 'absorbed_child_count': 325, 'absorbed_sample_count': 33274, 'child_conflict_warning_count': 13, 'positive_parent_count': 8, 'positive_parent_sample_ready_count': 1, 'positive_parent_conflict_count': 2, 'top_sample_ready_positive_parent_buckets': [{'parent_bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_mid_recovery|submit_quality_parent=submit_missing|exit_outcome_parent=exit_missing', 'parent_ev_pct': 1.681989, 'parent_joined_sample': 57, 'complete_flow_count': 0, 'parent_granularity_floor_passed': True, 'child_conflict_warning': True, 'entry_score_parent': 'score_mid_recovery', 'entry_source_parent': 'entry_source_wait6579', 'submit_quality_parent': 'submit_missing', 'exit_outcome_parent': 'exit_missing', 'major_holding_parent': 'holding_missing', 'scale_in_parent': 'scale_in_none'}], 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'parsed'}}`

## Lifecycle AI Context
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_ai_context/lifecycle_ai_context_2026-07-23.json`
- context_version: `lifecycle_ai_context_v1_2026-07-23` / authority: `ai_advisory_prompt_context_only`
- prompt_stage_count: `3` / runtime_effect: `False`
- stage_contexts: `[{'stage': 'entry', 'prompt_injection_allowed': True, 'policy_key': 'entry:weighted_adm_v1', 'alignment_hint': 'NO_CHANGE', 'context_contribution_score': -0.3435, 'attribution_quality_status': 'observational_only_pending_outcome'}, {'stage': 'submit', 'prompt_injection_allowed': False, 'policy_key': 'submit:weighted_adm_v1', 'alignment_hint': 'NO_CHANGE', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'holding', 'prompt_injection_allowed': True, 'policy_key': 'holding:weighted_adm_v1', 'alignment_hint': 'NO_CHANGE', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'scale_in', 'prompt_injection_allowed': False, 'policy_key': 'scale_in:weighted_adm_v1', 'alignment_hint': 'NO_CHANGE', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'exit', 'prompt_injection_allowed': True, 'policy_key': 'exit:weighted_adm_v1', 'alignment_hint': 'EXIT', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}]`

## Lifecycle AI Context Attribution
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_ai_context_attribution/lifecycle_ai_context_attribution_2026-07-23.json`
- eligible/applied/skipped: `108` / `108` / `0`
- replay_budget: `30`
- implementation_status: `implemented`
- stage_attribution: `{'entry': {'context_contribution_score': -0.3435, 'bounded_auxiliary_weight': -0.0515, 'attribution_quality_status': 'observational_only_pending_outcome', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': 0.0093, 'no_context_replay_observed': 0}, 'submit': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'holding': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'scale_in': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'exit': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}}`

## Institutional Flow Context
- artifact: `/home/ubuntu/KORStockScan/data/report/institutional_flow_context/institutional_flow_context_2026-07-23.json`
- status: `pass` / authority: `source_only_lifecycle_feature`
- rows ok/partial/missing/token_error: `120` / `0` / `0` / `0`
- join_rate_pct: `100.0`
- source_mix: `{'ka10059+ka10061': 120}`
- top_net_buy: `[{'stock_code': '005930', 'smart_money_net': 2172475, 'foreign_net_roll5': 8616883, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}, {'stock_code': '096770', 'smart_money_net': 1133187, 'foreign_net_roll5': 368129, 'inst_net_roll5': 1756925, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '073240', 'smart_money_net': 897518, 'foreign_net_roll5': 2171246, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}, {'stock_code': '035420', 'smart_money_net': 514683, 'foreign_net_roll5': 99994, 'inst_net_roll5': 938962, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '119850', 'smart_money_net': 198610, 'foreign_net_roll5': 177174, 'inst_net_roll5': 518127, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '102940', 'smart_money_net': 187109, 'foreign_net_roll5': 263125, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}, {'stock_code': '010120', 'smart_money_net': 183719, 'foreign_net_roll5': 131273, 'inst_net_roll5': 134033, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '476060', 'smart_money_net': 172326, 'foreign_net_roll5': 0, 'inst_net_roll5': 0, 'regime': 'UNKNOWN'}, {'stock_code': '002020', 'smart_money_net': 158156, 'foreign_net_roll5': 357898, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}, {'stock_code': '089890', 'smart_money_net': 149543, 'foreign_net_roll5': 76271, 'inst_net_roll5': 273833, 'regime': 'DUAL_ACCUMULATION'}]`

## Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-07-23.json`
- fresh: gemini=`False` claude=`True`
- consensus/orders/family_candidates: `0` / `10` / `0`

## Swing Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_2026-07-23.json`
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
- artifact: `/home/ubuntu/KORStockScan/data/report/swing_strategy_discovery_ev/swing_strategy_discovery_ev_2026-07-23.json`
- authority: `swing_sim_exploration_only` / source_only: `True`
- candidate/arm/policy_exit_rows: `2876` / `19214` / `19214`
- labeled/pending_future_quotes: `3385` / `6665`
- implementation_status: `implemented`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- surviving/avoid_bucket_count: `1` / `20`
- runtime_effect: `False`

## Pipeline Event Verbosity
- artifact: `/home/ubuntu/KORStockScan/data/report/pipeline_event_verbosity/pipeline_event_verbosity_2026-07-23.json`
- state: `v2_shadow_pending_flush`
- recommended_workorder_state: `observe_pending_next_flush`
- high_volume_line_count: `337`
- high_volume_byte_share_pct: `0.27`
- parity_ok: `False`
- suppress_eligibility: `False`

## Codebase Performance Workorder Source
- artifact: `/home/ubuntu/KORStockScan/data/report/codebase_performance_workorder/codebase_performance_workorder_2026-07-23.json`
- authority: `ops_performance_workorder_source`
- accepted/deferred/rejected: `8` / `2` / `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`

## Pattern Lab Audits
- currentness: status=`pass` fail=`0` orders=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-07-23.json`
- ai_review: status=`pass` orders=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_ai_review/pattern_lab_ai_review_2026-07-23.json`
- time_window_regime_counterfactual: status=`pass` artifact=`/home/ubuntu/KORStockScan/data/report/time_window_regime_counterfactual/time_window_regime_counterfactual_2026-07-23.json`
- producer_gap_discovery: status=`pass` orders=`0` artifact=`/home/ubuntu/KORStockScan/data/report/producer_gap_discovery/producer_gap_discovery_2026-07-23.json`
- stage_hook_workorder_discovery: status=`warning` orders=`2` artifact=`/home/ubuntu/KORStockScan/data/report/stage_hook_workorder_discovery/stage_hook_workorder_discovery_2026-07-23.json`
- propagation: status=`warning` fail=`0` warnings=`2` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_2026-07-23.json`

## Swing Runtime Approval
- request_report: `/home/ubuntu/KORStockScan/data/report/swing_runtime_approval/swing_runtime_approval_2026-07-22.json`
- approval_artifact: `-`
- requested/approved/live_dry_run: `0` / `0` / `0`
- dry_run_forced: `False`
- legacy_phase0_real_canary_ignored: `False`
- blocked: `[]`

## Code Improvement Workorder
- artifact: `/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-23.json`
- markdown: `/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-07-23.md`
- selected_order_count: `171`
- decision_counts: `{'attach_existing_family': 201, 'design_family_candidate': 3, 'defer_evidence': 3, 'reject': 3}`

## Approval Requests
- none

## Swing Approval Requests
- none

## Calibration Decisions
## Code Improvement Top Orders
- `order_latency_canary_tag_완화_1축_canary_승인` decision=`attach_existing_family` subsystem=`runtime_instrumentation`
- `order_lifecycle_bucket_discovery_source_contract_source_contract_source_added_entry_6d966faa56` decision=`attach_existing_family` subsystem=`lifecycle_bucket_discovery_taxonomy_provenance`
- `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_10_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_2ad7fdfe` decision=`attach_existing_family` subsystem=`lifecycle_decision_matrix`

- `soft_stop_whipsaw_confirmation`: `adjust_up` sample=`182/10`
- `holding_flow_ofi_smoothing`: `hold_sample` sample=`6/20`
- `protect_trailing_smoothing`: `adjust_down` sample=`100/20`
- `trailing_continuation`: `freeze` sample=`455/20`
- `market_regime_continuous_thresholds`: `hold_sample` sample=`9/10`
- `pre_submit_price_guard`: `hold` sample=`0/1`
- `dynamic_entry_price_resolver`: `hold_sample` sample=`36/20`
- `entry_split_order_plan`: `adjust_up` sample=`410/20`
- `scale_in_split_order_plan`: `adjust_up` sample=`7/0`
- `entry_price_execution_quality`: `hold` sample=`26/5`
- `score65_74_recovery_probe`: `hold_sample` sample=`7/20`
- `strength_momentum_soft_gate_p1`: `hold` sample=`440/20`
- `overbought_pullback_guard_p1`: `hold_sample` sample=`0/20`
- `liquidity_pre_submit_guard_p1`: `hold` sample=`22/20`
- `bad_entry_refined_canary`: `adjust_up` sample=`11594/10`
- `holding_exit_decision_matrix_advisory`: `hold_no_edge` sample=`0/1`
- `lifecycle_decision_matrix_runtime`: `adjust_up` sample=`353/20`
- `scale_in_price_guard`: `hold` sample=`32/20`
- `position_sizing_dynamic_formula`: `hold_sample` sample=`75/30`

## Warnings
- `trade_review_missing`
- `performance_tuning_missing`
- `scalp_entry_adm:joined_sample_below_sample_floor`
- `scalp_entry_adm:unknown_bucket_source_quality_gap`
- `lifecycle_bucket_discovery:source_contract_drift_warning`
- `lifecycle_bucket_discovery:source_contract_drift_warning`
- `swing_strategy_discovery:pending_future_quotes`
- `swing_strategy_discovery:clean_tuning_baseline_swing_discovery_lookback_filtered`
- `swing_lifecycle_decision_matrix:swing_intraday_live_equiv_probe_missing`
- `swing_lifecycle_decision_matrix:pending_future_quotes`
- `swing_lifecycle_decision_matrix:clean_tuning_baseline_swing_discovery_lookback_filtered`
- `pattern_lab_propagation_audit_warning`
