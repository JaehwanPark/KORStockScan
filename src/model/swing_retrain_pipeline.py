from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import text

from src.model.common_v2 import (
    DATA_DIR,
    META_END,
    META_START,
    MODEL_REGISTRY_DIR,
    RECO_DIAGNOSTIC_JSON_PATH,
    RECO_PATH,
    engine,
    resolve_bull_specialist_mode,
)
from src.model.swing_bull_period_ai_review import write_review
from src.model.swing_model_auto_remediation import write_remediation_report
from src.model.swing_model_tier2_review import write_tier2_review_report
from src.model.swing_model_tracking import log_model_run
from src.model.swing_model_upgrade import CANDIDATE_FAMILIES, FEATURE_SET_VERSION, LABEL_POLICY, METRIC_CONTRACT
from src.model.swing_retrain_diagnosis import write_diagnosis


ACTIVE_MODEL_FILES = [
    "hybrid_xgb_v2.pkl",
    "hybrid_lgbm_v2.pkl",
    "bull_xgb_v2.pkl",
    "bull_lgbm_v2.pkl",
    "stacking_meta_v2.pkl",
]
REQUIRED_NON_BULL_FILES = ["hybrid_xgb_v2.pkl", "hybrid_lgbm_v2.pkl", "stacking_meta_v2.pkl"]
REPORT_DIR = Path(DATA_DIR) / "report" / "swing_model_retrain"
REGISTRY_DIR = Path(MODEL_REGISTRY_DIR)
RUNS_DIR = REGISTRY_DIR / "runs"
PROMOTIONS_DIR = REGISTRY_DIR / "promotions"
BACKUP_MANIFEST_NAME = "backup_manifest.json"
BENCHMARK_REPORT_DIR = Path(DATA_DIR) / "report" / "swing_model_benchmark"
REQUIRED_RECOMMENDATION_COLUMNS = {
    "date",
    "code",
    "name",
    "score",
    "hybrid_mean",
    "bull_regime",
    "bull_specialist_mode",
    "bull_score_source",
    "bull_artifact_used",
}
REQUIRED_LIVE_RECOMMENDATION_COLUMNS = REQUIRED_RECOMMENDATION_COLUMNS | {
    "selection_mode",
    "meta_score",
    "generated_at",
}
REQUIRED_RECOMMENDATION_DIAGNOSTIC_KEYS = {
    "owner",
    "generated_at",
    "latest_date",
    "selection_mode",
    "recommendation_path",
    "diagnostic_path",
    "selected_count",
    "diagnostic_count",
    "bull_specialist_mode",
    "score_distribution",
}


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw in (None, ""):
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


def _run_id(target_date: str) -> str:
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    return f"{target_date}_{stamp}"


def _parse_iso_date(value: Any) -> date | None:
    try:
        if value in (None, ""):
            return None
        return datetime.fromisoformat(str(value)[:10]).date()
    except Exception:
        return None


def _latest_quote_date() -> date | None:
    try:
        with engine.connect() as conn:
            value = conn.execute(text("SELECT MAX(quote_date) FROM daily_stock_quotes")).scalar()
    except Exception:
        return None
    return _parse_iso_date(value)


def resolve_meta_period(target_date: str, *, label_safety_days: int = 5) -> dict[str, Any]:
    target = _parse_iso_date(target_date) or date.today()
    latest_quote = _latest_quote_date()
    target_safe_end = target - timedelta(days=label_safety_days)
    end = min(latest_quote, target_safe_end) if latest_quote else target_safe_end
    start = _parse_iso_date(os.getenv("KORSTOCKSCAN_SWING_META_START")) or _parse_iso_date(META_START)
    return {
        "meta_start": (start or date(2026, 1, 1)).isoformat(),
        "meta_end": end.isoformat(),
        "latest_quote_date": latest_quote.isoformat() if latest_quote else None,
        "label_safety_days": label_safety_days,
    }


def _run_command(args: list[str], *, env: dict[str, str], cwd: Path) -> dict[str, Any]:
    started = datetime.now().isoformat(timespec="seconds")
    proc = subprocess.run(args, cwd=str(cwd), env=env, text=True, capture_output=True)
    return {
        "args": args,
        "started_at": started,
        "finished_at": datetime.now().isoformat(timespec="seconds"),
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
    }


def evaluate_bull_specialist_mode(
    enabled_metrics: dict[str, Any],
    disabled_metrics: dict[str, Any],
    *,
    sample_floor: int = 10,
) -> dict[str, Any]:
    enabled_sample = _safe_int(enabled_metrics.get("sample_count"), 0)
    disabled_sample = _safe_int(disabled_metrics.get("sample_count"), 0)
    if min(enabled_sample, disabled_sample) < sample_floor:
        return {
            "bull_specialist_mode": "hold_current",
            "reason": "insufficient_bull_forward_sample",
            "tradeoff_delta": 0.0,
        }

    enabled_avg = _safe_float(enabled_metrics.get("avg_net_pct"), 0.0)
    disabled_avg = _safe_float(disabled_metrics.get("avg_net_pct"), 0.0)
    enabled_p10 = _safe_float(enabled_metrics.get("downside_p10_pct"), 0.0)
    disabled_p10 = _safe_float(disabled_metrics.get("downside_p10_pct"), 0.0)
    enabled_selected = _safe_int(enabled_metrics.get("selected_count"), 0)
    disabled_selected = max(1, _safe_int(disabled_metrics.get("selected_count"), 0))
    selected_drop = (disabled_selected - enabled_selected) / disabled_selected
    tradeoff_delta = (
        (enabled_avg - disabled_avg) * 0.45
        + (enabled_p10 - disabled_p10) * 0.25
        - max(0.0, selected_drop) * 0.30
    )
    if (
        tradeoff_delta >= 0.05
        and enabled_avg - disabled_avg >= 0.10
        and enabled_p10 - disabled_p10 >= -0.30
        and selected_drop <= 0.30
    ):
        mode = "enabled"
        reason = "enabled_outperformed_disabled"
    elif enabled_avg < disabled_avg or enabled_p10 < disabled_p10 - 0.30:
        mode = "disabled"
        reason = "disabled_outperformed_or_safer"
    else:
        mode = "hold_current"
        reason = "no_clear_bull_specialist_edge"
    return {
        "bull_specialist_mode": mode,
        "reason": reason,
        "tradeoff_delta": round(tradeoff_delta, 4),
        "selected_drop_ratio": round(selected_drop, 4),
    }


def _summarize_backtest(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"available": False, "sample_count": 0}
    try:
        df = pd.read_csv(path)
    except Exception as exc:
        return {"available": False, "sample_count": 0, "error": str(exc)}
    if df.empty or "net_ret" not in df.columns:
        return {"available": True, "sample_count": 0}
    bull_df = df[df.get("bull_regime", 0) == 1] if "bull_regime" in df.columns else df
    sample = len(bull_df)
    net = bull_df["net_ret"].astype(float) * 100.0 if sample else pd.Series(dtype=float)
    avg_net = float(net.mean()) if sample else 0.0
    return {
        "available": True,
        "sample_count": int(sample),
        "selected_count": int(len(df)),
        "avg_net_pct": avg_net,
        "equal_weight_avg_profit_pct": avg_net,
        "notional_weighted_ev_pct": avg_net,
        "source_quality_adjusted_ev_pct": avg_net,
        "downside_p10_pct": float(net.quantile(0.10)) if sample else 0.0,
        "diagnostic_win_rate": float((net > 0).mean()) if sample else 0.0,
        "win_rate": float((net > 0).mean()) if sample else 0.0,
    }


def candidate_tradeoff_score(metrics: dict[str, Any]) -> float:
    avg = max(-1.0, min(1.0, _safe_float(metrics.get("avg_net_pct"), 0.0) / 2.0))
    downside = max(0.0, min(1.0, (_safe_float(metrics.get("downside_p10_pct"), -4.0) + 4.0) / 4.0))
    win = max(0.0, min(1.0, _safe_float(metrics.get("win_rate"), 0.0)))
    participation = max(0.0, min(1.0, _safe_int(metrics.get("sample_count"), 0) / 40.0))
    return round(avg * 0.40 + downside * 0.20 + win * 0.15 + participation * 0.15 + 0.10, 4)


def _copy_if_exists(src: Path, dst: Path) -> None:
    if src.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def _prepare_hold_current_bull_artifacts(run_dir: Path) -> None:
    for name in ("bull_xgb_v2.pkl", "bull_lgbm_v2.pkl"):
        _copy_if_exists(Path(DATA_DIR) / name, run_dir / name)


def _staging_env(run_dir: Path, bull_mode: str, bull_review: dict[str, Any]) -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    env["KORSTOCKSCAN_SWING_MODEL_OUTPUT_DIR"] = str(run_dir)
    env["KORSTOCKSCAN_SWING_BULL_SPECIALIST_MODE"] = bull_mode
    decision = bull_review.get("decision") if isinstance(bull_review.get("decision"), dict) else {}
    if decision.get("bull_base_start"):
        env["KORSTOCKSCAN_SWING_BULL_BASE_START"] = str(decision["bull_base_start"])
    if decision.get("bull_base_end"):
        env["KORSTOCKSCAN_SWING_BULL_BASE_END"] = str(decision["bull_base_end"])
    return env


def _train_candidate(
    run_dir: Path,
    bull_mode: str,
    bull_review: dict[str, Any],
    *,
    meta_period: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    root = Path(__file__).resolve().parents[2]
    env = _staging_env(run_dir, bull_mode, bull_review)
    commands = [
        [sys.executable, "-m", "src.model.train_hybrid_xgb_v2"],
        [sys.executable, "-m", "src.model.train_hybrid_lgbm_v2"],
    ]
    if bull_mode == "enabled":
        commands.append(
            [
                sys.executable,
                "-m",
                "src.model.train_bull_specialists_v2",
                "--bull-base-start",
                str((bull_review.get("decision") or {}).get("bull_base_start") or ""),
                "--bull-base-end",
                str((bull_review.get("decision") or {}).get("bull_base_end") or ""),
            ]
        )
    elif bull_mode == "hold_current":
        _prepare_hold_current_bull_artifacts(run_dir)
    commands.extend(
        [
            [
                sys.executable,
                "-m",
                "src.model.train_meta_model_v2",
                "--bull-mode",
                bull_mode,
                "--meta-start",
                str((meta_period or {}).get("meta_start") or META_START),
                "--meta-end",
                str((meta_period or {}).get("meta_end") or META_END),
            ],
            [sys.executable, "-m", "src.model.backtest_v2"],
        ]
    )
    results: list[dict[str, Any]] = []
    for command in commands:
        result = _run_command(command, env=env, cwd=root)
        results.append(result)
        if result["returncode"] != 0:
            break
    return results


def _candidate_files_for_mode(mode: str) -> list[str]:
    if mode == "disabled":
        return REQUIRED_NON_BULL_FILES
    return ACTIVE_MODEL_FILES


def _validate_candidate_files(run_dir: Path, mode: str) -> list[str]:
    missing = []
    for name in _candidate_files_for_mode(mode):
        if not (run_dir / name).exists():
            missing.append(name)
    return missing


def _validate_csv_schema(path: Path, required_columns: set[str], *, missing_reason: str) -> dict[str, Any]:
    if not path.exists():
        return {"passed": False, "missing_columns": sorted(required_columns), "reason": missing_reason}
    try:
        df = pd.read_csv(path, nrows=5)
    except Exception as exc:
        return {"passed": False, "missing_columns": sorted(required_columns), "reason": str(exc)}
    missing = sorted(required_columns - set(df.columns))
    return {"passed": not missing, "missing_columns": missing}


def _validate_recommendation_schema(path: Path) -> dict[str, Any]:
    return _validate_csv_schema(path, REQUIRED_RECOMMENDATION_COLUMNS, missing_reason="missing_ai_predictions")


def _validate_diagnostic_json_schema(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "passed": False,
            "missing_keys": sorted(REQUIRED_RECOMMENDATION_DIAGNOSTIC_KEYS),
            "reason": "missing_recommendation_diagnostics",
        }
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"passed": False, "missing_keys": sorted(REQUIRED_RECOMMENDATION_DIAGNOSTIC_KEYS), "reason": str(exc)}
    missing = sorted(REQUIRED_RECOMMENDATION_DIAGNOSTIC_KEYS - set(payload))
    return {"passed": not missing, "missing_keys": missing}


def _validate_live_recommendation_schema() -> dict[str, Any]:
    csv_check = _validate_csv_schema(
        Path(RECO_PATH),
        REQUIRED_LIVE_RECOMMENDATION_COLUMNS,
        missing_reason="missing_daily_recommendations",
    )
    diagnostic_check = _validate_diagnostic_json_schema(Path(RECO_DIAGNOSTIC_JSON_PATH))
    return {
        "passed": bool(csv_check.get("passed")) and bool(diagnostic_check.get("passed")),
        "recommendation_csv": csv_check,
        "diagnostic_json": diagnostic_check,
    }


def evaluate_model_upgrade_promotion(
    candidate_metrics: dict[str, Any],
    incumbent_metrics: dict[str, Any],
    schema_check: dict[str, Any] | None = None,
    *,
    ev_delta_floor: float = 0.50,
    max_downside_worsening: float = 0.50,
    max_selected_drop: float = 0.30,
    sample_floor: int = 40,
) -> dict[str, Any]:
    candidate_ev = _safe_float(candidate_metrics.get("equal_weight_avg_profit_pct"), _safe_float(candidate_metrics.get("avg_net_pct"), 0.0))
    incumbent_ev = _safe_float(incumbent_metrics.get("equal_weight_avg_profit_pct"), _safe_float(incumbent_metrics.get("avg_net_pct"), 0.0))
    candidate_downside = _safe_float(candidate_metrics.get("downside_p10_pct"), 0.0)
    incumbent_downside = _safe_float(incumbent_metrics.get("downside_p10_pct"), 0.0)
    candidate_selected = _safe_int(candidate_metrics.get("selected_count"), 0)
    incumbent_selected = max(1, _safe_int(incumbent_metrics.get("selected_count"), 0))
    sample_count = _safe_int(candidate_metrics.get("sample_count"), 0)
    ev_delta = candidate_ev - incumbent_ev
    downside_worsening = incumbent_downside - candidate_downside
    selected_drop_ratio = max(0.0, (incumbent_selected - candidate_selected) / incumbent_selected)
    schema_passed = bool((schema_check or {}).get("passed", True))
    reasons = []
    if sample_count < sample_floor:
        reasons.append("sample_floor_not_met")
    if ev_delta < ev_delta_floor:
        reasons.append("ev_delta_below_floor")
    if downside_worsening > max_downside_worsening:
        reasons.append("downside_worsening_above_limit")
    if selected_drop_ratio > max_selected_drop:
        reasons.append("selected_drop_above_limit")
    if not schema_passed:
        reasons.append("schema_compatibility_failed")
    return {
        "passed": not reasons,
        "reasons": reasons,
        "primary_decision_metric": "equal_weight_avg_profit_pct",
        "candidate_ev_pct": round(candidate_ev, 6),
        "incumbent_ev_pct": round(incumbent_ev, 6),
        "ev_delta_pct": round(ev_delta, 6),
        "downside_worsening_pct": round(downside_worsening, 6),
        "selected_drop_ratio": round(selected_drop_ratio, 6),
        "sample_count": sample_count,
        "schema_check": schema_check or {"passed": True},
    }


def _upgrade_candidate_families() -> list[str]:
    raw = os.getenv("KORSTOCKSCAN_SWING_MODEL_UPGRADE_FAMILIES")
    if raw:
        requested = [item.strip() for item in raw.split(",") if item.strip()]
    else:
        requested = sorted(CANDIDATE_FAMILIES)
    return [family for family in requested if family in CANDIDATE_FAMILIES]


def _run_upgrade_candidates(
    base_run_dir: Path,
    mode: str,
    *,
    meta_period: dict[str, Any] | None,
    target_date: str,
    run_id: str,
    incumbent_metrics: dict[str, Any],
) -> dict[str, Any]:
    enabled = _env_bool("KORSTOCKSCAN_SWING_MODEL_UPGRADE_ENABLED", True)
    result: dict[str, Any] = {
        "enabled": enabled,
        "metric_contract": METRIC_CONTRACT,
        "incumbent_metrics": incumbent_metrics,
        "candidates": {},
        "selected_candidate_family": None,
        "selected_run_dir": None,
        "selected_metrics": None,
    }
    if not enabled:
        result["reason"] = "upgrade_disabled"
        return result

    root = Path(__file__).resolve().parents[2]
    families = _upgrade_candidate_families()
    if not families:
        result["reason"] = "no_candidate_families"
        return result
    for family in families:
        candidate_dir = base_run_dir / "upgrade_candidates" / family
        env = os.environ.copy()
        env["PYTHONPATH"] = "."
        env["KORSTOCKSCAN_SWING_MODEL_OUTPUT_DIR"] = str(candidate_dir)
        train_command = [
            sys.executable,
            "-m",
            "src.model.swing_model_upgrade",
            "--candidate-family",
            family,
            "--base-artifact-dir",
            str(base_run_dir),
            "--output-dir",
            str(candidate_dir),
            "--bull-mode",
            mode,
            "--meta-start",
            str((meta_period or {}).get("meta_start") or META_START),
            "--meta-end",
            str((meta_period or {}).get("meta_end") or META_END),
            "--target-date",
            target_date,
            "--run-id",
            run_id,
        ]
        train_result = _run_command(train_command, env=env, cwd=root)
        backtest_result: dict[str, Any] | None = None
        if train_result.get("returncode") == 0:
            backtest_result = _run_command([sys.executable, "-m", "src.model.backtest_v2"], env=env, cwd=root)
        metrics = _summarize_backtest(candidate_dir / "backtest_trades_v2.csv")
        schema_check = _validate_recommendation_schema(candidate_dir / "ai_predictions_v2.csv")
        gate = evaluate_model_upgrade_promotion(metrics, incumbent_metrics, schema_check)
        candidate_payload = {
            "candidate_family": family,
            "run_dir": str(candidate_dir),
            "train_command": train_result,
            "backtest_command": backtest_result,
            "metrics": metrics,
            "schema_check": schema_check,
            "promotion_gate": gate,
        }
        result["candidates"][family] = candidate_payload
        log_model_run(
            run_name=f"benchmark:{family}:{target_date}",
            params={
                "run_id": run_id,
                "target_date": target_date,
                "candidate_family": family,
                "bull_mode": mode,
                "feature_set_version": FEATURE_SET_VERSION,
                "label_policy": LABEL_POLICY,
                "primary_decision_metric": METRIC_CONTRACT["primary_decision_metric"],
                "active_promotion_decision": "gate_passed" if gate.get("passed") else "not_promoted_gate_failed",
            },
            metrics={
                "equal_weight_avg_profit_pct": metrics.get("equal_weight_avg_profit_pct"),
                "notional_weighted_ev_pct": metrics.get("notional_weighted_ev_pct"),
                "source_quality_adjusted_ev_pct": metrics.get("source_quality_adjusted_ev_pct"),
                "ev_delta_pct": gate.get("ev_delta_pct"),
                "downside_worsening_pct": gate.get("downside_worsening_pct"),
                "downside_p10_pct": metrics.get("downside_p10_pct"),
                "diagnostic_win_rate": metrics.get("diagnostic_win_rate"),
                "selected_drop_ratio": gate.get("selected_drop_ratio"),
                "selected_count": metrics.get("selected_count"),
                "sample_count": metrics.get("sample_count"),
            },
            tags={
                "stage": "candidate_benchmark",
                "promotion_gate_passed": gate.get("passed"),
                "active_live_behavior": "model_artifact_candidate",
            },
            artifact_paths=[candidate_dir / "candidate_manifest.json", candidate_dir / "shap_summary.json"],
        )

    passing = [
        item
        for item in result["candidates"].values()
        if (item.get("promotion_gate") or {}).get("passed")
    ]
    if passing:
        passing.sort(
            key=lambda item: (
                _safe_float((item.get("promotion_gate") or {}).get("ev_delta_pct"), 0.0),
                _safe_float((item.get("metrics") or {}).get("equal_weight_avg_profit_pct"), 0.0),
            ),
            reverse=True,
        )
        selected = passing[0]
        result["selected_candidate_family"] = selected["candidate_family"]
        result["selected_run_dir"] = selected["run_dir"]
        result["selected_metrics"] = selected["metrics"]
    return result


def _train_and_evaluate_mode(
    parent_run_dir: Path,
    mode: str,
    bull_review: dict[str, Any],
    *,
    meta_period: dict[str, Any] | None = None,
    target_date: str | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    mode_run_dir = parent_run_dir / mode
    mode_run_dir.mkdir(parents=True, exist_ok=True)
    command_results = _train_candidate(mode_run_dir, mode, bull_review, meta_period=meta_period)
    failed = [item for item in command_results if item.get("returncode") != 0]
    missing = _validate_candidate_files(mode_run_dir, mode)
    metrics = _summarize_backtest(mode_run_dir / "backtest_trades_v2.csv")
    if not failed and not missing:
        metrics["tradeoff_score"] = candidate_tradeoff_score(metrics)
    selected_run_dir = mode_run_dir
    selected_candidate_family = "incumbent_current_v2"
    upgrade_result: dict[str, Any] = {}
    if not failed and not missing:
        upgrade_result = _run_upgrade_candidates(
            mode_run_dir,
            mode,
            meta_period=meta_period,
            target_date=target_date or date.today().isoformat(),
            run_id=run_id or "",
            incumbent_metrics=metrics,
        )
        if upgrade_result.get("selected_run_dir") and upgrade_result.get("selected_metrics"):
            selected_run_dir = Path(str(upgrade_result["selected_run_dir"]))
            selected_candidate_family = str(upgrade_result["selected_candidate_family"])
            metrics = dict(upgrade_result["selected_metrics"] or {})
            metrics["tradeoff_score"] = candidate_tradeoff_score(metrics)
            missing = _validate_candidate_files(selected_run_dir, mode)
    return {
        "bull_specialist_mode": mode,
        "run_dir": str(selected_run_dir),
        "incumbent_run_dir": str(mode_run_dir),
        "selected_candidate_family": selected_candidate_family,
        "command_results": command_results,
        "failed": bool(failed),
        "missing_artifacts": missing,
        "metrics": metrics,
        "model_upgrade": upgrade_result,
    }


def _candidate_status(candidate: dict[str, Any]) -> str:
    if candidate.get("failed"):
        return "failed"
    missing = candidate.get("missing_artifacts") or []
    if missing:
        return "missing_artifacts"
    return "ready"


def _choose_candidate(
    candidates: dict[str, dict[str, Any]],
    initial_mode: str,
    bull_review: dict[str, Any],
    *,
    meta_period: dict[str, Any] | None = None,
    target_date: str | None = None,
    run_id: str | None = None,
) -> tuple[str | None, dict[str, Any]]:
    enabled = candidates.get("enabled")
    disabled = candidates.get("disabled")
    if enabled and disabled and _candidate_status(enabled) == "ready" and _candidate_status(disabled) == "ready":
        decision = evaluate_bull_specialist_mode(enabled.get("metrics") or {}, disabled.get("metrics") or {})
        chosen_mode = resolve_bull_specialist_mode(decision.get("bull_specialist_mode"))
        if chosen_mode == "hold_current":
            hold = candidates.get("hold_current")
            if hold and _candidate_status(hold) == "ready":
                return "hold_current", decision
            if (Path(DATA_DIR) / "bull_xgb_v2.pkl").exists() and (Path(DATA_DIR) / "bull_lgbm_v2.pkl").exists():
                hold = _train_and_evaluate_mode(
                    Path(candidates["enabled"]["run_dir"]).parent,
                    "hold_current",
                    bull_review,
                    meta_period=meta_period,
                    target_date=target_date,
                    run_id=run_id,
                )
                candidates["hold_current"] = hold
                if _candidate_status(hold) == "ready":
                    return "hold_current", decision
            fallback = "disabled" if _candidate_status(disabled) == "ready" else None
            decision = {
                **decision,
                "fallback_bull_specialist_mode": fallback,
                "fallback_reason": "hold_current_candidate_unavailable",
            }
            return fallback, decision
        return chosen_mode, decision

    preferred = candidates.get(initial_mode)
    if preferred and _candidate_status(preferred) == "ready":
        return initial_mode, {"bull_specialist_mode": initial_mode, "reason": "single_candidate_ready"}
    for mode in ("disabled", "enabled", "hold_current"):
        candidate = candidates.get(mode)
        if candidate and _candidate_status(candidate) == "ready":
            return mode, {
                "bull_specialist_mode": mode,
                "reason": "fallback_ready_candidate",
                "initial_mode": initial_mode,
            }
    return None, {"bull_specialist_mode": initial_mode, "reason": "no_ready_candidate"}


def _backup_active_models(backup_dir: Path) -> list[str]:
    copied = []
    backup_dir.mkdir(parents=True, exist_ok=True)
    for name in ACTIVE_MODEL_FILES:
        src = Path(DATA_DIR) / name
        if src.exists():
            shutil.copy2(src, backup_dir / name)
            copied.append(name)
    manifest = {"schema_version": 1, "existing_files": copied}
    (backup_dir / BACKUP_MANIFEST_NAME).write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return copied


def _promote_candidate(run_dir: Path, backup_dir: Path, mode: str) -> dict[str, Any]:
    copied = _backup_active_models(backup_dir)
    for name in _candidate_files_for_mode(mode):
        shutil.copy2(run_dir / name, Path(DATA_DIR) / name)
    if mode == "disabled":
        for name in ("bull_xgb_v2.pkl", "bull_lgbm_v2.pkl"):
            active = Path(DATA_DIR) / name
            if active.exists():
                active.unlink()
    return {"backup_files": copied, "promoted_files": _candidate_files_for_mode(mode)}


def _rollback_active_models(backup_dir: Path) -> list[str]:
    restored = []
    manifest_path = backup_dir / BACKUP_MANIFEST_NAME
    existing_files = set(ACTIVE_MODEL_FILES)
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            existing_files = set(manifest.get("existing_files") or [])
        except Exception:
            existing_files = set(ACTIVE_MODEL_FILES)
    for name in ACTIVE_MODEL_FILES:
        src = backup_dir / name
        dst = Path(DATA_DIR) / name
        if src.exists():
            shutil.copy2(src, dst)
            restored.append(name)
        elif name not in existing_files and dst.exists():
            dst.unlink()
            restored.append(f"removed:{name}")
    return restored


def _write_current_manifest(
    run_id: str,
    target_date: str,
    run_dir: Path,
    mode: str,
    metrics: dict[str, Any],
    *,
    candidate_family: str = "incumbent_current_v2",
) -> Path:
    REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": 1,
        "run_id": run_id,
        "target_date": target_date,
        "promoted_at": datetime.now().isoformat(timespec="seconds"),
        "bull_specialist_mode": mode,
        "candidate_family": candidate_family,
        "artifact_dir": str(run_dir),
        "active_live_behavior": True,
        "runtime_change": "model_artifact_promote_only",
        "swing_live_order_dry_run_required": True,
        "forbidden_runtime_uses": [
            "swing_dry_run_disable",
            "real_order_conversion",
            "cap_release",
            "provider_route_change",
            "bot_restart",
            "hard_safety_relaxation",
            "intraday_threshold_mutation",
        ],
        "metrics": metrics,
    }
    path = REGISTRY_DIR / "current.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return path


def _smoke_after_promote(mode: str) -> dict[str, Any]:
    root = Path(__file__).resolve().parents[2]
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    env["KORSTOCKSCAN_SWING_BULL_SPECIALIST_MODE"] = mode
    return _run_command([sys.executable, "-m", "src.model.recommend_daily_v2", "--bull-mode", mode], env=env, cwd=root)


def pipeline_paths(target_date: str) -> tuple[Path, Path]:
    base = REPORT_DIR / f"swing_model_retrain_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def render_markdown(report: dict[str, Any]) -> str:
    promotion_guard = report.get("promotion_guard") if isinstance(report.get("promotion_guard"), dict) else {}
    return "\n".join(
        [
            f"# Swing Model Retrain {report.get('target_date')}",
            "",
            f"- status: `{report.get('status')}`",
            f"- run_id: `{report.get('run_id')}`",
            f"- bull_specialist_mode: `{report.get('bull_specialist_mode')}`",
            f"- candidate_family: `{report.get('candidate_family')}`",
            f"- promoted: `{report.get('promoted')}`",
            f"- active_live_behavior: `{report.get('active_live_behavior')}`",
            f"- rollback_executed: `{report.get('rollback_executed')}`",
            f"- promotion_guard.decision: `{promotion_guard.get('decision')}`",
            f"- promotion_guard.candidate_score: `{promotion_guard.get('candidate_score')}`",
            f"- promotion_guard.reason: `{promotion_guard.get('reason')}`",
            "- swing_live_order_dry_run_required: `true`",
            "",
        ]
    )


def _write_benchmark_report(target_date: str, run_id: str, candidate_results: dict[str, dict[str, Any]]) -> dict[str, str]:
    BENCHMARK_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "report_type": "swing_model_benchmark",
        "target_date": target_date,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "run_id": run_id,
        "metric_contract": METRIC_CONTRACT,
        "candidate_results": {
            mode: {
                "selected_candidate_family": item.get("selected_candidate_family"),
                "run_dir": item.get("run_dir"),
                "incumbent_run_dir": item.get("incumbent_run_dir"),
                "metrics": item.get("metrics"),
                "model_upgrade": item.get("model_upgrade"),
            }
            for mode, item in candidate_results.items()
        },
    }
    json_path = BENCHMARK_REPORT_DIR / f"swing_model_benchmark_{target_date}.json"
    md_path = BENCHMARK_REPORT_DIR / f"swing_model_benchmark_{target_date}.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    lines = [
        f"# Swing Model Benchmark {target_date}",
        "",
        f"- run_id: `{run_id}`",
        f"- primary_decision_metric: `{METRIC_CONTRACT['primary_decision_metric']}`",
        "- active_live_behavior_scope: `model_artifact_promotion_only`",
        "",
    ]
    for mode, item in candidate_results.items():
        metrics = item.get("metrics") or {}
        lines.append(
            f"- {mode}: candidate=`{item.get('selected_candidate_family')}` "
            f"ev=`{metrics.get('equal_weight_avg_profit_pct')}` sample=`{metrics.get('sample_count')}`"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path)}


def _incumbent_metrics_for_selected_candidate(selected: dict[str, Any] | None) -> dict[str, Any]:
    selected = selected or {}
    upgrade = selected.get("model_upgrade") if isinstance(selected.get("model_upgrade"), dict) else {}
    incumbent = upgrade.get("incumbent_metrics") if isinstance(upgrade.get("incumbent_metrics"), dict) else {}
    if incumbent:
        return dict(incumbent)
    return dict(selected.get("metrics") or {})


def run_pipeline(
    target_date: str | None = None,
    *,
    auto_promote: bool = False,
    force: bool = False,
) -> dict[str, Any]:
    target = target_date or date.today().isoformat()
    diagnosis = write_diagnosis(target, force=force)
    bull_review = write_review(target)
    initial_mode = resolve_bull_specialist_mode((bull_review.get("decision") or {}).get("bull_specialist_mode"))
    meta_period = resolve_meta_period(target)
    run_id = _run_id(target)
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    status = "skipped"
    command_results: list[dict[str, Any]] = []
    candidate_results: dict[str, dict[str, Any]] = {}
    promoted = False
    rollback_executed = False
    promotion: dict[str, Any] = {}
    metrics: dict[str, Any] = {}
    selected_run_dir = run_dir
    selected_mode = initial_mode
    selected_candidate_family = "incumbent_current_v2"
    benchmark_report_paths: dict[str, str] = {}
    ai_tier2_review: dict[str, Any] = {}
    remediation: dict[str, Any] = {}
    mode_decision = {"bull_specialist_mode": initial_mode, "reason": "review_decision"}

    if bool(diagnosis.get("retrain_required")):
        modes_to_train = [initial_mode] if initial_mode == "hold_current" else ["enabled", "disabled"]
        for mode in modes_to_train:
            candidate_results[mode] = _train_and_evaluate_mode(
                run_dir,
                mode,
                bull_review,
                meta_period=meta_period,
                target_date=target,
                run_id=run_id,
            )
            command_results.extend(candidate_results[mode]["command_results"])
        chosen_mode, mode_decision = _choose_candidate(
            candidate_results,
            initial_mode,
            bull_review,
            meta_period=meta_period,
            target_date=target,
            run_id=run_id,
        )
        if chosen_mode:
            selected_mode = chosen_mode
            selected_run_dir = Path(candidate_results[chosen_mode]["run_dir"])
            selected_candidate_family = str(candidate_results[chosen_mode].get("selected_candidate_family") or "incumbent_current_v2")
            metrics = dict(candidate_results[chosen_mode].get("metrics") or {})
        benchmark_report_paths = _write_benchmark_report(target, run_id, candidate_results)
        failed = [mode for mode, item in candidate_results.items() if item.get("failed")]
        missing_by_mode = {
            mode: item.get("missing_artifacts") or []
            for mode, item in candidate_results.items()
            if item.get("missing_artifacts")
        }
        if not chosen_mode and failed:
            status = "failed"
            promotion["blocked_reason"] = "training_command_failed"
        elif not chosen_mode and missing_by_mode:
            status = "failed"
            promotion["blocked_reason"] = f"candidate_artifact_missing:{missing_by_mode}"
        elif not chosen_mode:
            status = "failed"
            promotion["blocked_reason"] = "no_ready_candidate"
        else:
            min_score = _safe_float(os.getenv("KORSTOCKSCAN_SWING_RETRAIN_MIN_SCORE"), 0.72)
            hard_floor_passed = _safe_int(metrics.get("sample_count"), 0) >= 40
            avg_ok = _safe_float(metrics.get("avg_net_pct"), 0.0) >= 0.10
            score_ok = _safe_float(metrics.get("tradeoff_score"), 0.0) >= min_score
            if not hard_floor_passed:
                status = "hold_sample"
                promotion["blocked_reason"] = "sample_floor_not_met"
            elif not avg_ok:
                status = "rejected"
                promotion["blocked_reason"] = "avg_net_below_floor"
            elif not score_ok:
                status = "rejected"
                promotion["blocked_reason"] = "tradeoff_score_below_floor"
                promotion["min_tradeoff_score"] = min_score
            elif auto_promote:
                selected_payload = candidate_results.get(selected_mode) or {}
                upgrade_payload = selected_payload.get("model_upgrade") if isinstance(selected_payload.get("model_upgrade"), dict) else {}
                upgrade_candidates = upgrade_payload.get("candidates") if isinstance(upgrade_payload.get("candidates"), dict) else {}
                upgrade_gate = (
                    (upgrade_candidates.get(selected_candidate_family) or {}).get("promotion_gate")
                    if selected_candidate_family != "incumbent_current_v2"
                    else None
                )
                deterministic_gate = upgrade_gate or {
                    "passed": True,
                    "reasons": [],
                    "primary_decision_metric": METRIC_CONTRACT["primary_decision_metric"],
                    "sample_floor": 40,
                    "avg_net_floor_pct": 0.10,
                    "min_tradeoff_score": min_score,
                    "sample_count": _safe_int(metrics.get("sample_count"), 0),
                    "candidate_score": _safe_float(metrics.get("tradeoff_score"), 0.0),
                    "avg_net_pct": _safe_float(metrics.get("avg_net_pct"), 0.0),
                    "sample_floor_passed": hard_floor_passed,
                    "avg_net_floor_passed": avg_ok,
                    "tradeoff_score_floor_passed": score_ok,
                }
                ai_tier2_review = write_tier2_review_report(
                    target_date=target,
                    run_id=run_id,
                    selected_candidate_family=selected_candidate_family,
                    selected_bull_mode=selected_mode,
                    selected_run_dir=selected_run_dir,
                    candidate_metrics=metrics,
                    incumbent_metrics=_incumbent_metrics_for_selected_candidate(selected_payload),
                    promotion_gate=deterministic_gate,
                    benchmark_report_paths=benchmark_report_paths,
                )
                promotion["ai_tier2_review"] = {
                    "status": ai_tier2_review.get("status"),
                    "decision": ai_tier2_review.get("decision"),
                    "approved": ai_tier2_review.get("approved"),
                    "blocking_reasons": ai_tier2_review.get("blocking_reasons") or [],
                    "json_path": ai_tier2_review.get("json_path"),
                    "markdown_path": ai_tier2_review.get("markdown_path"),
                }
                if not (ai_tier2_review.get("status") == "parsed" and ai_tier2_review.get("decision") == "approved"):
                    status = "not_promoted_ai_tier2_blocked"
                    promotion["blocked_reason"] = "ai_tier2_not_approved"
                    promotion["runtime_change"] = False
                    promotion["active_live_behavior"] = False
                    promotion["forbidden_runtime_uses"] = ai_tier2_review.get("forbidden_runtime_uses") or []
                    remediation = write_remediation_report(
                        target_date=target,
                        tier2_review=ai_tier2_review,
                        retrain_report={
                            "status": status,
                            "promotion": promotion,
                            "candidate_family": selected_candidate_family,
                            "bull_specialist_mode": selected_mode,
                            "metrics": metrics,
                        },
                        benchmark_report_paths=benchmark_report_paths,
                    )
                    promotion["remediation"] = {
                        "remediation_state": remediation.get("remediation_state"),
                        "retry_reason": remediation.get("retry_reason"),
                        "retry_count": remediation.get("retry_count"),
                        "max_retry_count": remediation.get("max_retry_count"),
                        "next_cron_allowed": remediation.get("next_cron_allowed"),
                        "retry_env_keys": sorted((remediation.get("retry_env") or {}).keys()),
                        "manifest_path": remediation.get("manifest_path"),
                        "json_path": remediation.get("json_path"),
                        "markdown_path": remediation.get("markdown_path"),
                    }
                    promotion["mlflow"] = log_model_run(
                        run_name=f"ai_tier2_blocked:{selected_candidate_family}:{target}",
                        params={
                            "run_id": run_id,
                            "target_date": target,
                            "candidate_family": selected_candidate_family,
                            "bull_mode": selected_mode,
                            "feature_set_version": FEATURE_SET_VERSION,
                            "label_policy": LABEL_POLICY,
                            "primary_decision_metric": METRIC_CONTRACT["primary_decision_metric"],
                            "active_promotion_decision": "not_promoted_ai_tier2_blocked",
                            "ai_tier2_status": ai_tier2_review.get("status"),
                            "ai_tier2_decision": ai_tier2_review.get("decision"),
                            "ai_tier2_blocking_reasons": ",".join(ai_tier2_review.get("blocking_reasons") or []),
                            "remediation_state": remediation.get("remediation_state"),
                            "retry_allowed": str(remediation.get("remediation_state") == "retry_allowed"),
                            "retry_env_keys": ",".join(sorted((remediation.get("retry_env") or {}).keys())),
                            "retry_reason": remediation.get("retry_reason"),
                        },
                        metrics={
                            "equal_weight_avg_profit_pct": metrics.get("equal_weight_avg_profit_pct"),
                            "notional_weighted_ev_pct": metrics.get("notional_weighted_ev_pct"),
                            "source_quality_adjusted_ev_pct": metrics.get("source_quality_adjusted_ev_pct"),
                            "sample_count": metrics.get("sample_count"),
                            "downside_p10_pct": metrics.get("downside_p10_pct"),
                            "diagnostic_win_rate": metrics.get("diagnostic_win_rate"),
                            "selected_count": metrics.get("selected_count"),
                        },
                        tags={
                            "stage": "ai_tier2_model_promotion_review",
                            "ai_tier2_status": ai_tier2_review.get("status"),
                            "ai_tier2_decision": ai_tier2_review.get("decision"),
                            "remediation_state": remediation.get("remediation_state"),
                            "retry_allowed": str(remediation.get("remediation_state") == "retry_allowed"),
                            "active_live_behavior": "false",
                            "runtime_change": "none",
                        },
                        artifact_paths=[
                            Path(str(ai_tier2_review["json_path"]))
                            for _ in [0]
                            if ai_tier2_review.get("json_path")
                        ]
                        + [
                            Path(str(remediation["manifest_path"]))
                            for _ in [0]
                            if remediation.get("manifest_path")
                        ],
                    )
                else:
                    backup_dir = PROMOTIONS_DIR / f"{run_id}_backup"
                    promotion.update(_promote_candidate(selected_run_dir, backup_dir, selected_mode))
                    smoke = _smoke_after_promote(selected_mode)
                    promotion["smoke"] = smoke
                    live_schema_check = {"passed": False, "reason": "smoke_failed"}
                    if smoke.get("returncode") == 0:
                        live_schema_check = _validate_live_recommendation_schema()
                    promotion["schema_check_after_promote"] = live_schema_check
                    if smoke.get("returncode") == 0 and live_schema_check.get("passed"):
                        promoted = True
                        status = "promoted"
                        current_path = _write_current_manifest(
                            run_id,
                            target,
                            selected_run_dir,
                            selected_mode,
                            metrics,
                            candidate_family=selected_candidate_family,
                        )
                        promotion["current_manifest"] = str(current_path)
                        promotion_artifacts = [current_path]
                        if benchmark_report_paths.get("json"):
                            promotion_artifacts.append(Path(benchmark_report_paths["json"]))
                        if ai_tier2_review.get("json_path"):
                            promotion_artifacts.append(Path(str(ai_tier2_review["json_path"])))
                        tracking = log_model_run(
                            run_name=f"promotion:{selected_candidate_family}:{target}",
                            params={
                                "run_id": run_id,
                                "target_date": target,
                                "candidate_family": selected_candidate_family,
                                "bull_mode": selected_mode,
                                "feature_set_version": FEATURE_SET_VERSION,
                                "label_policy": LABEL_POLICY,
                                "primary_decision_metric": METRIC_CONTRACT["primary_decision_metric"],
                                "active_promotion_decision": "promoted",
                                "ai_tier2_status": ai_tier2_review.get("status"),
                                "ai_tier2_decision": ai_tier2_review.get("decision"),
                                "ai_tier2_blocking_reasons": ",".join(ai_tier2_review.get("blocking_reasons") or []),
                            },
                            metrics={
                                "equal_weight_avg_profit_pct": metrics.get("equal_weight_avg_profit_pct"),
                                "notional_weighted_ev_pct": metrics.get("notional_weighted_ev_pct"),
                                "source_quality_adjusted_ev_pct": metrics.get("source_quality_adjusted_ev_pct"),
                                "sample_count": metrics.get("sample_count"),
                                "downside_p10_pct": metrics.get("downside_p10_pct"),
                                "diagnostic_win_rate": metrics.get("diagnostic_win_rate"),
                                "selected_count": metrics.get("selected_count"),
                            },
                            tags={
                                "stage": "active_promotion",
                                "ai_tier2_status": ai_tier2_review.get("status"),
                                "ai_tier2_decision": ai_tier2_review.get("decision"),
                                "active_live_behavior": "true",
                                "runtime_change": "model_artifact_promote_only",
                                "swing_live_order_dry_run_required": "true",
                            },
                            artifact_paths=promotion_artifacts,
                        )
                        promotion["mlflow"] = tracking
                    else:
                        rollback_executed = True
                        promotion["rollback_files"] = _rollback_active_models(backup_dir)
                        if smoke.get("returncode") == 0:
                            promotion["blocked_reason"] = "recommendation_schema_compatibility_failed"
                        status = "rolled_back"
            else:
                status = "passed_not_promoted"
                promotion["blocked_reason"] = "auto_promote_false"

    min_score = _safe_float(os.getenv("KORSTOCKSCAN_SWING_RETRAIN_MIN_SCORE"), 0.72)
    sample_count = _safe_int(metrics.get("sample_count"), 0)
    avg_net_pct = _safe_float(metrics.get("avg_net_pct"), 0.0)
    candidate_score = _safe_float(metrics.get("tradeoff_score"), 0.0)
    promotion_guard = {
        "min_tradeoff_score": min_score,
        "sample_floor": 40,
        "avg_net_floor_pct": 0.10,
        "candidate_score": candidate_score,
        "sample_count": sample_count,
        "avg_net_pct": avg_net_pct,
        "sample_floor_passed": sample_count >= 40,
        "avg_net_floor_passed": avg_net_pct >= 0.10,
        "tradeoff_score_floor_passed": candidate_score >= min_score,
        "decision": status,
        "reason": promotion.get("blocked_reason")
        or mode_decision.get("reason")
        or ("retrain_not_required" if not bool(diagnosis.get("retrain_required")) else status),
        "bull_specialist_mode": selected_mode,
    }

    report = {
        "schema_version": 1,
        "report_type": "swing_model_retrain",
        "target_date": target,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "run_id": run_id,
        "status": status,
        "runtime_change": "model_artifact_promote_only" if promoted else False,
        "active_live_behavior": bool(promoted),
        "swing_live_order_dry_run_required": True,
        "diagnosis": diagnosis,
        "bull_period_review": bull_review,
        "meta_period": meta_period,
        "bull_specialist_mode": selected_mode,
        "candidate_family": selected_candidate_family,
        "bull_mode_decision": mode_decision,
        "run_dir": str(run_dir),
        "selected_run_dir": str(selected_run_dir),
        "candidate_results": candidate_results,
        "command_results": command_results,
        "metrics": metrics,
        "benchmark_report": benchmark_report_paths,
        "metric_contract": METRIC_CONTRACT,
        "ai_tier2_review": ai_tier2_review,
        "remediation": remediation,
        "promotion_guard": promotion_guard,
        "auto_promote": auto_promote,
        "promoted": promoted,
        "rollback_executed": rollback_executed,
        "promotion": promotion,
    }
    json_path, md_path = pipeline_paths(target)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    PROMOTIONS_DIR.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    promotion_path = PROMOTIONS_DIR / f"promotion_{target}.json"
    promotion_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run swing v2 retrain pipeline.")
    parser.add_argument("--date", dest="target_date", default=date.today().isoformat())
    parser.add_argument("--auto-promote", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    report = run_pipeline(args.target_date, auto_promote=args.auto_promote, force=args.force)
    return 0 if report.get("status") not in {"failed", "rolled_back"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
