"""Audit pattern lab result propagation through the postclose chain."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from src.engine.build_code_improvement_workorder import code_improvement_workorder_paths
from src.engine.daily_threshold_cycle_report import REPORT_DIR
from src.engine.pattern_lab_currentness_audit import (
    report_paths as currentness_report_paths,
)
from src.engine.runtime_approval_summary import summary_paths as runtime_summary_paths
from src.engine.scalping_pattern_lab_automation import (
    automation_report_paths as scalping_automation_report_paths,
)
from src.engine.swing_pattern_lab_automation import (
    swing_pattern_lab_automation_report_paths,
)
from src.engine.threshold_cycle_ev_report import ev_report_paths

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT_TYPE = "pattern_lab_propagation_audit"
REPORT_SCHEMA_VERSION = 1
REPORT_DIRNAME = REPORT_TYPE
FORBIDDEN_USES = [
    "threshold mutation",
    "order guard mutation",
    "provider change",
    "bot restart",
    "broker order submit",
]


def report_paths(target_date: str) -> tuple[Path, Path]:
    base = REPORT_DIR / REPORT_DIRNAME / f"{REPORT_TYPE}_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _path_text(path: Path) -> str:
    return str(path)


def _source_dict(payload: dict[str, Any]) -> dict[str, Any]:
    source = payload.get("source") if isinstance(payload.get("source"), dict) else {}
    sources = payload.get("sources") if isinstance(payload.get("sources"), dict) else {}
    result = dict(source)
    result.update(sources)
    return result


def _has_source(source: dict[str, Any], key: str) -> bool:
    value = source.get(key)
    return value not in (None, "", "-", [])


def _ldm_bucket_workorder_count(payload: dict[str, Any], key: str) -> int:
    attribution = payload.get(key) if isinstance(payload.get(key), dict) else {}
    workorders = attribution.get("code_improvement_workorders")
    return len(workorders) if isinstance(workorders, list) else 0


def _check(
    check_id: str,
    *,
    status: str,
    severity: str,
    finding: str,
    source_paths: list[Path],
    recommended_order: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "status": status,
        "severity": severity,
        "finding": finding,
        "source_paths": [_path_text(path) for path in source_paths],
        "recommended_order": recommended_order,
    }


def _order(check_id: str, title: str, source_paths: list[Path]) -> dict[str, Any]:
    return {
        "order_id": f"order_{REPORT_TYPE}_{check_id}",
        "title": title,
        "source_report_type": REPORT_TYPE,
        "lifecycle_stage": "pattern_lab_propagation",
        "target_subsystem": "postclose_automation_chain",
        "priority": 20,
        "route": "implement_now",
        "confidence": "consensus",
        "intent": title,
        "expected_ev_effect": "Close report lineage/source-quality visibility without runtime mutation.",
        "evidence": [_path_text(path) for path in source_paths],
        "files_likely_touched": [
            "deploy/run_threshold_cycle_postclose.sh",
            "src/engine/threshold_cycle_ev_report.py",
            "src/engine/runtime_approval_summary.py",
            "src/engine/build_code_improvement_workorder.py",
        ],
        "acceptance_tests": [
            "PYTHONPATH=. .venv/bin/pytest -q src/tests/test_pattern_lab_propagation_audit.py",
            "PYTHONPATH=. .venv/bin/pytest -q src/tests/test_threshold_cycle_wrappers.py",
        ],
        "improvement_type": "propagation_lineage_gap",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "strategy_effect": False,
        "data_quality_effect": True,
        "tuning_axis_effect": False,
        "next_postclose_metric": f"{REPORT_TYPE}.{check_id}",
        "forbidden_uses": FORBIDDEN_USES,
    }


def _automation_fresh(
    report: dict[str, Any], target_date: str, summary_key: str
) -> tuple[str, str]:
    if not report:
        return "fail", "artifact parse failed or report missing"
    if str(report.get("date") or "") != target_date:
        return (
            "fail",
            f"date mismatch expected={target_date} actual={report.get('date')}",
        )
    summary = (
        report.get("ev_report_summary")
        if isinstance(report.get("ev_report_summary"), dict)
        else {}
    )
    if summary_key == "gemini_fresh" and summary.get("gemini_enabled") is False:
        return "pass", str(
            summary.get("gemini_retired_reason") or "retired_from_automatic_execution"
        )
    available = bool(summary.get(summary_key))
    if not available:
        stale_reason = (
            summary.get("stale_reason")
            or "lab output unavailable; downstream must block it explicitly"
        )
        return "warning", str(stale_reason)
    return "pass", "fresh lab automation source is available"


def _runtime_effect_violations(*reports: dict[str, Any]) -> list[str]:
    violations: list[str] = []

    def walk(value: Any, path: str) -> None:
        if isinstance(value, dict):
            if (
                value.get("runtime_effect") is True
                or value.get("runtime_change") is True
            ):
                violations.append(path)
            for key, child in value.items():
                walk(child, f"{path}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f"{path}[{index}]")

    for idx, report in enumerate(reports):
        walk(report, f"report{idx}")
    return violations


def build_pattern_lab_propagation_audit(target_date: str) -> dict[str, Any]:
    target_date = str(target_date).strip()
    scalping_path, _ = scalping_automation_report_paths(target_date)
    swing_path, _ = swing_pattern_lab_automation_report_paths(target_date)
    currentness_path, _ = currentness_report_paths(target_date)
    workorder_path, _ = code_improvement_workorder_paths(target_date)
    ev_path, _ = ev_report_paths(target_date)
    runtime_path, _ = runtime_summary_paths(target_date)

    scalping = _load_json(scalping_path)
    swing = _load_json(swing_path)
    currentness = _load_json(currentness_path)
    workorder = _load_json(workorder_path)
    ev_report = _load_json(ev_path)
    runtime_summary = _load_json(runtime_path)
    ev_source = _source_dict(ev_report)
    ldm_path = (
        Path(str(ev_source.get("lifecycle_decision_matrix")))
        if ev_source.get("lifecycle_decision_matrix")
        else None
    )
    lifecycle_report = _load_json(ldm_path) if ldm_path else {}

    checks: list[dict[str, Any]] = []

    scalping_status, scalping_finding = _automation_fresh(
        scalping, target_date, "gemini_fresh"
    )
    claude_status, claude_finding = _automation_fresh(
        scalping, target_date, "claude_fresh"
    )
    swing_status, swing_finding = _automation_fresh(
        swing, target_date, "deepseek_lab_available"
    )
    checks.append(
        _check(
            "scalping_gemini_automation_retired",
            status=scalping_status,
            severity=(
                "source_quality_blocker"
                if scalping_status == "fail"
                else "warning" if scalping_status == "warning" else "info"
            ),
            finding=scalping_finding,
            source_paths=[scalping_path],
        )
    )
    checks.append(
        _check(
            "scalping_claude_automation_fresh",
            status=claude_status,
            severity=(
                "source_quality_blocker"
                if claude_status == "fail"
                else "warning" if claude_status == "warning" else "info"
            ),
            finding=claude_finding,
            source_paths=[scalping_path],
        )
    )
    checks.append(
        _check(
            "deepseek_swing_automation_fresh",
            status=swing_status,
            severity=(
                "source_quality_blocker"
                if swing_status == "fail"
                else "warning" if swing_status == "warning" else "info"
            ),
            finding=swing_finding,
            source_paths=[swing_path],
        )
    )

    currentness_ok = (
        bool(currentness)
        and currentness.get("report_type") == "pattern_lab_currentness_audit"
    )
    checks.append(
        _check(
            "currentness_audit_available",
            status="pass" if currentness_ok else "fail",
            severity="info" if currentness_ok else "source_quality_blocker",
            finding="currentness audit must exist before code workorder build.",
            source_paths=[currentness_path],
            recommended_order=(
                None
                if currentness_ok
                else _order(
                    "currentness_audit_available",
                    "Connect pattern_lab_currentness_audit before workorder build",
                    [currentness_path],
                )
            ),
        )
    )

    workorder_source = _source_dict(workorder)
    workorder_source_ok = bool(workorder) and _has_source(
        workorder_source, "pattern_lab_currentness_audit"
    )
    checks.append(
        _check(
            "workorder_consumes_currentness_audit",
            status="pass" if workorder_source_ok else "fail",
            severity="info" if workorder_source_ok else "source_quality_blocker",
            finding="code_improvement_workorder must include pattern_lab_currentness_audit in source lineage.",
            source_paths=[workorder_path, currentness_path],
            recommended_order=(
                None
                if workorder_source_ok
                else _order(
                    "workorder_consumes_currentness_audit",
                    "Add currentness audit source to code improvement workorder",
                    [workorder_path, currentness_path],
                )
            ),
        )
    )

    currentness_order_count = (
        len(currentness.get("code_improvement_orders") or [])
        if isinstance(currentness.get("code_improvement_orders"), list)
        else 0
    )
    workorder_summary = (
        workorder.get("summary") if isinstance(workorder.get("summary"), dict) else {}
    )
    consumes_currentness_orders = (
        int(workorder_summary.get("pattern_lab_currentness_source_order_count") or 0)
        >= currentness_order_count
    )
    checks.append(
        _check(
            "workorder_currentness_order_count",
            status="pass" if consumes_currentness_orders else "fail",
            severity=(
                "info" if consumes_currentness_orders else "source_quality_blocker"
            ),
            finding="currentness audit selected orders must be counted by code_improvement_workorder.",
            source_paths=[workorder_path, currentness_path],
            recommended_order=(
                None
                if consumes_currentness_orders
                else _order(
                    "workorder_currentness_order_count",
                    "Consume currentness selected orders in code improvement workorder",
                    [workorder_path, currentness_path],
                )
            ),
        )
    )

    ev_currentness_ok = bool(ev_report) and _has_source(
        ev_source, "pattern_lab_currentness_audit"
    )
    ev_propagation_ok = bool(ev_report) and _has_source(
        ev_source, "pattern_lab_propagation_audit"
    )
    checks.append(
        _check(
            "threshold_cycle_ev_currentness_source_link",
            status="pass" if ev_currentness_ok else "fail",
            severity="info" if ev_currentness_ok else "source_quality_blocker",
            finding="threshold_cycle_ev must expose pattern_lab_currentness_audit source link.",
            source_paths=[ev_path, currentness_path],
            recommended_order=(
                None
                if ev_currentness_ok
                else _order(
                    "threshold_cycle_ev_currentness_source_link",
                    "Expose currentness audit in threshold_cycle_ev",
                    [ev_path, currentness_path],
                )
            ),
        )
    )
    checks.append(
        _check(
            "threshold_cycle_ev_propagation_source_link",
            status="pass" if ev_propagation_ok else "warning",
            severity=(
                "info" if ev_propagation_ok else "post_propagation_ev_refresh_pending"
            ),
            finding="threshold_cycle_ev must expose pattern_lab_propagation_audit after the post-propagation EV refresh.",
            source_paths=[ev_path, report_paths(target_date)[0]],
        )
    )

    runtime_source = _source_dict(runtime_summary)
    if not runtime_summary:
        runtime_status = "warning"
        runtime_severity = "runtime_summary_pending"
    else:
        runtime_status = (
            "pass"
            if _has_source(runtime_source, "pattern_lab_propagation_audit")
            else "fail"
        )
        runtime_severity = (
            "info" if runtime_status == "pass" else "source_quality_blocker"
        )
    checks.append(
        _check(
            "runtime_summary_propagation_source_link",
            status=runtime_status,
            severity=runtime_severity,
            finding="runtime_approval_summary must expose pattern_lab_propagation_audit source link when generated after this audit.",
            source_paths=[runtime_path, report_paths(target_date)[0]],
            recommended_order=(
                None
                if runtime_status != "fail"
                else _order(
                    "runtime_summary_propagation_source_link",
                    "Expose propagation audit in runtime approval summary",
                    [runtime_path],
                )
            ),
        )
    )

    workorder_ldm_ok = bool(workorder) and _has_source(
        workorder_source, "lifecycle_decision_matrix"
    )
    checks.append(
        _check(
            "workorder_consumes_lifecycle_decision_matrix",
            status="pass" if workorder_ldm_ok else "fail",
            severity="info" if workorder_ldm_ok else "source_quality_blocker",
            finding="code_improvement_workorder must include lifecycle_decision_matrix source so entry/scale-in/overnight bucket workorders are not dropped.",
            source_paths=[workorder_path, ldm_path or ev_path],
            recommended_order=(
                None
                if workorder_ldm_ok
                else _order(
                    "workorder_consumes_lifecycle_decision_matrix",
                    "Add lifecycle_decision_matrix source to code improvement workorder",
                    [workorder_path, ldm_path or ev_path],
                )
            ),
        )
    )

    expected_bucket_counts = {
        "entry": _ldm_bucket_workorder_count(
            lifecycle_report, "entry_bucket_attribution"
        ),
        "scale_in": _ldm_bucket_workorder_count(
            lifecycle_report, "scale_in_bucket_attribution"
        ),
        "overnight": _ldm_bucket_workorder_count(
            lifecycle_report, "overnight_bucket_attribution"
        ),
    }
    actual_bucket_counts = {
        "entry": int(
            workorder_summary.get("lifecycle_entry_bucket_source_order_count") or 0
        ),
        "scale_in": int(
            workorder_summary.get("lifecycle_scale_in_bucket_source_order_count") or 0
        ),
        "overnight": int(
            workorder_summary.get("lifecycle_overnight_bucket_source_order_count") or 0
        ),
    }
    bucket_counts_ok = all(
        actual_bucket_counts[key] >= expected_bucket_counts[key]
        for key in expected_bucket_counts
    )
    checks.append(
        _check(
            "workorder_lifecycle_bucket_order_counts",
            status="pass" if bucket_counts_ok else "fail",
            severity="info" if bucket_counts_ok else "source_quality_blocker",
            finding=(
                "code_improvement_workorder must count LDM entry/scale-in/overnight bucket workorders. "
                f"expected={expected_bucket_counts}, actual={actual_bucket_counts}"
            ),
            source_paths=[workorder_path, ldm_path or ev_path],
            recommended_order=(
                None
                if bucket_counts_ok
                else _order(
                    "workorder_lifecycle_bucket_order_counts",
                    "Consume all LDM lifecycle bucket workorders",
                    [workorder_path, ldm_path or ev_path],
                )
            ),
        )
    )

    deepseek_quality_path = (
        PROJECT_ROOT
        / "analysis"
        / "deepseek_swing_pattern_lab"
        / "outputs"
        / "data_quality_report.json"
    )
    deepseek_quality = _load_json(deepseek_quality_path)
    sim_probe_ok = bool(deepseek_quality.get("sim_probe_provenance"))
    checks.append(
        _check(
            "deepseek_sim_probe_provenance_propagated",
            status="pass" if sim_probe_ok else "fail",
            severity="info" if sim_probe_ok else "source_quality_blocker",
            finding="DeepSeek sim/probe provenance must be present before downstream propagation can be trusted.",
            source_paths=[deepseek_quality_path, swing_path],
            recommended_order=(
                None
                if sim_probe_ok
                else _order(
                    "deepseek_sim_probe_provenance_propagated",
                    "Propagate DeepSeek sim/probe provenance",
                    [swing_path],
                )
            ),
        )
    )

    runtime_violations = _runtime_effect_violations(
        currentness, scalping, swing, workorder
    )
    checks.append(
        _check(
            "runtime_effect_false_contract",
            status="pass" if not runtime_violations else "fail",
            severity="info" if not runtime_violations else "source_quality_blocker",
            finding="pattern lab source artifacts and workorders must not set runtime_effect=true/runtime_change=true. "
            + (
                f"violations={runtime_violations[:10]}"
                if runtime_violations
                else "No violations."
            ),
            source_paths=[currentness_path, scalping_path, swing_path, workorder_path],
            recommended_order=(
                None
                if not runtime_violations
                else _order(
                    "runtime_effect_false_contract",
                    "Reject runtime_effect=true pattern lab propagation",
                    [currentness_path, scalping_path, swing_path, workorder_path],
                )
            ),
        )
    )

    orders = [
        check["recommended_order"]
        for check in checks
        if isinstance(check.get("recommended_order"), dict)
    ]
    fail_count = sum(1 for check in checks if check.get("status") == "fail")
    warning_count = sum(1 for check in checks if check.get("status") == "warning")
    status = "fail" if fail_count else "warning" if warning_count else "pass"
    report = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "date": target_date,
        "report_type": REPORT_TYPE,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": status,
        "runtime_effect": False,
        "decision_authority": "source_quality_only",
        "forbidden_uses": FORBIDDEN_USES,
        "summary": {
            "check_count": len(checks),
            "fail_count": fail_count,
            "warning_count": warning_count,
            "code_improvement_order_count": len(orders),
            "currentness_order_count": currentness_order_count,
            "workorder_currentness_source_order_count": int(
                workorder_summary.get("pattern_lab_currentness_source_order_count") or 0
            ),
        },
        "checks": checks,
        "code_improvement_orders": orders,
    }
    json_path, md_path = report_paths(target_date)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return report


def render_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    lines = [
        f"# Pattern Lab Propagation Audit - {report.get('date')}",
        "",
        "## Summary",
        "",
        f"- status: `{report.get('status')}`",
        f"- runtime_effect: `{report.get('runtime_effect')}`",
        f"- decision_authority: `{report.get('decision_authority')}`",
        f"- check_count: `{summary.get('check_count')}`",
        f"- fail_count: `{summary.get('fail_count')}`",
        f"- warning_count: `{summary.get('warning_count')}`",
        "",
        "## Checks",
        "",
    ]
    for check in report.get("checks") or []:
        if not isinstance(check, dict):
            continue
        lines.extend(
            [
                f"### `{check.get('check_id')}`",
                "",
                f"- status: `{check.get('status')}`",
                f"- severity: `{check.get('severity')}`",
                f"- finding: {check.get('finding')}",
                f"- sources: `{check.get('source_paths')}`",
                "",
            ]
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    args = parser.parse_args(argv)
    report = build_pattern_lab_propagation_audit(args.date)
    json_path, md_path = report_paths(args.date)
    print(
        f"pattern_lab_propagation_audit status={report['status']} json={json_path} md={md_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
