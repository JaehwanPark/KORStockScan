# BUY Funnel Sentinel 2026-07-29

## 판정

- primary: `LATENCY_DROUGHT`
- secondary: `-`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `false`
- followup_route: `latency_quote_quality_review`
- followup_owner: `postclose_threshold_cycle`
- runtime_effect: `report_only_no_mutation`
- submit_contract_downstream: `code_improvement_workorder, lifecycle_decision_matrix.submit_bucket_attribution, threshold_cycle_ev_report, runtime_approval_summary, postclose_verifier`
- submit_contract_weak_matches: `ECONOMIC_PARTICIPATION, LATENCY_PRE_SUBMIT`

## 근거

- as_of: `2026-07-29T15:20:02`
- baseline_date: `2026-07-28`
- ai_confirmed unique: `9`
- budget_pass unique: `6`
- latency_pass unique: `2`
- submitted unique: `1`
- holding_started unique: `1`
- budget/ai unique: `66.7%` (baseline `1100.0`)
- submitted/ai unique: `11.1%` (baseline `100.0`)
- economic bundles: `observed=1, valid=1, probe_only=1, partial_residual=0, full=0`
- economic submitted/requested: `qty=1/43 (2.3%), notional=2990/128570 (2.3%)`
- economic participation by venue: `{'KRX': {'bundle_count': 1, 'probe_only_bundle_count': 1, 'partial_residual_bundle_count': 0, 'full_submitted_bundle_count': 0, 'requested_qty': 43, 'submitted_qty': 1, 'requested_notional_krw': 128570, 'submitted_notional_krw': 2990, 'submitted_qty_to_requested_qty_pct': 2.3, 'submitted_notional_to_requested_notional_pct': 2.3}}`
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:insufficient_history=155, blocked_strength_momentum:below_window_buy_value=112, first_ai_wait:-=14, blocked_liquidity:-=9, blocked_ai_score:score_0.0=8`
- swing blockers: `-`
- upstream blockers: `first_ai_wait:-=14, blocked_ai_score:score_0.0=8, blocked_ai_score:ai_score_50_buy_hold_override=5, blocked_ai_score:score_56.0=4, blocked_ai_score:score_32.0=3`
- AI terminal reasons: `ai_terminal:entry_policy_no_buy_score_prior=22, ai_terminal:first_ai_wait_big_bite_not_confirmed=14`
- latency blockers: `latency_block:latency_state_danger=3`
- price guards: `-`
- quote refresh: `attempted=5, applied=1, latency_recovered=1, submitted_after_refresh=0`
- quote refresh downstream: `{'no_downstream_event': 1}`

## 금지된 자동변경

- `score_threshold_relaxation`
- `spread_cap_relaxation`
- `fallback_reenable`
- `live_threshold_runtime_mutation`
- `bot_restart`

## 권고 액션

- Inspect latency_state_danger top reasons and recent quote quality.
- Do not auto-relax spread/ws/jitter caps; produce a candidate playbook with rollback guard first.

## Window Summary

- `5m`: ai=0, budget=0, latency=0, submitted=0, top=`-`, swing=`-`, upstream=`-`, ai_terminal=`-`
- `10m`: ai=0, budget=0, latency=0, submitted=0, top=`-`, swing=`-`, upstream=`-`, ai_terminal=`-`
- `30m`: ai=0, budget=1, latency=0, submitted=0, top=`latency_block:latency_state_danger=1`, swing=`-`, upstream=`-`, ai_terminal=`-`
