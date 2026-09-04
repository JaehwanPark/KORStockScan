# Machine Entry Timing Tuning

- Source date: `2026-09-04`
- Effective date: `2026-09-07`
- Decision: `baseline_immediate_entry_carry_forward`
- Axis: one owner scope, fixed delay or per-signal dynamic `0/1/3/5s` confirmation.
- Quantity, order price, target, stop, holding, and exit are unchanged.

- No scope passed its bounded fixed or dynamic floors; entry remains immediate.
- Sample-floor state: `source_quality_blocked`; next action `quarantine_exact_source_date_and_verify_next_runtime_receipt`.
- Per-signal dynamic confirmation: `source_only_evidence_accumulating` (selected for exact-date policy: `False`).
- Policy publication: `allowed_next_session_staging`.
- Candidate scope count: `0`.
