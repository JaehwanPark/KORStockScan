# BUY Funnel Sentinel 2026-08-11

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

- as_of: `2026-08-11T15:20:03`
- baseline_date: `2026-08-10`
- ai_confirmed unique: `70`
- budget_pass unique: `47`
- latency_pass unique: `6`
- submitted unique: `0`
- holding_started unique: `0`
- budget/ai unique: `67.1%` (baseline `21.2`)
- submitted/ai unique: `0.0%` (baseline `0.0`)
- economic bundles: `observed=0, valid=0, probe_only=0, partial_residual=0, full=0`
- economic submitted/requested: `qty=0/0 (0.0%), notional=0/0 (0.0%)`
- economic participation by venue: `{}`
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_overbought:-=526, blocked_strength_momentum:below_window_buy_value=455, blocked_strength_momentum:insufficient_history=451, blocked_zero_qty:-=273, blocked_strength_momentum:below_strength_base=235`
- swing blockers: `-`
- upstream blockers: `blocked_ai_score:ai_score_50_buy_hold_override=132, first_ai_wait:-=49, blocked_ai_score:score_11.0=36, blocked_ai_score:score_0.0=31, blocked_ai_score:score_14.0=15`
- AI terminal reasons: `ai_terminal:entry_policy_no_buy_score_prior=153, ai_terminal:first_ai_wait_big_bite_not_confirmed=49`
- AI actions: `events={'DROP': 152, 'WAIT': 95}, unique={'DROP': 152, 'WAIT': 95}`
- budget/AI lineage: `{'status': 'explicit_ai_trace_budget_block_observed', 'pipeline_stage_order_contract': 'latest_watching_ai_to_budget_precheck_to_final_authority_revalidation', 'raw_ai_budget_census_is_causal': False, 'ai_trace_count': 247, 'budget_or_block_event_count': 418, 'lineage_field_present_count': 8, 'lineage_exact_trusted_count': 6, 'lineage_joined_event_count': 6, 'lineage_join_coverage_pct': 1.44, 'linked_budget_pass_trace_count': 5, 'linked_budget_block_trace_count': 1, 'linked_stage_counts': {'blocked_zero_qty': 1, 'budget_pass': 5}, 'runtime_effect': False, 'allowed_runtime_apply': False}`
- latency blockers: `latency_block:latency_state_danger=112, latency_block:tp1_direct_recheck_expired=1`
- price guards: `-`
- quote refresh: `attempted=45, applied=25, latency_recovered=1, submitted_after_refresh=0`
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

- `5m`: ai=5, budget=2, latency=0, submitted=0, top=`blocked_overbought:-=12, blocked_strength_momentum:insufficient_history=8, blocked_strength_momentum:below_window_buy_value=8`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=5, first_ai_wait:-=1, blocked_ai_score:score_13.0=1`, ai_terminal=`ai_terminal:first_ai_wait_big_bite_not_confirmed=1, ai_terminal:entry_policy_no_buy_score_prior=1`
- `10m`: ai=8, budget=2, latency=0, submitted=0, top=`blocked_overbought:-=19, blocked_strength_momentum:below_window_buy_value=12, blocked_strength_momentum:insufficient_history=11`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=7, blocked_ai_score:score_19.0=1, first_ai_wait:-=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=2, ai_terminal:first_ai_wait_big_bite_not_confirmed=1`
- `30m`: ai=16, budget=12, latency=1, submitted=0, top=`blocked_overbought:-=66, blocked_strength_momentum:insufficient_history=30, blocked_strength_momentum:below_window_buy_value=28`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=14, blocked_ai_score:score_0.0=3, blocked_ai_score:score_19.0=2`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=9, ai_terminal:first_ai_wait_big_bite_not_confirmed=1`
