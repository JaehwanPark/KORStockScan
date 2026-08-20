# BUY Funnel Sentinel 2026-08-20

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

- as_of: `2026-08-20T15:20:04`
- baseline_date: `2026-08-19`
- ai_confirmed unique: `101`
- budget_pass unique: `133`
- latency_pass unique: `47`
- submitted unique: `14`
- holding_started unique: `12`
- budget/ai unique: `131.7%` (baseline `112.1`)
- submitted/ai unique: `13.9%` (baseline `13.2`)
- economic bundles: `observed=9, valid=9, probe_only=9, partial_residual=0, full=0`
- economic submitted/requested: `qty=9/255 (3.5%), notional=109048/1089192 (10.0%)`
- economic participation by venue: `{'KRX': {'bundle_count': 9, 'probe_only_bundle_count': 9, 'partial_residual_bundle_count': 0, 'full_submitted_bundle_count': 0, 'requested_qty': 255, 'submitted_qty': 9, 'requested_notional_krw': 1089192, 'submitted_notional_krw': 109048, 'submitted_qty_to_requested_qty_pct': 3.5, 'submitted_notional_to_requested_notional_pct': 10.0}}`
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:below_window_buy_value=571, blocked_strength_momentum:insufficient_history=554, latency_block:latency_state_danger=376, blocked_overbought:-=315, blocked_strength_momentum:below_strength_base=188`
- swing blockers: `-`
- upstream blockers: `blocked_ai_score:ai_score_50_buy_hold_override=169, wait65_79_ev_candidate:score_70.0=49, blocked_ai_score:score_4.0=38, blocked_ai_score:score_70.0=37, first_ai_wait:-=27`
- AI terminal reasons: `ai_terminal:entry_policy_no_buy_score_prior=163, ai_terminal:first_ai_wait_big_bite_not_confirmed=27`
- AI actions: `events={'DROP': 174, 'NOT_EVALUATED': 1, 'WAIT': 152}, unique={'DROP': 174, 'NOT_EVALUATED': 1, 'WAIT': 152}`
- budget/AI lineage: `{'status': 'explicit_ai_trace_budget_block_observed', 'pipeline_stage_order_contract': 'latest_watching_ai_to_budget_precheck_to_final_authority_revalidation', 'raw_ai_budget_census_is_causal': False, 'ai_trace_count': 362, 'ai_trace_source_stage_counts': {'ai_confirmed': 327, 'early_accel_strong_bundle_recheck_corrected': 11, 'early_accel_strong_bundle_recheck_failed': 24}, 'budget_or_block_event_count': 624, 'lineage_contract_event_count': 624, 'lineage_contract_coverage_pct': 100.0, 'pre_ai_parent_not_expected_event_count': 582, 'lineage_join_eligible_event_count': 33, 'lineage_contract_missing_event_count': 0, 'lineage_field_present_count': 33, 'parent_trace_missing_when_expected_event_count': 0, 'parent_attempt_without_trusted_result_event_count': 9, 'ai_attempt_result_unavailable_parent_not_expected_event_count': 9, 'parent_trace_missing_without_attempt_event_count': 0, 'lineage_exact_trusted_count': 26, 'lineage_untrusted_or_stale_event_count': 7, 'lineage_untrusted_or_stale_reason_counts': {'source_stale': 5, 'trace_id_mismatch_and_source_stale': 2}, 'lineage_joined_event_count': 26, 'exact_parent_trace_unresolved_event_count': 0, 'lineage_join_coverage_pct': 78.79, 'raw_event_lineage_join_coverage_pct': 4.17, 'lineage_join_coverage_denominator': 'events_with_a_trusted_ai_result_expected; excludes_pre_ai_and_explicit_attempt_result_unavailable', 'linked_budget_pass_trace_count': 21, 'linked_budget_block_trace_count': 1, 'linked_stage_counts': {'blocked_zero_qty': 1, 'budget_pass': 25}, 'runtime_effect': False, 'allowed_runtime_apply': False}`
- latency blockers: `latency_block:latency_state_danger=376, latency_block:tp1_direct_recheck_expired=2`
- price guards: `entry_ai_price_canary_fallback:pre_submit_price_guard=2, entry_ai_price_canary_fallback:skip_low_confidence=1, entry_ai_price_canary_skip_order:orderbook_micro is ready and micro_state is bearish, indicating unfavorable fill probability=1`
- quote refresh: `attempted=121, applied=71, latency_recovered=16, submitted_after_refresh=2`
- quote refresh downstream: `{'budget_pass_no_submit_event': 4, 'entry_ai_authority_revalidation': 9, 'no_downstream_event': 1, 'order_bundle_submitted': 2}`

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

- `5m`: ai=2, budget=3, latency=0, submitted=0, top=`blocked_overbought:-=7, blocked_strength_momentum:below_window_buy_value=6, blocked_vpw:-=5`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=4, blocked_ai_score:score_0.0=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=1`
- `10m`: ai=5, budget=4, latency=1, submitted=0, top=`blocked_overbought:-=18, blocked_strength_momentum:insufficient_history=9, blocked_vpw:-=8`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=7, blocked_ai_score:score_6.0=1, blocked_ai_score:score_0.0=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=2`
- `30m`: ai=12, budget=10, latency=3, submitted=0, top=`blocked_overbought:-=48, blocked_strength_momentum:below_strength_base=24, blocked_strength_momentum:insufficient_history=22`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=11, blocked_ai_score:score_4.0=4, blocked_ai_score:score_0.0=2`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=9`
