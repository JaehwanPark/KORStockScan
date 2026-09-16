# Widget postclose evaluation release pin repair (2026-09-16)

## Scope and cause

The user authorized repair of the release deployment omission identified during the 16:49 KST postclose reinspection. Only `korstockscan-samsung-widget-evaluation.service` is repinned. Main, widget trading/collector, episode and machine-final-refresh units, common selector, timer schedule, providers, thresholds, quantities, custody and safety guards are unchanged. This supersedes the earlier review's independent-pin preservation only for this named evaluation unit.

Its effective systemd drop-in pinned `intraday-entry-evidence-20260916-3e875fd0` even though the common reviewed release is `sell-no-call-aftermarket-20260916-0b712b54` (`0b712b542d075aaf1cd8e23aa250c75e32895f1d`). The old pin omits the latest changes in `widget_auto_trade_policy_calibration.py`, `widget_symbol_signal_policy_research.py` and `widget_symbol_runtime_policy.py`. This is a confirmed analysis/policy deployment omission, not proof of yesterday's verifier failure or a guaranteed process startup failure.

## Deployment and rollback contract

- Require the evaluation unit to be inactive with no main PID before mutation; verify target Git identity, clean source, executable wrapper and canonical shared mounts.
- Back up the previous effective drop-in at `tmp/widget-evaluation-release-pin-20260916.previous.conf`. Install the reviewed configuration over only `/etc/systemd/system/korstockscan-samsung-widget-evaluation.service.d/zzzzzzzzz-intraday-entry-evidence-20260916.conf`, retaining existing drop-in precedence; reload systemd without starting any service.
- Verify effective `WorkingDirectory`, `PYTHONPATH` and `ExecStart` all use the reviewed release. The existing timer remains scheduled for `2026-09-16 20:10 KST`.
- Rollback while this evaluation is inactive: reinstall the saved drop-in to the same exact path and reload systemd. Do not switch code while the evaluation is active or remove earlier releases.
- The 21:15 machine-final-refresh pin is unchanged: all directly executed producer modules and its wrapper match the latest reviewed code.

## Validation and natural acceptance

Deployment verified at 17:00 KST: effective working directory, PYTHONPATH and executable wrapper all point to `0b712b54`; evaluation remains inactive and its timer is active with next execution at 20:10 KST. Installed drop-in SHA256 is `8bfcf14339c7fa92628531c5936d4620437ff3912890d4c62dda94ad0be72054`; backup SHA256 is `093f893ab6958cfa0fd8a0eef2c0ae6099b1bbe6fef509cb5d6b5f382e80d9dd`.

Workspace and selected-release affected suites each passed `252` tests. Python compile, shell syntax, print-only checklist parser and diff checks passed. Re-review has no unresolved in-scope finding. Main PID `3779784`, widget collector PID `3654913`, widget trader PID `3654984` and their effective routes are unchanged. Machine-final-refresh route is unchanged. Systemd reload resets transient ExecStart execution statistics, so unchanged running processes were checked using MainPID and actual process existence, not the transient ExecStart pid field.

The [runtime deployment receipt](../../data/runtime/widget_evaluation_release_pin_repair_2026-09-16.json) records installation separately from scheduled natural acceptance. No reports, provider requests, real orders or service starts were used for this repair.

Natural acceptance belongs to `[WidgetPostcloseEvaluationPinAcceptance0916]` in the [daily checklist](../checklists/2026-09-16-stage2-todo-checklist.md). After the scheduled evaluation, require exact-date report generation and systemd terminal success. Late sources must flow through final control tower -> checklist -> strict verifier `--require-summary-handoff` -> controller/finalization. A configured pin or passing regression test is not natural completion, policy promotion, trading or economic acceptance.
