"""Aggregate DeepSeek swing pattern lab outputs into unattended improvement orders."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.engine.daily_threshold_cycle_report import REPORT_DIR

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEEPSEEK_SWING_LAB_DIR = PROJECT_ROOT / "analysis" / "deepseek_swing_pattern_lab"
SWING_PATTERN_LAB_AUTOMATION_DIR = REPORT_DIR / "swing_pattern_lab_automation"
AUTOMATION_SCHEMA_VERSION = 1
DECISION_AUTHORITY = "swing_pattern_lab_analysis_workorder_source_only"
FORBIDDEN_USES = [
    "swing_real_order_enable",
    "one_share_real_canary",
    "scale_in_real_canary",
    "runtime_threshold_mutation",
    "provider_route_change",
    "bot_restart",
    "recommendation_history_replace",
]
MICRO_CONTEXT_SOURCE_CONTRACT_VERSION = "swing_micro_context_source_quality_v1"

SWING_TARGET_SUBSYSTEM_MAP = {
    "selection": "swing_model_selection",
    "entry": "swing_entry_funnel",
    "holding_exit": "swing_holding_exit",
    "scale_in": "swing_scale_in",
    "ofi_qi": "swing_micro_context",
}


def _load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


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


def swing_pattern_lab_automation_report_paths(target_date: str) -> tuple[Path, Path]:
    base = SWING_PATTERN_LAB_AUTOMATION_DIR / f"swing_pattern_lab_automation_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _lab_output_paths() -> dict[str, Path]:
    outputs = DEEPSEEK_SWING_LAB_DIR / "outputs"
    return {
        "analysis_result": outputs / "swing_pattern_analysis_result.json",
        "data_quality": outputs / "data_quality_report.json",
        "payload_summary": outputs / "deepseek_payload_summary.json",
        "manifest": outputs / "run_manifest.json",
        "final_review": outputs / "final_review_report_for_lead_ai.md",
        "ev_backlog": outputs / "swing_ev_improvement_backlog_for_ops.md",
    }


def _lab_freshness(paths: dict[str, Path], target_date: str) -> dict[str, Any]:
    manifest = _load_json(paths["manifest"])
    analysis_window = manifest.get("analysis_window", {}) if isinstance(manifest.get("analysis_window"), dict) else {}
    coverage_start = str(analysis_window.get("start") or manifest.get("analysis_start") or "").strip()[:10]
    coverage_end = str(analysis_window.get("end") or manifest.get("analysis_end") or "").strip()[:10]
    analysis_result_exists = paths["analysis_result"].exists()
    data_quality_exists = paths["data_quality"].exists()
    payload_summary_exists = paths["payload_summary"].exists()
    required_outputs_present = analysis_result_exists and data_quality_exists and payload_summary_exists
    invalid_outputs: list[str] = []
    if required_outputs_present:
        analysis_result = _load_json(paths["analysis_result"])
        data_quality = _load_json(paths["data_quality"])
        payload_summary = _load_json(paths["payload_summary"])
        if not isinstance(analysis_result, dict) or not analysis_result:
            invalid_outputs.append("analysis_result(empty_or_non_dict)")
        elif not isinstance(analysis_result.get("stage_findings"), list) and not isinstance(analysis_result.get("code_improvement_orders"), list):
            invalid_outputs.append("analysis_result(missing_schema_keys)")
        if not isinstance(data_quality, dict) or not data_quality:
            invalid_outputs.append("data_quality_report(empty_or_non_dict)")
        if not isinstance(payload_summary, dict) or not payload_summary:
            invalid_outputs.append("deepseek_payload_summary(empty_or_non_dict)")
        elif not isinstance(payload_summary.get("cases"), list) and not isinstance(payload_summary.get("total_cases"), (int, float)):
            invalid_outputs.append("deepseek_payload_summary(missing_schema_keys)")
    fresh = bool(manifest) and coverage_start == target_date and coverage_end == target_date and required_outputs_present and not invalid_outputs
    stale_reason_parts: list[str] = []
    if not fresh:
        if not manifest:
            stale_reason_parts.append("manifest_missing")
        else:
            if coverage_start != target_date:
                stale_reason_parts.append(f"analysis_start_mismatch(expected={target_date}, actual={coverage_start or 'none'})")
            if coverage_end != target_date:
                stale_reason_parts.append(f"analysis_end_mismatch(expected={target_date}, actual={coverage_end or 'none'})")
        if not required_outputs_present:
            missing_outputs = []
            if not analysis_result_exists:
                missing_outputs.append("analysis_result")
            if not data_quality_exists:
                missing_outputs.append("data_quality_report")
            if not payload_summary_exists:
                missing_outputs.append("deepseek_payload_summary")
            stale_reason_parts.append(f"missing_required_output:{','.join(missing_outputs)}")
        if invalid_outputs:
            stale_reason_parts.append(f"invalid_required_output:{','.join(invalid_outputs)}")
    return {
        "lab": "deepseek",
        "fresh": fresh,
        "coverage_start": coverage_start or None,
        "coverage_end": coverage_end or None,
        "manifest": str(paths["manifest"]) if paths["manifest"].exists() else None,
        "analysis_result_exists": analysis_result_exists,
        "data_quality_exists": data_quality_exists,
        "stale_reason": "; ".join(stale_reason_parts) if stale_reason_parts else "",
    }


def _classify_order(order: dict[str, Any], data_quality_warnings: list[str]) -> dict[str, Any]:
    order_id = str(order.get("order_id") or "").strip()
    title = str(order.get("title") or "").strip()
    route = str(order.get("route") or "").strip()
    lifecycle_stage = str(order.get("lifecycle_stage") or "").strip()
    mapped_family = order.get("mapped_family") or order.get("threshold_family")

    if bool(order.get("runtime_effect")):
        return {
            **order,
            "decision": "reject",
            "decision_reason": "automation order must remain runtime_effect=false",
            "automation_reentry": "Reject and regenerate source lab report.",
        }

    if route in ("defer_evidence", ""):
        return {
            **order,
            "decision": "defer_evidence",
            "decision_reason": "Evidence insufficient or carryover-only; wait for more data.",
            "automation_reentry": "Re-evaluate in next postclose pattern lab run.",
        }

    if route == "implement_now":
        return {
            **order,
            "decision": "implement_now",
            "decision_reason": "Instrumentation/provenance enhancement can improve attribution without runtime mutation.",
            "automation_reentry": "After implementation, next postclose report must show source freshness or warning reduction.",
        }

    if route in ("attach_existing_family",) and mapped_family:
        return {
            **order,
            "decision": "attach_existing_family",
            "decision_reason": "Finding maps to existing threshold family; strengthen source metrics/provenance.",
            "automation_reentry": "After implementation, calibration should include updated family input.",
        }

    if route == "design_family_candidate":
        return {
            **order,
            "decision": "design_family_candidate",
            "decision_reason": (
                "Pattern lab can only propose source-only family design input; allowed_runtime_apply remains false."
            ),
            "automation_reentry": "Create report-only family metadata and validate through Swing LDM before runtime approval review.",
        }

    return {
        **order,
        "decision": "defer_evidence",
        "decision_reason": "Route unclear; keep as deferred context.",
        "automation_reentry": "Re-check after next daily EV report.",
    }


def _extract_carryover_warnings(analysis_result: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    for finding in (analysis_result.get("stage_findings") or []):
        if not isinstance(finding, dict):
            continue
        ev = finding.get("evidence") if isinstance(finding.get("evidence"), dict) else {}
        carry = _safe_int(ev.get("blocked_carryover_unique"))
        sel = _safe_int(ev.get("blocked_selection_unique"))
        if carry > 0 and sel == 0:
            warnings.append(
                f"{finding.get('finding_id', 'unknown')}: carryover-only blocker ({carry} events); no selection-population blocker"
            )
    return warnings


def _source_quality_blocked_families(ofi_qi_quality: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(ofi_qi_quality, dict):
        return []
    group_unique_counts = (
        ofi_qi_quality.get("stale_missing_group_unique_record_counts")
        if isinstance(ofi_qi_quality.get("stale_missing_group_unique_record_counts"), dict)
        else {}
    )
    group_to_family = {
        "entry": "swing_entry_ofi_qi_execution_quality",
        "scale_in": "swing_scale_in_ofi_qi_confirmation",
    }
    blocked: list[dict[str, Any]] = []
    for group, family in group_to_family.items():
        invalid_unique_count = _safe_int(group_unique_counts.get(group), 0)
        if invalid_unique_count <= 0:
            continue
        blocked.append(
            {
                "family": family,
                "stage": group,
                "metric_role": "source_quality_gate",
                "decision_authority": DECISION_AUTHORITY,
                "window_policy": "same_day_pattern_lab_source_quality",
                "sample_floor": 1,
                "primary_decision_metric": "source_quality_gate",
                "source_quality_gate": "swing_orderbook_micro_context_ready_or_blocker_provenance_recorded",
                "source_contract_version": MICRO_CONTEXT_SOURCE_CONTRACT_VERSION,
                "source_contract_status": "implemented",
                "source_quality_blockers": [f"{group}_ofi_qi_invalid_micro_context"],
                "invalid_micro_context_unique_record_count": invalid_unique_count,
                "invalid_reason_combination_unique_record_counts": (
                    ofi_qi_quality.get("reason_combination_unique_record_counts") or {}
                ),
                "reason_counts": ofi_qi_quality.get("reason_counts") or {},
                "reason_combination_counts": ofi_qi_quality.get("reason_combination_counts") or {},
                "observer_unhealthy_overlap": ofi_qi_quality.get("observer_unhealthy_overlap") or {},
                "automation_input": True,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "forbidden_uses": FORBIDDEN_USES,
            }
        )
    return blocked


def _micro_context_source_contract(
    ofi_qi_quality: dict[str, Any],
    source_quality_blocked_families: list[dict[str, Any]],
) -> dict[str, Any]:
    required_metric_keys = (
        "sample_count",
        "stale_missing_count",
        "stale_missing_ratio",
        "reason_counts",
        "reason_combination_counts",
        "reason_combination_unique_record_counts",
        "stale_missing_group_counts",
        "stale_missing_group_unique_record_counts",
        "observer_unhealthy_overlap",
    )
    present = {key: key in ofi_qi_quality for key in required_metric_keys}
    return {
        "contract_id": "swing_micro_context_source_quality",
        "source_contract_version": MICRO_CONTEXT_SOURCE_CONTRACT_VERSION,
        "source_contract_status": "implemented" if all(present.values()) else "instrumentation_gap",
        "metric_role": "source_quality_gate",
        "decision_authority": DECISION_AUTHORITY,
        "window_policy": "same_day_pattern_lab_source_quality",
        "sample_floor": 1,
        "primary_decision_metric": "source_quality_gate",
        "source_quality_gate": "swing_orderbook_micro_context_ready_or_blocker_provenance_recorded",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "forbidden_uses": FORBIDDEN_USES,
        "required_metric_keys": list(required_metric_keys),
        "missing_metric_keys": [key for key, exists in present.items() if not exists],
        "sample_count": _safe_int(ofi_qi_quality.get("sample_count"), 0),
        "stale_missing_count": _safe_int(ofi_qi_quality.get("stale_missing_count"), 0),
        "stale_missing_ratio": _safe_float(ofi_qi_quality.get("stale_missing_ratio"), 0.0),
        "reason_counts": ofi_qi_quality.get("reason_counts") or {},
        "reason_combination_counts": ofi_qi_quality.get("reason_combination_counts") or {},
        "reason_combination_unique_record_counts": (
            ofi_qi_quality.get("reason_combination_unique_record_counts") or {}
        ),
        "stale_missing_group_counts": ofi_qi_quality.get("stale_missing_group_counts") or {},
        "stale_missing_group_unique_record_counts": (
            ofi_qi_quality.get("stale_missing_group_unique_record_counts") or {}
        ),
        "observer_unhealthy_overlap": ofi_qi_quality.get("observer_unhealthy_overlap") or {},
        "source_quality_blocked_family_count": len(source_quality_blocked_families),
        "source_quality_blocked_families": [
            {
                "family": item.get("family"),
                "stage": item.get("stage"),
                "source_quality_blockers": item.get("source_quality_blockers") or [],
                "invalid_micro_context_unique_record_count": item.get(
                    "invalid_micro_context_unique_record_count"
                ),
                "source_contract_status": item.get("source_contract_status"),
            }
            for item in source_quality_blocked_families
            if isinstance(item, dict)
        ],
    }


def _ofi_qi_instrumentation_provenance(
    order: dict[str, Any],
    ofi_qi_quality: dict[str, Any],
    source_quality_blocked_families: list[dict[str, Any]],
) -> dict[str, Any]:
    order_id = str(order.get("order_id") or "")
    if order_id != "order_swing_pattern_lab_deepseek_ofi_qi_stale_missing":
        return {}

    required_metric_keys = (
        "sample_count",
        "stale_missing_count",
        "stale_missing_ratio",
        "reason_counts",
        "reason_combination_counts",
        "reason_combination_unique_record_counts",
        "stale_missing_group_counts",
        "stale_missing_group_unique_record_counts",
        "observer_unhealthy_overlap",
    )
    present = {key: key in ofi_qi_quality for key in required_metric_keys}
    implementation_ok = all(present.values()) and isinstance(source_quality_blocked_families, list)
    checks = [
        {
            "name": "ofi_qi_quality_metric_contract",
            "status": "pass" if all(present.values()) else "fail",
            "required_keys": list(required_metric_keys),
            "missing_keys": [key for key, exists in present.items() if not exists],
        },
        {
            "name": "source_quality_blocked_family_provenance",
            "status": "pass" if isinstance(source_quality_blocked_families, list) else "fail",
            "blocked_family_count": len(source_quality_blocked_families)
            if isinstance(source_quality_blocked_families, list)
            else 0,
        },
        {
            "name": "runtime_authority_contract",
            "status": "pass",
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "decision_authority": DECISION_AUTHORITY,
        },
    ]
    return {
        "implementation_status": "implemented" if implementation_ok else "instrumentation_gap",
        "implementation_checks": checks,
        "implementation_provenance": {
            "owner": "swing_pattern_lab_automation",
            "implemented_scope": "instrumentation_report_provenance_only",
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "decision_authority": DECISION_AUTHORITY,
            "source_quality_blocked_families": source_quality_blocked_families,
            "next_postclose_metric": "swing_ofi_qi_quality_score",
        },
    }


def build_swing_pattern_lab_automation_report(target_date: str) -> dict[str, Any]:
    target_date = str(target_date).strip()
    paths = _lab_output_paths()
    freshness = _lab_freshness(paths, target_date)

    analysis_result = _load_json(paths["analysis_result"])
    data_quality = _load_json(paths["data_quality"])
    payload_summary = _load_json(paths["payload_summary"])

    dq_warnings = data_quality.get("warnings", []) if isinstance(data_quality.get("warnings"), list) else []
    ofi_qi_quality = data_quality.get("ofi_qi_quality") if isinstance(data_quality.get("ofi_qi_quality"), dict) else {}
    source_quality_blocked_families = _source_quality_blocked_families(ofi_qi_quality)
    micro_context_contract = _micro_context_source_contract(ofi_qi_quality, source_quality_blocked_families)
    carryover_warnings = _extract_carryover_warnings(analysis_result)

    if freshness["fresh"]:
        findings = analysis_result.get("stage_findings", []) if isinstance(analysis_result.get("stage_findings"), list) else []
        raw_orders = analysis_result.get("code_improvement_orders", []) if isinstance(analysis_result.get("code_improvement_orders"), list) else []
        data_quality_carryover_raw: list[str] = []
    else:
        findings = []
        raw_orders = []
        data_quality_carryover_raw = list(carryover_warnings)
        carryover_warnings = []
        dq_warnings.append(f"swing_lab_stale: lab output blocked because {freshness['stale_reason']}")

    classified_orders = [_classify_order(order, dq_warnings) for order in raw_orders]
    selected_orders = [o for o in classified_orders if o.get("decision") not in ("reject", "defer_evidence")]
    all_orders = [o for o in classified_orders if o.get("decision") != "reject"]

    decision_counts: dict[str, int] = {}
    for o in classified_orders:
        d = str(o.get("decision") or "unknown")
        decision_counts[d] = decision_counts.get(d, 0) + 1

    report = {
        "schema_version": AUTOMATION_SCHEMA_VERSION,
        "report_type": "swing_pattern_lab_automation",
        "date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "owner": "DeepSeekSwingPatternLabAutomation",
        "runtime_effect": False,
        "runtime_change": False,
        "runtime_mutation_allowed": False,
        "allowed_runtime_apply": False,
        "decision_authority": DECISION_AUTHORITY,
        "policy": {
            "role": "analysis_review_source_quality_and_workorder_source",
            "runtime_patch_automation": False,
            "direct_family_design_authority": False,
            "downstream_route": "threshold_cycle_ev -> code_improvement_workorder -> implementation_review",
            "swing_lifecycle_owner": "swing_lifecycle_decision_matrix",
            "user_intervention_point": "generated code improvement workorder is pasted into Codex manually",
            "forbidden_uses": FORBIDDEN_USES,
        },
        "source_reports": {
            "swing_pattern_analysis_result": str(paths["analysis_result"]),
            "data_quality_report": str(paths["data_quality"]),
            "deepseek_payload_summary": str(paths["payload_summary"]),
        },
        "ev_report_summary": {
            "deepseek_lab_available": freshness["fresh"],
            "stale_reason": freshness["stale_reason"] or None,
            "findings_count": len(findings),
            "code_improvement_order_count": len(selected_orders),
            "data_quality_warning_count": len(dq_warnings),
            "carryover_warning_count": len(carryover_warnings),
            "population_split_available": freshness["fresh"],
            "source_quality_blocked_family_count": len(source_quality_blocked_families),
            "source_quality_blocked_families": source_quality_blocked_families,
            "source_quality_contracts": {
                "swing_micro_context": micro_context_contract,
            },
            "decision_authority": DECISION_AUTHORITY,
            "runtime_mutation_allowed": False,
        },
        "consensus_findings": [
            {
                "finding_id": f.get("finding_id"),
                "title": f.get("title"),
                "confidence": f.get("confidence", "solo"),
                "route": f.get("route"),
                "mapped_family": f.get("mapped_family"),
                "lifecycle_stage": f.get("lifecycle_stage"),
                "target_subsystem": SWING_TARGET_SUBSYSTEM_MAP.get(f.get("lifecycle_stage", ""), "swing_logic"),
            }
            for f in findings
            if isinstance(f, dict)
        ],
        "auto_family_candidates": [
            {
                "family_id": f"swing_pattern_lab_{f.get('finding_id', '')}",
                "lifecycle_stage": f.get("lifecycle_stage"),
                "source_labs": ["deepseek"],
                "evidence": [f.get("evidence") or {}],
                "sample_window": "rolling_10d_with_daily_guard",
                "sample_floor": 5,
                "target_metric": "daily_ev_delta_or_missed_upside_reduction",
                "proposed_runtime_touchpoint": SWING_TARGET_SUBSYSTEM_MAP.get(f.get("lifecycle_stage", ""), "swing_logic"),
                "implementation_order_id": f"order_{f.get('finding_id', '')}",
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "decision_authority": DECISION_AUTHORITY,
                "candidate_role": "analysis_only_family_design_input",
                "forbidden_uses": FORBIDDEN_USES,
            }
            for f in findings
            if isinstance(f, dict) and f.get("route") == "design_family_candidate"
        ],
        "code_improvement_orders": [
            {
                "order_id": o.get("order_id"),
                "title": o.get("title"),
                "target_subsystem": o.get("target_subsystem"),
                "source_report_type": "swing_pattern_lab_automation",
                "lifecycle_stage": o.get("lifecycle_stage"),
                "threshold_family": o.get("threshold_family") or o.get("mapped_family"),
                "improvement_type": o.get("improvement_type", "pattern_lab_observation"),
                "priority": o.get("priority"),
                "decision": o.get("decision"),
                "decision_reason": o.get("decision_reason"),
                "route": o.get("route"),
                "mapped_family": o.get("mapped_family"),
                "intent": o.get("intent"),
                "expected_ev_effect": o.get("expected_ev_effect"),
                "evidence": o.get("evidence") or [],
                "next_postclose_metric": o.get("next_postclose_metric"),
                "files_likely_touched": o.get("files_likely_touched") or [],
                "acceptance_tests": o.get("acceptance_tests") or [],
                "automation_reentry": o.get("automation_reentry"),
                "decision_authority": DECISION_AUTHORITY,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "forbidden_uses": FORBIDDEN_USES,
                **_ofi_qi_instrumentation_provenance(o, ofi_qi_quality, source_quality_blocked_families),
            }
            for o in all_orders
            if isinstance(o, dict)
        ],
        "data_quality": {
            "warnings": dq_warnings,
            "ofi_qi_quality": ofi_qi_quality,
            "source_quality_contracts": {
                "swing_micro_context": micro_context_contract,
            },
            "source_quality_blocked_families": source_quality_blocked_families,
            "carryover_warnings": carryover_warnings,
            "carryover_warnings_raw": data_quality_carryover_raw,
            "denominator_warnings": carryover_warnings,
        },
        "warnings": dq_warnings + carryover_warnings,
    }

    SWING_PATTERN_LAB_AUTOMATION_DIR.mkdir(parents=True, exist_ok=True)
    json_path, md_path = swing_pattern_lab_automation_report_paths(target_date)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(report), encoding="utf-8")

    return report


def _render_markdown(report: dict[str, Any]) -> str:
    summary = report.get("ev_report_summary", {}) or {}
    lines = [
        f"# Swing Pattern Lab Automation - {report.get('date')}",
        "",
        "## Summary",
        f"- deepseek_lab_available: `{summary.get('deepseek_lab_available')}`",
        f"- findings_count: `{summary.get('findings_count')}`",
        f"- code_improvement_order_count: `{summary.get('code_improvement_order_count')}`",
        f"- data_quality_warning_count: `{summary.get('data_quality_warning_count')}`",
        f"- carryover_warning_count: `{summary.get('carryover_warning_count')}`",
        f"- runtime_change: `{report.get('runtime_change')}`",
        f"- decision_authority: `{report.get('decision_authority')}`",
        f"- runtime_mutation_allowed: `{report.get('runtime_mutation_allowed')}`",
        "",
        "## Consensus Findings",
    ]
    for item in (report.get("consensus_findings") or [])[:10]:
        if isinstance(item, dict):
            lines.append(
                f"- `{item.get('finding_id')}` route=`{item.get('route')}` family=`{item.get('mapped_family') or '-'}` stage=`{item.get('lifecycle_stage')}`"
            )
    if not report.get("consensus_findings"):
        lines.append("- none")
    lines.extend(["", "## Code Improvement Orders"])
    for item in (report.get("code_improvement_orders") or [])[:10]:
        if isinstance(item, dict):
            lines.append(
                f"- `{item.get('order_id')}` {item.get('title')} decision=`{item.get('decision')}` subsystem=`{item.get('target_subsystem')}` runtime_effect=`{item.get('runtime_effect')}`"
            )
    if not report.get("code_improvement_orders"):
        lines.append("- none")
    ofi_qi_quality = report.get("data_quality", {}).get("ofi_qi_quality") if isinstance(report.get("data_quality"), dict) else {}
    if ofi_qi_quality:
        lines.extend(
            [
                "",
                "## OFI/QI Quality",
                f"- stale_missing_ratio: `{ofi_qi_quality.get('stale_missing_ratio', 0.0)}`",
                f"- stale_missing_unique_record_count: `{ofi_qi_quality.get('stale_missing_unique_record_count', 0)}`",
                f"- reason_counts: `{ofi_qi_quality.get('reason_counts', {})}`",
                f"- reason_combination_counts: `{ofi_qi_quality.get('reason_combination_counts', {})}`",
                f"- reason_combination_unique_record_counts: `{ofi_qi_quality.get('reason_combination_unique_record_counts', {})}`",
                f"- stale_missing_group_counts: `{ofi_qi_quality.get('stale_missing_group_counts', {})}`",
                f"- stale_missing_group_unique_record_counts: `{ofi_qi_quality.get('stale_missing_group_unique_record_counts', {})}`",
                f"- observer_unhealthy_overlap: `{ofi_qi_quality.get('observer_unhealthy_overlap', {})}`",
                f"- source_quality_blocked_families: `{summary.get('source_quality_blocked_families', [])}`",
            ]
        )
    if report.get("data_quality", {}).get("carryover_warnings"):
        lines.extend(["", "## Carryover Warnings"])
        for w in report["data_quality"]["carryover_warnings"]:
            lines.append(f"- {w}")
    stale_reason = summary.get("stale_reason")
    if stale_reason:
        lines.extend(["", "## Stale Warning", f"- {stale_reason}"])
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Aggregate DeepSeek swing pattern lab into improvement orders.")
    parser.add_argument("--date", dest="target_date", default=date.today().isoformat())
    args = parser.parse_args(argv)
    report = build_swing_pattern_lab_automation_report(args.target_date)
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
