# Widget and episode integrated WS entry-flow route repair

Owner: current2026-09-22 `DirectFamilyPreopenPolicyHandoff` for the Samsung incident handoff. User explicitly approved implementation, repeated review/fixes, commit/push, deployment and startup. The repair concerns the common existing widget/episode adverse-flow guard; main AI route binding is unchanged.

## Cause and implementation

The Samsung morning08:08 attempt used broker routeNXT, which the guard mapped directly to005930_NX. The shared checkpoint contained005930_AL. Both legs therefore endedSKIP_SOURCE_UNAVAILABLE/exact_route_missing_or_duplicate and the existing attempt becameNO_TRADE without a submitted order.

The existing market module now provides a widget/episode input adapter. It selects the same symbol's received integrated source while preserving the broker route in the policy scope, owner identity and gateway call. The receipt records both order_route and market_data_route. With no integrated receipt, the existing native exact-route path remains available. A partial, duplicate, conflicted or stale integrated source cannot fall back to native data. Both prepare and final pre-transport checks use the adapter; original timestamps, epoch, rolling-window continuity, adverse-flow conditions, quote age, owner deadline, policy pin and terminal identity checks remain unchanged. No new WS subscription, REST request, synthetic bar/volume, API packet change or threshold adjustment was added.

## Review and evidence

Self-review found that one completeAL route plus a partial duplicate could otherwise evade the existing full-match count; the adapter now rejects multipleAL-bearing routes before evaluation. Tests coverNXT/KRX/SOR orders, another symbol, native-only sources, incomplete/duplicate/stale/epoch/conflictingAL with a valid native source, NXT prepare-to-final binding, late final corruption, and existing real owner loops with native and integrated tapes. Existing custody, two-leg quantities, cancellation, policy revocation and no-duplicate-terminal behavior remain covered.

The affected suite passed706 tests. Initial isolated-worktree failures were absent historical fixtures and report-root containment; mounting the existing canonical report root and historical candidate fixtures resolved them without changing their contracts. Python compile and diff checks passed. The actual local checkpoint comparison changed from exact_route_missing_or_duplicate to the unchanged depth/trade age checks; it proves source selection repair, not that every live input is currently executable. Quiet pre/aftermarket alone triggers no new recovery or subscription here.

The original08:08 NO_TRADE/attempt_consumed state must remain terminal. This repair does not authorize resetting it or resubmitting that identity. Future-due episode timers retain their normal clocks. New runtime source must be verified for each affected consumer; a main restart is not needed.

## Official reference

Official upstream `953e5dbff123f437ab4d11a78a95191a685eb51f` was retrieved at `2026-09-22T08:30:31.192646+09:00`. Inspected `kiwoom/specs.py`, `kiwoom/core/ws_client.py`, `kiwoom/realtime/packets.py`, `kiwoom/realtime/schemas.py`, packaged0B/0D request/response specification, and Postman collection. `kiwoom_docs` is absent from this revision. The [official packaged spec](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/blob/953e5dbff123f437ab4d11a78a95191a685eb51f/kiwoom/_data/kiwoom_api_spec.json) distinguishes nativeNXT `_NX` and integratedSOR `_AL` items. This local consumer repair preserves those labels; it does not infer a native execution venue from integrated flow or change protocol/FID/auth/order envelopes.

[Tests](../../tmp/entry-adverse-al-20260922/validated-tests.log), [read-only frozen checkpoint comparison](../../tmp/entry-adverse-al-20260922/local-source-comparison.json), and [official retrieval receipt](../../tmp/entry-adverse-al-20260922/upstream.json) own validation evidence. Deployment receipts follow after completion.
