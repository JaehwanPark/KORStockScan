"""Non-secret startup evidence; never an order or runtime-apply authority.

The widget writes its own receipt. The read-only CLI checks the systemd MainPID
and Linux start identity without opening another process's ``environ``. Receipt
hashes detect corruption, not forgery by the trusted service user. Policy hashes
describe the in-memory startup configuration, not later policy reloads.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import stat
import subprocess
import tempfile
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

SCHEMA = "widget_startup_runtime_receipt_v1"
UNIT = "korstockscan-widget-signal-auto-trader.service"
# Keep the diagnostic CLI stdlib-only; importing live constants transitively
# initializes broker configuration in the trading package.
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RECEIPT_PATH = (
    PROJECT_ROOT / "data/runtime/widget_signal_auto_trade_state.runtime-receipt.json"
)
KST = ZoneInfo("Asia/Seoul")
# Exact allowlist: no provider keys, tokens, account identifiers, prefix matching,
# or raw environment values are serialized, including in exception messages.
ENV_KEYS = (
    "KORSTOCKSCAN_WIDGET_AUTO_TRADER_ENABLED",
    "KORSTOCKSCAN_WIDGET_AUTO_TRADER_ENTRY_QTY",
    "KORSTOCKSCAN_WIDGET_AUTO_TRADER_SYMBOLS",
    "KORSTOCKSCAN_WIDGET_AUTO_TRADER_SAMSUNG_EXECUTION_POLICY",
    "KORSTOCKSCAN_WIDGET_AUTO_TRADER_ENTRY_TELEGRAM_ENABLED",
    "KORSTOCKSCAN_WIDGET_EPISODE_MARKET_WEAKNESS_ENTRY_GUARD_ENABLED",
    "KORSTOCKSCAN_SYMBOL_OWNER_POLICY_FILE",
    "KORSTOCKSCAN_ORDER_OWNER_REGISTRY_PATH",
)
AUTHORITY = {
    "decision_authority": "startup_configuration_observation_only",
    "runtime_effect": False,
    "allowed_runtime_apply": False,
    "current_policy_consumption_verified": False,
}
MAX_RECEIPT_BYTES = 65536


def content_hash(value: object) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def environment_hashes(environment: dict[str, str]) -> dict[str, str | None]:
    return {
        key: content_hash(environment[key]) if key in environment else None
        for key in ENV_KEYS
    }


def process_identity(pid: int, *, proc_root: Path = Path("/proc")) -> dict:
    if type(pid) is not int or pid <= 0:
        raise ValueError("invalid_pid")
    path = proc_root / str(pid)
    # comm may contain spaces and parentheses. Field 22 is starttime.
    fields = (path / "stat").read_text().rsplit(") ", 1)[1].split()
    if fields[0] in {"Z", "X", "x"}:
        raise ValueError("process_not_running")
    start_ticks = int(fields[19])
    if start_ticks <= 0:
        raise ValueError("process_start_unavailable")
    status = {
        line.split(":", 1)[0]: line.split(":", 1)[1].split()
        for line in (path / "status").read_text().splitlines()
        if ":" in line
    }
    boot_id = (proc_root / "sys/kernel/random/boot_id").read_text().strip()
    if not re.fullmatch(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}", boot_id):
        raise ValueError("boot_identity_invalid")
    uids = [int(value) for value in status["Uid"]]
    gids = [int(value) for value in status["Gid"]]
    if len(uids) != 4 or len(gids) != 4 or min(*uids, *gids) < 0:
        raise ValueError("process_credentials_invalid")
    return {
        "pid": pid,
        "start_ticks": start_ticks,
        "boot_id": boot_id,
        "uids": uids,
        "gids": gids,
    }


def receipt_path(state_path: Path) -> Path:
    return state_path.with_suffix(".runtime-receipt.json")


def _warn_safely(message: str) -> None:
    """Diagnostics must not interrupt custody when the logging sink fails too."""
    try:
        logging.getLogger(__name__).warning(message)
    except Exception:
        try:
            # Only internal fixed messages are accepted by callers. Never emit
            # the exception or environment, including on the fallback path.
            os.write(2, (message + "\n").encode("ascii"))
        except Exception:
            # With both sinks unavailable, missing evidence still fails the
            # verifier. Preserve the existing trading/custody control flow.
            pass


def publish_startup_receipt(trader, *, interval_sec: float, once: bool) -> bool:
    """Best-effort observation after construction, before the first trade cycle.

    Instrumentation failure is visible but cannot interrupt existing custody or
    weaken order guards. A missing receipt blocks only the diagnostic verifier.
    """
    temporary = None
    try:
        payload = {
            "schema_version": SCHEMA,
            **AUTHORITY,
            "snapshot_phase": "startup_before_first_cycle",
            "captured_at_kst": datetime.now(KST).isoformat(),
            "startup_policy_date": trader._policy_date.isoformat(),
            "process": process_identity(os.getpid()),
            "environment_hashes": environment_hashes(os.environ),
            "effective_config_sha256": content_hash(
                {
                    "enabled": trader.enabled,
                    "entry_qty": trader.entry_qty,
                    "symbols": sorted(spec.code for spec in trader.specs),
                    "execution_policy_manifest": trader._configured_execution_policies,
                    "interval_sec": max(0.5, float(interval_sec)),
                    "once": bool(once),
                }
            ),
            "loaded_execution_policies_sha256": content_hash(
                trader._dated_execution_policies
            ),
        }
        payload["receipt_sha256"] = content_hash(payload)
        destination = receipt_path(trader.state_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        # mkstemp is 0600 even under a permissive umask. Same UID can read this
        # ordinary file despite the service's distinct primary group.
        fd, temporary = tempfile.mkstemp(
            prefix=".widget-receipt-", dir=destination.parent
        )
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, sort_keys=True, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, destination)
        temporary = None
        return True
    except Exception:
        # No exception text/traceback: malformed config may contain secrets.
        _warn_safely("widget_runtime_receipt_publish_failed")
        return False
    finally:
        if temporary is not None:
            try:
                Path(temporary).unlink()
            except OSError:
                _warn_safely("widget_runtime_receipt_cleanup_failed")


def _systemd_identity() -> dict:
    result = subprocess.run(
        [
            "systemctl",
            "show",
            UNIT,
            "--property=MainPID,ActiveState,SubState,ControlGroup",
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=5,
    )
    fields = dict(
        line.split("=", 1) for line in result.stdout.splitlines() if "=" in line
    )
    if fields.get("ActiveState") != "active" or fields.get("SubState") != "running":
        raise ValueError("unit_not_running")
    if not fields.get("ControlGroup"):
        raise ValueError("unit_cgroup_missing")
    return {"pid": int(fields["MainPID"]), "cgroup": fields["ControlGroup"]}


def _file_identity(info: os.stat_result) -> dict:
    return {
        "device": info.st_dev,
        "inode": info.st_ino,
        "uid": info.st_uid,
        "gid": info.st_gid,
        "mode": info.st_mode,
        "size": info.st_size,
        "mtime_ns": info.st_mtime_ns,
        "ctime_ns": info.st_ctime_ns,
    }


def _read_json_snapshot(path: Path) -> tuple[dict, dict]:
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate_json_key")
            result[key] = value
        return result

    # Never block on FIFO/device artifacts or follow a replaced symlink.
    fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
    with os.fdopen(fd, "rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode):
            raise ValueError("non_regular_json_file")
        identity = _file_identity(info)
        raw = stream.read(MAX_RECEIPT_BYTES + 1)
        if _file_identity(os.fstat(stream.fileno())) != identity:
            raise ValueError("json_changed_during_read")
    if len(raw) > MAX_RECEIPT_BYTES:
        raise ValueError("oversized_json")
    payload = json.loads(raw, object_pairs_hook=unique_pairs)
    if not isinstance(payload, dict):
        raise ValueError("invalid_json_object")
    return payload, identity


def _read_json(path: Path) -> dict:
    return _read_json_snapshot(path)[0]


def verify_startup_receipt(
    path: Path,
    *,
    target_date: date,
    expected_environment: dict | None = None,
    expected_config_sha256: str | None = None,
    expected_policy_sha256: str | None = None,
) -> dict:
    """Return bounded diagnostic output; never echo file contents or exceptions."""
    result = {"status": "blocked", "passed": False, **AUTHORITY, "findings": []}
    stage = "receipt_missing_or_invalid"
    try:
        try:
            payload, file_identity = _read_json_snapshot(path)
        except FileNotFoundError:
            stage = "receipt_missing"
            raise
        except PermissionError:
            stage = "receipt_unreadable"
            raise
        digest = payload.pop("receipt_sha256", None)
        if digest != content_hash(payload) or payload.get("schema_version") != SCHEMA:
            raise ValueError("invalid_receipt")
        for key, value in AUTHORITY.items():
            if type(payload.get(key)) is not type(value) or payload[key] != value:
                raise ValueError("invalid_authority")
        if payload.get("snapshot_phase") != "startup_before_first_cycle":
            raise ValueError("invalid_phase")
        hashes = payload.get("environment_hashes")
        if not isinstance(hashes, dict) or set(hashes) != set(ENV_KEYS):
            raise ValueError("invalid_environment_contract")
        if any(value is not None and not _is_hash(value) for value in hashes.values()):
            raise ValueError("invalid_environment_digest")
        if not all(
            _is_hash(payload.get(key))
            for key in ("effective_config_sha256", "loaded_execution_policies_sha256")
        ):
            raise ValueError("invalid_configuration_digest")
        stage = "startup_date_mismatch"
        captured = datetime.fromisoformat(payload["captured_at_kst"])
        if (
            captured.tzinfo is None
            or captured.astimezone(KST).date() != target_date
            or payload["startup_policy_date"] != target_date.isoformat()
            or captured > datetime.now(KST)
        ):
            raise ValueError("invalid_date")
        stage = "process_identity_unverified"
        unit = _systemd_identity()
        identity = process_identity(unit["pid"])
        # Canonical encoding also rejects bool/int credential substitutions.
        if content_hash(payload.get("process")) != content_hash(identity):
            raise ValueError("old_or_wrong_process")
        stage = "receipt_owner_or_permissions_invalid"
        if (
            file_identity["uid"] != identity["uids"][3]
            or stat.S_IMODE(file_identity["mode"]) != 0o600
        ):
            raise ValueError("untrusted_receipt_file")
        # No /proc/<pid>/environ reads and no sudo/setgid/ptrace fallback.
        stage = "expectation_invalid"
        expected = expected_environment if expected_environment is not None else {}
        if not isinstance(expected, dict) or set(expected) - set(ENV_KEYS):
            raise ValueError("unsupported_expectation")
        if any(
            value is not None and not isinstance(value, str)
            for value in expected.values()
        ):
            raise ValueError("invalid_expectation_type")
        for value in (expected_config_sha256, expected_policy_sha256):
            if value is not None and not _is_hash(value):
                raise ValueError("invalid_expected_digest")
        stage = "configuration_mismatch"
        mismatches = [
            key
            for key, value in expected.items()
            if hashes[key] != (content_hash(value) if value is not None else None)
        ]
        if (
            expected_config_sha256 is not None
            and payload["effective_config_sha256"] != expected_config_sha256
        ):
            mismatches.append("effective_config_sha256")
        if (
            expected_policy_sha256 is not None
            and payload["loaded_execution_policies_sha256"] != expected_policy_sha256
        ):
            mismatches.append("loaded_execution_policies_sha256")
        result["mismatched_keys"] = sorted(mismatches)
        if mismatches:
            raise ValueError("configuration_mismatch")
        stage = "process_changed_during_verification"
        if _systemd_identity() != unit or process_identity(unit["pid"]) != identity:
            raise ValueError("process_changed")
        stage = "receipt_changed_during_verification"
        latest, latest_file_identity = _read_json_snapshot(path)
        if latest_file_identity != file_identity or content_hash(
            latest
        ) != content_hash({**payload, "receipt_sha256": digest}):
            raise ValueError("receipt_generation_changed")
        result.update(
            {
                "receipt_sha256": digest,
                "pid": unit["pid"],
                "target_date": target_date.isoformat(),
                "verified_environment_keys": sorted(expected),
                "effective_config_sha256": payload["effective_config_sha256"],
                "loaded_execution_policies_sha256": payload[
                    "loaded_execution_policies_sha256"
                ],
            }
        )
        if (
            not expected
            and expected_config_sha256 is None
            and expected_policy_sha256 is None
        ):
            result.update(
                status="observed_not_compared",
                findings=["expected_configuration_not_supplied"],
            )
        else:
            result.update(status="verified_requested_startup_fields", passed=True)
    except Exception:
        result["findings"] = [stage]
    return result


def _is_hash(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-date", required=True, type=date.fromisoformat)
    parser.add_argument("--receipt-path", type=Path, default=DEFAULT_RECEIPT_PATH)
    parser.add_argument("--expected-env-json", type=Path)
    parser.add_argument("--expected-config-sha256")
    parser.add_argument("--expected-policy-sha256")
    args = parser.parse_args(argv)
    try:
        expected = (
            _read_json(args.expected_env_json) if args.expected_env_json else None
        )
    except Exception:
        print(
            json.dumps(
                {
                    "status": "blocked",
                    "passed": False,
                    **AUTHORITY,
                    "findings": ["expectation_file_invalid"],
                }
            )
        )
        return 2
    result = verify_startup_receipt(
        args.receipt_path,
        target_date=args.target_date,
        expected_environment=expected,
        expected_config_sha256=args.expected_config_sha256,
        expected_policy_sha256=args.expected_policy_sha256,
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
