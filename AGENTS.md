KORStockScan working rules:

## 1. Required References

- At task start, read [Plan Rebase](docs/plan-korStockScanPerformanceOptimization.rebase.md) §1–§8 and the current KST daily `docs/checklists/YYYY-MM-DD-stage2-todo-checklist.md` objective and mandatory rules. Reuse context already read in the session; reread when it changes.
- Plan Rebase owns tuning principles, active/observe/OFF axes and rollback guards. The current checklist owns executable OPEN work, stable IDs, schedules and acceptance. Completed old items are evidence, not current owners. Missing or conflicting current context must be reported, not replaced with a historical snapshot.
- Read only task-relevant sections of linked runbooks, contracts and evidence. Do not recursively load audit reports, older checklists or archives. Read the [session pointer](docs/plan-korStockScanPerformanceOptimization.prompt.md) only when requested or the document map is unclear.
- [Intraday instructions](docs/intraday-monitoring-task-instructions.md) and [postclose instructions](docs/postclose-tuning-result-review-task-instructions.md) execute only when monitoring is invoked. Editing, quoting or reviewing them does not execute their procedures. An invocation includes its bounded source-only repairs; it does not grant trading-process restart, manual env/lock/provider/threshold changes or orders.

## 1.1 Current State Baseline

Keep current strategy state in Plan Rebase §5/§7/§8 and executable owners in the daily checklist. This file does not duplicate dated PID/commit receipts, selected-family counts, completed reviews or deployment history. Verify exact-date policy/PREOPEN and current PID receipts before claiming live application. Preserve separately approved overrides and their expiry/custody boundaries; generic baseline values do not overwrite them.

## 1.2 Baseline Document Maintenance

- Update README, runbook, Plan Rebase, prompt and AGENTS only when explicitly requested. Update the owning document first and keep related references consistent.
- Check entry, holding/exit, operating overrides, observe/report-only, OFF/retired and sync boundaries. Keep current rules here; dated progress and numeric evidence belong in checklist/audit records. Do not append history or duplicate OPEN items to instructions.
- Keep document changes separate from runtime actions and close through review, fixes and parser validation.

## 2. Decision Principles

- Maximize expected value and net profit. Period baseline: `main-only`, `normal_only`, `post_fallback_deprecation`. Clean tuning starts at `2026-06-05T00:00:00+09:00`; earlier raw/report/analytics are archive/audit only, forbidden for tuning, promotion and real execution approval. Policy: `data/source_quality/clean_baseline_policy.json`. Remote comparison values are excluded.
- Follow Plan Rebase's canary, metric, source-quality and authority contracts. Exclude identifiable bad rows/windows; whole-input blocking requires missing/invalid preflight, failed isolation or unidentifiable high-volume contract loss. Unknown-token warnings alone are not a blanket stop.
- PnL uses only `COMPLETED + valid profit_rate`; never replace missing costs/outcomes with zero or gross EV. Separate full/partial fill, real/sim/probe/CF, owner and venue/session. Win rate is diagnostic; live approval also needs rolling/cumulative or post-apply version evidence.
- Split post-BUY non-entry into `latency guard miss`, `liquidity gate miss`, `AI threshold miss`, and `overbought gate miss`. Repair attribution/source consistency before tuning thresholds.
- Preserve main/widget/episode/manual custody and order owners, operator vetoes and hard safety. Old locks do not expire merely for age or absent EV. Retired consumers and OFF/sim sample absence do not create restoration or live authority.
- Report `decision -> evidence -> next action`, separating code review, deployment, natural generation, selection, PID consumption and cost-adjusted EV/net profit. Name each blocker's owner artifact, evidence, next action and closure test. Reopen completed reviews only for new defects, changed contracts or mandatory handoff failure.

## 3. Documentation And Automation

- Internal runtime AI system/user/reviewer/classifier/schema prompts use English ASCII. Keep role/rule/field/fallback text English; Korean user-facing briefing/Telegram and contract-required canonical labels are exceptions.
- Keep daily headers to short objective and mandatory rules. Future/time-specific/recheck work belongs in the daily checklist as `- [ ]` with `Due`, `Slot`, `TimeWindow`, `Track`; reuse existing stable IDs. Preserve acceptance/history on transfer and verify one current parsed owner.
- Do not cite `docs/personal-decision-flow-notes.md` as Source or decision evidence.
- Changes to automation rules, cron, workflows or wrappers also update operating documents and checklist in the same change set.
- After document/checklist changes, run only the print-only parser. Do not inspect Project/Calendar tokens or run external sync. Leave exactly one standard sync command for the user:
  `PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar`

## 4. Execution Environment

- Use project `.venv` and reproducible project-standard commands. Ask before installing, upgrading or removing packages.
- Preserve unrelated user/generated changes. Inspect the selected release and actual consumer before runtime follow-up; workspace edits are not deployment receipts.

### 4.1 Kiwoom Official API Reference Gate

- Before writing or modifying any Kiwoom REST/WebSocket request, response parser, realtime FID mapping, REG/REMOVE or recovery flow, authentication flow, account/order call, or continuation handler, inspect the current official [`Kiwoom-Securities/Kiwoom-REST-API`](https://github.com/Kiwoom-Securities/Kiwoom-REST-API) revision and the relevant upstream files.
- Use [Kiwoom API Data Contract](./docs/kiwoom-api-data-contract.md) `Official Kiwoom Reference Gate` as the local owner for source precedence and the mandatory verification checklist. Record the upstream commit SHA, inspected paths, and retrieval time in change/review evidence.
- Treat upstream `kiwoom_docs` as the protocol documentation owner; cross-check `kiwoom/specs.py`, `kiwoom/core`, `kiwoom/realtime`, and Postman. Treat `examples` as samples only, never as authority to execute real orders or bypass local guards.
- Verify REST path, `api-id`, headers, fields, sign/unit/time semantics, continuation, errors, and real/demo separation. Verify WebSocket URL, login/control packets, realtime type/FIDs, item/suffix/route, REG/REMOVE, reconnect/resubscribe, and documented limits.
- If official repository documents, SDK/specs, portal guidance, or observed packets conflict or leave semantics undefined, do not guess. Preserve raw provenance, fail closed for semantic/runtime promotion, and open a source-quality or contract gap with tests.
- Official protocol evidence does not override KORStockScan hard safety. Never relax stale/conflict, broker/account/order/quantity/cooldown, provider, threshold, cap, bot-state, or hard/protect/emergency guards solely because an upstream example permits a call.

## 5. Codebase Work Review And Fix Loop

- Every modification closes through `implementation -> self review -> supplemental fixes -> re-review -> targeted validation -> result report`. Use `$korstockscan-review-gate` when available; fix in-scope findings without waiting for another instruction.
- Review affected producers/consumers, silent failures, missing/stale inputs and runtime/order/provider/threshold authority leaks, not only the diff. Report any repair requiring new authority before that mutation.
- Do not restart the bot, regenerate expensive reports or run broad automation until review has no unresolved in-scope defects, targeted validation passes and that follow-up is allowed by the user/runbook/checklist.
- Before creating or moving a source file, package, CLI module, report producer, or test, enforce a mandatory location gate. `src/engine` root is closed to new Python modules by default; new `.py` files there are allowed only when the engine-root allowlist test is deliberately updated in the same change with a written ownership reason. First inspect the repository structure and nearby producers/consumers, then choose the directory that matches the work's role: live engine/runtime, swing dry-run/simulation, scanner, model/training, report producer, test, document, or offline/archive analysis. Prefer existing role packages such as `src/engine/automation`, `src/engine/swing`, `src/engine/scalping`, `src/engine/lifecycle`, `src/engine/monitoring`, `src/engine/risk`, `src/engine/error_detectors`, `src/engine/infrastructure`, or `src/engine/ai` over a root-level module. If multiple locations look plausible, state the chosen ownership boundary and keep compatibility wrappers only when an existing caller or documented command requires them. Wrapper modules must be temporary compatibility surfaces, not a way to leave duplicate implementation residue.
- Run relevant pytest and compile checks for Python, `bash -n` and contract tests for wrappers, and `git diff --check`. Document/checklist changes use link/owner/authority checks and `PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500`.
- Document-only work does not require trading suites, provider calls or report regeneration. Read-only lookup/explanation/review does not invoke an implementation loop. State skipped checks and residual risk in the final report.
