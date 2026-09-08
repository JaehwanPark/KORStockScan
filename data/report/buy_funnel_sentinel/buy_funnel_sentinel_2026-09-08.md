# BUY Funnel Sentinel 2026-09-08

## 판정

- primary: `SUBMIT_DROUGHT_CRITICAL`
- secondary: `PRICE_GUARD_DROUGHT, ENTRY_AI_AUTHORITY_DROUGHT, LATENCY_DROUGHT`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `false`
- followup_route: `entry_submit_drought_auto_workorder`
- followup_owner: `postclose_threshold_cycle`
- runtime_effect: `auto_workorder_no_intraday_mutation`
- submit_contract_downstream: `code_improvement_workorder, threshold_cycle_ev_report, runtime_approval_summary, postclose_verifier`
- submit_contract_weak_matches: `BROKER_RECEIPT, BUDGET_PASS_COLLAPSE, ENTRY_AI_AUTHORITY_REVALIDATION, FILL_QUALITY, LATENCY_PRE_SUBMIT, PRICE_REVALIDATION, SIM_REAL_AUTHORITY, TELEGRAM_POST_SUBMIT_ONLY`

## 근거

- as_of: `2026-09-08T12:30:03`
- baseline_date: `2026-09-07`
- ai_confirmed unique: `92`
- budget_pass unique: `230`
- latency_pass unique: `24`
- submitted unique: `0`
- holding_started unique: `0`
- budget/ai unique: `250.0%` (baseline `141.2`)
- submitted/ai unique: `0.0%` (baseline `0.0`)
- economic bundles: `observed=0, valid=0, probe_only=0, partial_residual=0, full=0`
- economic submitted/requested: `qty=0/0 (0.0%), notional=0/0 (0.0%)`
- economic participation by venue: `{}`
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- exact attempt contract: `status=source_quality_gap_excluded, identity=record_id, fallback_allowed=False, missing=0, order_violation=0, terminal_causal=347`
- submit drought core axes: `UPSTREAM_GATE, LATENCY_PRE_SUBMIT, ENTRY_AI_AUTHORITY_REVALIDATION, PRICE_REVALIDATION, BROKER_RECEIPT`
- top blockers: `blocked_strength_momentum:below_window_buy_value=164, latency_block:latency_state_danger=141, blocked_overbought:-=65, blocked_vpw:-=46, blocked_strength_momentum:below_strength_base=44`
- swing blockers: `-`
- upstream blockers: `blocked_strength_momentum:below_window_buy_value=164, blocked_overbought:-=65, blocked_vpw:-=46, blocked_strength_momentum:below_strength_base=44, blocked_liquidity:-=38`
- AI terminal reasons: `ai_terminal:entry_policy_no_buy_score_prior=36, ai_terminal:first_ai_wait_big_bite_not_confirmed=34`
- AI actions: `events={'DROP': 79, 'NOT_EVALUATED': 2, 'WAIT': 11}, unique={'DROP': 40, 'NOT_EVALUATED': 2, 'WAIT': 11}`
- budget/AI lineage: `{'status': 'explicit_ai_trace_budget_pass_only', 'pipeline_stage_order_contract': 'latest_watching_ai_to_budget_precheck_to_final_authority_revalidation', 'raw_ai_budget_census_is_causal': False, 'ai_trace_count': 95, 'ai_trace_source_stage_counts': {'ai_confirmed': 92, 'early_accel_strong_bundle_recheck_failed': 3}, 'budget_or_block_event_count': 231, 'lineage_contract_event_count': 231, 'lineage_contract_coverage_pct': 100.0, 'pre_ai_parent_not_expected_event_count': 197, 'lineage_join_eligible_event_count': 3, 'lineage_contract_missing_event_count': 0, 'lineage_field_present_count': 3, 'parent_trace_missing_when_expected_event_count': 0, 'parent_attempt_without_trusted_result_event_count': 31, 'ai_attempt_result_unavailable_parent_not_expected_event_count': 31, 'parent_trace_missing_without_attempt_event_count': 0, 'lineage_exact_trusted_count': 2, 'lineage_untrusted_or_stale_event_count': 1, 'lineage_untrusted_or_stale_reason_counts': {'source_stale': 1}, 'lineage_joined_event_count': 2, 'exact_parent_trace_unresolved_event_count': 0, 'lineage_join_coverage_pct': 66.67, 'raw_event_lineage_join_coverage_pct': 0.87, 'lineage_join_coverage_denominator': 'events_with_a_trusted_ai_result_expected; excludes_pre_ai_and_explicit_attempt_result_unavailable', 'linked_budget_pass_trace_count': 1, 'linked_budget_block_trace_count': 0, 'linked_stage_counts': {'budget_pass': 2}, 'runtime_effect': False, 'allowed_runtime_apply': False}`
- latency blockers: `latency_block:latency_state_danger=141`
- latency causal join: `raw_danger_events=141, raw_unique=49, joined_budget_events=141, joined_budget_unique=49, budget_missing_key=0, latency_missing_key=0`
- price guards: `entry_price_canary_submit_block:ai_input_preflight_blocked=29, entry_price_canary_submit_block:entry_price_feature_packet_source_quality_blocked=10, entry_price_canary_submit_block:entry_candle_source_quality_blocked=9, entry_submit_revalidation_block:standard_stale_context_or_quote=2, entry_submit_revalidation_block:observed_mark_gap_unresolved=2`
- quote refresh: `attempted=165, applied=142, latency_recovered=17, submitted_after_refresh=0`
- quote refresh downstream: `{'entry_ai_authority_revalidation': 15, 'price_guard_or_revalidation': 2}`

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

- `5m`: ai=2, budget=5, latency=0, submitted=0, top=`blocked_strength_momentum:below_window_buy_value=4, blocked_overbought:-=2, pre_submit_entry_ai_authority_guard_block:fresh_ai_drop_real_buy_veto=1`, swing=`-`, upstream=`blocked_strength_momentum:below_window_buy_value=4, blocked_overbought:-=2, blocked_strength_momentum:insufficient_history=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=1`
- `10m`: ai=4, budget=11, latency=2, submitted=0, top=`blocked_strength_momentum:below_window_buy_value=5, entry_price_canary_submit_block:entry_candle_source_quality_blocked=2, rising_missed_tick_speed_entry_block:tick_acceleration_ratio_lt_1=2`, swing=`-`, upstream=`blocked_strength_momentum:below_window_buy_value=5, rising_missed_tick_speed_entry_block:tick_acceleration_ratio_lt_1=2, blocked_overbought:-=2`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=2`
- `30m`: ai=14, budget=56, latency=8, submitted=0, top=`latency_block:latency_state_danger=28, blocked_strength_momentum:below_window_buy_value=20, blocked_overbought:-=10`, swing=`-`, upstream=`blocked_strength_momentum:below_window_buy_value=20, blocked_overbought:-=10, blocked_strength_momentum:below_strength_base=6`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=4, ai_terminal:first_ai_wait_big_bite_not_confirmed=3`
