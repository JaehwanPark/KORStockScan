"""Read-only generation contracts for the final postclose summaries.

Owned by automation, not runtime policy. Verifier/controller outputs are deliberately
not source hashes: binding their changing generation would create a verification loop.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

SCHEMA = "postclose_summary_sources_v1"
MARKER = "POSTCLOSE_SUMMARY_SOURCES"


def source_paths(report_dir: Path, target_date: str, consumer: str) -> dict[str, Path]:
    labels = {
        "tower": (
            "threshold_cycle_ev",
            "code_improvement_workorder",
            "runtime_approval_summary",
            "runtime_apply_gap_audit",
            "observation_source_quality_audit",
            "key_lineage_ledger",
            "conversion_lane",
        ),
        "checklist": (
            "threshold_cycle_ev",
            "code_improvement_workorder",
            "runtime_apply_gap_audit",
            "automation_chain_trigger_decision",
            "rising_missed_scout_workorder",
            "tuning_performance_control_tower",
        ),
    }[consumer]
    paths = {
        label: report_dir / label / f"{label}_{target_date}.json" for label in labels
    }
    # The recheck policy producer is an acyclic source, distinct from the DONE controller.
    from src.engine.automation.drought_handoff import (
        EFFECTIVE_DATE,
        CONTROLLER,
        report_path,
    )

    if target_date >= EFFECTIVE_DATE:
        paths[CONTROLLER] = report_path(report_dir, CONTROLLER, target_date)
    if consumer == "checklist":
        paths.update(
            {
                "main_ai_quality_r0_r3": report_dir
                / "main_ai_quality_r0_r3"
                / f"main_ai_quality_r0_r3_cycle_{target_date}.json",
                "machine_microstructure_policy_approval": report_dir
                / "machine_microstructure_policy_approval"
                / f"machine_microstructure_policy_approval_postclose_{target_date}.json",
                "machine_microstructure_attribution": report_dir
                / "machine_microstructure_attribution"
                / f"machine_microstructure_attribution_{target_date}.json",
            }
        )
    return paths


def source_receipt(paths: dict[str, Path], target_date: str) -> dict[str, Any]:
    sources = {}
    for label, path in paths.items():
        try:
            raw = path.read_bytes()
        except FileNotFoundError:
            raw = None
        # Missing optional inputs are explicit, so a later arriving input invalidates
        # the summary. Permission/I/O errors must not look like optional absence.
        sources[label] = {
            "sha256": hashlib.sha256(raw).hexdigest() if raw is not None else None,
        }
    return {
        "schema": SCHEMA,
        "source_date": target_date,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "sources": sources,
    }


def assert_sources_unchanged(receipt: dict[str, Any], paths: dict[str, Path]) -> None:
    if receipt != source_receipt(paths, receipt["source_date"]):
        raise RuntimeError("postclose_summary_sources_changed_during_render")


def checklist_marker(receipt: dict[str, Any]) -> str:
    return f"<!-- {MARKER} {json.dumps(receipt, sort_keys=True)} -->"


def verify_summary_handoff(
    target_date: str,
    *,
    report_dir: Path,
    checklist_path: Path,
    require_tower: bool = True,
    require_checklist: bool = True,
) -> dict[str, Any]:
    issues = []
    checked = []
    for consumer, required in (
        ("tower", require_tower),
        ("checklist", require_checklist),
    ):
        if not required:
            continue
        checked.append(consumer)
        try:
            if consumer == "tower":
                path = (
                    report_dir
                    / "tuning_performance_control_tower"
                    / f"tuning_performance_control_tower_{target_date}.json"
                )
                payload = json.loads(path.read_text(encoding="utf-8"))
                receipt = payload.get("source_generation_contract")
                if payload.get("date") != target_date:
                    raise ValueError("target date mismatch")
            else:
                text = checklist_path.read_text(encoding="utf-8")
                matches = re.findall(rf"<!-- {MARKER} (.+?) -->", text)
                if len(matches) != 1:
                    raise ValueError("missing or duplicate generation marker")
                receipt = json.loads(matches[0])
            expected = source_receipt(
                source_paths(report_dir, target_date, consumer), target_date
            )
            if receipt != expected:
                issues.append(
                    f"postclose_summary_handoff:{consumer}:source_generation_mismatch"
                )
        except (OSError, ValueError, TypeError, AttributeError):
            issues.append(
                f"postclose_summary_handoff:{consumer}:missing_or_invalid_contract"
            )
    return {
        "status": "fail" if issues else "pass",
        "issues": issues,
        "checked_consumers": checked,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }
