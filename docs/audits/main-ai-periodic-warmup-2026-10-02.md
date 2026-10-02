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
