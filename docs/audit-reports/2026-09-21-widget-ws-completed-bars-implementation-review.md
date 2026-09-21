# Widget / episode AL completed-bar implementation review

Owner: `KiwoomCommonHealthOpportunityCostAcceptance0917`. Scope: [P3 connection contract](../proposals/widget-episode-shared-ws-market-data-improvement-plan-2026-09-21.md#331-p3-연결-확정-원천-상태분리와-단일-완료-분봉-발행). User authorized implementation, repeated review/fixes and deployment/restart. Source projection, consumer selection, natural acceptance and actual orders/economics are distinct.

## Implementation and review corrections

- Existing durable canonical journal writer owns the new `scalping/micro_reversion/completed_bars.py` projection. No extra WS client/service, callback file I/O, raw recapture or source sequence invention. Atomic per-date/AL-item/session checkpoints retain original clocks, observer epoch, explicitly bound transport epoch, process generation, source commit, revision/hash and durable journal byte cursor.
- First/reconnect partial minutes, missing raw FID13/15, local sequence gaps, AL cumulative/print inconsistencies, late revisions and actual capture loss are excluded. Watermark requires subsequent source event time plus the existing one-second allowance; wall time alone never finalizes a stopped stream. No-print minutes are absent, never synthetic OHLCV. KRX/NXT versus AL price/volume equality is not a promotion gate.
- Projection exceptions do not undo successful raw persistence. Optional projection configuration cannot stop raw capture. Publication happens on sealing, source/generation change or invalidation rather than every pending price change. Bounded checkpoint restore preserves sealed historical provenance and excludes the new partial minute; no full-session replay runs.
- Timestamp rejections are bounded by item, so a rejected print for another identifiable item does not poison this item's bars. Unknown source/worker/writer loss retains conservative generation barriers. Pre-existing historical loss is not reconstructed from the diagnostic tail.
- Common reader validates live producer/process, current observer-to-transport binding, exact date/AL/session, content hash, causal availability and OHLCV. Historical completed bars have no 20-second quote TTL. Live quote/order guards remain unchanged. Each read checks the current revision; collector/episode minute caches cannot hide a late invalidation.
- Existing five widget collectors and four episode gateways use the same adapter and their existing bar parser/signal kernels. REST and WS retain separate source/adjustment namespaces. The regular machine records actual bar provenance. Existing widget policy minimum history and regular episode lookback govern cutover; bootstrap/gap seed and raw WS histories are homogeneous, never spliced across an unverified adjustment boundary.
- Bootstrap/identified-gap `ka10080` requests use the existing client and admission policy. Filesystem `flock` shares one date/item/session/adjustment admission lease across processes, and each missing-range result is hash bound. Contenders return wait; failed/crashed attempts retain 60-second retry backoff. Original receive/availability clocks survive reuse. Quiet history itself requests no REST refresh; missing current order freshness still blocks through the existing guard.
- Same-generation quiet pre/aftermarket subscriptions do not repeat age-only persistent REG/REMOVE. Missing type/route, actual disconnect or new generation retains restoration. Successful REMOVE invalidates local sent-epoch/type receipts. Observation-only AL demotion cannot implicitly promote itself back into runtime ownership.
- Failure attribution clears previous-symbol request receipts and preserves controlled WS/bar failure reasons. Both 0B and 0D clock/epoch facts are reported separately. No age-based recovery permission is inferred from those facts.

## Official reference and validation evidence

Official repository revision: `953e5dbff123f437ab4d11a78a95191a685eb51f`, retrieved `2026-09-21T16:52:42.306079+09:00`. [Exact paths, hashes and retrieval receipt](../../tmp/widget-p3-impl-20260921/official-receipt.json): `kiwoom/_data/kiwoom_api_spec.json`, realtime packets/schemas, core WS/REST clients, specs and Postman. `kiwoom_docs` was absent at that revision. Inspected ka10080 one-minute/adjustment/item semantics, 0B FID10/13/15/20, 0D cumulative volume and REG/REMOVE retention semantics. No sample order was executed.

Tests include durable writer -> atomic file -> independent process reader, all four episode adapters with REST forbidden, widget adapter/provenance, initial/reconnect partial, quiet tape, same-minute invalidation, actual loss, duplicate/late events, checkpoint restart, isolated projection failure, another-symbol rejection isolation, process-shared seed contention/backoff and history-floor cutover. Callback preflight: [source-bound measured receipt](2026-09-21-widget-ws-completed-bars-latency-validation.json.txt), 15,000 measured callbacks with unchanged 1ms/2ms guards. [Validation command](../../tmp/widget-p3-impl-20260921/validate.sh).

Review found and corrected an old storage-maintenance pin dependency omitted from the new benchmark receipt; the prior reviewed hash was verified unchanged against selected parent `90dd032e3`, rather than widening the frozen runtime guard. The first synthetic projection was relocated to [isolated test evidence](../../tmp/widget-p3-impl-20260921/initial-synthetic-projection/); custom temporary journal roots now keep projections inside that root. Synthetic evidence is not natural market evidence.

## Operating rollout and rollback

| Setting | Role / default |
| --- | --- |
| `KORSTOCKSCAN_WS_COMPLETED_BARS_PUBLISH` | Optional source projection; launcher default `1`, explicit `0` disables it |
| `KORSTOCKSCAN_WS_COMPLETED_BAR_SYMBOLS` | Publisher allowlist: `005930,034020,042660,006800,010140,080220`; no additional registrations |
| `KORSTOCKSCAN_WIDGET_BAR_SOURCE` / `KORSTOCKSCAN_EPISODE_BAR_SOURCE` | Independent consumer source, default `rest`; `ws` requires a valid explicit allowlist |
| `KORSTOCKSCAN_WIDGET_BAR_WS_SYMBOLS` / `KORSTOCKSCAN_EPISODE_BAR_WS_SYMBOLS` | Exact six-digit consumer cohort; not inferred from registration or quote source |

Preserve the latest selected main release as parent, including concurrent entry-clock/input repairs. Use immutable source validation and selection compare-and-swap before any restart. Bind only the three basic collectors and existing symbol observer; the research universe and ended episodes are not restarted or replayed. First deploy publisher plus reader code; consumer selection requires exact natural source/required-lookback evidence. No order, custody, balance, provider, threshold, cap or source freshness relaxation is included.

Rollback consumer bar source to its prior `rest` setting independently of quote rollout. Publisher may be disabled without removing raw canonical journals. Release rollback must preserve successor changes; use the saved selection/drop-in receipts rather than resetting the workspace. Natural acceptance remains three full 15-minute windows within one producer generation/cohort/session, actual consumer receipts and measured primary bar REST count. Missing evidence, source gaps, real submissions and net-of-cost outcomes are not converted into PASS by unit tests.

## Deployment and natural receipt

Pending exact immutable validation and authorized selection at this draft point. This paragraph is replaced with actual release/PID and bounded natural evidence after deployment.
