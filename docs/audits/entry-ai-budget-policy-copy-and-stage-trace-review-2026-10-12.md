# Entry AI preparation and response validation review — 2026-10-12

## Scope and causal evidence

User authorized performance repair, code review, deployment and restart. The original five-second signal deadline, native freshness/claim/policy/source checks, provider/model selection, durable outbox, custody and broker/quantity/order guards remain unchanged. This is a runtime implementation repair, not policy tuning or economic approval.

The three Doosan requests at 08:35:01/09/13 were joined by exact request ID to their machine observation and async lifecycle. Their recorded policy selection durations were 301.126/74.941/74.982 ms. Queue waits were 16.449/16.833/17.072 ms and preparation-service durations 162.572/31.901/157.918 ms. Signal origin to dispatch was approximately 3.20/2.84/1.45 s; the dispatch event's emitted timestamp is not a queue-start clock, so this interval does not establish a single internal cause. HTTP lock waits were zero; no authentication failure is inferred. Raw records remain intact.

Profiling the actual validated 3,067,675-byte policy showed repeated owned copies dominating warm reads. Both prompt resolution and response composition use the native loader. The repair materializes normalized frozen containers using scalar fast paths, while preserving full content, mutable consumer ownership, alias/cycle memo semantics and unknown-object deepcopy protocols. The original immutable cache and all dependency, atomic-replacement, symlink, activation-time and generation checks remain in place.

The final trace now retains the existing input preparation stages and final-refresh/revalidation durations under `transport_timing` with the exact evaluation attempt and original deadline. This adds small measurements to the existing append-only trace; it creates no comparison ledger or provider request. It does not invent timings for historical uninstrumented work or transport completion.

## Validation and performance boundary

Targeted suite: native policy/cache, live resolver, auxiliary readiness, AI transport, trace and v6 policy tests. Final counts and immutable-release checks are recorded in `tmp/entry-ai-budget-repair-20261012/completion.json` when deployment closes. Python compile and `git diff --check` are required.

Three alternating baseline/candidate trials each retain the same validated policy, with 20 attempts and three complete owned copies per attempt. SHA/content parity and sibling/cache mutation isolation pass. Copy p95: baseline 171.644/175.813/178.106 ms; candidate 96.563/97.992/98.112 ms (about 44% lower). This isolated measurement excludes provider and broker calls. It does not establish end-to-end deadline compliance or replace the separate full Main/postclose P9 performance acceptance.

## Deployment and rollback

Use the existing approved immutable intraday policy-preserving release handoff. Preserve original PREOPEN env/manifest/status/prepared index/receipt, policy bundle and postclose generation; verify native bootstrap and auxiliary compatibility before restart. No expensive postclose regeneration, policy/source hash rewriting or synthetic compatibility receipt is part of this repair. Roll back only to the verified predecessor using the same custody and handoff procedure; episode/widget remain permanently retired.

Actual selector/PID, code hashes, bootstrap/handoff consumption, first WS data and natural-call observations belong to the completion receipt. If the new PID has no eligible provider calls, report that absence explicitly rather than claiming a live deadline improvement. The preexisting Buy Funnel Sentinel datetime-serialization failure and recovered-late cron history remain separate from this review.
