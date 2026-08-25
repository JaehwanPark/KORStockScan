# BUY Funnel Sentinel 2026-08-25

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

- as_of: `2026-08-25T15:20:04`
- baseline_date: `2026-08-24`
- ai_confirmed unique: `82`
- budget_pass unique: `95`
- latency_pass unique: `49`
- submitted unique: `15`
- holding_started unique: `9`
- budget/ai unique: `115.9%` (baseline `94.1`)
- submitted/ai unique: `18.3%` (baseline `11.8`)
- economic bundles: `observed=15, valid=15, probe_only=15, partial_residual=0, full=0`
- economic submitted/requested: `qty=15/15 (100.0%), notional=1419350/1419350 (100.0%)`
- economic participation by venue: `{'KRX': {'bundle_count': 15, 'probe_only_bundle_count': 15, 'partial_residual_bundle_count': 0, 'full_submitted_bundle_count': 0, 'requested_qty': 15, 'submitted_qty': 15, 'requested_notional_krw': 1419350, 'submitted_notional_krw': 1419350, 'submitted_qty_to_requested_qty_pct': 100.0, 'submitted_notional_to_requested_notional_pct': 100.0}}`
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:below_window_buy_value=417, latency_block:latency_state_danger=368, blocked_overbought:-=284, blocked_strength_momentum:below_strength_base=169, blocked_strength_momentum:insufficient_history=169`
- swing blockers: `-`
- upstream blockers: `blocked_ai_score:ai_score_50_buy_hold_override=132, wait65_79_ev_candidate:score_70.0=48, first_ai_wait:-=32, blocked_ai_score:score_70.0=22, blocked_ai_score:score_4.0=19`
- AI terminal reasons: `ai_terminal:entry_policy_no_buy_score_prior=98, ai_terminal:first_ai_wait_big_bite_not_confirmed=32`
- AI actions: `events={'DROP': 149, 'NOT_EVALUATED': 1, 'WAIT': 158}, unique={'DROP': 149, 'NOT_EVALUATED': 1, 'WAIT': 158}`
- budget/AI lineage: `{'status': 'explicit_ai_trace_budget_block_observed', 'pipeline_stage_order_contract': 'latest_watching_ai_to_budget_precheck_to_final_authority_revalidation', 'raw_ai_budget_census_is_causal': False, 'ai_trace_count': 346, 'ai_trace_source_stage_counts': {'ai_confirmed': 308, 'early_accel_strong_bundle_recheck_corrected': 18, 'early_accel_strong_bundle_recheck_failed': 20}, 'budget_or_block_event_count': 756, 'lineage_contract_event_count': 756, 'lineage_contract_coverage_pct': 100.0, 'pre_ai_parent_not_expected_event_count': 692, 'lineage_join_eligible_event_count': 52, 'lineage_contract_missing_event_count': 0, 'lineage_field_present_count': 52, 'parent_trace_missing_when_expected_event_count': 0, 'parent_attempt_without_trusted_result_event_count': 12, 'ai_attempt_result_unavailable_parent_not_expected_event_count': 12, 'parent_trace_missing_without_attempt_event_count': 0, 'lineage_exact_trusted_count': 48, 'lineage_untrusted_or_stale_event_count': 4, 'lineage_untrusted_or_stale_reason_counts': {'source_stale': 4}, 'lineage_joined_event_count': 48, 'exact_parent_trace_unresolved_event_count': 0, 'lineage_join_coverage_pct': 92.31, 'raw_event_lineage_join_coverage_pct': 6.35, 'lineage_join_coverage_denominator': 'events_with_a_trusted_ai_result_expected; excludes_pre_ai_and_explicit_attempt_result_unavailable', 'linked_budget_pass_trace_count': 37, 'linked_budget_block_trace_count': 4, 'linked_stage_counts': {'blocked_zero_qty': 4, 'budget_pass': 44}, 'runtime_effect': False, 'allowed_runtime_apply': False}`
- latency blockers: `latency_block:latency_state_danger=368, latency_block:tp1_direct_recheck_expired=4`
- price guards: `entry_ai_price_canary_fallback:skip_low_confidence=4, entry_ai_price_canary_skip_order:orderbook_micro indicates bearish state with negative OFI and adverse regime=1, entry_ai_price_canary_fallback:pre_submit_price_guard=1`
- quote refresh: `attempted=89, applied=72, latency_recovered=32, submitted_after_refresh=3`
- quote refresh downstream: `{'budget_pass_no_submit_event': 6, 'entry_ai_authority_revalidation': 22, 'order_bundle_submitted': 3, 'upstream_block_after_latency_recovery': 1}`

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

- `5m`: ai=3, budget=4, latency=1, submitted=0, top=`blocked_overbought:-=9, blocked_vpw:-=4, blocked_strength_momentum:below_window_buy_value=3`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=2, blocked_ai_score:score_6.0=1, blocked_ai_score:score_9.0=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=2`
- `10m`: ai=5, budget=8, latency=3, submitted=1, top=`blocked_overbought:-=14, blocked_strength_momentum:below_window_buy_value=7, latency_block:latency_state_danger=4`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=2, blocked_ai_score:score_6.0=1, blocked_ai_score:score_9.0=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=2`
- `30m`: ai=15, budget=17, latency=8, submitted=1, top=`blocked_overbought:-=37, blocked_strength_momentum:below_window_buy_value=19, latency_block:latency_state_danger=14`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=9, wait65_79_ev_candidate:score_70.0=6, blocked_ai_score:score_70.0=2`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=7`
