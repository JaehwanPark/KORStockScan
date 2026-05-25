from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

from src.model.common_v2 import MODEL_REGISTRY_DIR


EXPERIMENT_NAME = "korstockscan_swing_v2_model_upgrade"
TRACKING_DIR = Path(MODEL_REGISTRY_DIR) / "mlruns"
TRACKING_URI = "file:data/model_registry/swing_v2/mlruns"


def tracking_uri() -> str:
    configured = os.getenv("KORSTOCKSCAN_SWING_MODEL_MLFLOW_TRACKING_URI")
    if configured:
        return configured
    return TRACKING_URI


def current_git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=Path(__file__).resolve().parents[2],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return ""


def log_model_run(
    *,
    run_name: str,
    params: dict[str, Any] | None = None,
    metrics: dict[str, Any] | None = None,
    tags: dict[str, Any] | None = None,
    artifact_paths: list[Path] | None = None,
) -> dict[str, Any]:
    """Best-effort MLflow tracking for model upgrade traceability."""
    try:
        import mlflow
    except Exception as exc:
        return {"status": "unavailable", "error": str(exc)}

    try:
        TRACKING_DIR.mkdir(parents=True, exist_ok=True)
        mlflow.set_tracking_uri(tracking_uri())
        mlflow.set_experiment(EXPERIMENT_NAME)
        with mlflow.start_run(run_name=run_name) as run:
            git_commit = current_git_commit()
            mlflow.set_tag("git_commit", git_commit)
            if git_commit:
                mlflow.log_param("git_commit", git_commit)
            for key, value in (tags or {}).items():
                mlflow.set_tag(str(key), str(value))
            for key, value in (params or {}).items():
                if value is not None:
                    mlflow.log_param(str(key), value)
            for key, value in (metrics or {}).items():
                try:
                    if value is not None:
                        mlflow.log_metric(str(key), float(value))
                except (TypeError, ValueError):
                    continue
            for path in artifact_paths or []:
                if path.exists():
                    if path.is_dir():
                        mlflow.log_artifacts(str(path))
                    else:
                        mlflow.log_artifact(str(path))
            return {
                "status": "logged",
                "run_id": run.info.run_id,
                "tracking_uri": tracking_uri(),
                "experiment_name": EXPERIMENT_NAME,
            }
    except Exception as exc:
        return {"status": "failed", "error": str(exc), "tracking_uri": tracking_uri()}
