# Main entry economic source and terminal lineage repair (2026-10-02)

## Owner and authority

User explicitly requested repair, repeated review/fix/re-review, deployment and guarded restart after the exact 108490 alert. Runtime observation belongs to the existing Main state handler; report classification belongs to the sentinel, its incremental cache and monitoring package. No engine-root module is added. Native family policies, order guards, account authority, quantities, price, provider routes and existing source-only rate/wait limits remain unchanged. No manual account, quote, provider, order or cancel calls are made for validation.

## Exact incident

Promotion `ZBPROM-108490-1790906257308-2`, attempt `aims-8a8b6322e9e01c9f5961`, KRX/KRX_REGULAR, bundle `6785d52e1ebb9b4ae4da4382b07f35baf1a7022e0b4c87025dcb48851900bc87`.

- 10:58:00 pre-AI source-only kt00011 admission was deferred with zero broker request attempts. Frozen pre-AI operating replay is source_gap, not zero EV or a failed machine policy.
- 10:58:02 ENTER_NOW/AI PASS completed in 2718ms.
- 10:58:03 normal sizing received kt00011 return_code 0, valid cash/applied contracts for exact 108490/311500. Normal capacity source hash `d39c03d3afa620c28a74858e9434e8727ca0a574439908c7a759701de3343313`. Valid quantity/price plan was produced.
- The 10:58:03 weak-context guard blocked before any broker order call. The 10:58:15 retry was blocked by weak momentum without micro confirmation. Broker submit attempt and success counts were 0. The generic residual reason `probe_broker_submit_failed` is not evidence of a broker rejection.
- Residual lacked the machine revision envelope; both detailed guard stages were absent from sentinel admission/classification. This produced identity_or_contract_gap and hid the direct guard evidence. The historical event predates 09a6a2df/Main PID 2815486 cutover.

## Official reference gate

Current official upstream [Kiwoom-Securities/Kiwoom-REST-API](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/tree/953e5dbff123f437ab4d11a78a95191a685eb51f), SHA `953e5dbff123f437ab4d11a78a95191a685eb51f`, retrieved `2026-10-02T11:38:02.560529+09:00`. Inspected paths: `kiwoom/specs.py`, `kiwoom/core/client.py`, `postman/kiwoom-openapi.postman_collection.json`, `kiwoom/_data/kiwoom_api_spec.json`.

`kiwoom_docs` is absent in this revision. Packaged kt00011 spec and SDK verify POST `/api/dostk/acnt`, api-id/authorization/content-type, stk_cd and optional uv in won, signed numeric amount/quantity responses, continuation and body business error handling, and distinct PRD/MOCK origins. Postman provides both environments but presents request arguments in URL query; the packaged request/body and SDK remain the cross-check for the unchanged local JSON-body call. No protocol semantics are inferred from the sample and no local request/parser/auth/REG/order wire contract is modified. Preparation only changes within the existing bounded worker/queue.

## Implementation and operating rules

1. Async capacity preparation runs once after final evaluation quote refresh. A refreshed price of 1003 prepares 1003 rather than the earlier 1001 in the sample. Existing source-only maximum wait 1.25 seconds, HTTP connect/read 0.15/0.15, retry count 1, context deadline and two-second exact reuse checks remain unchanged. Later price, account/inventory, date or source changes still invalidate reuse.
2. Pending legacy preparation replaces obsolete same-symbol prices within the existing eight-slot queue. ENTER_NOW source failure requests only future preparation for its exact reference price; BLOCK/RECHECK do not issue new reads. Original source_gap stays frozen. Main's normal sizing always reads afresh; source preparation is not order authority.
3. Two detailed guard stages inherit exact call-local machine provenance and are retained/classified as existing UPSTREAM_GATE terminals. No new bottleneck axis is created. Explicit caller fields retain precedence. Semantic assessment objects serialize after inheritance.
4. Freeze machine provenance into the probe bundle at creation. Residual records borrow only a matching bundle and stock receipt, even if a newer AI decision exists. A missing/foreign bundle remains unbound; do not attach current AI to historical custody. This changes logging only, not residual/order behavior.
5. Sentinel and monitor retain final_guard_evidence with stage, reason, time and local submit call ID. Zero broker calls log pre-broker non-submission rather than generic transmission failure.
6. Cache schemas 15->17 and 16->18 extend guard admission from a verified append cursor. Retain old cached rows, parse only appended raw bytes, preserve a migration receipt with historical_stage_coverage=not_backfilled_before_raw_offset. Historical absent stages are not restored or declared complete. Replaced/truncated/inconsistent sources fail migration. The native cache was schema 16 with raw offset 367959249 at 11:50; full raw bootstrap is not required for this cutover.

## Review and validation

Self-review and regression fixed refresh callback snapshot scope, full-queue price replacement, inherited semantic JSON serialization, migration population counts and file replacement/growth checks. Re-review covers source preparation, Main native consumer, exact residual custody, sentinel/monitor and shared terminal classification. In-scope unresolved findings: 0.

- Producer/cache/consumer gate: **448 PASS / 24.83s**.
- Actual guard and residual regression: **23 PASS / 2.99s**, 889 unrelated strategy tests deselected.
- Startup/router/handoff/warmup gate: **148 PASS / 3.39s**.
- Total disjoint targeted tests: **619 PASS**. No live account/order/provider benchmark was needed; source fixtures validate bounded calls, exact price/scope/freshness, queue limits and absence of backfill. Natural economic acceptance remains separate.

Python compile, diff whitespace and print-only parser PASS; exactly one current parsed owner. Immutable/PID follow-up is recorded below. Deployment uses the existing guarded policy-preserving handoff. Rollback restores the previous selected release through the same handoff. Forward cache prefixes keep their declared coverage gap; rollback cannot retroactively restore absent guard events. Natural new ENTER_NOW capacity proof and guard/residual closure require exact ID/hash receipts; absence is not_observed, never repaired history, a trade or improved profitability.

## Deployment and bounded natural acceptance

Code commit `a60143466290a06efcf141f139dd7141407a3f6f` is deployed at `/home/ubuntu/KORStockScan-runtime-releases/entry-economic-lineage-20261002-a6014346`. Immutable checkout repeated gates: 448 PASS/24.91s, 23 PASS/3.40s and 148 PASS/3.92s; total 619 PASS. Guarded Main restart completed at 11:56:46 KST. Exactly one Main PID `2831000`, start ticks `53063789`, runs from the new release's `src` directory; old PID `2815486` exited.

Evidence owner: `data/runtime/startup_readiness/2026-10-02/entry_economic_lineage_repair/`. `before.json` and `after.json` prove five frozen policy/PREOPEN/prepared files, 416 independent service pins and root/Ubuntu cron hashes unchanged. Widget and episode were not restarted. Manifest remains `7046d2a9feaf72c2d0893a18b0906108790ff12c57bbd5c3e30331e259bac4cb`. The exact same-day consumed receipt at `data/runtime/policy_bootstrap/intraday_handoff/2026-10-02/a60143466290a06efcf141f139dd7141407a3f6f.consumed.json` is PASS with `actual_pid_consumed=true` and the new PID identity. Prepared/completion verification PASS proves the preserved handoff; those preparation receipts themselves have `actual_pid_consumed=false`. The sealed-generation result does not clear the separate historical strict-summary/postclose failure.

The new PID's shared WS producer has matching root/commit, connection available, writer loss 0 and projection errors 0. Its item registry is local sent registration, not a broker acknowledgement or trade. The existing 12:00 scheduled sentinel produced report `as_of=2026-10-02T12:00:07`, followed by monitor `as_of=2026-10-02T12:00:33.470642+09:00`. Lossless cache migrated 16->18 at raw cursor `386527119`, advanced to `403799858`, retained 9035 rows, and reports `rebuilt=false`, decode errors 0 and `population_proof=forward_only_stage_extension`. Only the newly admitted guard stages before that cursor are explicitly `not_backfilled_before_raw_offset`. This is the lossless cache migration proof; the report's separate summary/baseline compaction metadata is not this proof.

`natural-acceptance.json` records a bounded 16 MiB raw tail lookup after restart. Three new exact machine receipts for 005930 were RECHECK (`aims-61d3eb3a7a8e92c5d374`, `aims-3831898fa4ae031f40b8`, `aims-4cd2858f7f7613ffaf14`), with distinct observation hashes and `capacity_observation_cache_miss_nonentry`. These rows preserve missing capacity without requesting new account reads for nonentry. New ENTER_NOW exact-capacity, guard and residual bundle lineage are **not_observed** in this bounded acceptance window. Keep the checklist owner OPEN for those natural receipts; validate their exact attempt/bundle/hash and freshness when they arise. No original 108490 source reconstruction, broker submission, fill or profitability improvement is claimed.
