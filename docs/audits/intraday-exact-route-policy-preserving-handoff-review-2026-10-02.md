# Intraday exact-route observation repair and policy-preserving handoff (2026-10-02)

## Authority and ownership

The user explicitly requests combining the missing NX observation subscription repair with authorized intraday release application, review/fix/review and graceful Main restart. This follows the prior deployment/restart approval. Startup code lives in `src/engine/automation/intraday_release_handoff.py`; the exact-item transport owner remains the existing WS manager, the bounded worker remains zero-base, and tests remain in `src/tests`. No new engine-root module is added. Independent Widget/Episode pins and all trading policy/threshold/custody guards remain their existing owners.

## Official protocol evidence

Retrieved 2026-10-02 08:23~08:46 KST from the current official [Kiwoom repository](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/tree/953e5dbff123f437ab4d11a78a95191a685eb51f). HEAD/clone SHA `953e5dbff123f437ab4d11a78a95191a685eb51f`. Inspected `kiwoom/realtime/packets.py`, `kiwoom/core/ws_client.py`, `kiwoom/realtime/stream.py`, `kiwoom/specs.py`, `_data/kiwoom_api_spec.json` under `kiwoom` (0B/0D), and `postman/kiwoom-openapi.postman_collection.json`. REG refresh=1 retains existing registrations; REMOVE carries an exact item/types list. Packaged specs document `_NX`/`_AL`, production/demo WS URL/path and REG response versus actual REAL data. Existing local cap and fresh same-epoch route/type gates are unchanged. Current repository has no `kiwoom_docs`; the portal could not be retrieved; Postman has 612 REST entries and no WS entry. No undocumented numeric broker limit, sparse-tape explanation or API outage is inferred.

## Implementation and review

- Add only a missing exact observation item, maintain an item lease per bounded worker, and preserve AL registration and aggregate trading data.
- Serialize REG/REMOVE wire operations. Never use force replacement for the probe. Reused/adopted items cannot be removed by probe cleanup; adoption while REMOVE is in flight serializes additive restoration and invalidates the removed receipt.
- Preserve existing item budget including uncertain sends, keep cleanup custody after an unconfirmed registration, cancel pending probe items on an explicit owner unsubscribe, and drop ephemeral unadopted items at reconnect.
- Keep exact fresh 0B/0D, REST route/receive clocks, machine-only probe and no-order contracts unchanged. One RECHECK shares the lease; late registration cleanup uses that exact token and keeps the bounded slot until completion.
- A separate immutable same-day handoff seals old Main PID/start/root, original succeeded PREOPEN and today's unchanged env/manifest/prepared files. It authorizes only a verified selected new commit. Native bootstrap/custody gates remain mandatory. First launch has a 15-minute bound; only verified new-PID consumption extends reuse to later same-day guarded restart.
- The previous 07:35 date gate remains for ordinary next-day preparation. No today PREOPEN rerun, marker synthesis, policy recalculation, invalid-source promotion or historical failure relabel occurs.

First regression found a missing UUID import and the test hook following the serialized REMOVE implementation; fixed. Subsequent review covered uncertain-send quota and adoption/REMOVE races; supplemental regression added. Workspace runs: 319 PASS for initial seven affected files; 348 PASS for expanded launcher/router/probe set before the final adoption regression. Final combined workspace gate: **434 PASS / 14.25 seconds**, including the adoption race and prepared-generation source-drift tests. Compile, bash syntax, diff whitespace and print-only checklist parser pass; both current stable owners parse exactly once. Actual deployment/PID evidence follows below. This report does not claim natural source repair or economic improvement from tests.

## Deployment and natural acceptance

Pending final gate and native guarded handoff. The selected original Main is `9dcbd482`, PID 2748464. Policy/PREOPEN/prepared bytes and independent owner pins are captured before selection. No changed historical source or successful postclose finalization is claimed. Actual release, restart, PID consumption, daemon observations and new exact-route attempt evidence will be appended with bounded timestamps.
