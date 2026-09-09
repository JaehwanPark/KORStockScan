# BUY Funnel Sentinel 2026-09-09

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

- as_of: `2026-09-09T12:25:08`
- baseline_date: `2026-09-08`
- ai_confirmed unique: `211`
- budget_pass unique: `336`
- latency_pass unique: `54`
- submitted unique: `0`
- holding_started unique: `0`
- budget/ai unique: `159.2%` (baseline `250.0`)
- submitted/ai unique: `0.0%` (baseline `0.0`)
- economic bundles: `observed=0, valid=0, probe_only=0, partial_residual=0, full=0`
- economic submitted/requested: `qty=0/0 (0.0%), notional=0/0 (0.0%)`
- economic participation by venue: `{}`
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- exact attempt contract: `status=source_quality_gap_excluded, identity=record_id, fallback_allowed=False, missing=0, order_violation=0, terminal_causal=682`
- submit drought core axes: `UPSTREAM_GATE, LATENCY_PRE_SUBMIT, ENTRY_AI_AUTHORITY_REVALIDATION, PRICE_REVALIDATION, BROKER_RECEIPT`
- top blockers: `blocked_strength_momentum:insufficient_history=416, blocked_strength_momentum:below_window_buy_value=342, latency_block:latency_state_danger=215, blocked_overbought:-=138, blocked_vpw:-=87`
- swing blockers: `-`
- upstream blockers: `blocked_strength_momentum:insufficient_history=416, blocked_strength_momentum:below_window_buy_value=342, blocked_overbought:-=138, blocked_vpw:-=87, blocked_zero_qty:-=86`
- AI terminal reasons: `ai_terminal:entry_policy_no_buy_score_prior=100, ai_terminal:first_ai_wait_big_bite_not_confirmed=63`
- AI actions: `events={'DROP': 129, 'WAIT': 82}, unique={'DROP': 52, 'WAIT': 46}`
- budget/AI lineage: `{'status': 'explicit_ai_trace_budget_pass_only', 'pipeline_stage_order_contract': 'latest_watching_ai_to_budget_precheck_to_final_authority_revalidation', 'raw_ai_budget_census_is_causal': False, 'ai_trace_count': 224, 'ai_trace_source_stage_counts': {'ai_confirmed': 211, 'early_accel_strong_bundle_recheck_failed': 13}, 'budget_or_block_event_count': 422, 'lineage_contract_event_count': 422, 'lineage_contract_coverage_pct': 100.0, 'pre_ai_parent_not_expected_event_count': 374, 'lineage_join_eligible_event_count': 42, 'lineage_contract_missing_event_count': 0, 'lineage_field_present_count': 42, 'parent_trace_missing_when_expected_event_count': 0, 'parent_attempt_without_trusted_result_event_count': 6, 'ai_attempt_result_unavailable_parent_not_expected_event_count': 6, 'parent_trace_missing_without_attempt_event_count': 0, 'lineage_exact_trusted_count': 30, 'lineage_untrusted_or_stale_event_count': 12, 'lineage_untrusted_or_stale_reason_counts': {'source_stale': 5, 'trace_id_mismatch': 3, 'trace_id_mismatch_and_source_stale': 4}, 'lineage_joined_event_count': 30, 'exact_parent_trace_unresolved_event_count': 0, 'lineage_join_coverage_pct': 71.43, 'raw_event_lineage_join_coverage_pct': 7.11, 'lineage_join_coverage_denominator': 'events_with_a_trusted_ai_result_expected; excludes_pre_ai_and_explicit_attempt_result_unavailable', 'linked_budget_pass_trace_count': 23, 'linked_budget_block_trace_count': 0, 'linked_stage_counts': {'budget_pass': 30}, 'runtime_effect': False, 'allowed_runtime_apply': False}`
- latency blockers: `latency_block:latency_state_danger=215`
- latency causal join: `raw_danger_events=215, raw_unique=39, joined_budget_events=215, joined_budget_unique=39, budget_missing_key=0, latency_missing_key=0`
- price guards: `entry_price_canary_submit_block:ai_input_preflight_blocked=15, entry_price_canary_submit_block:entry_candle_source_quality_blocked=2, entry_submit_revalidation_block:observed_mark_gap_unresolved=2`
- quote refresh: `attempted=261, applied=203, latency_recovered=40, submitted_after_refresh=0`
- quote refresh downstream: `{'entry_ai_authority_revalidation': 40}`
- refresh transitions (overlapping exact attempt sets): `{'version': 1, 'count_basis': 'exact_attempt_transition_sets_not_disjoint_terminals', 'legacy_still_blocked_semantics': 'refresh_not_applied_blocked', 'refresh_not_applied_blocked': 44, 'refresh_applied_still_blocked': 163, 'refresh_applied_latency_pass': 40, 'refresh_applied_still_blocked_reason_counts': {'spread_above_caution_below_guard_cap': 123, 'orderbook_micro_spread_wide': 163, 'spread_too_wide': 33, 'ws_age_too_high': 9}, 'next_ai_blocker_counts': {'fresh_drop_veto': 16, 'fresh_wait_veto': 23, 'semantic_contract_rejected': 1}, 'next_blocker_reason_counts': {'pre_submit_entry_ai_authority_guard_block:entry_ai_result_stale_or_untrusted': 1, 'pre_submit_entry_ai_authority_guard_block:fresh_ai_drop_real_buy_veto': 16, 'pre_submit_entry_ai_authority_guard_block:fresh_ai_wait_observation_only_probe_veto': 23}, 'next_blocker_count_basis': 'ordered_latency_pass_occurrences', 'runtime_effect': False, 'allowed_runtime_apply': False}`
- AI authority subcauses: `{'fresh_drop_veto': 21, 'fresh_wait_veto': 27, 'input_preflight_gap': 2, 'semantic_contract_rejected': 1}`
- zero-qty subcauses: `{'broker_cash_capacity_nonpositive': 4, 'cash_capacity_provenance_unavailable': 82}`
- recheck input classes (not runtime eligibility): `{'input_gap': 49, 'normal_veto': 48, 'not_evaluated': 103}`

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

- `5m`: ai=6, budget=8, latency=2, submitted=0, top=`blocked_strength_momentum:insufficient_history=16, blocked_strength_momentum:below_window_buy_value=15, blocked_overbought:-=6`, swing=`-`, upstream=`blocked_strength_momentum:insufficient_history=16, blocked_strength_momentum:below_window_buy_value=15, blocked_overbought:-=6`, ai_terminal=`ai_terminal:first_ai_wait_big_bite_not_confirmed=3, ai_terminal:entry_policy_no_buy_score_prior=1`
- `10m`: ai=11, budget=25, latency=4, submitted=0, top=`blocked_strength_momentum:insufficient_history=22, blocked_strength_momentum:below_window_buy_value=17, latency_block:latency_state_danger=12`, swing=`-`, upstream=`blocked_strength_momentum:insufficient_history=22, blocked_strength_momentum:below_window_buy_value=17, blocked_overbought:-=7`, ai_terminal=`ai_terminal:first_ai_wait_big_bite_not_confirmed=4, ai_terminal:entry_policy_no_buy_score_prior=3`
- `30m`: ai=22, budget=48, latency=7, submitted=0, top=`blocked_strength_momentum:insufficient_history=51, blocked_strength_momentum:below_window_buy_value=36, latency_block:latency_state_danger=26`, swing=`-`, upstream=`blocked_strength_momentum:insufficient_history=51, blocked_strength_momentum:below_window_buy_value=36, blocked_overbought:-=20`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=11, ai_terminal:first_ai_wait_big_bite_not_confirmed=5`
