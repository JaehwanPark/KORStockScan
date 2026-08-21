# Threshold Cycle Daily EV Report - 2026-08-21

## Summary
- status: `warning`
- warning_count: `5`
- warning_contract active/disabled/raw: `5` / `9` / `14`
- source_quality: status=`pass` allowed=`True`
- samples real/sim: `14` / `10`
- live_auto_ready_count: `0`
- primary_verdict: `real_primary_evidence_present`

## Runtime Apply
- status: `auto_bounded_live_ready`
- runtime_change: `True`
- selected_families: `entry_split_order_plan, score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, profit_stagnation_exit_runtime, latency_spread_relief_real_operator_override, quote_consistency_normalization, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, holding_decision_context_v1, weak_pullback_entry_block_runtime, early_accel_recheck_runtime, real_pyramid_scale_in_quality_guard_runtime, sell_side_open_time_block_runtime, pre_submit_liquidity_relief_runtime, entry_opportunity_recheck_runtime, weak_context_late_entry_guard_runtime, rising_missed_normal_buy_bridge, persistent_operator_overrides_2026_06_26`

## Daily EV
- completed: `14` / open: `0`
- win/loss: `8` / `6` (`57.14`%)
- avg_profit_rate: `-0.1866`%
- realized_pnl_krw: `-378`
- full_fill_completed_avg_profit_rate: `-3.71`%

## Entry Funnel
- budget_pass_to_submitted: `18` / `767` (`2.35`%)
- latency pass/block: `94` / `561`
- latency submit routing: `latency_classifier_runtime_semantics_gap`
- latency recommended action: `reject` (`recovery_count=0 below floor=63`)
- latency profile generation: `{'mode': 'grid_quantile_search', 'profile_count': 810, 'age_cap_ms': 1500, 'jitter_cap_ms': 1500, 'spread_cap_ratio': 0.012, 'counterfactual_sample_floor': 3, 'recovery_event_floor_ratio': 0.1}`
- safe/caution_normal/recovery: `0` / `0` / `0`
- recovery attempts/cf sample/cf ev: `0` / `0` / `None`%
- recovered/lost labels: `0` / `0`
- stale/broker override excluded: `0` / `0`
- full/partial fill: `2` / `11`
- entry_split_order_plan: status=`pass` candidates=`1` policy=`entry_split_order_plan:2026-08-21:d01391fe91`
- scale_in_split_order_plan: status=`pass` candidates=`2` policy=`scale_in_split_order_plan:2026-08-21:ba01b82f1996`

## Holding Exit
- holding_reviews: `717`
- exit_signals: `265`
- holding_review_ms_p95: `4381.0`

## Scalp Simulator
- authority: `equal_weight` / fill_policy: `signal_inclusive_best_ask_v1`
- armed/filled/sold: `14` / `14` / `10`
- expired/unpriced/duplicate: `0` / `0` / `11`
- entry_ai_price applied/skip: `14` / `9`
- submit_revalidation warning/block: `2` / `2`
- scale_in filled/unfilled: `0` / `0`
- overnight decision/sell/hold/carry_restored: `0` / `0` / `0` / `0`
- completed_profit_summary: `{'sample': 10, 'win_count': 6, 'loss_count': 4, 'avg_profit_rate': -1.194, 'median_profit_rate': 0.13, 'downside_p10_profit_rate': -4.2, 'upside_p90_profit_rate': 0.61, 'win_rate': 0.6, 'loss_rate': 0.4, 'stddev_profit_rate': 2.1265}`
- post_sell_join: joined=`10` / pending=`0`
- post_sell_mfe_mae_10m: mfe=`1.3349`% / mae=`-8.6824`% / close=`-0.3287`%

## Missed Probe Counterfactual
- book: `scalp_score65_74_probe_counterfactual` / role: `missed_buy_probe_counterfactual`
- total/score65_74: `30` / `0`
- avg_expected_ev: `4.1752`% / score65_74_avg_expected_ev: `0.0`%
- actual_order_submitted: `False` / broker_order_forbidden: `True`
- authority: `missed_probe_ev_only_not_broker_execution`

## Scalp Entry ADM
- artifact: `/home/ubuntu/KORStockScan/data/report/scalp_entry_action_decision_matrix/scalp_entry_action_decision_matrix_2026-08-21.json`
- status: `warning` / authority: `entry_advisory_prompt_context_only`
- total/joined/floor: `772` / `10` / `20`
- prompt_applied_count: `254`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 772}`
- forced_action_counts: `{'-': 772}`
- missing_actions: `[]`
- zero_sample_actions: `[]`
- outcome_join_diagnostic: `{'status': 'joined', 'zero_join_reason': '', 'candidate_key_count': 798, 'candidate_key_field_counts': {'candidate_id': 772, 'entry_adm_candidate_id': 0, 'sim_record_id': 14, 'record_id': 177}, 'post_sell_evaluation_rows': 10, 'post_sell_evaluation_join_keys': 20, 'sim_outcome_eligible_rows': 14, 'sim_outcome_eligible_key_count': 28, 'sim_eligible_joined_sample': 5, 'sim_eligible_outcome_coverage_rate': 0.3571, 'matched_post_sell_evaluation_rows': 10, 'post_sell_evaluation_match_rate': 1.0, 'coverage_state': 'source_outcome_underproduction', 'coverage_reason': 'sim_post_sell_evaluation_underproduction', 'candidate_post_sell_key_overlap_count': 15, 'joined_sample': 10, 'joined_sample_all_rows': 10, 'sample_floor': 20, 'sample_floor_met': False, 'decision_authority': 'source_quality_gap_discovery', 'runtime_effect': False, 'allowed_runtime_apply': False}`
- top_actions: `[{'action': 'BUY_NOW', 'sample_count': 2, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'WAIT_REQUOTE', 'sample_count': 392, 'joined_sample': 1, 'source_quality_adjusted_ev_pct': 0.0008}, {'action': 'SKIP_STALE', 'sample_count': 3, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'BUY_DEFENSIVE', 'sample_count': 81, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'NO_BUY_AI', 'sample_count': 276, 'joined_sample': 4, 'source_quality_adjusted_ev_pct': -0.0247}]`

## Lifecycle Decision Matrix
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-08-21.json`
- status: `pass` / version: `lifecycle_decision_matrix_v1_2026-08-21`
- total/joined: `2626` / `663`
- policy_pass/promote_ready: `3` / `0`
- lifecycle_flow buckets/complete/runtime/workorders: `44` / `11` / `0` / `20`
- holding/exit buckets: `14` / `26`
- holding/exit workorders: `6` / `10`
- lifecycle identity missing/join_rate: `0` / `1.0`
- lifecycle complete_flow_rate: `0.0055`
- incomplete_flow_reason_counts: `{'missing_holding': 1975, 'missing_exit': 804, 'missing_submit': 1897, 'missing_entry': 1794, 'candidate_id_only': 1808, 'scale_in_noise_only': 621, 'sim_record_id_only': 2, 'postclose_exit_without_entry': 1172}`
- fixed_threshold_roles: `{'hard_safety': ['broker_submit_guard', 'stale_quote_submit_block', 'price_freshness_guard', 'hard_stop', 'protect_stop', 'emergency_stop', 'account_order_cooldown_qty_guard'], 'baseline_prior': ['BUY_SCORE_THRESHOLD', 'VPW_MIN_SCORE', 'strength_momentum_cutoff', 'entry_score_cutoff'], 'bounded_tunable': ['SCALP_ENTRY_LATENCY_MAX_WS_AGE_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_WS_JITTER_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_SPREAD_RATIO_FOR_CAUTION', 'score65_74_recovery_probe', 'soft_stop_whipsaw_confirmation', 'holding_flow_override', 'scale_in_price_guard'], 'legacy_archive': ['fallback_scout_main', 'fallback_single', 'latency_fallback_split_entry', 'legacy_latency_composite', 'closed_shadow_axes']}`
- policy_entries: `[{'stage': 'entry', 'sample': 705, 'joined_sample': 5, 'stage_ev_composite_pct': -0.4734, 'confidence': 0.0035, 'selected_action': 'WAIT_REQUOTE', 'source_quality_gate': 'hold_sample', 'promote_ready': False}, {'stage': 'submit', 'sample': 94, 'joined_sample': 10, 'stage_ev_composite_pct': -1.4226, 'confidence': 0.1064, 'selected_action': 'NO_CHANGE', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'holding', 'sample': 14, 'joined_sample': 10, 'stage_ev_composite_pct': -1.3495, 'confidence': 0.7143, 'selected_action': 'EXIT', 'source_quality_gate': 'hold_sample', 'promote_ready': False}, {'stage': 'scale_in', 'sample': 621, 'joined_sample': 618, 'stage_ev_composite_pct': -0.7445, 'confidence': 1.0, 'selected_action': 'NO_CHANGE', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'exit', 'sample': 1192, 'joined_sample': 20, 'stage_ev_composite_pct': -1.0983, 'confidence': 0.0336, 'selected_action': 'EXIT', 'source_quality_gate': 'pass', 'promote_ready': False}]`

## Lifecycle Bucket Discovery
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-08-21.json`
- status: `pass` / human_intervention_required: `False`
- candidates/surfaced: `341` / `44`
- sim_auto/live_auto/new_bucket: `0` / `0` / `0`
- role/window: `new_pattern_detection` / `same_day_source_bundle_plus_rolling_threshold_cycle_consumer`
- parent_count/granularity/conflict: `22` / `too_broad` / `0`
- positive_parent/sample_ready/conflict: `2` / `0` / `0`
- active_positive_seed/nonpositive_seed: `0` / `0`
- positive_sim_auto/nonpositive_sim_auto: `2` / `0`
- state_counts: `{'source_only_keep_collecting': 339, 'lifecycle_flow_sim_probe_candidate': 2}`
- top_surfaced: `[{'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 503, 'source_quality_adjusted_ev_pct': -0.9886}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_pyramid_', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 115, 'source_quality_adjusted_ev_pct': 0.3231}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_f', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'tighten_or_exclude', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': -1.01}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_s', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'tighten_or_exclude', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': -0.6}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'tighten_or_exclude', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': -1.05}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'tighten_or_exclude', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': -0.8}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_watch_liquidit', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'tighten_or_exclude', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': -0.62}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'stage': 'lifecycle_flow', 'classification_state': 'lifecycle_flow_sim_probe_candidate', 'live_auto_apply_family': None, 'recommended_action': 'hold_no_edge', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': 0.0754}]`
- top_sample_ready_positive_parent_buckets: `[]`
- top_active_positive_seeds: `[]`
- top_positive_sim_auto_approved: `[{'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'classification_state': 'lifecycle_flow_sim_probe_candidate', 'stage': 'lifecycle_flow', 'bucket_type': 'combo_lifecycle_flow', 'source_quality_adjusted_ev_pct': 0.5283, 'joined_sample': 1, 'sample': 1}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'classification_state': 'lifecycle_flow_sim_probe_candidate', 'stage': 'lifecycle_flow', 'bucket_type': 'combo_lifecycle_flow', 'source_quality_adjusted_ev_pct': 0.0754, 'joined_sample': 1, 'sample': 1}]`
- top_nonpositive_sim_auto_approved: `[]`

## Lifecycle Bucket Windows
- promotion_window: `mtd`
- confirmation_windows: `['rolling5d', 'rolling10d']`
- windows: `{'rolling5d': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-08-21_rolling5d.json', 'window_role': 'rolling_confirmation', 'window_policy': 'rolling5d', 'status': 'pass', 'parent_bucket_count': 42, 'selected_parent_level': 'L2_default', 'parent_granularity_status': 'target_pass', 'absorbed_child_count': 101, 'absorbed_sample_count': 6788, 'child_conflict_warning_count': 3, 'positive_parent_count': 2, 'positive_parent_sample_ready_count': 0, 'positive_parent_conflict_count': 0, 'top_sample_ready_positive_parent_buckets': [], 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'parsed'}, 'rolling10d': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-08-21_rolling10d.json', 'window_role': 'rolling_confirmation', 'window_policy': 'rolling10d', 'status': 'pass', 'parent_bucket_count': 51, 'selected_parent_level': 'L2_default', 'parent_granularity_status': 'target_pass', 'absorbed_child_count': 133, 'absorbed_sample_count': 12524, 'child_conflict_warning_count': 3, 'positive_parent_count': 4, 'positive_parent_sample_ready_count': 0, 'positive_parent_conflict_count': 0, 'top_sample_ready_positive_parent_buckets': [], 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'parsed'}, 'mtd': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-08-21_mtd.json', 'window_role': 'promotion_confirmation', 'window_policy': 'mtd', 'status': 'pass', 'parent_bucket_count': 31, 'selected_parent_level': 'L1_broad', 'parent_granularity_status': 'target_pass', 'absorbed_child_count': 187, 'absorbed_sample_count': 17431, 'child_conflict_warning_count': 4, 'positive_parent_count': 6, 'positive_parent_sample_ready_count': 1, 'positive_parent_conflict_count': 0, 'top_sample_ready_positive_parent_buckets': [{'parent_bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_watch_recovery|submit_quality_parent=submit_missing|exit_outcome_parent=exit_missing', 'parent_ev_pct': 3.451308, 'parent_joined_sample': 59, 'complete_flow_count': 0, 'parent_granularity_floor_passed': True, 'child_conflict_warning': False, 'entry_score_parent': 'score_watch_recovery', 'entry_source_parent': 'entry_source_wait6579', 'submit_quality_parent': 'submit_missing', 'exit_outcome_parent': 'exit_missing', 'major_holding_parent': 'holding_missing', 'scale_in_parent': 'scale_in_none'}], 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'parsed'}}`

## Lifecycle AI Context
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_ai_context/lifecycle_ai_context_2026-08-21.json`
- context_version: `lifecycle_ai_context_v1_2026-08-21` / authority: `ai_advisory_prompt_context_only`
- prompt_stage_count: `3` / runtime_effect: `False`
- stage_contexts: `[{'stage': 'entry', 'prompt_injection_allowed': True, 'policy_key': 'entry:weighted_adm_v1', 'alignment_hint': 'WAIT_REQUOTE', 'context_contribution_score': 0.0241, 'attribution_quality_status': 'observational_only_pending_outcome'}, {'stage': 'submit', 'prompt_injection_allowed': False, 'policy_key': 'submit:weighted_adm_v1', 'alignment_hint': 'NO_CHANGE', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'holding', 'prompt_injection_allowed': True, 'policy_key': 'holding:weighted_adm_v1', 'alignment_hint': 'EXIT', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'scale_in', 'prompt_injection_allowed': False, 'policy_key': 'scale_in:weighted_adm_v1', 'alignment_hint': 'NO_CHANGE', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'exit', 'prompt_injection_allowed': True, 'policy_key': 'exit:weighted_adm_v1', 'alignment_hint': 'EXIT', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}]`

## Lifecycle AI Context Attribution
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_ai_context_attribution/lifecycle_ai_context_attribution_2026-08-21.json`
- eligible/applied/skipped: `348` / `348` / `0`
- replay_budget: `30`
- implementation_status: `implemented`
- stage_attribution: `{'entry': {'context_contribution_score': 0.0241, 'bounded_auxiliary_weight': 0.0036, 'attribution_quality_status': 'observational_only_pending_outcome', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': 0.5345, 'no_context_replay_observed': 0}, 'submit': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'holding': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'scale_in': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'exit': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}}`

## Institutional Flow Context
- artifact: `/home/ubuntu/KORStockScan/data/report/institutional_flow_context/institutional_flow_context_2026-08-21.json`
- status: `pass` / authority: `source_only_lifecycle_feature`
- rows ok/partial/missing/token_error: `120` / `0` / `0` / `0`
- join_rate_pct: `100.0`
- source_mix: `{'ka10059+ka10061': 120}`
- top_net_buy: `[{'stock_code': '005930', 'smart_money_net': 2785664, 'foreign_net_roll5': 8353152, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}, {'stock_code': '073240', 'smart_money_net': 714503, 'foreign_net_roll5': 916893, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}, {'stock_code': '005935', 'smart_money_net': 390771, 'foreign_net_roll5': 0, 'inst_net_roll5': 1107836, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '011200', 'smart_money_net': 339365, 'foreign_net_roll5': 570130, 'inst_net_roll5': 1919970, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '041190', 'smart_money_net': 255515, 'foreign_net_roll5': 0, 'inst_net_roll5': 85121, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '257720', 'smart_money_net': 183785, 'foreign_net_roll5': 0, 'inst_net_roll5': 1296858, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '330350', 'smart_money_net': 152207, 'foreign_net_roll5': 149238, 'inst_net_roll5': 15002, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '760028', 'smart_money_net': 146622, 'foreign_net_roll5': 0, 'inst_net_roll5': 0, 'regime': 'UNKNOWN'}, {'stock_code': '001210', 'smart_money_net': 102215, 'foreign_net_roll5': 0, 'inst_net_roll5': 10748, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '008930', 'smart_money_net': 76443, 'foreign_net_roll5': 0, 'inst_net_roll5': 243137, 'regime': 'INSTITUTION_ACCUMULATION'}]`

## Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-08-21.json`
- fresh: gemini=`False` claude=`True`
- consensus/orders/family_candidates: `0` / `10` / `0`

## Swing Pattern Lab Automation
- artifact: `-`
- deepseek_lab_available: `None`
- findings/orders: `0` / `0`
- data_quality_warnings: `0`
- top_level_data_quality_warnings: `None`
- resolved_data_quality_warnings: `None`
- ofi_qi_stale_missing_unique_records: `0`
- ofi_qi_stale_missing_reasons: `{}`
- ofi_qi_stale_missing_reason_combinations: `{}`
- ofi_qi_stale_missing_reason_combination_unique_records: `{}`
- ofi_qi_observer_unhealthy_overlap: `{}`
- source_quality_blocked_families: `[]`
- carryover_warnings: `0`
- population_split_available: `False`

## Swing Strategy Discovery Sim
- artifact: `-`
- authority: `swing_sim_exploration_only` / source_only: `None`
- candidate/arm/policy_exit_rows: `0` / `0` / `None`
- labeled/pending_future_quotes: `0` / `0`
- implementation_status: `-`
- top_surviving_arm: `-`
- surviving/avoid_bucket_count: `None` / `0`
- runtime_effect: `False`

## Pipeline Event Verbosity
- artifact: `/home/ubuntu/KORStockScan/data/report/pipeline_event_verbosity/pipeline_event_verbosity_2026-08-21.json`
- state: `v2_shadow_pending_flush`
- recommended_workorder_state: `observe_pending_next_flush`
- high_volume_line_count: `244449`
- high_volume_byte_share_pct: `64.94`
- parity_ok: `False`
- suppress_eligibility: `False`

## Codebase Performance Workorder Source
- artifact: `-`
- authority: `-`
- accepted/deferred/rejected: `0` / `0` / `0`
- runtime_effect: `False`
- strategy_effect: `None`
- data_quality_effect: `None`
- tuning_axis_effect: `None`

## Pattern Lab Audits
- currentness: status=`pass` fail=`0` orders=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-08-21.json`
- ai_review: status=`warning` orders=`1` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_ai_review/pattern_lab_ai_review_2026-08-21.json`
- time_window_regime_counterfactual: status=`missing` artifact=`-`
- producer_gap_discovery: status=`missing` orders=`0` artifact=`-`
- stage_hook_workorder_discovery: status=`missing` orders=`0` artifact=`-`
- propagation: status=`warning` fail=`0` warnings=`2` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_2026-08-21.json`

## Swing Runtime Approval
- request_report: `-`
- approval_artifact: `-`
- requested/approved/live_dry_run: `0` / `0` / `0`
- dry_run_forced: `False`
- legacy_phase0_real_canary_ignored: `False`
- blocked: `[]`

## Code Improvement Workorder
- artifact: `/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-21.json`
- markdown: `/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-08-21.md`
- selected_order_count: `53`
- decision_counts: `{'attach_existing_family': 64, 'design_family_candidate': 3, 'defer_evidence': 1, 'reject': 1}`

## Approval Requests
- none

## Swing Approval Requests
- none

## Calibration Decisions
## Code Improvement Top Orders
- `order_latency_canary_tag_완화_1축_canary_승인` decision=`attach_existing_family` subsystem=`runtime_instrumentation`
- `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_10_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_f12338ed` decision=`attach_existing_family` subsystem=`lifecycle_decision_matrix`
- `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_11_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_0d98e7ec` decision=`attach_existing_family` subsystem=`lifecycle_decision_matrix`

- `soft_stop_whipsaw_confirmation`: `hold_sample` sample=`1830/10`
- `holding_flow_ofi_smoothing`: `hold_sample` sample=`5/20`
- `protect_trailing_smoothing`: `hold_no_edge` sample=`45/20`
- `trailing_continuation`: `freeze` sample=`1956/20`
- `market_regime_continuous_thresholds`: `hold_sample` sample=`7/10`
- `pre_submit_price_guard`: `hold` sample=`0/1`
- `dynamic_entry_price_resolver`: `hold_sample` sample=`55/20`
- `entry_split_order_plan`: `adjust_up` sample=`4069/20`
- `scale_in_split_order_plan`: `hold_sample` sample=`2/3`
- `entry_price_execution_quality`: `hold` sample=`44/5`
- `score65_74_recovery_probe`: `adjust_up` sample=`125/20`
- `strength_momentum_soft_gate_p1`: `hold` sample=`6310/20`
- `overbought_pullback_guard_p1`: `hold` sample=`1881/20`
- `liquidity_pre_submit_guard_p1`: `hold` sample=`865/20`
- `bad_entry_refined_canary`: `hold_sample` sample=`13/10`
- `holding_exit_decision_matrix_advisory`: `hold_no_edge` sample=`13/1`
- `lifecycle_decision_matrix_runtime`: `adjust_up` sample=`2626/20`
- `scale_in_price_guard`: `hold_sample` sample=`2/20`
- `position_sizing_dynamic_formula`: `hold_sample` sample=`42/30`
- `scalping_avg_down_recovery_quality_gate`: `hold_no_edge` sample=`44/rolling_shallow_primary>=10 and rolling_deep_primary>=5`

## Warnings
- `scalp_entry_adm:joined_sample_below_sample_floor`
- `scalp_entry_adm:sim_post_sell_outcome_source_below_sample_floor`
- `scalp_entry_adm:unknown_bucket_source_quality_gap`
- `pattern_lab_ai_review_warning`
- `pattern_lab_propagation_audit_warning`
