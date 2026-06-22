# Pattern Lab Currentness Audit - 2026-06-22

## Summary

- status: `pass`
- runtime_effect: `False`
- decision_authority: `source_quality_only`
- check_count: `12`
- fail_count: `0`
- code_improvement_orders: `0`

## Checks

### `claude_scalping_metric_contract`

- status: `pass`
- severity: `info`
- finding: claude_scalping output must expose schema_version>=2 and required metric_contract fields.
- sources: `['analysis/claude_scalping_pattern_lab/outputs/ev_analysis_result.json']`

### `claude_scalping_observability_metric_contract`

- status: `pass`
- severity: `info`
- finding: claude_scalping tuning observability output must expose the common metric contract.
- sources: `['analysis/claude_scalping_pattern_lab/outputs/tuning_observability_summary.json']`

### `claude_scalping_observability_source_contract`

- status: `pass`
- severity: `info`
- finding: claude_scalping tuning observability output must expose schema_version>=3, source_quality, source_contract_status=pass, and source contract workorders when producer/consumer inputs drift.
- sources: `['analysis/claude_scalping_pattern_lab/outputs/tuning_observability_summary.json']`

### `claude_scalping_manifest_freshness`

- status: `pass`
- severity: `info`
- finding: claude_scalping manifest must cover target_date=2026-06-22; stale outputs cannot be reused as fresh source.
- sources: `['analysis/claude_scalping_pattern_lab/outputs/run_manifest.json']`

### `deepseek_swing_metric_contract`

- status: `pass`
- severity: `info`
- finding: deepseek_swing output must expose schema_version>=2 and required metric_contract fields.
- sources: `['analysis/deepseek_swing_pattern_lab/outputs/swing_pattern_analysis_result.json']`

### `deepseek_swing_manifest_freshness`

- status: `pass`
- severity: `info`
- finding: deepseek_swing manifest must cover target_date=2026-06-22; stale outputs cannot be reused as fresh source.
- sources: `['analysis/deepseek_swing_pattern_lab/outputs/run_manifest.json']`

### `active_source_forbidden_terms`

- status: `pass`
- severity: `info`
- finding: Active pattern lab code/docs/prompts must not use legacy shadow-only or canary-ready wording.
- sources: `['analysis']`

### `claude_empty_trade_fact_overwrite_guard`

- status: `pass`
- severity: `info`
- finding: Claude empty input must overwrite trade_fact.csv with header-only CSV to prevent stale reuse.
- sources: `['analysis/claude_scalping_pattern_lab/prepare_dataset.py']`

### `deepseek_sim_probe_provenance`

- status: `pass`
- severity: `info`
- finding: DeepSeek swing sim/probe/dry-run outputs must include actual_order_submitted/broker_order_forbidden/decision_authority provenance.
- sources: `['analysis/deepseek_swing_pattern_lab/outputs/data_quality_report.json']`

### `scalping_ldm_threshold_reentry_sources`

- status: `pass`
- severity: `info`
- finding: Scalping pattern labs must consume threshold_cycle_ev, lifecycle_decision_matrix, and lifecycle_bucket_discovery as re-entry sources so LDM/threshold outcomes improve the next lab run.
- sources: `['analysis/claude_scalping_pattern_lab']`

### `swing_ldm_threshold_reentry_sources`

- status: `pass`
- severity: `info`
- finding: DeepSeek swing pattern lab must consume threshold_cycle_ev, swing_lifecycle_decision_matrix, swing_lifecycle_bucket_discovery, and swing_strategy_discovery_ev as re-entry sources.
- sources: `['analysis/deepseek_swing_pattern_lab']`

### `pattern_lab_ai_review_contract`

- status: `pass`
- severity: `info`
- finding: Pattern lab must have a source-only two-pass AI reviewer contract: first interpretation, second-pass audit, and final conclusions that re-rank findings against LDM/threshold/workorder feedback and emit explicit source-quality gaps.
- sources: `['src/engine', 'analysis/claude_scalping_pattern_lab', 'analysis/deepseek_swing_pattern_lab']`
