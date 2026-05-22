"""Aggregate scalping pattern lab outputs into unattended improvement orders."""

from __future__ import annotations

import argparse
import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.engine.daily_threshold_cycle_report import CALIBRATION_SAFETY_GUARDS, REPORT_DIR


PROJECT_ROOT = Path(__file__).resolve().parents[2]
GEMINI_LAB_DIR = PROJECT_ROOT / "analysis" / "gemini_scalping_pattern_lab"
CLAUDE_LAB_DIR = PROJECT_ROOT / "analysis" / "claude_scalping_pattern_lab"
PATTERN_LAB_AUTOMATION_DIR = REPORT_DIR / "scalping_pattern_lab_automation"
SCALP_ENTRY_ADM_DIR = REPORT_DIR / "scalp_entry_action_decision_matrix"
AUTOMATION_SCHEMA_VERSION = 1
DECISION_AUTHORITY = "pattern_lab_analysis_workorder_source_only"
FORBIDDEN_USES = [
    "runtime_threshold_mutation",
    "broker_order_submit",
    "provider_route_change",
    "bot_restart",
    "real_order_gate",
]


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _parse_date_prefix(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    match = re.search(r"\d{4}-\d{2}-\d{2}", raw)
    return match.group(0) if match else ""


def automation_report_paths(target_date: str) -> tuple[Path, Path]:
    base = PATTERN_LAB_AUTOMATION_DIR / f"scalping_pattern_lab_automation_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _entry_adm_summary(target_date: str) -> tuple[dict[str, Any], str | None]:
    path = SCALP_ENTRY_ADM_DIR / f"scalp_entry_action_decision_matrix_{target_date}.json"
    payload = _load_json(path)
    if not payload:
        return {"available": False, "status": "missing", "runtime_effect": False}, None
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    return (
        {
            "available": True,
            "status": payload.get("status"),
            "runtime_effect": bool(payload.get("runtime_effect")),
            "decision_authority": payload.get("decision_authority"),
            "application_mode": payload.get("application_mode"),
            "total_candidates": _safe_int(summary.get("total_candidates"), 0),
            "joined_sample": _safe_int(summary.get("joined_sample"), 0),
            "sample_floor": _safe_int(summary.get("sample_floor"), 0),
            "missing_actions": summary.get("missing_actions") if isinstance(summary.get("missing_actions"), list) else [],
            "prompt_applied_count": _safe_int(summary.get("prompt_applied_count"), 0),
        },
        str(path),
    )


def _lab_output_paths(lab_dir: Path, lab_name: str) -> dict[str, Path]:
    outputs = lab_dir / "outputs"
    final_name = "final_review_report_for_lead_ai.md"
    return {
        "ev": outputs / "ev_analysis_result.json",
        "observability": outputs / "tuning_observability_summary.json",
        "manifest": outputs / "run_manifest.json",
        "final_review": outputs / final_name,
        "backlog": outputs / ("ev_improvement_backlog_for_ops.md" if lab_name == "claude" else "ev_improvement_backlog.md"),
    }


def _lab_freshness(lab_name: str, paths: dict[str, Path], target_date: str) -> dict[str, Any]:
    manifest = _load_json(paths["manifest"])
    run_date = _parse_date_prefix(manifest.get("run_at") or manifest.get("executed_at"))
    coverage_end = _parse_date_prefix(manifest.get("history_coverage_end") or manifest.get("analysis_end"))
    fresh = bool(manifest) and run_date == target_date and coverage_end == target_date
    return {
        "lab": lab_name,
        "fresh": fresh,
        "run_date": run_date or None,
        "coverage_end": coverage_end or None,
        "manifest": str(paths["manifest"]) if paths["manifest"].exists() else None,
        "final_review_exists": paths["final_review"].exists(),
        "ev_result_exists": paths["ev"].exists(),
        "observability_exists": paths["observability"].exists(),
        "stale_reason": ""
        if fresh
        else "missing_manifest_or_target_date_mismatch"
        if not manifest or run_date != target_date or coverage_end != target_date
        else "",
    }


def _slug(value: str) -> str:
    lowered = re.sub(r"[^a-zA-Z0-9가-힣]+", "_", value.strip().lower()).strip("_")
    return lowered[:80] or "unknown"


def _normalize_route(title: str) -> dict[str, str]:
    haystack = title.lower()
    if any(token in haystack for token in ("ai threshold", "wait65", "wait65~79", "score65", "submitted drought")):
        return {
            "route": "existing_family",
            "family": "score65_74_recovery_probe",
            "stage": "entry",
            "target_subsystem": "entry_funnel",
        }
    if any(token in haystack for token in ("gatekeeper latency", "latency", "quote_fresh", "lock/model")):
        return {
            "route": "instrumentation_order",
            "family": "",
            "stage": "runtime_ops",
            "target_subsystem": "runtime_instrumentation",
        }
    if any(token in haystack for token in ("soft_stop", "soft-stop", "same_symbol", "same-symbol")):
        return {
            "route": "existing_family",
            "family": "soft_stop_whipsaw_confirmation",
            "stage": "holding_exit",
            "target_subsystem": "holding_exit",
        }
    if any(token in haystack for token in ("split-entry", "split entry", "bad_entry", "rebase", "partial")):
        return {
            "route": "existing_family",
            "family": "bad_entry_refined_canary",
            "stage": "holding_exit",
            "target_subsystem": "holding_exit",
        }
    if any(token in haystack for token in ("overbought", "liquidity")):
        return {
            "route": "auto_family_candidate",
            "family": "",
            "stage": "entry",
            "target_subsystem": "entry_filter_quality",
        }
    return {
        "route": "auto_family_candidate",
        "family": "",
        "stage": "unknown",
        "target_subsystem": "scalping_logic",
    }


def _finding_from_backlog_item(lab: str, item: dict[str, Any]) -> dict[str, Any]:
    title = str(item.get("title") or item.get("제목") or "").strip()
    route = _normalize_route(title)
    return {
        "finding_id": _slug(title),
        "title": title,
        "source_lab": lab,
        "kind": "ev_backlog",
        "route": route["route"],
        "mapped_family": route["family"] or None,
        "stage": route["stage"],
        "target_subsystem": route["target_subsystem"],
        "evidence": {
            "expected_effect": item.get("기대효과") or item.get("expected_effect"),
            "risk": item.get("리스크") or item.get("risk"),
            "required_sample": item.get("필요표본") or item.get("필요 표본") or item.get("required_sample"),
            "metric": item.get("검증지표") or item.get("metric"),
            "apply_stage": item.get("적용단계") or item.get("apply_stage"),
        },
    }


def _finding_from_opportunity(lab: str, item: dict[str, Any]) -> dict[str, Any]:
    blocker = str(item.get("blocker") or "").strip()
    title = f"{blocker} EV recovery"
    route = _normalize_route(title)
    return {
        "finding_id": _slug(title),
        "title": title,
        "source_lab": lab,
        "kind": "opportunity_cost",
        "route": route["route"],
        "mapped_family": route["family"] or None,
        "stage": route["stage"],
        "target_subsystem": route["target_subsystem"],
        "evidence": {
            "total_blocked": _safe_int(item.get("total_blocked"), 0),
            "block_ratio": _safe_float(item.get("block_ratio"), 0.0),
            "days": _safe_int(item.get("days"), 0),
        },
    }


def _finding_from_priority(lab: str, item: dict[str, Any]) -> dict[str, Any]:
    title = str(item.get("label") or "").strip()
    route = _normalize_route(title)
    return {
        "finding_id": _slug(title),
        "title": title,
        "source_lab": lab,
        "kind": "priority_finding",
        "route": route["route"],
        "mapped_family": route["family"] or None,
        "stage": route["stage"],
        "target_subsystem": route["target_subsystem"],
        "evidence": {
            "judgment": item.get("judgment"),
            "why": item.get("why"),
        },
    }


def _extract_findings(lab: str, ev_result: dict[str, Any], observability: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for item in ev_result.get("ev_backlog") or []:
        if isinstance(item, dict):
            finding = _finding_from_backlog_item(lab, item)
            if finding["title"]:
                findings.append(finding)
    for item in ev_result.get("opportunity_cost") or []:
        if isinstance(item, dict):
            finding = _finding_from_opportunity(lab, item)
            if finding["title"]:
                findings.append(finding)
    for item in observability.get("priority_findings") or []:
        if isinstance(item, dict):
            finding = _finding_from_priority(lab, item)
            if finding["title"]:
                findings.append(finding)
    return findings


def _load_lab(lab_name: str, lab_dir: Path, target_date: str) -> dict[str, Any]:
    paths = _lab_output_paths(lab_dir, lab_name)
    ev_result = _load_json(paths["ev"])
    observability = _load_json(paths["observability"])
    freshness = _lab_freshness(lab_name, paths, target_date)
    findings = _extract_findings(lab_name, ev_result, observability) if freshness["fresh"] else []
    rejected = []
    if not freshness["fresh"]:
        rejected.append(
            {
                "lab": lab_name,
                "reason": freshness["stale_reason"],
                "manifest": freshness["manifest"],
                "run_date": freshness["run_date"],
                "coverage_end": freshness["coverage_end"],
            }
        )
    return {
        "lab": lab_name,
        "paths": {key: str(path) if path.exists() else None for key, path in paths.items()},
        "freshness": freshness,
        "findings": findings,
        "rejected_findings": rejected,
    }


def _merge_findings(lab_results: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    solo: list[dict[str, Any]] = []
    for result in lab_results:
        for finding in result.get("findings") or []:
            grouped.setdefault(str(finding.get("finding_id") or ""), []).append(finding)
    consensus: list[dict[str, Any]] = []
    for finding_id, items in sorted(grouped.items()):
        labs = sorted({str(item.get("source_lab")) for item in items})
        representative = items[0]
        merged = {
            "finding_id": finding_id,
            "title": representative.get("title"),
            "source_labs": labs,
            "confidence": "consensus" if len(labs) >= 2 else "solo",
            "route": representative.get("route"),
            "mapped_family": representative.get("mapped_family"),
            "stage": representative.get("stage"),
            "target_subsystem": representative.get("target_subsystem"),
            "evidence": [item.get("evidence") or {} for item in items],
        }
        if len(labs) >= 2:
            consensus.append(merged)
        else:
            solo.append(merged)
    consensus.sort(key=lambda item: (item.get("route") != "existing_family", item.get("title") or ""))
    solo.sort(key=lambda item: (item.get("route") != "instrumentation_order", item.get("title") or ""))
    return consensus, solo


def _existing_family_inputs(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for finding in findings:
        family = finding.get("mapped_family")
        if not family:
            continue
        row = rows.setdefault(
            str(family),
            {
                "family": family,
                "stage": finding.get("stage"),
                "source_findings": [],
                "runtime_effect": False,
            },
        )
        row["source_findings"].append(finding.get("finding_id"))
    return list(rows.values())


def _auto_family_candidates(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for finding in findings:
        if finding.get("route") != "auto_family_candidate":
            continue
        family_id = f"pattern_lab_{finding.get('finding_id')}"
        candidates.append(
            {
                "family_id": family_id,
                "stage": finding.get("stage") or "unknown",
                "source_labs": finding.get("source_labs") or [],
                "evidence": finding.get("evidence") or [],
                "sample_window": "rolling_10d_with_daily_guard",
                "sample_floor": 20,
                "target_metric": "daily_ev_delta_or_missed_upside_reduction",
                "safety_guard": list(CALIBRATION_SAFETY_GUARDS),
                "proposed_runtime_touchpoint": finding.get("target_subsystem") or "scalping_logic",
                "implementation_order_id": f"order_{family_id}",
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "decision_authority": DECISION_AUTHORITY,
                "candidate_role": "analysis_only_family_design_input",
                "forbidden_uses": FORBIDDEN_USES,
            }
        )
    return candidates


def _code_improvement_orders(findings: list[dict[str, Any]], solo_findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    source = list(findings) + list(solo_findings)
    orders: list[dict[str, Any]] = []
    seen: set[str] = set()
    for priority, finding in enumerate(source, start=1):
        order_id = f"order_{finding.get('finding_id')}"
        if order_id in seen:
            continue
        seen.add(order_id)
        subsystem = str(finding.get("target_subsystem") or "scalping_logic")
        files = {
            "entry_funnel": ["src/engine/daily_threshold_cycle_report.py", "src/engine/sniper_missed_entry_counterfactual.py"],
            "holding_exit": ["src/engine/daily_threshold_cycle_report.py", "src/engine/sniper_state_handlers.py"],
            "runtime_instrumentation": ["src/engine/sniper_performance_tuning_report.py", "src/engine/daily_threshold_cycle_report.py"],
            "entry_filter_quality": ["src/engine/daily_threshold_cycle_report.py", "src/engine/sniper_state_handlers.py"],
        }.get(subsystem, ["src/engine/daily_threshold_cycle_report.py"])
        orders.append(
            {
                "order_id": order_id,
                "title": str(finding.get("title") or ""),
                "target_subsystem": subsystem,
                "intent": "Generate implementation work from pattern-lab EV evidence without direct runtime mutation.",
                "evidence": finding.get("evidence") or [],
                "expected_ev_effect": "Improve EV attribution and prepare bounded calibration input.",
                "files_likely_touched": files,
                "acceptance_tests": [
                    "pytest relevant report/threshold tests",
                    "runtime_effect remains false until a separate implementation order is completed",
                    "daily EV report includes the order summary",
                ],
                "source_report_type": "scalping_pattern_lab_automation",
                "decision_authority": DECISION_AUTHORITY,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "forbidden_uses": FORBIDDEN_USES,
                "priority": priority,
            }
        )
    return orders


def build_scalping_pattern_lab_automation_report(target_date: str) -> dict[str, Any]:
    target_date = str(target_date).strip()
    lab_results = [
        _load_lab("gemini", GEMINI_LAB_DIR, target_date),
        _load_lab("claude", CLAUDE_LAB_DIR, target_date),
    ]
    consensus, solo = _merge_findings(lab_results)
    accepted_for_family = [item for item in consensus if item.get("route") in {"existing_family", "auto_family_candidate"}]
    existing_inputs = _existing_family_inputs(accepted_for_family)
    family_candidates = _auto_family_candidates(accepted_for_family)
    orders = _code_improvement_orders(consensus, solo)
    rejected = [item for result in lab_results for item in result.get("rejected_findings") or []]
    entry_adm_summary, entry_adm_path = _entry_adm_summary(target_date)
    report = {
        "schema_version": AUTOMATION_SCHEMA_VERSION,
        "date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "runtime_effect": False,
        "runtime_change": False,
        "runtime_mutation_allowed": False,
        "allowed_runtime_apply": False,
        "decision_authority": DECISION_AUTHORITY,
        "purpose": "pattern_lab_to_improvement_order_automation",
        "policy": {
            "role": "analysis_review_and_workorder_source",
            "runtime_patch_automation": False,
            "direct_family_design_authority": False,
            "downstream_route": "threshold_cycle_ev -> code_improvement_workorder -> implementation_review",
            "forbidden_uses": FORBIDDEN_USES,
        },
        "lab_freshness": {result["lab"]: result["freshness"] for result in lab_results},
        "consensus_findings": consensus,
        "solo_findings": solo,
        "existing_family_inputs": existing_inputs,
        "auto_family_candidates": family_candidates,
        "code_improvement_orders": orders,
        "rejected_findings": rejected,
        "scalp_entry_adm_summary": entry_adm_summary,
        "ev_report_summary": {
            "gemini_fresh": bool(lab_results[0]["freshness"]["fresh"]),
            "claude_fresh": bool(lab_results[1]["freshness"]["fresh"]),
            "consensus_count": len(consensus),
            "auto_family_candidate_count": len(family_candidates),
            "code_improvement_order_count": len(orders),
            "top_consensus_findings": [
                {"title": item.get("title"), "route": item.get("route"), "mapped_family": item.get("mapped_family")}
                for item in consensus[:3]
            ],
            "top_code_improvement_orders": [
                {"order_id": item.get("order_id"), "title": item.get("title"), "target_subsystem": item.get("target_subsystem")}
                for item in orders[:3]
            ],
            "scalp_entry_adm_status": entry_adm_summary.get("status"),
            "scalp_entry_adm_joined_sample": entry_adm_summary.get("joined_sample"),
            "decision_authority": DECISION_AUTHORITY,
            "runtime_mutation_allowed": False,
        },
        "sources": {
            **{result["lab"]: result["paths"] for result in lab_results},
            "scalp_entry_action_decision_matrix": entry_adm_path,
        },
    }
    PATTERN_LAB_AUTOMATION_DIR.mkdir(parents=True, exist_ok=True)
    json_path, md_path = automation_report_paths(target_date)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_scalping_pattern_lab_automation_markdown(report), encoding="utf-8")
    return report


def render_scalping_pattern_lab_automation_markdown(report: dict[str, Any]) -> str:
    summary = report.get("ev_report_summary") if isinstance(report.get("ev_report_summary"), dict) else {}
    freshness = report.get("lab_freshness") if isinstance(report.get("lab_freshness"), dict) else {}
    lines = [
        f"# Scalping Pattern Lab Automation - {report.get('date')}",
        "",
        "## Summary",
        f"- gemini_fresh: `{summary.get('gemini_fresh')}`",
        f"- claude_fresh: `{summary.get('claude_fresh')}`",
        f"- consensus_count: `{summary.get('consensus_count')}`",
        f"- auto_family_candidate_count: `{summary.get('auto_family_candidate_count')}`",
        f"- code_improvement_order_count: `{summary.get('code_improvement_order_count')}`",
        f"- scalp_entry_adm_status/joined: `{summary.get('scalp_entry_adm_status')}` / `{summary.get('scalp_entry_adm_joined_sample')}`",
        f"- runtime_effect: `{report.get('runtime_effect')}`",
        f"- decision_authority: `{report.get('decision_authority')}`",
        f"- runtime_mutation_allowed: `{report.get('runtime_mutation_allowed')}`",
        "",
        "## Consensus Findings",
    ]
    for item in (report.get("consensus_findings") or [])[:10]:
        if isinstance(item, dict):
            lines.append(
                f"- `{item.get('title')}` route=`{item.get('route')}` family=`{item.get('mapped_family') or '-'}`"
            )
    if not report.get("consensus_findings"):
        lines.append("- none")
    lines.extend(["", "## Code Improvement Orders"])
    for item in (report.get("code_improvement_orders") or [])[:10]:
        if isinstance(item, dict):
            lines.append(
                f"- `{item.get('order_id')}` {item.get('title')} subsystem=`{item.get('target_subsystem')}` runtime_effect=`{item.get('runtime_effect')}`"
            )
    if not report.get("code_improvement_orders"):
        lines.append("- none")
    stale = [
        f"{lab}:{data.get('stale_reason')}"
        for lab, data in freshness.items()
        if isinstance(data, dict) and not bool(data.get("fresh"))
    ]
    if stale:
        lines.extend(["", "## Warnings"])
        lines.extend([f"- `{item}`" for item in stale])
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Aggregate scalping pattern labs into improvement orders.")
    parser.add_argument("--date", dest="target_date", default=date.today().isoformat())
    args = parser.parse_args(argv)
    report = build_scalping_pattern_lab_automation_report(args.target_date)
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
