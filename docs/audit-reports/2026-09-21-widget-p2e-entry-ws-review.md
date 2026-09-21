# Widget/episode P2E entry market-data review — 2026-09-21

Owner: [WS plan §3.4–3.5](../proposals/widget-episode-shared-ws-market-data-improvement-plan-2026-09-21.md), checklist `KiwoomCommonHealthOpportunityCostAcceptance0917`. User requested execution, with deployment/restart authorization retained. Main decision/threshold work is separate.

## Problem and implementation

The nine unsent attempts are [frozen causal evidence](../../tmp/widget-episode-nine-block-causal-check-20260921.json), not nine independent opportunities. WS adverse-flow approval preceded sequential REST liquidity/velocity reads; three deadline rejects completed REST after the 6.5-second signal lifetime. Samsung morning additionally terminalized a nonterminal WAIT on EntryNotSent.

- `src/trading/market/entry_ws_snapshot.py` owns the exact-route market-data adapter; no new engine-root module, collector, scheduler, DB or broker request. Five existing gateways select it with `KORSTOCKSCAN_ENTRY_MARKET_DATA_SOURCE=ws`; absent/`rest` preserves legacy REST, invalid values fail closed. Optional `KORSTOCKSCAN_ENTRY_WS_ITEMS` pins the rollout to exact items; unselected items retain REST, malformed lists fail closed.
- WS mode performs no REST recovery because existing helpers cannot bound complete admission/retry time to the remaining entry lifetime. Missing/stale data remains explicit source failure; no hidden REST retry, authority widening, forced signal or expired-signal resurrection. A future bounded recovery adapter requires its own total-time proof before activation.
- Preserve existing quantity/depth/volume floors, 2-second liquidity freshness, 10-print/20-second velocity span and 5-second latest-print age, independent 1.5-second adverse-flow freshness and 6.5-second lifetime. Regular KRX widget input already maps to SOR `_AL` in the existing owner contract; preserve that alias, never substitute `_AL` for `_NX`.
- Preserve original receive/provider clocks, exact route/type, live producer generation, connection epoch, local contiguous sequence and cumulative-volume order. Local sequence does not attest exchange completeness. Full-file parse reuse keys path/inode/stat/PID generation, with source-age/liveness revalidation on every consumption.
- Existing WS receiver retains FID13 cumulative volume, but the cross-process projection omitted it. One additive writer field now preserves `cum_volume` without inventing missing values; missing/duplicate cumulative volume prevents velocity use. No REG/REMOVE/authentication/order wire changes.
- Existing guard DTOs carry explicit WS provenance. Restore it through delayed-entry state coercion; source-specific event contracts never label WS as a REST receipt. Widget startup verification includes the new source selector.
- Samsung morning mirrors the regular machine: after exact unsent intent release, nonterminal WAIT returns to PLANNED with unchanged identity/t0/deadline. Terminal/ambiguous/sent states and historical ledger rows remain unchanged.

## Review and validation

Official reference: [retrieval receipt](../../tmp/widget-p2e-20260921/official-reference.json), upstream `953e5dbff123f437ab4d11a78a95191a685eb51f`. Inspected packaged specs for 0B/0D/ka10003/ka10004, `kiwoom/specs.py`, `kiwoom/realtime/{schemas,packets}.py`, `kiwoom/core/{ws_client,client}.py`, PRD/MOCK Postman envelopes. `kiwoom_docs` is absent. 0B FID20 is HHmmss, FID15 signed trade quantity, FID13 cumulative shares; 0D FID41/51 prices and61/71 quantities. Existing normalized units/signs and original route evidence are retained; no examples were executed as orders.

Review fixes: initial route fixture incorrectly treated regular KRX as dedicated KRX despite existing SOR alias; corrected without changing the owner mapping. Added cumulative-volume provenance instead of weakening the REST-equivalent check. Repaired delayed-anchor serialization and malformed injected numeric/provenance rejection. Source gaps remain blocked; source validation is not economic acceptance.

- [Full affected owner tests](../../tmp/widget-p2e-20260921/tests-final.log): 748 PASS before final serialization/invalid-input additions.
- [Serialization follow-up](../../tmp/widget-p2e-20260921/tests-roundtrip.log): 70 PASS; [final affected regression run](../../tmp/widget-p2e-20260921/tests-reviewed.log) owns the last changes.
- Existing post-prepare/source-loss/deadline/save-latency/mock-transport tests, five-gateway zero-REST tests, same-identity retry/reload/no-duplicate tests and writer cumulative-volume tests are included. No broker/provider calls or real-order tests.
- Previous unshipped shared-reader fixes (idempotent comparison count, cross-scope clocks, registration shape, suffix conflict) are reviewed/reused with their existing tests; unrelated main working-tree changes are excluded from release.

## Deployment and natural acceptance

Pending at review: immutable release validation, producer field consumption, scoped consumer/source selection, state preservation and release/PID receipts. P1's 14:00–14:45 raw observations must be reconciled before producer/collector restart; old v3 aggregate alone is insufficient. New-generation P2E source windows and actual natural submit-path evidence remain separately owned by the checklist. No historic opportunity is replayed and no order is created by this review.

Rollback: restore recorded per-unit configuration/source selector and previous immutable main selection using the guarded restart path. Do not restore old position snapshots or erase WAIT/terminal/order identities. Samsung manual sale0027855 and remaining0 custody must survive. An old release may ignore the additional market-data field; delayed-source metadata must not be relabeled as REST.
