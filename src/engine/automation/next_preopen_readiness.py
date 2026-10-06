"""Prepare and verify the next trading day's isolated PREOPEN bootstrap.

The prepared files are never sourced by the bot. The exact-date PREOPEN owner
still activates dated policies and writes the live bootstrap on the target day.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from src.engine.automation import runtime_policy_bootstrap as bootstrap
from src.engine.automation.postclose_done_controller import done_terminal_receipt_issues
from src.engine.infrastructure.runtime_release_router import selected_release
from src.utils.constants import DATA_DIR
from src.utils.market_day import is_krx_trading_day

KST = ZoneInfo("Asia/Seoul")
PREPARED_DIR = DATA_DIR / "runtime" / "policy_bootstrap" / "prepared"
PREOPEN_START = time(7, 35)


def _next_trading_day(day: date) -> date:
    for offset in range(1, 15):
        candidate = day + timedelta(days=offset)
        if is_krx_trading_day(candidate):
            return candidate
    raise ValueError("next_krx_trading_day_unresolved")


def target_after_postclose(source_date: str, *, now: datetime | None = None) -> str:
    source = date.fromisoformat(source_date)
    current = (now or datetime.now(KST)).astimezone(KST)
    if source > current.date():
        raise ValueError("future_postclose_source_date")
    first = _next_trading_day(source)
    if current.date() < first:
        return first.isoformat()
    # Late closure/release preparation retains today's still-unopened session,
    # even when the sealed source predates the immediately preceding day.
    if current.time() < PREOPEN_START and is_krx_trading_day(current.date()):
        return current.date().isoformat()
    return _next_trading_day(current.date()).isoformat()


def finalization_preparation_disposition(
    source_date: str, effective_date: str, *, recovery: bool = False,
    now: datetime | None = None,
) -> str:
    """A historical finalizer closes its source, never rolls it into a new day."""
    source = date.fromisoformat(source_date)
    effective = date.fromisoformat(effective_date)
    current = (now or datetime.now(KST)).astimezone(KST)
    if (source.isoformat() != source_date or effective.isoformat() != effective_date
            or source > current.date() or _next_trading_day(source) != effective):
        raise ValueError("preopen_source_session_mismatch")
    if (current.date() > effective
            or (current.date() == effective and current.time() >= PREOPEN_START)):
        if recovery:
            return "historical_recovery_no_prepare"
        raise ValueError("preopen_source_session_already_opened")
    return "prepare_exact_effective_date"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"object_required:{path}")
    return value


def _selected_release() -> tuple[dict[str, Any], Path, str]:
    path = DATA_DIR / "runtime" / "runtime_release_selection.json"
    selection = _read(path)
    release, commit = selected_release(DATA_DIR.parent)
    if release != Path.cwd().resolve() or selection.get("git_commit") != commit:
        raise ValueError("selected_release_identity_mismatch")
    return selection, path, commit


def _source_receipts(source_date: str, target_date: str, *, generation_only: bool = False) -> dict[str, Any]:
    controller_path = (DATA_DIR / "report" / "postclose_done_controller"
                       / f"postclose_done_controller_{source_date}.json")
    issues = done_terminal_receipt_issues(controller_path, source_date, started_after_ns=0,
                                        **({"generation_only": True} if generation_only else {}))
    if issues:
        raise ValueError("postclose_controller_not_closed:" + ",".join(issues))
    summary_path = (DATA_DIR / "report" / "runtime_approval_summary"
                    / f"runtime_approval_summary_{source_date}.json")
    summary = _read(summary_path)
    if summary.get("date") != source_date:
        raise ValueError("postclose_summary_date_mismatch")
    policy_receipts = []
    for family in ("main_mechanistic_entry", "compact_auxiliary"):
        row = (summary.get("sources") or {}).get(family) or {}
        receipt = row.get("policy_receipt") or {}
        path = Path(str(receipt.get("path") or ""))
        if (receipt.get("valid") is not True
                or receipt.get("target_date_matches") is not True
                or path != DATA_DIR / "runtime" / "mechanistic_entry_policy" / f"policy_{target_date}.json"
                or not path.is_file() or _sha(path) != receipt.get("sha256")):
            raise ValueError(f"{family}_target_policy_receipt_invalid")
        policy_receipts.append({"family": family, "path": str(path), "sha256": receipt["sha256"]})
    return {
        "controller_path": str(controller_path), "controller_sha256": _sha(controller_path),
        "summary_path": str(summary_path), "summary_sha256": _sha(summary_path),
        "policy_receipts": policy_receipts,
    }


def _generation_dir(source_date: str, target_date: str, controller_sha: str, commit: str) -> Path:
    return (PREPARED_DIR / target_date
            / f"{source_date}_{controller_sha[:16]}_{commit[:16]}")


def prepare(source_date: str, *, target_date: str | None = None,
            now: datetime | None = None) -> dict[str, Any]:
    expected = target_after_postclose(source_date, now=now)
    target_date = target_date or expected
    if target_date != expected:
        raise ValueError("preopen_target_not_next_operating_day")
    _, selection_path, commit = _selected_release()
    source = _source_receipts(source_date, target_date)
    output_dir = _generation_dir(source_date, target_date, source["controller_sha256"], commit)
    manifest = bootstrap.write_bootstrap(target_date, output_dir=output_dir)
    verification = bootstrap.verify_bootstrap(target_date, output_dir=output_dir)
    if (verification.get("status") != "pass"
            or manifest.get("selected_release_sha") != commit
            or manifest.get("source_incumbent_target_date", "") >= target_date):
        raise ValueError("prepared_bootstrap_verification_failed:" + ",".join(verification.get("findings") or []))
    manifest_file = bootstrap.manifest_path(target_date, output_dir=output_dir)
    env_file = bootstrap.env_path(target_date, output_dir=output_dir)
    verify_file = bootstrap.verify_path(target_date, output_dir=output_dir)
    receipt = {
        "schema": "next_preopen_readiness_v1",
        "status": "prepared_verified",
        "source_date": source_date,
        "target_date": target_date,
        "prepared_at_kst": (now or datetime.now(KST)).astimezone(KST).isoformat(),
        "selected_release_commit": commit,
        "selection_path": str(selection_path),
        "selection_sha256": _sha(selection_path),
        **source,
        "manifest_path": str(manifest_file), "manifest_file_sha256": _sha(manifest_file),
        "manifest_content_sha256": manifest["manifest_sha256"],
        "env_path": str(env_file), "env_sha256": _sha(env_file),
        "verification_path": str(verify_file), "verification_sha256": _sha(verify_file),
        "actual_pid_consumed": False,
        "runtime_effect": False,
        "day_of_activation_required": True,
    }
    receipt_file = output_dir / "readiness.json"
    bootstrap._publish(receipt_file, json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    index = {
        "schema": "next_preopen_readiness_index_v1",
        "target_date": target_date,
        "receipt_path": str(receipt_file),
        "receipt_sha256": _sha(receipt_file),
    }
    bootstrap._publish(PREPARED_DIR / target_date / "latest.json",
                       json.dumps(index, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    return receipt


def verify_prepared(target_date: str, *, require_today: bool = False,
                    now: datetime | None = None, generation_only: bool = False) -> dict[str, Any]:
    findings = []
    handoff_basis = ""
    current = (now or datetime.now(KST)).astimezone(KST)
    if require_today and target_date != current.date().isoformat():
        findings.append("preopen_target_not_today")
    try:
        index = _read(PREPARED_DIR / target_date / "latest.json")
        receipt_path = Path(str(index["receipt_path"]))
        if (receipt_path.resolve().parent.parent != (PREPARED_DIR / target_date).resolve()
                or _sha(receipt_path) != index["receipt_sha256"]):
            raise ValueError("prepared_receipt_path_or_hash_invalid")
        receipt = _read(receipt_path)
        if (index.get("target_date") != target_date
                or receipt.get("schema") != "next_preopen_readiness_v1"
                or receipt.get("status") != "prepared_verified"
                or receipt.get("target_date") != target_date
                or receipt.get("actual_pid_consumed") is not False
                or receipt.get("runtime_effect") is not False):
            raise ValueError("prepared_receipt_contract_invalid")
        _, selection_path, commit = _selected_release()
        source = _source_receipts(receipt["source_date"], target_date,
                                  **({"generation_only": True} if generation_only else {}))
        release_changed = (receipt["selected_release_commit"] != commit
                           or receipt["selection_sha256"] != _sha(selection_path))
        expected_source = receipt
        if release_changed:
            from src.engine.automation.intraday_release_handoff import verify as verify_intraday
            handoff = verify_intraday(target_date, commit, now=now)
            preserved = handoff.get("handoff") or {}
            if (handoff["status"] != "pass" or preserved.get("prepared_receipt_path") != str(receipt_path)
                    or preserved.get("prepared_receipt_sha256") != _sha(receipt_path)):
                raise ValueError("prepared_source_or_release_changed")
            handoff_basis = "intraday_preserved_preopen_generation"
            reseal = preserved.get('postclose_source_reseal')
            if reseal is not None:
                expected_source = reseal['current_source_receipts']
                handoff_basis = 'intraday_preserved_preopen_generation_current_postclose_resealed'
        if any(expected_source.get(key) != value for key, value in source.items()):
            raise ValueError("prepared_source_or_release_changed")
        output_dir = receipt_path.parent
        for key, path in (
            ("manifest_file_sha256", bootstrap.manifest_path(target_date, output_dir=output_dir)),
            ("env_sha256", bootstrap.env_path(target_date, output_dir=output_dir)),
            ("verification_sha256", bootstrap.verify_path(target_date, output_dir=output_dir)),
        ):
            if receipt.get(key) != _sha(path):
                raise ValueError(f"prepared_{key}_changed")
        if generation_only:
            # Reuse the sealed full PASS; no policy/economics re-evaluation.
            manifest = _read(bootstrap.manifest_path(target_date, output_dir=output_dir))
            check = _read(bootstrap.verify_path(target_date, output_dir=output_dir))
            errors = bootstrap.bootstrap_source_receipt_issues(manifest, max_source_bytes=64 * 1024 * 1024)
            quantity = manifest.get("initial_quantity_policy_receipt")
            if quantity:
                current_path = Path(quantity["current_file"])
                if _sha(current_path) != quantity["current_file_sha256"]:
                    errors.append("prepared_initial_quantity_generation_changed")
                else:
                    current_quantity = _read(current_path)
                    for key in ("policy_file", "stage_file", "parent_policy_file", "parent_current_file"):
                        if current_quantity.get(key) and (Path(current_quantity[key]).stat().st_size > 64 * 1024 * 1024
                                or _sha(Path(current_quantity[key])) != current_quantity[key + "_sha256"]):
                            errors.append("prepared_initial_quantity_source_changed")
            elif bootstrap.INITIAL_QUANTITY_CURRENT.exists():
                errors.append("prepared_initial_quantity_generation_changed")
            if (manifest.get("target_date") != target_date
                or check.get("target_date") != target_date
                or manifest.get("manifest_sha256") != receipt["manifest_content_sha256"]
                or check.get("findings") or errors):
                raise ValueError("prepared_sealed_generation_changed:" + ",".join(errors))
        else:
            check = bootstrap.verify_bootstrap(target_date, output_dir=output_dir, write=False)
        if (check.get("status") != "pass"
                or check.get("manifest_sha256") != receipt["manifest_content_sha256"]):
            raise ValueError("prepared_bootstrap_changed:" + ",".join(check.get("findings") or []))
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as exc:
        findings.append(str(exc))
        receipt = {}
    return {
        "schema": "next_preopen_readiness_verification_v1",
        "target_date": target_date,
        "status": "pass" if not findings else "fail",
        "findings": findings,
        "source_date": receipt.get("source_date"),
        "selected_release_commit": commit if handoff_basis and not findings else receipt.get("selected_release_commit"),
        "preserved_preopen_commit": receipt.get("selected_release_commit") if handoff_basis else None,
        "handoff_basis": handoff_basis,
        "actual_pid_consumed": False,
        "runtime_effect": False,
        "validation_scope": "sealed_generation" if generation_only else "current_full_contract",
    }


def verify_preopen_completion(
    target_date: str, selected_release_commit: str, *, now: datetime | None = None,
) -> dict[str, Any]:
    path = (DATA_DIR / "report" / "threshold_cycle_preopen_status"
            / f"threshold_cycle_preopen_{target_date}.status.json")
    findings = []
    current = (now or datetime.now(KST)).astimezone(KST)
    try:
        receipt = _read(path)
        updated = datetime.fromisoformat(str(receipt.get("updated_at") or ""))
        if (receipt.get("target_date") != target_date
                or receipt.get("status") != "succeeded"
                or receipt.get("exit_code") != 0
                or receipt.get("runtime_env_exists") is not True
                or updated.tzinfo is None
                or updated.astimezone(KST).date().isoformat() != target_date
                or current.date().isoformat() != target_date):
            findings.append("exact_preopen_status_not_succeeded_on_selected_release")
        elif receipt.get("selected_release_commit") != selected_release_commit:
            from src.engine.automation.intraday_release_handoff import verify as verify_intraday
            return verify_intraday(target_date, selected_release_commit, now=now)
    except (OSError, ValueError, TypeError):
        findings.append("exact_preopen_status_missing_or_invalid")
    return {"status": "pass" if not findings else "fail", "target_date": target_date,
            "findings": findings, "actual_pid_consumed": False}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--prepare", action="store_true")
    group.add_argument("--verify", action="store_true")
    group.add_argument("--verify-completion", action="store_true")
    parser.add_argument("--source-date")
    parser.add_argument("--target-date")
    parser.add_argument("--require-today", action="store_true")
    parser.add_argument("--selected-release-commit")
    args = parser.parse_args(argv)
    if args.prepare and not args.source_date:
        parser.error("--prepare requires --source-date")
    if (args.verify or args.verify_completion) and not args.target_date:
        parser.error("verification requires --target-date")
    if args.verify_completion and not args.selected_release_commit:
        parser.error("--verify-completion requires --selected-release-commit")
    try:
        result = (prepare(args.source_date, target_date=args.target_date)
                  if args.prepare else verify_prepared(args.target_date, require_today=args.require_today)
                  if args.verify else verify_preopen_completion(
                      args.target_date, args.selected_release_commit))
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as exc:
        result = {"status": "fail", "reason": str(exc), "actual_pid_consumed": False}
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] in {"prepared_verified", "pass"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
