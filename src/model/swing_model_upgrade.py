from __future__ import annotations

import argparse
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from catboost import CatBoostClassifier, CatBoostRanker, Pool
from lightgbm import LGBMRanker, early_stopping, log_evaluation
from xgboost import XGBRanker

try:
    import optuna
except Exception:  # pragma: no cover - dependency validation covers this path
    optuna = None

from src.model.common_v2 import (
    AI_PRED_PATH,
    BULL_LGBM_PATH,
    BULL_XGB_PATH,
    FEATURES_LGBM,
    FEATURES_XGB,
    HYBRID_LGBM_PATH,
    HYBRID_XGB_PATH,
    META_FEATURES,
    META_MODEL_PATH,
    PassThroughCalibrator,
    PredictProbaScoreAdapter,
    build_base_score_frame,
    get_top_kospi_codes,
    resolve_bull_specialist_mode,
    split_by_unique_dates,
)
from src.model.dataset_builder_v2 import build_panel_dataset
from src.model.swing_model_tracking import log_model_run


CANDIDATE_FAMILIES = {
    "catboost_ranker_v1",
    "catboost_classifier_v1",
    "optuna_lgbm_ranker_v1",
    "optuna_xgb_ranker_v1",
}
FEATURE_SET_VERSION = "swing_meta_features_v2"
LABEL_POLICY = "risk_adjusted_top10_rank_label"
METRIC_CONTRACT = {
    "metric_role": "primary_ev",
    "decision_authority": "swing_model_artifact_promotion_guard",
    "window_policy": "offline_forward_backtest_then_active_artifact_promotion",
    "sample_floor": 40,
    "primary_decision_metric": "equal_weight_avg_profit_pct",
    "source_quality_gate": "schema_compatible_no_label_leakage",
    "forbidden_uses": [
        "swing_dry_run_disable",
        "real_order_conversion",
        "cap_release",
        "provider_route_change",
        "bot_restart",
        "hard_safety_relaxation",
        "intraday_threshold_mutation",
    ],
}
SAVE_COLS = [
    "date",
    "code",
    "name",
    "bull_regime",
    "idx_ret20",
    "idx_atr_ratio",
    "hx",
    "hl",
    "bx",
    "bl",
    "mean_prob",
    "std_prob",
    "max_prob",
    "min_prob",
    "bull_mean",
    "hybrid_mean",
    "bull_hybrid_gap",
    "bull_specialist_mode",
    "bull_score_source",
    "bull_artifact_used",
    "score",
    "target_loose",
    "target_strict",
    "realized_ret_3d",
]


def _env_int(name: str, default: int) -> int:
    try:
        raw = os.getenv(name)
        if raw in (None, ""):
            return default
        return int(float(raw))
    except (TypeError, ValueError):
        return default


def _env_float(name: str, default: float) -> float:
    try:
        raw = os.getenv(name)
        if raw in (None, ""):
            return default
        return float(raw)
    except (TypeError, ValueError):
        return default


def _copy_base_artifacts(base_artifact_dir: Path, output_dir: Path, bull_mode: str) -> list[str]:
    names = ["hybrid_xgb_v2.pkl", "hybrid_lgbm_v2.pkl", "stacking_meta_v2.pkl"]
    if bull_mode != "disabled":
        names.extend(["bull_xgb_v2.pkl", "bull_lgbm_v2.pkl"])
    copied: list[str] = []
    output_dir.mkdir(parents=True, exist_ok=True)
    for name in names:
        src = base_artifact_dir / name
        if src.exists():
            shutil.copy2(src, output_dir / name)
            copied.append(name)
    return copied


def _prepare_meta_frame(
    *,
    base_artifact_dir: Path,
    bull_mode: str,
    meta_start: str,
    meta_end: str,
    codes_limit: int,
) -> pd.DataFrame:
    meta_start_dt = pd.to_datetime(meta_start)
    fetch_start = (meta_start_dt - pd.Timedelta(days=200)).strftime("%Y-%m-%d")
    codes = get_top_kospi_codes(limit=codes_limit)
    panel = build_panel_dataset(codes, fetch_start, meta_end, min_rows=150, include_labels=True)
    if panel.empty:
        return pd.DataFrame()
    panel = panel[panel["date"] >= meta_start_dt].copy()
    if panel.empty:
        return pd.DataFrame()

    mode = resolve_bull_specialist_mode(bull_mode)
    meta_df = build_base_score_frame(
        panel,
        bull_mode=mode,
        hybrid_xgb_path=str(base_artifact_dir / "hybrid_xgb_v2.pkl"),
        hybrid_lgbm_path=str(base_artifact_dir / "hybrid_lgbm_v2.pkl"),
        bull_xgb_path=str(base_artifact_dir / "bull_xgb_v2.pkl"),
        bull_lgbm_path=str(base_artifact_dir / "bull_lgbm_v2.pkl"),
        include_columns=[
            "date",
            "code",
            "name",
            "bull_regime",
            "idx_ret20",
            "idx_atr_ratio",
            "target_loose",
            "target_strict",
            "realized_ret_3d",
            "atr_ratio",
        ],
    )
    meta_df["risk_adj_ret"] = meta_df["realized_ret_3d"] / (meta_df["atr_ratio"] + 1e-9)
    meta_df["target_rank_pct"] = meta_df.groupby("date")["risk_adj_ret"].rank(pct=True, ascending=True)
    meta_df["target_rank_label"] = (meta_df["target_rank_pct"] >= 0.90).astype(int)
    return meta_df.sort_values(["date", "code"]).reset_index(drop=True)


def _groups_by_date(frame: pd.DataFrame) -> np.ndarray:
    return frame.groupby("date", sort=False).size().values


def _train_catboost_ranker(train_df: pd.DataFrame, valid_df: pd.DataFrame):
    model = CatBoostRanker(
        iterations=600,
        learning_rate=0.035,
        depth=5,
        loss_function="YetiRank",
        random_seed=42,
        verbose=False,
        allow_writing_files=False,
    )
    model.fit(
        Pool(
            train_df[META_FEATURES],
            train_df["risk_adj_ret"].astype(float),
            group_id=train_df["date"].astype(str),
        ),
        eval_set=Pool(
            valid_df[META_FEATURES],
            valid_df["risk_adj_ret"].astype(float),
            group_id=valid_df["date"].astype(str),
        ),
        verbose=False,
    )
    return model


def _train_catboost_classifier(train_df: pd.DataFrame, valid_df: pd.DataFrame):
    model = CatBoostClassifier(
        iterations=600,
        learning_rate=0.035,
        depth=5,
        loss_function="Logloss",
        eval_metric="AUC",
        random_seed=42,
        verbose=False,
        allow_writing_files=False,
    )
    model.fit(
        train_df[META_FEATURES],
        train_df["target_rank_label"].astype(int),
        eval_set=(valid_df[META_FEATURES], valid_df["target_rank_label"].astype(int)),
        verbose=False,
    )
    return PredictProbaScoreAdapter(model)


def _train_optuna_lgbm_ranker(train_df: pd.DataFrame, valid_df: pd.DataFrame):
    if optuna is None:
        raise RuntimeError("optuna_unavailable")
    trials = _env_int("KORSTOCKSCAN_SWING_MODEL_OPTUNA_TRIALS", 40)
    timeout = _env_int("KORSTOCKSCAN_SWING_MODEL_OPTUNA_TIMEOUT_SEC", 1800)
    seed = _env_int("KORSTOCKSCAN_SWING_MODEL_OPTUNA_SEED", 42)

    def objective(trial):
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 300, 900),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.08, log=True),
            "num_leaves": trial.suggest_int("num_leaves", 7, 31),
            "max_depth": trial.suggest_int("max_depth", 3, 7),
            "min_child_samples": trial.suggest_int("min_child_samples", 10, 60),
            "subsample": trial.suggest_float("subsample", 0.65, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.65, 1.0),
            "random_state": seed,
            "n_jobs": -1,
            "importance_type": "gain",
        }
        model = LGBMRanker(**params)
        model.fit(
            train_df[META_FEATURES],
            train_df["target_rank_label"].astype(int),
            group=_groups_by_date(train_df),
            eval_set=[(valid_df[META_FEATURES], valid_df["target_rank_label"].astype(int))],
            eval_group=[_groups_by_date(valid_df)],
            eval_metric="ndcg",
            callbacks=[early_stopping(30), log_evaluation(0)],
        )
        scored = valid_df.copy()
        scored["candidate_score"] = model.predict(valid_df[META_FEATURES])
        top = scored.sort_values(["date", "candidate_score"], ascending=[True, False]).groupby("date").head(3)
        return float(top["realized_ret_3d"].mean()) if not top.empty else -99.0

    study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=seed))
    study.optimize(objective, n_trials=trials, timeout=timeout, show_progress_bar=False)
    params = {
        **study.best_params,
        "random_state": seed,
        "n_jobs": -1,
        "importance_type": "gain",
    }
    model = LGBMRanker(**params)
    model.fit(
        train_df[META_FEATURES],
        train_df["target_rank_label"].astype(int),
        group=_groups_by_date(train_df),
        eval_set=[(valid_df[META_FEATURES], valid_df["target_rank_label"].astype(int))],
        eval_group=[_groups_by_date(valid_df)],
        eval_metric="ndcg",
        callbacks=[early_stopping(50), log_evaluation(0)],
    )
    return model


def _train_optuna_xgb_ranker(train_df: pd.DataFrame, valid_df: pd.DataFrame):
    if optuna is None:
        raise RuntimeError("optuna_unavailable")
    trials = _env_int("KORSTOCKSCAN_SWING_MODEL_OPTUNA_TRIALS", 40)
    timeout = _env_int("KORSTOCKSCAN_SWING_MODEL_OPTUNA_TIMEOUT_SEC", 1800)
    seed = _env_int("KORSTOCKSCAN_SWING_MODEL_OPTUNA_SEED", 42)

    def objective(trial):
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 300, 900),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.08, log=True),
            "max_depth": trial.suggest_int("max_depth", 3, 7),
            "min_child_weight": trial.suggest_float("min_child_weight", 1.0, 20.0),
            "subsample": trial.suggest_float("subsample", 0.65, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.65, 1.0),
            "objective": "rank:ndcg",
            "eval_metric": "ndcg",
            "random_state": seed,
            "n_jobs": -1,
        }
        model = XGBRanker(**params)
        model.fit(
            train_df[META_FEATURES],
            train_df["target_rank_label"].astype(int),
            group=_groups_by_date(train_df),
            eval_set=[(valid_df[META_FEATURES], valid_df["target_rank_label"].astype(int))],
            eval_group=[_groups_by_date(valid_df)],
            verbose=False,
        )
        scored = valid_df.copy()
        scored["candidate_score"] = model.predict(valid_df[META_FEATURES])
        top = scored.sort_values(["date", "candidate_score"], ascending=[True, False]).groupby("date").head(3)
        return float(top["realized_ret_3d"].mean()) if not top.empty else -99.0

    study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=seed))
    study.optimize(objective, n_trials=trials, timeout=timeout, show_progress_bar=False)
    model = XGBRanker(
        **study.best_params,
        objective="rank:ndcg",
        eval_metric="ndcg",
        random_state=seed,
        n_jobs=-1,
    )
    model.fit(
        train_df[META_FEATURES],
        train_df["target_rank_label"].astype(int),
        group=_groups_by_date(train_df),
        eval_set=[(valid_df[META_FEATURES], valid_df["target_rank_label"].astype(int))],
        eval_group=[_groups_by_date(valid_df)],
        verbose=False,
    )
    return model


def _train_candidate_model(candidate_family: str, train_df: pd.DataFrame, valid_df: pd.DataFrame):
    if candidate_family == "catboost_ranker_v1":
        return _train_catboost_ranker(train_df, valid_df)
    if candidate_family == "catboost_classifier_v1":
        return _train_catboost_classifier(train_df, valid_df)
    if candidate_family == "optuna_lgbm_ranker_v1":
        return _train_optuna_lgbm_ranker(train_df, valid_df)
    if candidate_family == "optuna_xgb_ranker_v1":
        return _train_optuna_xgb_ranker(train_df, valid_df)
    raise ValueError(f"unknown_candidate_family:{candidate_family}")


def _write_shap_summary(model, sample_x: pd.DataFrame, output_dir: Path) -> dict[str, Any]:
    if str(os.getenv("KORSTOCKSCAN_SWING_MODEL_SHAP_ENABLED", "true")).lower() not in {"1", "true", "yes", "on"}:
        return {"status": "skipped_disabled"}
    try:
        import shap

        x = sample_x.head(min(200, len(sample_x))).copy()
        target_model = getattr(model, "model", model)
        explainer = shap.Explainer(target_model, x)
        values = explainer(x)
        arr = np.asarray(values.values)
        if arr.ndim > 2:
            arr = arr[:, :, -1]
        importance = np.abs(arr).mean(axis=0)
        rows = [
            {"feature": feature, "mean_abs_shap": float(value)}
            for feature, value in sorted(zip(x.columns, importance), key=lambda item: item[1], reverse=True)
        ]
        path = output_dir / "shap_summary.json"
        path.write_text(json.dumps({"status": "ok", "top_features": rows[:20]}, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"status": "ok", "path": str(path), "top_features": rows[:10]}
    except Exception as exc:
        path = output_dir / "shap_summary.json"
        payload = {"status": "failed", "error": str(exc)}
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return {**payload, "path": str(path)}


def train_upgrade_candidate(
    *,
    candidate_family: str,
    base_artifact_dir: Path,
    output_dir: Path,
    bull_mode: str,
    meta_start: str,
    meta_end: str,
    target_date: str | None = None,
    run_id: str | None = None,
    codes_limit: int = 300,
) -> dict[str, Any]:
    if candidate_family not in CANDIDATE_FAMILIES:
        raise ValueError(f"unknown_candidate_family:{candidate_family}")
    output_dir.mkdir(parents=True, exist_ok=True)
    copied = _copy_base_artifacts(base_artifact_dir, output_dir, resolve_bull_specialist_mode(bull_mode))
    meta_df = _prepare_meta_frame(
        base_artifact_dir=base_artifact_dir,
        bull_mode=bull_mode,
        meta_start=meta_start,
        meta_end=meta_end,
        codes_limit=codes_limit,
    )
    if meta_df.empty:
        raise RuntimeError("empty_meta_training_frame")

    train_df, valid_df, test_df = split_by_unique_dates(meta_df, ratios=(0.70, 0.15, 0.15))
    model = _train_candidate_model(candidate_family, train_df, valid_df)
    save_df = meta_df.copy()
    save_df["score"] = model.predict(save_df[META_FEATURES])
    save_df = save_df[SAVE_COLS].sort_values(["date", "code"]).reset_index(drop=True)
    save_df.to_csv(output_dir / Path(AI_PRED_PATH).name, index=False, encoding="utf-8-sig")

    artifact = {
        "model": model,
        "calibrator": PassThroughCalibrator(),
        "features": META_FEATURES,
        "model_name": candidate_family,
        "feature_set_version": FEATURE_SET_VERSION,
        "label_policy": LABEL_POLICY,
        "metric_contract": METRIC_CONTRACT,
        "bull_specialist_mode": resolve_bull_specialist_mode(bull_mode),
        "trained_at": datetime.now().isoformat(timespec="seconds"),
    }
    joblib.dump(artifact, output_dir / Path(META_MODEL_PATH).name)
    shap_summary = _write_shap_summary(model, test_df[META_FEATURES], output_dir)
    manifest = {
        "schema_version": 1,
        "report_type": "swing_model_upgrade_candidate",
        "target_date": target_date,
        "run_id": run_id,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "candidate_family": candidate_family,
        "base_artifact_dir": str(base_artifact_dir),
        "output_dir": str(output_dir),
        "copied_base_artifacts": copied,
        "feature_set_version": FEATURE_SET_VERSION,
        "label_policy": LABEL_POLICY,
        "metric_contract": METRIC_CONTRACT,
        "row_counts": {
            "meta": int(len(meta_df)),
            "train": int(len(train_df)),
            "valid": int(len(valid_df)),
            "test": int(len(test_df)),
        },
        "shap": shap_summary,
    }
    manifest_path = output_dir / "candidate_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    tracking = log_model_run(
        run_name=f"{candidate_family}:{target_date or meta_end}",
        params={
            "run_id": run_id or "",
            "target_date": target_date or "",
            "candidate_family": candidate_family,
            "bull_mode": resolve_bull_specialist_mode(bull_mode),
            "feature_set_version": FEATURE_SET_VERSION,
            "label_policy": LABEL_POLICY,
            "primary_decision_metric": METRIC_CONTRACT["primary_decision_metric"],
            "active_promotion_decision": "training_only_not_promoted",
        },
        tags={"stage": "candidate_training", "active_live_behavior": "false"},
        artifact_paths=[manifest_path, output_dir / "shap_summary.json"],
    )
    manifest["mlflow"] = tracking
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Train a swing v2 upgraded model candidate.")
    parser.add_argument("--candidate-family", required=True, choices=sorted(CANDIDATE_FAMILIES))
    parser.add_argument("--base-artifact-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--bull-mode", default="disabled", choices=["enabled", "disabled", "hold_current"])
    parser.add_argument("--meta-start", required=True)
    parser.add_argument("--meta-end", required=True)
    parser.add_argument("--target-date", default=None)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--codes-limit", type=int, default=_env_int("KORSTOCKSCAN_SWING_MODEL_CODES_LIMIT", 300))
    args = parser.parse_args(argv)
    train_upgrade_candidate(
        candidate_family=args.candidate_family,
        base_artifact_dir=Path(args.base_artifact_dir),
        output_dir=Path(args.output_dir),
        bull_mode=args.bull_mode,
        meta_start=args.meta_start,
        meta_end=args.meta_end,
        target_date=args.target_date,
        run_id=args.run_id,
        codes_limit=args.codes_limit,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
