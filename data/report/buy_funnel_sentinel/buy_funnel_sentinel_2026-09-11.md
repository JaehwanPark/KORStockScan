# BUY Funnel Sentinel 2026-09-11

## 판정

- primary: `SUBMIT_DROUGHT_CRITICAL`
- secondary: `LATENCY_DROUGHT`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `false`
- followup_route: `entry_submit_drought_auto_workorder`
- followup_owner: `postclose_threshold_cycle`
- runtime_effect: `auto_workorder_no_intraday_mutation`
- submit_contract_downstream: `code_improvement_workorder, threshold_cycle_ev_report, runtime_approval_summary, postclose_verifier`
- submit_contract_weak_matches: `BROKER_RECEIPT, BUDGET_PASS_COLLAPSE, ECONOMIC_PARTICIPATION, FILL_QUALITY, LATENCY_PRE_SUBMIT, SIM_REAL_AUTHORITY, TELEGRAM_POST_SUBMIT_ONLY`

## 근거

- as_of: `2026-09-11T15:20:04`
- baseline_date: `2026-09-10`
- ai_confirmed unique: `228`
- budget_pass unique: `463`
- latency_pass unique: `83`
- submitted unique: `12`
- holding_started unique: `11`
- budget/ai unique: `203.1%` (baseline `214.7`)
- submitted/ai unique: `5.3%` (baseline `2.3`)
- economic bundles: `observed=12, valid=12, probe_only=12, partial_residual=0, full=0`
- economic submitted/requested: `qty=12/57 (21.1%), notional=635345/1020390 (62.3%)`
- economic participation by venue: `{'KRX': {'bundle_count': 12, 'probe_only_bundle_count': 12, 'partial_residual_bundle_count': 0, 'full_submitted_bundle_count': 0, 'requested_qty': 57, 'submitted_qty': 12, 'requested_notional_krw': 1020390, 'submitted_notional_krw': 635345, 'submitted_qty_to_requested_qty_pct': 21.1, 'submitted_notional_to_requested_notional_pct': 62.3}}`
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- exact attempt contract: `status=source_quality_gap_excluded, identity=record_id, fallback_allowed=False, missing=0, order_violation=0, terminal_causal=803`
- submit drought core axes: `UPSTREAM_GATE, LATENCY_PRE_SUBMIT, ENTRY_AI_AUTHORITY_REVALIDATION, PRICE_REVALIDATION, BROKER_RECEIPT`
- capital-shortfall attempts excluded from drought: `15` (raw evidence retained)
- top blockers: `blocked_strength_momentum:below_window_buy_value=369, blocked_overbought:-=275, latency_block:latency_state_danger=256, blocked_strength_momentum:below_strength_base=185, blocked_liquidity:-=137`
- swing blockers: `-`
- upstream blockers: `blocked_strength_momentum:below_window_buy_value=369, blocked_overbought:-=275, blocked_strength_momentum:below_strength_base=185, blocked_liquidity:-=137, blocked_vpw:-=136`
- AI terminal reasons: `ai_terminal:entry_policy_no_buy_score_prior=82, ai_terminal:first_ai_wait_big_bite_not_confirmed=56`
- AI actions: `events={'DROP': 156, 'NOT_EVALUATED': 2, 'WAIT': 71}, unique={'DROP': 60, 'NOT_EVALUATED': 2, 'WAIT': 47}`
- budget/AI lineage: `{'status': 'explicit_ai_trace_budget_pass_only', 'pipeline_stage_order_contract': 'latest_watching_ai_to_budget_precheck_to_final_authority_revalidation', 'raw_ai_budget_census_is_causal': False, 'ai_trace_count': 242, 'ai_trace_source_stage_counts': {'ai_confirmed': 229, 'early_accel_strong_bundle_recheck_corrected': 9, 'early_accel_strong_bundle_recheck_failed': 4}, 'budget_or_block_event_count': 463, 'lineage_contract_event_count': 463, 'lineage_contract_coverage_pct': 100.0, 'pre_ai_parent_not_expected_event_count': 423, 'lineage_join_eligible_event_count': 23, 'lineage_contract_missing_event_count': 0, 'lineage_field_present_count': 23, 'parent_trace_missing_when_expected_event_count': 0, 'parent_attempt_without_trusted_result_event_count': 17, 'ai_attempt_result_unavailable_parent_not_expected_event_count': 17, 'parent_trace_missing_without_attempt_event_count': 0, 'lineage_exact_trusted_count': 21, 'lineage_untrusted_or_stale_event_count': 2, 'lineage_untrusted_or_stale_reason_counts': {'source_stale': 2}, 'lineage_joined_event_count': 21, 'exact_parent_trace_unresolved_event_count': 0, 'lineage_join_coverage_pct': 91.3, 'raw_event_lineage_join_coverage_pct': 4.54, 'lineage_join_coverage_denominator': 'events_with_a_trusted_ai_result_expected; excludes_pre_ai_and_explicit_attempt_result_unavailable', 'linked_budget_pass_trace_count': 20, 'linked_budget_block_trace_count': 0, 'linked_stage_counts': {'budget_pass': 21}, 'runtime_effect': False, 'allowed_runtime_apply': False}`
- latency blockers: `latency_block:latency_state_danger=256`
- latency causal join: `raw_danger_events=256, raw_unique=88, joined_budget_events=256, joined_budget_unique=88, budget_missing_key=0, latency_missing_key=0`
- price guards: `entry_price_canary_submit_block:ai_input_preflight_blocked=31, entry_price_canary_submit_block:entry_candle_source_quality_blocked=12, entry_submit_revalidation_block:standard_stale_context_or_quote=10`
- quote refresh: `attempted=336, applied=297, latency_recovered=60, submitted_after_refresh=11`
- quote refresh downstream: `{'entry_ai_authority_revalidation': 35, 'lineage_gap': 9, 'order_bundle_submitted': 11, 'price_guard_or_revalidation': 5}`
- refresh transitions (overlapping exact attempt sets): `{'version': 1, 'count_basis': 'exact_attempt_transition_sets_not_disjoint_terminals', 'legacy_still_blocked_semantics': 'refresh_not_applied_blocked', 'refresh_not_applied_blocked': 16, 'refresh_applied_still_blocked': 237, 'refresh_applied_latency_pass': 60, 'refresh_applied_still_blocked_reason_counts': {'spread_too_wide': 78, 'spread_above_caution_below_guard_cap': 139, 'orderbook_micro_spread_wide': 237, 'ws_age_too_high': 27}, 'next_ai_blocker_counts': {'authority_untrusted_or_unknown': 1, 'fresh_drop_veto': 25, 'fresh_wait_veto': 6, 'input_preflight_gap': 2, 'semantic_contract_rejected': 1}, 'next_blocker_reason_counts': {'entry_submit_revalidation_block:standard_stale_context_or_quote': 5, 'order_bundle_submitted:caution_normal_entry_allowed': 10, 'order_bundle_submitted:safe_normal_entry_allowed': 1, 'pre_submit_entry_ai_authority_guard_block:entry_ai_result_stale_or_untrusted': 4, 'pre_submit_entry_ai_authority_guard_block:fresh_ai_drop_real_buy_veto': 25, 'pre_submit_entry_ai_authority_guard_block:fresh_ai_wait_observation_only_probe_veto': 6}, 'next_blocker_count_basis': 'ordered_latency_pass_occurrences', 'runtime_effect': False, 'allowed_runtime_apply': False}`
- AI authority subcauses: `{'authority_untrusted_or_unknown': 1, 'fresh_drop_veto': 34, 'fresh_wait_veto': 8, 'input_preflight_gap': 6, 'semantic_contract_rejected': 1}`
- zero-qty subcauses: `{}`
- recheck input classes (not runtime eligibility): `{'input_gap': 45, 'normal_veto': 42, 'not_evaluated': 101}`

## 금지된 자동변경

- `score_threshold_relaxation`
- `spread_cap_relaxation`
- `fallback_reenable`
- `live_threshold_runtime_mutation`
- `bot_restart`

## 권고 액션

- Auto-route ai_confirmed -> budget_pass -> latency_pass -> order_bundle_submitted drought into postclose code-improvement workorder handoff.
- Split root cause into exact-attempt upstream, latency/pre-submit, Entry-AI-authority revalidation, price revalidation, and broker-receipt axes before tuning thresholds.
- Do not require operator approval for submitted drought surfacing or downstream workorder generation.

## Window Summary

- `5m`: ai=0, budget=0, latency=0, submitted=0, top=`-`, swing=`-`, upstream=`-`, ai_terminal=`-`
- `10m`: ai=0, budget=1, latency=0, submitted=0, top=`rising_missed_tick_speed_entry_block:tick_acceleration_ratio_lt_1=2, blocked_strength_momentum:below_strength_base=1`, swing=`-`, upstream=`rising_missed_tick_speed_entry_block:tick_acceleration_ratio_lt_1=2, blocked_strength_momentum:below_strength_base=1`, ai_terminal=`-`
- `30m`: ai=7, budget=10, latency=0, submitted=0, top=`blocked_strength_momentum:below_window_buy_value=20, blocked_overbought:-=18, blocked_vpw:-=10`, swing=`-`, upstream=`blocked_strength_momentum:below_window_buy_value=20, blocked_overbought:-=18, blocked_vpw:-=10`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=3, ai_terminal:first_ai_wait_big_bite_not_confirmed=2`
