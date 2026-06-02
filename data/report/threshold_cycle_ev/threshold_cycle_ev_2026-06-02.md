# Threshold Cycle Daily EV Report - 2026-06-02

## Runtime Apply
- status: `auto_bounded_live_ready`
- runtime_change: `True`
- selected_families: `score65_74_recovery_probe, bad_entry_refined_canary, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, lifecycle_decision_matrix_runtime, swing_one_share_real_canary_phase0, swing_market_regime_sensitivity`

## Daily EV
- completed: `17` / open: `0`
- win/loss: `11` / `6` (`64.71`%)
- avg_profit_rate: `-0.13`%
- realized_pnl_krw: `15688`
- full_fill_completed_avg_profit_rate: `-0.132`%

## Entry Funnel
- budget_pass_to_submitted: `22` / `27662` (`0.08`%)
- latency pass/block: `358` / `27299`
- latency submit routing: `latency_classifier_runtime_semantics_gap`
- latency recommended action: `reject` (`recovery_count=0 below floor=2729`)
- latency profile generation: `{'mode': 'grid_quantile_search', 'profile_count': 900, 'age_cap_ms': 1500, 'jitter_cap_ms': 1500, 'spread_cap_ratio': 0.012, 'counterfactual_sample_floor': 3, 'recovery_event_floor_ratio': 0.1}`
- safe/caution_normal/recovery: `0` / `0` / `0`
- recovery attempts/cf sample/cf ev: `0` / `0` / `None`%
- recovered/lost labels: `0` / `0`
- stale/broker override excluded: `0` / `0`
- full/partial fill: `20` / `3`

## Holding Exit
- holding_reviews: `4448`
- exit_signals: `379`
- holding_review_ms_p95: `2382.0`

## Scalp Simulator
- authority: `equal_weight` / fill_policy: `signal_inclusive_best_ask_v1`
- armed/filled/sold: `378` / `378` / `359`
- expired/unpriced/duplicate: `0` / `0` / `1896`
- entry_ai_price applied/skip: `110` / `0`
- submit_revalidation warning/block: `309` / `0`
- scale_in filled/unfilled: `0` / `0`
- overnight decision/sell/hold/carry_restored: `17` / `17` / `0` / `0`
- completed_profit_summary: `{'sample': 357, 'win_count': 99, 'loss_count': 258, 'avg_profit_rate': -1.2209, 'median_profit_rate': -1.92, 'downside_p10_profit_rate': -2.93, 'upside_p90_profit_rate': 1.59, 'win_rate': 0.2773, 'loss_rate': 0.7227, 'stddev_profit_rate': 1.9649}`
- post_sell_join: joined=`355` / pending=`2`
- post_sell_mfe_mae_10m: mfe=`2.1645`% / mae=`-4.5901`% / close=`0.0503`%

## Missed Probe Counterfactual
- book: `scalp_score65_74_probe_counterfactual` / role: `missed_buy_probe_counterfactual`
- total/score65_74: `138` / `7`
- avg_expected_ev: `3.5676`% / score65_74_avg_expected_ev: `0.3774`%
- actual_order_submitted: `False` / broker_order_forbidden: `True`
- authority: `missed_probe_ev_only_not_broker_execution`

## Scalp Entry ADM
- artifact: `/home/ubuntu/KORStockScan/data/report/scalp_entry_action_decision_matrix/scalp_entry_action_decision_matrix_2026-06-02.json`
- status: `pass` / authority: `entry_advisory_prompt_context_only`
- total/joined/floor: `563` / `236` / `20`
- prompt_applied_count: `195`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 563}`
- forced_action_counts: `{'-': 563}`
- missing_actions: `[]`
- zero_sample_actions: `['SKIP_STALE']`
- top_actions: `[{'action': 'BUY_NOW', 'sample_count': 11, 'joined_sample': 8, 'source_quality_adjusted_ev_pct': -0.0009}, {'action': 'WAIT_REQUOTE', 'sample_count': 7, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'BUY_DEFENSIVE', 'sample_count': 20, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'NO_BUY_AI', 'sample_count': 291, 'joined_sample': 34, 'source_quality_adjusted_ev_pct': -0.0142}, {'action': 'SKIP_SOURCE_QUALITY', 'sample_count': 6, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}]`

## Lifecycle Decision Matrix
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-06-02.json`
- status: `pass` / version: `lifecycle_decision_matrix_v1_2026-06-02`
- total/joined: `22915` / `21855`
- policy_pass/promote_ready: `5` / `1`
- lifecycle_flow buckets/complete/runtime/workorders: `132` / `113` / `0` / `20`
- holding/exit buckets: `40` / `64`
- holding/exit workorders: `10` / `10`
- lifecycle identity missing/join_rate: `0` / `1.0`
- lifecycle complete_flow_rate: `0.0053`
- incomplete_flow_reason_counts: `{'missing_entry': 20665, 'missing_holding': 21159, 'missing_exit': 20511, 'missing_submit': 21166, 'postclose_exit_without_entry': 682, 'candidate_id_only': 20776, 'sim_record_id_only': 370}`
- fixed_threshold_roles: `{'hard_safety': ['broker_submit_guard', 'stale_quote_submit_block', 'price_freshness_guard', 'hard_stop', 'protect_stop', 'emergency_stop', 'account_order_cooldown_qty_guard'], 'baseline_prior': ['BUY_SCORE_THRESHOLD', 'VPW_MIN_SCORE', 'strength_momentum_cutoff', 'entry_score_cutoff'], 'bounded_tunable': ['SCALP_ENTRY_LATENCY_MAX_WS_AGE_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_WS_JITTER_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_SPREAD_RATIO_FOR_CAUTION', 'score65_74_recovery_probe', 'soft_stop_whipsaw_confirmation', 'holding_flow_override', 'scale_in_price_guard'], 'legacy_archive': ['fallback_scout_main', 'fallback_single', 'latency_fallback_split_entry', 'legacy_latency_composite', 'closed_shadow_axes']}`
- policy_entries: `[{'stage': 'entry', 'sample': 789, 'joined_sample': 178, 'stage_ev_composite_pct': 1.7872, 'confidence': 1.0, 'selected_action': 'BUY_DEFENSIVE', 'source_quality_gate': 'pass', 'promote_ready': True}, {'stage': 'submit', 'sample': 417, 'joined_sample': 364, 'stage_ev_composite_pct': -0.3534, 'confidence': 1.0, 'selected_action': 'NO_CHANGE', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'holding', 'sample': 395, 'joined_sample': 364, 'stage_ev_composite_pct': -0.8068, 'confidence': 1.0, 'selected_action': 'EXIT', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'scale_in', 'sample': 20284, 'joined_sample': 20282, 'stage_ev_composite_pct': -0.4158, 'confidence': 1.0, 'selected_action': 'NO_CHANGE', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'exit', 'sample': 1030, 'joined_sample': 667, 'stage_ev_composite_pct': -0.9337, 'confidence': 1.0, 'selected_action': 'EXIT', 'source_quality_gate': 'pass', 'promote_ready': False}]`

## Lifecycle Bucket Discovery
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-06-02.json`
- status: `pass` / human_intervention_required: `False`
- candidates/surfaced: `500` / `218`
- sim_auto/live_auto/new_bucket: `73` / `0` / `0`
- role/window: `new_pattern_detection` / `same_day_source_bundle_plus_rolling_threshold_cycle_consumer`
- parent_count/granularity/conflict: `31` / `target_pass` / `5`
- state_counts: `{'source_only_keep_collecting': 404, 'lifecycle_flow_sim_probe_candidate': 10, 'sim_auto_approved': 73, 'entry_only_sim_auto_approved': 9, 'entry_only_source_candidate': 4}`
- top_surfaced: `[{'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_bel', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 4, 'source_quality_adjusted_ev_pct': 1.5118}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 2, 'source_quality_adjusted_ev_pct': 1.4929}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_bel', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': 5.0381}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_bel', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': 1.1243}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_unknown_liquid', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': 1.7412}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_unknown_liquid', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': 1.0903}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 16264, 'source_quality_adjusted_ev_pct': -0.6332}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_pyramid_', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 3706, 'source_quality_adjusted_ev_pct': 0.5762}]`

## Lifecycle Bucket Windows
- promotion_window: `mtd`
- confirmation_windows: `['rolling5d', 'rolling10d']`
- windows: `{'rolling5d': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-06-02_rolling5d.json', 'window_role': 'rolling_confirmation', 'window_policy': 'rolling5d', 'status': 'pass', 'parent_bucket_count': 34, 'selected_parent_level': 'L1_broad', 'parent_granularity_status': 'target_pass', 'absorbed_child_count': 278, 'absorbed_sample_count': 54399, 'child_conflict_warning_count': 12, 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'parsed'}, 'rolling10d': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-06-02_rolling10d.json', 'window_role': 'rolling_confirmation', 'window_policy': 'rolling10d', 'status': 'pass', 'parent_bucket_count': 40, 'selected_parent_level': 'L1_broad', 'parent_granularity_status': 'target_pass', 'absorbed_child_count': 399, 'absorbed_sample_count': 115305, 'child_conflict_warning_count': 17, 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'parsed'}, 'mtd': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-06-02_mtd.json', 'window_role': 'promotion_confirmation', 'window_policy': 'mtd', 'status': 'pass', 'parent_bucket_count': 32, 'selected_parent_level': 'L1_broad', 'parent_granularity_status': 'target_pass', 'absorbed_child_count': 208, 'absorbed_sample_count': 42881, 'child_conflict_warning_count': 7, 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'parsed'}}`

## Lifecycle AI Context
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_ai_context/lifecycle_ai_context_2026-06-02.json`
- context_version: `lifecycle_ai_context_v1_2026-06-02` / authority: `ai_advisory_prompt_context_only`
- prompt_stage_count: `3` / runtime_effect: `False`
- stage_contexts: `[{'stage': 'entry', 'prompt_injection_allowed': True, 'policy_key': 'entry:weighted_adm_v1', 'alignment_hint': 'BUY_DEFENSIVE', 'context_contribution_score': -0.2952, 'attribution_quality_status': 'observational_only_pending_outcome'}, {'stage': 'submit', 'prompt_injection_allowed': False, 'policy_key': 'submit:weighted_adm_v1', 'alignment_hint': 'NO_CHANGE', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'holding', 'prompt_injection_allowed': True, 'policy_key': 'holding:weighted_adm_v1', 'alignment_hint': 'EXIT', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'scale_in', 'prompt_injection_allowed': False, 'policy_key': 'scale_in:weighted_adm_v1', 'alignment_hint': 'NO_CHANGE', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'exit', 'prompt_injection_allowed': True, 'policy_key': 'exit:weighted_adm_v1', 'alignment_hint': 'EXIT', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}]`

## Lifecycle AI Context Attribution
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_ai_context_attribution/lifecycle_ai_context_attribution_2026-06-02.json`
- eligible/applied/skipped: `2937` / `2937` / `0`
- replay_budget: `30`
- implementation_status: `implemented`
- stage_attribution: `{'entry': {'context_contribution_score': -0.2952, 'bounded_auxiliary_weight': -0.0443, 'attribution_quality_status': 'observational_only_pending_outcome', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': 0.0783, 'no_context_replay_observed': 0}, 'submit': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'holding': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'scale_in': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'exit': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}}`

## Institutional Flow Context
- artifact: `/home/ubuntu/KORStockScan/data/report/institutional_flow_context/institutional_flow_context_2026-06-02.json`
- status: `pass` / authority: `source_only_lifecycle_feature`
- rows ok/partial/missing/token_error: `120` / `0` / `0` / `0`
- join_rate_pct: `100.0`
- source_mix: `{'ka10059+ka10061': 120}`
- top_net_buy: `[{'stock_code': '034220', 'smart_money_net': 5732195, 'foreign_net_roll5': 612098, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}, {'stock_code': '043260', 'smart_money_net': 923448, 'foreign_net_roll5': 222859, 'inst_net_roll5': 997505, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '473330', 'smart_money_net': 469471, 'foreign_net_roll5': 5828, 'inst_net_roll5': 932810, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '472870', 'smart_money_net': 465729, 'foreign_net_roll5': 3340, 'inst_net_roll5': 1938868, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '092220', 'smart_money_net': 235834, 'foreign_net_roll5': 369337, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}, {'stock_code': '358570', 'smart_money_net': 233732, 'foreign_net_roll5': 0, 'inst_net_roll5': 1174814, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '085620', 'smart_money_net': 231216, 'foreign_net_roll5': 161577, 'inst_net_roll5': 242864, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '402340', 'smart_money_net': 194645, 'foreign_net_roll5': 480703, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}, {'stock_code': '347850', 'smart_money_net': 184470, 'foreign_net_roll5': 0, 'inst_net_roll5': 1472710, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '028670', 'smart_money_net': 183491, 'foreign_net_roll5': 1038838, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}]`

## Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-06-02.json`
- fresh: gemini=`True` claude=`True`
- consensus/orders/family_candidates: `5` / `11` / `2`

## Swing Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_2026-06-02.json`
- deepseek_lab_available: `True`
- findings/orders: `5` / `3`
- data_quality_warnings: `0`
- top_level_data_quality_warnings: `0`
- resolved_data_quality_warnings: `0`
- ofi_qi_stale_missing_unique_records: `16`
- ofi_qi_stale_missing_reasons: `{'micro_missing': 5487, 'micro_stale': 0, 'observer_unhealthy': 1, 'micro_not_ready': 5496, 'state_insufficient': 5496}`
- ofi_qi_stale_missing_reason_combinations: `{'micro_not_ready+state_insufficient': 9, 'micro_missing+micro_not_ready+state_insufficient': 5486, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 1}`
- ofi_qi_stale_missing_reason_combination_unique_records: `{'micro_missing+micro_not_ready+state_insufficient': 16, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 1}`
- ofi_qi_observer_unhealthy_overlap: `{'observer_unhealthy_total': 1, 'observer_unhealthy_with_other_reason': 1, 'observer_unhealthy_only': 0}`
- source_quality_blocked_families: `[{'family': 'swing_entry_ofi_qi_execution_quality', 'stage': 'entry', 'metric_role': 'source_quality_gate', 'decision_authority': 'swing_pattern_lab_analysis_workorder_source_only', 'window_policy': 'same_day_pattern_lab_source_quality', 'sample_floor': 1, 'primary_decision_metric': 'source_quality_gate', 'source_quality_gate': 'swing_orderbook_micro_context_ready_or_blocker_provenance_recorded', 'source_contract_version': 'swing_micro_context_source_quality_v1', 'source_contract_status': 'implemented', 'source_quality_blockers': ['entry_ofi_qi_invalid_micro_context'], 'invalid_micro_context_unique_record_count': 16, 'invalid_reason_combination_unique_record_counts': {'micro_missing+micro_not_ready+state_insufficient': 16, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 1}, 'reason_counts': {'micro_missing': 5487, 'micro_stale': 0, 'observer_unhealthy': 1, 'micro_not_ready': 5496, 'state_insufficient': 5496}, 'reason_combination_counts': {'micro_not_ready+state_insufficient': 9, 'micro_missing+micro_not_ready+state_insufficient': 5486, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 1}, 'observer_unhealthy_overlap': {'observer_unhealthy_total': 1, 'observer_unhealthy_with_other_reason': 1, 'observer_unhealthy_only': 0}, 'automation_input': True, 'runtime_effect': False, 'allowed_runtime_apply': False, 'forbidden_uses': ['swing_real_order_enable', 'one_share_real_canary', 'scale_in_real_canary', 'runtime_threshold_mutation', 'provider_route_change', 'bot_restart', 'recommendation_history_replace']}]`
- carryover_warnings: `0`
- population_split_available: `True`

## Swing Strategy Discovery Sim
- artifact: `/home/ubuntu/KORStockScan/data/report/swing_strategy_discovery_ev/swing_strategy_discovery_ev_2026-06-02.json`
- authority: `swing_sim_exploration_only` / source_only: `True`
- candidate/arm/policy_exit_rows: `684` / `4925` / `4925`
- labeled/pending_future_quotes: `232` / `3634`
- implementation_status: `implemented`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- surviving/avoid_bucket_count: `1` / `9`
- runtime_effect: `False`

## Pipeline Event Verbosity
- artifact: `/home/ubuntu/KORStockScan/data/report/pipeline_event_verbosity/pipeline_event_verbosity_2026-06-02.json`
- state: `v2_shadow_pending_flush`
- recommended_workorder_state: `observe_pending_next_flush`
- high_volume_line_count: `70422`
- high_volume_byte_share_pct: `7.48`
- parity_ok: `False`
- suppress_eligibility: `False`

## Codebase Performance Workorder Source
- artifact: `/home/ubuntu/KORStockScan/data/report/codebase_performance_workorder/codebase_performance_workorder_2026-06-02.json`
- authority: `ops_performance_workorder_source`
- accepted/deferred/rejected: `7` / `3` / `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`

## Pattern Lab Audits
- currentness: status=`pass` fail=`0` orders=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-06-02.json`
- ai_review: status=`pass` orders=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_ai_review/pattern_lab_ai_review_2026-06-02.json`
- time_window_regime_counterfactual: status=`pass` artifact=`/home/ubuntu/KORStockScan/data/report/time_window_regime_counterfactual/time_window_regime_counterfactual_2026-06-02.json`
- producer_gap_discovery: status=`pass` orders=`0` artifact=`/home/ubuntu/KORStockScan/data/report/producer_gap_discovery/producer_gap_discovery_2026-06-02.json`
- stage_hook_workorder_discovery: status=`pass` orders=`0` artifact=`/home/ubuntu/KORStockScan/data/report/stage_hook_workorder_discovery/stage_hook_workorder_discovery_2026-06-02.json`
- propagation: status=`warning` fail=`0` warnings=`2` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_2026-06-02.json`

## Swing Runtime Approval
- request_report: `/home/ubuntu/KORStockScan/data/report/swing_runtime_approval/swing_runtime_approval_2026-06-01.json`
- approval_artifact: `-`
- requested/approved/live_dry_run: `3` / `3` / `2`
- dry_run_forced: `True`
- legacy_phase0_real_canary_ignored: `False`
- blocked: `[]`

## Code Improvement Workorder
- artifact: `/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-06-02.json`
- markdown: `/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-06-02.md`
- selected_order_count: `109`
- decision_counts: `{'implement_now': 6, 'attach_existing_family': 125, 'design_family_candidate': 5, 'defer_evidence': 3, 'reject': 3}`

## Approval Requests
- `position_sizing_cap_release` sample=`50/30` reason=`window_policy primary=rolling_10d 기준 재평가: 1주 cap 해제 efficient trade-off 기준 충족(score=0.21/0.70): 자동 적용하지 않고 사용자 승인 요청 artifact로만 승격한다.` contract=`final_user_approval_required` live_ready=`False`

## Swing Approval Requests
- `swing_model_floor` approval_id=`swing_runtime_approval:2026-06-01:swing_model_floor` score=`0.8554` target_env_keys=`['SWING_FLOOR_BULL', 'SWING_FLOOR_BEAR']`
- `swing_market_regime_sensitivity` approval_id=`swing_runtime_approval:2026-06-01:swing_market_regime_sensitivity` score=`0.8554` target_env_keys=`['SWING_MARKET_REGIME_SENSITIVITY']`
- `swing_one_share_real_canary_phase0` approval_id=`swing_one_share_real_canary:2026-06-01:phase0` score=`0.8554` target_env_keys=`['SWING_ONE_SHARE_REAL_CANARY_ENABLED', 'SWING_ONE_SHARE_REAL_CANARY_ALLOWED_CODES', 'SWING_ONE_SHARE_REAL_CANARY_MAX_QTY', 'SWING_ONE_SHARE_REAL_CANARY_MAX_NEW_ENTRIES_PER_DAY', 'SWING_ONE_SHARE_REAL_CANARY_MAX_OPEN_POSITIONS', 'SWING_ONE_SHARE_REAL_CANARY_MAX_TOTAL_NOTIONAL_KRW', 'SWING_ONE_SHARE_REAL_CANARY_REQUIRE_APPROVAL_ARTIFACT']`

## Calibration Decisions
## Code Improvement Top Orders
- `order_holding_exit_decision_matrix_edge_counterfactual` decision=`implement_now` subsystem=`runtime_instrumentation`
- `order_swing_pattern_lab_deepseek_ofi_qi_smoothing_review` decision=`implement_now` subsystem=`swing_micro_context`
- `order_latency_canary_tag_완화_1축_canary_승인` decision=`implement_now` subsystem=`runtime_instrumentation`

## Pattern Lab Top Findings
- `AI threshold dominance` route=`existing_family` family=`score65_74_recovery_probe`
- `AI threshold miss EV recovery` route=`existing_family` family=`score65_74_recovery_probe`
- `latency guard miss EV recovery` route=`instrumentation_order` family=`-`

- `soft_stop_whipsaw_confirmation`: `hold_sample` sample=`9116/10`
- `holding_flow_ofi_smoothing`: `hold` sample=`4594/20`
- `protect_trailing_smoothing`: `adjust_down` sample=`84/20`
- `trailing_continuation`: `freeze` sample=`448/20`
- `market_regime_continuous_thresholds`: `hold_sample` sample=`6/10`
- `pre_submit_price_guard`: `hold_sample` sample=`27299/20`
- `score65_74_recovery_probe`: `adjust_up` sample=`385/20`
- `strength_momentum_soft_gate_p1`: `hold` sample=`70235/20`
- `overbought_pullback_guard_p1`: `hold` sample=`35243/20`
- `liquidity_pre_submit_guard_p1`: `hold` sample=`3563/20`
- `bad_entry_refined_canary`: `adjust_up` sample=`93054/10`
- `holding_exit_decision_matrix_advisory`: `hold_no_edge` sample=`9/1`
- `lifecycle_decision_matrix_runtime`: `adjust_up` sample=`22915/20`
- `scale_in_price_guard`: `hold` sample=`452/20`
- `position_sizing_cap_release`: `approval_required` sample=`50/30`
- `position_sizing_dynamic_formula`: `hold_sample` sample=`50/30`

## Warnings
- `lifecycle_bucket_discovery:source_contract_drift_warning`
- `lifecycle_bucket_discovery:source_contract_drift_warning`
- `swing_strategy_discovery:pending_future_quotes`
- `swing_lifecycle_decision_matrix:pending_future_quotes`
- `swing_lifecycle_bucket_discovery:ai_two_pass_review_missing_fail_closed`
- `swing_lifecycle_bucket_discovery:ai_two_pass_review_fail_closed_sim_auto_blocked`
- `pattern_lab_propagation_audit_warning`
