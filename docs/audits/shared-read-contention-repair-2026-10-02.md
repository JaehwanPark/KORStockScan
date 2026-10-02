# Source read contention repair — 2026-10-02

## Authority and evidence

User approved implementation, repeated review/fix, deployment and startup. Existing utils own the shared read bucket/cache; the existing zero-base probe owns source preparation; scanner emits receipts and monitoring classifies them. No engine-root module is added. Existing policy, quantities, price, broker/account/order guards, provider and independent service pins remain protected.

The bounded 11:57–12:27 log lookup observed 17 deferred admissions, including 11 probe chart/tick admissions. Recent four discovery cycles reported 13 successful pages each (activity 1+1, gainers 6+5). These are physical admission/page diagnostics, not trade counts or failure rates without a successful-request denominator. Exact 103590 claim 9 at 11:55:25 had ready AL WS (0B 6/0D 16), but ka10080 admission was deferred before HTTP. Original source hash `2b7355b1d8c180cb7efa8586de2e4a94dc664306e67a1587c6a575fd1837d209` stays a gap.

## Official reference gate

Official `Kiwoom-Securities/Kiwoom-REST-API` HEAD remains `953e5dbff123f437ab4d11a78a95191a685eb51f`; retrieval time and local copies are in `tmp/shared-read-repair-20261002/official-reference.json`. Inspected `kiwoom/specs.py`, `kiwoom/core/client.py`, `kiwoom/_data/kiwoom_api_spec.json` and Postman PRD/MOCK for ka10003/ka10080/ka10023/ka10027. Verified POST paths, api-id/Bearer/JSON fields, exact suffix, signed numeric chart/trade values, continuation and business errors. `kiwoom_docs` is absent in this revision. Existing local request/parser/REG/FID/auth/order contracts are unchanged; no real API calls were made for validation.

## Implementation and operating rules

1. Empty/invalid chart returns before tick REST. Preserve the original gap reason; no source synthesis or backfill.
2. After the chart read, refresh exact WS and reuse the existing machine feature selection rule. Only `ws_exact_route` with trusted pressure and valid event age skips REST ticks. Untrusted/short/stale sources retain existing fallback or fail closed. Recheck before machine evaluation; a changed source produces a gap.
3. Shared source-only FIFO prevents waiting requests being overtaken by a newly queued continuation page. Original 4/5 slots, wait/retry limits, cooldown, per-TR mock scope and reserved runtime slot remain. Timed-out/crashed tickets expire; malformed queues block source-only, not required reads. Five concurrent probes and 200-row panels remain.
4. Successful exact source-only ka10080 requests may join across processes. Original receive clock survives; TTL cannot renew. Only default-coordinator, same scope/class/bounds requests participate. Cache is 512 slots with complete chart/business/HTTP success checks, atomic 0600 writes and bounded follower wait. Slot collisions bypass reuse; failed owner/follower timeout never starts another transport. Account/order/auth and required/critical calls remain independent.
5. Scanner records tick source/selection reason; monitor preserves known candle gaps rather than unclassified. Lossless sentinel stages are unchanged, so no historical cache rebuild is needed.

Independent older pins may still bypass FIFO while sharing the unchanged hard bucket. FIFO acceptance is for participants consuming this release; no global priority guarantee is claimed for older code. Rollback selects the prior release through the same policy-preserving handoff. Extra optional state fields are retained by older readers; locks release on process exit and tickets expire. Historical gaps and policy economics remain separate.

## Review and validation

Review fixed follower retry amplification, the native chart metadata contract (HTTP/business success instead of a panel-only status field), and an additional exact WS refresh expectation. Targeted source/cache/feature/queue/monitor gate: 320 PASS/8.36s. Native machine consumer gate: 3 PASS/1.67s. Samples prove one chart plus trusted WS needs one REST read instead of chart+tick; a failed chart also saves the followup tick. Two processes joining a successful chart make one physical mocked request. These are fixture request savings, not measured live latency, improved decision quality or profit. No packages, provider, account/order calls or historical report regeneration are used.

Deployment/PID and final validation evidence are appended after guarded startup. Natural acceptance requires current PID tick-selection receipts and exact source/decision hashes; absence is not_observed. Causal before/after admission reduction requires comparable successful-request denominators and workload, not raw deferred counts alone.

Final re-review also prevents token replacement responses from entering the old shared scope, prevents a source waiter from rejoining after an overslept deadline, and makes optional cache I/O failures use normal admission. Final disjoint gates: source/cache/feature/queue/scanner/monitor **471 PASS/10.68s**, market/candle/order/startup/router/bootstrap **248 PASS/3.88s**, native machine **3 PASS/1.67s**; total **722 PASS**. Compile, whitespace and print-only parser PASS; one current checklist owner. In-scope unresolved code findings: 0.
