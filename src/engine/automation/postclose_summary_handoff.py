"""Read-only generation contracts for the final postclose summaries.

Owned by automation, not runtime policy. Verifier/controller outputs are deliberately
not source hashes: binding their changing generation would create a verification loop.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import date
from pathlib import Path
from typing import Any

from src.engine.automation.postclose_workorder_contract import exact_equal

SCHEMA = "postclose_summary_sources_v1"
MARKER = "POSTCLOSE_SUMMARY_SOURCES"
FUTURE_HANDOFF_SCHEMA = "direct_family_future_handoff_v1"
FUTURE_HANDOFF_MARKER = "DIRECT_FAMILY_FUTURE_HANDOFF"
COMMON_THRESHOLD_TUNING_RETIRED_FROM = "2026-09-19"


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


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
        owner = "widget" if "widget-evaluation" in unit else "machine"
        receipt_path = producer_receipt_path(report_dir, target_date, owner)
        if receipt_path.exists():
            receipt = _load_json(receipt_path)
            problems = producer_receipt_issues(report_dir, target_date, owner)
            result[unit] = ("waiting_running" if receipt.get("status") == "running" else
                            ("failed_receipt:" + ",".join(problems) if problems else "done"))
            continue
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
    summary_path = (
        report_dir
        / "runtime_approval_summary"
        / f"runtime_approval_summary_{target_date}.json"
    )
    summary = _load_json(summary_path)
    if (
        target_date >= COMMON_THRESHOLD_TUNING_RETIRED_FROM
        or summary.get("schema_version") == 3
    ):
        # PREOPEN artifacts are expected future outputs at postclose time.  A
        # later normal bootstrap must not invalidate the immutable postclose
        # generation receipt merely because its previously absent file arrived.
        paths = {"runtime_approval_summary": summary_path}
        for owner in ("widget", "machine"):
            path = producer_receipt_path(report_dir, target_date, owner)
            if path.exists():
                paths[f"independent_{owner}_terminal"] = path
        return paths
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
    if consumer == "checklist":
        paths.update(
            {
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
    if target_date >= "2026-09-17":
        paths["pipeline_event_verbosity"] = report_dir / "pipeline_event_verbosity" / f"pipeline_event_verbosity_{target_date}.json"
        paths['entry_cancel_wait_tuning'] = report_dir / 'entry_cancel_wait_tuning' / f'entry_cancel_wait_tuning_{target_date}.json'
        paths['entry_cancel_wait_policy'] = report_dir / 'entry_cancel_wait_tuning' / f'entry_cancel_wait_policy_{target_date}.json'
        from src.engine.automation.machine_research_closed_loop_refresh import (
            report_path,
        )

        paths["machine_research_closed_loop"] = report_path(report_dir, target_date)
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


def direct_future_handoff(summary: dict[str, Any], source_date: str) -> dict[str, Any]:
    preopen = (
        summary.get("preopen_consumption_receipt")
        if isinstance(summary.get("preopen_consumption_receipt"), dict)
        else {}
    )
    policies: list[dict[str, Any]] = []
    sources = summary.get("sources") if isinstance(summary.get("sources"), dict) else {}
    for owner, source in sorted(sources.items()):
        if not isinstance(source, dict):
            continue
        receipt = source.get("policy_receipt")
        if not isinstance(receipt, dict) or not receipt.get("path"):
            continue
        policies.append(
            {
                "owner": owner,
                "policy_owner": receipt.get("owner"),
                "policy_sha256": receipt.get("sha256"),
                "valid": receipt.get("valid") is True,
            }
        )
    return {
        "schema": FUTURE_HANDOFF_SCHEMA,
        "source_date": source_date,
        "apply_date": preopen.get("apply_date"),
        "expected_state": (
            "future_due"
            if preopen.get("apply_date")
            and summary.get("preopen_consumption_state") == "pending"
            else summary.get("preopen_consumption_state")
        ),
        "source_preopen_state": summary.get("preopen_consumption_state"),
        "manifest_path": preopen.get("manifest_path"),
        "verification_path": preopen.get("verification_path"),
        "policy_receipts": policies,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }


def direct_future_handoff_marker(payload: dict[str, Any]) -> str:
    return f"<!-- {FUTURE_HANDOFF_MARKER} {json.dumps(payload, sort_keys=True)} -->"


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

    summary_path = (
        report_dir
        / "runtime_approval_summary"
        / f"runtime_approval_summary_{target_date}.json"
    )
    summary = _load_json(summary_path)
    direct_mode = (
        target_date >= COMMON_THRESHOLD_TUNING_RETIRED_FROM
        or summary.get("schema_version") == 3
    )
    intake = (
        build_intake(report_dir, target_date)
        if EFFECTIVE_DATE <= target_date < COMMON_THRESHOLD_TUNING_RETIRED_FROM
        and not direct_mode
        else None
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
            if consumer == "checklist" and direct_mode:
                future_matches = re.findall(
                    rf"<!-- {FUTURE_HANDOFF_MARKER} (.+?) -->", text
                )
                if len(future_matches) != 1:
                    issues.append(
                        "postclose_summary_handoff:checklist:"
                        "future_handoff_marker_missing_or_duplicate"
                    )
                else:
                    if not exact_equal(
                        json.loads(future_matches[0]),
                        direct_future_handoff(summary, target_date),
                    ):
                        issues.append(
                            "postclose_summary_handoff:checklist:"
                            "future_handoff_semantics_mismatch"
                        )
            if intake is not None:
                if consumer == "tower":
                    if not exact_equal(payload.get("recommendation_intake"), intake):
                        issues.append(
                            "postclose_summary_handoff:tower:intake_semantics_mismatch"
                        )
                    from src.engine.automation.tuning_performance_control_tower import (
                        _load_json as _tower_load_json,
                        _selected_runtime,
                    )

                    paths = source_paths(report_dir, target_date, consumer)
                    selected = _selected_runtime(
                        _tower_load_json(paths["preopen_apply_plan"]),
                        _tower_load_json(paths["threshold_cycle_ev"]),
                        _tower_load_json(paths["preopen_runtime_manifest"]),
                        pid_receipt=_tower_load_json(paths["preopen_pid_verification"]),
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


# Independent producer receipts survive manual historical recovery and do not
# depend on systemd's most recent (possibly different-date) invocation.
INDEPENDENT_SOURCES = {
    "widget": ("widget_advisory_calibration", "widget_auto_trade_policy_calibration",
               "widget_symbol_signal_policy_research", "widget_symbol_runtime_policy_apply"),
    "machine": ("widget_collector_expansion_recommendation", "machine_microstructure_attribution",
                "machine_entry_timing_tuning", "machine_microstructure_policy_approval",
                "market_weakness_hysteresis_tuning", "machine_research_closed_loop"),
}


def producer_receipt_path(report_dir: Path, day: str, owner: str) -> Path:
    return report_dir / "postclose_producer_terminal" / f"{owner}_{day}.json"


def producer_receipt_issues(report_dir: Path, day: str, owner: str) -> list[str]:
    from src.engine.verify_threshold_cycle_postclose_chain import _sha
    value = _load_json(producer_receipt_path(report_dir, day, owner))
    if (value.get("status") != "succeeded" or value.get("target_date") != day
        or value.get("owner") != owner or type(value.get("exit_code")) is not int
        or value.get("exit_code") != 0 or not value.get("run_id")
        or not re.fullmatch(r"[0-9a-f]{40}", str(value.get("code_commit") or ""))):
        return [f"{owner}:terminal_missing_or_invalid"]
    sources = value.get("sources") or {}
    issues = []
    refreshed = {}
    if owner == "widget":
        machine = _load_json(producer_receipt_path(report_dir, day, "machine"))
        upstream = machine.get("upstream_widget") or {}
        if upstream.get("sha256") == _sha(producer_receipt_path(report_dir, day, "widget")) and not producer_receipt_issues(report_dir, day, "machine"):
            refreshed = machine.get("refreshed_widget_sources") or {}
    elif value.get("upstream_widget"):
        from src.engine.automation.machine_research_closed_loop_refresh import validate_current_receipt
        closure = sources.get("machine_research_closed_loop") or {}
        if not validate_current_receipt(_load_json(Path(closure.get("path") or "")), day):
            issues.append("machine:study_refresh_receipt_invalid")
    for label in INDEPENDENT_SOURCES[owner]:
        row = sources.get(label) or {}
        current = _sha(Path(row.get("path") or ""))
        if not row.get("sha256") or current != row["sha256"]:
            adopted = refreshed.get(label) or {}
            if (label in {"widget_symbol_signal_policy_research", "widget_symbol_runtime_policy_apply"}
                and adopted.get("origin_sha256") == row.get("sha256")
                and adopted.get("sha256") == current and current):
                continue
            issues.append(f"{owner}:source_hash_invalid:{label}")
    return issues


def _verified_machine_refresh_retry(report_dir: Path, day: str, previous: dict, issues: list[str]) -> bool:
    """Permit rebuilding a completed attempt, never infer terminal success."""
    from src.engine.verify_threshold_cycle_postclose_chain import _sha
    from src.engine.automation.machine_research_closed_loop_refresh import validate_current_receipt
    allowed = {f"widget:source_hash_invalid:{label}" for label in (
        "widget_symbol_signal_policy_research", "widget_symbol_runtime_policy_apply")}
    widget_path = producer_receipt_path(report_dir, day, "widget")
    upstream = previous.get("upstream_widget") or {}
    if (not issues or not set(issues) <= allowed or previous.get("status") not in {"failed", "succeeded"}
        or previous.get("owner") != "machine" or previous.get("target_date") != day
        or not previous.get("run_id") or type(previous.get("exit_code")) is not int
        or (previous.get("exit_code") == 0) != (previous.get("status") == "succeeded")
        or not re.fullmatch(r"[0-9a-f]{40}", str(previous.get("code_commit") or ""))
        or upstream.get("sha256") != _sha(widget_path)
        or upstream.get("sources") != _load_json(widget_path).get("sources")):
        return False
    closure_path = report_dir / "machine_research_closed_loop" / f"machine_research_closed_loop_{day}.json"
    closure = _load_json(closure_path)
    if validate_current_receipt(closure, day):
        return True
    # A main retry or a code repair can invalidate other closure dependencies.
    # Authenticate only the completed widget handoff to permit reconstruction;
    # finished/succeeded still requires a fully current closure receipt.
    from src.engine.automation.machine_research_closed_loop_refresh import validate_receipt
    from src.engine.monitoring import research_closed_loop as loop
    if not validate_receipt(closure, day):
        return False
    try:
        row = upstream["sources"]["widget_symbol_signal_policy_research"]
        source = Path(row["path"])
        if loop.digest(loop.read_object(source, limit=64 * 1024 * 1024)) != closure["dependency_sources"].get(str(source.resolve())):
            return False
        publication = closure["publications"]["widget"]
        directory = Path(publication["directory"])
        effective = date.fromisoformat(publication["effective_date"])
        manifest = loop.read_object(directory / f"research_publication_{effective}.json")
        if manifest["generation_sha256"] != publication["generation_sha256"]:
            return False
        for name in manifest["files"]:
            loop.verify_publication(directory, effective_date=effective, name=name,
                                    value=loop.read_object(directory / name, limit=32 * 1024 * 1024))
        return True
    except (OSError, ValueError, TypeError, KeyError):
        return False


def machine_input_issues(report_dir: Path, day: str) -> list[str]:
    """Cheap exact-date dependency barrier, before any costly machine stage.

    Producers retain their full schema/hash validation. Do not wait on main
    success: final main verification may itself consume machine evidence.
    """
    from src.engine.automation.postclose_recommendation_intake import _report_date
    issues = producer_receipt_issues(report_dir, day, "widget")
    if issues and _verified_machine_refresh_retry(
        report_dir, day, _load_json(producer_receipt_path(report_dir, day, "machine")), issues
    ):
        issues = []
    main = _load_json(report_dir / "threshold_cycle_postclose_status" /
                      f"threshold_cycle_postclose_{day}.status.json")
    if main.get("status") == "running":
        issues.append("main:producer_running")
    if issues:
        return issues
    for label in ("ai_decision_outcome_labels", "low_price_two_leg_expanded_candidate_research",
                  "runtime_approval_summary"):
        path = report_dir / label / f"{label}_{day}.json"
        if _report_date(_load_json(path)) != day:
            issues.append(f"{label}:exact_date_input_missing_or_invalid")
            break
    return issues


def wait_for_machine_inputs(report_dir: Path, day: str, *, timeout: float, poll: float = 30) -> int:
    import time
    deadline = time.monotonic() + max(0, timeout)
    previous = None
    while True:
        issues = machine_input_issues(report_dir, day)
        if issues != previous:
            print(json.dumps(dict(owner="machine", target_date=day,
                status="waiting_inputs" if issues else "inputs_ready", issues=issues)), flush=True)
            previous = issues
        if not issues:
            return 0
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return 75
        time.sleep(min(max(0.1, poll), remaining))


def _producer_main(argv=None) -> int:
    import argparse
    import os
    import uuid
    from datetime import date, datetime
    from zoneinfo import ZoneInfo
    from src.utils.constants import DATA_DIR, PROJECT_ROOT
    from src.engine.verify_threshold_cycle_postclose_chain import _atomic_write, _sha
    from src.engine.automation.postclose_recommendation_intake import source_paths, _report_date
    parser = argparse.ArgumentParser(description="Record existing independent postclose owner execution")
    parser.add_argument("--owner", choices=sorted(INDEPENDENT_SOURCES), required=True)
    parser.add_argument("--date", required=True, type=date.fromisoformat)
    parser.add_argument("--phase", choices=("started", "finished", "wait-inputs"), required=True)
    parser.add_argument("--source-wait-sec", type=float, default=43200)
    parser.add_argument("--exit-code", type=int, default=0)
    parser.add_argument("--reuse-widget-prefix", action="store_true")
    args = parser.parse_args(argv)
    day = args.date.isoformat()
    if args.date > datetime.now(ZoneInfo("Asia/Seoul")).date():
        parser.error("future source date is not supported")
    report_dir = DATA_DIR / "report"
    if args.phase == "wait-inputs":
        if args.owner != "machine":
            parser.error("wait-inputs is only supported for machine")
        return wait_for_machine_inputs(report_dir, day, timeout=args.source_wait_sec)
    path = producer_receipt_path(report_dir, day, args.owner)
    value = _load_json(path)
    now = datetime.now(ZoneInfo("Asia/Seoul")).isoformat()
    if args.phase == "started":
        upstream_widget = None
        if args.owner == "machine":
            widget_path = producer_receipt_path(report_dir, day, "widget")
            if widget_path.exists():
                widget_issues = producer_receipt_issues(report_dir, day, "widget")
                if widget_issues and not _verified_machine_refresh_retry(report_dir, day, value, widget_issues):
                    raise RuntimeError("machine_upstream_widget_terminal_invalid")
                upstream_widget = dict(path=str(widget_path), sha256=_sha(widget_path),
                                       sources=_load_json(widget_path)["sources"])
        reuse = None
        if args.reuse_widget_prefix:
            if args.owner != "widget" or value.get("target_date") != day or not value.get("run_id"):
                raise RuntimeError("widget_prefix_predecessor_missing")
            old_commit = str(value.get("code_commit") or "")
            if not re.fullmatch(r"[0-9a-f]{40}", old_commit):
                raise RuntimeError("widget_prefix_code_identity_invalid")
            changed = subprocess.check_output(["git", "-C", str(PROJECT_ROOT), "diff", "--name-only", old_commit, "HEAD", "--", "src"], text=True).splitlines()
            allowed = {"src/engine/monitoring/widget_symbol_signal_policy_research.py",
                       "src/engine/automation/postclose_summary_handoff.py",
                       # The advisory/auto-policy prefix does not consume the
                       # joint research allocator; signal research revalidates it.
                       "src/engine/monitoring/research_closed_loop.py",
                       "src/engine/monitoring/machine_candidate_lifecycle.py",
                       "src/engine/automation/machine_research_closed_loop_refresh.py",
                       "src/engine/monitoring/low_price_two_leg_expanded_candidate_research.py"}
            changed = [name for name in changed if not name.startswith("src/tests/")]
            if set(changed) - allowed:
                raise RuntimeError("widget_prefix_dependency_revision_requires_revalidation")
            retained = {}
            for label in INDEPENDENT_SOURCES["widget"][:2]:
                row = ((value.get("sources") or {}).get(label)
                       or ((value.get("reused_prefix") or {}).get("sources") or {}).get(label) or {})
                path_ = Path(row.get("path") or "")
                if not row.get("sha256") or _sha(path_) != row["sha256"] or _report_date(_load_json(path_)) != day:
                    raise RuntimeError("widget_prefix_source_generation_mismatch")
                retained[label] = row
            reuse = dict(run_id=value["run_id"], code_commit=old_commit, sources=retained,
                         reason="unchanged_completed_prefix_and_dependencies")
        if value:
            old = path.parent / "attempts" / f"{args.owner}_{day}_{uuid.uuid4().hex}.json"
            _atomic_write(old, json.dumps(value, indent=2) + "\n")
        value = dict(schema="postclose_producer_terminal_v1", owner=args.owner,
                     target_date=day, status="running", run_id=uuid.uuid4().hex,
                     started_at=now, code_root=str(PROJECT_ROOT),
                     code_commit=subprocess.check_output(["git", "-C", str(PROJECT_ROOT), "rev-parse", "HEAD"], text=True).strip(),
                     wrapper_pid=os.getppid(), runtime_effect=False, reused_prefix=reuse, upstream_widget=upstream_widget)
    else:
        if value.get("status") != "running" or value.get("wrapper_pid") != os.getppid():
            raise RuntimeError("producer_run_identity_mismatch")
        paths = source_paths(report_dir, day)
        sources, issues = {}, []
        for label in INDEPENDENT_SOURCES[args.owner]:
            source = paths.get(label, report_dir / label / f"{label}_{day}.json")
            payload = _load_json(source)
            sources[label] = dict(path=str(source.resolve()), sha256=_sha(source))
            if not sources[label]["sha256"] or _report_date(payload) != day:
                issues.append(f"source_missing_or_date_invalid:{label}")
        if args.owner == "machine" and value.get("upstream_widget") and args.exit_code == 0:
            from src.engine.automation.machine_research_closed_loop_refresh import validate_current_receipt
            upstream = value["upstream_widget"]
            if _sha(Path(upstream["path"])) != upstream["sha256"] or not validate_current_receipt(
                _load_json(Path(sources["machine_research_closed_loop"]["path"])), day
            ):
                issues.append("machine_widget_refresh_provenance_invalid")
            refreshed = {}
            for label, row in upstream["sources"].items():
                current = _sha(Path(row["path"]))
                if current != row["sha256"]:
                    if label not in {"widget_symbol_signal_policy_research", "widget_symbol_runtime_policy_apply"} or not current:
                        issues.append(f"unexpected_widget_source_change:{label}")
                    else:
                        refreshed[label] = dict(origin_sha256=row["sha256"], sha256=current)
            value["refreshed_widget_sources"] = refreshed
        value.update(status="succeeded" if args.exit_code == 0 and not issues else "failed",
                     exit_code=args.exit_code if args.exit_code else (1 if issues else 0),
                     sources=sources, issues=issues, finished_at=now)
    _atomic_write(path, json.dumps(value, indent=2) + "\n")
    return 0 if value["status"] != "failed" else 1


if __name__ == "__main__":
    raise SystemExit(_producer_main())
