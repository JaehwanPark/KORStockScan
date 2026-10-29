# Operational log retention

This owner covers ordinary logs and explicitly closed temporary runs. Pipeline,
policy, research, broker/order and manual custody evidence retain their native
owners. No age/name-only deletion is authorized.

The generic interpreter/tool cache census prunes `.venv`, `.git`, `data`,
`logs`, `tmp` and `docs` at the workspace boundary. It neither traverses nor
deletes caches embedded in policy/research evidence or preserved private
deployment workdirs, including intentionally inaccessible OS-isolation trees.
Those trees retain their native storage owner. Enumeration failures inside the
remaining cache scope still fail cleanup; permission errors are not suppressed.

An explicitly authorized closed-target recovery may resume only a failed final
detector with `run_postclose_finalization.sh SOURCE_DATE --recover-closed-target
--resume-final-detector`. Under the existing finalizer lock, it verifies the
latest native failed detector attempt, successful cleanup chronology and unchanged
whole-chain controller/strict/snapshot generation. It preserves original logs and
the failed report in an immutable recovery receipt, reports the original cleanup
time, and runs a fresh detector. Controller, checklist, prepared/PREOPEN and policy
artifacts are not rewritten. Only the normal fresh-detector and generation checks
can emit DONE. Missing, changed or incomplete prefix evidence refuses recovery.

Module writers rotate their own file at 20 MiB under the existing process flock.
The closed inode receives a `closed_operational_log_v1` manifest in
`logs/.retention`. Cron stdout uses `deploy/run_with_owned_log.sh` before opening
the output file; internal tee writers call the rotation helper before their first
open. The previous half-hour truncation of Main's information log is removed by
the stage2 installer. Writer gzip generations retain logical hash/size receipts.

The selected `log-retention` router operation runs daily at 06:17 KST, including
holidays, independently of postclose. Registered closed generations have a
30-day, 10-generation, 200-MiB per-active-file budget. Current active logs and
unregistered old files remain protected; the old 14-day active census is not a
deletion promise. Reference/pin protection can exceed the budget and is reported
with bytes and a next-day review deadline. The full postclose cleanup invokes
the same bounded owner and retains its separate native-source gates.

Before deletion the owner checks the generation signature, content hash when
recorded, open file descriptors, current Markdown references and explicit pins.
`data/config/log_retention_pins.json` uses schema
`operational_retention_pins_v1` and a `pins` list of absolute paths, basenames or
SHA-256 values. Evidence retained outside Markdown must be pinned before its
operational generation is eligible. Unknown old files are not enrolled merely
because their names contain `.log`. A read-only all-process FD census may use
`sudo -n /usr/bin/python3` with constant code when `/proc` denies access; cleanup
itself remains unprivileged. An unavailable census prevents deletion.

Document protection uses the existing
[`DocumentReferences`](../src/engine/infrastructure/log_retention.py) owner.
It reads repository-root Markdown, all `docs` Markdown (including history), and
linked local Markdown indexes. It resolves relative/absolute paths, URL encoding,
fragments/line suffixes, reference definitions and symlink destinations; directory
references protect their descendants. Literal path/name pins remain conservative.
An archive manifest or Git commit alone does not replace a clickable file link.
Missing/unreadable document roots, symlinked document trees, invalid text and scan
limits prevent deletion when candidates exist. An empty deletion lane does not
need a document or process census.

The census reads text once per invocation and checks the file/directory identity
set and linked indexes/aliases around each unlink. New, removed or changed
documents stop that attempt; do not reuse its plan or automatically retry it.
For a verified closed archive batch, the existing owner can watch the entire
census and alias ancestors with Linux inotify after a full baseline check. Each
unlink still checks the watch; an ordinary change forces full census checks,
and lost/overflowed/unmounted watches abort. Unavailable watches retain the
original full-check path. The watch is closed on success and failure. This
avoids rescanning thousands of unchanged document paths for every archived leaf.
Keep document writers quiescent during deletion: these checks detect observed
races but cannot lock arbitrary editors. Preserve the source archive and failure
journal if a post-unlink check fails, restore the affected reference through the
existing recovery procedure, and validate before retrying. Tmp document-census
failure propagates to the existing CLI terminal/nonzero exit.

The previously untracked, reused
[`archive_tmp.py`](../tmp/source-disk-cleanup-20261022/worktree-audit/archive_tmp.py)
is now tracked at its existing path so the dated `reclaim_tmp`, archive and resume
callers retain one implementation. Both `check` and the shared `delete_verified`
entry protect document references, including partial-tree deletion. This is a
deliberate source-file exception to ignored `tmp/`, not enrollment of generated
evidence. Its original dated host census/closure dependencies and allowed-root
checks remain required; absent dependencies fail closed. Invoke reviewed source
from the workspace with its project interpreter and `PYTHONPATH=.`. Do not copy
an old unguarded helper into a new cleanup caller or substitute a selected release
that lacks this reviewed API. Changing this source does not deploy scheduled code.

Before moving cited evidence, follow the existing
[storage plan S4–S5](proposals/runtime-and-research-storage-cleanup-plan-2026-10-05.md#s4-사용-종료된-연구-tempsnapshotcache):
verify archive/member hashes, recover individually cited original bytes or a
directory index outside the removal set, update editable links, and validate them
before deletion. Strict-bound originals retain their native historical snapshot;
their receipts are never resealed to match a document edit. Recovered indexes,
original archives/manifests and linked files remain protected in later cleanup.
This gate preserves references; it does not authorize deletion or automatically
rewrite documents.

Project pytest retains failed/interrupted temporary evidence with its native
`tmp_path_retention_policy=failed`; passing per-test scratch is removed promptly.
Explicit `--basetemp` runs and historical private clones still require a closed
run, reference/FD/pin checks and verified archive custody before cleanup.
Persistent audit evidence belongs outside operational tmp. A same-filesystem
move with a validated original-path alias reduces tmp occupancy but reclaims no
filesystem space; report it separately from compressed or unlinked bytes.

Resource-pressure recovery runs only the bounded log lane. Exit zero and the
exact run-id/applied/complete terminal are required before recording success and
the 30-minute cooldown. It does not launch Parquet/research compaction. The daily
lane also keeps three calendar days of system metrics under the sampler's lock;
malformed rows retain their original bytes.

The `--pre-postclose` interface resumes completed closed-log deletion prefixes
within a shared bounded budget, without relaxing the existing per-batch budget
or the reference, pin and open-writer checks. No progress, a failed batch or an
expired budget is reported as incomplete. Its caller must use a separate
terminal from the daily receipt and a bounded execution deadline. This interface
does not stop Main or install a schedule; a reviewed stopped-consumer transition
and an authorized caller are required before operational use.

Temporary files expire only through an adjacent `*.retention.json` manifest:
schema `temporary_run_retention_v1`, nonempty `owner`, `closed=true`,
`pinned=false`, finite epoch `expires_at`, and `files` mapping direct-child
filenames to SHA-256. Unknown runs, worktrees, symlinks, open/changed files and
documented runs remain. No directory-wide recursive deletion is used. The daily
capacity census includes protected trees without following symlinks; incomplete
census stays explicit. The resource detector reports an 8-GiB budget or growth
over 2 GiB within two days. These warnings do not authorize deleting evidence.

Historical pipeline compaction may use the immutable checklist snapshot whose
hash appears in the original whole-chain strict receipt, after the next policy
day has elapsed. All other controller/strict generation checks remain required.
The compressor validates Parquet presence and gzip round-trip identity, records
original custody references, and rechecks them before publishing. It never
reseals historical PASS. `--pipeline-date YYYY-MM-DD` may be repeated to bound
an approved storage repair; today/future sources and unelapsed policy dates stay
protected. Actual `saved_bytes` subtracts the retained gzip size; dry-run bytes
remain an upper estimate. Logical hash receipts preserve gzip/plain consumer
identity.

Monitor snapshots use `monitor_snapshot_archive_identity_v1`: the compressor
verifies the full gzip round trip, original byte hash/size/inode/mtime/ctime,
and compressed byte hash/generation before removing the plain representation.
The existing next-policy-day and native controller protection still applies.
Existing gzip bytes are preserved and enrolled only after exact original-byte
comparison. Trade snapshots and completed projections may be compressed while
the small producer dependency receipt stays plain. Holding policy ancestry,
input windows, all-scope/stop consumers and bootstrap bind the same logical
source through this receipt; their census, cost and policy checks stay required.
Metadata consumers verify compressed bytes without decoding huge timelines,
and the existing explicit digest session can reuse unchanged generations.
The native postclose snapshot and stop CLIs share this invocation-local session
through their full producer/publication boundary. Intraday snapshots and normal
library callers retain full native reads; no persistent validator verdict is
published. Diagnostic full/reused bytes remain separate from semantic results.
Content-consuming research streams gzip and checks CRC. Old archives without
an original-identity receipt cannot fabricate a former raw inode or close an
existing source gap.

The trade snapshot publisher compacts row bodies but retains the root and section
line locators used by the authenticated carry-position reader. It preserves all
source fields, event order, census, cost/null values and logical section names.
Machine quote JSON and internal classifier observations remain in `fields`; they
are omitted only from the duplicate human-display `details` list. Private
`SnapshotRows` scratch uses compressed, content-addressed rows while retaining
every occurrence in its ordered list. Scratch is unlinked on close and has no
policy or archival authority. Existing completion-prefix generation checks still
own reuse; storage changes do not authorize rebuilding sealed historical reports.

The stage2 installer defines `SNAPSHOT_ARCHIVE_DAILY` at 06:25 KST every day through
the selected `snapshot-archive` router operation and its scheduled-execution lease.
It invokes the existing compressor with `--snapshots-only --days 1` against the
actual KST date, independently of today's EOD. The evening archive remains in
place. Each source must still pass its native next-policy-day, controller, strict
and custody gates; a holiday does not expire a pending policy consumer. The
original remains plain through its next trading policy day, then becomes eligible
at the following daily sweep only if native closure is valid. Eligibility is not
a promise of immediate deletion. Protected bytes and exact reasons are reported.

`--snapshot-date YYYY-MM-DD` restricts an authorized repair to those snapshots;
it cannot be combined with pipeline-only scope. The compressor discovers remaining
completed projections even after an earlier attempt archived their parent. The
parent must have a valid native archive receipt. Publication and compression share
the parent's JSON generation lock; custody is checked again immediately before
source removal. Preserve dependency receipts and one verified logical archive,
including failed-attempt evidence. There is no age-only purge of policy/research
archives: their existing reference/custody owner must prove retirement first.
Code delivery, installer application and the first natural sweep are separate;
see the [report storage review](audits/report-storage-growth-review-2026-10-27.md)
for the observed deployment state and verification.

The journald drop-in `deploy/korstockscan-journald-retention.conf` specifies
30 days, 512 MiB persistent, 128 MiB volatile and 1 GiB disk reserve. Installation
backs up any prior drop-in and preserves the current journal; no immediate
vacuum is part of this change.

Cron installation and release selection share `data/runtime/runtime_release_set.lock`.
Installers preserve unrelated cron entries. Deployment uses the normal ordered
transition and separately records selected commit, actual PID, immutable policy
hashes and post-start detector results. Applying retention is not evidence of a
successful order or improved economics.
