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
FUTURE_HANDOFF_SCHEMA = "direct_family_future_handoff_v2"
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
            checks = [issue for stage in stages for issue in stage_receipt_issues(
                report_dir, target_date, stage, allow_historical_terminal=True)]
            running = any(_load_json(stage_path(report_dir, target_date, stage)).get('status') in {'running','pending'} for stage in stages)
            result['stage_group:' + owner] = 'waiting_running' if running else 'failed_receipt:' + ','.join(checks) if checks else 'done'
        return result
    paths = intake_source_paths(report_dir, target_date)
    runner = runner or subprocess.run
    result = {}
    owner_sources = {
        "korstockscan-machine-microstructure-final-refresh.service": (
            "machine_microstructure_attribution",
            "machine_entry_timing_tuning",
            "machine_microstructure_policy_approval",
        ),
    }
    for unit, labels in owner_sources.items():
        owner = "machine"
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


def _initial_quantity_refresh_due(report_dir: Path, target_date: str) -> bool:
    """Bind the direct consumer to the selected policy, not a rollout date."""
    current_path = report_dir.parent / "runtime" / "initial_quantity" / "current.json"
    if not current_path.exists():
        return False
    try:
        current = json.loads(current_path.read_text())
        from datetime import date
        target = date.fromisoformat(target_date)
        effective = date.fromisoformat(current["effective_from"])
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise RuntimeError("initial_quantity_current_invalid") from exc
    if target < effective:
        return False
    from src.engine.scalping.initial_quantity_activation import (
        selected_initial_quantity_env,
    )
    try:
        selected_initial_quantity_env(current_path, target_date)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise RuntimeError("initial_quantity_current_invalid") from exc
    return True


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
        cancel_path = report_dir / 'entry_cancel_wait_tuning' / f'entry_cancel_wait_tuning_{target_date}.json'
        if target_date >= '2026-10-02' or cancel_path.exists():
            paths['entry_cancel_wait_tuning'] = cancel_path
            paths['entry_cancel_wait_policy'] = cancel_path.with_name(f'entry_cancel_wait_policy_{target_date}.json')
        from src.engine.scalping.holding_path_vote_policy import (
            START_DATE as HOLDING_VOTE_POLICY_START_DATE,
            policy_path as holding_vote_policy_path,
        )
        if target_date >= HOLDING_VOTE_POLICY_START_DATE:
            from src.engine.build_next_stage2_checklist import _next_krx_trading_day
            paths["holding_path_vote_policy"] = holding_vote_policy_path(
                report_dir.parent, _next_krx_trading_day(target_date),
            )
        if _initial_quantity_refresh_due(report_dir, target_date):
            paths["initial_quantity_refresh_stage"] = (
                report_dir / "initial_entry_quantity_type_policy"
                / f"refresh_postclose_{target_date}"
                / f"initial_quantity_refresh_stage_{target_date}.json")
        if any(stage_path(report_dir, target_date, s).exists() for s in STAGE_REGISTRY):
            paths.update({f'stage_{stage}':stage_path(report_dir, target_date, stage)
                for stage in active_stage_names(target_date) if stage != 'summary_handoff'})
            return paths
        for owner in ("machine",):
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
        if label == "initial_quantity_refresh_stage":
            from src.engine.scalping.initial_quantity_policy import (
                refresh_quantity_stage_terminal_valid,
            )
            stage = json.loads(raw) if raw is not None else None
            if (not refresh_quantity_stage_terminal_valid(stage)
                    or stage.get("source_date") != target_date):
                raise RuntimeError("initial_quantity_refresh_stage_invalid")
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
        "manifest_sha256": preopen.get("manifest_sha256"),
        "verification_path": preopen.get("verification_path"),
        "verification_sha256": preopen.get("verification_sha256"),
        "release_selection_sha256": preopen.get("release_selection_sha256"),
        "selected_release_commit": preopen.get("selected_release_commit"),
        "manifest_content_sha256": preopen.get("manifest_content_sha256"),
        "manifest_env_sha256": preopen.get("manifest_env_sha256"),
        "source_reported_pid_receipt": preopen.get("actual_pid_consumed") is True,
        "actual_pid_consumed": False,
        "policy_receipts": policies,
        **({"holding_path_vote_policy": summary["holding_path_vote_policy"]}
           if "holding_path_vote_policy" in summary else {}),
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }


def direct_future_handoff_marker(payload: dict[str, Any]) -> str:
    return f"<!-- {FUTURE_HANDOFF_MARKER} {json.dumps(payload, sort_keys=True)} -->"


def inspect_future_handoff(
    summary: dict[str, Any], source_date: str, *, report_dir: Path,
) -> dict[str, Any]:
    """Read the current future bootstrap without granting PREOPEN or PID authority."""
    from src.engine.automation.runtime_policy_bootstrap import (
        future_handoff_transition_contract,
        future_handoff_transition_path,
        release_selection_for_generation,
    )

    preopen = summary.get("preopen_consumption_receipt") or {}
    apply_date = preopen.get("apply_date") if isinstance(preopen, dict) else None
    base = {"source_date": source_date, "apply_date": apply_date,
            "actual_pid_consumed": False, "pid_receipt_present": False,
            "valid_empty": False, "issues": []}
    if not apply_date:
        return {**base, "status": "not_applicable"}
    try:
        if (date.fromisoformat(source_date).isoformat() != source_date
                or date.fromisoformat(apply_date).isoformat() != apply_date
                or source_date >= apply_date):
            raise ValueError("invalid_date_order")
    except (TypeError, ValueError):
        return {**base, "status": "rejected", "issues": ["future_pointer_date_invalid"]}
    data_dir = Path(report_dir).resolve().parent
    root = data_dir / "runtime" / "policy_bootstrap"
    manifest_file = root / f"runtime_policy_bootstrap_{apply_date}.json"
    verification_file = root / f"runtime_policy_bootstrap_verify_{apply_date}.json"
    if (summary.get("date") != source_date or preopen.get("source_date") != source_date
            or preopen.get("manifest_path") != str(manifest_file)
            or preopen.get("verification_path") != str(verification_file)):
        return {**base, "status": "rejected", "issues": ["future_pointer_identity_invalid"]}
    if summary.get("preopen_consumption_state") == "off":
        return {**base, "status": "off", "issues": ["source_summary_explicit_off"]}
    try:
        manifest_raw = manifest_file.read_bytes()
    except FileNotFoundError:
        manifest_raw = None
    except OSError:
        return {**base, "status": "rejected", "issues": ["future_manifest_unreadable"]}
    try:
        verification_raw = verification_file.read_bytes()
    except FileNotFoundError:
        verification_raw = None
    except OSError:
        return {**base, "status": "rejected", "issues": ["future_verification_unreadable"]}
    if manifest_raw is None or verification_raw is None:
        if (manifest_raw is None and verification_raw is None
                and preopen.get("manifest_sha256") is None
                and preopen.get("verification_sha256") is None):
            return {**base, "status": "pending"}
        return {**base, "status": "stale", "issues": ["future_generation_missing_or_partial"]}
    manifest_sha = hashlib.sha256(manifest_raw).hexdigest()
    verification_sha = hashlib.sha256(verification_raw).hexdigest()
    try:
        verification = json.loads(verification_raw)
        manifest = json.loads(manifest_raw)
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return {**base, "status": "rejected", "issues": ["future_generation_unreadable"]}
    if not isinstance(verification, dict) or not isinstance(manifest, dict):
        return {**base, "status": "rejected", "issues": ["future_generation_object_invalid"]}
    selection_binding = release_selection_for_generation(data_dir, manifest, verification)
    if selection_binding["status"] == "invalid":
        return {**base, "status": "stale", "issues": selection_binding["issues"]}
    base["pid_receipt_present"] = (
        type(verification.get("pid")) is int and verification["pid"] > 0
        and verification.get("pid_passed") is True
        and verification.get("pid_env_available") is True
    )
    if verification.get("status") in {"fail", "failed", "error"}:
        return {**base, "status": "rejected", "issues": ["future_verification_failed"]}
    if verification.get("status") == "off":
        return {**base, "status": "off", "issues": ["future_verification_explicit_off"]}
    contract = future_handoff_transition_contract(
        source_date, apply_date, data_dir=data_dir,
        allow_pid_receipt=base["pid_receipt_present"],
    )
    if contract.get("status") != "linked":
        return {**base, "status": "stale", "issues": contract.get("issues", [])}
    result = {**base, "valid_empty": contract["valid_empty"],
              "manifest_sha256": manifest_sha, "verification_sha256": verification_sha,
              "manifest_content_sha256": contract["manifest_content_sha256"],
              "env_sha256": contract["env_sha256"],
              "selected_release_commit": contract["selected_release_commit"],
              "release_selection_status": selection_binding["status"]}
    same = (
        preopen.get("manifest_sha256") == manifest_sha
        and preopen.get("verification_sha256") == verification_sha
        and preopen.get("release_selection_sha256") == contract["release_selection_sha256"]
        and preopen.get("selected_release_commit") == contract["selected_release_commit"]
    )
    if same:
        return {**result, "status": (
            "historical_generation_pid_receipt_unconfirmed"
            if selection_binding["status"] == "historical" and base["pid_receipt_present"]
            else "historical_generation_no_pid"
            if selection_binding["status"] == "historical"
            else "same_generation_pid_receipt_unconfirmed"
            if base["pid_receipt_present"] else "same_generation_no_pid"
        )}
    path = future_handoff_transition_path(
        source_date, apply_date, contract["source_summary_sha256"],
        manifest_sha, verification_sha, data_dir=data_dir,
    )
    if _load_json(path) == contract:
        return {**result, "status": "transitioned_no_pid", "transition_path": str(path)}
    return {**result, "status": "stale", "issues": ["future_transition_missing_or_mismatched"]}


def direct_tower_required(target_date: str, summary: dict[str, Any]) -> bool:
    """Require the report consumer for the issued cancel reconciliation contract."""
    if target_date < '2026-10-02':
        return False
    from src.engine.automation.entry_cancel_wait_tuning import RECONCILIATION_VERSION
    sources = summary.get('sources') or {}
    source = sources.get('entry_cancel_wait') or {}
    evidence = source.get('economic_evidence') or {}
    view = evidence.get('cancel_wait_reconciliation') or {}
    return view.get('reconciliation_contract_version') == RECONCILIATION_VERSION


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
    future_handoff = (
        inspect_future_handoff(summary, target_date, report_dir=report_dir)
        if direct_mode and target_date >= "2026-09-23"
        else {"status": "not_applicable", "actual_pid_consumed": False, "issues": []}
    )
    if (future_handoff["status"] in {"stale", "rejected"}
            or (future_handoff["status"] == "off"
                and summary.get("preopen_consumption_state") != "off")):
        issues.append("postclose_summary_handoff:future_preopen_generation_stale")
    from src.engine.scalping.holding_path_vote_policy import (
        START_DATE as HOLDING_VOTE_POLICY_START_DATE,
        load_bundle as load_holding_vote_policy,
    )
    if direct_mode and target_date >= HOLDING_VOTE_POLICY_START_DATE:
        receipt = summary.get("holding_path_vote_policy") or {}
        from src.engine.build_next_stage2_checklist import _next_krx_trading_day
        target_policy_date = _next_krx_trading_day(target_date)
        observation_path = (report_dir / "monitor_snapshots" /
                            f"holding_exit_observation_{target_date}.json")
        try:
            observation_sha = hashlib.sha256(observation_path.read_bytes()).hexdigest()
            bundle = load_holding_vote_policy(
                report_dir.parent, target_policy_date,
                source_report_sha256=observation_sha,
            )
            if (receipt.get("status") != "estimated_provisional_published"
                    or receipt.get("source_date") != target_date
                    or receipt.get("target_date") != target_policy_date
                    or receipt.get("bundle_sha256") != bundle["bundle_sha256"]
                    or receipt.get("policy_set_sha256") != bundle["policy_set_sha256"]
                    or receipt.get("source_report_sha256") != observation_sha
                    or receipt.get("cell_count") != len(bundle["cells"])
                    or receipt.get("allowed_runtime_apply") is not True):
                issues.append("postclose_summary_handoff:holding_vote_policy_semantics_invalid")
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
            issues.append("postclose_summary_handoff:holding_vote_policy_missing_or_invalid")
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
        "future_handoff": future_handoff,
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
    "machine": ("machine_microstructure_attribution", "machine_entry_timing_tuning",
                "machine_microstructure_policy_approval", "market_weakness_hysteresis_tuning",
                "machine_research_closed_loop"),
}


def producer_receipt_path(report_dir: Path, day: str, owner: str) -> Path:
    return report_dir / "postclose_producer_terminal" / f"{owner}_{day}.json"


def producer_receipt_issues(report_dir: Path, day: str, owner: str) -> list[str]:
    if owner not in INDEPENDENT_SOURCES:
        raise ValueError("retired_or_unknown_postclose_owner")
    from src.engine.verify_threshold_cycle_postclose_chain import _sha
    if any(stage_path(report_dir, day, s).exists() for s in STAGE_REGISTRY):
        return [issue for stage in STAGE_OWNER_GROUPS[owner]
                for issue in stage_receipt_issues(
                    report_dir, day, stage, allow_historical_terminal=True)]
    value = _load_json(producer_receipt_path(report_dir, day, owner))
    if (value.get("status") != "succeeded" or value.get("target_date") != day
        or value.get("owner") != owner or type(value.get("exit_code")) is not int
        or value.get("exit_code") != 0 or not value.get("run_id")
        or not re.fullmatch(r"[0-9a-f]{40}", str(value.get("code_commit") or ""))):
        return [f"{owner}:terminal_missing_or_invalid"]
    issues = []
    for label in INDEPENDENT_SOURCES[owner]:
        row = (value.get("sources") or {}).get(label) or {}
        if not row.get("sha256") or _sha(Path(row.get("path") or "")) != row["sha256"]:
            issues.append(f"{owner}:source_hash_invalid:{label}")
    return issues


def machine_input_issues(report_dir: Path, day: str) -> list[str]:
    """Cheap exact-date dependency barrier, before any costly machine stage.

    Producers retain their full schema/hash validation. Do not wait on main
    success: final main verification may itself consume machine evidence.
    """
    from src.engine.automation.postclose_recommendation_intake import _report_date
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
    import argparse, os, uuid
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from src.utils.constants import DATA_DIR, PROJECT_ROOT
    from src.engine.verify_threshold_cycle_postclose_chain import _atomic_write, _sha
    from src.engine.automation.postclose_recommendation_intake import source_paths, _report_date
    parser = argparse.ArgumentParser(description="Record surviving independent postclose execution")
    parser.add_argument("--owner", choices=sorted(INDEPENDENT_SOURCES), required=True)
    parser.add_argument("--date", required=True, type=date.fromisoformat)
    parser.add_argument("--phase", choices=("started", "finished", "wait-inputs"), required=True)
    parser.add_argument("--source-wait-sec", type=float, default=43200)
    parser.add_argument("--exit-code", type=int, default=0)
    args = parser.parse_args(argv)
    day = str(args.date)
    if args.date > datetime.now(ZoneInfo("Asia/Seoul")).date():
        parser.error("future source date is not supported")
    report_dir = DATA_DIR / "report"
    if args.phase == "wait-inputs":
        return wait_for_machine_inputs(report_dir, day, timeout=args.source_wait_sec)
    path = producer_receipt_path(report_dir, day, args.owner)
    now = datetime.now(ZoneInfo("Asia/Seoul")).isoformat()
    if args.phase == "started":
        previous = _load_json(path)
        if previous:
            old = path.parent / "attempts" / f"{args.owner}_{day}_{uuid.uuid4().hex}.json"
            _atomic_write(old, json.dumps(previous, indent=2) + "\n")
        value = dict(schema="postclose_producer_terminal_v2", target_date=day, owner=args.owner,
            status="running", run_id=uuid.uuid4().hex, started_at=now, wrapper_pid=os.getppid(),
            code_commit=subprocess.check_output(["git", "-C", str(PROJECT_ROOT), "rev-parse", "HEAD"], text=True).strip(),
            runtime_effect=False)
    else:
        value = _load_json(path)
        if (value.get("owner") != args.owner or value.get("target_date") != day
            or value.get("status") != "running" or value.get("wrapper_pid") != os.getppid()):
            raise RuntimeError("producer_started_receipt_missing")
        paths = source_paths(report_dir, day)
        sources, issues = {}, []
        for label in INDEPENDENT_SOURCES[args.owner]:
            source = paths.get(label, report_dir / label / f"{label}_{day}.json")
            payload = _load_json(source)
            sources[label] = dict(path=str(source.resolve()), sha256=_sha(source))
            if not sources[label]["sha256"] or _report_date(payload) != day:
                issues.append(f"source_missing_or_date_invalid:{label}")
        value.update(status="succeeded" if args.exit_code == 0 and not issues else "failed",
            exit_code=args.exit_code if args.exit_code else (1 if issues else 0),
            sources=sources, issues=issues, finished_at=now)
    _atomic_write(path, json.dumps(value, indent=2)+"\n")
    return 0 if value["status"] != "failed" else 1


# Stage registry is shared by dispatch, summary, verifier and controller. Legacy
# v1 terminals remain readable, but never synthesize a successful v2 stage.
STAGE_SCHEMA = 'postclose_stage_terminal_v3'
# Episode research reports can legitimately exceed the legacy 32 MiB
# validation bound. Keep the read bounded while matching the producer's
# existing artifact-size contract.
FAMILY_ARTIFACT_MAX_BYTES = 64 * 1024 * 1024
STAGE_REGISTRY = {
    'main_machine_policy': ((), ('machine_policy', 'machine_policy_terminal')),
    'pre_submit_delay': ((), ('pre_submit_delay_tuning', 'pre_submit_delay_policy')),
    'legacy_machine_report': ((), ('ai_decision_action_outcome_calibration',)),
    'main_auxiliary_policy': (('outcome_labels', 'legacy_machine_report'), ('compact_auxiliary_paired_economic',)),
    'outcome_labels': ((), ('ai_decision_outcome_labels',)),
    'episode_policy': ((), ('low_price_two_leg_expanded_candidate_research', 'episode_policy_refresh')),
    'machine_attribution': ((), ('machine_microstructure_attribution',)),
    'machine_timing': (('machine_attribution',), ('machine_entry_timing_tuning',)),
    'market_weakness': (('machine_attribution',), ('market_weakness_hysteresis_tuning',)),
    'research_capacity': ((), ('research_native_capacity',)),
    'research_allocation': (('episode_policy', 'research_capacity'), ('machine_research_closed_loop',)),
    'legacy_policy_approval': (('machine_attribution',), ('machine_microstructure_policy_approval',)),
    'summary_handoff': ((), ('postclose_done_controller',)),
}


def active_stage_names(day):
    """A new mandatory family must not retroactively invalidate old dates."""
    return tuple(stage for stage in STAGE_REGISTRY
                 if stage != 'pre_submit_delay' or day >= '2026-09-23')
STAGE_OWNER_GROUPS = {
    'machine': ('machine_attribution', 'machine_timing',
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
        filename = {'machine_policy': 'winrate_policy',
                    'machine_policy_terminal': 'winrate_policy_terminal'}.get(label, label)
        paths[label] = Path(report_dir) / folder / f'{filename}_{day}.json'
    paths['research_native_capacity'] = Path(report_dir).parent / 'runtime' / 'machine_research_closed_loop' / f'capacity_source_{day}.json'
    paths['pre_submit_delay_tuning'] = Path(report_dir) / 'pre_submit_delay_tuning' / f'pre_submit_delay_tuning_{day}.json'
    paths['pre_submit_delay_policy'] = Path(report_dir).parent / 'threshold_cycle' / 'pre_submit_delay_policy' / f'pre_submit_delay_policy_{day}.json'
    paths['episode_policy_refresh'] = Path(report_dir) / 'machine_research_closed_loop' / f'episode_policy_refresh_{day}.json'
    outputs = {name: paths.get(name, Path(report_dir) / name / f'{name}_{day}.json') for name in STAGE_REGISTRY[stage][1]}
    if stage == 'main_machine_policy' and day >= '2026-10-06':
        outputs['main_fixed_watch_policy_research'] = Path(report_dir) / 'main_fixed_watch_policy_research' / f'main_fixed_watch_policy_research_{day}.json'
        from src.engine.scalping.main_fixed_watch import SPECS
        for spec in SPECS:
            if spec.episode_entry_forbidden:
                outputs['main_fixed_watch_policy_research_' + spec.symbol] = Path(report_dir) / 'main_fixed_watch_policy_research' / f'main_fixed_watch_policy_research_{spec.symbol}_{day}.json'
    return outputs


def _stage_digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()


def _stage_sources(paths):
    result = {}
    for name, path in paths.items():
        path = Path(path)
        # Exact AI storage may replace a closed-date plain source with a
        # verified gzip. Keep the original logical path and decoded SHA in
        # older stage receipts; validate the producer's date/schema contract.
        if (path.parent.name in {'ai_decision_payloads', 'ai_decision_outcome_labels'}
            and re.fullmatch(r'(ai_decision_payloads_\d{4}-\d{2}-\d{2}\.jsonl|ai_decision_outcome_labels_\d{4}-\d{2}-\d{2}\.json)', path.name)
            and path.with_suffix(path.suffix + '.gz').exists()):
            from src.engine.scalping.micro_reversion.storage_maintenance import validate_exact_ai_artifact_source
            try:
                source_date = date.fromisoformat(path.stem.rsplit('_', 1)[-1])
                verified = validate_exact_ai_artifact_source(path, expected_date=source_date)
                sha = verified['decoded_content_sha256']
            except (OSError, ValueError, KeyError):
                sha = None
            result[name] = dict(path=str(path.resolve()), sha256=sha)
            continue
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


def reseal_summary_handoff_for_final_controller(report_dir, day, controller_path):
    """Bind the already verified summary stage to the final DONE controller.

    The summary worker first writes ``summary_verified``. The subsequent
    whole-chain controller replaces that output with ``done``; without this
    bounded reseal, the successful stage immediately becomes stale.
    """
    import fcntl
    path = stage_path(report_dir, day, 'summary_handoff')
    if not path.exists():
        return False  # Legacy dates have no independent summary stage.
    expected = stage_artifacts(report_dir, day, 'summary_handoff')
    owner = expected['postclose_done_controller']
    if Path(controller_path).resolve() != owner.resolve():
        raise ValueError('summary_handoff:final_controller_path_invalid')
    with path.with_suffix('.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        value = _load_json(path)
        issues = stage_receipt_issues(report_dir, day, 'summary_handoff')
        if (value.get('status') != 'succeeded' or value.get('exit_code') != 0
                or any(issue != 'summary_handoff:output_generation_changed' for issue in issues)):
            raise ValueError('summary_handoff:final_controller_stage_invalid')
        controller = _load_json(owner)
        if (controller.get('date') != day or controller.get('status') != 'done'
                or controller.get('whole_native_chain_done_claimed') is not True
                or controller.get('final_verifier_status') != 'pass'):
            raise ValueError('summary_handoff:final_controller_not_verified')
        # Output drift is reported before input drift by stage_receipt_issues.
        # Validate the consumed generation before changing the saved receipt.
        # A refreshed controller cannot make an old summary computation current.
        prerequisites = {s: str(stage_path(report_dir, day, s))
                         for s in STAGE_REGISTRY['summary_handoff'][0]}
        if value.get('prerequisite_receipts') != _stage_sources(prerequisites):
            raise ValueError('summary_handoff:prerequisite_generation_changed')
        if value.get('input_sources') != _stage_sources(
                stage_input_paths(report_dir, day, 'summary_handoff')):
            raise ValueError('summary_handoff:input_generation_changed')
        sources = _stage_sources(expected)
        if not sources['postclose_done_controller']['sha256']:
            raise ValueError('summary_handoff:final_controller_missing')
        if value.get('sources') != sources:
            value['sources'] = sources
            value['final_controller_reseal'] = {
                'status': 'done',
                'controller_sha256': sources['postclose_done_controller']['sha256'],
            }
            _stage_write(path, value)
        if stage_receipt_issues(report_dir, day, 'summary_handoff'):
            raise ValueError('summary_handoff:final_controller_reseal_invalid')
    return True


def stage_receipt_issues(report_dir, day, stage, *, code_hash=None,
                         allow_historical_summary=False,
                         allow_historical_terminal=False):
    value = _load_json(stage_path(report_dir, day, stage))
    # Read-only consumers may authenticate unchanged pre-retirement evidence.
    # Dispatch/check/reuse of a producer still requires v3. This never rewrites
    # a v2 receipt or brings the retired Widget stages back into the registry.
    historical_summary = False
    historical_terminal = False
    if ((allow_historical_terminal or (allow_historical_summary and stage == 'summary_handoff'))
            and value.get('schema') == 'postclose_stage_terminal_v2'):
        from datetime import date
        try:
            publication = value.get('publication_date', day)
            historical_terminal = (
                date.fromisoformat(day).isoformat() == day
                and date.fromisoformat(publication).isoformat() == publication
                and '2026-06-05' <= day <= publication < '2026-10-06'
            )
        except (TypeError, ValueError):
            pass
        historical_summary = historical_terminal and stage == 'summary_handoff'
    if ((value.get('schema') != STAGE_SCHEMA and not historical_terminal) or value.get('stage_id') != stage
        or value.get('source_date') != day or not value.get('run_id')
        or value.get('receipt_sha256') != _stage_digest({k:v for k,v in value.items() if k != 'receipt_sha256'})):
        return [f'{stage}:terminal_missing_or_invalid']
    if value.get('status') == 'off' and value.get('off_reason') == 'explicit_schedule_disabled':
        return []
    if value.get('status') != 'succeeded' or value.get('exit_code') != 0:
        return [f'{stage}:{value.get("status")}']
    if stage == 'summary_handoff' and (
        value.get('prepared_effective_date') is not None
        or value.get('publication_date', day) > day
    ):
        from src.engine.build_next_stage2_checklist import _next_krx_trading_day
        if value.get('prepared_effective_date') != _next_krx_trading_day(day):
            return ['summary_handoff:prepared_source_session_mismatch']
    if stage == 'pre_submit_delay':
        from src.engine.scalping.pre_submit_delay_tuning import family_source_ledger_issues
        source_issues = family_source_ledger_issues(Path(report_dir).parent, day)
        if source_issues:
            return [f'{stage}:{issue}' for issue in source_issues]
        ledger = _load_json(stage_input_paths(report_dir, day, stage)['pre_submit_delay_source_ledger'])
        if value.get('pipeline_source_generation_sha256') != ledger.get('ledger_sha256'):
            return [f'{stage}:pipeline_source_generation_changed']
    if code_hash is None:
        code_hash = _stage_code(stage, stage_commands(stage, day, value.get('publication_date') or day, recovery=value.get('recovery_mode', False)), Path(__file__).resolve().parents[3])
    if value.get('stage_code_sha256') != code_hash:
        # A code-only release transition must not force unchanged stages to
        # replay. Accept the exact hash from a bounded set of managed immutable
        # releases; artifact, input, and prerequisite hashes remain checked
        # below in either case.
        compatible = set()
        selection = _load_json(Path(report_dir).parent / 'runtime' / 'runtime_release_selection.json')
        selected_root = Path(selection.get('release_root', ''))
        if (selection.get('schema') == 'runtime_release_selection_v1'
            and len(selection.get('git_commit', '')) == 40
            and all(ch in '0123456789abcdef' for ch in selection.get('git_commit', ''))
            and selected_root.is_absolute()
            and selected_root.parent.name == 'KORStockScan-runtime-releases'):
            release_roots = [selected_root]
            try:
                managed_roots = sorted(
                    child for child in selected_root.parent.iterdir()
                    if child.is_dir() and (child / '.git').exists()
                )
            except OSError:
                managed_roots = []
            if len(managed_roots) <= 256:
                release_roots.extend(root for root in managed_roots if root != selected_root)
                commands = stage_commands(stage, day,
                    value.get('publication_date') or day,
                    recovery=value.get('recovery_mode', False))
                for release_root in release_roots:
                    release_dispatcher = release_root / 'src/engine/automation/postclose_summary_handoff.py'
                    if release_dispatcher.is_file():
                        compatible.add(_stage_code(stage, commands, release_root,
                            dispatcher_path=release_dispatcher))
                        if value.get('stage_code_sha256') in compatible:
                            break
                        if historical_terminal and stage == 'main_machine_policy':
                            # Before fixed-watch publication, this stage did
                            # not include the three newly added dependencies.
                            # Authenticate that old contract against retained
                            # immutable code, never against a supplied hash.
                            compatible.add(_stage_code(stage, commands, release_root,
                                dispatcher_path=release_dispatcher,
                                legacy_main_machine=True))
                            if value.get('stage_code_sha256') in compatible:
                                break
        if value.get('stage_code_sha256') not in compatible:
            return [f'{stage}:code_changed']
    expected = stage_artifacts(report_dir, day, stage)
    if set(value.get('sources', {})) != set(expected):
        return [f'{stage}:source_set_invalid']
    if value['sources'] != _stage_sources(expected) or any(not r['sha256'] for r in value['sources'].values()):
        return [f'{stage}:output_generation_changed']
    prerequisites = {s:str(stage_path(report_dir, day, s)) for s in STAGE_REGISTRY[stage][0]}
    if value.get('prerequisite_receipts') != _stage_sources(prerequisites):
        return [f'{stage}:prerequisite_generation_changed']
    input_paths = stage_input_paths(report_dir, day, stage)
    if historical_summary:
        # Retired terminals remain immutable evidence; reading them does not
        # restore their producers or grant current Widget trading authority.
        for retired_stage in ('widget_policy', 'collector_recommendation'):
            input_paths[retired_stage] = (
                Path(report_dir) / 'postclose_stage_terminal' / day / f'{retired_stage}.json'
            )
    if value.get('input_sources') != _stage_sources(input_paths):
        return [f'{stage}:input_generation_changed']
    return _safe_stage_output_issues(report_dir, day, stage)


def _joint_research_peer_off(report_dir, day):
    """The joint allocation has no active peer when episode policy is OFF."""
    receipt = _load_json(stage_path(report_dir, day, 'episode_policy'))
    return (receipt.get('status') == 'off'
            and receipt.get('off_reason') == 'explicit_schedule_disabled'
            and not stage_receipt_issues(report_dir, day, 'episode_policy'))


def stage_input_paths(report_dir, day, stage):
    paths = {s:stage_path(report_dir, day, s) for s in STAGE_REGISTRY[stage][0]}
    if stage == 'research_capacity':
        root = Path(report_dir).parent / 'runtime' / 'machine_research_closed_loop' / 'native_capacity' / day
        paths['native_cash'] = root / 'native_cash.json'
        paths['native_inventory'] = root / 'native_inventory.json'
    if stage == 'summary_handoff':
        paths.update({s:stage_path(report_dir, day, s) for s in active_stage_names(day)
                      if s != 'summary_handoff'})
    if stage == 'pre_submit_delay':
        paths['pre_submit_delay_source_ledger'] = Path(report_dir).parent / 'pipeline_event_summaries' / f'pre_submit_delay_source_ledger_{day}.json'
    if stage in {'outcome_labels'}:
        paths['labels'] = Path(report_dir) / 'ai_decision_outcome_labels' / f'ai_decision_outcome_labels_{day}.json'
        paths['payloads'] = Path(report_dir).parent / 'ai_decision_payloads' / f'ai_decision_payloads_{day}.jsonl'
    if stage == 'outcome_labels': paths.pop('labels', None)
    return paths


def _machine_source_preflight_issue(report_dir, day, *, recovery=False):
    """Require a bound audit; closed-date recovery may use its final successor."""
    source_path = (Path(report_dir) / 'observation_source_quality_audit'
                   / f'observation_source_quality_audit_{day}.json')
    binding = _load_json(Path(str(source_path) + '.final-contract.json'))
    try:
        source_bytes = source_path.read_bytes()
        source = json.loads(source_bytes)
    except (OSError, ValueError, TypeError):
        return 'source_quality_preflight_missing_or_invalid'
    if not isinstance(source, dict) or not binding:
        return 'source_quality_preflight_missing_or_invalid'
    phase = source.get('audit_phase')
    if (source.get('target_date') != day
        or phase not in ({'preflight', 'final'} if recovery else {'preflight'})
        or binding.get('schema') != 'observation_source_quality_final_binding_v1'
        or binding.get('target_date') != day
        or binding.get('audit_phase') != phase
        or binding.get('artifact_sha256') != hashlib.sha256(source_bytes).hexdigest()
        or binding.get('implementation_sha256') != source.get('consumer_implementation_sha256')):
        return 'source_quality_preflight_identity_or_hash_invalid'
    if recovery and phase == 'final':
        from src.engine.observation_source_quality_audit import check_audit_reusable
        if check_audit_reusable(day, audit_phase='final', artifact_path=source_path).get('reusable') is not True:
            return 'source_quality_final_audit_not_reusable'
    summary = source.get('summary')
    generation = source.get('source')
    if (source.get('status') not in {'pass', 'warning'}
        or not isinstance(summary, dict)
        or summary.get('tuning_input_allowed') is not True
        or not isinstance(generation, dict)
        or generation.get('generation_stable') is not True):
        return 'source_quality_preflight_blocked'
    raw_path = generation.get('pipeline_events')
    raw_generation = generation.get('generation')
    raw_root = Path(report_dir).parent / 'pipeline_events'
    allowed_raw = {raw_root / f'pipeline_events_{day}.jsonl',
                   raw_root / f'pipeline_events_{day}.jsonl.gz'}
    if (not isinstance(raw_path, str) or not isinstance(raw_generation, dict)
        or Path(raw_path).resolve() not in {path.resolve() for path in allowed_raw}):
        return 'source_quality_preflight_raw_identity_invalid'
    try:
        stat = Path(raw_path).stat()
    except OSError:
        return 'source_quality_preflight_raw_generation_changed'
    if any(getattr(stat, stat_field) != raw_generation.get(receipt_field)
           for stat_field, receipt_field in (
               ('st_dev', 'device'), ('st_ino', 'inode'),
               ('st_size', 'size_bytes'), ('st_mtime_ns', 'mtime_ns'),
               ('st_ctime_ns', 'ctime_ns'))):
        return 'source_quality_preflight_raw_generation_changed'
    return None


def _existing_incumbent_winrate_binding_valid(report, staged, bundle, previous, runtime_policy,
                                              staged_bundle=None, data_root=None):
    """Validate a fresh carry evaluation against an already staged immutable bundle."""
    if not all(isinstance(value, dict) for value in (report, staged, bundle, previous)):
        return False
    try:
        previous_machine = runtime_policy.for_cohort(
            previous, ('KRX', 'KRX_REGULAR')
        )['machine_policy']
        existing_machine = runtime_policy.for_cohort(
            bundle, ('KRX', 'KRX_REGULAR')
        )['machine_policy']
        machine_sha = runtime_policy.digest(previous_machine)
    except (KeyError, TypeError, ValueError):
        return False
    proof = bundle.get('winrate_selection') or {}
    staged_hash = staged.get('bundle_sha256')
    same_generation = bundle.get('bundle_sha256') == staged_hash
    preserving_descendant = bundle.get('bundle_sha256') == staged_hash
    if isinstance(staged_bundle, dict):
        preserving_descendant = preserving_descendant or (
            staged_bundle.get('bundle_sha256') == staged_hash
            and staged_bundle.get('target_date') == staged.get('target_date')
            and bundle.get('previous_bundle_sha256') == staged_hash
            and bundle.get('winrate_selection') == staged_bundle.get('winrate_selection')
            and runtime_policy.for_cohort(bundle, ('KRX', 'KRX_REGULAR'))['machine_policy']
                == runtime_policy.for_cohort(staged_bundle, ('KRX', 'KRX_REGULAR'))['machine_policy']
        )
    if not preserving_descendant and data_root is not None:
        current = bundle
        expected_proof = bundle.get('winrate_selection')
        expected_machine = existing_machine
        seen = {bundle.get('bundle_sha256')}
        # A bounded chain permits independently receipted same-policy refreshes
        # while rejecting a reparented or policy-changing generation.
        for _ in range(8):
            parent_hash = current.get('previous_bundle_sha256')
            if (not isinstance(parent_hash, str) or len(parent_hash) != 64
                or parent_hash in seen):
                break
            seen.add(parent_hash)
            parent_path = (runtime_policy.root(Path(data_root)) / 'generations'
                           / f'{parent_hash}.json')
            try:
                parent_generation = runtime_policy._read(parent_path)
                runtime_policy.validate(parent_generation, target_date=staged.get('target_date'))
                runtime_policy._validate_bundle_sources(parent_generation, Path(data_root))
                parent_machine = runtime_policy.for_cohort(
                    parent_generation, ('KRX', 'KRX_REGULAR'))['machine_policy']
            except (OSError, ValueError, TypeError, KeyError, AttributeError):
                break
            if (parent_generation.get('bundle_sha256') != parent_hash
                or parent_generation.get('target_date') != staged.get('target_date')
                or parent_generation.get('winrate_selection') != expected_proof
                or parent_machine != expected_machine):
                break
            if parent_hash == staged_hash:
                preserving_descendant = True
                break
            current = parent_generation
    return (
        staged.get('current_report_sha256') == report.get('artifact_content_sha256')
        and staged.get('bundle_report_sha256') == proof.get('report_sha256')
        and staged.get('previous_bundle_sha256') == report.get('parent_bundle_sha256')
        and proof.get('disposition') == 'incumbent_carried'
        and proof.get('policy_version') == report.get('policy_version')
        and proof.get('parent_bundle_sha256') == report.get('parent_bundle_sha256')
        and proof.get('machine_policy_sha256') == machine_sha
        and report.get('disposition') == 'incumbent_carried'
        and report.get('candidate_policy') is None
        and (same_generation or preserving_descendant)
        and previous.get('bundle_sha256') == report.get('parent_bundle_sha256')
        and bundle.get('machine_policy') == previous_machine
        and existing_machine == previous_machine
        and staged.get('machine_policy_sha256') == machine_sha
        and report.get('parent_machine_policy_sha256') == machine_sha
    )


def _staged_winrate_generation_preserved(staged, bundle, runtime_policy, data_root,
                                        *, generation_only=False):
    """Accept a later same-policy bundle only with an intact archived parent chain."""
    expected = staged.get('bundle_sha256')
    if bundle.get('bundle_sha256') == expected:
        return True
    current = bundle
    seen = {current.get('bundle_sha256')}
    proof = current.get('winrate_selection')
    machine = runtime_policy.for_cohort(current, ('KRX', 'KRX_REGULAR'))['machine_policy']
    for _ in range(8):
        parent_hash = current.get('previous_bundle_sha256')
        if not isinstance(parent_hash, str) or len(parent_hash) != 64 or parent_hash in seen:
            return False
        seen.add(parent_hash)
        path = runtime_policy.root(Path(data_root)) / 'generations' / f'{parent_hash}.json'
        try:
            if generation_only and (path.is_symlink() or path.stat().st_size > FAMILY_ARTIFACT_MAX_BYTES):
                return False
            parent = runtime_policy._read(path)
            if generation_only:
                # The caller fully validates the current bundle. Ancestors must
                # retain its exact machine/proof below; do not rerun the same
                # policy coordinate validation at each archived generation.
                if (parent.get('bundle_sha256') != runtime_policy.digest({
                        k: v for k, v in parent.items() if k != 'bundle_sha256'})
                    or parent.get('target_date') != staged.get('target_date')
                    or any(parent.get(k) != bundle.get(k) for k in (
                        'schema', 'cohort', 'role_contract', 'adoption_basis',
                        'actual_order_submitted', 'hard_guards_unchanged'))):
                    return False
            else:
                runtime_policy.validate(parent, target_date=staged.get('target_date'))
            runtime_policy._validate_bundle_sources(parent, Path(data_root))
            parent_machine = runtime_policy.for_cohort(parent, ('KRX', 'KRX_REGULAR'))['machine_policy']
        except (OSError, ValueError, TypeError, KeyError, AttributeError):
            return False
        if (parent.get('bundle_sha256') != parent_hash
            or parent.get('winrate_selection') != proof
            or parent_machine != machine):
            return False
        if parent_hash == expected:
            return True
        current = parent
    return False


def _stage_output_issues(report_dir, day, stage):
    from src.engine.automation.postclose_recommendation_intake import _report_date
    errors = []
    for name, path in stage_artifacts(report_dir, day, stage).items():
        if (name == 'ai_decision_outcome_labels'
            and path.with_suffix(path.suffix + '.gz').exists()):
            from src.engine.scalping.micro_reversion.storage_maintenance import _read_owned_bytes
            value = json.loads(_read_owned_bytes(path))
            if not isinstance(value, dict):
                value = {}
        else:
            value = _load_json(path)
        if not value or (_report_date(value) or value.get('source_date') or value.get('end_date')) != day:
            errors.append(f'{stage}:invalid_output:{name}')
        elif str(value.get('status', '')).lower() in {'failed', 'error', 'running', 'waiting', 'searching_train', 'pending'}:
            errors.append(f'{stage}:incomplete_output:{name}')
        if name.startswith('main_fixed_watch_policy_research'):
            from src.engine.monitoring.main_fixed_watch_policy_research import validate_report
            try:
                validate_report(value, source_date=day)
                expected_symbol = '034020' if name == 'main_fixed_watch_policy_research' else name.rsplit('_', 1)[-1]
                if value['symbol'] != expected_symbol:
                    raise ValueError('fixed_watch_research_symbol_mismatch')
            except (OSError, ValueError, KeyError, TypeError):
                errors.append(f'{stage}:fixed_watch_research_contract_invalid')
        if name == 'machine_policy_terminal' and value.get('status') not in {'completed', 'source_gap'}:
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
        if name == 'research_native_capacity':
            from src.engine.monitoring.research_native_capacity_source import validate_existing
            native = validate_existing(date.fromisoformat(day), directory=Path(report_dir).parent / 'runtime' / 'machine_research_closed_loop')
            if native.get('status') != 'complete':
                errors.append(f'{stage}:native_source_invalid:{native.get("reason")}')
        if name in {'episode_policy_refresh'}:
            from src.engine.monitoring.research_closed_loop import digest, read_object
            if (value.get('receipt_sha256') != digest({k:v for k,v in value.items() if k != 'receipt_sha256'})
                or value.get('source_sha256') != digest(read_object(Path(value.get('source_path') or ''), limit=FAMILY_ARTIFACT_MAX_BYTES))
                or value.get('policy_sha256') != digest(read_object(Path(value.get('policy_path') or ''), limit=FAMILY_ARTIFACT_MAX_BYTES))):
                errors.append(f'{stage}:family_publication_invalid')
        if name == 'machine_research_closed_loop':
            from src.engine.automation.machine_research_closed_loop_refresh import validate_current_receipt
            if not validate_current_receipt(value, day):
                errors.append(f'{stage}:allocation_receipt_invalid')
    if stage == 'main_machine_policy':
        paths = stage_artifacts(report_dir, day, stage)
        report, terminal = _load_json(paths['machine_policy']), _load_json(paths['machine_policy_terminal'])
        from src.engine.scalping.ai_action_outcome_calibration import (
            MACHINE_COMPLETED_PRICE_CACHE_SCHEMA, _artifact_content_sha256_valid,
        )
        source_counts = report.get('observation_source_counts') or {}
        if not isinstance(source_counts, dict):
            errors.append(f'{stage}:completed_price_source_receipts_invalid')
            source_counts = {}
        receipts = source_counts.get('completed_price_cache_receipts') or []
        if not isinstance(receipts, list):
            errors.append(f'{stage}:completed_price_source_receipts_invalid')
            receipts = []
        for receipt in receipts:
            if not isinstance(receipt, dict):
                errors.append(f'{stage}:completed_price_source_receipts_invalid')
                continue
            if not receipt.get('artifact_content_sha256'):
                if receipt.get('status') not in {'cache_missing', 'cache_missing_or_invalid'}:
                    errors.append(f'{stage}:completed_price_source_receipts_invalid')
                continue
            source_day = receipt.get('source_date')
            if not isinstance(source_day, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', source_day) or source_day > day:
                errors.append(f'{stage}:completed_price_source_date_invalid')
                continue
            expected_path = (Path(report_dir).parent / 'report' / 'machine_completed_price_source'
                             / f'machine_completed_price_source_{source_day}.json')
            if (not isinstance(receipt.get('path'), str)
                or Path(receipt['path']).resolve() != expected_path.resolve()):
                errors.append(f'{stage}:completed_price_source_path_invalid')
                continue
            cache = _load_json(expected_path)
            if (cache.get('schema') != MACHINE_COMPLETED_PRICE_CACHE_SCHEMA
                or cache.get('source_date') != source_day
                or not _artifact_content_sha256_valid(cache)
                or cache.get('artifact_content_sha256') != receipt['artifact_content_sha256']):
                errors.append(f'{stage}:completed_price_source_generation_changed')
        if (terminal.get('report_sha256') != report.get('artifact_content_sha256')
            or terminal.get('policy_sha256') != report.get('policy_sha256')):
            errors.append(f'{stage}:report_terminal_binding_invalid')
        if terminal.get('status') == 'source_gap' and report.get('selection_basis') != 'win_rate_only':
            errors.append(f'{stage}:source_gap_contract_invalid')
        if report.get('selection_basis') == 'win_rate_only':
            from src.engine.scalping import mechanistic_entry_runtime_policy as runtime_policy
            staged = terminal.get('staged') or {}
            counts = report.get('excluded_attempt_counts') or {}
            market_counts_valid = runtime_policy.winrate_market_census_valid(report)
            if (report.get('schema') != 'main_entry_winrate_policy_report_v1'
                or (report.get('observation_status') == 'source_gap' and
                    (terminal.get('status') != 'source_gap' or report.get('accepted_attempt_count') != 0
                     or report.get('candidate_policy') is not None))
                or (report.get('observation_status') != 'source_gap' and terminal.get('status') != 'completed')
                or report.get('disposition') not in {'initial_adopted', 'successor_selected', 'incumbent_carried'}
                or terminal.get('disposition') != report.get('disposition')
                or staged.get('status') not in {'staged', 'already_staged', 'pending_initial_preserved', 'existing_incumbent_preserved', 'operator_designation_preserved', 'designated_policy_staged'}
                or type(report.get('input_attempt_count')) is not int
                or type(report.get('accepted_attempt_count')) is not int
                or type(report.get('source_contract_excluded_count')) is not int
                or any(type(value) is not int or value < 0 for value in counts.values())
                or report['accepted_attempt_count'] + report['source_contract_excluded_count']
                    + sum(counts.values()) != report.get('input_attempt_count')
                or sum((report.get('situation_attempt_counts') or {}).values()) != report['accepted_attempt_count']
                or not market_counts_valid):
                errors.append(f'{stage}:winrate_semantics_invalid')
            else:
                try:
                    if report.get('acceptance_contract') is not None:
                        from src.engine.scalping.entry_admission_acceptance import validate_source
                        validate_source(report)
                    bundle = runtime_policy.load(data_root=Path(report_dir).parent,
                        target_date=staged['target_date'])
                    proof = (bundle or {}).get('winrate_selection') or {}
                    pending = staged['status'] == 'pending_initial_preserved'
                    reused_incumbent = staged['status'] == 'existing_incumbent_preserved'
                    designated = proof.get('schema') == 'main_machine_designated_selection_v1'
                    if designated:
                        from src.engine.scalping.entry_designated_policy import binding_valid
                        binding_invalid = (not binding_valid(report, bundle, Path(report_dir).parent)
                            or staged.get('bundle_sha256') != bundle['bundle_sha256'])
                    elif reused_incumbent:
                        previous = runtime_policy.load_effective(
                            data_root=Path(report_dir).parent,
                            target_date=report.get('publication_date'),
                        )
                        binding_invalid = not _existing_incumbent_winrate_binding_valid(
                            report, staged, bundle, previous, runtime_policy,
                            data_root=Path(report_dir).parent,
                        )
                    else:
                        binding_invalid = (
                            not _staged_winrate_generation_preserved(
                                staged, bundle, runtime_policy, Path(report_dir).parent)
                            or proof.get('machine_policy_sha256') != runtime_policy.digest(bundle['machine_policy'])
                        )
                    if (binding_invalid
                        or (pending and (report.get('pending_initial_bundle_sha256') != bundle['bundle_sha256']
                            or report.get('pending_initial_target_date') != staged['target_date']
                            or report.get('hurdle_errors') != ['initial_policy_pending_activation']
                            or report['disposition'] != 'incumbent_carried'
                            or proof.get('disposition') != 'initial_adopted'
                            or proof.get('policy_version') != 'winrate_initial_v1'
                            or proof.get('parent_bundle_sha256') != report.get('parent_bundle_sha256')
                            or bundle.get('previous_bundle_sha256') != report.get('parent_bundle_sha256')
                            or (bundle['machine_policy'].get('entry_situation_veto') or {}).get('threshold_bp') != 68.75))
                        or (not pending and not reused_incumbent and not designated
                            and (proof.get('report_sha256') != report.get('artifact_content_sha256')
                            or proof.get('disposition') != report['disposition']))):
                        errors.append(f'{stage}:winrate_staged_binding_invalid')
                except (OSError, ValueError, TypeError, KeyError, AttributeError):
                    errors.append(f'{stage}:winrate_staged_binding_invalid')
    if stage == 'pre_submit_delay':
        from src.engine.scalping.pre_submit_delay_tuning import _digest, price_pattern_projection
        paths = stage_artifacts(report_dir, day, stage)
        report = _load_json(paths['pre_submit_delay_tuning'])
        policy = _load_json(paths['pre_submit_delay_policy'])
        if (report.get('schema') != 'pre_submit_delay_tuning_v1'
            or policy.get('schema') != 'pre_submit_delay_policy_v1'
            or report.get('source_date') != day or policy.get('source_date') != day
            or report.get('effective_date') != policy.get('effective_from')
            or report.get('policy_sha256') != policy.get('policy_sha256')
            or policy.get('report_sha256') != _digest({k:v for k,v in report.items() if k != 'policy_sha256'})
            or policy.get('policy_sha256') != _digest({k:v for k,v in policy.items() if k != 'policy_sha256'})):
            errors.append(f'{stage}:report_policy_binding_invalid')
        if price_pattern_projection(report)['status'] == 'source_invalid':
            errors.append(f'{stage}:price_pattern_contract_invalid')
    return errors


def _safe_stage_output_issues(report_dir, day, stage):
    try:
        return _stage_output_issues(report_dir, day, stage)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        return [f'{stage}:output_validation_failed:{type(exc).__name__}']


def stage_commands(stage, day, publication, *, recovery=False):
    import sys
    from src.engine.build_next_stage2_checklist import _next_krx_trading_day
    prefix = [sys.executable, '-m']
    def command(module, *args):
        return prefix + ['src.engine.' + module, *args]
    def fixed_watch_commands():
        if day < '2026-10-06':
            return []
        from src.engine.scalping.main_fixed_watch import SPECS
        return [command('monitoring.main_fixed_watch_policy_research', '--source-date', day,
                        '--publication-date', publication, '--symbol', spec.symbol)
                for spec in SPECS if spec.initial_policy_scope == 'non_samsung']
    date_args = ['--target-date', day, '--write']
    if stage == 'main_machine_policy' and recovery:
        return fixed_watch_commands()
    if stage == 'main_machine_policy':
        return [command('scalping.ai_action_outcome_calibration', *date_args,
                        '--winrate-policy-only', '--admission-recipe', 'pullback_p60_v0',
                        '--publication-date', publication)] + fixed_watch_commands()
    if stage == 'pre_submit_delay':
        return [command('scalping.pre_submit_delay_tuning', '--date', day,
                        '--effective-date', _next_krx_trading_day(publication), '--require-family-ledger')]
    if stage == 'legacy_machine_report':
        return [command('scalping.ai_action_outcome_calibration', *date_args, '--machine-only', '--publication-date', publication, '--activate-now')]
    if stage == 'main_auxiliary_policy':
        common = ['--date', day, '--compact-only', '--write']
        return [command('scalping.entry_setup_paired_replay_batch', *common, '--execute-compact-candidate'),
                command('scalping.entry_setup_paired_replay_batch', *common, '--finalize-compact', '--publication-date', publication)]
    if stage == 'outcome_labels':
        return [command('scalping.ai_decision_quality', '--date', day, '--mode', 'postclose', '--write')]
    if stage == 'episode_policy':
        study = [] if recovery else [command('monitoring.low_price_two_leg_expanded_candidate_research', *date_args)]
        return study + [command('automation.machine_research_closed_loop_refresh', '--source-date', day, '--family', 'episode', '--write', '--source-wait-sec', '0')]
    modules = dict(
        machine_attribution='monitoring.machine_microstructure_attribution', machine_timing='automation.machine_entry_timing_tuning',
        market_weakness='automation.market_weakness_hysteresis_tuning', legacy_policy_approval='automation.machine_microstructure_policy_approval')
    if stage in modules:
        extra = ['--phase', 'postclose'] if stage == 'legacy_policy_approval' else []
        return [command(modules[stage], *date_args, *extra)]
    if stage == 'research_capacity':
        return [] if recovery else [command('monitoring.research_native_capacity_source', '--source-date', day, '--write')]
    if stage == 'research_allocation':
        return [command('automation.machine_research_closed_loop_refresh', '--source-date', day, '--family', 'allocation', '--write', '--source-wait-sec', '0')]
    return [command('automation.postclose_done_controller', '--date', day, '--summary-handoff-only', '--require-independent-producers')]


def _stage_code(stage, commands, project, *, dispatcher_path=None,
                legacy_main_machine=False):
    paths = {'dispatcher': Path(dispatcher_path or __file__)}
    for cmd in commands:
        if '-m' in cmd:
            module = cmd[cmd.index('-m') + 1]
            paths[module] = project / (module.replace('.', '/') + '.py')
        elif cmd[0] == '/bin/bash':
            paths[cmd[1]] = project / cmd[1]
    if stage in {'episode_policy', 'research_allocation'}:
        from src.engine.automation.machine_research_closed_loop_refresh import code_contract
        return _stage_digest([_stage_sources(paths), code_contract()])
    if stage == 'summary_handoff':
        paths['next_stage2_checklist'] = project / 'src/engine/build_next_stage2_checklist.py'
        paths['direct_tower'] = project / 'src/engine/automation/tuning_performance_control_tower.py'
    if stage == 'research_capacity':
        paths['native_capacity'] = project / 'src/engine/monitoring/research_native_capacity_source.py'
    if stage == 'main_machine_policy':
        if not legacy_main_machine:
            paths['main_fixed_watch_research'] = project / 'src/engine/monitoring/main_fixed_watch_policy_research.py'
            paths['fixed_watch_runtime'] = project / 'src/engine/scalping/main_fixed_watch.py'
            paths['owner_retirement'] = project / 'src/trading/config/owner_retirement.py'
        for name in ('entry_strategy_policy', 'entry_setup_evidence', 'ai_decision_quality', 'entry_candle_context', 'mechanistic_entry_runtime_policy',
                     'entry_admission_analysis', 'entry_admission_acceptance', 'entry_admission_recipe', 'entry_designated_policy'):
            paths[name] = project / f'src/engine/scalping/{name}.py'
    return _stage_digest(_stage_sources(paths))


def run_stage(stage, day, *, report_dir, project, publication=None, effective=None,
              recovery=False, execute=True, runner=None, timeout=14400, off=False,
              prerequisite_wait=0, stop_event=None, resource_blocked=None):
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
        if (resource_blocked is not None and old.get('status') == 'succeeded'
            and not stage_receipt_issues(report_dir, day, stage, code_hash=code)
            and old.get('publication_date') == publication
            and old.get('effective_date') == effective):
            return {**old, 'cache_reused': True}
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
        if stage == 'summary_handoff':
            # Summary/PREOPEN reconciliation belongs to the original source
            # day even if policy publication and recovery occur later.
            value['prepared_effective_date'] = _next_krx_trading_day(day)
        if old:
            _stage_write(path.parent / 'attempts' / f'{stage}_{old.get("run_id", uuid.uuid4().hex)}.json', old)
        if off:
            return _stage_write(path, {**value, 'status':'off', 'off_reason':'explicit_schedule_disabled', 'exit_code':0})
        if resource_blocked is not None:
            if stage != 'main_machine_policy' or not isinstance(resource_blocked, dict) or resource_blocked.get('ok') is not False:
                raise ValueError('resource_blocked_receipt_invalid')
            return _stage_write(path, {**value, 'status':'deferred', 'exit_code':75,
                'issues':['resource_guard_timeout'], 'policy_disposition':'source_gap',
                'resource_guard':resource_blocked, 'finished_at':now()})
        prerequisites = {s:stage_path(report_dir, day, s) for s in STAGE_REGISTRY[stage][0]}
        wait_deadline = time.monotonic() + prerequisite_wait
        while True:
            if stop_event is not None and stop_event.is_set():
                return _stage_write(path, {**value, 'status':'deferred', 'exit_code':75, 'issues':['stage_interrupted_at_saved_checkpoint']})
            issues = [e for s in prerequisites for e in stage_receipt_issues(report_dir, day, s)]
            waiting = any(_load_json(p).get('status', 'pending') in {'pending', 'running'} for p in prerequisites.values())
            terminal_blocked = any(
                _load_json(p).get('status', 'pending') not in {'pending', 'running'}
                and stage_receipt_issues(report_dir, day, s)
                for s, p in prerequisites.items()
            )
            if not issues or terminal_blocked or not waiting or time.monotonic() >= wait_deadline:
                break
            _stage_write(path, {**value, 'heartbeat_at':now(), 'reason':'prerequisite_pending', 'issues':issues})
            time.sleep(min(5, max(0, wait_deadline - time.monotonic())))
        value['prerequisite_receipts'] = _stage_sources(prerequisites)
        if issues:
            return _stage_write(path, {**value, 'status':'deferred', 'exit_code':75, 'issues':issues, 'policy_disposition':'source_gap'})
        if stage == 'main_machine_policy':
            preflight_issue = _machine_source_preflight_issue(report_dir, day, recovery=recovery)
            if preflight_issue:
                return _stage_write(path, {**value, 'status':'deferred', 'exit_code':75,
                    'issues':[preflight_issue], 'policy_disposition':'source_quality_blocked',
                    'finished_at':now()})
            preflight_path = (Path(report_dir) / 'observation_source_quality_audit'
                              / f'observation_source_quality_audit_{day}.json')
            value['source_quality_preflight_sha256'] = hashlib.sha256(preflight_path.read_bytes()).hexdigest()
            value['source_quality_audit_phase'] = _load_json(preflight_path).get('audit_phase')
            binding_path = Path(str(preflight_path) + '.final-contract.json')
            if _load_json(binding_path).get('artifact_sha256') != value['source_quality_preflight_sha256']:
                return _stage_write(path, {**value, 'status':'deferred', 'exit_code':75,
                    'issues':['source_quality_preflight_changed_before_consumption'],
                    'policy_disposition':'source_quality_blocked', 'finished_at':now()})
        if stage == 'pre_submit_delay':
            from src.engine.scalping.pre_submit_delay_tuning import seal_family_source_ledger, family_source_ledger_issues
            try:
                source_manifest = seal_family_source_ledger(Path(report_dir).parent, day)
                source_issues = family_source_ledger_issues(Path(report_dir).parent, day)
                if source_issues:
                    raise ValueError(','.join(source_issues))
                value['pipeline_source_generation_sha256'] = source_manifest['ledger_sha256']
            except (OSError, ValueError, KeyError, TypeError) as exc:
                return _stage_write(path, {**value, 'status':'deferred', 'exit_code':75,
                    'issues':[f'pipeline_source_quality:{exc}'], 'policy_disposition':'source_gap',
                    'finished_at':now()})
        if not execute:
            # Review-only intake is explicit: validates existing artifacts, never
            # claims that their calculation was executed by this new runner.
            value['input_sources'] = _stage_sources(stage_input_paths(report_dir, day, stage))
            issues = _safe_stage_output_issues(report_dir, day, stage)
            return _stage_write(path, {**value, 'sources':_stage_sources(stage_artifacts(report_dir, day, stage)),
                'status':'failed' if issues else 'succeeded', 'exit_code':1 if issues else 0,
                'issues':issues, 'execution_mode':'existing_output_validation', 'finished_at':now()})
        value['input_sources'] = _stage_sources(stage_input_paths(report_dir, day, stage))
        # Host-wide admission shared across independent scheduled wrappers.
        slots = Path(report_dir).parent / 'runtime' / 'postclose_stage_slots'; slots.mkdir(parents=True, exist_ok=True)
        slot = None; admission_started = time.monotonic(); deadline = admission_started + timeout
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
            value['resource_admission_wait_sec'] = round(time.monotonic() - admission_started, 3)
            value.update(status='running', heartbeat_at=now()); _stage_write(path, value)
            env = {**os.environ, 'PYTHONPATH':str(project), 'POSTCLOSE_STAGE_WORKER':'1', 'POSTCLOSE_SOURCE_DATE':day,
                'POSTCLOSE_POLICY_PUBLICATION_DATE':publication,
                'POSTCLOSE_PREPARED_EFFECTIVE_DATE':value.get('prepared_effective_date', effective)}
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
            if stage == 'research_capacity' and not rc:
                # Native files are produced by this command on the current
                # source date; bind their final generation to the stage.
                value['input_sources'] = _stage_sources(stage_input_paths(report_dir, day, stage))
            issues = _safe_stage_output_issues(report_dir, day, stage) if not rc else [f'command_exit:{rc}']
            if value['prerequisite_receipts'] != _stage_sources(prerequisites): issues.append('prerequisite_changed_during_consumption')
            if value['input_sources'] != _stage_sources(stage_input_paths(report_dir, day, stage)): issues.append('input_changed_during_consumption')
            if stage == 'main_machine_policy':
                preflight_path = (Path(report_dir) / 'observation_source_quality_audit'
                                  / f'observation_source_quality_audit_{day}.json')
                preflight_issue = _machine_source_preflight_issue(report_dir, day, recovery=recovery)
                try:
                    current_preflight_sha = hashlib.sha256(preflight_path.read_bytes()).hexdigest()
                except OSError:
                    current_preflight_sha = None
                if (preflight_issue or current_preflight_sha != value.get('source_quality_preflight_sha256')):
                    issues.append('source_quality_preflight_changed_during_consumption')
            if stage == 'pre_submit_delay':
                from src.engine.scalping.pre_submit_delay_tuning import family_source_ledger_issues
                issues.extend(f'pipeline_source_quality:{issue}' for issue in
                              family_source_ledger_issues(Path(report_dir).parent, day))
            machine_gap = (stage == 'main_machine_policy' and not rc and not issues and
                _load_json(stage_artifacts(report_dir, day, stage)['machine_policy_terminal']).get('status') == 'source_gap')
            if machine_gap:
                issues.append('machine_observation_source_gap')
            value.update(status='deferred' if machine_gap or rc == 75 else 'failed' if rc or issues else 'succeeded',
                exit_code=75 if machine_gap else rc or (1 if issues else 0), issues=issues, finished_at=now(), heartbeat_at=now(),
                sources=_stage_sources(stage_artifacts(report_dir, day, stage)))
            if stage == 'main_machine_policy' and (not issues or machine_gap):
                terminal = _load_json(stage_artifacts(report_dir, day, stage)['machine_policy_terminal'])
                staging = terminal.get('staged') or {}
                activation = (terminal.get('activation') or {}).get('status')
                value['policy_disposition'] = ('source_gap' if machine_gap else terminal.get('disposition')
                    if terminal.get('selection_basis') == 'win_rate_only' and staging.get('status') in {'staged', 'already_staged', 'pending_initial_preserved', 'existing_incumbent_preserved'}
                    else 'operator_designated' if staging.get('status') in {'operator_designation_preserved', 'designated_policy_staged'}
                    else 'updated' if activation == 'activated' else 'incumbent_carry' if activation in {'already_active', 'incumbent_carry'} else 'no_valid_candidate')
                if staging.get('status') in {'operator_designation_preserved', 'designated_policy_staged'}:
                    value['automatic_policy_disposition'] = terminal.get('disposition')
                    value['designated_bundle_sha256'] = staging.get('bundle_sha256')
                value['policy_sha256'] = terminal.get('policy_sha256')
            if stage in {'episode_policy'} and not issues:
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
    states = {s:_load_json(stage_path(report_dir, day, s)) for s in active_stage_names(day)}
    issues = {s:stage_receipt_issues(report_dir, day, s, allow_historical_terminal=True)
              for s in states if s != 'summary_handoff'}
    # Startup evidence has its own date and contract, independent of diagnostics.
    from src.engine.build_next_stage2_checklist import _next_krx_trading_day
    effective = _next_krx_trading_day(day)
    bootstrap = _load_json(Path(report_dir).parent / 'runtime' / 'policy_bootstrap' / f'runtime_policy_bootstrap_verify_{effective}.json')
    ready = bootstrap.get('passed') is True and bootstrap.get('target_date') == effective
    if ready:
        from src.engine.automation.runtime_policy_bootstrap import verify_bootstrap, manifest_path
        ready = (manifest_path(effective).parent.resolve() == (Path(report_dir).parent / 'runtime' / 'policy_bootstrap').resolve()
            and verify_bootstrap(effective, write=False).get('passed') is True)
    startup_basis = 'dated_live_bootstrap' if ready else 'unverified'
    if not ready:
        # Before PREOPEN, only the isolated preparation exists. Its owner
        # rechecks the current whole-chain, policies and selected release.
        # Never create or activate tomorrow's live bootstrap here.
        from src.engine.automation.next_preopen_readiness import verify_prepared
        prepared_index = (Path(report_dir).parent / 'runtime' / 'policy_bootstrap' /
                          'prepared' / effective / 'latest.json')
        if prepared_index.is_file():
            try:
                prepared = verify_prepared(effective)
                receipt = _load_json(Path(str(_load_json(prepared_index).get('receipt_path') or '')))
                ready = prepared.get('status') == 'pass' and receipt.get('source_date') == day
                if ready:
                    startup_basis = 'isolated_prepared_next_preopen'
            except (OSError, ValueError, TypeError, KeyError):
                ready = False
    policy_checks = {}
    from src.engine.scalping.mechanistic_entry_runtime_policy import load_effective
    from src.engine.automation.low_price_two_leg_auto_expansion_policy import load_policy
    data_root = Path(report_dir).parent
    try: policy_checks['main'] = bool(load_effective(data_root=data_root, target_date=effective))
    except (OSError, ValueError, TypeError, KeyError): policy_checks['main'] = False
    try: policy_checks['episode'] = bool(load_policy(date.fromisoformat(effective), policy_dir=data_root / 'runtime' / 'low_price_two_leg_auto_expansion'))
    except (OSError, ValueError, TypeError, KeyError): policy_checks['episode'] = False
    episode_authority = 'dated_policy' if policy_checks['episode'] else 'missing'
    episode_state = states.get('episode_policy') or {}
    if (not policy_checks['episode'] and episode_state.get('status') == 'off'
        and episode_state.get('off_reason') == 'explicit_schedule_disabled'
        and not issues.get('episode_policy')):
        policy_checks['episode'] = True
        episode_authority = 'explicit_schedule_disabled'
    ready = ready and all(policy_checks.values())
    future_handoff = {"status": "not_applicable", "actual_pid_consumed": False}
    if day >= "2026-09-23":
        summary = _load_json(Path(report_dir) / "runtime_approval_summary" /
                             f"runtime_approval_summary_{day}.json")
        future_handoff = inspect_future_handoff(summary, day, report_dir=report_dir)
        ready = ready and (startup_basis == 'isolated_prepared_next_preopen' or future_handoff["status"] in {
            "same_generation_no_pid", "transitioned_no_pid",
            "same_generation_pid_receipt_unconfirmed",
        })
    return dict(schema='postclose_stage_overview_v2', source_date=day, effective_date=effective,
        stages={s:dict(status=v.get('status', 'pending'), issues=issues.get(s, []), policy_disposition=v.get('policy_disposition')) for s,v in states.items()},
        postclose_all_active_stages_complete=not any(issues.values()) and states['summary_handoff'].get('status') == 'succeeded',
        next_session_policy_ready=ready, policy_loader_checks=policy_checks,
        future_handoff=future_handoff,
        episode_policy_authority=episode_authority,
        startup_basis=startup_basis, day_of_activation_required=startup_basis == 'isolated_prepared_next_preopen',
        actual_pid_consumed=False,
        startup_contract='prepared_verified' if startup_basis == 'isolated_prepared_next_preopen' else bootstrap.get('status', 'not_verified'))


def _stage_main(argv):
    import argparse, sys
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
    parser.add_argument('--resource-guard-status')
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
        # The checklist binds every producer receipt, including independent
        # stages. Rendering while any producer still updates its heartbeat
        # would invalidate the generation immediately after publication.
        # Summary/controller is the later consumer, never its own predecessor.
        required = tuple(stage for stage in active_stage_names(day)
                         if stage != 'summary_handoff')
        while any(_load_json(stage_path(DATA_DIR / 'report', day, s)).get('status', 'pending') in {'pending','running'} for s in required):
            if time.monotonic() >= deadline: return 75
            if stop_event.is_set(): return 75
            time.sleep(1)
        return 0
    if args.check:
        status = _load_json(stage_path(DATA_DIR / 'report', day, args.stage)).get('status', 'pending')
        if status in {'pending', 'running', 'deferred'}: return 75
        return 1 if stage_receipt_issues(DATA_DIR / 'report', day, args.stage) else 0
    if args.resource_guard_status is not None and (args.stage != 'main_machine_policy' or args.launch or args.off):
        parser.error('resource_guard_status_requires_machine_terminal')
    if args.launch:
        subprocess.Popen([sys.executable, '-m', 'src.engine.automation.postclose_summary_handoff', *[a for a in argv if a != '--launch']],
            cwd=PROJECT_ROOT, start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return 0
    if args.stage == 'overview':
        print(json.dumps(stage_overview(DATA_DIR / 'report', day))); return 0
    def run(s):
        resource_blocked = None
        if args.resource_guard_status is not None:
            try:
                resource_blocked = json.loads(args.resource_guard_status)
            except json.JSONDecodeError:
                parser.error('resource_guard_status_invalid_json')
        return run_stage(s, day, report_dir=DATA_DIR / 'report', project=PROJECT_ROOT,
            publication=args.publication_date, recovery=args.recover_closed_target,
            execute=not args.validate_existing, timeout=args.timeout_sec,
            off=args.off or (s == 'research_allocation' and
                             _joint_research_peer_off(DATA_DIR / 'report', day)),
            # Native recovery launches Main and compact together. Compact must
            # wait for that live predecessor outside the compute slot; zero
            # wait would defer it permanently before Main can finish.
            prerequisite_wait=(args.timeout_sec if s == 'main_auxiliary_policy'
                               else 0) if args.recover_closed_target else args.timeout_sec,
            stop_event=stop_event, resource_blocked=resource_blocked)
    if args.stage == 'machine_group':
        # Finish refreshed parents before launching their consumers. Otherwise
        # a consumer can accept the previous succeeded parent receipt before
        # the concurrent parent has published its new pending/running state.
        # The existing host-wide two-child compute limit remains unchanged.
        results=[run('research_capacity')]
        with ThreadPoolExecutor(max_workers=6) as pool:
            parents = ('machine_attribution',)
            results += list(pool.map(run, parents))
            children = tuple(stage for stage in STAGE_OWNER_GROUPS['machine'][:6]
                             if stage not in parents)
            results += list(pool.map(run, children))
        results.append(run('summary_handoff'))
    else: results=[run(args.stage)]
    print(json.dumps([dict(stage=r.get('stage_id'), status=r['status'], exit_code=r['exit_code'], cache_reused=r.get('cache_reused',False)) for r in results]))
    return 1 if any(r['exit_code'] not in (0,75) for r in results) else 75 if any(r['exit_code']==75 for r in results) else 0


if __name__ == "__main__":
    import sys
    raise SystemExit(_stage_main(sys.argv[1:]) if "--stage" in sys.argv else _producer_main())
