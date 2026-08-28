# BUY Funnel Sentinel 2026-08-28

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

- as_of: `2026-08-28T15:20:04`
- baseline_date: `2026-08-27`
- ai_confirmed unique: `77`
- budget_pass unique: `79`
- latency_pass unique: `37`
- submitted unique: `5`
- holding_started unique: `3`
- budget/ai unique: `102.6%` (baseline `131.0`)
- submitted/ai unique: `6.5%` (baseline `4.6`)
- economic bundles: `observed=5, valid=5, probe_only=5, partial_residual=0, full=0`
- economic submitted/requested: `qty=5/5 (100.0%), notional=346680/346680 (100.0%)`
- economic participation by venue: `{'KRX': {'bundle_count': 5, 'probe_only_bundle_count': 5, 'partial_residual_bundle_count': 0, 'full_submitted_bundle_count': 0, 'requested_qty': 5, 'submitted_qty': 5, 'requested_notional_krw': 346680, 'submitted_notional_krw': 346680, 'submitted_qty_to_requested_qty_pct': 100.0, 'submitted_notional_to_requested_notional_pct': 100.0}}`
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:below_window_buy_value=395, latency_block:latency_state_danger=274, blocked_overbought:-=243, blocked_strength_momentum:insufficient_history=237, blocked_strength_momentum:below_strength_base=153`
- swing blockers: `-`
- upstream blockers: `blocked_ai_score:ai_score_50_buy_hold_override=100, first_ai_wait:-=43, blocked_ai_score:score_0.0=27, wait65_79_ev_candidate:score_70.0=21, blocked_ai_score:score_4.0=14`
- AI terminal reasons: `ai_terminal:entry_policy_no_buy_score_prior=105, ai_terminal:first_ai_wait_big_bite_not_confirmed=43`
- AI actions: `events={'DROP': 166, 'NOT_EVALUATED': 1, 'WAIT': 106}, unique={'DROP': 166, 'NOT_EVALUATED': 1, 'WAIT': 106}`
- budget/AI lineage: `{'status': 'explicit_ai_trace_budget_pass_only', 'pipeline_stage_order_contract': 'latest_watching_ai_to_budget_precheck_to_final_authority_revalidation', 'raw_ai_budget_census_is_causal': False, 'ai_trace_count': 295, 'ai_trace_source_stage_counts': {'ai_confirmed': 273, 'early_accel_strong_bundle_recheck_corrected': 9, 'early_accel_strong_bundle_recheck_failed': 13}, 'budget_or_block_event_count': 673, 'lineage_contract_event_count': 673, 'lineage_contract_coverage_pct': 100.0, 'pre_ai_parent_not_expected_event_count': 562, 'lineage_join_eligible_event_count': 98, 'lineage_contract_missing_event_count': 0, 'lineage_field_present_count': 98, 'parent_trace_missing_when_expected_event_count': 0, 'parent_attempt_without_trusted_result_event_count': 13, 'ai_attempt_result_unavailable_parent_not_expected_event_count': 13, 'parent_trace_missing_without_attempt_event_count': 0, 'lineage_exact_trusted_count': 75, 'lineage_untrusted_or_stale_event_count': 23, 'lineage_untrusted_or_stale_reason_counts': {'source_stale': 23}, 'lineage_joined_event_count': 75, 'exact_parent_trace_unresolved_event_count': 0, 'lineage_join_coverage_pct': 76.53, 'raw_event_lineage_join_coverage_pct': 11.14, 'lineage_join_coverage_denominator': 'events_with_a_trusted_ai_result_expected; excludes_pre_ai_and_explicit_attempt_result_unavailable', 'linked_budget_pass_trace_count': 30, 'linked_budget_block_trace_count': 0, 'linked_stage_counts': {'budget_pass': 75}, 'runtime_effect': False, 'allowed_runtime_apply': False}`
- latency blockers: `latency_block:latency_state_danger=274, latency_block:tp1_direct_recheck_expired=4`
- latency causal join: `raw_danger_events=278, raw_unique=63, joined_budget_events=278, joined_budget_unique=63, budget_missing_key=0, latency_missing_key=0`
- price guards: `entry_ai_price_canary_fallback:skip_low_confidence=1`
- quote refresh: `attempted=72, applied=59, latency_recovered=29, submitted_after_refresh=1`
- quote refresh downstream: `{'budget_pass_no_submit_event': 5, 'entry_ai_authority_revalidation': 23, 'order_bundle_submitted': 1}`

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

- `5m`: ai=3, budget=5, latency=3, submitted=0, top=`blocked_zero_qty:-=6, blocked_strength_momentum:below_strength_base=3, blocked_overbought:-=2`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=1`, ai_terminal=`-`
- `10m`: ai=6, budget=8, latency=4, submitted=0, top=`blocked_strength_momentum:below_strength_base=8, blocked_zero_qty:-=7, latency_block:latency_state_danger=6`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=2, blocked_ai_score:score_0.0=1, first_ai_wait:-=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=2, ai_terminal:first_ai_wait_big_bite_not_confirmed=1`
- `30m`: ai=17, budget=20, latency=7, submitted=0, top=`blocked_strength_momentum:below_window_buy_value=23, blocked_overbought:-=22, latency_block:latency_state_danger=15`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=8, blocked_ai_score:score_0.0=4, wait65_79_ev_candidate:score_70.0=2`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=7, ai_terminal:first_ai_wait_big_bite_not_confirmed=1`
