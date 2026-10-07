from __future__ import annotations


import csv
import gzip
import glob
import hashlib
import json
import math
import os
import re
import time
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from src.utils.constants import PROJECT_ROOT
from src.utils.jsonl_io import existing_or_gzip_path
from src.utils.market_day import is_krx_trading_day

from src.engine.error_detectors.base import (
    BaseDetector,
    DetectionResult,
    register_detector,
)
from src.engine.error_detectors.schedule_contract import (
    evaluate_schedule_contract,
    load_installed_crontab,
)
from src.engine.error_detectors.cron_completion import CronCompletionDetector


def _today_kst_str(now_kst: datetime | None = None) -> str:
    return (now_kst or datetime.now()).strftime("%Y-%m-%d")


def _holding_profit_exit_semantics(root: Path, source_date: str) -> dict[str, Any]:
    """Check the sentinel's exact-date semantic receipt separately from freshness."""
    # The vote/terminal semantic payload was introduced for the next natural
    # trading session. Older sentinel files are audit history, not malformed
    # receipts under the new schema.
    if source_date < "2026-09-28":
        return {"status": "not_required_before_introduction", "findings": []}
    path = (root / "data/report/holding_exit_sentinel" /
            f"holding_exit_sentinel_{source_date}.json")
    if not path.exists() and not path.is_symlink():
        markdown = path.with_suffix(".md")
        if markdown.exists() or markdown.is_symlink():
            return {"status": "source_invalid", "findings": [
                "holding_semantic_json_missing_with_markdown_report"]}
        return {"status": "not_assessed", "findings": []}
    try:
        if path.is_symlink() or path.stat().st_size > 8 * 1024 * 1024:
            raise ValueError("untrusted_path_or_size")
        report = json.loads(path.read_text(encoding="utf-8"))
        semantics = report.get("profit_exit_semantics") or {}
        if (report.get("target_date") != source_date
                or semantics.get("target_date") != source_date
                or semantics.get("schema") != "holding_profit_exit_semantics_v1"
                or semantics.get("status") not in {
                    "pass", "valid_empty", "source_gap", "policy_binding_gap",
                    "runtime_not_consumed", "pending_terminal", "economics_null",
                    "semantic_contract_invalid",
                }):
            raise ValueError("semantic_receipt_missing_or_invalid")
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        return {"status": "source_invalid", "findings": [str(exc)]}
    status = semantics["status"]
    return {
        "status": status,
        "findings": ([status] if status in {
            "source_gap", "policy_binding_gap", "runtime_not_consumed",
            "economics_null",
            "semantic_contract_invalid"
        } else []),
        "signal_count": (semantics.get("funnel") or {}).get("tp_signal_snapshots", 0),
        "source_gap_count": len(semantics.get("source_gaps") or []),
        "invalid_count": len(semantics.get("findings") or []),
    }


def _initial_quantity_semantics(
    root: Path, source_date: str, *, now_epoch: float | None = None,
) -> dict[str, Any]:
    """Read-only quantity, sequential leg, and post-start timeout checks."""
    if source_date < "2026-09-28":
        return {"status": "not_required_before_introduction", "findings": []}
    from src.engine.scalping.initial_quantity_activation import (
        ENV_FILE, ENV_SHA, selected_initial_quantity_env,
    )
    from src.engine.scalping.initial_quantity_bundle_state import bundle_state_valid
    from src.engine.scalping.initial_quantity_policy import (
        refresh_quantity_stage_terminal_valid,
    )

    current_path = root / "data/runtime/initial_quantity/current.json"
    if not current_path.is_file() or current_path.is_symlink():
        return {"status": "source_invalid", "findings": [
            "initial_quantity_current_missing_or_untrusted"]}
    try:
        if current_path.stat().st_size > 1024 * 1024:
            raise ValueError("current_oversize")
        # Postclose may have selected tomorrow's policy already. Validate that
        # chain, then inspect the ancestor that actually applied on this date.
        seen_current: set[Path] = set()
        while True:
            if current_path in seen_current or len(seen_current) >= 32:
                raise ValueError("current_parent_cycle")
            seen_current.add(current_path)
            current = json.loads(current_path.read_text(encoding="utf-8"))
            effective = str(current.get("effective_from") or "")
            selected_initial_quantity_env(current_path, effective)
            if effective <= source_date:
                break
            parent = current.get("parent_current_file")
            if not isinstance(parent, str) or not parent:
                raise ValueError("current_parent_missing")
            current_path = Path(parent)
            if (not current_path.is_absolute() or current_path.is_symlink()
                    or not current_path.is_file()
                    or current_path.stat().st_size > 1024 * 1024):
                raise ValueError("current_parent_untrusted")
        env = selected_initial_quantity_env(current_path, source_date)
        policy_path = Path(env[ENV_FILE])
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        policy_sha = env[ENV_SHA]
        rows = policy["type_policies"]
        if not isinstance(rows, dict) or not rows:
            raise ValueError("policy_types_missing")
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        return {"status": "source_invalid", "findings": [
            "initial_quantity_current_binding_invalid:" + type(exc).__name__]}

    details: dict[str, Any] = {
        "status": "policy_selected", "findings": [],
        "policy_file_sha256": policy_sha,
        "quantity_type_count": len(rows),
        "ratio_modes": dict(Counter(
            str(row.get("ratio_mode")) for row in rows.values())),
        "selected_shapes": dict(Counter(
            str(row.get("selected_shape")) for row in rows.values())),
        "timeout_modes": dict(Counter(
            str(row.get("timeout_mode")) for row in rows.values())),
        "runtime_pid_status": "not_observed",
        "runtime_consumption_scope": "pid_env_receipt_only",
        "postclose_stage_status": "not_observed",
        "bundle_count": 0, "terminal_bundle_count": 0,
        "open_bundle_count": 0,
        "quantity_lineage_status": "not_observed",
    }
    stage_path = (root / "data/report/initial_entry_quantity_type_policy" /
                  f"refresh_postclose_{source_date}" /
                  f"initial_quantity_refresh_stage_{source_date}.json")
    if stage_path.exists() or stage_path.is_symlink():
        try:
            if stage_path.is_symlink() or stage_path.stat().st_size > 1024 * 1024:
                raise ValueError("stage_untrusted_or_oversize")
            stage = json.loads(stage_path.read_text(encoding="utf-8"))
            if not refresh_quantity_stage_terminal_valid(stage):
                raise ValueError("stage_contract_invalid")
            count = stage["all_completed_initial_trades"]
            decision = stage["decision"]
            details["postclose_stage_status"] = (
                "valid_empty" if count == 0 and decision == "carry_parent"
                else decision)
            details["postclose_completed_trade_count"] = count
        except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
            details["findings"].append(
                "initial_quantity_stage_invalid:" + type(exc).__name__)
            details["postclose_stage_status"] = "source_invalid"
    elif source_date < datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat():
        details["postclose_stage_status"] = "source_gap"
        details["findings"].append("initial_quantity_stage_missing_after_date")

    archive_dir = (root / "data/runtime/policy_bootstrap" /
                   "verified_initial_quantity_pid" / source_date)
    if archive_dir.is_symlink():
        details["findings"].append("initial_quantity_pid_archive_untrusted")
    if archive_dir.is_dir() and not archive_dir.is_symlink():
        verified = 0
        for index, receipt_path in enumerate(sorted(
                archive_dir.glob("initial_quantity_pid_*.json"))):
            if index >= 64:
                details["findings"].append("initial_quantity_pid_archive_oversize")
                break
            try:
                if (receipt_path.is_symlink()
                        or receipt_path.stat().st_size > 1024 * 1024):
                    raise ValueError("pid_receipt_untrusted_or_oversize")
                receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
                body = {k: v for k, v in receipt.items()
                        if k != "receipt_content_sha256"}
                digest = hashlib.sha256(json.dumps(
                    body, ensure_ascii=True, allow_nan=False, sort_keys=True,
                    separators=(",", ":")).encode()).hexdigest()
                verification = receipt.get("verification") or {}
                if (receipt.get("schema_version") !=
                        "initial_quantity_pid_verification_v1"
                        or receipt.get("target_date") != source_date
                        or receipt_path.name != (
                            f"initial_quantity_pid_{receipt.get('pid')}_"
                            f"{str(receipt.get('receipt_content_sha256') or '')[:12]}.json")
                        or receipt.get("policy_file_sha256") != policy_sha
                        or receipt.get("policy_file") != str(policy_path.resolve())
                        or receipt.get("policy_content_sha256") !=
                        policy.get("policy_content_sha256")
                        or receipt.get("receipt_content_sha256") != digest
                        or verification.get("target_date") != source_date
                        or verification.get("status") != "pass"
                        or verification.get("passed") is not True
                        or verification.get("pid_passed") is not True
                        or verification.get("pid_env_available") is not True
                        or verification.get("findings") != []
                        or verification.get("pid_mismatches") != []
                        or verification.get("pid") != receipt.get("pid")
                        or verification.get("manifest_sha256") !=
                        receipt.get("manifest_sha256")):
                    raise ValueError("pid_receipt_binding_invalid")
                verified += 1
            except (OSError, ValueError, TypeError, AttributeError):
                details["findings"].append("initial_quantity_pid_receipt_invalid")
        if verified:
            details["runtime_pid_status"] = "verified_receipt"
            details["verified_pid_count"] = verified
    latest_pid_path = (root / "data/runtime/policy_bootstrap" /
                       f"runtime_policy_bootstrap_verify_{source_date}.json")
    if (details["runtime_pid_status"] == "not_observed"
            and latest_pid_path.is_file() and not latest_pid_path.is_symlink()):
        try:
            if latest_pid_path.stat().st_size > 1024 * 1024:
                raise ValueError("pid_verify_oversize")
            latest = json.loads(latest_pid_path.read_text(encoding="utf-8"))
            if (latest.get("target_date") == source_date
                    and latest.get("pid_passed") is True):
                details["findings"].append("initial_quantity_pid_archive_missing")
        except (OSError, ValueError, TypeError, AttributeError):
            details["findings"].append("initial_quantity_pid_verify_invalid")

    bundle_dir = root / "data/runtime/initial_quantity/bundles"
    if bundle_dir.is_symlink():
        details["findings"].append("initial_quantity_bundle_dir_untrusted")
    if bundle_dir.is_dir() and not bundle_dir.is_symlink():
        now = time.time() if now_epoch is None else now_epoch
        for index, path in enumerate(bundle_dir.glob("*.json")):
            if index >= 5000:
                details["findings"].append("initial_quantity_bundle_inventory_oversize")
                break
            belongs_to_date = False
            try:
                if path.is_symlink() or path.stat().st_size > 1024 * 1024:
                    raise ValueError("bundle_untrusted_or_oversize")
                bundle = json.loads(path.read_text(encoding="utf-8"))
                schedule = bundle.get("schedule") or {}
                belongs_to_date = (
                    str(schedule.get("order_start_at") or "")[:10] == source_date)
                if not belongs_to_date:
                    if (not schedule.get("order_start_at")
                            and datetime.fromtimestamp(
                                path.stat().st_mtime,
                                ZoneInfo("Asia/Seoul")).date().isoformat()
                            == source_date):
                        raise ValueError("bundle_date_missing")
                    continue
                if (not bundle_state_valid(bundle)
                        or path.name != hashlib.sha256(
                            bundle["attempt_id"].encode()).hexdigest() + ".json"):
                    raise ValueError("bundle_contract_invalid")
                details["bundle_count"] += 1
                details["quantity_lineage_status"] = "journal_conservation_only"
                states = bundle["leg_states"]
                terminal = all(item["state"].startswith("TERMINAL_")
                               for item in states)
                if terminal:
                    details["terminal_bundle_count"] += 1
                else:
                    details["open_bundle_count"] += 1
                    if now > schedule["bundle_deadline_epoch"]:
                        details["findings"].append(
                            "initial_quantity_bundle_terminal_overdue")
                if any(item.get("terminal_confirmed_at_epoch", 0) >
                       schedule["slots"][index]["terminal_confirm_by_epoch"]
                       for index, item in enumerate(states)
                       if item["state"].startswith("TERMINAL_")):
                    details["findings"].append(
                        "initial_quantity_leg_terminal_after_slot")
                if bundle["policy_sha256"] != policy_sha:
                    details["findings"].append(
                        "initial_quantity_bundle_policy_mismatch")
                else:
                    row = rows.get(schedule["quantity_type"]) or {}
                    shape = row.get("selected_shape")
                    expected = (2 if str(shape).startswith("two_leg_") else
                                3 if str(shape).startswith("three_leg_") else 0)
                    if (expected == 0 or bundle["requested_qty"] < 2
                            or schedule["leg_count"] !=
                            min(bundle["requested_qty"], expected)
                            or (row.get("timeout_mode") == "selected_total_wait_sec"
                                and row.get("selected_total_wait_sec") !=
                                schedule["total_wait_sec"])):
                        details["findings"].append(
                            "initial_quantity_bundle_policy_mismatch")
            except (OSError, ValueError, TypeError, KeyError, AttributeError):
                try:
                    file_day = datetime.fromtimestamp(
                        path.lstat().st_mtime,
                        ZoneInfo("Asia/Seoul")).date().isoformat()
                except OSError:
                    file_day = None
                if belongs_to_date or file_day == source_date:
                    details["findings"].append("initial_quantity_bundle_invalid")
    if details["findings"]:
        details["status"] = "source_invalid" if any(
            item not in {"initial_quantity_bundle_terminal_overdue",
                         "initial_quantity_leg_terminal_after_slot",
                         "initial_quantity_stage_missing_after_date"}
            for item in details["findings"]) else (
                "source_gap" if "initial_quantity_stage_missing_after_date"
                in details["findings"] else "pending_terminal")
    elif details["bundle_count"] == 0 and details["postclose_stage_status"] == "valid_empty":
        details["status"] = "valid_empty"
    elif details["bundle_count"]:
        details["status"] = (
            "journal_terminal_observed" if not details["open_bundle_count"] else
            "pending_terminal")
    return details


def _semantic_object(path: Path, *, limit: int = 64 * 1024 * 1024,
                     hash_only: bool = False) -> tuple[dict, str]:
    """Read one bounded, stable generation without following file symlinks."""
    actual = existing_or_gzip_path(path)
    if actual.is_symlink() or actual.stat().st_size > limit:
        raise ValueError("semantic_artifact_untrusted_path_or_size")
    before = actual.stat()
    opener = gzip.open if actual.suffix == ".gz" else open
    with opener(actual, "rb") as handle:
        if hash_only:
            digest, size = hashlib.sha256(), 0
            while chunk := handle.read(128 * 1024):
                size += len(chunk)
                if size > limit:
                    raise ValueError("semantic_artifact_uncompressed_size_exceeded")
                digest.update(chunk)
        else:
            raw = handle.read(limit + 1)
    after = actual.stat()
    if (before.st_ino, before.st_mtime_ns, before.st_ctime_ns, before.st_size) != (
            after.st_ino, after.st_mtime_ns, after.st_ctime_ns, after.st_size):
        raise ValueError("semantic_generation_changed_during_read")
    if hash_only:
        return {}, digest.hexdigest()
    if len(raw) > limit:
        raise ValueError("semantic_artifact_uncompressed_size_exceeded")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("semantic_artifact_object_invalid")
    return value, hashlib.sha256(raw).hexdigest()


def _semantic_failure(exc):
    if str(exc) == "semantic_generation_changed_during_read":
        return {"status": "unobservable", "findings": [], "reason": str(exc)}
    return {"status": "source_invalid", "findings": [str(exc)]}


def _semantic_stage_binding(root, day, stage, *, artifact=None, artifact_sha=None, artifact_path=None):
    path = root / "data/report/postclose_stage_terminal" / day / f"{stage}.json"
    if not (path.exists() or path.is_symlink()):
        return {"status": "not_assessed"}
    value, _ = _semantic_object(path, limit=1024 * 1024)
    body = {k: v for k, v in value.items() if k != "receipt_sha256"}
    digest = hashlib.sha256(json.dumps(body, ensure_ascii=True, sort_keys=True,
                                      separators=(",", ":")).encode()).hexdigest()
    if (value.get("schema") not in ({"postclose_stage_terminal_v3", "postclose_stage_terminal_v2"} if day < "2026-10-06" else {"postclose_stage_terminal_v3"})
        or value.get("source_date") != day or value.get("stage_id") != stage
        or value.get("receipt_sha256") != digest):
        raise ValueError(f"{stage}:terminal_identity_or_hash_invalid")
    if value.get("status") == "succeeded":
        if value.get("exit_code") != 0:
            raise ValueError(f"{stage}:terminal_exit_invalid")
        if artifact is not None:
            source = (value.get("sources") or {}).get(artifact) or {}
            if source.get("sha256") != artifact_sha or not artifact_sha:
                raise ValueError(f"{stage}:completed_report_generation_mismatch")
            if artifact_path is not None and source.get("path") != str(artifact_path.resolve()):
                raise ValueError(f"{stage}:terminal_source_path_invalid")
    if value.get('status') == 'off' and value.get('off_reason') != 'explicit_schedule_disabled':
        raise ValueError(f'{stage}:terminal_off_reason_invalid')
    return {"status": value.get("status"), "receipt_sha256": digest, 'off_reason': value.get('off_reason')}


def _continuous_reversal_result_semantics(root, source_date, component):
    """Consume the native reversal contract, without legacy economics gates."""
    report_path = root / 'data/report/continuous_reversal' / source_date / (component + '.json')
    if not report_path.exists() and not report_path.is_symlink():
        from src.engine.scalping import mechanistic_entry_runtime_policy as native
        dated = native.root(root / 'data') / ('policy_' + native.next_target(source_date) + '.json')
        if not dated.exists() and not dated.is_symlink():
            return None
        try:
            candidate, _ = _semantic_object(dated)
            if not candidate.get('continuous_reversal'):
                return None
        except (OSError, ValueError, TypeError, KeyError):
            return dict(status='source_invalid', findings=['continuous_reversal_dated_policy_invalid'],
                        source_date=source_date, artifact=str(dated))
    try:
        from src.engine.scalping import continuous_reversal_postclose as reports
        from src.engine.scalping import continuous_reversal_policy as policy
        from src.engine.scalping import mechanistic_entry_runtime_policy as native
        report, report_sha = _semantic_object(report_path)
        if report.get('schema') != reports.SCHEMA:
            raise ValueError('continuous_reversal_report_schema_invalid')
        if (report != reports.seal(report) or report.get('source_date') != source_date
                or report.get('status') != 'completed'):
            raise ValueError('continuous_reversal_report_hash_or_date_invalid')
        stage_id = 'main_machine_policy' if component == 'machine' else 'main_auxiliary_policy'
        for required in ('main_machine_policy', 'main_auxiliary_policy'):
            stage = _semantic_stage_binding(root, source_date, required)
            if stage['status'] in {'pending', 'running'}:
                return dict(status='unobservable', findings=[], stage_id=stage_id, execution=stage)
            if stage['status'] != 'succeeded':
                raise ValueError('continuous_reversal_execution_not_completed:' + required)
        if component == 'machine':
            bound_path = root / 'data/report/ai_decision_action_outcome_calibration' / f'winrate_policy_{source_date}.json'
            artifact = 'machine_policy'
        else:
            bound_path = root / 'data/report/ai_entry_setup_paired_replay_batch' / f'compact_auxiliary_paired_economic_{source_date}.json'
            artifact = 'compact_auxiliary_paired_economic'
        bound, bound_sha = _semantic_object(bound_path)
        _semantic_stage_binding(root, source_date, stage_id, artifact=artifact,
                                artifact_sha=bound_sha, artifact_path=bound_path)
        if component == 'auxiliary':
            bound = reports.seal({k: v for k, v in bound.items() if k not in {'staged', 'artifact_content_sha256'}})
        if bound != report:
            raise ValueError('continuous_reversal_stage_report_mismatch')
        handoff = policy.direct_handoff(root / 'data', source_date)
        bundle = native.load(data_root=root / 'data', target_date=handoff['effective_date'])
        return dict(status='cumulative_winrate_selected', findings=[], stage_id=stage_id,
                    source_date=source_date, target_date=handoff['effective_date'],
                    artifact=str(report_path), report_sha256=report_sha,
                    selection_metric=handoff['selection_metric'],
                    cells=bundle['continuous_reversal'][component + '_cells'],
                    native_handoff=handoff, realized_profit_assessed=False,
                    runtime_effect=False, actual_pid_consumed=False)
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        return dict(_semantic_failure(exc), source_date=source_date,
                    stage_id='main_machine_policy' if component == 'machine' else 'main_auxiliary_policy',
                    artifact=str(report_path))


def _machine_result_semantics(root: Path, source_date: str) -> dict[str, Any]:
    """Check exact-date machine economics separately from stage completion."""
    reversal = _continuous_reversal_result_semantics(root, source_date, 'machine')
    if reversal is not None:
        return reversal
    report_path = (root / "data/report/ai_decision_action_outcome_calibration"
                   / f"ai_decision_action_outcome_calibration_{source_date}.json")
    try:
        stage = _semantic_stage_binding(root, source_date, "legacy_machine_report")
        if stage["status"] in {"pending", "running"}:
            return {"status": "unobservable", "findings": [], "execution": stage}
        if stage["status"] in {"failed", "blocked", "source_quality_blocked"}:
            return {"status": "source_invalid", "findings": ["machine_execution_failed"], "execution": stage}
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        return _semantic_failure(exc)
    if not (report_path.exists() or report_path.is_symlink()):
        # A standalone win-rate sidecar is evidence that the machine family
        # ran; do not mark its missing full-evaluation partner unassessed.
        sidecar = report_path.with_name(f"winrate_policy_{source_date}.json")
        if sidecar.exists() or sidecar.is_symlink():
            return {"status": "source_invalid", "findings": [
                "machine_full_report_missing_with_winrate_sidecar"]}
        return {"status": "not_assessed", "findings": []}
    try:
        if report_path.is_symlink() or report_path.stat().st_size > 64 * 1024 * 1024:
            return {"status": "source_invalid", "findings": ["machine_report_untrusted_path_or_size"]}
        report, report_file_sha = _semantic_object(report_path)
        declared = report.get("artifact_content_sha256")
        body = {key: value for key, value in report.items() if key != "artifact_content_sha256"}
        actual = hashlib.sha256(json.dumps(body, ensure_ascii=True, sort_keys=True,
            separators=(",", ":"), default=str).encode("utf-8")).hexdigest()
        if report.get("target_date") != source_date or declared != actual:
            raise ValueError("machine_report_date_or_hash_invalid")
        scopes = (report.get("machine_full_evaluation") or {}).get("scope_evaluations")
        if not isinstance(scopes, dict):
            raise ValueError("machine_scope_evaluations_missing")
    except (OSError, UnicodeError, ValueError, TypeError, AttributeError) as exc:
        return _semantic_failure(exc)
    findings: list[str] = []
    scope_details: dict[str, dict[str, Any]] = {}
    try:
        execution = _semantic_stage_binding(root, source_date, "legacy_machine_report",
            artifact="ai_decision_action_outcome_calibration",
            artifact_sha=report_file_sha, artifact_path=report_path)
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        return _semantic_failure(exc)
    for scope, row in scopes.items():
        if not isinstance(row, dict):
            findings.append("machine_scope_row_invalid")
            continue
        full = row.get("full_population_count")
        eligible = row.get("current_structure_eligible_count")
        paired = row.get("paired_comparable_count")
        exclusions = row.get("row_exclusion_reason_counts") or {}
        if not isinstance(exclusions, dict):
            findings.append("machine_exclusion_counts_invalid")
            continue
        invalid = exclusions.get("source_contract_invalid", 0)
        if (any(type(value) is not int or value < 0 for value in (full, eligible, invalid))
            or eligible > full or (paired is not None and (type(paired) is not int or paired < 0))):
            findings.append("machine_population_count_invalid")
            continue
        if not full and not invalid:
            continue
        scope_details[scope] = {"full": full, "eligible": eligible,
            "operating_paired": paired, "source_contract_invalid": invalid,
            "findings": []}
        start = len(findings)
        if invalid:
            findings.append("machine_source_contract_exclusions")
        if full and not eligible:
            findings.append("machine_current_structure_empty")
        if eligible and not paired:
            findings.append("machine_operating_paired_unbound")
        if eligible and row.get("downstream_operating_evidence_complete") is not True:
            findings.append("machine_operating_economics_incomplete")
        scope_details[scope]["findings"] = findings[start:]
    selections = report.get("strategy_refinements_by_scope") or {}
    if not isinstance(selections, dict):
        findings.append("machine_selection_contract_invalid")
        selections = {}
    from src.engine.scalping import entry_strategy_policy as strategy
    from src.engine.scalping.postclose_entry_validation import NEW_LOGIC_SOURCE_DATE
    if source_date >= NEW_LOGIC_SOURCE_DATE and set(scope_details) - set(selections):
        findings.append("machine_scope_selection_missing")
    for scope, selection in selections.items():
        if not isinstance(selection, dict):
            findings.append("machine_selection_contract_invalid")
            continue
        if source_date >= NEW_LOGIC_SOURCE_DATE:
            diagnostic_hold = (
                selection.get('selection_basis') == strategy.MACHINE_SELECTION_VERSION
                and selection.get('status') in {'source_gap', 'hold_candidate'}
                and selection.get('promotion_pass') is False
                and ((selection.get('status') == 'source_gap' and not selection.get('candidate'))
                     or (selection.get('status') == 'hold_candidate'
                         and selection.get('runtime_effect') is False
                         and selection.get('allowed_runtime_apply') is False)))
            if (selection.get("selection_basis") != strategy.RECOVERY_SELECTION_VERSION
                    and not diagnostic_hold):
                findings.append("machine_selection_version_invalid")
            if selection.get("promotion_pass") is True:
                candidate = selection.get("candidate") or {}
                try:
                    errors = strategy.promotion_errors(candidate, candidate.get("parent_policy"),
                                                        tuple(scope.split("|")))
                except (ValueError, TypeError, KeyError, AttributeError):
                    errors = ["candidate_contract_invalid"]
                if (errors or selection.get("promotion_errors")
                    or candidate.get("selection_score_version") != strategy.RECOVERY_SELECTION_VERSION):
                    findings.append("machine_selected_without_recovery_evidence")
        scope_details.setdefault(scope, {}).update(
            selection_status=selection.get("status"),
            selection_version=selection.get("selection_basis"),
            selection_blocker=selection.get("blocker"),
            promotion_errors=selection.get("promotion_errors"),
            source_excluded_count=len(selection.get("source_exclusions") or []))
    compact_path = (root / "data/report/ai_entry_setup_paired_replay_batch"
                    / f"compact_auxiliary_paired_economic_{source_date}.source.json")
    compact_exclusions: dict[str, int] = {}
    compact_path = existing_or_gzip_path(compact_path)
    if compact_path.exists() or compact_path.is_symlink():
        try:
            if compact_path.is_symlink() or compact_path.stat().st_size > 64 * 1024 * 1024:
                findings.append("compact_projection_untrusted_path_or_size")
            else:
                opener = gzip.open if compact_path.suffix == ".gz" else open
                with opener(compact_path, "rt", encoding="utf-8") as handle:
                    compact_text = handle.read(64 * 1024 * 1024 + 1)
                if len(compact_text) > 64 * 1024 * 1024:
                    raise ValueError("compact_projection_uncompressed_size_exceeded")
                compact = json.loads(compact_text)
                if compact.get("target_date") != source_date or not isinstance(compact.get("rows"), list):
                    raise ValueError("compact_projection_date_or_rows_invalid")
                compact_hash = compact.get("artifact_content_sha256")
                compact_body = {k: v for k, v in compact.items() if k != "artifact_content_sha256"}
                actual_hash = hashlib.sha256(json.dumps(compact_body, ensure_ascii=False,
                    sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
                if compact_hash != actual_hash:
                    raise ValueError("compact_projection_hash_invalid")
                if any(not isinstance(row, dict) for row in compact["rows"]):
                    raise ValueError("compact_projection_rows_invalid")
                compact_exclusions = dict(Counter(str(row.get("exclusion_reason"))
                    for row in compact["rows"] if row.get("exclusion_reason")))
                if compact["rows"] and sum(compact_exclusions.values()) == len(compact["rows"]):
                    findings.append("compact_operating_rows_all_excluded")
        except (OSError, EOFError, UnicodeError, ValueError, TypeError, AttributeError) as exc:
            if str(exc) == 'semantic_generation_changed_during_read':
                return dict(_semantic_failure(exc), source_date=source_date)
            findings.append("compact_projection_invalid")
    winrate_path = (root / 'data/report/ai_decision_action_outcome_calibration'
                    / f'winrate_policy_{source_date}.json')
    if winrate_path.exists() or winrate_path.is_symlink():
        try:
            if winrate_path.is_symlink() or winrate_path.stat().st_size > 64 * 1024 * 1024:
                raise ValueError('winrate_report_untrusted_path_or_size')
            from src.engine.scalping import ai_action_outcome_calibration as calibration
            from src.engine.scalping import mechanistic_entry_runtime_policy as runtime_policy
            winrate, winrate_file_sha = _semantic_object(winrate_path)
            winrate_stage = _semantic_stage_binding(root, source_date, 'main_machine_policy',
                artifact='machine_policy', artifact_sha=winrate_file_sha, artifact_path=winrate_path)
            if winrate_stage['status'] in {'pending', 'running'}:
                return {'status': 'unobservable', 'findings': [], 'execution': winrate_stage}
            if winrate_stage['status'] in {'failed', 'blocked', 'source_quality_blocked'}:
                findings.append('winrate_execution_failed')
            if winrate.get('schema') == 'main_entry_winrate_policy_report_v1':
                if (not calibration._artifact_content_sha256_valid(winrate)
                    or winrate.get('target_date') != source_date
                    or winrate.get('selection_basis') != 'win_rate_only'):
                    findings.append('winrate_report_hash_or_scope_invalid')
                accepted = winrate.get('accepted_attempt_count')
                input_count = winrate.get('input_attempt_count')
                source_excluded = winrate.get('source_contract_excluded_count')
                excluded = winrate.get('excluded_attempt_counts') or {}
                if (type(input_count) is not int or input_count < 0
                    or type(accepted) is not int or accepted < 0
                    or type(source_excluded) is not int or source_excluded < 0
                    or any(type(v) is not int or v < 0 for v in excluded.values())
                    or accepted + source_excluded + sum(excluded.values()) != input_count
                    or sum((winrate.get('situation_attempt_counts') or {}).values()) != accepted):
                    findings.append('winrate_population_denominator_invalid')
                if not runtime_policy.winrate_market_census_valid(winrate):
                    findings.append('winrate_market_denominator_invalid')
                elif any(item['input_attempt_count'] == 0
                    for item in winrate['market_census'].values()):
                    findings.append('winrate_market_source_empty')
                disposition = winrate.get('disposition')
                fixed_pair_report = winrate.get('fixed_pair_contract') is not None
                if (not fixed_pair_report and disposition == 'successor_selected'
                    and not runtime_policy._winrate_successor_hurdles_valid(winrate)):
                    findings.append('winrate_successor_hurdle_invalid')
                if not fixed_pair_report and disposition in {'initial_adopted', 'successor_selected'}:
                    for part in ('train', 'holdout'):
                        metrics = (winrate.get('candidate') or {}).get(part) or {}
                        if (not metrics.get('selected_opportunity_count')
                            or metrics.get('win_rate_pct') is None
                            or metrics.get('support_adjusted_win_rate_pct') is None):
                            findings.append('winrate_selected_zero_or_undefined')
                terminal_path = winrate_path.with_name(f'winrate_policy_terminal_{source_date}.json')
                terminal, terminal_sha = _semantic_object(terminal_path, limit=1024 * 1024)
                _semantic_stage_binding(root, source_date, 'main_machine_policy',
                    artifact='machine_policy_terminal', artifact_sha=terminal_sha, artifact_path=terminal_path)
                target = (terminal.get('staged') or {}).get('target_date')
                if (not calibration._artifact_content_sha256_valid(terminal)
                    or terminal.get('report_sha256') != winrate.get('artifact_content_sha256')
                    or not isinstance(target, str)):
                    raise ValueError('winrate_terminal_binding_invalid')
                bundle = runtime_policy.load(data_root=root / 'data', target_date=target)
                selection = (bundle or {}).get('winrate_selection') or {}
                pending = (terminal.get('staged') or {}).get('status') == 'pending_initial_preserved'
                reused = (terminal.get('staged') or {}).get('status') == 'existing_incumbent_preserved'
                from src.engine.scalping import entry_designated_policy as designated_policy
                designated = selection.get('schema') == designated_policy.PROOF
                if fixed_pair_report and not designated:
                    findings.append('winrate_candidate_bundle_or_scope_mismatch')
                if designated:
                    if (not designated_policy.binding_valid(winrate, bundle, root / 'data')
                        or terminal['staged'].get('bundle_sha256') != bundle['bundle_sha256']):
                        findings.append('winrate_candidate_bundle_or_scope_mismatch')
                    else:
                        # The loader validates the frozen pair, original request,
                        # parent and actual activation receipts. Do not compare an
                        # automatic carry disposition to operator designation.
                        scope_details['designated_fixed_pair'] = {
                            'status': 'bound', 'target_date': target,
                            'disposition': selection.get('disposition'),
                            'pair': bundle.get('designated_pair'),
                            'comparison': winrate.get('fixed_pair_comparison'),
                            'consumption': 'not_assessed_by_postclose_selection'}
                if not pending and not reused and not designated:
                    from src.engine.automation.postclose_summary_handoff import _staged_winrate_generation_preserved
                    if not _staged_winrate_generation_preserved(terminal['staged'], bundle,
                            runtime_policy, root / 'data', generation_only=True):
                        findings.append('winrate_candidate_bundle_or_scope_mismatch')
                if reused:
                    from src.engine.automation.postclose_summary_handoff import _existing_incumbent_winrate_binding_valid
                    previous = runtime_policy.load_effective(data_root=root / 'data', target_date=winrate.get('publication_date'))
                    if not _existing_incumbent_winrate_binding_valid(winrate, terminal['staged'],
                            bundle, previous, runtime_policy, data_root=root / 'data'):
                        findings.append('winrate_candidate_bundle_or_scope_mismatch')
                if (pending and (winrate.get('pending_initial_bundle_sha256') != bundle['bundle_sha256']
                    or winrate.get('pending_initial_target_date') != target
                    or winrate.get('hurdle_errors') != ['initial_policy_pending_activation']
                    or disposition != 'incumbent_carried'
                    or selection.get('disposition') != 'initial_adopted'
                    or selection.get('parent_bundle_sha256') != winrate.get('parent_bundle_sha256')
                    or bundle.get('previous_bundle_sha256') != winrate.get('parent_bundle_sha256'))
                    or not pending and not reused and not designated and (selection.get('report_sha256') != winrate.get('artifact_content_sha256')
                    or selection.get('disposition') != disposition)
                    or selection.get('machine_policy_sha256') != runtime_policy.digest(bundle['machine_policy'])
                    or not pending and not reused and not designated and (bundle.get('scope_policies') or {}).get('KRX|KRX_REGULAR', {}).get('machine_disposition') != disposition):
                    findings.append('winrate_candidate_bundle_or_scope_mismatch')
            else:
                findings.append('winrate_report_schema_invalid')
        except (OSError, EOFError, UnicodeError, ValueError, TypeError, KeyError, AttributeError) as exc:
            if str(exc) == 'semantic_generation_changed_during_read':
                return dict(_semantic_failure(exc), source_date=source_date)
            findings.append('winrate_semantic_validation_failed')
    return {"status": "warning" if findings else "pass", "findings": sorted(set(findings)),
        "scopes": scope_details, "compact_exclusions": compact_exclusions,
        "source_date": source_date, "execution": execution,
        "report_sha256": actual, "artifact": str(report_path),
        "publication": "see_winrate_terminal_and_dated_bundle",
        "consumption": "not_assessed_by_postclose_selection"}


def _auxiliary_scope_contract(value, report, source_date, scope):
    """Audit frozen evidence, never rerank candidates or execute a replay."""
    from src.engine.scalping import compact_auxiliary_paired_replay as paired
    from src.engine.scalping.postclose_entry_validation import (
        NEW_LOGIC_SOURCE_DATE, split_manifest_valid, opportunity_identity,
    )
    if source_date < NEW_LOGIC_SOURCE_DATE:
        return []
    errors = []
    version = value.get("selection_rank_version")
    if version not in {"train_top1_frozen_paired_net_ev_holdout_gate_v4", paired.STAGE_SELECTION_VERSION}:
        errors.append("auxiliary_selection_version_invalid")
    manifest = value.get("split_manifest") or {}
    try:
        train = [tuple(row) for row in manifest["train_opportunity_ids"]]
        held = [tuple(row) for row in manifest["holdout_opportunity_ids"]]
        purged = [tuple(row) for row in manifest["purged_opportunity_ids"]]
        for identity in train + held + purged:
            if len(identity) == 5:
                lineage = {'scanner_promotion_id': identity[4]}
            elif len(identity) == 7 and identity[4] == 'MAIN_FIXED_WATCH':
                lineage = dict(zip(('watch_origin', 'watch_admission_id',
                                    'watch_generation_id'), identity[4:]))
            else:
                raise ValueError('opportunity_shape_invalid')
            row = {**dict(zip(('source_date', 'stock_code', 'effective_venue',
                              'session_bucket'), identity[:4])), **lineage}
            if opportunity_identity(row) != identity:
                raise ValueError('opportunity_identity_invalid')
        if (any(len(rows) != len(set(rows)) for rows in (train, held, purged))
            or set(purged) & (set(train) | set(held))
            or (train and held and not split_manifest_valid(manifest, train, held))
            or (value.get("status") == "candidate_selected" and (not train or not held))):
            raise ValueError("split_invalid")
    except (ValueError, TypeError, KeyError):
        errors.append("auxiliary_chronological_split_invalid")
    cost_count = value.get("full_cost_candidate_population_count")
    diagnostic = value.get("cost_incomplete_diagnostic_count")
    if (type(cost_count) is not int or cost_count < 0
        or type(diagnostic) is not int or diagnostic < 0
        or value.get("metric_authority") != "full_cost_fixed_checkpoint_cf_not_owner_portfolio"):
        errors.append("auxiliary_full_cost_census_invalid")
    trials = value.get("candidates")
    if (not isinstance(trials, list) or any(not isinstance(t, dict) for t in trials)
        or value.get("completed_candidate_count") != sum(
            t.get("evaluation_status") == "evaluated" for t in trials)
        or value.get("holdout_selection_candidate_count") != int(bool(value.get("frozen_train_choice")))):
        errors.append("auxiliary_completed_response_census_invalid")
    selected = value.get("selected") or {}
    frozen = value.get("frozen_train_choice")
    if frozen:
        receipt = report.get("auxiliary_train_selection") or {}
        saved = (receipt.get("scopes") or {}).get(scope) or {}
        if (not paired.valid(receipt) or receipt.get("schema") != "auxiliary_train_selection_v1"
            or receipt.get("target_date") != source_date
            or any(not isinstance(value.get(key), str) or len(value[key]) != 64
                   or any(c not in "0123456789abcdef" for c in value[key])
                   for key in ("train_population_sha256", "current_machine_policy_sha256"))
            or saved.get("policy_sha256") != frozen.get("policy_sha256")
            or saved.get("policy") != frozen.get("policy")
            or saved.get("prompt_version") != frozen.get("prompt_version")
            or saved.get("machine_policy_sha256") != value.get("current_machine_policy_sha256")
            or saved.get("parent_prompt_version") not in (value.get("parent_prompt_versions") or [])
            or saved.get("parent_soft_sha256") not in (value.get("parent_soft_policy_sha256s") or [])
            or saved.get("train_population_sha256") != value.get("train_population_sha256")
            or saved.get("split_manifest") != manifest):
            errors.append("auxiliary_frozen_selection_binding_invalid")
    if value.get("status") == "candidate_selected":
        if version == paired.STAGE_SELECTION_VERSION:
            receipt = report.get('auxiliary_train_selection') or {}
            saved = (receipt.get('scopes') or {}).get(scope) or {}
            incumbent = (trials or [{}])[0]
            if any(not paired.auxiliary_winrate_improves(selected, incumbent, part) for part in ('train', 'holdout')):
                errors.append('auxiliary_selected_winrate_not_improved')
            if (receipt.get('selection_rank_version') != paired.STAGE_SELECTION_VERSION
                or saved.get('selection_rank_version') != paired.STAGE_SELECTION_VERSION):
                errors.append('auxiliary_selection_objective_binding_invalid')
        if (not isinstance(frozen, dict) or selected != frozen
            or value.get("holdout_errors") or not cost_count
            or cost_count < selected.get("train_count", 0) + selected.get("holdout_count", 0)
            or selected.get("evaluation_status") != "evaluated"
            or selected.get("policy_sha256") != paired.digest(selected.get("policy"))
            or (selected.get("train_veto_to_pass_count")
                and not selected.get("holdout_veto_to_pass_count"))):
            errors.append("auxiliary_selected_without_frozen_full_cost_evidence")
    return errors


def _auxiliary_result_semantics(root: Path, source_date: str) -> dict[str, Any]:
    """Audit the bounded AI-stage receipt; selection is not live consumption."""
    reversal = _continuous_reversal_result_semantics(root, source_date, 'auxiliary')
    if reversal is not None:
        return reversal
    from src.engine.scalping import compact_auxiliary_paired_replay as paired

    terminal_path = (root / "data/report/postclose_stage_terminal" / source_date
                     / "main_auxiliary_policy.json")
    terminal_source_sha = None
    if terminal_path.exists() or terminal_path.is_symlink():
        try:
            if terminal_path.is_symlink() or terminal_path.stat().st_size > 1024 * 1024:
                raise ValueError("auxiliary_terminal_untrusted_path_or_size")
            terminal, _ = _semantic_object(terminal_path, limit=1024 * 1024)
            receipt = terminal.get("receipt_sha256")
            body = {k: v for k, v in terminal.items() if k != "receipt_sha256"}
            digest = hashlib.sha256(json.dumps(body, ensure_ascii=True,
                sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            if (terminal.get("schema") not in ({"postclose_stage_terminal_v3", "postclose_stage_terminal_v2"} if source_date < "2026-10-06" else {"postclose_stage_terminal_v3"})
                or terminal.get("stage_id") != "main_auxiliary_policy"
                or terminal.get("source_date") != source_date or receipt != digest):
                raise ValueError("auxiliary_terminal_identity_or_hash_invalid")
            if terminal.get("status") in {"pending", "running"}:
                return {"status": "unobservable", "findings": [], "execution": terminal.get("status")}
            if terminal.get("status") in {"failed", "blocked", "source_quality_blocked"}:
                return {"status": "source_invalid", "findings": ["auxiliary_execution_failed"]}
            if terminal.get("status") == "succeeded" and terminal.get("exit_code") != 0:
                raise ValueError("auxiliary_terminal_exit_invalid")
            if terminal.get("status") == "succeeded" and terminal.get("exit_code") == 0:
                source = ((terminal.get("sources") or {}).get(
                    "compact_auxiliary_paired_economic") or {})
                terminal_source_sha = source.get("sha256")
                if (not isinstance(terminal_source_sha, str)
                    or len(terminal_source_sha) != 64
                    or any(c not in "0123456789abcdef" for c in terminal_source_sha)
                    or source.get("path") != str((root /
                        "data/report/ai_entry_setup_paired_replay_batch" /
                        f"compact_auxiliary_paired_economic_{source_date}.json").resolve())):
                    raise ValueError("auxiliary_terminal_source_binding_missing")
        except (OSError, UnicodeError, ValueError, TypeError, AttributeError) as exc:
            return _semantic_failure(exc)
    path = existing_or_gzip_path(
        root / "data/report/ai_entry_setup_paired_replay_batch"
        / f"compact_auxiliary_paired_economic_{source_date}.json"
    )
    if not (path.exists() or path.is_symlink()):
        if terminal_source_sha:
            return {"status": "source_invalid", "findings": ["auxiliary_completed_report_missing"]}
        return {"status": "not_assessed", "findings": []}
    try:
        report, file_sha = _semantic_object(path)
        if terminal_source_sha and file_sha != terminal_source_sha:
            raise ValueError("auxiliary_completed_report_generation_mismatch")
        stage = report.get("auxiliary_stage") or {}
        if (not paired.valid(report)
            or report.get("schema") != paired.SCHEMA
            or report.get("target_date") != source_date
            or not paired.valid(stage)
            or stage.get("schema") != "auxiliary_ai_stage_evaluation_v1"
            or stage.get("source_date") != source_date
            or stage.get("source_projection_sha256") != report.get("source_projection_sha256")
            or stage.get("source_manifest_sha256") != report.get("source_manifest_sha256")
            or report.get("runtime_effect") is not False
            or stage.get("runtime_effect") is not False
            or stage.get("actual_order_submitted") is not False):
            raise ValueError("auxiliary_stage_report_contract_invalid")
        screened, eligible, excluded = (stage.get(k) for k in
            ("screened_total", "eligible_count", "excluded_count"))
        eligible_keys = stage.get("eligible_keys")
        candidate_keys = stage.get("candidate_population_keys")
        if (any(type(n) is not int or n < 0 for n in (screened, eligible, excluded))
            or screened != eligible + excluded
            or (eligible_keys is not None and (
                not isinstance(eligible_keys, list)
                or any(not isinstance(key, str) or not key for key in eligible_keys)
                or len(eligible_keys) != eligible
                or len(set(eligible_keys)) != eligible))
            or not isinstance(stage.get("scope_results"), dict)):
            raise ValueError("auxiliary_population_denominator_invalid")
        if candidate_keys is not None and (
            not isinstance(candidate_keys, list)
            or any(not isinstance(key, str) or not key for key in candidate_keys)
            or len(set(candidate_keys)) != len(candidate_keys)
            or eligible_keys is None
            or not set(candidate_keys) <= set(eligible_keys)
            or any(not isinstance(v, dict)
                   or type(v.get("eligible_count")) is not int
                   or v["eligible_count"] < 0
                   for v in stage["scope_results"].values())
            or sum(v["eligible_count"] if source_date < "2026-10-02"
                   else v.get("full_cost_candidate_population_count", 0)
                   for v in stage["scope_results"].values())
                != len(candidate_keys)):
            raise ValueError("auxiliary_candidate_population_invalid")
    except (OSError, EOFError, UnicodeError, ValueError, TypeError, AttributeError) as exc:
        return _semantic_failure(exc)
    findings: list[str] = []
    if eligible_keys is None:
        findings.append("auxiliary_eligible_identity_uninstrumented")
    if stage.get("source_tuning_allowed") is not True:
        findings.append("auxiliary_source_tuning_not_allowed")
    economic = report.get("metrics") or {}
    if not isinstance(economic, dict):
        return {"status": "source_invalid", "findings": ["auxiliary_economic_metrics_invalid"]}
    economic_screened = economic.get("screened_total")
    economic_compared = economic.get("paired_comparable_count")
    if report.get("status") == "source_contract_blocked":
        if (type(economic_screened) is not int or economic_screened < 0
            or type(economic_compared) is not int or economic_compared < 0
            or economic_compared > economic_screened):
            return {"status": "source_invalid", "findings": ["auxiliary_economic_denominator_invalid"]}
        if economic_screened and not economic_compared:
            findings.append("auxiliary_primary_economics_source_blocked")
    prospective = report.get("prospective_source_contract") or {}
    if not isinstance(prospective, dict):
        return {"status": "source_invalid", "findings": ["auxiliary_source_lineage_invalid"]}
    lineage = prospective.get("source_lineage_counts") or {}
    if not isinstance(lineage, dict):
        return {"status": "source_invalid", "findings": ["auxiliary_source_lineage_invalid"]}
    first_gap = prospective.get("first_source_gap")
    if (first_gap == "writer_plan_hash_missing"
        and type(lineage.get("prompt_exact_input_present")) is int
        and lineage["prompt_exact_input_present"] > 0
        and lineage.get("writer_trace_plan_joined") == 0):
        findings.append("auxiliary_exact_plan_lineage_missing")
    label_gap_count = 0
    label_hash = report.get("source_label_report_sha256")
    if type(economic_screened) is int and economic_screened > 0 and not label_hash:
        findings.append("auxiliary_outcome_label_binding_missing")
    independent_path_counts = None
    if label_hash:
        label_path = existing_or_gzip_path(
            root / "data/report/ai_decision_outcome_labels"
            / f"ai_decision_outcome_labels_{source_date}.json")
        try:
            if (not isinstance(label_hash, str) or len(label_hash) != 64
                or any(c not in "0123456789abcdef" for c in label_hash)
                or label_path.is_symlink()):
                raise ValueError("auxiliary_label_report_untrusted_path_or_size")
            if not label_path.exists():
                raise ValueError("auxiliary_label_report_missing")
            if label_path.stat().st_size > 64 * 1024 * 1024:
                raise ValueError("auxiliary_label_report_untrusted_path_or_size")
            opener = gzip.open if label_path.suffix == ".gz" else open
            with opener(label_path, "rb") as handle:
                label_raw = handle.read(64 * 1024 * 1024 + 1)
            if len(label_raw) > 64 * 1024 * 1024:
                raise ValueError("auxiliary_label_report_uncompressed_size_exceeded")
            labels = json.loads(label_raw)
            if not isinstance(labels, dict):
                raise ValueError("auxiliary_label_report_binding_invalid")
            counts = labels.get("label_contract_status_counts")
            label_rows = labels.get("labels")
            actual_counts = Counter()
            if isinstance(label_rows, list):
                for row in label_rows:
                    role = row.get("evaluation_label_contract") if isinstance(row, dict) else None
                    price_path = role.get("diagnostic_price_path") if isinstance(role, dict) else None
                    status = price_path.get("status") if isinstance(price_path, dict) else None
                    actual_counts[status] += 1
            if (labels.get("schema") != "ai_decision_outcome_labels_v1"
                or labels.get("target_date") != source_date
                or paired.digest(labels) != label_hash
                or not isinstance(label_rows, list)
                or not isinstance(counts, dict)
                or any(type(n) is not int or n < 0 for n in counts.values())
                or sum(counts.values()) != len(label_rows)
                or dict(actual_counts) != counts):
                raise ValueError("auxiliary_label_report_binding_invalid")
            # Holding/exit labels are not the compact auxiliary population.
            entry_rows = [row for row in label_rows
                          if row.get("decision_stage") in {"entry", "entry_screen"}]
            if source_date >= "2026-10-02" and economic_screened:
                projection, _ = _semantic_object(path.with_name(
                    f"compact_auxiliary_paired_economic_{source_date}.source.json"))
                if (not paired.valid(projection) or projection.get("target_date") != source_date
                    or projection.get("artifact_content_sha256") != report.get("source_projection_sha256")):
                    raise ValueError("auxiliary_label_population_binding_invalid")
                keys = {row["evaluation_key"] for row in projection["rows"]}
                entry_rows = [row for row in entry_rows if row.get("decision_trace_id") in keys]
                if (len(keys) != economic_screened or len(entry_rows) != len(keys)
                    or {row.get("decision_trace_id") for row in entry_rows} != keys):
                    raise ValueError("auxiliary_label_population_binding_invalid")
                label_index = {row['decision_trace_id']: row for row in entry_rows}
                joined = [row for row in projection['rows']
                          if paired.stage_path_label_matches(row, label_index[row['evaluation_key']])]
                independent_path_counts = dict(total=len(keys), exact_price_label_joined=len(joined),
                    net_path_evaluable=sum(paired.auxiliary_stage_net(row) is not None for row in joined),
                    authority='fixed_10m_counterfactual_path_not_operating_or_realized_economics')
            label_gap_count = sum((row.get("evaluation_label_contract") or {}).get(
                "diagnostic_price_path", {}).get("status") == "source_gap" for row in entry_rows)
        except (OSError, EOFError, UnicodeError, ValueError, TypeError, KeyError, AttributeError) as exc:
            return _semantic_failure(exc)
        if label_gap_count:
            findings.append("auxiliary_outcome_label_source_gap")
    scopes = {}
    for scope, value in stage["scope_results"].items():
        if not isinstance(value, dict):
            findings.append("auxiliary_scope_selection_status_invalid")
            continue
        selected = value.get("selected") or {}
        if not isinstance(selected, dict):
            findings.append("auxiliary_scope_selection_status_invalid")
            continue
        status = value.get("status")
        try:
            scope_findings = _auxiliary_scope_contract(value, report, source_date, scope)
        except (ValueError, TypeError, KeyError, AttributeError):
            scope_findings = ["auxiliary_scope_selection_contract_invalid"]
        findings.extend(scope_findings)
        independent = bool(value.get("holdout_day") or value.get("same_day_holdout_keys"))
        scopes[scope] = {"status": status, "eligible_count": value.get("eligible_count"),
                         "holdout_day": value.get("holdout_day"),
                         "paired_delta_ev_pct": selected.get("paired_delta_ev_pct"),
                         "selection_version": value.get("selection_rank_version"),
                         "selection_blocker": value.get("selection_blocker"),
                         "holdout_errors": value.get("holdout_errors"),
                         "full_cost_count": value.get("full_cost_candidate_population_count"),
                         "cost_incomplete_diagnostic_count": value.get("cost_incomplete_diagnostic_count"),
                         "metric_authority": value.get("metric_authority"),
                         "findings": scope_findings,
                         "actual_fill_or_realized_pnl": False}
        if status not in {"candidate_selected", "incumbent_carry"}:
            findings.append("auxiliary_scope_selection_status_invalid")
        train_delta = selected.get("train_paired_delta_ev_pct")
        holdout_delta = selected.get("holdout_paired_delta_ev_pct")
        if status == "candidate_selected" and (
            stage.get("source_tuning_allowed") is not True
            or candidate_keys is None
            or type(selected.get("paired_delta_ev_pct")) not in (int, float)
            or not math.isfinite(selected["paired_delta_ev_pct"])
            or selected["paired_delta_ev_pct"] <= 0
            or not isinstance(selected.get("policy"), dict)
            or selected.get("policy_sha256") != paired.digest(selected["policy"])
            or not selected.get("prompt_version")
            or type(selected.get("train_count")) is not int or selected["train_count"] < 5
            or type(selected.get("holdout_count")) is not int or selected["holdout_count"] < 3
            or type(value.get("eligible_count")) is not int
            or selected["train_count"] + selected["holdout_count"] != value["eligible_count"]
            or value["eligible_count"] > eligible
            or type(train_delta) not in (int, float) or not math.isfinite(train_delta) or train_delta <= 0
            or type(holdout_delta) not in (int, float) or not math.isfinite(holdout_delta) or holdout_delta < 0
            or any(type(selected.get(key)) is not int or selected[key] < 1 for key in (
                "train_positive_count", "train_negative_count", "holdout_positive_count",
                "holdout_negative_count", "train_pass_count", "holdout_pass_count",
                "holdout_changed_count"))
            or type(selected.get("train_changed_count")) is not int
            or selected["train_changed_count"] < 2
            or selected.get("successful_pass_changed_count") != 0
            or selected.get("prompt_response_missing_count") != 0
            or not independent
        ):
            findings.append("auxiliary_selected_without_independent_evidence")
    if not eligible:
        findings.append("auxiliary_economic_population_empty")
    elif not any(isinstance(value, dict) and (value.get("holdout_day") or value.get("same_day_holdout_keys"))
                 for value in stage["scope_results"].values()):
        findings.append("auxiliary_independent_holdout_missing")
    if any(f.endswith("invalid") or f.startswith("auxiliary_selected_without_")
           for f in findings):
        status = "review_required"
    elif findings:
        status = "source_gap"
    elif any(isinstance(v, dict) and v.get("status") == "candidate_selected"
             for v in stage["scope_results"].values()):
        status = "candidate_selected"
    else:
        status = "incumbent_carry"
    return {"status": status,
            "findings": sorted(set(findings)), "screened_total": screened,
            "eligible_count": eligible, "excluded_count": excluded,
            "economic_screened_total": economic_screened,
            "paired_comparable_count": economic_compared,
            "outcome_label_source_gap_count": label_gap_count,
            "independent_price_path_counts": independent_path_counts,
            "first_source_gap": first_gap,
            "source_lineage_counts": lineage,
            "source_date": source_date, "report_sha256": report["artifact_content_sha256"],
            "artifact": str(path), "execution": "report_observed",
            "publication": report.get("selection_disposition"),
            "consumption": "not_assessed_by_postclose_selection",
            "scopes": scopes, "runtime_effect": False}


def _cancel_wait_monitor_source_date(root, day, *, data_root=None):
    """Keep a native run's original date over midnight, including holidays."""
    data_root = Path(data_root) if data_root is not None else Path(root)/'data'
    previous = (datetime.fromisoformat(day) - timedelta(days=1)).date().isoformat()
    for source_date in (day, previous):
        path = data_root/'report/threshold_cycle_postclose_status'/f'threshold_cycle_postclose_{source_date}.status.json'
        if path.exists() and not path.is_symlink():
            try:
                state, _ = _semantic_object(path, limit=1024*1024)
                if (state.get('status') in {'running', 'producers_completed', 'succeeded', 'failed'}
                    and state.get('target_date') == source_date and state.get('run_id')):
                    return source_date
            except (OSError, ValueError, TypeError):
                pass
    return day


def _cancel_wait_native_execution(root, data_root, source_date):
    """Read native wrapper receipts; cancel-wait has no launch-owned stage."""
    result = {'status':'not_observed', 'source_date':source_date}
    path = data_root/'report/threshold_cycle_postclose_status'/f'threshold_cycle_postclose_{source_date}.status.json'
    if path.exists() or path.is_symlink():
        state, sha = _semantic_object(path)
        if state.get('target_date') != source_date:
            raise ValueError('cancel_wait_native_run_date_invalid')
        result.update(status=state.get('status'), status_sha256=sha, run_id=state.get('run_id'),
                      code_commit=state.get('code_commit'))
    log = root/'logs/threshold_cycle_postclose_cron.log'
    if log.is_file() and not log.is_symlink():
        before = log.stat()
        with log.open('rb') as handle:
            handle.seek(max(0, before.st_size - 4 * 1024 * 1024))
            rows = handle.read().splitlines()
        after = log.stat()
        if (before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns):
            result['command_status'] = 'generation_in_transition'
            return result
        for line in reversed(rows):
            if b'[PERF] ' not in line:
                continue
            try:
                metric = json.loads(line.split(b'[PERF] ', 1)[1])
            except (ValueError, UnicodeError):
                continue
            if (metric.get('schema') != 'postclose_command_metrics_v1'
                or metric.get('producer_module') != 'src.engine.automation.entry_cancel_wait_tuning'
                or metric.get('target_date') != source_date
                or (result.get('run_id') and metric.get('run_id') != result['run_id'])
                or (result.get('code_commit') and metric.get('code_commit') != result['code_commit'])):
                continue
            result['command'] = metric
            result['command_status'] = ('succeeded' if metric.get('measurement_complete') is True
                and type(metric.get('exit_code')) is int and metric['exit_code'] == 0 else 'failed')
            break
    return result


def _entry_cancel_wait_result_semantics(root, source_date, now=None, *, data_root=None):
    from src.engine.automation import entry_cancel_wait_tuning as owner
    root = Path(root)
    data_root = Path(data_root) if data_root is not None else root/'data'
    directory = data_root/'report/entry_cancel_wait_tuning'
    path = directory/f'entry_cancel_wait_tuning_{source_date}.json'
    policy_path = directory/f'entry_cancel_wait_policy_{source_date}.json'
    result = {'status':'not_assessed', 'source_date':source_date, 'findings':[],
              'artifact':str(path), 'runtime_effect':False, 'actual_pid_consumed':False,
              'whole_native_chain_done_claimed':False}
    reading_consumers = False
    try:
        execution = _cancel_wait_native_execution(root, data_root, source_date)
        result['execution'] = execution
        if execution.get('command_status') == 'generation_in_transition':
            return {**result, 'status':'unobservable', 'reason':'generation_in_transition'}
        if execution.get('command_status') == 'failed':
            return {**result, 'status':'source_invalid', 'findings':['cancel_wait_execution_failed']}
        if not path.exists() and not path.is_symlink():
            if execution.get('command_status') == 'succeeded':
                return {**result, 'status':'source_invalid', 'findings':['cancel_wait_completed_report_missing']}
            current = now or datetime.now(ZoneInfo('Asia/Seoul'))
            current = current.replace(tzinfo=ZoneInfo('Asia/Seoul')) if current.tzinfo is None else current.astimezone(ZoneInfo('Asia/Seoul'))
            due = source_date < current.date().isoformat() or (source_date == current.date().isoformat() and current.hour >= 20)
            return {**result, 'status':'pending' if due else 'not_yet_due'}
        payload, report_sha = _semantic_object(path)
        result['report_sha256'] = report_sha
        if payload.get('date') != source_date:
            raise ValueError('cancel_wait_report_date_or_hash_invalid')
        if payload.get('reconciliation_contract_version') is None:
            return {**result, **owner.validated_reconciliation_view(payload), 'findings':[]}
        if not policy_path.exists() and execution.get('status') == 'running':
            return {**result, 'status':'pending', 'reason':'policy_publication_pending'}
        policy, policy_sha = _semantic_object(policy_path)
        view = owner.validated_reconciliation_view(payload, policy, data_root=data_root,
                                                    read_object=_semantic_object)
        result.update(view, findings=list(view['findings']), policy_sha256=policy_sha)
        if view.get('status') == 'unobservable':
            return result
        # Recheck the multi-file publication after reading the bound sources.
        if (_semantic_object(path, hash_only=True)[1] != report_sha
            or _semantic_object(policy_path, hash_only=True)[1] != policy_sha):
            return {**result, 'status':'unobservable', 'findings':[], 'reason':'generation_in_transition'}
        if (result['findings'] and execution.get('status') == 'running'
            and execution.get('command_status') != 'succeeded'
            and set(result['findings']) <= {'cancel_wait_stale_source_generation', 'cancel_wait_policy_binding_invalid'}):
            return {**result, 'status':'pending', 'findings':[], 'reason':'producer_generation_pending'}
        reuse_path = path.with_suffix('.reuse-contract.json')
        if reuse_path.exists() or reuse_path.is_symlink():
            reuse, _ = _semantic_object(reuse_path)
            result['reuse'] = {'artifact_sha256':reuse.get('artifact_sha256'),
                               'preflight_fingerprint':reuse.get('preflight_fingerprint')}
            if (reuse.get('artifact_sha256') != report_sha
                or reuse.get('preflight_fingerprint') != payload.get('preflight_fingerprint')):
                result['findings'].append('cancel_wait_reuse_generation_invalid')
        if view.get('findings'):
            result['consumers'] = {'status':'not_assessed'}
            return result
        summary_path = data_root/'report/runtime_approval_summary'/f'runtime_approval_summary_{source_date}.json'
        tower_path = data_root/'report/tuning_performance_control_tower'/f'tuning_performance_control_tower_{source_date}.json'
        checklist = root/'docs/checklists'/f"{policy['effective_date']}-stage2-todo-checklist.md"
        native_path = data_root/'report/threshold_cycle_postclose_status'/f'threshold_cycle_postclose_{source_date}.status.json'
        def stamp(candidate):
            actual = existing_or_gzip_path(candidate)
            try:
                value = actual.lstat()
            except FileNotFoundError:
                return None
            return (str(actual), value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns, actual.is_symlink())
        consumers = (summary_path, tower_path, checklist)
        generation_paths = (*consumers, path, policy_path, native_path, reuse_path)
        consumer_generation = tuple(stamp(candidate) for candidate in generation_paths)
        result['consumers'] = dict(status='pending', summary='pending', tower='pending', checklist='pending')
        reading_consumers = True
        completed = execution.get('status') in {'producers_completed', 'succeeded'} and bool(execution.get('run_id'))
        summary_sha = None
        if summary_path.exists() or summary_path.is_symlink():
            summary, summary_sha = _semantic_object(summary_path)
            source = (summary.get('sources') or {}).get('entry_cancel_wait') or {}
            summary_view = (source.get('economic_evidence') or {}).get('cancel_wait_reconciliation')
            if summary.get('date') == source_date and source.get('sha256') == report_sha and summary_view == view:
                result['consumers']['summary'] = 'verified'
            elif source.get('sha256') == report_sha:
                result['findings'].append('cancel_wait_consumer_projection_invalid')
        expected = owner.handoff_view(payload, policy, policy_path)
        if tower_path.exists() or tower_path.is_symlink():
            tower, _ = _semantic_object(tower_path)
            observed = tower.get('entry_cancel_wait_economic_tuning')
            # Older successor generations are pending during the native chain.
            receipt = tower.get('source_generation_contract') or {}
            sources = receipt.get('sources') or {}
            bound = (receipt.get('schema') == 'postclose_summary_sources_v1'
                and receipt.get('source_date') == source_date
                and (sources.get('entry_cancel_wait_tuning') or sources.get('entry_cancel_wait') or {}).get('sha256') == report_sha
                and (sources.get('entry_cancel_wait_policy') or {}).get('sha256') == policy_sha
                and summary_sha is not None
                and (sources.get('runtime_approval_summary') or {}).get('sha256') == summary_sha)
            if tower.get('date') == source_date and bound and observed == expected:
                result['consumers']['tower'] = 'verified'
            elif bound:
                result['findings'].append('cancel_wait_consumer_projection_invalid')
        if checklist.exists() or checklist.is_symlink():
            if checklist.is_symlink() or checklist.stat().st_size > 8 * 1024 * 1024:
                raise ValueError('cancel_wait_checklist_size_invalid')
            with checklist.open('rb') as handle:
                raw = handle.read(8 * 1024 * 1024 + 1)
            if len(raw) > 8 * 1024 * 1024:
                raise ValueError('cancel_wait_checklist_size_invalid')
            text = raw.decode('utf-8')
            markers = re.findall(r'<!-- POSTCLOSE_SUMMARY_SOURCES (.*?) -->', text)
            receipt = json.loads(markers[0]) if len(markers) == 1 else {}
            sources = receipt.get('sources') or {}
            bound = (receipt.get('schema') == 'postclose_summary_sources_v1'
                and receipt.get('source_date') == source_date
                and (sources.get('entry_cancel_wait_tuning') or {}).get('sha256') == report_sha
                and (sources.get('entry_cancel_wait_policy') or {}).get('sha256') == policy_sha
                and summary_sha is not None
                and (sources.get('runtime_approval_summary') or {}).get('sha256') == summary_sha)
            if (bound and text.count(owner.checklist_handoff(expected)) == 1
                and text.count('<!-- entry_cancel_wait_handoff:start -->') == 1
                and text.count('<!-- entry_cancel_wait_handoff:end -->') == 1):
                result['consumers']['checklist'] = 'verified'
        if all(result['consumers'][stage] == 'verified' for stage in ('summary', 'tower', 'checklist')):
            result['consumers']['status'] = 'verified'
        elif completed:
            result['findings'].append('cancel_wait_consumer_projection_invalid')
        native_sha = (_semantic_object(native_path, hash_only=True)[1]
            if native_path.exists() or native_path.is_symlink() else None)
        if (tuple(stamp(candidate) for candidate in generation_paths) != consumer_generation
            or _semantic_object(path, hash_only=True)[1] != report_sha
            or _semantic_object(policy_path, hash_only=True)[1] != policy_sha
            or native_sha != execution.get('status_sha256')
            or owner.validated_reconciliation_view(payload, policy, data_root=data_root,
                                                  read_object=_semantic_object) != view):
            return {**result, 'status':'unobservable', 'findings':[], 'reason':'generation_in_transition'}
        if result['findings']:
            result['status'] = 'source_invalid'
        result['findings'] = sorted(set(result['findings']))
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        failure = _semantic_failure(exc)
        if reading_consumers and failure['status'] != 'unobservable':
            try:
                changed = tuple(stamp(candidate) for candidate in generation_paths) != consumer_generation
            except OSError:
                changed = False
            if changed:
                failure = _semantic_failure(ValueError('semantic_generation_changed_during_read'))
            else:
                failure['findings'] = sorted(set(result['findings'] + ['cancel_wait_consumer_projection_invalid']))
                failure['error'] = str(exc)[:160]
        result.update(failure)
    return result


def _family_policy_semantics(root, source_date, family):
    from src.engine.monitoring import family_policy_semantics as native
    folders = {'episode': 'low_price_two_leg_tuning'}
    path = root / 'data/report' / folders[family] / f'{family}_policy_semantics_{source_date}.json'
    try:
        execution = _semantic_stage_binding(root, source_date, family + '_policy')
        if execution['status'] in {'pending', 'running'}:
            return dict(status='unobservable', source_date=source_date, artifact=str(path),
                        findings=[], execution=execution, reason='family_generation_in_transition')
    except (OSError, ValueError, TypeError, KeyError) as exc:
        return dict(_semantic_failure(exc), source_date=source_date, artifact=str(path))
    if not path.exists() and not path.is_symlink():
        if source_date >= '2026-10-06':
            try:
                stage = _semantic_stage_binding(root, source_date, family + '_policy')
                if stage['status'] == 'succeeded':
                    return dict(status='source_invalid', source_date=source_date, artifact=str(path),
                                findings=[f'{family}_semantic_projection_missing_after_completed_producer'])
            except (OSError, ValueError, TypeError, KeyError) as exc:
                return dict(_semantic_failure(exc), source_date=source_date, artifact=str(path))
        return {'status': 'not_assessed' if source_date < '2026-10-06' else 'waiting_producer',
                'source_date': source_date, 'findings': [], 'artifact': str(path)}
    try:
        value, sha = _semantic_object(path, limit=4 * 1024 * 1024)
        if (value != native.seal(value) or value.get('schema') != native.SCHEMA
            or value.get('metric_contract') != native.CONTRACT or value.get('family') != family
            or value.get('source_date') != source_date or value.get('runtime_effect') is not False
            or value.get('actual_order_submitted') is not False):
            raise ValueError(f'{family}_semantic_projection_invalid')
        for receipt in [value['report'], value['policy']]:
            _, source_sha = _semantic_object(Path(receipt['path']), hash_only=True)
            if source_sha != receipt['sha256']:
                raise ValueError(f'{family}_semantic_generation_mismatch')
        if not value.get('producer_kernels'):
            raise ValueError(f'{family}_semantic_producer_missing')
        kernel_custody = {}
        for source_path, source_sha in value['producer_kernels'].items():
            kernel_custody[source_path] = native.verify_kernel(root / 'data', source_path, source_sha)
        # The summary itself must still agree with its bound original report.
        # Retaining an old kernel is no authority to attach a different summary.
        original_report, _ = _semantic_object(Path(value['report']['path']))
        if value['summary'] != native.episode_summary(original_report):
            raise ValueError(f'{family}_semantic_summary_generation_mismatch')
        summary = value['summary']
        rows = summary['rows']
        if not isinstance(rows, list) or any(not isinstance(r, dict) for r in rows):
            raise ValueError(f'{family}_semantic_population_invalid')
        findings = []
        if family == 'episode':
            counts = summary.get('stage_counts') or {}
            dispositions = dict(Counter(r['disposition'] for r in rows))
            if counts.get('profiles') != len(rows) or summary.get('dispositions') != dispositions:
                raise ValueError('episode_semantic_population_invalid')
            if len({r['profile_id'] for r in rows}) != len(rows):
                raise ValueError('episode_semantic_duplicate_profile')
            from src.trading.config.owner_retirement import episode_profile_retired
            active_dispositions = Counter(r['disposition'] for r in rows if not episode_profile_retired(r['profile_id']))
            if active_dispositions.get('source_gap'):
                findings.append('episode_native_source_gap')
            if (summary.get('capture_manifest') or {}).get('invalid_event_count'):
                findings.append('episode_capture_invalid_events')
        # Re-read the small seal after its predecessor hashes to catch publication
        # between reads. A moving generation is unobservable, not corruption.
        if _semantic_object(path, limit=4 * 1024 * 1024)[1] != sha:
            raise ValueError('semantic_generation_changed_during_read')
        historical = execution.get('status') == 'off'
        return dict(status='off' if historical else 'warning' if findings else 'pass',
            findings=[] if historical else findings, historical_findings=findings if historical else [],
            source_date=source_date, target_date=value.get('target_date'),
            artifact=str(path), report_sha256=sha, summary=summary, kernel_custody=kernel_custody,
            scopes={r.get('profile_id') or f"{r['symbol']}|{r['session']}": r for r in rows},
            actual_pid_consumed=False, decision_authority='report_only')
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        return dict(_semantic_failure(exc), source_date=source_date, artifact=str(path))


def _samsung_forward_semantics(root, source_date, *, current_main=False):
    path = root / 'data/report/samsung_tick_transition_forward_validation' / source_date / 'latest.json'
    if source_date < '2026-10-06':
        return {'status': 'not_assessed', 'findings': [], 'source_date': source_date}
    if not path.exists() and not path.is_symlink():
        return dict(status='waiting_producer', findings=[], source_date=source_date,
                    artifact=str(path), consumption='not_observed')
    try:
        from src.engine.scalping import samsung_tick_transition_forward_validation as native
        index, sha = _semantic_object(path, limit=1024 * 1024)
        if (index != native.A.seal(index) or index.get('schema') != 'samsung_frozen_postclose_index_v1'
            or index.get('source_date') != source_date or index.get('candidate_id') != native.CANDIDATE
            or index.get('runtime_effect') is not False or index.get('policy_publication') is not False
            or index.get('actual_order_submitted') is not False
            or index.get('owner') != 'SamsungFrozenCandidateValidation1006'
            or index.get('decision_authority') != 'report_only'):
            raise ValueError('samsung_forward_index_invalid')
        result_path = Path(index['result_path'])
        if (result_path.resolve().parent.parent != path.parent.resolve()
            or result_path.parent.name != index.get('generation')
            or (index.get('status') != 'failed' and native.S.digest(index.get('identity')) != index.get('generation'))):
            raise ValueError('samsung_forward_result_path_invalid')
        result, result_sha = _semantic_object(result_path)
        if (result != native.A.seal(result) or result_sha != index['result_file_sha256']
            or result.get('schema') != 'samsung_tick_transition_forward_result_v1'
            or result.get('candidate_id') != native.CANDIDATE
            or any(type(result.get(k)) is not type(v) or result.get(k) != v for k, v in native.AUTHORITY.items())
            or result.get('day') != source_date or result.get('status') != index.get('status')
            or index.get('status') not in {'failed', 'waiting_new_source_date', 'evaluated', 'valid_empty', 'source_quality_excluded_all'}):
            raise ValueError('samsung_forward_result_invalid')
        findings = ['samsung_forward_execution_failed'] if index['status'] == 'failed' else []
        return dict(status='historical_diagnostic' if current_main else index['status'],
            findings=[] if current_main else findings, historical_findings=findings if current_main else [], source_date=source_date,
            artifact=str(path), report_sha256=sha, comparison=result.get('comparisons'),
            source_quality=result.get('source_quality'), missing_source_paths=result.get('missing_source_paths'),
            decision_authority='report_only')
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        return dict(_semantic_failure(exc), source_date=source_date, artifact=str(path))


def _semantic_due_target(now):
    from src.engine.automation import next_preopen_readiness as readiness
    current = now.replace(tzinfo=ZoneInfo('Asia/Seoul')) if now.tzinfo is None else now.astimezone(ZoneInfo('Asia/Seoul'))
    if is_krx_trading_day(current.date()) and current.hour * 60 + current.minute < 455:
        return current.date().isoformat()
    return readiness._next_trading_day(current.date()).isoformat()


def _completed_semantic_source(root, now):
    """Select a receipt-owned date, never yesterday/last weekday by guesswork.

    The native handoff validator checks the selected controller and prepared
    generation below. Invalid latest receipts must remain visible, not fall back
    to an older PASS. Limit the directory census to the newest 32 dated owners.
    """
    target = _semantic_due_target(now)
    as_of = now.date().isoformat()
    result = {'status': 'not_assessed', 'as_of_date': as_of, 'target_date': target,
              'source_date': None, 'findings': []}
    try:
        folder = root / 'data/report/postclose_done_controller'
        paths = sorted(folder.glob('postclose_done_controller_????-??-??.json'), reverse=True)[:32]
        for path in paths:
            day = path.stem[-10:]
            if day > as_of:
                continue
            result['artifact'] = str(path)
            value, sha = _semantic_object(path, limit=4 * 1024 * 1024)
            if (value.get('date') != day or value.get('report_type') != 'postclose_done_controller'
                or value.get('schema_version') != 2):
                raise ValueError('completed_semantic_controller_date_invalid')
            if value.get('status') not in {'done', 'failed', 'blocked'}:
                continue
            result.update(status='receipt_selected', source_date=day,
                          artifact=str(path), generation=sha)
            break
        index = root / 'data/runtime/policy_bootstrap/prepared' / target / 'latest.json'
        if index.exists() or index.is_symlink():
            pointer, _ = _semantic_object(index, limit=1024 * 1024)
            receipt_path = Path(pointer['receipt_path'])
            if receipt_path.resolve().parent.parent != index.parent.resolve():
                raise ValueError('completed_semantic_prepared_path_invalid')
            receipt, sha = _semantic_object(receipt_path, limit=1024 * 1024)
            if (pointer.get('schema') != 'next_preopen_readiness_index_v1'
                or pointer.get('target_date') != target or pointer.get('receipt_sha256') != sha
                or receipt.get('schema') != 'next_preopen_readiness_v1'
                or receipt.get('target_date') != target or receipt.get('status') != 'prepared_verified'
                or not isinstance(receipt.get('source_date'), str) or receipt['source_date'] > as_of):
                raise ValueError('completed_semantic_prepared_identity_invalid')
            result['prepared_source_date'] = receipt['source_date']
            result['prepared_generation'] = sha
            if result['source_date'] is None:
                result.update(status='receipt_selected', source_date=receipt['source_date'],
                              artifact=str(receipt_path), generation=sha)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        result.update(_semantic_failure(exc))
    return result


def _postclose_handoff_semantics(root, source_date, now):
    """Use native read-only closure/readiness checks; never prepare or apply."""
    from src.engine.automation import next_preopen_readiness as readiness
    from src.engine.automation.postclose_done_controller import done_terminal_receipt_issues
    result = {"status": "not_assessed", "source_date": source_date,
              "findings": [], "stages": {}, "consumption": "not_observed"}
    try:
        for stage in ("episode_policy",):
            result["stages"][stage] = _semantic_stage_binding(root, source_date, stage)
            if result["stages"][stage]["status"] == "succeeded":
                from src.engine.automation.postclose_summary_handoff import stage_artifacts
                for name, path in stage_artifacts(root / "data/report", source_date, stage).items():
                    _, sha = _semantic_object(path, hash_only=True)
                    _semantic_stage_binding(root, source_date, stage, artifact=name,
                                            artifact_sha=sha, artifact_path=path)
            if result["stages"][stage]["status"] in {"failed", "blocked", "source_quality_blocked"}:
                result["findings"].append(f"{stage}:execution_failed")
        if any(value['status'] in {'pending', 'running'} for value in result['stages'].values()):
            result.update(status='unobservable', target_date=_semantic_due_target(now),
                prepared=dict(status='unobservable', reason='producer_generation_in_transition'),
                reason='producer_generation_in_transition')
            return result
        controller_path = (root / "data/report/postclose_done_controller"
                           / f"postclose_done_controller_{source_date}.json")
        if controller_path.exists() or controller_path.is_symlink():
            controller, controller_sha = _semantic_object(controller_path)
            result["status"] = controller.get("status", "source_invalid")
            if controller.get("status") in {"failed", "blocked"}:
                result["findings"].append("postclose_handoff_execution_failed")
            if controller.get("status") == "done":
                errors = done_terminal_receipt_issues(controller_path, source_date, started_after_ns=0,
                                                     generation_only=True)
                result["validation_scope"] = "sealed_generation_not_new_full_chain_verification"
                if errors:
                    result["findings"].append("postclose_handoff_generation_invalid")
                    result["closure_errors"] = errors
                else:
                    result["report_sha256"] = controller_sha
                    result["artifact"] = str(controller_path)
        target = _semantic_due_target(now)
        result['target_date'] = target
        index = root / "data/runtime/policy_bootstrap/prepared" / target / "latest.json"
        if index.exists() or index.is_symlink():
            _semantic_object(index, limit=1024 * 1024)
            check = readiness.verify_prepared(target, generation_only=True)
            result["prepared"] = check
            if check.get("status") != "pass":
                result["findings"].append("next_preopen_prepared_contract_invalid")
        else:
            result['prepared'] = {'status': 'future_due', 'target_date': target,
                                  'consumption': 'not_observed'}
        # Actual PREOPEN/PID consumption remains in the startup detectors.
        if result["findings"]:
            result["status"] = "source_invalid"
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        if str(exc) == "semantic_generation_changed_during_read":
            result.update(_semantic_failure(exc))
        else:
            result.update(status="source_invalid", findings=["postclose_handoff_contract_invalid"], error=str(exc))
    return result


def _current_semantic_owners(root, day):
    """Project only today's parsed OPEN stable IDs; no historical fallback."""
    from src.engine.sync_docs_backlog_to_project import parse_checklist_tasks
    owners = Counter()
    path = root / 'docs/checklists' / (day + '-stage2-todo-checklist.md')
    for task in parse_checklist_tasks(current_path=path):
        if Path(task.source).resolve() != path.resolve():
            continue
        match = re.match(r'^\[([^\]]+)\]', task.title)
        if match:
            owners[match[1]] += 1
    return {key for key, count in owners.items() if count == 1}


def _semantic_alerts(name, semantics, source_date, *, current_owners=None, as_of_date=None):
    alerts = _semantic_alert_candidates(name, semantics, source_date)
    if current_owners is None:
        return alerts
    for alert in alerts:
        _project_semantic_owner(alert, current_owners, as_of_date)
    return alerts


def _project_semantic_owner(alert, current_owners, as_of_date):
    mapping = {
        'main_machine_policy': 'DirectFamilySourceRepairMainMechanisticEntry',
        'main_auxiliary_policy': 'DirectFamilySourceRepairMainMechanisticEntry',
        'postclose_handoff': 'DirectFamilyPreopenPolicyHandoff',
        'entry_cancel_wait_tuning': 'DirectFamilySourceRepairEntryCancelWait',
        'episode_policy': 'DirectFamilySourceRepairLowPriceTwoLeg',
        'episode_startup': 'EpisodeCaptureSequence1006',
        'samsung_frozen_validation': 'SemanticMonitorProducerConsumerRefresh1007',
        'legacy_machine_report': 'SemanticMonitorProducerConsumerRefresh1007',
    }
    owner = mapping.get(alert['stage'])
    alert.update(producer_owner=alert['owner'], historical_owner=alert['owner'],
                     owner=owner if owner in current_owners else 'UNRESOLVED_CURRENT_OWNER:' + str(owner),
                     owner_status='current_open' if owner in current_owners else 'unresolved',
                     observation_date=as_of_date, effective_date=alert.get('target_date'))


def _semantic_alert_candidates(name, semantics, source_date):
    if semantics.get('status') in {'off', 'historical_diagnostic'}:
        return []
    if name in {'episode_policy', 'samsung_frozen_validation', 'episode_startup'}:
        if semantics.get('status') in {'not_assessed', 'unobservable', 'waiting_producer', 'future_due'}:
            return []
        return [dict(source_date=source_date, target_date=semantics.get('target_date'),
            stage=name, scope='report', reason=reason, status=semantics['status'],
            artifact=semantics.get('artifact'), generation=semantics.get('report_sha256'),
            **(dict(affected=sum(reason in row.get('findings', []) for row in semantics.get('rows', [])),
                    eligible=sum(row.get('status') not in {'future_due', 'quarantined'}
                                 for row in semantics.get('rows', [])),
                    total=len(semantics.get('rows', [])), count_unit='profile')
               if name == 'episode_startup' and any(reason in row.get('findings', [])
                                                   for row in semantics.get('rows', [])) else {}),
            owner='WidgetEpisodeNextSessionStartup1006' if name == 'episode_startup'
                  else 'SamsungFrozenCandidateValidation1006' if name == 'samsung_frozen_validation'
                  else 'SemanticPolicyCoverageRemediation1006',
            closure_test='exact_family_date_generation_source_policy_and_native_validator')
            for reason in semantics.get('findings', [])]
    if name == "entry_cancel_wait_tuning":
        if semantics.get("status") != "source_invalid":
            return []
        return [{"source_date":source_date, "stage":name, "scope":"report",
            "reason":reason if reason.startswith("cancel_wait_") else "cancel_wait_reconciliation_ledger_invalid",
            "status":semantics["status"], "artifact":semantics.get("artifact"),
            "generation":semantics.get("report_sha256"),
            "affected":semantics.get("unclassified_submission_count"),
            "eligible":semantics.get("daily_submitted_parent_count"),
            "owner":"EntryCancelWaitSourceReconciliation1002",
            "closure_test":"same_date_original_source_ledger_policy_and_consumer_projection"}
            for reason in semantics.get("findings", [])]
    actionable = set("""
        auxiliary_candidate_population_invalid auxiliary_completed_report_generation_mismatch
        auxiliary_completed_report_missing auxiliary_execution_failed auxiliary_economic_denominator_invalid
        auxiliary_economic_metrics_invalid auxiliary_exact_plan_lineage_missing
        auxiliary_label_population_binding_invalid auxiliary_label_report_binding_invalid
        auxiliary_label_report_missing auxiliary_outcome_label_binding_missing auxiliary_outcome_label_source_gap
        auxiliary_population_denominator_invalid auxiliary_primary_economics_source_blocked
        auxiliary_scope_selection_contract_invalid auxiliary_scope_selection_status_invalid
        auxiliary_selected_without_independent_evidence auxiliary_source_lineage_invalid
        auxiliary_source_tuning_not_allowed auxiliary_stage_report_contract_invalid
        auxiliary_terminal_identity_or_hash_invalid auxiliary_terminal_source_binding_missing
        auxiliary_chronological_split_invalid auxiliary_frozen_selection_binding_invalid
        auxiliary_full_cost_census_invalid auxiliary_completed_response_census_invalid
        auxiliary_selected_without_frozen_full_cost_evidence auxiliary_selection_version_invalid
        auxiliary_eligible_identity_uninstrumented compact_operating_rows_all_excluded compact_projection_invalid
        machine_execution_failed machine_exclusion_counts_invalid machine_full_report_missing_with_winrate_sidecar
        machine_operating_economics_incomplete machine_operating_paired_unbound machine_population_count_invalid
        machine_report_date_or_hash_invalid machine_scope_evaluations_missing machine_scope_row_invalid
        machine_selected_without_recovery_evidence machine_selection_contract_invalid machine_selection_version_invalid
        machine_scope_selection_missing machine_source_contract_exclusions
        winrate_candidate_bundle_or_scope_mismatch winrate_market_denominator_invalid winrate_population_denominator_invalid
        winrate_report_hash_or_scope_invalid winrate_report_schema_invalid winrate_successor_hurdle_invalid
        winrate_selected_zero_or_undefined winrate_semantic_validation_failed winrate_terminal_binding_invalid
        winrate_execution_failed next_preopen_prepared_contract_invalid postclose_handoff_contract_invalid
        continuous_reversal_report_schema_invalid continuous_reversal_report_hash_or_date_invalid
        continuous_reversal_stage_report_mismatch continuous_reversal_dated_policy_invalid
        postclose_handoff_generation_invalid postclose_handoff_execution_failed
        episode_policy:execution_failed
    """.split())
    if semantics.get("status") in {"not_assessed", "unobservable"}:
        return []
    reasons = [reason for reason in semantics.get("findings", []) if reason in actionable]
    if not reasons and semantics.get("status") == "source_invalid":
        reasons = ["postclose_handoff_contract_invalid" if name == "postclose_handoff"
                   else "auxiliary_stage_report_contract_invalid" if name == "main_auxiliary_policy"
                   else "machine_report_date_or_hash_invalid"]
    return [{"source_date": source_date, "target_date": semantics.get('target_date'), "stage": name,
             "scope": scope, "reason": reason, "status": semantics.get("status"),
             "artifact": semantics.get("artifact"), "generation": semantics.get("report_sha256"),
             "affected": (semantics.get("outcome_label_source_gap_count")
                          if reason == "auxiliary_outcome_label_source_gap" else None),
             "eligible": (semantics.get("paired_comparable_count")
                          if reason == "auxiliary_primary_economics_source_blocked"
                          else semantics.get("source_lineage_counts", {}).get("writer_trace_plan_joined")
                          if reason == "auxiliary_exact_plan_lineage_missing"
                          else (semantics["economic_screened_total"] - semantics["outcome_label_source_gap_count"])
                          if reason == "auxiliary_outcome_label_source_gap" and type(semantics.get("economic_screened_total")) is int
                          else semantics.get("scopes", {}).get(scope, {}).get("eligible_count",
                           semantics.get("scopes", {}).get(scope, {}).get("eligible",
                           semantics.get("eligible_count")))),
             "total": (semantics.get("economic_screened_total") if reason in {
                 "auxiliary_primary_economics_source_blocked", "auxiliary_exact_plan_lineage_missing",
                 "auxiliary_outcome_label_source_gap", "auxiliary_outcome_label_binding_missing"}
                 else semantics.get("scopes", {}).get(scope, {}).get("full", semantics.get("screened_total"))),
             "owner": ("continuous_reversal_postclose" if semantics.get('stage_id') in {'main_machine_policy', 'main_auxiliary_policy'}
                       and (semantics.get('selection_metric') == 'cumulative_raw_win_fraction'
                            or str(semantics.get('artifact') or '').find('/continuous_reversal/') >= 0)
                       else "compact_auxiliary_paired_replay" if name == "main_auxiliary_policy"
                       else "next_preopen_readiness" if name == "postclose_handoff"
                       else "ai_action_outcome_calibration"),
             "closure_test": "same_date_scope_source_selection_and_terminal_hashes"}
            for reason in reasons
            for scope in ([key for key, value in (semantics.get("scopes") or {}).items()
                           if reason in value.get("findings", [])] or ["report"])]


def _reconcile_update_kospi_master_difference(
    payload: dict[str, Any],
    details: dict[str, Any],
) -> bool:
    """Accept only a fully verified, non-active eligibility difference.

    ``update_kospi`` deliberately preserves FDR rows even when the official
    ka10099 listing response does not return them.  That is a useful warning
    until the same-date canonical common-stock master proves every omitted
    code is outside the active trading universe.  Keep the reconciliation in
    the detector so the producer's raw warning and missing-code evidence stay
    intact.
    """

    if payload.get("status") != "completed_with_warnings":
        return False
    if payload.get("failed_steps") != []:
        return False
    if payload.get("warning_steps") != ["update_kospi_data"]:
        return False

    target_date_text = str(payload.get("target_date") or "").strip()
    try:
        target_date = date.fromisoformat(target_date_text)
    except ValueError:
        return False

    steps = payload.get("steps")
    if not isinstance(steps, list):
        return False
    update_steps = [
        step
        for step in steps
        if isinstance(step, dict) and step.get("name") == "update_kospi_data"
    ]
    if len(update_steps) != 1:
        return False
    update_step = update_steps[0]
    step_details = update_step.get("details")
    if not isinstance(step_details, dict):
        return False
    eligibility = step_details.get("eligibility")
    if (
        update_step.get("status") != "completed_with_warnings"
        or step_details.get("reason") != "market_eligibility_partial"
        or not isinstance(eligibility, dict)
        or eligibility.get("complete") is not True
        or eligibility.get("status") != "partial"
    ):
        return False

    market_meta = eligibility.get("market_source_meta")
    missing_codes = eligibility.get("missing_codes")
    requested_count = eligibility.get("requested_code_count")
    received_count = eligibility.get("received_code_count")
    if (
        not isinstance(market_meta, list)
        or {str(row.get("market")) for row in market_meta if isinstance(row, dict)}
        != {"0", "10"}
        or any(
            not isinstance(row, dict)
            or row.get("complete") is not True
            or row.get("continuous_next_key_missing") is True
            or row.get("continuous_page_limit_reached") is True
            for row in market_meta
        )
        or not isinstance(missing_codes, list)
        or not missing_codes
        or len({str(code) for code in missing_codes}) != len(missing_codes)
        or any(len(str(code)) != 6 or not str(code).isdigit() for code in missing_codes)
        or not isinstance(requested_count, int)
        or isinstance(requested_count, bool)
        or not isinstance(received_count, int)
        or isinstance(received_count, bool)
        or received_count + len(missing_codes) != requested_count
    ):
        return False

    master_path = existing_or_gzip_path(
        PROJECT_ROOT
        / "data/report/micro_reversion_economic_reference"
        / f"micro_reversion_symbol_master_{target_date_text}.json"
    )
    if not master_path.exists():
        return False

    try:
        from src.engine.scalping.micro_reversion.symbol_master import (
            SymbolLookupStatus,
            VerifiedSymbolMaster,
        )

        master = VerifiedSymbolMaster.from_json_path(
            master_path,
            require_canonical_owner=True,
        )
        allowed_statuses = {
            SymbolLookupStatus.MISSING,
            SymbolLookupStatus.OUTSIDE_EFFECTIVE_WINDOW,
        }
        lookup_statuses = {
            str(code): master.lookup(code, as_of=target_date).status
            for code in missing_codes
        }
    except (OSError, TypeError, ValueError):
        return False

    unresolved = {
        code: status.value
        for code, status in lookup_statuses.items()
        if status not in allowed_statuses
    }
    details["update_kospi_status_master_path"] = str(master_path)
    details["update_kospi_status_master_difference_count"] = len(missing_codes)
    details["update_kospi_status_master_difference_unresolved"] = unresolved
    if unresolved:
        return False
    details["update_kospi_status_warning_reconciliation"] = "benign_master_difference"
    return True


ARTIFACT_SCHEDULE_CONTRACTS: dict[str, dict[str, Any]] = {
    "pattern_lab_currentness_audit_report": {"markers": ["THRESHOLD_CYCLE_POSTCLOSE"], "parent_env_key": "THRESHOLD_CYCLE_RUN_SWING_POSTCLOSE", "parent_default_enabled": False},
    "pattern_lab_propagation_audit_report": {"markers": ["THRESHOLD_CYCLE_POSTCLOSE"], "parent_env_key": "THRESHOLD_CYCLE_RUN_SWING_POSTCLOSE", "parent_default_enabled": False},
    "codebase_performance_workorder_report": {
        "markers": ["THRESHOLD_CYCLE_POSTCLOSE"],
        "parent_env_key": "THRESHOLD_CYCLE_RUN_CODEBASE_PERFORMANCE_WORKORDER_REPORT",
        "parent_default_enabled": False,
    },
    "codex_workorder_runner_report": {
        "markers": ["POSTCLOSE_DONE_CONTROLLER"],
        "parent_env_key": "POSTCLOSE_DONE_CONTROLLER_RUN_CODEX",
        "parent_default_enabled": False,
    },
    "swing_live_dry_run_status": {"markers": ["SWING_LIVE_DRY_RUN"]},
    "swing_selection_funnel_report": {"markers": ["SWING_LIVE_DRY_RUN"]},
    "swing_lifecycle_audit_report": {
        "markers": ["THRESHOLD_CYCLE_POSTCLOSE"],
        "parent_env_key": "THRESHOLD_CYCLE_RUN_SWING_POSTCLOSE",
        "parent_default_enabled": False,
    },
    "swing_threshold_ai_review_report": {
        "markers": ["THRESHOLD_CYCLE_POSTCLOSE"],
        "parent_env_key": "THRESHOLD_CYCLE_RUN_SWING_POSTCLOSE",
        "parent_default_enabled": False,
    },
    "swing_improvement_automation_report": {
        "markers": ["THRESHOLD_CYCLE_POSTCLOSE"],
        "parent_env_key": "THRESHOLD_CYCLE_RUN_SWING_POSTCLOSE",
        "parent_default_enabled": False,
    },
    "swing_runtime_approval_report": {
        "markers": ["THRESHOLD_CYCLE_POSTCLOSE"],
        "parent_env_key": "THRESHOLD_CYCLE_RUN_SWING_POSTCLOSE",
        "parent_default_enabled": False,
    },
    "swing_pattern_lab_automation_report": {
        "markers": ["THRESHOLD_CYCLE_POSTCLOSE"],
        "parent_env_key": "THRESHOLD_CYCLE_RUN_SWING_POSTCLOSE",
        "parent_default_enabled": False,
    },
    "swing_model_retrain_diagnosis": {"markers": ["SWING_MODEL_RETRAIN_POSTCLOSE"]},
    "swing_bull_period_ai_review": {"markers": ["SWING_MODEL_RETRAIN_POSTCLOSE"]},
    "swing_model_retrain_report": {"markers": ["SWING_MODEL_RETRAIN_POSTCLOSE"]},
    "swing_model_retrain_status": {"markers": ["SWING_MODEL_RETRAIN_POSTCLOSE"]},
    "swing_model_registry_current": {"markers": ["SWING_MODEL_RETRAIN_POSTCLOSE"]},
    "swing_daily_simulation_status": {
        "markers": ["THRESHOLD_CYCLE_POSTCLOSE"],
        "parent_env_key": "THRESHOLD_CYCLE_RUN_SWING_POSTCLOSE",
        "parent_default_enabled": False,
    },
    "swing_daily_simulation_report": {
        "markers": ["THRESHOLD_CYCLE_POSTCLOSE"],
        "parent_env_key": "THRESHOLD_CYCLE_RUN_SWING_POSTCLOSE",
        "parent_default_enabled": False,
    },
}

ARTIFACT_TERMINAL_SKIP_CONTRACTS: dict[str, dict[str, str]] = {
    "codebase_performance_workorder_report": {
        "log": "logs/threshold_cycle_postclose_cron.log",
        "step": "codebase_performance_workorder",
    }
}


ARTIFACT_REGISTRY: list[dict[str, Any]] = [
    {
        "id": "pipeline_events",
        "path_template": "data/pipeline_events/pipeline_events_{date}.jsonl",
        "max_staleness_sec": 600,
        "critical": True,
        "trading_day_only": True,
        "window_start": (9, 0),
        "window_end": (15, 30),
        "window_grace_sec": 300,
    },
    {
        "id": "threshold_events",
        "path_template": "data/threshold_cycle/threshold_events_{date}.jsonl",
        "partitioned_compact": {
            "checkpoint_template": "data/threshold_cycle/checkpoints/{date}.json",
            "partition_glob_template": "data/threshold_cycle/date={date}/family=*/part-*.jsonl*",
        },
        "max_staleness_sec": 600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (9, 0),
        "window_end": (15, 30),
        "window_grace_sec": 300,
    },
    {
        "id": "daily_recommendations_csv",
        "path_template": "data/daily_recommendations_v2.csv",
        "max_staleness_sec": 3600,
        "critical": False,
        "window_start": (7, 20),
        "window_end": (8, 0),
        "trading_day_only": True,
        "content_freshness": {
            "format": "csv",
            "date_field": "date",
            "max_age_days": 7,
            "min_rows": 1,
        },
    },
    {
        "id": "daily_recommendations_diag",
        "path_template": "data/daily_recommendations_v2_diagnostics.json",
        "max_staleness_sec": 3600,
        "critical": False,
        "window_start": (7, 20),
        "window_end": (8, 0),
        "trading_day_only": True,
        "content_freshness": {
            "format": "json",
            "date_field": "latest_date",
            "max_age_days": 7,
            "min_count_field": "selected_count",
            "min_count": 1,
        },
    },
    {
        "id": "runtime_policy_bootstrap",
        "path_template": "data/runtime/policy_bootstrap/runtime_policy_bootstrap_{date}.json",
        "max_staleness_sec": 900,
        "critical": True,
        "window_start": (7, 35),
        "window_end": (7, 50),
        # The producer and the full detector are both installed at 07:35.
        # Allow one detector interval for the producer to replace the previous
        # evening's target-date handoff before treating it as stale.
        "window_grace_sec": 300,
        "trading_day_only": True,
    },
    {
        "id": "threshold_preopen_status",
        "path_template": "data/report/threshold_cycle_preopen_status/threshold_cycle_preopen_{date}.status.json",
        "max_staleness_sec": 1800,
        "critical": True,
        "trading_day_only": True,
        "window_start": (7, 50),
        "window_end": (8, 5),
        "json_status_field": "status",
        "json_ok_values": ["succeeded"],
    },
    {
        "id": "submission_bottleneck_monitor",
        "first_required_date": "2026-09-21",
        "path_template": "data/report/buy_funnel_sentinel/submission_bottleneck_monitor_{date}.json",
        "max_staleness_sec": 600,
        "critical": True,
        "trading_day_only": True,
        "window_start": (8, 10),
        "window_end": (20, 0),
        "json_status_field": "notification_status",
        "json_ok_values": ["idle", "sent", "cooldown"],
    },
    {
        "id": "buy_funnel_sentinel_report",
        "path_template": "data/report/buy_funnel_sentinel/buy_funnel_sentinel_{date}.md",
        "max_staleness_sec": 600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (9, 5),
        "window_end": (15, 30),
    },
    {
        "id": "bd_fbuy_accum_pre_artifact",
        "path_template": "data/runtime/bd_fbuy_accum_pre/BD_FBUY_ACCUM_PRE_V1_{date}.json",
        "max_staleness_sec": 900,
        "critical": False,
        "trading_day_only": True,
        "window_start": (9, 5),
        "window_end": (15, 20),
        "json_status_field": "schema_version",
        "json_ok_values": ["BD_FBUY_ACCUM_PRE_V1"],
    },
    {
        "id": "holding_exit_sentinel_report",
        "path_template": "data/report/holding_exit_sentinel/holding_exit_sentinel_{date}.md",
        "max_staleness_sec": 600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (9, 5),
        "window_end": (15, 30),
    },
    {
        "id": "holding_exit_sentinel_premarket_report",
        "path_template": "data/report/holding_exit_sentinel/holding_exit_sentinel_{date}.md",
        "max_staleness_sec": 600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (8, 5),
        "window_end": (8, 55),
    },
    {
        "id": "holding_exit_sentinel_aftermarket_report",
        "path_template": "data/report/holding_exit_sentinel/holding_exit_sentinel_{date}.md",
        "max_staleness_sec": 600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (16, 0),
        "window_end": (19, 50),
    },
    {
        "id": "panic_sell_defense_report",
        "path_template": "data/report/panic_sell_defense/panic_sell_defense_{date}.md",
        "max_staleness_sec": 600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (9, 5),
        "window_end": (15, 30),
    },
    {
        "id": "market_panic_breadth_report",
        "path_template": "data/report/market_panic_breadth/market_panic_breadth_{date}.json",
        "max_staleness_sec": 600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (9, 5),
        "window_end": (15, 30),
    },
    {
        "id": "runtime_approval_summary_report",
        "path_template": "data/report/runtime_approval_summary/runtime_approval_summary_{date}.json",
        "max_staleness_sec": 1800,
        "critical": True,
        "one_shot": True,
        "trading_day_only": True,
        "window_start": (20, 10),
        "window_end": (21, 40),
        "window_grace_sec": 1200,
        "suppress_missing_while_cron_in_progress": {
            "id": "threshold_cycle_postclose",
            "log": "logs/threshold_cycle_postclose_cron.log",
            "process_patterns": [
                "deploy/run_threshold_cycle_postclose.sh",
                "run_threshold_cycle_postclose.sh",
            ],
        },
        "allow_missing_after_window_while_cron_in_progress": True,
    },
    {
        "id": "threshold_postclose_status",
        "path_template": "data/report/threshold_cycle_postclose_status/threshold_cycle_postclose_{date}.status.json",
        "max_staleness_sec": 3600,
        "critical": True,
        "one_shot": True,
        "trading_day_only": True,
        "window_start": (21, 40),
        "window_end": (22, 10),
        "json_status_field": "status",
        "json_ok_values": ["succeeded"],
        "running_status_deadline": (23, 20),
        "suppress_missing_while_cron_in_progress": {
            "id": "threshold_cycle_postclose",
            "log": "logs/threshold_cycle_postclose_cron.log",
            "process_patterns": [
                "deploy/run_threshold_cycle_postclose.sh",
                "run_threshold_cycle_postclose.sh",
            ],
        },
        "allow_missing_after_window_while_cron_in_progress": True,
    },
    {
        "id": "postclose_done_controller_report",
        "path_template": "data/report/postclose_done_controller/postclose_done_controller_{date}.json",
        "max_staleness_sec": 3600,
        "critical": True,
        "one_shot": True,
        "trading_day_only": True,
        "window_start": (20, 10),
        "window_end": (21, 55),
        "window_grace_sec": 300,
        "json_status_field": "status",
        "json_ok_values": ["done", "dry_run_planned"],
        "suppress_missing_while_cron_in_progress": {
            "id": "postclose_done_controller",
            "log": "logs/postclose_done_controller_cron.log",
        },
        "allow_missing_after_window_while_cron_in_progress": True,
    },
    {
        "id": "codex_workorder_runner_report",
        "path_template": "data/report/codex_workorder_runner/codex_workorder_runner_{date}.json",
        "max_staleness_sec": 3600,
        "critical": False,
        "one_shot": True,
        "trading_day_only": True,
        "window_start": (20, 10),
        "window_end": (21, 55),
        "json_status_field": "status",
        "json_ok_values": ["completed", "dry_run_planned"],
        "suppress_missing_while_cron_in_progress": {
            "id": "postclose_done_controller",
            "log": "logs/postclose_done_controller_cron.log",
        },
        "allow_missing_after_window_while_cron_in_progress": True,
    },
    {
        "id": "code_improvement_workorder",
        "path_template": "docs/code-improvement-workorders/code_improvement_workorder_{date}.md",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (20, 10),
        "window_end": (21, 40),
    },
    {
        "id": "pipeline_event_verbosity_report",
        "path_template": "data/report/pipeline_event_verbosity/pipeline_event_verbosity_{date}.md",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (20, 10),
        "window_end": (21, 40),
        "suppress_missing_while_cron_in_progress": {
            "id": "threshold_cycle_postclose",
            "log": "logs/threshold_cycle_postclose_cron.log",
        },
        "allow_missing_after_window_while_cron_in_progress": True,
    },
    {
        "id": "observation_source_quality_audit_report",
        "path_template": "data/report/observation_source_quality_audit/observation_source_quality_audit_{date}.md",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (20, 10),
        "window_end": (21, 40),
        "suppress_missing_while_cron_in_progress": {
            "id": "threshold_cycle_postclose",
            "log": "logs/threshold_cycle_postclose_cron.log",
        },
        "allow_missing_after_window_while_cron_in_progress": True,
    },
    {
        "id": "codebase_performance_workorder_report",
        "path_template": "data/report/codebase_performance_workorder/codebase_performance_workorder_{date}.md",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (20, 10),
        "window_end": (21, 40),
        "suppress_missing_while_cron_in_progress": {
            "id": "threshold_cycle_postclose",
            "log": "logs/threshold_cycle_postclose_cron.log",
        },
        "allow_missing_after_window_while_cron_in_progress": True,
    },
    {
        "id": "system_metric_samples",
        "path_template": "logs/system_metric_samples.jsonl",
        "max_staleness_sec": 180,
        "critical": False,
        "trading_day_only": True,
        "window_start": (9, 0),
        "window_end": (15, 30),
    },
    {
        "id": "swing_live_dry_run_status",
        "path_template": "data/report/swing_selection_funnel/status/swing_live_dry_run_{date}.status.json",
        "max_staleness_sec": 1800,
        "critical": False,
        "trading_day_only": True,
        "window_start": (20, 15),
        "window_end": (20, 35),
        "json_status_field": "status",
        "json_ok_values": ["succeeded", "skipped"],
    },
    {
        "id": "swing_selection_funnel_report",
        "path_template": "data/report/swing_selection_funnel/swing_selection_funnel_{date}.md",
        "max_staleness_sec": 1800,
        "critical": False,
        "trading_day_only": True,
        "window_start": (20, 15),
        "window_end": (20, 35),
    },
    {
        "id": "swing_lifecycle_audit_report",
        "path_template": "data/report/swing_lifecycle_audit/swing_lifecycle_audit_{date}.md",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (20, 10),
        "window_end": (21, 40),
    },
    {
        "id": "swing_threshold_ai_review_report",
        "path_template": "data/report/swing_threshold_ai_review/swing_threshold_ai_review_{date}.md",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (20, 10),
        "window_end": (21, 40),
    },
    {
        "id": "swing_improvement_automation_report",
        "path_template": "data/report/swing_improvement_automation/swing_improvement_automation_{date}.json",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (20, 10),
        "window_end": (21, 40),
    },
    {
        "id": "swing_runtime_approval_report",
        "path_template": "data/report/swing_runtime_approval/swing_runtime_approval_{date}.json",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (20, 10),
        "window_end": (21, 40),
    },
    {
        "id": "swing_pattern_lab_automation_report",
        "path_template": "data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_{date}.json",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (20, 10),
        "window_end": (21, 40),
    },
    {
        "id": "pattern_lab_currentness_audit_report",
        "path_template": "data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_{date}.json",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (20, 10),
        "window_end": (21, 40),
        "suppress_missing_while_cron_in_progress": {
            "id": "threshold_cycle_postclose",
            "log": "logs/threshold_cycle_postclose_cron.log",
        },
        "allow_missing_after_window_while_cron_in_progress": True,
    },
    {
        "id": "pattern_lab_propagation_audit_report",
        "path_template": "data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_{date}.json",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (20, 10),
        "window_end": (21, 40),
        "suppress_missing_while_cron_in_progress": {
            "id": "threshold_cycle_postclose",
            "log": "logs/threshold_cycle_postclose_cron.log",
        },
        "allow_missing_after_window_while_cron_in_progress": True,
    },
    {
        "id": "swing_model_retrain_diagnosis",
        "path_template": "data/report/swing_model_retrain/diagnosis_{date}.json",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (17, 30),
        "window_end": (18, 30),
    },
    {
        "id": "swing_bull_period_ai_review",
        "path_template": "data/report/swing_model_retrain/bull_period_ai_review_{date}.json",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (17, 30),
        "window_end": (18, 30),
    },
    {
        "id": "swing_model_retrain_report",
        "path_template": "data/report/swing_model_retrain/swing_model_retrain_{date}.json",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (17, 30),
        "window_end": (18, 30),
    },
    {
        "id": "swing_model_retrain_status",
        "path_template": "data/report/swing_model_retrain/status/swing_model_retrain_{date}.status.json",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (17, 30),
        "window_end": (18, 30),
        "json_status_field": "status",
        "json_ok_values": ["succeeded", "skipped"],
    },
    {
        "id": "swing_model_registry_current",
        "path_template": "data/model_registry/swing_v2/current.json",
        "max_staleness_sec": 7776000,
        "critical": False,
        "trading_day_only": True,
        "window_start": (17, 30),
        "window_end": (18, 30),
    },
    {
        "id": "swing_daily_simulation_status",
        "path_template": "data/report/swing_daily_simulation/status/swing_daily_simulation_{date}.status.json",
        "max_staleness_sec": 3600,
        "critical": False,
        "one_shot": True,
        "trading_day_only": True,
        "window_start": (21, 0),
        "window_end": (21, 50),
        "json_status_field": "status",
        "json_ok_values": ["succeeded", "skipped"],
    },
    {
        "id": "swing_daily_simulation_report",
        "path_template": "data/report/swing_daily_simulation/swing_daily_simulation_{date}.json",
        "max_staleness_sec": 3600,
        "critical": False,
        "one_shot": True,
        "trading_day_only": True,
        "window_start": (21, 0),
        "window_end": (21, 50),
    },
    {
        "id": "update_kospi_status",
        "path_template": "data/runtime/update_kospi_status/update_kospi_{date}.json",
        "max_staleness_sec": 1800,
        "critical": False,
        "trading_day_only": False,
        "window_start": (20, 5),
        "window_end": (21, 5),
        "json_status_field": "status",
        "json_ok_values": ["completed", "skipped_non_trading_day"],
    },
]


@register_detector
class ArtifactFreshnessDetector(BaseDetector):
    id = "artifact_freshness"
    name = "Artifact Freshness Detector"
    category = "artifact"

    def check(self) -> DetectionResult:
        now_dt = datetime.now()
        now_ts = time.time()
        now_h, now_m = _kst_time_tuple(now_dt)
        now_total = now_h * 60 + now_m
        source_day = getattr(self, "postclose_source_date", None)
        today = source_day or _today_kst_str(now_dt)
        past_source_day = bool(source_day and source_day < _today_kst_str(now_dt))
        if past_source_day:
            now_total = 24 * 60
        trading_day = is_krx_trading_day(datetime.strptime(today, "%Y-%m-%d").date())
        details: dict = {}
        issues: list[str] = []
        warnings: list[str] = []
        installed_crontab = load_installed_crontab()

        for artifact in ARTIFACT_REGISTRY:
            aid = artifact["id"]
            if today < artifact.get("first_required_date", "0001-01-01"):
                details[f"{aid}_status"] = "not_required_before_introduction"
                continue
            artifact_day = today
            artifact_now_total = now_total
            artifact_past_source_day = past_source_day
            if aid == "runtime_policy_bootstrap" and past_source_day:
                prepared = os.environ.get("POSTCLOSE_PREPARED_EFFECTIVE_DATE", "")
                try:
                    prepared_day = date.fromisoformat(prepared)
                    if prepared <= today or not is_krx_trading_day(prepared_day):
                        raise ValueError("invalid prepared date")
                except ValueError:
                    details[f"{aid}_status"] = "fail"
                    issues.append(f"{aid}: explicit prepared effective date missing or invalid")
                    continue
                details[f"{aid}_historical_source_date"] = today
                details[f"{aid}_prepared_effective_date"] = prepared
                if prepared > _today_kst_str(now_dt):
                    details[f"{aid}_status"] = "future_due"
                    continue
                artifact_day = prepared
                artifact_past_source_day = prepared < _today_kst_str(now_dt)
                artifact_now_total = 24 * 60 if artifact_past_source_day else now_h * 60 + now_m
            path_str = artifact["path_template"].replace("{date}", artifact_day)
            artifact_path = PROJECT_ROOT / path_str
            artifact_path = existing_or_gzip_path(artifact_path)
            critical = artifact.get("critical", False)
            max_stale = artifact.get("max_staleness_sec", 600)
            trading_day_only = artifact.get("trading_day_only", False)
            ws = artifact.get("window_start")
            we = artifact.get("window_end")

            if trading_day_only and not trading_day:
                details[f"{aid}_status"] = "skip_non_trading_day"
                continue

            schedule_contract = ARTIFACT_SCHEDULE_CONTRACTS.get(aid)
            if schedule_contract:
                schedule_status, schedule_details = evaluate_schedule_contract(
                    installed_crontab,
                    **schedule_contract,
                )
                details[f"{aid}_schedule_contract"] = schedule_details
                if schedule_status.startswith("disabled_"):
                    details[f"{aid}_status"] = schedule_status
                    continue

            ws_total = ws[0] * 60 + ws[1] if ws else None

            if ws_total is not None and artifact_now_total < ws_total:
                details[f"{aid}_status"] = "not_yet_due"
                details[f"{aid}_window"] = f"{ws[0]:02d}:{ws[1]:02d}"
                continue

            past_window_end = False
            if we is not None:
                window_end = now_dt.replace(
                    hour=we[0], minute=we[1], second=0, microsecond=0
                )
                past_window_end = artifact_past_source_day or now_dt >= window_end
            exists = artifact_path.exists()
            grace_sec = int(artifact.get("window_grace_sec") or 0)
            in_startup_grace = False
            if grace_sec > 0 and ws and not past_window_end:
                window_start = now_dt.replace(
                    hour=ws[0], minute=ws[1], second=0, microsecond=0
                )
                elapsed_from_start = (now_dt - window_start).total_seconds()
                in_startup_grace = 0 <= elapsed_from_start <= grace_sec
            if not exists and in_startup_grace:
                details[f"{aid}_status"] = "startup_grace"
                details[f"{aid}_window"] = f"{ws[0]:02d}:{ws[1]:02d}"
                details[f"{aid}_grace_sec"] = grace_sec
                continue

            if not exists:
                terminal_skip = self._terminal_skip_status(aid, artifact_day)
                if terminal_skip:
                    details[f"{aid}_status"] = "pass_terminal_skip"
                    details[f"{aid}_terminal_skip"] = terminal_skip
                    continue
                alternate_status = self._validate_partitioned_compact(
                    artifact,
                    artifact_day,
                    details,
                )
                if alternate_status:
                    status, warning = alternate_status
                    details[f"{aid}_status"] = status
                    if warning:
                        warnings.append(warning)
                    continue

                in_progress_cron = self._is_upstream_cron_in_progress(
                    artifact.get("suppress_missing_while_cron_in_progress"),
                    artifact_day,
                )
                if in_progress_cron and not past_window_end:
                    warnings.append(
                        f"{aid}: upstream cron in progress; artifact not generated yet"
                    )
                    details[f"{aid}_status"] = "warning"
                    details[f"{aid}_upstream_status"] = "in_progress"
                    continue
                if (
                    in_progress_cron
                    and past_window_end
                    and bool(
                        artifact.get(
                            "allow_missing_after_window_while_cron_in_progress"
                        )
                    )
                ):
                    warnings.append(
                        f"{aid}: upstream cron still in progress after window end"
                    )
                    details[f"{aid}_status"] = "warning"
                    details[f"{aid}_upstream_status"] = "in_progress_after_window"
                    continue
                if past_window_end:
                    if critical:
                        issues.append(f"{aid}: missing after window end")
                        details[f"{aid}_status"] = "fail"
                    else:
                        warnings.append(f"{aid}: not generated within window")
                        details[f"{aid}_status"] = "warning"
                else:
                    if critical:
                        issues.append(f"{aid}: {path_str} missing")
                        details[f"{aid}_status"] = "fail"
                    else:
                        warnings.append(f"{aid}: {path_str} not found")
                        details[f"{aid}_status"] = "warning"
                continue

            mtime = artifact_path.stat().st_mtime
            age_sec = now_ts - mtime
            details[f"{aid}_age_sec"] = round(age_sec, 1)
            json_error = self._validate_json_artifact(artifact_path)
            if json_error:
                details[f"{aid}_content_status"] = "invalid_json"
                message = f"{aid}: invalid JSON ({json_error})"
                if critical:
                    issues.append(message)
                    details[f"{aid}_status"] = "fail"
                else:
                    warnings.append(message)
                    details[f"{aid}_status"] = "warning"
                continue
            status_warning = self._validate_json_status(
                artifact, artifact_path, details
            )
            if status_warning:
                if self._is_bounded_postclose_running(
                    artifact, artifact_path, artifact_day, now_dt
                ):
                    warnings.append(
                        f"{aid}: exact-date postclose still running before deadline"
                    )
                    details[f"{aid}_status"] = "warning"
                    details[f"{aid}_upstream_status"] = "running_before_deadline"
                    details[f"{aid}_running_deadline"] = "23:20"
                    continue
                if critical:
                    issues.append(status_warning)
                    details[f"{aid}_status"] = "fail"
                else:
                    warnings.append(status_warning)
                    details[f"{aid}_status"] = "warning"
                continue
            content_warning, content_passed = self._validate_content_freshness(
                artifact,
                artifact_path,
                details,
                now_dt,
            )
            if content_warning:
                warnings.append(content_warning)
                details[f"{aid}_status"] = "warning"
                continue
            if content_passed:
                details[f"{aid}_status"] = "pass_content_date"
                continue

            if artifact.get("one_shot"):
                details[f"{aid}_status"] = "pass_one_shot"
                continue

            if past_window_end:
                details[f"{aid}_status"] = "pass_after_window"
                continue

            if age_sec > max_stale:
                if in_startup_grace:
                    details[f"{aid}_status"] = "startup_grace"
                    details[f"{aid}_window"] = f"{ws[0]:02d}:{ws[1]:02d}" if ws else ""
                    details[f"{aid}_grace_sec"] = grace_sec
                    details[f"{aid}_startup_stale_suppressed"] = True
                    continue
                if critical:
                    issues.append(f"{aid}: stale ({age_sec:.0f}s > {max_stale}s)")
                    details[f"{aid}_status"] = "fail"
                else:
                    warnings.append(f"{aid}: stale ({age_sec:.0f}s > {max_stale}s)")
                    details[f"{aid}_status"] = "warning"
            else:
                details[f"{aid}_status"] = "pass"

        cancel_wait_day = _cancel_wait_monitor_source_date(PROJECT_ROOT, today)
        cancel_wait = None
        if trading_day or cancel_wait_day != today:
            cancel_wait = _entry_cancel_wait_result_semantics(PROJECT_ROOT, cancel_wait_day, now_dt)
            details["entry_cancel_wait_result_semantics"] = cancel_wait
            if cancel_wait["findings"]:
                warnings.append("entry_cancel_wait_result_semantics: " + ", ".join(cancel_wait["findings"]))
        if trading_day:
            holding_semantics = _holding_profit_exit_semantics(PROJECT_ROOT, today)
            details["holding_profit_exit_semantics"] = holding_semantics
            if holding_semantics["findings"]:
                warnings.append("holding_profit_exit_semantics: " + ", ".join(
                    holding_semantics["findings"]))
        selection = _completed_semantic_source(PROJECT_ROOT, now_dt)
        details['completed_semantic_source'] = selection
        semantic_days = list(dict.fromkeys(
            ([today] if trading_day or source_day else []) +
            [d for d in (selection.get('source_date'), selection.get('prepared_source_date')) if d]))
        alerts = []
        bindings = []
        observations = []
        for semantic_day in semantic_days:
            machine_semantics = _machine_result_semantics(PROJECT_ROOT, semantic_day)
            details["machine_result_semantics"] = machine_semantics
            if machine_semantics["findings"]:
                warnings.append("machine_result_semantics: " + ", ".join(machine_semantics["findings"]))
            auxiliary_semantics = _auxiliary_result_semantics(PROJECT_ROOT, semantic_day)
            details["auxiliary_result_semantics"] = auxiliary_semantics
            if auxiliary_semantics["findings"]:
                warnings.append("auxiliary_result_semantics: " + ", ".join(
                    auxiliary_semantics["findings"]))
            handoff = _postclose_handoff_semantics(PROJECT_ROOT, semantic_day, now_dt)
            details["postclose_handoff_semantics"] = handoff
            if handoff["findings"]:
                warnings.append("postclose_handoff_semantics: " + ", ".join(handoff["findings"]))
            family_results = [(name, _family_policy_semantics(PROJECT_ROOT, semantic_day, family))
                              for name, family in (('episode_policy', 'episode'),)]
            family_results.append(('samsung_frozen_validation', _samsung_forward_semantics(
                PROJECT_ROOT, semantic_day, current_main=machine_semantics.get('selection_metric') == 'cumulative_raw_win_fraction')))
            for name, result in family_results:
                details[name + '_semantics'] = result
                if result['findings']:
                    warnings.append(name + '_semantics: ' + ', '.join(result['findings']))
            for name, semantics in (
                (machine_semantics.get('stage_id', "legacy_machine_report"), machine_semantics),
                ("main_auxiliary_policy", auxiliary_semantics),
                ("postclose_handoff", handoff), *family_results):
                semantics.setdefault('target_date', selection['target_date'])
                semantics['due_target_date'] = selection['target_date']
                observations.append(dict(stage=name, semantics=semantics))
                bindings.append({'stage': name, 'source_date': semantic_day,
                    'target_date': semantics.get('target_date'), 'as_of_date': _today_kst_str(now_dt),
                    'generation': semantics.get('report_sha256'), 'status': semantics.get('status')})
                alerts.extend(_semantic_alerts(name, semantics, semantic_day))
        if selection.get('findings'):
            alerts.extend(_semantic_alerts('postclose_handoff', selection, selection.get('source_date') or today))
            bindings.append(dict(stage='postclose_handoff', source_date=selection.get('source_date') or today,
                target_date=selection['target_date'], as_of_date=_today_kst_str(now_dt),
                generation=selection.get('report_sha256'), status=selection['status']))
            warnings.append('completed_semantic_source: ' + ', '.join(selection['findings']))
        details['semantic_source_bindings'] = bindings
        details['semantic_observations'] = observations
        if cancel_wait is not None:
            alerts.extend(_semantic_alerts('entry_cancel_wait_tuning', cancel_wait, cancel_wait_day))
        details['semantic_alerts'] = alerts
        from src.engine.error_detectors.episode_health import check as episode_check
        episode_startup = episode_check(PROJECT_ROOT, now_dt,
            target_date=selection['target_date'] if not trading_day else today, reader=_semantic_object,
            read_clock=lambda: datetime.now(ZoneInfo('Asia/Seoul')))
        details['episode_startup_semantics'] = episode_startup
        if episode_startup['findings']:
            warnings.append('episode_startup_semantics: ' + ', '.join(episode_startup['findings']))
        startup_alerts = _semantic_alerts('episode_startup', episode_startup, episode_startup['source_date'])
        alerts.extend(startup_alerts)
        bindings.append(dict(stage='episode_startup', source_date=episode_startup['source_date'],
            target_date=episode_startup['target_date'], as_of_date=_today_kst_str(now_dt),
            generation=episode_startup.get('report_sha256'), status=episode_startup['status']))
        current_owners = _current_semantic_owners(PROJECT_ROOT, today)
        # Apply one exact-date owner projection to every semantic hook,
        # including startup and cancel-wait hooks outside the stage loop.
        for alert in alerts:
            _project_semantic_owner(alert, current_owners, today)
        details['semantic_owner_projection'] = dict(as_of_date=today, open_ids=sorted(current_owners))
        from src.engine.monitoring.error_detector_coverage import validate_semantic_coverage
        coverage = validate_semantic_coverage(today)
        details['functional_semantic_coverage'] = coverage
        issues.extend('semantic_coverage: ' + finding for finding in coverage['findings'])
        if trading_day:
            quantity_semantics = _initial_quantity_semantics(
                PROJECT_ROOT, today, now_epoch=now_ts)
            details["initial_quantity_semantics"] = quantity_semantics
            if quantity_semantics["findings"]:
                warnings.append("initial_quantity_semantics: " + ", ".join(
                    sorted(set(quantity_semantics["findings"]))))

        severity, summary = self._classify(issues, warnings)
        return DetectionResult(
            detector_id=self.id,
            category=self.category,
            severity=severity,
            summary=summary,
            details=details,
            recommended_action=self._recommend_action(severity, issues),
        )

    @staticmethod
    def _terminal_skip_status(aid: str, today: str) -> dict[str, str] | None:
        contract = ARTIFACT_TERMINAL_SKIP_CONTRACTS.get(aid)
        if not contract:
            return None
        log_path = PROJECT_ROOT / contract["log"]
        if not log_path.exists():
            return None
        try:
            lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()[
                -5000:
            ]
        except OSError:
            return None
        step_token = f"step={contract['step']}"
        for line in reversed(lines):
            if (
                "[SKIP]" in line
                and f"target_date={today}" in line
                and step_token in line
            ):
                return {
                    "log": contract["log"],
                    "step": contract["step"],
                    "marker": line.strip(),
                }
        return None

    @staticmethod
    def _classify(issues: list[str], warnings: list[str]) -> tuple[str, str]:
        if issues:
            return "fail", f"Artifact failures: {'; '.join(issues[:5])}"
        if warnings:
            return "warning", f"Artifact warnings: {'; '.join(warnings[:5])}"
        return "pass", "All critical artifacts fresh."

    @staticmethod
    def _recommend_action(severity: str, issues: list[str]) -> str:
        if severity == "fail":
            return f"Check missing/stale artifacts: {'; '.join(issues[:3])}"
        if severity == "warning":
            return "Non-critical artifacts missing/stale. Monitor next cycle."
        return ""

    @staticmethod
    def _is_bounded_postclose_running(
        artifact: dict[str, Any], artifact_path: Path, today: str, now: datetime
    ) -> bool:
        # Only the postclose owner can be pending here, never a failed status,
        # a prior-day recovery, a generic live process, or an unbounded wait.
        if (
            artifact.get("id") != "threshold_postclose_status"
            or artifact.get("running_status_deadline") != (23, 20)
            or today != now.date().isoformat()
            or (now.hour, now.minute) >= (23, 20)
        ):
            return False
        try:
            payload = json.loads(artifact_path.read_text(encoding="utf-8"))
            if (
                not isinstance(payload, dict)
                or type(payload.get("schema_version")) is not int
                or payload.get("schema_version") != 1
                or payload.get("report_type") != "threshold_cycle_postclose_status"
                or payload.get("runtime_effect") is not False
                or payload.get("status") != "running"
                or payload.get("target_date") != today
                or payload.get("reason") != "started"
                or type(payload.get("exit_code")) is not int
                or payload["exit_code"] != 0
            ):
                return False
            started = datetime.fromisoformat(payload["started_at"])
            if (
                started.date().isoformat() != today
                or started.timestamp() > now.timestamp()
            ):
                return False
        except (OSError, ValueError, TypeError, KeyError):
            return False
        config = artifact.get("suppress_missing_while_cron_in_progress")
        if not isinstance(config, dict) or not config.get("log"):
            return False
        # A live PID alone must not hide a newer FAIL/DONE or another date.
        markers = CronCompletionDetector._read_once_markers(
            PROJECT_ROOT / config["log"], today
        )
        if not (
            ("[START]" in markers.upper() or "[BEGIN]" in markers.upper())
            and CronCompletionDetector._last_terminal_marker(markers) == "none"
        ):
            return False
        return ArtifactFreshnessDetector._has_matching_live_process(
            config, target_date=today
        )

    @staticmethod
    def _is_upstream_cron_in_progress(config: Any, today: str) -> bool:
        if not isinstance(config, dict):
            return False
        if ArtifactFreshnessDetector._has_matching_live_process(config):
            return True
        log_value = str(config.get("log") or "").strip()
        if not log_value:
            return False
        log_path = PROJECT_ROOT / log_value
        if not log_path.exists():
            return False
        # Reuse the cron owner's exact-date, latest-run and rotated-log
        # contract. Verbose JSON must not evict START; prior-day recovery DONE
        # or an older failed attempt must not terminate the current run.
        markers = CronCompletionDetector._read_once_markers(log_path, today)
        has_start = "[START]" in markers.upper() or "[BEGIN]" in markers.upper()
        return (
            has_start
            and CronCompletionDetector._last_terminal_marker(markers) == "none"
        )

    @staticmethod
    def _has_matching_live_process(
        config: dict[str, Any], *, target_date: str | None = None
    ) -> bool:
        patterns_raw = config.get("process_patterns")
        if not isinstance(patterns_raw, list):
            return False
        patterns = [
            str(pattern).strip() for pattern in patterns_raw if str(pattern).strip()
        ]
        if not patterns:
            return False
        proc_root = Path("/proc")
        try:
            proc_entries = list(proc_root.iterdir())
        except OSError:
            return False
        current_pid = os.getpid()
        for entry in proc_entries:
            if not entry.name.isdigit():
                continue
            try:
                pid = int(entry.name)
            except ValueError:
                continue
            if pid == current_pid:
                continue
            try:
                raw_cmdline = (entry / "cmdline").read_bytes()
            except OSError:
                continue
            if target_date is not None:
                argv = raw_cmdline.decode("utf-8", errors="replace").split("\x00")
                for index, arg in enumerate(argv[:-1]):
                    name = Path(arg).name
                    is_wrapper = name == "run_threshold_cycle_postclose.sh" or (
                        name.startswith(".run_threshold_cycle_postclose.snapshot.")
                        and name.endswith(".sh")
                    )
                    if is_wrapper and argv[index + 1] == target_date:
                        return True
                continue
            cmdline = raw_cmdline.replace(b"\x00", b" ").decode(
                "utf-8", errors="replace"
            )
            if cmdline and any(pattern in cmdline for pattern in patterns):
                return True
        return False

    @staticmethod
    def _validate_partitioned_compact(
        artifact: dict[str, Any],
        today: str,
        details: dict[str, Any],
    ) -> tuple[str, str] | None:
        config = artifact.get("partitioned_compact")
        if not isinstance(config, dict):
            return None

        aid = str(artifact["id"])
        checkpoint_template = str(config.get("checkpoint_template") or "").strip()
        partition_glob_template = str(
            config.get("partition_glob_template") or ""
        ).strip()
        if not checkpoint_template or not partition_glob_template:
            return "warning", f"{aid}: partitioned compact detector config incomplete"

        checkpoint_path = PROJECT_ROOT / checkpoint_template.replace("{date}", today)
        partition_glob = partition_glob_template.replace("{date}", today)
        if Path(partition_glob).is_absolute():
            partition_paths = sorted(Path(path) for path in glob.glob(partition_glob))
        else:
            partition_paths = sorted(PROJECT_ROOT.glob(partition_glob))
        partition_paths = [
            path
            for path in partition_paths
            if path.name.endswith((".jsonl", ".jsonl.gz"))
        ]

        details[f"{aid}_legacy_path_missing"] = True
        details[f"{aid}_partitioned_checkpoint_path"] = str(checkpoint_path)
        details[f"{aid}_partitioned_part_count"] = len(partition_paths)

        if not checkpoint_path.exists():
            return "warning", f"{aid}: partitioned checkpoint missing"
        if not partition_paths:
            return "warning", f"{aid}: partitioned compact parts missing"

        try:
            checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        except Exception as exc:
            details[f"{aid}_partitioned_checkpoint_status"] = "invalid_json"
            return "warning", f"{aid}: invalid partitioned checkpoint ({exc})"

        completed = bool(checkpoint.get("completed"))
        status = str(checkpoint.get("status") or checkpoint.get("state") or "").strip()
        paused_reason = checkpoint.get("paused_reason")
        written_count = checkpoint.get("written_count", checkpoint.get("written_total"))

        details[f"{aid}_partitioned_checkpoint_status"] = status or "unknown"
        details[f"{aid}_partitioned_completed"] = completed
        details[f"{aid}_partitioned_written_count"] = written_count
        if paused_reason:
            details[f"{aid}_partitioned_paused_reason"] = paused_reason

        if not completed:
            reason = f" paused_reason={paused_reason}" if paused_reason else ""
            return (
                "warning",
                f"{aid}: partitioned compact checkpoint incomplete{reason}",
            )

        latest_mtime = max(path.stat().st_mtime for path in partition_paths)
        details[f"{aid}_age_sec"] = round(time.time() - latest_mtime, 1)
        return "pass_partitioned_checkpoint", ""

    @staticmethod
    def _validate_json_status(
        artifact: dict[str, Any],
        artifact_path: Path,
        details: dict[str, Any],
    ) -> str:
        status_field = artifact.get("json_status_field")
        if not status_field:
            return ""

        aid = artifact["id"]
        ok_values = {str(v) for v in artifact.get("json_ok_values", [])}
        try:
            payload = json.loads(artifact_path.read_text(encoding="utf-8"))
        except Exception as exc:
            details[f"{aid}_content_status"] = "invalid_json"
            return f"{aid}: invalid status JSON ({exc})"

        current: Any = payload
        for part in str(status_field).split("."):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                details[f"{aid}_content_status"] = "missing_status_field"
                return f"{aid}: missing JSON status field {status_field}"

        status_value = str(current)
        details[f"{aid}_content_status"] = status_value
        if (
            aid == "update_kospi_status"
            and status_value == "completed_with_warnings"
            and _reconcile_update_kospi_master_difference(payload, details)
        ):
            return ""
        if ok_values and status_value not in ok_values:
            return f"{aid}: JSON status is {status_value}"
        return ""

    @staticmethod
    def _validate_json_artifact(artifact_path: Path) -> str:
        if artifact_path.suffix != ".json":
            return ""
        try:
            json.loads(artifact_path.read_text(encoding="utf-8"))
        except Exception as exc:
            return str(exc)
        return ""

    @staticmethod
    def _validate_content_freshness(
        artifact: dict[str, Any],
        artifact_path: Path,
        details: dict[str, Any],
        now_dt: datetime,
    ) -> tuple[str, bool]:
        config = artifact.get("content_freshness")
        if not isinstance(config, dict):
            return "", False

        aid = artifact["id"]
        data_format = str(config.get("format") or "").strip().lower()
        try:
            payload = ArtifactFreshnessDetector._load_content_payload(
                data_format, artifact_path
            )
        except Exception as exc:
            details[f"{aid}_content_status"] = "invalid_content"
            return f"{aid}: invalid content freshness payload ({exc})", False

        min_rows = config.get("min_rows")
        if (
            min_rows is not None
            and isinstance(payload, list)
            and len(payload) < int(min_rows)
        ):
            details[f"{aid}_content_status"] = "insufficient_rows"
            details[f"{aid}_content_rows"] = len(payload)
            return f"{aid}: insufficient rows ({len(payload)} < {int(min_rows)})", False
        if isinstance(payload, list):
            details[f"{aid}_content_rows"] = len(payload)

        min_count_field = str(config.get("min_count_field") or "").strip()
        if min_count_field:
            count_value = ArtifactFreshnessDetector._resolve_field(
                payload, min_count_field
            )
            try:
                count_int = int(count_value)
            except (TypeError, ValueError):
                details[f"{aid}_content_status"] = "invalid_count"
                return f"{aid}: invalid count field {min_count_field}", False
            details[f"{aid}_{min_count_field}"] = count_int
            min_count = int(config.get("min_count") or 0)
            if count_int < min_count:
                details[f"{aid}_content_status"] = "insufficient_count"
                return (
                    f"{aid}: insufficient {min_count_field} ({count_int} < {min_count})",
                    False,
                )

        date_field = str(config.get("date_field") or "").strip()
        if not date_field:
            details[f"{aid}_content_status"] = "pass"
            return "", True
        raw_date = ArtifactFreshnessDetector._resolve_field(payload, date_field)
        content_date = ArtifactFreshnessDetector._parse_date_value(raw_date)
        if content_date is None:
            details[f"{aid}_content_status"] = "invalid_date"
            return f"{aid}: invalid content date field {date_field}", False

        age_days = (now_dt.date() - content_date.date()).days
        max_age_days = int(config.get("max_age_days") or 0)
        details[f"{aid}_content_date"] = content_date.date().isoformat()
        details[f"{aid}_content_age_days"] = age_days
        if age_days < 0:
            details[f"{aid}_content_status"] = "future_date"
            return (
                f"{aid}: content date is in the future ({content_date.date().isoformat()})",
                False,
            )
        if max_age_days >= 0 and age_days > max_age_days:
            details[f"{aid}_content_status"] = "stale_date"
            return f"{aid}: content date stale ({age_days}d > {max_age_days}d)", False

        details[f"{aid}_content_status"] = "pass"
        return "", True

    @staticmethod
    def _load_content_payload(data_format: str, artifact_path: Path) -> Any:
        if data_format == "json":
            return json.loads(artifact_path.read_text(encoding="utf-8"))
        if data_format == "csv":
            with artifact_path.open("r", encoding="utf-8-sig", newline="") as handle:
                return list(csv.DictReader(handle))
        raise ValueError(f"unsupported content freshness format: {data_format}")

    @staticmethod
    def _resolve_field(payload: Any, field_path: str) -> Any:
        current = payload[0] if isinstance(payload, list) and payload else payload
        for part in field_path.split("."):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current

    @staticmethod
    def _parse_date_value(value: Any) -> datetime | None:
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            return None
        if " " in text and "T" not in text:
            text = text.split(" ", 1)[0]
        if text.endswith("Z"):
            text = f"{text[:-1]}+00:00"
        try:
            return datetime.fromisoformat(text)
        except ValueError:
            pass
        for fmt in ("%Y%m%d", "%Y/%m/%d"):
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                continue
        return None


def _kst_time_tuple(now_kst: datetime | None = None) -> tuple[int, int]:
    now_kst = now_kst or datetime.now()
    return now_kst.hour, now_kst.minute
