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


## Deployment and final verification (08:43 KST)

Code `dfe202068` was pushed on `codex/entry-adverse-al-20260922` and released at `/home/ubuntu/KORStockScan-runtime-releases/entry-adverse-al-20260922-dfe202068`. The source and immutable release each passed706 affected tests. Six backed-up systemd override definitions cover66 loaded consumers: widget trader, three Samsung machines,61 static two-leg machines and the auto-expansion worker. All effective WorkingDirectory/ExecStart paths match this release; systemd unit syntax verification passed. The branch retains the previously reviewed546693088 widget/I/O baseline instead of replacing it with a main-only branch missing those fixes. The current-date checklist was carried from committed2f26ced01 and the workspace's other edits were preserved.

The widget trader restarted08:41:14 as PID32218. Its08:41:25 startup receipt and actual cwd match the new release; a subsequent08:42:53 cycle completed, with no orders in any of the three widget ledgers. Samsung morning started08:41:27 as PID32298 and exited0 at08:41:34. Its terminalNO_TRADE, attempt_consumed, legs, original audit and empty order ownership are unchanged. Normal timing-programme observed_at/tick bookkeeping refreshed during startup; the full state file is therefore not byte-identical. No attempt reset or historical resubmission was made. Future-due midday/afternoon/static and auto-expansion services retain their scheduled startup; their future PID consumption is not claimed. Main selection and PID13962 were preserved.

The detector validates the new widget release binding and Samsung terminal success. Its overall08:42:34 result isFAIL for a separate `sniper_engine` stale/dead thread: main loop alive, sniper thread_alivefalse, heartbeat age1233.9 seconds. That is not a widget source-route verification failure, and overall fleet health is not claimed. This task did not restart the main bot. The main thread health issue remains a distinct operational follow-up.

No unresolved defect remains in this reviewed route adapter. Natural future order/fill/profit acceptance remains separate; the live read-only tape sample still failed its preserved stale depth/trade checks after route resolution. Quiet-market reconnects, extra subscriptions, REST retries, threshold changes and report regeneration were not added or executed.

[Deployment/PID receipt](../../tmp/entry-adverse-al-20260922/deployment-final.json), [release tests](../../tmp/entry-adverse-al-20260922/release-tests.log), [override backups](../../tmp/entry-adverse-al-20260922/deployment-plan.json), [health detail](../../tmp/entry-adverse-al-20260922/health-after.json). Rollback restores the six saved overrides and reloads systemd, then restarts only consumers active at rollback. Preserve completed morning state, future schedules, main selection and policy/order ledgers.
