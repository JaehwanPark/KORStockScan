# BUY Funnel Sentinel 2026-09-01

## 판정

- primary: `SUBMIT_DROUGHT_CRITICAL`
- secondary: `ENTRY_AI_AUTHORITY_DROUGHT, UPSTREAM_AI_THRESHOLD`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `false`
- followup_route: `entry_submit_drought_auto_workorder`
- followup_owner: `postclose_threshold_cycle_and_lifecycle_decision_matrix`
- runtime_effect: `auto_workorder_no_intraday_mutation`
- submit_contract_downstream: `code_improvement_workorder, lifecycle_decision_matrix.submit_bucket_attribution, threshold_cycle_ev_report, runtime_approval_summary, postclose_verifier`
- submit_contract_weak_matches: `BROKER_RECEIPT, BUDGET_PASS_COLLAPSE, ECONOMIC_PARTICIPATION, ENTRY_AI_AUTHORITY_REVALIDATION, FILL_QUALITY, SIM_REAL_AUTHORITY, TELEGRAM_POST_SUBMIT_ONLY, UPSTREAM_GATE`

## 근거

- as_of: `2026-09-01T19:20:03`
- baseline_date: `2026-08-31`
- ai_confirmed unique: `76`
- budget_pass unique: `101`
- latency_pass unique: `36`
- submitted unique: `4`
- holding_started unique: `3`
- budget/ai unique: `132.9%` (baseline `184.9`)
- submitted/ai unique: `5.3%` (baseline `3.5`)
- economic bundles: `observed=4, valid=4, probe_only=4, partial_residual=0, full=0`
- economic submitted/requested: `qty=4/11 (36.4%), notional=59780/152040 (39.3%)`
- economic participation by venue: `{'KRX': {'bundle_count': 3, 'probe_only_bundle_count': 3, 'partial_residual_bundle_count': 0, 'full_submitted_bundle_count': 0, 'requested_qty': 10, 'submitted_qty': 3, 'requested_notional_krw': 141260, 'submitted_notional_krw': 49000, 'submitted_qty_to_requested_qty_pct': 30.0, 'submitted_notional_to_requested_notional_pct': 34.7}, 'NXT': {'bundle_count': 1, 'probe_only_bundle_count': 1, 'partial_residual_bundle_count': 0, 'full_submitted_bundle_count': 0, 'requested_qty': 1, 'submitted_qty': 1, 'requested_notional_krw': 10780, 'submitted_notional_krw': 10780, 'submitted_qty_to_requested_qty_pct': 100.0, 'submitted_notional_to_requested_notional_pct': 100.0}}`
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:below_window_buy_value=513, blocked_strength_momentum:insufficient_history=414, blocked_overbought:-=344, latency_block:latency_state_danger=253, blocked_strength_momentum:below_strength_base=241`
- swing blockers: `-`
- upstream blockers: `blocked_ai_score:ai_score_50_buy_hold_override=141, blocked_ai_score:score_0.0=39, first_ai_wait:-=34, blocked_ai_score:score_11.0=20, wait65_79_ev_candidate:score_70.0=20`
- AI terminal reasons: `ai_terminal:entry_policy_no_buy_score_prior=119, ai_terminal:first_ai_wait_big_bite_not_confirmed=34`
- AI actions: `events={'DROP': 141, 'NOT_EVALUATED': 24, 'WAIT': 107}, unique={'DROP': 141, 'NOT_EVALUATED': 24, 'WAIT': 107}`
- budget/AI lineage: `{'status': 'explicit_ai_trace_budget_block_observed', 'pipeline_stage_order_contract': 'latest_watching_ai_to_budget_precheck_to_final_authority_revalidation', 'raw_ai_budget_census_is_causal': False, 'ai_trace_count': 299, 'ai_trace_source_stage_counts': {'ai_confirmed': 272, 'early_accel_strong_bundle_recheck_corrected': 9, 'early_accel_strong_bundle_recheck_failed': 18}, 'budget_or_block_event_count': 566, 'lineage_contract_event_count': 566, 'lineage_contract_coverage_pct': 100.0, 'pre_ai_parent_not_expected_event_count': 496, 'lineage_join_eligible_event_count': 56, 'lineage_contract_missing_event_count': 0, 'lineage_field_present_count': 56, 'parent_trace_missing_when_expected_event_count': 0, 'parent_attempt_without_trusted_result_event_count': 14, 'ai_attempt_result_unavailable_parent_not_expected_event_count': 14, 'parent_trace_missing_without_attempt_event_count': 0, 'lineage_exact_trusted_count': 44, 'lineage_untrusted_or_stale_event_count': 12, 'lineage_untrusted_or_stale_reason_counts': {'source_stale': 9, 'trace_id_mismatch': 2, 'trace_id_mismatch_and_source_stale': 1}, 'lineage_joined_event_count': 44, 'exact_parent_trace_unresolved_event_count': 0, 'lineage_join_coverage_pct': 78.57, 'raw_event_lineage_join_coverage_pct': 7.77, 'lineage_join_coverage_denominator': 'events_with_a_trusted_ai_result_expected; excludes_pre_ai_and_explicit_attempt_result_unavailable', 'linked_budget_pass_trace_count': 26, 'linked_budget_block_trace_count': 2, 'linked_stage_counts': {'blocked_zero_qty': 2, 'budget_pass': 42}, 'runtime_effect': False, 'allowed_runtime_apply': False}`
- latency blockers: `latency_block:latency_state_danger=253`
- latency causal join: `raw_danger_events=253, raw_unique=76, joined_budget_events=253, joined_budget_unique=76, budget_missing_key=0, latency_missing_key=0`
- price guards: `entry_ai_price_canary_skip_order:orderbook_micro indicates bearish state with strong sell pressure and adverse liquidity=1, entry_ai_price_canary_fallback:pre_submit_price_guard=1, entry_ai_price_canary_fallback:skip_low_confidence=1`
- quote refresh: `attempted=8, applied=3, latency_recovered=3, submitted_after_refresh=0`
- quote refresh downstream: `{'entry_ai_authority_revalidation': 3}`

## 금지된 자동변경

- `score_threshold_relaxation`
- `spread_cap_relaxation`
- `fallback_reenable`
- `live_threshold_runtime_mutation`
- `bot_restart`

## 권고 액션

- Auto-route ai_confirmed -> budget_pass -> latency_pass -> order_bundle_submitted drought into postclose workorder/LDM handoff.
- Split root cause into upstream gate, budget pass, latency/pre-submit guard, and broker receipt buckets before tuning thresholds.
- Do not require operator approval for submitted drought surfacing or downstream workorder generation.

## Window Summary

- `5m`: ai=1, budget=1, latency=1, submitted=0, top=`blocked_strength_momentum:insufficient_history=4, pre_submit_entry_ai_authority_guard_block:fresh_ai_wait_observation_only_probe_veto=3, blocked_strength_momentum:below_window_buy_value=2`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=1`, ai_terminal=`-`
- `10m`: ai=2, budget=1, latency=1, submitted=0, top=`blocked_strength_momentum:insufficient_history=14, pre_submit_entry_ai_authority_guard_block:fresh_ai_wait_observation_only_probe_veto=4, blocked_strength_momentum:below_window_buy_value=4`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=2`, ai_terminal=`-`
- `30m`: ai=7, budget=1, latency=1, submitted=0, top=`blocked_strength_momentum:insufficient_history=40, blocked_strength_momentum:below_window_buy_value=25, blocked_ai_score:ai_score_50_buy_hold_override=10`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=10, first_ai_wait:-=1, blocked_ai_score:score_11.0=1`, ai_terminal=`ai_terminal:first_ai_wait_big_bite_not_confirmed=1, ai_terminal:entry_policy_no_buy_score_prior=1`
