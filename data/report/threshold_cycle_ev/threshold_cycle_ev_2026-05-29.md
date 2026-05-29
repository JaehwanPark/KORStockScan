# Threshold Cycle Daily EV Report - 2026-05-29

## Runtime Apply
- status: `auto_bounded_live_ready`
- runtime_change: `True`
- selected_families: `soft_stop_whipsaw_confirmation, score65_74_recovery_probe, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, lifecycle_decision_matrix_runtime`

## Daily EV
- completed: `3` / open: `0`
- win/loss: `1` / `2` (`33.33`%)
- avg_profit_rate: `-1.17`%
- realized_pnl_krw: `-6151`
- full_fill_completed_avg_profit_rate: `-1.173`%

## Entry Funnel
- budget_pass_to_submitted: `7` / `16148` (`0.04`%)
- latency pass/block: `133` / `16003`
- latency submit routing: `latency_classifier_runtime_semantics_gap`
- latency recommended action: `reject` (`recovery_count=0 below floor=1600`)
- latency profile generation: `{'mode': 'grid_quantile_search', 'profile_count': 900, 'age_cap_ms': 1500, 'jitter_cap_ms': 1500, 'spread_cap_ratio': 0.012, 'counterfactual_sample_floor': 3, 'recovery_event_floor_ratio': 0.1}`
- safe/caution_normal/recovery: `0` / `0` / `0`
- recovery attempts/cf sample/cf ev: `0` / `0` / `None`%
- recovered/lost labels: `0` / `0`
- stale/broker override excluded: `0` / `0`
- full/partial fill: `3` / `0`

## Holding Exit
- holding_reviews: `2483`
- exit_signals: `203`
- holding_review_ms_p95: `2136.0`

## Scalp Simulator
- authority: `equal_weight` / fill_policy: `signal_inclusive_best_ask_v1`
- armed/filled/sold: `192` / `192` / `192`
- expired/unpriced/duplicate: `0` / `0` / `1491`
- entry_ai_price applied/skip: `44` / `0`
- submit_revalidation warning/block: `172` / `0`
- scale_in filled/unfilled: `0` / `0`
- overnight decision/sell/hold/carry_restored: `15` / `15` / `0` / `0`
- completed_profit_summary: `{'sample': 192, 'win_count': 91, 'loss_count': 101, 'avg_profit_rate': -0.2341, 'median_profit_rate': -0.88, 'downside_p10_profit_rate': -2.71, 'upside_p90_profit_rate': 3.07, 'win_rate': 0.474, 'loss_rate': 0.526, 'stddev_profit_rate': 2.4504}`
- post_sell_join: joined=`189` / pending=`3`
- post_sell_mfe_mae_10m: mfe=`1.4292`% / mae=`-5.4066`% / close=`-0.0501`%

## Missed Probe Counterfactual
- book: `scalp_score65_74_probe_counterfactual` / role: `missed_buy_probe_counterfactual`
- total/score65_74: `81` / `0`
- avg_expected_ev: `3.0981`% / score65_74_avg_expected_ev: `0.0`%
- actual_order_submitted: `False` / broker_order_forbidden: `True`
- authority: `missed_probe_ev_only_not_broker_execution`

## Scalp Entry ADM
- artifact: `/home/ubuntu/KORStockScan/data/report/scalp_entry_action_decision_matrix/scalp_entry_action_decision_matrix_2026-05-29.json`
- status: `pass` / authority: `entry_advisory_prompt_context_only`
- total/joined/floor: `545` / `153` / `20`
- prompt_applied_count: `271`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 545}`
- forced_action_counts: `{'-': 545}`
- missing_actions: `[]`
- zero_sample_actions: `['SKIP_STALE']`
- top_actions: `[{'action': 'BUY_NOW', 'sample_count': 13, 'joined_sample': 7, 'source_quality_adjusted_ev_pct': 0.0246}, {'action': 'WAIT_REQUOTE', 'sample_count': 11, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'BUY_DEFENSIVE', 'sample_count': 2, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'NO_BUY_AI', 'sample_count': 365, 'joined_sample': 14, 'source_quality_adjusted_ev_pct': -0.0118}, {'action': 'SKIP_SOURCE_QUALITY', 'sample_count': 2, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}]`

## Lifecycle Decision Matrix
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-05-29.json`
- status: `pass` / version: `lifecycle_decision_matrix_v1_2026-05-29`
- total/joined: `22977` / `22200`
- policy_pass/promote_ready: `5` / `1`
- lifecycle_flow buckets/complete/runtime/workorders: `102` / `81` / `0` / `20`
- holding/exit buckets: `34` / `70`
- holding/exit workorders: `10` / `10`
- lifecycle identity missing/join_rate: `0` / `1.0`
- lifecycle complete_flow_rate: `0.007`
- incomplete_flow_reason_counts: `{'missing_entry': 11141, 'missing_holding': 11417, 'missing_exit': 11070, 'missing_submit': 11420, 'postclose_exit_without_entry': 367, 'candidate_id_only': 11203, 'sim_record_id_only': 190}`
- fixed_threshold_roles: `{'hard_safety': ['broker_submit_guard', 'stale_quote_submit_block', 'price_freshness_guard', 'hard_stop', 'protect_stop', 'emergency_stop', 'account_order_cooldown_qty_guard'], 'baseline_prior': ['BUY_SCORE_THRESHOLD', 'VPW_MIN_SCORE', 'strength_momentum_cutoff', 'entry_score_cutoff'], 'bounded_tunable': ['SCALP_ENTRY_LATENCY_MAX_WS_AGE_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_WS_JITTER_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_SPREAD_RATIO_FOR_CAUTION', 'score65_74_recovery_probe', 'soft_stop_whipsaw_confirmation', 'holding_flow_override', 'scale_in_price_guard'], 'legacy_archive': ['fallback_scout_main', 'fallback_single', 'latency_fallback_split_entry', 'legacy_latency_composite', 'closed_shadow_axes']}`
- policy_entries: `[{'stage': 'entry', 'sample': 628, 'joined_sample': 102, 'stage_ev_composite_pct': 1.4025, 'confidence': 1.0, 'selected_action': 'BUY_DEFENSIVE', 'source_quality_gate': 'pass', 'promote_ready': True}, {'stage': 'submit', 'sample': 217, 'joined_sample': 192, 'stage_ev_composite_pct': -0.5838, 'confidence': 1.0, 'selected_action': 'NO_CHANGE', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'holding', 'sample': 207, 'joined_sample': 192, 'stage_ev_composite_pct': -0.4373, 'confidence': 1.0, 'selected_action': 'EXIT', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'scale_in', 'sample': 21057, 'joined_sample': 21047, 'stage_ev_composite_pct': 0.0949, 'confidence': 1.0, 'selected_action': 'NO_CHANGE', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'exit', 'sample': 868, 'joined_sample': 667, 'stage_ev_composite_pct': -0.4226, 'confidence': 1.0, 'selected_action': 'EXIT', 'source_quality_gate': 'pass', 'promote_ready': False}]`

## Lifecycle Bucket Discovery
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-05-29.json`
- status: `pass` / human_intervention_required: `False`
- candidates/surfaced: `500` / `238`
- sim_auto/live_auto/new_bucket: `123` / `9` / `9`
- state_counts: `{'live_auto_apply_ready': 9, 'runtime_blocked_contract_gap': 4, 'source_only_keep_collecting': 330, 'new_bucket_candidate': 9, 'lifecycle_flow_sim_probe_candidate': 12, 'sim_auto_approved': 123, 'entry_only_sim_auto_approved': 9, 'entry_only_source_candidate': 4}`
- top_surfaced: `[{'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq', 'stage': 'lifecycle_flow', 'classification_state': 'live_auto_apply_ready', 'live_auto_apply_family': 'greenfield_real_environment_authority', 'recommended_action': 'relax_or_recover', 'joined_sample': 4, 'source_quality_adjusted_ev_pct': 2.7842}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'stage': 'lifecycle_flow', 'classification_state': 'runtime_blocked_contract_gap', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 2, 'source_quality_adjusted_ev_pct': 1.2894}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq', 'stage': 'lifecycle_flow', 'classification_state': 'live_auto_apply_ready', 'live_auto_apply_family': 'greenfield_real_environment_authority', 'recommended_action': 'relax_or_recover', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': 2.4291}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_stale_block_liquidi', 'stage': 'lifecycle_flow', 'classification_state': 'live_auto_apply_ready', 'live_auto_apply_family': 'greenfield_real_environment_authority', 'recommended_action': 'relax_or_recover', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': 1.1187}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'stage': 'lifecycle_flow', 'classification_state': 'runtime_blocked_contract_gap', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': 1.0433}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'stage': 'lifecycle_flow', 'classification_state': 'runtime_blocked_contract_gap', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': 1.5054}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_scalp_entry_action_decision_snapshot_stale', 'stage': 'lifecycle_flow', 'classification_state': 'live_auto_apply_ready', 'live_auto_apply_family': 'greenfield_real_environment_authority', 'recommended_action': 'relax_or_recover', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': 1.0295}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_scalp_entry_action_decision_snapshot_stale', 'stage': 'lifecycle_flow', 'classification_state': 'live_auto_apply_ready', 'live_auto_apply_family': 'greenfield_real_environment_authority', 'recommended_action': 'relax_or_recover', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': 1.7616}]`

## Lifecycle AI Context
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_ai_context/lifecycle_ai_context_2026-05-29.json`
- context_version: `lifecycle_ai_context_v1_2026-05-29` / authority: `ai_advisory_prompt_context_only`
- prompt_stage_count: `3` / runtime_effect: `False`
- stage_contexts: `[{'stage': 'entry', 'prompt_injection_allowed': True, 'policy_key': 'entry:weighted_adm_v1', 'alignment_hint': 'BUY_DEFENSIVE', 'context_contribution_score': -0.0385, 'attribution_quality_status': 'observational_only_pending_outcome'}, {'stage': 'submit', 'prompt_injection_allowed': False, 'policy_key': 'submit:weighted_adm_v1', 'alignment_hint': 'NO_CHANGE', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'holding', 'prompt_injection_allowed': True, 'policy_key': 'holding:weighted_adm_v1', 'alignment_hint': 'EXIT', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'scale_in', 'prompt_injection_allowed': False, 'policy_key': 'scale_in:weighted_adm_v1', 'alignment_hint': 'NO_CHANGE', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'exit', 'prompt_injection_allowed': True, 'policy_key': 'exit:weighted_adm_v1', 'alignment_hint': 'EXIT', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}]`

## Lifecycle AI Context Attribution
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_ai_context_attribution/lifecycle_ai_context_attribution_2026-05-29.json`
- eligible/applied/skipped: `1636` / `1636` / `0`
- replay_budget: `30`
- implementation_status: `implemented`
- stage_attribution: `{'entry': {'context_contribution_score': -0.0385, 'bounded_auxiliary_weight': -0.0058, 'attribution_quality_status': 'observational_only_pending_outcome', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': 0.445, 'no_context_replay_observed': 0}, 'submit': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'holding': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'scale_in': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'exit': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}}`

## Institutional Flow Context
- artifact: `/home/ubuntu/KORStockScan/data/report/institutional_flow_context/institutional_flow_context_2026-05-29.json`
- status: `pass` / authority: `source_only_lifecycle_feature`
- rows ok/partial/missing/token_error: `120` / `0` / `0` / `0`
- join_rate_pct: `100.0`
- source_mix: `{'ka10059+ka10061': 120}`
- top_net_buy: `[{'stock_code': '018880', 'smart_money_net': 7284839, 'foreign_net_roll5': 11871883, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}, {'stock_code': '005930', 'smart_money_net': 4260411, 'foreign_net_roll5': 0, 'inst_net_roll5': 6773194, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '035420', 'smart_money_net': 1026952, 'foreign_net_roll5': 0, 'inst_net_roll5': 847064, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '064400', 'smart_money_net': 752457, 'foreign_net_roll5': 508497, 'inst_net_roll5': 702460, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '336370', 'smart_money_net': 579282, 'foreign_net_roll5': 0, 'inst_net_roll5': 934228, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '034220', 'smart_money_net': 492521, 'foreign_net_roll5': 3471423, 'inst_net_roll5': 43445, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '066570', 'smart_money_net': 379199, 'foreign_net_roll5': 0, 'inst_net_roll5': 944153, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '005380', 'smart_money_net': 367102, 'foreign_net_roll5': 0, 'inst_net_roll5': 493932, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '242040', 'smart_money_net': 283168, 'foreign_net_roll5': 1006759, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}, {'stock_code': '373220', 'smart_money_net': 245051, 'foreign_net_roll5': 95832, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}]`

## Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-05-29.json`
- fresh: gemini=`True` claude=`True`
- consensus/orders/family_candidates: `5` / `12` / `2`

## Swing Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_2026-05-29.json`
- deepseek_lab_available: `True`
- findings/orders: `5` / `3`
- data_quality_warnings: `0`
- top_level_data_quality_warnings: `0`
- resolved_data_quality_warnings: `0`
- ofi_qi_stale_missing_unique_records: `17`
- ofi_qi_stale_missing_reasons: `{'micro_missing': 2880, 'micro_stale': 0, 'observer_unhealthy': 8, 'micro_not_ready': 2890, 'state_insufficient': 2890}`
- ofi_qi_stale_missing_reason_combinations: `{'micro_not_ready+state_insufficient': 10, 'micro_missing+micro_not_ready+state_insufficient': 2872, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 8}`
- ofi_qi_stale_missing_reason_combination_unique_records: `{'micro_missing+micro_not_ready+state_insufficient': 17, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 2}`
- ofi_qi_observer_unhealthy_overlap: `{'observer_unhealthy_total': 8, 'observer_unhealthy_with_other_reason': 8, 'observer_unhealthy_only': 0}`
- source_quality_blocked_families: `[{'family': 'swing_entry_ofi_qi_execution_quality', 'stage': 'entry', 'metric_role': 'source_quality_gate', 'decision_authority': 'swing_pattern_lab_analysis_workorder_source_only', 'window_policy': 'same_day_pattern_lab_source_quality', 'sample_floor': 1, 'primary_decision_metric': 'source_quality_gate', 'source_quality_gate': 'swing_orderbook_micro_context_ready_or_blocker_provenance_recorded', 'source_contract_version': 'swing_micro_context_source_quality_v1', 'source_contract_status': 'implemented', 'source_quality_blockers': ['entry_ofi_qi_invalid_micro_context'], 'invalid_micro_context_unique_record_count': 17, 'invalid_reason_combination_unique_record_counts': {'micro_missing+micro_not_ready+state_insufficient': 17, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 2}, 'reason_counts': {'micro_missing': 2880, 'micro_stale': 0, 'observer_unhealthy': 8, 'micro_not_ready': 2890, 'state_insufficient': 2890}, 'reason_combination_counts': {'micro_not_ready+state_insufficient': 10, 'micro_missing+micro_not_ready+state_insufficient': 2872, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 8}, 'observer_unhealthy_overlap': {'observer_unhealthy_total': 8, 'observer_unhealthy_with_other_reason': 8, 'observer_unhealthy_only': 0}, 'automation_input': True, 'runtime_effect': False, 'allowed_runtime_apply': False, 'forbidden_uses': ['swing_real_order_enable', 'one_share_real_canary', 'scale_in_real_canary', 'runtime_threshold_mutation', 'provider_route_change', 'bot_restart', 'recommendation_history_replace']}]`
- carryover_warnings: `0`
- population_split_available: `True`

## Swing Strategy Discovery Sim
- artifact: `/home/ubuntu/KORStockScan/data/report/swing_strategy_discovery_ev/swing_strategy_discovery_ev_2026-05-29.json`
- authority: `swing_sim_exploration_only` / source_only: `True`
- candidate/arm/policy_exit_rows: `482` / `3604` / `3604`
- labeled/pending_future_quotes: `59` / `3033`
- implementation_status: `implemented`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- surviving/avoid_bucket_count: `1` / `6`
- runtime_effect: `False`

## Pipeline Event Verbosity
- artifact: `/home/ubuntu/KORStockScan/data/report/pipeline_event_verbosity/pipeline_event_verbosity_2026-05-29.json`
- state: `v2_shadow_pending_flush`
- recommended_workorder_state: `observe_pending_next_flush`
- high_volume_line_count: `78324`
- high_volume_byte_share_pct: `12.14`
- parity_ok: `False`
- suppress_eligibility: `False`

## Codebase Performance Workorder Source
- artifact: `/home/ubuntu/KORStockScan/data/report/codebase_performance_workorder/codebase_performance_workorder_2026-05-29.json`
- authority: `ops_performance_workorder_source`
- accepted/deferred/rejected: `7` / `3` / `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`

## Pattern Lab Audits
- currentness: status=`pass` fail=`0` orders=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-05-29.json`
- ai_review: status=`warning` orders=`2` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_ai_review/pattern_lab_ai_review_2026-05-29.json`
- time_window_regime_counterfactual: status=`pass` artifact=`/home/ubuntu/KORStockScan/data/report/time_window_regime_counterfactual/time_window_regime_counterfactual_2026-05-29.json`
- producer_gap_discovery: status=`warning` orders=`9` artifact=`/home/ubuntu/KORStockScan/data/report/producer_gap_discovery/producer_gap_discovery_2026-05-29.json`
- stage_hook_workorder_discovery: status=`warning` orders=`2` artifact=`/home/ubuntu/KORStockScan/data/report/stage_hook_workorder_discovery/stage_hook_workorder_discovery_2026-05-29.json`
- propagation: status=`pass` fail=`0` warnings=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_2026-05-29.json`

## Swing Runtime Approval
- request_report: `/home/ubuntu/KORStockScan/data/report/swing_runtime_approval/swing_runtime_approval_2026-05-28.json`
- approval_artifact: `-`
- requested/approved/live_dry_run: `0` / `0` / `0`
- dry_run_forced: `False`
- real_canary_policy: `swing_one_share_real_canary_phase0`
- one_share_real_canary_artifact: `-`
- selected_one_share_real_canary: `0`
- real_order_allowed_actions: `BUY_INITIAL, SELL_CLOSE`
- sim_only_actions: `AVG_DOWN, PYRAMID, SCALE_IN`
- scale_in_real_canary_policy: `swing_scale_in_real_canary_phase0`
- selected_scale_in_real_canary: `0`
- scale_in_real_execution_quality: `{'one_share_canary_selected': 0, 'scale_in_canary_selected': 0, 'execution_quality_source': 'real_only', 'sim_probe_ev_source': 'separate_from_broker_execution_quality'}`
- blocked: `[]`

## Code Improvement Workorder
- artifact: `/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-05-29.json`
- markdown: `/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-05-29.md`
- selected_order_count: `99`
- decision_counts: `{'implement_now': 2, 'attach_existing_family': 117, 'design_family_candidate': 6, 'defer_evidence': 10, 'reject': 3}`

## Approval Requests
- none

## Swing Approval Requests
- none

## Calibration Decisions
## Code Improvement Top Orders
- `order_lifecycle_bucket_discovery_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_90c49526` decision=`implement_now` subsystem=`lifecycle_bucket_discovery_taxonomy_provenance`
- `order_lifecycle_bucket_discovery_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_97d8b767` decision=`implement_now` subsystem=`lifecycle_bucket_discovery_taxonomy_provenance`
- `order_entry_submit_drought_auto_resolution` decision=`attach_existing_family` subsystem=`runtime_instrumentation`

## Pattern Lab Top Findings
- `AI threshold dominance` route=`existing_family` family=`score65_74_recovery_probe`
- `AI threshold miss EV recovery` route=`existing_family` family=`score65_74_recovery_probe`
- `latency guard miss EV recovery` route=`instrumentation_order` family=`-`

- `soft_stop_whipsaw_confirmation`: `adjust_up` sample=`9267/10`
- `holding_flow_ofi_smoothing`: `hold` sample=`3429/20`
- `protect_trailing_smoothing`: `adjust_down` sample=`120/20`
- `trailing_continuation`: `freeze` sample=`389/20`
- `market_regime_continuous_thresholds`: `hold_sample` sample=`6/10`
- `pre_submit_price_guard`: `hold_sample` sample=`16003/20`
- `score65_74_recovery_probe`: `adjust_up` sample=`470/20`
- `strength_momentum_soft_gate_p1`: `hold` sample=`82656/20`
- `overbought_pullback_guard_p1`: `hold` sample=`43244/20`
- `liquidity_pre_submit_guard_p1`: `hold` sample=`4686/20`
- `bad_entry_refined_canary`: `adjust_up` sample=`93758/10`
- `holding_exit_decision_matrix_advisory`: `hold_no_edge` sample=`10/1`
- `lifecycle_decision_matrix_runtime`: `adjust_up` sample=`22977/20`
- `scale_in_price_guard`: `hold` sample=`639/20`
- `position_sizing_cap_release`: `hold_sample` sample=`25/30`
- `position_sizing_dynamic_formula`: `hold_sample` sample=`21/30`

## Warnings
- `swing_strategy_discovery:pending_future_quotes`
- `swing_lifecycle_decision_matrix:pending_future_quotes`
- `pattern_lab_ai_review_warning`
