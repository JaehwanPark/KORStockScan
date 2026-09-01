# Machine Entry Timing Tuning

- Source date: `2026-09-01`
- Effective date: `2026-09-02`
- Decision: `baseline_immediate_entry_carry_forward`
- Axis: entry confirmation delay only (`0/1/3/5s`).
- Quantity, order price, target, stop, holding, and exit are unchanged.

- No scope passed all cumulative and 5/10/20-day floors; delay remains `0s`.
- Sample-floor state: `instrumentation_or_join_gap`; next action `repair_exact_entry_anchor_market_join_and_rerun`.
- Applied scope count: `0`.
