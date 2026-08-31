# BUY Funnel Sentinel 2026-08-31

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

- as_of: `2026-08-31T19:20:04`
- baseline_date: `2026-08-28`
- ai_confirmed unique: `86`
- budget_pass unique: `159`
- latency_pass unique: `59`
- submitted unique: `3`
- holding_started unique: `2`
- budget/ai unique: `184.9%` (baseline `91.4`)
- submitted/ai unique: `3.5%` (baseline `7.5`)
- economic bundles: `observed=3, valid=3, probe_only=3, partial_residual=0, full=0`
- economic submitted/requested: `qty=3/3 (100.0%), notional=181120/181120 (100.0%)`
- economic participation by venue: `{'KRX': {'bundle_count': 3, 'probe_only_bundle_count': 3, 'partial_residual_bundle_count': 0, 'full_submitted_bundle_count': 0, 'requested_qty': 3, 'submitted_qty': 3, 'requested_notional_krw': 181120, 'submitted_notional_krw': 181120, 'submitted_qty_to_requested_qty_pct': 100.0, 'submitted_notional_to_requested_notional_pct': 100.0}}`
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:below_window_buy_value=623, latency_block:latency_state_danger=553, blocked_overbought:-=364, blocked_strength_momentum:insufficient_history=308, blocked_strength_momentum:below_strength_base=241`
- swing blockers: `-`
- upstream blockers: `blocked_ai_score:ai_score_50_buy_hold_override=111, blocked_ai_score:score_0.0=33, wait65_79_ev_candidate:score_70.0=33, first_ai_wait:-=28, blocked_ai_score:score_4.0=21`
- AI terminal reasons: `ai_terminal:entry_policy_no_buy_score_prior=146, ai_terminal:first_ai_wait_big_bite_not_confirmed=28`
- AI actions: `events={'DROP': 202, 'NOT_EVALUATED': 7, 'WAIT': 154}, unique={'DROP': 202, 'NOT_EVALUATED': 7, 'WAIT': 154}`
- budget/AI lineage: `{'status': 'explicit_ai_trace_budget_pass_only', 'pipeline_stage_order_contract': 'latest_watching_ai_to_budget_precheck_to_final_authority_revalidation', 'raw_ai_budget_census_is_causal': False, 'ai_trace_count': 399, 'ai_trace_source_stage_counts': {'ai_confirmed': 363, 'early_accel_strong_bundle_recheck_corrected': 17, 'early_accel_strong_bundle_recheck_failed': 19}, 'budget_or_block_event_count': 1105, 'lineage_contract_event_count': 1105, 'lineage_contract_coverage_pct': 100.0, 'pre_ai_parent_not_expected_event_count': 922, 'lineage_join_eligible_event_count': 161, 'lineage_contract_missing_event_count': 0, 'lineage_field_present_count': 161, 'parent_trace_missing_when_expected_event_count': 0, 'parent_attempt_without_trusted_result_event_count': 22, 'ai_attempt_result_unavailable_parent_not_expected_event_count': 22, 'parent_trace_missing_without_attempt_event_count': 0, 'lineage_exact_trusted_count': 118, 'lineage_untrusted_or_stale_event_count': 43, 'lineage_untrusted_or_stale_reason_counts': {'source_stale': 42, 'trace_id_mismatch_and_source_stale': 1}, 'lineage_joined_event_count': 118, 'exact_parent_trace_unresolved_event_count': 0, 'lineage_join_coverage_pct': 73.29, 'raw_event_lineage_join_coverage_pct': 10.68, 'lineage_join_coverage_denominator': 'events_with_a_trusted_ai_result_expected; excludes_pre_ai_and_explicit_attempt_result_unavailable', 'linked_budget_pass_trace_count': 59, 'linked_budget_block_trace_count': 0, 'linked_stage_counts': {'budget_pass': 118}, 'runtime_effect': False, 'allowed_runtime_apply': False}`
- latency blockers: `latency_block:latency_state_danger=553`
- latency causal join: `raw_danger_events=553, raw_unique=126, joined_budget_events=553, joined_budget_unique=126, budget_missing_key=0, latency_missing_key=0`
- price guards: `entry_ai_price_canary_fallback:skip_low_confidence=3, entry_ai_price_canary_skip_order:orderbook_micro indicates bearish state with strong negative OFI and low quote depth, suggesting unfavorable fill probability=1, entry_ai_price_canary_fallback:low_confidence=1, entry_ai_price_canary_skip_order:orderbook micro state is bearish with negative OFI and high spread ratio=1`
- quote refresh: `attempted=20, applied=10, latency_recovered=3, submitted_after_refresh=0`
- quote refresh downstream: `{'entry_ai_authority_revalidation': 3}`

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

- `5m`: ai=3, budget=2, latency=1, submitted=0, top=`blocked_strength_momentum:below_strength_base=3, blocked_strength_momentum:insufficient_history=3, blocked_strength_momentum:below_window_buy_value=2`, swing=`-`, upstream=`blocked_ai_score:score_13.0=1, blocked_ai_score:score_64.0=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=2`
- `10m`: ai=6, budget=5, latency=1, submitted=0, top=`blocked_strength_momentum:insufficient_history=7, blocked_strength_momentum:below_window_buy_value=7, blocked_overbought:-=5`, swing=`-`, upstream=`blocked_ai_score:score_0.0=2, blocked_ai_score:ai_score_50_buy_hold_override=1, blocked_ai_score:score_13.0=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=4`
- `30m`: ai=10, budget=9, latency=1, submitted=0, top=`blocked_strength_momentum:below_window_buy_value=14, blocked_strength_momentum:insufficient_history=13, blocked_overbought:-=13`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=4, blocked_ai_score:score_17.0=2, blocked_ai_score:score_0.0=2`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=6`
