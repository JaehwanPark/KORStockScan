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

- as_of: `2026-08-28T10:20:03`
- baseline_date: `2026-08-27`
- ai_confirmed unique: `26`
- budget_pass unique: `19`
- latency_pass unique: `7`
- submitted unique: `1`
- holding_started unique: `1`
- budget/ai unique: `73.1%` (baseline `117.6`)
- submitted/ai unique: `3.8%` (baseline `5.9`)
- economic bundles: `observed=1, valid=1, probe_only=1, partial_residual=0, full=0`
- economic submitted/requested: `qty=1/1 (100.0%), notional=114400/114400 (100.0%)`
- economic participation by venue: `{'KRX': {'bundle_count': 1, 'probe_only_bundle_count': 1, 'partial_residual_bundle_count': 0, 'full_submitted_bundle_count': 0, 'requested_qty': 1, 'submitted_qty': 1, 'requested_notional_krw': 114400, 'submitted_notional_krw': 114400, 'submitted_qty_to_requested_qty_pct': 100.0, 'submitted_notional_to_requested_notional_pct': 100.0}}`
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:below_window_buy_value=36, latency_block:latency_state_danger=31, blocked_liquidity:-=25, blocked_overbought:-=18, blocked_zero_qty:-=16`
- swing blockers: `-`
- upstream blockers: `first_ai_wait:-=14, blocked_ai_score:ai_score_50_buy_hold_override=14, blocked_ai_score:score_0.0=3, wait65_79_ev_candidate:score_70.0=2, blocked_ai_score:score_20.0=2`
- AI terminal reasons: `ai_terminal:first_ai_wait_big_bite_not_confirmed=14, ai_terminal:entry_policy_no_buy_score_prior=11`
- AI actions: `events={'DROP': 26, 'WAIT': 8}, unique={'DROP': 26, 'WAIT': 8}`
- budget/AI lineage: `{'status': 'pre_ai_budget_order_observed_no_parent_expected', 'pipeline_stage_order_contract': 'latest_watching_ai_to_budget_precheck_to_final_authority_revalidation', 'raw_ai_budget_census_is_causal': False, 'ai_trace_count': 35, 'ai_trace_source_stage_counts': {'ai_confirmed': 34, 'early_accel_strong_bundle_recheck_failed': 1}, 'budget_or_block_event_count': 70, 'lineage_contract_event_count': 70, 'lineage_contract_coverage_pct': 100.0, 'pre_ai_parent_not_expected_event_count': 70, 'lineage_join_eligible_event_count': 0, 'lineage_contract_missing_event_count': 0, 'lineage_field_present_count': 0, 'parent_trace_missing_when_expected_event_count': 0, 'parent_attempt_without_trusted_result_event_count': 0, 'ai_attempt_result_unavailable_parent_not_expected_event_count': 0, 'parent_trace_missing_without_attempt_event_count': 0, 'lineage_exact_trusted_count': 0, 'lineage_untrusted_or_stale_event_count': 0, 'lineage_untrusted_or_stale_reason_counts': {}, 'lineage_joined_event_count': 0, 'exact_parent_trace_unresolved_event_count': 0, 'lineage_join_coverage_pct': 0.0, 'raw_event_lineage_join_coverage_pct': 0.0, 'lineage_join_coverage_denominator': 'events_with_a_trusted_ai_result_expected; excludes_pre_ai_and_explicit_attempt_result_unavailable', 'linked_budget_pass_trace_count': 0, 'linked_budget_block_trace_count': 0, 'linked_stage_counts': {}, 'runtime_effect': False, 'allowed_runtime_apply': False}`
- latency blockers: `latency_block:latency_state_danger=31, latency_block:tp1_direct_recheck_expired=4`
- latency causal join: `raw_danger_events=35, raw_unique=10, joined_budget_events=35, joined_budget_unique=10, budget_missing_key=0, latency_missing_key=0`
- price guards: `-`
- quote refresh: `attempted=16, applied=15, latency_recovered=6, submitted_after_refresh=0`
- quote refresh downstream: `{'entry_ai_authority_revalidation': 6}`

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

- `5m`: ai=4, budget=3, latency=2, submitted=0, top=`blocked_strength_momentum:below_window_buy_value=6, blocked_vpw:-=2, blocked_zero_qty:-=2`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=1, first_ai_wait:-=1, blocked_ai_score:score_20.0=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=2, ai_terminal:first_ai_wait_big_bite_not_confirmed=1`
- `10m`: ai=5, budget=6, latency=3, submitted=1, top=`blocked_strength_momentum:below_window_buy_value=7, latency_block:latency_state_danger=5, blocked_zero_qty:-=3`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=2, blocked_ai_score:score_64.0=1, first_ai_wait:-=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=3, ai_terminal:first_ai_wait_big_bite_not_confirmed=1`
- `30m`: ai=17, budget=13, latency=6, submitted=1, top=`blocked_strength_momentum:below_window_buy_value=23, blocked_overbought:-=12, blocked_liquidity:-=11`, swing=`-`, upstream=`first_ai_wait:-=8, blocked_ai_score:ai_score_50_buy_hold_override=6, blocked_ai_score:score_20.0=2`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=9, ai_terminal:first_ai_wait_big_bite_not_confirmed=8`
