from __future__ import annotations


import csv
import gzip
import glob
import hashlib
import json
import math
import os
import time
from collections import Counter
from datetime import date, datetime
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


def _machine_result_semantics(root: Path, source_date: str) -> dict[str, Any]:
    """Check exact-date machine economics separately from stage completion."""
    report_path = (root / "data/report/ai_decision_action_outcome_calibration"
                   / f"ai_decision_action_outcome_calibration_{source_date}.json")
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
        report = json.loads(report_path.read_text(encoding="utf-8"))
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
        return {"status": "source_invalid", "findings": [str(exc)]}
    findings: list[str] = []
    scope_details: dict[str, dict[str, Any]] = {}
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
            "operating_paired": paired, "source_contract_invalid": invalid}
        if invalid:
            findings.append("machine_source_contract_exclusions")
        if full and not eligible:
            findings.append("machine_current_structure_empty")
        if eligible and not paired:
            findings.append("machine_operating_paired_unbound")
        if eligible and row.get("downstream_operating_evidence_complete") is not True:
            findings.append("machine_operating_economics_incomplete")
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
        except (OSError, EOFError, UnicodeError, ValueError, TypeError, AttributeError):
            findings.append("compact_projection_invalid")
    winrate_path = (root / 'data/report/ai_decision_action_outcome_calibration'
                    / f'winrate_policy_{source_date}.json')
    if winrate_path.exists() or winrate_path.is_symlink():
        try:
            if winrate_path.is_symlink() or winrate_path.stat().st_size > 64 * 1024 * 1024:
                raise ValueError('winrate_report_untrusted_path_or_size')
            from src.engine.scalping import ai_action_outcome_calibration as calibration
            from src.engine.scalping import mechanistic_entry_runtime_policy as runtime_policy
            winrate = json.loads(winrate_path.read_text(encoding='utf-8'))
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
                if (disposition == 'successor_selected'
                    and not runtime_policy._winrate_successor_hurdles_valid(winrate)):
                    findings.append('winrate_successor_hurdle_invalid')
                if disposition in {'initial_adopted', 'successor_selected'}:
                    for part in ('train', 'holdout'):
                        metrics = (winrate.get('candidate') or {}).get(part) or {}
                        if (not metrics.get('selected_opportunity_count')
                            or metrics.get('win_rate_pct') is None
                            or metrics.get('support_adjusted_win_rate_pct') is None):
                            findings.append('winrate_selected_zero_or_undefined')
                terminal_path = winrate_path.with_name(f'winrate_policy_terminal_{source_date}.json')
                terminal = json.loads(terminal_path.read_text(encoding='utf-8'))
                target = (terminal.get('staged') or {}).get('target_date')
                if (not calibration._artifact_content_sha256_valid(terminal)
                    or terminal.get('report_sha256') != winrate.get('artifact_content_sha256')
                    or not isinstance(target, str)):
                    raise ValueError('winrate_terminal_binding_invalid')
                bundle = runtime_policy.load(data_root=root / 'data', target_date=target)
                selection = (bundle or {}).get('winrate_selection') or {}
                pending = (terminal.get('staged') or {}).get('status') == 'pending_initial_preserved'
                if (pending and (winrate.get('pending_initial_bundle_sha256') != bundle['bundle_sha256']
                    or winrate.get('pending_initial_target_date') != target
                    or winrate.get('hurdle_errors') != ['initial_policy_pending_activation']
                    or disposition != 'incumbent_carried'
                    or selection.get('disposition') != 'initial_adopted'
                    or selection.get('parent_bundle_sha256') != winrate.get('parent_bundle_sha256')
                    or bundle.get('previous_bundle_sha256') != winrate.get('parent_bundle_sha256'))
                    or not pending and (selection.get('report_sha256') != winrate.get('artifact_content_sha256')
                    or selection.get('disposition') != disposition)
                    or selection.get('machine_policy_sha256') != runtime_policy.digest(bundle['machine_policy'])
                    or not pending and (bundle.get('scope_policies') or {}).get('KRX|KRX_REGULAR', {}).get('machine_disposition') != disposition):
                    findings.append('winrate_candidate_bundle_or_scope_mismatch')
            else:
                findings.append('winrate_report_schema_invalid')
        except (OSError, ValueError, TypeError, KeyError, AttributeError):
            findings.append('winrate_semantic_validation_failed')
    return {"status": "warning" if findings else "pass", "findings": sorted(set(findings)),
        "scopes": scope_details, "compact_exclusions": compact_exclusions}


def _auxiliary_result_semantics(root: Path, source_date: str) -> dict[str, Any]:
    """Audit the bounded AI-stage receipt; selection is not live consumption."""
    from src.engine.scalping import compact_auxiliary_paired_replay as paired

    terminal_path = (root / "data/report/postclose_stage_terminal" / source_date
                     / "main_auxiliary_policy.json")
    terminal_source_sha = None
    if terminal_path.exists() or terminal_path.is_symlink():
        try:
            if terminal_path.is_symlink() or terminal_path.stat().st_size > 1024 * 1024:
                raise ValueError("auxiliary_terminal_untrusted_path_or_size")
            terminal = json.loads(terminal_path.read_text(encoding="utf-8"))
            receipt = terminal.get("receipt_sha256")
            body = {k: v for k, v in terminal.items() if k != "receipt_sha256"}
            digest = hashlib.sha256(json.dumps(body, ensure_ascii=True,
                sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            if (terminal.get("schema") != "postclose_stage_terminal_v2"
                or terminal.get("stage_id") != "main_auxiliary_policy"
                or terminal.get("source_date") != source_date or receipt != digest):
                raise ValueError("auxiliary_terminal_identity_or_hash_invalid")
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
            return {"status": "source_invalid", "findings": [str(exc)]}
    path = existing_or_gzip_path(
        root / "data/report/ai_entry_setup_paired_replay_batch"
        / f"compact_auxiliary_paired_economic_{source_date}.json"
    )
    if not (path.exists() or path.is_symlink()):
        if terminal_source_sha:
            return {"status": "source_invalid", "findings": ["auxiliary_completed_report_missing"]}
        return {"status": "not_assessed", "findings": []}
    try:
        if path.is_symlink() or path.stat().st_size > 64 * 1024 * 1024:
            raise ValueError("auxiliary_report_untrusted_path_or_size")
        opener = gzip.open if path.suffix == ".gz" else open
        with opener(path, "rb") as handle:
            raw = handle.read(64 * 1024 * 1024 + 1)
        if len(raw) > 64 * 1024 * 1024:
            raise ValueError("auxiliary_report_uncompressed_size_exceeded")
        if terminal_source_sha and hashlib.sha256(raw).hexdigest() != terminal_source_sha:
            raise ValueError("auxiliary_completed_report_generation_mismatch")
        report = json.loads(raw)
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
            or sum(v["eligible_count"] for v in stage["scope_results"].values())
                != len(candidate_keys)):
            raise ValueError("auxiliary_candidate_population_invalid")
    except (OSError, EOFError, UnicodeError, ValueError, TypeError, AttributeError) as exc:
        return {"status": "source_invalid", "findings": [str(exc)]}
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
            label_gap_count = counts.get("source_gap", 0)
        except (OSError, EOFError, UnicodeError, ValueError, TypeError, AttributeError) as exc:
            return {"status": "source_invalid", "findings": [str(exc)]}
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
        scopes[scope] = {"status": status, "eligible_count": value.get("eligible_count"),
                         "holdout_day": value.get("holdout_day"),
                         "paired_delta_ev_pct": selected.get("paired_delta_ev_pct"),
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
            or not value.get("holdout_day")
        ):
            findings.append("auxiliary_selected_without_independent_evidence")
    if not eligible:
        findings.append("auxiliary_economic_population_empty")
    elif not any(isinstance(value, dict) and value.get("holdout_day")
                 for value in stage["scope_results"].values()):
        findings.append("auxiliary_independent_holdout_missing")
    if any(f.endswith("invalid") or f == "auxiliary_selected_without_independent_evidence"
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
            "first_source_gap": first_gap,
            "scopes": scopes, "runtime_effect": False}


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

        if trading_day:
            holding_semantics = _holding_profit_exit_semantics(PROJECT_ROOT, today)
            details["holding_profit_exit_semantics"] = holding_semantics
            if holding_semantics["findings"]:
                warnings.append("holding_profit_exit_semantics: " + ", ".join(
                    holding_semantics["findings"]))
            machine_semantics = _machine_result_semantics(PROJECT_ROOT, today)
            details["machine_result_semantics"] = machine_semantics
            if machine_semantics["findings"]:
                warnings.append("machine_result_semantics: " + ", ".join(machine_semantics["findings"]))
            auxiliary_semantics = _auxiliary_result_semantics(PROJECT_ROOT, today)
            details["auxiliary_result_semantics"] = auxiliary_semantics
            if auxiliary_semantics["findings"]:
                warnings.append("auxiliary_result_semantics: " + ", ".join(
                    auxiliary_semantics["findings"]))
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
