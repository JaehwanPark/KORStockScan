# DeepSeek Swing Pattern Lab - Final Review Report

## 판정

- 분석 기간: `2026-07-21` ~ `2026-07-21`
- trade_rows: `0`
- lifecycle_event_rows: `3`
- completed_valid_profit_rows: `0`
- ofi_qi_rows: `0`
- total_findings: `3`
- code_improvement_orders: `2`
- runtime_change: `False`

## 분류 요약

- implement_now: `0`
- attach_existing_family: `1`
- design_family_candidate: `1`
- defer_evidence: `1`
- reject: `0`

## Stage별 분석

- `entry`: 1 findings
- `holding_exit`: 1 findings
- `selection`: 1 findings

## Stage Findings

### 1. `swing_pattern_lab_deepseek_selection_low_candidate_count`

- title: Low swing candidate count per day
- lifecycle_stage: `selection`
- route: `attach_existing_family`
- mapped_family: `swing_selection_top_k`
- confidence: `solo`
- runtime_effect: `False`
- expected_ev_effect: Increase top_k or adjust floor slightly to expand candidate pool.

### 2. `swing_pattern_lab_deepseek_entry_no_submissions`

- title: All selected candidates failed to reach order submission
- lifecycle_stage: `entry`
- route: `design_family_candidate`
- mapped_family: `-`
- confidence: `solo`
- runtime_effect: `False`
- expected_ev_effect: Investigate the entry funnel for swing-specific bottlenecks.

### 3. `swing_pattern_lab_deepseek_holding_exit_no_trades`

- title: No completed swing trades in analysis window
- lifecycle_stage: `holding_exit`
- route: `defer_evidence`
- mapped_family: `-`
- confidence: `low_sample`
- runtime_effect: `False`
- expected_ev_effect: Insufficient evidence; defer until more trades complete.

## Code Improvement Orders

### 1. `order_swing_pattern_lab_deepseek_selection_low_candidate_count`

- title: Low swing candidate count per day
- lifecycle_stage: `selection`
- target_subsystem: `swing_model_selection`
- route: `attach_existing_family`
- mapped_family: `swing_selection_top_k`
- threshold_family: `swing_selection_top_k`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- expected_ev_effect: Increase top_k or adjust floor slightly to expand candidate pool.
- files_likely_touched: `src/engine/swing_lifecycle_audit.py`, `src/engine/swing_selection_funnel_report.py`, `src/model/common_v2.py`

### 2. `order_swing_pattern_lab_deepseek_entry_no_submissions`

- title: All selected candidates failed to reach order submission
- lifecycle_stage: `entry`
- target_subsystem: `swing_entry_funnel`
- route: `design_family_candidate`
- mapped_family: `-`
- threshold_family: `-`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- expected_ev_effect: Investigate the entry funnel for swing-specific bottlenecks.
- files_likely_touched: `src/engine/swing_lifecycle_audit.py`, `src/engine/swing_selection_funnel_report.py`, `src/model/common_v2.py`

## Data Quality Warnings

- no OFI/QI micro context data found
