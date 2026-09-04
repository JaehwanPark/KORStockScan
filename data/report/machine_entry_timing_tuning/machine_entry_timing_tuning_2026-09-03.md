# Machine Entry Timing Tuning

- Source date: `2026-09-03`
- Effective date: `2026-09-04`
- Decision: `baseline_immediate_entry_carry_forward`
- Axis: one owner scope, fixed delay or per-signal dynamic `0/1/3/5s` confirmation.
- Quantity, order price, target, stop, holding, and exit are unchanged.

- No scope passed its bounded fixed or dynamic floors; entry remains immediate.
- Sample-floor state: `source_quality_blocked`; next action `repair_blocked_exact_scope_source_and_rerun`.
- Per-signal dynamic confirmation: `source_only_evidence_accumulating` (selected for exact-date policy: `False`).
- Policy publication: `blocked_effective_date_preopen_cutoff_elapsed`.
- Candidate scope count: `0`.
