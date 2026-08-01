# Threshold Cycle Daily EV Report - 2026-07-31

## Summary
- status: `warning`
- warning_count: `3`
- warning_contract active/disabled/raw: `3` / `9` / `13`
- source_quality: status=`warning` allowed=`True`
- samples real/sim: `5` / `12`
- live_auto_ready_count: `0`
- primary_verdict: `real_primary_evidence_present`

## Runtime Apply
- status: `auto_bounded_live_ready`
- runtime_change: `True`
- selected_families: `soft_stop_whipsaw_confirmation, entry_split_order_plan, scale_in_split_order_plan, score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, profit_stagnation_exit_runtime, latency_spread_relief_real_operator_override, quote_consistency_normalization, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, ai_watching_score_smoothing_report_only, holding_decision_context_v1, weak_pullback_entry_block_runtime, early_accel_recheck_runtime, real_pyramid_scale_in_quality_guard_runtime, sell_side_open_time_block_runtime, pre_submit_liquidity_relief_runtime, entry_opportunity_recheck_runtime, weak_context_late_entry_guard_runtime, rising_missed_normal_buy_bridge, persistent_operator_overrides_2026_06_26`

## Daily EV
- completed: `5` / open: `2`
- win/loss: `5` / `0` (`100.0`%)
- avg_profit_rate: `0.56`%
- realized_pnl_krw: `96087`
- full_fill_completed_avg_profit_rate: `0.0`%

## Entry Funnel
- budget_pass_to_submitted: `4` / `179` (`2.23`%)
- latency pass/block: `24` / `115`
- latency submit routing: `latency_classifier_runtime_semantics_gap`
- latency recommended action: `reject` (`recovery_count=0 below floor=19`)
- latency profile generation: `{'mode': 'grid_quantile_search', 'profile_count': 720, 'age_cap_ms': 1500, 'jitter_cap_ms': 1500, 'spread_cap_ratio': 0.012, 'counterfactual_sample_floor': 3, 'recovery_event_floor_ratio': 0.1}`
- safe/caution_normal/recovery: `0` / `0` / `0`
- recovery attempts/cf sample/cf ev: `0` / `0` / `None`%
- recovered/lost labels: `0` / `0`
- stale/broker override excluded: `0` / `0`
- full/partial fill: `0` / `4`
- entry_split_order_plan: status=`pass` candidates=`1` policy=`entry_split_order_plan:2026-07-31:9adfdbe8d9`
- scale_in_split_order_plan: status=`pass` candidates=`1` policy=`scale_in_split_order_plan:2026-07-31:c91179494131`

## Holding Exit
- holding_reviews: `115`
- exit_signals: `6`
- holding_review_ms_p95: `4156.0`

## Scalp Simulator
- authority: `equal_weight` / fill_policy: `signal_inclusive_best_ask_v1`
- armed/filled/sold: `5` / `5` / `3`
- expired/unpriced/duplicate: `0` / `0` / `0`
- entry_ai_price applied/skip: `5` / `92`
- submit_revalidation warning/block: `0` / `0`
- scale_in filled/unfilled: `0` / `0`
- overnight decision/sell/hold/carry_restored: `0` / `0` / `0` / `0`
- completed_profit_summary: `{'sample': 3, 'win_count': 0, 'loss_count': 2, 'avg_profit_rate': -1.83, 'median_profit_rate': -1.44, 'downside_p10_profit_rate': -4.05, 'upside_p90_profit_rate': -0.0, 'win_rate': 0.0, 'loss_rate': 0.6667, 'stddev_profit_rate': 2.053}`
- post_sell_join: joined=`3` / pending=`0`
- post_sell_mfe_mae_10m: mfe=`1.15`% / mae=`-8.8973`% / close=`0.758`%

## Missed Probe Counterfactual
- book: `scalp_score65_74_probe_counterfactual` / role: `missed_buy_probe_counterfactual`
- total/score65_74: `32` / `0`
- avg_expected_ev: `3.0594`% / score65_74_avg_expected_ev: `0.0`%
- actual_order_submitted: `False` / broker_order_forbidden: `True`
- authority: `missed_probe_ev_only_not_broker_execution`

## Scalp Entry ADM
- artifact: `/home/ubuntu/KORStockScan/data/report/scalp_entry_action_decision_matrix/scalp_entry_action_decision_matrix_2026-07-31.json`
- status: `warning` / authority: `entry_advisory_prompt_context_only`
- total/joined/floor: `645` / `3` / `20`
- prompt_applied_count: `245`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 645}`
- forced_action_counts: `{'-': 645}`
- missing_actions: `[]`
- zero_sample_actions: `['BUY_NOW', 'SKIP_SOURCE_QUALITY']`
- outcome_join_diagnostic: `{'status': 'joined', 'zero_join_reason': '', 'candidate_key_count': 729, 'candidate_key_field_counts': {'candidate_id': 645, 'entry_adm_candidate_id': 0, 'sim_record_id': 75, 'record_id': 227}, 'post_sell_evaluation_rows': 3, 'post_sell_evaluation_join_keys': 6, 'sim_outcome_eligible_rows': 75, 'sim_outcome_eligible_key_count': 150, 'sim_eligible_joined_sample': 3, 'sim_eligible_outcome_coverage_rate': 0.04, 'matched_post_sell_evaluation_rows': 3, 'post_sell_evaluation_match_rate': 1.0, 'coverage_state': 'source_outcome_underproduction', 'coverage_reason': 'sim_post_sell_evaluation_underproduction', 'candidate_post_sell_key_overlap_count': 3, 'joined_sample': 3, 'joined_sample_all_rows': 3, 'sample_floor': 20, 'sample_floor_met': False, 'decision_authority': 'source_quality_gap_discovery', 'runtime_effect': False, 'allowed_runtime_apply': False}`
- top_actions: `[{'action': 'WAIT_REQUOTE', 'sample_count': 181, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'SKIP_STALE', 'sample_count': 2, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'BUY_DEFENSIVE', 'sample_count': 28, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'NO_BUY_AI', 'sample_count': 358, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'SKIP_PRE_SUBMIT_SAFETY', 'sample_count': 76, 'joined_sample': 3, 'source_quality_adjusted_ev_pct': -0.0722}]`

## Lifecycle Decision Matrix
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-07-31.json`
- status: `pass` / version: `lifecycle_decision_matrix_v1_2026-07-31`
- total/joined: `1169` / `421`
- policy_pass/promote_ready: `1` / `0`
- lifecycle_flow buckets/complete/runtime/workorders: `40` / `3` / `0` / `20`
- holding/exit buckets: `9` / `18`
- holding/exit workorders: `3` / `2`
- lifecycle identity missing/join_rate: `0` / `1.0`
- lifecycle complete_flow_rate: `0.0041`
- incomplete_flow_reason_counts: `{'missing_submit': 693, 'missing_holding': 733, 'missing_exit': 638, 'missing_entry': 513, 'candidate_id_only': 511, 'scale_in_noise_only': 414, 'postclose_exit_without_entry': 97}`
- fixed_threshold_roles: `{'hard_safety': ['broker_submit_guard', 'stale_quote_submit_block', 'price_freshness_guard', 'hard_stop', 'protect_stop', 'emergency_stop', 'account_order_cooldown_qty_guard'], 'baseline_prior': ['BUY_SCORE_THRESHOLD', 'VPW_MIN_SCORE', 'strength_momentum_cutoff', 'entry_score_cutoff'], 'bounded_tunable': ['SCALP_ENTRY_LATENCY_MAX_WS_AGE_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_WS_JITTER_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_SPREAD_RATIO_FOR_CAUTION', 'score65_74_recovery_probe', 'soft_stop_whipsaw_confirmation', 'holding_flow_override', 'scale_in_price_guard'], 'legacy_archive': ['fallback_scout_main', 'fallback_single', 'latency_fallback_split_entry', 'legacy_latency_composite', 'closed_shadow_axes']}`
- policy_entries: `[{'stage': 'entry', 'sample': 605, 'joined_sample': 3, 'stage_ev_composite_pct': -1.0359, 'confidence': 0.0015, 'selected_action': 'WAIT_REQUOTE', 'source_quality_gate': 'hold_sample', 'promote_ready': False}, {'stage': 'submit', 'sample': 45, 'joined_sample': 3, 'stage_ev_composite_pct': -1.0359, 'confidence': 0.02, 'selected_action': 'NO_CHANGE', 'source_quality_gate': 'hold_sample', 'promote_ready': False}, {'stage': 'holding', 'sample': 5, 'joined_sample': 3, 'stage_ev_composite_pct': -1.4428, 'confidence': 0.18, 'selected_action': 'EXIT', 'source_quality_gate': 'hold_sample', 'promote_ready': False}, {'stage': 'scale_in', 'sample': 414, 'joined_sample': 409, 'stage_ev_composite_pct': -0.9752, 'confidence': 1.0, 'selected_action': 'NO_CHANGE', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'exit', 'sample': 100, 'joined_sample': 3, 'stage_ev_composite_pct': -1.4428, 'confidence': 0.009, 'selected_action': 'EXIT', 'source_quality_gate': 'hold_sample', 'promote_ready': False}]`

## Lifecycle Bucket Discovery
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-07-31.json`
- status: `pass` / human_intervention_required: `False`
- candidates/surfaced: `324` / `52`
- sim_auto/live_auto/new_bucket: `0` / `0` / `10`
- role/window: `new_pattern_detection` / `same_day_source_bundle_plus_rolling_threshold_cycle_consumer`
- parent_count/granularity/conflict: `20` / `too_broad` / `0`
- positive_parent/sample_ready/conflict: `0` / `0` / `0`
- active_positive_seed/nonpositive_seed: `0` / `0`
- positive_sim_auto/nonpositive_sim_auto: `0` / `0`
- state_counts: `{'source_only_keep_collecting': 312, 'runtime_blocked_contract_gap': 2, 'new_bucket_candidate': 10}`
- top_surfaced: `[{'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 383, 'source_quality_adjusted_ev_pct': -1.0657}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_pyramid_', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 26, 'source_quality_adjusted_ev_pct': 0.3582}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_sim_entry_ai_price_skip_order_stale_', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'tighten_or_exclude', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': -1.1229}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_sim_entry_ai_price_skip_order_stale_', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'tighten_or_exclude', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': -0.6279}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'tighten_or_exclude', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': -2.5775}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_ai_confirmed_stale_fresh_liquidity_liquidi', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 0, 'source_quality_adjusted_ev_pct': None}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_ai_confirmed_stale_fresh_liquidity_liquidi', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 0, 'source_quality_adjusted_ev_pct': None}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_blocked_ai_score_stale_fresh_liquidity_liq', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 0, 'source_quality_adjusted_ev_pct': None}]`
- top_sample_ready_positive_parent_buckets: `[]`
- top_active_positive_seeds: `[]`
- top_positive_sim_auto_approved: `[]`
- top_nonpositive_sim_auto_approved: `[]`

## Lifecycle Bucket Windows
- promotion_window: `mtd`
- confirmation_windows: `['rolling5d', 'rolling10d']`
- windows: `{'rolling5d': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-07-31_rolling5d.json', 'window_role': 'rolling_confirmation', 'window_policy': 'rolling5d', 'status': 'pass', 'parent_bucket_count': 29, 'selected_parent_level': 'L3_detailed', 'parent_granularity_status': 'too_broad', 'absorbed_child_count': 64, 'absorbed_sample_count': 1067, 'child_conflict_warning_count': 0, 'positive_parent_count': 1, 'positive_parent_sample_ready_count': 0, 'positive_parent_conflict_count': 0, 'top_sample_ready_positive_parent_buckets': [], 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'parsed'}, 'rolling10d': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-07-31_rolling10d.json', 'window_role': 'rolling_confirmation', 'window_policy': 'rolling10d', 'status': 'pass', 'parent_bucket_count': 36, 'selected_parent_level': 'L2_default', 'parent_granularity_status': 'target_pass', 'absorbed_child_count': 98, 'absorbed_sample_count': 1823, 'child_conflict_warning_count': 0, 'positive_parent_count': 0, 'positive_parent_sample_ready_count': 0, 'positive_parent_conflict_count': 0, 'top_sample_ready_positive_parent_buckets': [], 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'parsed'}, 'mtd': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-07-31_mtd.json', 'window_role': 'promotion_confirmation', 'window_policy': 'mtd', 'status': 'pass', 'parent_bucket_count': 38, 'selected_parent_level': 'L1_broad', 'parent_granularity_status': 'target_pass', 'absorbed_child_count': 265, 'absorbed_sample_count': 13639, 'child_conflict_warning_count': 9, 'positive_parent_count': 4, 'positive_parent_sample_ready_count': 0, 'positive_parent_conflict_count': 0, 'top_sample_ready_positive_parent_buckets': [], 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'parsed'}}`

## Lifecycle AI Context
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_ai_context/lifecycle_ai_context_2026-07-31.json`
- context_version: `lifecycle_ai_context_v1_2026-07-31` / authority: `ai_advisory_prompt_context_only`
- prompt_stage_count: `3` / runtime_effect: `False`
- stage_contexts: `[{'stage': 'entry', 'prompt_injection_allowed': True, 'policy_key': 'entry:weighted_adm_v1', 'alignment_hint': 'WAIT_REQUOTE', 'context_contribution_score': -0.3448, 'attribution_quality_status': 'observational_only_pending_outcome'}, {'stage': 'submit', 'prompt_injection_allowed': False, 'policy_key': 'submit:weighted_adm_v1', 'alignment_hint': 'NO_CHANGE', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'holding', 'prompt_injection_allowed': True, 'policy_key': 'holding:weighted_adm_v1', 'alignment_hint': 'EXIT', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'scale_in', 'prompt_injection_allowed': False, 'policy_key': 'scale_in:weighted_adm_v1', 'alignment_hint': 'NO_CHANGE', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'exit', 'prompt_injection_allowed': True, 'policy_key': 'exit:weighted_adm_v1', 'alignment_hint': 'EXIT', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}]`

## Lifecycle AI Context Attribution
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_ai_context_attribution/lifecycle_ai_context_attribution_2026-07-31.json`
- eligible/applied/skipped: `538` / `538` / `0`
- replay_budget: `30`
- implementation_status: `implemented`
- stage_attribution: `{'entry': {'context_contribution_score': -0.3448, 'bounded_auxiliary_weight': -0.0517, 'attribution_quality_status': 'observational_only_pending_outcome', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': 0.0074, 'no_context_replay_observed': 0}, 'submit': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'holding': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'scale_in': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'exit': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}}`

## Institutional Flow Context
- artifact: `/home/ubuntu/KORStockScan/data/report/institutional_flow_context/institutional_flow_context_2026-07-31.json`
- status: `pass` / authority: `source_only_lifecycle_feature`
- rows ok/partial/missing/token_error: `120` / `0` / `0` / `0`
- join_rate_pct: `100.0`
- source_mix: `{'ka10059+ka10061': 120}`
- top_net_buy: `[{'stock_code': '005930', 'smart_money_net': 12544639, 'foreign_net_roll5': 0, 'inst_net_roll5': 6469526, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '073240', 'smart_money_net': 3921023, 'foreign_net_roll5': 4517484, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}, {'stock_code': '229200', 'smart_money_net': 3779962, 'foreign_net_roll5': 0, 'inst_net_roll5': 0, 'regime': 'UNKNOWN'}, {'stock_code': '000660', 'smart_money_net': 2981284, 'foreign_net_roll5': 0, 'inst_net_roll5': 1262583, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '396500', 'smart_money_net': 1196292, 'foreign_net_roll5': 0, 'inst_net_roll5': 82782, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '047040', 'smart_money_net': 745604, 'foreign_net_roll5': 1183932, 'inst_net_roll5': 4646, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '042700', 'smart_money_net': 576278, 'foreign_net_roll5': 843188, 'inst_net_roll5': 9071, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '226490', 'smart_money_net': 397145, 'foreign_net_roll5': 8267, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}, {'stock_code': '025320', 'smart_money_net': 389236, 'foreign_net_roll5': 90235, 'inst_net_roll5': 229043, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '010120', 'smart_money_net': 385960, 'foreign_net_roll5': 22643, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}]`

## Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-07-31.json`
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
- artifact: `/home/ubuntu/KORStockScan/data/report/pipeline_event_verbosity/pipeline_event_verbosity_2026-07-31.json`
- state: `v2_shadow_partial_coverage`
- recommended_workorder_state: `observe_next_full_coverage_day`
- high_volume_line_count: `364634`
- high_volume_byte_share_pct: `90.26`
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
- currentness: status=`pass` fail=`0` orders=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-07-31.json`
- ai_review: status=`pass` orders=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_ai_review/pattern_lab_ai_review_2026-07-31.json`
- time_window_regime_counterfactual: status=`missing` artifact=`-`
- producer_gap_discovery: status=`missing` orders=`0` artifact=`-`
- stage_hook_workorder_discovery: status=`missing` orders=`0` artifact=`-`
- propagation: status=`pass` fail=`0` warnings=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_2026-07-31.json`

## Swing Runtime Approval
- request_report: `-`
- approval_artifact: `-`
- requested/approved/live_dry_run: `0` / `0` / `0`
- dry_run_forced: `False`
- legacy_phase0_real_canary_ignored: `False`
- blocked: `[]`

## Code Improvement Workorder
- artifact: `/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-31.json`
- markdown: `/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-07-31.md`
- selected_order_count: `78`
- decision_counts: `{'attach_existing_family': 91, 'design_family_candidate': 3, 'defer_evidence': 1, 'reject': 1}`

## Approval Requests
- none

## Swing Approval Requests
- none

## Calibration Decisions
## Code Improvement Top Orders
- `order_entry_submit_drought_auto_resolution` decision=`attach_existing_family` subsystem=`runtime_instrumentation`
- `order_conversion_lane_submit_drought_submit_drought_broker_receipt` decision=`attach_existing_family` subsystem=`sim_to_real_conversion_lineage`
- `order_entry_broker_receipt_contract_gap_review` decision=`attach_existing_family` subsystem=`runtime_instrumentation`

- `soft_stop_whipsaw_confirmation`: `adjust_up` sample=`476/10`
- `holding_flow_ofi_smoothing`: `hold_sample` sample=`1/20`
- `protect_trailing_smoothing`: `hold` sample=`117/20`
- `trailing_continuation`: `freeze` sample=`522/20`
- `market_regime_continuous_thresholds`: `hold_sample` sample=`9/10`
- `pre_submit_price_guard`: `hold` sample=`0/1`
- `dynamic_entry_price_resolver`: `hold_sample` sample=`107/20`
- `entry_split_order_plan`: `adjust_up` sample=`748/20`
- `scale_in_split_order_plan`: `adjust_up` sample=`1/0`
- `entry_price_execution_quality`: `hold` sample=`10/5`
- `score65_74_recovery_probe`: `adjust_up` sample=`98/20`
- `strength_momentum_soft_gate_p1`: `hold` sample=`2852/20`
- `overbought_pullback_guard_p1`: `hold` sample=`1721/20`
- `liquidity_pre_submit_guard_p1`: `hold` sample=`316/20`
- `bad_entry_refined_canary`: `adjust_up` sample=`5471/10`
- `holding_exit_decision_matrix_advisory`: `hold_no_edge` sample=`13/1`
- `lifecycle_decision_matrix_runtime`: `adjust_up` sample=`1169/20`
- `scale_in_price_guard`: `hold_sample` sample=`5/20`
- `position_sizing_dynamic_formula`: `hold_sample` sample=`59/30`
- `scalping_avg_down_recovery_quality_gate`: `hold_no_edge` sample=`44/rolling_shallow_primary>=10 and rolling_deep_primary>=5`

## Warnings
- `scalp_entry_adm:joined_sample_below_sample_floor`
- `scalp_entry_adm:sim_post_sell_outcome_source_below_sample_floor`
- `lifecycle_bucket_discovery:source_contract_drift_warning`
