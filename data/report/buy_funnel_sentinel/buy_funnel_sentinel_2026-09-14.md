# BUY Funnel Sentinel 2026-09-14

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

- as_of: `2026-09-14T19:40:05`
- baseline_date: `2026-09-11`
- ai_confirmed unique: `918`
- budget_pass unique: `203`
- latency_pass unique: `9`
- submitted unique: `2`
- holding_started unique: `1`
- budget/ai unique: `22.1%` (baseline `188.5`)
- submitted/ai unique: `0.2%` (baseline `5.2`)
- economic bundles: `observed=0, valid=0, probe_only=0, partial_residual=0, full=0`
- economic submitted/requested: `qty=0/0 (0.0%), notional=0/0 (0.0%)`
- economic participation by venue: `{}`
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- exact attempt contract: `status=source_quality_gap_excluded, identity=record_id, fallback_allowed=False, missing=0, order_violation=0, terminal_causal=160`
- submit drought core axes: `UPSTREAM_GATE, LATENCY_PRE_SUBMIT, ENTRY_AI_AUTHORITY_REVALIDATION, PRICE_REVALIDATION, BROKER_RECEIPT`
- capital-shortfall attempts excluded from drought: `0` (raw evidence retained)
- top blockers: `blocked_overbought:-=396, blocked_strength_momentum:below_window_buy_value=334, blocked_strength_momentum:below_strength_base=322, blocked_liquidity:-=250, blocked_vpw:-=207`
- swing blockers: `-`
- upstream blockers: `blocked_overbought:-=396, blocked_strength_momentum:below_window_buy_value=334, blocked_strength_momentum:below_strength_base=322, blocked_liquidity:-=250, blocked_vpw:-=207`
- AI terminal reasons: `ai_terminal:first_ai_wait_big_bite_not_confirmed=92, ai_terminal:entry_policy_no_buy_score_prior=74`
- AI actions: `events={'BUY': 5, 'DROP': 4505, 'NOT_EVALUATED': 10, 'WAIT': 1210}, unique={'BUY': 4, 'DROP': 203, 'NOT_EVALUATED': 9, 'WAIT': 124}`
- budget/AI lineage: `{'status': 'explicit_ai_trace_budget_block_observed', 'pipeline_stage_order_contract': 'latest_watching_ai_to_budget_precheck_to_final_authority_revalidation', 'raw_ai_budget_census_is_causal': False, 'ai_trace_count': 5730, 'ai_trace_source_stage_counts': {'ai_confirmed': 5730}, 'budget_or_block_event_count': 206, 'lineage_contract_event_count': 206, 'lineage_contract_coverage_pct': 100.0, 'pre_ai_parent_not_expected_event_count': 0, 'lineage_join_eligible_event_count': 206, 'lineage_contract_missing_event_count': 0, 'lineage_field_present_count': 206, 'parent_trace_missing_when_expected_event_count': 0, 'parent_attempt_without_trusted_result_event_count': 0, 'ai_attempt_result_unavailable_parent_not_expected_event_count': 0, 'parent_trace_missing_without_attempt_event_count': 0, 'lineage_exact_trusted_count': 28, 'lineage_untrusted_or_stale_event_count': 178, 'lineage_untrusted_or_stale_reason_counts': {'source_stale': 76, 'trace_id_mismatch_and_source_stale': 102}, 'lineage_joined_event_count': 28, 'exact_parent_trace_unresolved_event_count': 0, 'lineage_join_coverage_pct': 13.59, 'raw_event_lineage_join_coverage_pct': 13.59, 'lineage_join_coverage_denominator': 'events_with_a_trusted_ai_result_expected; excludes_pre_ai_and_explicit_attempt_result_unavailable', 'linked_budget_pass_trace_count': 16, 'linked_budget_block_trace_count': 2, 'linked_stage_counts': {'blocked_zero_qty': 2, 'budget_pass': 26}, 'runtime_effect': False, 'allowed_runtime_apply': False}`
- latency blockers: `latency_block:latency_state_danger=170`
- latency causal join: `raw_danger_events=170, raw_unique=12, joined_budget_events=170, joined_budget_unique=12, budget_missing_key=0, latency_missing_key=0`
- price guards: `entry_price_canary_submit_block:entry_candle_source_quality_blocked=11, entry_price_canary_submit_block:ai_input_preflight_blocked=8, entry_submit_revalidation_block:standard_stale_context_or_quote=2, entry_submit_revalidation_block:observed_mark_gap_unresolved=1`
- quote refresh: `attempted=2, applied=1, latency_recovered=0, submitted_after_refresh=0`
- quote refresh downstream: `{}`
- refresh transitions (overlapping exact attempt sets): `{'version': 1, 'count_basis': 'exact_attempt_transition_sets_not_disjoint_terminals', 'legacy_still_blocked_semantics': 'refresh_not_applied_blocked', 'refresh_not_applied_blocked': 1, 'refresh_applied_still_blocked': 1, 'refresh_applied_latency_pass': 0, 'refresh_applied_still_blocked_reason_counts': {'spread_above_caution_below_guard_cap': 1, 'orderbook_micro_spread_wide': 1}, 'next_ai_blocker_counts': {}, 'next_blocker_reason_counts': {}, 'next_blocker_count_basis': 'ordered_latency_pass_occurrences', 'runtime_effect': False, 'allowed_runtime_apply': False}`
- AI authority subcauses: `{'fresh_drop_veto': 1, 'fresh_wait_veto': 1, 'input_preflight_gap': 2}`
- zero-qty subcauses: `{'other_sizing_cap': 2}`
- recheck input classes (not runtime eligibility): `{'input_gap': 40, 'machine_block_point_drop': 3, 'machine_recheck_observation': 2, 'normal_veto': 2, 'not_evaluated': 150}`

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

- `5m`: ai=6, budget=9, latency=0, submitted=0, top=`entry_price_canary_submit_block:entry_candle_source_quality_blocked=7, blocked_strength_momentum:insufficient_history=4, entry_price_canary_submit_block:ai_input_preflight_blocked=2`, swing=`-`, upstream=`blocked_strength_momentum:insufficient_history=4, blocked_overbought:-=1`, ai_terminal=`-`
- `10m`: ai=10, budget=12, latency=0, submitted=0, top=`blocked_overbought:-=11, blocked_strength_momentum:insufficient_history=11, entry_price_canary_submit_block:entry_candle_source_quality_blocked=8`, swing=`-`, upstream=`blocked_overbought:-=10, blocked_strength_momentum:insufficient_history=10, blocked_strength_momentum:below_strength_base=4`, ai_terminal=`-`
- `30m`: ai=28, budget=15, latency=0, submitted=0, top=`blocked_strength_momentum:insufficient_history=23, blocked_overbought:-=21, blocked_strength_momentum:below_strength_base=13`, swing=`-`, upstream=`blocked_strength_momentum:insufficient_history=23, blocked_overbought:-=21, blocked_strength_momentum:below_strength_base=13`, ai_terminal=`ai_terminal:first_ai_wait_big_bite_not_confirmed=2, ai_terminal:entry_policy_no_buy_score_prior=1`
