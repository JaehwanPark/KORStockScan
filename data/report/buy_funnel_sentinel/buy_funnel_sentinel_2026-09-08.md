# BUY Funnel Sentinel 2026-09-08

## 판정

- primary: `SUBMIT_DROUGHT_CRITICAL`
- secondary: `PRICE_GUARD_DROUGHT, LATENCY_DROUGHT, UPSTREAM_AI_THRESHOLD`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `false`
- followup_route: `entry_submit_drought_auto_workorder`
- followup_owner: `postclose_threshold_cycle`
- runtime_effect: `auto_workorder_no_intraday_mutation`
- submit_contract_downstream: `code_improvement_workorder, threshold_cycle_ev_report, runtime_approval_summary, postclose_verifier`
- submit_contract_weak_matches: `BROKER_RECEIPT, BUDGET_PASS_COLLAPSE, FILL_QUALITY, LATENCY_PRE_SUBMIT, PRICE_REVALIDATION, SIM_REAL_AUTHORITY, TELEGRAM_POST_SUBMIT_ONLY, UPSTREAM_GATE`

## 근거

- as_of: `2026-09-08T16:30:07`
- baseline_date: `2026-09-07`
- ai_confirmed unique: `235`
- budget_pass unique: `607`
- latency_pass unique: `91`
- submitted unique: `0`
- holding_started unique: `0`
- budget/ai unique: `258.3%` (baseline `160.8`)
- submitted/ai unique: `0.0%` (baseline `0.4`)
- economic bundles: `observed=0, valid=0, probe_only=0, partial_residual=0, full=0`
- economic submitted/requested: `qty=0/0 (0.0%), notional=0/0 (0.0%)`
- economic participation by venue: `{}`
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- exact attempt contract: `status=pass, identity=record_id, fallback_allowed=False, missing=0, order_violation=0, terminal_causal=46`
- submit drought core axes: `UPSTREAM_GATE, LATENCY_PRE_SUBMIT, ENTRY_AI_AUTHORITY_REVALIDATION, PRICE_REVALIDATION, BROKER_RECEIPT`
- top blockers: `latency_block:latency_state_danger=359, blocked_strength_momentum:below_window_buy_value=278, blocked_overbought:-=194, blocked_strength_momentum:below_strength_base=151, blocked_vpw:-=127`
- swing blockers: `-`
- upstream blockers: `blocked_strength_momentum:below_window_buy_value=278, blocked_overbought:-=194, blocked_strength_momentum:below_strength_base=151, blocked_vpw:-=127, blocked_strength_momentum:insufficient_history=123`
- AI terminal reasons: `ai_terminal:entry_policy_no_buy_score_prior=80, ai_terminal:first_ai_wait_big_bite_not_confirmed=55`
- AI actions: `events={'DROP': 169, 'NOT_EVALUATED': 3, 'WAIT': 63}, unique={'DROP': 66, 'NOT_EVALUATED': 3, 'WAIT': 39}`
- budget/AI lineage: `{'status': 'explicit_ai_trace_budget_pass_only', 'pipeline_stage_order_contract': 'latest_watching_ai_to_budget_precheck_to_final_authority_revalidation', 'raw_ai_budget_census_is_causal': False, 'ai_trace_count': 249, 'ai_trace_source_stage_counts': {'ai_confirmed': 235, 'early_accel_strong_bundle_recheck_failed': 14}, 'budget_or_block_event_count': 624, 'lineage_contract_event_count': 624, 'lineage_contract_coverage_pct': 100.0, 'pre_ai_parent_not_expected_event_count': 516, 'lineage_join_eligible_event_count': 44, 'lineage_contract_missing_event_count': 0, 'lineage_field_present_count': 44, 'parent_trace_missing_when_expected_event_count': 0, 'parent_attempt_without_trusted_result_event_count': 64, 'ai_attempt_result_unavailable_parent_not_expected_event_count': 64, 'parent_trace_missing_without_attempt_event_count': 0, 'lineage_exact_trusted_count': 30, 'lineage_untrusted_or_stale_event_count': 14, 'lineage_untrusted_or_stale_reason_counts': {'source_stale': 7, 'trace_id_mismatch_and_source_stale': 7}, 'lineage_joined_event_count': 30, 'exact_parent_trace_unresolved_event_count': 0, 'lineage_join_coverage_pct': 68.18, 'raw_event_lineage_join_coverage_pct': 4.81, 'lineage_join_coverage_denominator': 'events_with_a_trusted_ai_result_expected; excludes_pre_ai_and_explicit_attempt_result_unavailable', 'linked_budget_pass_trace_count': 23, 'linked_budget_block_trace_count': 0, 'linked_stage_counts': {'budget_pass': 30}, 'runtime_effect': False, 'allowed_runtime_apply': False}`
- latency blockers: `latency_block:latency_state_danger=359`
- latency causal join: `raw_danger_events=359, raw_unique=95, joined_budget_events=359, joined_budget_unique=95, budget_missing_key=0, latency_missing_key=0`
- price guards: `entry_price_canary_submit_block:ai_input_preflight_blocked=59, entry_price_canary_submit_block:entry_candle_source_quality_blocked=20, entry_price_canary_submit_block:entry_price_feature_packet_source_quality_blocked=13, entry_submit_revalidation_block:observed_mark_gap_unresolved=5, entry_submit_revalidation_block:standard_stale_context_or_quote=2`
- quote refresh: `attempted=15, applied=12, latency_recovered=0, submitted_after_refresh=0`
- quote refresh downstream: `{}`

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

- `5m`: ai=1, budget=4, latency=0, submitted=0, top=`latency_block:latency_state_danger=4, blocked_strength_momentum:below_window_buy_value=4, blocked_strength_momentum:insufficient_history=3`, swing=`-`, upstream=`blocked_strength_momentum:below_window_buy_value=4, blocked_strength_momentum:insufficient_history=3, blocked_vpw:-=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=1`
- `10m`: ai=2, budget=8, latency=0, submitted=0, top=`blocked_strength_momentum:below_window_buy_value=8, latency_block:latency_state_danger=8, blocked_strength_momentum:insufficient_history=7`, swing=`-`, upstream=`blocked_strength_momentum:below_window_buy_value=8, blocked_strength_momentum:insufficient_history=7, blocked_ai_score:ai_score_50_buy_hold_override=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=1`
- `30m`: ai=11, budget=19, latency=0, submitted=0, top=`blocked_strength_momentum:insufficient_history=30, blocked_strength_momentum:below_window_buy_value=28, latency_block:latency_state_danger=15`, swing=`-`, upstream=`blocked_strength_momentum:insufficient_history=30, blocked_strength_momentum:below_window_buy_value=28, blocked_vpw:-=7`, ai_terminal=`ai_terminal:first_ai_wait_big_bite_not_confirmed=5, ai_terminal:entry_policy_no_buy_score_prior=4`
