# BUY Funnel Sentinel 2026-08-10

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

- as_of: `2026-08-10T15:20:04`
- baseline_date: `2026-08-07`
- ai_confirmed unique: `137`
- budget_pass unique: `29`
- latency_pass unique: `4`
- submitted unique: `0`
- holding_started unique: `0`
- budget/ai unique: `21.2%` (baseline `26.6`)
- submitted/ai unique: `0.0%` (baseline `0.0`)
- economic bundles: `observed=0, valid=0, probe_only=0, partial_residual=0, full=0`
- economic submitted/requested: `qty=0/0 (0.0%), notional=0/0 (0.0%)`
- economic participation by venue: `{}`
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:below_window_buy_value=832, blocked_overbought:-=753, blocked_strength_momentum:insufficient_history=565, blocked_liquidity:-=304, blocked_zero_qty:-=291`
- swing blockers: `-`
- upstream blockers: `first_ai_wait:-=162, blocked_ai_score:ai_score_50_buy_hold_override=118, blocked_ai_score:score_11.0=47, blocked_ai_score:score_64.0=38, blocked_ai_score:score_0.0=35`
- AI terminal reasons: `ai_terminal:entry_policy_no_buy_score_prior=244, ai_terminal:first_ai_wait_big_bite_not_confirmed=162`
- AI actions: `events={'DROP': 214, 'NOT_EVALUATED': 20, 'WAIT': 166}, unique={'DROP': 214, 'NOT_EVALUATED': 20, 'WAIT': 166}`
- budget/AI lineage: `{'status': 'explicit_ai_trace_budget_block_observed', 'pipeline_stage_order_contract': 'latest_watching_ai_to_budget_precheck_to_final_authority_revalidation', 'raw_ai_budget_census_is_causal': False, 'ai_trace_count': 400, 'budget_or_block_event_count': 361, 'lineage_field_present_count': 10, 'lineage_exact_trusted_count': 7, 'lineage_joined_event_count': 6, 'lineage_join_coverage_pct': 1.66, 'linked_budget_pass_trace_count': 3, 'linked_budget_block_trace_count': 2, 'linked_stage_counts': {'blocked_zero_qty': 2, 'budget_pass': 4}, 'runtime_effect': False, 'allowed_runtime_apply': False}`
- latency blockers: `latency_block:latency_state_danger=49`
- price guards: `-`
- quote refresh: `attempted=25, applied=12, latency_recovered=1, submitted_after_refresh=0`
- quote refresh downstream: `{'entry_ai_authority_revalidation': 1}`

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

- `5m`: ai=3, budget=0, latency=0, submitted=0, top=`blocked_overbought:-=31, blocked_strength_momentum:below_window_buy_value=8, blocked_strength_momentum:insufficient_history=7`, swing=`-`, upstream=`blocked_ai_score:score_64.0=1, wait65_79_ev_candidate:score_65.0=1, blocked_ai_score:score_65.0=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=3`
- `10m`: ai=7, budget=0, latency=0, submitted=0, top=`blocked_overbought:-=46, blocked_strength_momentum:insufficient_history=13, blocked_strength_momentum:below_window_buy_value=11`, swing=`-`, upstream=`blocked_ai_score:score_0.0=3, blocked_ai_score:ai_score_50_buy_hold_override=2, blocked_ai_score:score_62.0=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=6`
- `30m`: ai=21, budget=6, latency=1, submitted=0, top=`blocked_overbought:-=104, blocked_strength_momentum:below_window_buy_value=46, blocked_strength_momentum:insufficient_history=29`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=12, blocked_ai_score:score_0.0=6, wait65_79_ev_candidate:score_65.0=3`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=16, ai_terminal:first_ai_wait_big_bite_not_confirmed=2`
