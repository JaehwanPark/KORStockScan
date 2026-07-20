from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.model.common_v2 import DATA_DIR

AI_REVIEW_SCHEMA_NAME = "swing_model_tier2_review_v1"
REPORT_DIR = Path(DATA_DIR) / "report" / "swing_model_tier2_review"
CHECK_KEYS = {
    "label_leakage",
    "source_quality",
    "schema_compatibility",
    "metric_interpretation",
    "forbidden_use",
}
VALID_STATUSES = {"parsed", "parse_rejected", "unavailable"}
VALID_DECISIONS = {"approved", "blocked"}
VALID_CHECK_VALUES = {"pass", "block", "warning"}
FORBIDDEN_RUNTIME_USES = [
    "swing_dry_run_disable",
    "real_order_conversion",
    "phase0_real_canary_enablement",
    "cap_release",
    "provider_route_change",
    "bot_restart",
    "hard_safety_relaxation",
    "intraday_threshold_mutation",
]


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


def _text_hash(payload: Any) -> str:
    raw = json.dumps(payload, ensure_ascii=True, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def review_paths(target_date: str) -> tuple[Path, Path]:
    base = REPORT_DIR / f"swing_model_tier2_review_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _build_review_context(
    *,
    target_date: str,
    run_id: str,
    selected_candidate_family: str,
    selected_bull_mode: str,
    selected_run_dir: Path,
    candidate_metrics: dict[str, Any],
    incumbent_metrics: dict[str, Any],
    promotion_gate: dict[str, Any],
    benchmark_report: dict[str, Any],
    candidate_manifest: dict[str, Any],
    shap_summary: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "target_date": target_date,
        "run_id": run_id,
        "selected_candidate_family": selected_candidate_family,
        "selected_bull_mode": selected_bull_mode,
        "selected_run_dir": str(selected_run_dir),
        "candidate_metrics": candidate_metrics,
        "incumbent_metrics": incumbent_metrics,
        "promotion_gate": promotion_gate,
        "benchmark_report_summary": {
            "available": bool(benchmark_report),
            "report_type": benchmark_report.get("report_type"),
            "metric_contract": benchmark_report.get("metric_contract"),
            "candidate_modes": sorted(
                (benchmark_report.get("candidate_results") or {}).keys()
            ),
        },
        "candidate_manifest": candidate_manifest,
        "shap_summary": shap_summary,
        "allowed_decisions": ["approved", "blocked"],
        "approval_preconditions": [
            "deterministic promotion gate already passed",
            "candidate family and bull mode match the selected deterministic candidate",
            "label leakage check has no explicit gap",
            "source quality check has no explicit gap",
            "recommendation schema compatibility has no explicit gap",
            "metric contract uses equal_weight_avg_profit_pct as the primary metric",
            "no forbidden runtime use is requested",
        ],
        "allowed_blocking_reasons": [
            "label_leakage",
            "source_quality",
            "schema",
            "metric_contract",
            "forbidden_use",
            "active_artifact_path_inconsistency",
        ],
        "forbidden_runtime_uses": FORBIDDEN_RUNTIME_USES,
        "authority": "review_only_fail_closed_model_artifact_promotion_gate",
    }


def _build_review_instructions() -> str:
    return (
        "You are the Tier2 reviewer for swing v2 model artifact promotion.\n"
        "Your authority is review-only and fail-closed. You may approve or block only the deterministic candidate "
        "already selected by the pipeline.\n"
        "You must not create candidates, change thresholds, change providers, restart the bot, release caps, "
        "disable swing dry-run, enable real orders, or relax hard safety.\n\n"
        "Approve only when every explicit gap check passes. Blocking reasons must be limited to: "
        "label_leakage, source_quality, schema, metric_contract, forbidden_use, "
        "active_artifact_path_inconsistency.\n"
        "Return only JSON that conforms to the strict swing_model_tier2_review_v1 schema."
    )


def _call_openai_review(
    input_context: dict[str, Any],
) -> tuple[str | None, dict[str, Any]]:
    try:
        from openai import OpenAI, RateLimitError
        from src.engine.ai_response_contracts import build_openai_response_text_format
        from src.engine.daily_threshold_cycle_report import (
            _extract_openai_response_text,
            _load_threshold_ai_openai_keys,
            _threshold_ai_openai_model_sequence,
        )
    except Exception as exc:
        return None, {
            "provider": "openai",
            "status": "unavailable",
            "reason": f"openai import failed: {exc}",
        }

    api_keys = _load_threshold_ai_openai_keys()
    if not api_keys:
        return None, {
            "provider": "openai",
            "status": "unavailable",
            "reason": "OPENAI_API_KEY not configured",
        }

    model_sequence = _threshold_ai_openai_model_sequence()
    prompt = json.dumps(input_context, ensure_ascii=True, indent=2, default=str)
    errors: list[dict[str, str]] = []
    for model in model_sequence:
        for attempt_index, (key_name, api_key) in enumerate(api_keys, start=1):
            try:
                client = OpenAI(api_key=api_key)
                response = client.responses.create(
                    model=model,
                    instructions=_build_review_instructions(),
                    input=prompt,
                    text={
                        "format": build_openai_response_text_format(
                            AI_REVIEW_SCHEMA_NAME
                        ),
                        "verbosity": "low",
                    },
                    reasoning={"effort": "high"},
                    store=False,
                    metadata={
                        "endpoint_name": "swing_model_tier2_review",
                        "schema_name": AI_REVIEW_SCHEMA_NAME,
                        "report_type": "swing_model_tier2_review",
                    },
                    timeout=180,
                )
                raw_text = _extract_openai_response_text(response)
                usage = getattr(response, "usage", None)
                return raw_text, {
                    "provider": "openai",
                    "status": "success",
                    "key_name": key_name,
                    "attempt_index": attempt_index,
                    "attempted_key_count": len(api_keys),
                    "model": model,
                    "schema_name": AI_REVIEW_SCHEMA_NAME,
                    "reasoning_effort": "high",
                    "input_context_hash": _text_hash(input_context),
                    "input_context_chars": len(prompt),
                    "output_chars": len(raw_text),
                    "input_tokens": (
                        int(getattr(usage, "input_tokens", 0) or 0) if usage else 0
                    ),
                    "output_tokens": (
                        int(getattr(usage, "output_tokens", 0) or 0) if usage else 0
                    ),
                    "total_tokens": (
                        int(getattr(usage, "total_tokens", 0) or 0) if usage else 0
                    ),
                }
            except RateLimitError as exc:
                errors.append(
                    {"model": model, "key_name": key_name, "error": f"rate_limit:{exc}"}
                )
            except Exception as exc:
                errors.append({"model": model, "key_name": key_name, "error": str(exc)})
    return None, {
        "provider": "openai",
        "status": "unavailable",
        "reason": "all OpenAI attempts failed",
        "models": model_sequence,
        "errors": errors[-5:],
    }


def parse_tier2_review_response(
    raw_response: Any,
    *,
    expected_candidate_family: str,
    expected_bull_mode: str,
) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    if raw_response in (None, ""):
        return {
            "schema_version": 1,
            "status": "unavailable",
            "decision": "blocked",
            "blocking_reasons": ["ai_response_unavailable"],
            "reviewed_candidate_family": expected_candidate_family,
            "reviewed_bull_mode": expected_bull_mode,
            "checks": {key: "block" for key in CHECK_KEYS},
        }, ["ai_response_unavailable"]

    if isinstance(raw_response, dict):
        payload = raw_response
    else:
        try:
            payload = json.loads(str(raw_response))
        except Exception as exc:
            return {
                "schema_version": 1,
                "status": "parse_rejected",
                "decision": "blocked",
                "blocking_reasons": ["ai_json_parse_failed"],
                "reviewed_candidate_family": expected_candidate_family,
                "reviewed_bull_mode": expected_bull_mode,
                "checks": {key: "block" for key in CHECK_KEYS},
                "parse_error": str(exc),
            }, ["ai_json_parse_failed"]

    if not isinstance(payload, dict):
        warnings.append("ai_payload_not_object")
        payload = {}
    status = str(payload.get("status") or "").strip()
    decision = str(payload.get("decision") or "").strip()
    reasons = payload.get("blocking_reasons")
    checks = payload.get("checks") if isinstance(payload.get("checks"), dict) else {}

    if payload.get("schema_version") != 1:
        warnings.append("schema_version_mismatch")
    if status not in VALID_STATUSES:
        warnings.append("invalid_status")
    if decision not in VALID_DECISIONS:
        warnings.append("invalid_decision")
    if not isinstance(reasons, list) or any(
        not isinstance(item, str) for item in reasons
    ):
        warnings.append("invalid_blocking_reasons")
        reasons = ["invalid_blocking_reasons"]
    if str(payload.get("reviewed_candidate_family") or "") != str(
        expected_candidate_family
    ):
        warnings.append("candidate_family_mismatch")
    if str(payload.get("reviewed_bull_mode") or "") != str(expected_bull_mode):
        warnings.append("bull_mode_mismatch")
    missing_checks = sorted(CHECK_KEYS - set(checks))
    invalid_checks = sorted(
        key
        for key, value in checks.items()
        if key in CHECK_KEYS and value not in VALID_CHECK_VALUES
    )
    if missing_checks:
        warnings.append(f"missing_checks:{','.join(missing_checks)}")
    if invalid_checks:
        warnings.append(f"invalid_checks:{','.join(invalid_checks)}")
    if (
        any(value == "block" for key, value in checks.items() if key in CHECK_KEYS)
        and decision != "blocked"
    ):
        warnings.append("block_check_requires_blocked_decision")

    if warnings:
        return {
            "schema_version": 1,
            "status": "parse_rejected",
            "decision": "blocked",
            "blocking_reasons": sorted(set([*list(reasons or []), *warnings])),
            "reviewed_candidate_family": expected_candidate_family,
            "reviewed_bull_mode": expected_bull_mode,
            "checks": {key: checks.get(key, "block") for key in CHECK_KEYS},
            "raw_payload": payload,
        }, warnings

    return {
        "schema_version": 1,
        "status": status,
        "decision": decision,
        "blocking_reasons": list(reasons or []),
        "reviewed_candidate_family": expected_candidate_family,
        "reviewed_bull_mode": expected_bull_mode,
        "checks": {key: checks[key] for key in sorted(CHECK_KEYS)},
    }, []


def render_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"# Swing Model Tier2 Review {report.get('target_date')}",
            "",
            f"- status: `{report.get('status')}`",
            f"- decision: `{report.get('decision')}`",
            f"- approved: `{report.get('approved')}`",
            f"- candidate_family: `{report.get('reviewed_candidate_family')}`",
            f"- bull_specialist_mode: `{report.get('reviewed_bull_mode')}`",
            f"- provider_status: `{(report.get('provider') or {}).get('status')}`",
            f"- blocking_reasons: `{', '.join(report.get('blocking_reasons') or [])}`",
            "- authority: `review_only_fail_closed_model_artifact_promotion_gate`",
            "- runtime_change: `model_artifact_promote_only_if_approved`",
            "- swing_live_order_dry_run_required: `true`",
            "",
        ]
    )


def write_tier2_review_report(
    *,
    target_date: str,
    run_id: str,
    selected_candidate_family: str,
    selected_bull_mode: str,
    selected_run_dir: Path | str,
    candidate_metrics: dict[str, Any],
    incumbent_metrics: dict[str, Any],
    promotion_gate: dict[str, Any],
    benchmark_report_paths: dict[str, str] | None = None,
    ai_review_provider: str | None = None,
    ai_raw_response: Any = None,
) -> dict[str, Any]:
    selected_path = Path(selected_run_dir)
    benchmark_report = _safe_load_json((benchmark_report_paths or {}).get("json"))
    candidate_manifest = _safe_load_json(selected_path / "candidate_manifest.json")
    shap_summary = _safe_load_json(selected_path / "shap_summary.json")
    context = _build_review_context(
        target_date=target_date,
        run_id=run_id,
        selected_candidate_family=selected_candidate_family,
        selected_bull_mode=selected_bull_mode,
        selected_run_dir=selected_path,
        candidate_metrics=candidate_metrics,
        incumbent_metrics=incumbent_metrics,
        promotion_gate=promotion_gate,
        benchmark_report=benchmark_report,
        candidate_manifest=candidate_manifest,
        shap_summary=shap_summary,
    )
    provider_name = (
        str(
            ai_review_provider
            or os.getenv("KORSTOCKSCAN_SWING_MODEL_TIER2_REVIEW_PROVIDER")
            or "openai"
        )
        .strip()
        .lower()
    )
    raw_response = ai_raw_response
    provider = {"provider": provider_name, "status": "not_called"}
    if raw_response is None:
        if provider_name == "openai":
            raw_response, provider = _call_openai_review(context)
        else:
            provider = {
                "provider": provider_name,
                "status": "unavailable",
                "reason": "unsupported_or_disabled_provider",
            }

    parsed, warnings = parse_tier2_review_response(
        raw_response,
        expected_candidate_family=selected_candidate_family,
        expected_bull_mode=selected_bull_mode,
    )
    approved = parsed.get("status") == "parsed" and parsed.get("decision") == "approved"
    blocking_reasons = list(parsed.get("blocking_reasons") or [])
    if provider.get("status") == "unavailable" and provider.get("reason"):
        blocking_reasons.append(str(provider["reason"]))
    if warnings:
        blocking_reasons.extend(warnings)
    if not approved and not blocking_reasons:
        blocking_reasons.append("ai_tier2_not_approved")

    report = {
        "schema_version": 1,
        "report_type": "swing_model_tier2_review",
        "target_date": target_date,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "run_id": run_id,
        "status": parsed.get("status"),
        "decision": parsed.get("decision"),
        "approved": approved,
        "blocking_reasons": sorted(set(blocking_reasons)),
        "reviewed_candidate_family": selected_candidate_family,
        "reviewed_bull_mode": selected_bull_mode,
        "checks": parsed.get("checks") or {},
        "provider": provider,
        "input_context_hash": _text_hash(context),
        "selected_run_dir": str(selected_path),
        "candidate_manifest_path": str(selected_path / "candidate_manifest.json"),
        "shap_summary_path": str(selected_path / "shap_summary.json"),
        "benchmark_report": benchmark_report_paths or {},
        "candidate_metrics": candidate_metrics,
        "incumbent_metrics": incumbent_metrics,
        "promotion_gate": promotion_gate,
        "forbidden_runtime_uses": FORBIDDEN_RUNTIME_USES,
        "active_live_behavior_scope": "model_artifact_current_json_daily_recommendations_only",
        "runtime_change": "model_artifact_promote_only_if_approved",
        "swing_live_order_dry_run_required": True,
    }
    json_path, md_path = review_paths(target_date)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    md_path.write_text(render_markdown(report), encoding="utf-8")
    report["json_path"] = str(json_path)
    report["markdown_path"] = str(md_path)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run swing model Tier2 promotion review."
    )
    parser.add_argument("--date", dest="target_date", default=date.today().isoformat())
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--candidate-family", required=True)
    parser.add_argument("--bull-mode", required=True)
    parser.add_argument("--selected-run-dir", required=True)
    parser.add_argument("--benchmark-report")
    parser.add_argument("--ai-review-provider")
    args = parser.parse_args(argv)
    report = write_tier2_review_report(
        target_date=args.target_date,
        run_id=args.run_id,
        selected_candidate_family=args.candidate_family,
        selected_bull_mode=args.bull_mode,
        selected_run_dir=args.selected_run_dir,
        candidate_metrics={},
        incumbent_metrics={},
        promotion_gate={},
        benchmark_report_paths=(
            {"json": args.benchmark_report} if args.benchmark_report else {}
        ),
        ai_review_provider=args.ai_review_provider,
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "decision": report["decision"],
                "approved": report["approved"],
            }
        )
    )
    return 0 if report.get("approved") else 2


if __name__ == "__main__":
    raise SystemExit(main())
