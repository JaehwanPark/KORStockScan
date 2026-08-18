# BUY Funnel Sentinel 2026-08-18

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

- as_of: `2026-08-18T11:00:04`
- baseline_date: `2026-08-14`
- ai_confirmed unique: `61`
- budget_pass unique: `86`
- latency_pass unique: `28`
- submitted unique: `2`
- holding_started unique: `2`
- budget/ai unique: `141.0%` (baseline `88.6`)
- submitted/ai unique: `3.3%` (baseline `0.0`)
- economic bundles: `observed=2, valid=2, probe_only=2, partial_residual=0, full=0`
- economic submitted/requested: `qty=2/271 (0.7%), notional=129837/1000344 (13.0%)`
- economic participation by venue: `{'KRX': {'bundle_count': 2, 'probe_only_bundle_count': 2, 'partial_residual_bundle_count': 0, 'full_submitted_bundle_count': 0, 'requested_qty': 271, 'submitted_qty': 2, 'requested_notional_krw': 1000344, 'submitted_notional_krw': 129837, 'submitted_qty_to_requested_qty_pct': 0.7, 'submitted_notional_to_requested_notional_pct': 13.0}}`
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:below_window_buy_value=241, blocked_strength_momentum:insufficient_history=207, latency_block:latency_state_danger=198, blocked_overbought:-=162, blocked_liquidity:-=83`
- swing blockers: `-`
- upstream blockers: `blocked_ai_score:ai_score_50_buy_hold_override=52, first_ai_wait:-=40, blocked_ai_score:score_11.0=14, blocked_ai_score:score_19.0=9, blocked_ai_score:score_13.0=5`
- AI terminal reasons: `ai_terminal:entry_policy_no_buy_score_prior=59, ai_terminal:first_ai_wait_big_bite_not_confirmed=40`
- AI actions: `events={'DROP': 85, 'NOT_EVALUATED': 1, 'WAIT': 58}, unique={'DROP': 85, 'NOT_EVALUATED': 1, 'WAIT': 58}`
- budget/AI lineage: `{'status': 'explicit_ai_trace_budget_pass_only', 'pipeline_stage_order_contract': 'latest_watching_ai_to_budget_precheck_to_final_authority_revalidation', 'raw_ai_budget_census_is_causal': False, 'ai_trace_count': 154, 'ai_trace_source_stage_counts': {'ai_confirmed': 144, 'early_accel_strong_bundle_recheck_failed': 10}, 'budget_or_block_event_count': 294, 'lineage_contract_event_count': 294, 'lineage_contract_coverage_pct': 100.0, 'pre_ai_parent_not_expected_event_count': 243, 'lineage_join_eligible_event_count': 41, 'lineage_contract_missing_event_count': 0, 'lineage_field_present_count': 41, 'parent_trace_missing_when_expected_event_count': 0, 'parent_attempt_without_trusted_result_event_count': 10, 'ai_attempt_result_unavailable_parent_not_expected_event_count': 10, 'parent_trace_missing_without_attempt_event_count': 0, 'lineage_exact_trusted_count': 39, 'lineage_untrusted_or_stale_event_count': 2, 'lineage_untrusted_or_stale_reason_counts': {'source_stale': 2}, 'lineage_joined_event_count': 39, 'exact_parent_trace_unresolved_event_count': 0, 'lineage_join_coverage_pct': 95.12, 'raw_event_lineage_join_coverage_pct': 13.27, 'lineage_join_coverage_denominator': 'events_with_a_trusted_ai_result_expected; excludes_pre_ai_and_explicit_attempt_result_unavailable', 'linked_budget_pass_trace_count': 17, 'linked_budget_block_trace_count': 0, 'linked_stage_counts': {'budget_pass': 39}, 'runtime_effect': False, 'allowed_runtime_apply': False}`
- latency blockers: `latency_block:latency_state_danger=198, latency_block:tp1_direct_recheck_positive_micro_not_recovered=1`
- price guards: `entry_ai_price_canary_fallback:skip_low_confidence=1`
- quote refresh: `attempted=79, applied=35, latency_recovered=9, submitted_after_refresh=2`
- quote refresh downstream: `{'budget_pass_no_submit_event': 1, 'entry_ai_authority_revalidation': 6, 'order_bundle_submitted': 2}`

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

- `5m`: ai=8, budget=2, latency=2, submitted=0, top=`latency_block:latency_state_danger=11, blocked_overbought:-=7, blocked_strength_momentum:below_window_buy_value=7`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=3, blocked_ai_score:score_17.0=1, blocked_ai_score:score_27.0=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=3`
- `10m`: ai=9, budget=2, latency=2, submitted=0, top=`blocked_strength_momentum:insufficient_history=16, blocked_overbought:-=16, blocked_strength_momentum:below_window_buy_value=13`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=4, blocked_ai_score:score_17.0=2, blocked_ai_score:score_11.0=2`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=7`
- `30m`: ai=21, budget=19, latency=7, submitted=0, top=`blocked_strength_momentum:below_window_buy_value=84, latency_block:latency_state_danger=73, blocked_strength_momentum:insufficient_history=63`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=12, blocked_ai_score:score_11.0=6, first_ai_wait:-=4`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=18, ai_terminal:first_ai_wait_big_bite_not_confirmed=4`
