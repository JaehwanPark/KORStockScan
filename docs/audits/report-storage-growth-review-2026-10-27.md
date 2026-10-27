# Trade report storage growth and lifecycle repair — 2026-10-27

## Decision and scope

Implement at the existing report publisher, private row store, native compressor
and selected-release scheduler. Preserve sealed source26 report/policy bytes,
all observation fields and chronological occurrences, completion/cost/null
semantics, policy-day protection and original failed attempts. This review is
source closure and bounded storage verification; it is not a deployment, a new
policy generation, a regenerated postclose completion or natural acceptance.

Development baseline: `6d0d197562c67ebdf5cd3524e71001c5257eb603`, branch
`codex/report-storage-20261027`, isolated worktree
`/home/ubuntu/KORStockScan-worktrees/report-storage-20261027`. The canonical
workspace's unrelated code/document changes remain intact. Initial census:
260 registered worktrees, 154 release-directory entries, 60.43GiB available.
This task added one development worktree and no runtime release. The256 bound
belongs to service units, not a release-directory/worktree count; no limit changed.

## Cause proven against the original report

A single bounded-memory line census read the original7,485,855,103 bytes in267.43s
(about14MiB resident during observation). Before/after identity matched and the
SHA256 was `b80221df9267c028dec7e354e682ae65537e59d3da3f03aad1ef550356352492`.
The companion completed projection occupies1,036,615,680 allocated bytes. Together
they account for approximately7.94GiB; this is two representations, not one7.94GiB
JSON object. [Census](/home/ubuntu/KORStockScan/tmp/report-storage-20261027/census.json).

| Component of original JSON | Bytes | Role and finding |
| --- | ---: | --- |
| `recent_trades` | 3,063,584,393 | Three display rows with complete timelines |
| `completed_trades` + `open_trades` | 3,063,584,423 | Same three rows classified again; stable API sections retained |
| `completed_trade_projection` | 1,132,548,013 | Two completed positions; exact research/cost/census source |
| `open_scalp_position_projection` | 226,086,922 | One open position; carry provenance, not completed economics |
| Other fields/sections | 51,352 | Headers, facts, lineage, candidates and summaries |

The2,332,586,401 bytes of indentation/newlines/key spacing (2.17GiB) are included
in that table, not additional data. Machine `universal_trailing_quote` is also
serialized as a display `details.value` string alongside its original `fields`.
The original full report and completed projection are intentionally separate
consumer contracts; their names/hashes cannot be collapsed without migrating
holding/carry/research/quantity readers.

This is predominantly same-day observation growth, not inclusion of June through
September research. Source26 declares17 day rows, three entered positions,
two native completed positions, one open position and107,801 holding events.
Its structured receipt binds the26th partition (2,852,858,609 bytes); quantity
cost source dates are only2026-10-26. The loader selects the target date and uses
prior dates only for the allowed carry-fill projection. On23 October the report
had4,287 events: source26 is25.15 times larger by count. It contains80,540 trailing
input transitions and25,878 mechanical observations. The timeline census also
counts compact timeline repeats; those counts must not be added to the native
107,801-event denominator. New classifier observations and heartbeat/state
transitions have a real replay consumer; this repair does not reinstate the
retired256-sample truncation or throttle live observations.

The existing20:50 archive completed at20:58:45 on26 October, before this report
was published at21:07–21:08. More fundamentally, native protection rejects source26
on26 October as current and through27 October as its next policy day. An evening
job alone cannot provide a morning sweep immediately after that protected day.
There is a separate resume defect: after compressing the main JSON, an interruption
before its completed projection removes the parent's plain filename from the next
census, leaving the large sidecar indefinitely undiscovered.

## Repair, replacement and retained consumers

| Existing owner/path | Disposition | Result and consumer evidence |
| --- | --- | --- |
| `log_archive_service.SnapshotRows` | consolidated | Private row bytes use zlib1 and content identity reuse. Every logical occurrence/order remains; checksum, expansion bound and corruption failures remain enforced. Unlinked scratch cannot become policy evidence. |
| `save_monitor_snapshot` trade JSON formatting | replaced | Compact row bodies with unchanged full values; retain two-space root/four-space section locators required by `load_prior_entry_projection`. Native writer publishes the actual new generation hash. |
| `_build_event_details` | removed duplicate display copies | Hide machine quote and internal classifier observation JSON from human chips only. Preserve their original typed `fields`, all event timestamps and research timelines. |
| Main-only compressor enumeration | replaced | Include parents discovered from remaining completed projections. Require a valid original parent archive receipt before resuming a sidecar. Dependency receipts stay plain. |
| Snapshot publication/compression | consolidated | Share the native parent JSON generation lock. Verify controller/strict custody again immediately before unlink. Gzip CRC/logical SHA/size/original identity remain required. |
| Evening archive and completion-prefix reuse | retained | Same EOD/source/custody contracts; unchanged generations reuse the existing prefix owner, without another cache or producer. |
| Stage2 scheduler/router | added invocation of existing compressor | `snapshot-archive` at06:25 daily, selected code and scheduled-execution lease, `--snapshots-only --days 1`; actual date controls age. Weekends do not bypass the next trading policy day. |
| Display classification lists and research sidecar | retained | `/api/trade-review` returns the full report; the existing public schema remains intact. Internal page uses `recent_trades`; historical readers and research use their own complete projections. No unproved deletion of API fields. |
| Policy/research archives | retained | Raw becomes one verified gzip after native eligibility; automatic age-only purge is not introduced. Reference/custody retirement remains required. |

The operating owner is [Operational log retention](../operational-log-retention.md).
No new engine-root module, alternate report producer or trading-policy owner was
introduced. `--snapshot-date` permits a bounded snapshot-only repair; combining
it with pipeline-only scope is rejected. Protected bytes/reasons remain visible.

## Review and validation

- Eight focused regressions fail on the original implementation, including the
  orphan-sidecar case using the original `run` API. They pass after the repair.
  [Original failures](/home/ubuntu/KORStockScan/tmp/report-storage-20261027/regression-original.log).
- Publisher, native archive, compressor, report, router and owned-cron suites:
  **466 passed**. Review found and corrected an installer-comment idempotence
  defect; the final test installs twice and preserves unrelated schedules.
  [Final tests](/home/ubuntu/KORStockScan/tmp/report-storage-20261027/tests-final.log).
- Negative coverage retains changed/missing archive parent, corrupt private row,
  source hash mismatch, invalid controller/strict custody, policy-day retention,
  source change at receipt publication, unknown costs/null and unrelated-family
  isolation. Plain and gzip carry consumers authenticate the compact format.
- The first128 real source26 timeline events were sampled under a64MiB read cap.
  All128 source fields, stages and timestamps/order match. Only duplicate display
  chips differ. Serialized sample3,317,312→1,886,137 bytes (**43.14% less**), private
  scratch1,885,893→655,031 bytes. This is a bounded sample, not a whole-day saving
  or economic claim. [Sample proof](/home/ubuntu/KORStockScan/tmp/report-storage-20261027/sample-benchmark.json).
- Current selected code successfully consumed source26 through the native
  `_verified_trade_review_projection(..., metadata_only=True)` reader. Original
  identity remained unchanged; its native result still protects source26 with
  `postclose_policy_day_not_elapsed:2026-10-27`.
  [Actual consumer](/home/ubuntu/KORStockScan/tmp/report-storage-20261027/native-consumer-verification.log).
- Before editing the daily owner, native `preserve_checklist` verified the original
  strict-bound checklist SHA `baf879d462f2f6dc49c5011ad1581d1ecacf0df740b205469b155dfe5ca7e111`.
  Its historical bytes and current editable document remain separate.

- Downstream holding-window/holding-observation/fact/quantity/stop suites covered
  453 cases.452 passed initially; one pre-existing test fixture placed its alias
  outside the per-test temporary root and collided after successful-test cleanup.
  Moving that alias under its owning temporary root passed all four parametrized
  native fact→quantity→stop cases. No production assertion or guard was relaxed.
  [Consumer run](/home/ubuntu/KORStockScan/tmp/report-storage-20261027/tests-consumers.log),
  [revalidated cases](/home/ubuntu/KORStockScan/tmp/report-storage-20261027/tests-consumer-fixture.log).
- `git diff --check`, Python compile, shell syntax and print-only checklist parser
  pass. The current shared owner was carried forward with its existing history
  and28 October due date; its window now includes06:25 compression. External
  Project/Calendar synchronization was not run.

- Final clock review: compressor/router/owned-cron278 cases pass, including
  explicit KST date selection on a UTC host. The clock fixture also passed alone
  with every optional source root isolated. Across the producer/storage and
  downstream sets,920 distinct cases are covered; repeated checks are not added
  to that count. [Clock review](/home/ubuntu/KORStockScan/tmp/report-storage-20261027/tests-clock-review.log).
- Source/test/document additions and deletions are recorded separately in
  [change statistics](/home/ubuntu/KORStockScan/tmp/report-storage-20261027/change-stats.json).
  Net growth implements compact encoding, verified temporary storage, resumable
  native archive enumeration and its existing-owner invocation. Tests add the
  corresponding corruption/identity/custody/clock/consumer checks; no module was
  moved or duplicated to claim a reduction.

## Application state and remaining acceptance

At the runtime recheck, selected6d0d19756/Main670131/start71972259 and actual cwd
still matched the task baseline. No selector, process, active policy, order,
provider, calendar, source report or sealed completion was changed. No production
report bytes were reclaimed in this task: **0GiB**. The earlier cleanup's savings
must not be counted again. Future-format savings and physical current disk delta
are different measurements.

The changes are prepared in the isolated branch; **runtime deployment and cron
installer application have not occurred**. The existing
`DirectFamilyPreopenPolicyHandoff` remains the executable acceptance owner.
Integration must include native code-profile/independent preparation compatibility,
then selected source generation and actual successor-PID/policy verification if
that transition includes a Main restart. A source-only test result cannot authorize
or certify that transition.

After reviewed integration/installer application, verify source27's native
postclose report and exact downstream census/cost/carry/holding/quantity bindings
under the unchanged resource limits, through28 October PREOPEN/Main. At the first
06:25 eligible sweep on28 October, source26 can be compressed only if its original
whole-chain/custody proofs still validate; source27 remains policy-day protected.
Verify logical hashes, original identities and downstream readers after compression.
If integration misses that window, keep this same owner OPEN with the actual next
sweep; do not rewrite source26 or report an unobserved natural run as PASS.
