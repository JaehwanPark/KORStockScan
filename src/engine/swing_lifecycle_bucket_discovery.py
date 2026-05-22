"""Classify Swing LDM buckets into sim-only automation routes."""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.engine.swing_lifecycle_decision_matrix import report_paths as matrix_report_paths
from src.utils.constants import DATA_DIR


REPORT_DIR = Path(DATA_DIR) / "report" / "swing_lifecycle_bucket_discovery"
REPORT_TYPE = "swing_lifecycle_bucket_discovery"
DISCOVERY_VERSION = "swing_lifecycle_bucket_discovery_v1"
DECISION_AUTHORITY = "swing_ldm_bucket_discovery_sim_auto"
FORBIDDEN_USES = [
    "real_order_submit",
    "one_share_real_canary",
    "scale_in_real_canary",
    "provider_route_change",
    "bot_restart",
    "runtime_threshold_mutation",
]

CLASSIFICATION_STATES = {
    "sim_auto_approved",
    "source_only_keep_collecting",
    "code_patch_required",
    "runtime_blocked_contract_gap",
    "automation_handoff_gap",
}


def _date_text(value: str | date | datetime | None) -> str:
    if value is None:
        return date.today().isoformat()
    return str(value)[:10]


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _slug(value: Any) -> str:
    text = re.sub(r"[^a-zA-Z0-9가-힣]+", "_", str(value or "").strip().lower()).strip("_")
    return text[:80] or "unknown"


def report_paths(target_date: str) -> tuple[Path, Path]:
    base = REPORT_DIR / f"swing_lifecycle_bucket_discovery_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _bucket_id(stage: str, bucket_type: str, bucket_key: str) -> str:
    return f"swing_bucket_{_slug(stage)}_{_slug(bucket_type)}_{_slug(bucket_key)}"


def _classification_from_bucket(bucket: dict[str, Any]) -> str:
    route = str(bucket.get("recommended_route") or "")
    gate = str(bucket.get("source_quality_gate") or "")
    try:
        joined = int(float(bucket.get("joined_sample") or 0))
    except (TypeError, ValueError):
        joined = 0
    if route == "sim_auto_approved":
        return "sim_auto_approved"
    if route == "code_patch_required" or gate == "source_quality_blocker":
        return "code_patch_required"
    if joined <= 0 or gate == "hold_sample":
        return "source_only_keep_collecting"
    return "source_only_keep_collecting"


def _candidate_from_bucket(section_name: str, bucket: dict[str, Any]) -> dict[str, Any]:
    stage = str(bucket.get("lifecycle_stage") or "swing")
    bucket_type = str(bucket.get("bucket_type") or section_name)
    bucket_key = str(bucket.get("bucket_key") or "-")
    state = _classification_from_bucket(bucket)
    return {
        "bucket_id": _bucket_id(stage, bucket_type, bucket_key),
        "source_section": section_name,
        "lifecycle_stage": stage,
        "bucket_type": bucket_type,
        "bucket_key": bucket_key,
        "classification_state": state,
        "source_quality_gate": bucket.get("source_quality_gate"),
        "joined_sample": bucket.get("joined_sample"),
        "sample_count": bucket.get("sample_count"),
        "source_quality_adjusted_ev_pct": bucket.get("source_quality_adjusted_ev_pct"),
        "decision_authority": DECISION_AUTHORITY,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "human_approval_required": False,
        "next_route": "next_preopen_swing_sim_policy_input"
        if state == "sim_auto_approved"
        else "postclose_source_quality_or_sample_collection",
        "forbidden_uses": FORBIDDEN_USES,
    }


def _workorder_contract_fields() -> dict[str, Any]:
    return {
        "decision_authority": DECISION_AUTHORITY,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "human_approval_required": False,
        "forbidden_uses": FORBIDDEN_USES,
    }


def _normalize_explicit_workorder(item: dict[str, Any]) -> dict[str, Any]:
    return {
        **item,
        **_workorder_contract_fields(),
    }


def _ai_review_augmentation_points(*, matrix: dict[str, Any], candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not matrix:
        return []
    candidate_states = {str(item.get("classification_state") or "") for item in candidates}
    points = [
        {
            "point_id": "swing_ldm_bucket_semantic_two_pass_review",
            "stage": "bucket_discovery",
            "reason": "deterministic bucket classifications are not yet reviewed by AI interpretation/audit/final conclusion",
            "recommended_route": "code_improvement_workorder",
        },
        {
            "point_id": "swing_ldm_source_contract_ai_audit",
            "stage": "source_contract",
            "reason": "AI audit can flag explicit probe/discovery source-quality or forbidden-source contract gaps",
            "recommended_route": "code_improvement_workorder",
        },
        {
            "point_id": "swing_ldm_sim_policy_handoff_ai_audit",
            "stage": "sim_policy_handoff",
            "reason": "AI audit can verify sim_auto_approved remains sim-only and does not imply real/canary/provider/bot changes",
            "recommended_route": "code_improvement_workorder",
        },
    ]
    if "source_only_keep_collecting" in candidate_states or "code_patch_required" in candidate_states:
        points.append(
            {
                "point_id": "swing_ldm_source_quality_gap_ai_triage",
                "stage": "source_quality",
                "reason": "AI triage can summarize explicit source-quality gaps without blocking sim-only auto approval for ambiguity",
                "recommended_route": "code_improvement_workorder",
            }
        )
    return points


def _iter_attribution_sections(matrix: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    sections = []
    for name in (
        "entry_bucket_attribution",
        "holding_exit_bucket_attribution",
        "scale_in_bucket_attribution",
        "discovery_arm_attribution",
    ):
        section = matrix.get(name)
        if isinstance(section, dict):
            sections.append((name, section))
    return sections


def build_swing_lifecycle_bucket_discovery(target_date: str) -> dict[str, Any]:
    date_key = _date_text(target_date)
    matrix_json, _ = matrix_report_paths(date_key)
    matrix = _load_json(matrix_json)

    candidates: list[dict[str, Any]] = []
    explicit_workorders: list[dict[str, Any]] = []
    for section_name, section in _iter_attribution_sections(matrix):
        for bucket in section.get("buckets") or []:
            if isinstance(bucket, dict):
                candidates.append(_candidate_from_bucket(section_name, bucket))
        for item in section.get("code_improvement_workorders") or []:
            if isinstance(item, dict):
                explicit_workorders.append(item)

    by_state: dict[str, int] = defaultdict(int)
    by_stage: dict[str, int] = defaultdict(int)
    for candidate in candidates:
        by_state[str(candidate.get("classification_state"))] += 1
        by_stage[str(candidate.get("lifecycle_stage") or "-")] += 1

    source_contract_status = "missing" if not matrix else "pass"
    contract = matrix.get("input_contract") if isinstance(matrix.get("input_contract"), dict) else {}
    if contract and contract.get("swing_daily_simulation_consumed") is not False:
        source_contract_status = "fail"
        candidates.append(
            {
                "bucket_id": "swing_bucket_contract_forbidden_daily_simulation",
                "source_section": "input_contract",
                "lifecycle_stage": "source_quality",
                "bucket_type": "forbidden_source",
                "bucket_key": "swing_daily_simulation",
                "classification_state": "runtime_blocked_contract_gap",
                "decision_authority": DECISION_AUTHORITY,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "human_approval_required": False,
                "next_route": "code_improvement_workorder",
                "forbidden_uses": FORBIDDEN_USES,
            }
        )
        by_state["runtime_blocked_contract_gap"] += 1

    sim_auto = [item for item in candidates if item.get("classification_state") == "sim_auto_approved"]
    code_patch = [
        item
        for item in candidates
        if item.get("classification_state") in {"code_patch_required", "runtime_blocked_contract_gap", "automation_handoff_gap"}
    ]
    ai_review_points = _ai_review_augmentation_points(matrix=matrix, candidates=candidates)
    warnings: list[str] = []
    if not matrix:
        warnings.append("swing_lifecycle_decision_matrix_missing")
    if source_contract_status == "fail":
        warnings.append("source_contract_fail")
    if ai_review_points:
        warnings.append("swing_ldm_ai_review_not_configured")

    report = {
        "schema_version": 1,
        "report_type": REPORT_TYPE,
        "date": date_key,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "discovery_version": DISCOVERY_VERSION,
        "runtime_effect": False,
        "source_only": True,
        "decision_authority": DECISION_AUTHORITY,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "human_intervention_required": False,
        "ai_review_policy": {
            "status": "not_configured",
            "ambiguity_blocks_sim_auto_approval": False,
            "allowed_flags": ["explicit_contract_gap", "source_quality_gap"],
            "required_flow": ["interpretation", "audit", "final_conclusions"],
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        },
        "summary": {
            "status": "missing" if not matrix else "pass" if source_contract_status == "pass" else "fail",
            "source_contract_status": source_contract_status,
            "candidate_count": len(candidates),
            "surfaced_candidate_count": len(candidates),
            "sim_auto_approved_count": len(sim_auto),
            "source_only_keep_collecting_count": by_state.get("source_only_keep_collecting", 0),
            "code_patch_required_count": len(code_patch) + len(explicit_workorders) + len(ai_review_points),
            "runtime_blocked_contract_gap_count": by_state.get("runtime_blocked_contract_gap", 0),
            "automation_handoff_gap_count": by_state.get("automation_handoff_gap", 0),
            "ai_review_augmentation_point_count": len(ai_review_points),
            "state_counts": dict(by_state),
            "stage_counts": dict(by_stage),
            "human_intervention_required": False,
        },
        "ai_review_augmentation_points": ai_review_points,
        "surfaced_candidate_ids": [str(item.get("bucket_id")) for item in candidates if item.get("bucket_id")],
        "surfaced_candidates": candidates,
        "sim_auto_approved_candidates": sim_auto,
        "code_improvement_workorders": [
            {
                "workorder_id": f"swing_bucket_discovery_{_slug(item.get('bucket_id'))}",
                "bucket_id": item.get("bucket_id"),
                "classification_state": item.get("classification_state"),
                "reason": "swing_ldm_bucket_contract_or_source_quality_gap",
                "target_subsystem": "swing_lifecycle_bucket_discovery",
                **_workorder_contract_fields(),
            }
            for item in code_patch
        ]
        + [
            {
                "workorder_id": f"swing_bucket_discovery_ai_review_{_slug(item.get('point_id'))}",
                "bucket_id": item.get("point_id"),
                "classification_state": "code_patch_required",
                "reason": item.get("reason"),
                "target_subsystem": "swing_lifecycle_bucket_discovery_ai_review",
                "required_flow": ["interpretation", "audit", "final_conclusions"],
                **_workorder_contract_fields(),
            }
            for item in ai_review_points
        ]
        + [_normalize_explicit_workorder(item) for item in explicit_workorders],
        "sources": {
            "swing_lifecycle_decision_matrix": str(matrix_json) if matrix_json.exists() else None,
            "swing_daily_simulation": None,
        },
        "warnings": warnings,
    }
    return report


def render_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    lines = [
        f"# Swing Lifecycle Bucket Discovery {report.get('date')}",
        "",
        "## Summary",
        f"- runtime_effect: `{report.get('runtime_effect')}`",
        f"- decision_authority: `{report.get('decision_authority')}`",
        f"- source_contract_status: `{summary.get('source_contract_status')}`",
        f"- surfaced_candidate_count: `{summary.get('surfaced_candidate_count')}`",
        f"- sim_auto_approved_count: `{summary.get('sim_auto_approved_count')}`",
        f"- code_patch_required_count: `{summary.get('code_patch_required_count')}`",
        f"- ai_review_augmentation_point_count: `{summary.get('ai_review_augmentation_point_count')}`",
        f"- human_intervention_required: `{summary.get('human_intervention_required')}`",
        f"- warnings: `{report.get('warnings') or []}`",
        "",
        "## Surfaced Candidates",
    ]
    for item in (report.get("surfaced_candidates") or [])[:20]:
        lines.append(
            f"- `{item.get('bucket_id')}` state=`{item.get('classification_state')}` "
            f"stage=`{item.get('lifecycle_stage')}` route=`{item.get('next_route')}`"
        )
    lines.extend(["", "## AI Review Augmentation Points"])
    for item in report.get("ai_review_augmentation_points") or []:
        lines.append(
            f"- `{item.get('point_id')}` stage=`{item.get('stage')}` route=`{item.get('recommended_route')}`"
        )
    return "\n".join(lines).rstrip() + "\n"


def write_report(report: dict[str, Any]) -> tuple[Path, Path]:
    json_path, md_path = report_paths(str(report.get("date")))
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return json_path, md_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Swing lifecycle bucket discovery.")
    parser.add_argument("--date", dest="target_date", default=date.today().isoformat())
    args = parser.parse_args()
    report = build_swing_lifecycle_bucket_discovery(args.target_date)
    json_path, md_path = write_report(report)
    print(f"[swing-lifecycle-bucket-discovery] wrote {json_path} {md_path}")


if __name__ == "__main__":
    main()
