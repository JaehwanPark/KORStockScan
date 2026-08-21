# BUY Funnel Sentinel 2026-08-21

## 판정

- primary: `UPSTREAM_AI_THRESHOLD`
- secondary: `ENTRY_AI_AUTHORITY_DROUGHT, LATENCY_DROUGHT`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `false`
- followup_route: `score65_74_counterfactual_review`
- followup_owner: `postclose_threshold_cycle`
- runtime_effect: `report_only_no_mutation`
- submit_contract_downstream: `code_improvement_workorder, lifecycle_decision_matrix.submit_bucket_attribution, threshold_cycle_ev_report, runtime_approval_summary, postclose_verifier`
- submit_contract_weak_matches: `ECONOMIC_PARTICIPATION, ENTRY_AI_AUTHORITY_REVALIDATION, LATENCY_PRE_SUBMIT, UPSTREAM_GATE`

## 근거

- as_of: `2026-08-21T15:20:05`
- baseline_date: `2026-08-20`
- ai_confirmed unique: `78`
- budget_pass unique: `135`
- latency_pass unique: `47`
- submitted unique: `18`
- holding_started unique: `13`
- budget/ai unique: `173.1%` (baseline `131.7`)
- submitted/ai unique: `23.1%` (baseline `13.9`)
- economic bundles: `observed=11, valid=11, probe_only=11, partial_residual=0, full=0`
- economic submitted/requested: `qty=11/199 (5.5%), notional=147140/2577840 (5.7%)`
- economic participation by venue: `{'KRX': {'bundle_count': 11, 'probe_only_bundle_count': 11, 'partial_residual_bundle_count': 0, 'full_submitted_bundle_count': 0, 'requested_qty': 199, 'submitted_qty': 11, 'requested_notional_krw': 2577840, 'submitted_notional_krw': 147140, 'submitted_qty_to_requested_qty_pct': 5.5, 'submitted_notional_to_requested_notional_pct': 5.7}}`
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `latency_block:latency_state_danger=536, blocked_overbought:-=390, blocked_strength_momentum:below_strength_base=319, blocked_strength_momentum:insufficient_history=254, blocked_strength_momentum:below_window_buy_value=235`
- swing blockers: `-`
- upstream blockers: `blocked_ai_score:ai_score_50_buy_hold_override=150, first_ai_wait:-=48, wait65_79_ev_candidate:score_70.0=30, blocked_ai_score:score_70.0=14, blocked_ai_score:score_4.0=12`
- AI terminal reasons: `ai_terminal:entry_policy_no_buy_score_prior=62, ai_terminal:first_ai_wait_big_bite_not_confirmed=48`
- AI actions: `events={'DROP': 116, 'NOT_EVALUATED': 5, 'WAIT': 131}, unique={'DROP': 116, 'NOT_EVALUATED': 5, 'WAIT': 131}`
- budget/AI lineage: `{'status': 'explicit_ai_trace_budget_block_observed', 'pipeline_stage_order_contract': 'latest_watching_ai_to_budget_precheck_to_final_authority_revalidation', 'raw_ai_budget_census_is_causal': False, 'ai_trace_count': 294, 'ai_trace_source_stage_counts': {'ai_confirmed': 252, 'early_accel_strong_bundle_recheck_corrected': 16, 'early_accel_strong_bundle_recheck_failed': 26}, 'budget_or_block_event_count': 837, 'lineage_contract_event_count': 837, 'lineage_contract_coverage_pct': 100.0, 'pre_ai_parent_not_expected_event_count': 619, 'lineage_join_eligible_event_count': 206, 'lineage_contract_missing_event_count': 0, 'lineage_field_present_count': 206, 'parent_trace_missing_when_expected_event_count': 0, 'parent_attempt_without_trusted_result_event_count': 12, 'ai_attempt_result_unavailable_parent_not_expected_event_count': 12, 'parent_trace_missing_without_attempt_event_count': 0, 'lineage_exact_trusted_count': 66, 'lineage_untrusted_or_stale_event_count': 140, 'lineage_untrusted_or_stale_reason_counts': {'source_stale': 138, 'trace_id_mismatch': 2}, 'lineage_joined_event_count': 66, 'exact_parent_trace_unresolved_event_count': 0, 'lineage_join_coverage_pct': 32.04, 'raw_event_lineage_join_coverage_pct': 7.89, 'lineage_join_coverage_denominator': 'events_with_a_trusted_ai_result_expected; excludes_pre_ai_and_explicit_attempt_result_unavailable', 'linked_budget_pass_trace_count': 31, 'linked_budget_block_trace_count': 1, 'linked_stage_counts': {'blocked_zero_qty': 1, 'budget_pass': 65}, 'runtime_effect': False, 'allowed_runtime_apply': False}`
- latency blockers: `latency_block:latency_state_danger=536, latency_block:tp1_direct_recheck_expired=15`
- price guards: `entry_ai_price_canary_fallback:pre_submit_price_guard=2, entry_ai_price_canary_fallback:above_best_ask=1, entry_ai_price_canary_fallback:skip_low_confidence=1, entry_ai_price_canary_skip_order:orderbook_micro is ready and micro_state is bearish, indicating unfavorable entry conditions=1, entry_ai_price_canary_skip_order:orderbook micro state is bearish with strong negative OFI and wide spread=1`
- quote refresh: `attempted=122, applied=74, latency_recovered=25, submitted_after_refresh=6`
- quote refresh downstream: `{'budget_pass_no_submit_event': 3, 'entry_ai_authority_revalidation': 16, 'order_bundle_submitted': 6}`

## 금지된 자동변경

- `score_threshold_relaxation`
- `spread_cap_relaxation`
- `fallback_reenable`
- `live_threshold_runtime_mutation`
- `bot_restart`

## 권고 액션

- Append score50/wait65_74 missed-winner and avoided-loser cohorts to report-only review.
- Do not relax score threshold or revive fallback without a new single-axis workorder.

## Window Summary

- `5m`: ai=0, budget=3, latency=0, submitted=0, top=`latency_block:latency_state_danger=5, blocked_overbought:-=4, blocked_strength_momentum:below_window_buy_value=3`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=1`, ai_terminal=`-`
- `10m`: ai=3, budget=6, latency=1, submitted=1, top=`latency_block:latency_state_danger=9, blocked_strength_momentum:below_window_buy_value=8, blocked_overbought:-=4`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=3, first_ai_wait:-=1`, ai_terminal=`ai_terminal:first_ai_wait_big_bite_not_confirmed=1`
- `30m`: ai=9, budget=21, latency=2, submitted=1, top=`latency_block:latency_state_danger=38, blocked_overbought:-=37, blocked_strength_momentum:below_strength_base=34`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=9, first_ai_wait:-=5, wait65_79_ev_candidate:score_70.0=3`, ai_terminal=`ai_terminal:first_ai_wait_big_bite_not_confirmed=5, ai_terminal:entry_policy_no_buy_score_prior=3`
