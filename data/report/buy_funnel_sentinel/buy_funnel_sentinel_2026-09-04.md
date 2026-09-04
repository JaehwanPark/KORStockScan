# BUY Funnel Sentinel 2026-09-04

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

- as_of: `2026-09-04T19:20:03`
- baseline_date: `2026-09-03`
- ai_confirmed unique: `66`
- budget_pass unique: `69`
- latency_pass unique: `21`
- submitted unique: `3`
- holding_started unique: `1`
- budget/ai unique: `104.5%` (baseline `113.4`)
- submitted/ai unique: `4.5%` (baseline `3.1`)
- economic bundles: `observed=3, valid=3, probe_only=3, partial_residual=0, full=0`
- economic submitted/requested: `qty=3/40 (7.5%), notional=131890/839430 (15.7%)`
- economic participation by venue: `{'KRX': {'bundle_count': 3, 'probe_only_bundle_count': 3, 'partial_residual_bundle_count': 0, 'full_submitted_bundle_count': 0, 'requested_qty': 40, 'submitted_qty': 3, 'requested_notional_krw': 839430, 'submitted_notional_krw': 131890, 'submitted_qty_to_requested_qty_pct': 7.5, 'submitted_notional_to_requested_notional_pct': 15.7}}`
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:below_window_buy_value=629, blocked_strength_momentum:insufficient_history=408, latency_block:latency_state_danger=251, blocked_overbought:-=171, blocked_liquidity:-=134`
- swing blockers: `-`
- upstream blockers: `blocked_ai_score:score_0.0=124, blocked_ai_score:ai_score_50_buy_hold_override=88, first_ai_wait:-=44, blocked_ai_score:score_11.0=9, wait65_79_ev_candidate:score_70.0=7`
- AI terminal reasons: `ai_terminal:entry_policy_no_buy_score_prior=172, ai_terminal:first_ai_wait_big_bite_not_confirmed=44`
- AI actions: `events={'DROP': 228, 'NOT_EVALUATED': 1, 'WAIT': 43}, unique={'DROP': 228, 'NOT_EVALUATED': 1, 'WAIT': 43}`
- budget/AI lineage: `{'status': 'explicit_ai_trace_budget_pass_only', 'pipeline_stage_order_contract': 'latest_watching_ai_to_budget_precheck_to_final_authority_revalidation', 'raw_ai_budget_census_is_causal': False, 'ai_trace_count': 281, 'ai_trace_source_stage_counts': {'ai_confirmed': 272, 'early_accel_strong_bundle_recheck_corrected': 2, 'early_accel_strong_bundle_recheck_failed': 7}, 'budget_or_block_event_count': 443, 'lineage_contract_event_count': 443, 'lineage_contract_coverage_pct': 100.0, 'pre_ai_parent_not_expected_event_count': 392, 'lineage_join_eligible_event_count': 31, 'lineage_contract_missing_event_count': 0, 'lineage_field_present_count': 31, 'parent_trace_missing_when_expected_event_count': 0, 'parent_attempt_without_trusted_result_event_count': 20, 'ai_attempt_result_unavailable_parent_not_expected_event_count': 20, 'parent_trace_missing_without_attempt_event_count': 0, 'lineage_exact_trusted_count': 20, 'lineage_untrusted_or_stale_event_count': 11, 'lineage_untrusted_or_stale_reason_counts': {'source_stale': 8, 'trace_id_mismatch_and_source_stale': 3}, 'lineage_joined_event_count': 20, 'exact_parent_trace_unresolved_event_count': 0, 'lineage_join_coverage_pct': 64.52, 'raw_event_lineage_join_coverage_pct': 4.51, 'lineage_join_coverage_denominator': 'events_with_a_trusted_ai_result_expected; excludes_pre_ai_and_explicit_attempt_result_unavailable', 'linked_budget_pass_trace_count': 9, 'linked_budget_block_trace_count': 0, 'linked_stage_counts': {'budget_pass': 20}, 'runtime_effect': False, 'allowed_runtime_apply': False}`
- latency blockers: `latency_block:latency_state_danger=251`
- latency causal join: `raw_danger_events=251, raw_unique=59, joined_budget_events=251, joined_budget_unique=59, budget_missing_key=0, latency_missing_key=0`
- price guards: `entry_ai_price_canary_skip_order:orderbook_micro indicates bearish state with negative OFI and high spread ratio=1, entry_ai_price_canary_fallback:skip_low_confidence=1, entry_ai_price_canary_fallback:above_best_ask=1`
- quote refresh: `attempted=13, applied=13, latency_recovered=2, submitted_after_refresh=0`
- quote refresh downstream: `{'entry_ai_authority_revalidation': 2}`

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

- `5m`: ai=0, budget=0, latency=0, submitted=0, top=`blocked_ai_score:ai_score_50_buy_hold_override=2, blocked_strength_momentum:insufficient_history=2, blocked_liquidity:-=1`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=2`, ai_terminal=`-`
- `10m`: ai=1, budget=0, latency=0, submitted=0, top=`blocked_strength_momentum:below_window_buy_value=6, blocked_strength_momentum:insufficient_history=4, blocked_ai_score:ai_score_50_buy_hold_override=3`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=3, blocked_ai_score:score_11.0=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=1`
- `30m`: ai=5, budget=4, latency=1, submitted=0, top=`blocked_strength_momentum:insufficient_history=24, blocked_strength_momentum:below_window_buy_value=22, latency_block:latency_state_danger=7`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=6, blocked_ai_score:score_19.0=1, blocked_ai_score:score_0.0=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=4`
