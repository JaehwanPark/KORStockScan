# Machine Entry Timing Tuning

- Source date: `2026-09-10`
- Effective date: `2026-09-11`
- Decision: `baseline_immediate_entry_carry_forward`
- Axis: one owner scope, fixed delay or per-signal dynamic `0/1/3/5s` confirmation.
- Quantity, order price, target, stop, holding, and exit are unchanged.

- No scope passed its bounded fixed or dynamic floors; entry remains immediate.
- Rebound/reentry: `source_contract_gap`; eligible paired opportunities `0`.
- Rebound source gaps: `{"source_contract_gap": 11, "source_section_missing": 15}`.
- Rebound automatic PREOPEN: standing user authority; no per-candidate approval; exact scope, source/EV/owner/conflict/rollback checks remain.
- Rebound modeled owner exits are not actual broker fills; missing control resumption is not zero PnL.
- Sample-floor state: `source_quality_blocked`; next action `quarantine_exact_source_date_and_verify_next_runtime_receipt`.
- Per-signal dynamic confirmation: `source_only_evidence_accumulating` (selected for exact-date policy: `False`).
- Policy publication: `allowed_next_session_staging`.
- Candidate scope count: `0`.
- Four-arm study: see cohorts[].feature_ablation_study for same-population cost comparisons and chronological holdout; research does not select a runtime policy.
