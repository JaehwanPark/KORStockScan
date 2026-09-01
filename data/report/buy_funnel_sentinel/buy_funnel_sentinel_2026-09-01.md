# BUY Funnel Sentinel 2026-09-01

## 판정

- primary: `SUBMIT_DROUGHT_CRITICAL`
- secondary: `ENTRY_AI_AUTHORITY_DROUGHT, LATENCY_DROUGHT, UPSTREAM_AI_THRESHOLD`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `false`
- followup_route: `entry_submit_drought_auto_workorder`
- followup_owner: `postclose_threshold_cycle_and_lifecycle_decision_matrix`
- runtime_effect: `auto_workorder_no_intraday_mutation`
- submit_contract_downstream: `code_improvement_workorder, lifecycle_decision_matrix.submit_bucket_attribution, threshold_cycle_ev_report, runtime_approval_summary, postclose_verifier`
- submit_contract_weak_matches: `BROKER_RECEIPT, BUDGET_PASS_COLLAPSE, ECONOMIC_PARTICIPATION, ENTRY_AI_AUTHORITY_REVALIDATION, FILL_QUALITY, LATENCY_PRE_SUBMIT, SIM_REAL_AUTHORITY, TELEGRAM_POST_SUBMIT_ONLY, UPSTREAM_GATE`

## 근거

- as_of: `2026-09-01T16:00:05`
- baseline_date: `2026-08-31`
- ai_confirmed unique: `63`
- budget_pass unique: `96`
- latency_pass unique: `31`
- submitted unique: `3`
- holding_started unique: `2`
- budget/ai unique: `152.4%` (baseline `201.4`)
- submitted/ai unique: `4.8%` (baseline `4.1`)
- economic bundles: `observed=3, valid=3, probe_only=3, partial_residual=0, full=0`
- economic submitted/requested: `qty=3/10 (30.0%), notional=49000/141260 (34.7%)`
- economic participation by venue: `{'KRX': {'bundle_count': 3, 'probe_only_bundle_count': 3, 'partial_residual_bundle_count': 0, 'full_submitted_bundle_count': 0, 'requested_qty': 10, 'submitted_qty': 3, 'requested_notional_krw': 141260, 'submitted_notional_krw': 49000, 'submitted_qty_to_requested_qty_pct': 30.0, 'submitted_notional_to_requested_notional_pct': 34.7}}`
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:below_window_buy_value=317, latency_block:latency_state_danger=246, blocked_overbought:-=246, blocked_strength_momentum:below_strength_base=173, blocked_liquidity:-=157`
- swing blockers: `-`
- upstream blockers: `blocked_ai_score:ai_score_50_buy_hold_override=100, first_ai_wait:-=27, blocked_ai_score:score_0.0=23, wait65_79_ev_candidate:score_70.0=20, blocked_ai_score:score_11.0=14`
- AI terminal reasons: `ai_terminal:entry_policy_no_buy_score_prior=89, ai_terminal:first_ai_wait_big_bite_not_confirmed=27`
- AI actions: `events={'DROP': 106, 'NOT_EVALUATED': 17, 'WAIT': 76}, unique={'DROP': 106, 'NOT_EVALUATED': 17, 'WAIT': 76}`
- budget/AI lineage: `{'status': 'explicit_ai_trace_budget_block_observed', 'pipeline_stage_order_contract': 'latest_watching_ai_to_budget_precheck_to_final_authority_revalidation', 'raw_ai_budget_census_is_causal': False, 'ai_trace_count': 219, 'ai_trace_source_stage_counts': {'ai_confirmed': 199, 'early_accel_strong_bundle_recheck_corrected': 9, 'early_accel_strong_bundle_recheck_failed': 11}, 'budget_or_block_event_count': 523, 'lineage_contract_event_count': 523, 'lineage_contract_coverage_pct': 100.0, 'pre_ai_parent_not_expected_event_count': 468, 'lineage_join_eligible_event_count': 42, 'lineage_contract_missing_event_count': 0, 'lineage_field_present_count': 42, 'parent_trace_missing_when_expected_event_count': 0, 'parent_attempt_without_trusted_result_event_count': 13, 'ai_attempt_result_unavailable_parent_not_expected_event_count': 13, 'parent_trace_missing_without_attempt_event_count': 0, 'lineage_exact_trusted_count': 34, 'lineage_untrusted_or_stale_event_count': 8, 'lineage_untrusted_or_stale_reason_counts': {'source_stale': 8}, 'lineage_joined_event_count': 34, 'exact_parent_trace_unresolved_event_count': 0, 'lineage_join_coverage_pct': 80.95, 'raw_event_lineage_join_coverage_pct': 6.5, 'lineage_join_coverage_denominator': 'events_with_a_trusted_ai_result_expected; excludes_pre_ai_and_explicit_attempt_result_unavailable', 'linked_budget_pass_trace_count': 21, 'linked_budget_block_trace_count': 2, 'linked_stage_counts': {'blocked_zero_qty': 2, 'budget_pass': 32}, 'runtime_effect': False, 'allowed_runtime_apply': False}`
- latency blockers: `latency_block:latency_state_danger=246`
- latency causal join: `raw_danger_events=246, raw_unique=75, joined_budget_events=246, joined_budget_unique=75, budget_missing_key=0, latency_missing_key=0`
- price guards: `entry_ai_price_canary_skip_order:orderbook_micro indicates bearish state with strong sell pressure and adverse liquidity=1, entry_ai_price_canary_fallback:pre_submit_price_guard=1, entry_ai_price_canary_fallback:skip_low_confidence=1`
- quote refresh: `attempted=86, applied=70, latency_recovered=22, submitted_after_refresh=1`
- quote refresh downstream: `{'budget_pass_no_submit_event': 1, 'entry_ai_authority_revalidation': 20, 'order_bundle_submitted': 1}`

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

- `5m`: ai=0, budget=0, latency=0, submitted=0, top=`-`, swing=`-`, upstream=`-`, ai_terminal=`-`
- `10m`: ai=0, budget=0, latency=0, submitted=0, top=`-`, swing=`-`, upstream=`-`, ai_terminal=`-`
- `30m`: ai=0, budget=0, latency=0, submitted=0, top=`-`, swing=`-`, upstream=`-`, ai_terminal=`-`
