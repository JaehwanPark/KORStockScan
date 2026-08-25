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

- as_of: `2026-08-25T12:00:03`
- baseline_date: `2026-08-24`
- ai_confirmed unique: `62`
- budget_pass unique: `59`
- latency_pass unique: `30`
- submitted unique: `7`
- holding_started unique: `5`
- budget/ai unique: `95.2%` (baseline `88.2`)
- submitted/ai unique: `11.3%` (baseline `5.9`)
- economic bundles: `observed=7, valid=7, probe_only=7, partial_residual=0, full=0`
- economic submitted/requested: `qty=7/7 (100.0%), notional=965310/965310 (100.0%)`
- economic participation by venue: `{'KRX': {'bundle_count': 7, 'probe_only_bundle_count': 7, 'partial_residual_bundle_count': 0, 'full_submitted_bundle_count': 0, 'requested_qty': 7, 'submitted_qty': 7, 'requested_notional_krw': 965310, 'submitted_notional_krw': 965310, 'submitted_qty_to_requested_qty_pct': 100.0, 'submitted_notional_to_requested_notional_pct': 100.0}}`
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `latency_block:latency_state_danger=231, blocked_strength_momentum:below_window_buy_value=221, blocked_strength_momentum:below_strength_base=92, blocked_liquidity:-=82, blocked_overbought:-=81`
- swing blockers: `-`
- upstream blockers: `blocked_ai_score:ai_score_50_buy_hold_override=75, first_ai_wait:-=24, wait65_79_ev_candidate:score_70.0=23, blocked_ai_score:score_70.0=12, blocked_ai_score:score_0.0=10`
- AI terminal reasons: `ai_terminal:entry_policy_no_buy_score_prior=55, ai_terminal:first_ai_wait_big_bite_not_confirmed=24`
- AI actions: `events={'DROP': 89, 'NOT_EVALUATED': 1, 'WAIT': 85}, unique={'DROP': 89, 'NOT_EVALUATED': 1, 'WAIT': 85}`
- budget/AI lineage: `{'status': 'explicit_ai_trace_budget_block_observed', 'pipeline_stage_order_contract': 'latest_watching_ai_to_budget_precheck_to_final_authority_revalidation', 'raw_ai_budget_census_is_causal': False, 'ai_trace_count': 196, 'ai_trace_source_stage_counts': {'ai_confirmed': 175, 'early_accel_strong_bundle_recheck_corrected': 5, 'early_accel_strong_bundle_recheck_failed': 16}, 'budget_or_block_event_count': 426, 'lineage_contract_event_count': 426, 'lineage_contract_coverage_pct': 100.0, 'pre_ai_parent_not_expected_event_count': 400, 'lineage_join_eligible_event_count': 18, 'lineage_contract_missing_event_count': 0, 'lineage_field_present_count': 18, 'parent_trace_missing_when_expected_event_count': 0, 'parent_attempt_without_trusted_result_event_count': 8, 'ai_attempt_result_unavailable_parent_not_expected_event_count': 8, 'parent_trace_missing_without_attempt_event_count': 0, 'lineage_exact_trusted_count': 15, 'lineage_untrusted_or_stale_event_count': 3, 'lineage_untrusted_or_stale_reason_counts': {'source_stale': 3}, 'lineage_joined_event_count': 15, 'exact_parent_trace_unresolved_event_count': 0, 'lineage_join_coverage_pct': 83.33, 'raw_event_lineage_join_coverage_pct': 3.52, 'lineage_join_coverage_denominator': 'events_with_a_trusted_ai_result_expected; excludes_pre_ai_and_explicit_attempt_result_unavailable', 'linked_budget_pass_trace_count': 12, 'linked_budget_block_trace_count': 1, 'linked_stage_counts': {'blocked_zero_qty': 1, 'budget_pass': 14}, 'runtime_effect': False, 'allowed_runtime_apply': False}`
- latency blockers: `latency_block:latency_state_danger=231, latency_block:tp1_direct_recheck_expired=2`
- price guards: `entry_ai_price_canary_fallback:skip_low_confidence=2, entry_ai_price_canary_skip_order:orderbook_micro indicates bearish state with negative OFI and adverse regime=1`
- quote refresh: `attempted=57, applied=52, latency_recovered=24, submitted_after_refresh=3`
- quote refresh downstream: `{'budget_pass_no_submit_event': 4, 'entry_ai_authority_revalidation': 16, 'order_bundle_submitted': 3, 'upstream_block_after_latency_recovery': 1}`

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

- `5m`: ai=3, budget=1, latency=0, submitted=0, top=`blocked_strength_momentum:below_window_buy_value=6, blocked_strength_momentum:insufficient_history=4, blocked_ai_score:score_7.0=2`, swing=`-`, upstream=`blocked_ai_score:score_7.0=2, blocked_ai_score:score_0.0=1, wait65_79_ev_candidate:score_70.0=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=4`
- `10m`: ai=7, budget=1, latency=0, submitted=0, top=`blocked_strength_momentum:below_window_buy_value=10, blocked_strength_momentum:insufficient_history=5, blocked_liquidity:-=4`, swing=`-`, upstream=`blocked_ai_score:score_0.0=3, blocked_ai_score:score_7.0=2, blocked_ai_score:score_11.0=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=8`
- `30m`: ai=19, budget=18, latency=4, submitted=0, top=`blocked_strength_momentum:below_window_buy_value=63, blocked_overbought:-=28, blocked_strength_momentum:below_strength_base=22`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=8, blocked_ai_score:score_0.0=5, wait65_79_ev_candidate:score_70.0=4`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=17, ai_terminal:first_ai_wait_big_bite_not_confirmed=3`
