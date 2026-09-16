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

## Installed release and bounded natural evidence (18:56 KST)

- Code commit `98d1b75e925efb66046558c97ffddd8c972eaffd` is pushed. The exact immutable release also passed `1480` affected tests, with clean source and canonical shared mounts. Tracked data/docs were preserved in the release's `.shared_mount_backups`, not deleted.
- New main PID `3940280`, receipt at `18:54:51.654898 KST`, consumes `integrated-runtime-route-20260916-98d1b75e`; actual cwd/env Git/source-root match and source dirty is false. Old PID `3779784` exited. Runtime env verification is PASS with unverified selected families 0 and dated override failures 0; Samsung morning handoff is not required. Common cron 9 routes pass; widget collector/trader PIDs `3654913`/`3654984` and the 20:10 evaluation pin/schedule are unchanged.
- Before restart, bounded native log at 18:54:40 shows default runtime `086670` and `482630` registered as plain codes. New-generation REG at 18:55:43 sends `086670_AL` and `482630_AL`, preserving additive semantics and the item budget.
- Native snapshot generated 18:56:37 has new-generation exact AL 0B/0D. A read-only call to the unchanged per-type provenance/venue-consistency consumer at actual read time passes the route axis for `005930`, `178320`, `000660` and `010170` (four symbols, no blockers). Per-type source ages are retained in the [deployment receipt](../../data/runtime/integrated_aftermarket_runtime_route_repair_2026-09-16.json). This is not a claim that the stricter executable quote TTL, full source setup, machine ENTER, submit/fill or economics passed.
- New-generation complete machine-funnel acceptance remains waiting; the bounded 1 MiB AI trace tail still ended at pre-restart 18:54:48 when sampled. Do not count that historical tail or the reported 196 rows as new generation. Large/growing traces are not fully scanned.

The review gate influenced connection/epoch binding, nonblocking receive scheduling, program-subscription preservation and exact-item cache isolation. No unresolved finding remains in this repair scope. The remaining natural owner is intentionally OPEN, not a deployment failure or a fabricated economic success.
