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
- submit_contract_weak_matches: `BROKER_RECEIPT, BUDGET_PASS_COLLAPSE, ENTRY_AI_AUTHORITY_REVALIDATION, FILL_QUALITY, LATENCY_PRE_SUBMIT, PRICE_REVALIDATION, SIM_REAL_AUTHORITY, TELEGRAM_POST_SUBMIT_ONLY, UPSTREAM_GATE`

## 근거

- as_of: `2026-08-14T12:25:03`
- baseline_date: `2026-08-13`
- ai_confirmed unique: `57`
- budget_pass unique: `69`
- latency_pass unique: `21`
- submitted unique: `3`
- holding_started unique: `2`
- budget/ai unique: `121.1%` (baseline `51.0`)
- submitted/ai unique: `5.3%` (baseline `2.0`)
- economic bundles: `observed=0, valid=0, probe_only=0, partial_residual=0, full=0`
- economic submitted/requested: `qty=0/0 (0.0%), notional=0/0 (0.0%)`
- economic participation by venue: `{}`
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:below_window_buy_value=347, blocked_strength_momentum:insufficient_history=261, blocked_overbought:-=196, latency_block:latency_state_danger=134, blocked_strength_momentum:below_strength_base=111`
- swing blockers: `-`
- upstream blockers: `blocked_ai_score:ai_score_50_buy_hold_override=69, wait65_79_ev_candidate:score_70.0=27, first_ai_wait:-=26, blocked_ai_score:score_70.0=19, blocked_ai_score:score_4.0=13`
- AI terminal reasons: `ai_terminal:entry_policy_no_buy_score_prior=62, ai_terminal:first_ai_wait_big_bite_not_confirmed=26`
- AI actions: `events={'DROP': 106, 'NOT_EVALUATED': 1, 'WAIT': 72}, unique={'DROP': 106, 'NOT_EVALUATED': 1, 'WAIT': 72}`
- budget/AI lineage: `{'status': 'explicit_ai_trace_budget_block_observed', 'pipeline_stage_order_contract': 'latest_watching_ai_to_budget_precheck_to_final_authority_revalidation', 'raw_ai_budget_census_is_causal': False, 'ai_trace_count': 201, 'ai_trace_source_stage_counts': {'ai_confirmed': 179, 'early_accel_strong_bundle_recheck_corrected': 10, 'early_accel_strong_bundle_recheck_failed': 12}, 'budget_or_block_event_count': 356, 'lineage_contract_event_count': 356, 'lineage_contract_coverage_pct': 100.0, 'pre_ai_parent_not_expected_event_count': 294, 'lineage_join_eligible_event_count': 20, 'lineage_contract_missing_event_count': 0, 'lineage_field_present_count': 20, 'parent_trace_missing_when_expected_event_count': 0, 'parent_attempt_without_trusted_result_event_count': 42, 'ai_attempt_result_unavailable_parent_not_expected_event_count': 42, 'parent_trace_missing_without_attempt_event_count': 0, 'lineage_exact_trusted_count': 17, 'lineage_untrusted_or_stale_event_count': 3, 'lineage_untrusted_or_stale_reason_counts': {'attempt_untrusted': 1, 'source_stale': 1, 'trace_id_mismatch': 1}, 'lineage_joined_event_count': 17, 'exact_parent_trace_unresolved_event_count': 0, 'lineage_join_coverage_pct': 85.0, 'raw_event_lineage_join_coverage_pct': 4.78, 'lineage_join_coverage_denominator': 'events_with_a_trusted_ai_result_expected; excludes_pre_ai_and_explicit_attempt_result_unavailable', 'linked_budget_pass_trace_count': 12, 'linked_budget_block_trace_count': 2, 'linked_stage_counts': {'blocked_zero_qty': 2, 'budget_pass': 15}, 'runtime_effect': False, 'allowed_runtime_apply': False}`
- latency blockers: `latency_block:latency_state_danger=134, latency_block:tp1_direct_recheck_positive_micro_not_recovered=1`
- price guards: `entry_ai_price_canary_fallback:low_confidence=81, entry_ai_price_canary_fallback:pre_submit_price_guard=1`
- quote refresh: `attempted=60, applied=29, latency_recovered=10, submitted_after_refresh=0`
- quote refresh downstream: `{'armed_expired_before_submit': 1, 'entry_ai_authority_revalidation': 9}`

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

- `5m`: ai=3, budget=9, latency=1, submitted=0, top=`blocked_overbought:-=17, latency_block:latency_state_danger=7, blocked_strength_momentum:below_strength_base=7`, swing=`-`, upstream=`wait65_79_ev_candidate:score_70.0=1, blocked_ai_score:ai_score_50_buy_hold_override=1, blocked_ai_score:score_7.0=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=1`
- `10m`: ai=5, budget=15, latency=2, submitted=0, top=`blocked_overbought:-=23, latency_block:latency_state_danger=15, blocked_strength_momentum:below_window_buy_value=15`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=2, blocked_ai_score:score_11.0=1, wait65_79_ev_candidate:score_70.0=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=2`
- `30m`: ai=14, budget=22, latency=5, submitted=2, top=`blocked_strength_momentum:below_window_buy_value=84, blocked_overbought:-=39, blocked_strength_momentum:insufficient_history=36`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=12, first_ai_wait:-=4, wait65_79_ev_candidate:score_70.0=4`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=7, ai_terminal:first_ai_wait_big_bite_not_confirmed=4`
