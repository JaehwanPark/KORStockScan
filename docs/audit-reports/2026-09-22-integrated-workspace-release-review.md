# Integrated workspace and runtime release review

The user requested committing the complete workspace and an integrated deployment. Existing deployment/restart approval remains applicable. This consolidation brings the previously reviewed widget observed-history, reader/policy cache, research scope and integrated adverse-flow changes into main together with the current machine, AI transport, stage runner and notification fixes. It changes no policy value, provider, quantity, custody, timer schedule or operator override.

## Review and corrections

- Compared each installed service's source release against its merge base and the complete workspace. No unique deployed production fix is absent from the integrated tree. The only branch-side test difference is the later joint-allocation failure coverage already present in main.
- Traced quote/bar producers through shared-frame reuse, historical row exclusions, widget and episode gateways, prepare/final adverse-flow checks, policy ancestry and current publication validation. Previously approved observed-history scope and strict execution-time quote guards remain separate; caches do not grant policy authority.
- Corrected a cross-process completed-bar test that mixed fixed 2026-09-21 input with the wall-clock date. Both producer and consumer now use the fixture clock; the real independent-process/read and live PID check remain exercised.
- Excluded nested generated partition lock files from Git. Runtime data and lock files remain local; all source, tests, service templates and review documents are committed.
- Found the web service repeatedly failing with status203 because its old release executable path no longer exists. Its effective command is included in the integrated code-path rebinding; no package installation is needed.

## Validation

Affected source/collector/research tests:562 passed. Additional episode/gateway, restart authority, release router, machine policy and notification tests:560 passed. Total1,122 distinct tests; one existing multiprocessing fork deprecation warning. Final immutable-release validation, compile, diff, shell syntax and print-only document parsing are required before selection and recorded in the evidence directory below. No broker request or broad report regeneration is used for validation.

The existing API reference receipts remain applicable: the integrated source files match the reviewed deployed feature branches, and this consolidation introduces no new protocol/FID/auth/REG/order parser changes. See the [integrated source adapter review](2026-09-22-entry-adverse-integrated-ws-route-repair.md) and [observed-history review](2026-09-21-widget-ws-completed-bars-implementation-review.md).

## Deployment and rollback contract

One immutable release supplies the main selector/cron router and active/future service code paths. Back up the selector and every changed systemd definition, preserve all non-code environment values and schedules, and verify the final effective paths. Restart the main through its guarded launcher and only currently running consumers (plus the already-enabled web service that is failing to start). Ended Samsung/static episode identities and inactive/manual/OFF services are not replayed. Running postclose work retains its current source until completion; do not interrupt an active writer.

The machine policy pointer must remain byte-identical across this source-only handoff. Actual PID/cwd, release commit, dated bootstrap, service state and web HTTP checks are distinct from future session source quality, orders and net-profit acceptance.

Evidence owner: `tmp/integrated-deploy-20260922/`. `services-before.json`, `source-comparison.json`, `branch-comparison.json`, test logs, release metadata and deployment/acceptance receipts record exact versions and times. Final completion is established by those receipts, not this pre-deployment review. Rollback restores the saved selection and changed unit definitions, reloads systemd and uses the standard guarded restart; preserve live custody, policies and completed attempts. The prior main release remains retained. The pre-existing broken web path is not a healthy rollback target.
