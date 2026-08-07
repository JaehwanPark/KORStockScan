# BUY Funnel Sentinel 2026-08-07

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

- as_of: `2026-08-07T15:20:00`
- baseline_date: `2026-08-06`
- ai_confirmed unique: `139`
- budget_pass unique: `37`
- latency_pass unique: `14`
- submitted unique: `0`
- holding_started unique: `0`
- budget/ai unique: `26.6%` (baseline `71.2`)
- submitted/ai unique: `0.0%` (baseline `0.0`)
- economic bundles: `observed=0, valid=0, probe_only=0, partial_residual=0, full=0`
- economic submitted/requested: `qty=0/0 (0.0%), notional=0/0 (0.0%)`
- economic participation by venue: `{}`
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:insufficient_history=757, blocked_strength_momentum:below_window_buy_value=519, blocked_strength_momentum:below_strength_base=436, blocked_vpw:-=349, blocked_liquidity:-=341`
- swing blockers: `-`
- upstream blockers: `blocked_ai_score:ai_score_50_buy_hold_override=246, first_ai_wait:-=166, blocked_ai_score:score_0.0=149, wait65_79_ev_candidate:score_70.0=36, blocked_ai_score:score_7.0=13`
- AI terminal reasons: `ai_terminal:entry_policy_no_buy_score_prior=193, ai_terminal:first_ai_wait_big_bite_not_confirmed=166`
- AI actions: `events={'DROP': 314, 'NOT_EVALUATED': 27, 'WAIT': 93}, unique={'DROP': 314, 'NOT_EVALUATED': 27, 'WAIT': 93}`
- budget/AI lineage: `{'status': 'instrumentation_gap_parent_ai_trace_missing', 'pipeline_stage_order_contract': 'latest_watching_ai_to_budget_precheck_to_final_authority_revalidation', 'raw_ai_budget_census_is_causal': False, 'ai_trace_count': 434, 'budget_or_block_event_count': 517, 'lineage_field_present_count': 0, 'lineage_joined_event_count': 0, 'lineage_join_coverage_pct': 0.0, 'linked_budget_pass_trace_count': 0, 'linked_budget_block_trace_count': 0, 'linked_stage_counts': {}, 'runtime_effect': False, 'allowed_runtime_apply': False}`
- latency blockers: `latency_block:latency_state_danger=121, latency_block:tp1_direct_recheck_expired=2`
- price guards: `entry_ai_price_canary_fallback:above_best_ask=1`
- quote refresh: `attempted=36, applied=24, latency_recovered=4, submitted_after_refresh=0`
- quote refresh downstream: `{'budget_pass_no_submit_event': 1, 'entry_ai_authority_revalidation': 3}`

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

- `5m`: ai=0, budget=0, latency=0, submitted=0, top=`-`, swing=`-`, upstream=`-`, ai_terminal=`-`
- `10m`: ai=0, budget=0, latency=0, submitted=0, top=`blocked_zero_qty:-=5`, swing=`-`, upstream=`-`, ai_terminal=`-`
- `30m`: ai=16, budget=0, latency=0, submitted=0, top=`blocked_zero_qty:-=32, blocked_strength_momentum:below_strength_base=17, blocked_vpw:-=15`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=10, first_ai_wait:-=6, wait65_79_ev_candidate:score_70.0=4`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=6, ai_terminal:first_ai_wait_big_bite_not_confirmed=6`
