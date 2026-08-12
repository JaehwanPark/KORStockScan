# BUY Funnel Sentinel 2026-08-12

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

- as_of: `2026-08-12T17:13:42`
- baseline_date: `2026-08-11`
- ai_confirmed unique: `102`
- budget_pass unique: `121`
- latency_pass unique: `51`
- submitted unique: `0`
- holding_started unique: `0`
- budget/ai unique: `118.6%` (baseline `57.3`)
- submitted/ai unique: `0.0%` (baseline `0.0`)
- economic bundles: `observed=0, valid=0, probe_only=0, partial_residual=0, full=0`
- economic submitted/requested: `qty=0/0 (0.0%), notional=0/0 (0.0%)`
- economic participation by venue: `{}`
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:insufficient_history=652, blocked_strength_momentum:below_window_buy_value=590, blocked_overbought:-=469, latency_block:latency_state_danger=286, blocked_vpw:-=204`
- swing blockers: `-`
- upstream blockers: `blocked_ai_score:ai_score_50_buy_hold_override=137, first_ai_wait:-=57, blocked_ai_score:score_11.0=50, blocked_ai_score:score_0.0=27, blocked_ai_score:score_14.0=21`
- AI terminal reasons: `ai_terminal:entry_policy_no_buy_score_prior=203, ai_terminal:first_ai_wait_big_bite_not_confirmed=57`
- AI actions: `events={'DROP': 227, 'NOT_EVALUATED': 7, 'WAIT': 142}, unique={'DROP': 227, 'NOT_EVALUATED': 7, 'WAIT': 142}`
- budget/AI lineage: `{'status': 'explicit_ai_trace_budget_pass_only', 'pipeline_stage_order_contract': 'latest_watching_ai_to_budget_precheck_to_final_authority_revalidation', 'raw_ai_budget_census_is_causal': False, 'ai_trace_count': 376, 'ai_trace_source_stage_counts': {'ai_confirmed': 376}, 'budget_or_block_event_count': 625, 'lineage_contract_event_count': 625, 'lineage_contract_coverage_pct': 100.0, 'pre_ai_parent_not_expected_event_count': 558, 'lineage_join_eligible_event_count': 67, 'lineage_contract_missing_event_count': 0, 'lineage_field_present_count': 50, 'parent_trace_missing_when_expected_event_count': 17, 'parent_attempt_without_trusted_result_event_count': 17, 'parent_trace_missing_without_attempt_event_count': 0, 'lineage_exact_trusted_count': 37, 'lineage_untrusted_or_stale_event_count': 13, 'lineage_untrusted_or_stale_reason_counts': {'source_stale': 6, 'trace_id_mismatch': 6, 'trace_id_mismatch_and_source_stale': 1}, 'lineage_joined_event_count': 36, 'exact_parent_trace_unresolved_event_count': 1, 'lineage_join_coverage_pct': 53.73, 'raw_event_lineage_join_coverage_pct': 5.76, 'lineage_join_coverage_denominator': 'all_events_except_explicit_pre_ai_parent_not_expected', 'linked_budget_pass_trace_count': 31, 'linked_budget_block_trace_count': 0, 'linked_stage_counts': {'budget_pass': 36}, 'runtime_effect': False, 'allowed_runtime_apply': False}`
- latency blockers: `latency_block:latency_state_danger=286, latency_block:tp1_direct_recheck_expired=1`
- price guards: `entry_ai_price_canary_skip_order:orderbook_micro indicates bearish state with negative OFI and adverse order flow pressure=1, entry_ai_price_canary_skip_order:orderbook_micro state is bearish with negative OFI and soft stop conditions=1, entry_ai_price_canary_fallback:skip_low_confidence=1, entry_ai_price_canary_skip_order:orderbook micro state bearish with negative OFI and high spread ratio=1`
- quote refresh: `attempted=111, applied=38, latency_recovered=9, submitted_after_refresh=0`
- quote refresh downstream: `{'budget_pass_no_submit_event': 2, 'entry_ai_authority_revalidation': 7}`

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

- `5m`: ai=1, budget=2, latency=0, submitted=0, top=`blocked_strength_momentum:below_window_buy_value=8, blocked_strength_momentum:insufficient_history=6, blocked_vpw:-=1`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=1, blocked_ai_score:score_0.0=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=1`
- `10m`: ai=2, budget=4, latency=0, submitted=0, top=`blocked_strength_momentum:below_window_buy_value=11, blocked_strength_momentum:insufficient_history=10, blocked_overbought:-=4`, swing=`-`, upstream=`wait65_79_ev_candidate:score_69.0=1, first_ai_wait:-=1, blocked_ai_score:score_20.0=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=2, ai_terminal:first_ai_wait_big_bite_not_confirmed=1`
- `30m`: ai=7, budget=8, latency=0, submitted=0, top=`blocked_strength_momentum:insufficient_history=32, blocked_strength_momentum:below_window_buy_value=29, latency_block:latency_state_danger=7`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=4, first_ai_wait:-=3, blocked_ai_score:score_64.0=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=6, ai_terminal:first_ai_wait_big_bite_not_confirmed=3`
