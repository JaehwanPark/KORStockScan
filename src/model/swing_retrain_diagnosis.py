from __future__ import annotations

import argparse
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.model.common_v2 import DATA_DIR, load_swing_model_current_manifest

REPORT_DIR = Path(DATA_DIR) / "report" / "swing_model_retrain"
MODEL_PATHS = [
    Path(DATA_DIR) / "hybrid_xgb_v2.pkl",
    Path(DATA_DIR) / "hybrid_lgbm_v2.pkl",
    Path(DATA_DIR) / "bull_xgb_v2.pkl",
    Path(DATA_DIR) / "bull_lgbm_v2.pkl",
    Path(DATA_DIR) / "stacking_meta_v2.pkl",
]


def _safe_load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _parse_date(value: Any) -> date | None:
    try:
        if value in (None, ""):
            return None
        return datetime.fromisoformat(str(value)[:10]).date()
    except Exception:
        return None


def _artifact_age_days(target: date) -> int | None:
    existing = [path for path in MODEL_PATHS if path.exists()]
    if not existing:
        return None
    oldest_mtime = min(path.stat().st_mtime for path in existing)
    artifact_date = datetime.fromtimestamp(oldest_mtime).date()
    return max(0, (target - artifact_date).days)


def _latest_recommendation_diag() -> dict[str, Any]:
    return _safe_load_json(Path(DATA_DIR) / "daily_recommendations_v2_diagnostics.json")


def _latest_ev_report(target: date) -> dict[str, Any]:
    return _safe_load_json(
        Path(DATA_DIR)
        / "report"
        / "threshold_cycle_ev"
        / f"threshold_cycle_ev_{target.isoformat()}.json"
    )


def build_retrain_diagnosis(
    target_date: str | None = None, *, force: bool = False
) -> dict[str, Any]:
    target = _parse_date(target_date) or date.today()
    manifest = load_swing_model_current_manifest()
    diag = _latest_recommendation_diag()
    ev_report = _latest_ev_report(target)
    artifact_age = _artifact_age_days(target)
    selected_count = int(diag.get("selected_count") or 0)
    fallback_written = bool(diag.get("fallback_written_to_recommendations"))
    ev_summary = (
        ev_report.get("daily_ev_summary")
        if isinstance(ev_report.get("daily_ev_summary"), dict)
        else {}
    )
    avg_profit = float(ev_summary.get("avg_profit_rate_pct") or 0.0)

    hard_triggers: list[str] = []
    if force:
        hard_triggers.append("force_requested")
    if artifact_age is None:
        hard_triggers.append("model_artifact_missing")
    elif artifact_age >= 60:
        hard_triggers.append("model_artifact_age_ge_60d")
    if selected_count <= 0:
        hard_triggers.append("selected_count_zero")
    if fallback_written:
        hard_triggers.append("fallback_contamination")
    if avg_profit <= -0.25:
        hard_triggers.append("recent_ev_degradation")

    soft_components = {
        "artifact_age": min(1.0, (artifact_age or 0) / 60.0) * 0.20,
        "forward_ev": (1.0 if avg_profit <= -0.25 else 0.0) * 0.35,
        "candidate_funnel": (1.0 if selected_count <= 0 else 0.0) * 0.15,
        "drift_proxy": 0.0,
        "data_quality": (1.0 if fallback_written else 0.0) * 0.10,
    }
    soft_score = round(sum(soft_components.values()), 4)
    retrain_required = bool(hard_triggers) or soft_score >= 0.70
    return {
        "schema_version": 1,
        "report_type": "swing_retrain_diagnosis",
        "target_date": target.isoformat(),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "runtime_change": False,
        "manifest": {
            "available": bool(manifest),
            "run_id": manifest.get("run_id"),
            "bull_specialist_mode": manifest.get("bull_specialist_mode"),
        },
        "metrics": {
            "artifact_age_days": artifact_age,
            "selected_count": selected_count,
            "fallback_written_to_recommendations": fallback_written,
            "avg_profit_rate_pct": avg_profit,
        },
        "hard_triggers": hard_triggers,
        "soft_components": soft_components,
        "soft_score": soft_score,
        "retrain_required": retrain_required,
        "reason": "hard_trigger_or_soft_score" if retrain_required else "no_trigger",
    }


def diagnosis_paths(target_date: str) -> tuple[Path, Path]:
    base = REPORT_DIR / f"diagnosis_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def render_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"# Swing Retrain Diagnosis {report.get('target_date')}",
            "",
            f"- retrain_required: `{report.get('retrain_required')}`",
            f"- hard_triggers: `{', '.join(report.get('hard_triggers') or []) or '-'}`",
            f"- soft_score: `{report.get('soft_score')}`",
            "- runtime_change: `false`",
            "",
        ]
    )


def write_diagnosis(
    target_date: str | None = None, *, force: bool = False
) -> dict[str, Any]:
    report = build_retrain_diagnosis(target_date, force=force)
    json_path, md_path = diagnosis_paths(str(report["target_date"]))
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Diagnose whether swing v2 model retraining is required."
    )
    parser.add_argument("--date", dest="target_date", default=date.today().isoformat())
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    write_diagnosis(args.target_date, force=args.force)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
