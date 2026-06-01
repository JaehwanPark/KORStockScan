# Threshold Cycle Daily EV Report - 2026-05-22

## Runtime Apply
- status: `auto_bounded_live_ready`
- runtime_change: `True`
- selected_families: `soft_stop_whipsaw_confirmation, score65_74_recovery_probe, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, lifecycle_decision_matrix_runtime, swing_one_share_real_canary_phase0, swing_gatekeeper_reject_cooldown`

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
- latency profile generation: `{'mode': 'grid_quantile_search', 'profile_count': 378, 'age_cap_ms': 1500, 'jitter_cap_ms': 1500, 'spread_cap_ratio': 0.012, 'counterfactual_sample_floor': 3, 'recovery_event_floor_ratio': 0.1}`
- safe/caution_normal/recovery: `0` / `1` / `0`
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
- armed/filled/sold: `125` / `125` / `123`
- expired/unpriced/duplicate: `0` / `0` / `49`
- entry_ai_price applied/skip: `2` / `1`
- submit_revalidation warning/block: `117` / `0`
- scale_in filled/unfilled: `0` / `0`
- overnight decision/sell/hold/carry_restored: `20` / `20` / `0` / `0`
- completed_profit_summary: `{'sample': 123, 'win_count': 46, 'loss_count': 76, 'avg_profit_rate': -0.5776, 'median_profit_rate': -0.6, 'downside_p10_profit_rate': -2.66, 'upside_p90_profit_rate': 1.66, 'win_rate': 0.374, 'loss_rate': 0.6179, 'stddev_profit_rate': 1.9006}`
- post_sell_join: joined=`111` / pending=`12`
- post_sell_mfe_mae_10m: mfe=`1.4753`% / mae=`-4.3798`% / close=`0.0908`%

## Missed Probe Counterfactual
- book: `-` / role: `-`
- total/score65_74: `None` / `None`
- avg_expected_ev: `None`% / score65_74_avg_expected_ev: `None`%
- actual_order_submitted: `None` / broker_order_forbidden: `None`
- authority: `-`

## Scalp Entry ADM
- artifact: `/home/ubuntu/KORStockScan/data/report/scalp_entry_action_decision_matrix/scalp_entry_action_decision_matrix_2026-05-22.json`
- status: `pass` / authority: `entry_advisory_prompt_context_only`
- total/joined/floor: `1327` / `102` / `20`
- prompt_applied_count: `1132`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 1327}`
- forced_action_counts: `{'-': 1327}`
- missing_actions: `[]`
- zero_sample_actions: `['BUY_NOW', 'SKIP_STALE', 'BUY_DEFENSIVE']`
- top_actions: `[{'action': 'WAIT_REQUOTE', 'sample_count': 5, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'NO_BUY_AI', 'sample_count': 1317, 'joined_sample': 102, 'source_quality_adjusted_ev_pct': -0.0523}, {'action': 'SKIP_SOURCE_QUALITY', 'sample_count': 1, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'SKIP_PRE_SUBMIT_SAFETY', 'sample_count': 4, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}]`

## Lifecycle Decision Matrix
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-05-22.json`
- status: `pass` / version: `lifecycle_decision_matrix_v1_2026-05-22`
- total/joined: `35193` / `33596`
- policy_pass/promote_ready: `5` / `0`
- lifecycle_flow buckets/complete/runtime/workorders: `60` / `0` / `0` / `20`
- holding/exit buckets: `27` / `74`
- holding/exit workorders: `10` / `10`
- lifecycle identity missing/join_rate: `0` / `1.0`
- lifecycle complete_flow_rate: `0.0`
- incomplete_flow_reason_counts: `{'missing_submit': 21259, 'missing_holding': 21263, 'missing_exit': 21106, 'missing_entry': 19960}`
- fixed_threshold_roles: `{'hard_safety': ['broker_submit_guard', 'stale_quote_submit_block', 'price_freshness_guard', 'hard_stop', 'protect_stop', 'emergency_stop', 'account_order_cooldown_qty_guard'], 'baseline_prior': ['BUY_SCORE_THRESHOLD', 'VPW_MIN_SCORE', 'strength_momentum_cutoff', 'entry_score_cutoff'], 'bounded_tunable': ['SCALP_ENTRY_LATENCY_MAX_WS_AGE_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_WS_JITTER_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_SPREAD_RATIO_FOR_CAUTION', 'score65_74_recovery_probe', 'soft_stop_whipsaw_confirmation', 'holding_flow_override', 'scale_in_price_guard'], 'legacy_archive': ['fallback_scout_main', 'fallback_single', 'latency_fallback_split_entry', 'legacy_latency_composite', 'closed_shadow_axes']}`
- policy_entries: `[{'stage': 'entry', 'sample': 1486, 'joined_sample': 102, 'stage_ev_composite_pct': -0.3299, 'confidence': 0.7001, 'selected_action': 'WAIT_REQUOTE', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'submit', 'sample': 129, 'joined_sample': 123, 'stage_ev_composite_pct': -0.2676, 'confidence': 1.0, 'selected_action': 'NO_CHANGE', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'holding', 'sample': 145, 'joined_sample': 123, 'stage_ev_composite_pct': -0.4473, 'confidence': 1.0, 'selected_action': 'EXIT', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'scale_in', 'sample': 32811, 'joined_sample': 32785, 'stage_ev_composite_pct': -0.159, 'confidence': 1.0, 'selected_action': 'NO_CHANGE', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'exit', 'sample': 622, 'joined_sample': 463, 'stage_ev_composite_pct': -0.428, 'confidence': 1.0, 'selected_action': 'EXIT', 'source_quality_gate': 'pass', 'promote_ready': False}]`

## Lifecycle Bucket Discovery
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-05-22.json`
- status: `pass` / human_intervention_required: `False`
- candidates/surfaced: `379` / `120`
- sim_auto/live_auto/new_bucket: `119` / `1` / `0`
- role/window: `new_pattern_detection` / `daily_lifecycle_bucket_discovery_with_preopen_auto_apply`
- parent_count/granularity/conflict: `0` / `None` / `0`
- state_counts: `{'live_auto_apply_ready': 1, 'sim_auto_approved': 119, 'source_only_keep_collecting': 259}`
- top_surfaced: `[{'bucket_id': 'entry:combo_entry_spot:score_score_66_69_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_unknown', 'stage': 'entry', 'classification_state': 'live_auto_apply_ready', 'live_auto_apply_family': 'entry_wait6579_score66_69_recovery_gate_v1', 'recommended_action': 'relax_or_recover', 'joined_sample': 24, 'source_quality_adjusted_ev_pct': 2.1843}, {'bucket_id': 'entry:chosen_action:no_buy_ai', 'stage': 'entry', 'classification_state': 'sim_auto_approved', 'live_auto_apply_family': None, 'recommended_action': 'tighten_or_exclude', 'joined_sample': 102, 'source_quality_adjusted_ev_pct': -0.3299}, {'bucket_id': 'entry:source_stage:scalp_entry_action_decision_snapshot', 'stage': 'entry', 'classification_state': 'sim_auto_approved', 'live_auto_apply_family': None, 'recommended_action': 'tighten_or_exclude', 'joined_sample': 102, 'source_quality_adjusted_ev_pct': -0.3299}, {'bucket_id': 'entry:stale_bucket:fresh', 'stage': 'entry', 'classification_state': 'sim_auto_approved', 'live_auto_apply_family': None, 'recommended_action': 'tighten_or_exclude', 'joined_sample': 80, 'source_quality_adjusted_ev_pct': -0.3696}, {'bucket_id': 'entry:source_stage:wait6579_ev_cohort', 'stage': 'entry', 'classification_state': 'sim_auto_approved', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 35, 'source_quality_adjusted_ev_pct': 2.3199}, {'bucket_id': 'entry:stale_bucket:fresh_or_unflagged', 'stage': 'entry', 'classification_state': 'sim_auto_approved', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 35, 'source_quality_adjusted_ev_pct': 2.3199}, {'bucket_id': 'entry:exit_rule:scalp_trailing_take_profit', 'stage': 'entry', 'classification_state': 'sim_auto_approved', 'live_auto_apply_family': None, 'recommended_action': 'tighten_or_exclude', 'joined_sample': 34, 'source_quality_adjusted_ev_pct': -0.3781}, {'bucket_id': 'entry:time_bucket:time_1000_1200', 'stage': 'entry', 'classification_state': 'sim_auto_approved', 'live_auto_apply_family': None, 'recommended_action': 'tighten_or_exclude', 'joined_sample': 33, 'source_quality_adjusted_ev_pct': -0.8942}]`

## Lifecycle Bucket Windows
- promotion_window: `mtd`
- confirmation_windows: `['rolling5d', 'rolling10d']`
- windows: `{'rolling5d': {'available': False, 'artifact': None, 'window_role': 'rolling_confirmation', 'window_policy': 'rolling5d', 'status': 'missing', 'parent_bucket_count': 0, 'selected_parent_level': None, 'parent_granularity_status': None, 'absorbed_child_count': 0, 'absorbed_sample_count': 0, 'child_conflict_warning_count': 0, 'live_auto_apply_ready_count': 0, 'source_contract_status': None, 'ai_two_pass_review_status': None}, 'rolling10d': {'available': False, 'artifact': None, 'window_role': 'rolling_confirmation', 'window_policy': 'rolling10d', 'status': 'missing', 'parent_bucket_count': 0, 'selected_parent_level': None, 'parent_granularity_status': None, 'absorbed_child_count': 0, 'absorbed_sample_count': 0, 'child_conflict_warning_count': 0, 'live_auto_apply_ready_count': 0, 'source_contract_status': None, 'ai_two_pass_review_status': None}, 'mtd': {'available': False, 'artifact': None, 'window_role': 'promotion_confirmation', 'window_policy': 'mtd', 'status': 'missing', 'parent_bucket_count': 0, 'selected_parent_level': None, 'parent_granularity_status': None, 'absorbed_child_count': 0, 'absorbed_sample_count': 0, 'child_conflict_warning_count': 0, 'live_auto_apply_ready_count': 0, 'source_contract_status': None, 'ai_two_pass_review_status': None}}`

## Lifecycle AI Context
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_ai_context/lifecycle_ai_context_2026-05-22.json`
- context_version: `lifecycle_ai_context_v1_2026-05-22` / authority: `ai_advisory_prompt_context_only`
- prompt_stage_count: `3` / runtime_effect: `False`
- stage_contexts: `[{'stage': 'entry', 'prompt_injection_allowed': True, 'policy_key': 'entry:weighted_adm_v1', 'alignment_hint': 'BUY_DEFENSIVE', 'context_contribution_score': 0.3478, 'attribution_quality_status': 'observational_only_pending_outcome'}, {'stage': 'submit', 'prompt_injection_allowed': False, 'policy_key': 'submit:weighted_adm_v1', 'alignment_hint': 'NO_CHANGE', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'holding', 'prompt_injection_allowed': True, 'policy_key': 'holding:weighted_adm_v1', 'alignment_hint': 'EXIT', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'scale_in', 'prompt_injection_allowed': False, 'policy_key': 'scale_in:weighted_adm_v1', 'alignment_hint': 'NO_CHANGE', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'exit', 'prompt_injection_allowed': True, 'policy_key': 'exit:weighted_adm_v1', 'alignment_hint': 'EXIT', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}]`

## Lifecycle AI Context Attribution
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_ai_context_attribution/lifecycle_ai_context_attribution_2026-05-22.json`
- eligible/applied/skipped: `3237` / `3237` / `0`
- replay_budget: `30`
- implementation_status: `implemented`
- stage_attribution: `{'entry': {'context_contribution_score': 0.3478, 'bounded_auxiliary_weight': 0.0522, 'attribution_quality_status': 'observational_only_pending_outcome', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': 0.9969, 'no_context_replay_observed': 0}, 'submit': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'holding': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'scale_in': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'exit': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}}`

## Institutional Flow Context
- artifact: `/home/ubuntu/KORStockScan/data/report/institutional_flow_context/institutional_flow_context_2026-05-22.json`
- status: `pass` / authority: `source_only_lifecycle_feature`
- rows ok/partial/missing/token_error: `120` / `0` / `0` / `0`
- join_rate_pct: `100.0`
- source_mix: `{'ka10059+ka10061': 120}`
- top_net_buy: `[{'stock_code': '069540', 'smart_money_net': 5888940, 'foreign_net_roll5': 4362265, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}, {'stock_code': '034220', 'smart_money_net': 3297688, 'foreign_net_roll5': 3330662, 'inst_net_roll5': 196025, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '050890', 'smart_money_net': 1809007, 'foreign_net_roll5': 2493467, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}, {'stock_code': '036540', 'smart_money_net': 1155545, 'foreign_net_roll5': 4766791, 'inst_net_roll5': 56671, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '088350', 'smart_money_net': 1086488, 'foreign_net_roll5': 1753025, 'inst_net_roll5': 4195272, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '064400', 'smart_money_net': 632665, 'foreign_net_roll5': 0, 'inst_net_roll5': 408612, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '032500', 'smart_money_net': 582864, 'foreign_net_roll5': 842641, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}, {'stock_code': '036710', 'smart_money_net': 546007, 'foreign_net_roll5': 491026, 'inst_net_roll5': 196376, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '003490', 'smart_money_net': 533874, 'foreign_net_roll5': 1053077, 'inst_net_roll5': 803838, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '011200', 'smart_money_net': 502761, 'foreign_net_roll5': 2619076, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}]`

## Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-05-22.json`
- fresh: gemini=`True` claude=`True`
- consensus/orders/family_candidates: `6` / `13` / `3`

## Swing Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_2026-05-22.json`
- deepseek_lab_available: `True`
- findings/orders: `5` / `4`
- data_quality_warnings: `1`
- top_level_data_quality_warnings: `1`
- resolved_data_quality_warnings: `0`
- ofi_qi_stale_missing_unique_records: `0`
- ofi_qi_stale_missing_reasons: `{'micro_missing': 517, 'micro_stale': 0, 'observer_unhealthy': 0, 'micro_not_ready': 1, 'state_insufficient': 1}`
- ofi_qi_stale_missing_reason_combinations: `{'micro_missing': 516, 'micro_missing+micro_not_ready+state_insufficient': 1}`
- ofi_qi_stale_missing_reason_combination_unique_records: `{}`
- ofi_qi_observer_unhealthy_overlap: `{'observer_unhealthy_total': 0, 'observer_unhealthy_with_other_reason': 0, 'observer_unhealthy_only': 0}`
- source_quality_blocked_families: `[]`
- carryover_warnings: `0`
- population_split_available: `True`

## Swing Strategy Discovery Sim
- artifact: `/home/ubuntu/KORStockScan/data/report/swing_strategy_discovery_ev/swing_strategy_discovery_ev_2026-05-22.json`
- authority: `swing_sim_exploration_only` / source_only: `True`
- candidate/arm/policy_exit_rows: `150` / `1200` / `1200`
- labeled/pending_future_quotes: `32` / `1118`
- implementation_status: `implemented`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- surviving/avoid_bucket_count: `1` / `1`
- runtime_effect: `False`

## Pipeline Event Verbosity
- artifact: `/home/ubuntu/KORStockScan/data/report/pipeline_event_verbosity/pipeline_event_verbosity_2026-05-22.json`
- state: `v2_shadow_pending_flush`
- recommended_workorder_state: `observe_pending_next_flush`
- high_volume_line_count: `285741`
- high_volume_byte_share_pct: `50.05`
- parity_ok: `False`
- suppress_eligibility: `False`

## Codebase Performance Workorder Source
- artifact: `/home/ubuntu/KORStockScan/data/report/codebase_performance_workorder/codebase_performance_workorder_2026-05-22.json`
- authority: `ops_performance_workorder_source`
- accepted/deferred/rejected: `7` / `3` / `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`

## Pattern Lab Audits
- currentness: status=`pass` fail=`0` orders=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-05-22.json`
- ai_review: status=`warning` orders=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_ai_review/pattern_lab_ai_review_2026-05-22.json`
- time_window_regime_counterfactual: status=`missing` artifact=`-`
- producer_gap_discovery: status=`missing` orders=`0` artifact=`-`
- stage_hook_workorder_discovery: status=`missing` orders=`0` artifact=`-`
- propagation: status=`pass` fail=`0` warnings=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_2026-05-22.json`

## Swing Runtime Approval
- request_report: `/home/ubuntu/KORStockScan/data/report/swing_runtime_approval/swing_runtime_approval_2026-05-21.json`
- approval_artifact: `/home/ubuntu/KORStockScan/data/threshold_cycle/approvals/swing_runtime_approvals_2026-05-21.json`
- requested/approved/live_dry_run: `3` / `3` / `2`
- dry_run_forced: `True`
- real_canary_policy: `swing_one_share_real_canary_phase0`
- one_share_real_canary_artifact: `/home/ubuntu/KORStockScan/data/threshold_cycle/approvals/swing_one_share_real_canary_2026-05-21.json`
- selected_one_share_real_canary: `1`
- real_order_allowed_actions: `BUY_INITIAL, SELL_CLOSE`
- sim_only_actions: `AVG_DOWN, PYRAMID, SCALE_IN`
- scale_in_real_canary_policy: `swing_scale_in_real_canary_phase0`
- selected_scale_in_real_canary: `0`
- scale_in_real_execution_quality: `{'one_share_canary_selected': 1, 'scale_in_canary_selected': 0, 'execution_quality_source': 'real_only', 'sim_probe_ev_source': 'separate_from_broker_execution_quality'}`
- blocked: `[]`

## Code Improvement Workorder
- artifact: `/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-05-22.json`
- markdown: `/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-05-22.md`
- selected_order_count: `71`
- decision_counts: `{'implement_now': 23, 'attach_existing_family': 66, 'design_family_candidate': 7, 'defer_evidence': 10, 'reject': 3}`

## Approval Requests
- none

## Swing Approval Requests
- `swing_model_floor` approval_id=`swing_runtime_approval:2026-05-21:swing_model_floor` score=`0.955` target_env_keys=`['SWING_FLOOR_BULL', 'SWING_FLOOR_BEAR']`
- `swing_gatekeeper_reject_cooldown` approval_id=`swing_runtime_approval:2026-05-21:swing_gatekeeper_reject_cooldown` score=`0.955` target_env_keys=`['ML_GATEKEEPER_REJECT_COOLDOWN']`
- `swing_one_share_real_canary_phase0` approval_id=`swing_one_share_real_canary:2026-05-21:phase0` score=`0.955` target_env_keys=`['SWING_ONE_SHARE_REAL_CANARY_ENABLED', 'SWING_ONE_SHARE_REAL_CANARY_ALLOWED_CODES', 'SWING_ONE_SHARE_REAL_CANARY_MAX_QTY', 'SWING_ONE_SHARE_REAL_CANARY_MAX_NEW_ENTRIES_PER_DAY', 'SWING_ONE_SHARE_REAL_CANARY_MAX_OPEN_POSITIONS', 'SWING_ONE_SHARE_REAL_CANARY_MAX_TOTAL_NOTIONAL_KRW', 'SWING_ONE_SHARE_REAL_CANARY_REQUIRE_APPROVAL_ARTIFACT']`

## Calibration Decisions
## Code Improvement Top Orders
- `order_entry_submit_drought_auto_resolution` decision=`implement_now` subsystem=`runtime_instrumentation`
- `order_entry_broker_receipt_contract_gap_review` decision=`implement_now` subsystem=`runtime_instrumentation`
- `order_entry_fill_quality_contract_gap_review` decision=`implement_now` subsystem=`runtime_instrumentation`

## Pattern Lab Top Findings
- `AI threshold dominance` route=`existing_family` family=`score65_74_recovery_probe`
- `AI threshold miss EV recovery` route=`existing_family` family=`score65_74_recovery_probe`
- `Budget pass without submit` route=`auto_family_candidate` family=`-`

- `soft_stop_whipsaw_confirmation`: `adjust_up` sample=`6103/10`
- `holding_flow_ofi_smoothing`: `hold` sample=`3425/20`
- `protect_trailing_smoothing`: `adjust_down` sample=`96/20`
- `trailing_continuation`: `freeze` sample=`185/20`
- `market_regime_continuous_thresholds`: `hold_sample` sample=`2/10`
- `pre_submit_price_guard`: `hold_sample` sample=`82/20`
- `score65_74_recovery_probe`: `adjust_up` sample=`152/20`
- `strength_momentum_soft_gate_p1`: `hold` sample=`200027/20`
- `overbought_pullback_guard_p1`: `hold` sample=`116572/20`
- `liquidity_pre_submit_guard_p1`: `hold` sample=`10903/20`
- `bad_entry_refined_canary`: `adjust_up` sample=`47899/10`
- `holding_exit_decision_matrix_advisory`: `hold_no_edge` sample=`5/1`
- `lifecycle_decision_matrix_runtime`: `adjust_up` sample=`35228/20`
- `scale_in_price_guard`: `hold` sample=`666/20`
- `position_sizing_cap_release`: `hold_sample` sample=`42/30`
- `position_sizing_dynamic_formula`: `hold_sample` sample=`3/30`

## Warnings
- `trade_review_missing`
- `performance_tuning_missing`
- `swing_lab_dq:OFI/QI stale/missing ratio: 0.915 (517/565); reasons: micro_missing=517, micro_not_ready=1, state_insufficient=1`
- `lifecycle_bucket_discovery:ai_review_provider_disabled`
- `lifecycle_bucket_discovery:ai_two_pass_review_disabled_live_auto_deferred_to_post_apply`
- `lifecycle_bucket_discovery:ai_review_provider_disabled`
- `lifecycle_bucket_discovery:ai_two_pass_review_disabled_live_auto_deferred_to_post_apply`
- `lifecycle_bucket_windows:rolling5d_missing`
- `lifecycle_bucket_windows:rolling10d_missing`
- `lifecycle_bucket_windows:mtd_missing`
- `swing_strategy_discovery:pending_future_quotes`
- `swing_lifecycle_decision_matrix:pending_future_quotes`
- `pattern_lab_ai_review_warning`
- `time_window_regime_counterfactual_missing`
- `producer_gap_discovery_missing`
- `stage_hook_workorder_discovery_missing`
- `stage_hook_runtime_scaffold_missing`
