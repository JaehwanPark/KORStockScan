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
