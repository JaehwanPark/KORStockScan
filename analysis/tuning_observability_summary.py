"""Common observability summary builder for pattern labs."""

from __future__ import annotations

import gzip
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT_DIR = PROJECT_ROOT / "data" / "report" / "monitor_snapshots"
SCHEMA_VERSION = 3
FORBIDDEN_USES = [
    "runtime_threshold_apply",
    "broker_order_enable",
    "provider_route_change",
    "bot_restart",
    "single_day_live_canary_approval",
]
OBSERVABILITY_METRIC_CONTRACT = {
    "metric_role": "funnel_count",
    "decision_authority": "source_quality_only",
    "window_policy": "daily_only_for_ops_with_rolling_consumer_required",
    "sample_floor": 1,
    "primary_decision_metric": "submitted_drought_and_blocker_count",
    "source_quality_gate": "performance_tuning + wait6579_ev_cohort + trade_review + post_sell_feedback source presence",
    "forbidden_uses": FORBIDDEN_USES,
    "runtime_effect": False,
}
SNAPSHOT_CONTRACTS: dict[str, dict[str, Any]] = {
    "performance_tuning": {
        "producer": "sniper_performance_tuning_report",
        "required_fields": ("metrics",),
        "consumers": ("tuning_observability_summary", "pattern_lab_currentness_audit"),
    },
    "wait6579_ev_cohort": {
        "producer": "wait6579_ev_cohort_monitor_snapshot",
        "required_fields": ("metrics", "preflight"),
        "consumers": ("tuning_observability_summary", "pattern_lab_currentness_audit"),
    },
    "trade_review": {
        "producer": "trade_review_monitor_snapshot",
        "required_fields": ("metrics",),
        "consumers": ("tuning_observability_summary", "pattern_lab_currentness_audit"),
    },
    "post_sell_feedback": {
        "producer": "post_sell_feedback_monitor_snapshot",
        "required_fields": ("metrics",),
        "consumers": ("tuning_observability_summary", "pattern_lab_currentness_audit"),
    },
}


def _load_json(path: Path) -> Any | None:
    try:
        if path.suffix == ".gz":
            with gzip.open(path, "rt", encoding="utf-8") as handle:
                return json.load(handle)
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _load_snapshot_with_status(kind: str, target_date: str) -> tuple[dict[str, Any], dict[str, Any]]:
    for suffix in (".json", ".json.gz"):
        path = SNAPSHOT_DIR / f"{kind}_{target_date}{suffix}"
        if path.exists():
            payload = _load_json(path)
            if isinstance(payload, dict):
                return payload, {
                    "present": True,
                    "json_valid": True,
                    "type_valid": True,
                    "path": str(path),
                    "status": "loaded",
                }
            return {}, {
                "present": True,
                "json_valid": payload is not None,
                "type_valid": False,
                "path": str(path),
                "status": "invalid_json_type" if payload is not None else "unreadable",
            }
    return {}, {
        "present": False,
        "json_valid": False,
        "type_valid": False,
        "path": None,
        "status": "missing",
    }


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, "", "-", "None"):
            return default
        return int(float(value))
    except Exception:
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, "", "-", "None"):
            return default
        number = float(value)
    except Exception:
        return default
    return number if number == number else default


def _snapshot_contract(target_date: str) -> dict[str, Any]:
    contracts: dict[str, Any] = {}
    for source_id, contract in SNAPSHOT_CONTRACTS.items():
        paths = [
            SNAPSHOT_DIR / f"{source_id}_{target_date}.json",
            SNAPSHOT_DIR / f"{source_id}_{target_date}.json.gz",
        ]
        contracts[source_id] = {
            "producer": contract["producer"],
            "expected_paths": [str(path) for path in paths],
            "required_fields": list(contract["required_fields"]),
            "consumers": list(contract["consumers"]),
            "metric_role": "source_quality_gate",
            "decision_authority": "source_quality_only",
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "forbidden_uses": FORBIDDEN_USES,
        }
    return contracts


def _source_contract_findings(
    *,
    target_date: str,
    payloads: dict[str, dict[str, Any]],
    source_status: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for source_id, contract in SNAPSHOT_CONTRACTS.items():
        status = source_status[source_id]
        if not status.get("present"):
            findings.append(
                {
                    "source_id": source_id,
                    "finding_type": "missing",
                    "severity": "fail",
                    "reason": f"{source_id}_{target_date}.json or .json.gz is missing",
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                }
            )
            continue
        if not status.get("json_valid"):
            findings.append(
                {
                    "source_id": source_id,
                    "finding_type": "unreadable",
                    "severity": "fail",
                    "reason": str(status.get("status") or "unreadable"),
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                }
            )
            continue
        if not status.get("type_valid"):
            findings.append(
                {
                    "source_id": source_id,
                    "finding_type": "non_dict_json",
                    "severity": "fail",
                    "reason": str(status.get("status") or "invalid_json_type"),
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                }
            )
            continue
        payload = payloads.get(source_id) or {}
        for field in contract["required_fields"]:
            value = payload.get(field)
            if not isinstance(value, dict):
                findings.append(
                    {
                        "source_id": source_id,
                        "finding_type": "required_field_missing",
                        "field": field,
                        "severity": "warning",
                        "reason": f"required field {field} is missing or not an object",
                        "runtime_effect": False,
                        "allowed_runtime_apply": False,
                    }
                )
    return findings


def _contract_status(findings: list[dict[str, Any]]) -> str:
    if any(str(item.get("severity")) == "fail" for item in findings):
        return "fail"
    if findings:
        return "warning"
    return "pass"


def _observability_order(finding: dict[str, Any]) -> dict[str, Any]:
    source_id = str(finding.get("source_id") or "pattern_lab")
    finding_type = str(finding.get("finding_type") or "contract_gap")
    return {
        "order_id": f"order_tuning_observability_{source_id}_{finding_type}_contract_gap",
        "title": f"Tuning observability {source_id} {finding_type} contract gap",
        "source_report_type": "tuning_observability_summary",
        "lifecycle_stage": "pattern_lab_observability",
        "target_subsystem": "pattern_lab",
        "priority": 8 if str(finding.get("severity")) == "fail" else 6,
        "route": "source_contract_gap",
        "confidence": "deterministic_source_contract",
        "intent": str(finding.get("reason") or "Close tuning observability source contract gap."),
        "expected_ev_effect": "Improve report/source-quality handoff without runtime mutation.",
        "evidence": [json.dumps(finding, ensure_ascii=False, sort_keys=True)],
        "files_likely_touched": ["analysis/tuning_observability_summary.py"],
        "acceptance_tests": [
            "PYTHONPATH=. .venv/bin/pytest -q src/tests/test_tuning_observability_summary.py src/tests/test_pattern_lab_currentness_audit.py",
        ],
        "improvement_type": "source_contract_gap",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "strategy_effect": False,
        "data_quality_effect": True,
        "tuning_axis_effect": False,
        "next_postclose_metric": f"tuning_observability_summary.{source_id}.{finding_type}",
        "forbidden_uses": FORBIDDEN_USES,
    }


def build_tuning_observability_summary(
    *,
    target_date: str,
    analysis_start: str,
    analysis_end: str,
) -> dict[str, Any]:
    performance, performance_status = _load_snapshot_with_status("performance_tuning", target_date)
    wait6579, wait6579_status = _load_snapshot_with_status("wait6579_ev_cohort", target_date)
    trade_review, trade_review_status = _load_snapshot_with_status("trade_review", target_date)
    post_sell, post_sell_status = _load_snapshot_with_status("post_sell_feedback", target_date)
    source_status = {
        "performance_tuning": performance_status,
        "wait6579_ev_cohort": wait6579_status,
        "trade_review": trade_review_status,
        "post_sell_feedback": post_sell_status,
    }
    payloads = {
        "performance_tuning": performance,
        "wait6579_ev_cohort": wait6579,
        "trade_review": trade_review,
        "post_sell_feedback": post_sell,
    }
    source_contract_findings = _source_contract_findings(
        target_date=target_date,
        payloads=payloads,
        source_status=source_status,
    )
    source_contract_status = _contract_status(source_contract_findings)
    code_improvement_orders = [
        _observability_order(finding)
        for finding in source_contract_findings
        if finding.get("finding_type") in {"missing", "unreadable", "non_dict_json", "required_field_missing"}
    ]

    perf_metrics = performance.get("metrics", {}) or {}
    wait_metrics = wait6579.get("metrics", {}) or {}
    preflight = wait6579.get("preflight", {}) or {}
    trade_metrics = trade_review.get("metrics", {}) or {}
    post_metrics = post_sell.get("metrics", {}) or {}
    terminal_rows = wait6579.get("terminal_breakdown", []) or []
    terminal_map = {
        str(row.get("terminal_blocker") or ""): _safe_int(row.get("samples"))
        for row in terminal_rows
        if isinstance(row, dict)
    }
    submission_rows = preflight.get("submission_blocker_breakdown", []) or []
    submission_map = {
        str(row.get("label") or ""): _safe_int(row.get("samples"))
        for row in submission_rows
        if isinstance(row, dict)
    }

    blocked_ai_score = terminal_map.get("blocked_ai_score", 0)
    total_candidates = _safe_int(wait_metrics.get("total_candidates"))
    blocked_ai_score_share = round((blocked_ai_score / total_candidates) * 100, 1) if total_candidates else 0.0

    summary = {
        "schema_version": SCHEMA_VERSION,
        "metric_contract": OBSERVABILITY_METRIC_CONTRACT,
        "source_contract": _snapshot_contract(target_date),
        "source_contract_status": source_contract_status,
        "source_contract_findings": source_contract_findings,
        "code_improvement_orders": code_improvement_orders,
        "automation_handoff": {
            "producer": "tuning_observability_summary",
            "consumers": [
                "gemini_scalping_pattern_lab.outputs",
                "claude_scalping_pattern_lab.outputs",
                "pattern_lab_currentness_audit",
                "build_code_improvement_workorder_via_currentness_audit",
            ],
            "direct_workorder_consumer": False,
            "currentness_audit_handoff_required": True,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        },
        "meta": {
            "target_date": target_date,
            "analysis_period": {
                "start_date": analysis_start,
                "end_date": analysis_end,
            },
        },
        "entry_funnel": {
            "gatekeeper_decisions": _safe_int(perf_metrics.get("gatekeeper_decisions")),
            "gatekeeper_eval_ms_p95": _safe_float(perf_metrics.get("gatekeeper_eval_ms_p95")),
            "gatekeeper_lock_wait_ms_p95": _safe_float(perf_metrics.get("gatekeeper_lock_wait_ms_p95")),
            "gatekeeper_model_call_ms_p95": _safe_float(perf_metrics.get("gatekeeper_model_call_ms_p95")),
            "budget_pass_events": _safe_int(perf_metrics.get("budget_pass_events")),
            "submitted_events": _safe_int(perf_metrics.get("order_bundle_submitted_events")),
            "budget_pass_to_submitted_rate": _safe_float(perf_metrics.get("budget_pass_to_submitted_rate")),
            "latency_block_events": _safe_int(perf_metrics.get("latency_block_events")),
            "quote_fresh_latency_blocks": _safe_int(perf_metrics.get("quote_fresh_latency_blocks")),
            "full_fill_events": _safe_int(perf_metrics.get("full_fill_events")),
            "partial_fill_events": _safe_int(perf_metrics.get("partial_fill_events")),
            "completed_trades": _safe_int(trade_metrics.get("completed_trades")),
            "realized_pnl_krw": _safe_int(trade_metrics.get("realized_pnl_krw")),
        },
        "buy_recovery_canary": {
            "total_candidates": total_candidates,
            "recovery_check_candidates": _safe_int(preflight.get("recovery_check_candidates")),
            "recovery_promoted_candidates": _safe_int(preflight.get("recovery_promoted_candidates")),
            "submitted_candidates": _safe_int(preflight.get("submitted_candidates")),
            "latency_block_candidates": _safe_int(preflight.get("latency_block_candidates")),
            "blocked_ai_score_samples": blocked_ai_score,
            "blocked_ai_score_share_pct": blocked_ai_score_share,
            "terminal_blockers": terminal_rows,
            "submission_blockers": submission_rows,
        },
        "holding_axis": {
            "evaluated_candidates": _safe_int(post_metrics.get("evaluated_candidates")),
            "missed_upside_rate": _safe_float(post_metrics.get("missed_upside_rate")),
            "good_exit_rate": _safe_float(post_metrics.get("good_exit_rate")),
            "capture_efficiency_avg_pct": _safe_float(post_metrics.get("capture_efficiency_avg_pct")),
        },
    }

    findings: list[dict[str, str]] = []
    source_quality_findings = [
        f"{name}:{status['status']}"
        for name, status in source_status.items()
        if status.get("status") != "loaded"
    ]
    source_quality_findings.extend(
        f"{item.get('source_id')}:{item.get('finding_type')}:{item.get('field') or '-'}"
        for item in source_contract_findings
        if item.get("finding_type") == "required_field_missing"
    )
    for finding in source_quality_findings:
        findings.append(
            {
                "label": "Source quality warning",
                "judgment": "경고",
                "why": f"`{finding}` 때문에 관제 입력이 불완전하다.",
            }
        )
    if blocked_ai_score_share >= 70.0:
        findings.append(
            {
                "label": "AI threshold dominance",
                "judgment": "경고",
                "why": (
                    f"`blocked_ai_score_share={blocked_ai_score_share:.1f}%`로 WAIT/BLOCK 비중이 높아 "
                    "BUY drought 해석을 지지한다."
                ),
            }
        )
    if summary["buy_recovery_canary"]["recovery_promoted_candidates"] > 0 and summary["buy_recovery_canary"]["submitted_candidates"] == 0:
        findings.append(
            {
                "label": "Prompt improved but submit disconnected",
                "judgment": "경고",
                "why": (
                    f"`promoted={summary['buy_recovery_canary']['recovery_promoted_candidates']}`인데 "
                    f"`submitted={summary['buy_recovery_canary']['submitted_candidates']}`라 "
                    "프롬프트 개선과 주문 회복을 동일시할 수 없다."
                ),
            }
        )
    if summary["entry_funnel"]["gatekeeper_eval_ms_p95"] > 15900:
        findings.append(
            {
                "label": "Gatekeeper latency high",
                "judgment": "경고",
                "why": (
                    f"`gatekeeper_eval_ms_p95={summary['entry_funnel']['gatekeeper_eval_ms_p95']:.0f}ms`로 "
                    "지연 경고 구간에 들어가 있다."
                ),
            }
        )
    if summary["entry_funnel"]["budget_pass_events"] > 0 and summary["entry_funnel"]["submitted_events"] == 0:
        findings.append(
            {
                "label": "Budget pass without submit",
                "judgment": "경고",
                "why": (
                    f"`budget_pass={summary['entry_funnel']['budget_pass_events']}`인데 "
                    f"`submitted={summary['entry_funnel']['submitted_events']}`라 "
                    "제출 전 병목이 기대값 회복을 끊고 있다."
                ),
            }
        )
    if not findings:
        findings.append(
            {
                "label": "No acute observability alert",
                "judgment": "중립",
                "why": "주요 관찰축에서 즉시 경고할 단일 병목이 두드러지지 않는다.",
            }
        )

    summary["priority_findings"] = findings
    summary["source_presence"] = {
        name: bool(status.get("present") and status.get("json_valid") and status.get("type_valid"))
        for name, status in source_status.items()
    }
    summary["source_quality"] = {
        "status": source_contract_status if source_contract_status != "pass" else "pass",
        "findings": source_quality_findings,
        "source_contract_findings": source_contract_findings,
        "sources": source_status,
    }
    summary["submission_blocker_sample_count"] = sum(submission_map.values())
    return summary


def write_tuning_observability_outputs(
    *,
    output_dir: Path,
    target_date: str,
    analysis_start: str,
    analysis_end: str,
) -> dict[str, Any]:
    summary = build_tuning_observability_summary(
        target_date=target_date,
        analysis_start=analysis_start,
        analysis_end=analysis_end,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "tuning_observability_summary.json"
    md_path = output_dir / "tuning_observability_summary.md"
    json_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# Tuning Observability Summary",
        "",
        f"- target_date: `{target_date}`",
        f"- analysis_period: `{analysis_start} ~ {analysis_end}`",
        "",
        "## Entry Funnel",
        "",
        f"- gatekeeper_decisions: `{summary['entry_funnel']['gatekeeper_decisions']}`",
        f"- gatekeeper_eval_ms_p95: `{summary['entry_funnel']['gatekeeper_eval_ms_p95']:.0f}ms`",
        f"- gatekeeper_lock_wait_ms_p95: `{summary['entry_funnel']['gatekeeper_lock_wait_ms_p95']:.0f}ms`",
        f"- gatekeeper_model_call_ms_p95: `{summary['entry_funnel']['gatekeeper_model_call_ms_p95']:.0f}ms`",
        f"- budget_pass_events: `{summary['entry_funnel']['budget_pass_events']}`",
        f"- submitted_events: `{summary['entry_funnel']['submitted_events']}`",
        f"- budget_pass_to_submitted_rate: `{summary['entry_funnel']['budget_pass_to_submitted_rate']:.1f}%`",
        f"- latency_block_events: `{summary['entry_funnel']['latency_block_events']}`",
        f"- quote_fresh_latency_blocks: `{summary['entry_funnel']['quote_fresh_latency_blocks']}`",
        "",
        "## Buy Recovery Canary",
        "",
        f"- total_candidates: `{summary['buy_recovery_canary']['total_candidates']}`",
        f"- recovery_check: `{summary['buy_recovery_canary']['recovery_check_candidates']}`",
        f"- promoted: `{summary['buy_recovery_canary']['recovery_promoted_candidates']}`",
        f"- submitted: `{summary['buy_recovery_canary']['submitted_candidates']}`",
        f"- blocked_ai_score_share: `{summary['buy_recovery_canary']['blocked_ai_score_share_pct']:.1f}%`",
        "",
        "## Priority Findings",
        "",
    ]
    for item in summary["priority_findings"]:
        lines.append(f"- `{item['label']}`: {item['judgment']} — {item['why']}")
    lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return summary
