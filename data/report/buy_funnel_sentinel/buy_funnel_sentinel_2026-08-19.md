# BUY Funnel Sentinel 2026-08-19

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
- submit_contract_weak_matches: `BROKER_RECEIPT, BUDGET_PASS_COLLAPSE, ENTRY_AI_AUTHORITY_REVALIDATION, FILL_QUALITY, LATENCY_PRE_SUBMIT, SIM_REAL_AUTHORITY, TELEGRAM_POST_SUBMIT_ONLY, UPSTREAM_GATE`

## 근거

- as_of: `2026-08-19T15:20:03`
- baseline_date: `2026-08-18`
- ai_confirmed unique: `91`
- budget_pass unique: `102`
- latency_pass unique: `51`
- submitted unique: `12`
- holding_started unique: `8`
- budget/ai unique: `112.1%` (baseline `150.0`)
- submitted/ai unique: `13.2%` (baseline `2.3`)
- economic bundles: `observed=0, valid=0, probe_only=0, partial_residual=0, full=0`
- economic submitted/requested: `qty=0/0 (0.0%), notional=0/0 (0.0%)`
- economic participation by venue: `{}`
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_overbought:-=362, blocked_strength_momentum:insufficient_history=300, blocked_strength_momentum:below_window_buy_value=259, latency_block:latency_state_danger=231, blocked_strength_momentum:below_strength_base=195`
- swing blockers: `-`
- upstream blockers: `blocked_ai_score:ai_score_50_buy_hold_override=112, wait65_79_ev_candidate:score_70.0=34, blocked_ai_score:score_4.0=23, first_ai_wait:-=17, blocked_ai_score:score_70.0=12`
- AI terminal reasons: `ai_terminal:entry_policy_no_buy_score_prior=66, ai_terminal:first_ai_wait_big_bite_not_confirmed=17`
- AI actions: `events={'DROP': 100, 'NOT_EVALUATED': 3, 'WAIT': 128}, unique={'DROP': 100, 'NOT_EVALUATED': 3, 'WAIT': 128}`
- budget/AI lineage: `{'status': 'explicit_ai_trace_budget_block_observed', 'pipeline_stage_order_contract': 'latest_watching_ai_to_budget_precheck_to_final_authority_revalidation', 'raw_ai_budget_census_is_causal': False, 'ai_trace_count': 269, 'ai_trace_source_stage_counts': {'ai_confirmed': 231, 'early_accel_strong_bundle_recheck_corrected': 14, 'early_accel_strong_bundle_recheck_failed': 24}, 'budget_or_block_event_count': 489, 'lineage_contract_event_count': 489, 'lineage_contract_coverage_pct': 100.0, 'pre_ai_parent_not_expected_event_count': 442, 'lineage_join_eligible_event_count': 33, 'lineage_contract_missing_event_count': 0, 'lineage_field_present_count': 33, 'parent_trace_missing_when_expected_event_count': 0, 'parent_attempt_without_trusted_result_event_count': 14, 'ai_attempt_result_unavailable_parent_not_expected_event_count': 14, 'parent_trace_missing_without_attempt_event_count': 0, 'lineage_exact_trusted_count': 31, 'lineage_untrusted_or_stale_event_count': 2, 'lineage_untrusted_or_stale_reason_counts': {'source_stale': 2}, 'lineage_joined_event_count': 31, 'exact_parent_trace_unresolved_event_count': 0, 'lineage_join_coverage_pct': 93.94, 'raw_event_lineage_join_coverage_pct': 6.34, 'lineage_join_coverage_denominator': 'events_with_a_trusted_ai_result_expected; excludes_pre_ai_and_explicit_attempt_result_unavailable', 'linked_budget_pass_trace_count': 28, 'linked_budget_block_trace_count': 2, 'linked_stage_counts': {'blocked_zero_qty': 2, 'budget_pass': 29}, 'runtime_effect': False, 'allowed_runtime_apply': False}`
- latency blockers: `latency_block:latency_state_danger=231, latency_block:tp1_direct_recheck_expired=2, latency_block:tp1_direct_recheck_positive_micro_not_recovered=1`
- price guards: `entry_ai_price_canary_skip_order:orderbook micro state is bearish with negative OFI and high spread ratio=1, entry_ai_price_canary_fallback:pre_submit_price_guard=1`
- quote refresh: `attempted=94, applied=54, latency_recovered=13, submitted_after_refresh=3`
- quote refresh downstream: `{'budget_pass_no_submit_event': 1, 'entry_ai_authority_revalidation': 8, 'no_downstream_event': 1, 'order_bundle_submitted': 3}`

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

- `5m`: ai=2, budget=2, latency=1, submitted=1, top=`blocked_strength_momentum:insufficient_history=5, blocked_strength_momentum:below_strength_base=3, blocked_vpw:-=2`, swing=`-`, upstream=`blocked_ai_score:score_4.0=1, blocked_ai_score:ai_score_50_buy_hold_override=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=1`
- `10m`: ai=2, budget=3, latency=1, submitted=1, top=`blocked_strength_momentum:insufficient_history=11, blocked_strength_momentum:below_strength_base=7, blocked_strength_momentum:below_window_buy_value=4`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=2, blocked_ai_score:score_4.0=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=1`
- `30m`: ai=10, budget=8, latency=1, submitted=1, top=`blocked_strength_momentum:insufficient_history=30, blocked_overbought:-=23, blocked_strength_momentum:below_window_buy_value=22`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=8, wait65_79_ev_candidate:score_70.0=3, blocked_ai_score:score_4.0=3`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=6`
