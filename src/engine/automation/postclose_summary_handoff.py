"""Stage dispatch and generation contracts for final postclose summaries.

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
    if any(stage_path(report_dir, target_date, s).exists() for s in STAGE_REGISTRY):
        result = {}
        for owner, stages in STAGE_OWNER_GROUPS.items():
            checks = [issue for stage in stages for issue in stage_receipt_issues(report_dir, target_date, stage)]
            running = any(_load_json(stage_path(report_dir, target_date, stage)).get('status') in {'running','pending'} for stage in stages)
            result['stage_group:' + owner] = 'waiting_running' if running else 'failed_receipt:' + ','.join(checks) if checks else 'done'
        return result
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
        if any(stage_path(report_dir, target_date, s).exists() for s in STAGE_REGISTRY):
            paths.update({f'stage_{stage}':stage_path(report_dir, target_date, stage)
                for stage in STAGE_REGISTRY if stage != 'summary_handoff'})
            return paths
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
    if any(stage_path(report_dir, day, s).exists() for s in STAGE_REGISTRY):
        return [issue for stage in STAGE_OWNER_GROUPS[owner] for issue in stage_receipt_issues(report_dir, day, stage)]
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


# Stage registry is shared by dispatch, summary, verifier and controller. Legacy
# v1 terminals remain readable, but never synthesize a successful v2 stage.
STAGE_SCHEMA = 'postclose_stage_terminal_v2'
STAGE_REGISTRY = {
    'main_machine_policy': ((), ('machine_policy', 'machine_policy_terminal')),
    'main_auxiliary_policy': (('outcome_labels',), ('compact_auxiliary_paired_economic',)),
    'legacy_machine_report': ((), ('ai_decision_action_outcome_calibration',)),
    'outcome_labels': ((), ('ai_decision_outcome_labels',)),
    'widget_policy': ((), ('widget_advisory_calibration', 'widget_auto_trade_policy_calibration', 'widget_symbol_signal_policy_research', 'widget_symbol_runtime_policy_apply', 'widget_policy_refresh')),
    'episode_policy': ((), ('low_price_two_leg_expanded_candidate_research', 'episode_policy_refresh')),
    'collector_recommendation': (('outcome_labels',), ('widget_collector_expansion_recommendation',)),
    'machine_attribution': ((), ('machine_microstructure_attribution',)),
    'machine_timing': (('machine_attribution',), ('machine_entry_timing_tuning',)),
    'market_weakness': ((), ('market_weakness_hysteresis_tuning',)),
    'research_capacity': ((), ('research_native_capacity',)),
    'research_allocation': (('widget_policy', 'episode_policy', 'research_capacity'), ('machine_research_closed_loop',)),
    'legacy_policy_approval': (('machine_attribution',), ('machine_microstructure_policy_approval',)),
    'summary_handoff': ((), ('postclose_done_controller',)),
}
STAGE_OWNER_GROUPS = {
    'widget': ('widget_policy',),
    'machine': ('collector_recommendation', 'machine_attribution', 'machine_timing',
                'market_weakness', 'research_allocation', 'legacy_policy_approval',
                'main_machine_policy', 'main_auxiliary_policy', 'legacy_machine_report', 'outcome_labels', 'episode_policy', 'research_capacity'),
}


def stage_path(report_dir, day, stage):
    if stage not in STAGE_REGISTRY:
        raise ValueError('unknown_postclose_stage')
    return Path(report_dir) / 'postclose_stage_terminal' / day / f'{stage}.json'


def stage_artifacts(report_dir, day, stage):
    from src.engine.automation.postclose_recommendation_intake import source_paths as catalog
    paths = catalog(Path(report_dir), day)
    for label in ('machine_policy', 'machine_policy_terminal', 'compact_auxiliary_paired_economic'):
        folder = 'ai_entry_setup_paired_replay_batch' if label.startswith('compact') else 'ai_decision_action_outcome_calibration'
        paths[label] = Path(report_dir) / folder / f'{label}_{day}.json'
    paths['research_native_capacity'] = Path(report_dir).parent / 'runtime' / 'machine_research_closed_loop' / f'capacity_source_{day}.json'
    paths['widget_policy_refresh'] = Path(report_dir) / 'machine_research_closed_loop' / f'widget_policy_refresh_{day}.json'
    paths['episode_policy_refresh'] = Path(report_dir) / 'machine_research_closed_loop' / f'episode_policy_refresh_{day}.json'
    return {name: paths.get(name, Path(report_dir) / name / f'{name}_{day}.json') for name in STAGE_REGISTRY[stage][1]}


def _stage_digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()


def _stage_sources(paths):
    result = {}
    for name, path in paths.items():
        path = Path(path)
        try:
            before = path.stat()
            h = hashlib.sha256()
            with path.open('rb') as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b''):
                    h.update(block)
            after = path.stat()
            if (before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns):
                raise ValueError('stage_source_changed_during_read')
            result[name] = dict(path=str(path.resolve()), sha256=h.hexdigest())
        except FileNotFoundError:
            result[name] = dict(path=str(path.resolve()), sha256=None)
    return result


def _stage_write(path, value):
    from src.engine.verify_threshold_cycle_postclose_chain import _atomic_write
    value = {k:v for k,v in value.items() if k != 'receipt_sha256'}
    value['receipt_sha256'] = _stage_digest(value)
    _atomic_write(path, json.dumps(value, indent=2) + '\n')
    return value


def stage_receipt_issues(report_dir, day, stage, *, code_hash=None):
    value = _load_json(stage_path(report_dir, day, stage))
    if (value.get('schema') != STAGE_SCHEMA or value.get('stage_id') != stage
        or value.get('source_date') != day or not value.get('run_id')
        or value.get('receipt_sha256') != _stage_digest({k:v for k,v in value.items() if k != 'receipt_sha256'})):
        return [f'{stage}:terminal_missing_or_invalid']
    if value.get('status') == 'off' and value.get('off_reason') == 'explicit_schedule_disabled':
        return []
    if value.get('status') != 'succeeded' or value.get('exit_code') != 0:
        return [f'{stage}:{value.get("status")}']
    if code_hash is None:
        code_hash = _stage_code(stage, stage_commands(stage, day, value.get('publication_date') or day, recovery=value.get('recovery_mode', False)), Path(__file__).resolve().parents[3])
    if value.get('stage_code_sha256') != code_hash:
        return [f'{stage}:code_changed']
    expected = stage_artifacts(report_dir, day, stage)
    if set(value.get('sources', {})) != set(expected):
        return [f'{stage}:source_set_invalid']
    if value['sources'] != _stage_sources(expected) or any(not r['sha256'] for r in value['sources'].values()):
        return [f'{stage}:output_generation_changed']
    prerequisites = {s:str(stage_path(report_dir, day, s)) for s in STAGE_REGISTRY[stage][0]}
    if value.get('prerequisite_receipts') != _stage_sources(prerequisites):
        return [f'{stage}:prerequisite_generation_changed']
    if value.get('input_sources') != _stage_sources(stage_input_paths(report_dir, day, stage)):
        return [f'{stage}:input_generation_changed']
    return _safe_stage_output_issues(report_dir, day, stage)


def stage_input_paths(report_dir, day, stage):
    paths = {s:stage_path(report_dir, day, s) for s in STAGE_REGISTRY[stage][0]}
    if stage in {'collector_recommendation', 'outcome_labels'}:
        paths['labels'] = Path(report_dir) / 'ai_decision_outcome_labels' / f'ai_decision_outcome_labels_{day}.json'
        paths['payloads'] = Path(report_dir).parent / 'ai_decision_payloads' / f'ai_decision_payloads_{day}.jsonl'
    if stage == 'outcome_labels': paths.pop('labels', None)
    return paths


def _stage_output_issues(report_dir, day, stage):
    from src.engine.automation.postclose_recommendation_intake import _report_date
    errors = []
    for name, path in stage_artifacts(report_dir, day, stage).items():
        value = _load_json(path)
        if not value or (_report_date(value) or value.get('source_date') or value.get('end_date')) != day:
            errors.append(f'{stage}:invalid_output:{name}')
        elif str(value.get('status', '')).lower() in {'failed', 'error', 'running', 'waiting', 'searching_train', 'pending'}:
            errors.append(f'{stage}:incomplete_output:{name}')
        if name == 'machine_policy_terminal' and value.get('status') != 'completed':
            errors.append(f'{stage}:search_incomplete')
        if name in {'machine_policy', 'machine_policy_terminal'}:
            from src.engine.scalping.ai_action_outcome_calibration import _artifact_content_sha256_valid
            if not _artifact_content_sha256_valid(value):
                errors.append(f'{stage}:artifact_hash_invalid')
        if name == 'ai_decision_outcome_labels':
            from datetime import datetime
            from zoneinfo import ZoneInfo
            generated = datetime.fromisoformat(str(value.get('generated_at')))
            if (value.get('schema') != 'ai_decision_outcome_labels_v1' or not isinstance(value.get('labels'), list)
                or value.get('status') not in {'mature_label_rows_available','partial_horizons_keep_maturing'}
                or generated.tzinfo is None or generated.astimezone(ZoneInfo('Asia/Seoul')) < datetime.fromisoformat(day + 'T20:00:00+09:00')):
                errors.append(f'{stage}:label_contract_invalid')
        if name in {'episode_policy_refresh', 'widget_policy_refresh'}:
            from src.engine.monitoring.research_closed_loop import digest, read_object
            if (value.get('receipt_sha256') != digest({k:v for k,v in value.items() if k != 'receipt_sha256'})
                or value.get('source_sha256') != digest(read_object(Path(value.get('source_path') or ''), limit=32*1024*1024))
                or value.get('policy_sha256') != digest(read_object(Path(value.get('policy_path') or ''), limit=32*1024*1024))):
                errors.append(f'{stage}:family_publication_invalid')
        if name == 'machine_research_closed_loop':
            from src.engine.automation.machine_research_closed_loop_refresh import validate_current_receipt
            if not validate_current_receipt(value, day):
                errors.append(f'{stage}:allocation_receipt_invalid')
    if stage == 'main_machine_policy':
        paths = stage_artifacts(report_dir, day, stage)
        report, terminal = _load_json(paths['machine_policy']), _load_json(paths['machine_policy_terminal'])
        if (terminal.get('report_sha256') != report.get('artifact_content_sha256')
            or terminal.get('policy_sha256') != report.get('policy_sha256')):
            errors.append(f'{stage}:report_terminal_binding_invalid')
    return errors


def _safe_stage_output_issues(report_dir, day, stage):
    try:
        return _stage_output_issues(report_dir, day, stage)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        return [f'{stage}:output_validation_failed:{type(exc).__name__}']


def stage_commands(stage, day, publication, *, recovery=False):
    import sys
    prefix = [sys.executable, '-m']
    def command(module, *args):
        return prefix + ['src.engine.' + module, *args]
    date_args = ['--target-date', day, '--write']
    if stage == 'main_machine_policy':
        return [command('scalping.ai_action_outcome_calibration', *date_args, '--machine-policy-only', '--activate-now')]
    if stage == 'legacy_machine_report':
        return [command('scalping.ai_action_outcome_calibration', *date_args, '--machine-only', '--publication-date', publication, '--require-policy-publication')]
    if stage == 'main_auxiliary_policy':
        common = ['--date', day, '--compact-only', '--write']
        return [command('scalping.entry_setup_paired_replay_batch', *common, '--execute-compact-candidate'),
                command('scalping.entry_setup_paired_replay_batch', *common, '--finalize-compact', '--publication-date', publication)]
    if stage == 'outcome_labels':
        return [command('scalping.ai_decision_quality', '--date', day, '--mode', 'postclose', '--write')]
    if stage == 'widget_policy' and recovery:
        return [command('automation.machine_research_closed_loop_refresh', '--source-date', day, '--family', 'widget', '--write', '--source-wait-sec', '0')]
    if stage == 'widget_policy':
        return [['/bin/bash', 'deploy/run_widget_evaluation.sh', day, '--recover-closed-target'] if recovery else ['/bin/bash', 'deploy/run_widget_evaluation.sh']]
    if stage == 'episode_policy':
        study = [] if recovery else [command('monitoring.low_price_two_leg_expanded_candidate_research', *date_args)]
        return study + [command('automation.machine_research_closed_loop_refresh', '--source-date', day, '--family', 'episode', '--write', '--source-wait-sec', '0')]
    modules = dict(collector_recommendation='monitoring.widget_collector_expansion_recommendation',
        machine_attribution='monitoring.machine_microstructure_attribution', machine_timing='automation.machine_entry_timing_tuning',
        market_weakness='automation.market_weakness_hysteresis_tuning', legacy_policy_approval='automation.machine_microstructure_policy_approval')
    if stage in modules:
        extra = ['--phase', 'postclose'] if stage == 'legacy_policy_approval' else ['--source-wait-sec', '0'] if stage == 'collector_recommendation' else []
        return [command(modules[stage], *date_args, *extra)]
    if stage == 'research_capacity':
        return [] if recovery else [command('monitoring.research_native_capacity_source', '--source-date', day, '--write')]
    if stage == 'research_allocation':
        return [command('automation.machine_research_closed_loop_refresh', '--source-date', day, '--family', 'allocation', '--write', '--source-wait-sec', '0')]
    return [command('automation.postclose_done_controller', '--date', day, '--summary-handoff-only', '--require-independent-producers')]


def _stage_code(stage, commands, project):
    paths = {'dispatcher': Path(__file__)}
    for cmd in commands:
        if '-m' in cmd:
            module = cmd[cmd.index('-m') + 1]
            paths[module] = project / (module.replace('.', '/') + '.py')
        elif cmd[0] == '/bin/bash':
            paths[cmd[1]] = project / cmd[1]
    if stage in {'widget_policy', 'episode_policy', 'research_allocation'}:
        from src.engine.automation.machine_research_closed_loop_refresh import code_contract
        return _stage_digest([_stage_sources(paths), code_contract()])
    if stage == 'research_capacity':
        paths['native_capacity'] = project / 'src/engine/monitoring/research_native_capacity_source.py'
    if stage == 'main_machine_policy':
        for name in ('entry_strategy_policy', 'entry_setup_evidence', 'ai_decision_quality', 'entry_candle_context', 'mechanistic_entry_runtime_policy'):
            paths[name] = project / f'src/engine/scalping/{name}.py'
    return _stage_digest(_stage_sources(paths))


def run_stage(stage, day, *, report_dir, project, publication=None, effective=None,
              recovery=False, execute=True, runner=None, timeout=14400, off=False, prerequisite_wait=0, stop_event=None):
    import os, fcntl, time, uuid
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from src.engine.build_next_stage2_checklist import _next_krx_trading_day
    publication = publication or day
    effective = effective or _next_krx_trading_day(publication)
    if not '2026-06-05' <= day <= publication <= datetime.now(ZoneInfo('Asia/Seoul')).date().isoformat() or effective != _next_krx_trading_day(publication):
        raise ValueError('stage_date_contract_invalid')
    if not execute and stage != 'outcome_labels':
        raise ValueError('only_committed_labels_support_validation_intake')
    path = stage_path(report_dir, day, stage); path.parent.mkdir(parents=True, exist_ok=True)
    with path.with_suffix('.lock').open('a') as lock:
        try: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError: return dict(stage_id=stage, status='running', exit_code=75, reason='existing_stage_writer')
        commands = stage_commands(stage, day, publication, recovery=recovery)
        code = _stage_code(stage, commands, project)
        old = _load_json(path)
        try:
            if old.get('status') == 'running' and old.get('child_start_ticks') and Path(f"/proc/{old['child_pid']}/stat").read_text().split()[21] == old['child_start_ticks']:
                return dict(stage_id=stage, status='running', exit_code=75, reason='existing_child_running')
        except (OSError, KeyError, IndexError):
            pass
        if not off and not execute and not stage_receipt_issues(report_dir, day, stage, code_hash=code) and old.get('publication_date') == publication and old.get('effective_date') == effective:
            return {**old, 'cache_reused': True}
        now = lambda: datetime.now(ZoneInfo('Asia/Seoul')).isoformat()
        value = dict(schema=STAGE_SCHEMA, stage_id=stage, source_date=day, target_date=day,
            publication_date=publication, effective_date=effective, run_id=uuid.uuid4().hex,
            stage_code_sha256=code, recovery_mode=recovery, status='pending', exit_code=None, pid=os.getpid(),
            process_start_ticks=Path('/proc/self/stat').read_text().split()[21], started_at=now(),
            heartbeat_at=now(), prerequisite_receipts={}, sources={}, retryable=True,
            policy_disposition='incumbent_carry', computation_executed=execute,
            checkpoint=str(report_dir / 'ai_decision_action_outcome_calibration') if stage == 'main_machine_policy' else None)
        if old:
            _stage_write(path.parent / 'attempts' / f'{stage}_{old.get("run_id", uuid.uuid4().hex)}.json', old)
        if off:
            return _stage_write(path, {**value, 'status':'off', 'off_reason':'explicit_schedule_disabled', 'exit_code':0})
        prerequisites = {s:stage_path(report_dir, day, s) for s in STAGE_REGISTRY[stage][0]}
        wait_deadline = time.monotonic() + prerequisite_wait
        while True:
            if stop_event is not None and stop_event.is_set():
                return _stage_write(path, {**value, 'status':'deferred', 'exit_code':75, 'issues':['stage_interrupted_at_saved_checkpoint']})
            issues = [e for s in prerequisites for e in stage_receipt_issues(report_dir, day, s)]
            waiting = any(_load_json(p).get('status', 'pending') in {'pending', 'running'} for p in prerequisites.values())
            if not issues or not waiting or time.monotonic() >= wait_deadline:
                break
            _stage_write(path, {**value, 'heartbeat_at':now(), 'reason':'prerequisite_pending', 'issues':issues})
            time.sleep(min(5, max(0, wait_deadline - time.monotonic())))
        value['prerequisite_receipts'] = _stage_sources(prerequisites)
        value['input_sources'] = _stage_sources(stage_input_paths(report_dir, day, stage))
        if issues:
            return _stage_write(path, {**value, 'status':'deferred', 'exit_code':75, 'issues':issues, 'policy_disposition':'source_gap'})
        if not execute:
            # Review-only intake is explicit: validates existing artifacts, never
            # claims that their calculation was executed by this new runner.
            issues = _safe_stage_output_issues(report_dir, day, stage)
            return _stage_write(path, {**value, 'sources':_stage_sources(stage_artifacts(report_dir, day, stage)),
                'status':'failed' if issues else 'succeeded', 'exit_code':1 if issues else 0,
                'issues':issues, 'execution_mode':'existing_output_validation', 'finished_at':now()})
        # Host-wide admission shared across independent scheduled wrappers.
        slots = Path(report_dir).parent / 'runtime' / 'postclose_stage_slots'; slots.mkdir(parents=True, exist_ok=True)
        slot = None; deadline = time.monotonic() + timeout
        while slot is None and time.monotonic() < deadline:
            if stop_event is not None and stop_event.is_set():
                return _stage_write(path, {**value, 'status':'deferred', 'exit_code':75, 'issues':['stage_interrupted_at_saved_checkpoint']})
            for n in range(2):
                handle = (slots / f'{n}.lock').open('a')
                try: fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB); slot = handle; break
                except BlockingIOError: handle.close()
            if slot is None:
                _stage_write(path, {**value, 'status':'pending', 'heartbeat_at':now(), 'reason':'resource_admission'})
                time.sleep(1)
        if slot is None:
            return _stage_write(path, {**value, 'status':'deferred', 'exit_code':75, 'issues':['resource_admission_timeout']})
        try:
            value.update(status='running', heartbeat_at=now()); _stage_write(path, value)
            env = {**os.environ, 'PYTHONPATH':str(project), 'POSTCLOSE_STAGE_WORKER':'1', 'POSTCLOSE_SOURCE_DATE':day,
                'POSTCLOSE_POLICY_PUBLICATION_DATE':publication, 'POSTCLOSE_PREPARED_EFFECTIVE_DATE':effective}
            rc = 0
            child = None
            for command in commands:
                if runner:
                    rc = runner(command, env=env, cwd=project)
                else:
                    with path.with_suffix('.log').open('a') as log:
                        child = subprocess.Popen(command, env=env, cwd=project, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                        while child.poll() is None:
                            if stop_event is not None and stop_event.is_set():
                                raise InterruptedError('stage_interrupted_at_saved_checkpoint')
                            try:
                                start_ticks = Path(f'/proc/{child.pid}/stat').read_text().split()[21]
                            except FileNotFoundError:
                                child.wait()
                                break
                            value.update(child_pid=child.pid, child_start_ticks=start_ticks, heartbeat_at=now()); _stage_write(path, value)
                            if time.monotonic() >= deadline:
                                import signal
                                os.killpg(child.pid, signal.SIGTERM)
                                try: child.wait(timeout=30)
                                except subprocess.TimeoutExpired: os.killpg(child.pid, signal.SIGKILL); child.wait()
                                break
                            time.sleep(1)
                        rc = child.returncode
                if rc: break
            issues = _safe_stage_output_issues(report_dir, day, stage) if not rc else [f'command_exit:{rc}']
            if value['prerequisite_receipts'] != _stage_sources(prerequisites): issues.append('prerequisite_changed_during_consumption')
            if value['input_sources'] != _stage_sources(stage_input_paths(report_dir, day, stage)): issues.append('input_changed_during_consumption')
            value.update(status=('deferred' if rc == 75 else 'failed') if rc or issues else 'succeeded',
                exit_code=rc or (1 if issues else 0), issues=issues, finished_at=now(), heartbeat_at=now(),
                sources=_stage_sources(stage_artifacts(report_dir, day, stage)))
            if stage == 'main_machine_policy' and not issues:
                terminal = _load_json(stage_artifacts(report_dir, day, stage)['machine_policy_terminal'])
                activation = (terminal.get('activation') or {}).get('status')
                value['policy_disposition'] = 'updated' if activation == 'activated' else 'incumbent_carry' if activation in {'already_active', 'incumbent_carry'} else 'no_valid_candidate'
                value['policy_sha256'] = terminal.get('policy_sha256')
            if stage in {'widget_policy', 'episode_policy'} and not issues:
                family_receipt = _load_json(stage_artifacts(report_dir, day, stage)[stage.replace('_policy', '_policy_refresh')])
                value['policy_sha256'] = family_receipt.get('policy_sha256')
                value['policy_disposition'] = 'updated' if old.get('policy_sha256') != value['policy_sha256'] else 'incumbent_carry'
            return _stage_write(path, value)
        except (OSError, ValueError, TypeError, KeyError, InterruptedError) as exc:
            return _stage_write(path, {**value, 'status':'failed', 'exit_code':1, 'issues':[str(exc)], 'finished_at':now()})
        finally:
            if 'child' in locals() and child is not None and child.poll() is None:
                import signal
                os.killpg(child.pid, signal.SIGTERM)
                try: child.wait(timeout=30)
                except subprocess.TimeoutExpired: os.killpg(child.pid, signal.SIGKILL); child.wait()
            slot.close()


def stage_overview(report_dir, day):
    states = {s:_load_json(stage_path(report_dir, day, s)) for s in STAGE_REGISTRY}
    issues = {s:stage_receipt_issues(report_dir, day, s) for s in states if s != 'summary_handoff'}
    # Startup evidence has its own date and contract, independent of diagnostics.
    from src.engine.build_next_stage2_checklist import _next_krx_trading_day
    effective = _next_krx_trading_day(day)
    bootstrap = _load_json(Path(report_dir).parent / 'runtime' / 'policy_bootstrap' / f'runtime_policy_bootstrap_verify_{effective}.json')
    ready = bootstrap.get('passed') is True and bootstrap.get('target_date') == effective
    if ready:
        from src.engine.automation.runtime_policy_bootstrap import verify_bootstrap, manifest_path
        ready = (manifest_path(effective).parent.resolve() == (Path(report_dir).parent / 'runtime' / 'policy_bootstrap').resolve()
            and verify_bootstrap(effective, write=False).get('passed') is True)
    policy_checks = {}
    from src.engine.scalping.mechanistic_entry_runtime_policy import load_effective
    from src.engine.automation.low_price_two_leg_auto_expansion_policy import load_policy
    from src.engine.monitoring.widget_symbol_runtime_policy import WidgetSymbolRuntimePolicyLoader
    data_root = Path(report_dir).parent
    try: policy_checks['main'] = bool(load_effective(data_root=data_root, target_date=effective))
    except (OSError, ValueError, TypeError, KeyError): policy_checks['main'] = False
    try: policy_checks['episode'] = bool(load_policy(date.fromisoformat(effective), policy_dir=data_root / 'runtime' / 'low_price_two_leg_auto_expansion'))
    except (OSError, ValueError, TypeError, KeyError): policy_checks['episode'] = False
    try: policy_checks['widget'] = bool(WidgetSymbolRuntimePolicyLoader(data_root / 'runtime' / 'widget_symbol_runtime_policy').resolve_all(observed_date=date.fromisoformat(effective)))
    except (OSError, ValueError, TypeError, KeyError): policy_checks['widget'] = False
    ready = ready and all(policy_checks.values())
    return dict(schema='postclose_stage_overview_v2', source_date=day, effective_date=effective,
        stages={s:dict(status=v.get('status', 'pending'), issues=issues.get(s, []), policy_disposition=v.get('policy_disposition')) for s,v in states.items()},
        postclose_all_active_stages_complete=not any(issues.values()) and states['summary_handoff'].get('status') == 'succeeded',
        next_session_policy_ready=ready, policy_loader_checks=policy_checks, startup_contract=bootstrap.get('status', 'not_verified'))


def _stage_main(argv):
    import argparse, os, sys
    from concurrent.futures import ThreadPoolExecutor
    from src.utils.constants import DATA_DIR, PROJECT_ROOT
    parser = argparse.ArgumentParser(description='Independent postclose stage dispatcher')
    parser.add_argument('--stage', choices=[*STAGE_REGISTRY, 'machine_group', 'overview', 'wait'], required=True)
    parser.add_argument('--date', required=True, type=date.fromisoformat)
    parser.add_argument('--publication-date')
    parser.add_argument('--recover-closed-target', action='store_true')
    parser.add_argument('--validate-existing', action='store_true')
    parser.add_argument('--off', action='store_true')
    parser.add_argument('--launch', action='store_true')
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--timeout-sec', type=int, default=14400)
    args = parser.parse_args(argv); day = args.date.isoformat()
    from datetime import datetime
    from zoneinfo import ZoneInfo
    publication = args.publication_date or day
    if not '2026-06-05' <= day <= publication <= datetime.now(ZoneInfo('Asia/Seoul')).date().isoformat() or args.timeout_sec <= 0:
        parser.error('stage_date_or_timeout_contract_invalid')
    if (args.check or args.off or args.validate_existing or args.launch) and args.stage not in STAGE_REGISTRY:
        parser.error('action_requires_one_stage')
    if args.validate_existing and args.stage != 'outcome_labels':
        parser.error('only_committed_labels_support_validation_intake')
    if args.launch and (args.off or args.check or args.validate_existing):
        parser.error('launch_requires_execution')
    import signal, threading
    stop_event = threading.Event()
    def interrupted(signum, frame):
        stop_event.set()
    signal.signal(signal.SIGTERM, interrupted)
    if args.stage == 'wait':
        import time
        deadline = time.monotonic() + args.timeout_sec
        required = ('main_machine_policy', 'main_auxiliary_policy', 'legacy_machine_report', 'episode_policy', 'outcome_labels')
        while any(_load_json(stage_path(DATA_DIR / 'report', day, s)).get('status', 'pending') in {'pending','running'} for s in required):
            if time.monotonic() >= deadline: return 75
            if stop_event.is_set(): return 75
            time.sleep(1)
        return 0
    if args.check:
        status = _load_json(stage_path(DATA_DIR / 'report', day, args.stage)).get('status', 'pending')
        if status in {'pending', 'running', 'deferred'}: return 75
        return 1 if stage_receipt_issues(DATA_DIR / 'report', day, args.stage) else 0
    if args.launch:
        subprocess.Popen([sys.executable, '-m', 'src.engine.automation.postclose_summary_handoff', *[a for a in argv if a != '--launch']],
            cwd=PROJECT_ROOT, start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return 0
    if args.stage == 'overview':
        print(json.dumps(stage_overview(DATA_DIR / 'report', day))); return 0
    def run(s):
        return run_stage(s, day, report_dir=DATA_DIR / 'report', project=PROJECT_ROOT,
            publication=args.publication_date, recovery=args.recover_closed_target,
            execute=not args.validate_existing, timeout=args.timeout_sec, off=args.off,
            prerequisite_wait=0 if args.recover_closed_target else args.timeout_sec, stop_event=stop_event)
    if args.stage == 'machine_group':
        # Waiting threads hold no compute slot; only two child stages run host-wide.
        results=[run('research_capacity')]
        with ThreadPoolExecutor(max_workers=6) as pool:
            results += list(pool.map(run, STAGE_OWNER_GROUPS['machine'][:6]))
        results.append(run('summary_handoff'))
    else: results=[run(args.stage)]
    print(json.dumps([dict(stage=r.get('stage_id'), status=r['status'], exit_code=r['exit_code'], cache_reused=r.get('cache_reused',False)) for r in results]))
    return 1 if any(r['exit_code'] not in (0,75) for r in results) else 75 if any(r['exit_code']==75 for r in results) else 0


if __name__ == "__main__":
    import sys
    raise SystemExit(_stage_main(sys.argv[1:]) if "--stage" in sys.argv else _producer_main())
