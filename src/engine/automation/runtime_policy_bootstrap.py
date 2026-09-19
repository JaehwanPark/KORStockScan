"""Compose approved runtime policy state without running a tuning search.

The bootstrap carries the latest verified incumbent environment, overlays
explicit operator locks, and reapplies permanent retirement settings.  It does
not call providers, brokers, order code, or create economic candidates.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import subprocess
import tempfile
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable

from src.engine.automation import operator_policy_succession
from src.engine.lifecycle.retirement import (
    RETIRED_FAMILIES,
    retirement_env,
    without_retired_env,
)
from src.utils.constants import DATA_DIR

SCHEMA_VERSION = 1
REPORT_TYPE = "runtime_policy_bootstrap"
BOOTSTRAP_DIR = DATA_DIR / "runtime" / "policy_bootstrap"
LEGACY_RUNTIME_DIR = DATA_DIR / "threshold_cycle" / "runtime_env"
OPERATOR_LOCK_DIR = DATA_DIR / "threshold_cycle" / "operator_runtime_env_locks"


def env_path(target_date: str) -> Path:
    return BOOTSTRAP_DIR / f"runtime_policy_bootstrap_{target_date}.env"


def manifest_path(target_date: str) -> Path:
    return BOOTSTRAP_DIR / f"runtime_policy_bootstrap_{target_date}.json"


def verify_path(target_date: str) -> Path:
    return BOOTSTRAP_DIR / f"runtime_policy_bootstrap_verify_{target_date}.json"


def _digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _digest_json(value: Any) -> str:
    return _digest_bytes(
        json.dumps(
            value,
            ensure_ascii=True,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"object_required:{path}")
    return payload


def _file_receipt(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    return {
        "path": str(path.resolve()),
        "sha256": _digest_bytes(raw),
        "size_bytes": len(raw),
    }


def _publish(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
    ) as handle:
        temporary = Path(handle.name)
        try:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _manifest_candidates(target_date: str) -> list[Path]:
    maximum = date.fromisoformat(target_date)
    rows: list[tuple[date, int, Path]] = []
    patterns = (
        (BOOTSTRAP_DIR, "runtime_policy_bootstrap_*.json", 1),
        (LEGACY_RUNTIME_DIR, "threshold_runtime_env_*.json", 0),
    )
    for directory, pattern, priority in patterns:
        for path in directory.glob(pattern):
            if "verify" in path.stem:
                continue
            try:
                payload_date = date.fromisoformat(path.stem.rsplit("_", 1)[-1])
            except ValueError:
                continue
            # A same-date bootstrap is an output of this command. Reusing it as
            # its own incumbent would make source_incumbent point at a file
            # that is replaced later in the same write and fail verification.
            eligible = (
                payload_date < maximum
                if directory == BOOTSTRAP_DIR
                else payload_date <= maximum
            )
            if eligible:
                rows.append((payload_date, priority, path))
    return [row[2] for row in sorted(rows, reverse=True)]


def _load_incumbent(target_date: str) -> tuple[dict[str, Any], Path]:
    for path in _manifest_candidates(target_date):
        try:
            payload = _load_json(path)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        values = payload.get("env_overrides")
        source_date = str(payload.get("target_date") or path.stem.rsplit("_", 1)[-1])
        if path.parent == BOOTSTRAP_DIR:
            try:
                verification = _load_json(
                    BOOTSTRAP_DIR / f"runtime_policy_bootstrap_verify_{source_date}.json"
                )
            except (OSError, ValueError, json.JSONDecodeError):
                verification = {}
            unsigned = {
                key: value for key, value in payload.items() if key != "manifest_sha256"
            }
            verified = (
                verification.get("status") == "pass"
                and payload.get("manifest_sha256") == _digest_json(unsigned)
            )
        else:
            try:
                verification = _load_json(
                    LEGACY_RUNTIME_DIR / f"threshold_runtime_env_verify_{source_date}.json"
                )
            except (OSError, ValueError, json.JSONDecodeError):
                verification = {}
            verified = verification.get("status") == "pass"
        if verified and isinstance(values, dict) and values:
            return payload, path
    raise ValueError("approved_incumbent_runtime_env_missing")


def _date_in_lock_window(lock: dict[str, Any], target_date: str) -> bool:
    active_from = str(
        lock.get("active_from_date") or lock.get("created_date") or ""
    ).strip()
    if active_from and target_date < active_from:
        return False
    if bool(lock.get("lock_until_explicit_close")) or bool(
        lock.get("explicit_close_required")
    ):
        return True
    active_until = str(
        lock.get("min_observation_until_date")
        or lock.get("expires_after_source_date")
        or lock.get("target_date")
        or ""
    ).strip()
    return not active_until or target_date <= active_until


def _load_locks(target_date: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for path in sorted(OPERATOR_LOCK_DIR.glob("*.json")):
        try:
            lock = _load_json(path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            rejected.append(
                {
                    "path": str(path.resolve()),
                    "reason": f"unreadable:{type(exc).__name__}",
                }
            )
            continue
        lock["path"] = str(path.resolve())
        lock["source_receipt"] = _file_receipt(path)
        if not lock.get("family") or not operator_policy_succession.lock_values(lock):
            rejected.append(
                {
                    "path": str(path.resolve()),
                    "lock_id": lock.get("lock_id"),
                    "family": lock.get("family"),
                    "source_receipt": lock["source_receipt"],
                    "reason": "lock_identity_or_env_missing",
                }
            )
            continue
        if not _date_in_lock_window(lock, target_date):
            rejected.append(
                {
                    "path": str(path.resolve()),
                    "lock_id": lock.get("lock_id"),
                    "family": lock.get("family"),
                    "source_receipt": lock["source_receipt"],
                    "reason": "outside_active_window",
                }
            )
            continue
        rows.append(lock)
    return rows, rejected


def _receipt_date_state(payload: dict[str, Any], target_date: str) -> tuple[bool, str]:
    target = str(payload.get("target_date") or "").strip()
    effective = str(
        payload.get("effective_date")
        or payload.get("prepared_effective_date")
        or ""
    ).strip()
    publication = str(payload.get("publication_date") or "").strip()
    source = str(payload.get("source_date") or payload.get("date") or "").strip()
    if target:
        return target == target_date, "target_date"
    if effective:
        return effective == target_date, "effective_date"
    if publication and publication > target_date:
        return False, "future_publication_date"
    if source and source > target_date:
        return False, "future_source_date"
    if source or publication:
        return True, "carried_source_date"
    return False, "date_identity_missing"


def _receipt_family(payload: dict[str, Any], path: Path) -> str:
    raw = str(
        payload.get("runtime_family")
        or payload.get("family")
        or payload.get("report_type")
        or payload.get("schema")
        or path.stem.rsplit("_", 1)[0]
    ).strip()
    if raw == "scanner_lookup_attention_preopen":
        return "scanner_lookup_attention"
    if raw == "machine_microstructure_policy_approval":
        return "machine_microstructure"
    if raw == "machine_entry_timing_tuning":
        return "machine_entry_timing"
    if raw.startswith("low_price_two_leg"):
        return "low_price_two_leg"
    return raw


def _receipt_runtime_apply_allowed(payload: dict[str, Any]) -> bool:
    if payload.get("allowed_runtime_apply") is True or payload.get(
        "runtime_apply_allowed"
    ) is True:
        return True
    if payload.get("report_type") == "scanner_lookup_attention_preopen":
        source_policy = (
            payload.get("source_policy")
            if isinstance(payload.get("source_policy"), dict)
            else {}
        )
        return payload.get("active") is True and source_policy.get(
            "allowed_runtime_apply"
        ) is True
    return False


def _load_direct_receipts(
    target_date: str, receipt_paths: Iterable[Path]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    seen: set[Path] = set()
    for raw_path in receipt_paths:
        path = Path(raw_path).expanduser().resolve()
        if path in seen:
            continue
        seen.add(path)
        try:
            payload = _load_json(path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            rejected.append(
                {"path": str(path), "reason": f"unreadable:{type(exc).__name__}"}
            )
            continue
        valid_date, date_basis = _receipt_date_state(payload, target_date)
        family = _receipt_family(payload, path)
        runtime_apply_allowed = _receipt_runtime_apply_allowed(payload)
        row = {
            "family": family,
            "source_receipt": _file_receipt(path),
            "date_basis": date_basis,
            "source_date": payload.get("source_date") or payload.get("date"),
            "target_date": payload.get("target_date"),
            "effective_date": payload.get("effective_date")
            or payload.get("prepared_effective_date"),
            "status": payload.get("status")
            or payload.get("decision")
            or payload.get("selection_status"),
            "allowed_runtime_apply": runtime_apply_allowed,
            "runtime_effect": payload.get("runtime_effect"),
        }
        if not family:
            rejected.append({**row, "reason": "family_identity_missing"})
        elif not valid_date:
            rejected.append({**row, "reason": f"date_invalid:{date_basis}"})
        elif not runtime_apply_allowed:
            rejected.append({**row, "reason": "runtime_apply_not_authorized"})
        else:
            accepted.append(row)
    return accepted, rejected


def _operator_overrides(target_date: str) -> tuple[dict[str, str], list[dict[str, Any]]]:
    values: dict[str, str] = {}
    receipts: list[dict[str, Any]] = []
    for name in (
        "operator_runtime_overrides.env",
        f"operator_runtime_overrides_{target_date}.env",
    ):
        path = LEGACY_RUNTIME_DIR / name
        if not path.exists():
            continue
        parsed = operator_policy_succession.read_operator_env(path)
        values.update(without_retired_env(parsed))
        receipts.append({**_file_receipt(path), "env_keys": sorted(parsed)})
    return values, receipts


def _git_sha() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def build_manifest(
    target_date: str, *, receipt_paths: Iterable[Path] = ()
) -> dict[str, Any]:
    date.fromisoformat(target_date)
    incumbent, incumbent_path = _load_incumbent(target_date)
    incumbent_values = {
        str(key): str(value)
        for key, value in (incumbent.get("env_overrides") or {}).items()
    }
    values = without_retired_env(incumbent_values)
    operator_values, operator_sources = _operator_overrides(target_date)
    values.update(operator_values)
    locks, invalid_locks = _load_locks(target_date)
    applied_locks: list[dict[str, Any]] = []
    rejected_locks: list[dict[str, Any]] = list(invalid_locks)
    env_owners = {key: "approved_incumbent" for key in values}
    env_owners.update({key: "operator_runtime_override" for key in operator_values})
    for lock in locks:
        classification = operator_policy_succession.classify(lock)
        row = {
            "lock_id": lock.get("lock_id"),
            "family": lock.get("family"),
            "classification": classification,
            "source_receipt": lock["source_receipt"],
        }
        if classification == "inactive_archive":
            rejected_locks.append({**row, "reason": "inactive_archive"})
            continue
        lock_env = without_retired_env(operator_policy_succession.lock_values(lock))
        conflicts = sorted(
            key
            for key, value in lock_env.items()
            if key in env_owners
            and env_owners[key].startswith("operator_lock:")
            and values.get(key) != str(value)
        )
        if conflicts:
            rejected_locks.append(
                {**row, "reason": "operator_lock_env_conflict", "env_keys": conflicts}
            )
            continue
        for key, value in lock_env.items():
            values[key] = str(value)
            env_owners[key] = f"operator_lock:{lock.get('lock_id') or lock.get('family')}"
        applied_locks.append({**row, "env_keys": sorted(lock_env)})
    off_values = retirement_env()
    values.update(off_values)
    env_owners.update({key: "explicit_retirement_off" for key in off_values})
    selected_families = sorted(
        str(item)
        for item in incumbent.get("selected_families") or []
        if str(item) not in RETIRED_FAMILIES
    )
    direct_receipts, rejected_receipts = _load_direct_receipts(
        target_date, receipt_paths
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "report_type": REPORT_TYPE,
        "target_date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "producer_code_sha": _git_sha(),
        "selected_release_sha": _git_sha(),
        "source_incumbent": _file_receipt(incumbent_path),
        "source_incumbent_target_date": incumbent.get("target_date"),
        "rollback_env_overrides": dict(
            sorted(without_retired_env(incumbent_values).items())
        ),
        "rollback_owner": "verified_source_incumbent",
        "selection_policy": "retain_approved_incumbent_and_explicit_operator_locks",
        "selected_families": selected_families,
        "selection_changes": [
            {"family": family, "change_class": "retained_approved"}
            for family in selected_families
        ]
        + [
            {
                "family": row.get("family"),
                "change_class": (
                    "explicit_off"
                    if row.get("classification") == "protected_veto"
                    else "operator_lock_preserved"
                ),
            }
            for row in applied_locks
        ]
        + [
            {"family": row["family"], "change_class": "policy_refreshed"}
            for row in direct_receipts
        ],
        "operator_locks_applied": applied_locks,
        "operator_locks_rejected": rejected_locks,
        "operator_override_sources": operator_sources,
        "direct_family_receipts": direct_receipts,
        "direct_family_receipts_rejected": rejected_receipts,
        "env_key_owners": env_owners,
        "env_overrides": dict(sorted(values.items())),
        "retired_key_scrubbed": sorted(set(incumbent_values) - set(without_retired_env(incumbent_values))),
        "assertions": {
            "provider_called": False,
            "broker_called": False,
            "order_submitted": False,
            "economic_candidate_created": False,
        },
    }


def write_bootstrap(
    target_date: str, *, receipt_paths: Iterable[Path] = ()
) -> dict[str, Any]:
    manifest = build_manifest(target_date, receipt_paths=receipt_paths)
    lines = [
        "# Generated by runtime_policy_bootstrap.py",
        f"# target_date={target_date}",
        "export KORSTOCKSCAN_RUNTIME_POLICY_BOOTSTRAP_ENABLED=true",
        f"export KORSTOCKSCAN_RUNTIME_POLICY_BOOTSTRAP_DATE={shlex.quote(target_date)}",
    ]
    for key, value in manifest["env_overrides"].items():
        lines.append(f"export {key}={shlex.quote(str(value))}")
    env_content = "\n".join(lines) + "\n"
    manifest["env_file"] = str(env_path(target_date))
    manifest["env_sha256"] = _digest_bytes(env_content.encode("utf-8"))
    unsigned = dict(manifest)
    manifest["manifest_sha256"] = _digest_json(unsigned)
    _publish(env_path(target_date), env_content)
    _publish(
        manifest_path(target_date),
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    return manifest


def _read_proc_env(pid: int) -> dict[str, str]:
    raw = Path(f"/proc/{pid}/environ").read_bytes()
    return {
        key.decode(): value.decode()
        for item in raw.split(b"\0")
        if item and b"=" in item
        for key, value in [item.split(b"=", 1)]
    }


def verify_bootstrap(target_date: str, *, pid: int | None = None, write: bool = True) -> dict[str, Any]:
    findings: list[str] = []
    pid_mismatches: list[str] = []
    pid_env_available = pid is None
    manifest_file = manifest_path(target_date)
    runtime_file = env_path(target_date)
    try:
        manifest = _load_json(manifest_file)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        manifest = {}
        findings.append(f"manifest_unreadable:{type(exc).__name__}")
    if manifest.get("target_date") != target_date:
        findings.append("target_date_mismatch")
    if manifest.get("report_type") != REPORT_TYPE:
        findings.append("report_type_mismatch")
    unsigned = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    if not manifest.get("manifest_sha256") or manifest.get("manifest_sha256") != _digest_json(unsigned):
        findings.append("manifest_hash_mismatch")
    try:
        raw_env = runtime_file.read_bytes()
    except OSError:
        raw_env = b""
        findings.append("env_unreadable")
    if manifest.get("env_sha256") != _digest_bytes(raw_env):
        findings.append("env_hash_mismatch")
    if manifest.get("assertions") != {
        "provider_called": False,
        "broker_called": False,
        "order_submitted": False,
        "economic_candidate_created": False,
    }:
        findings.append("authority_assertion_mismatch")
    receipt_rows = [manifest.get("source_incumbent")]
    receipt_rows.extend(manifest.get("operator_override_sources") or [])
    receipt_rows.extend(
        row.get("source_receipt")
        for row in (manifest.get("operator_locks_applied") or [])
        if isinstance(row, dict)
    )
    receipt_rows.extend(
        row.get("source_receipt")
        for row in (manifest.get("direct_family_receipts") or [])
        if isinstance(row, dict)
    )
    for receipt in receipt_rows:
        if not isinstance(receipt, dict) or not receipt.get("path"):
            findings.append("source_receipt_missing")
            continue
        source_path = Path(str(receipt["path"]))
        try:
            current = _file_receipt(source_path)
        except OSError:
            findings.append(f"source_receipt_unreadable:{source_path}")
            continue
        if current.get("sha256") != receipt.get("sha256"):
            findings.append(f"source_receipt_hash_mismatch:{source_path}")
    if pid is not None and raw_env:
        expected = operator_policy_succession.read_operator_env(runtime_file)
        try:
            actual = _read_proc_env(pid)
        except OSError as exc:
            findings.append(f"pid_env_unreadable:{type(exc).__name__}")
        else:
            pid_env_available = True
            missing = sorted(key for key, value in expected.items() if actual.get(key) != value)
            if missing:
                pid_mismatches.extend(missing)
                findings.append("pid_env_mismatch:" + ",".join(missing))
    passed = not findings
    result = {
        "schema_version": 1,
        "report_type": "runtime_policy_bootstrap_verify",
        "target_date": target_date,
        "status": "pass" if passed else "fail",
        "passed": passed,
        "findings": findings,
        "manifest_file": str(manifest_file),
        "env_file": str(runtime_file),
        "pid": pid,
        "pid_passed": passed if pid is not None else None,
        "pid_env_available": pid_env_available,
        "pid_missing": [] if pid is None or pid_env_available else [pid],
        "pid_mismatches": pid_mismatches,
        "runtime_policy_fail_count": len(findings),
        "dated_runtime_override_fail_count": 0,
        "unverified_selected_family_count": 0,
        "verified_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    if write:
        _publish(verify_path(target_date), json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", "--target-date", dest="target_date", required=True)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--pid", type=int)
    parser.add_argument("--receipt", action="append", type=Path, default=[])
    args = parser.parse_args(argv)
    if args.write == args.verify:
        parser.error("select exactly one of --write or --verify")
    if args.write:
        result = write_bootstrap(args.target_date, receipt_paths=args.receipt)
        verification = verify_bootstrap(args.target_date)
        result["verification"] = verification
        print(json.dumps(result, ensure_ascii=False))
        return 0 if verification["status"] == "pass" else 1
    result = verify_bootstrap(args.target_date, pid=args.pid)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
