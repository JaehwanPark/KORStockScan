# BUY Funnel Sentinel 2026-09-11

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
- submit_contract_weak_matches: `BROKER_RECEIPT, BUDGET_PASS_COLLAPSE, ECONOMIC_PARTICIPATION, FILL_QUALITY, LATENCY_PRE_SUBMIT, PRICE_REVALIDATION, SIM_REAL_AUTHORITY, TELEGRAM_POST_SUBMIT_ONLY, UPSTREAM_GATE`

## 근거

- as_of: `2026-09-11T19:20:04`
- baseline_date: `2026-09-10`
- ai_confirmed unique: `270`
- budget_pass unique: `504`
- latency_pass unique: `88`
- submitted unique: `14`
- holding_started unique: `13`
- budget/ai unique: `186.7%` (baseline `191.8`)
- submitted/ai unique: `5.2%` (baseline `1.8`)
- economic bundles: `observed=14, valid=14, probe_only=14, partial_residual=0, full=0`
- economic submitted/requested: `qty=14/65 (21.5%), notional=655645/1101590 (59.5%)`
- economic participation by venue: `{'KRX': {'bundle_count': 12, 'probe_only_bundle_count': 12, 'partial_residual_bundle_count': 0, 'full_submitted_bundle_count': 0, 'requested_qty': 57, 'submitted_qty': 12, 'requested_notional_krw': 1020390, 'submitted_notional_krw': 635345, 'submitted_qty_to_requested_qty_pct': 21.1, 'submitted_notional_to_requested_notional_pct': 62.3}, 'NXT': {'bundle_count': 2, 'probe_only_bundle_count': 2, 'partial_residual_bundle_count': 0, 'full_submitted_bundle_count': 0, 'requested_qty': 8, 'submitted_qty': 2, 'requested_notional_krw': 81200, 'submitted_notional_krw': 20300, 'submitted_qty_to_requested_qty_pct': 25.0, 'submitted_notional_to_requested_notional_pct': 25.0}}`
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- exact attempt contract: `status=pass, identity=record_id, fallback_allowed=False, missing=0, order_violation=0, terminal_causal=191`
- submit drought core axes: `UPSTREAM_GATE, LATENCY_PRE_SUBMIT, ENTRY_AI_AUTHORITY_REVALIDATION, PRICE_REVALIDATION, BROKER_RECEIPT`
- capital-shortfall attempts excluded from drought: `18` (raw evidence retained)
- top blockers: `blocked_strength_momentum:below_window_buy_value=510, blocked_overbought:-=329, latency_block:latency_state_danger=275, blocked_strength_momentum:insufficient_history=261, blocked_strength_momentum:below_strength_base=238`
- swing blockers: `-`
- upstream blockers: `blocked_strength_momentum:below_window_buy_value=510, blocked_overbought:-=329, blocked_strength_momentum:insufficient_history=261, blocked_strength_momentum:below_strength_base=238, blocked_vpw:-=167`
- AI terminal reasons: `ai_terminal:entry_policy_no_buy_score_prior=96, ai_terminal:first_ai_wait_big_bite_not_confirmed=64`
- AI actions: `events={'DROP': 179, 'NOT_EVALUATED': 2, 'WAIT': 90}, unique={'DROP': 71, 'NOT_EVALUATED': 2, 'WAIT': 56}`
- budget/AI lineage: `{'status': 'explicit_ai_trace_budget_pass_only', 'pipeline_stage_order_contract': 'latest_watching_ai_to_budget_precheck_to_final_authority_revalidation', 'raw_ai_budget_census_is_causal': False, 'ai_trace_count': 289, 'ai_trace_source_stage_counts': {'ai_confirmed': 271, 'early_accel_strong_bundle_recheck_corrected': 11, 'early_accel_strong_bundle_recheck_failed': 7}, 'budget_or_block_event_count': 504, 'lineage_contract_event_count': 504, 'lineage_contract_coverage_pct': 100.0, 'pre_ai_parent_not_expected_event_count': 462, 'lineage_join_eligible_event_count': 25, 'lineage_contract_missing_event_count': 0, 'lineage_field_present_count': 25, 'parent_trace_missing_when_expected_event_count': 0, 'parent_attempt_without_trusted_result_event_count': 17, 'ai_attempt_result_unavailable_parent_not_expected_event_count': 17, 'parent_trace_missing_without_attempt_event_count': 0, 'lineage_exact_trusted_count': 23, 'lineage_untrusted_or_stale_event_count': 2, 'lineage_untrusted_or_stale_reason_counts': {'source_stale': 2}, 'lineage_joined_event_count': 23, 'exact_parent_trace_unresolved_event_count': 0, 'lineage_join_coverage_pct': 92.0, 'raw_event_lineage_join_coverage_pct': 4.56, 'lineage_join_coverage_denominator': 'events_with_a_trusted_ai_result_expected; excludes_pre_ai_and_explicit_attempt_result_unavailable', 'linked_budget_pass_trace_count': 21, 'linked_budget_block_trace_count': 0, 'linked_stage_counts': {'budget_pass': 23}, 'runtime_effect': False, 'allowed_runtime_apply': False}`
- latency blockers: `latency_block:latency_state_danger=275`
- latency causal join: `raw_danger_events=275, raw_unique=93, joined_budget_events=275, joined_budget_unique=93, budget_missing_key=0, latency_missing_key=0`
- price guards: `entry_price_canary_submit_block:ai_input_preflight_blocked=36, entry_price_canary_submit_block:entry_candle_source_quality_blocked=15, entry_submit_revalidation_block:standard_stale_context_or_quote=10`
- quote refresh: `attempted=24, applied=19, latency_recovered=3, submitted_after_refresh=1`
- quote refresh downstream: `{'entry_ai_authority_revalidation': 2, 'order_bundle_submitted': 1}`
- refresh transitions (overlapping exact attempt sets): `{'version': 1, 'count_basis': 'exact_attempt_transition_sets_not_disjoint_terminals', 'legacy_still_blocked_semantics': 'refresh_not_applied_blocked', 'refresh_not_applied_blocked': 3, 'refresh_applied_still_blocked': 16, 'refresh_applied_latency_pass': 3, 'refresh_applied_still_blocked_reason_counts': {'spread_above_caution_below_guard_cap': 15, 'orderbook_micro_spread_wide': 16, 'spread_too_wide': 1}, 'next_ai_blocker_counts': {'fresh_drop_veto': 2}, 'next_blocker_reason_counts': {'order_bundle_submitted:caution_normal_entry_allowed': 1, 'pre_submit_entry_ai_authority_guard_block:fresh_ai_drop_real_buy_veto': 2}, 'next_blocker_count_basis': 'ordered_latency_pass_occurrences', 'runtime_effect': False, 'allowed_runtime_apply': False}`
- AI authority subcauses: `{'authority_untrusted_or_unknown': 1, 'fresh_drop_veto': 37, 'fresh_wait_veto': 8, 'input_preflight_gap': 6, 'semantic_contract_rejected': 1}`
- zero-qty subcauses: `{}`
- recheck input classes (not runtime eligibility): `{'input_gap': 53, 'normal_veto': 45, 'not_evaluated': 141}`

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

- `5m`: ai=2, budget=0, latency=0, submitted=0, top=`blocked_strength_momentum:insufficient_history=6, blocked_strength_momentum:below_window_buy_value=5, blocked_liquidity:-=1`, swing=`-`, upstream=`blocked_strength_momentum:insufficient_history=6, blocked_strength_momentum:below_window_buy_value=4, blocked_liquidity:-=1`, ai_terminal=`ai_terminal:first_ai_wait_big_bite_not_confirmed=1, ai_terminal:entry_policy_no_buy_score_prior=1`
- `10m`: ai=3, budget=0, latency=0, submitted=0, top=`blocked_overbought:-=13, blocked_strength_momentum:insufficient_history=11, blocked_strength_momentum:below_strength_base=9`, swing=`-`, upstream=`blocked_overbought:-=13, blocked_strength_momentum:insufficient_history=11, blocked_strength_momentum:below_strength_base=9`, ai_terminal=`ai_terminal:first_ai_wait_big_bite_not_confirmed=1, ai_terminal:entry_policy_no_buy_score_prior=1`
- `30m`: ai=6, budget=2, latency=0, submitted=0, top=`blocked_strength_momentum:insufficient_history=36, blocked_strength_momentum:below_window_buy_value=28, blocked_strength_momentum:below_strength_base=15`, swing=`-`, upstream=`blocked_strength_momentum:insufficient_history=36, blocked_strength_momentum:below_window_buy_value=28, blocked_strength_momentum:below_strength_base=15`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=3, ai_terminal:first_ai_wait_big_bite_not_confirmed=2`
