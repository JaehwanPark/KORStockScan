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
- budget_pass_to_submitted: `0` / `86` (`0.0`%)
- latency pass/block: `6` / `80`
- latency submit routing: `latency_classifier_runtime_semantics_gap`
- latency recommended action: `-` (`-`)
- latency profile generation: `{}`
- safe/caution/recovery: `0` / `0` / `0`
- recovery attempts/cf sample/cf ev: `0` / `0` / `None`%
- recovered/lost labels: `0` / `0`
- stale/broker override excluded: `0` / `0`
- full/partial fill: `15` / `15`

## Holding Exit
- holding_reviews: `1288`
- exit_signals: `121`
- holding_review_ms_p95: `1749.0`

## Scalp Simulator
- authority: `-` / fill_policy: `-`
- armed/filled/sold: `None` / `None` / `None`
- expired/unpriced/duplicate: `None` / `None` / `None`
- entry_ai_price applied/skip: `None` / `None`
- submit_revalidation warning/block: `None` / `None`
- scale_in filled/unfilled: `None` / `None`
- overnight decision/sell/hold/carry_restored: `None` / `None` / `None` / `None`
- completed_profit_summary: `{}`
- post_sell_join: joined=`None` / pending=`None`
- post_sell_mfe_mae_10m: mfe=`None`% / mae=`None`% / close=`None`%

## Missed Probe Counterfactual
- book: `scalp_score65_74_probe_counterfactual` / role: `missed_buy_probe_counterfactual`
- total/score65_74: `19` / `3`
- avg_expected_ev: `4.8144`% / score65_74_avg_expected_ev: `-0.1213`%
- actual_order_submitted: `False` / broker_order_forbidden: `True`
- authority: `missed_probe_ev_only_not_broker_execution`

## Scalp Entry ADM
- artifact: `-`
- status: `missing` / authority: `entry_advisory_prompt_context_only`
- total/joined/floor: `0` / `0` / `20`
- prompt_applied_count: `0`
- runtime_bias_applied_count: `0`
- runtime_effect_counts: `{}`
- forced_action_counts: `{}`
- missing_actions: `[]`
- zero_sample_actions: `[]`
- top_actions: `[]`

## Lifecycle Decision Matrix
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-05-22.json`
- status: `pass` / version: `lifecycle_decision_matrix_v1_2026-05-22`
- total/joined: `9863` / `9641`
- policy_pass/promote_ready: `5` / `0`
- fixed_threshold_roles: `{'hard_safety': ['broker_submit_guard', 'stale_quote_submit_block', 'price_freshness_guard', 'hard_stop', 'protect_stop', 'emergency_stop', 'account_order_cooldown_qty_guard'], 'baseline_prior': ['BUY_SCORE_THRESHOLD', 'VPW_MIN_SCORE', 'strength_momentum_cutoff', 'entry_score_cutoff'], 'bounded_tunable': ['SCALP_ENTRY_LATENCY_MAX_WS_AGE_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_WS_JITTER_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_SPREAD_RATIO_FOR_CAUTION', 'score65_74_recovery_probe', 'soft_stop_whipsaw_confirmation', 'holding_flow_override', 'scale_in_price_guard'], 'legacy_archive': ['fallback_scout_main', 'fallback_single', 'latency_fallback_split_entry', 'legacy_latency_composite', 'closed_shadow_axes']}`
- policy_entries: `[{'stage': 'entry', 'sample': 100, 'joined_sample': 16, 'stage_ev_composite_pct': 3.4568, 'confidence': 0.256, 'selected_action': 'BUY_DEFENSIVE', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'submit', 'sample': 89, 'joined_sample': 75, 'stage_ev_composite_pct': -0.6286, 'confidence': 1.0, 'selected_action': 'NO_CHANGE', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'holding', 'sample': 89, 'joined_sample': 75, 'stage_ev_composite_pct': -0.6204, 'confidence': 1.0, 'selected_action': 'EXIT', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'scale_in', 'sample': 9296, 'joined_sample': 9289, 'stage_ev_composite_pct': -0.142, 'confidence': 1.0, 'selected_action': 'NO_CHANGE', 'source_quality_gate': 'pass', 'promote_ready': False}, {'stage': 'exit', 'sample': 289, 'joined_sample': 186, 'stage_ev_composite_pct': -0.4256, 'confidence': 1.0, 'selected_action': 'EXIT', 'source_quality_gate': 'pass', 'promote_ready': False}]`

## Lifecycle Bucket Discovery
- artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-05-22.json`
- status: `pass` / human_intervention_required: `False`
- candidates/surfaced: `229` / `94`
- sim_auto/live_auto/new_bucket: `84` / `0` / `10`
- state_counts: `{'sim_auto_approved': 84, 'new_bucket_candidate': 10, 'source_only_keep_collecting': 135}`
- top_surfaced: `[{'bucket_id': 'entry:source_stage:wait6579_ev_cohort', 'stage': 'entry', 'classification_state': 'sim_auto_approved', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 16, 'source_quality_adjusted_ev_pct': 3.4568}, {'bucket_id': 'entry:stale_bucket:fresh_or_unflagged', 'stage': 'entry', 'classification_state': 'sim_auto_approved', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 16, 'source_quality_adjusted_ev_pct': 3.4568}, {'bucket_id': 'entry:chosen_action:action_unknown', 'stage': 'entry', 'classification_state': 'new_bucket_candidate', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 16, 'source_quality_adjusted_ev_pct': 3.4568}, {'bucket_id': 'entry:exit_rule:exit_unknown', 'stage': 'entry', 'classification_state': 'new_bucket_candidate', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 16, 'source_quality_adjusted_ev_pct': 3.4568}, {'bucket_id': 'entry:liquidity_bucket:liquidity_unknown', 'stage': 'entry', 'classification_state': 'new_bucket_candidate', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 16, 'source_quality_adjusted_ev_pct': 3.4568}, {'bucket_id': 'entry:overbought_bucket:overbought_unknown', 'stage': 'entry', 'classification_state': 'new_bucket_candidate', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 16, 'source_quality_adjusted_ev_pct': 3.4568}, {'bucket_id': 'entry:strength_bucket:strength_unknown', 'stage': 'entry', 'classification_state': 'new_bucket_candidate', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 16, 'source_quality_adjusted_ev_pct': 3.4568}, {'bucket_id': 'entry:time_bucket:time_unknown', 'stage': 'entry', 'classification_state': 'new_bucket_candidate', 'live_auto_apply_family': None, 'recommended_action': 'relax_or_recover', 'joined_sample': 16, 'source_quality_adjusted_ev_pct': 3.4568}]`

## Lifecycle AI Context
- artifact: `-`
- context_version: `-` / authority: `ai_advisory_prompt_context_only`
- prompt_stage_count: `0` / runtime_effect: `False`
- stage_contexts: `[]`

## Lifecycle AI Context Attribution
- artifact: `-`
- eligible/applied/skipped: `0` / `0` / `None`
- replay_budget: `None`
- implementation_status: `-`
- stage_attribution: `{}`

## Institutional Flow Context
- artifact: `-`
- status: `missing` / authority: `source_only_lifecycle_feature`
- rows ok/partial/missing/token_error: `None` / `None` / `None` / `None`
- join_rate_pct: `0.0`
- source_mix: `{}`
- top_net_buy: `[]`

## Pattern Lab Automation
- artifact: `-`
- fresh: gemini=`False` claude=`False`
- consensus/orders/family_candidates: `0` / `0` / `0`

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
- artifact: `-`
- state: `missing`
- recommended_workorder_state: `missing`
- high_volume_line_count: `None`
- high_volume_byte_share_pct: `None`
- parity_ok: `None`
- suppress_eligibility: `None`

## Codebase Performance Workorder Source
- artifact: `-`
- authority: `-`
- accepted/deferred/rejected: `0` / `0` / `0`
- runtime_effect: `False`
- strategy_effect: `None`
- data_quality_effect: `None`
- tuning_axis_effect: `None`

## Pattern Lab Audits
- currentness: status=`missing` fail=`0` orders=`0` artifact=`-`
- propagation: status=`missing` fail=`0` warnings=`0` artifact=`-`

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
- selected_order_count: `30`
- decision_counts: `{'implement_now': 18, 'attach_existing_family': 12}`

## Approval Requests
- none

## Swing Approval Requests
- `swing_model_floor` approval_id=`swing_runtime_approval:2026-05-21:swing_model_floor` score=`0.955` target_env_keys=`['SWING_FLOOR_BULL', 'SWING_FLOOR_BEAR']`
- `swing_gatekeeper_reject_cooldown` approval_id=`swing_runtime_approval:2026-05-21:swing_gatekeeper_reject_cooldown` score=`0.955` target_env_keys=`['ML_GATEKEEPER_REJECT_COOLDOWN']`
- `swing_one_share_real_canary_phase0` approval_id=`swing_one_share_real_canary:2026-05-21:phase0` score=`0.955` target_env_keys=`['SWING_ONE_SHARE_REAL_CANARY_ENABLED', 'SWING_ONE_SHARE_REAL_CANARY_ALLOWED_CODES', 'SWING_ONE_SHARE_REAL_CANARY_MAX_QTY', 'SWING_ONE_SHARE_REAL_CANARY_MAX_NEW_ENTRIES_PER_DAY', 'SWING_ONE_SHARE_REAL_CANARY_MAX_OPEN_POSITIONS', 'SWING_ONE_SHARE_REAL_CANARY_MAX_TOTAL_NOTIONAL_KRW', 'SWING_ONE_SHARE_REAL_CANARY_REQUIRE_APPROVAL_ARTIFACT']`

## Calibration Decisions
## Code Improvement Top Orders
- `order_lifecycle_entry_bucket_chosen_action_action_unknown` decision=`implement_now` subsystem=`runtime_instrumentation`
- `order_lifecycle_entry_bucket_exit_rule_exit_unknown` decision=`implement_now` subsystem=`runtime_instrumentation`
- `order_lifecycle_entry_bucket_liquidity_bucket_liquidity_unknown` decision=`implement_now` subsystem=`runtime_instrumentation`

- no calibration decisions

## Warnings
- `calibration_report_missing`
- `pattern_lab_automation_missing`
- `swing_pattern_lab_automation_missing`
- `scalp_entry_action_decision_matrix_missing`
- `lifecycle_bucket_discovery:ai_review_provider_disabled`
- `lifecycle_ai_context_missing`
- `lifecycle_ai_context_attribution_missing`
- `swing_strategy_discovery_ev_missing`
- `institutional_flow_context_missing`
- `pipeline_event_verbosity_missing`
- `codebase_performance_workorder_missing`
- `pattern_lab_currentness_audit_missing`
- `pattern_lab_propagation_audit_missing`
