# Threshold Cycle Daily EV Report - 2026-05-26

## Runtime Apply
- status: `auto_bounded_live_ready`
- runtime_change: `True`
- selected_families: `soft_stop_whipsaw_confirmation, score65_74_recovery_probe, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, lifecycle_decision_matrix_runtime, swing_one_share_real_canary_phase0, swing_gatekeeper_reject_cooldown, entry_wait6579_score66_69_recovery_gate_v1`

## Daily EV
- completed: `7` / open: `0`
- win/loss: `4` / `3` (`57.14`%)
- avg_profit_rate: `-0.46`%
- realized_pnl_krw: `-2184`
- full_fill_completed_avg_profit_rate: `-0.46`%

## Entry Funnel
- budget_pass_to_submitted: `23` / `2706` (`0.85`%)
- latency pass/block: `316` / `2389`
- latency submit routing: `latency_classifier_runtime_semantics_gap`
- latency recommended action: `reject` (`recovery_count=0 below floor=238`)
- latency profile generation: `{'mode': 'grid_quantile_search', 'profile_count': 810, 'age_cap_ms': 1500, 'jitter_cap_ms': 1500, 'spread_cap_ratio': 0.012, 'counterfactual_sample_floor': 3, 'recovery_event_floor_ratio': 0.1}`
- safe/caution_normal/recovery: `0` / `0` / `0`
- recovery attempts/cf sample/cf ev: `0` / `0` / `None`%
- recovered/lost labels: `0` / `0`
- stale/broker override excluded: `0` / `0`
- full/partial fill: `28` / `21`

## Holding Exit
- holding_reviews: `4422`
- exit_signals: `242`
- holding_review_ms_p95: `1859.0`

## Scalp Simulator
- authority: `equal_weight` / fill_policy: `signal_inclusive_best_ask_v1`
- armed/filled/sold: `274` / `274` / `202`
- expired/unpriced/duplicate: `0` / `0` / `2613`
- entry_ai_price applied/skip: `117` / `0`
- submit_revalidation warning/block: `235` / `0`
- scale_in filled/unfilled: `0` / `0`
- overnight decision/sell/hold/carry_restored: `23` / `23` / `0` / `0`
- completed_profit_summary: `{'sample': 202, 'win_count': 79, 'loss_count': 123, 'avg_profit_rate': -0.6362, 'median_profit_rate': -1.28, 'downside_p10_profit_rate': -2.6, 'upside_p90_profit_rate': 1.64, 'win_rate': 0.3911, 'loss_rate': 0.6089, 'stddev_profit_rate': 1.9092}`
- post_sell_join: joined=`194` / pending=`8`
- post_sell_mfe_mae_10m: mfe=`1.3407`% / mae=`-8.1817`% / close=`0.2344`%

## Missed Probe Counterfactual
- book: `scalp_score65_74_probe_counterfactual` / role: `missed_buy_probe_counterfactual`
- total/score65_74: `163` / `5`
- avg_expected_ev: `5.9305`% / score65_74_avg_expected_ev: `0.8393`%
- actual_order_submitted: `False` / broker_order_forbidden: `True`
- authority: `missed_probe_ev_only_not_broker_execution`

## Scalp Entry ADM
- artifact: `/home/ubuntu/KORStockScan/data/report/scalp_entry_action_decision_matrix/scalp_entry_action_decision_matrix_2026-05-26.json`
- status: `pass` / authority: `entry_advisory_prompt_context_only`
- total/joined/floor: `1159` / `168` / `20`
- prompt_applied_count: `784`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{'-': 1159}`
- forced_action_counts: `{'-': 1159}`
- missing_actions: `[]`
- zero_sample_actions: `['SKIP_STALE']`
- top_actions: `[{'action': 'BUY_NOW', 'sample_count': 43, 'joined_sample': 26, 'source_quality_adjusted_ev_pct': -0.2474}, {'action': 'WAIT_REQUOTE', 'sample_count': 1, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'BUY_DEFENSIVE', 'sample_count': 15, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'NO_BUY_AI', 'sample_count': 892, 'joined_sample': 20, 'source_quality_adjusted_ev_pct': -0.0237}, {'action': 'SKIP_SOURCE_QUALITY', 'sample_count': 3, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}]`

## Lifecycle Decision Matrix
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-05-26.json`
- status: `pass` / version: `lifecycle_decision_matrix_v1_2026-05-26`
- total/joined: `48781` / `47168`
- policy_pass/promote_ready: `5` / `1`
- fixed_threshold_roles: `{'hard_safety': ['broker_submit_guard', 'stale_quote_submit_block', 'price_freshness_guard', 'hard_stop', 'protect_stop', 'emergency_stop', 'account_order_cooldown_qty_guard'], 'baseline_prior': ['BUY_SCORE_THRESHOLD', 'VPW_MIN_SCORE', 'strength_momentum_cutoff', 'entry_score_cutoff'], 'bounded_tunable': ['SCALP_ENTRY_LATENCY_MAX_WS_AGE_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_WS_JITTER_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_SPREAD_RATIO_FOR_CAUTION', 'score65_74_recovery_probe', 'soft_stop_whipsaw_confirmation', 'holding_flow_override', 'scale_in_price_guard'], 'legacy_archive': ['fallback_scout_main', 'fallback_single', 'latency_fallback_split_entry', 'legacy_latency_composite', 'closed_shadow_axes']}`
- policy_entries: `[{'stage': 'entry', 'sample': 1331, 'joined_sample': 209, 'stage_ev_composite_pct': 2.28, 'confidence': 1.0, 'selected_action': 'BUY_DEFENSIVE', 'source_quality_gate': 'pass', 'promote_ready': True}, {'stage': 'submit', 'sample': 312, 'joined_sample': 209, 'stage_ev_composite_pct': -1.0091, 'confidence': 1.0, 'selected_action': 'NO_CHANGE', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'holding', 'sample': 297, 'joined_sample': 209, 'stage_ev_composite_pct': -0.8449, 'confidence': 1.0, 'selected_action': 'EXIT', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'scale_in', 'sample': 45601, 'joined_sample': 45572, 'stage_ev_composite_pct': -0.3171, 'confidence': 1.0, 'selected_action': 'NO_CHANGE', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'exit', 'sample': 1240, 'joined_sample': 969, 'stage_ev_composite_pct': -0.5627, 'confidence': 1.0, 'selected_action': 'EXIT', 'source_quality_gate': 'pass', 'promote_ready': False}]`

## Lifecycle Bucket Discovery
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-05-26.json`
- status: `pass` / human_intervention_required: `False`
- candidates/surfaced: `414` / `184`
- sim_auto/live_auto/new_bucket: `184` / `0` / `0`
- state_counts: `{'sim_auto_approved': 184, 'source_only_keep_collecting': 230}`
- top_surfaced: `[{'bucket_id': 'entry:source_stage:wait6579_ev_cohort', 'stage': 'entry', 'classification_state': 'sim_auto_approved', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 163, 'source_quality_adjusted_ev_pct': 3.3661}, {'bucket_id': 'entry:stale_bucket:fresh_or_unflagged', 'stage': 'entry', 'classification_state': 'sim_auto_approved', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 163, 'source_quality_adjusted_ev_pct': 3.3661}, {'bucket_id': 'entry:time_bucket:time_unknown', 'stage': 'entry', 'classification_state': 'sim_auto_approved', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 163, 'source_quality_adjusted_ev_pct': 3.3661}, {'bucket_id': 'entry:score_band:score_70p', 'stage': 'entry', 'classification_state': 'sim_auto_approved', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 135, 'source_quality_adjusted_ev_pct': 2.7821}, {'bucket_id': 'entry:combo_entry_spot:score_score_70p_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_unknown_o', 'stage': 'entry', 'classification_state': 'sim_auto_approved', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 107, 'source_quality_adjusted_ev_pct': 3.9731}, {'bucket_id': 'entry:combo_entry_spot:score_score_66_69_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_unknown', 'stage': 'entry', 'classification_state': 'sim_auto_approved', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 49, 'source_quality_adjusted_ev_pct': 2.3066}, {'bucket_id': 'entry:score_band:score_66_69', 'stage': 'entry', 'classification_state': 'sim_auto_approved', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 49, 'source_quality_adjusted_ev_pct': 2.3066}, {'bucket_id': 'entry:source_stage:scalp_entry_action_decision_snapshot', 'stage': 'entry', 'classification_state': 'sim_auto_approved', 'live_auto_apply_family': None, 'recommended_action': 'tighten_or_exclude', 'joined_sample': 46, 'source_quality_adjusted_ev_pct': -1.5688}]`

## Lifecycle AI Context
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_ai_context/lifecycle_ai_context_2026-05-26.json`
- context_version: `lifecycle_ai_context_v1_2026-05-26` / authority: `ai_advisory_prompt_context_only`
- prompt_stage_count: `3` / runtime_effect: `False`
- stage_contexts: `[{'stage': 'entry', 'prompt_injection_allowed': True, 'policy_key': 'entry:weighted_adm_v1', 'alignment_hint': 'BUY_DEFENSIVE', 'context_contribution_score': -0.3003, 'attribution_quality_status': 'observational_only_pending_outcome'}, {'stage': 'submit', 'prompt_injection_allowed': False, 'policy_key': 'submit:weighted_adm_v1', 'alignment_hint': 'NO_CHANGE', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'holding', 'prompt_injection_allowed': True, 'policy_key': 'holding:weighted_adm_v1', 'alignment_hint': 'EXIT', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'scale_in', 'prompt_injection_allowed': False, 'policy_key': 'scale_in:weighted_adm_v1', 'alignment_hint': 'NO_CHANGE', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}, {'stage': 'exit', 'prompt_injection_allowed': True, 'policy_key': 'exit:weighted_adm_v1', 'alignment_hint': 'EXIT', 'context_contribution_score': 0.0, 'attribution_quality_status': 'hold_sample'}]`

## Lifecycle AI Context Attribution
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_ai_context_attribution/lifecycle_ai_context_attribution_2026-05-26.json`
- eligible/applied/skipped: `3860` / `3860` / `0`
- replay_budget: `30`
- implementation_status: `implemented`
- stage_attribution: `{'entry': {'context_contribution_score': -0.3003, 'bounded_auxiliary_weight': -0.045, 'attribution_quality_status': 'observational_only_pending_outcome', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': 0.071, 'no_context_replay_observed': 0}, 'submit': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'holding': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'scale_in': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'exit': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}}`

## Institutional Flow Context
- artifact: `/home/ubuntu/KORStockScan/data/report/institutional_flow_context/institutional_flow_context_2026-05-26.json`
- status: `pass` / authority: `source_only_lifecycle_feature`
- rows ok/partial/missing/token_error: `120` / `0` / `0` / `0`
- join_rate_pct: `100.0`
- source_mix: `{'ka10059+ka10061': 120}`
- top_net_buy: `[{'stock_code': '005930', 'smart_money_net': 3420634, 'foreign_net_roll5': 0, 'inst_net_roll5': 8706515, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '018880', 'smart_money_net': 1914814, 'foreign_net_roll5': 6901518, 'inst_net_roll5': 196569, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '034220', 'smart_money_net': 1798927, 'foreign_net_roll5': 5505330, 'inst_net_roll5': 870338, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '347700', 'smart_money_net': 1445748, 'foreign_net_roll5': 626375, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}, {'stock_code': '357880', 'smart_money_net': 910633, 'foreign_net_roll5': 1903947, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}, {'stock_code': '100790', 'smart_money_net': 563994, 'foreign_net_roll5': 259022, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}, {'stock_code': '061970', 'smart_money_net': 527757, 'foreign_net_roll5': 1064455, 'inst_net_roll5': 128320, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '030530', 'smart_money_net': 449422, 'foreign_net_roll5': 798325, 'inst_net_roll5': 25523, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '356680', 'smart_money_net': 432919, 'foreign_net_roll5': 329752, 'inst_net_roll5': 71374, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '047040', 'smart_money_net': 344982, 'foreign_net_roll5': 1271253, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}]`

## Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-05-26.json`
- fresh: gemini=`True` claude=`True`
- consensus/orders/family_candidates: `5` / `12` / `2`

## Swing Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_2026-05-26.json`
- deepseek_lab_available: `True`
- findings/orders: `5` / `3`
- data_quality_warnings: `0`
- top_level_data_quality_warnings: `0`
- resolved_data_quality_warnings: `0`
- ofi_qi_stale_missing_unique_records: `1`
- ofi_qi_stale_missing_reasons: `{'micro_missing': 1, 'micro_stale': 0, 'observer_unhealthy': 1, 'micro_not_ready': 4, 'state_insufficient': 4}`
- ofi_qi_stale_missing_reason_combinations: `{'micro_not_ready+state_insufficient': 3, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 1}`
- ofi_qi_stale_missing_reason_combination_unique_records: `{'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 1}`
- ofi_qi_observer_unhealthy_overlap: `{'observer_unhealthy_total': 1, 'observer_unhealthy_with_other_reason': 1, 'observer_unhealthy_only': 0}`
- source_quality_blocked_families: `[]`
- carryover_warnings: `0`
- population_split_available: `True`

## Swing Strategy Discovery Sim
- artifact: `/home/ubuntu/KORStockScan/data/report/swing_strategy_discovery_ev/swing_strategy_discovery_ev_2026-05-26.json`
- authority: `swing_sim_exploration_only` / source_only: `True`
- candidate/arm/policy_exit_rows: `200` / `1600` / `1600`
- labeled/pending_future_quotes: `71` / `1434`
- implementation_status: `implemented`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- surviving/avoid_bucket_count: `1` / `0`
- runtime_effect: `False`

## Pipeline Event Verbosity
- artifact: `/home/ubuntu/KORStockScan/data/report/pipeline_event_verbosity/pipeline_event_verbosity_2026-05-26.json`
- state: `v2_shadow_pending_flush`
- recommended_workorder_state: `observe_pending_next_flush`
- high_volume_line_count: `287148`
- high_volume_byte_share_pct: `36.89`
- parity_ok: `False`
- suppress_eligibility: `False`

## Codebase Performance Workorder Source
- artifact: `/home/ubuntu/KORStockScan/data/report/codebase_performance_workorder/codebase_performance_workorder_2026-05-26.json`
- authority: `ops_performance_workorder_source`
- accepted/deferred/rejected: `7` / `3` / `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`

## Pattern Lab Audits
- currentness: status=`pass` fail=`0` orders=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-05-26.json`
- ai_review: status=`pass` orders=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_ai_review/pattern_lab_ai_review_2026-05-26.json`
- time_window_regime_counterfactual: status=`pass` artifact=`/home/ubuntu/KORStockScan/data/report/time_window_regime_counterfactual/time_window_regime_counterfactual_2026-05-26.json`
- producer_gap_discovery: status=`warning` orders=`8` artifact=`/home/ubuntu/KORStockScan/data/report/producer_gap_discovery/producer_gap_discovery_2026-05-26.json`
- stage_hook_workorder_discovery: status=`warning` orders=`2` artifact=`/home/ubuntu/KORStockScan/data/report/stage_hook_workorder_discovery/stage_hook_workorder_discovery_2026-05-26.json`
- propagation: status=`pass` fail=`0` warnings=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_2026-05-26.json`

## Swing Runtime Approval
- request_report: `/home/ubuntu/KORStockScan/data/report/swing_runtime_approval/swing_runtime_approval_2026-05-22.json`
- approval_artifact: `/home/ubuntu/KORStockScan/data/threshold_cycle/approvals/swing_runtime_approvals_2026-05-22.json`
- requested/approved/live_dry_run: `3` / `3` / `2`
- dry_run_forced: `True`
- real_canary_policy: `swing_one_share_real_canary_phase0`
- one_share_real_canary_artifact: `/home/ubuntu/KORStockScan/data/threshold_cycle/approvals/swing_one_share_real_canary_2026-05-22.json`
- selected_one_share_real_canary: `1`
- real_order_allowed_actions: `BUY_INITIAL, SELL_CLOSE`
- sim_only_actions: `AVG_DOWN, PYRAMID, SCALE_IN`
- scale_in_real_canary_policy: `swing_scale_in_real_canary_phase0`
- selected_scale_in_real_canary: `0`
- scale_in_real_execution_quality: `{'one_share_canary_selected': 1, 'scale_in_canary_selected': 0, 'execution_quality_source': 'real_only', 'sim_probe_ev_source': 'separate_from_broker_execution_quality'}`
- blocked: `[]`

## Code Improvement Workorder
- artifact: `/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-05-26.json`
- markdown: `/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-05-26.md`
- selected_order_count: `64`
- decision_counts: `{'implement_now': 38, 'attach_existing_family': 44, 'design_family_candidate': 6, 'defer_evidence': 10, 'reject': 3}`

## Approval Requests
- none

## Swing Approval Requests
- `swing_model_floor` approval_id=`swing_runtime_approval:2026-05-22:swing_model_floor` score=`0.955` target_env_keys=`['SWING_FLOOR_BULL', 'SWING_FLOOR_BEAR']`
- `swing_gatekeeper_reject_cooldown` approval_id=`swing_runtime_approval:2026-05-22:swing_gatekeeper_reject_cooldown` score=`0.955` target_env_keys=`['ML_GATEKEEPER_REJECT_COOLDOWN']`
- `swing_one_share_real_canary_phase0` approval_id=`swing_one_share_real_canary:2026-05-22:phase0` score=`0.955` target_env_keys=`['SWING_ONE_SHARE_REAL_CANARY_ENABLED', 'SWING_ONE_SHARE_REAL_CANARY_ALLOWED_CODES', 'SWING_ONE_SHARE_REAL_CANARY_MAX_QTY', 'SWING_ONE_SHARE_REAL_CANARY_MAX_NEW_ENTRIES_PER_DAY', 'SWING_ONE_SHARE_REAL_CANARY_MAX_OPEN_POSITIONS', 'SWING_ONE_SHARE_REAL_CANARY_MAX_TOTAL_NOTIONAL_KRW', 'SWING_ONE_SHARE_REAL_CANARY_REQUIRE_APPROVAL_ARTIFACT']`

## Calibration Decisions
## Code Improvement Top Orders
- `order_entry_submit_drought_auto_resolution` decision=`implement_now` subsystem=`runtime_instrumentation`
- `order_swing_entry_bottleneck_auto_resolution` decision=`implement_now` subsystem=`swing_entry`
- `order_entry_broker_receipt_contract_gap_review` decision=`implement_now` subsystem=`runtime_instrumentation`

## Pattern Lab Top Findings
- `AI threshold dominance` route=`existing_family` family=`score65_74_recovery_probe`
- `AI threshold miss EV recovery` route=`existing_family` family=`score65_74_recovery_probe`
- `latency guard miss EV recovery` route=`instrumentation_order` family=`-`

- `soft_stop_whipsaw_confirmation`: `adjust_up` sample=`7939/10`
- `holding_flow_ofi_smoothing`: `hold` sample=`5658/20`
- `protect_trailing_smoothing`: `adjust_down` sample=`108/20`
- `trailing_continuation`: `freeze` sample=`254/20`
- `market_regime_continuous_thresholds`: `hold_sample` sample=`3/10`
- `pre_submit_price_guard`: `hold_sample` sample=`2389/20`
- `score65_74_recovery_probe`: `adjust_up` sample=`198/20`
- `strength_momentum_soft_gate_p1`: `hold` sample=`93458/20`
- `overbought_pullback_guard_p1`: `hold` sample=`45733/20`
- `liquidity_pre_submit_guard_p1`: `hold` sample=`2607/20`
- `bad_entry_refined_canary`: `adjust_up` sample=`67484/10`
- `holding_exit_decision_matrix_advisory`: `hold_no_edge` sample=`9/1`
- `lifecycle_decision_matrix_runtime`: `adjust_up` sample=`48781/20`
- `scale_in_price_guard`: `hold` sample=`685/20`
- `position_sizing_cap_release`: `hold_sample` sample=`49/30`
- `position_sizing_dynamic_formula`: `hold_sample` sample=`10/30`

## Warnings
- `swing_strategy_discovery:pending_future_quotes`
- `swing_lifecycle_decision_matrix:pending_future_quotes`
