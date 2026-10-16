# Operational log retention

This owner covers ordinary logs and explicitly closed temporary runs. Pipeline,
policy, research, broker/order and manual custody evidence retain their native
owners. No age/name-only deletion is authorized.

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

Resource-pressure recovery runs only the bounded log lane. Exit zero and the
exact run-id/applied/complete terminal are required before recording success and
the 30-minute cooldown. It does not launch Parquet/research compaction. The daily
lane also keeps three calendar days of system metrics under the sampler's lock;
malformed rows retain their original bytes.

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
Content-consuming research streams gzip and checks CRC. Old archives without
an original-identity receipt cannot fabricate a former raw inode or close an
existing source gap.

The journald drop-in `deploy/korstockscan-journald-retention.conf` specifies
30 days, 512 MiB persistent, 128 MiB volatile and 1 GiB disk reserve. Installation
backs up any prior drop-in and preserves the current journal; no immediate
vacuum is part of this change.

Cron installation and release selection share `data/runtime/runtime_release_set.lock`.
Installers preserve unrelated cron entries. Deployment uses the normal ordered
transition and separately records selected commit, actual PID, immutable policy
hashes and post-start detector results. Applying retention is not evidence of a
successful order or improved economics.
