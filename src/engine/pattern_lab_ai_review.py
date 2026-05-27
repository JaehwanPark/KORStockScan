"""Build a source-only two-pass AI review for pattern lab feedback."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from src.engine.daily_threshold_cycle_report import REPORT_DIR
from src.utils.constants import TRADING_RULES


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT_TYPE = "pattern_lab_ai_review"
REPORT_SCHEMA_VERSION = 1
AI_REVIEW_SCHEMA_NAME = "pattern_lab_ai_review_v1"
AI_REVIEW_MODEL = str(getattr(TRADING_RULES, "GPT_DEEP_MODEL", "gpt-5.4") or "gpt-5.4")
AI_REVIEW_DEFAULT_PROVIDER = "openai"
REPORT_DIRNAME = REPORT_TYPE
FORBIDDEN_USES = [
    "threshold mutation",
    "order guard mutation",
    "provider change",
    "bot restart",
    "broker order submit",
    "runtime env apply",
    "real order enable",
]
FINAL_STATES = {
    "source_only_keep_collecting",
    "automation_handoff_gap",
    "source_quality_gap",
    "ai_review_gap",
    "code_patch_required",
}
FINAL_DECISIONS = {"keep", "surface_workorder", "block_runtime_use"}
GAP_STATES = {"automation_handoff_gap", "source_quality_gap", "ai_review_gap", "code_patch_required"}


def report_paths(target_date: str) -> tuple[Path, Path]:
    base = REPORT_DIR / REPORT_DIRNAME / f"{REPORT_TYPE}_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _text_hash(payload: Any) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except Exception:
        return default


def _slug(value: Any, *, max_len: int = 80) -> str:
    text = re.sub(r"[^a-zA-Z0-9가-힣]+", "_", str(value or "").strip().lower()).strip("_")
    return text[:max_len] or "unknown"


def _source_rel(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _source_paths(target_date: str) -> dict[str, Path]:
    return {
        "scalping_pattern_lab_automation": REPORT_DIR
        / "scalping_pattern_lab_automation"
        / f"scalping_pattern_lab_automation_{target_date}.json",
        "swing_pattern_lab_automation": REPORT_DIR
        / "swing_pattern_lab_automation"
        / f"swing_pattern_lab_automation_{target_date}.json",
        "pattern_lab_currentness_audit": REPORT_DIR
        / "pattern_lab_currentness_audit"
        / f"pattern_lab_currentness_audit_{target_date}.json",
        "threshold_cycle_ev": REPORT_DIR / "threshold_cycle_ev" / f"threshold_cycle_ev_{target_date}.json",
        "code_improvement_workorder": REPORT_DIR
        / "code_improvement_workorder"
        / f"code_improvement_workorder_{target_date}.json",
        "lifecycle_decision_matrix": REPORT_DIR
        / "lifecycle_decision_matrix"
        / f"lifecycle_decision_matrix_{target_date}.json",
        "lifecycle_bucket_discovery": REPORT_DIR
        / "lifecycle_bucket_discovery"
        / f"lifecycle_bucket_discovery_{target_date}.json",
        "swing_lifecycle_decision_matrix": REPORT_DIR
        / "swing_lifecycle_decision_matrix"
        / f"swing_lifecycle_decision_matrix_{target_date}.json",
        "swing_lifecycle_bucket_discovery": REPORT_DIR
        / "swing_lifecycle_bucket_discovery"
        / f"swing_lifecycle_bucket_discovery_{target_date}.json",
        "swing_strategy_discovery_ev": REPORT_DIR
        / "swing_strategy_discovery_ev"
        / f"swing_strategy_discovery_ev_{target_date}.json",
    }


def _top_list(value: Any, limit: int = 5) -> list[Any]:
    return list(value[:limit]) if isinstance(value, list) else []


def _summary_for(payload: dict[str, Any]) -> dict[str, Any]:
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    ev_summary = payload.get("ev_report_summary") if isinstance(payload.get("ev_report_summary"), dict) else {}
    data_quality = payload.get("data_quality") if isinstance(payload.get("data_quality"), dict) else {}
    return {
        "status": payload.get("status") or summary.get("status"),
        "runtime_effect": payload.get("runtime_effect"),
        "allowed_runtime_apply": payload.get("allowed_runtime_apply"),
        "decision_authority": payload.get("decision_authority"),
        "summary": summary,
        "ev_report_summary": ev_summary,
        "source_quality_contracts": (
            ev_summary.get("source_quality_contracts")
            if isinstance(ev_summary.get("source_quality_contracts"), dict)
            else data_quality.get("source_quality_contracts")
            if isinstance(data_quality.get("source_quality_contracts"), dict)
            else {}
        ),
        "warnings": _top_list(payload.get("warnings"), 10),
    }


def _swing_micro_context_source_contract(context: dict[str, Any]) -> dict[str, Any]:
    sources = context.get("sources") if isinstance(context.get("sources"), dict) else {}
    swing = sources.get("swing_pattern_lab_automation") if isinstance(sources.get("swing_pattern_lab_automation"), dict) else {}
    summary = swing.get("summary") if isinstance(swing.get("summary"), dict) else {}
    contracts = summary.get("source_quality_contracts") if isinstance(summary.get("source_quality_contracts"), dict) else {}
    contract = contracts.get("swing_micro_context") if isinstance(contracts.get("swing_micro_context"), dict) else {}
    return contract


def _is_resolved_swing_micro_context_gap(item: dict[str, Any], context: dict[str, Any]) -> bool:
    if str(item.get("final_state") or "") != "source_quality_gap":
        return False
    review_id = str(item.get("review_id") or "").lower()
    reason = str(item.get("reason") or "").lower()
    if not any(token in f"{review_id} {reason}" for token in ("micro_context", "micro context", "ofi_qi")):
        return False
    contract = _swing_micro_context_source_contract(context)
    return (
        contract.get("source_contract_status") == "implemented"
        and contract.get("runtime_effect") is False
        and contract.get("allowed_runtime_apply") is False
        and contract.get("decision_authority") == "swing_pattern_lab_analysis_workorder_source_only"
    )


def _apply_source_contract_resolutions(payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    conclusions = payload.get("final_conclusions") if isinstance(payload.get("final_conclusions"), list) else []
    resolved_ids: list[str] = []
    resolved_conclusions: list[dict[str, Any]] = []
    for item in conclusions:
        if not isinstance(item, dict):
            continue
        if _is_resolved_swing_micro_context_gap(item, context):
            resolved_ids.append(str(item.get("review_id") or "unknown"))
            resolved_conclusions.append(
                {
                    **item,
                    "final_state": "source_only_keep_collecting",
                    "final_decision": "keep",
                    "explicit_gap_type": None,
                    "auditor_pass": True,
                    "source_contract_resolution": {
                        "status": "resolved_by_implemented_source_contract",
                        "contract_id": "swing_micro_context_source_quality",
                        "runtime_effect": False,
                        "allowed_runtime_apply": False,
                    },
                }
            )
        else:
            resolved_conclusions.append(item)
    if not resolved_ids:
        return payload
    audit = payload.get("audit") if isinstance(payload.get("audit"), dict) else {}
    remaining_gap = any(
        isinstance(item, dict)
        and str(item.get("final_state") or "") in GAP_STATES
        and str(item.get("final_decision") or "") != "keep"
        for item in resolved_conclusions
    )
    payload = {**payload, "final_conclusions": resolved_conclusions}
    payload["audit"] = {
        **audit,
        "status": "correction_required" if remaining_gap else "pass",
        "source_contract_resolutions": resolved_ids,
        "issues": audit.get("issues") if remaining_gap else [],
        "reason": (
            audit.get("reason")
            if remaining_gap
            else "Source-only review gaps were resolved by implemented source contracts; runtime authority remains false."
        ),
    }
    return payload


def _build_input_context(target_date: str) -> dict[str, Any]:
    paths = _source_paths(target_date)
    payloads = {label: _load_json(path) for label, path in paths.items()}
    currentness = payloads["pattern_lab_currentness_audit"]
    currentness_checks = [
        {
            "check_id": item.get("check_id"),
            "status": item.get("status"),
            "severity": item.get("severity"),
            "finding": item.get("finding"),
        }
        for item in currentness.get("checks", [])
        if isinstance(item, dict)
    ][:20]
    workorder = payloads["code_improvement_workorder"]
    workorder_orders = [
        {
            "order_id": item.get("order_id"),
            "title": item.get("title"),
            "source_report_type": item.get("source_report_type"),
            "decision": item.get("decision"),
        }
        for item in workorder.get("orders", [])
        if isinstance(item, dict)
        and str(item.get("source_report_type") or "").startswith("pattern_lab")
    ][:20]
    sources = {
        label: {
            "path": str(path) if path.exists() else None,
            "exists": path.exists(),
            "summary": _summary_for(payloads[label]),
        }
        for label, path in paths.items()
    }
    return {
        "date": target_date,
        "review_authority": "pattern_lab_ai_review_source_only",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "forbidden_uses": FORBIDDEN_USES,
        "sources": sources,
        "currentness_checks": currentness_checks,
        "pattern_lab_workorder_orders": workorder_orders,
    }


def _state_for_check(check: dict[str, Any]) -> str:
    severity = str(check.get("severity") or "")
    if severity == "automation_handoff_gap":
        return "automation_handoff_gap"
    if severity == "ai_review_gap":
        return "ai_review_gap"
    if severity == "source_quality_blocker":
        return "source_quality_gap"
    if str(check.get("status") or "") == "fail":
        return "code_patch_required"
    return "source_only_keep_collecting"


def _domain_for_check(check_id: str) -> str:
    if "swing" in check_id or "deepseek" in check_id:
        return "swing"
    if "scalping" in check_id or "gemini" in check_id or "claude" in check_id:
        return "scalping"
    return "cross_domain"


def _explicit_gap_type(final_state: str) -> str | None:
    if final_state == "automation_handoff_gap":
        return "automation_handoff_gap"
    if final_state == "source_quality_gap":
        return "source_quality_gap"
    if final_state == "ai_review_gap":
        return "ai_review_gap"
    if final_state == "code_patch_required":
        return "code_patch_required"
    return None


def _source_path_labels_for_domain(context: dict[str, Any], domain: str) -> list[str]:
    sources = context.get("sources") if isinstance(context.get("sources"), dict) else {}
    if domain == "scalping":
        labels = [
            "scalping_pattern_lab_automation",
            "pattern_lab_currentness_audit",
            "threshold_cycle_ev",
            "lifecycle_decision_matrix",
            "lifecycle_bucket_discovery",
        ]
    elif domain == "swing":
        labels = [
            "swing_pattern_lab_automation",
            "pattern_lab_currentness_audit",
            "threshold_cycle_ev",
            "swing_lifecycle_decision_matrix",
            "swing_lifecycle_bucket_discovery",
            "swing_strategy_discovery_ev",
        ]
    else:
        labels = list(sources)
    result: list[str] = []
    for label in labels:
        source = sources.get(label) if isinstance(sources.get(label), dict) else {}
        path = source.get("path")
        if path:
            result.append(str(path))
    return result[:12]


def _normalize_final_conclusion(item: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    final_state = str(item.get("final_state") or "source_only_keep_collecting")
    if final_state not in FINAL_STATES:
        final_state = "code_patch_required"
    final_decision = str(item.get("final_decision") or "")
    if final_decision not in FINAL_DECISIONS:
        final_decision = "surface_workorder" if final_state in GAP_STATES else "keep"
    domain = str(item.get("domain") or "cross_domain")
    auditor_pass = item.get("auditor_pass")
    if auditor_pass is None:
        auditor_pass = final_decision != "block_runtime_use" and final_state not in {"ai_review_gap"}
    explicit_gap_type = item.get("explicit_gap_type") or _explicit_gap_type(final_state)
    source_paths = item.get("source_paths") if isinstance(item.get("source_paths"), list) else []
    if not source_paths:
        source_paths = _source_path_labels_for_domain(context, domain)
    return {
        **item,
        "review_id": str(item.get("review_id") or "unknown"),
        "domain": domain,
        "final_state": final_state,
        "final_decision": final_decision,
        "auditor_pass": bool(auditor_pass),
        "explicit_gap_type": explicit_gap_type,
        "source_paths": [str(path) for path in source_paths][:12],
        "forbidden_runtime_uses": FORBIDDEN_USES,
    }


def _deterministic_two_pass_review(context: dict[str, Any]) -> dict[str, Any]:
    checks = [
        item
        for item in context.get("currentness_checks", [])
        if isinstance(item, dict) and str(item.get("status") or "") == "fail"
    ]
    review_items: list[dict[str, Any]] = []
    for check in checks[:20]:
        check_id = str(check.get("check_id") or "unknown")
        state = _state_for_check(check)
        review_items.append(
            {
                "review_id": f"currentness:{check_id}",
                "domain": _domain_for_check(check_id),
                "interpreted_state": state,
                "confidence": "high" if state in {"automation_handoff_gap", "ai_review_gap"} else "medium",
                "reason": str(check.get("finding") or "currentness audit surfaced a source-quality gap")[:240],
            }
        )
    if not review_items:
        review_items.append(
            {
                "review_id": "pattern_lab_feedback_loop:keep_collecting",
                "domain": "cross_domain",
                "interpreted_state": "source_only_keep_collecting",
                "confidence": "medium",
                "reason": "No currentness failure was present; preserve pattern lab output as source-only feedback.",
            }
        )
    forbidden_violations: list[str] = []
    for source in (context.get("sources") or {}).values():
        if not isinstance(source, dict):
            continue
        summary = source.get("summary") if isinstance(source.get("summary"), dict) else {}
        if summary.get("runtime_effect") is True or summary.get("allowed_runtime_apply") is True:
            forbidden_violations.append(str(source.get("path") or "unknown"))
    audit_status = "correction_required" if forbidden_violations else "pass"
    issue_counts = Counter(str(item.get("interpreted_state") or "") for item in review_items)
    audit_issues = [
        f"{state}:{count}"
        for state, count in sorted(issue_counts.items())
        if state in GAP_STATES and count > 0
    ]
    final_conclusions = [
        _normalize_final_conclusion(
            {
            "review_id": item["review_id"],
            "domain": item["domain"],
            "final_state": item["interpreted_state"],
            "final_decision": (
                "block_runtime_use"
                if forbidden_violations
                else "surface_workorder"
                if item["interpreted_state"] in GAP_STATES
                else "keep"
            ),
            "reason": item["reason"],
            "required_followup": (
                ["preserve_runtime_effect_false", "surface_code_improvement_workorder"]
                if item["interpreted_state"] in GAP_STATES
                else ["keep_collecting"]
            ),
            },
            context,
        )
        for item in review_items
    ]
    return {
        "schema_version": 1,
        "interpretation": {
            "review_items": review_items,
            "source_feedback_status": "warning" if audit_issues else "pass",
        },
        "audit": {
            "status": audit_status,
            "issues": audit_issues,
            "forbidden_use_violations": forbidden_violations,
            "reason": (
                "Audit found forbidden runtime authority in source-only pattern lab flow."
                if forbidden_violations
                else "Second-pass audit preserved source-only authority and surfaced explicit gaps only."
            ),
        },
        "final_conclusions": final_conclusions,
    }


def _build_ai_review_instructions() -> str:
    return (
        "You are the Pattern Lab source-only AI reviewer.\n"
        "Use a mandatory two-pass process: first interpretation, then audit, then final conclusions.\n"
        "Your output is report/workorder source only. Never propose threshold mutation, broker order submit, "
        "provider change, bot restart, runtime env apply, real order enable, cap release, or safety guard bypass.\n"
        "Treat pattern labs as analysis and source-quality workorder inputs. They cannot replace LDM, bucket "
        "discovery, runtime bridge, approval contracts, or deterministic guards.\n"
        "If LDM/threshold feedback is missing from pattern lab inputs, classify it as automation_handoff_gap.\n"
        "If the reviewer contract itself is missing or incomplete, classify it as ai_review_gap.\n"
        "Ambiguity alone must not block sim-only collection; only explicit source-quality, schema, handoff, "
        "forbidden-use, or instrumentation gaps should surface workorders.\n"
        "Return only JSON conforming to pattern_lab_ai_review_v1."
    )


def _call_openai_ai_review(context: dict[str, Any]) -> tuple[Any | None, dict[str, Any]]:
    try:
        from openai import OpenAI, RateLimitError
        from src.engine.ai_response_contracts import build_openai_response_text_format
        from src.engine.daily_threshold_cycle_report import (
            _extract_openai_response_text,
            _load_threshold_ai_openai_keys,
        )
    except Exception as exc:
        return None, {"provider": "openai", "status": "unavailable", "reason": f"openai import failed: {exc}"}

    api_keys = _load_threshold_ai_openai_keys()
    if not api_keys:
        return None, {"provider": "openai", "status": "unavailable", "reason": "OPENAI_API_KEY not configured"}

    prompt = json.dumps(context, ensure_ascii=False, indent=2, default=str)
    errors: list[dict[str, str]] = []
    for attempt_index, (key_name, api_key) in enumerate(api_keys, start=1):
        try:
            client = OpenAI(api_key=api_key)
            response = client.responses.create(
                model=AI_REVIEW_MODEL,
                instructions=_build_ai_review_instructions(),
                input=prompt,
                text={
                    "format": build_openai_response_text_format(AI_REVIEW_SCHEMA_NAME),
                    "verbosity": "low",
                },
                reasoning={"effort": "high"},
                store=False,
                metadata={
                    "endpoint_name": "pattern_lab_ai_review",
                    "schema_name": AI_REVIEW_SCHEMA_NAME,
                    "report_type": REPORT_TYPE,
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
                "model": AI_REVIEW_MODEL,
                "schema_name": AI_REVIEW_SCHEMA_NAME,
                "reasoning_effort": "high",
                "input_context_hash": _text_hash(context),
                "input_context_chars": len(prompt),
                "output_chars": len(raw_text),
                "input_tokens": int(getattr(usage, "input_tokens", 0) or 0) if usage else 0,
                "output_tokens": int(getattr(usage, "output_tokens", 0) or 0) if usage else 0,
                "total_tokens": int(getattr(usage, "total_tokens", 0) or 0) if usage else 0,
            }
        except RateLimitError as exc:
            errors.append({"key_name": key_name, "error": f"rate_limit:{exc}"})
        except Exception as exc:
            errors.append({"key_name": key_name, "error": str(exc)})
    return None, {
        "provider": "openai",
        "status": "unavailable",
        "reason": "all OpenAI attempts failed",
        "model": AI_REVIEW_MODEL,
        "errors": errors[-3:],
    }


def _parse_ai_review_response(raw_response: Any | None) -> tuple[str, dict[str, Any], list[str]]:
    if raw_response in (None, ""):
        return "missing", {}, ["ai_review_response_missing"]
    if isinstance(raw_response, dict):
        payload = raw_response
    else:
        try:
            payload = json.loads(str(raw_response))
        except Exception as exc:
            return "parse_rejected", {}, [f"ai_review_json_parse_failed:{exc}"]
    warnings: list[str] = []
    if payload.get("schema_version") != 1:
        warnings.append("ai_review_schema_version_invalid")
    interpretation = payload.get("interpretation") if isinstance(payload.get("interpretation"), dict) else {}
    audit = payload.get("audit") if isinstance(payload.get("audit"), dict) else {}
    conclusions = payload.get("final_conclusions") if isinstance(payload.get("final_conclusions"), list) else []
    if not isinstance(interpretation.get("review_items"), list):
        warnings.append("ai_review_interpretation_missing_review_items")
    if str(audit.get("status") or "") not in {"pass", "correction_required", "insufficient_context"}:
        warnings.append("ai_review_audit_status_invalid")
    if not isinstance(audit.get("forbidden_use_violations"), list):
        warnings.append("ai_review_audit_forbidden_uses_missing")
    for item in conclusions:
        if not isinstance(item, dict):
            warnings.append("ai_review_final_conclusion_non_dict")
            continue
        if str(item.get("final_state") or "") not in FINAL_STATES:
            warnings.append(f"ai_review_invalid_final_state:{item.get('review_id')}")
        if str(item.get("final_decision") or "") not in FINAL_DECISIONS:
            warnings.append(f"ai_review_invalid_final_decision:{item.get('review_id')}")
    if warnings:
        return "parse_rejected", payload, warnings
    return "parsed", payload, []


def _order_from_conclusion(conclusion: dict[str, Any]) -> dict[str, Any]:
    review_id = str(conclusion.get("review_id") or "unknown")
    final_state = str(conclusion.get("final_state") or "code_patch_required")
    return {
        "order_id": f"order_{REPORT_TYPE}_{_slug(review_id)}",
        "title": f"Pattern Lab AI review follow-up: {review_id}",
        "source_report_type": REPORT_TYPE,
        "lifecycle_stage": "pattern_lab_ai_review",
        "target_subsystem": "pattern_lab",
        "priority": 10,
        "route": "implement_now",
        "confidence": "ai_two_pass_review" if conclusion.get("final_decision") != "keep" else "source_only",
        "intent": str(conclusion.get("reason") or "Pattern lab AI review surfaced a source-only follow-up."),
        "expected_ev_effect": "Improve pattern lab feedback quality without runtime mutation.",
        "evidence": [
            f"review_id={review_id}",
            f"domain={conclusion.get('domain')}",
            f"final_state={final_state}",
            f"final_decision={conclusion.get('final_decision')}",
            f"auditor_pass={conclusion.get('auditor_pass')}",
            f"explicit_gap_type={conclusion.get('explicit_gap_type')}",
            f"source_paths={conclusion.get('source_paths') or []}",
        ],
        "files_likely_touched": [
            "src/engine/pattern_lab_ai_review.py",
            "src/engine/pattern_lab_currentness_audit.py",
            "analysis/gemini_scalping_pattern_lab",
            "analysis/claude_scalping_pattern_lab",
            "analysis/deepseek_swing_pattern_lab",
        ],
        "acceptance_tests": [
            "PYTHONPATH=. .venv/bin/pytest -q src/tests/test_pattern_lab_ai_review.py src/tests/test_pattern_lab_currentness_audit.py",
        ],
        "improvement_type": final_state,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "strategy_effect": False,
        "data_quality_effect": True,
        "tuning_axis_effect": False,
        "next_postclose_metric": f"{REPORT_TYPE}.{review_id}",
        "forbidden_uses": FORBIDDEN_USES,
    }


def build_pattern_lab_ai_review_report(
    target_date: str,
    *,
    provider: str | None = None,
    ai_raw_response: Any | None = None,
) -> dict[str, Any]:
    target_date = str(target_date).strip()
    resolved_provider = str(
        provider if provider is not None else os.getenv("KORSTOCKSCAN_PATTERN_LAB_AI_REVIEW_PROVIDER", AI_REVIEW_DEFAULT_PROVIDER)
    ).strip().lower() or "none"
    context = _build_input_context(target_date)
    provider_status: dict[str, Any] = {
        "provider": resolved_provider,
        "status": "disabled" if resolved_provider in {"none", "off", "false", "0"} else "not_called",
        "model": AI_REVIEW_MODEL if resolved_provider not in {"none", "off", "false", "0"} else None,
        "schema_name": AI_REVIEW_SCHEMA_NAME,
        "input_context_hash": _text_hash(context),
    }
    raw_response = ai_raw_response
    if raw_response is None and resolved_provider == "openai":
        raw_response, provider_status = _call_openai_ai_review(context)
    ai_status, ai_payload, ai_warnings = _parse_ai_review_response(raw_response)
    fallback_used = False
    if ai_status != "parsed":
        fallback_used = True
        ai_payload = _deterministic_two_pass_review(context)
        if resolved_provider in {"none", "off", "false", "0"}:
            ai_status = "disabled_deterministic_review"
        else:
            ai_status = "unavailable_deterministic_review"
    ai_payload = _apply_source_contract_resolutions(ai_payload, context)
    conclusions = (
        ai_payload.get("final_conclusions")
        if isinstance(ai_payload.get("final_conclusions"), list)
        else []
    )
    conclusions = [
        _normalize_final_conclusion(item, context)
        for item in conclusions
        if isinstance(item, dict)
    ]
    ai_payload["final_conclusions"] = conclusions
    orders = [
        _order_from_conclusion(item)
        for item in conclusions
        if isinstance(item, dict)
        and str(item.get("final_state") or "") in GAP_STATES
        and str(item.get("final_decision") or "") != "keep"
    ]
    audit = ai_payload.get("audit") if isinstance(ai_payload.get("audit"), dict) else {}
    state_counts = Counter(str(item.get("final_state") or "unknown") for item in conclusions if isinstance(item, dict))
    ai_status_ok = ai_status in {"parsed", "disabled_deterministic_review"}
    status = "warning" if orders or not ai_status_ok or audit.get("status") != "pass" else "pass"
    source_paths = _source_paths(target_date)
    report = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "report_type": REPORT_TYPE,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "runtime_mutation_allowed": False,
        "decision_authority": "pattern_lab_ai_review_source_only",
        "metric_role": "source_quality_gate",
        "window_policy": "same_day_postclose_pattern_lab_feedback_review",
        "sample_floor": "report_only_no_hard_decision",
        "primary_decision_metric": "source_quality_adjusted_ev_pct",
        "source_quality_gate": "pattern_lab_currentness + LDM/threshold feedback re-entry contract",
        "forbidden_uses": FORBIDDEN_USES,
        "status": status,
        "sources": {
            label: str(path) if path.exists() else None
            for label, path in source_paths.items()
        },
        "source_context_hash": _text_hash(context),
        "summary": {
            "status": status,
            "ai_two_pass_review_status": ai_status,
            "provider": resolved_provider,
            "model": provider_status.get("model") or (AI_REVIEW_MODEL if resolved_provider == "openai" else None),
            "fallback_used": fallback_used,
            "audit_status": audit.get("status"),
            "final_conclusion_count": len(conclusions),
            "workorder_count": len(orders),
            "state_counts": dict(state_counts),
            "human_intervention_required": False,
        },
        "ai_two_pass_review": {
            "provider": resolved_provider,
            "status": ai_status,
            "model": provider_status.get("model") or (AI_REVIEW_MODEL if resolved_provider == "openai" else None),
            "model_tier": "tier3" if resolved_provider == "openai" else "deterministic_fallback",
            "schema_name": AI_REVIEW_SCHEMA_NAME,
            "provider_status": provider_status,
            "input_context_hash": _text_hash(context),
            "interpretation": ai_payload.get("interpretation") if isinstance(ai_payload.get("interpretation"), dict) else {},
            "audit": audit,
            "final_conclusions": conclusions,
            "warnings": ai_warnings,
        },
        "code_improvement_orders": orders,
    }
    json_path, md_path = report_paths(target_date)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return report


def render_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    review = report.get("ai_two_pass_review") if isinstance(report.get("ai_two_pass_review"), dict) else {}
    audit = review.get("audit") if isinstance(review.get("audit"), dict) else {}
    lines = [
        f"# Pattern Lab AI Review - {report.get('date')}",
        "",
        "## Summary",
        "",
        f"- status: `{report.get('status')}`",
        f"- runtime_effect: `{report.get('runtime_effect')}`",
        f"- allowed_runtime_apply: `{report.get('allowed_runtime_apply')}`",
        f"- decision_authority: `{report.get('decision_authority')}`",
        f"- ai_two_pass_review_status: `{summary.get('ai_two_pass_review_status')}`",
        f"- provider: `{summary.get('provider')}`",
        f"- model: `{summary.get('model') or '-'}`",
        f"- fallback_used: `{summary.get('fallback_used')}`",
        f"- audit_status: `{summary.get('audit_status')}`",
        f"- final_conclusion_count: `{summary.get('final_conclusion_count')}`",
        f"- workorder_count: `{summary.get('workorder_count')}`",
        "",
        "## Two-Pass Review",
        "",
        f"- interpretation_count: `{len(((review.get('interpretation') or {}).get('review_items') or []) if isinstance(review.get('interpretation'), dict) else [])}`",
        f"- audit_issues: `{audit.get('issues') or []}`",
        f"- forbidden_use_violations: `{audit.get('forbidden_use_violations') or []}`",
        "",
        "## Final Conclusions",
        "",
    ]
    for item in (review.get("final_conclusions") or [])[:20]:
        if not isinstance(item, dict):
            continue
        lines.append(
            f"- `{item.get('review_id')}` domain=`{item.get('domain')}` "
            f"state=`{item.get('final_state')}` decision=`{item.get('final_decision')}` "
            f"reason=`{item.get('reason')}`"
        )
    lines.extend(["", "## Code Improvement Orders", ""])
    for order in report.get("code_improvement_orders") or []:
        if isinstance(order, dict):
            lines.append(f"- `{order.get('order_id')}`: {order.get('title')}")
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument(
        "--provider",
        default=os.getenv("KORSTOCKSCAN_PATTERN_LAB_AI_REVIEW_PROVIDER", AI_REVIEW_DEFAULT_PROVIDER),
        choices=["openai", "none", "off", "false", "0"],
    )
    args = parser.parse_args(argv)
    report = build_pattern_lab_ai_review_report(args.date, provider=args.provider)
    json_path, md_path = report_paths(args.date)
    print(json.dumps({"status": report.get("status"), "json": str(json_path), "md": str(md_path)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
