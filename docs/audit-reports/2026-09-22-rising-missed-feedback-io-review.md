# Rising-missed feedback repeated-source I/O repair

## Incident and scope

At19:46 the resource sampler measured40.19% I/O wait. The19:45 rising-missed feedback job ended19:51:26. Two read-only process samples attributed138–161MiB/s to that report reader, with the approximately6.5GB same-day pipeline open. The module contains eleven possible raw passes per report. Main/service startup overlapped the spike; the measurement does not isolate every cause. By19:51 the detector passed at9.85% I/O wait with no automatic mutation.

The user authorized implementation, review/fixes, commit/push and deployment. The owner remains `src/engine/monitoring/rising_missed_intraday_feedback.py`; no new engine module, external cache service, dependency, threshold or order authority is introduced. The existing intraday wrapper and postclose CLI call this same producer.

## Repair and review

The public builder captures one bounded source prefix and serializes every accepted dictionary to a process-private compressed replay. All existing aggregators consume that same prefix, preserving field values, ordering, duplicates, independent mutable objects, candidate counts, costs and outcome logic. Gzip source fallback and malformed/non-object line handling are preserved. Original source path and decoded-prefix hash/length are recorded separately from the scratch representation.

The compressed spool holds at most8MiB before spilling to a private temporary file. It is closed/deleted on success or failure, and every execution starts from the current source. Pickle is used only for objects just parsed and serialized by this process; no external/persistent pickle path is accepted. There is no durable cache or historical-result reuse/invalidation contract. Existing candidate/label memory remains separately owned and is not claimed to fit within the spool limit.

Source append after the capture boundary belongs to the next execution. Truncation, replacement or same-size mutation during capture fails before publication. Review corrected a race where a missing source created after capture could otherwise be labelled present; report availability/provenance now use the captured state. This assumes the existing append-only pipeline writer; it does not certify arbitrary concurrent in-place rewrites combined with appends.

Tests cover full report equivalence, one raw read, nested/mutable field preservation, append cutoff and fresh next run, gzip input, missing source, source replacement, bounded-spool spill and exception cleanup. Existing report, replay, wrapper and release-router tests remain the consumer contract. All guards, chronology, diagnostic/economic definitions and authority fields are unchanged.

## Bounded real-data comparison

An8,366,699-byte complete-line tail of the current pipeline produced an identical report. Legacy raw passes:9, logical raw reads75,300,291 bytes. New raw passes:1, raw reads8,366,699 bytes, compressed replay1,045,896 bytes. Even charging all nine replay reads, logical source/replay I/O falls to17,779,763 bytes (about76% lower; scratch write adds about1MiB). These are logical byte counts, not a physical-disk benchmark. Small-sample times0.426s legacy and0.456s new do not establish a speedup; peak process RSS36,800KiB includes both runs. A targeted full-day producer run and its actual source receipt are recorded separately.

## Deployment, evidence and rollback

Evidence directory: `tmp/rising-feedback-io-20260922/`. It owns test logs, benchmark receipt, immutable-release metadata, selection backup, deployment receipt and the bounded follow-up run measurements. Select the reviewed immutable successor for scheduled report execution; do not interrupt an active prior writer. Preserve existing locks/cooldown and source/policy files. Only this producer needs regeneration for acceptance, not the complete postclose chain. A main restart is unnecessary for the report implementation itself; if the selector/PID handoff requires it, use only the already-authorized guarded restart and record it separately.

Rollback selects the saved predecessor release. No policy, provider, cap, timer or trading-safety value changes. Runtime process health and future cost-adjusted economics remain separate from this report I/O correction.
