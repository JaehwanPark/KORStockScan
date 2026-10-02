# Main AI periodic transport warmup (2026-10-02)

## Ownership and authority

The user requests periodic calls and selection of the best practical interval. The prior explicit review/fix/deploy/restart approval remains in force. This change owns Main transport diagnostics in `src/engine/ai/transport_warmup.py`, persistent HTTP clients in the existing OpenAI engine, and the existing Main startup/shutdown consumer. No engine-root module is created. Widget/Episode/offline/test-mode engines do not start the diagnostic scheduler. No Kiwoom request/parser/REG/REMOVE code changes.

## Interval samples and decision

Official OpenAI prompt-caching, latency-optimization and Responses documentation were inspected on 2026-10-02. Installed SDK: OpenAI 2.29.0, SDK retries 0; original HTTP keepalive expiry 5 seconds. First local SDK Responses lookup measured 340.63ms. These facts do not establish the historical remote timeout cause.

Six authorized non-trading requests used the current `gpt-5.4-nano`, 16 output-token cap, reasoning none, store false and five-second timeout. Three independent persistent client pools used 300-second connection expiry. Same request and key; no market/account/order input or decision ledger output. Results are in `data/report/ai_transport_warmup/interval_sample_2026-10-02.json`.

| Idle interval | Initial request | After idle | Reused connection |
| --- | --- | --- | --- |
| 120 seconds | 1985.84ms | 1329.67ms | yes |
| 180 seconds | 1104.65ms | 642.43ms | yes |
| 240 seconds | 646.72ms | 703.47ms | yes |

All six completed with OK; input/output tokens 31/5, cached tokens 0. Initial TCP/TLS completed in under 9ms. After-idle samples have no new TCP/TLS phase. Select **240 seconds per key** as the initial operating interval: 15 diagnostics/hour/key, 25% fewer than 180 seconds and 50% fewer than 120 seconds. The 61ms difference from 180 seconds is a single observation, not statistical evidence. This is a latency/call-count compromise, not a proven global optimum. A tiny diagnostic does not establish full prompt/schema readiness, provider model residency, actual entry latency recovery, source recovery or economics.

## Operating rules and rollback

- Start only in native Main, outside test mode, on the already-validated trading day. Calls run only in the existing allowed scalping BUY time windows and stop across date rollover.
- Keep original key rotation order and SDK retry policy; retain one client/pool per key with 300-second expiry.
- One separate diagnostic executor prevents diagnostic waits from occupying the real decision executor or API lock. Skip admission while Main locks are busy or AI is disabled. An already-running diagnostic can overlap a subsequently arriving real call; it cannot be preempted, and real calls do not queue behind it locally.
- Same-model real HTTP activity defers that key's next diagnostic. Failed diagnostics also consume their interval; no immediate retry or automatic cadence escalation. Late work prevents a second diagnostic from being queued.
- Responses are discarded. Receipts alone append to `data/runtime/ai_transport_warmup/YYYY-MM-DD.jsonl`, bound to PID/root/key index/model. No credentials, response text, decision cache, circuit/failure counters, AI verdict, cooldown, order, policy or postclose training inputs are changed.
- Rollback selects the previous immutable release through the existing guarded policy-preserving handoff. Diagnostic failures do not restart Main or alter its live guards.

## Review and validation

Implementation/self-review fixed atomic cadence admission, test-mode/date isolation and storage-failure visibility. Targeted tests cover persistent key order/pools, cadence, exact diagnostic arguments, disabled/session/live priority, failures without hot retries, late worker queue bounds, stop/idempotent start and preservation of live engine caches/failure state. Transport/cache regressions: 281 PASS; startup/router/handoff gate: 139 PASS before the final supplemental isolation test. Final consolidated results and deployment evidence follow below.

Final consolidated validation: **410 PASS / 5.28 seconds**. Python compile, diff whitespace and print-only checklist parser pass. No package installation or trading-suite expansion is needed for the closed diagnostic scope.

Current selected policy/PREOPEN/prepared byte hashes and independent service pins must remain unchanged. Existing 10/1 finalization/source failure is separate and must not be converted to PASS by this transport work.

## Deployment and natural cadence acceptance

- Immutable code `c124f476f6b107ffeb3f65c446ff1f3c42dcf68d`, root `/home/ubuntu/KORStockScan-runtime-releases/main-ai-warmup-240s-20261002-c124f476`: repeated gate **410 PASS / 9.15 seconds**, source tree clean.
- Guarded Main restart completed at 10:49:58 KST: old PID 2792150 exited, new PID **2809235**, start ticks 52663056, native cwd/root/code attested. Runtime bootstrap verification PASS, no missing/mismatched env. Same-day consumption receipt PASS/actual_pid_consumed=true; native release-cwd sealed-generation and completion checks PASS. Verification from workspace cwd intentionally rejects the selected-release identity and is not a native consumer check.
- Conservation receipt confirms **five frozen policy/PREOPEN/prepared files**, **416 independent service pins**, root/Ubuntu cron hashes unchanged and exactly one Main PID. Policy manifest remains `7046d2a9feaf72c2d0893a18b0906108790ff12c57bbd5c3e30331e259bac4cb`.
- Natural key 0 diagnostics: 10:50:15, 2316.405ms; 10:54:19, 1079.306ms; interval **244.146s**. Key 1: 10:50:17, 1737.514ms; 10:54:20, 930.450ms; interval **242.929s**. All four completed with OK in the same PID/root. The ten-second scheduler poll and execution/busy time can extend the 240-second minimum cadence; intervals are not a precise timer guarantee.
- Evidence directory: `data/runtime/startup_readiness/2026-10-02/ai_periodic_warmup/{before.json,selection.before.json,selection.published.json,prepare.json,restart.log,prepared.verify.json,completion.verify.json,after.json,natural-acceptance.json}`. Native consumption: `data/runtime/policy_bootstrap/intraday_handoff/2026-10-02/c124f476f6b107ffeb3f65c446ff1f3c42dcf68d.consumed.json`. Diagnostic ledger: `data/runtime/ai_transport_warmup/2026-10-02.jsonl`.

Code review, deployment/PID and natural periodic diagnostics are complete. At the 10:54 acceptance snapshot, real entry-response latency recovery remained not observed; the initial period selection is not a statistical global optimum. Historical source/finalization and realized economics remain separate.


## Supplemental review and repair (11:06 KST)

The user explicitly reauthorized repeated code review, fixes, deployment and guarded restart. The existing stable checklist owner is reopened for newly found defects; prior acceptance remains historical evidence.

1. Move lazy SDK Responses lookup into the diagnostic worker. One absolute five-second deadline now includes executor admission, lazy lookup and response wait; the SDK receives only the remaining budget. Recheck live priority, session/date/disabled status and stop after lookup. Expired preparation never starts a late provider call. A blocked worker can outlive the scheduler wait; it is not forcibly killed, and no second diagnostic is queued behind it.
2. Serialize controller start/stop/admission and reject overlapping ticks without waiting. Stop-before-start creates no scheduler. Failed thread startup resets the thread; failed engine startup detaches the diagnostic controller even when its cleanup also fails.
3. Isolate diagnostic shutdown errors from Main's heartbeat, scanner, exit-monitor and WS cleanup. Log exception types only. Diagnostic receipts distinguish deferred/expired preparation and record provider-call start only as observed at receipt time; they do not prove remote delivery or completion.
4. Clear each pending handle before admission. Submission failure cannot cancel a prior completed future. Keep cadence 240 seconds, pool expiry 300 seconds, model/key rotation, SDK retries, existing live deadline, policies and all hard guards unchanged.

Re-review covers controller/engine/startup/shutdown consumers and diagnostic ledger separation. Targeted gate: **422 PASS / 5.82 seconds**, including slow/blocked lazy lookup, remaining SDK budget, priority/session/stop changes during lookup, concurrent tick/start, failed start plus failed cleanup, and stale-future cancellation isolation. No unresolved findings remain in this diagnostic scope. Python compile, diff whitespace and print-only parser validation PASS; exactly one current parsed owner. Immutable/PID follow-up is recorded after completion below.

Additional natural evidence from the prior PID: the 108490 real decision at 10:58:02 KST was evaluated without timeout in **2718ms**. This one real request does not establish causal latency improvement, statistical optimality, an order or realized profit. Historical finalization/source failures remain separate.


### Supplemental deployment acceptance

- Immutable code **09a6a2dfa49d42381f653e8bcb57a0176653c555**, root `/home/ubuntu/KORStockScan-runtime-releases/main-ai-warmup-review-20261002-09a6a2df`: repeated gate **422 PASS / 9.09 seconds**, clean code/deploy source.
- Native guarded restart completed **11:07:56 KST**. Previous PID 2809235 exited; exactly one new Main PID **2815486**, start ticks 52770763. Native env verification PASS, missing/mismatch 0; same-day consumed receipt PASS with `actual_pid_consumed=true`. Selected-root sealed-generation and completion checks PASS. Prepared verification's static `actual_pid_consumed=false` is distinct from the native consumed receipt.
- Before/after conservation verifies five policy/PREOPEN/prepared files, 416 independent service pins and both cron hashes unchanged. No Widget/Episode restart or policy/source-report regeneration occurred.
- New PID natural diagnostic key 0: **11:08:10, 2020.415ms**; key 1: **11:08:12, 2433.075ms**. Both completed with provider-call start observed, correct code/root/PID and diagnostic-only ledger. New PID repeat cadence is not yet observed; prior PID's two-cycle natural acceptance remains historical cadence evidence. No additional benchmark API calls were made for this repair.
- Shared WS producer is the same new PID/code/root, connection available, writer loss 0 and projection errors 0. Registration is local sent-registry evidence, not broker acknowledgement or economic acceptance.
- Evidence: `data/runtime/startup_readiness/2026-10-02/ai_warmup_review/{before.json,selection.before.json,selection.published.json,prepare.json,restart.log,prepared.verify.json,completion.verify.json,after.json,natural-acceptance.json}`; exact consumption: `data/runtime/policy_bootstrap/intraday_handoff/2026-10-02/09a6a2dfa49d42381f653e8bcb57a0176653c555.consumed.json`.

The diagnostic repair/review/deployment/PID gate is closed. Actual latency causality, interval optimality and realized economics remain unestablished. Broad trading suites, postclose regeneration, manual orders and external Project/Calendar sync were outside this change's required validation.
