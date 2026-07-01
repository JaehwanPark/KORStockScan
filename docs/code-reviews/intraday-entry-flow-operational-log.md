# Intraday Entry Flow Operational Log

Purpose: keep only durable decisions, code/report contract changes, validation results, and operating boundaries for intraday entry flow diagnostics.

This file is cumulative. Do not append every 10-minute loop result here. Loop-level numeric detail belongs in `data/report/intraday_entry_blocker_diagnostics/` and the current flow artifact under `data/report/intraday_entry_flow/`.

## Operating Rules

- Record only meaningful changes: source-quality fixes, report contract changes, artifact retention decisions, validation outcomes, and guard boundaries.
- Keep each entry short and audit-oriented: decision, change, validation, operating boundary.
- Do not use this file as a checklist owner. Time-specific work belongs in the dated checklist.
- Do not use this file as tuning evidence by itself. The evidence source remains the generated report artifact named in the entry.
- Runtime/order/provider/bot/threshold changes are forbidden unless a separate approved artifact and checklist owner explicitly allow them.

## Artifact Retention Contract

- `data/report/intraday_entry_flow/intraday_entry_flow_YYYY-MM-DD_current.md` is the fixed cumulative flow artifact for the target date.
- `data/report/intraday_entry_flow/intraday_entry_flow_YYYY-MM-DD_<HHMM>_to_<HHMM>_final_stabilization.md` is allowed as a final goal/session summary.
- Timestamp loop snapshots such as `intraday_entry_flow_YYYY-MM-DD_1300_to_1410.md` and matching CSV files are intermediate artifacts. Delete them after the fixed file or final summary has absorbed the evidence.
- Temporary CSV output should use `/tmp/...` and be deleted after the final check.
- Final stabilization summaries must point `source_flow_final` to the fixed `*_current.md` file, not to a deleted timestamp snapshot.

## Entry Template

```md
## N. YYYY-MM-DD short title

### Decision

- ...

### Change

- ...

### Validation

- ...

### Operating Boundary

- `runtime_effect=false`
- `allowed_runtime_apply=false`
- Preserved guards: stale quote, latency DANGER, spread, broker/account/order/quantity/cooldown, hard/protect/emergency.
```

## 1. 2026-06-29 Fixed Flow Artifact Operation

### Decision

- Keep one fixed flow artifact for the day instead of retaining every timestamp snapshot.
- Treat timestamp `intraday_entry_flow_*` files as intermediate outputs after the fixed file is updated.

### Change

- Fixed artifact: `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-29_0800_to_1004.md`.
- Later runs used explicit output paths and temporary CSV files.

### Validation

- Directory cleanup left only the fixed 2026-06-29 flow markdown artifact for that date.
- Follow-up validations used targeted pytest, py_compile, and `git diff --check` around the touched report code and runtime fixes.

### Operating Boundary

- `runtime_effect=false`
- `allowed_runtime_apply=false`
- No threshold/order/provider/bot change was authorized by this artifact cleanup.

## 2. 2026-06-30 Latency Provenance Gap Closure

### Decision

- A `latency_provenance_gap` finding for `033100` was a diagnostic/event-cache consumption gap, not missing source evidence in the original pipeline events.
- The original latency block rows contained spread, WS age, and orderbook microstructure fields.

### Change

- `src/engine/monitoring/intraday_entry_blocker_diagnostics.py` preserves per-symbol `latency_danger_root_cause` and recent latency provenance fields.
- `src/engine/monitoring/intraday_entry_flow_report.py` uses diagnostic `latency_danger_root_cause` when event-cache rows are missing.
- Added regression coverage in the intraday blocker diagnostics and flow report tests.

### Validation

- Targeted report regeneration restored `033100` as `spread_microstructure_wide`.
- Validation at implementation time: targeted pytest for intraday diagnostics and flow report, plus py_compile for touched modules.

### Operating Boundary

- `runtime_effect=false`
- `allowed_runtime_apply=false`
- This was source-quality/diagnostic repair only. It did not bypass stale quote, latency DANGER, spread, broker/account/order/quantity/cooldown, or hard/protect/emergency guards.

## 3. 2026-06-30 Spread Microstructure Handoff

### Decision

- Submit-drought root cause handoff must preserve orderbook microstructure spread separately from generic spread/slippage.

### Change

- BUY Funnel Sentinel splits `spread_microstructure_guard` from generic spread/slippage root causes.
- Daily threshold-cycle source metrics preserve latency root-cause counts and expose microstructure spread, spread/slippage, and quote-stale counts separately.
- Workorder provenance now preserves the microstructure spread root-cause count.

### Validation

- Targeted tests covered BUY Funnel classification, code-improvement workorder provenance, daily threshold-cycle source metrics, intraday diagnostics, and flow report behavior.

### Operating Boundary

- `runtime_effect=false`
- `allowed_runtime_apply=false`
- This changed source taxonomy and downstream handoff only. It did not relax spread cap, stale quote, latency DANGER, broker/account/order/quantity/cooldown, or hard/protect/emergency guards.

## 4. 2026-06-30 Known Latency Guard Suppression

### Decision

- Known latency guard causes (`quote_stale`, `spread_too_wide`, `spread_microstructure_wide`) should not remain actionable major blockers after root-cause classification closes them as preserved quality guards.
- Unknown, other, or unresolved latency danger remains actionable.

### Change

- Intraday blocker taxonomy consumes `latency_root_cause`.
- Known preserved quality guards are routed as non-major `pre_submit_quality_guard`.
- Unknown latency danger remains in actionable major blocker counts.

### Validation

- Regression tests cover known guard suppression, unknown latency actionability, and mixed known/unknown causes within the same symbol.
- Final targeted validation at commit time: `276 passed` across BUY Funnel, code-improvement workorder, daily threshold-cycle report, intraday blocker diagnostics, and intraday entry flow report tests.

### Operating Boundary

- `runtime_effect=false`
- `allowed_runtime_apply=false`
- Diagnostic taxonomy changed only; runtime guards were not relaxed.

## 5. 2026-06-30 Flow Snapshot Cleanup

### Decision

- 2026-06-30 timestamp flow snapshots were intermediate artifacts and should not remain as durable files.
- The durable files are the daily fixed current flow artifact and final stabilization summaries.

### Change

- Kept:
  - `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-30_current.md`
  - `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-30_final_stabilization.md`
  - `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-30_1300_to_1500_final_stabilization.md`
- Deleted:
  - 2026-06-30 `0800_to_*`, `1100_to_*`, and `1300_to_*` intermediate flow markdown/CSV snapshots.
- Updated final stabilization references so deleted intermediate files are not required.

### Validation

- No 2026-06-30 intraday entry flow CSV files remained in `data/report/intraday_entry_flow/`.
- Deleted intermediate flow file references were removed from final summaries.
- `git diff --check` passed.

### Operating Boundary

- `runtime_effect=false`
- `allowed_runtime_apply=false`
- This was artifact retention cleanup only.

## 6. 2026-07-01 Rising Missed Classification And Current Artifact Output

### Decision

- Forced `rising_missed_one_share_entry` scout events remain separate observations and must not count as normal BUY/submit/fill resolution.
- Rising missed diagnosis should prioritize eligible actionable blockers and exclude source-quality churn, intended guards, runtime backpressure observations, strategy rejects, and already-submitted candidates from forced one-share eligibility.
- Intraday flow report defaults must update only the fixed `intraday_entry_flow_YYYY-MM-DD_current.md` artifact; CSV output is temporary under `/tmp`.

### Change

- Added common rising-missed classification fields and one-share eligibility gates.
- Raised the default rising-missed full-eval threshold from `0.5%` to `1.0%` for scanner/runtime diagnostics.
- Blocked forced one-share scout evaluation when a normal submit has already resolved the candidate.
- Changed intraday flow report default output paths to fixed current markdown plus temporary `/tmp` CSV.
- Added a rest-quote-only confirmation block before stop-line-touch mandatory averaging down.

### Validation

- `PYTHONPATH=. .venv/bin/pytest src/tests/test_sniper_scale_in.py src/tests/test_intraday_entry_blocker_diagnostics.py src/tests/test_intraday_entry_flow_report.py -q` passed with `403 passed`.
- `PYTHONPATH=. .venv/bin/python -m py_compile src/engine/monitoring/intraday_entry_flow_report.py src/engine/monitoring/intraday_entry_blocker_diagnostics.py src/engine/scalping/rising_missed_one_share_entry.py src/engine/kiwoom_sniper_v2.py src/engine/sniper_state_handlers.py` passed.
- `git diff --check` passed.

### Operating Boundary

- `runtime_effect=false` for report/classification changes.
- `allowed_runtime_apply=false`
- No intraday threshold mutation, provider route change, bot restart, cap change, or stale/broker/account/order/quantity/cooldown/hard-safety guard relaxation was performed.

## 7. 2026-07-01 Runtime Attach Identity Mismatch Exclusion

### Decision

- A rising scanner promotion that cannot attach to the runtime target because of `scanner_identity_name_mismatch` is a source-quality/identity mismatch exclusion, not a normal BUY submit blocker or forced one-share scout candidate.

### Change

- Intraday blocker diagnostics now summarize `scalping_scanner_runtime_target_attach` rows skipped by `scanner_identity_name_mismatch`.
- Rising-missed classification routes those rows to `source_quality_excluded` and sets forced one-share eligibility to false.

### Validation

- Regression test added for a rising candidate with repeated runtime attach identity mismatch.
- Live 2026-07-01 diagnostic regeneration changed the raw eligible case to `source_quality_excluded` and returned `rising_missed_one_share_eligible_symbol_count=0`.

### Operating Boundary

- `runtime_effect=false`
- `allowed_runtime_apply=false`
- This changed diagnostic/source-quality classification only. It did not alter runtime target attachment, order submission, stale/latency/broker/account/order/quantity/cooldown, hard safety, provider route, bot state, or thresholds.

## 8. 2026-07-01 16:00 Flow Live Source And Active Window Repair

### Decision

- The 16:00~19:00 flow goal must use live `pipeline_events_YYYY-MM-DD.jsonl`, not the 15:20 buy-funnel sentinel cache snapshot.
- A symbol promoted before the window but still active inside the window must remain visible in the fixed current flow report.

### Change

- `intraday_entry_flow_report` now prefers `data/pipeline_events/pipeline_events_YYYY-MM-DD.jsonl` as the default event source when present.
- Diagnostic promotion filtering now keeps rows whose `last_event_at` is inside the requested window even when `first_promoted_at` is before `since`.
- Window reports clamp the displayed first observation to the requested `since` boundary or the first in-window event, preventing old promotion timestamps from leaking into current-window flow rows.

### Validation

- `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_intraday_entry_flow_report.py` passed with `18 passed`.
- `PYTHONPATH=. .venv/bin/python -m py_compile src/engine/monitoring/intraday_entry_flow_report.py src/tests/test_intraday_entry_flow_report.py` passed.
- `git diff --check` passed for the changed report/test paths.
- 2026-07-01 16:00 current flow regenerated with `source_events=data/pipeline_events/pipeline_events_2026-07-01.jsonl`, `symbol_count=17`, and `rising_symbol_count_by_max_delta=8`.

### Operating Boundary

- `runtime_effect=false`
- `allowed_runtime_apply=false`
- This is report-source and window-filter repair only. It does not change thresholds, provider route, bot state, order submission, stale/latency/broker/account/order/quantity/cooldown guards, or hard safety.
