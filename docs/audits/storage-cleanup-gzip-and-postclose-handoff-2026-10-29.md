# Storage cleanup and postclose handoff — 2026-10-29

Baseline: selected release commit `8fadd634d89d3e617680f5deabd1080cf89d6caf`.
This change is source-only. It does not select a release, change cron, stop or
restart Main, establish policy consumption, or authorize deletion of a bound
source. The currently installed schedule remains authoritative until the native
change is reviewed and installed.

The projection research readers can read a verified gzip representation of a
missing logical JSON source, using the original byte SHA and size; explicit gzip
paths retain their physical-byte seal. The intraday flow report also reads an
already selected gzip input. Original frozen contracts are not rewritten. A
10/06 report validated with both the incumbent and this reader, while evaluation
of the old frozen contract failed its kernel binding under both; historical
re-evaluation therefore remains open under its original reader. Four 10/06
frozen contracts were matched to original Git commit `04920b5bc5d6796d430050d5592a0ec6065ef4a6`
in an isolated original-path reader; the origin of four later contracts remains
unknown, and a full source evaluation was not run. Changed physical
source fingerprints and their native stage-code origins still require candidate,
predecessor and selected-generation validation before deployment.

The log owner can resume verified deletion prefixes under a fixed shared budget.
The routing owner supports an explicitly authorized one-day schedule delay and
guarded restoration, and the cron detector interprets the delay only when its
producer receipt, selected source and installed cron agree. This is not a Main
stop-only implementation: EOD terminal, actual PID and supervisor closure,
collector evidence, isolation ownership and next PREOPEN hold recovery must be
closed by the native transition owner. No pre-postclose ordering, installed
20:30 schedule, actual stopped PID or next-day startup is asserted.

The matching sentinel cache gzip copies do not authorize deleting plain files:
live writers, compact SQLite offsets and historical physical identities remain
bound to the original generations. The isolated successor-index prototype is
not included until its actual closed-generation issuer, readers, rollback and
historical receipts are connected and validated. Six similarly named projection
gzip/plain pairs were fully compared and contain different logical bytes.

Validation for this integration: 560 targeted tests passed; ten existing Samsung
historical-intake tests were excluded after reproducing the same
`invalid_current_receipt` failure with the incumbent release. Python compile,
`git diff --check` and the documentation backlog print-only parser passed. The
current daily checklist is a shared, untracked workspace document and is not
included in this commit; its `PrePostcloseStorageSequencing` item owns the open
handoff and actual consumption criteria.

Data cleanup evidence stays outside the commit under
`data/audit/storage_cleanup/2026-10-29-1312/` and
`data/audit/storage_cleanup/2026-10-29-log-retention/`. It records the retired
Samsung widget source removal and its historical replay limitation, redundant
worktree baseline removal, log-retention batches, and full gzip comparisons.
