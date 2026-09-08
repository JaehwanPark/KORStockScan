# Entry Recheck Drought Controller - 2026-09-07

## Decision

- runtime_candidate_ready: `True`
- calibration_state: `adjust_down`
- desired_enabled: `False`
- allowed_scopes: `[]`
- intraday_escalation_scopes: `[]`

## Evidence

- drought_history_dates: `['2026-09-03', '2026-09-04', '2026-09-07']`
- activation/stop: `False/True`
- stop_reasons: `['drought_history_source_quality_gap']`
- runtime_acceptance_state: `runtime_not_evaluated`
- evaluated/armed/submitted/filled/completed/paired: `0/0/0/0/0/0`
- top_evaluation_reason: `None`
- evaluation_reason_counts_by_scope: `{}`
- aggregate_diagnostic_after_cost_ev_pct/net_pnl_krw: `None/None`

## Scope decisions and fill-quality cohorts

| Scope | Enabled | Escalation | Stop reasons | Evidence start |
|---|---|---|---|---|
| KRX/KRX_REGULAR | False | False | drought_history_source_quality_gap | 2026-06-05 |
| NXT/NXT_AFTERMARKET | False | False | drought_history_source_quality_gap | 2026-06-05 |
| NXT/NXT_REGULAR | False | False | drought_history_source_quality_gap | 2026-06-05 |
| PREMARKET_KRX_LIKE/PREMARKET_KRX_LIKE | False | False | drought_history_source_quality_gap | 2026-06-05 |

| Scope | Cohort | Paired | Cost-adjusted EV (%) | Net PnL (KRW) | Decision eligible |
|---|---|---|---|---|---|

- Stops and widening use same-scope, same-fill-quality evidence; mixed scale-in is diagnostic only.

## Next action

- PREOPEN consumes only this controller report; the cumulative score sweep is diagnostic-only.
- Use the dominant evaluated blocker to design one later non-safety relaxation only after exact paired economics reaches its floor.
- Never relax stale quote, DANGER, broker/account/order/quantity/cooldown, or probe-first guards.
