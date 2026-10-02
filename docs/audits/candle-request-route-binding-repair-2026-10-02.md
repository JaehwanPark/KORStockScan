# Main candle request and exact WS route binding repair (2026-10-02)

## Scope and authority

The user approves implementation, repeated review/fixes, deployment and guarded Main restart. Ownership remains in the existing entry candle producer, canonical snapshot and WATCHING consumers; tests remain in `src/tests`. Current policy/PREOPEN/prepared bytes and independent Widget/Episode pins are preserved. No new module, REST/provider/registration call, replay, threshold or order authority is added.

## Incident and defect

Original incident: `086520`, promotion `ZBPROM-086520-1790900011094-1`, attempt `aims-cb6028c8e84ee8300d6f`, observation `615e853bb507734872454bd4558f3322d498a1fbad13dc86d57def301d58beaa`.

Integrated probe/watch attachment at 09:13:32 precedes a KRX watching recovery registration at 09:13:42. At 09:13:54 price/tape are 145.504ms old, BBO 243.638ms, current-session bars 14, completed bars 13 and decision-window missing bars 0. Candle `rest_request_code_conflict` and `venue_conflict` reject evaluation before provider/order submission. Historical actual supplied REST code was not stored; exact historical reconstruction remains unverified and the original SOURCE_INVALID is preserved.

Fetch resolves a request code, then context construction resolves it again from changing aggregate WS provenance. Concurrent subscriptions or receive-age changes can retarget the second resolution. Async construction also discarded its generation venue. Fixtures reproduce both aggregate route transitions without an API call.

## Official source gate

Current official HEAD/local checkout verified before edits: `953e5dbff123f437ab4d11a78a95191a685eb51f`, during 2026-10-02 09:30-09:50 KST. Inspected `kiwoom/_data/kiwoom_api_spec.json` ka10080 request/response, `kiwoom/specs.py`, `kiwoom/core/client.py`, `kiwoom/realtime/packets.py`, and `postman/kiwoom-openapi.postman_collection.json`. `kiwoom_docs` is absent from this tree.

ka10080 is POST `/api/dostk/chart`: api-id/bearer authorization, optional continuation, stk_cd/tic_scope/upd_stkpc_tp. Plain is KRX, `_NX` NXT, `_AL` SOR; signed KRW prices, share quantities, YYYYMMDDHHmmss time. Production/demo separation, envelopes/parsers/auth/continuation, REG/REMOVE and limits are unchanged. Only existing local source rows are selected.

## Implementation and supplemental review

- Capture chart request code/session/broker route and transport epoch before REST. A reconnect cannot attach the old chart to a new generation.
- Bind Main KRX regular execution-view candles to exact existing 0B/0D item/route/epoch. Another newer aggregate route cannot retarget the chart. Missing/conflicting/malformed rows fail closed.
- Preserve scanner-owned venue in synchronous fetch/build and async generation context.
- Keep actual receive clocks, feature/source/canonical gates and final-submit guards. Neutral holding and other sessions retain their behavior; exact probes keep their narrower registration-bound tick filtering.
- Canonical capture and pipeline fields record resolved/supplied request codes, binding and blockers for future diagnosis.
- Supplemental review fixed epoch timing and prohibited replacing probe-filtered tape with the shared route buffer. Tests cover both transitions, other symbol/item/route, missing rows/depth, stale/future clocks, reconnect/bool/split epoch, metadata mismatch and caller immutability.

## Validation

Initial related tests: 197 PASS. Expanded source/consumer gate: 320 PASS / 10.13s. Final reviewed gate: **522 PASS / 9.10s**, three historical rebound PREOPEN tests deselected only after the untouched selected `1ac3fc80` release reproduced the same three failures (31 PASS / 1.33s). They are not patch regressions; no historical source/policy gate was relaxed. Compile/diff and document parser are checked before publication.

Local processing sample: three runs of 1,000 bindings, median 0.01149ms/binding; no extra source/provider call or budget increase. This is processing overhead, not trading performance.

## Deployment and natural acceptance

Deployment/PID evidence will follow after immutable release validation and native policy-preserving handoff. Natural acceptance requires new-PID exact request/route/epoch captures, unchanged freshness gates, and normal evaluation or honest source exclusion. Past loss is not repaired and missed-upside/net-profit improvement is not established by these tests. The existing 10/1 finalization failure remains separate.
