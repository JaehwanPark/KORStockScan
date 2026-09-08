# BUY Funnel Sentinel 2026-09-08

## 판정

- primary: `SUBMIT_DROUGHT_CRITICAL`
- secondary: `PRICE_GUARD_DROUGHT, ENTRY_AI_AUTHORITY_DROUGHT, LATENCY_DROUGHT, UPSTREAM_AI_THRESHOLD`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `false`
- followup_route: `entry_submit_drought_auto_workorder`
- followup_owner: `postclose_threshold_cycle`
- runtime_effect: `auto_workorder_no_intraday_mutation`
- submit_contract_downstream: `code_improvement_workorder, threshold_cycle_ev_report, runtime_approval_summary, postclose_verifier`
- submit_contract_weak_matches: `BROKER_RECEIPT, BUDGET_PASS_COLLAPSE, ENTRY_AI_AUTHORITY_REVALIDATION, FILL_QUALITY, LATENCY_PRE_SUBMIT, PRICE_REVALIDATION, SIM_REAL_AUTHORITY, TELEGRAM_POST_SUBMIT_ONLY, UPSTREAM_GATE`

## 근거

- as_of: `2026-09-08T19:20:05`
- baseline_date: `2026-09-07`
- ai_confirmed unique: `277`
- budget_pass unique: `665`
- latency_pass unique: `106`
- submitted unique: `0`
- holding_started unique: `0`
- budget/ai unique: `240.1%` (baseline `163.7`)
- submitted/ai unique: `0.0%` (baseline `1.0`)
- economic bundles: `observed=0, valid=0, probe_only=0, partial_residual=0, full=0`
- economic submitted/requested: `qty=0/0 (0.0%), notional=0/0 (0.0%)`
- economic participation by venue: `{}`
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- exact attempt contract: `status=pass, identity=record_id, fallback_allowed=False, missing=0, order_violation=0, terminal_causal=212`
- submit drought core axes: `UPSTREAM_GATE, LATENCY_PRE_SUBMIT, ENTRY_AI_AUTHORITY_REVALIDATION, PRICE_REVALIDATION, BROKER_RECEIPT`
- top blockers: `latency_block:latency_state_danger=378, blocked_strength_momentum:below_window_buy_value=366, blocked_strength_momentum:insufficient_history=256, blocked_overbought:-=194, blocked_strength_momentum:below_strength_base=171`
- swing blockers: `-`
- upstream blockers: `blocked_strength_momentum:below_window_buy_value=366, blocked_strength_momentum:insufficient_history=256, blocked_overbought:-=194, blocked_strength_momentum:below_strength_base=171, blocked_vpw:-=144`
- AI terminal reasons: `ai_terminal:entry_policy_no_buy_score_prior=96, ai_terminal:first_ai_wait_big_bite_not_confirmed=62`
- AI actions: `events={'DROP': 194, 'NOT_EVALUATED': 4, 'WAIT': 79}, unique={'DROP': 71, 'NOT_EVALUATED': 4, 'WAIT': 44}`
- budget/AI lineage: `{'status': 'explicit_ai_trace_budget_pass_only', 'pipeline_stage_order_contract': 'latest_watching_ai_to_budget_precheck_to_final_authority_revalidation', 'raw_ai_budget_census_is_causal': False, 'ai_trace_count': 296, 'ai_trace_source_stage_counts': {'ai_confirmed': 277, 'early_accel_strong_bundle_recheck_failed': 19}, 'budget_or_block_event_count': 685, 'lineage_contract_event_count': 685, 'lineage_contract_coverage_pct': 100.0, 'pre_ai_parent_not_expected_event_count': 566, 'lineage_join_eligible_event_count': 53, 'lineage_contract_missing_event_count': 0, 'lineage_field_present_count': 53, 'parent_trace_missing_when_expected_event_count': 0, 'parent_attempt_without_trusted_result_event_count': 66, 'ai_attempt_result_unavailable_parent_not_expected_event_count': 66, 'parent_trace_missing_without_attempt_event_count': 0, 'lineage_exact_trusted_count': 38, 'lineage_untrusted_or_stale_event_count': 15, 'lineage_untrusted_or_stale_reason_counts': {'source_stale': 8, 'trace_id_mismatch_and_source_stale': 7}, 'lineage_joined_event_count': 38, 'exact_parent_trace_unresolved_event_count': 0, 'lineage_join_coverage_pct': 71.7, 'raw_event_lineage_join_coverage_pct': 5.55, 'lineage_join_coverage_denominator': 'events_with_a_trusted_ai_result_expected; excludes_pre_ai_and_explicit_attempt_result_unavailable', 'linked_budget_pass_trace_count': 28, 'linked_budget_block_trace_count': 0, 'linked_stage_counts': {'budget_pass': 38}, 'runtime_effect': False, 'allowed_runtime_apply': False}`
- latency blockers: `latency_block:latency_state_danger=378`
- latency causal join: `raw_danger_events=378, raw_unique=96, joined_budget_events=378, joined_budget_unique=96, budget_missing_key=0, latency_missing_key=0`
- price guards: `entry_price_canary_submit_block:ai_input_preflight_blocked=69, entry_price_canary_submit_block:entry_candle_source_quality_blocked=20, entry_price_canary_submit_block:entry_price_feature_packet_source_quality_blocked=13, entry_submit_revalidation_block:observed_mark_gap_unresolved=5, entry_submit_revalidation_block:standard_stale_context_or_quote=2`
- quote refresh: `attempted=49, applied=35, latency_recovered=9, submitted_after_refresh=0`
- quote refresh downstream: `{'entry_ai_authority_revalidation': 9}`

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

- `5m`: ai=3, budget=1, latency=1, submitted=0, top=`blocked_strength_momentum:below_window_buy_value=4, blocked_strength_momentum:insufficient_history=4, blocked_strength_momentum:below_strength_base=2`, swing=`-`, upstream=`blocked_strength_momentum:below_window_buy_value=4, blocked_strength_momentum:insufficient_history=4, blocked_strength_momentum:below_strength_base=2`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=1`
- `10m`: ai=4, budget=2, latency=1, submitted=0, top=`blocked_strength_momentum:insufficient_history=8, blocked_strength_momentum:below_window_buy_value=6, blocked_vpw:-=2`, swing=`-`, upstream=`blocked_strength_momentum:insufficient_history=8, blocked_strength_momentum:below_window_buy_value=6, blocked_vpw:-=2`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=2`
- `30m`: ai=9, budget=4, latency=2, submitted=0, top=`blocked_strength_momentum:insufficient_history=17, blocked_strength_momentum:below_window_buy_value=11, blocked_strength_momentum:below_strength_base=4`, swing=`-`, upstream=`blocked_strength_momentum:insufficient_history=17, blocked_strength_momentum:below_window_buy_value=11, blocked_strength_momentum:below_strength_base=4`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=5`
