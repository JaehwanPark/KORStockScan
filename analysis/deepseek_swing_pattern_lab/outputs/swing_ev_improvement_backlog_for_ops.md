# Swing EV Improvement Backlog for OPS

## 개요

- total_findings: `5`
- runtime_change: `False`
- purpose: report-only / proposal-only improvement backlog

## Improvement Candidates

### 1. All selected candidates failed to reach order submission

- finding_id: `swing_pattern_lab_deepseek_entry_no_submissions`
- lifecycle_stage: `entry`
- route: `design_family_candidate`
- priority: `MEDIUM`
- mapped_family: `-`
- confidence: `consensus`
- expected_ev_effect: Investigate the entry funnel for swing-specific bottlenecks.

### 2. No completed swing trades in analysis window

- finding_id: `swing_pattern_lab_deepseek_holding_exit_no_trades`
- lifecycle_stage: `holding_exit`
- route: `defer_evidence`
- priority: `LOW`
- mapped_family: `-`
- confidence: `low_sample`
- expected_ev_effect: Insufficient evidence; defer until more trades complete.

### 3. Scale-in events observed for swing positions

- finding_id: `swing_pattern_lab_deepseek_scale_in_events_observed`
- lifecycle_stage: `scale_in`
- route: `attach_existing_family`
- priority: `MEDIUM`
- mapped_family: `swing_scale_in_ofi_qi_confirmation`
- confidence: `consensus`
- expected_ev_effect: Evaluate PYRAMID/AVG_DOWN outcome quality with OFI/QI confirmation.

### 4. OFI/QI stale/missing quality review

- finding_id: `swing_pattern_lab_deepseek_ofi_qi_stale_missing`
- lifecycle_stage: `ofi_qi`
- route: `implement_now`
- priority: `HIGH`
- mapped_family: `swing_entry_ofi_qi_execution_quality`
- confidence: `consensus`
- expected_ev_effect: If stale ratio > 0.3, consider instrumentation/observer enhancement.

### 5. OFI/QI exit smoothing action distribution

- finding_id: `swing_pattern_lab_deepseek_ofi_qi_smoothing_review`
- lifecycle_stage: `ofi_qi`
- route: `attach_existing_family`
- priority: `MEDIUM`
- mapped_family: `swing_exit_ofi_qi_smoothing`
- confidence: `solo`
- expected_ev_effect: Monitor DEBOUNCE_EXIT/CONFIRM_EXIT rate for holding flow quality.

