"""Read-only generation contracts for the final postclose summaries.

Owned by automation, not runtime policy. Verifier/controller outputs are deliberately
not source hashes: binding their changing generation would create a verification loop.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from src.engine.automation.postclose_workorder_contract import exact_equal

SCHEMA = "postclose_summary_sources_v1"
MARKER = "POSTCLOSE_SUMMARY_SOURCES"


def installed_producer_terminal_states(
    target_date: str, *, runner=None, report_dir: Path | None = None
) -> dict[str, str]:
    """Read installed independent owners before the last summary closure.

    A running producer is a bounded wait, not failure. Explicitly masked units
    are operational OFF evidence; merely disabled timers are not successful runs.
    """
    from src.engine.automation.postclose_recommendation_intake import (
        _read,
        _report_date,
        source_paths as intake_source_paths,
    )

    if report_dir is None:
        from src.utils.constants import DATA_DIR

        report_dir = DATA_DIR / "report"
    paths = intake_source_paths(report_dir, target_date)
    runner = runner or subprocess.run
    result = {}
    owner_sources = {
        "korstockscan-samsung-widget-evaluation.service": (
            "widget_advisory_calibration",
            "widget_auto_trade_policy_calibration",
            "widget_symbol_signal_policy_research",
            "widget_symbol_runtime_policy_apply",
        ),
        "korstockscan-machine-microstructure-final-refresh.service": (
            "widget_collector_expansion_recommendation",
            "machine_microstructure_attribution",
            "machine_entry_timing_tuning",
            "machine_microstructure_policy_approval",
        ),
    }
    for unit, labels in owner_sources.items():
        try:
            command = runner(
                [
                    "systemctl",
                    "show",
                    unit,
                    "--no-pager",
                    "--property="
                    "LoadState,UnitFileState,ActiveState,Result,ExecMainStartTimestamp",
                ],
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )
            properties = dict(
                line.split("=", 1)
                for line in command.stdout.splitlines()
                if "=" in line
            )
            active = properties.get("ActiveState")
            started = re.search(
                r"\b\d{4}-\d{2}-\d{2}\b",
                properties.get("ExecMainStartTimestamp", ""),
            )
            if command.returncode or properties.get("LoadState") not in {
                "loaded",
                "masked",
            }:
                state = "failed_installed_owner_contract"
            elif active in {"activating", "active", "deactivating", "reloading"}:
                state = "waiting_running"
            elif (
                properties.get("LoadState") == "masked"
                or properties.get("UnitFileState") == "masked"
            ):
                state = (
                    "done_off_masked"  # Explicit operator OFF, never strategy approval.
                )
            elif not started or started.group() < target_date:
                state = "waiting_exact_date_run"
            elif active == "inactive" and properties.get("Result") == "success":
                state = "done"
                for label in labels:
                    payload, _, read_status = _read(paths[label])
                    if read_status is not None or _report_date(payload) != target_date:
                        state = f"failed_exact_source_artifact:{label}"
                        break
            else:
                state = "failed_producer_terminal"
        except (OSError, subprocess.TimeoutExpired, ValueError):
            state = "failed_installed_owner_check"
        result[unit] = state
    return result


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
            # Route/session/venue provenance is emitted by the lineage and
            # conversion-lane reports.  Bind both consumers to their hashes so a
            # checklist marker cannot remain current after either input changes.
            "key_lineage_ledger",
            "conversion_lane",
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
    from src.engine.automation.postclose_recommendation_intake import (
        EFFECTIVE_DATE,
        source_paths as intake_source_paths,
    )

    if target_date >= EFFECTIVE_DATE:
        paths.update(intake_source_paths(report_dir, target_date))
        data_dir = report_dir.parent
        paths["preopen_apply_plan"] = (
            data_dir
            / "threshold_cycle"
            / "apply_plans"
            / f"threshold_apply_{target_date}.json"
        )
        paths["preopen_runtime_manifest"] = (
            data_dir
            / "threshold_cycle"
            / "runtime_env"
            / f"threshold_runtime_env_{target_date}.json"
        )
        paths["preopen_pid_verification"] = (
            data_dir
            / "threshold_cycle"
            / "runtime_env"
            / f"threshold_runtime_env_verify_{target_date}.json"
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
    if not exact_equal(receipt, source_receipt(paths, receipt["source_date"])):
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
    from src.engine.automation.postclose_recommendation_intake import (
        EFFECTIVE_DATE,
        SECTION_START,
        SECTION_END,
        build_intake,
        markdown_section,
    )

    intake = (
        build_intake(report_dir, target_date) if target_date >= EFFECTIVE_DATE else None
    )
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
            if not exact_equal(receipt, expected):
                issues.append(
                    f"postclose_summary_handoff:{consumer}:source_generation_mismatch"
                )
            if intake is not None:
                if consumer == "tower":
                    if not exact_equal(payload.get("recommendation_intake"), intake):
                        issues.append(
                            "postclose_summary_handoff:tower:intake_semantics_mismatch"
                        )
                    from src.engine.automation.tuning_performance_control_tower import (
                        _load_json,
                        _selected_runtime,
                    )

                    paths = source_paths(report_dir, target_date, consumer)
                    selected = _selected_runtime(
                        _load_json(paths["preopen_apply_plan"]),
                        _load_json(paths["threshold_cycle_ev"]),
                        _load_json(paths["preopen_runtime_manifest"]),
                        pid_receipt=_load_json(paths["preopen_pid_verification"]),
                        target_date=target_date,
                    )
                    if not exact_equal(payload.get("selected_runtime"), selected):
                        issues.append(
                            "postclose_summary_handoff:tower:runtime_selection_semantics_mismatch"
                        )
                elif (
                    text.count(SECTION_START) != 1
                    or text.count(SECTION_END) != 1
                    or markdown_section(intake).rstrip() not in text
                ):
                    issues.append(
                        "postclose_summary_handoff:checklist:intake_semantics_mismatch"
                    )
        except (OSError, ValueError, TypeError, AttributeError):
            issues.append(
                f"postclose_summary_handoff:{consumer}:missing_or_invalid_contract"
            )
    if intake is not None and intake["issues"]:
        issues.append(
            "postclose_summary_handoff:intake:source_or_disposition_contract_invalid"
        )
    return {
        "status": "fail" if issues else "pass",
        "issues": issues,
        "checked_consumers": checked,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "recommendation_intake": (
            {
                key: intake[key]
                for key in (
                    "status",
                    "counts",
                    "issues",
                    "missing_sources",
                    "rows_sha256",
                    "implementation_fixed_point",
                    "all_implementations_completed",
                )
            }
            if intake is not None
            else {"status": "legacy_not_required"}
        ),
    }
