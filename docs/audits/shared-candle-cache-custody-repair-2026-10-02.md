# Shared candle cache custody repair — 2026-10-02

## Scope and authority

User approved repair, repeated code review/fix, deployment and restart. The
existing shared read utility owns this cache; existing tests own regressions.
No new engine module, model/provider, order authority, policy or guard is added.
The earlier source-only FIFO, total 5/source-only 4 read slots, wait budgets,
retry/continuation bounds, three-second/minute cache limit and exact route,
token digest and receive-clock checks remain unchanged.

At 16:00 the deployed `8d055923` Main had four deferred chart admissions and a
separate census had one deferred ranking admission since 14:35. Two chart
continuation deferrals still reached machine assessment; 011200 lost a RECHECK
followup chart, and 065500 lost its first chart before assessment. These are
read/source receipts, not five failed orders. The 30-minute before/after raw
deferred counts (20 vs 2) lack matching successful-request denominators; the
quiet later window has no assessed probe population and proves no reduction
rate. Existing gaps are not reconstructed.

The shared directory belonged to Ubuntu (0700), while 157 lock files and 154
cache files were root-owned (0600), so Ubuntu could not join those slots.
Main's privileged file creation and atomic temporary cache publication caused
this custody defect. No direct causal assignment of the five deferrals to this
defect is made. Older independently pinned consumers may not use the new cache.

## Reference and implementation

Official Kiwoom upstream HEAD was reverified at 16:18 KST as
`953e5dbff123f437ab4d11a78a95191a685eb51f`. Previously retrieved immutable
`kiwoom/specs.py`, `kiwoom/core/client.py`, packaged API spec and Postman at
that same SHA were reused (original retrieval 14:12:16 KST). Core continuation
headers and ka10080 chart specification were rechecked. `kiwoom_docs` is absent
at that revision. This repair changes filesystem custody only, not the request,
parser, continuation, FID, auth, account/order or protocol limit contract.

Before using a lock or publishing a cache, bind its descriptor to the shared
directory's UID/GID and keep mode 0600. Do not unlink/recreate an existing lock
inode. Reject symlink lock paths. Failure opening/binding an optional lock
closes its descriptor and uses normal budget-controlled fetching. Publication
failure preserves the real reply but creates no shared cache and removes the
temporary file. No chmod to public/group-readable mode is used.

## Review and validation

Self review and re-review covered mixed launch users, atomic publication,
permissions, lock contention/identity, descriptor/temp cleanup, exact cached
scope/freshness and required/account/order exclusion. Targeted utility/probe/
market contract regressions **144 PASS/10.60s**; router/intraday handoff
**95 PASS/1.22s**; total **239 PASS**. Compile/diff checks PASS. Known fork and
Pandas deprecation warnings remain unrelated to this change.

An isolated root producer used one mocked chart fetch to replace a pre-existing
root lock's custody without changing its inode and published both files as
Ubuntu/0600. A separate real Ubuntu process reused the cache with zero
additional fetches and the original `601000` receive clock. This is a genuine
mixed-UID process test using synthetic data, not a broker/API or live edge test.
Evidence is in `tmp/shared-candle-custody-repair-20261002/`.

## Deployment and natural acceptance

First immutable release `aa6b0123` repeated **239 PASS/10.93s** and completed a
guarded restart at 16:27:35, PID 2901939/start ticks 54688643. Exact-date bootstrap
and intraday consumption PASS; frozen files (5), independent pins (416), both
cron hashes unchanged. The bounded slot repair checked 368 files and corrected
365, retaining inode/mtime/size and 0600. Ubuntu denied locks became zero. Two
natural cache writes from the new PID remained Ubuntu-owned/0600. The 16:30
scheduled Ubuntu sentinel/monitor completed at 16:30:34; no manual report or
model/API replay was used. Live identical-request joining remains not_observed;
cache production and a mixed-UID fixture do not prove a live join or economics.

Consumer re-review uncovered a second custody-related monitoring defect: the
Ubuntu cron's signal-zero probe interpreted EPERM for a live root Main as a
dead PID, while the same Main's own heartbeat/thread checks passed. The existing
process-health owner now treats signal permission denial as PID presence;
missing PID and other OS errors still fail, and heartbeat freshness/thread
checks are unchanged. Its initial regression reproduced the false absence;
after the correction the full owner gate **88 PASS** and an actual Ubuntu probe
of root PID 2901939 returned true. Final immutable publication/restart evidence
is appended after this supplemental fix. Live cache join and overall admission
rate improvement remain separate from this diagnostic repair.

Final release **b096f7ca80186eb712bbbe17af92d08187ec1a8f** at
`/home/ubuntu/KORStockScan-runtime-releases/shared-candle-custody-final-20261002-b096f7ca`
repeated all **327 PASS/13.67s**; compile/diff/parser checks PASS. The second
guarded restart succeeded, with singleton Main **2904478**, start ticks
**54744253**, exact-date bootstrap and native consumption PASS. The pure Ubuntu
consumer check at 16:37:38 confirmed PID presence, fresh heartbeat/threads PASS.
Policy/PREOPEN/prepared (5), independent pins (416) and root/Ubuntu cron hashes
are unchanged. The original five hashes also matched the first handoff; no
policy re-publishing or independent service restart occurred.

The 16:40 Ubuntu full detector has process/freshness PASS and only the existing
prior-postclose cron terminal failure remains. Its scheduled sentinel/monitor
completed **16:40:28** from the final root. The monitor still declares
`no_identified_machine_evaluation`/unobservable for its current funnel evidence;
normal artifact creation is not a claim of a successful trade or healed source
identity. Current WS provenance is bound to final PID/commit and connected.
Final slot census has every chart cache/lock file Ubuntu-owned/0600; original
slot inode/mtime/size were retained during repair. The first fixed release had
natural private Ubuntu-owned cache writes; live identical-request cross-user
joining is still not_observed. A short final-PID log lookup found no deferred
admissions, but lacks a matched workload denominator and proves no rate uplift.
Direct closure evidence: `tmp/shared-candle-custody-repair-20261002/final-closure.json`
and `data/runtime/startup_readiness/2026-10-02/shared_candle_custody_repair/final/`.

## Additional requested review: first directory creation

At the user's 16:43 re-review/deploy/restart instruction, current source and
consumers were checked again. A new defect was reproduced in an isolated
cache directory: when the shared directory is absent, a root first writer
creates the directory and its lock as root/0700+0600 under Ubuntu's parent.
The earlier file custody repair therefore does not prevent recurrence after
directory removal. The live cache directory itself was still Ubuntu-owned;
no production cache directory was removed to manufacture a sample.

The existing helper now prepares its own directory with a descriptor, rejects
directory symlinks, preserves non-root directory custody, and restores a
root-owned cache directory to its non-root parent's UID/GID. Directory mode is
0700; file mode remains 0600. A missing parent or directory custody failure
uses normal admission without creating an inaccessible root-owned hierarchy.
Lock inodes, exact request scopes and source TTLs remain unchanged.

Review covered first creation, existing root directory, directory symlinks,
descriptor closure/custody failure and missing-parent fallback. Final targeted
gate **331 PASS/8.61s**, with only the same three deprecation warnings. Actual
root producer and Ubuntu consumer tests covered both a newly created directory
and the original root-owned repro: private Ubuntu custody, one mocked fetch
per fixture, zero consumer fetches and source clock 601000 retained. Evidence:
`tmp/shared-candle-directory-review-20261002/`. Official upstream HEAD was
rechecked at 16:51 KST and remained 953e5dbff123f437ab4d11a78a95191a685eb51f;
the previously inspected immutable protocol files remain unchanged. This
supplemental fix does not modify the Kiwoom wire/response/continuation contract.

Immutable deployment and current PID acceptance for this new defect follow
below; the earlier b096f7ca receipt is retained as prior evidence.

Supplemental release **d19d0d7bf9d9bd5cb491c977648783ccffb11bdc**, root
`/home/ubuntu/KORStockScan-runtime-releases/shared-candle-directory-20261002-d19d0d7b`,
repeated **331 PASS/12.91s**. Compile/diff and print-only parser PASS. Source and
consumer re-review found no remaining defects in this directory/file custody
and PID presence scope. The authorized guarded restart succeeded at **16:57:14**,
singleton Main **2909356**, start ticks **54866604**, exact-date bootstrap/native
consumption PASS with no missing/mismatched env fields. Policy/PREOPEN/prepared
five files, 416 independent pins and both cron hashes remain unchanged.

Ubuntu process health at 16:58:38 PASS; current WS producer is bound to this
PID/commit and connected. Live cache directory is Ubuntu/0700 and the closure
census of 389 cache/lock files is entirely Ubuntu/0600. No production directory
deletion or source timestamp change was used to validate first creation.
The **17:00** scheduled Ubuntu sentinel/monitor completed **17:00:32** from this
root; detector process/freshness checks PASS, and the prior-postclose terminal
failure remains unchanged. The current monitor still reports unobservable
funnel evidence (`no_identified_machine_evaluation`), not a trading success.
Evidence: `tmp/shared-candle-directory-review-20261002/closure.json` and
`data/runtime/startup_readiness/2026-10-02/shared_candle_directory_review/`.
Live identical-request sharing, matched admission-rate reduction and economics
remain unverified; the synthetic mixed-UID first-creation acceptance is complete.
