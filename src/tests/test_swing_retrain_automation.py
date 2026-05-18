import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.model import common_v2
from src.model import recommend_daily_v2 as reco
from src.model import swing_bull_period_ai_review as bull_review
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


def test_build_base_score_frame_disabled_neutralizes_bull_without_loading_bull(monkeypatch):
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
    monkeypatch.setattr(reco, "build_base_score_frame", lambda *args, **kwargs: scored.copy())
    monkeypatch.setattr(reco, "load_model_artifact", lambda path: {"model": _DummyModel(0.5)})
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
    enabled = {"sample_count": 20, "avg_net_pct": 0.4, "downside_p10_pct": -1.0, "selected_count": 8}
    disabled = {"sample_count": 20, "avg_net_pct": 0.2, "downside_p10_pct": -1.1, "selected_count": 8}
    assert pipeline.evaluate_bull_specialist_mode(enabled, disabled)["bull_specialist_mode"] == "enabled"

    weak = {"sample_count": 20, "avg_net_pct": 0.1, "downside_p10_pct": -1.8, "selected_count": 8}
    assert pipeline.evaluate_bull_specialist_mode(weak, disabled)["bull_specialist_mode"] == "disabled"

    small = {"sample_count": 2, "avg_net_pct": 0.9, "downside_p10_pct": -0.5, "selected_count": 8}
    assert pipeline.evaluate_bull_specialist_mode(small, disabled)["bull_specialist_mode"] == "hold_current"


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


def test_promote_candidate_disabled_removes_active_bull_and_rollback_restores(tmp_path, monkeypatch):
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
    assert (data_dir / "stacking_meta_v2.pkl").read_text(encoding="utf-8").startswith("candidate:")

    restored = pipeline._rollback_active_models(backup_dir)

    assert "bull_xgb_v2.pkl" in restored
    assert (data_dir / "bull_xgb_v2.pkl").read_text(encoding="utf-8").startswith("active:")


def test_pipeline_trains_enabled_and_disabled_then_selects_better_candidate(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "RUNS_DIR", tmp_path / "runs")
    monkeypatch.setattr(pipeline, "PROMOTIONS_DIR", tmp_path / "promotions")
    monkeypatch.setattr(pipeline, "REPORT_DIR", tmp_path / "reports")
    monkeypatch.setattr(pipeline, "write_diagnosis", lambda target, force=False: {"retrain_required": True})
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
    monkeypatch.setattr(pipeline, "_promote_candidate", lambda run_dir, backup_dir, mode: {"promoted_files": [mode]})
    monkeypatch.setattr(pipeline, "_smoke_after_promote", lambda mode: {"returncode": 0})
    monkeypatch.setattr(
        pipeline,
        "_write_current_manifest",
        lambda run_id, target_date, run_dir, mode, metrics: tmp_path / "current.json",
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


def test_swing_live_dry_run_wrapper_tracks_runtime_approval_artifact():
    script = Path("deploy/run_swing_live_dry_run_report.sh").read_text(encoding="utf-8")

    assert "runtime_approval_artifact" in script
    assert "runtime_approval_markdown_artifact" in script
    assert "runtime_approval_missing" in script
    assert "swing_runtime_approval_${TARGET_DATE}.json" in script
    assert 'RUN_LIFECYCLE_AUDIT="${SWING_LIVE_DRY_RUN_RUN_LIFECYCLE_AUDIT:-false}"' in script
    assert "selection_completed_lifecycle_deferred_to_postclose" in script
    assert "lifecycle_audit_mode" in script


def test_auto_retrain_status_tracks_promotion_guard():
    script = Path("auto_retrain_pipeline.sh").read_text(encoding="utf-8")

    assert '"promotion_guard": %s' in script
    assert 'payload.get("promotion_guard")' in script
