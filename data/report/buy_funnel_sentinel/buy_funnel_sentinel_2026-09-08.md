# BUY Funnel Sentinel 2026-09-08

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
- submit_contract_weak_matches: `BROKER_RECEIPT, BUDGET_PASS_COLLAPSE, FILL_QUALITY, LATENCY_PRE_SUBMIT, SIM_REAL_AUTHORITY, TELEGRAM_POST_SUBMIT_ONLY`

## 근거

- as_of: `2026-09-08T09:15:04`
- baseline_date: `2026-09-07`
- ai_confirmed unique: `4`
- budget_pass unique: `10`
- latency_pass unique: `1`
- submitted unique: `0`
- holding_started unique: `0`
- budget/ai unique: `250.0%` (baseline `42.9`)
- submitted/ai unique: `0.0%` (baseline `0.0`)
- economic bundles: `observed=0, valid=0, probe_only=0, partial_residual=0, full=0`
- economic submitted/requested: `qty=0/0 (0.0%), notional=0/0 (0.0%)`
- economic participation by venue: `{}`
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- exact attempt contract: `status=pass, identity=record_id, fallback_allowed=False, missing=0, order_violation=0, terminal_causal=12`
- submit drought core axes: `UPSTREAM_GATE, LATENCY_PRE_SUBMIT, ENTRY_AI_AUTHORITY_REVALIDATION, PRICE_REVALIDATION, BROKER_RECEIPT`
- top blockers: `latency_block:latency_state_danger=7, blocked_strength_momentum:below_window_buy_value=4, first_ai_wait:-=3, blocked_strength_momentum:below_buy_ratio=2, blocked_vpw:-=2`
- swing blockers: `-`
- upstream blockers: `blocked_strength_momentum:below_window_buy_value=4, first_ai_wait:-=3, blocked_strength_momentum:below_buy_ratio=2, blocked_vpw:-=2, blocked_strength_momentum:below_strength_base=2`
- AI terminal reasons: `ai_terminal:first_ai_wait_big_bite_not_confirmed=3`
- AI actions: `events={'DROP': 3, 'NOT_EVALUATED': 1}, unique={'DROP': 3, 'NOT_EVALUATED': 1}`
- budget/AI lineage: `{'status': 'pre_ai_budget_order_observed_no_parent_expected', 'pipeline_stage_order_contract': 'latest_watching_ai_to_budget_precheck_to_final_authority_revalidation', 'raw_ai_budget_census_is_causal': False, 'ai_trace_count': 4, 'ai_trace_source_stage_counts': {'ai_confirmed': 4}, 'budget_or_block_event_count': 14, 'lineage_contract_event_count': 14, 'lineage_contract_coverage_pct': 100.0, 'pre_ai_parent_not_expected_event_count': 14, 'lineage_join_eligible_event_count': 0, 'lineage_contract_missing_event_count': 0, 'lineage_field_present_count': 0, 'parent_trace_missing_when_expected_event_count': 0, 'parent_attempt_without_trusted_result_event_count': 0, 'ai_attempt_result_unavailable_parent_not_expected_event_count': 0, 'parent_trace_missing_without_attempt_event_count': 0, 'lineage_exact_trusted_count': 0, 'lineage_untrusted_or_stale_event_count': 0, 'lineage_untrusted_or_stale_reason_counts': {}, 'lineage_joined_event_count': 0, 'exact_parent_trace_unresolved_event_count': 0, 'lineage_join_coverage_pct': 0.0, 'raw_event_lineage_join_coverage_pct': 0.0, 'lineage_join_coverage_denominator': 'events_with_a_trusted_ai_result_expected; excludes_pre_ai_and_explicit_attempt_result_unavailable', 'linked_budget_pass_trace_count': 0, 'linked_budget_block_trace_count': 0, 'linked_stage_counts': {}, 'runtime_effect': False, 'allowed_runtime_apply': False}`
- latency blockers: `latency_block:latency_state_danger=7`
- latency causal join: `raw_danger_events=7, raw_unique=4, joined_budget_events=7, joined_budget_unique=4, budget_missing_key=0, latency_missing_key=0`
- price guards: `-`
- quote refresh: `attempted=5, applied=5, latency_recovered=1, submitted_after_refresh=0`
- quote refresh downstream: `{'entry_ai_authority_revalidation': 1}`

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

- `5m`: ai=1, budget=3, latency=0, submitted=0, top=`blocked_strength_momentum:below_window_buy_value=3, blocked_overbought:-=1, blocked_vpw:-=1`, swing=`-`, upstream=`blocked_strength_momentum:below_window_buy_value=3, blocked_overbought:-=1, blocked_vpw:-=1`, ai_terminal=`ai_terminal:first_ai_wait_big_bite_not_confirmed=1`
- `10m`: ai=4, budget=10, latency=1, submitted=0, top=`latency_block:latency_state_danger=7, blocked_strength_momentum:below_window_buy_value=4, first_ai_wait:-=3`, swing=`-`, upstream=`blocked_strength_momentum:below_window_buy_value=4, first_ai_wait:-=3, blocked_strength_momentum:below_buy_ratio=2`, ai_terminal=`ai_terminal:first_ai_wait_big_bite_not_confirmed=3`
- `30m`: ai=4, budget=10, latency=1, submitted=0, top=`latency_block:latency_state_danger=7, blocked_strength_momentum:below_window_buy_value=4, first_ai_wait:-=3`, swing=`-`, upstream=`blocked_strength_momentum:below_window_buy_value=4, first_ai_wait:-=3, blocked_strength_momentum:below_buy_ratio=2`, ai_terminal=`ai_terminal:first_ai_wait_big_bite_not_confirmed=3`
