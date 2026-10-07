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

## Applied release and actual consumption

- Workspace and immutable release both passed 441 tests; compile, diff and print-only parser passed. Execution release: `/home/ubuntu/KORStockScan-runtime-releases/reversal-registration-20261007-v1`, commit `2950f674c371c0990025530aab25a7428855ebae`.
- An initial restart request overlapped the native selection lock and was rejected by the router (`runtime_release_transition_in_progress`); no restart occurred from that attempt. After prepared verification completed, the normal restart succeeded at 14:39:36 KST: old PID 896349 exited, new PID 918591/start ticks `97240815` is the sole Main process. Both attempt logs are preserved.
- Native bootstrap, intraday handoff, prepared and release-set validation passed. Ten protected PREOPEN/checklist/postclose/log files retain exact SHA; all 186 independent episode policy pins passed.
- New execution metadata uses bundle `6b615c1b1dc97682b097a4e6781d407e17d523317acb83ee82f1d2affa4b90cf`, family `b301a104a2392d19029f97e95052758cc3d69ee5ade1710fccbfde0a27ced2f8`. Machine/auxiliary cells, label and research kernel/branch/input contract hashes are identical to the previous active policy.
- Actual new-PID policy consumption was recorded at **14:42:12.779059 KST**. Shared WS producer is PID 918591 and all fixed-watch subscriptions receive data. Natural health from the new release shows process/auth/log/resource/lock PASS; genuine historical late completion and independent episode source warnings remain.
- At 14:45:46 KST, all five fixed-watch symbols (`005930`, `034020`, `403870`, `196170`, `036930`) have new-PID machine captures (1 RECHECK, 9 BLOCK), live events and numeric volume ratios. Shared WS snapshot age is 0.42 seconds. Natural registered-claim rejection v3 is not yet observed in the bounded trace window. Registration-after-cleanup attribution must be confirmed by a future natural exact receipt; replay tests do not replace that receipt.
- The 14:10 Alteogen historical source gap is unchanged. The latest rolling monitor reports recovered because the old event left its window; this is not recovery of its missing original registration.
- Final read-only closure at 14:46:22 KST reconfirmed selected commit, actual PID/cwd, native policy consumption and current-bundle captures. The 14:45:41 natural health report has process/auth/log/resource/lock PASS; independent episode-source and historical late-cron warnings remain. No manual provider call, forced rejection or order was used for acceptance.
- Final evidence: `tmp/alteogen-generation-source-review-20261007/final-closure.json`, with hashes of the exact alert, deployment verification, PID consumption, natural captures, rejected-receipt inspection and both regression logs. Code/deployment closure is complete; historical source reconstruction remains impossible and natural v3 rejection attribution remains unobserved.
