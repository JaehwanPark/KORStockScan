# Rising-missed TP1 dated handoff repair

## Decision and cause

Scope: source `2026-09-17`, intended effective date `2026-09-21`.
The September 20 report regeneration replaced the canonical source, but the
publisher defaulted to the next trading day after the source date (September 18).
The September 21 receipt retained the September 19 generation's source hash and
PREOPEN correctly rejected it with `source_report_sha256_mismatch`.

The current source is `measured_no_edge`. Recovery retains `incumbent_preserved`,
`runtime_effect=false`, and empty runtime overrides. This is an integrity repair,
not a threshold promotion or proof of improved profit.

## Publication and verification contract

- Default effective date is the next trading day after the later of source date
  and the report's recorded publication date. Explicit recovery dates remain
  available to the existing publisher.
- Before writing any output, validate the report self hash and generated policy
  through the existing PREOPEN receipt validator. Invalid binding fails before
  replacing an output.
- Bootstrap verification revalidates the accepted Rising-missed policy against
  its current source report, including when checking a running PID. An unchanged
  policy file alone is insufficient after source regeneration.
- For this recovery, preserve prior source/policy/bootstrap artifacts, reuse the
  existing report without recalibration, and republish the source and effective
  policy pair using the existing writer. Preserve the report's generation time
  and record the actual repair time separately. Do not rewrite old September 18
  policy history or claim the old postclose summary is freshly verified.

## Validation and authorized deployment

Targeted producer/bootstrap tests cover ordinary publication, weekend recovery,
replacement of a stale dated policy, tampered-source rejection before writes,
and source mutation after bootstrap acceptance. Python compile and diff checks
are required before selection. Daily checklist changes use the print-only parser.

The user explicitly approved deployment and graceful restart. The existing
managed release router and custody-aware `restart.sh` own the transition.
Closure requires a new immutable release/PID, accepted Rising-missed receipt,
empty Rising-missed overrides, full PID verification PASS, and a living sniper
loop. Other family rejections and economic acceptance remain separate.

Machine-readable validation, rollback backups and final PID receipt:
[deployment evidence](../../tmp/rising-missed-tp1-handoff-fix-20260921/deployment.json).
The executable owner remains `DirectFamilyPreopenPolicyHandoff` in the
[daily checklist](../checklists/2026-09-21-stage2-todo-checklist.md).
