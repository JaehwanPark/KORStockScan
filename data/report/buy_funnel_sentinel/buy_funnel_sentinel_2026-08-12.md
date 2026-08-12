# BUY Funnel Sentinel 2026-08-12

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

- as_of: `2026-08-12T15:00:03`
- baseline_date: `2026-08-11`
- ai_confirmed unique: `96`
- budget_pass unique: `104`
- latency_pass unique: `48`
- submitted unique: `0`
- holding_started unique: `0`
- budget/ai unique: `108.3%` (baseline `62.7`)
- submitted/ai unique: `0.0%` (baseline `0.0`)
- economic bundles: `observed=0, valid=0, probe_only=0, partial_residual=0, full=0`
- economic submitted/requested: `qty=0/0 (0.0%), notional=0/0 (0.0%)`
- economic participation by venue: `{}`
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:insufficient_history=546, blocked_strength_momentum:below_window_buy_value=478, blocked_overbought:-=395, latency_block:latency_state_danger=244, blocked_vpw:-=170`
- swing blockers: `-`
- upstream blockers: `blocked_ai_score:ai_score_50_buy_hold_override=121, blocked_ai_score:score_11.0=42, first_ai_wait:-=33, blocked_ai_score:score_0.0=24, blocked_ai_score:score_19.0=19`
- AI terminal reasons: `ai_terminal:entry_policy_no_buy_score_prior=176, ai_terminal:first_ai_wait_big_bite_not_confirmed=33`
- AI actions: `events={'DROP': 191, 'NOT_EVALUATED': 4, 'WAIT': 121}, unique={'DROP': 191, 'NOT_EVALUATED': 4, 'WAIT': 121}`
- budget/AI lineage: `{'status': 'explicit_ai_trace_budget_pass_only', 'pipeline_stage_order_contract': 'latest_watching_ai_to_budget_precheck_to_final_authority_revalidation', 'raw_ai_budget_census_is_causal': False, 'ai_trace_count': 316, 'budget_or_block_event_count': 529, 'lineage_field_present_count': 46, 'lineage_exact_trusted_count': 35, 'lineage_joined_event_count': 34, 'lineage_join_coverage_pct': 6.43, 'linked_budget_pass_trace_count': 29, 'linked_budget_block_trace_count': 0, 'linked_stage_counts': {'budget_pass': 34}, 'runtime_effect': False, 'allowed_runtime_apply': False}`
- latency blockers: `latency_block:latency_state_danger=244`
- price guards: `entry_ai_price_canary_skip_order:orderbook_micro indicates bearish state with negative OFI and adverse order flow pressure=1, entry_ai_price_canary_skip_order:orderbook_micro state is bearish with negative OFI and soft stop conditions=1`
- quote refresh: `attempted=97, applied=33, latency_recovered=6, submitted_after_refresh=0`
- quote refresh downstream: `{'budget_pass_no_submit_event': 2, 'entry_ai_authority_revalidation': 4}`

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

- `5m`: ai=6, budget=4, latency=2, submitted=0, top=`blocked_overbought:-=16, blocked_strength_momentum:below_window_buy_value=8, blocked_strength_momentum:insufficient_history=7`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=2, blocked_ai_score:score_19.0=2, blocked_ai_score:score_11.0=2`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=4`
- `10m`: ai=6, budget=8, latency=2, submitted=0, top=`blocked_overbought:-=17, blocked_strength_momentum:below_window_buy_value=11, latency_block:latency_state_danger=9`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=2, blocked_ai_score:score_19.0=2, blocked_ai_score:score_11.0=2`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=4`
- `30m`: ai=23, budget=19, latency=12, submitted=0, top=`blocked_overbought:-=51, latency_block:latency_state_danger=32, blocked_strength_momentum:below_window_buy_value=24`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=5, blocked_ai_score:score_19.0=3, blocked_ai_score:score_11.0=3`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=12`
