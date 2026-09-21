# 2026-09-21 preflight / submission bottleneck repair

Scope: user-authorized defect repair, immutable deployment and graceful main-bot restart. Existing dirty widget/process-health changes are excluded. No threshold, provider, sizing, custody or source-freshness guard changes.

## Cause and repair

- Retired pre-cutover context promotion files triggered a baseline rollback without a baseline artifact date. The consumer selected a nonexistent current-day baseline and returned `artifact_missing` before machine assessment. The rollback now binds the original date and SHA-256 of the protective baseline available before that promotion; explicit prior pins take precedence. Missing, invalid, future or hash-mismatched evidence fails closed. This baseline is a protective rule version, not current-day market evidence. Exact live source checks and the existing process handoff remain mandatory.
- The monitor labeled source-invalid attempts with an economic event gap despite their `not_applicable_machine_source_invalid` status. Economic gaps now apply only to evaluated machine actions; source alerts use the recorded source blocker.
- `KRX_LIKE_PREMARKET` and `PREMARKET_KRX_LIKE` split one exact attempt into two report identities. The Sentinel normalizes this declared alias while preserving the other five identity fields. Existing alias incidents remain as `superseded_alias` evidence, never as a claimed recovery.

## Operating closure

The launcher resolves the protective baseline before launching and exports its source date/hash. Runtime consumers revalidate the hash and source date, including after a cached read. An invalid newest baseline is not skipped in favor of older evidence. No baseline file is copied or relabeled as today's evidence.

The scheduled Sentinel consumes the selected immutable release. Old failed attempts remain historical evidence; closure requires new source-valid evaluations reaching the machine assessment. Broker acceptance, fills and net economics remain separate observations.

## Validation and deployment

- Targeted regression: 152 promotion/snapshot/monitor tests and 145 bootstrap/Sentinel tests passed. Compile and diff checks passed.
- Read-only actual-artifact check: original baseline `2026-07-23`, SHA-256 `27e607109fc1dbf4120b9d86c161b2e0773cc38ca58b6a712662bf06d91b8343`, `ready_baseline_v1`. Its source date is retained. Print-only backlog parser passed. Ruff F/E9 found two pre-existing F841 findings in unchanged Sentinel diagnostics; comparison against the base commit confirmed both are unrelated.
- Source base: `17330cdad79fcbac552d8eae75e86cfdf8805b6c`. Isolated worktree: `KORStockScan-worktrees/preflight-submit-repair-20260921`.
- Deployment/PID/natural acceptance: pending at code review; final receipt will be recorded below after authorized restart.
