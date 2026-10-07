# Alteogen registered reversal source review — 2026-10-07

## Exact alert and decision

The user's source-only alert identifies Alteogen (`196170`), integrated KRX/NXT route, native error `reversal_signal_generation_changed`. Exact trace: 2026-10-07 14:10:18.488641 KST, evaluation `aims-6c9388e9a7d451bbb11c`, trace `aidt-ed0fb527072e493a9b1fcfbbf5447b53`.

- Requested family and supplied claim generation both equal `eb10bbcce0a53a40186f682b028c75883edc140636f71bd6a879065c9d9729ca`.
- Native registration is absent at validation. Stored generation, snapshot, scope and signal age are null. This native error is also raised for an absent claim, so it does not establish an actual policy generation change.
- Tick source has ten trusted ticks with positive quantity provenance. Current price/tape age is 1,093.887ms and BBO age 484.593ms, all marked fresh in the exact preflight. There is no API outage evidence in this attempt.
- Provider and actual order calls are false. This is one rejected pre-assessment attempt, not a failed order or proven missed winning entry.
- Registration deletion time/cause and original snapshot cannot be recovered from this trace. Raw market replay has a different collector identity and cannot replace a missing live registration. Preserve this historical row as an unresolved source gap; do not synthesize its snapshot, signal age or a WIN/BLOCK policy label.

At inspection, the moving latest monitor had advanced to another 14:22 HPSP attempt. Freeze the exact Alteogen trace independently; absence from a later recent window is not historical repair.

## Source repair and authority

Existing owners: `DirectFamilySourceRepairMainMechanisticEntry` and `SemanticMonitorProducerConsumerRefresh1007`. The current request authorizes bounded source repairs; earlier explicit code review/integrated deployment/restart approval persists. No threshold, prompt, provider, native freshness TTL, broker, order, quantity, cap or custody guard changes are introduced.

1. Wrap the unchanged native claim registration in the existing source-diagnostics module. Copy registered token/generation/scope/snapshot with claim/observation clocks under the same ingestion lock. Attach a hashed source receipt to the returned claim, without modifying native state, token or snapshot. No disk/API work occurs under this lock.
2. Both WATCHING admission and the existing AI-engine fallback use this wrapper. Existing native validation and exception remain identical. A telemetry serialization failure leaves admission unchanged and reports unobservable source metadata.
3. Rejection receipt v3 retains supplied snapshot, original-registration proof, active generation and whether native registration still exists. A missing current registry is not filled with a fabricated current snapshot; original `snapshot` and `stored_generation` remain null.
4. The report consumer may classify a registered claim as normal expiry only with exact proof/hash/token/snapshot, symbol/item/market/day, unchanged active generation, valid registration time, age above five seconds, fresh intact native route/epoch/sequence/path and matching attempt/bundle/trace. Unexplained disappearance, generation change, tampering, missing source or unexpired loss remains a source issue. v1/v2 historical receipts retain their original checks.

Implementation lives in existing source/runtime/monitor owners. Research kernel and branch modules are unchanged. This is observation repair, not an entry-policy promotion.

## Review and validation

- Registration identity and native admission/guard invariance, native cleanup expiry, missing/tampered registration, different active generation/snapshot/symbol/session/day/clock, unexpired disappearance and invalid market source were reviewed and tested.
- Native trace projection preserves v1/v2/v3 source receipts. Original rejected error remains `reversal_signal_generation_changed`; only verified report attribution distinguishes expiry.
- Seven targeted pytest files: **441 PASS**. Four changed Python modules compile; `git diff --check` and document print-only parser are required before release selection.
- Evidence: `tmp/alteogen-generation-source-review-20261007/`, including exact-alert source, frozen generation rejection traces and regression logs.

## Deployment acceptance

Apply a reviewed immutable source-only release using native same-day handoff. Preserve original PREOPEN/current checklist/postclose sources and 186 episode pins; reissue only identical machine/auxiliary cells and research contract hashes for the execution commit. Verify actual new PID, source registration/rejection capture and direct report consumer. The original 14:10 Alteogen gap remains unresolved even if future recent-window alerts recover.
