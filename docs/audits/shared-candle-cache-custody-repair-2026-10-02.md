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

Pending immutable validation, policy-preserving guarded restart, exact-date
PID consumption, bounded existing-slot custody repair and the next scheduled
Ubuntu report. Live identical-request cache joining needs a natural receipt;
absence remains not_observed and is not manufactured through API calls.
