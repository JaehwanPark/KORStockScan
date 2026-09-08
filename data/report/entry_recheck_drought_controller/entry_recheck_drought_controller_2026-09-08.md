# Entry Recheck Drought Controller - 2026-09-08

## Decision

- runtime_candidate_ready: `True`
- calibration_state: `adjust_down`
- desired_enabled: `False`
- allowed_scopes: `[]`
- intraday_escalation_scopes: `[]`

## Evidence

- drought_history_dates: `['2026-09-04', '2026-09-07', '2026-09-08']`
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
- Investigate source/consumption gaps and design source-only repairs immediately; positive economics is not a prerequisite for investigation.
- Live widening still requires the existing exact paired economics and separate policy authority. The finite maintenance review may recommend repair, merge, or retirement, never automatic runtime mutation.
- maintenance acceptance owner: `EntryRecheckNaturalAttribution0907`
- conditional next PREOPEN date (all existing guards required): `2026-09-11`
- source transition dates: `['2026-09-04', '2026-09-07']`
- Never relax stale quote, DANGER, broker/account/order/quantity/cooldown, or probe-first guards.

| Scope | Valid drought dates / review bound | First depleted stage | Maintenance due | Review options |
|---|---|---|---|---|
| KRX/KRX_REGULAR | 1/20 | exact_evaluated_count | False | investigate_source_and_consumption, keep_collecting_if_finite |
| NXT/NXT_AFTERMARKET | 1/20 | exact_evaluated_count | False | investigate_source_and_consumption, keep_collecting_if_finite |