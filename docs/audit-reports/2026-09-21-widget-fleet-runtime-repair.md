# Widget fleet runtime repair — 2026-09-21

## Findings and repair

The symbol collector repeatedly exceeded its 90-second ExecCondition deadline
under the installed 20% CPU quota. A bounded read-only diagnostic completed in
38.68 seconds without the quota. Policy reconstruction hashed the entire 10 MB
report for every observation seed and rebuilt the same frozen trading calendar
for every candidate revision. Hash once per reconstruction; reuse immutable
process-local calendar results with independent lists returned to callers.
The exact-date reader still reconstructs and compares the complete policy,
source hash, publication, revision, allocation and feedback contracts.
The same 58 observation policies validate in 0.57 seconds after repair.

`process_health` previously omitted the failing collector. It now checks five
widget collector units during the trading-day collection window, with bounded
startup grace and explicit failure/query-error evidence. This is process
liveness coverage, not proof of data quality, all episode readiness or economics.
No recovery action or order authority is added to the detector.

The September 21 static widget policy referenced a deleted publisher release.
Publication now records resolved shared-data paths. Historical incumbent path
relocation is accepted only for the policy owner's directory and exact frozen
bytes, policy identity, dates and recipe; an existing changed source fails closed.
The historical September 18 incumbent also changed bytes (expected `fa519776`,
current `0678be06`) and no retained matching copy was found in the checked policy
and release-snapshot locations. The publisher now emits the existing
`paired_incumbent_policy_missing` block for that invalid Samsung premarket carry.
KRX `execution_quality_safety_veto` remains unchanged for all three static symbols.
The existing source report can be republished without economic recalibration;
consumer closure requires four explicit blocked sessions and zero eligible ones.
Historical study results remain historical evidence, not valid live incumbent proof.

Review also reproduced three existing research tests failing in the previous
release: feedback ignored the active isolated research directory and read the
live directory. The feedback reader now honors the same scope as its producer;
production's default directory and validation rules are unchanged.

## Validation and operational acceptance

Use targeted producer/reader, paired-policy, collector, health and research-loop
tests, Python compile, diff validation and the print-only checklist parser.
Checks include tampered source/hash rejection, mutable result isolation,
startup/close/nontrading windows, missing units, condition timeout, query failure,
retired publication symlinks, and changed incumbent byte rejection.

The user explicitly approved repair, deployment and restart on September 21.
Preserve backups before source-only publication and unit pin changes. Deploy an
immutable reviewed release, retain CPU/memory limits, and restart the affected
collector/widget trader and main bot through their existing owners. Verify real
PID/cwd, current policy consumption, natural source receipts and health separately.
Do not replay missed episode starts, place manual orders or weaken quarantine.

CJ CGV morning preflight exit 4 is explicit terminal quarantine:
`research_half_robustness_review_requires_new_profile_revision`. Jeju Semiconductor
and SK Telecom morning services naturally started. Later episode schedules remain
pending until their own windows. A process PASS must not close these policy or
natural-acceptance obligations.

Evidence and rollback snapshots: [repair directory](../../tmp/widget-fleet-repair-20260921/).
Final runtime receipt: [deployment.json](../../tmp/widget-fleet-repair-20260921/deployment.json).
Executable acceptance remains with `KiwoomCommonHealthOpportunityCostAcceptance0917`
and the existing low-price/PREOPEN owners in the
[daily checklist](../checklists/2026-09-21-stage2-todo-checklist.md).
