# Market read singleflight and cache review

Source date: `2026-09-17 KST`. Owner: U5 in the [integrated implementation plan](../proposals/entry-opportunity-cost-full-population-tuning-implementation-plan-2026-09-17.md), under existing checklist `KiwoomCommonHealthOpportunityCostAcceptance0917`.

## Implementation and review

The utils market cache missed concurrently and each caller could issue the same HTTP read. Normalized results also shared a symbol/date key across tokens and production/demo origins. The old 2,048-entry cleanup threshold removed expired entries only, allowing unlimited live entries.

- Added process-local singleflight in the existing read-control owner. Exact wire/priority/page/retry/timeout/token/origin/date/coordinator scope is hashed; different request owners can share a physical read only within the same class. Owner errors release waiters and remove the flight; completed results are not retained. A timed-out follower cannot cancel its owner or create a duplicate retry.
- The metadata-aware utils path records `read_singleflight_status`, waited seconds, caller HTTP attempts and original transport owner. Physical source receive time and attempts remain unchanged. A deferred follower has null receive time and zero physical/caller attempts.
- All twelve existing normalized market cache namespaces separate resolved token, origin and KST date. TTL values remain unchanged. Cache entries are bounded at the existing 2,048 threshold, including all-live TTLs.
- Re-review found that tuple-only deferred filtering missed dataframe attrs. Deferred/rate-exhausted dataframe and tuple outcomes now skip publication, preserving any valid entry.
- Legacy callers without metadata and unbounded continuous history bypass singleflight: silently representing deferral as empty market data or duplicating unbounded history is not acceptable. Account/order/auth, `ka10004`, execution-critical reads and other direct clients preserve their original paths.

No new module, producer, job, subscription, broker write, provider call or package was introduced. Request fields, pagination, auth refresh, shared admission, retry counts, numeric strategy/policy parameters, quantities, custody and hard safety remain unchanged.

## Official reference

Before editing the transport wrapper, fetched official `main` in `/tmp/widget-kiwoom-reference-20260917` at `2026-09-17 13:46~13:50 KST`, SHA `953e5dbff123f437ab4d11a78a95191a685eb51f`. Inspected `kiwoom/specs.py`, `kiwoom/core/client.py`, `kiwoom/_data/kiwoom_api_spec.json` for the twelve read IDs and comparison account contracts, and their production/demo Postman envelopes. `kiwoom_docs` is absent in this revision. Existing POST paths, Bearer/content-type/api-id, continuation headers, HTTP/body return errors and production/demo boundaries are retained. Protocol reference is not order authority.

## Validation

Final implementation worktree: nine affected suites, **707 passed**; compile, Ruff and `git diff --check` passed. Coverage includes concurrent owner/follower, bounded timeout, error cleanup, reentrancy rejection, invalid wait, token/origin/route/date/priority/page/timeout/coordinator isolation, immutable receive time, guarded-path bypass, all-live cache bound and tuple/dataframe deferred-cache preservation. Scope unresolved findings: **0**.

Initial broad run had 502 passes and two fixture failures in physical-worktree low-price research tests; after copying only the existing bounded read fixtures (candidate 520,562 bytes and report 6,145,805 bytes), 504 passed. No source rows, policies or economics were synthesized. A attempted nonexistent suite path ran no tests; it is not counted as validation. The final nine-suite 707 run includes the affected low-price tests. Existing pandas deprecation warning remains a dependency warning, with no package mutation.

## Fork re-review supplement

After the first guarded deployment, the final concurrency review identified inherited parent-thread mutexes and unfinished flights in forked children. Singleflight now resets its mutex/flights in the child; utils resets the process-local normalized cache mutex/cache and token-resolution mutex while retaining valid token replacements. Parent state is unchanged. Regression tests fork with a live parent owner and parent-only held mutexes, require bounded child completion and independent child reads, and preserve the parent response/cache and token handoff. This introduces no authentication request or retry change. Final validation and deployment are recorded below.

## Remaining acceptance and scope

This closes the reviewed process-local metadata-aware market-read and normalized-cache defects. It does **not** close whole U0–U12, all U5 scheduling/direct-client/WS subscription budgets, production executable no-submit/no-fill/exit/cost quartets, admission/capacity/joint selection, natural next-date policy consumption or economics. Original guards and the existing OPEN owner remain; missing costs/outcomes stay null.

Selected release, actual main PID, independent service pins and dated broker/custody/env receipts are deployment checks, separately recorded after runtime follow-up. No future PREOPEN, natural selection or trading profit is predeclared.


## Final release and actual PID

Source commits **819b1788 / 1fb6df0c** were fast-forward pushed to main after preserving concurrent changes during checklist conflict resolution. Managed final release **5ca24599** / `market-read-singleflight-final-20260917` and its release branch were pushed. Source and managed final ten-suite runs each **776 passed**; compile/Ruff/shell syntax/diff and print-only parser (32 tasks, one current acceptance owner) passed. Four reviewed files match the worktree by SHA256; managed source is clean. The new fork tests intentionally exercise held parent-only mutexes and produce Python's fork deprecation warning; no dependency was changed.

A concurrent deployment selected **e47587c9** while the first prepared integration **b612a35e** was being checked. It was preserved in the new integration **0a874057**, rather than reverted. The inactive prepared root, original mounts and all selector backups remain available. Two actual graceful main restarts occurred: PID467975 → **492210** at13:58:37, then the fork supplement → **501022** at **14:04:58.644561+09:00**. Neither prepared-root validation nor a failed checklist merge is reported as a restart or clean initial success.

Final **14:05:56 KST** broker receipt confirms complete KRX/NXT inventory and current unfilled-order contracts: Samsung **25 shares**, open orders **0**. Final pre/post inventory, orders, owner-registry/env/dated-mechanistic-policy hashes and the eight compared independent service PID/state/drop-in records are unchanged. No independent service was restarted and future research pins were retained. Actual main cwd/commit/source-clean provenance, singleton and strict dated env/PID verification passed with mismatch/missing/unverified selected-family counts0. A post-launch WS snapshot contains **14** symbols with new0B and **14** with new0D timestamps; this is not all-scope freshness or economic acceptance.

[Scoped runtime validation record](../../data/runtime/runtime_release_validation/market-read-singleflight-20260917-5ca24599.json) preserves both broker receipts, actual PID attestation, scope exclusions and backup paths. Natural joined-request receipt, new policy selection and cost-adjusted economic improvement remain unestablished. Whole U0–U12, nonmetadata/direct-client and WS/scheduler parity, executable quartet production, admission/capacity/joint selection and future dated consumer acceptance remain OPEN under the existing owner. This record does not close the full implementation plan.


## Direct read-only client re-review supplement

Re-fetched the official reference before changes at `2026-09-17T14:09:07+09:00`;
SHA remains `953e5dbff123f437ab4d11a78a95191a685eb51f`. Inspected the existing
read specs and `kiwoom/core/client.py` HTTP/body error contract. No wire fields,
timeout, authentication lifecycle, numeric read limit or retry change was made.

Direct client parallel requests previously overwrote one shared receipt, and
local budget inspection/charge was not atomic. Receipts are now thread-local,
with original HTTP receive time, attempt count and validated success. Local
window inspection/charge, rate cooldown and snapshot use one mutex; fork resets
only the mutex and retains inherited request window/count/cooldown. Re-review
also rejected bool/float/collection/malformed return codes that integer coercion
previously accepted as success. The calling-thread property remains compatible
with runtime/research collector direct consumers.

Seven affected source suites **264 passed**; compile/Ruff/diff passed. Tests
cover parallel distinct-symbol receipts, atomic optional/mandatory reservation,
fork with held parent mutex and preserved counts, and nine malformed body return
codes. Four missing historical research config source fixtures were copied from
existing bounded original reports, with configured SHA256 verified; no source
or policy was fabricated. Scope findings0. Deployment and natural collector
receipts are recorded separately after integration validation. Whole-plan and
other direct-client/WS/scheduler or economic acceptance remain OPEN.


## Direct-client deployment and source-clock supplement

Source **60bb8169** was pushed to main. Preserve the two independent collector
parents: original Samsung/Doosan/Hanwha collectors `3e875fd0` → scoped
`08428ee8` / `collector-read-receipts-base-20260917`; runtime/research collectors
`77abb524` → scoped `c34b5fa2` / `collector-read-receipts-research-20260917`.
Both release branches were pushed, only the two reviewed classes and regression
tests were transplanted, and their AST parity passed. Physical suites **179**
and **170** passed; the research shared-path run also **170** passed.

At14:19:29~14:19:41 the five read-only collectors were restarted once each:
Samsung **531852**, Doosan **531869**, Hanwha **531874**, runtime **532006**,
research **532245**. Immediate `/proc/cwd` inspection raced with process startup
and failed; settled read-only verification proved all five selected roots,
active/success and restart count0, without an additional restart. All launch
intervals, conditional checks, resource caps, request limits and configurations
were retained. The four compared trading-service records/PIDs are unchanged
since14:05:56. Today env and dated mechanistic policy hashes are unchanged.
The owner registry gained natural BUY028050 reserved/rejected records; the full
prior registry prefix hash is preserved, so append activity is not reported as
registry immutability or as a custody mutation by this repair.

[Collector deployment record](../../data/runtime/collector_read_receipts_deployment.json)
retains current roots/PIDs, prior PIDs, scopes and rollback. Original three
snapshots resumed updating. Research reports include PASS, source gaps and an
explicit shared-read deferred receipt with HTTP attempts0/receive clock null.
A source warning or full population acceptance is not replaced by service success.

The next re-review found direct runtime/research quote/BBO clocks still stamped
with collection-start time and source checks performed before later reads. Exact
successful API/request-bound response receive time is now validated and retained
in caches and output. The final source check recalculates age after collection,
retains existing 35-second runtime source and 10-second research reuse ceilings,
blocks crossed date/session or backwards clocks, and preserves recognized safe
error reasons. No transport retry/API field, TTL, admission or numeric live
policy change occurs. Existing injected fixture clients retain their simulated
clock only as a compatibility seam, not production receipt evidence.

Re-fetched official main at **14:23:33 KST**, same SHA953e5dbf; read/time semantics
and error contract remain as inspected above. Final source seven suites **278 passed**, compile/Ruff/diff and print-only parser
passed; scope findings0. Initial new fixture missed its timedelta import and was
fixed before this final run. Managed source-clock integration/deployment receipts
follow after closure.
Whole U0–U12, full transport migration/scheduler, executable four-arm production,
admission/capacity/joint selection, next-date natural policy and economics remain
OPEN; these are not all mislabeled as sample waits.


## Price evidence and KST dated handoff re-review

The existing entry-price prompt selector accepted bool/nonfinite numeric evidence,
and hashed one file read before parsing another. Reject bool, NaN, infinity and
numeric overflow; hash and parse one UTF-8 opened snapshot. The bounded evidence
cache also binds device/inode/ctime, so equal-size retimestamped replacement does
not reuse an earlier PASS. Invalid evidence keeps the original v1 fallback;
operator enable/date, economic/sample floors and order/provider authority remain
unchanged. This is evidence validation, not activation of a new prompt.

The atomic execution-sizing dated loader and signed quantity/leg four-arm source
date upper bound now use explicit KST instead of host-local date. Regression
fixtures cover UTC/KST midnight, future signed date rejection and explicit-date
mismatch. Existing sizing policy pins, quantity conservation and promotion
contracts remain unchanged. Scope findings0; nine affected suites **826 passed**, compile/Ruff/diff and
print-only parser passed. Managed release/PID receipts follow below. Whole U0–U12 and economic acceptance remain
OPEN under the same owner.
