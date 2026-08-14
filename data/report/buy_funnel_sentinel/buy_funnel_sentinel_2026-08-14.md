# BUY Funnel Sentinel 2026-08-14

## 판정

- primary: `SUBMIT_DROUGHT_CRITICAL`
- secondary: `PRICE_GUARD_DROUGHT, ENTRY_AI_AUTHORITY_DROUGHT, LATENCY_DROUGHT, UPSTREAM_AI_THRESHOLD`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `false`
- followup_route: `entry_submit_drought_auto_workorder`
- followup_owner: `postclose_threshold_cycle_and_lifecycle_decision_matrix`
- runtime_effect: `auto_workorder_no_intraday_mutation`
- submit_contract_downstream: `code_improvement_workorder, lifecycle_decision_matrix.submit_bucket_attribution, threshold_cycle_ev_report, runtime_approval_summary, postclose_verifier`
- submit_contract_weak_matches: `BROKER_RECEIPT, BUDGET_PASS_COLLAPSE, ECONOMIC_PARTICIPATION, ENTRY_AI_AUTHORITY_REVALIDATION, FILL_QUALITY, LATENCY_PRE_SUBMIT, PRICE_REVALIDATION, SIM_REAL_AUTHORITY, TELEGRAM_POST_SUBMIT_ONLY, UPSTREAM_GATE`

## 근거

- as_of: `2026-08-14T15:20:03`
- baseline_date: `2026-08-13`
- ai_confirmed unique: `82`
- budget_pass unique: `128`
- latency_pass unique: `41`
- submitted unique: `10`
- holding_started unique: `6`
- budget/ai unique: `156.1%` (baseline `95.0`)
- submitted/ai unique: `12.2%` (baseline `6.2`)
- economic bundles: `observed=1, valid=1, probe_only=1, partial_residual=0, full=0`
- economic submitted/requested: `qty=1/3 (33.3%), notional=10350/30960 (33.4%)`
- economic participation by venue: `{'KRX': {'bundle_count': 1, 'probe_only_bundle_count': 1, 'partial_residual_bundle_count': 0, 'full_submitted_bundle_count': 0, 'requested_qty': 3, 'submitted_qty': 1, 'requested_notional_krw': 30960, 'submitted_notional_krw': 10350, 'submitted_qty_to_requested_qty_pct': 33.3, 'submitted_notional_to_requested_notional_pct': 33.4}}`
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:below_window_buy_value=554, blocked_strength_momentum:insufficient_history=466, blocked_overbought:-=401, latency_block:latency_state_danger=266, blocked_strength_momentum:below_strength_base=236`
- swing blockers: `-`
- upstream blockers: `blocked_ai_score:ai_score_50_buy_hold_override=119, wait65_79_ev_candidate:score_70.0=49, first_ai_wait:-=48, blocked_ai_score:score_70.0=33, blocked_ai_score:score_4.0=33`
- AI terminal reasons: `ai_terminal:entry_policy_no_buy_score_prior=117, ai_terminal:first_ai_wait_big_bite_not_confirmed=48`
- AI actions: `events={'DROP': 181, 'NOT_EVALUATED': 1, 'WAIT': 132}, unique={'DROP': 181, 'NOT_EVALUATED': 1, 'WAIT': 132}`
- budget/AI lineage: `{'status': 'explicit_ai_trace_budget_block_observed', 'pipeline_stage_order_contract': 'latest_watching_ai_to_budget_precheck_to_final_authority_revalidation', 'raw_ai_budget_census_is_causal': False, 'ai_trace_count': 344, 'ai_trace_source_stage_counts': {'ai_confirmed': 314, 'early_accel_strong_bundle_recheck_corrected': 16, 'early_accel_strong_bundle_recheck_failed': 14}, 'budget_or_block_event_count': 680, 'lineage_contract_event_count': 680, 'lineage_contract_coverage_pct': 100.0, 'pre_ai_parent_not_expected_event_count': 587, 'lineage_join_eligible_event_count': 42, 'lineage_contract_missing_event_count': 0, 'lineage_field_present_count': 42, 'parent_trace_missing_when_expected_event_count': 0, 'parent_attempt_without_trusted_result_event_count': 51, 'ai_attempt_result_unavailable_parent_not_expected_event_count': 51, 'parent_trace_missing_without_attempt_event_count': 0, 'lineage_exact_trusted_count': 39, 'lineage_untrusted_or_stale_event_count': 3, 'lineage_untrusted_or_stale_reason_counts': {'attempt_untrusted': 1, 'source_stale': 1, 'trace_id_mismatch': 1}, 'lineage_joined_event_count': 39, 'exact_parent_trace_unresolved_event_count': 0, 'lineage_join_coverage_pct': 92.86, 'raw_event_lineage_join_coverage_pct': 5.74, 'lineage_join_coverage_denominator': 'events_with_a_trusted_ai_result_expected; excludes_pre_ai_and_explicit_attempt_result_unavailable', 'linked_budget_pass_trace_count': 28, 'linked_budget_block_trace_count': 3, 'linked_stage_counts': {'blocked_zero_qty': 3, 'budget_pass': 36}, 'runtime_effect': False, 'allowed_runtime_apply': False}`
- latency blockers: `latency_block:latency_state_danger=266, latency_block:tp1_direct_recheck_positive_micro_not_recovered=1`
- price guards: `entry_ai_price_canary_fallback:low_confidence=146, entry_ai_price_canary_fallback:pre_submit_price_guard=2`
- quote refresh: `attempted=115, applied=49, latency_recovered=14, submitted_after_refresh=0`
- quote refresh downstream: `{'armed_expired_before_submit': 2, 'entry_ai_authority_revalidation': 12}`

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

- `5m`: ai=2, budget=5, latency=1, submitted=0, top=`blocked_strength_momentum:below_strength_base=6, latency_block:latency_state_danger=4, blocked_vpw:-=4`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=4, first_ai_wait:-=1`, ai_terminal=`ai_terminal:first_ai_wait_big_bite_not_confirmed=1`
- `10m`: ai=8, budget=10, latency=5, submitted=2, top=`blocked_overbought:-=13, blocked_strength_momentum:below_strength_base=10, blocked_vpw:-=7`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=5, first_ai_wait:-=3, wait65_79_ev_candidate:score_70.0=1`, ai_terminal=`ai_terminal:first_ai_wait_big_bite_not_confirmed=3, ai_terminal:entry_policy_no_buy_score_prior=2`
- `30m`: ai=16, budget=26, latency=7, submitted=2, top=`blocked_overbought:-=42, blocked_strength_momentum:below_strength_base=26, latency_block:latency_state_danger=25`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=9, first_ai_wait:-=5, wait65_79_ev_candidate:score_70.0=3`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=5, ai_terminal:first_ai_wait_big_bite_not_confirmed=5`
