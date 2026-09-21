"""Verify the direct family postclose chain after common Daily/EV retirement."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.utils.constants import DATA_DIR

REPORT_DIR = DATA_DIR / "report"
OUTPUT_DIR = REPORT_DIR / "threshold_cycle_postclose_verification"
EXPLICIT_DISABLED_STAGE_ALLOWLIST = frozenset({
    "swing_lifecycle", "swing_strategy_discovery", "swing_lifecycle_matrix",
    "swing_lifecycle_bucket_discovery", "deepseek_swing_lab",
})


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def _sha(path: Path) -> str | None:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None


def _artifact_paths(target_date: str) -> dict[str, Path]:
    return {
        "runtime_summary": REPORT_DIR / "runtime_approval_summary" / f"runtime_approval_summary_{target_date}.json",
        "postclose_status": REPORT_DIR / "threshold_cycle_postclose_status" / f"threshold_cycle_postclose_{target_date}.status.json",
        "scanner_lookup_attention_selection": DATA_DIR / "threshold_cycle" / "scanner_lookup_attention_preopen" / f"scanner_lookup_attention_preopen_{target_date}.json",
        "scanner_lookup_attention_policy": DATA_DIR / "threshold_cycle" / "scanner_lookup_attention_policy" / f"scanner_lookup_attention_policy_{target_date}.json",
    }


def _direct_source_checks(summary: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    checks: list[dict[str, Any]] = []
    issues: list[str] = []
    sources = summary.get("sources") if isinstance(summary.get("sources"), dict) else {}
    for owner, source in sources.items():
        if not isinstance(source, dict):
            issues.append(f"direct_source_invalid:{owner}")
            continue
        check = {
            "owner": owner,
            "path": source.get("path"),
            "exists": source.get("exists") is True,
            "target_date_matches": source.get("target_date_matches") is True,
            "sha256": source.get("sha256"),
            "status": source.get("status"),
            "error": source.get("error"),
            "applicability": source.get("applicability"),
            "economic_evidence": source.get("economic_evidence"),
            "required": source.get("required") is True,
            "current_sha256": _sha(Path(str(source.get("path") or ""))),
        }
        checks.append(check)
        evidence = check["economic_evidence"] if isinstance(check["economic_evidence"], dict) else {}
        comparison_status = evidence.get("comparison_status")
        if comparison_status in {"source_gap", "unsupported_scope", "mixed"} and evidence.get("policy_apply_allowed") is True:
            issues.append(f"blocked_economic_source_marked_applyable:{owner}")
        if comparison_status == "validated_edge":
            policy_receipt = source.get("policy_receipt") if isinstance(source.get("policy_receipt"), dict) else {}
            if evidence.get("policy_handoff_state") != "candidate_published" or policy_receipt.get("valid") is not True:
                issues.append(f"validated_edge_policy_handoff_missing:{owner}")
        if check["required"] and check["error"]:
            issues.append(f"direct_source_contract_error:{owner}:{check['error']}")
        elif check["exists"] and check["current_sha256"] != check["sha256"]:
            issues.append(f"direct_source_hash_mismatch:{owner}")
        elif not check["exists"] and check["required"]:
            issues.append(f"direct_source_missing:{owner}")
        elif check["required"] and check["exists"] and not check["target_date_matches"]:
            issues.append(f"direct_source_date_mismatch:{owner}")
        elif check["required"] and check["exists"] and not check["sha256"]:
            issues.append(f"direct_source_hash_missing:{owner}")
    return checks, issues


def _direct_checklist_checks(
    target_date: str, summary: dict[str, Any], summary_path: Path
) -> tuple[dict[str, Any], list[str]]:
    from src.engine.automation.postclose_summary_handoff import verify_summary_handoff
    from src.engine.build_next_stage2_checklist import (
        _next_krx_trading_day,
        _project_direct_tasks,
        _render_task,
        stage2_checklist_path,
    )

    preopen = (
        summary.get("preopen_consumption_receipt")
        if isinstance(summary.get("preopen_consumption_receipt"), dict)
        else {}
    )
    apply_date = str(preopen.get("apply_date") or _next_krx_trading_day(target_date))
    checklist_path = stage2_checklist_path(apply_date)
    handoff = verify_summary_handoff(
        target_date,
        report_dir=REPORT_DIR,
        checklist_path=checklist_path,
        require_tower=False,
        require_checklist=True,
    )
    issues = list(handoff.get("issues") or [])
    summary_sha256 = _sha(summary_path) or "missing"
    expected_tasks, _ = _project_direct_tasks(
        summary=summary,
        source_date=target_date,
        target_date=apply_date,
        summary_path=summary_path,
        summary_sha256=summary_sha256,
    )
    expected_ids = sorted(task.task_id for task in expected_tasks)
    try:
        checklist_text = checklist_path.read_text(encoding="utf-8")
    except OSError:
        checklist_text = ""
    actual_ids = sorted(
        match.group(1)
        for match in re.finditer(
            r"^- \[[ xX]\] `\[(DirectFamily[A-Za-z0-9_:-]+)\]",
            checklist_text,
            re.MULTILINE,
        )
    )
    if actual_ids != expected_ids:
        issues.append("direct_checklist_task_projection_mismatch")
    normalized = checklist_text.replace("- [x]", "- [ ]").replace("- [X]", "- [ ]")
    if any(_render_task(task, apply_date)[0] not in normalized for task in expected_tasks):
        issues.append("direct_checklist_schedule_contract_mismatch")
    return {
        "status": "pass" if not issues else "fail",
        "path": str(checklist_path),
        "apply_date": apply_date,
        "expected_task_ids": expected_ids,
        "actual_task_ids": actual_ids,
        "handoff": handoff,
    }, issues


def _terminal_issues(target_date: str, terminal: dict, *, seal: bool = False,
                     expected_run_id: str | None = None) -> list[str]:
    issues = []
    expected_status = "producers_completed" if seal else "succeeded"
    if terminal.get("status") != expected_status:
        issues.append("postclose_terminal_status_missing")
    if terminal.get("target_date") != target_date:
        issues.append("postclose_terminal_date_mismatch")
    if type(terminal.get("exit_code")) is not int or terminal["exit_code"] != 0:
        issues.append("postclose_terminal_exit_code_invalid")
    if not terminal.get("run_id") or (expected_run_id and terminal.get("run_id") != expected_run_id):
        issues.append("postclose_terminal_run_mismatch")
    if not re.fullmatch(r"[0-9a-f]{40}", str(terminal.get("code_commit") or "")):
        issues.append("postclose_terminal_code_missing")
    if not terminal.get("started_at") or not terminal.get("finished_at"):
        issues.append("postclose_terminal_clock_missing")
    try:
        started = datetime.fromisoformat(terminal.get("started_at") or "")
        finished = datetime.fromisoformat(terminal.get("finished_at") or "")
        if started.tzinfo is None or finished.tzinfo is None or finished < started:
            raise ValueError("invalid terminal clock")
    except (ValueError, TypeError):
        issues.append("postclose_terminal_clock_invalid")
    if not seal:
        receipt = terminal.get("verification_receipt") or {}
        path = Path(str(receipt.get("path") or ""))
        proof = _load(path)
        if (not receipt.get("sha256") or _sha(path) != receipt.get("sha256")
            or proof.get("status") != "pass"
            or proof.get("verification_scope") != "main_precommit"
            or proof.get("date") != target_date
            or proof.get("run_id") != terminal.get("run_id")
            or proof.get("code_commit") != terminal.get("code_commit")):
            issues.append("postclose_terminal_verification_binding_invalid")
    return issues


def _effective_date(target_date: str, explicit: str | None = None) -> str | None:
    if explicit:
        date.fromisoformat(explicit)
        return explicit
    summary = _load(_artifact_paths(target_date)["runtime_summary"])
    return (summary.get("preopen_consumption_receipt") or {}).get("apply_date")


def build_threshold_cycle_postclose_verification(
    target_date: str,
    *,
    require_done_marker: bool = True,
    disabled_stages: set[str] | None = None,
    require_summary_handoff: bool = False,
    allow_pending_entry_replay: bool = False,
    seal_main_run: bool = False,
    expected_run_id: str | None = None,
    effective_date: str | None = None,
) -> dict[str, Any]:
    paths = _artifact_paths(target_date)
    summary = _load(paths["runtime_summary"])
    postclose = _load(paths["postclose_status"])
    checks, issues = _direct_source_checks(summary)
    summary_contract_valid = False
    if paths["runtime_summary"].exists():
        try:
            from src.engine.build_next_stage2_checklist import _validate_direct_summary

            _validate_direct_summary(summary, target_date)
            summary_contract_valid = True
        except (OSError, RuntimeError, ValueError) as exc:
            issues.append(f"runtime_summary_contract_invalid:{exc}")
    if summary.get("date") != target_date:
        issues.append("runtime_summary_date_mismatch")
    if summary.get("status") != "direct_evidence_complete":
        issues.append("runtime_summary_incomplete")
    if summary.get("direct_evidence_state") != "complete":
        issues.append("runtime_summary_direct_evidence_state_incomplete")
    if summary.get("runtime_effect") is not False:
        issues.append("runtime_summary_authority_invalid")
    if summary.get("allowed_runtime_apply") is not False:
        issues.append("runtime_summary_apply_authority_invalid")
    if summary.get("daily_threshold_cycle_retired") is not True:
        issues.append("daily_retirement_contract_missing")
    if summary.get("threshold_cycle_ev_retired") is not True:
        issues.append("ev_retirement_contract_missing")
    if require_done_marker or seal_main_run:
        issues.extend(_terminal_issues(target_date, postclose, seal=seal_main_run,
                                      expected_run_id=expected_run_id))
    for stage in sorted((disabled_stages or set()) - EXPLICIT_DISABLED_STAGE_ALLOWLIST):
        issues.append(f"disabled_stage_not_allowed:{stage}")
    if effective_date and (summary.get("preopen_consumption_receipt") or {}).get("apply_date") != effective_date:
        issues.append("runtime_summary_effective_date_mismatch")
    if require_summary_handoff and not paths["runtime_summary"].exists():
        issues.append("summary_handoff_missing")
    checklist_handoff: dict[str, Any] = {
        "status": "not_required",
        "path": None,
        "expected_task_ids": [],
        "actual_task_ids": [],
    }
    if (
        require_summary_handoff
        and paths["runtime_summary"].exists()
        and summary_contract_valid
    ):
        checklist_handoff, checklist_issues = _direct_checklist_checks(
            target_date, summary, paths["runtime_summary"]
        )
        issues.extend(checklist_issues)
    elif require_summary_handoff and paths["runtime_summary"].exists():
        checklist_handoff["status"] = "blocked_invalid_summary"
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 3,
        "report_type": "threshold_cycle_postclose_verification",
        "verification_scope": "main_precommit" if seal_main_run else ("main_terminal" if require_done_marker else "preterminal"),
        "whole_native_chain_done_claimed": False,
        "run_id": postclose.get("run_id"),
        "code_commit": postclose.get("code_commit"),
        "completion_state": "failed" if issues else ("preterminal_verified" if not require_done_marker else "main_verified"),
        "date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": status,
        "issues": issues,
        "failure_summary": {"issue_count": len(issues), "issues": issues},
        "direct_source_checks": checks,
        "summary_handoff": {
            "status": "pass" if paths["runtime_summary"].exists() else "missing",
            "path": str(paths["runtime_summary"]),
            "sha256": _sha(paths["runtime_summary"]),
            "recommendation_intake": "family_owned_direct_only",
        },
        "checklist_handoff": checklist_handoff,
        "retired_common_layers": [
            "daily_threshold_cycle_report", "threshold_cycle_ev_report", "threshold_cycle_preopen_apply"
        ],
        "disabled_stages": sorted(disabled_stages or set()),
        "allow_pending_entry_replay": allow_pending_entry_replay,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }


def _render(report: dict[str, Any]) -> str:
    lines = [
        f"# Direct postclose verification - {report['date']}", "",
        f"- status: `{report['status']}`",
        "- common Daily/EV/PREOPEN selector: `retired`",
        f"- issue_count: `{len(report['issues'])}`", "", "## Direct sources",
    ]
    lines.extend(
        f"- `{row['owner']}`: exists=`{row['exists']}` date_match=`{row['target_date_matches']}`"
        for row in report["direct_source_checks"]
    )
    if report["issues"]:
        lines.extend(["", "## Issues", *[f"- `{issue}`" for issue in report["issues"]]])
    return "\n".join(lines) + "\n"


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _write_verification_receipts(
    target_date: str, report: dict[str, Any], *, invocation: dict[str, Any]
) -> tuple[dict[str, Any], Path, Path, Path]:
    json_path = OUTPUT_DIR / f"threshold_cycle_postclose_verification_{target_date}.json"
    md_path = OUTPUT_DIR / f"threshold_cycle_postclose_verification_{target_date}.md"
    attempt_path = OUTPUT_DIR / "attempts" / target_date / f"{uuid.uuid4().hex}.json"
    report = dict(report)
    report["verification_attempt"] = {
        "immutable": True,
        "path": str(attempt_path.resolve()),
        "invocation": invocation,
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    if report.get("status") == "fail":
        report["first_failure_receipt"] = {
            "issues": list(report.get("issues") or []),
            "created_at": report["verification_attempt"]["created_at"],
        }
    body = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    attempt_path.parent.mkdir(parents=True, exist_ok=True)
    with attempt_path.open("x", encoding="utf-8") as handle:
        handle.write(body)
        handle.flush()
        os.fsync(handle.fileno())
    _atomic_write(json_path, body)
    _atomic_write(md_path, _render(report))
    return report, json_path, md_path, attempt_path


def _scanner_scope(target_date: str) -> dict[str, Any]:
    paths = _artifact_paths(target_date)
    issues = [name for name in ("scanner_lookup_attention_selection", "scanner_lookup_attention_policy") if not paths[name].exists()]
    return {"status": "pass" if not issues else "fail", "scope": "scanner_lookup_attention_only", "issues": issues, "whole_native_chain_done_claimed": False}


def _main_mechanistic_scope(target_date: str, effective_date: str | None = None, publication_date: str | None = None) -> dict[str, Any]:
    from src.engine.scalping import ai_action_outcome_calibration as calibration
    from src.engine.scalping import mechanistic_entry_runtime_policy as policy

    source_path = (
        REPORT_DIR
        / "ai_decision_action_outcome_calibration"
        / f"ai_decision_action_outcome_calibration_{target_date}.json"
    )
    source = _load(source_path)
    issues: list[str] = []
    if not calibration._artifact_content_sha256_valid(source):
        issues.append("main_machine_report_hash_invalid")
    if source.get("report_scope") != "main_mechanistic_entry":
        issues.append("main_machine_report_scope_invalid")
    if source.get("noncompact_sections_refreshed") is not True:
        issues.append("main_machine_noncompact_refresh_missing")
    terminal = source.get("machine_full_evaluation") or {}
    refinement = source.get("mechanistic_entry_refinement") or {}
    source_contract = refinement.get("source_contract") or {}
    hierarchy = source.get("hierarchical_entry_quality") or {}
    if (
        refinement.get("schema") != calibration.MECHANISTIC_REFINEMENT_SCHEMA
        or refinement.get("target_date") != target_date
        or source_contract.get("schema")
        != "machine_common_refinement_population_v1"
        or terminal.get("full_population_count") != source_contract.get(
            "structure_contract_population_count", source_contract.get("accepted_unique_trace_count"))
        or ("structure_contract_population_count" in source_contract and (
            terminal.get("current_structure_eligible_count") != source_contract.get("accepted_unique_trace_count")
            or type(source_contract.get("accepted_unique_trace_count")) is not int
            or type(source_contract.get("structure_contract_population_count")) is not int
            or not 0 <= source_contract["accepted_unique_trace_count"] <= source_contract["structure_contract_population_count"]
            or source_contract["structure_contract_population_count"] - source_contract["accepted_unique_trace_count"]
                != (source_contract.get("row_exclusion_reason_counts") or {}).get("structure_contract_version_mismatch", 0)
        ))
    ):
        issues.append("main_machine_refinement_contract_invalid")
    if (
        not isinstance(hierarchy.get("runtime_extensions_by_scope"), dict)
        or not isinstance(hierarchy.get("machine_decision_case_table"), dict)
    ):
        issues.append("main_machine_hierarchy_or_case_table_missing")
    if terminal.get("state") not in {
        "source_gap",
        "insufficient_mature_sample",
        "evaluated_no_edge",
        "validated_edge",
    }:
        issues.append("main_machine_terminal_state_invalid")
    matching: list[tuple[Path, dict[str, Any]]] = []
    for candidate in sorted(
        (DATA_DIR / "runtime/mechanistic_entry_policy").glob("policy_????-??-??.json")
    ):
        bundle = _load(candidate)
        machine_source = bundle.get("machine_evaluation_source") or {}
        if (machine_source.get("source_date") == target_date
            and (not effective_date or bundle.get("target_date") == effective_date)
            and (not publication_date or bundle.get("publication_date") == publication_date)):
            matching.append((candidate, bundle))
    if len(matching) != 1:
        issues.append("main_machine_future_policy_missing_or_ambiguous")
    else:
        _, bundle = matching[-1]
        machine_source = bundle.get("machine_evaluation_source") or {}
        try:
            loaded = policy.load(
                data_root=DATA_DIR,
                target_date=str(bundle.get("target_date") or ""),
            )
            if not loaded or loaded.get("bundle_sha256") != bundle.get(
                "bundle_sha256"
            ):
                raise ValueError("main_machine_loaded_bundle_mismatch")
        except (OSError, ValueError):
            issues.append("main_machine_future_policy_invalid")
        if (
            machine_source.get("report_scope") != "main_mechanistic_entry"
            or machine_source.get("noncompact_sections_refreshed") is not True
        ):
            issues.append("main_machine_policy_source_scope_invalid")
        if machine_source.get("artifact_content_sha256") != source.get(
            "artifact_content_sha256"
        ):
            issues.append("main_machine_report_policy_hash_mismatch")
        if machine_source.get("terminal_state") != terminal.get("state"):
            issues.append("main_machine_terminal_disposition_mismatch")
        expected = (
            "evidence_qualified_threshold_update"
            if terminal.get("state") == "validated_edge"
            else None
        )
        if expected and bundle.get("machine_disposition") != expected:
            issues.append("main_machine_validated_edge_not_published")
        if (
            terminal.get("state") != "validated_edge"
            and bundle.get("machine_disposition")
            == "evidence_qualified_threshold_update"
        ):
            issues.append("main_machine_unqualified_edge_published")
    try:
        current_strategy = policy.current_strategy_receipt(data_root=DATA_DIR)
        from src.engine.scalping.entry_strategy_policy import select_report_candidate
        selected_strategy = select_report_candidate(source)
        if selected_strategy and selected_strategy[1].get('promotion_pass') is True:
            if (current_strategy.get('activation') or {}).get('candidate_sha256') != policy.digest(selected_strategy[1]['candidate']):
                issues.append('main_machine_qualified_strategy_not_current')
    except (OSError, ValueError, TypeError, KeyError) as exc:
        current_strategy = dict(status='active_generation_invalid', reason=str(exc))
        issues.append('main_machine_current_strategy_invalid')
    return {
        'current_strategy_generation': current_strategy,
        "status": "pass" if not issues else "fail",
        "scope": "main_mechanistic_entry_only",
        "issues": issues,
        "source_path": str(source_path),
        "whole_native_chain_done_claimed": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument("--effective-date")
    parser.add_argument("--publication-date")
    parser.add_argument("--seal-main-run", action="store_true")
    parser.add_argument("--expected-run-id")
    parser.add_argument("--require-summary-handoff", action="store_true")
    parser.add_argument("--scanner-lookup-summary-only", action="store_true")
    parser.add_argument("--compact-summary-only", action="store_true")
    parser.add_argument("--main-mechanistic-summary-only", action="store_true")
    parser.add_argument("--entry-cancel-wait-summary-only", action="store_true")
    parser.add_argument("--allow-pending-done-marker", action="store_true")
    parser.add_argument("--allow-pending-entry-replay", action="store_true")
    parser.add_argument("--disabled-stage", action="append", default=[])
    args = parser.parse_args(argv)
    if args.seal_main_run and (not args.expected_run_id or args.allow_pending_done_marker
        or not args.require_summary_handoff):
        parser.error("seal requires expected run identity and strict summary handoff")
    if args.scanner_lookup_summary_only:
        report = _scanner_scope(args.date)
        print(json.dumps(report, ensure_ascii=False))
        return 0 if report["status"] == "pass" else 2
    if args.entry_cancel_wait_summary_only:
        from src.engine.automation.entry_cancel_wait_tuning import verify_handoff
        report = verify_handoff(args.date)
        print(json.dumps(report, ensure_ascii=False))
        return 0 if report.get("status") == "PASS" else 2
    if args.compact_summary_only or args.main_mechanistic_summary_only:
        effective = _effective_date(args.date, args.effective_date)
        if args.compact_summary_only:
            from src.engine.scalping.main_ai_prompt_consumer import verify_compact_handoff
            report = verify_compact_handoff(DATA_DIR, args.date, effective_date=effective,
                                            publication_date=args.publication_date)
        else:
            report = _main_mechanistic_scope(args.date, effective, args.publication_date)
        if args.require_summary_handoff:
            handoff = build_threshold_cycle_postclose_verification(
                args.date, require_done_marker=False, require_summary_handoff=True,
                effective_date=effective)
            report["issues"].extend(handoff["issues"])
            report["summary_handoff"] = handoff["checklist_handoff"]
        report.update(status="fail" if report["issues"] else "pass", date=args.date,
                      direct_source_checks=[], effective_date=effective,
                      failure_summary={"issues": report["issues"]})
        original_output = globals()["OUTPUT_DIR"]
        try:
            globals()["OUTPUT_DIR"] = original_output / "scoped" / report["scope"]
            report, *_ = _write_verification_receipts(args.date, report, invocation=vars(args))
        finally:
            globals()["OUTPUT_DIR"] = original_output
        print(json.dumps(report, ensure_ascii=False))
        return 0 if report["status"] == "pass" else 2
    report = build_threshold_cycle_postclose_verification(
        args.date,
        require_done_marker=not args.allow_pending_done_marker,
        disabled_stages=set(args.disabled_stage),
        require_summary_handoff=args.require_summary_handoff,
        allow_pending_entry_replay=args.allow_pending_entry_replay,
        seal_main_run=args.seal_main_run,
        expected_run_id=args.expected_run_id,
        effective_date=args.effective_date,
    )
    report, json_path, md_path, attempt_path = _write_verification_receipts(
        args.date, report,
        invocation={
            "require_done_marker": not args.allow_pending_done_marker,
            "require_summary_handoff": args.require_summary_handoff,
            "disabled_stages": sorted(set(args.disabled_stage)),
        },
    )
    if args.seal_main_run and report["status"] == "pass":
        status_path = _artifact_paths(args.date)["postclose_status"]
        terminal = _load(status_path)
        if _terminal_issues(args.date, terminal, seal=True, expected_run_id=report["run_id"]):
            raise RuntimeError("postclose_terminal_changed_during_seal")
        terminal.update(status="succeeded", reason="verified_main_completed",
                        verification_receipt={"path": str(attempt_path.resolve()), "sha256": _sha(attempt_path)})
        _atomic_write(status_path, json.dumps(terminal, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "json": str(json_path), "md": str(md_path), "attempt_json": str(attempt_path), "failure_summary": report["failure_summary"]}, ensure_ascii=False))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
