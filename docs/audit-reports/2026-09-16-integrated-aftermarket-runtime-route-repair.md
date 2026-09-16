# Integrated aftermarket runtime market-data route repair (2026-09-16)

## Cause and scope

The reported `196` `integrated_market_data_route_required` decisions describe an integrated aftermarket cohort receiving exact plain KRX 0B/0D receipts. They are not AI vetoes or threshold defects. The supplied count is incident context, not a recomputed current-generation count.

The default WS registration used `get_effective_kiwoom_code`, whose `is_nxt=false` branch returns plain KRX. It did not consult the integrated aftermarket session owner. Existing registrations also survived session transition/reconnect without ensuring a trading-owned AL source. An AL observation-only registration is not equivalent to the runtime's trading frame.

Only the existing `kiwoom_websocket.py` registration, reconnect and receive paths are repaired. The common-data-health proposal is reference context; its broader quiet-tape framework is not implemented here. No new modules, processes, services, schedules, policy families or report producers are introduced.

## Current official Kiwoom reference gate

Retrieved and inspected at `2026-09-16T18:48:07+09:00`, official upstream HEAD is [`953e5dbff123f437ab4d11a78a95191a685eb51f`](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/tree/953e5dbff123f437ab4d11a78a95191a685eb51f). Inspected `kiwoom/specs.py`, `kiwoom/_data/kiwoom_api_spec.json` entries for 0B/0D, `kiwoom/realtime/{packets,events,stream,schemas}.py`, `kiwoom/core/{client,ws_client}.py` and `postman/kiwoom-openapi.postman_collection.json`. `kiwoom_docs` is absent from this current upstream tree; attempts to retrieve the portal's realtime pages through browsing did not succeed. The packaged protocol spec explicitly supplies the relevant request fields and suffixes; no undefined venue/FID semantics are inferred.

The packaged 0B/0D spec and packet builder agree: production/mock WebSocket domains are separate, path is `/api/dostk/websocket`, REG uses `trnm`, `grp_no`, `refresh` and `data.item/type`; `refresh=1` retains existing items/types. Plain code is KRX, `_NX` is NXT and `_AL` is SOR. AL does not prove an individual event's execution venue. LOGIN, URLs, authentication, FID parsing, account/order calls and limits are not modified. Existing item budgets and source-quality guards remain authoritative.

## Repair and review supplements

1. Unqualified runtime registration consults the existing session owner. Integrated aftermarket, close-only and terminal-exit regimes request AL independently of `is_nxt`; regular and explicit-suffix behavior remains separate.
2. Successful default runtime registration tracks its implicit route intent. Explicit NX/AL requests and observation-only owners are not silently migrated. Reconnect preserves that original intent.
3. The existing WS loop schedules at most one bounded asynchronous route reconciliation, checked every 30 seconds. Missing AL is added with additive REG and only 0B/0D, preserving program subscriptions. It does not block `recv` while REG batches yield/sleep, and is bound to the original connection/transport epoch. Existing item budget failures remain source gaps.
4. A successful runtime AL registration separates other exact items from the canonical runtime frame. Their raw receipts remain in the existing route-isolated store and observer path; they cannot overwrite the integrated runtime BBO/tape. Top-of-book cache references use the exact received item, not the canonical symbol's unrelated cache.
5. Existing KRX receipts are not relabeled or made fresh. Registration alone does not supply a trade, quote or actual execution venue. Both fresh AL type receipts are still required by the unchanged consumer contract; actual event venue remains unknown.

Re-review covers producers, route-isolated consumers, reconnect, cancellation, budget, duplicate reconciliation, provenance and order authority. No guard, price/sizing, quantity, provider, threshold, custody, manual exclusion or bot-state rule is relaxed. Tests freeze legacy registration cases to their intended regular-session context and separately exercise actual session boundaries.

## Validation, deployment and rollback

Final workspace validation: affected route/source suites plus full sniper regression passed `1480` tests (`403` route/source and `1077` sniper). Python compile, Black, shell syntax, print-only checklist parser and diff checks passed. Re-review has no unresolved in-scope finding. Immutable release validation, deployment/PID and natural acceptance are recorded separately after this code commit; tests alone do not attest deployment.

Use a clean immutable managed release, back up the common selector, retain previous release `sell-no-call-aftermarket-20260916-0b712b54`, and use the approved graceful main restart. Do not switch an active postclose wrapper. The repaired widget evaluation pin stays on `0b712b54`: its three analysis/policy modules are unchanged by this WS-source repair. Other independent unit pins and schedules remain unchanged.

Natural acceptance belongs to `[IntegratedAftermarketRouteRepair0916]` in the [daily checklist](../checklists/2026-09-16-stage2-todo-checklist.md): exact new PID/source identity, actual AL REG, fresh exact AL 0B/0D, unchanged fail-closed for plain/missing/stale/cross-epoch sources, and new-generation source-valid decisions. Historical 196 rows remain historical; submit/fill and cost-adjusted economics are separate.
