# Threshold Cycle Daily EV Report - 2026-06-08

## Runtime Apply
- status: `auto_bounded_live_ready`
- runtime_change: `True`
- selected_families: `soft_stop_whipsaw_confirmation, score65_74_recovery_probe, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, lifecycle_decision_matrix_runtime`

## Daily EV
- completed: `25` / open: `0`
- win/loss: `12` / `13` (`48.0`%)
- avg_profit_rate: `-0.42`%
- realized_pnl_krw: `29366`
- full_fill_completed_avg_profit_rate: `-0.424`%

## Entry Funnel
- budget_pass_to_submitted: `32` / `15074` (`0.21`%)
- latency pass/block: `159` / `14908`
- latency submit routing: `latency_classifier_runtime_semantics_gap`
- latency recommended action: `reject` (`recovery_count=0 below floor=1658`)
- latency profile generation: `{'mode': 'grid_quantile_search', 'profile_count': 720, 'age_cap_ms': 1500, 'jitter_cap_ms': 1500, 'spread_cap_ratio': 0.012, 'counterfactual_sample_floor': 3, 'recovery_event_floor_ratio': 0.1}`
- safe/caution_normal/recovery: `0` / `0` / `0`
- recovery attempts/cf sample/cf ev: `0` / `0` / `None`%
- recovered/lost labels: `0` / `0`
- stale/broker override excluded: `0` / `0`
- full/partial fill: `25` / `0`

## Holding Exit
- holding_reviews: `5215`
- exit_signals: `411`
- holding_review_ms_p95: `2171.0`

## Scalp Simulator
- authority: `equal_weight` / fill_policy: `signal_inclusive_best_ask_v1`
- armed/filled/sold: `376` / `376` / `376`
- expired/unpriced/duplicate: `0` / `0` / `3431`
- entry_ai_price applied/skip: `208` / `0`
- submit_revalidation warning/block: `282` / `0`
- scale_in filled/unfilled: `0` / `0`
- overnight decision/sell/hold/carry_restored: `10` / `10` / `0` / `0`
- completed_profit_summary: `{'sample': 376, 'win_count': 96, 'loss_count': 280, 'avg_profit_rate': -1.4089, 'median_profit_rate': -2.13, 'downside_p10_profit_rate': -3.28, 'upside_p90_profit_rate': 1.55, 'win_rate': 0.2553, 'loss_rate': 0.7447, 'stddev_profit_rate': 2.5343}`
- post_sell_join: joined=`374` / pending=`2`
- post_sell_mfe_mae_10m: mfe=`3.6575`% / mae=`-5.2882`% / close=`0.01`%

## Missed Probe Counterfactual
- book: `scalp_score65_74_probe_counterfactual` / role: `missed_buy_probe_counterfactual`
- total/score65_74: `113` / `80`
- avg_expected_ev: `0.7753`% / score65_74_avg_expected_ev: `-0.2622`%
- actual_order_submitted: `False` / broker_order_forbidden: `True`
- authority: `missed_probe_ev_only_not_broker_execution`

## Scalp Entry ADM
- artifact: `/home/ubuntu/KORStockScan/data/report/scalp_entry_action_decision_matrix/scalp_entry_action_decision_matrix_2026-06-08.json`
- status: `warning` / authority: `entry_advisory_prompt_context_only`
- total/joined/floor: `338` / `158` / `20`
- prompt_applied_count: `119`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 338}`
- forced_action_counts: `{'-': 338}`
- missing_actions: `[]`
- zero_sample_actions: `['SKIP_STALE']`
- top_actions: `[{'action': 'BUY_NOW', 'sample_count': 2, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'WAIT_REQUOTE', 'sample_count': 15, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'BUY_DEFENSIVE', 'sample_count': 28, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'NO_BUY_AI', 'sample_count': 160, 'joined_sample': 53, 'source_quality_adjusted_ev_pct': -0.289}, {'action': 'SKIP_SOURCE_QUALITY', 'sample_count': 12, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}]`

## Lifecycle Decision Matrix
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-06-08.json`
- status: `pass` / version: `lifecycle_decision_matrix_v1_2026-06-08`
- total/joined: `25034` / `24122`
- policy_pass/promote_ready: `5` / `1`
- lifecycle_flow buckets/complete/runtime/workorders: `115` / `79` / `0` / `20`
- holding/exit buckets: `35` / `52`
- holding/exit workorders: `10` / `10`
- lifecycle identity missing/join_rate: `0` / `1.0`
- lifecycle complete_flow_rate: `0.0034`
- incomplete_flow_reason_counts: `{'missing_entry': 22936, 'missing_holding': 23389, 'missing_exit': 22692, 'postclose_exit_without_entry': 719, 'missing_submit': 23373, 'candidate_id_only': 22981, 'sim_record_id_only': 376}`
- fixed_threshold_roles: `{'hard_safety': ['broker_submit_guard', 'stale_quote_submit_block', 'price_freshness_guard', 'hard_stop', 'protect_stop', 'emergency_stop', 'account_order_cooldown_qty_guard'], 'baseline_prior': ['BUY_SCORE_THRESHOLD', 'VPW_MIN_SCORE', 'strength_momentum_cutoff', 'entry_score_cutoff'], 'bounded_tunable': ['SCALP_ENTRY_LATENCY_MAX_WS_AGE_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_WS_JITTER_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_SPREAD_RATIO_FOR_CAUTION', 'score65_74_recovery_probe', 'soft_stop_whipsaw_confirmation', 'holding_flow_override', 'scale_in_price_guard'], 'legacy_archive': ['fallback_scout_main', 'fallback_single', 'latency_fallback_split_entry', 'legacy_latency_composite', 'closed_shadow_axes']}`
- policy_entries: `[{'stage': 'entry', 'sample': 622, 'joined_sample': 166, 'stage_ev_composite_pct': 0.3266, 'confidence': 1.0, 'selected_action': 'BUY_DEFENSIVE', 'source_quality_gate': 'pass', 'promote_ready': True}, {'stage': 'submit', 'sample': 434, 'joined_sample': 376, 'stage_ev_composite_pct': -0.3636, 'confidence': 1.0, 'selected_action': 'NO_CHANGE', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'holding', 'sample': 386, 'joined_sample': 376, 'stage_ev_composite_pct': -0.9469, 'confidence': 1.0, 'selected_action': 'EXIT', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'scale_in', 'sample': 22511, 'joined_sample': 22510, 'stage_ev_composite_pct': -0.3299, 'confidence': 1.0, 'selected_action': 'NO_CHANGE', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'exit', 'sample': 1081, 'joined_sample': 694, 'stage_ev_composite_pct': -1.0085, 'confidence': 1.0, 'selected_action': 'EXIT', 'source_quality_gate': 'pass', 'promote_ready': False}]`

## Lifecycle Bucket Discovery
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-06-08.json`
- status: `pass` / human_intervention_required: `False`
- candidates/surfaced: `500` / `237`
- sim_auto/live_auto/new_bucket: `118` / `0` / `0`
- role/window: `new_pattern_detection` / `same_day_source_bundle_plus_rolling_threshold_cycle_consumer`
- parent_count/granularity/conflict: `53` / `target_pass` / `12`
- state_counts: `{'source_only_keep_collecting': 370, 'lifecycle_flow_sim_probe_candidate': 8, 'sim_auto_approved': 118, 'entry_only_sim_auto_approved': 4}`
- top_surfaced: `[{'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': 1.3597}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': 1.3089}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': 1.8776}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': 1.7838}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': 6.0932}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': 1.393}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': 1.1746}, {'bucket_id': 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'stage': 'lifecycle_flow', 'classification_state': 'source_only_keep_collecting', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 1, 'source_quality_adjusted_ev_pct': 1.3499}]`

## Lifecycle Bucket Windows
- promotion_window: `mtd`
- confirmation_windows: `['rolling5d', 'rolling10d']`
- windows: `{'rolling5d': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-06-08_rolling5d.json', 'window_role': 'rolling_confirmation', 'window_policy': 'rolling5d', 'status': 'pass', 'parent_bucket_count': 31, 'selected_parent_level': 'L1_broad', 'parent_granularity_status': 'target_pass', 'absorbed_child_count': 217, 'absorbed_sample_count': 38087, 'child_conflict_warning_count': 12, 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'parsed'}, 'rolling10d': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-06-08_rolling10d.json', 'window_role': 'rolling_confirmation', 'window_policy': 'rolling10d', 'status': 'pass', 'parent_bucket_count': 31, 'selected_parent_level': 'L1_broad', 'parent_granularity_status': 'target_pass', 'absorbed_child_count': 217, 'absorbed_sample_count': 38087, 'child_conflict_warning_count': 12, 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'parsed'}, 'mtd': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-06-08_mtd.json', 'window_role': 'promotion_confirmation', 'window_policy': 'mtd', 'status': 'pass', 'parent_bucket_count': 31, 'selected_parent_level': 'L1_broad', 'parent_granularity_status': 'target_pass', 'absorbed_child_count': 217, 'absorbed_sample_count': 38087, 'child_conflict_warning_count': 12, 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'parsed'}}`

## Lifecycle AI Context
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_ai_context/lifecycle_ai_context_2026-06-08.json`
- context_version: `lifecycle_ai_context_v1_2026-06-08` / authority: `ai_advisory_prompt_context_only`
- prompt_stage_count: `3` / runtime_effect: `False`
- stage_contexts: `[{'stage': 'entry', 'prompt_injection_allowed': True, 'policy_key': 'entry:weighted_adm_v1', 'alignment_hint': 'BUY_DEFENSIVE', 'context_contribution_score': -0.13, 'attribution_quality_status': 'observational_only_pending_outcome'}, {'stage': 'submit', 'prompt_injection_allowed': False, 'policy_key': 'submit:weighted_adm_v1', 'alignment_hint': 'NO_CHANGE', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'holding', 'prompt_injection_allowed': True, 'policy_key': 'holding:weighted_adm_v1', 'alignment_hint': 'EXIT', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'scale_in', 'prompt_injection_allowed': False, 'policy_key': 'scale_in:weighted_adm_v1', 'alignment_hint': 'NO_CHANGE', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'exit', 'prompt_injection_allowed': True, 'policy_key': 'exit:weighted_adm_v1', 'alignment_hint': 'EXIT', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}]`

## Lifecycle AI Context Attribution
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_ai_context_attribution/lifecycle_ai_context_attribution_2026-06-08.json`
- eligible/applied/skipped: `2421` / `2421` / `0`
- replay_budget: `30`
- implementation_status: `implemented`
- stage_attribution: `{'entry': {'context_contribution_score': -0.13, 'bounded_auxiliary_weight': -0.0195, 'attribution_quality_status': 'observational_only_pending_outcome', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': 0.3143, 'no_context_replay_observed': 0}, 'submit': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'holding': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'scale_in': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'exit': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}}`

## Institutional Flow Context
- artifact: `/home/ubuntu/KORStockScan/data/report/institutional_flow_context/institutional_flow_context_2026-06-08.json`
- status: `pass` / authority: `source_only_lifecycle_feature`
- rows ok/partial/missing/token_error: `120` / `0` / `0` / `0`
- join_rate_pct: `100.0`
- source_mix: `{'ka10059+ka10061': 120}`
- top_net_buy: `[{'stock_code': '001740', 'smart_money_net': 1958783, 'foreign_net_roll5': 2181793, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}, {'stock_code': '035420', 'smart_money_net': 1735284, 'foreign_net_roll5': 0, 'inst_net_roll5': 2407377, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '010170', 'smart_money_net': 602228, 'foreign_net_roll5': 1605699, 'inst_net_roll5': 336759, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '279570', 'smart_money_net': 597316, 'foreign_net_roll5': 0, 'inst_net_roll5': 1909644, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '080220', 'smart_money_net': 423863, 'foreign_net_roll5': 425442, 'inst_net_roll5': 188819, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '064400', 'smart_money_net': 366648, 'foreign_net_roll5': 0, 'inst_net_roll5': 0, 'regime': 'UNKNOWN'}, {'stock_code': '034220', 'smart_money_net': 307329, 'foreign_net_roll5': 1878669, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}, {'stock_code': '038500', 'smart_money_net': 272311, 'foreign_net_roll5': 1759663, 'inst_net_roll5': 26660, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '425040', 'smart_money_net': 226159, 'foreign_net_roll5': 14683, 'inst_net_roll5': 101002, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '090710', 'smart_money_net': 223470, 'foreign_net_roll5': 1100379, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}]`

## Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-06-08.json`
- fresh: gemini=`False` claude=`True`
- consensus/orders/family_candidates: `0` / `7` / `0`

## Swing Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_2026-06-08.json`
- deepseek_lab_available: `True`
- findings/orders: `5` / `4`
- data_quality_warnings: `1`
- top_level_data_quality_warnings: `0`
- resolved_data_quality_warnings: `1`
- ofi_qi_stale_missing_unique_records: `23`
- ofi_qi_stale_missing_reasons: `{'micro_missing': 16275, 'micro_stale': 0, 'observer_unhealthy': 3563, 'micro_not_ready': 16249, 'state_insufficient': 16249}`
- ofi_qi_stale_missing_reason_combinations: `{'micro_not_ready+state_insufficient': 9, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 3528, 'micro_missing+observer_unhealthy': 35, 'micro_missing+micro_not_ready+state_insufficient': 12712}`
- ofi_qi_stale_missing_reason_combination_unique_records: `{'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 18, 'micro_missing+observer_unhealthy': 1, 'micro_missing+micro_not_ready+state_insufficient': 22}`
- ofi_qi_observer_unhealthy_overlap: `{'observer_unhealthy_total': 3563, 'observer_unhealthy_with_other_reason': 3563, 'observer_unhealthy_only': 0}`
- source_quality_blocked_families: `[{'family': 'swing_entry_ofi_qi_execution_quality', 'stage': 'entry', 'metric_role': 'source_quality_gate', 'decision_authority': 'swing_pattern_lab_analysis_workorder_source_only', 'window_policy': 'same_day_pattern_lab_source_quality', 'sample_floor': 1, 'primary_decision_metric': 'source_quality_gate', 'source_quality_gate': 'swing_orderbook_micro_context_ready_or_blocker_provenance_recorded', 'source_contract_version': 'swing_micro_context_source_quality_v1', 'source_contract_status': 'implemented', 'source_quality_blockers': ['entry_ofi_qi_invalid_micro_context'], 'invalid_micro_context_unique_record_count': 22, 'invalid_reason_combination_unique_record_counts': {'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 18, 'micro_missing+observer_unhealthy': 1, 'micro_missing+micro_not_ready+state_insufficient': 22}, 'reason_counts': {'micro_missing': 16275, 'micro_stale': 0, 'observer_unhealthy': 3563, 'micro_not_ready': 16249, 'state_insufficient': 16249}, 'reason_combination_counts': {'micro_not_ready+state_insufficient': 9, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 3528, 'micro_missing+observer_unhealthy': 35, 'micro_missing+micro_not_ready+state_insufficient': 12712}, 'observer_unhealthy_overlap': {'observer_unhealthy_total': 3563, 'observer_unhealthy_with_other_reason': 3563, 'observer_unhealthy_only': 0}, 'automation_input': True, 'runtime_effect': False, 'allowed_runtime_apply': False, 'forbidden_uses': ['swing_real_order_enable', 'one_share_real_canary', 'scale_in_real_canary', 'runtime_threshold_mutation', 'provider_route_change', 'bot_restart', 'recommendation_history_replace']}, {'family': 'swing_scale_in_ofi_qi_confirmation', 'stage': 'scale_in', 'metric_role': 'source_quality_gate', 'decision_authority': 'swing_pattern_lab_analysis_workorder_source_only', 'window_policy': 'same_day_pattern_lab_source_quality', 'sample_floor': 1, 'primary_decision_metric': 'source_quality_gate', 'source_quality_gate': 'swing_orderbook_micro_context_ready_or_blocker_provenance_recorded', 'source_contract_version': 'swing_micro_context_source_quality_v1', 'source_contract_status': 'implemented', 'source_quality_blockers': ['scale_in_ofi_qi_invalid_micro_context'], 'invalid_micro_context_unique_record_count': 2, 'invalid_reason_combination_unique_record_counts': {'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 18, 'micro_missing+observer_unhealthy': 1, 'micro_missing+micro_not_ready+state_insufficient': 22}, 'reason_counts': {'micro_missing': 16275, 'micro_stale': 0, 'observer_unhealthy': 3563, 'micro_not_ready': 16249, 'state_insufficient': 16249}, 'reason_combination_counts': {'micro_not_ready+state_insufficient': 9, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 3528, 'micro_missing+observer_unhealthy': 35, 'micro_missing+micro_not_ready+state_insufficient': 12712}, 'observer_unhealthy_overlap': {'observer_unhealthy_total': 3563, 'observer_unhealthy_with_other_reason': 3563, 'observer_unhealthy_only': 0}, 'automation_input': True, 'runtime_effect': False, 'allowed_runtime_apply': False, 'forbidden_uses': ['swing_real_order_enable', 'one_share_real_canary', 'scale_in_real_canary', 'runtime_threshold_mutation', 'provider_route_change', 'bot_restart', 'recommendation_history_replace']}]`
- carryover_warnings: `0`
- population_split_available: `True`

## Swing Strategy Discovery Sim
- artifact: `/home/ubuntu/KORStockScan/data/report/swing_strategy_discovery_ev/swing_strategy_discovery_ev_2026-06-08.json`
- authority: `swing_sim_exploration_only` / source_only: `True`
- candidate/arm/policy_exit_rows: `232` / `1562` / `1562`
- labeled/pending_future_quotes: `52` / `1455`
- implementation_status: `implemented`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- surviving/avoid_bucket_count: `1` / `7`
- runtime_effect: `False`

## Pipeline Event Verbosity
- artifact: `/home/ubuntu/KORStockScan/data/report/pipeline_event_verbosity/pipeline_event_verbosity_2026-06-08.json`
- state: `v2_shadow_pending_flush`
- recommended_workorder_state: `observe_pending_next_flush`
- high_volume_line_count: `44285`
- high_volume_byte_share_pct: `6.66`
- parity_ok: `False`
- suppress_eligibility: `False`

## Codebase Performance Workorder Source
- artifact: `/home/ubuntu/KORStockScan/data/report/codebase_performance_workorder/codebase_performance_workorder_2026-06-08.json`
- authority: `ops_performance_workorder_source`
- accepted/deferred/rejected: `7` / `3` / `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`

## Pattern Lab Audits
- currentness: status=`pass` fail=`0` orders=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-06-08.json`
- ai_review: status=`warning` orders=`6` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_ai_review/pattern_lab_ai_review_2026-06-08.json`
- time_window_regime_counterfactual: status=`pass` artifact=`/home/ubuntu/KORStockScan/data/report/time_window_regime_counterfactual/time_window_regime_counterfactual_2026-06-08.json`
- producer_gap_discovery: status=`pass` orders=`0` artifact=`/home/ubuntu/KORStockScan/data/report/producer_gap_discovery/producer_gap_discovery_2026-06-08.json`
- stage_hook_workorder_discovery: status=`pass` orders=`0` artifact=`/home/ubuntu/KORStockScan/data/report/stage_hook_workorder_discovery/stage_hook_workorder_discovery_2026-06-08.json`
- propagation: status=`pass` fail=`0` warnings=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_2026-06-08.json`

## Swing Runtime Approval
- request_report: `/home/ubuntu/KORStockScan/data/report/swing_runtime_approval/swing_runtime_approval_2026-06-05.json`
- approval_artifact: `-`
- requested/approved/live_dry_run: `0` / `0` / `0`
- dry_run_forced: `False`
- legacy_phase0_real_canary_ignored: `False`
- blocked: `[]`

## Code Improvement Workorder
- artifact: `/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-06-08.json`
- markdown: `/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-06-08.md`
- selected_order_count: `106`
- decision_counts: `{'attach_existing_family': 127, 'design_family_candidate': 5, 'defer_evidence': 7, 'reject': 2}`

## Approval Requests
- `position_sizing_cap_release` sample=`63/30` reason=`window_policy primary=rolling_10d 기준 재평가: 1주 cap 해제 efficient trade-off 기준 충족(score=0.18/0.70): 자동 적용하지 않고 사용자 승인 요청 artifact로만 승격한다.` contract=`final_user_approval_required` live_ready=`False`

## Swing Approval Requests
- none

## Calibration Decisions
## Code Improvement Top Orders
- `order_latency_canary_tag_완화_1축_canary_승인` decision=`attach_existing_family` subsystem=`runtime_instrumentation`
- `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_10_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_submit_submit_c_a680eadf` decision=`attach_existing_family` subsystem=`lifecycle_decision_matrix`
- `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_11_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_submit_submit_c_a680eadf` decision=`attach_existing_family` subsystem=`lifecycle_decision_matrix`

- `soft_stop_whipsaw_confirmation`: `adjust_up` sample=`6602/10`
- `holding_flow_ofi_smoothing`: `hold` sample=`1459/20`
- `protect_trailing_smoothing`: `adjust_down` sample=`39/20`
- `trailing_continuation`: `freeze` sample=`335/20`
- `market_regime_continuous_thresholds`: `hold_sample` sample=`3/10`
- `pre_submit_price_guard`: `hold_sample` sample=`14908/20`
- `score65_74_recovery_probe`: `hold` sample=`167/20`
- `strength_momentum_soft_gate_p1`: `hold` sample=`32848/20`
- `overbought_pullback_guard_p1`: `hold` sample=`8421/20`
- `liquidity_pre_submit_guard_p1`: `hold` sample=`3513/20`
- `bad_entry_refined_canary`: `adjust_up` sample=`68648/10`
- `holding_exit_decision_matrix_advisory`: `hold_no_edge` sample=`11/1`
- `lifecycle_decision_matrix_runtime`: `adjust_up` sample=`25034/20`
- `scale_in_price_guard`: `hold` sample=`344/20`
- `position_sizing_cap_release`: `approval_required` sample=`63/30`
- `position_sizing_dynamic_formula`: `hold_sample` sample=`63/30`

## Warnings
- `scalp_entry_adm:unknown_bucket_source_quality_gap`
- `lifecycle_bucket_discovery:source_contract_drift_warning`
- `lifecycle_bucket_discovery:source_contract_drift_warning`
- `swing_strategy_discovery:pending_future_quotes`
- `swing_strategy_discovery:clean_tuning_baseline_swing_discovery_lookback_filtered`
- `swing_lifecycle_decision_matrix:pending_future_quotes`
- `swing_lifecycle_decision_matrix:clean_tuning_baseline_swing_discovery_lookback_filtered`
- `pattern_lab_ai_review_warning`
- `pattern_lab_ai_review_ai_review_followup_required`
