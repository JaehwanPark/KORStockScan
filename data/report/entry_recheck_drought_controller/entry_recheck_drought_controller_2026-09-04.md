# Entry Recheck Drought Controller - 2026-09-04

## Decision

- runtime_candidate_ready: `True`
- calibration_state: `adjust_up`
- desired_enabled: `True`
- allowed_scopes: `['KRX|KRX_REGULAR', 'NXT|NXT_AFTERMARKET']`
- intraday_escalation_scopes: `[]`

## Evidence

- drought_history_dates: `['2026-09-02', '2026-09-03', '2026-09-04']`
- activation/stop: `True/False`
- stop_reasons: `[]`
- runtime_acceptance_state: `runtime_not_evaluated`
- evaluated/armed/submitted/filled/completed/paired: `0/0/0/0/0/0`
- top_evaluation_reason: `None`
- evaluation_reason_counts_by_scope: `{}`
- after_cost_ev_pct/net_pnl_krw: `None/None`

## Next action

- PREOPEN consumes only this controller report; the cumulative score sweep is diagnostic-only.
- Use the dominant evaluated blocker to design one later non-safety relaxation only after exact paired economics reaches its floor.
- Never relax stale quote, DANGER, broker/account/order/quantity/cooldown, or probe-first guards.
