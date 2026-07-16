import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.model import common_v2
from src.model import backtest_v2
from src.model import recommend_daily_v2 as reco
from src.model import swing_bull_period_ai_review as bull_review
from src.model import swing_model_auto_remediation as remediation
from src.model import swing_model_tier2_review as tier2_review
from src.model import swing_model_tracking
from src.model import swing_retrain_pipeline as pipeline


class _DummyModel:
    def __init__(self, value):
        self.value = value

    def predict_proba(self, frame):
        return np.array([[1.0 - self.value, self.value] for _ in range(len(frame))])

    def predict(self, frame):
        return [0.5 for _ in range(len(frame))]


def _artifact(value):
    return {
        "model": _DummyModel(value),
        "calibrator": common_v2.IdentityCalibrator(),
        "features": ["f"],
    }


def test_build_base_score_frame_disabled_neutralizes_bull_without_loading_bull(
    monkeypatch,
):
    loaded = []

    def fake_load(path):
        loaded.append(str(path))
        if "bull_" in str(path):
            raise AssertionError("bull artifact should not be loaded in disabled mode")
        return _artifact(0.7 if "xgb" in str(path) else 0.3)

    monkeypatch.setattr(common_v2, "load_model_artifact", fake_load)
    df = pd.DataFrame(
        [
            {
                "date": pd.Timestamp("2026-05-08"),
                "code": "000001",
                "name": "A",
                "bull_regime": 1,
                "idx_ret20": 0.1,
                "idx_atr_ratio": 0.02,
                "f": 1.0,
            }
        ]
    )

    scored = common_v2.build_base_score_frame(df, bull_mode="disabled")

    assert scored.iloc[0]["bx"] == scored.iloc[0]["hx"]
    assert scored.iloc[0]["bl"] == scored.iloc[0]["hl"]
    assert scored.iloc[0]["bull_mean"] == scored.iloc[0]["hybrid_mean"]
    assert scored.iloc[0]["bull_hybrid_gap"] == 0.0
    assert scored.iloc[0]["bull_score_source"] == "neutralized_from_hybrid"
    assert bool(scored.iloc[0]["bull_artifact_used"]) is False
    assert len(loaded) == 2


def test_recommend_daily_disabled_writes_bull_provenance(tmp_path, monkeypatch):
    latest = pd.Timestamp("2026-05-08")
    panel = pd.DataFrame(
        [
            {
                "date": latest,
                "code": "000001",
                "name": "A",
                "close": 1000,
                "bull_regime": 1,
                "idx_ret20": 0.1,
                "idx_atr_ratio": 0.02,
            }
        ]
    )
    scored = panel.copy()
    scored["hx"] = 0.7
    scored["hl"] = 0.3
    scored["bx"] = 0.7
    scored["bl"] = 0.3
    scored["mean_prob"] = 0.5
    scored["std_prob"] = 0.2
    scored["max_prob"] = 0.7
    scored["min_prob"] = 0.3
    scored["bull_mean"] = 0.5
    scored["hybrid_mean"] = 0.5
    scored["bull_hybrid_gap"] = 0.0
    scored["bull_specialist_mode"] = "disabled"
    scored["bull_score_source"] = "neutralized_from_hybrid"
    scored["bull_artifact_used"] = False

    monkeypatch.setattr(reco, "get_latest_quote_date", lambda: latest)
    monkeypatch.setattr(reco, "get_top_kospi_codes", lambda limit=300: ["000001"])
    monkeypatch.setattr(reco, "build_panel_dataset", lambda *args, **kwargs: panel)
    monkeypatch.setattr(
        reco, "build_base_score_frame", lambda *args, **kwargs: scored.copy()
    )
    monkeypatch.setattr(
        reco, "load_model_artifact", lambda path: {"model": _DummyModel(0.5)}
    )
    monkeypatch.setattr(reco, "RECO_PATH", str(tmp_path / "reco.csv"))
    monkeypatch.setattr(reco, "RECO_DIAGNOSTIC_PATH", str(tmp_path / "diag.csv"))
    monkeypatch.setattr(reco, "RECO_DIAGNOSTIC_JSON_PATH", str(tmp_path / "diag.json"))

    reco.recommend_daily_v2(bull_mode="disabled")

    summary = json.loads((tmp_path / "diag.json").read_text(encoding="utf-8"))
    assert summary["bull_specialist_mode"] == "disabled"
    assert summary["bull_score_source"] == "neutralized_from_hybrid"
    assert summary["bull_artifact_used"] is False
    assert summary["selected_count"] == 1


def test_evaluate_bull_specialist_mode_enabled_disabled_and_hold():
    enabled = {
        "sample_count": 20,
        "avg_net_pct": 0.4,
        "downside_p10_pct": -1.0,
        "selected_count": 8,
    }
    disabled = {
        "sample_count": 20,
        "avg_net_pct": 0.2,
        "downside_p10_pct": -1.1,
        "selected_count": 8,
    }
    assert (
        pipeline.evaluate_bull_specialist_mode(enabled, disabled)[
            "bull_specialist_mode"
        ]
        == "enabled"
    )

    weak = {
        "sample_count": 20,
        "avg_net_pct": 0.1,
        "downside_p10_pct": -1.8,
        "selected_count": 8,
    }
    assert (
        pipeline.evaluate_bull_specialist_mode(weak, disabled)["bull_specialist_mode"]
        == "disabled"
    )

    small = {
        "sample_count": 2,
        "avg_net_pct": 0.9,
        "downside_p10_pct": -0.5,
        "selected_count": 8,
    }
    assert (
        pipeline.evaluate_bull_specialist_mode(small, disabled)["bull_specialist_mode"]
        == "hold_current"
    )


def test_mlflow_tracking_uri_defaults_to_plan_contract(monkeypatch):
    monkeypatch.delenv("KORSTOCKSCAN_SWING_MODEL_MLFLOW_TRACKING_URI", raising=False)

    assert (
        swing_model_tracking.tracking_uri()
        == "file:data/model_registry/swing_v2/mlruns"
    )


def test_backtest_v2_uses_configured_max_hold_days_for_time_exit(monkeypatch):
    class DummyConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class DummyEngine:
        def connect(self):
            return DummyConnection()

    pred = pd.DataFrame(
        [
            {
                "date": "2026-05-01",
                "code": "000001",
                "name": "A",
                "score": 0.8,
                "hybrid_mean": 0.8,
                "bull_regime": 1,
            }
        ]
    )
    prices = pd.DataFrame(
        {
            "quote_date": pd.date_range("2026-05-04", periods=4, freq="B"),
            "stock_code": ["000001"] * 4,
            "open_price": [100.0] * 4,
            "high_price": [101.0] * 4,
            "low_price": [99.0] * 4,
            "close_price": [100.0] * 4,
        }
    )

    monkeypatch.setattr(backtest_v2, "engine", DummyEngine())
    monkeypatch.setattr(backtest_v2.pd, "read_csv", lambda path: pred.copy())
    monkeypatch.setattr(backtest_v2.pd, "read_sql", lambda query, conn: prices.copy())

    result = backtest_v2.run_backtest_v2(save=False, max_hold_days=4)

    assert len(result) == 1
    assert result.iloc[0]["hold_days"] == 4
    assert result.iloc[0]["exit_reason"] == "TIME"


def test_bull_period_guard_blocks_leakage_and_uses_hold_current():
    proposal = {
        "bull_specialist_mode": "enabled",
        "bull_base_start": "2026-01-01",
        "bull_base_end": "2026-05-10",
    }

    report = bull_review.guard_bull_period_proposal(
        proposal,
        target_date="2026-05-10",
        stats={"bull_rows": 5000, "bull_trading_days": 80},
    )

    assert report["guard"]["passed"] is False
    assert "label_safety_gap_violation" in report["guard"]["reasons"]
    assert report["decision"]["bull_specialist_mode"] == "hold_current"


def test_promote_candidate_disabled_removes_active_bull_and_rollback_restores(
    tmp_path, monkeypatch
):
    data_dir = tmp_path / "data"
    run_dir = tmp_path / "run"
    backup_dir = tmp_path / "backup"
    data_dir.mkdir()
    run_dir.mkdir()
    for name in pipeline.ACTIVE_MODEL_FILES:
        (data_dir / name).write_text(f"active:{name}", encoding="utf-8")
    for name in pipeline.REQUIRED_NON_BULL_FILES:
        (run_dir / name).write_text(f"candidate:{name}", encoding="utf-8")
    monkeypatch.setattr(pipeline, "DATA_DIR", str(data_dir))

    result = pipeline._promote_candidate(run_dir, backup_dir, "disabled")

    assert "bull_xgb_v2.pkl" not in result["promoted_files"]
    assert not (data_dir / "bull_xgb_v2.pkl").exists()
    assert (
        (data_dir / "stacking_meta_v2.pkl")
        .read_text(encoding="utf-8")
        .startswith("candidate:")
    )

    restored = pipeline._rollback_active_models(backup_dir)

    assert "bull_xgb_v2.pkl" in restored
    assert (
        (data_dir / "bull_xgb_v2.pkl").read_text(encoding="utf-8").startswith("active:")
    )


def test_rollback_removes_artifacts_that_were_absent_before_promotion(
    tmp_path, monkeypatch
):
    data_dir = tmp_path / "data"
    run_dir = tmp_path / "run"
    backup_dir = tmp_path / "backup"
    data_dir.mkdir()
    run_dir.mkdir()
    for name in pipeline.REQUIRED_NON_BULL_FILES:
        (data_dir / name).write_text(f"active:{name}", encoding="utf-8")
    for name in pipeline.ACTIVE_MODEL_FILES:
        (run_dir / name).write_text(f"candidate:{name}", encoding="utf-8")
    monkeypatch.setattr(pipeline, "DATA_DIR", str(data_dir))

    pipeline._promote_candidate(run_dir, backup_dir, "enabled")
    assert (data_dir / "bull_xgb_v2.pkl").exists()

    restored = pipeline._rollback_active_models(backup_dir)

    assert "removed:bull_xgb_v2.pkl" in restored
    assert "removed:bull_lgbm_v2.pkl" in restored
    assert not (data_dir / "bull_xgb_v2.pkl").exists()
    assert (
        (data_dir / "stacking_meta_v2.pkl")
        .read_text(encoding="utf-8")
        .startswith("active:")
    )


def test_pipeline_trains_enabled_and_disabled_then_selects_better_candidate(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(pipeline, "RUNS_DIR", tmp_path / "runs")
    monkeypatch.setattr(pipeline, "PROMOTIONS_DIR", tmp_path / "promotions")
    monkeypatch.setattr(pipeline, "REPORT_DIR", tmp_path / "reports")
    monkeypatch.setattr(
        pipeline,
        "write_diagnosis",
        lambda target, force=False: {"retrain_required": True},
    )
    monkeypatch.setattr(
        pipeline,
        "write_review",
        lambda target: {
            "decision": {
                "bull_specialist_mode": "enabled",
                "bull_base_start": "2024-05-01",
                "bull_base_end": "2026-05-01",
            }
        },
    )

    trained = []

    def fake_train_and_evaluate(parent_run_dir, mode, bull_review, **kwargs):
        trained.append(mode)
        assert kwargs["meta_period"]["meta_end"] == "2026-05-05"
        metrics_by_mode = {
            "enabled": {
                "available": True,
                "sample_count": 50,
                "selected_count": 10,
                "avg_net_pct": 0.35,
                "downside_p10_pct": -1.00,
                "win_rate": 0.60,
                "tradeoff_score": 0.80,
            },
            "disabled": {
                "available": True,
                "sample_count": 50,
                "selected_count": 10,
                "avg_net_pct": 0.15,
                "downside_p10_pct": -1.10,
                "win_rate": 0.52,
                "tradeoff_score": 0.70,
            },
        }
        run_dir = parent_run_dir / mode
        run_dir.mkdir(parents=True, exist_ok=True)
        return {
            "bull_specialist_mode": mode,
            "run_dir": str(run_dir),
            "command_results": [{"returncode": 0, "mode": mode}],
            "failed": False,
            "missing_artifacts": [],
            "metrics": metrics_by_mode[mode],
        }

    monkeypatch.setattr(pipeline, "_train_and_evaluate_mode", fake_train_and_evaluate)
    monkeypatch.setattr(
        pipeline,
        "resolve_meta_period",
        lambda target: {
            "meta_start": "2026-01-01",
            "meta_end": "2026-05-05",
            "latest_quote_date": "2026-05-10",
            "label_safety_days": 5,
        },
    )
    monkeypatch.setattr(
        pipeline,
        "_promote_candidate",
        lambda run_dir, backup_dir, mode: {"promoted_files": [mode]},
    )
    monkeypatch.setattr(
        pipeline, "_smoke_after_promote", lambda mode: {"returncode": 0}
    )
    monkeypatch.setattr(
        pipeline, "_validate_live_recommendation_schema", lambda: {"passed": True}
    )
    monkeypatch.setattr(
        pipeline,
        "write_tier2_review_report",
        lambda **kwargs: {
            "status": "parsed",
            "decision": "approved",
            "approved": True,
            "blocking_reasons": [],
            "json_path": str(tmp_path / "tier2.json"),
            "markdown_path": str(tmp_path / "tier2.md"),
        },
    )
    monkeypatch.setattr(
        pipeline,
        "_write_current_manifest",
        lambda run_id, target_date, run_dir, mode, metrics, **kwargs: tmp_path
        / "current.json",
    )
    monkeypatch.setattr(pipeline, "BENCHMARK_REPORT_DIR", tmp_path / "benchmark")
    monkeypatch.setattr(
        pipeline, "log_model_run", lambda **kwargs: {"status": "skipped_test"}
    )

    report = pipeline.run_pipeline("2026-05-10", auto_promote=True, force=True)

    assert trained == ["enabled", "disabled"]
    assert report["bull_specialist_mode"] == "enabled"
    assert report["bull_mode_decision"]["reason"] == "enabled_outperformed_disabled"
    assert report["promoted"] is True
    assert set(report["candidate_results"]) == {"enabled", "disabled"}
    assert report["meta_period"]["meta_end"] == "2026-05-05"
    assert report["promotion_guard"] == {
        "min_tradeoff_score": 0.72,
        "sample_floor": 40,
        "avg_net_floor_pct": 0.10,
        "candidate_score": 0.80,
        "sample_count": 50,
        "avg_net_pct": 0.35,
        "sample_floor_passed": True,
        "avg_net_floor_passed": True,
        "tradeoff_score_floor_passed": True,
        "decision": "promoted",
        "reason": "enabled_outperformed_disabled",
        "bull_specialist_mode": "enabled",
    }
    assert report["ai_tier2_review"]["status"] == "parsed"


def test_pipeline_blocks_auto_promotion_when_tier2_unavailable(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "RUNS_DIR", tmp_path / "runs")
    monkeypatch.setattr(pipeline, "PROMOTIONS_DIR", tmp_path / "promotions")
    monkeypatch.setattr(pipeline, "REPORT_DIR", tmp_path / "reports")
    monkeypatch.setattr(pipeline, "BENCHMARK_REPORT_DIR", tmp_path / "benchmark")
    monkeypatch.setattr(
        pipeline,
        "write_diagnosis",
        lambda target, force=False: {"retrain_required": True},
    )
    monkeypatch.setattr(
        pipeline,
        "write_review",
        lambda target: {
            "decision": {
                "bull_specialist_mode": "enabled",
                "bull_base_start": "2024-05-01",
                "bull_base_end": "2026-05-01",
            }
        },
    )
    monkeypatch.setattr(
        pipeline,
        "resolve_meta_period",
        lambda target: {
            "meta_start": "2026-01-01",
            "meta_end": "2026-05-05",
            "latest_quote_date": "2026-05-10",
            "label_safety_days": 5,
        },
    )

    def fake_train_and_evaluate(parent_run_dir, mode, bull_review, **kwargs):
        run_dir = parent_run_dir / mode
        run_dir.mkdir(parents=True, exist_ok=True)
        return {
            "bull_specialist_mode": mode,
            "run_dir": str(run_dir),
            "command_results": [{"returncode": 0, "mode": mode}],
            "failed": False,
            "missing_artifacts": [],
            "metrics": {
                "available": True,
                "sample_count": 50,
                "selected_count": 10,
                "avg_net_pct": 0.35 if mode == "enabled" else 0.15,
                "equal_weight_avg_profit_pct": 0.35 if mode == "enabled" else 0.15,
                "downside_p10_pct": -1.00,
                "win_rate": 0.60,
                "tradeoff_score": 0.80 if mode == "enabled" else 0.70,
            },
        }

    monkeypatch.setattr(pipeline, "_train_and_evaluate_mode", fake_train_and_evaluate)
    monkeypatch.setattr(
        pipeline,
        "write_tier2_review_report",
        lambda **kwargs: {
            "status": "unavailable",
            "decision": "blocked",
            "approved": False,
            "blocking_reasons": ["OPENAI_API_KEY not configured"],
            "json_path": str(tmp_path / "tier2.json"),
            "markdown_path": str(tmp_path / "tier2.md"),
            "forbidden_runtime_uses": ["real_order_conversion"],
        },
    )
    monkeypatch.setattr(
        pipeline,
        "write_remediation_report",
        lambda **kwargs: {
            "remediation_state": "retry_deferred",
            "retry_reason": "deferred_until_next_source_or_ai_availability",
            "retry_count": 0,
            "max_retry_count": 1,
            "next_cron_allowed": False,
            "retry_env": {},
            "manifest_path": str(tmp_path / "remediation.json"),
            "json_path": str(tmp_path / "remediation_report.json"),
            "markdown_path": str(tmp_path / "remediation_report.md"),
        },
    )
    monkeypatch.setattr(
        pipeline,
        "_promote_candidate",
        lambda run_dir, backup_dir, mode: (_ for _ in ()).throw(
            AssertionError("promotion must be blocked before copy")
        ),
    )
    monkeypatch.setattr(
        pipeline, "log_model_run", lambda **kwargs: {"status": "skipped_test"}
    )

    report = pipeline.run_pipeline("2026-05-10", auto_promote=True, force=True)

    assert report["status"] == "not_promoted_ai_tier2_blocked"
    assert report["promoted"] is False
    assert report["active_live_behavior"] is False
    assert report["promotion"]["blocked_reason"] == "ai_tier2_not_approved"
    assert report["promotion"]["ai_tier2_review"]["status"] == "unavailable"
    assert report["remediation"]["remediation_state"] == "retry_deferred"


def test_remediation_deferred_for_ai_unavailable(tmp_path, monkeypatch):
    monkeypatch.setattr(remediation, "REMEDIATION_DIR", tmp_path / "remediation")
    monkeypatch.setattr(remediation, "REPORT_DIR", tmp_path / "reports")

    report = remediation.write_remediation_report(
        target_date="2026-05-26",
        tier2_review={
            "status": "unavailable",
            "decision": "blocked",
            "blocking_reasons": ["OPENAI_API_KEY not configured"],
        },
    )

    assert report["remediation_state"] == "retry_deferred"
    assert report["retry_env"] == {}
    assert report["next_cron_allowed"] is False
    assert Path(report["manifest_path"]).exists()


def test_remediation_schema_block_allows_safe_retry_env(tmp_path, monkeypatch):
    monkeypatch.setattr(remediation, "REMEDIATION_DIR", tmp_path / "remediation")
    monkeypatch.setattr(remediation, "REPORT_DIR", tmp_path / "reports")

    report = remediation.write_remediation_report(
        target_date="2026-05-26",
        tier2_review={
            "status": "parsed",
            "decision": "blocked",
            "blocking_reasons": ["schema_compatibility"],
        },
    )

    assert report["remediation_state"] == "retry_allowed"
    assert report["retry_env"] == {
        "KORSTOCKSCAN_SWING_RETRAIN_FORCE": "true",
        "KORSTOCKSCAN_SWING_MODEL_TIER2_REVIEW_PROVIDER": "openai",
    }
    assert report["next_cron_allowed"] is True


def test_remediation_candidate_artifact_retry_uses_capped_optuna_env(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(remediation, "REMEDIATION_DIR", tmp_path / "remediation")
    monkeypatch.setattr(remediation, "REPORT_DIR", tmp_path / "reports")
    benchmark_path = tmp_path / "benchmark.json"
    benchmark_path.write_text(
        json.dumps(
            {
                "candidate_results": {
                    "enabled": {"selected_candidate_family": "optuna_lgbm_ranker_v1"},
                    "disabled": {"selected_candidate_family": "unknown_family"},
                }
            }
        ),
        encoding="utf-8",
    )

    report = remediation.write_remediation_report(
        target_date="2026-05-26",
        tier2_review={
            "status": "parsed",
            "decision": "blocked",
            "blocking_reasons": ["candidate_artifact_missing"],
        },
        benchmark_report_paths={"json": str(benchmark_path)},
    )

    assert report["remediation_state"] == "retry_allowed"
    assert report["retry_env"]["KORSTOCKSCAN_SWING_MODEL_OPTUNA_TRIALS"] == "80"
    assert report["retry_env"]["KORSTOCKSCAN_SWING_MODEL_OPTUNA_TIMEOUT_SEC"] == "3600"
    assert (
        report["retry_env"]["KORSTOCKSCAN_SWING_MODEL_UPGRADE_FAMILIES"]
        == "optuna_lgbm_ranker_v1"
    )


def test_remediation_manual_for_label_and_metric_policy(tmp_path, monkeypatch):
    monkeypatch.setattr(remediation, "REMEDIATION_DIR", tmp_path / "remediation")
    monkeypatch.setattr(remediation, "REPORT_DIR", tmp_path / "reports")

    label = remediation.write_remediation_report(
        target_date="2026-05-26",
        tier2_review={
            "status": "parsed",
            "decision": "blocked",
            "blocking_reasons": ["label_leakage"],
        },
    )
    metric = remediation.write_remediation_report(
        target_date="2026-05-27",
        tier2_review={
            "status": "parsed",
            "decision": "blocked",
            "blocking_reasons": ["metric_contract"],
        },
    )

    assert label["remediation_state"] == "manual_required"
    assert label["retry_env"] == {}
    assert metric["remediation_state"] == "manual_required"
    assert metric["retry_env"] == {}


def test_remediation_forbidden_use_blocks_retry_env(tmp_path, monkeypatch):
    monkeypatch.setattr(remediation, "REMEDIATION_DIR", tmp_path / "remediation")
    monkeypatch.setattr(remediation, "REPORT_DIR", tmp_path / "reports")

    report = remediation.write_remediation_report(
        target_date="2026-05-26",
        tier2_review={
            "status": "parsed",
            "decision": "blocked",
            "blocking_reasons": ["forbidden_use"],
        },
    )

    assert report["remediation_state"] == "blocked_forbidden_use"
    assert report["retry_env"] == {}


def test_remediation_retry_budget_exhaustion_becomes_manual(tmp_path, monkeypatch):
    monkeypatch.setattr(remediation, "REMEDIATION_DIR", tmp_path / "remediation")
    monkeypatch.setattr(remediation, "REPORT_DIR", tmp_path / "reports")
    remediation.REMEDIATION_DIR.mkdir(parents=True)
    remediation.remediation_manifest_path("2026-05-26").write_text(
        json.dumps({"retry_count": 0}),
        encoding="utf-8",
    )

    report = remediation.write_remediation_report(
        target_date="2026-05-26",
        tier2_review={
            "status": "parsed",
            "decision": "blocked",
            "blocking_reasons": ["schema_compatibility"],
        },
    )

    assert report["retry_count"] == 1
    assert report["remediation_state"] == "manual_required"
    assert report["retry_env"] == {}


def test_remediation_resolver_sanitizes_disallowed_env(tmp_path, monkeypatch):
    monkeypatch.setattr(remediation, "REMEDIATION_DIR", tmp_path / "remediation")
    remediation.REMEDIATION_DIR.mkdir(parents=True)
    remediation.remediation_manifest_path("2026-05-26").write_text(
        json.dumps(
            {
                "remediation_state": "retry_allowed",
                "retry_count": 0,
                "max_retry_count": 1,
                "retry_reason": "schema_retry",
                "retry_env": {
                    "KORSTOCKSCAN_SWING_RETRAIN_FORCE": "true",
                    "KORSTOCKSCAN_SWING_MODEL_OPTUNA_TRIALS": "999",
                    "KORSTOCKSCAN_SCALPING_AI_ROUTE": "gemini",
                    "KORSTOCKSCAN_SWING_DRY_RUN_DISABLE": "true",
                },
            }
        ),
        encoding="utf-8",
    )

    resolved = remediation.resolve_cron_remediation("2026-05-26")

    assert resolved["action"] == "apply_retry_env"
    assert resolved["retry_env"] == {
        "KORSTOCKSCAN_SWING_RETRAIN_FORCE": "true",
        "KORSTOCKSCAN_SWING_MODEL_OPTUNA_TRIALS": "80",
    }
    assert (
        "removed_disallowed_env:KORSTOCKSCAN_SCALPING_AI_ROUTE" in resolved["warnings"]
    )


def test_tier2_review_parser_fail_closes_unknown_status_and_decision():
    parsed, warnings = tier2_review.parse_tier2_review_response(
        {
            "schema_version": 1,
            "status": "maybe",
            "decision": "ship_it",
            "blocking_reasons": [],
            "reviewed_candidate_family": "catboost_ranker_v1",
            "reviewed_bull_mode": "enabled",
            "checks": {key: "pass" for key in tier2_review.CHECK_KEYS},
        },
        expected_candidate_family="catboost_ranker_v1",
        expected_bull_mode="enabled",
    )

    assert parsed["status"] == "parse_rejected"
    assert parsed["decision"] == "blocked"
    assert "invalid_status" in warnings
    assert "invalid_decision" in warnings


def test_model_upgrade_promotion_gate_requires_ev_schema_sample_and_downside():
    incumbent = {
        "equal_weight_avg_profit_pct": 1.0,
        "downside_p10_pct": -2.0,
        "selected_count": 10,
    }
    candidate = {
        "equal_weight_avg_profit_pct": 1.7,
        "downside_p10_pct": -2.2,
        "selected_count": 9,
        "sample_count": 45,
    }

    passed = pipeline.evaluate_model_upgrade_promotion(
        candidate, incumbent, {"passed": True}
    )

    assert passed["passed"] is True
    assert passed["ev_delta_pct"] == 0.7
    assert passed["primary_decision_metric"] == "equal_weight_avg_profit_pct"

    blocked = pipeline.evaluate_model_upgrade_promotion(
        {**candidate, "sample_count": 12},
        incumbent,
        {"passed": False, "missing_columns": ["hybrid_mean"]},
    )

    assert blocked["passed"] is False
    assert "sample_floor_not_met" in blocked["reasons"]
    assert "schema_compatibility_failed" in blocked["reasons"]


def test_live_recommendation_schema_checks_csv_and_diagnostics(tmp_path, monkeypatch):
    csv_path = tmp_path / "daily_recommendations_v2.csv"
    diagnostics_path = tmp_path / "daily_recommendations_v2_diagnostics.json"
    row = {column: "x" for column in pipeline.REQUIRED_LIVE_RECOMMENDATION_COLUMNS}
    pd.DataFrame([row]).to_csv(csv_path, index=False)
    diagnostics_path.write_text(
        json.dumps(
            {key: "x" for key in pipeline.REQUIRED_RECOMMENDATION_DIAGNOSTIC_KEYS}
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(pipeline, "RECO_PATH", str(csv_path))
    monkeypatch.setattr(pipeline, "RECO_DIAGNOSTIC_JSON_PATH", str(diagnostics_path))

    passed = pipeline._validate_live_recommendation_schema()

    assert passed["passed"] is True

    diagnostics_path.write_text(
        json.dumps({"owner": "missing_fields"}), encoding="utf-8"
    )
    blocked = pipeline._validate_live_recommendation_schema()
    assert blocked["passed"] is False
    assert "latest_date" in blocked["diagnostic_json"]["missing_keys"]


def test_write_current_manifest_records_active_live_scope(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "REGISTRY_DIR", tmp_path)

    path = pipeline._write_current_manifest(
        "run-1",
        "2026-05-26",
        tmp_path / "candidate",
        "disabled",
        {"equal_weight_avg_profit_pct": 1.2},
        candidate_family="catboost_ranker_v1",
    )

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["candidate_family"] == "catboost_ranker_v1"
    assert payload["active_live_behavior"] is True
    assert payload["runtime_change"] == "model_artifact_promote_only"
    assert payload["swing_live_order_dry_run_required"] is True
    assert "real_order_conversion" in payload["forbidden_runtime_uses"]


def test_swing_live_dry_run_wrapper_tracks_runtime_approval_artifact():
    script = Path("deploy/run_swing_live_dry_run_report.sh").read_text(encoding="utf-8")

    assert "runtime_approval_artifact" in script
    assert "runtime_approval_markdown_artifact" in script
    assert "runtime_approval_missing" in script
    assert "swing_runtime_approval_${TARGET_DATE}.json" in script
    assert (
        'RUN_LIFECYCLE_AUDIT="${SWING_LIVE_DRY_RUN_RUN_LIFECYCLE_AUDIT:-false}"'
        in script
    )
    assert "selection_completed_lifecycle_deferred_to_postclose" in script
    assert "lifecycle_audit_mode" in script


def test_auto_retrain_status_tracks_promotion_guard():
    script = Path("auto_retrain_pipeline.sh").read_text(encoding="utf-8")

    assert '"promotion_guard": _object(payload.get("promotion_guard"))' in script
    assert '"ai_tier2_review": _object(payload.get("ai_tier2_review"))' in script
    assert '"selected_candidate_family": payload.get("candidate_family")' in script
    assert '"current_manifest": promotion.get("current_manifest")' in script
    assert '"recommendation_smoke": _object(promotion.get("smoke"))' in script
    assert '"rollback_files": promotion.get("rollback_files") or []' in script
    assert (
        '"remediation_applied": bool(remediation_context.get("remediation_applied"))'
        in script
    )
    assert '"remediation_state": remediation_context.get("remediation_state")' in script
    assert '"retry_count": remediation_context.get("retry_count")' in script
    assert '"retry_env_keys": _retry_env_keys(remediation_context)' in script
    assert "src.model.swing_model_auto_remediation --resolve-cron" in script
    assert (
        'KORSTOCKSCAN_SWING_MODEL_TIER2_REVIEW_PROVIDER="$MODEL_TIER2_REVIEW_PROVIDER"'
        in script
    )
    assert 'write_status "blocked_ai_tier2" 0 "ai_tier2_not_approved"' in script
