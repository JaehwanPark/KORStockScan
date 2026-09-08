# BUY Funnel Sentinel 2026-09-07

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

- as_of: `2026-09-07T19:20:05`
- baseline_date: `2026-09-04`
- ai_confirmed unique: `306`
- budget_pass unique: `382`
- latency_pass unique: `73`
- submitted unique: `3`
- holding_started unique: `2`
- budget/ai unique: `124.8%` (baseline `116.2`)
- submitted/ai unique: `1.0%` (baseline `0.7`)
- economic bundles: `observed=3, valid=3, probe_only=3, partial_residual=0, full=0`
- economic submitted/requested: `qty=3/36 (8.3%), notional=49930/572410 (8.7%)`
- economic participation by venue: `{'KRX': {'bundle_count': 1, 'probe_only_bundle_count': 1, 'partial_residual_bundle_count': 0, 'full_submitted_bundle_count': 0, 'requested_qty': 1, 'submitted_qty': 1, 'requested_notional_krw': 18240, 'submitted_notional_krw': 18240, 'submitted_qty_to_requested_qty_pct': 100.0, 'submitted_notional_to_requested_notional_pct': 100.0}, 'NXT': {'bundle_count': 2, 'probe_only_bundle_count': 2, 'partial_residual_bundle_count': 0, 'full_submitted_bundle_count': 0, 'requested_qty': 35, 'submitted_qty': 2, 'requested_notional_krw': 554170, 'submitted_notional_krw': 31690, 'submitted_qty_to_requested_qty_pct': 5.7, 'submitted_notional_to_requested_notional_pct': 5.7}}`
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- exact attempt contract: `status=source_quality_gap_excluded, identity=record_id, fallback_allowed=False, missing=0, order_violation=1, terminal_causal=111`
- submit drought core axes: `UPSTREAM_GATE, LATENCY_PRE_SUBMIT, ENTRY_AI_AUTHORITY_REVALIDATION, PRICE_REVALIDATION, BROKER_RECEIPT`
- top blockers: `blocked_strength_momentum:below_window_buy_value=606, blocked_strength_momentum:insufficient_history=384, blocked_overbought:-=342, latency_block:latency_state_danger=286, blocked_strength_momentum:below_strength_base=155`
- swing blockers: `-`
- upstream blockers: `blocked_strength_momentum:below_window_buy_value=606, blocked_strength_momentum:insufficient_history=384, blocked_overbought:-=342, blocked_strength_momentum:below_strength_base=155, blocked_vpw:-=146`
- AI terminal reasons: `ai_terminal:entry_policy_no_buy_score_prior=137, ai_terminal:first_ai_wait_big_bite_not_confirmed=88`
- AI actions: `events={'DROP': 221, 'NOT_EVALUATED': 3, 'WAIT': 83}, unique={'DROP': 63, 'NOT_EVALUATED': 3, 'WAIT': 42}`
- budget/AI lineage: `{'status': 'explicit_ai_trace_budget_pass_only', 'pipeline_stage_order_contract': 'latest_watching_ai_to_budget_precheck_to_final_authority_revalidation', 'raw_ai_budget_census_is_causal': False, 'ai_trace_count': 329, 'ai_trace_source_stage_counts': {'ai_confirmed': 307, 'early_accel_strong_bundle_recheck_failed': 22}, 'budget_or_block_event_count': 553, 'lineage_contract_event_count': 553, 'lineage_contract_coverage_pct': 100.0, 'pre_ai_parent_not_expected_event_count': 501, 'lineage_join_eligible_event_count': 26, 'lineage_contract_missing_event_count': 0, 'lineage_field_present_count': 26, 'parent_trace_missing_when_expected_event_count': 0, 'parent_attempt_without_trusted_result_event_count': 26, 'ai_attempt_result_unavailable_parent_not_expected_event_count': 26, 'parent_trace_missing_without_attempt_event_count': 0, 'lineage_exact_trusted_count': 23, 'lineage_untrusted_or_stale_event_count': 3, 'lineage_untrusted_or_stale_reason_counts': {'source_stale': 2, 'trace_id_mismatch': 1}, 'lineage_joined_event_count': 23, 'exact_parent_trace_unresolved_event_count': 0, 'lineage_join_coverage_pct': 88.46, 'raw_event_lineage_join_coverage_pct': 4.16, 'lineage_join_coverage_denominator': 'events_with_a_trusted_ai_result_expected; excludes_pre_ai_and_explicit_attempt_result_unavailable', 'linked_budget_pass_trace_count': 19, 'linked_budget_block_trace_count': 0, 'linked_stage_counts': {'budget_pass': 23}, 'runtime_effect': False, 'allowed_runtime_apply': False}`
- latency blockers: `latency_block:latency_state_danger=286`
- latency causal join: `raw_danger_events=286, raw_unique=69, joined_budget_events=286, joined_budget_unique=69, budget_missing_key=0, latency_missing_key=0`
- price guards: `-`
- quote refresh: `attempted=15, applied=15, latency_recovered=5, submitted_after_refresh=1`
- quote refresh downstream: `{'entry_ai_authority_revalidation': 4, 'order_bundle_submitted': 1}`

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

- `5m`: ai=0, budget=1, latency=0, submitted=0, top=`blocked_overbought:-=4, blocked_strength_momentum:insufficient_history=4, blocked_strength_momentum:below_strength_base=2`, swing=`-`, upstream=`blocked_overbought:-=4, blocked_strength_momentum:insufficient_history=4, blocked_strength_momentum:below_strength_base=2`, ai_terminal=`-`
- `10m`: ai=0, budget=1, latency=0, submitted=0, top=`blocked_strength_momentum:insufficient_history=8, blocked_overbought:-=4, blocked_strength_momentum:below_strength_base=2`, swing=`-`, upstream=`blocked_strength_momentum:insufficient_history=8, blocked_overbought:-=4, blocked_strength_momentum:below_strength_base=2`, ai_terminal=`-`
- `30m`: ai=5, budget=5, latency=0, submitted=0, top=`blocked_strength_momentum:insufficient_history=21, blocked_strength_momentum:below_window_buy_value=11, blocked_overbought:-=9`, swing=`-`, upstream=`blocked_strength_momentum:insufficient_history=21, blocked_strength_momentum:below_window_buy_value=11, blocked_overbought:-=9`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=4`
