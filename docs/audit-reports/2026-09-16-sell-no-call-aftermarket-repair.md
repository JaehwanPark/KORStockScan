# After-market SELL and local no-call recovery repair (2026-09-16)

Scope: user-authorized defect repair, review/fix loop, commit/push, common immutable release deployment and graceful main restart. Preserve independent machine pins, owner custody, requested quantities, broker/account/quote/cooldown guards, thresholds and providers. Do not submit a manual SELL or clear ambiguous orders by age or an empty order list.

## Confirmed cause

- TEMC `425040`, record `45050`: `16:01:12.419566` fast-exit claim -> `16:01:12.423952` LOSS exit signal -> `16:01:12.700655` local `order_type_unsupported`, no broker dispatch/order number. The raw event line SHA256 is `207ad487ffd40c2f90eefcf42bdaafbc38e5f545d74dd35ef417448bca717e7f`; a bounded historical window was read, not a full scan of the growing 4GB source.
- The fast exit calls the shared `send_exit_best_ioc` holding-exit wrapper, not `send_smart_sell_order`. The wrapper always requested regular-session best-IOC `16`; after-market preflight prohibits that type. A simulation of market `3` was therefore the wrong call-path reproduction.
- DB/journal custody is written before transport for crash safety. The local preflight response carries a process-local no-call token, but the classifier recognized only `SELL_TIME_BLOCKED`. It classified `ORDER_TYPE_PREFLIGHT_BLOCKED` as ambiguous, retaining `SELL_ORDERED` and retrying reconciliation for a nonexistent order number.

## Repair and safety contract

1. The holding-exit wrapper chooses ordinary best-limit `6` for integrated after-market/close-only/terminal-exit and legacy NXT after-market. Regular-session best-IOC `16` is unchanged. Session transitions/closed sessions remain blocked by normal preflight. Existing-holding context is explicit; quantities/routes/owner context and normal transport remain unchanged.
2. Time, order-preflight and owner-registry local blocks count as no-call only with the exact process-local token, `broker_order_attempted is False` and no order number. A raw dictionary, replaced token, attempted transport or order number cannot grant this disposition. Owner-registry tokens are attached only before the first transport instruction; post-transport registry ambiguity stays blocked.
3. Use the existing fsynced no-order terminal outcome -> exact DB CAS -> exact-generation journal clear. Clear the old reconciliation interlock only after this contract succeeds. Persist/DB/clear failures remain interlocked and restart-recoverable. Local no-call is not logged as a broker rejection.
4. Do not infer observed market-data route from SOR or the clock. The existing receipt regression now tests absent, KRX-only and integrated observed routes separately from preferred clock route and actual execution venue.

## Approved one-generation recovery at deployment

- The user confirmed no actual SELL; the original local preflight event confirms no dispatch. The exact pending generation is `3b66289a035c4c39966e34882f08947c`, context SHA256 `2ba35fc63264fa105477ee56fd7ddc2a285bad6ce508421190aadcf946596331`, original file SHA256 `666be8a2858228bf5284a159ef10ae27ce1fd83444966e6ddd2256a588609be4`.
- Immediately before approved restart, recheck this exact DB ID/code/status/10-share quantity, unchanged journal bytes/generation/context and absence of broker/cancel/terminal evidence in the journal. Back up original bytes. Publish only this generation's no-order outcome through the existing writer; never manually update DB or bulk-remove journals. A changed identity/state/hash aborts the disposition.
- The normal startup consumer must perform its exact terminal recovery. Verify the journal is gone, DB no longer has the orphan `SELL_ORDERED`, current PID/release receipt is exact, and no new missing-original-order retry occurs. A later genuine automated SELL is a separate generation/order; no test or deployment receipt proves fill or net profitability.
- Preserve the prior selected release/selector for rollback; switch only with scheduled wrappers inactive. Independent widget/episode systemd pins are not changed by common main deployment. Actual deployment/PID/natural receipts live in runtime artifacts, not this source-validation document.

## Official reference and validation

Official upstream HEAD `953e5dbff123f437ab4d11a78a95191a685eb51f`, retrieved `2026-09-16T16:34:36+09:00`: inspected `kiwoom/_data/kiwoom_api_spec.json` (`kt10001` request/response), `kiwoom/specs.py`, `kiwoom/core/client.py` and production/demo SELL envelopes in `postman/kiwoom-openapi.postman_collection.json`. `kiwoom_docs/주문.md` is absent (404); no missing protocol semantics are inferred. SELL remains POST `/api/dostk/ordr`, `api-id=kt10001`, the existing headers/body, shared route enum `KRX|NXT|SOR`, positive quantity, normal/best-limit types. No wire/auth/response parser/continuation/transport retry changes or real broker calls were used for tests. [KRX after-market order-type authority](https://regulation.krx.co.kr/contents/RGL/03/03020302/RGL03020302.jsp).

Final workspace regression: `1348 passed` (shared trading utilities, Kiwoom SELL adapter, main lifecycle receipt/custody, market session and full sniper scale-in suite), compile/diff/parser PASS. Covers normal transport once with type `6`, regular IOC preservation, closed/transition guards, token/attempt/order-number tampering, preflight/owner veto, crash recovery from both DB states and leftover reconciliation flags. Self review -> supplemental fixes -> re-review closed with no unresolved in-scope finding. The pandas deprecation warning is unrelated. Natural generation and economics are separate acceptance states.
