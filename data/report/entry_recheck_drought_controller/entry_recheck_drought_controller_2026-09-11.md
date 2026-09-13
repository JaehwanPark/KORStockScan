# Entry Recheck Drought Controller - 2026-09-11

## Decision

- runtime_candidate_ready: `True`
- calibration_state: `adjust_up`
- desired_enabled: `True`
- allowed_scopes: `['KRX|KRX_REGULAR', 'NXT|NXT_AFTERMARKET']`
- intraday_escalation_scopes: `[]`

## Evidence

- drought_history_dates: `['2026-09-09', '2026-09-10', '2026-09-11']`
- activation/stop: `True/False`
- stop_reasons: `[]`
- runtime_acceptance_state: `economics_sample_pending`
- evaluated/armed/submitted/filled/completed/paired: `46/17/1/1/1/1`
- top_evaluation_reason: `edge_wait_recovery_probe_intent_fresh_strong_micro`
- evaluation_reason_counts_by_scope: `{"KRX|KRX_REGULAR": {"daily_buy_recovery_cap_exhausted": 2, "edge_wait_recovery_probe_intent_fresh_strong_micro": 16, "quote_freshness_not_confirmed": 8, "recheck_submit_budget_bootstrap_pending": 2, "strong_micro_confirmation_missing": 14}, "NXT|NXT_AFTERMARKET": {"edge_wait_recovery_probe_intent_fresh_strong_micro": 1, "strong_micro_confirmation_missing": 3}}`
- aggregate_diagnostic_after_cost_ev_pct/net_pnl_krw: `1.172922/175.0`

## Scope decisions and fill-quality cohorts

| Scope | Enabled | Escalation | Stop reasons | Evidence start |
|---|---|---|---|---|
| KRX/KRX_REGULAR | True | False | - | 2026-06-05 |
| NXT/NXT_AFTERMARKET | True | False | - | 2026-06-05 |
| NXT/NXT_REGULAR | False | False | - | 2026-06-05 |
| PREMARKET_KRX_LIKE/PREMARKET_KRX_LIKE | False | False | - | 2026-06-05 |

| Scope | Cohort | Paired | Cost-adjusted EV (%) | Net PnL (KRW) | Decision eligible |
|---|---|---|---|---|---|
| KRX/KRX_REGULAR | probe_only | 1 | 1.1729222520107239 | 175.0 | True |

- Stops and widening use same-scope, same-fill-quality evidence; mixed scale-in is diagnostic only.

## Next action

- PREOPEN consumes only this controller report; the cumulative score sweep is diagnostic-only.
- Investigate source/consumption gaps and design source-only repairs immediately; positive economics is not a prerequisite for investigation.
- Live widening still requires the existing exact paired economics and separate policy authority. The finite maintenance review may recommend repair, merge, or retirement, never automatic runtime mutation.
- maintenance acceptance owner: `EntryRecheckNaturalAttribution0907`
- conditional next PREOPEN date (all existing guards required): `2026-09-14`
- source transition dates: `['2026-09-09', '2026-09-11']`
- Never relax stale quote, DANGER, broker/account/order/quantity/cooldown, or probe-first guards.

| Scope | Valid drought dates / review bound | First depleted stage | Maintenance due | Review options |
|---|---|---|---|---|
| KRX/KRX_REGULAR | 4/20 | exact_paired_economic_sample | False | investigate_source_and_consumption, keep_collecting_if_finite |
| NXT/NXT_AFTERMARKET | 4/20 | exact_direct_submitted_count | False | investigate_source_and_consumption, keep_collecting_if_finite |