# Model Training Traceability

## Purpose

`src/model` swing v2 model upgrades use MLflow tracking as a traceability layer and keep the repository model registry as the active source of truth.

## Active Source Of Truth

- Active manifest: `data/model_registry/swing_v2/current.json`
- Active artifacts: `data/hybrid_xgb_v2.pkl`, `data/hybrid_lgbm_v2.pkl`, `data/bull_xgb_v2.pkl`, `data/bull_lgbm_v2.pkl`, `data/stacking_meta_v2.pkl`
- Live recommendation inputs: `data/daily_recommendations_v2.csv`, `data/daily_recommendations_v2_diagnostics.json`

## MLflow Tracking

- Package: `mlflow-skinny==3.12.0`
- Tracking URI: `file:data/model_registry/swing_v2/mlruns`
- Experiment: `korstockscan_swing_v2_model_upgrade`
- Required tags/params: `run_id`, `git_commit`, `target_date`, `candidate_family`, `feature_set_version`, `label_policy`, `active_live_behavior`
- Required metrics: `equal_weight_avg_profit_pct`, `notional_weighted_ev_pct`, `source_quality_adjusted_ev_pct`, `downside_p10_pct`, `diagnostic_win_rate`, `selected_count`, `sample_count`

MLflow is a traceability and review surface only. Active model ownership stays with `current.json` and the copied artifact files.

## AI Tier2 Fail-Closed Promotion Gate

- Provider env: `KORSTOCKSCAN_SWING_MODEL_TIER2_REVIEW_PROVIDER=openai`
- Review report: `data/report/swing_model_tier2_review/swing_model_tier2_review_YYYY-MM-DD.{json,md}`
- Required pass condition: deterministic gate passed, AI Tier2 `status=parsed`, AI Tier2 `decision=approved`, recommendation smoke passed, and CSV/diagnostics schema compatibility passed.
- Fail-closed states: API unavailable, parse rejected, unknown status/decision, blocked decision, explicit label/source/schema/metric/forbidden-use gap, or active artifact path inconsistency.
- Status surface: `auto_retrain_pipeline.sh` writes `blocked_ai_tier2` when the pipeline exits successfully but AI Tier2 blocks promotion.
- MLflow records `ai_tier2_status`, `ai_tier2_decision`, and `ai_tier2_blocking_reasons` for blocked and promoted runs.

AI Tier2 cannot create a candidate, override a deterministic gate failure, change a runtime threshold, change providers, restart the bot, release caps, disable swing dry-run, enable real orders, or relax hard safety.

## AI Tier2 Blocked Auto-Remediation

- Remediation manifest: `data/model_registry/swing_v2/remediation/remediation_YYYY-MM-DD.json`
- Remediation report: `data/report/swing_model_remediation/swing_model_remediation_YYYY-MM-DD.{json,md}`
- Allowed retry env keys are limited to `KORSTOCKSCAN_SWING_RETRAIN_FORCE`, `KORSTOCKSCAN_SWING_MODEL_OPTUNA_TRIALS`, `KORSTOCKSCAN_SWING_MODEL_OPTUNA_TIMEOUT_SEC`, `KORSTOCKSCAN_SWING_MODEL_UPGRADE_FAMILIES`, and `KORSTOCKSCAN_SWING_MODEL_TIER2_REVIEW_PROVIDER`.
- `retry_allowed` may only regenerate training/backtest/recommendation artifacts and must pass the same deterministic gate, AI Tier2 gate, and recommendation smoke before promotion.
- `retry_deferred`, `manual_required`, and `blocked_forbidden_use` keep active artifacts unchanged.
- Label policy, feature semantics, metric contract, active promotion criteria, dry-run state, real orders, caps, provider route, bot state, hard safety, and intraday thresholds are not auto-remediation surfaces.

## Promotion Contract

- Primary metric: `equal_weight_avg_profit_pct`
- Candidate must beat incumbent by at least `+0.50pp`.
- Candidate downside p10 worsening must be `<=0.50pp`.
- Candidate selected count drop must be `<=30%`.
- Candidate sample count must be `>=40`.
- Recommendation CSV and diagnostics schema must remain compatible with existing scanner consumers.
- Promotion smoke must regenerate `data/daily_recommendations_v2.csv` and `data/daily_recommendations_v2_diagnostics.json`; if either schema check fails, the artifact copy is rolled back and `current.json` is not updated.

Promotion changes active model artifacts only. It must not disable swing dry-run, approve real-order conversion, release caps, change provider route, restart the bot, relax hard safety, or mutate intraday thresholds.
