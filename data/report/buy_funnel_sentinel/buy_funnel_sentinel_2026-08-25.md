# BUY Funnel Sentinel 2026-08-25

## 판정

- primary: `NORMAL`
- secondary: `-`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `false`
- followup_route: `normal_no_action`
- followup_owner: `none`
- runtime_effect: `report_only_no_mutation`
- submit_contract_downstream: `code_improvement_workorder, lifecycle_decision_matrix.submit_bucket_attribution, threshold_cycle_ev_report, runtime_approval_summary, postclose_verifier`
- submit_contract_weak_matches: `-`

## 근거

- as_of: `2026-08-25T09:10:02`
- baseline_date: `2026-08-24`
- ai_confirmed unique: `4`
- budget_pass unique: `1`
- latency_pass unique: `0`
- submitted unique: `0`
- holding_started unique: `0`
- budget/ai unique: `25.0%` (baseline `100.0`)
- submitted/ai unique: `0.0%` (baseline `0.0`)
- economic bundles: `observed=0, valid=0, probe_only=0, partial_residual=0, full=0`
- economic submitted/requested: `qty=0/0 (0.0%), notional=0/0 (0.0%)`
- economic participation by venue: `{}`
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:below_buy_ratio=6, blocked_liquidity:-=5, blocked_vpw:-=3, first_ai_wait:-=3, blocked_ai_score:ai_score_50_buy_hold_override=3`
- swing blockers: `-`
- upstream blockers: `first_ai_wait:-=3, blocked_ai_score:ai_score_50_buy_hold_override=3, wait65_79_ev_candidate:score_65.0=1`
- AI terminal reasons: `ai_terminal:first_ai_wait_big_bite_not_confirmed=3`
- AI actions: `events={'DROP': 2, 'WAIT': 2}, unique={'DROP': 2, 'WAIT': 2}`
- budget/AI lineage: `{'status': 'pre_ai_budget_order_observed_no_parent_expected', 'pipeline_stage_order_contract': 'latest_watching_ai_to_budget_precheck_to_final_authority_revalidation', 'raw_ai_budget_census_is_causal': False, 'ai_trace_count': 6, 'ai_trace_source_stage_counts': {'ai_confirmed': 4, 'early_accel_strong_bundle_recheck_failed': 2}, 'budget_or_block_event_count': 3, 'lineage_contract_event_count': 3, 'lineage_contract_coverage_pct': 100.0, 'pre_ai_parent_not_expected_event_count': 3, 'lineage_join_eligible_event_count': 0, 'lineage_contract_missing_event_count': 0, 'lineage_field_present_count': 0, 'parent_trace_missing_when_expected_event_count': 0, 'parent_attempt_without_trusted_result_event_count': 0, 'ai_attempt_result_unavailable_parent_not_expected_event_count': 0, 'parent_trace_missing_without_attempt_event_count': 0, 'lineage_exact_trusted_count': 0, 'lineage_untrusted_or_stale_event_count': 0, 'lineage_untrusted_or_stale_reason_counts': {}, 'lineage_joined_event_count': 0, 'exact_parent_trace_unresolved_event_count': 0, 'lineage_join_coverage_pct': 0.0, 'raw_event_lineage_join_coverage_pct': 0.0, 'lineage_join_coverage_denominator': 'events_with_a_trusted_ai_result_expected; excludes_pre_ai_and_explicit_attempt_result_unavailable', 'linked_budget_pass_trace_count': 0, 'linked_budget_block_trace_count': 0, 'linked_stage_counts': {}, 'runtime_effect': False, 'allowed_runtime_apply': False}`
- latency blockers: `latency_block:latency_state_danger=1`
- price guards: `-`
- quote refresh: `attempted=1, applied=1, latency_recovered=0, submitted_after_refresh=0`
- quote refresh downstream: `{}`

## 금지된 자동변경

- `score_threshold_relaxation`
- `spread_cap_relaxation`
- `fallback_reenable`
- `live_threshold_runtime_mutation`
- `bot_restart`

## 권고 액션

- Continue monitoring; no dynamic action required.

## Window Summary

- `5m`: ai=3, budget=0, latency=0, submitted=0, top=`blocked_strength_momentum:below_buy_ratio=4, blocked_liquidity:-=3, blocked_vpw:-=2`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=2, first_ai_wait:-=2, wait65_79_ev_candidate:score_65.0=1`, ai_terminal=`ai_terminal:first_ai_wait_big_bite_not_confirmed=2`
- `10m`: ai=4, budget=1, latency=0, submitted=0, top=`blocked_strength_momentum:below_buy_ratio=6, blocked_liquidity:-=5, blocked_vpw:-=3`, swing=`-`, upstream=`first_ai_wait:-=3, blocked_ai_score:ai_score_50_buy_hold_override=3, wait65_79_ev_candidate:score_65.0=1`, ai_terminal=`ai_terminal:first_ai_wait_big_bite_not_confirmed=3`
- `30m`: ai=4, budget=1, latency=0, submitted=0, top=`blocked_strength_momentum:below_buy_ratio=6, blocked_liquidity:-=5, blocked_vpw:-=3`, swing=`-`, upstream=`first_ai_wait:-=3, blocked_ai_score:ai_score_50_buy_hold_override=3, wait65_79_ev_candidate:score_65.0=1`, ai_terminal=`ai_terminal:first_ai_wait_big_bite_not_confirmed=3`
