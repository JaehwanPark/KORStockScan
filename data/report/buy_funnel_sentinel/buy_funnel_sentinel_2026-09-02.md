# BUY Funnel Sentinel 2026-09-02

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

- as_of: `2026-09-02T11:55:03`
- baseline_date: `2026-09-01`
- ai_confirmed unique: `46`
- budget_pass unique: `81`
- latency_pass unique: `20`
- submitted unique: `2`
- holding_started unique: `1`
- budget/ai unique: `176.1%` (baseline `125.5`)
- submitted/ai unique: `4.3%` (baseline `6.4`)
- economic bundles: `observed=3, valid=3, probe_only=3, partial_residual=0, full=0`
- economic submitted/requested: `qty=3/3 (100.0%), notional=211990/211990 (100.0%)`
- economic participation by venue: `{'KRX': {'bundle_count': 3, 'probe_only_bundle_count': 3, 'partial_residual_bundle_count': 0, 'full_submitted_bundle_count': 0, 'requested_qty': 3, 'submitted_qty': 3, 'requested_notional_krw': 211990, 'submitted_notional_krw': 211990, 'submitted_qty_to_requested_qty_pct': 100.0, 'submitted_notional_to_requested_notional_pct': 100.0}}`
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `latency_block:latency_state_danger=146, blocked_overbought:-=99, blocked_strength_momentum:below_window_buy_value=91, blocked_liquidity:-=68, blocked_strength_momentum:below_strength_base=62`
- swing blockers: `-`
- upstream blockers: `blocked_ai_score:ai_score_50_buy_hold_override=43, first_ai_wait:-=19, blocked_ai_score:score_4.0=9, blocked_ai_score:score_0.0=9, wait65_79_ev_candidate:score_70.0=7`
- AI terminal reasons: `ai_terminal:entry_policy_no_buy_score_prior=35, ai_terminal:first_ai_wait_big_bite_not_confirmed=19`
- AI actions: `events={'DROP': 51, 'WAIT': 57}, unique={'DROP': 51, 'WAIT': 57}`
- budget/AI lineage: `{'status': 'explicit_ai_trace_budget_pass_only', 'pipeline_stage_order_contract': 'latest_watching_ai_to_budget_precheck_to_final_authority_revalidation', 'raw_ai_budget_census_is_causal': False, 'ai_trace_count': 118, 'ai_trace_source_stage_counts': {'ai_confirmed': 108, 'early_accel_strong_bundle_recheck_corrected': 1, 'early_accel_strong_bundle_recheck_failed': 9}, 'budget_or_block_event_count': 294, 'lineage_contract_event_count': 294, 'lineage_contract_coverage_pct': 100.0, 'pre_ai_parent_not_expected_event_count': 266, 'lineage_join_eligible_event_count': 25, 'lineage_contract_missing_event_count': 0, 'lineage_field_present_count': 25, 'parent_trace_missing_when_expected_event_count': 0, 'parent_attempt_without_trusted_result_event_count': 3, 'ai_attempt_result_unavailable_parent_not_expected_event_count': 3, 'parent_trace_missing_without_attempt_event_count': 0, 'lineage_exact_trusted_count': 23, 'lineage_untrusted_or_stale_event_count': 2, 'lineage_untrusted_or_stale_reason_counts': {'source_stale': 1, 'trace_id_mismatch': 1}, 'lineage_joined_event_count': 23, 'exact_parent_trace_unresolved_event_count': 0, 'lineage_join_coverage_pct': 92.0, 'raw_event_lineage_join_coverage_pct': 7.82, 'lineage_join_coverage_denominator': 'events_with_a_trusted_ai_result_expected; excludes_pre_ai_and_explicit_attempt_result_unavailable', 'linked_budget_pass_trace_count': 15, 'linked_budget_block_trace_count': 0, 'linked_stage_counts': {'budget_pass': 23}, 'runtime_effect': False, 'allowed_runtime_apply': False}`
- latency blockers: `latency_block:latency_state_danger=146`
- latency causal join: `raw_danger_events=146, raw_unique=63, joined_budget_events=146, joined_budget_unique=63, budget_missing_key=0, latency_missing_key=0`
- price guards: `-`
- quote refresh: `attempted=70, applied=57, latency_recovered=15, submitted_after_refresh=2`
- quote refresh downstream: `{'budget_pass_no_submit_event': 2, 'entry_ai_authority_revalidation': 11, 'order_bundle_submitted': 2}`

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

- `5m`: ai=1, budget=2, latency=0, submitted=0, top=`blocked_overbought:-=6, blocked_ai_score:ai_score_50_buy_hold_override=3, blocked_liquidity:-=2`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=3`, ai_terminal=`-`
- `10m`: ai=1, budget=4, latency=0, submitted=0, top=`blocked_overbought:-=6, latency_block:latency_state_danger=5, blocked_zero_qty:-=5`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=3`, ai_terminal=`-`
- `30m`: ai=15, budget=23, latency=5, submitted=0, top=`blocked_overbought:-=28, latency_block:latency_state_danger=27, blocked_liquidity:-=14`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=9, wait65_79_ev_candidate:score_70.0=2, blocked_ai_score:score_7.0=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=4, ai_terminal:first_ai_wait_big_bite_not_confirmed=1`
