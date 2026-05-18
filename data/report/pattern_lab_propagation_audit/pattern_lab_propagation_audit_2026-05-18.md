# Pattern Lab Propagation Audit - 2026-05-18

## Summary

- status: `warning`
- runtime_effect: `False`
- decision_authority: `source_quality_only`
- check_count: `11`
- fail_count: `0`
- warning_count: `1`

## Checks

### `scalping_gemini_automation_fresh`

- status: `pass`
- severity: `info`
- finding: fresh lab automation source is available
- sources: `['/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-05-18.json']`

### `scalping_claude_automation_fresh`

- status: `pass`
- severity: `info`
- finding: fresh lab automation source is available
- sources: `['/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-05-18.json']`

### `deepseek_swing_automation_fresh`

- status: `pass`
- severity: `info`
- finding: fresh lab automation source is available
- sources: `['/home/ubuntu/KORStockScan/data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_2026-05-18.json']`

### `currentness_audit_available`

- status: `pass`
- severity: `info`
- finding: currentness audit must exist before code workorder build.
- sources: `['/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-05-18.json']`

### `workorder_consumes_currentness_audit`

- status: `pass`
- severity: `info`
- finding: code_improvement_workorder must include pattern_lab_currentness_audit in source lineage.
- sources: `['/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-05-18.json', '/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-05-18.json']`

### `workorder_currentness_order_count`

- status: `pass`
- severity: `info`
- finding: currentness audit selected orders must be counted by code_improvement_workorder.
- sources: `['/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-05-18.json', '/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-05-18.json']`

### `threshold_cycle_ev_currentness_source_link`

- status: `pass`
- severity: `info`
- finding: threshold_cycle_ev must expose pattern_lab_currentness_audit source link.
- sources: `['/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-18.json', '/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-05-18.json']`

### `threshold_cycle_ev_propagation_source_link`

- status: `pass`
- severity: `info`
- finding: threshold_cycle_ev must expose pattern_lab_propagation_audit after the post-propagation EV refresh.
- sources: `['/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-18.json', '/home/ubuntu/KORStockScan/data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_2026-05-18.json']`

### `runtime_summary_propagation_source_link`

- status: `warning`
- severity: `runtime_summary_pending`
- finding: runtime_approval_summary must expose pattern_lab_propagation_audit source link when generated after this audit.
- sources: `['/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-05-18.json', '/home/ubuntu/KORStockScan/data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_2026-05-18.json']`

### `deepseek_sim_probe_provenance_propagated`

- status: `pass`
- severity: `info`
- finding: DeepSeek sim/probe provenance must be present before downstream propagation can be trusted.
- sources: `['/home/ubuntu/KORStockScan/analysis/deepseek_swing_pattern_lab/outputs/data_quality_report.json', '/home/ubuntu/KORStockScan/data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_2026-05-18.json']`

### `runtime_effect_false_contract`

- status: `pass`
- severity: `info`
- finding: pattern lab source artifacts and workorders must not set runtime_effect=true/runtime_change=true. No violations.
- sources: `['/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-05-18.json', '/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-05-18.json', '/home/ubuntu/KORStockScan/data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_2026-05-18.json', '/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-05-18.json']`
