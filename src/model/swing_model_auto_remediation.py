from __future__ import annotations

import argparse
import json
import os
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from src.model.common_v2 import DATA_DIR, MODEL_REGISTRY_DIR
from src.model.swing_model_tier2_review import FORBIDDEN_RUNTIME_USES
from src.model.swing_model_upgrade import CANDIDATE_FAMILIES

REPORT_DIR = Path(DATA_DIR) / "report" / "swing_model_remediation"
REMEDIATION_DIR = Path(MODEL_REGISTRY_DIR) / "remediation"
MAX_OPTUNA_TRIALS = 80
MAX_OPTUNA_TIMEOUT_SEC = 3600
DEFAULT_MAX_RETRY_COUNT = 1
ALLOWED_RETRY_ENV = {
    "KORSTOCKSCAN_SWING_RETRAIN_FORCE",
    "KORSTOCKSCAN_SWING_MODEL_OPTUNA_TRIALS",
    "KORSTOCKSCAN_SWING_MODEL_OPTUNA_TIMEOUT_SEC",
    "KORSTOCKSCAN_SWING_MODEL_UPGRADE_FAMILIES",
    "KORSTOCKSCAN_SWING_MODEL_TIER2_REVIEW_PROVIDER",
}
FORBIDDEN_ENV_TOKENS = {
    "RUNTIME",
    "ORDER",
    "PROVIDER_ROUTE",
    "BOT",
    "THRESHOLD",
    "CAP_RELEASE",
    "DRY_RUN_DISABLE",
    "LIVE_ORDER",
}
RETRY_ALLOWED_REASONS = {
    "schema",
    "schema_compatibility",
    "schema_compatibility_failed",
    "active_artifact_path_inconsistency",
    "candidate_artifact_missing",
    "artifact_missing",
    "training_command_failed",
}
RETRY_DEFERRED_REASONS = {
    "ai_response_unavailable",
    "openai_api_key not configured",
    "all openai attempts failed",
    "parse_rejected",
    "ai_json_parse_failed",
    "sample_floor_not_met",
    "insufficient_sample",
}


def _safe_load_json(path: Path | str | None) -> dict[str, Any]:
    if not path:
        return {}
    try:
        target = Path(path)
        if not target.exists():
            return {}
        payload = json.loads(target.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except Exception as exc:
        return {"load_error": str(exc), "path": str(path)}


def remediation_manifest_path(target_date: str) -> Path:
    return REMEDIATION_DIR / f"remediation_{target_date}.json"


def remediation_report_paths(target_date: str) -> tuple[Path, Path]:
    base = REPORT_DIR / f"swing_model_remediation_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _normalize_reasons(*payloads: Any) -> list[str]:
    reasons: list[str] = []
    for payload in payloads:
        if payload is None:
            continue
        if isinstance(payload, str):
            reasons.append(payload)
        elif isinstance(payload, list):
            reasons.extend(str(item) for item in payload if item not in (None, ""))
        elif isinstance(payload, dict):
            for key in ("blocking_reasons", "reasons"):
                value = payload.get(key)
                if isinstance(value, list):
                    reasons.extend(
                        str(item) for item in value if item not in (None, "")
                    )
            if payload.get("reason"):
                reasons.append(str(payload["reason"]))
    return sorted(set(reason.strip() for reason in reasons if str(reason).strip()))


def _reason_blob(reasons: list[str]) -> str:
    return " | ".join(reasons).lower()


def _sanitize_retry_env(raw_env: dict[str, Any]) -> tuple[dict[str, str], list[str]]:
    sanitized: dict[str, str] = {}
    warnings: list[str] = []
    for key, value in (raw_env or {}).items():
        key = str(key)
        if key not in ALLOWED_RETRY_ENV or any(
            token in key for token in FORBIDDEN_ENV_TOKENS
        ):
            warnings.append(f"removed_disallowed_env:{key}")
            continue
        if key == "KORSTOCKSCAN_SWING_RETRAIN_FORCE":
            sanitized[key] = (
                "true" if str(value).lower() in {"1", "true", "yes", "on"} else "false"
            )
        elif key == "KORSTOCKSCAN_SWING_MODEL_OPTUNA_TRIALS":
            try:
                sanitized[key] = str(min(MAX_OPTUNA_TRIALS, max(40, int(float(value)))))
            except Exception:
                warnings.append(f"invalid_env_value:{key}")
        elif key == "KORSTOCKSCAN_SWING_MODEL_OPTUNA_TIMEOUT_SEC":
            try:
                sanitized[key] = str(
                    min(MAX_OPTUNA_TIMEOUT_SEC, max(1800, int(float(value))))
                )
            except Exception:
                warnings.append(f"invalid_env_value:{key}")
        elif key == "KORSTOCKSCAN_SWING_MODEL_UPGRADE_FAMILIES":
            requested = [item.strip() for item in str(value).split(",") if item.strip()]
            allowed = [item for item in requested if item in CANDIDATE_FAMILIES]
            if allowed:
                sanitized[key] = ",".join(allowed)
            elif requested:
                warnings.append(f"invalid_env_value:{key}")
        elif key == "KORSTOCKSCAN_SWING_MODEL_TIER2_REVIEW_PROVIDER":
            sanitized[key] = "openai"
    return sanitized, warnings


def _default_retry_env(
    reason_state: str, benchmark_report: dict[str, Any]
) -> dict[str, Any]:
    retry_env: dict[str, Any] = {
        "KORSTOCKSCAN_SWING_RETRAIN_FORCE": "true",
        "KORSTOCKSCAN_SWING_MODEL_TIER2_REVIEW_PROVIDER": "openai",
    }
    if reason_state == "candidate_retry":
        retry_env["KORSTOCKSCAN_SWING_MODEL_OPTUNA_TRIALS"] = str(MAX_OPTUNA_TRIALS)
        retry_env["KORSTOCKSCAN_SWING_MODEL_OPTUNA_TIMEOUT_SEC"] = str(
            MAX_OPTUNA_TIMEOUT_SEC
        )
        families = sorted(CANDIDATE_FAMILIES)
        candidates = (
            benchmark_report.get("candidate_results")
            if isinstance(benchmark_report.get("candidate_results"), dict)
            else {}
        )
        seen = []
        for item in candidates.values():
            family = str((item or {}).get("selected_candidate_family") or "")
            if family in CANDIDATE_FAMILIES and family not in seen:
                seen.append(family)
        retry_env["KORSTOCKSCAN_SWING_MODEL_UPGRADE_FAMILIES"] = ",".join(
            seen or families
        )
    return retry_env


def _previous_retry_count(target_date: str) -> int:
    existing = _safe_load_json(remediation_manifest_path(target_date))
    if not existing:
        return 0
    try:
        return int(existing.get("retry_count", 0) or 0) + 1
    except Exception:
        return 1


def classify_remediation(
    *,
    target_date: str,
    tier2_review: dict[str, Any],
    retrain_report: dict[str, Any] | None = None,
    benchmark_report: dict[str, Any] | None = None,
    max_retry_count: int = DEFAULT_MAX_RETRY_COUNT,
) -> dict[str, Any]:
    retrain_report = retrain_report or {}
    benchmark_report = benchmark_report or {}
    reasons = _normalize_reasons(
        tier2_review,
        (
            retrain_report.get("promotion")
            if isinstance(retrain_report.get("promotion"), dict)
            else {}
        ),
        (
            (retrain_report.get("promotion_guard") or {}).get("reason")
            if isinstance(retrain_report.get("promotion_guard"), dict)
            else None
        ),
    )
    if not reasons and tier2_review.get("status") in {"unavailable", "parse_rejected"}:
        reasons = [str(tier2_review.get("status"))]
    blob = _reason_blob(reasons)
    retry_count = _previous_retry_count(target_date)
    retry_env: dict[str, Any] = {}
    retry_reason = "unclassified_ai_tier2_block"
    state = "manual_required"
    next_cron_allowed = False

    if "forbidden_use" in blob:
        state = "blocked_forbidden_use"
        retry_reason = "forbidden_use"
    elif "label_leakage" in blob:
        state = "manual_required"
        retry_reason = "label_leakage"
    elif "metric_contract" in blob:
        state = "manual_required"
        retry_reason = "metric_contract"
    elif retry_count >= max_retry_count:
        state = "manual_required"
        retry_reason = "retry_budget_exhausted"
    elif any(reason in blob for reason in RETRY_ALLOWED_REASONS):
        state = "retry_allowed"
        retry_reason = "schema_or_candidate_artifact_retry"
        retry_env = _default_retry_env(
            (
                "candidate_retry"
                if "artifact" in blob or "training_command" in blob
                else "schema_retry"
            ),
            benchmark_report,
        )
        next_cron_allowed = True
    elif any(reason in blob for reason in RETRY_DEFERRED_REASONS) or str(
        tier2_review.get("status")
    ) in {"unavailable", "parse_rejected"}:
        state = "retry_deferred"
        retry_reason = "deferred_until_next_source_or_ai_availability"
    elif "source_quality" in blob and ("sample" in blob or "insufficient" in blob):
        state = "retry_deferred"
        retry_reason = "source_quality_sample_wait"
    elif "source_quality" in blob and (
        "artifact" in blob or "family" in blob or "training" in blob
    ):
        state = "retry_allowed"
        retry_reason = "source_quality_candidate_retry"
        retry_env = _default_retry_env("candidate_retry", benchmark_report)
        next_cron_allowed = True

    sanitized_env, warnings = _sanitize_retry_env(retry_env)
    if state != "retry_allowed":
        sanitized_env = {}
    return {
        "schema_version": 1,
        "target_date": target_date,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_status": tier2_review.get("status") or retrain_report.get("status"),
        "source_blocking_reasons": reasons,
        "remediation_state": state,
        "retry_env": sanitized_env,
        "retry_reason": retry_reason,
        "max_retry_count": int(max_retry_count),
        "retry_count": int(retry_count),
        "next_cron_allowed": bool(next_cron_allowed and sanitized_env),
        "forbidden_runtime_uses": FORBIDDEN_RUNTIME_USES,
        "warnings": warnings,
    }


def render_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"# Swing Model Remediation {report.get('target_date')}",
            "",
            f"- remediation_state: `{report.get('remediation_state')}`",
            f"- retry_reason: `{report.get('retry_reason')}`",
            f"- retry_count: `{report.get('retry_count')}` / `{report.get('max_retry_count')}`",
            f"- next_cron_allowed: `{report.get('next_cron_allowed')}`",
            f"- retry_env_keys: `{', '.join(sorted((report.get('retry_env') or {}).keys()))}`",
            "- runtime_change: `none_until_candidate_repasses_all_gates`",
            "- active_artifact_change: `false`",
            "",
        ]
    )


def write_remediation_report(
    *,
    target_date: str,
    tier2_review: dict[str, Any],
    retrain_report: dict[str, Any] | None = None,
    benchmark_report_paths: dict[str, str] | None = None,
    max_retry_count: int = DEFAULT_MAX_RETRY_COUNT,
) -> dict[str, Any]:
    benchmark_report = _safe_load_json((benchmark_report_paths or {}).get("json"))
    report = classify_remediation(
        target_date=target_date,
        tier2_review=tier2_review,
        retrain_report=retrain_report or {},
        benchmark_report=benchmark_report,
        max_retry_count=max_retry_count,
    )
    source_artifacts = {
        "tier2_review_json": tier2_review.get("json_path"),
        "tier2_review_markdown": tier2_review.get("markdown_path"),
        "benchmark_json": (benchmark_report_paths or {}).get("json"),
        "benchmark_markdown": (benchmark_report_paths or {}).get("markdown"),
    }
    report["source_artifacts"] = source_artifacts
    manifest_path = remediation_manifest_path(target_date)
    json_path, md_path = remediation_report_paths(target_date)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return {
        **report,
        "manifest_path": str(manifest_path),
        "json_path": str(json_path),
        "markdown_path": str(md_path),
    }


def _candidate_manifest_paths(target_date: str) -> list[Path]:
    paths = [remediation_manifest_path(target_date)]
    try:
        previous = (
            datetime.fromisoformat(target_date).date() - timedelta(days=1)
        ).isoformat()
        paths.append(remediation_manifest_path(previous))
    except Exception:
        pass
    return paths


def resolve_cron_remediation(target_date: str) -> dict[str, Any]:
    selected_path = None
    manifest: dict[str, Any] = {}
    for path in _candidate_manifest_paths(target_date):
        payload = _safe_load_json(path)
        if payload:
            selected_path = path
            manifest = payload
            break
    if not manifest:
        return {"found": False, "action": "ignore", "remediation_applied": False}
    retry_env, warnings = _sanitize_retry_env(
        manifest.get("retry_env") if isinstance(manifest.get("retry_env"), dict) else {}
    )
    state = str(manifest.get("remediation_state") or "manual_required")
    retry_count = int(manifest.get("retry_count") or 0)
    max_retry_count = int(manifest.get("max_retry_count") or DEFAULT_MAX_RETRY_COUNT)
    if state == "retry_allowed" and retry_env and retry_count < max_retry_count:
        action = "apply_retry_env"
    elif state == "retry_allowed" and retry_count >= max_retry_count:
        action = "exit"
        state = "manual_required"
    elif state in {"retry_deferred", "manual_required", "blocked_forbidden_use"}:
        action = "exit"
    else:
        action = "exit"
        state = "manual_required"
    return {
        "found": True,
        "action": action,
        "remediation_applied": action == "apply_retry_env",
        "remediation_state": state,
        "retry_env": retry_env if action == "apply_retry_env" else {},
        "retry_env_keys": sorted(retry_env) if action == "apply_retry_env" else [],
        "retry_reason": manifest.get("retry_reason"),
        "retry_count": retry_count,
        "max_retry_count": max_retry_count,
        "manifest_path": str(selected_path) if selected_path else None,
        "warnings": sorted(set([*(manifest.get("warnings") or []), *warnings])),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Create or resolve swing model auto-remediation manifests."
    )
    parser.add_argument(
        "--resolve-cron",
        metavar="DATE",
        help="Resolve retry env for an auto_retrain cron date.",
    )
    parser.add_argument("--date", dest="target_date", default=date.today().isoformat())
    parser.add_argument("--tier2-review-json")
    parser.add_argument("--retrain-json")
    parser.add_argument("--benchmark-json")
    args = parser.parse_args(argv)
    if args.resolve_cron:
        print(
            json.dumps(
                resolve_cron_remediation(args.resolve_cron),
                ensure_ascii=False,
                separators=(",", ":"),
            )
        )
        return 0
    if not args.tier2_review_json:
        raise SystemExit(
            "--tier2-review-json is required unless --resolve-cron is used"
        )
    report = write_remediation_report(
        target_date=args.target_date,
        tier2_review=_safe_load_json(args.tier2_review_json),
        retrain_report=_safe_load_json(args.retrain_json),
        benchmark_report_paths=(
            {"json": args.benchmark_json} if args.benchmark_json else {}
        ),
    )
    print(
        json.dumps(
            {
                "remediation_state": report["remediation_state"],
                "manifest_path": report["manifest_path"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
