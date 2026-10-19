# Main initial BUY SOR route repair — 2026-10-19

## Decision and scope

User instruction: repair the observed defects and repeat code review and fixes.
The isolated candidate starts at selected release commit
`34798c60c43984ab9fb97b07e224f9a29883503d`. The shared workspace's unrelated
changes, live release, selector, policy files, environment and Main process are
preserved. This change does not deploy, restart, invoke a provider or submit an
order.

Monitoring evidence is in
`tmp/submission-monitor-20261019-latest-restart-1730/` in the shared workspace.
The natural 16:27:14 Jusung attempt `aims-8445534c8d713a078c0b` passed machine
and auxiliary AI, then reached an AUTO-to-NXT request and local
`route_ineligible` with zero broker attempts. Controlled current-code tests
also showed direct KRX allowed but SOR rejected for KRX=True/NXT=False.

## Implementation and consumers

- Rename the zero-base-only request binder to
  `_bind_main_entry_order_request` and use it for fixed watch and zero-base
  Main entries. Verify current watch generation, observed route, session,
  effective venue, buy window and agreement with the decision's recorded
  broker route. Reject conflicting explicit routes without rewriting them.
- Bind each planned leg before sequential-quantity conversion and immutable
  sizing/price-plan hashes. Preserve the planned exchange fields in normal,
  probe, market-first and IOC request conversion. Recheck at the final request
  boundary. Existing successor, cancellation and journal consumers retain the
  original order's explicit route.
- Freeze the same observed broker route in the operating contract. An invalid
  or conflicting watch cannot silently obtain a different frozen route.
- SOR preflight accepts either verified eligible venue when both eligibility
  axes are known. Direct KRX/NXT retain their respective venue requirements.
  Unknown axes, invalid/partial source quality and existing date/session/type
  restrictions continue to block. There is no UNKNOWN-to-True conversion.
- Repair the affected frozen-policy producer's pre-existing omission of
  `reversal_cumulative_data.json` and `reversal_price_progress_data.json`.
  Capture their original bytes through the existing bounded, compressed file
  snapshot. ENTRY replay still uses frozen files and checks the catalog's
  pinned hashes; no read from current disk is allowed as a substitute.

The legacy AUTO route resolver, quantity allocation, prices, order-type
restrictions, source freshness, exact WS leases, machine/AI authority,
account/order/custody guards and operator approval checks are unchanged.
Observation admission remains separate from permission to submit an order.

## Review and supplemental fixes

1. A final-request-only fix would leave earlier operating/sizing contracts on
   another route. Bind before plan hashing and retain the route in all request
   variants and the frozen operating contract.
2. A binder must not replace an explicit conflicting venue or an AI decision's
   recorded venue. Those cases now fail closed; request bytes remain intact.
3. Real regular-session consumers use both `krx_regular` and `KRX_REGULAR`.
   Treat these case variants as the same bucket while rejecting a different
   session, old generation or different source route/venue.
4. Reject malformed decision metadata and numeric/boolean exchange values
   without an uncaught exception in the Main loop.
5. A source-to-consumer test initially used SQLite, which strips timezone
   offsets from these ORM datetimes. Reuse the existing aware-ORM boundary
   fixture that models PostgreSQL; do not infer a timezone or relax production
   source checks to make SQLite pass.
6. The additional pre-AI replay test failed with `unrecorded_file_read` both
   before this change (clean 34798c60c) and in the candidate. The catalog module
   imports two immutable JSON sources omitted by `policy_snapshot`. Add both
   to that producer's existing file list. The representative full ENTRY replay
   and both source-hash/size proofs then pass, preserving the snapshot byte
   bound and sandbox's missing-file rejection. Older snapshots remain missing
   evidence; this does not backfill them or manufacture economic outcomes.

Re-review covers producer -> operating contract -> split/sequential plans ->
request conversion -> SOR preflight -> mocked adapter and original-route
cancel/restart consumers. No new Python module or test file is introduced;
existing runtime, pure market-contract and test owners retain their locations.

## Official reference gate

Upstream HEAD `953e5dbff123f437ab4d11a78a95191a685eb51f`, retrieved
`2026-10-19T17:33:33.495669+09:00`. Inspected:

- `kiwoom/specs.py`
- `kiwoom/core/client.py`
- `kiwoom/_data/kiwoom_api_spec.json`: kt10000 and ka10099/ka10100
- `postman/kiwoom-openapi.postman_collection.json`: PRD and MOCK kt10000

`kiwoom_docs` is absent at this revision. The packaged spec specifies
`POST /api/dostk/ordr`, required `dmst_stex_tp=KRX|NXT|SOR`, quantity in shares,
price in KRW and the existing order-type enum. Core uses a JSON body; Postman
also repeats parameters in the query. That existing representation gap is
preserved, and this change does not alter the JSON envelope, auth/continuation,
response parsing, real/demo separation or API limits. No WebSocket packet,
mapping, subscription or recovery code changes.

The reference does not supply a KRX aftermarket eligibility field through
`nxtEnable`. It remains NXT-specific. Do not derive KRX permission from it.
Reference bytes, retrieval receipt and SHA-256 values are preserved in
`tmp/sor-entry-repair-20261019/official-reference/` in the shared workspace.

## Validation and remaining acceptance

Final targeted regressions: **1,120 passed** across 418 core, 602 consumer,
and 100 complete sizing/replay/original-route tests. This includes real
WATCHING/submit-body tests with a mocked adapter. Repeated exploratory runs
are excluded from this total. Python compile, diff whitespace and print-only
document parser checks passed. Detailed results and log hashes are recorded in
`validation.json`. Raw command logs and the final
validation receipt are in `tmp/sor-entry-repair-20261019/` in the shared
workspace. Tests perform no actual broker/provider calls.

Code validation does not prove deployment, current PID consumption, a natural
SOR order, fill or net profit. At the monitored production snapshot the KRX
eligibility axis was unknown, and exact-date SOR policy consumption was not
proven. This candidate deliberately leaves those conditions blocked. Runtime
acceptance requires the existing current-date KRX source and valid approval
policy to reach their consumers; source/approval artifacts must not be
fabricated to claim submission recovery. `ka10099` alone cannot close that gap.

The repair remains an isolated code candidate. Any later release transition
must follow the existing [runtime release routing](../runtime-release-routing.md)
preflight, including the exact active-policy code handoff and affected native
source contracts before Main is drained. This audit is not that deployment or
PID-consumption receipt.
