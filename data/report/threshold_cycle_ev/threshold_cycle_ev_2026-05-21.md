# Threshold Cycle Daily EV Report - 2026-05-21

## Runtime Apply
- status: `auto_bounded_live_ready`
- runtime_change: `True`
- selected_families: `soft_stop_whipsaw_confirmation, score65_74_recovery_probe, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, lifecycle_decision_matrix_runtime`

## Daily EV
- completed: `1` / open: `0`
- win/loss: `1` / `0` (`100.0`%)
- avg_profit_rate: `4.63`%
- realized_pnl_krw: `4942`
- full_fill_completed_avg_profit_rate: `4.63`%

## Entry Funnel
- budget_pass_to_submitted: `5` / `339` (`1.47`%)
- latency pass/block: `6` / `333`
- latency submit routing: `latency_classifier_runtime_semantics_gap`
- latency recommended action: `reject` (`recovery_count=0 below floor=33`)
- latency profile generation: `{'mode': 'grid_quantile_search', 'profile_count': 900, 'age_cap_ms': 1500, 'jitter_cap_ms': 1500, 'spread_cap_ratio': 0.012, 'counterfactual_sample_floor': 3, 'recovery_event_floor_ratio': 0.1}`
- safe/caution/recovery: `0` / `4` / `0`
- recovery attempts/cf sample/cf ev: `0` / `0` / `None`%
- recovered/lost labels: `0` / `0`
- stale/broker override excluded: `0` / `0`
- full/partial fill: `4` / `3`

## Holding Exit
- holding_reviews: `3457`
- exit_signals: `133`
- holding_review_ms_p95: `1859.0`

## Scalp Simulator
- authority: `equal_weight` / fill_policy: `signal_inclusive_best_ask_v1`
- armed/filled/sold: `186` / `186` / `166`
- expired/unpriced/duplicate: `0` / `0` / `374`
- entry_ai_price applied/skip: `12` / `1`
- submit_revalidation warning/block: `167` / `0`
- scale_in filled/unfilled: `0` / `0`
- overnight decision/sell/hold/carry_restored: `0` / `0` / `0` / `0`
- completed_profit_summary: `{'sample': 166, 'win_count': 67, 'loss_count': 99, 'avg_profit_rate': -0.2567, 'median_profit_rate': -0.41, 'downside_p10_profit_rate': -2.44, 'upside_p90_profit_rate': 1.73, 'win_rate': 0.4036, 'loss_rate': 0.5964, 'stddev_profit_rate': 1.8018}`
- post_sell_join: joined=`166` / pending=`0`
- post_sell_mfe_mae_10m: mfe=`1.448`% / mae=`-7.5974`% / close=`0.2237`%

## Missed Probe Counterfactual
- book: `scalp_score65_74_probe_counterfactual` / role: `missed_buy_probe_counterfactual`
- total/score65_74: `57` / `14`
- avg_expected_ev: `3.7223`% / score65_74_avg_expected_ev: `1.2058`%
- actual_order_submitted: `False` / broker_order_forbidden: `True`
- authority: `missed_probe_ev_only_not_broker_execution`

## Scalp Entry ADM
- artifact: `/home/ubuntu/KORStockScan/data/report/scalp_entry_action_decision_matrix/scalp_entry_action_decision_matrix_2026-05-21.json`
- status: `pass` / authority: `entry_advisory_prompt_context_only`
- total/joined/floor: `1450` / `175` / `20`
- prompt_applied_count: `1280`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 1450}`
- forced_action_counts: `{'-': 1450}`
- missing_actions: `[]`
- zero_sample_actions: `['BUY_NOW', 'SKIP_STALE']`
- top_actions: `[{'action': 'WAIT_REQUOTE', 'sample_count': 1, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'BUY_DEFENSIVE', 'sample_count': 5, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'NO_BUY_AI', 'sample_count': 1440, 'joined_sample': 174, 'source_quality_adjusted_ev_pct': -0.0322}, {'action': 'SKIP_SOURCE_QUALITY', 'sample_count': 2, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'SKIP_PRE_SUBMIT_SAFETY', 'sample_count': 2, 'joined_sample': 1, 'source_quality_adjusted_ev_pct': 2.785}]`

## Lifecycle Decision Matrix
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-05-21.json`
- status: `pass` / version: `lifecycle_decision_matrix_v1_2026-05-21`
- total/joined: `40910` / `39149`
- policy_pass/promote_ready: `5` / `0`
- fixed_threshold_roles: `{'hard_safety': ['broker_submit_guard', 'stale_quote_submit_block', 'price_freshness_guard', 'hard_stop', 'protect_stop', 'emergency_stop', 'account_order_cooldown_qty_guard'], 'baseline_prior': ['BUY_SCORE_THRESHOLD', 'VPW_MIN_SCORE', 'strength_momentum_cutoff', 'entry_score_cutoff'], 'bounded_tunable': ['SCALP_ENTRY_LATENCY_MAX_WS_AGE_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_WS_JITTER_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_SPREAD_RATIO_FOR_CAUTION', 'score65_74_recovery_probe', 'soft_stop_whipsaw_confirmation', 'holding_flow_override', 'scale_in_price_guard'], 'legacy_archive': ['fallback_scout_main', 'fallback_single', 'latency_fallback_split_entry', 'legacy_latency_composite', 'closed_shadow_axes']}`
- policy_entries: `[{'stage': 'entry', 'sample': 1671, 'joined_sample': 232, 'stage_ev_composite_pct': -0.2995, 'confidence': 1.0, 'selected_action': 'WAIT_REQUOTE', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'submit', 'sample': 196, 'joined_sample': 180, 'stage_ev_composite_pct': -1.011, 'confidence': 1.0, 'selected_action': 'NO_CHANGE', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'holding', 'sample': 189, 'joined_sample': 180, 'stage_ev_composite_pct': -0.6538, 'confidence': 1.0, 'selected_action': 'EXIT', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'scale_in', 'sample': 37853, 'joined_sample': 37788, 'stage_ev_composite_pct': -0.1504, 'confidence': 1.0, 'selected_action': 'NO_CHANGE', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'exit', 'sample': 1001, 'joined_sample': 769, 'stage_ev_composite_pct': -0.5019, 'confidence': 1.0, 'selected_action': 'EXIT', 'source_quality_gate': 'pass', 'promote_ready': False}]`

## Lifecycle AI Context
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_ai_context/lifecycle_ai_context_2026-05-21.json`
- context_version: `lifecycle_ai_context_v1_2026-05-21` / authority: `ai_advisory_prompt_context_only`
- prompt_stage_count: `3` / runtime_effect: `False`
- stage_contexts: `[{'stage': 'entry', 'prompt_injection_allowed': True, 'policy_key': 'entry:weighted_adm_v1', 'alignment_hint': 'WAIT_REQUOTE', 'context_contribution_score': 0.3478, 'attribution_quality_status': 'observational_only_pending_outcome'}, {'stage': 'submit', 'prompt_injection_allowed': False, 'policy_key': 'submit:weighted_adm_v1', 'alignment_hint': 'NO_CHANGE', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'holding', 'prompt_injection_allowed': True, 'policy_key': 'holding:weighted_adm_v1', 'alignment_hint': 'EXIT', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'scale_in', 'prompt_injection_allowed': False, 'policy_key': 'scale_in:weighted_adm_v1', 'alignment_hint': 'NO_CHANGE', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'exit', 'prompt_injection_allowed': True, 'policy_key': 'exit:weighted_adm_v1', 'alignment_hint': 'EXIT', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}]`

## Lifecycle AI Context Attribution
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_ai_context_attribution/lifecycle_ai_context_attribution_2026-05-21.json`
- eligible/applied/skipped: `3196` / `3196` / `0`
- replay_budget: `30`
- implementation_status: `implemented`
- stage_attribution: `{'entry': {'context_contribution_score': 0.3478, 'bounded_auxiliary_weight': 0.0522, 'attribution_quality_status': 'observational_only_pending_outcome', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': 0.9969, 'no_context_replay_observed': 0}, 'submit': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'holding': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'scale_in': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'exit': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}}`

## Institutional Flow Context
- artifact: `/home/ubuntu/KORStockScan/data/report/institutional_flow_context/institutional_flow_context_2026-05-21.json`
- status: `pass` / authority: `source_only_lifecycle_feature`
- rows ok/partial/missing/token_error: `120` / `0` / `0` / `0`
- join_rate_pct: `100.0`
- source_mix: `{'ka10059+ka10061': 120}`
- top_net_buy: `[{'stock_code': '005930', 'smart_money_net': 6190749, 'foreign_net_roll5': 0, 'inst_net_roll5': 9118293, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '034220', 'smart_money_net': 3326808, 'foreign_net_roll5': 6537917, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}, {'stock_code': '088350', 'smart_money_net': 1371141, 'foreign_net_roll5': 6495422, 'inst_net_roll5': 4545869, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '125020', 'smart_money_net': 1324323, 'foreign_net_roll5': 852478, 'inst_net_roll5': 20649, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '003490', 'smart_money_net': 1281486, 'foreign_net_roll5': 1021374, 'inst_net_roll5': 783553, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '017900', 'smart_money_net': 871829, 'foreign_net_roll5': 641423, 'inst_net_roll5': 36444, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '357880', 'smart_money_net': 728621, 'foreign_net_roll5': 860590, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}, {'stock_code': '067310', 'smart_money_net': 590582, 'foreign_net_roll5': 1761765, 'inst_net_roll5': 462107, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '033640', 'smart_money_net': 543559, 'foreign_net_roll5': 293673, 'inst_net_roll5': 222636, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '061970', 'smart_money_net': 482443, 'foreign_net_roll5': 661807, 'inst_net_roll5': 593696, 'regime': 'DUAL_ACCUMULATION'}]`

## Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-05-21.json`
- fresh: gemini=`True` claude=`True`
- consensus/orders/family_candidates: `5` / `12` / `3`

## Swing Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_2026-05-21.json`
- deepseek_lab_available: `True`
- findings/orders: `5` / `4`
- data_quality_warnings: `1`
- top_level_data_quality_warnings: `0`
- resolved_data_quality_warnings: `1`
- ofi_qi_stale_missing_unique_records: `2`
- ofi_qi_stale_missing_reasons: `{'micro_missing': 735, 'micro_stale': 0, 'observer_unhealthy': 0, 'micro_not_ready': 6, 'state_insufficient': 6}`
- ofi_qi_stale_missing_reason_combinations: `{'micro_missing': 729, 'micro_missing+micro_not_ready+state_insufficient': 6}`
- ofi_qi_stale_missing_reason_combination_unique_records: `{'micro_missing+micro_not_ready+state_insufficient': 1, 'micro_missing': 1}`
- ofi_qi_observer_unhealthy_overlap: `{'observer_unhealthy_total': 0, 'observer_unhealthy_with_other_reason': 0, 'observer_unhealthy_only': 0}`
- source_quality_blocked_families: `[{'family': 'swing_scale_in_ofi_qi_confirmation', 'stage': 'scale_in', 'source_quality_blockers': ['scale_in_ofi_qi_invalid_micro_context'], 'invalid_micro_context_unique_record_count': 1, 'invalid_reason_combination_unique_record_counts': {'micro_missing+micro_not_ready+state_insufficient': 1, 'micro_missing': 1}, 'automation_input': True, 'runtime_effect': False}]`
- carryover_warnings: `0`
- population_split_available: `True`

## Swing Strategy Discovery Sim
- artifact: `/home/ubuntu/KORStockScan/data/report/swing_strategy_discovery_ev/swing_strategy_discovery_ev_2026-05-21.json`
- authority: `swing_sim_exploration_only` / source_only: `True`
- candidate/arm/policy_exit_rows: `100` / `800` / `800`
- labeled/pending_future_quotes: `0` / `800`
- implementation_status: `implemented`
- top_surviving_arm: `-`
- surviving/avoid_bucket_count: `0` / `0`
- runtime_effect: `False`

## Pipeline Event Verbosity
- artifact: `/home/ubuntu/KORStockScan/data/report/pipeline_event_verbosity/pipeline_event_verbosity_2026-05-21.json`
- state: `v2_shadow_pending_flush`
- recommended_workorder_state: `observe_pending_next_flush`
- high_volume_line_count: `380183`
- high_volume_byte_share_pct: `51.19`
- parity_ok: `False`
- suppress_eligibility: `False`

## Codebase Performance Workorder Source
- artifact: `/home/ubuntu/KORStockScan/data/report/codebase_performance_workorder/codebase_performance_workorder_2026-05-21.json`
- authority: `ops_performance_workorder_source`
- accepted/deferred/rejected: `7` / `3` / `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`

## Pattern Lab Audits
- currentness: status=`pass` fail=`0` orders=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-05-21.json`
- propagation: status=`warning` fail=`0` warnings=`2` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_2026-05-21.json`

## Swing Runtime Approval
- request_report: `/home/ubuntu/KORStockScan/data/report/swing_runtime_approval/swing_runtime_approval_2026-05-20.json`
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
- artifact: `/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-05-21.json`
- markdown: `/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-05-21.md`
- selected_order_count: `12`
- decision_counts: `{'implement_now': 18, 'attach_existing_family': 18, 'design_family_candidate': 6, 'defer_evidence': 11, 'reject': 3}`

## Approval Requests
- none

## Swing Approval Requests
- none

## Calibration Decisions
## Code Improvement Top Orders
- `order_ai_source_quality_not_evaluated_provenance` decision=`implement_now` subsystem=`runtime_instrumentation`
- `order_high_volume_diagnostic_stage_contract_labels` decision=`implement_now` subsystem=`runtime_instrumentation`
- `order_lifecycle_entry_bucket_chosen_action_action_unknown` decision=`implement_now` subsystem=`runtime_instrumentation`

## Pattern Lab Top Findings
- `AI threshold miss EV recovery` route=`existing_family` family=`score65_74_recovery_probe`
- `No acute observability alert` route=`auto_family_candidate` family=`-`
- `latency guard miss EV recovery` route=`instrumentation_order` family=`-`

- `soft_stop_whipsaw_confirmation`: `adjust_up` sample=`4929/10`
- `holding_flow_ofi_smoothing`: `hold` sample=`5232/20`
- `protect_trailing_smoothing`: `adjust_down` sample=`96/20`
- `trailing_continuation`: `freeze` sample=`151/20`
- `market_regime_continuous_thresholds`: `hold_sample` sample=`1/10`
- `pre_submit_price_guard`: `hold_sample` sample=`333/20`
- `score65_74_recovery_probe`: `adjust_up` sample=`117/20`
- `strength_momentum_soft_gate_p1`: `hold` sample=`139107/20`
- `overbought_pullback_guard_p1`: `hold` sample=`91688/20`
- `liquidity_pre_submit_guard_p1`: `hold` sample=`9727/20`
- `bad_entry_refined_canary`: `adjust_up` sample=`33709/10`
- `holding_exit_decision_matrix_advisory`: `hold_no_edge` sample=`0/1`
- `lifecycle_decision_matrix_runtime`: `adjust_up` sample=`40910/20`
- `scale_in_price_guard`: `hold` sample=`677/20`
- `position_sizing_cap_release`: `hold_sample` sample=`35/30`
- `position_sizing_dynamic_formula`: `hold_sample` sample=`3/30`

## Warnings
- `swing_strategy_discovery:pending_future_quotes`
- `swing_strategy_discovery:sample_floor_not_met`
- `pattern_lab_propagation_audit_warning`
