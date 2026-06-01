# Threshold Cycle Daily EV Report - 2026-05-28

## Runtime Apply
- status: `auto_bounded_live_ready`
- runtime_change: `True`
- selected_families: `soft_stop_whipsaw_confirmation, score65_74_recovery_probe, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, lifecycle_decision_matrix_runtime, entry_wait6579_score66_69_recovery_gate_v1`

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
- latency recommended action: `reject` (`recovery_count=0 below floor=1539`)
- latency profile generation: `{'mode': 'grid_quantile_search', 'profile_count': 900, 'age_cap_ms': 1500, 'jitter_cap_ms': 1500, 'spread_cap_ratio': 0.012, 'counterfactual_sample_floor': 3, 'recovery_event_floor_ratio': 0.1}`
- safe/caution_normal/recovery: `0` / `0` / `0`
- recovery attempts/cf sample/cf ev: `0` / `0` / `None`%
- recovered/lost labels: `0` / `0`
- stale/broker override excluded: `0` / `0`
- full/partial fill: `0` / `0`

## Holding Exit
- holding_reviews: `0`
- exit_signals: `0`
- holding_review_ms_p95: `0.0`

## Scalp Simulator
- authority: `equal_weight` / fill_policy: `signal_inclusive_best_ask_v1`
- armed/filled/sold: `183` / `183` / `164`
- expired/unpriced/duplicate: `0` / `0` / `1290`
- entry_ai_price applied/skip: `52` / `0`
- submit_revalidation warning/block: `170` / `0`
- scale_in filled/unfilled: `0` / `1`
- overnight decision/sell/hold/carry_restored: `0` / `0` / `0` / `0`
- completed_profit_summary: `{'sample': 164, 'win_count': 58, 'loss_count': 106, 'avg_profit_rate': -0.9954, 'median_profit_rate': -1.87, 'downside_p10_profit_rate': -2.71, 'upside_p90_profit_rate': 1.99, 'win_rate': 0.3537, 'loss_rate': 0.6463, 'stddev_profit_rate': 2.8403}`
- post_sell_join: joined=`164` / pending=`0`
- post_sell_mfe_mae_10m: mfe=`2.5096`% / mae=`-5.0835`% / close=`-0.1202`%

## Missed Probe Counterfactual
- book: `-` / role: `-`
- total/score65_74: `None` / `None`
- avg_expected_ev: `None`% / score65_74_avg_expected_ev: `None`%
- actual_order_submitted: `None` / broker_order_forbidden: `None`
- authority: `-`

## Scalp Entry ADM
- artifact: `/home/ubuntu/KORStockScan/data/report/scalp_entry_action_decision_matrix/scalp_entry_action_decision_matrix_2026-05-28.json`
- status: `pass` / authority: `entry_advisory_prompt_context_only`
- total/joined/floor: `484` / `184` / `20`
- prompt_applied_count: `193`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 484}`
- forced_action_counts: `{'-': 484}`
- missing_actions: `[]`
- zero_sample_actions: `['SKIP_STALE']`
- top_actions: `[{'action': 'BUY_NOW', 'sample_count': 8, 'joined_sample': 5, 'source_quality_adjusted_ev_pct': -0.4437}, {'action': 'WAIT_REQUOTE', 'sample_count': 12, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'BUY_DEFENSIVE', 'sample_count': 2, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'NO_BUY_AI', 'sample_count': 304, 'joined_sample': 27, 'source_quality_adjusted_ev_pct': 0.0589}, {'action': 'SKIP_SOURCE_QUALITY', 'sample_count': 4, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}]`

## Lifecycle Decision Matrix
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-05-28.json`
- status: `pass` / version: `lifecycle_decision_matrix_v1_2026-05-28`
- total/joined: `24484` / `23761`
- policy_pass/promote_ready: `5` / `0`
- lifecycle_flow buckets/complete/runtime/workorders: `97` / `84` / `0` / `20`
- holding/exit buckets: `34` / `68`
- holding/exit workorders: `10` / `10`
- lifecycle identity missing/join_rate: `0` / `1.0`
- lifecycle complete_flow_rate: `0.0066`
- incomplete_flow_reason_counts: `{'missing_entry': 12410, 'missing_holding': 12694, 'missing_exit': 12349, 'missing_submit': 12697, 'sim_record_id_only': 195, 'postclose_exit_without_entry': 364, 'candidate_id_only': 12472}`
- fixed_threshold_roles: `{'hard_safety': ['broker_submit_guard', 'stale_quote_submit_block', 'price_freshness_guard', 'hard_stop', 'protect_stop', 'emergency_stop', 'account_order_cooldown_qty_guard'], 'baseline_prior': ['BUY_SCORE_THRESHOLD', 'VPW_MIN_SCORE', 'strength_momentum_cutoff', 'entry_score_cutoff'], 'bounded_tunable': ['SCALP_ENTRY_LATENCY_MAX_WS_AGE_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_WS_JITTER_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_SPREAD_RATIO_FOR_CAUTION', 'score65_74_recovery_probe', 'soft_stop_whipsaw_confirmation', 'holding_flow_override', 'scale_in_price_guard'], 'legacy_archive': ['fallback_scout_main', 'fallback_single', 'latency_fallback_split_entry', 'legacy_latency_composite', 'closed_shadow_axes']}`
- policy_entries: `[{'stage': 'entry', 'sample': 569, 'joined_sample': 112, 'stage_ev_composite_pct': -0.8361, 'confidence': 1.0, 'selected_action': 'WAIT_REQUOTE', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'submit', 'sample': 217, 'joined_sample': 199, 'stage_ev_composite_pct': -0.6071, 'confidence': 1.0, 'selected_action': 'NO_CHANGE', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'holding', 'sample': 216, 'joined_sample': 199, 'stage_ev_composite_pct': -0.7334, 'confidence': 1.0, 'selected_action': 'EXIT', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'scale_in', 'sample': 22529, 'joined_sample': 22492, 'stage_ev_composite_pct': -0.4456, 'confidence': 1.0, 'selected_action': 'NO_CHANGE', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'exit', 'sample': 953, 'joined_sample': 759, 'stage_ev_composite_pct': -0.5616, 'confidence': 1.0, 'selected_action': 'EXIT', 'source_quality_gate': 'pass', 'promote_ready': False}]`

## Lifecycle Bucket Discovery
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-05-28.json`
- status: `pass` / human_intervention_required: `False`
- candidates/surfaced: `500` / `249`
- sim_auto/live_auto/new_bucket: `140` / `0` / `10`
- role/window: `new_pattern_detection` / `daily_lifecycle_bucket_discovery_with_preopen_auto_apply`
- parent_count/granularity/conflict: `0` / `None` / `0`
- state_counts: `{'runtime_blocked_contract_gap': 7, 'source_only_keep_collecting': 319, 'lifecycle_flow_sim_probe_candidate': 12, 'new_bucket_candidate': 10, 'sim_auto_approved': 140, 'entry_only_sim_auto_approved': 8, 'entry_only_source_candidate': 4}`
- top_surfaced: `[{'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_stale_watch_liquidi', 'stage': 'lifecycle_flow', 'classification_state': 'runtime_blocked_contract_gap', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': 2.5302}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'stage': 'lifecycle_flow', 'classification_state': 'runtime_blocked_contract_gap', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': 4.8703}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_blocked_ai_score_stale_fresh_liquidity_liq', 'stage': 'lifecycle_flow', 'classification_state': 'runtime_blocked_contract_gap', 'live_auto_apply_family': 'greenfield_real_environment_authority', 'recommended_action': 'relax_or_recover', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': 1.3233}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_f', 'stage': 'lifecycle_flow', 'classification_state': 'runtime_blocked_contract_gap', 'live_auto_apply_family': 'greenfield_real_environment_authority', 'recommended_action': 'relax_or_recover', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': 1.0122}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_fresh_liquidity_liqu', 'stage': 'lifecycle_flow', 'classification_state': 'runtime_blocked_contract_gap', 'live_auto_apply_family': 'greenfield_real_environment_authority', 'recommended_action': 'relax_or_recover', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': 2.2548}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 9690, 'source_quality_adjusted_ev_pct': -0.6679}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_pyramid_', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 2309, 'source_quality_adjusted_ev_pct': 0.6159}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'keep_collecting', 'joined_sample': 128, 'source_quality_adjusted_ev_pct': -0.6448}]`

## Lifecycle Bucket Windows
- promotion_window: `mtd`
- confirmation_windows: `['rolling5d', 'rolling10d']`
- windows: `{'rolling5d': {'available': False, 'artifact': None, 'window_role': 'rolling_confirmation', 'window_policy': 'rolling5d', 'status': 'missing', 'parent_bucket_count': 0, 'selected_parent_level': None, 'parent_granularity_status': None, 'absorbed_child_count': 0, 'absorbed_sample_count': 0, 'child_conflict_warning_count': 0, 'live_auto_apply_ready_count': 0, 'source_contract_status': None, 'ai_two_pass_review_status': None}, 'rolling10d': {'available': False, 'artifact': None, 'window_role': 'rolling_confirmation', 'window_policy': 'rolling10d', 'status': 'missing', 'parent_bucket_count': 0, 'selected_parent_level': None, 'parent_granularity_status': None, 'absorbed_child_count': 0, 'absorbed_sample_count': 0, 'child_conflict_warning_count': 0, 'live_auto_apply_ready_count': 0, 'source_contract_status': None, 'ai_two_pass_review_status': None}, 'mtd': {'available': False, 'artifact': None, 'window_role': 'promotion_confirmation', 'window_policy': 'mtd', 'status': 'missing', 'parent_bucket_count': 0, 'selected_parent_level': None, 'parent_granularity_status': None, 'absorbed_child_count': 0, 'absorbed_sample_count': 0, 'child_conflict_warning_count': 0, 'live_auto_apply_ready_count': 0, 'source_contract_status': None, 'ai_two_pass_review_status': None}}`

## Lifecycle AI Context
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_ai_context/lifecycle_ai_context_2026-05-28.json`
- context_version: `lifecycle_ai_context_v1_2026-05-28` / authority: `ai_advisory_prompt_context_only`
- prompt_stage_count: `3` / runtime_effect: `False`
- stage_contexts: `[{'stage': 'entry', 'prompt_injection_allowed': True, 'policy_key': 'entry:weighted_adm_v1', 'alignment_hint': 'WAIT_REQUOTE', 'context_contribution_score': -0.3013, 'attribution_quality_status': 'observational_only_pending_outcome'}, {'stage': 'submit', 'prompt_injection_allowed': False, 'policy_key': 'submit:weighted_adm_v1', 'alignment_hint': 'NO_CHANGE', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'holding', 'prompt_injection_allowed': True, 'policy_key': 'holding:weighted_adm_v1', 'alignment_hint': 'EXIT', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'scale_in', 'prompt_injection_allowed': False, 'policy_key': 'scale_in:weighted_adm_v1', 'alignment_hint': 'NO_CHANGE', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'exit', 'prompt_injection_allowed': True, 'policy_key': 'exit:weighted_adm_v1', 'alignment_hint': 'EXIT', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}]`

## Lifecycle AI Context Attribution
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_ai_context_attribution/lifecycle_ai_context_attribution_2026-05-28.json`
- eligible/applied/skipped: `2125` / `2125` / `0`
- replay_budget: `30`
- implementation_status: `implemented`
- stage_attribution: `{'entry': {'context_contribution_score': -0.3013, 'bounded_auxiliary_weight': -0.0452, 'attribution_quality_status': 'observational_only_pending_outcome', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': 0.0696, 'no_context_replay_observed': 0}, 'submit': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'holding': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'scale_in': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'exit': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}}`

## Institutional Flow Context
- artifact: `/home/ubuntu/KORStockScan/data/report/institutional_flow_context/institutional_flow_context_2026-05-28.json`
- status: `pass` / authority: `source_only_lifecycle_feature`
- rows ok/partial/missing/token_error: `120` / `0` / `0` / `0`
- join_rate_pct: `100.0`
- source_mix: `{'ka10059+ka10061': 120}`
- top_net_buy: `[{'stock_code': '347850', 'smart_money_net': 989122, 'foreign_net_roll5': 0, 'inst_net_roll5': 1508620, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '001440', 'smart_money_net': 838329, 'foreign_net_roll5': 0, 'inst_net_roll5': 152680, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '242040', 'smart_money_net': 651255, 'foreign_net_roll5': 963314, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}, {'stock_code': '393890', 'smart_money_net': 648550, 'foreign_net_roll5': 357659, 'inst_net_roll5': 284055, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '003490', 'smart_money_net': 581052, 'foreign_net_roll5': 2048995, 'inst_net_roll5': 891349, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '279570', 'smart_money_net': 567615, 'foreign_net_roll5': 82115, 'inst_net_roll5': 1654635, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '006400', 'smart_money_net': 436116, 'foreign_net_roll5': 181967, 'inst_net_roll5': 183612, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '463050', 'smart_money_net': 366710, 'foreign_net_roll5': 0, 'inst_net_roll5': 68783, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '417010', 'smart_money_net': 364307, 'foreign_net_roll5': 332683, 'inst_net_roll5': 1192, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '204270', 'smart_money_net': 351119, 'foreign_net_roll5': 411430, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}]`

## Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-05-28.json`
- fresh: gemini=`False` claude=`False`
- consensus/orders/family_candidates: `0` / `0` / `0`

## Swing Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_2026-05-28.json`
- deepseek_lab_available: `True`
- findings/orders: `8` / `3`
- data_quality_warnings: `0`
- top_level_data_quality_warnings: `1`
- resolved_data_quality_warnings: `0`
- ofi_qi_stale_missing_unique_records: `18`
- ofi_qi_stale_missing_reasons: `{'micro_missing': 4070, 'micro_stale': 0, 'observer_unhealthy': 8, 'micro_not_ready': 4078, 'state_insufficient': 4078}`
- ofi_qi_stale_missing_reason_combinations: `{'micro_not_ready+state_insufficient': 8, 'micro_missing+micro_not_ready+state_insufficient': 4062, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 8}`
- ofi_qi_stale_missing_reason_combination_unique_records: `{'micro_missing+micro_not_ready+state_insufficient': 18, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 3}`
- ofi_qi_observer_unhealthy_overlap: `{'observer_unhealthy_total': 8, 'observer_unhealthy_with_other_reason': 8, 'observer_unhealthy_only': 0}`
- source_quality_blocked_families: `[{'family': 'swing_entry_ofi_qi_execution_quality', 'stage': 'entry', 'metric_role': 'source_quality_gate', 'decision_authority': 'swing_pattern_lab_analysis_workorder_source_only', 'window_policy': 'same_day_pattern_lab_source_quality', 'sample_floor': 1, 'primary_decision_metric': 'source_quality_gate', 'source_quality_gate': 'swing_orderbook_micro_context_ready_or_blocker_provenance_recorded', 'source_contract_version': 'swing_micro_context_source_quality_v1', 'source_contract_status': 'implemented', 'source_quality_blockers': ['entry_ofi_qi_invalid_micro_context'], 'invalid_micro_context_unique_record_count': 17, 'invalid_reason_combination_unique_record_counts': {'micro_missing+micro_not_ready+state_insufficient': 18, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 3}, 'reason_counts': {'micro_missing': 4070, 'micro_stale': 0, 'observer_unhealthy': 8, 'micro_not_ready': 4078, 'state_insufficient': 4078}, 'reason_combination_counts': {'micro_not_ready+state_insufficient': 8, 'micro_missing+micro_not_ready+state_insufficient': 4062, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 8}, 'observer_unhealthy_overlap': {'observer_unhealthy_total': 8, 'observer_unhealthy_with_other_reason': 8, 'observer_unhealthy_only': 0}, 'automation_input': True, 'runtime_effect': False, 'allowed_runtime_apply': False, 'forbidden_uses': ['swing_real_order_enable', 'one_share_real_canary', 'scale_in_real_canary', 'runtime_threshold_mutation', 'provider_route_change', 'bot_restart', 'recommendation_history_replace']}, {'family': 'swing_scale_in_ofi_qi_confirmation', 'stage': 'scale_in', 'metric_role': 'source_quality_gate', 'decision_authority': 'swing_pattern_lab_analysis_workorder_source_only', 'window_policy': 'same_day_pattern_lab_source_quality', 'sample_floor': 1, 'primary_decision_metric': 'source_quality_gate', 'source_quality_gate': 'swing_orderbook_micro_context_ready_or_blocker_provenance_recorded', 'source_contract_version': 'swing_micro_context_source_quality_v1', 'source_contract_status': 'implemented', 'source_quality_blockers': ['scale_in_ofi_qi_invalid_micro_context'], 'invalid_micro_context_unique_record_count': 1, 'invalid_reason_combination_unique_record_counts': {'micro_missing+micro_not_ready+state_insufficient': 18, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 3}, 'reason_counts': {'micro_missing': 4070, 'micro_stale': 0, 'observer_unhealthy': 8, 'micro_not_ready': 4078, 'state_insufficient': 4078}, 'reason_combination_counts': {'micro_not_ready+state_insufficient': 8, 'micro_missing+micro_not_ready+state_insufficient': 4062, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 8}, 'observer_unhealthy_overlap': {'observer_unhealthy_total': 8, 'observer_unhealthy_with_other_reason': 8, 'observer_unhealthy_only': 0}, 'automation_input': True, 'runtime_effect': False, 'allowed_runtime_apply': False, 'forbidden_uses': ['swing_real_order_enable', 'one_share_real_canary', 'scale_in_real_canary', 'runtime_threshold_mutation', 'provider_route_change', 'bot_restart', 'recommendation_history_replace']}]`
- carryover_warnings: `3`
- population_split_available: `True`

## Swing Strategy Discovery Sim
- artifact: `/home/ubuntu/KORStockScan/data/report/swing_strategy_discovery_ev/swing_strategy_discovery_ev_2026-05-28.json`
- authority: `swing_sim_exploration_only` / source_only: `True`
- candidate/arm/policy_exit_rows: `432` / `3204` / `3204`
- labeled/pending_future_quotes: `84` / `2617`
- implementation_status: `implemented`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- surviving/avoid_bucket_count: `1` / `4`
- runtime_effect: `False`

## Pipeline Event Verbosity
- artifact: `/home/ubuntu/KORStockScan/data/report/pipeline_event_verbosity/pipeline_event_verbosity_2026-05-28.json`
- state: `v2_shadow_pending_flush`
- recommended_workorder_state: `observe_pending_next_flush`
- high_volume_line_count: `32250`
- high_volume_byte_share_pct: `3.97`
- parity_ok: `False`
- suppress_eligibility: `False`

## Codebase Performance Workorder Source
- artifact: `/home/ubuntu/KORStockScan/data/report/codebase_performance_workorder/codebase_performance_workorder_2026-05-28.json`
- authority: `ops_performance_workorder_source`
- accepted/deferred/rejected: `7` / `3` / `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`

## Pattern Lab Audits
- currentness: status=`pass` fail=`0` orders=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-05-28.json`
- ai_review: status=`warning` orders=`1` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_ai_review/pattern_lab_ai_review_2026-05-28.json`
- time_window_regime_counterfactual: status=`pass` artifact=`/home/ubuntu/KORStockScan/data/report/time_window_regime_counterfactual/time_window_regime_counterfactual_2026-05-28.json`
- producer_gap_discovery: status=`warning` orders=`6` artifact=`/home/ubuntu/KORStockScan/data/report/producer_gap_discovery/producer_gap_discovery_2026-05-28.json`
- stage_hook_workorder_discovery: status=`warning` orders=`2` artifact=`/home/ubuntu/KORStockScan/data/report/stage_hook_workorder_discovery/stage_hook_workorder_discovery_2026-05-28.json`
- propagation: status=`warning` fail=`0` warnings=`2` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_2026-05-28.json`

## Swing Runtime Approval
- request_report: `/home/ubuntu/KORStockScan/data/report/swing_runtime_approval/swing_runtime_approval_2026-05-27.json`
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
- artifact: `/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-05-28.json`
- markdown: `/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-05-28.md`
- selected_order_count: `148`
- decision_counts: `{'implement_now': 47, 'attach_existing_family': 119, 'design_family_candidate': 3, 'defer_evidence': 5, 'reject': 2}`

## Approval Requests
- none

## Swing Approval Requests
- none

## Calibration Decisions
## Code Improvement Top Orders
- `order_lifecycle_bucket_discovery_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_f6cddc94` decision=`implement_now` subsystem=`lifecycle_bucket_discovery_taxonomy_provenance`
- `order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_04a0c69a` decision=`implement_now` subsystem=`lifecycle_bucket_discovery_taxonomy_provenance`
- `order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_053f28f4` decision=`implement_now` subsystem=`lifecycle_bucket_discovery_taxonomy_provenance`

- `soft_stop_whipsaw_confirmation`: `adjust_up` sample=`10131/10`
- `holding_flow_ofi_smoothing`: `hold` sample=`2848/20`
- `protect_trailing_smoothing`: `adjust_down` sample=`120/20`
- `trailing_continuation`: `freeze` sample=`353/20`
- `market_regime_continuous_thresholds`: `hold_sample` sample=`5/10`
- `pre_submit_price_guard`: `hold_sample` sample=`20790/20`
- `score65_74_recovery_probe`: `hold` sample=`389/20`
- `strength_momentum_soft_gate_p1`: `hold` sample=`57122/20`
- `overbought_pullback_guard_p1`: `hold` sample=`31377/20`
- `liquidity_pre_submit_guard_p1`: `hold` sample=`3796/20`
- `bad_entry_refined_canary`: `adjust_up` sample=`93625/10`
- `holding_exit_decision_matrix_advisory`: `hold_no_edge` sample=`10/1`
- `lifecycle_decision_matrix_runtime`: `adjust_up` sample=`24484/20`
- `scale_in_price_guard`: `hold` sample=`808/20`
- `position_sizing_cap_release`: `hold_sample` sample=`18/30`
- `position_sizing_dynamic_formula`: `hold_sample` sample=`18/30`

## Warnings
- `trade_review_missing`
- `performance_tuning_missing`
- `pattern_lab_gemini_stale`
- `pattern_lab_claude_stale`
- `swing_lab_carryover:3`
- `lifecycle_bucket_discovery:contamination_quarantine_live_auto_blocked:3`
- `lifecycle_bucket_discovery:contamination_quarantine_live_auto_blocked:3`
- `lifecycle_bucket_windows:rolling5d_missing`
- `lifecycle_bucket_windows:rolling10d_missing`
- `lifecycle_bucket_windows:mtd_missing`
- `swing_strategy_discovery:pending_future_quotes`
- `swing_lifecycle_decision_matrix:pending_future_quotes`
- `pattern_lab_ai_review_warning`
- `pattern_lab_propagation_audit_warning`
