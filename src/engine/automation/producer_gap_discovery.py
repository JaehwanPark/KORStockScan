"""Discover missing source-only producer candidates from sim/probe lifecycle results."""

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
REPORT_TYPE = "producer_gap_discovery"
REPORT_SCHEMA_VERSION = 1
DISCOVERY_VERSION = "producer_gap_discovery_v1"
AI_REVIEW_SCHEMA_NAME = "producer_gap_discovery_ai_review_v1"
AI_REVIEWER_NAME = "producer_gap_discovery_ai_review"
AI_REVIEW_MODEL = str(getattr(TRADING_RULES, "GPT_DEEP_MODEL", "gpt-5.4") or "gpt-5.4")
AI_REVIEW_DEFAULT_PROVIDER = "openai"
POST_SELL_DIR = PROJECT_ROOT / "data" / "post_sell"

FORBIDDEN_USES = [
    "real order enablement",
    "threshold mutation",
    "provider change",
    "bot restart",
    "position cap release",
    "entry decision override",
    "exit decision override",
    "broker order submit",
]
PATTERN_TYPES = {
    "stop_recovery_counterfactual_missing",
    "missed_fill_recovery_counterfactual_missing",
    "swing_sim_probe_label_gap_missing",
    "scale_in_counterfactual_gap_missing",
}
PRIORITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def report_paths(target_date: str) -> tuple[Path, Path]:
    base = REPORT_DIR / REPORT_TYPE / f"{REPORT_TYPE}_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _load_jsonl(path: Path, *, limit: int = 20000) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return rows
    for line in lines[-limit:]:
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except Exception:
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except Exception:
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return default
        return int(float(value))
    except Exception:
        return default


def _slug(value: Any, *, max_len: int = 80) -> str:
    text = re.sub(r"[^a-zA-Z0-9가-힣]+", "_", str(value or "").strip().lower()).strip("_")
    return text[:max_len] or "unknown"


def _text_hash(payload: Any) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _source_paths(target_date: str) -> dict[str, Path]:
    return {
        "sim_post_sell_evaluations": POST_SELL_DIR / f"sim_post_sell_evaluations_{target_date}.jsonl",
        "lifecycle_decision_matrix": REPORT_DIR
        / "lifecycle_decision_matrix"
        / f"lifecycle_decision_matrix_{target_date}.json",
        "lifecycle_bucket_discovery": REPORT_DIR
        / "lifecycle_bucket_discovery"
        / f"lifecycle_bucket_discovery_{target_date}.json",
        "swing_strategy_discovery_ev": REPORT_DIR
        / "swing_strategy_discovery_ev"
        / f"swing_strategy_discovery_ev_{target_date}.json",
        "swing_lifecycle_decision_matrix": REPORT_DIR
        / "swing_lifecycle_decision_matrix"
        / f"swing_lifecycle_decision_matrix_{target_date}.json",
        "swing_lifecycle_bucket_discovery": REPORT_DIR
        / "swing_lifecycle_bucket_discovery"
        / f"swing_lifecycle_bucket_discovery_{target_date}.json",
        "swing_lifecycle_audit": REPORT_DIR / "swing_lifecycle_audit" / f"swing_lifecycle_audit_{target_date}.json",
    }


def _iter_nested(value: Any) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    if isinstance(value, dict):
        found.append(value)
        for child in value.values():
            found.extend(_iter_nested(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(_iter_nested(child))
    return found


def _candidate(
    *,
    candidate_id: str,
    domain: str,
    pattern_type: str,
    lifecycle_stage: str,
    priority: str,
    evidence: list[str],
    source_paths: list[str],
    sample_count: int,
) -> dict[str, Any]:
    return {
        "candidate_id": candidate_id,
        "domain": domain,
        "pattern_type": pattern_type,
        "lifecycle_stage": lifecycle_stage,
        "priority": priority,
        "producer_gap_state": "missing_producer_candidate",
        "metric_role": "source_quality_gate",
        "decision_authority": "producer_gap_discovery_source_only",
        "window_policy": "same_day_postclose_sim_probe_real_flow_review",
        "sample_floor": 1,
        "primary_decision_metric": "source_quality_adjusted_ev_pct",
        "source_quality_gate": "source artifact exists and contains pattern evidence",
        "forbidden_uses": FORBIDDEN_USES,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "sample_count": sample_count,
        "evidence": evidence[:20],
        "source_paths": source_paths[:12],
        "recommended_producer_contract": {
            "runtime_effect": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "decision_authority": "source_only_producer_gap_observation",
            "required_metric_contract_fields": [
                "metric_role",
                "decision_authority",
                "window_policy",
                "sample_floor",
                "primary_decision_metric",
                "source_quality_gate",
                "forbidden_uses",
            ],
        },
    }


def _detect_stop_recovery(rows: list[dict[str, Any]], source_path: Path) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for row in rows:
        text = json.dumps(row, ensure_ascii=False, default=str).lower()
        exit_reason = str(row.get("exit_reason") or row.get("sell_reason") or row.get("reason") or "").lower()
        profit = _safe_float(row.get("profit_rate") or row.get("profit_pct") or row.get("realized_profit_pct"), 0.0)
        mfe = _safe_float(row.get("mfe_pct") or row.get("max_favorable_excursion_pct") or row.get("post_exit_mfe_pct"), 0.0)
        recovery = _safe_float(row.get("recovery_profit_pct") or row.get("post_stop_recovery_pct"), 0.0)
        if ("hard" in exit_reason and "stop" in exit_reason) or "hard_stop" in text or "soft_stop" in text:
            if profit < 0 or mfe > 0 or recovery > 0:
                matches.append(row)
    if not matches:
        return []
    symbols = sorted({str(row.get("code") or row.get("symbol") or row.get("stock_code") or "unknown") for row in matches})[:8]
    return [
        _candidate(
            candidate_id="producer_gap_stop_recovery_counterfactual_missing",
            domain="scalping",
            pattern_type="stop_recovery_counterfactual_missing",
            lifecycle_stage="exit",
            priority="high",
            sample_count=len(matches),
            source_paths=[str(source_path)],
            evidence=[
                f"matched_stop_exit_rows={len(matches)}",
                f"symbols={','.join(symbols)}",
                "gap=post-stop recovery is not isolated as a dedicated producer input",
            ],
        )
    ]


def _detect_missed_fill(payloads: dict[str, Any], paths: dict[str, Path]) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for label in ("lifecycle_decision_matrix", "lifecycle_bucket_discovery"):
        for item in _iter_nested(payloads.get(label)):
            text = json.dumps(item, ensure_ascii=False, default=str).lower()
            if any(token in text for token in ("missed_fill", "unfilled", "not_filled", "cancel", "defensive_price", "below_window", "fill_quality")):
                matches.append({"label": label, "item": item})
    if not matches:
        return []
    labels = sorted({row["label"] for row in matches})
    return [
        _candidate(
            candidate_id="producer_gap_missed_fill_recovery_counterfactual_missing",
            domain="scalping",
            pattern_type="missed_fill_recovery_counterfactual_missing",
            lifecycle_stage="submit",
            priority="high",
            sample_count=len(matches),
            source_paths=[str(paths[label]) for label in labels if paths[label].exists()],
            evidence=[
                f"matched_submit_fill_gap_rows={len(matches)}",
                f"source_labels={','.join(labels)}",
                "gap=post-submit missed fill and re-entry/recovery quality lacks a dedicated producer",
            ],
        )
    ]


def _detect_swing_label_gap(payloads: dict[str, Any], paths: dict[str, Path]) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for label in ("swing_strategy_discovery_ev", "swing_lifecycle_decision_matrix", "swing_lifecycle_bucket_discovery", "swing_lifecycle_audit"):
        for item in _iter_nested(payloads.get(label)):
            text = json.dumps(item, ensure_ascii=False, default=str).lower()
            if any(token in text for token in ("label_missing", "missing_label", "pending_label", "insufficient_label", "source_quality", "handoff_missing")):
                matches.append({"label": label, "item": item})
    if not matches:
        return []
    labels = sorted({row["label"] for row in matches})
    return [
        _candidate(
            candidate_id="producer_gap_swing_sim_probe_label_gap_missing",
            domain="swing",
            pattern_type="swing_sim_probe_label_gap_missing",
            lifecycle_stage="selection",
            priority="high",
            sample_count=len(matches),
            source_paths=[str(paths[label]) for label in labels if paths[label].exists()],
            evidence=[
                f"matched_swing_label_or_source_gap_rows={len(matches)}",
                f"source_labels={','.join(labels)}",
                "gap=swing sim/probe label and EV handoff defects need a dedicated source producer",
            ],
        )
    ]


def _detect_scale_in_gap(payloads: dict[str, Any], paths: dict[str, Path]) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for label in ("lifecycle_decision_matrix", "swing_lifecycle_decision_matrix", "swing_lifecycle_bucket_discovery"):
        for item in _iter_nested(payloads.get(label)):
            text = json.dumps(item, ensure_ascii=False, default=str).lower()
            if "scale_in" in text or "avg_down" in text or "pyramid" in text:
                if any(token in text for token in ("blocked", "missing", "would", "counterfactual", "mfe", "mae", "price_guard", "qty_reason")):
                    matches.append({"label": label, "item": item})
    if not matches:
        return []
    labels = sorted({row["label"] for row in matches})
    return [
        _candidate(
            candidate_id="producer_gap_scale_in_counterfactual_gap_missing",
            domain="cross_domain",
            pattern_type="scale_in_counterfactual_gap_missing",
            lifecycle_stage="scale_in",
            priority="high",
            sample_count=len(matches),
            source_paths=[str(paths[label]) for label in labels if paths[label].exists()],
            evidence=[
                f"matched_scale_in_gap_rows={len(matches)}",
                f"source_labels={','.join(labels)}",
                "gap=scale-in blocked/fill/unfill outcome comparison lacks a dedicated source producer",
            ],
        )
    ]


def _deterministic_candidates(target_date: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    paths = _source_paths(target_date)
    payloads = {label: _load_json(path) for label, path in paths.items() if label != "sim_post_sell_evaluations"}
    sim_rows = _load_jsonl(paths["sim_post_sell_evaluations"])
    candidates: list[dict[str, Any]] = []
    candidates.extend(_detect_stop_recovery(sim_rows, paths["sim_post_sell_evaluations"]))
    candidates.extend(_detect_missed_fill(payloads, paths))
    candidates.extend(_detect_swing_label_gap(payloads, paths))
    candidates.extend(_detect_scale_in_gap(payloads, paths))
    context = {
        "date": target_date,
        "report_type": REPORT_TYPE,
        "discovery_version": DISCOVERY_VERSION,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "forbidden_uses": FORBIDDEN_USES,
        "sources": {
            label: {
                "path": str(path) if path.exists() else None,
                "exists": path.exists(),
                "row_count": len(sim_rows) if label == "sim_post_sell_evaluations" else None,
            }
            for label, path in paths.items()
        },
        "producer_gap_candidates": candidates,
    }
    return candidates, context


def _build_ai_review_instructions() -> str:
    return (
        "You are producer_gap_discovery_ai_review, a source-only missing producer reviewer.\n"
        "Use a mandatory two-pass process: first interpretation, then audit, then final conclusions.\n"
        "Review deterministic missing producer candidates for scalping and swing sim/probe/real-flow results.\n"
        "You may adjust priority, recommended route, implementation requirements, and acceptance tests.\n"
        "You must not delete deterministic candidates and must not grant runtime, threshold, provider, bot, cap, "
        "entry, exit, or broker order authority. Any forbidden-use leak must be surfaced in the audit.\n"
        "AI unavailable or parse rejection is fail-closed by the caller, so return strict JSON only.\n"
        "Return only JSON conforming to producer_gap_discovery_ai_review_v1."
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
                text={"format": build_openai_response_text_format(AI_REVIEW_SCHEMA_NAME), "verbosity": "low"},
                reasoning={"effort": "high"},
                store=False,
                metadata={
                    "endpoint_name": AI_REVIEWER_NAME,
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
    if payload.get("reviewer") != AI_REVIEWER_NAME:
        warnings.append("ai_review_reviewer_invalid")
    if not isinstance(payload.get("candidate_reviews"), list):
        warnings.append("ai_review_candidate_reviews_missing")
    audit = payload.get("audit") if isinstance(payload.get("audit"), dict) else {}
    if str(audit.get("status") or "") not in {"pass", "correction_required", "insufficient_context"}:
        warnings.append("ai_review_audit_status_invalid")
    if not isinstance(audit.get("forbidden_use_violations"), list):
        warnings.append("ai_review_forbidden_use_violations_missing")
    if warnings:
        return "parse_rejected", payload, warnings
    return "parsed", payload, []


def _review_by_candidate(ai_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in ai_payload.get("candidate_reviews") or []:
        if isinstance(item, dict) and item.get("candidate_id"):
            result[str(item["candidate_id"])] = item
    return result


def _order_from_candidate(candidate: dict[str, Any], review: dict[str, Any]) -> dict[str, Any]:
    candidate_id = str(candidate.get("candidate_id") or "unknown")
    pattern_type = str(candidate.get("pattern_type") or "producer_gap")
    priority = str(review.get("priority") or candidate.get("priority") or "high")
    return {
        "order_id": f"order_{REPORT_TYPE}_{_slug(candidate_id)}",
        "title": f"Implement missing producer: {pattern_type}",
        "source_report_type": REPORT_TYPE,
        "lifecycle_stage": candidate.get("lifecycle_stage"),
        "target_subsystem": review.get("target_subsystem") or "postclose_source_producer",
        "route": review.get("recommended_route") or "implement_now",
        "priority": PRIORITY_RANK.get(priority, 1) + 1,
        "producer_gap_priority": priority,
        "confidence": review.get("confidence") or "ai_two_pass_review",
        "improvement_type": pattern_type,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "decision_authority": "producer_gap_discovery_workorder_source_only",
        "intent": review.get("reason") or "Add a source-only producer for a missing observation gap.",
        "expected_ev_effect": "Improve source-quality adjusted EV attribution by making the missing producer observable.",
        "evidence": list(candidate.get("evidence") or []) + [f"ai_priority={priority}", f"ai_route={review.get('recommended_route')}"],
        "source_paths": candidate.get("source_paths") or [],
        "files_likely_touched": review.get("files_likely_touched")
        or [
            "src/engine/automation/producer_gap_discovery.py",
            "src/engine/build_code_improvement_workorder.py",
            "src/engine/verify_threshold_cycle_postclose_chain.py",
        ],
        "acceptance_tests": review.get("acceptance_tests")
        or [
            "PYTHONPATH=. .venv/bin/pytest -q src/tests/test_producer_gap_discovery.py src/tests/test_build_code_improvement_workorder.py",
            "runtime_effect remains false and broker/order/provider/bot/threshold authority is forbidden",
        ],
        "next_postclose_metric": f"{REPORT_TYPE}.{candidate_id}",
        "forbidden_uses": FORBIDDEN_USES,
        "implementation_requirements": review.get("implementation_requirements") or [],
    }


def build_producer_gap_discovery_report(
    target_date: str,
    *,
    provider: str | None = None,
    ai_raw_response: Any | None = None,
) -> dict[str, Any]:
    target_date = str(target_date).strip()
    resolved_provider = str(
        provider
        if provider is not None
        else os.getenv("KORSTOCKSCAN_PRODUCER_GAP_DISCOVERY_AI_PROVIDER", AI_REVIEW_DEFAULT_PROVIDER)
    ).strip().lower() or "none"
    candidates, context = _deterministic_candidates(target_date)
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
    audit = ai_payload.get("audit") if isinstance(ai_payload.get("audit"), dict) else {}
    fail_closed = ai_status != "parsed" or audit.get("status") != "pass"
    review_map = _review_by_candidate(ai_payload) if ai_status == "parsed" else {}
    reviewed_candidates = []
    orders = []
    for candidate in candidates:
        review = review_map.get(str(candidate.get("candidate_id"))) or {}
        merged = {
            **candidate,
            "ai_review": review,
            "ai_review_status": ai_status,
            "ai_priority": review.get("priority") or candidate.get("priority"),
            "ai_recommended_route": review.get("recommended_route") or "implement_now",
        }
        reviewed_candidates.append(merged)
        priority = str(merged.get("ai_priority") or "high")
        if ai_status == "parsed" and PRIORITY_RANK.get(priority, 99) <= PRIORITY_RANK["high"]:
            orders.append(_order_from_candidate(candidate, review))
    state_counts = Counter(str(item.get("pattern_type") or "unknown") for item in candidates)
    status = "fail" if fail_closed else ("warning" if orders else "pass")
    report = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "report_type": REPORT_TYPE,
        "discovery_version": DISCOVERY_VERSION,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "runtime_mutation_allowed": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "decision_authority": "producer_gap_discovery_source_only",
        "metric_role": "source_quality_gate",
        "window_policy": "same_day_postclose_sim_probe_real_flow_review",
        "sample_floor": 1,
        "primary_decision_metric": "source_quality_adjusted_ev_pct",
        "source_quality_gate": "source artifact exists and parsed AI review passed",
        "forbidden_uses": FORBIDDEN_USES,
        "status": status,
        "sources": {
            label: str(path) if path.exists() else None
            for label, path in _source_paths(target_date).items()
        },
        "summary": {
            "status": status,
            "candidate_count": len(candidates),
            "high_priority_candidate_count": sum(
                1 for item in reviewed_candidates if PRIORITY_RANK.get(str(item.get("ai_priority")), 99) <= 1
            ),
            "workorder_count": len(orders),
            "ai_two_pass_review_status": ai_status,
            "ai_fail_closed": fail_closed,
            "provider": resolved_provider,
            "model": provider_status.get("model") or (AI_REVIEW_MODEL if resolved_provider == "openai" else None),
            "audit_status": audit.get("status"),
            "pattern_type_counts": dict(state_counts),
            "human_intervention_required": False,
        },
        "ai_two_pass_review": {
            "provider": resolved_provider,
            "status": ai_status,
            "model": provider_status.get("model") or (AI_REVIEW_MODEL if resolved_provider == "openai" else None),
            "schema_name": AI_REVIEW_SCHEMA_NAME,
            "provider_status": provider_status,
            "input_context_hash": _text_hash(context),
            "audit": audit,
            "candidate_reviews": ai_payload.get("candidate_reviews") if isinstance(ai_payload.get("candidate_reviews"), list) else [],
            "warnings": ai_warnings,
            "fail_closed": fail_closed,
        },
        "producer_gap_candidates": reviewed_candidates,
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
    lines = [
        f"# Producer Gap Discovery - {report.get('date')}",
        "",
        "## Summary",
        "",
        f"- status: `{report.get('status')}`",
        f"- runtime_effect: `{report.get('runtime_effect')}`",
        f"- allowed_runtime_apply: `{report.get('allowed_runtime_apply')}`",
        f"- decision_authority: `{report.get('decision_authority')}`",
        f"- candidate_count: `{summary.get('candidate_count')}`",
        f"- high_priority_candidate_count: `{summary.get('high_priority_candidate_count')}`",
        f"- workorder_count: `{summary.get('workorder_count')}`",
        f"- ai_two_pass_review_status: `{summary.get('ai_two_pass_review_status')}`",
        f"- ai_fail_closed: `{summary.get('ai_fail_closed')}`",
        f"- audit_status: `{summary.get('audit_status')}`",
        "",
        "## AI Review",
        "",
        f"- provider: `{review.get('provider')}`",
        f"- model: `{review.get('model') or '-'}`",
        f"- warnings: `{review.get('warnings') or []}`",
        "",
        "## Candidates",
        "",
    ]
    for item in report.get("producer_gap_candidates") or []:
        if not isinstance(item, dict):
            continue
        lines.append(
            f"- `{item.get('candidate_id')}` type=`{item.get('pattern_type')}` "
            f"priority=`{item.get('ai_priority')}` samples=`{item.get('sample_count')}`"
        )
    lines.extend(["", "## Code Improvement Orders", ""])
    for order in report.get("code_improvement_orders") or []:
        if isinstance(order, dict):
            lines.append(f"- `{order.get('order_id')}`: {order.get('title')}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument(
        "--provider",
        default=os.getenv("KORSTOCKSCAN_PRODUCER_GAP_DISCOVERY_AI_PROVIDER", AI_REVIEW_DEFAULT_PROVIDER),
        choices=["openai", "none", "off", "false", "0"],
    )
    args = parser.parse_args(argv)
    report = build_producer_gap_discovery_report(args.date, provider=args.provider)
    json_path, md_path = report_paths(args.date)
    print(json.dumps({"status": report.get("status"), "json": str(json_path), "md": str(md_path)}, ensure_ascii=False))
    return 1 if report.get("status") == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
