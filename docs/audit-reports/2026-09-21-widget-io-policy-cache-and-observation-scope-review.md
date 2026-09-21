# Widget I/O repair and bounded observation review

Owner: `KiwoomCommonHealthOpportunityCostAcceptance0917`. User authorized the recommended repair sequence, repeated review/fix, deployment and restart in the current session. Main trading policy, quantities, orders, existing custody and quote freshness are unchanged.

## Cause and changes

The 19:44–19:46 host diagnosis identified PID33200 auto-expansion under a 512MiB memory limit. In a 15.02-second sample its read/write deltas were 68,894,720/89,108,480 bytes, almost exactly 16,818/21,755 swapped pages. The current source snapshot is 113,511,954 bytes. The live policy loader recursively retained whole research reports and repeated their full parsing on publication checks. The observation collector's same-window read/write were 3,051,520/3,805,184 bytes. This is attribution of a major current contributor, not proof of every earlier submission failure.

- Policy loading now resolves ancestry before loading this date's large report. Generation-bound hashes and a bounded, source-hash-bound small projection avoid repeated full parsing. Full native recommendation inventory is checked on initial intake. Publication/generation, parent policy, current registry, prospective economics and execution receipt checks still run on every call; the cache grants no authority. Source replacement, content change and symlinks are rejected or force verification.
- Research collectors accept `KORSTOCKSCAN_WIDGET_RESEARCH_PRIORITY_SYMBOLS`. The installed scope is 006800/010140/080220. Existing execution-policy symbols and active advisory episodes are preserved by the symbol collector. Other idle prospective observations receive one explicit `observation_paused` snapshot, with no synthetic entry/exit or repeated budget-wait writes. Raw research collection is limited to the configured scope. Source catalogs, historical samples and main/holding subscriptions are not deleted or altered.
- The shared quote reader parses one bounded checkpoint per file generation per process. It still checks original field clocks, route, epoch, current producer PID and consumer time on every read. Returned mutable fields are detached from the cached frame. Missing, corrupt, replaced or changing files do not reuse an old accepted frame. This is per-process parse reuse, not shared memory across processes or permission to expand WS registrations.

## Review and validation

447 targeted tests passed (one existing multiprocessing/fork warning). Coverage includes source tampering after cache use, nested recommendation corruption, source symlink, selected reconstruction fields, current publication failure with a warm cache, shared-frame parse reuse/freshness/replacement/deletion, caller mutation isolation, and preservation of execution or active-episode collection. Initial isolated-worktree historical fixture failure was resolved by making its existing source report directory available; no fixture contract was relaxed.

Read-only actual-date policy benchmark: cold 5.909 seconds, warm 0.0147 seconds, identical policy hash `5a6ec2c04625a937eb44c1d33e0e5c36a39a1cde7d15bd82ffefc4d12703c883`, two cached source projections totaling 1,850 bytes. Initial process peak RSS529,576KiB includes full first-intake verification; steady-state cache does not retain that report population. The service-budget check and release receipt are recorded in the deployment section after completion.

No Kiwoom wire request, FID mapping, subscription/recovery flow, threshold or order protocol was modified. Existing API semantics and hard guards remain. No historical report regeneration or external Project/Calendar sync was performed.

## Remaining boundary

The existing main publisher still serializes a roughly4MB checkpoint. Its observed capture lock was365–663ms; this change optimizes readers, not the main writer. Full-universe WS expansion is deferred. Retained samples and reduced prospective collection coverage must not be represented as full-population economics. Natural next-session signal/submission and net-profit acceptance are separate from code and deployment validation.

## Deployment and final checks (20:07 KST)

Code release `415255eb09a53b799400eccb41065a8002c67287`, branch `codex/widget-io-repair-20260921`, was pushed and independently passed the same447 tests in the immutable release. Compile, diff, systemd unit syntax, document links and print-only checklist parsing passed; one current OPEN owner is preserved.

All six selected service definitions point to `/home/ubuntu/KORStockScan-runtime-releases/widget-io-repair-20260921-415255eb0`. Samsung/Doosan/Hanwha actual new PIDs are407040/407037/407039 with matching cwd. Symbol collector, research collector and auto-expansion started successfully and exited0 under their after20:01 normal schedule. Auto-expansion's new PID407172 was observed with swap0 before its normal exit. No service-memory or WS-registration budget was increased.

A separately authorized read-only source collector `--once` completed after closing time:58 current policy observations became55 explicit `observation_paused` plus3 priority symbols `closed` (006800/010140/080220). This is an installed-scope acceptance, not live quote or trading acceptance. Active advisory episodes and executable symbols remain preserved by code and regression tests.

The deployment boundary preserved the then-selected main commit `b9be2da6e5e03bb1f5b89d67360ff1230129d436` / PID401859. This main was updated by separate work after the earlier19:44 diagnosis; this task did not restart it. I/O wait after the deployment was0.84–1.01%, disk utilization3.8–4.6%; market close, natural old-service exit and the other main release confound comparison, so these are current health observations, not an isolated measured speedup.

The read-only service-budget validation used512MiB memory and25% CPU limits: first policy load21.296 seconds, next calls0.00477/0.00546 seconds, same policy hash and1,850-byte summary, exit0 with no reported memory-limit/OOM events. See [source benchmark](../../tmp/widget-io-policy-benchmark.log), [budget check](../../tmp/widget-io-policy-cgroup.log), [release tests](../../tmp/widget-io-repair-20260921/release-tests.log), [deployment](../../tmp/widget-io-repair-20260921/deployment-final.json), [scope receipt](../../tmp/widget-io-repair-20260921/scope-verification.json).

Natural next-session collection, submit-path receipts and cost-adjusted outcome remain prospective evidence. The implementation, repair review, push, deployment and scheduled-exit verification are complete for this change.
