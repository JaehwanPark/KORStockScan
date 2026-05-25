# BUY Funnel Sentinel 2026-05-25

## 판정

- primary: `RUNTIME_OPS`
- secondary: `-`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `true`
- followup_route: `runtime_ops_playbook`
- followup_owner: `operator_review`
- runtime_effect: `report_only_no_mutation`
- submit_contract_downstream: `code_improvement_workorder, lifecycle_decision_matrix.submit_bucket_attribution, threshold_cycle_ev_report, runtime_approval_summary, postclose_verifier`
- submit_contract_weak_matches: `-`

## 근거

- as_of: `2026-05-25T15:20:03`
- baseline_date: `2026-05-22`
- ai_confirmed unique: `0`
- budget_pass unique: `0`
- latency_pass unique: `0`
- submitted unique: `0`
- holding_started unique: `0`
- budget/ai unique: `0.0%` (baseline `1.3`)
- submitted/ai unique: `0.0%` (baseline `0.0`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `-`
- upstream blockers: `-`
- latency blockers: `-`
- price guards: `-`

## 금지된 자동변경

- `score_threshold_relaxation`
- `spread_cap_relaxation`
- `fallback_reenable`
- `live_threshold_runtime_mutation`
- `bot_restart`

## 권고 액션

- Check WS/token/event stream health immediately.
- Do not restart automatically; use the restart playbook only after explicit approval.

## Window Summary

- `5m`: ai=0, budget=0, latency=0, submitted=0, top=`-`, upstream=`-`
- `10m`: ai=0, budget=0, latency=0, submitted=0, top=`-`, upstream=`-`
- `30m`: ai=0, budget=0, latency=0, submitted=0, top=`-`, upstream=`-`
