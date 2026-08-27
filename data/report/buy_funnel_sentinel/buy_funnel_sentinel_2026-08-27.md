# BUY Funnel Sentinel 2026-08-27

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

- as_of: `2026-08-27T15:20:04`
- baseline_date: `2026-08-26`
- ai_confirmed unique: `87`
- budget_pass unique: `114`
- latency_pass unique: `44`
- submitted unique: `4`
- holding_started unique: `2`
- budget/ai unique: `131.0%` (baseline `141.9`)
- submitted/ai unique: `4.6%` (baseline `0.0`)
- economic bundles: `observed=5, valid=5, probe_only=5, partial_residual=0, full=0`
- economic submitted/requested: `qty=5/16 (31.2%), notional=242960/438650 (55.4%)`
- economic participation by venue: `{'KRX': {'bundle_count': 5, 'probe_only_bundle_count': 5, 'partial_residual_bundle_count': 0, 'full_submitted_bundle_count': 0, 'requested_qty': 16, 'submitted_qty': 5, 'requested_notional_krw': 438650, 'submitted_notional_krw': 242960, 'submitted_qty_to_requested_qty_pct': 31.2, 'submitted_notional_to_requested_notional_pct': 55.4}}`
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `latency_block:latency_state_danger=477, blocked_strength_momentum:below_window_buy_value=356, blocked_overbought:-=338, blocked_strength_momentum:below_strength_base=213, blocked_strength_momentum:insufficient_history=212`
- swing blockers: `-`
- upstream blockers: `blocked_ai_score:ai_score_50_buy_hold_override=94, first_ai_wait:-=48, blocked_ai_score:score_0.0=21, blocked_ai_score:score_64.0=18, wait65_79_ev_candidate:score_70.0=14`
- AI terminal reasons: `ai_terminal:entry_policy_no_buy_score_prior=121, ai_terminal:first_ai_wait_big_bite_not_confirmed=48`
- AI actions: `events={'DROP': 180, 'NOT_EVALUATED': 2, 'WAIT': 97}, unique={'DROP': 180, 'NOT_EVALUATED': 2, 'WAIT': 97}`
- budget/AI lineage: `{'status': 'explicit_ai_trace_budget_block_observed', 'pipeline_stage_order_contract': 'latest_watching_ai_to_budget_precheck_to_final_authority_revalidation', 'raw_ai_budget_census_is_causal': False, 'ai_trace_count': 298, 'ai_trace_source_stage_counts': {'ai_confirmed': 279, 'early_accel_strong_bundle_recheck_corrected': 2, 'early_accel_strong_bundle_recheck_failed': 17}, 'budget_or_block_event_count': 835, 'lineage_contract_event_count': 835, 'lineage_contract_coverage_pct': 100.0, 'pre_ai_parent_not_expected_event_count': 764, 'lineage_join_eligible_event_count': 36, 'lineage_contract_missing_event_count': 0, 'lineage_field_present_count': 36, 'parent_trace_missing_when_expected_event_count': 0, 'parent_attempt_without_trusted_result_event_count': 35, 'ai_attempt_result_unavailable_parent_not_expected_event_count': 35, 'parent_trace_missing_without_attempt_event_count': 0, 'lineage_exact_trusted_count': 33, 'lineage_untrusted_or_stale_event_count': 3, 'lineage_untrusted_or_stale_reason_counts': {'source_stale': 3}, 'lineage_joined_event_count': 33, 'exact_parent_trace_unresolved_event_count': 0, 'lineage_join_coverage_pct': 91.67, 'raw_event_lineage_join_coverage_pct': 3.95, 'lineage_join_coverage_denominator': 'events_with_a_trusted_ai_result_expected; excludes_pre_ai_and_explicit_attempt_result_unavailable', 'linked_budget_pass_trace_count': 26, 'linked_budget_block_trace_count': 1, 'linked_stage_counts': {'blocked_zero_qty': 1, 'budget_pass': 32}, 'runtime_effect': False, 'allowed_runtime_apply': False}`
- latency blockers: `latency_block:latency_state_danger=477, latency_block:tp1_direct_recheck_expired=5`
- price guards: `entry_ai_price_canary_fallback:skip_low_confidence=4`
- quote refresh: `attempted=106, applied=77, latency_recovered=27, submitted_after_refresh=0`
- quote refresh downstream: `{'entry_ai_authority_revalidation': 27}`

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

- `5m`: ai=4, budget=1, latency=1, submitted=0, top=`blocked_strength_momentum:below_window_buy_value=11, blocked_overbought:-=5, blocked_liquidity:-=4`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=3, blocked_ai_score:score_14.0=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=1`
- `10m`: ai=6, budget=3, latency=1, submitted=0, top=`blocked_strength_momentum:below_window_buy_value=16, blocked_overbought:-=13, blocked_liquidity:-=7`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=4, blocked_ai_score:score_13.0=1, blocked_ai_score:score_11.0=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=3`
- `30m`: ai=18, budget=12, latency=7, submitted=0, top=`blocked_strength_momentum:below_window_buy_value=31, blocked_overbought:-=29, blocked_liquidity:-=18`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=13, blocked_ai_score:score_18.0=4, blocked_ai_score:score_11.0=3`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=13`
