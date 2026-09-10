# BUY Funnel Sentinel 2026-09-10

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

- as_of: `2026-09-10T19:20:03`
- baseline_date: `2026-09-09`
- ai_confirmed unique: `331`
- budget_pass unique: `631`
- latency_pass unique: `134`
- submitted unique: `6`
- holding_started unique: `5`
- budget/ai unique: `190.6%` (baseline `150.6`)
- submitted/ai unique: `1.8%` (baseline `0.0`)
- economic bundles: `observed=5, valid=5, probe_only=5, partial_residual=0, full=0`
- economic submitted/requested: `qty=5/5 (100.0%), notional=163086/163086 (100.0%)`
- economic participation by venue: `{'KRX': {'bundle_count': 5, 'probe_only_bundle_count': 5, 'partial_residual_bundle_count': 0, 'full_submitted_bundle_count': 0, 'requested_qty': 5, 'submitted_qty': 5, 'requested_notional_krw': 163086, 'submitted_notional_krw': 163086, 'submitted_qty_to_requested_qty_pct': 100.0, 'submitted_notional_to_requested_notional_pct': 100.0}}`
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- exact attempt contract: `status=pass, identity=record_id, fallback_allowed=False, missing=0, order_violation=0, terminal_causal=271`
- submit drought core axes: `UPSTREAM_GATE, LATENCY_PRE_SUBMIT, ENTRY_AI_AUTHORITY_REVALIDATION, PRICE_REVALIDATION, BROKER_RECEIPT`
- top blockers: `blocked_strength_momentum:below_window_buy_value=441, latency_block:latency_state_danger=344, blocked_strength_momentum:insufficient_history=298, blocked_strength_momentum:below_strength_base=277, blocked_liquidity:-=209`
- swing blockers: `-`
- upstream blockers: `blocked_strength_momentum:below_window_buy_value=441, blocked_strength_momentum:insufficient_history=298, blocked_strength_momentum:below_strength_base=277, blocked_liquidity:-=209, blocked_vpw:-=187`
- AI terminal reasons: `ai_terminal:entry_policy_no_buy_score_prior=114, ai_terminal:first_ai_wait_big_bite_not_confirmed=89`
- AI actions: `events={'DROP': 271, 'NOT_EVALUATED': 3, 'WAIT': 57}, unique={'DROP': 67, 'NOT_EVALUATED': 3, 'WAIT': 36}`
- budget/AI lineage: `{'status': 'explicit_ai_trace_budget_block_observed', 'pipeline_stage_order_contract': 'latest_watching_ai_to_budget_precheck_to_final_authority_revalidation', 'raw_ai_budget_census_is_causal': False, 'ai_trace_count': 344, 'ai_trace_source_stage_counts': {'ai_confirmed': 331, 'early_accel_strong_bundle_recheck_corrected': 7, 'early_accel_strong_bundle_recheck_failed': 6}, 'budget_or_block_event_count': 738, 'lineage_contract_event_count': 738, 'lineage_contract_coverage_pct': 100.0, 'pre_ai_parent_not_expected_event_count': 536, 'lineage_join_eligible_event_count': 101, 'lineage_contract_missing_event_count': 0, 'lineage_field_present_count': 101, 'parent_trace_missing_when_expected_event_count': 0, 'parent_attempt_without_trusted_result_event_count': 101, 'ai_attempt_result_unavailable_parent_not_expected_event_count': 101, 'parent_trace_missing_without_attempt_event_count': 0, 'lineage_exact_trusted_count': 22, 'lineage_untrusted_or_stale_event_count': 79, 'lineage_untrusted_or_stale_reason_counts': {'source_stale': 79}, 'lineage_joined_event_count': 22, 'exact_parent_trace_unresolved_event_count': 0, 'lineage_join_coverage_pct': 21.78, 'raw_event_lineage_join_coverage_pct': 2.98, 'lineage_join_coverage_denominator': 'events_with_a_trusted_ai_result_expected; excludes_pre_ai_and_explicit_attempt_result_unavailable', 'linked_budget_pass_trace_count': 15, 'linked_budget_block_trace_count': 2, 'linked_stage_counts': {'blocked_zero_qty': 2, 'budget_pass': 20}, 'runtime_effect': False, 'allowed_runtime_apply': False}`
- latency blockers: `latency_block:latency_state_danger=344`
- latency causal join: `raw_danger_events=344, raw_unique=82, joined_budget_events=344, joined_budget_unique=82, budget_missing_key=0, latency_missing_key=0`
- price guards: `entry_price_canary_submit_block:ai_input_preflight_blocked=55, entry_price_canary_submit_block:entry_price_feature_packet_source_quality_blocked=20, entry_price_canary_submit_block:entry_candle_source_quality_blocked=4, entry_submit_revalidation_block:standard_stale_context_or_quote=4, entry_submit_revalidation_block:observed_mark_gap_unresolved=1`
- quote refresh: `attempted=55, applied=34, latency_recovered=2, submitted_after_refresh=0`
- quote refresh downstream: `{'entry_ai_authority_revalidation': 2}`
- refresh transitions (overlapping exact attempt sets): `{'version': 1, 'count_basis': 'exact_attempt_transition_sets_not_disjoint_terminals', 'legacy_still_blocked_semantics': 'refresh_not_applied_blocked', 'refresh_not_applied_blocked': 20, 'refresh_applied_still_blocked': 32, 'refresh_applied_latency_pass': 2, 'refresh_applied_still_blocked_reason_counts': {'spread_above_caution_below_guard_cap': 23, 'orderbook_micro_spread_wide': 32, 'ws_age_too_high': 6, 'spread_too_wide': 3}, 'next_ai_blocker_counts': {'fresh_drop_veto': 2}, 'next_blocker_reason_counts': {'pre_submit_entry_ai_authority_guard_block:fresh_ai_drop_real_buy_veto': 2}, 'next_blocker_count_basis': 'ordered_latency_pass_occurrences', 'runtime_effect': False, 'allowed_runtime_apply': False}`
- AI authority subcauses: `{'authority_untrusted_or_unknown': 4, 'fresh_drop_veto': 29, 'fresh_wait_veto': 6, 'input_preflight_gap': 75}`
- zero-qty subcauses: `{'broker_cash_capacity_nonpositive': 97, 'other_sizing_cap': 10}`
- recheck input classes (not runtime eligibility): `{'input_gap': 131, 'normal_veto': 35, 'not_evaluated': 157}`

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

- `5m`: ai=1, budget=1, latency=0, submitted=0, top=`blocked_strength_momentum:insufficient_history=4, blocked_vpw:-=2, blocked_strength_momentum:below_window_buy_value=2`, swing=`-`, upstream=`blocked_strength_momentum:insufficient_history=4, blocked_vpw:-=2, blocked_strength_momentum:below_window_buy_value=2`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=1`
- `10m`: ai=6, budget=2, latency=0, submitted=0, top=`blocked_strength_momentum:insufficient_history=16, blocked_strength_momentum:below_window_buy_value=9, blocked_liquidity:-=4`, swing=`-`, upstream=`blocked_strength_momentum:insufficient_history=16, blocked_strength_momentum:below_window_buy_value=9, blocked_liquidity:-=4`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=5, ai_terminal:first_ai_wait_big_bite_not_confirmed=1`
- `30m`: ai=11, budget=10, latency=1, submitted=0, top=`blocked_strength_momentum:insufficient_history=38, blocked_strength_momentum:below_window_buy_value=22, latency_block:latency_state_danger=9`, swing=`-`, upstream=`blocked_strength_momentum:insufficient_history=38, blocked_strength_momentum:below_window_buy_value=22, blocked_vpw:-=8`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=8, ai_terminal:first_ai_wait_big_bite_not_confirmed=2`
