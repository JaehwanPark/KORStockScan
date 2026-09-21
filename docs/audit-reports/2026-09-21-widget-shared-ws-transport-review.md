# Widget shared WS transport: first P0/P1 handoff

## Scope and authority

User authorized implementation, repeated review/fixes, commit/push, deployment and startup of the [staged proposal](../proposals/widget-episode-shared-ws-market-data-improvement-plan-2026-09-21.md). Its former document-only statement is historical, not a veto of this approval. First handoff is P0/P1/P4; P2 input selection/58-symbol and research-watch expansion requires P5 comparison acceptance. P3 completed-bar/episode changes are explicitly later work. No extra daemon, database, CLI, policy, subscription, token lifecycle, account/order request or live source selection is introduced here.

Location gate: one small common reader/comparison module belongs in `src/trading/market/shared_ws_snapshot.py`. Existing `market_data_cache` is in-process quote storage, not an on-disk consumer; putting file/process validation there would mix contracts. Existing publisher, three advisory collectors/recorder and tests are extended; no engine-root module is added.

## Official gate and P0 evidence

- Upstream main freshly resolved at `2026-09-21T02:22:43.295586+00:00` to `953e5dbff123f437ab4d11a78a95191a685eb51f`. Inspected complete `kiwoom/realtime/packets.py`, `kiwoom/realtime/schemas.py`, `kiwoom/core/ws_client.py`; packaged `kiwoom/_data/kiwoom_api_spec.json` request/selected response fields for0B/0D/ka10001/ka10004; PRD/MOCK requests in `postman/kiwoom-openapi.postman_collection.json`. Tree confirms no `kiwoom_docs`. Same-session specs/core REST checks retain their unchanged protocol relevance; no transport envelope/parser/FID/REG/REMOVE code is modified.
- Official WS endpoint is `/api/dostk/websocket` on real/demo port10000; LOGIN/PING echo and REG refresh1 retain-existing semantics remain unchanged. The local cap56 from main PID117559 is not an official broker maximum. No additional subscriptions are attempted; expanded cohort capacity remains unverified.
- Read-only current checkpoint: roughly3.5MB, 30 stock rows initially; subsequent snapshot40 exact routes/36 recent0B+0D pairs is a receive census, **not** broker registration acceptance or all-owner capacity. Three actual widget symbols are Samsung005930, Doosan Enerbility034020 and Hanwha Ocean042660. All three currently have their required KRX route; Samsung also has NXT/integrated observations. Doosan000150 is a different symbol, not this widget's input gap.
- Base main release `0d7fed630`, PID117559; three read-only collectors are still pinned to `ffd565c83` (`entry-source-clock-scope-r3-20260917`), PIDs682/665/666. Those three collector source files have no source diff from the pre-change main HEAD; user custody/strategy state is not migrated or rewritten.

| Consumer field | Existing REST | Official WS field | Constraint |
| --- | --- | --- | --- |
| current price | ka10001 cur_prc | 0B FID10 | KRW, signed protocol value normalized by existing parser |
| best ask/bid | ka10004 sel_fpr_bid / buy_fpr_bid | 0D FID41/51 | Exact item/route, positive prices, no crossed book |
| best ask/bid size | ka10004 sel_fpr_req / buy_fpr_req | 0D FID61/71 | Shares, required complete positive depth |
| clocks | REST response received time | Separate0B/0D receive times; optional0B FID20 trade time | No snapshot timestamp substitution, no common exchange sequence claimed |

REST symbol suffix definitions explicitly distinguish raw KRX, `_NX` and `_AL`. Static ka10001 fields, previous-day values, flows and minute bars are **not** replaced by current price. Postman includes query and JSON-body examples; unchanged client uses JSON body. ka10004 bid_req_base_tm is provenance-only; packaged description is not used to invent a fresh quote clock. No WS-derived minute bars are constructed from bounded tails.

## Implementation and review

- Existing atomic publisher adds process generation (PID/start ticks/boot ID), source commit/root, connection epoch, locally sent item registry, local cap and lock duration. Metadata/file I/O occurs outside the receiver lock. Registration state is explicitly not broker ACK; real0B/0D receipt remains separate.
- Reader is bounded to8MiB and one read per collector cycle. It checks original field ages <=20seconds (unchanged consumer limit), same date/session, exact item/route, positive complete fields, process lifetime, publisher/field epoch, and snapshot authority. File rewrite alone cannot renew old field clocks. Source/projection hashes, per-type sequences and optional provider trade-clock provenance are retained. Source absence has no recovery/network side effect.
- Samsung/Doosan/Hanwha keep existing REST prices/BBO and kernels. WS only adds `market_data_transport` comparison evidence. Different values are retained, never averaged or promoted; REST has no common exchange sequence, so even matched fields do not claim the same broker event. Actual source adoption and80% reduction/99% availability are not claimed.
- Per-process, exact consumer/session15-minute counters keep every active comparison including failed REST cycles; at most four windows are retained. Existing minute/state recorder retains the same transport annotation and DATA_WAIT failures. Existing paired replay rejects non-PASS source rows; missing prices/outcomes are not changed to zero. Comparison coverage is separate from adopted-input coverage and economics.
- Review covers producer freeze/atomic publication, standalone reader, stale/future/mixed routes, partial book, duplicate route, connection/producer generation, missing/invalid schema, failed REST denominator and unchanged collector requests. P1 does not use the Samsung display comparison or micro-reversion registration artifact as trading authority. Existing source subscriptions/locks/holdings and the separately approved25-share Samsung custody remain intact.

## Verification and handoff

- First targeted writer/reader/WS/three-collector run:426 tests PASS, including independent-process reader and unchanged REST request sets. Review fixes move cap-file access out of the WS lock, preserve failing comparison denominator, and expose exact rejection causes. Final validation/deployment/actual consumer evidence follow below.
- Existing owner remains `KiwoomCommonHealthOpportunityCostAcceptance0917`; no duplicate OPEN. P5 requires three consecutive15-minute windows and explained exact-route/field differences before P2. Missing/partial/mismatched comparison evidence keeps the current REST input and the source gap visible. No broad report regeneration, external sync, manual broker/provider probe or order is permitted by this diagnostic comparison.
- Final affected writer/reader/WS/three-collector/paired-replay suite:471 PASS; subsequently added exact NXT/integrated-route positives and reran the reader/quote suite:51 PASS. Ruff F/E9, Python compilation, diff whitespace and print-only checklist parser PASS. Existing fork-in-multithreaded-test DeprecationWarning is unchanged. Re-review has no unresolved in-scope P1 finding; P2/P3 and natural acceptance remain open.
- Rollback: restore the saved main release selection to `capacity-legacy-20260921-0d7fed630`, use the guarded restart, and remove only the three newly installed shared-WS P1 collector drop-ins before daemon-reload/restarting those collectors. Existing service drop-ins, trading owners, source history and daily generated data remain untouched. This is a rollback procedure, not an instruction to execute it now.
