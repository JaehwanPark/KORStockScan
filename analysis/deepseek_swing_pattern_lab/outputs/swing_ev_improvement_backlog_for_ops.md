# Swing EV Improvement Backlog for OPS

## 개요

- total_findings: `3`
- runtime_change: `False`
- purpose: report-only / proposal-only improvement backlog

## Improvement Candidates

### 1. Low swing candidate count per day

- finding_id: `swing_pattern_lab_deepseek_selection_low_candidate_count`
- lifecycle_stage: `selection`
- route: `attach_existing_family`
- priority: `MEDIUM`
- mapped_family: `swing_selection_top_k`
- confidence: `solo`
- expected_ev_effect: Increase top_k or adjust floor slightly to expand candidate pool.

### 2. All selected candidates failed to reach order submission

- finding_id: `swing_pattern_lab_deepseek_entry_no_submissions`
- lifecycle_stage: `entry`
- route: `design_family_candidate`
- priority: `MEDIUM`
- mapped_family: `-`
- confidence: `solo`
- expected_ev_effect: Investigate the entry funnel for swing-specific bottlenecks.

### 3. No completed swing trades in analysis window

- finding_id: `swing_pattern_lab_deepseek_holding_exit_no_trades`
- lifecycle_stage: `holding_exit`
- route: `defer_evidence`
- priority: `LOW`
- mapped_family: `-`
- confidence: `low_sample`
- expected_ev_effect: Insufficient evidence; defer until more trades complete.
