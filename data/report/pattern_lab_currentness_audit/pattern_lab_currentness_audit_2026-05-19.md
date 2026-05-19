# Pattern Lab Currentness Audit - 2026-05-19

## Summary

- status: `pass`
- runtime_effect: `False`
- decision_authority: `source_quality_only`
- check_count: `12`
- fail_count: `0`
- code_improvement_orders: `0`

## Checks

### `gemini_scalping_metric_contract`

- status: `pass`
- severity: `info`
- finding: gemini_scalping output must expose schema_version>=2 and required metric_contract fields.
- sources: `['analysis/gemini_scalping_pattern_lab/outputs/ev_analysis_result.json']`

### `gemini_scalping_observability_metric_contract`

- status: `pass`
- severity: `info`
- finding: gemini_scalping tuning observability output must expose the common metric contract.
- sources: `['analysis/gemini_scalping_pattern_lab/outputs/tuning_observability_summary.json']`

### `gemini_scalping_manifest_freshness`

- status: `pass`
- severity: `info`
- finding: gemini_scalping manifest must cover target_date=2026-05-19; stale outputs cannot be reused as fresh source.
- sources: `['analysis/gemini_scalping_pattern_lab/outputs/run_manifest.json']`

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

### `claude_scalping_manifest_freshness`

- status: `pass`
- severity: `info`
- finding: claude_scalping manifest must cover target_date=2026-05-19; stale outputs cannot be reused as fresh source.
- sources: `['analysis/claude_scalping_pattern_lab/outputs/run_manifest.json']`

### `deepseek_swing_metric_contract`

- status: `pass`
- severity: `info`
- finding: deepseek_swing output must expose schema_version>=2 and required metric_contract fields.
- sources: `['analysis/deepseek_swing_pattern_lab/outputs/swing_pattern_analysis_result.json']`

### `deepseek_swing_manifest_freshness`

- status: `pass`
- severity: `info`
- finding: deepseek_swing manifest must cover target_date=2026-05-19; stale outputs cannot be reused as fresh source.
- sources: `['analysis/deepseek_swing_pattern_lab/outputs/run_manifest.json']`

### `active_source_forbidden_terms`

- status: `pass`
- severity: `info`
- finding: Active pattern lab code/docs/prompts must not use legacy shadow-only or canary-ready wording.
- sources: `['analysis']`

### `gemini_remote_default_excluded`

- status: `pass`
- severity: `info`
- finding: Gemini remote logs must be excluded by default and enabled only by PATTERN_LAB_INCLUDE_REMOTE=true.
- sources: `['analysis/gemini_scalping_pattern_lab/config.py']`

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
